#!/usr/bin/env python3
"""Site-wide health fingerprint and day-over-day diff.

Most SEO tooling only checks the page you just shipped. Drift happens in the
pages you stopped looking at: a canonical flips, a title gets truncated by a
template change, a sitemap starts emitting the build date as lastmod, a page
quietly starts 301-ing. This script fingerprints every URL in the sitemap,
stores the fingerprint, and reports what moved since the last run.

It is a report, not a gate. It always exits 0. Read the violations.

Usage
  health_diff.py --sitemap https://example.com/sitemap.xml
  health_diff.py --sitemap web/public/sitemap.xml --base-url https://example.com
  health_diff.py --sitemap https://example.com/sitemap.xml --limit 40 --json
  health_diff.py --sitemap https://example.com/sitemap.xml \
      --expect-schema '*/guides/*' --expect-schema '*/compare/*'
  health_diff.py --sitemap https://example.com/sitemap.xml --check-links
  health_diff.py --sitemap https://example.com/sitemap.xml --keep-text

--sitemap accepts a sitemap URL, a sitemap index URL, a local sitemap file, or a
site root (in which case sitemap.py's robots.txt-first discovery runs).
--local-root reads each URL's HTML from disk (static build output) instead of
over the network, falling back to a fetch when no file matches the path.
--keep-text stores each page's visible body text on the fingerprint as
body_text (capped at 40,000 characters, body_text_truncated: true when cut) so
truth_check.py --from-health can check the rendered copy of a site whose
content lives in a database. Off by default so daily snapshots stay small.

Standard library only.
"""

import argparse
import concurrent.futures
import datetime
import fnmatch
import gzip
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import sitemap as sitemap_mod  # shared with robots_check.py / depth_check.py
except Exception:  # noqa: BLE001
    sitemap_mod = None

UA = "Mozilla/5.0 (compatible; seo-skill-health-diff/1.0)"
TIMEOUT = 15
MAX_BODY = 4_000_000
MAX_SITEMAP_CHILDREN = 50
MAX_SITEMAP_DEPTH = 3
MAX_REDIRECT_HOPS = 5
# Stripped before counting body words: chrome and machine-readable payloads are
# not the page's content, and counting them hides thin pages.
SKIP_TEXT_TAGS = {"script", "style", "noscript", "template", "svg", "nav", "footer"}
MAX_BODY_TEXT = 40_000     # --keep-text cap, per page
DATE_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")
SLOW_TTFB_MS = 1000        # slow on two consecutive runs before it is reported
SLOW_TTFB_MS_FIRST_RUN = 2000  # with no previous fingerprint, only the egregious
HEAVY_HTML_BYTES = 600_000


# ---------------------------------------------------------------- url helpers

def normalise(url):
    if sitemap_mod is not None:
        return sitemap_mod.normalise(url)
    try:
        p = urllib.parse.urlsplit((url or "").strip())
    except ValueError:
        return (url or "").strip()
    path = p.path or "/"
    if len(path) > 1:
        path = path.rstrip("/")
    return urllib.parse.urlunsplit(
        (p.scheme.lower(), p.netloc.lower(), path, p.query, ""))


def host_of(url):
    try:
        return urllib.parse.urlsplit(url).netloc.lower()
    except ValueError:
        return ""


# ------------------------------------------------------------------- fetching

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Redirects are counted by hand so redirect_hops is real, not inferred."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _decode(raw, headers):
    charset = None
    ctype = (headers.get("Content-Type") or "") if headers else ""
    m = re.search(r"charset=([\w\-]+)", ctype, re.I)
    if m:
        charset = m.group(1)
    for enc in (charset, "utf-8", "latin-1"):
        if not enc:
            continue
        try:
            return raw.decode(enc, "replace")
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", "replace")


def fetch(url):
    """Follow redirects by hand. Retry once on 5xx or a transport error.

    The retry matters more than it looks: a single DNS blip turns into a
    "non-200 in sitemap" violation and a fake status change in the diff, which
    is exactly the kind of noise that gets a health report ignored."""
    result = _fetch_once(url)
    status = result["status"]
    if status == 0 or (status and 500 <= status < 600):
        result = _fetch_once(url)
    return result


