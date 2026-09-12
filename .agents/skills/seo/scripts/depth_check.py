#!/usr/bin/env python3
"""Click depth from the homepage, and orphan pages against the sitemap.

  python3 depth_check.py --url https://example.com
  python3 depth_check.py --url https://example.com --max-depth 4 --max-pages 300 --out depth.json

Breadth-first crawl of internal links from the homepage, without executing
JavaScript. Reports how many links deep each page sits, and separately every
sitemap URL the crawl never reached.

A page an engine can fetch but cannot find is a real reachability failure, and it
shows up in neither robots.txt nor a per-page check. Depth is measured in links
followed, so the homepage is depth 0.

Two honest limits, both reported rather than hidden:

  - Navigation that only exists after JavaScript runs is invisible here, exactly
    as it is to a retrieval agent that does not run scripts. An "orphan" on this
    report may be linked by a menu that never rendered. That is still worth
    knowing, so orphans are labelled "not reached", never "unlinked".
  - The crawl stops at --max-pages. Anything past the cap is unknown, not orphaned.

Standard library only.
"""

import argparse
import collections
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sitemap as sitemap_mod  # noqa: E402

UA = "Mozilla/5.0 (compatible; aeo-skill-depth-check/1.0)"
TIMEOUT = 20
SKIP_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
            ".zip", ".gz", ".mp4", ".mp3", ".css", ".js", ".xml", ".json", ".rss")
