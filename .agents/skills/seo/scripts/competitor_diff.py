#!/usr/bin/env python3
"""Weekly competitor delta: what a competitor shipped and what it started ranking for.

Reads the dated artifacts a competitor directory accumulates and turns the
newest two of each into candidates. The fingerprints come from
health_diff.py run against the competitor's sitemap; the ranked files are the
raw DataForSEO Labs ranked_keywords response saved once a month.

  .seo/competitors/<host>/YYYY-MM-DD.json          health_diff.py fingerprint
  .seo/competitors/<host>/ranked-YYYY-MM-DD.json   dataforseo_labs_google_ranked_keywords

It is a report, not a gate. It always exits 0. One file of a kind means
"baseline saved", never an error.

Usage
  competitor_diff.py --dir .seo/competitors/example.com
  competitor_diff.py --dir .seo/competitors/example.com \
      --gsc-queries .seo/gsc/queries-2026-09-09.json
  competitor_diff.py --dir .seo/competitors/example.com --json

--gsc-queries is our own Search Console pull with dimensions query,page:
{"rows":[{"keys":["<query>","<page>"], clicks, impressions, ctr, position}]}.
Rows carrying query/page fields instead of keys are accepted too. It is joined
onto every competitor gain so the candidate is `refresh` (we already have a
page for that query) or `create` (we have nothing).

Standard library only.
"""

import argparse
import datetime
import json
import os
import re
import sys

FP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")
RANKED_RE = re.compile(r"^ranked-\d{4}-\d{2}-\d{2}\.json$")
TOP = 20
GAIN_STEP = 5
EXPANDED_RATIO = 1.30
MAX_GAINS = 50


# ------------------------------------------------------------------- loading

def newest_two(dir_path, pattern):
    """(newest, previous) paths, either may be None."""
    if not os.path.isdir(dir_path):
        return None, None
    names = sorted(n for n in os.listdir(dir_path) if pattern.match(n))
    paths = [os.path.join(dir_path, n) for n in names]
    if not paths:
        return None, None
    if len(paths) == 1:
        return paths[0], None
    return paths[-1], paths[-2]


def load_json(path, notes):
    if not path:
        return None
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception as ex:  # noqa: BLE001
        notes.append("could not read %s (%s)" % (path, ex))
        return None


