#!/usr/bin/env python3
"""Seasonality lookahead: which topics peak in the next 6-10 weeks.

A page has to be live and indexed weeks before its season, so selection needs
to know today what will be big in two months. This reads the saved historical
keyword data for the radar seeds and the site's top queries, builds a mean
volume per calendar month for each keyword, compares the month `--lead-weeks`
ahead against this month, and suggests a movement bonus that select.md applies.

It is a report, not a gate. It always exits 0.

Usage
  seasonality.py --data .seo/seasonality.json
  seasonality.py --data .seo/seasonality.json --today 2026-09-09 --lead-weeks 8
  seasonality.py --data .seo/seasonality.json --json --out .seo/seasonality-report.json

Inputs
  --data  any of:
            the raw dataforseo_labs_google_historical_keyword_data response
              (tasks[0].result[0].items[] with keyword + history[]),
            a flat {keyword: [{year, month, search_volume}, ...]} map,
            or a list of {keyword, monthly: [{year, month, search_volume}]}.
          For every keyword item every {year, month, search_volume} triple found
          anywhere under it is collected and deduped by (year, month), so the
          exact nesting does not matter.

Status per keyword
  rising        volume `lead_weeks` ahead >= min-ratio x this month (and >= min-volume)
  peaking       the peak month is this month or next
  falling       volume ahead <= this month / min-ratio
  flat          none of the above
  insufficient  fewer than 12 data points, or no data for now/ahead month

Bonus: rising +1 (+2 when ahead is 2x now), falling -1, else 0.

Standard library only.
"""

import argparse
import calendar
import datetime
import json
import sys

MIN_POINTS = 12
STATUS_ORDER = ["rising", "peaking", "flat", "falling", "insufficient"]


# ------------------------------------------------------------------- loading

def load_json(path):
    with open(path) as fh:
        raw = fh.read()
    try:
        doc = json.loads(raw)
    except ValueError as ex:
        raise SystemExit("could not parse %s: %s" % (path, ex))
    # Some clients wrap the payload as {"result": "<json string>"}.
    for _ in range(3):
        if isinstance(doc, dict):
            inner = next((doc[k] for k in ("result", "content", "data", "text")
                          if isinstance(doc.get(k), str)
                          and doc[k].lstrip()[:1] in "[{"), None)
            if inner is None:
                break
            try:
                doc = json.loads(inner)
            except ValueError:
                break
    return doc


def _triple(d):
    """(year, month, volume) if this dict is a monthly point, else None."""
    if "year" not in d or "month" not in d:
        return None
    sv = d.get("search_volume")
    if sv is None and isinstance(d.get("keyword_info"), dict):
        sv = d["keyword_info"].get("search_volume")
    try:
        y, m = int(d["year"]), int(d["month"])
        return (y, m, int(sv)) if sv is not None and 1 <= m <= 12 else None
    except (TypeError, ValueError):
        return None