def _fetch_once(url):
    opener = urllib.request.build_opener(_NoRedirect)
    cur, hops = url, 0
    while True:
        req = urllib.request.Request(
            cur, headers={"User-Agent": UA,
                          "Accept": "text/html,application/xhtml+xml,*/*"})
        # Timed per hop, so ttfb_ms describes the response that was actually
        # rendered rather than the sum of a redirect chain.
        t0 = time.monotonic()
        try:
            with opener.open(req, timeout=TIMEOUT) as r:
                # Headers are in hand here; the body read below is not counted.
                ttfb = int(round((time.monotonic() - t0) * 1000))
                status = getattr(r, "status", None) or r.getcode()
                headers = dict(r.headers.items())
                raw = r.read(MAX_BODY)
                body = _decode(raw, r.headers)
                return {"status": status, "final_url": r.geturl() or cur,
                        "redirect_hops": hops, "headers": headers,
                        "body": body, "error": None,
                        "ttfb_ms": ttfb, "html_bytes": len(raw)}
        except urllib.error.HTTPError as e:
            ttfb = int(round((time.monotonic() - t0) * 1000))
            loc = e.headers.get("Location") if e.headers else None
            if e.code in (301, 302, 303, 307, 308) and loc and hops < MAX_REDIRECT_HOPS:
                cur = urllib.parse.urljoin(cur, loc)
                hops += 1
                continue
            body, raw = "", b""
            try:
                raw = e.read(MAX_BODY)
                body = _decode(raw, e.headers)
            except Exception:  # noqa: BLE001
                pass
            return {"status": e.code, "final_url": cur, "redirect_hops": hops,
                    "headers": dict(e.headers.items()) if e.headers else {},
                    "body": body, "error": None,
                    "ttfb_ms": ttfb, "html_bytes": len(raw)}
        except Exception as ex:  # noqa: BLE001
            return {"status": 0, "final_url": cur, "redirect_hops": hops,
                    "headers": {}, "body": "",
                    "error": "%s: %s" % (type(ex).__name__, ex),
                    "ttfb_ms": None, "html_bytes": 0}


def _link_once(url, method):
    """One request, redirects NOT followed: a 3xx is a finding, not a detour."""
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(
        url, method=method,
        headers={"User-Agent": UA,
                 "Accept": "text/html,application/xhtml+xml,*/*"})
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            status = getattr(r, "status", None) or r.getcode()
            if method == "GET":
                r.read(MAX_BODY)
            return {"status": status, "location": None, "error": None,
                    "method": method}
    except urllib.error.HTTPError as e:
        loc = e.headers.get("Location") if e.headers else None
        try:
            e.read(MAX_BODY)
        except Exception:  # noqa: BLE001
            pass
        return {"status": e.code,
                "location": urllib.parse.urljoin(url, loc) if loc else None,
                "error": None, "method": method}
    except Exception as ex:  # noqa: BLE001
        return {"status": 0, "location": None,
                "error": "%s: %s" % (type(ex).__name__, ex), "method": method}


def check_link(url):
    """HEAD, falling back to GET when the server refuses the method.

    Same retry policy as fetch(): one retry on a transport error or a 5xx, so a
    single blip does not manufacture a broken-link finding."""
    r = _link_once(url, "HEAD")
    if r["status"] in (405, 501):
        r = _link_once(url, "GET")
    if r["status"] == 0 or (r["status"] and 500 <= r["status"] < 600):
        r = _link_once(url, r["method"])
        if r["status"] in (405, 501):
            r = _link_once(url, "GET")
    return r


def local_file_for(url, root):
    path = urllib.parse.unquote(urllib.parse.urlsplit(url).path or "/")
    rel = path.lstrip("/")
    if rel in ("", "/"):
        cands = ["index.html"]
    elif rel.endswith("/"):
        cands = [rel + "index.html", rel.rstrip("/") + ".html"]
    else:
        cands = [rel, rel + ".html", os.path.join(rel, "index.html")]
    for c in cands:
        fp = os.path.normpath(os.path.join(root, c))
        if os.path.isfile(fp):
            return fp
    return None


def read_local(url, root):
    fp = local_file_for(url, root)
    if fp is None:
        return None
    with open(fp, "rb") as fh:
        raw = fh.read(MAX_BODY)
    # No network hop, so there is no TTFB to report — null, not zero, so the
    # slow-ttfb rule and the median both skip local reads instead of being
    # dragged to 0 by them.
    return {"status": 200, "final_url": url, "redirect_hops": 0,
            "headers": {}, "body": _decode(raw, None), "error": None,
            "local_file": fp, "ttfb_ms": None, "html_bytes": len(raw)}


# -------------------------------------------------------------------- sitemap

def _sitemap_bytes(src):
    """Return raw bytes for a sitemap URL or local path, ungzipping if needed."""
    if os.path.exists(src):
        with open(src, "rb") as fh:
            raw = fh.read()
    else:
        req = urllib.request.Request(src, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                raw = r.read()
        except Exception:  # noqa: BLE001
            return None
    if raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except Exception:  # noqa: BLE001
            return None
    return raw


def _entries(xml):
    """[(loc, lastmod)] from a <urlset>."""
    out = []
    for block in re.findall(r"<url\b[^>]*>(.*?)</url\s*>", xml, re.I | re.S):
        loc = re.search(r"<loc>\s*([^<]+?)\s*</loc>", block, re.I)
        if not loc:
            continue
        lm = re.search(r"<lastmod>\s*([^<]+?)\s*</lastmod>", block, re.I)
        out.append((loc.group(1).strip(), lm.group(1).strip() if lm else None))
    if not out:
        for loc in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml, re.I):
            out.append((loc.strip(), None))
    return out