def _num(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _get(node, *path):
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def ranked_items(doc):
    """Find the item list in a DFS response, a bare result, or a flat list."""
    if isinstance(doc, list):
        if doc and isinstance(doc[0], dict) and "items" in doc[0]:
            return doc[0].get("items") or []
        return doc
    if not isinstance(doc, dict):
        return []
    if isinstance(doc.get("items"), list):
        return doc["items"]
    for task in doc.get("tasks") or []:
        for res in (task or {}).get("result") or []:
            if isinstance(res, dict) and isinstance(res.get("items"), list):
                return res["items"]
    return []


def load_ranked(path, notes):
    """{keyword: {volume, rank, url}} from a saved ranked_keywords response."""
    doc = load_json(path, notes)
    if doc is None:
        return {}
    out = {}
    for it in ranked_items(doc):
        if not isinstance(it, dict):
            continue
        kw = _get(it, "keyword_data", "keyword") or it.get("keyword")
        if not kw:
            continue
        vol = (_get(it, "keyword_data", "keyword_info", "search_volume")
               if "keyword_data" in it else it.get("search_volume"))
        serp = _get(it, "ranked_serp_element", "serp_item") or it
        rank = _num(serp.get("rank_absolute"))
        if rank is None:
            rank = _num(serp.get("rank_group"))
        kw = str(kw).strip().lower()
        rec = {"volume": int(_num(vol) or 0),
               "rank": int(rank) if rank is not None else None,
               "url": serp.get("url")}
        # A keyword can appear once per ranking URL. Keep the best rank.
        old = out.get(kw)
        if old is None or (rec["rank"] is not None
                           and (old["rank"] is None or rec["rank"] < old["rank"])):
            out[kw] = rec
    if not out:
        notes.append("no ranked keywords found in %s" % path)
    return out


def load_queries(path, notes):
    """{query: {position, page, clicks, impressions}}, best position per query."""
    if not path:
        return {}
    doc = load_json(path, notes)
    if doc is None:
        return {}
    rows = doc.get("rows") if isinstance(doc, dict) else doc
    out = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        keys = row.get("keys") if isinstance(row.get("keys"), list) else []
        query = row.get("query") or (keys[0] if keys else None)
        page = row.get("page") or (keys[1] if len(keys) > 1 else None)
        if not query:
            continue
        query = str(query).strip().lower()
        pos = _num(row.get("position"))
        rec = {"position": pos, "page": page,
               "clicks": int(_num(row.get("clicks")) or 0),
               "impressions": int(_num(row.get("impressions")) or 0)}
        old = out.get(query)
        if old is None or (pos is not None
                           and (old["position"] is None or pos < old["position"])):
            out[query] = rec
    if not out:
        notes.append("no query rows found in %s" % path)
    return out


# ---------------------------------------------------------------------- diffs

def page_diff(prev_pages, cur_pages):
    d = {"new": [], "removed": [], "retitled": [], "schema_added": [],
         "expanded": []}
    for url in sorted(set(cur_pages) - set(prev_pages)):
        rec = cur_pages[url]
        d["new"].append({"url": url, "title": rec.get("title"),
                         "words": rec.get("body_words") or 0})
    d["removed"] = sorted(set(prev_pages) - set(cur_pages))
    for url in sorted(set(cur_pages) & set(prev_pages)):
        a, b = prev_pages[url], cur_pages[url]
        if a.get("title") != b.get("title"):
            d["retitled"].append({"url": url, "old": a.get("title"),
                                  "new": b.get("title")})
        added = [t for t in (b.get("jsonld_types") or [])
                 if t not in (a.get("jsonld_types") or [])]
        if added:
            d["schema_added"].append({"url": url, "types": added})
        wa, wb = a.get("body_words") or 0, b.get("body_words") or 0
        if wa and wb >= wa * EXPANDED_RATIO:
            d["expanded"].append({"url": url, "old_words": wa, "words": wb,
                                  "lastmod": b.get("sitemap_lastmod")})
    return d


def in_top(rank):
    return rank is not None and rank <= TOP


def keyword_diff(prev, cur, ours):
    gains, losses = [], []
    for kw, rec in cur.items():
        rank, prev_rank = rec["rank"], (prev.get(kw) or {}).get("rank")
        if not in_top(rank):
            continue
        newly = not in_top(prev_rank)
        improved = prev_rank is not None and prev_rank - rank >= GAIN_STEP
        if not (newly or improved):
            continue
        mine = ours.get(kw)
        row = {"keyword": kw, "volume": rec["volume"], "rank": rank,
               "prev_rank": prev_rank, "url": rec["url"],
               "our_position": mine["position"] if mine else None,
               "our_page": mine["page"] if mine else None,
               "candidate": "refresh" if mine else "create"}
        if not mine:
            row["demand"] = "competitor gain"
            row["note"] = ("no GSC row for this query; a create still needs a "
                           "thread for provenance before it is scored")
        gains.append(row)
    for kw, rec in prev.items():
        if not in_top(rec["rank"]):
            continue
        now = cur.get(kw)
        if now is None or not in_top(now["rank"]):
            losses.append({"keyword": kw, "volume": rec["volume"],
                           "prev_rank": rec["rank"],
                           "rank": now["rank"] if now else None,
                           "url": rec["url"]})
    gains.sort(key=lambda r: (-r["volume"], r["rank"], r["keyword"]))
    losses.sort(key=lambda r: (-r["volume"], r["keyword"]))
    return gains[:MAX_GAINS], losses


# --------------------------------------------------------------------- output

def print_report(out, fp_paths, ranked_paths):
    p, k = out["pages"], out["keywords"]
    print("Competitor diff — %s" % out["host"])
    print("  fingerprints: %s vs %s" % (fp_paths[0] or "(none)",
                                        fp_paths[1] or "(none)"))
    print("  ranked:       %s vs %s" % (ranked_paths[0] or "(none)",
                                        ranked_paths[1] or "(none)"))
    for n in out["notes"]:
        print("  note: %s" % n)
    print("")
    print("PAGES: %d new, %d removed, %d retitled, %d schema added, %d expanded"
          % (len(p["new"]), len(p["removed"]), len(p["retitled"]),
             len(p["schema_added"]), len(p["expanded"])))
    for r in p["new"][:20]:
        print("  + %s  (%d words) %s" % (r["url"], r["words"], r["title"] or ""))
    if len(p["new"]) > 20:
        print("  …and %d more" % (len(p["new"]) - 20))
    print("")
    print("KEYWORDS: %d gains, %d losses" % (len(k["gains"]), len(k["losses"])))
    for r in k["gains"][:10]:
        ours = ("we rank %.1f" % r["our_position"]
                if r["our_position"] is not None else "we have nothing")
        print("  %-40s vol %6d  #%d (was %s)  %s -> %s"
              % (r["keyword"][:40], r["volume"], r["rank"],
                 r["prev_rank"] if r["prev_rank"] is not None else "-",
                 ours, r["candidate"]))
    print("")
    print(summary_line(out))


def summary_line(out):
    p, k = out["pages"], out["keywords"]
    return ("SUMMARY: %d new pages, %d gains, %d losses, %d create, %d refresh"
            % (len(p["new"]), len(k["gains"]), len(k["losses"]),
               sum(1 for r in k["gains"] if r["candidate"] == "create"),
               sum(1 for r in k["gains"] if r["candidate"] == "refresh")))


# ----------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Weekly competitor delta from saved fingerprints and "
                    "ranked-keyword pulls. Always exits 0.")
    ap.add_argument("--dir", required=True, help=".seo/competitors/<host>")
    ap.add_argument("--gsc-queries", help="our Search Console query,page rows")
    ap.add_argument("--out", help="diff JSON path (default <dir>/diff-<today>.json)")
    ap.add_argument("--today", help="YYYY-MM-DD override")
    ap.add_argument("--json", action="store_true", help="print the diff as JSON")
    args = ap.parse_args()

    notes = []
    today = args.today or datetime.date.today().isoformat()
    host = os.path.basename(os.path.normpath(args.dir))

    fp_cur, fp_prev = newest_two(args.dir, FP_RE)
    cur_doc = load_json(fp_cur, notes) or {}
    prev_doc = load_json(fp_prev, notes) or {}
    if cur_doc.get("base_url"):
        host = re.sub(r"^https?://", "", cur_doc["base_url"]).rstrip("/")
    if fp_cur and fp_prev:
        pages = page_diff(prev_doc.get("pages") or {}, cur_doc.get("pages") or {})
    else:
        pages = page_diff({}, {})
        notes.append("pages: %s" % ("baseline saved, diff next week" if fp_cur
                                    else "no fingerprint yet; run health_diff.py "
                                         "--sitemap <competitor sitemap> --out %s"
                                         % args.dir))

    rk_cur, rk_prev = newest_two(args.dir, RANKED_RE)
    ours = load_queries(args.gsc_queries, notes)
    if rk_cur and rk_prev:
        gains, losses = keyword_diff(load_ranked(rk_prev, notes),
                                     load_ranked(rk_cur, notes), ours)
    else:
        gains, losses = [], []
        notes.append("keywords: %s" % ("baseline saved, diff next month" if rk_cur
                                       else "no ranked file yet; save the "
                                            "ranked_keywords response as %s/"
                                            "ranked-%s.json" % (args.dir, today)))
    if gains and not ours:
        notes.append("no --gsc-queries given, so every gain is a create candidate")

    out = {
        "generated": datetime.datetime.now(datetime.timezone.utc)
                     .replace(microsecond=0).isoformat(),
        "host": host,
        "pages": pages,
        "keywords": {"gains": gains, "losses": losses},
        "notes": notes,
    }
    out_path = args.out or os.path.join(args.dir, "diff-%s.json" % today)
    try:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w") as fh:
            json.dump(out, fh, indent=2, sort_keys=True)
    except OSError as ex:
        notes.append("could not write %s (%s)" % (out_path, ex))

    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
        print(summary_line(out), file=sys.stderr)
    else:
        print_report(out, (fp_cur, fp_prev), (rk_cur, rk_prev))
        print("  written: %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
