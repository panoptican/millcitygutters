#!/usr/bin/env python3
"""Internal link opportunity mining from Search Console queries.

Page A ranks for query Q. Page B's body text already says Q and does not link
to A. Adding that link is the cheapest repair-class action there is, and it
moves striking-distance pages (position 3-25) more than anything else that
costs ten minutes. link_audit.py checks minimums and orphans; this finds the
specific sentence on the specific page where the link belongs.

It is a report, not a gate. It always exits 0.

Usage
  link_opportunities.py --gsc-queries .seo/gsc/queries-2026-09-09.json \
      --sitemap https://example.com/sitemap.xml --domain https://example.com
  link_opportunities.py --gsc-queries q.json --health .seo/health/2026-09-09.json \
      --local-root web/out --stop '/legal/*' --json --out .seo/links.json

--gsc-queries is a Search Console pull with dimensions "query,page":
  {"rows":[{"keys":["<query>","<page>"], clicks, impressions, position}]}
  ("query"/"page" fields accepted too). A query's owner is the page with the
  best position among its rows with >= 20 impressions.

Standard library only.
"""

import argparse
import concurrent.futures
import datetime
import fnmatch
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import health_diff as hd  # noqa: E402  fetch, read_local, _Page, sitemap loading

OWNER_ROW_MIN_IMPRESSIONS = 20   # a row below this cannot claim a query
MIN_POSITION = 3.0               # already top-3: a link changes little
SNIPPET_CHARS = 160


# ------------------------------------------------------------------- loading

def path_key(url):
    """Host-independent comparison key: normalised path only. GSC reports the
    canonical host and sitemaps often do not agree with it on www."""
    try:
        p = urllib.parse.urlsplit(hd.normalise(url)).path or "/"
    except ValueError:
        return url
    return p


def load_queries(path, notes):
    """{query: [(page, clicks, impressions, position)]}"""
    try:
        with open(path) as fh:
            doc = json.load(fh)
    except Exception as ex:  # noqa: BLE001
        notes.append("could not read %s (%s)" % (path, ex))
        return {}
    rows = doc.get("rows") if isinstance(doc, dict) else doc
    out = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        keys = row.get("keys") if isinstance(row.get("keys"), list) else []
        q = row.get("query") or (keys[0] if len(keys) > 0 else None)
        page = row.get("page") or (keys[1] if len(keys) > 1 else None)
        if not q or not page:
            continue
        q = re.sub(r"\s+", " ", str(q)).strip().lower()
        try:
            pos = float(row.get("position") or 0)
        except (TypeError, ValueError):
            pos = 0.0
        out.setdefault(q, []).append((str(page), int(row.get("clicks") or 0),
                                      int(row.get("impressions") or 0), pos))
    return out


def pick_owners(queries, min_impressions, max_position, min_words):
    """One owner per query, filtered to striking distance."""
    owners = []
    for q, rows in queries.items():
        if len(q.split()) < min_words:
            continue
        eligible = [r for r in rows if r[2] >= OWNER_ROW_MIN_IMPRESSIONS and r[3] > 0]
        if not eligible:
            continue
        page, clicks, impr, pos = min(eligible, key=lambda r: r[3])
        if impr < min_impressions or not (MIN_POSITION <= pos <= max_position):
            continue
        owners.append({"query": q, "page": page, "path": path_key(page),
                       "position": round(pos, 1), "impressions": impr,
                       "clicks": clicks})
    owners.sort(key=lambda o: -o["impressions"])
    return owners


def load_pages(args, notes):
    urls = []
    if args.health:
        try:
            with open(args.health) as fh:
                urls = sorted((json.load(fh).get("pages") or {}).keys())
        except Exception as ex:  # noqa: BLE001
            notes.append("could not read %s (%s)" % (args.health, ex))
    elif args.sitemap:
        urls = list(dict.fromkeys(u for u, _ in hd.discover_sitemap(args.sitemap, notes)))
    else:
        notes.append("no --sitemap or --health given; nothing to scan")
    if args.limit and len(urls) > args.limit:
        notes.append("--limit %d of %d pages" % (args.limit, len(urls)))
    return urls[:args.limit] if args.limit else urls


# ------------------------------------------------------------------ scanning