def load_sitemap(src, depth=0, seen=None, notes=None):
    """[(url, lastmod)], recursing sitemap indexes."""
    seen = seen if seen is not None else set()
    notes = notes if notes is not None else []
    if src in seen or depth > MAX_SITEMAP_DEPTH:
        return []
    seen.add(src)

    raw = _sitemap_bytes(src)
    if raw is None:
        notes.append("could not read sitemap %s" % src)
        return []
    xml = raw.decode("utf-8", "replace")

    if "<sitemapindex" in xml[:4000].lower():
        children = [m.strip() for m in
                    re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml, re.I)]
        if len(children) > MAX_SITEMAP_CHILDREN:
            notes.append("sitemap index lists %d children, read the first %d"
                         % (len(children), MAX_SITEMAP_CHILDREN))
        out = []
        for child in children[:MAX_SITEMAP_CHILDREN]:
            out.extend(load_sitemap(child, depth + 1, seen, notes))
        return out
    return _entries(xml)


def discover_sitemap(src, notes):
    """Accept a sitemap URL/path or a bare site root."""
    looks_like_sitemap = (os.path.exists(src)
                          or src.lower().endswith((".xml", ".xml.gz"))
                          or "sitemap" in src.lower())
    if looks_like_sitemap:
        entries = load_sitemap(src, notes=notes)
        if entries:
            return entries
    if sitemap_mod is not None and src.startswith(("http://", "https://")):
        got = sitemap_mod.collect(src)
        notes.extend(got.get("notes") or [])
        if got["urls"]:
            notes.append("discovered sitemaps via sitemap.py: %s"
                         % ", ".join(got["sources"]))
            merged = []
            for source in got["sources"]:
                merged.extend(load_sitemap(source, notes=notes))
            if merged:
                return merged
            return [(u, None) for u in got["urls"]]
    return []


# ---------------------------------------------------------------- html parsing