def collect_points(node, out):
    """Walk dicts/lists; every {year, month, search_volume} lands in out."""
    if isinstance(node, dict):
        t = _triple(node)
        if t:
            out.setdefault((t[0], t[1]), t[2])
        for v in node.values():
            collect_points(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_points(v, out)


def find_items(node, depth=0):
    """The list of {keyword: ...} dicts, wherever the payload keeps it."""
    if depth > 8:
        return None
    if isinstance(node, list):
        if node and all(isinstance(x, dict) and "keyword" in x for x in node):
            return node
        for v in node:
            got = find_items(v, depth + 1)
            if got:
                return got
    elif isinstance(node, dict):
        vals = list(node.values())
        if vals and all(isinstance(v, list) for v in vals) \
                and any(isinstance(x, dict) and _triple(x) for v in vals for x in v):
            return [{"keyword": k, "monthly": v} for k, v in node.items()]
        for v in vals:
            got = find_items(v, depth + 1)
            if got:
                return got
    return None


def load_keywords(path, notes):
    """{keyword: {(year, month): volume}}"""
    items = find_items(load_json(path))
    if not items:
        notes.append("no keyword items found in %s" % path)
        return {}
    out = {}
    for item in items:
        kw = str(item.get("keyword") or "").strip()
        if not kw:
            continue
        points = out.setdefault(kw, {})
        collect_points(item, points)
    return out


# ------------------------------------------------------------------- compute

def month_ahead(today, lead_weeks):
    return (today + datetime.timedelta(weeks=lead_weeks)).month


def analyse(keyword, points, today, lead_weeks, min_ratio, min_volume):
    rec = {"keyword": keyword, "points": len(points), "annual_mean": None,
           "peak_month": None, "peak_ratio": None,
           "now_month": today.month, "now_volume": None,
           "ahead_month": month_ahead(today, lead_weeks), "ahead_volume": None,
           "ahead_ratio": None, "status": "insufficient", "bonus": 0}
    if len(points) < MIN_POINTS:
        return rec
    by_month = {}
    for (_, m), sv in points.items():
        by_month.setdefault(m, []).append(sv)
    means = {m: sum(v) / float(len(v)) for m, v in by_month.items()}
    annual = sum(means.values()) / float(len(means))
    peak_month = max(means, key=lambda m: means[m])
    rec.update({
        "annual_mean": round(annual, 1),
        "peak_month": peak_month,
        "peak_ratio": round(means[peak_month] / annual, 2) if annual else None,
        "now_volume": (round(means[rec["now_month"]])
                       if rec["now_month"] in means else None),
        "ahead_volume": (round(means[rec["ahead_month"]])
                         if rec["ahead_month"] in means else None),
    })
    now, ahead = rec["now_volume"], rec["ahead_volume"]
    if now is None or ahead is None:
        return rec
    ratio = ahead / float(max(now, 1))
    rec["ahead_ratio"] = round(ratio, 2)
    next_month = rec["now_month"] % 12 + 1
    if ratio >= min_ratio and ahead >= min_volume:
        rec["status"], rec["bonus"] = "rising", (2 if ratio >= 2.0 else 1)
    elif peak_month in (rec["now_month"], next_month):
        rec["status"] = "peaking"
    elif ratio <= 1.0 / min_ratio:
        rec["status"], rec["bonus"] = "falling", -1
    else:
        rec["status"] = "flat"
    return rec


# -------------------------------------------------------------------- output

def _mon(m):
    return calendar.month_abbr[m] if m else "-"


def summary_line(rows):
    counts = {s: sum(1 for r in rows if r["status"] == s) for s in STATUS_ORDER}
    top = [r["keyword"] for r in rows if r["status"] == "rising"][:3]
    top_s = " (top: %s)" % ", ".join(top) if top else ""
    return ("Seasonality: %d rising%s, %d peaking, %d falling, %d flat, "
            "%d insufficient" % (counts["rising"], top_s, counts["peaking"],
                                 counts["falling"], counts["flat"],
                                 counts["insufficient"]))


def print_report(rows, today, lead_weeks, notes):
    print("Seasonality lookahead — today %s, %d weeks ahead (%s)"
          % (today.isoformat(), lead_weeks, _mon(month_ahead(today, lead_weeks))))
    for n in notes:
        print("  note: %s" % n)
    print("")
    print("%-40s %7s %12s %6s %10s  %-12s %s"
          % ("keyword", "now", "ahead", "ratio", "peak", "status", "bonus"))
    for r in rows:
        print("%-40s %7s %12s %6s %10s  %-12s %+d"
              % (r["keyword"][:40],
                 "-" if r["now_volume"] is None else r["now_volume"],
                 "-" if r["ahead_volume"] is None
                 else "%d (%s)" % (r["ahead_volume"], _mon(r["ahead_month"])),
                 "-" if r["ahead_ratio"] is None else "%.2f" % r["ahead_ratio"],
                 "-" if r["peak_month"] is None
                 else "%.1fx (%s)" % (r["peak_ratio"], _mon(r["peak_month"])),
                 r["status"], r["bonus"]))
    print("")
    print(summary_line(rows))


# ---------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Seasonality lookahead over saved historical keyword data. "
                    "Always exits 0.")
    ap.add_argument("--data", required=True, help="saved DFS historical keyword "
                    "response, or a {keyword: [monthly...]} map")
    ap.add_argument("--today", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--lead-weeks", type=int, default=8,
                    help="how far ahead to look (default 8)")
    ap.add_argument("--min-ratio", type=float, default=1.3,
                    help="ahead/now ratio for rising; 1/ratio for falling")
    ap.add_argument("--min-volume", type=int, default=50,
                    help="ahead volume below this is never rising")
    ap.add_argument("--json", action="store_true", help="print JSON to stdout")
    ap.add_argument("--out", help="also write the JSON here")
    args = ap.parse_args()

    notes = []
    today = (datetime.date.fromisoformat(args.today) if args.today
             else datetime.date.today())
    keywords = load_keywords(args.data, notes)
    rows = [analyse(kw, pts, today, args.lead_weeks, args.min_ratio,
                    args.min_volume) for kw, pts in keywords.items()]
    rows.sort(key=lambda r: (STATUS_ORDER.index(r["status"]) != 0,
                             -(r["ahead_ratio"] or -1), r["keyword"]))

    doc = {"generated": datetime.datetime.now(datetime.timezone.utc)
                        .replace(microsecond=0).isoformat(),
           "today": today.isoformat(), "lead_weeks": args.lead_weeks,
           "summary": summary_line(rows), "notes": notes, "keywords": rows}
    if args.out:
        with open(args.out, "w") as fh:
            json.dump(doc, fh, indent=2)
    if args.json:
        print(json.dumps(doc, indent=2))
        print(summary_line(rows), file=sys.stderr)
    else:
        print_report(rows, today, args.lead_weeks, notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