class _TextPage(hd._Page):
    """health_diff's parser joins text nodes with nothing between them, so
    '</h1><p>' glues a heading onto a paragraph and the <title> lands in the
    body. A space per tag boundary keeps whole-phrase matching honest."""

    def handle_starttag(self, tag, attrs):
        hd._Page.handle_starttag(self, tag, attrs)
        self._text.append(" ")

    def handle_endtag(self, tag):
        hd._Page.handle_endtag(self, tag)
        self._text.append(" ")

    def handle_data(self, data):
        if not self._in_title:
            hd._Page.handle_data(self, data)


def scan_page(url, local_root, domain_host):
    """Visible body text plus the set of internal link paths."""
    got = hd.read_local(url, local_root) if local_root else None
    if got is None:
        got = hd.fetch(url)
    p = _TextPage()
    try:
        p.feed(got.get("body") or "")
        p.close()
    except Exception:  # noqa: BLE001
        pass
    links = set()
    for href in p.links:
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absu = urllib.parse.urljoin(got.get("final_url") or url, href)
        if absu.startswith(("http://", "https://")) and hd.host_of(absu) == domain_host:
            links.add(path_key(absu))
    return {"status": got.get("status"), "text": p.text(), "links": links,
            "error": got.get("error")}


def phrase_re(phrase):
    words = [re.escape(w) for w in phrase.split()]
    return re.compile(r"(?<!\w)" + r"\s+".join(words) + r"(?!\w)", re.I)


def snippet(text, m):
    half = SNIPPET_CHARS // 2
    start = max(0, m.start() - half)
    end = min(len(text), m.end() + half)
    s = text[start:end].strip()
    return ("\u2026" if start > 0 else "") + s + ("\u2026" if end < len(text) else "")


def stopped(url, stops):
    path = path_key(url)
    return any(fnmatch.fnmatch(path, s) or path == path_key(s) for s in stops)


def mine(owners, pages, stops):
    """[(from, to, owner, occurrences, snippet)], one per from->to pair."""
    inbound = {}
    for o in owners:
        inbound[o["path"]] = sum(
            1 for u, rec in pages.items()
            if o["path"] in rec["links"] and path_key(u) != o["path"])

    best = {}  # (from_path, to_path) -> opportunity
    for o in owners:
        rx = phrase_re(o["query"])
        for url, rec in pages.items():
            from_path = path_key(url)
            if (from_path == o["path"] or hd.is_home(url)
                    or o["path"] in rec["links"] or stopped(url, stops)):
                continue
            hits = list(rx.finditer(rec["text"]))
            if not hits:
                continue
            key = (from_path, o["path"])
            if key in best and best[key]["owner_impressions"] >= o["impressions"]:
                continue
            best[key] = {
                "from": url, "to": o["page"], "phrase": o["query"],
                "owner_position": o["position"], "owner_impressions": o["impressions"],
                "owner_clicks": o["clicks"], "owner_inbound": inbound[o["path"]],
                "occurrences": len(hits), "snippet": snippet(rec["text"], hits[0]),
                "score": round(o["impressions"] * (1.0 if o["position"] <= 10 else 1.5)),
            }
    opps = sorted(best.values(), key=lambda x: (-x["score"], x["from"]))

    per_owner = {}
    for o in owners:
        rec = per_owner.setdefault(o["path"], {
            "page": o["page"], "phrases": [], "position": o["position"],
            "impressions": 0, "clicks": 0, "inbound": inbound[o["path"]],
            "opportunities": 0})
        rec["phrases"].append(o["query"])
        rec["impressions"] += o["impressions"]
        rec["clicks"] += o["clicks"]
    for x in opps:
        per_owner[path_key(x["to"])]["opportunities"] += 1
    # Fewest inbound links first: a page nothing links to gains most.
    return opps, sorted(per_owner.values(), key=lambda r: (
        r["inbound"], -r["opportunities"], -r["impressions"]))


# -------------------------------------------------------------------- output

def _short(url, width):
    s = path_key(url)
    return s if len(s) <= width else s[:width - 1] + "\u2026"