class _Page(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.title_parts = []
        self._in_title = False
        self.meta_description = None
        self.meta_robots = []
        self.html_lang = None
        self.h1_count = 0
        self.canonical = None
        self.ld_blocks = []
        self._ld_buf = None
        self.links = []
        self._skip = 0
        self._text = []

    # HTMLParser calls this for <br/> style tags too, via handle_startendtag.
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html" and a.get("lang"):
            self.html_lang = a["lang"].strip()
        elif tag == "title":
            self._in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "meta":
            name = (a.get("name") or a.get("property") or "").lower()
            if name == "description" and self.meta_description is None:
                self.meta_description = (a.get("content") or "").strip()
            elif name == "robots":
                self.meta_robots.append((a.get("content") or "").strip())
        elif tag == "link":
            rels = (a.get("rel") or "").lower().split()
            if "canonical" in rels and self.canonical is None:
                self.canonical = (a.get("href") or "").strip()
        elif tag == "a":
            href = (a.get("href") or "").strip()
            if href:
                self.links.append(href)
        elif tag == "script" and "ld+json" in (a.get("type") or "").lower():
            self._ld_buf = []
        if tag in SKIP_TEXT_TAGS:
            self._skip += 1

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._ld_buf is not None:
            self.ld_blocks.append("".join(self._ld_buf))
            self._ld_buf = None
        if tag in SKIP_TEXT_TAGS and self._skip > 0:
            self._skip -= 1

    def handle_data(self, data):
        if self._ld_buf is not None:
            self._ld_buf.append(data)
            return
        if self._in_title:
            self.title_parts.append(data)
        if self._skip == 0:
            self._text.append(data)

    def text(self):
        return re.sub(r"\s+", " ", "".join(self._text)).strip()

    def title(self):
        t = re.sub(r"\s+", " ", "".join(self.title_parts)).strip()
        return t or None


def jsonld_types(blocks):
    """@type values, walking @graph. Nested node types are deliberately ignored:
    an author's Person type says nothing about whether the page has schema."""
    types = []

    def walk(node):
        if isinstance(node, dict):
            t = node.get("@type")
            if isinstance(t, str):
                types.append(t)
            elif isinstance(t, list):
                types.extend([x for x in t if isinstance(x, str)])
            g = node.get("@graph")
            if g is not None:
                walk(g)
        elif isinstance(node, list):
            for x in node:
                walk(x)

    for raw in blocks:
        raw = (raw or "").strip()
        if not raw:
            continue
        try:
            walk(json.loads(raw))
        except Exception:  # noqa: BLE001
            continue
    seen, out = set(), []
    for t in types:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


ARTICLE_TYPES = {"article", "blogposting", "newsarticle"}


def jsonld_article_dates(blocks):
    """(datePublished, dateModified) from the first Article/BlogPosting/
    NewsArticle node, walking @graph. Freshness lives on the article node, so a
    sibling Organization or BreadcrumbList is skipped rather than merged in."""
    state = {"done": False, "published": None, "modified": None}

    def types_of(node):
        t = node.get("@type")
        if isinstance(t, str):
            return [t]
        if isinstance(t, list):
            return [x for x in t if isinstance(x, str)]
        return []

    def walk(node):
        if state["done"]:
            return
        if isinstance(node, dict):
            if any(t.lower() in ARTICLE_TYPES for t in types_of(node)):
                dp, dm = node.get("datePublished"), node.get("dateModified")
                state["published"] = dp.strip() if isinstance(dp, str) and dp.strip() else None
                state["modified"] = dm.strip() if isinstance(dm, str) and dm.strip() else None
                state["done"] = True
                return
            g = node.get("@graph")
            if g is not None:
                walk(g)
        elif isinstance(node, list):
            for x in node:
                walk(x)

    for raw in blocks:
        raw = (raw or "").strip()
        if not raw:
            continue
        try:
            walk(json.loads(raw))
        except Exception:  # noqa: BLE001
            continue
        if state["done"]:
            break
    return state["published"], state["modified"]


def fingerprint(url, lastmod, base_host, local_root, keep_text=False):
    got = None
    if local_root:
        try:
            got = read_local(url, local_root)
        except Exception:  # noqa: BLE001
            got = None
    if got is None:
        got = fetch(url)

    rec = {
        "status": got["status"],
        "final_url": got["final_url"],
        "redirect_hops": got["redirect_hops"],
        "canonical": None,
        "title": None,
        "meta_description": None,
        "html_lang": None,
        "h1_count": 0,
        "jsonld_types": [],
        "date_published": None,
        "date_modified": None,
        "sitemap_lastmod": lastmod,
        "body_words": 0,
        "noindex": False,
        "internal_link_count": 0,
        "content_hash": None,
        "ttfb_ms": got.get("ttfb_ms"),
        "html_bytes": got.get("html_bytes") or 0,
    }
    if got.get("error"):
        rec["error"] = got["error"]
    if got.get("local_file"):
        rec["local_file"] = got["local_file"]

    xrobots = ""
    for k, v in (got.get("headers") or {}).items():
        if k.lower() == "x-robots-tag":
            xrobots += " " + (v or "")

    body = got.get("body") or ""
    if not body:
        rec["noindex"] = "noindex" in xrobots.lower()
        rec["_internal_links"] = []
        if keep_text:
            rec["body_text"] = ""
        return rec

    p = _Page()
    try:
        p.feed(body)
        p.close()
    except Exception:  # noqa: BLE001
        pass

    text = p.text()
    canonical = p.canonical
    if canonical:
        canonical = urllib.parse.urljoin(got["final_url"], canonical)

    dates = jsonld_article_dates(p.ld_blocks)
    page_host = base_host or host_of(got["final_url"])
    internal = 0
    targets, seen_targets = [], set()
    for href in p.links:
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absu = urllib.parse.urljoin(got["final_url"], href)
        if not absu.startswith(("http://", "https://")):
            continue
        if host_of(absu) == page_host:
            internal += 1
            absu = urllib.parse.urldefrag(absu)[0]
            if absu not in seen_targets:
                seen_targets.add(absu)
                targets.append(absu)
    # Carried out-of-band on the record and popped before the fingerprint is
    # written: the link graph is a working set, not something to store 217 times.
    rec["_internal_links"] = targets

    rec.update({
        "canonical": canonical,
        "title": p.title(),
        "meta_description": p.meta_description or None,
        "html_lang": p.html_lang,
        "h1_count": p.h1_count,
        "jsonld_types": jsonld_types(p.ld_blocks),
        "date_published": dates[0],
        "date_modified": dates[1],
        "body_words": len(text.split()),
        "noindex": ("noindex" in (" ".join(p.meta_robots) + xrobots).lower()),
        "internal_link_count": internal,
        "content_hash": hashlib.sha1(text.encode("utf-8")).hexdigest(),
    })
    # Not part of the diff: content_hash already says whether the copy moved,
    # this is the copy itself for truth_check.py --from-health.
    if keep_text:
        rec["body_text"] = text[:MAX_BODY_TEXT]
        if len(text) > MAX_BODY_TEXT:
            rec["body_text_truncated"] = True
    return rec


# ----------------------------------------------------------------- link graph

def link_pass(pages, link_graph, workers):
    """Fill inbound_link_count on every page, then check the off-sitemap targets.

    Two different questions share one crawl of the collected hrefs: which
    sitemap pages nothing links to (orphans), and which link targets are dead.
    Targets already in the sitemap are skipped — they were fetched a moment ago
    and non-200-in-sitemap already reports them."""
    by_norm = {}
    for u in pages:
        by_norm.setdefault(normalise(u), u)

    inbound = {u: set() for u in pages}
    todo = {}
    for src, targets in link_graph.items():
        for t in targets:
            hit = by_norm.get(normalise(t))
            if hit is not None:
                if hit != src:  # a self-link is not an inbound link
                    inbound[hit].add(src)
                continue
            todo.setdefault(t, []).append(src)

    for u, rec in pages.items():
        rec["inbound_link_count"] = len(inbound.get(u) or ())
        rec["broken_internal_links"] = []
        rec["redirecting_internal_links"] = []

    results = {}
    if todo:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(check_link, t): t for t in todo}
            for fut in concurrent.futures.as_completed(futs):
                t = futs[fut]
                try:
                    results[t] = fut.result()
                except Exception as ex:  # noqa: BLE001
                    results[t] = {"status": 0, "location": None,
                                  "error": "%s: %s" % (type(ex).__name__, ex)}

    broken_n = redirecting_n = 0
    for target, srcs in todo.items():
        r = results.get(target) or {"status": 0, "location": None}
        st = r.get("status") or 0
        if st and 300 <= st < 400:
            redirecting_n += 1
            for src in srcs:
                pages[src]["redirecting_internal_links"].append(
                    {"href": target, "status": st, "location": r.get("location")})
        elif st == 0 or st >= 400:
            broken_n += 1
            for src in srcs:
                pages[src]["broken_internal_links"].append(
                    {"href": target, "status": st})

    for rec in pages.values():
        rec["broken_internal_links"].sort(key=lambda x: x["href"])
        rec["redirecting_internal_links"].sort(key=lambda x: x["href"])

    return {"unique_targets": len(todo), "broken": broken_n,
            "redirecting": redirecting_n}


