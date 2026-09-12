#!/usr/bin/env python3
"""Weekly backlink new/lost panel: raw DataForSEO dumps in, ranked candidates out.

DataForSEO says a link appeared or vanished. It cannot say whether the page it
pointed at still earns clicks, whether the URL it points at now 404s, or whether
a page that talks about the brand ever linked at all. Those are joins against
Search Console and our own site, so this script does them once and writes a
dated snapshot beside last week's, so the domain-level trend prints as one line.

Candidate kinds, in report order:
  lost-link         offpage-brief  lost backlink whose target still earns
                                   clicks/impressions (or is a --priority page)
  inbound-404       repair         live backlink whose target on our site is
                                   not 200 — 301 it to the nearest owner
  unlinked-mention  offpage-brief  page mentioning the brand with no link to us
                                   (DFS has no link flag, so always 'unverified')
  new-link          informational  new backlink; action is 'spam-watch' when the
                                   source has spam_score >= 30 or rank < 5

It is a report, not a gate. It always exits 0.

Usage
  backlink_diff.py --domain https://example.com --backlinks raw/backlinks.json
  backlink_diff.py --domain <d> --backlinks a.json --backlinks b.json \
      --new-lost raw/new_lost.json --mentions raw/mentions.json \
      --brand "Example" --brand "ExampleApp" --gsc .seo/gsc/2026-09-09.json \
      --priority https://example.com/pricing --out .seo/backlinks/2026-09-09.json
  backlink_diff.py ... --json

Inputs (all optional; the report uses whatever is given)
  --backlinks  raw backlinks_backlinks response(s): tasks[0].result[0].items[],
               or a flat list of item dicts
  --new-lost   raw bulk_new_lost_backlinks / timeseries_new_lost_summary; the
               first dict carrying new_backlinks/lost_backlinks is used
  --mentions   raw content_analysis_search response(s)
  --gsc        Search Console page rows ({"rows":[{page|keys, clicks, ...}]})
  <out dir>/<YYYY-MM-DD>.json  the previous run, read for the trend line

Standard library only.
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse

KINDS = ["lost-link", "inbound-404", "unlinked-mention", "new-link"]
ACTIONS = {"lost-link": "offpage-brief", "inbound-404": "repair",
           "unlinked-mention": "offpage-brief", "new-link": "informational"}
SPAM_SCORE_WATCH, LOW_RANK_WATCH, PER_KIND_CAP = 30, 5, 20
SKIP_MENTION_DOMAINS = {
    "reddit.com", "twitter.com", "x.com", "facebook.com", "linkedin.com",
    "youtube.com", "github.com", "instagram.com", "tiktok.com", "pinterest.com",
    "threads.net"}
DATE_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")


# ------------------------------------------------------------------- helpers

def normalise(url):
    try:
        p = urllib.parse.urlsplit((url or "").strip())
    except ValueError:
        return (url or "").strip()
    path = p.path or "/"
    if len(path) > 1:
        path = path.rstrip("/")
    return urllib.parse.urlunsplit(
        (p.scheme.lower(), p.netloc.lower(), path, p.query, ""))


def host_of(url_or_host):
    s = (url_or_host or "").strip().lower()
    if "://" in s:
        s = urllib.parse.urlsplit(s).netloc
    s = s.split("/")[0].split(":")[0]
    return s[4:] if s.startswith("www.") else s


def under(host, parent):
    return bool(host and parent) and (host == parent or host.endswith("." + parent))


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def load_json(path, label, notes):
    if not path:
        return None
    if not os.path.isfile(path):
        notes.append("%s file not found: %s" % (label, path))
        return None
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError) as ex:
        notes.append("could not parse %s (%s): %s" % (label, path, ex))
        return None


def _unwrap(node):
    """Some clients wrap the payload as {"result": "<json string>"}."""
    if isinstance(node, dict):
        for key in ("result", "content", "data", "body", "text"):
            v = node.get(key)
            if isinstance(v, str) and v.lstrip()[:1] in "[{":
                try:
                    return json.loads(v)
                except ValueError:
                    continue
    return node


def find(node, want, as_list, depth=0):
    """Hunt the payload for the first list of dicts (as_list) or the first dict
    whose head rows carry any key in `want`. Covers tasks[0].result[0].items[],
    a bare {"items": [...]}, a flat list, and string-wrapped envelopes."""
    if depth > 8:
        return None
    node = _unwrap(node)
    if isinstance(node, list):
        head = [r for r in node[:5] if isinstance(r, dict)]
        if as_list and head and all(any(k in r for k in want) for r in head):
            return node
        kids = node
    elif isinstance(node, dict):
        if not as_list and any(k in node for k in want):
            return node
        kids = [node[k] for k in ("items", "tasks", "result", "rows", "data")
                if k in node] + list(node.values())
    else:
        return None
    for v in kids:
        got = find(v, want, as_list, depth + 1)
        if got:
            return got
    return None


def load_many(paths, label, want, notes):
    out = []
    for p in paths or []:
        doc = load_json(p, label, notes)
        items = find(doc, want, True) if doc is not None else None
        if doc is not None and not items:
            notes.append("%s: no items found in %s" % (label, p))
        out.extend(r for r in items or [] if isinstance(r, dict))
    return out


def load_gsc(path, notes):
    """{normalised_url: {clicks, impressions}} from a Search Console page pull."""
    out = {}
    for row in load_many([path], "gsc", ("clicks", "impressions"), notes):
        page = row.get("page") or row.get("url") or (row.get("keys") or [None])[0]
        if not page:
            continue
        rec = out.setdefault(normalise(str(page)), {"clicks": 0, "impressions": 0})
        rec["clicks"] += int(row.get("clicks") or 0)
        rec["impressions"] += int(row.get("impressions") or 0)
    return out


def load_previous(out_path, notes):
    """The most recent dated file in the same directory, if any."""
    d = os.path.dirname(os.path.abspath(out_path))
    me = os.path.basename(out_path)
    names = sorted(n for n in (os.listdir(d) if os.path.isdir(d) else [])
                   if DATE_FILE_RE.match(n) and n != me)
    return load_json(os.path.join(d, names[-1]), "previous", notes) if names else None


# ---------------------------------------------------------------- candidates

def candidate(kind, item, url_to, clicks, note, action=None):
    return {
        "kind": kind, "action": action or ACTIONS[kind],
        "url_from": item.get("url_from") or item.get("url"),
        "domain_from": host_of(item.get("domain_from") or item.get("domain")
                               or item.get("url_from") or item.get("url")),
        "url_to": url_to, "status_code": _int(item.get("url_to_status_code")),
        "target_clicks": clicks, "rank": _int(item.get("rank")) or 0,
        "spam_score": _int(item.get("backlink_spam_score")),
        "anchor": item.get("anchor"), "dofollow": item.get("dofollow"),
        "first_seen": (item.get("first_seen") or "")[:10] or None,
        "last_seen": (item.get("last_seen") or "")[:10] or None,
        "note": note}


def classify_backlinks(items, gsc, priority, ours, notes):
    """One candidate per backlink item, or none when it is unremarkable."""
    out, counts, dropped = [], {"new": 0, "lost": 0}, 0
    for it in items:
        src = host_of(it.get("domain_from") or it.get("url_from"))
        if under(src, ours):
            continue
        url_to = normalise(it.get("url_to") or "")
        tgt = gsc.get(url_to) or {}
        clicks, impr = tgt.get("clicks", 0), tgt.get("impressions", 0)
        status = _int(it.get("url_to_status_code"))
        if it.get("is_lost"):
            counts["lost"] += 1
            if url_to in priority:
                why = "a priority page"
            elif not gsc:
                why = "unscored (no --gsc)"
            elif clicks or impr:
                why = "earning %d clicks / %d impressions" % (clicks, impr)
            else:
                dropped += 1
                continue
            out.append(candidate("lost-link", it, url_to, clicks,
                                 "target is %s; ask %s to restore" % (why, src)))
        elif it.get("is_broken") or (status is not None and status != 200):
            out.append(candidate("inbound-404", it, url_to, clicks,
                                 "target returns %s; 301 it to the nearest owner"
                                 % (status if status is not None else "broken")))
        elif it.get("is_new"):
            counts["new"] += 1
            spam, rank = _int(it.get("backlink_spam_score")) or 0, _int(it.get("rank"))
            if spam >= SPAM_SCORE_WATCH or (rank is not None and rank < LOW_RANK_WATCH):
                out.append(candidate("new-link", it, url_to, clicks,
                                     "spam score %d, rank %s; disavow if it grows"
                                     % (spam, rank), action="spam-watch"))
            else:
                out.append(candidate("new-link", it, url_to, clicks, "new %s link, rank %s"
                                     % ("dofollow" if it.get("dofollow") else "nofollow", rank)))
    if dropped:
        notes.append("%d lost link(s) dropped: target has no clicks/impressions "
                     "and is not --priority" % dropped)
    return out, counts


def classify_mentions(items, brands, ours, notes):
    pats = [b.lower() for b in brands if b]
    if items and not pats:
        notes.append("no --brand given: every mention is kept unfiltered")
    mentions, cands, seen = [], [], set()
    for it in items:
        url, host = it.get("url") or "", host_of(it.get("domain") or it.get("main_domain")
                                                 or it.get("url"))
        if not url or url in seen or under(host, ours) or any(
                under(host, d) for d in SKIP_MENTION_DOMAINS):
            continue
        info = it.get("content_info") if isinstance(it.get("content_info"), dict) else {}
        snippet = it.get("snippet") or info.get("snippet") or ""
        text = " ".join(str(x) for x in (it.get("title"), snippet, info.get("main_title"),
                                          info.get("content")) if x).lower()
        if pats and not any(p in text for p in pats):
            continue
        seen.add(url)
        date = (it.get("date_published") or it.get("fetch_time") or "")[:10] or None
        mentions.append({"url": url, "domain": host, "title": it.get("title"),
                         "date": date, "snippet": snippet[:240]})
        c = candidate("unlinked-mention", {"url_from": url, "domain_from": host,
                                           "rank": it.get("rank")}, None, 0,
                      "unverified: fetch the page and confirm no link to %s" % ours)
        c["first_seen"] = c["last_seen"] = date
        cands.append(c)
    return mentions, cands


def summary_from(doc, counts, notes):
    block = find(doc, ("new_backlinks", "lost_backlinks"), False) if doc else None
    if block:
        return {"new_backlinks": _int(block.get("new_backlinks")),
                "lost_backlinks": _int(block.get("lost_backlinks")),
                "new_domains": _int(block.get("new_referring_domains")),
                "lost_domains": _int(block.get("lost_referring_domains")),
                "source": "new-lost"}
    if counts["new"] or counts["lost"]:
        notes.append("summary counted from --backlinks items (no --new-lost)")
        return {"new_backlinks": counts["new"], "lost_backlinks": counts["lost"],
                "new_domains": None, "lost_domains": None, "source": "backlinks"}
    return None


def delta_line(summary, prev):
    ps = (prev or {}).get("summary") if isinstance(prev, dict) else None
    if not summary or not isinstance(ps, dict):
        return None
    parts = ["%s %d -> %d (%+d)" % (label, ps[k], summary[k], summary[k] - ps[k])
             for k, label in (("new_backlinks", "new"), ("lost_backlinks", "lost"))
             if ps.get(k) is not None and summary.get(k) is not None]
    return "vs %s: %s" % (prev.get("date", "previous"), ", ".join(parts)) if parts else None


# -------------------------------------------------------------------- output

def _short(s, width):
    s = s or ""
    return s if len(s) <= width else s[:width - 1] + "…"


def print_report(doc, out_path):
    s = doc["summary"]
    print("Backlinks — %s (%s)" % (doc["domain"] or "(no --domain)", doc["date"]))
    print("  summary: " + ("%s new / %s lost backlinks, %s new / %s lost domains [%s]"
                           % tuple("?" if s[k] is None else s[k] for k in
                                   ("new_backlinks", "lost_backlinks", "new_domains",
                                    "lost_domains", "source")) if s else
                           "n/a (no --new-lost and no flagged --backlinks items)"))
    if doc.get("delta"):
        print("  trend:   %s" % doc["delta"])
    print("  written: %s" % out_path)
    for n in doc["notes"]:
        print("  note: %s" % n)
    by_kind = {}
    for c in doc["candidates"]:
        by_kind.setdefault(c["kind"], []).append(c)
    for kind in KINDS:
        rows = by_kind.get(kind) or []
        if not rows:
            continue
        print("\n%s (%d) -> %s" % (kind.upper(), len(rows), ACTIONS[kind]))
        for c in rows[:PER_KIND_CAP]:
            tgt = urllib.parse.urlsplit(c["url_to"] or "").path or "-"
            flag = "" if c["action"] == ACTIONS[kind] else c["action"].upper() + ": "
            print("  %-44s %-28s %4d clk rank %3d  %s%s"
                  % (_short(c["url_from"], 44), _short(tgt, 28), c["target_clicks"],
                     c["rank"], flag, c["note"]))
        if len(rows) > PER_KIND_CAP:
            print("  …and %d more" % (len(rows) - PER_KIND_CAP))
    print("\nSUMMARY: " + ", ".join("%d %s" % (len(by_kind.get(k) or []), k) for k in KINDS))


# ---------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Turn raw DataForSEO backlink/mention dumps into reclamation, "
                    "repair and outreach candidates. Always exits 0.")
    ap.add_argument("--backlinks", action="append", help="raw backlinks_backlinks JSON")
    ap.add_argument("--new-lost", help="raw new/lost summary JSON (domain-level counts)")
    ap.add_argument("--mentions", action="append", help="raw content_analysis_search JSON")
    ap.add_argument("--gsc", help="Search Console page rows for the current window")
    ap.add_argument("--domain", default="", help="our site, e.g. https://example.com")
    ap.add_argument("--brand", action="append", help="brand name or alias (repeatable)")
    ap.add_argument("--priority", action="append", help="priority page URL (repeatable)")
    ap.add_argument("--out", help="output file (default .seo/backlinks/<today>.json)")
    ap.add_argument("--today", help="override the date (YYYY-MM-DD)")
    ap.add_argument("--json", action="store_true", help="print the object as JSON")
    args = ap.parse_args()

    notes = []
    today = args.today or datetime.date.today().isoformat()
    out_path = args.out or os.path.join(".seo", "backlinks", "%s.json" % today)
    ours = host_of(args.domain)
    if not ours:
        notes.append("no --domain: self-links and own-domain mentions cannot be skipped")

    backlinks = load_many(args.backlinks, "backlinks", ("url_from", "domain_from"), notes)
    mentions_raw = load_many(args.mentions, "mentions", ("url", "main_domain"), notes)
    gsc = load_gsc(args.gsc, notes) if args.gsc else {}
    if args.gsc and not gsc:
        notes.append("gsc: no page rows loaded from %s" % args.gsc)
    priority = {normalise(p) for p in (args.priority or [])}

    cands, counts = classify_backlinks(backlinks, gsc, priority, ours, notes)
    mentions, mention_cands = classify_mentions(mentions_raw, args.brand or [], ours, notes)
    cands.extend(mention_cands)
    cands.sort(key=lambda c: (KINDS.index(c["kind"]), -c["target_clicks"], -c["rank"],
                              c["url_from"] or ""))

    summary = summary_from(load_json(args.new_lost, "new-lost", notes), counts, notes)
    prev = load_previous(out_path, notes)
    doc = {"date": today, "domain": ours or None, "summary": summary,
           "delta": delta_line(summary, prev), "candidates": cands,
           "mentions": mentions, "notes": notes}

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(doc, fh, indent=2)
    if args.json:
        print(json.dumps(doc, indent=2))
    else:
        print_report(doc, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