def print_report(doc, top, notes):
    opps, owners = doc["opportunities"], doc["owners"]
    print("Internal link opportunities \u2014 %s" % (doc["domain"] or "(unknown)"))
    print("  pages scanned: %d   owners (striking distance): %d   "
          "opportunities: %d" % (doc["pages_scanned"], len(owners), len(opps)))
    for n in notes:
        print("  note: %s" % n)
    print("")
    needy = [o for o in owners if o["inbound"] <= 1 and o["opportunities"]]
    if needy:
        print("OWNERS WITH <=1 INBOUND LINK AND OPEN OPPORTUNITIES (%d)" % len(needy))
        for o in needy[:10]:
            print("  %-44s pos %5.1f  impr %6d  inbound %d  opps %d  %r"
                  % (_short(o["page"], 44), o["position"], o["impressions"],
                     o["inbound"], o["opportunities"], o["phrases"][0]))
        print("")
    print("OPPORTUNITIES (top %d of %d, by score)" % (min(top, len(opps)), len(opps)))
    if not opps:
        print("  none")
    for x in opps[:top]:
        print("  %-34s \u2192 %-34s %-32r pos %5.1f  impr %6d  inbound %d"
              % (_short(x["from"], 34), _short(x["to"], 34), x["phrase"][:30],
                 x["owner_position"], x["owner_impressions"], x["owner_inbound"]))
        print("      %s" % x["snippet"])
    if len(opps) > top:
        print("  \u2026and %d more (--top)" % (len(opps) - top))
    print("")
    print("SUMMARY: %d pages, %d owners, %d opportunities"
          % (doc["pages_scanned"], len(owners), len(opps)))


# ---------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Find pages whose body text says a query another page "
                    "ranks for, but does not link to it. Always exits 0.")
    add = ap.add_argument
    add("--gsc-queries", required=True, help="Search Console JSON, query,page dimensions")
    add("--sitemap", help="sitemap URL/file or site root")
    add("--health", help="health_diff.py fingerprint; its URL list is the page set")
    add("--domain", help="site root for internal-link matching (default: first page's host)")
    add("--local-root", help="read HTML from this static build dir instead of fetching")
    add("--limit", type=int, help="cap pages scanned")
    add("--concurrency", type=int, default=8)
    add("--min-impressions", type=int, default=50)
    add("--max-position", type=float, default=25.0)
    add("--min-phrase-words", type=int, default=2,
        help="skip shorter queries; 1-word queries match everything")
    add("--stop", action="append", default=[],
        help="page path or glob never to link from, e.g. '/legal/*' (repeatable)")
    add("--top", type=int, default=30)
    add("--json", action="store_true")
    add("--out", help="also write the JSON report here")
    args = ap.parse_args()

    notes = []
    stops = [s.strip() for chunk in args.stop for s in chunk.split(",") if s.strip()]

    queries = load_queries(args.gsc_queries, notes)
    owners = pick_owners(queries, args.min_impressions, args.max_position,
                         args.min_phrase_words)
    if queries and not owners:
        notes.append("%d queries loaded, none met the owner filter "
                     "(position %g-%g, >= %d impressions)"
                     % (len(queries), MIN_POSITION, args.max_position,
                        args.min_impressions))

    urls = load_pages(args, notes)
    domain = args.domain
    if not domain and urls:
        p = urllib.parse.urlsplit(urls[0])
        domain = "%s://%s" % (p.scheme, p.netloc)
    domain_host = hd.host_of(domain or "")

    pages = {}
    workers = max(1, min(args.concurrency, 16))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(scan_page, u, args.local_root, domain_host): u
                for u in urls}
        for fut in concurrent.futures.as_completed(futs):
            try:
                pages[futs[fut]] = fut.result()
            except Exception as ex:  # noqa: BLE001
                pages[futs[fut]] = {"status": 0, "text": "", "links": set(),
                                    "error": "%s: %s" % (type(ex).__name__, ex)}
    failed = sorted(u for u, r in pages.items() if r["status"] != 200)
    if failed:
        notes.append("%d page(s) not 200, scanned as empty: %s"
                     % (len(failed), ", ".join(failed[:3])))

    opps, owner_rows = mine(owners, pages, stops)
    doc = {"generated": datetime.datetime.now(datetime.timezone.utc)
                        .replace(microsecond=0).isoformat(),
           "domain": domain, "pages_scanned": len(pages), "notes": notes,
           "owners": owner_rows, "opportunities": opps}
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w") as fh:
            json.dump(doc, fh, indent=2)
    if args.json:
        print(json.dumps(doc, indent=2))
        print("SUMMARY: %d pages, %d owners, %d opportunities"
              % (len(pages), len(owner_rows), len(opps)), file=sys.stderr)
    else:
        print_report(doc, args.top, notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