# ------------------------------------------------------------------ violations

def parse_lastmod(value):
    if not value:
        return None
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    for attempt in (v, v[:10]):
        try:
            d = datetime.datetime.fromisoformat(attempt)
            if d.tzinfo is None:
                d = d.replace(tzinfo=datetime.timezone.utc)
            return d
        except ValueError:
            continue
    return None


def is_home(url):
    try:
        return (urllib.parse.urlsplit(url).path or "/").rstrip("/") == ""
    except ValueError:
        return False


def violations(pages, expect_schema, prev_pages=None):
    out = []
    titles, descs, lastmod_days = {}, {}, {}
    prev_pages = prev_pages or {}
    now = datetime.datetime.now(datetime.timezone.utc)

    for url, rec in pages.items():
        st = rec.get("status")
        if st != 200:
            detail = "status %s" % st
            if rec.get("error"):
                detail += " (%s)" % rec["error"]
            out.append({"rule": "non-200-in-sitemap", "url": url, "detail": detail})
        if rec.get("redirect_hops"):
            out.append({"rule": "sitemap-url-redirects", "url": url,
                        "detail": "%d hop(s) to %s"
                                  % (rec["redirect_hops"], rec.get("final_url"))})
        can = rec.get("canonical")
        if st == 200:
            if not can:
                out.append({"rule": "canonical-mismatch", "url": url,
                            "detail": "no canonical"})
            elif normalise(can) != normalise(rec.get("final_url") or url):
                out.append({"rule": "canonical-mismatch", "url": url,
                            "detail": "canonical %s != final %s"
                                      % (can, rec.get("final_url"))})
            if not rec.get("html_lang"):
                out.append({"rule": "missing-html-lang", "url": url, "detail": ""})
            if not rec.get("title"):
                out.append({"rule": "missing-title", "url": url, "detail": ""})
            else:
                titles.setdefault(rec["title"].strip().lower(), []).append(url)
            if rec.get("meta_description"):
                descs.setdefault(rec["meta_description"].strip().lower(), []).append(url)
            if rec.get("h1_count") != 1:
                out.append({"rule": "h1-count", "url": url,
                            "detail": "h1_count=%s" % rec.get("h1_count")})
            if expect_schema and not rec.get("jsonld_types"):
                if any(fnmatch.fnmatch(url, g) for g in expect_schema):
                    out.append({"rule": "missing-schema", "url": url,
                                "detail": "no JSON-LD @type"})
        if rec.get("noindex"):
            out.append({"rule": "noindex-in-sitemap", "url": url, "detail": ""})

        # Speed and weight. One slow sample is a blip, so slow-ttfb needs the
        # same page to have been slow on the previous fingerprint too; with no
        # previous run to corroborate, only the egregious cases are reported.
        ttfb = rec.get("ttfb_ms")
        if isinstance(ttfb, (int, float)) and ttfb > SLOW_TTFB_MS:
            prev_ttfb = (prev_pages.get(url) or {}).get("ttfb_ms")
            if prev_pages and isinstance(prev_ttfb, (int, float)):
                if prev_ttfb > SLOW_TTFB_MS:
                    out.append({"rule": "slow-ttfb", "url": url,
                                "detail": "%d ms now, %d ms on the previous run"
                                          % (ttfb, prev_ttfb)})
            elif ttfb > SLOW_TTFB_MS_FIRST_RUN:
                out.append({"rule": "slow-ttfb", "url": url,
                            "detail": "%d ms (no previous run to corroborate, "
                                      "so the bar is %d ms)"
                                      % (ttfb, SLOW_TTFB_MS_FIRST_RUN)})
        hb = rec.get("html_bytes")
        if isinstance(hb, (int, float)) and hb > HEAVY_HTML_BYTES:
            out.append({"rule": "heavy-html", "url": url,
                        "detail": "%d bytes of HTML" % int(hb)})

        broken_links = rec.get("broken_internal_links") or []
        if broken_links:
            shown = ", ".join("%s (%s)" % (b["href"], b["status"] or "failed")
                              for b in broken_links[:3])
            more = "" if len(broken_links) <= 3 else " (+%d more)" % (
                len(broken_links) - 3)
            out.append({"rule": "broken-internal-link", "url": url,
                        "detail": "%d broken: %s%s"
                                  % (len(broken_links), shown, more)})
        redirecting = rec.get("redirecting_internal_links") or []
        if redirecting:
            shown = ", ".join("%s -> %s" % (b["href"], b.get("location"))
                              for b in redirecting[:3])
            out.append({"rule": "redirecting-internal-link", "url": url,
                        "detail": "%d redirecting: %s"
                                  % (len(redirecting), shown)})
        if "inbound_link_count" in rec and not rec["inbound_link_count"] \
                and not is_home(url):
            out.append({"rule": "orphan-page", "url": url,
                        "detail": "no other sitemap page links to it"})

        lm = rec.get("sitemap_lastmod")
        d = parse_lastmod(lm)
        if d:
            if d > now + datetime.timedelta(hours=26):
                out.append({"rule": "lastmod-in-future", "url": url,
                            "detail": lm})
            lastmod_days.setdefault(lm.strip()[:10], []).append(url)
        dp = parse_lastmod(rec.get("date_published"))
        dm = parse_lastmod(rec.get("date_modified"))
        if dm and d:
            if dp and dm.date() == dp.date() and d.date() > dm.date():
                out.append({
                    "rule": "freshness-contradiction", "url": url,
                    "detail": "dateModified == datePublished (%s) but sitemap "
                              "lastmod is %s — the page says it was never "
                              "updated and the sitemap says it was"
                              % (rec.get("date_modified"), lm)})
            elif (dm - d).days > 1:
                out.append({
                    "rule": "freshness-contradiction", "url": url,
                    "detail": "dateModified %s is %d days after sitemap lastmod "
                              "%s" % (rec.get("date_modified"),
                                      (dm - d).days, lm)})

    for title, urls in sorted(titles.items()):
        if len(urls) > 1:
            out.append({"rule": "duplicate-title", "url": urls[0],
                        "detail": "%d pages share %r (e.g. %s)"
                                  % (len(urls), title[:70], ", ".join(urls[1:4]))})
    for desc, urls in sorted(descs.items()):
        if len(urls) > 1:
            out.append({"rule": "duplicate-meta-description", "url": urls[0],
                        "detail": "%d pages share %r (e.g. %s)"
                                  % (len(urls), desc[:70], ", ".join(urls[1:4]))})

    total_lm = sum(len(v) for v in lastmod_days.values())
    if total_lm >= 5:
        for day, urls in sorted(lastmod_days.items()):
            if len(urls) / float(total_lm) > 0.80:
                out.append({
                    "rule": "build-date-lastmod", "url": "(sitemap)",
                    "detail": "%d of %d URLs with lastmod share %s — lastmod "
                              "should be a content date, not a build date"
                              % (len(urls), total_lm, day)})
    return out