SKIP_PATH = ("/cdn-cgi/",)  # Cloudflare internals, never a content page
DEEP = 3  # depth at or beyond which a page is flagged


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []
        self.nofollow_meta = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            rel = (a.get("rel") or "").lower()
            self.hrefs.append((a["href"], "nofollow" in rel))
        elif tag == "meta" and (a.get("name") or "").lower() == "robots":
            if "nofollow" in (a.get("content") or "").lower():
                self.nofollow_meta = True


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            ctype = (r.headers.get("Content-Type") or "").lower()
            if "html" not in ctype:
                return r.status, "", r.geturl()
            return r.status, r.read().decode("utf-8", "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, "", url
    except Exception:  # noqa: BLE001
        return None, "", url


def internal(href, base, host):
    """Resolve href against base. Return a normalised URL, or None if not crawlable."""
    href = href.strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    full = urllib.parse.urljoin(base, href)
    p = urllib.parse.urlsplit(full)
    if p.scheme not in ("http", "https") or p.netloc.lower() != host:
        return None
    low = p.path.lower()
    if low.endswith(SKIP_EXT) or low.startswith(SKIP_PATH):
        return None
    return sitemap_mod.normalise(full)


def crawl(root, max_depth, max_pages, delay):
    start = sitemap_mod.normalise(root)
    host = urllib.parse.urlsplit(start).netloc.lower()
    depth = {start: 0}
    order = [start]
    queue = collections.deque([start])
    fetched, failures = {}, {}
    hit_cap = False

    while queue:
        if len(fetched) >= max_pages:
            hit_cap = True
            break
        url = queue.popleft()
        if fetched:
            time.sleep(delay)
        status, body, final = fetch(url)
        fetched[url] = status
        if status != 200 or not body:
            if status != 200:
                failures[url] = status
            continue
        if depth[url] >= max_depth:
            continue
        parser = Links()
        try:
            parser.feed(body)
        except Exception:  # noqa: BLE001
            pass
        for href, _nofollow in parser.hrefs:
            nxt = internal(href, final or url, host)
            if nxt and nxt not in depth:
                depth[nxt] = depth[url] + 1
                order.append(nxt)
                queue.append(nxt)

    return {
        "start": start, "host": host, "depth": depth, "order": order,
        "fetched": fetched, "failures": failures,
        "hit_cap": hit_cap, "queued_unvisited": len(queue),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="site root, e.g. https://example.com")
    ap.add_argument("--max-depth", type=int, default=4)
    ap.add_argument("--max-pages", type=int, default=200)
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--no-sitemap", action="store_true", help="skip orphan detection")
    ap.add_argument("--out", help="write JSON here")
    args = ap.parse_args()

    root = args.url.rstrip("/")
    c = crawl(root, args.max_depth, args.max_pages, args.delay)

    reached = {u for u, st in c["fetched"].items() if st == 200}
    by_depth = collections.Counter(c["depth"][u] for u in reached)
    deep = sorted(u for u in reached if c["depth"][u] >= DEEP)

    result = {
        "site": root,
        "max_depth": args.max_depth,
        "max_pages": args.max_pages,
        "pages_fetched": len(c["fetched"]),
        "pages_ok": len(reached),
        "depth_histogram": {str(k): v for k, v in sorted(by_depth.items())},
        "deep_pages": [{"url": u, "depth": c["depth"][u]} for u in deep],
        "fetch_failures": [{"url": u, "status": st} for u, st in sorted(c["failures"].items())],
        "crawl_complete": not c["hit_cap"],
        "notes": [],
    }
    if c["hit_cap"]:
        result["notes"].append(
            "Crawl stopped at the %d page cap with %d URLs still queued. Depth and orphan "
            "results below are partial. Raise --max-pages for a full read."
            % (args.max_pages, c["queued_unvisited"]))

    if args.no_sitemap:
        result["orphans"] = None
        result["notes"].append("Orphan detection skipped (--no-sitemap). Orphan state is UNKNOWN.")
    else:
        sm = sitemap_mod.collect(root)
        sm_urls = [sitemap_mod.normalise(u) for u in sm["urls"]]
        result["sitemap"] = {
            "sources": sm["sources"], "url_count": len(sm_urls),
            "truncated": sm["truncated"], "notes": sm["notes"],
        }
        if not sm_urls:
            result["orphans"] = None
            result["notes"].append(
                "No sitemap URLs read, so orphan state is UNKNOWN, not clean. %s"
                % (" ".join(sm["notes"]) or ""))
        else:
            missing = [u for u in sm_urls if u not in reached]
            result["orphans"] = missing
            result["orphan_rate"] = round(len(missing) / len(sm_urls), 3)
            result["orphans_reliable"] = not c["hit_cap"]
            if c["hit_cap"]:
                result["notes"].append(
                    "Orphan list is unreliable while the crawl is capped: an uncrawled page "
                    "cannot be distinguished from an unlinked one.")

    print("crawl:   %s" % root)
    print("fetched: %d pages, %d returned 200%s"
          % (result["pages_fetched"], result["pages_ok"],
             ", CAPPED" if c["hit_cap"] else ""))
    print("\ndepth (links from the homepage)")
    for d, n in sorted(by_depth.items()):
        print("  %d  %s %d" % (d, "#" * min(n, 40), n))
    if deep:
        print("\n%d page(s) at depth %d or deeper:" % (len(deep), DEEP))
        for u in deep[:15]:
            print("  %d  %s" % (c["depth"][u], u))
        if len(deep) > 15:
            print("  ... and %d more" % (len(deep) - 15))

    orphans = result.get("orphans")
    if orphans is None:
        print("\norphans: UNKNOWN")
    elif not result.get("orphans_reliable", True):
        # A capped crawl cannot tell an unlinked page from one it never got to, so it
        # does not get to publish a list. Naming 492 false orphans is worse than silence.
        print("\norphans: UNKNOWN, the crawl was capped at %d pages. %d sitemap URL(s) went "
              "unreached,\n         but that is indistinguishable from uncrawled. Re-run with "
              "--max-pages above %d." % (args.max_pages, len(orphans), len(orphans)))
    elif orphans:
        print("\n%d sitemap URL(s) not reached by any internal link (%.0f%% of the sitemap):"
              % (len(orphans), result["orphan_rate"] * 100))
        for u in orphans[:15]:
            print("  %s" % u)
        if len(orphans) > 15:
            print("  ... and %d more" % (len(orphans) - 15))
    else:
        print("\norphans: none, every sitemap URL was reached")

    if result["fetch_failures"]:
        print("\nfetch failures:")
        for f in result["fetch_failures"][:10]:
            print("  %-6s %s" % (f["status"], f["url"]))

    for n in result["notes"]:
        print("\nnote: %s" % n)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        print("\nwrote %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
