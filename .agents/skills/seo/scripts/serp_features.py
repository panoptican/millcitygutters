#!/usr/bin/env python3
"""SERP-feature and AI Overview theft on the queries that earn our clicks.

Rankings can hold while clicks fall. The usual cause is something that appeared
above us: an AI Overview, a featured snippet, a video carousel. Search Console
cannot see any of that; it shows a stable position and fewer clicks. So this
script keeps a dated record of which features sit on our top queries and joins
it back to the click data. The theft signature is: position stable, clicks
down, a feature that was not there last time. It also flags queries where an
AI Overview is present and does not cite us: Google answers the question, we
rank for it, and we are not a source.

It is a report, not a gate. It always exits 0.

Usage
  1. Pick queries (the model then fetches each SERP via DataForSEO):
     serp_features.py --top-queries 20 --gsc-queries .seo/gsc/queries-<date>.json \
         --domain https://example.com
  2. Normalise raw DataForSEO responses into today's serp file (upserts):
     serp_features.py --ingest raw1.json [--ingest raw2.json] \
         --domain https://example.com --out .seo/serp/<today>.json
  3. Diff the two newest serp files against both GSC query pulls (default):
     serp_features.py --diff --serp-dir .seo/serp \
         --gsc-queries <cur.json> --gsc-prev <prev.json> [--json]

Inputs
  GSC query rows: {"rows":[{"keys":[query, page], clicks, impressions, position}]}
    (plain query/page fields accepted). Aggregated per query, best page kept.
  --ingest: a serp_organic_live_advanced response, a list of them, or an
    already-normalised record. tasks[].result[] carries keyword + items[].

Standard library only.
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse

DATE_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")
THEFT_FEATURES = ["ai_overview", "featured_snippet", "video", "people_also_ask",
                  "shopping", "top_stories", "local_pack"]
CLICK_DROP_PCT = 20.0
POSITION_STABLE = 1.5


def host_of(value):
    """Bare hostname, www stripped, from a URL or a bare domain."""
    v = (value or "").strip().lower()
    if not v:
        return ""
    if "://" not in v:
        v = "https://" + v
    try:
        host = urllib.parse.urlsplit(v).netloc.split("@")[-1].split(":")[0]
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def is_ours(value, domain):
    h = host_of(value)
    return bool(h) and (h == domain or h.endswith("." + domain))


# ------------------------------------------------------------------- loading

def load_json(path, label, notes):
    if not path or not os.path.isfile(path):
        notes.append("%s file not found: %s" % (label, path))
        return None
    try:
        with open(path) as fh:
            node = json.load(fh)
    except (OSError, ValueError) as ex:
        notes.append("could not parse %s (%s): %s" % (label, path, ex))
        return None
    if isinstance(node, dict):  # {"result": "<json string>"} envelopes
        for key in ("result", "content", "data", "text"):
            v = node.get(key)
            if isinstance(v, str) and v.lstrip()[:1] in "[{":
                try:
                    return json.loads(v)
                except ValueError:
                    continue
    return node


def _row_query_page(row):
    query = row.get("query") or row.get("keyword")
    page = row.get("page") or row.get("url")
    keys = row.get("keys")
    if isinstance(keys, list):
        query = query or (keys[0] if keys else None)
        page = page or (keys[1] if len(keys) > 1 else None)
    return (str(query).strip().lower() if query else None,
            str(page) if page else None)


def find_rows(node, depth=0):
    """The first list of dicts that look like query rows, anywhere in the doc."""
    if depth > 6:
        return None
    if isinstance(node, list) and node and all(
            isinstance(r, dict) and _row_query_page(r)[0]
            and ("clicks" in r or "impressions" in r) for r in node[:5]):
        return node
    kids = node.values() if isinstance(node, dict) else node \
        if isinstance(node, list) else []
    for v in kids:
        got = find_rows(v, depth + 1) if isinstance(v, (dict, list)) else None
        if got:
            return got
    return None


def load_gsc_queries(path, label, notes):
    """{query: {query, clicks, impressions, position, page}} aggregated per query."""
    doc = load_json(path, label, notes)
    rows = find_rows(doc) if doc is not None else None
    if doc is not None and not rows:
        notes.append("%s: no query rows found in %s" % (label, path))
    out, weight, best = {}, {}, {}
    for row in rows or []:
        query, page = _row_query_page(row)
        if not query:
            continue
        clicks, imps = int(row.get("clicks") or 0), int(row.get("impressions") or 0)
        rec = out.setdefault(query, {"query": query, "clicks": 0, "impressions": 0,
                                     "position": None, "page": None})
        rec["clicks"] += clicks
        rec["impressions"] += imps
        try:  # impression-weighted average position across the query's pages
            pos, w = float(row["position"]), max(imps, 1)
            prior = (rec["position"] or 0) * weight.get(query, 0)
            weight[query] = weight.get(query, 0) + w
            rec["position"] = round((prior + pos * w) / weight[query], 1)
        except (KeyError, TypeError, ValueError):
            pass
        if page and clicks > best.get(query, -1):
            rec["page"], best[query] = page, clicks
    return out


# --------------------------------------------------------------------- ingest

def walk_hosts(node, depth=0):
    """Every url/domain hostname nested anywhere under an item."""
    if depth > 8:
        return
    if isinstance(node, dict):
        for k in ("url", "domain"):
            if isinstance(node.get(k), str) and host_of(node[k]):
                yield host_of(node[k])
        node = list(node.values())
    if isinstance(node, list):
        for v in node:
            if isinstance(v, (dict, list)):
                for h in walk_hosts(v, depth + 1):
                    yield h


def normalise_result(result, domain):
    """One DFS result ({keyword, items}) -> one query record."""
    keyword = result.get("keyword") or result.get("query")
    items = result.get("items")
    if not keyword or not isinstance(items, list):
        return None
    rec = {"query": str(keyword).strip().lower(), "features": [],
           "our_position": None, "our_url": None, "aio_present": False,
           "aio_cites_us": False, "aio_cited_domains": []}
    for item in items:
        if not isinstance(item, dict):
            continue
        kind = item.get("type")
        if kind == "organic":
            if rec["our_position"] is None and is_ours(
                    item.get("url") or item.get("domain"), domain):
                rec["our_position"] = item.get("rank_absolute") or item.get("rank_group")
                rec["our_url"] = item.get("url")
            continue
        if kind and kind not in rec["features"]:
            rec["features"].append(kind)
        if kind == "ai_overview":
            rec["aio_present"] = True
            for h in walk_hosts(item):
                if h not in rec["aio_cited_domains"]:
                    rec["aio_cited_domains"].append(h)
                rec["aio_cites_us"] = rec["aio_cites_us"] or is_ours(h, domain)
    return rec


def extract_records(node, domain, depth=0):
    """Query records from a raw DFS response, a list of them, or a record."""
    if depth > 6:
        return []
    if isinstance(node, list):
        return [r for v in node for r in extract_records(v, domain, depth + 1)]
    if not isinstance(node, dict):
        return []
    if "features" in node and "query" in node:  # already normalised
        for k, v in (("aio_present", "ai_overview" in node["features"]),
                     ("aio_cites_us", False), ("aio_cited_domains", []),
                     ("our_position", None), ("our_url", None)):
            node.setdefault(k, v)
        return [node]
    if "items" in node and ("keyword" in node or "query" in node):
        rec = normalise_result(node, domain)
        return [rec] if rec else []
    return [r for key in ("tasks", "result", "results", "data", "queries")
            if key in node for r in extract_records(node[key], domain, depth + 1)]


def ingest(paths, domain, out_path, today, notes):
    doc = {"date": today.isoformat(), "domain": domain, "queries": []}
    if os.path.isfile(out_path):
        prev = load_json(out_path, "existing out file", notes)
        if isinstance(prev, dict) and isinstance(prev.get("queries"), list):
            doc["queries"] = prev["queries"]
    merged = {q.get("query"): q for q in doc["queries"] if isinstance(q, dict)}
    added = 0
    for path in paths:
        recs = extract_records(load_json(path, "ingest", notes), domain)
        if not recs:
            notes.append("no SERP results recognised in %s" % path)
        for rec in recs:
            merged[rec["query"]] = rec
            added += 1
    doc["queries"] = sorted(merged.values(), key=lambda q: q["query"])
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
    return doc, added


# ----------------------------------------------------------------------- diff

def load_serp_dir(serp_dir, notes):
    """[(date, doc)] oldest first."""
    out = []
    if not os.path.isdir(serp_dir):
        notes.append("serp dir not found: %s" % serp_dir)
        return out
    for name in sorted(os.listdir(serp_dir)):
        if DATE_FILE_RE.match(name):
            doc = load_json(os.path.join(serp_dir, name), "serp file", notes)
            if isinstance(doc, dict) and isinstance(doc.get("queries"), list):
                out.append((name[:10], doc))
    return out


def by_query(doc):
    return {q["query"]: q for q in (doc or {}).get("queries", [])
            if isinstance(q, dict) and q.get("query")}


def diff(cur_doc, prev_doc, gsc, gsc_prev, notes):
    cur, prev = by_query(cur_doc), by_query(prev_doc)
    if prev_doc is None:
        notes.append("only one serp file: theft needs a previous one, "
                     "aio checks still run")
    candidates, counts = [], {f: 0 for f in THEFT_FEATURES}
    counts["aio_cites_us"] = 0
    for query, rec in sorted(cur.items()):
        feats = rec.get("features") or []
        for f in feats:
            if f in counts:
                counts[f] += 1
        counts["aio_cites_us"] += bool(rec.get("aio_present") and rec.get("aio_cites_us"))
        g, gp = gsc.get(query) or {}, gsc_prev.get(query) or {}
        cur_clicks, prev_clicks = int(g.get("clicks") or 0), int(gp.get("clicks") or 0)
        trend = (round((cur_clicks - prev_clicks) * 100.0 / prev_clicks, 1)
                 if prev_clicks else None)
        base = {"query": query, "page": g.get("page") or rec.get("our_url"),
                "our_position": rec.get("our_position"),
                "gsc_position": g.get("position"), "gsc_position_prev": gp.get("position"),
                "clicks": cur_clicks, "clicks_prev": prev_clicks if gsc_prev else None,
                "click_trend": trend, "features": feats}

        if query in prev:
            old = prev[query].get("features") or []
            new_feats = [f for f in THEFT_FEATURES if f in feats and f not in old]
            pa, pb = g.get("position"), gp.get("position")
            stable = pa is not None and pb is not None and abs(pa - pb) <= POSITION_STABLE
            if new_feats and stable and trend is not None and trend <= -CLICK_DROP_PCT:
                candidates.append(dict(
                    base, kind="theft", action="aeo-fix", new_features=new_feats,
                    clicks_at_risk=prev_clicks - cur_clicks,
                    reason="%s appeared; clicks %d -> %d (%+.0f%%) at stable "
                           "position %.1f -> %.1f" % (", ".join(new_feats), prev_clicks,
                                                      cur_clicks, trend, pb, pa)))
        if rec.get("aio_present"):
            cited = rec.get("aio_cited_domains") or []
            if rec.get("aio_cites_us"):
                candidates.append(dict(
                    base, kind="aio-cited", action="defend", clicks_at_risk=0,
                    cited_domains=cited,
                    reason="AI Overview cites us; keep the answer current"))
            else:
                candidates.append(dict(
                    base, kind="aio-uncited", action="aeo-fix",
                    clicks_at_risk=cur_clicks, cited_domains=cited,
                    reason="AI Overview present, cites %s, not us"
                           % (", ".join(cited[:4]) or "nobody")))
    candidates.sort(key=lambda c: (-c["clicks_at_risk"], c["kind"], c["query"]))
    return candidates, counts


# --------------------------------------------------------------------- output

def feature_line(counts, total):
    parts = ["%s=%d" % (f, counts[f]) for f in THEFT_FEATURES if counts.get(f)]
    return ("FEATURES: %d tracked queries; %s; aio cites us on %d"
            % (total, ", ".join(parts) or "no features", counts.get("aio_cites_us", 0)))


def print_diff(candidates, counts, cur_date, prev_date, total, notes):
    print("SERP features — %s vs %s" % (cur_date or "(no serp file)",
                                       prev_date or "(no previous)"))
    for n in notes:
        print("  note: %s" % n)
    print("")
    if not candidates:
        print("  no theft or AI Overview candidates on the tracked queries")
    else:
        print("  %-11s %6s  %-40s %-11s %s" % ("kind", "risk", "query", "action", "reason"))
        for c in candidates:
            q = c["query"] if len(c["query"]) <= 40 else c["query"][:39] + "…"
            print("  %-11s %6d  %-40s %-11s %s"
                  % (c["kind"], c["clicks_at_risk"], q, c["action"], c["reason"]))
    kinds = {}
    for c in candidates:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    print("")
    print("SUMMARY: %d theft, %d aio-uncited, %d aio-cited; clicks_at_risk=%d"
          % (kinds.get("theft", 0), kinds.get("aio-uncited", 0),
             kinds.get("aio-cited", 0), sum(c["clicks_at_risk"] for c in candidates)))
    print(feature_line(counts, total))


# ------------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(
        description="SERP-feature and AI Overview theft on our top queries. "
                    "Always exits 0.")
    ap.add_argument("--top-queries", type=int, metavar="N",
                    help="print the top N queries by clicks from --gsc-queries")
    ap.add_argument("--ingest", action="append", metavar="RAW.json",
                    help="raw DataForSEO SERP response(s) to normalise; repeatable")
    ap.add_argument("--diff", action="store_true",
                    help="compare the two newest serp files (default mode)")
    ap.add_argument("--domain", help="our site, e.g. https://example.com")
    ap.add_argument("--gsc-queries", help="Search Console query rows, current window")
    ap.add_argument("--gsc-prev", help="Search Console query rows, prior window")
    ap.add_argument("--serp-dir", default=".seo/serp")
    ap.add_argument("--out", help="ingest target, .seo/serp/<YYYY-MM-DD>.json")
    ap.add_argument("--json", action="store_true", help="JSON on stdout")
    args = ap.parse_args()

    notes, today = [], datetime.date.today()
    domain = host_of(args.domain) if args.domain else ""

    if args.top_queries:
        gsc = load_gsc_queries(args.gsc_queries, "gsc-queries", notes)
        rows = sorted(gsc.values(),
                      key=lambda r: (-r["clicks"], -r["impressions"], r["query"]))
        if domain:
            rows = [r for r in rows if not r["page"] or is_ours(r["page"], domain)]
        for n in notes:
            print("note: %s" % n, file=sys.stderr)
        print(json.dumps(rows[:args.top_queries], indent=2))
        return 0

    if args.ingest:
        if not domain:
            print("--ingest needs --domain", file=sys.stderr)
            return 0
        out_path = args.out or os.path.join(args.serp_dir, "%s.json" % today)
        doc, added = ingest(args.ingest, domain, out_path, today, notes)
        for n in notes:
            print("note: %s" % n, file=sys.stderr)
        if args.json:
            print(json.dumps(doc, indent=2, sort_keys=True))
        else:
            print("wrote %s: %d query record(s) from %d file(s), %d total"
                  % (out_path, added, len(args.ingest), len(doc["queries"])))
        return 0

    files = load_serp_dir(args.serp_dir, notes)
    if not files:
        notes.append("no serp files in %s — run --ingest first" % args.serp_dir)
    cur_date, cur_doc = files[-1] if files else (None, {"queries": []})
    prev_date, prev_doc = files[-2] if len(files) > 1 else (None, None)
    gsc = load_gsc_queries(args.gsc_queries, "gsc-queries", notes)
    gsc_prev = load_gsc_queries(args.gsc_prev, "gsc-prev", notes) if args.gsc_prev else {}
    if not gsc:
        notes.append("no GSC query rows: theft and clicks_at_risk read as 0")
    candidates, counts = diff(cur_doc, prev_doc, gsc, gsc_prev, notes)
    total = len(cur_doc.get("queries") or [])
    if args.json:
        print(json.dumps({"serp_date": cur_date, "serp_prev_date": prev_date,
                          "tracked_queries": total, "feature_counts": counts,
                          "notes": notes, "candidates": candidates},
                         indent=2, sort_keys=True))
        print(feature_line(counts, total), file=sys.stderr)
    else:
        print_diff(candidates, counts, cur_date, prev_date, total, notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