# ------------------------------------------------------------------------ diff

def build_diff(prev, cur):
    prev_pages = (prev or {}).get("pages") or {}
    cur_pages = cur["pages"]
    prev_urls, cur_urls = set(prev_pages), set(cur_pages)

    d = {
        "new_urls": sorted(cur_urls - prev_urls),
        "removed_urls": sorted(prev_urls - cur_urls),
        "status_changes": [],
        "canonical_changes": [],
        "title_changes": [],
        "lastmod_changes": [],
        "redirect_appeared": [],
        "content_changed": {"count": 0, "urls": []},
    }
    changed_hashes = []
    for url in sorted(cur_urls & prev_urls):
        a, b = prev_pages[url], cur_pages[url]
        if a.get("status") != b.get("status"):
            d["status_changes"].append(
                {"url": url, "from": a.get("status"), "to": b.get("status")})
        if a.get("canonical") != b.get("canonical"):
            d["canonical_changes"].append(
                {"url": url, "from": a.get("canonical"), "to": b.get("canonical")})
        if a.get("title") != b.get("title"):
            d["title_changes"].append(
                {"url": url, "from": a.get("title"), "to": b.get("title")})
        if a.get("sitemap_lastmod") != b.get("sitemap_lastmod"):
            d["lastmod_changes"].append(
                {"url": url, "from": a.get("sitemap_lastmod"),
                 "to": b.get("sitemap_lastmod")})
        if not a.get("redirect_hops") and b.get("redirect_hops"):
            d["redirect_appeared"].append(
                {"url": url, "to": b.get("final_url"),
                 "hops": b.get("redirect_hops")})
        if a.get("content_hash") and b.get("content_hash") \
                and a["content_hash"] != b["content_hash"]:
            changed_hashes.append(url)
    d["content_changed"] = {"count": len(changed_hashes),
                            "urls": changed_hashes[:20]}
    touched = set(d["new_urls"]) | set(d["removed_urls"]) | set(changed_hashes)
    for key in ("status_changes", "canonical_changes", "title_changes",
                "lastmod_changes", "redirect_appeared"):
        touched |= {r["url"] for r in d[key]}
    d["changed_count"] = len(touched)
    return d


