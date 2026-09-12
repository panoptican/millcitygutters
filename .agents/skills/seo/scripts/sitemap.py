#!/usr/bin/env python3
"""Fetch and flatten a site's XML sitemaps into a URL list.

Shared by robots_check.py (llms.txt cross-reference) and depth_check.py (orphan
detection).

Reads a sitemap index one level deep. Skips gzipped children and says so in the
notes, because silently returning fewer URLs turns an orphan report into a list
of false positives.

Standard library only.
"""

import re
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; aeo-skill-sitemap/1.0)"
TIMEOUT = 20
MAX_CHILDREN = 5
MAX_URLS = 5000


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:  # noqa: BLE001
        return None, ""


def _locs(xml):
    return [m.strip() for m in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml, re.I)]


def normalise(url):
    """Canonical form for comparing two URLs. Drops the fragment and a trailing slash."""
    try:
        p = urllib.parse.urlsplit(url.strip())
    except ValueError:
        return url.strip()
    path = p.path or "/"
    if len(path) > 1:
        path = path.rstrip("/")
    return urllib.parse.urlunsplit(
        (p.scheme.lower(), p.netloc.lower(), path, p.query, "")
    )


def from_robots(root):
    """Sitemap: lines in robots.txt. The only declaration that is not a guess."""
    st, body = _get(root.rstrip("/") + "/robots.txt")
    if st != 200:
        return []
    return [m.strip() for m in
            re.findall(r"^\s*sitemap\s*:\s*(\S+)", body, re.I | re.M)]


def collect(root, candidates=None):
    """Return {'urls', 'sources', 'notes', 'truncated'} for a site root."""
    root = root.rstrip("/")
    # robots.txt first, because a declared sitemap beats a guessed filename. Sites
    # using sitemap-index.xml, /sitemap/, or a CDN-hosted sitemap are invisible to
    # a guess and produce a silent "no sitemap" that reads as a finding.
    tried = candidates or (from_robots(root) +
                           [root + "/sitemap.xml", root + "/sitemap_index.xml",
                            root + "/sitemap-index.xml"])
    out = {"urls": [], "sources": [], "notes": [], "truncated": False}
    seen = set()

    index_xml, index_url = None, None
    for cand in tried:
        st, body = _get(cand)
        if st == 200 and "<loc" in body.lower():
            index_xml, index_url = body, cand
            break
    if index_xml is None:
        out["notes"].append("no sitemap found at %s" % " or ".join(tried))
        return out

    out["sources"].append(index_url)

    if "<sitemapindex" in index_xml[:2000].lower():
        children = _locs(index_xml)
        for child in children[:MAX_CHILDREN]:
            if child.endswith(".gz"):
                out["notes"].append("skipped gzipped sitemap %s" % child)
                continue
            st, body = _get(child)
            if st != 200:
                out["notes"].append("child sitemap %s returned %s" % (child, st))
                continue
            out["sources"].append(child)
            for u in _locs(body):
                if u not in seen:
                    seen.add(u)
                    out["urls"].append(u)
        if len(children) > MAX_CHILDREN:
            out["truncated"] = True
            out["notes"].append(
                "sitemap index lists %d children, read the first %d"
                % (len(children), MAX_CHILDREN))
    else:
        for u in _locs(index_xml):
            if u not in seen:
                seen.add(u)
                out["urls"].append(u)

    if len(out["urls"]) > MAX_URLS:
        out["urls"] = out["urls"][:MAX_URLS]
        out["truncated"] = True
        out["notes"].append("truncated to the first %d URLs" % MAX_URLS)
    return out
