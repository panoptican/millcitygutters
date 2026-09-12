#!/usr/bin/env python3
"""Branded vs non-branded split of Search Console queries, one line per run.

Answer-engine and off-page work has no click to measure. What it moves is the
number of people who type the brand into Google afterwards, so branded
impressions over time is the only cheap outcome metric for it. This script
splits a query pull by a brand regex, compares it with the prior window, and
lists the branded queries worth reading (misspellings, "<brand> vs …",
"<brand> pricing", "<brand> alternative"). Always exits 0.

Usage
  brand_split.py --gsc-queries .seo/gsc/queries-cur.json --prev .seo/gsc/queries-prev.json
  brand_split.py --gsc-queries cur.json --config .seo/config.json --out .seo/gsc/brand-<today>.json
  brand_split.py --gsc-queries cur.json --brand Acme --brand "acme app" --json

Inputs
  --gsc-queries / --prev   {"rows":[{"keys":["<query>", "<page>"], clicks,
                           impressions, ctr, position}]}; a "query" field works
                           too. Rows are summed per query across pages.
  brand regex, first hit wins: --brand-regex; config site.brand_regex; built
  from --brand names or config site.name + site.aliases (case-insensitive,
  spaces/hyphens optional inside multiword names, so "Acme App" matches
  "acmeapp"). <today> in --out is replaced with the run date.

Standard library only.
"""

import argparse
import datetime
import json
import os
import re
import sys

TAG_RE = re.compile(r"\b(vs|alternatives?|pricing|reviews?|reddit|login)\b", re.I)
TAG_NAMES = {"alternatives": "alternative", "reviews": "review"}


def load_rows(path):
    """{query: {clicks, impressions, position}} summed across pages."""
    if not path:
        return {}
    if not os.path.isfile(path):
        print("note: file not found: %s" % path, file=sys.stderr)
        return {}
    with open(path) as fh:
        payload = json.load(fh)
    rows = payload.get("rows", []) if isinstance(payload, dict) else payload
    out = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        keys = row.get("keys")
        query = row.get("query") or (keys[0] if isinstance(keys, list) and keys else None)
        if not query:
            continue
        rec = out.setdefault(str(query).strip().lower(),
                             {"clicks": 0, "impressions": 0, "_pos_sum": 0.0})
        impr = int(row.get("impressions") or 0)
        rec["clicks"] += int(row.get("clicks") or 0)
        rec["impressions"] += impr
        rec["_pos_sum"] += float(row.get("position") or 0) * impr
    for rec in out.values():
        s = rec.pop("_pos_sum")
        rec["position"] = round(s / rec["impressions"], 1) if rec["impressions"] else None
    return out


def build_regex(names):
    """One alternative per name; words may run together or split on space/hyphen."""
    alts = []
    for name in names:
        words = [re.escape(w) for w in re.split(r"[\s-]+", name.strip()) if w]
        if words and r"[\s-]*".join(words) not in alts:
            alts.append(r"[\s-]*".join(words))
    return "(%s)" % "|".join(alts) if alts else None


def resolve_regex(args):
    if args.brand_regex:
        return args.brand_regex
    site = {}
    if args.config and os.path.isfile(args.config):
        with open(args.config) as fh:
            site = (json.load(fh) or {}).get("site") or {}
    if site.get("brand_regex"):
        return site["brand_regex"]
    names = list(args.brand or [])
    names += [n for n in [site.get("name")] + list(site.get("aliases") or [])
              if isinstance(n, str) and n.strip()]
    return build_regex(names)


def split(rows, brand_re):
    brand = {"clicks": 0, "impressions": 0}
    non = {"clicks": 0, "impressions": 0}
    for q, rec in rows.items():
        bucket = brand if brand_re.search(q) else non
        bucket["clicks"] += rec["clicks"]
        bucket["impressions"] += rec["impressions"]
    return brand, non


def pct(cur, prev):
    return "n/a" if not prev else "%+d%%" % round((cur - prev) * 100.0 / prev)


def tag_for(query):
    m = TAG_RE.search(query)
    return TAG_NAMES.get(m.group(1).lower(), m.group(1).lower()) if m else None


def main():
    ap = argparse.ArgumentParser(description="Branded vs non-branded Search "
                                 "Console query split. Always exits 0.")
    ap.add_argument("--gsc-queries", required=True, help="current window query rows")
    ap.add_argument("--prev", help="prior window query rows")
    ap.add_argument("--brand-regex", help="explicit regex (wins over config)")
    ap.add_argument("--config", default=".seo/config.json",
                    help="reads site.brand_regex, site.name, site.aliases")
    ap.add_argument("--brand", action="append", help="brand name/alias (repeatable)")
    ap.add_argument("--out", help="write the JSON result here (<today> is replaced)")
    ap.add_argument("--today", help="run date YYYY-MM-DD (default: today)")
    ap.add_argument("--json", action="store_true", help="print JSON on stdout")
    args = ap.parse_args()

    today = args.today or datetime.date.today().isoformat()
    pattern = resolve_regex(args)
    if not pattern:
        print("no brand regex: pass --brand-regex, --brand, or a config with site.name")
        return 0
    brand_re = re.compile(pattern, re.I)
    cur, prev = load_rows(args.gsc_queries), load_rows(args.prev)
    b, n = split(cur, brand_re)
    pb, pn = split(prev, brand_re)
    b.update(prev_clicks=pb["clicks"], prev_impressions=pb["impressions"])
    n.update(prev_clicks=pn["clicks"], prev_impressions=pn["impressions"])
    total_clicks = b["clicks"] + n["clicks"]
    share = round(b["clicks"] / float(total_clicks), 3) if total_clicks else None

    top = sorted(((q, r) for q, r in cur.items() if brand_re.search(q)),
                 key=lambda kv: (-kv[1]["impressions"], kv[0]))[:10]
    top_branded = [{"query": q, "impressions": r["impressions"],
                    "prev_impressions": prev[q]["impressions"] if q in prev else None,
                    "clicks": r["clicks"], "position": r["position"],
                    "tag": tag_for(q)} for q, r in top]
    doc = {"generated": today, "regex": pattern, "brand": b, "nonbrand": n,
           "brand_share_clicks": share, "top_branded": top_branded}

    if args.out:
        out = args.out.replace("<today>", today)
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w") as fh:
            json.dump(doc, fh, indent=2)
    if args.json:
        print(json.dumps(doc, indent=2))
        return 0

    print("Brand: {:,} impr / {:,} clicks (prev {:,} / {:,}, {} / {}) · non-brand "
          "{:,} / {:,} (prev {:,} / {:,}) · brand share of clicks {}".format(
              b["impressions"], b["clicks"], pb["impressions"], pb["clicks"],
              pct(b["impressions"], pb["impressions"]), pct(b["clicks"], pb["clicks"]),
              n["impressions"], n["clicks"], pn["impressions"], pn["clicks"],
              "n/a" if share is None else "%d%%" % round(share * 100)))
    for t in top_branded:
        prev_s = "new" if t["prev_impressions"] is None else "prev {:,}".format(t["prev_impressions"])
        print("  %-40s %6s impr  %-10s %s" % (t["query"][:40], "{:,}".format(t["impressions"]),
                                             prev_s, t["tag"] or ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