def previous_file(out_dir, exclude=None):
    if not os.path.isdir(out_dir):
        return None
    files = sorted(f for f in os.listdir(out_dir) if DATE_FILE_RE.match(f))
    files = [f for f in files if os.path.join(out_dir, f) != exclude]
    return os.path.join(out_dir, files[-1]) if files else None


# ---------------------------------------------------------------------- output

def _fmt(v, width=70):
    s = "(none)" if v is None else str(v)
    return s if len(s) <= width else s[:width - 1] + "\u2026"


def summary_text(cur, diff, viols, link_check=None):
    s = ("SUMMARY: %d pages, %d changed, %d violations"
         % (len(cur["pages"]), diff["changed_count"], len(viols)))
    if link_check:
        s += (" links: %d targets, %d broken, %d redirecting"
              % (link_check["unique_targets"], link_check["broken"],
                 link_check["redirecting"]))
    return s


def print_report(cur, diff, viols, prev_path, notes, link_check=None):
    print("SEO health diff \u2014 %s" % (cur.get("base_url") or "(unknown site)"))
    print("  current:  %s (%d pages)" % (cur["_path"], len(cur["pages"])))
    same_day = prev_path == cur["_path"]
    print("  previous: %s%s"
          % (prev_path or "(none \u2014 first run, baseline written)",
             "  (prior run, same day)" if same_day else ""))
    for n in notes:
        print("  note: %s" % n)
    print("")

    def section(title, rows, render):
        if not rows:
            return
        print("%s (%d)" % (title, len(rows)))
        for r in rows[:20]:
            print("  %s" % render(r))
        if len(rows) > 20:
            print("  \u2026and %d more" % (len(rows) - 20))
        print("")

    section("NEW URLS", diff["new_urls"], lambda u: u)
    section("REMOVED URLS", diff["removed_urls"], lambda u: u)
    section("STATUS CHANGES", diff["status_changes"],
            lambda r: "%s  %s -> %s" % (r["url"], r["from"], r["to"]))
    section("REDIRECT APPEARED", diff["redirect_appeared"],
            lambda r: "%s  -> %s (%d hop)" % (r["url"], r["to"], r["hops"]))
    section("CANONICAL CHANGES", diff["canonical_changes"],
            lambda r: "%s\n    from %s\n    to   %s"
                      % (r["url"], _fmt(r["from"]), _fmt(r["to"])))
    section("TITLE CHANGES", diff["title_changes"],
            lambda r: "%s\n    from %s\n    to   %s"
                      % (r["url"], _fmt(r["from"]), _fmt(r["to"])))
    section("LASTMOD CHANGES", diff["lastmod_changes"],
            lambda r: "%s  %s -> %s" % (r["url"], r["from"], r["to"]))

    cc = diff["content_changed"]
    if cc["count"]:
        print("CONTENT CHANGED (%d)" % cc["count"])
        for u in cc["urls"]:
            print("  %s" % u)
        if cc["count"] > len(cc["urls"]):
            print("  \u2026and %d more" % (cc["count"] - len(cc["urls"])))
        print("")

    print("RULE VIOLATIONS (%d)" % len(viols))
    if not viols:
        print("  none")
    else:
        by_rule = {}
        for v in viols:
            by_rule.setdefault(v["rule"], []).append(v)
        for rule in sorted(by_rule):
            rows = by_rule[rule]
            print("  [%s] %d" % (rule, len(rows)))
            for v in rows[:10]:
                line = "    %s" % v["url"]
                if v.get("detail"):
                    line += "  \u2014 %s" % v["detail"]
                print(line)
            if len(rows) > 10:
                print("    \u2026and %d more" % (len(rows) - 10))
    print("")
    if link_check:
        print("INTERNAL LINKS")
        print("  %d unique off-sitemap targets checked, %d broken, %d redirecting"
              % (link_check["unique_targets"], link_check["broken"],
                 link_check["redirecting"]))
        print("")
    print(summary_text(cur, diff, viols, link_check))


# ------------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(
        description="Site-wide health fingerprint and diff. Always exits 0.")
    ap.add_argument("--sitemap", required=True,
                    help="sitemap URL, sitemap index URL, local sitemap file, "
                         "or a site root to discover from")
    ap.add_argument("--base-url", help="site root, used for internal-link counting")
    ap.add_argument("--out", default=".seo/health", help="fingerprint directory")
    ap.add_argument("--limit", type=int, help="cap the number of URLs checked")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--local-root",
                    help="read HTML from this static-build directory instead of "
                         "fetching, when a file matches the URL path")
    ap.add_argument("--expect-schema", action="append", default=[],
                    help="glob of URLs that must carry JSON-LD (repeatable, "
                         "comma-separated accepted)")
    ap.add_argument("--check-links", action="store_true",
                    help="HEAD every internal link target that is not itself in "
                         "the sitemap, and count inbound links per page "
                         "(adds broken/redirecting/orphan findings)")
    ap.add_argument("--keep-text", action="store_true",
                    help="store each page's visible body text on the "
                         "fingerprint (body_text, capped at %d chars) for "
                         "truth_check.py --from-health" % MAX_BODY_TEXT)
    ap.add_argument("--json", action="store_true",
                    help="print the diff report as JSON")
    args = ap.parse_args()

    expect = []
    for g in args.expect_schema:
        expect.extend([x.strip() for x in g.split(",") if x.strip()])

    notes = []
    entries = discover_sitemap(args.sitemap, notes)
    if not entries:
        notes.append("no URLs found in %s" % args.sitemap)

    seen, urls = set(), []
    for loc, lm in entries:
        if loc in seen:
            continue
        seen.add(loc)
        urls.append((loc, lm))
    if args.limit and len(urls) > args.limit:
        notes.append("--limit %d is set (sitemap has %d URLs); any REMOVED URLS "
                     "below are the cap, not a site change" % (args.limit, len(urls)))
        urls = urls[:args.limit]

    base_url = args.base_url
    if not base_url and urls:
        p = urllib.parse.urlsplit(urls[0][0])
        base_url = "%s://%s" % (p.scheme, p.netloc)
    base_host = host_of(base_url or "")

    pages = {}
    workers = max(1, min(args.concurrency, 16))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(fingerprint, u, lm, base_host, args.local_root,
                            args.keep_text): u
                for u, lm in urls}
        for fut in concurrent.futures.as_completed(futs):
            u = futs[fut]
            try:
                pages[u] = fut.result()
            except Exception as ex:  # noqa: BLE001
                pages[u] = {"status": 0, "final_url": u, "redirect_hops": 0,
                            "error": "%s: %s" % (type(ex).__name__, ex),
                            "canonical": None, "title": None,
                            "meta_description": None, "html_lang": None,
                            "h1_count": 0, "jsonld_types": [],
                            "date_published": None, "date_modified": None,
                            "sitemap_lastmod": None, "body_words": 0,
                            "noindex": False, "internal_link_count": 0,
                            "content_hash": None, "ttfb_ms": None,
                            "html_bytes": 0}

    link_graph = {u: (rec.pop("_internal_links", None) or [])
                  for u, rec in pages.items()}
    link_check = None
    if args.check_links:
        link_check = link_pass(pages, link_graph, workers)

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)
    # Read the previous fingerprint before writing today's, so a second run on
    # the same day still diffs against the first one instead of nothing.
    prev_path = previous_file(out_dir)
    prev = None
    if prev_path:
        try:
            with open(prev_path) as fh:
                prev = json.load(fh)
        except Exception as ex:  # noqa: BLE001
            notes.append("could not read %s (%s)" % (prev_path, ex))
            prev_path = None

    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    cur_path = os.path.join(out_dir, "%s.json" % today)
    cur = {
        "generated": datetime.datetime.now(datetime.timezone.utc)
                     .replace(microsecond=0).isoformat(),
        "base_url": base_url,
        "pages": {u: pages[u] for u in sorted(pages)},
    }
    if link_check is not None:
        cur["link_check"] = link_check
    with open(cur_path, "w") as fh:
        json.dump(cur, fh, indent=2, sort_keys=True)
    cur["_path"] = cur_path

    viols = violations(cur["pages"], expect, (prev or {}).get("pages"))
    diff = build_diff(prev, cur)

    if args.json:
        payload = {
            "generated": cur["generated"],
            "base_url": cur["base_url"],
            "current_file": cur_path,
            "previous_file": prev_path,
            "notes": notes,
            "pages": len(cur["pages"]),
            "diff": diff,
            "violations": viols,
            "summary": {"pages": len(cur["pages"]),
                        "changed": diff["changed_count"],
                        "violations": len(viols)},
        }
        if link_check is not None:
            payload["link_check"] = link_check
            payload["summary"]["link_check"] = link_check
        print(json.dumps(payload, indent=2))
        # stderr, so stdout stays valid JSON for a pipe into jq.
        print(summary_text(cur, diff, viols, link_check), file=sys.stderr)
    else:
        print_report(cur, diff, viols, prev_path, notes, link_check)
    return 0


if __name__ == "__main__":
    sys.exit(main())
