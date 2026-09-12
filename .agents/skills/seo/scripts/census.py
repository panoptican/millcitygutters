#!/usr/bin/env python3
"""Whole-inventory content census: every URL gets a verdict, and a time series.

A page-by-page audit tells you about the page you are looking at. It cannot tell
you that 40% of the site has never received an impression, that the pages you
shipped in March have quietly flatlined, or that two of them are eating each
other's rankings. Those are portfolio facts, and they only show up when you join
the whole inventory against demand and keep the answer around for months.

So this script joins three things — the health fingerprint (what exists), Search
Console (what demand reaches it), and the content ledger (when it shipped and
what type it is) — assigns every URL one verdict, and writes a dated snapshot.
Decay ("this used to get clicks"), staleness ("nothing has changed here in a
year") and durable invisibility ("still zero, 90 days later") are all
cross-snapshot facts, so they need yesterday's file to be readable today.

It is a report, not a gate. It always exits 0.

Usage
  census.py --health .seo/health/2026-09-09.json --gsc .seo/gsc/2026-09-09.json
  census.py --health <h> --gsc <cur> --gsc-prev <older> --ledger .seo/content-ledger.md
  census.py --health <h> --gsc <cur> --out .seo/census --min-age-days 21 --json

Inputs
  --health    health_diff.py fingerprint: {generated, base_url, pages: {url: {...}}}
  --gsc       Search Console page rows. Either
                {"site_url":…, "start_date":…, "end_date":…, "rows":[…]}
              or the raw shape an MCP/API client hands back — the loader hunts
              for the first list of row dicts carrying page/keys + clicks, and
              unwraps a JSON-string "result" envelope if it finds one.
  --gsc-prev  the same shape for the prior window (enables click_trend + decay).
  --ledger    markdown; the shipped table is read leniently for per-slug date
              and type. Optional.
  <out>/<YYYY-MM-DD>.json   previous censuses, read for the trend fields.

age_days resolves in this order, and the source is recorded on each row:
  date_published (JSON-LD) -> sitemap_lastmod -> ledger date -> first census
  that saw the URL. A URL first seen today with no other date has age 0, which
  is why rule 1 exists: unknown age reads as young, and young is not judged.

Standard library only.
"""

import argparse
import datetime
import json
import math
import os
import re
import statistics
import sys
import urllib.parse

DATE_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")

# Verdicts, in report order. Order is also the rule order in verdict_for().
VERDICTS = ["broken", "prune-candidate", "merge-candidate", "refresh",
            "invisible", "watch", "keep"]

# Dropped from title stems and slug stems before comparing two pages. Without
# this every "how to …" page collides with every other one.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "does", "for",
    "from", "how", "in", "into", "is", "it", "its", "my", "of", "on", "or",
    "our", "that", "the", "their", "this", "to", "up", "us", "was", "what",
    "when", "where", "which", "who", "why", "will", "with", "you", "your",
}

# Health fingerprints count OUTBOUND internal links, which says nothing about
# how well linked a page is. Only a real inbound measure fills inbound_links.
INBOUND_KEYS = ("inbound_link_count", "inbound_links", "internal_inbound_links",
                "inlinks")

THIN_WORDS = 300
STRIKING_MIN_POS, STRIKING_MAX_POS = 5.0, 20.0
STRIKING_MIN_IMPRESSIONS = 100
DECAY_PCT = -30.0
DECAY_MIN_PREV_CLICKS = 10
STALE_AGE_DAYS = 365
PRUNE_AGE_DAYS = 90
PRUNE_REPEAT_GAP_DAYS = 90
INVISIBLE_AGE_DAYS = 90
INVISIBLE_IMPRESSIONS = 10
MERGE_MAX_IMPRESSIONS = 50
WINNING_POSITION = 10.0

# Expected organic CTR by average position. Blended across query types and
# deliberately conservative: the point is to catch a page earning a fraction of
# what its rank should earn, not to predict clicks. A SERP with an AI Overview
# or a pack above it will read low here and be nobody's fault — the rule is a
# prompt to look at the title and snippet, not a verdict on them.
CTR_CURVE = [(1, 0.28), (2, 0.15), (3, 0.11), (4, 0.08), (5, 0.07), (6, 0.05),
             (7, 0.04), (8, 0.035), (9, 0.03), (10, 0.025), (15, 0.015),
             (20, 0.01)]
CTR_FLOOR = 0.005
CTR_MIN_IMPRESSIONS = 100
LOW_CTR_GAP = 0.5
SLOW_TTFB_MS = 1000
LOW_INBOUND = 2


# ---------------------------------------------------------------- url helpers

def normalise(url):
    """Lowercase scheme+host, drop the fragment, drop one trailing slash.

    GSC reports canonical URLs and sitemaps often carry a different trailing
    slash convention, so the join has to happen on a normalised key or half the
    inventory silently shows zero traffic."""
    try:
        p = urllib.parse.urlsplit((url or "").strip())
    except ValueError:
        return (url or "").strip()
    path = p.path or "/"
    if len(path) > 1:
        path = path.rstrip("/")
    return urllib.parse.urlunsplit(
        (p.scheme.lower(), p.netloc.lower(), path, p.query, ""))


def path_of(url):
    try:
        p = urllib.parse.urlsplit(url).path or "/"
    except ValueError:
        return "/"
    return p if len(p) == 1 else p.rstrip("/")


def last_segment(url):
    seg = path_of(url).rstrip("/").rsplit("/", 1)[-1]
    return seg or "(root)"


def words(text):
    return [w for w in re.split(r"[^a-z0-9]+", (text or "").lower()) if w]


def significant(seq, n):
    out = [w for w in seq if w not in STOPWORDS and len(w) > 1]
    return out[:n]


def title_stem(title):
    """First 5 significant words of the title, brand suffix removed.

    Titles almost always end in a separator plus the site name, and comparing
    that would match every page against every other page."""
    if not title:
        return None
    head = re.split(r"\s+[|—–·•]\s+", title)[0]
    stem = significant(words(head), 5)
    return " ".join(stem) if len(stem) >= 2 else None


def slug_stem(url):
    """First 3 significant words of the last path segment."""
    stem = significant(words(last_segment(url)), 3)
    return " ".join(stem) if len(stem) >= 2 else None


# ------------------------------------------------------------------ date math

def parse_date(value):
    """A date out of an ISO timestamp, a bare date, or an RFC-ish string."""
    if not value:
        return None
    v = str(value).strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    for attempt in (v, v[:10]):
        try:
            d = datetime.datetime.fromisoformat(attempt)
            return d.date()
        except ValueError:
            continue
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", v)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)),
                                 int(m.group(3)))
        except ValueError:
            return None
    return None


def expected_ctr(position):
    """Expected CTR for an average position, or None when position is unknown."""
    if position is None:
        return None
    try:
        pos = float(position)
    except (TypeError, ValueError):
        return None
    for edge, ctr in CTR_CURVE:
        if pos <= edge:
            return ctr
    return CTR_FLOOR


def days_between(then, now):
    if then is None:
        return None
    return (now - then).days


# ------------------------------------------------------------------- loading

def load_json(path, label):
    with open(path) as fh:
        raw = fh.read()
    try:
        return json.loads(raw)
    except ValueError as ex:
        raise SystemExit("could not parse %s (%s): %s" % (label, path, ex))


def _unwrap(node, depth=0):
    """Some clients wrap the payload as {"result": "<json string>"}."""
    if depth > 4:
        return node
    if isinstance(node, dict):
        for key in ("result", "content", "data", "body", "text"):
            v = node.get(key)
            if isinstance(v, str) and v.lstrip()[:1] in "[{":
                try:
                    return _unwrap(json.loads(v), depth + 1)
                except ValueError:
                    continue
    return node


def _row_page(row):
    page = row.get("page") or row.get("url") or row.get("Page")
    if page:
        return str(page)
    keys = row.get("keys")
    if isinstance(keys, list) and keys:
        return str(keys[0])
    return None


def _looks_like_rows(node):
    if not isinstance(node, list) or not node:
        return False
    head = [r for r in node[:5] if isinstance(r, dict)]
    if not head:
        return False
    return all(_row_page(r) is not None and
               ("clicks" in r or "impressions" in r) for r in head)


def find_rows(node, depth=0):
    """Hunt for the row list anywhere in the payload, breadth-first-ish."""
    if depth > 6:
        return None
    node = _unwrap(node, depth)
    if _looks_like_rows(node):
        return node
    if isinstance(node, dict):
        for key in ("rows", "results", "data", "pages"):
            if key in node:
                got = find_rows(node[key], depth + 1)
                if got:
                    return got
        for v in node.values():
            if isinstance(v, (dict, list)):
                got = find_rows(v, depth + 1)
                if got:
                    return got
    elif isinstance(node, list):
        for v in node:
            if isinstance(v, (dict, list)):
                got = find_rows(v, depth + 1)
                if got:
                    return got
    return None


def load_gsc(path, label, notes):
    """{normalised_url: {clicks, impressions, ctr, position}} plus window dates."""
    if not path:
        return {}, {}
    if not os.path.isfile(path):
        notes.append("%s file not found: %s" % (label, path))
        return {}, {}
    payload = _unwrap(load_json(path, label))
    rows = find_rows(payload)
    if rows is None:
        notes.append("%s: no page rows found in %s" % (label, path))
        return {}, {}

    meta = {}
    if isinstance(payload, dict):
        rng = payload.get("date_range") if isinstance(
            payload.get("date_range"), dict) else {}
        meta = {
            "site_url": payload.get("site_url"),
            "start_date": payload.get("start_date") or rng.get("start"),
            "end_date": payload.get("end_date") or rng.get("end"),
            "rows": len(rows),
        }
    else:
        meta = {"rows": len(rows)}

    out = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        page = _row_page(row)
        if not page:
            continue
        key = normalise(page)
        rec = out.setdefault(key, {"clicks": 0, "impressions": 0,
                                   "ctr": None, "position": None})
        rec["clicks"] += int(row.get("clicks") or 0)
        rec["impressions"] += int(row.get("impressions") or 0)
        # Position is an average; on a duplicate key keep the first, which is
        # the higher-impression row because GSC sorts that way.
        if rec["position"] is None and row.get("position") is not None:
            try:
                rec["position"] = float(row["position"])
            except (TypeError, ValueError):
                pass
        if rec["ctr"] is None and row.get("ctr") is not None:
            try:
                rec["ctr"] = float(row["ctr"])
            except (TypeError, ValueError):
                pass
    return out, meta


LEDGER_ROW_RE = re.compile(r"^\|(.+)\|\s*$")


def load_ledger(path, notes):
    """{normalised_path: {date, type}} from the shipped markdown table.

    Deliberately lenient: the ledger is hand-maintained prose with tables in it,
    so anything that is not a pipe row with a date and a path is skipped rather
    than treated as a parse failure."""
    if not path:
        return {}
    if not os.path.isfile(path):
        notes.append("ledger not found: %s" % path)
        return {}
    out = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as ex:
        notes.append("could not read ledger (%s)" % ex)
        return {}

    for line in lines:
        m = LEDGER_ROW_RE.match(line.rstrip("\n"))
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if len(cells) < 3:
            continue
        date = parse_date(cells[0]) if re.match(r"^\d{4}-\d{2}-\d{2}", cells[0]) \
            else None
        if date is None:
            continue
        slug = None
        for cell in cells[1:]:
            hit = re.search(r"`\s*(/[^`\s]*)\s*`", cell)
            if hit:
                slug = hit.group(1)
                break
            hit = re.search(r"https?://[^\s)\]]+", cell)
            if hit:
                slug = path_of(hit.group(0))
                break
        if not slug:
            continue
        key = slug if len(slug) == 1 else slug.rstrip("/")
        kind = cells[2] if len(cells) > 2 else None
        prev = out.get(key)
        # Keep the earliest date: the ledger can list a piece twice (shipped,
        # then refreshed) and age is measured from first publication.
        if prev is None or (prev.get("date") and date < prev["date"]):
            out[key] = {"date": date, "type": kind or None}
    return out


def load_history(out_dir, today_name, notes):
    """[(date, {url: record})] for every prior census, oldest first."""
    hist = []
    if not os.path.isdir(out_dir):
        return hist
    for name in sorted(os.listdir(out_dir)):
        if not DATE_FILE_RE.match(name) or name == today_name:
            continue
        path = os.path.join(out_dir, name)
        try:
            with open(path) as fh:
                doc = json.load(fh)
        except Exception as ex:  # noqa: BLE001
            notes.append("skipped unreadable census %s (%s)" % (path, ex))
            continue
        pages = doc.get("pages")
        if isinstance(pages, list):
            pages = {p.get("url"): p for p in pages if isinstance(p, dict)}
        if not isinstance(pages, dict):
            continue
        d = parse_date(name[:10])
        if d is None:
            continue
        hist.append((d, {normalise(u): r for u, r in pages.items() if u}))
    return hist


# ------------------------------------------------------------------- verdicts

def pct_change(cur, prev):
    if prev is None or prev == 0:
        return None
    return round((cur - prev) * 100.0 / float(prev), 1)


def build_records(health, gsc, gsc_prev, ledger, history, today, min_age_days,
                  notes):
    pages = health.get("pages") or {}
    inbound_key = None
    for rec in pages.values():
        if not isinstance(rec, dict):
            continue
        for k in INBOUND_KEYS:
            if k in rec:
                inbound_key = k
                break
        if inbound_key:
            break
    if inbound_key is None:
        notes.append("health file carries no inbound-link measure "
                     "(internal_link_count is outbound), so inbound_links is null")

    hist_by_url = {}
    for d, snap in history:
        for u, r in snap.items():
            hist_by_url.setdefault(u, []).append((d, r))

    records = {}
    for url, page in sorted(pages.items()):
        if not isinstance(page, dict):
            continue
        key = normalise(url)
        cur = gsc.get(key) or {}
        prev = gsc_prev.get(key) or {}
        led = ledger.get(path_of(url)) or {}
        hist = hist_by_url.get(key) or []

        clicks = int(cur.get("clicks") or 0)
        impressions = int(cur.get("impressions") or 0)
        position = cur.get("position")
        clicks_prev = int(prev.get("clicks") or 0) if gsc_prev else None
        impressions_prev = int(prev.get("impressions") or 0) if gsc_prev else None

        # Computed from the totals rather than trusting the reported ctr, which
        # is a per-row average and goes wrong the moment two rows merge onto one
        # normalised URL.
        if impressions:
            ctr = round(clicks / float(impressions), 5)
        elif cur.get("ctr") is not None:
            ctr = round(float(cur["ctr"]), 5)
        else:
            ctr = None
        exp_ctr = expected_ctr(position)
        ctr_gap = None
        if (impressions >= CTR_MIN_IMPRESSIONS and ctr is not None
                and exp_ctr):
            ctr_gap = round(ctr / exp_ctr, 3)

        published = parse_date(page.get("date_published"))
        age_source = "date_published"
        if published is None:
            published = parse_date(page.get("sitemap_lastmod"))
            age_source = "sitemap_lastmod"
        if published is None and led.get("date"):
            published = led["date"]
            age_source = "ledger"
        first_seen = hist[0][0] if hist else today
        if published is None:
            published = first_seen
            age_source = "first_seen"
        age_days = max(0, days_between(published, today) or 0)

        last_hash = None
        for _, r in reversed(hist):
            if r.get("content_hash") is not None:
                last_hash = r.get("content_hash")
                break
        content_hash = page.get("content_hash")
        hash_changed = (bool(last_hash) and bool(content_hash)
                        and last_hash != content_hash)

        records[key] = {
            "url": url,
            "status": page.get("status"),
            "title": page.get("title"),
            "canonical": page.get("canonical"),
            "final_url": page.get("final_url"),
            "body_words": int(page.get("body_words") or 0),
            "age_days": age_days,
            "age_source": age_source,
            "ledger_type": led.get("type"),
            "clicks_28": clicks,
            "impressions_28": impressions,
            "position_28": position,
            "ctr_28": ctr,
            "expected_ctr": exp_ctr,
            "ctr_gap": ctr_gap,
            "ttfb_ms": page.get("ttfb_ms"),
            "clicks_prev": clicks_prev,
            "impressions_prev": impressions_prev,
            "click_trend": (pct_change(clicks, clicks_prev)
                            if gsc_prev else None),
            "inbound_links": (page.get(inbound_key) if inbound_key else None),
            "content_hash": content_hash,
            "content_hash_changed_since_last_census": hash_changed,
            "first_seen": first_seen.isoformat(),
            "snapshots": len(hist),
            "verdict": None,
            "reasons": [],
        }
    return records, hist_by_url


def sibling_index(records):
    """{stem_key: [urls]} over 200-status pages, for the cannibalization check."""
    idx = {}
    for key, r in records.items():
        if r["status"] != 200:
            continue
        for stem in (title_stem(r.get("title")), slug_stem(r["url"])):
            if stem:
                idx.setdefault(stem, []).append(key)
    return {k: v for k, v in idx.items() if len(v) > 1}


def canonical_mismatch(rec):
    can = rec.get("canonical")
    if not can:
        return "no canonical"
    if normalise(can) != normalise(rec.get("final_url") or rec["url"]):
        return "canonical %s != %s" % (can, rec.get("final_url") or rec["url"])
    return None


def inbound_suffix(rec):
    """' and only N inbound links', when a real inbound measure is present.

    A page with no demand and no internal links has an obvious first move that
    is not rewriting it, so the count belongs on the reason line rather than in
    a column nobody reads."""
    n = rec.get("inbound_links")
    if isinstance(n, int) and n < LOW_INBOUND:
        return " and only %d inbound link%s" % (n, "" if n == 1 else "s")
    return ""


def assign_verdicts(records, hist_by_url, siblings, today, min_age_days,
                    have_prev):
    for key, r in records.items():
        reasons = []

        # 1. too young to judge. A page with no date evidence at all lands
        # here too, because first_seen is today on a cold start — say so, or
        # 100+ pages read as "new" when they are only undated.
        if r["age_days"] < min_age_days:
            if r["age_source"] == "first_seen" and r["snapshots"] == 0:
                reasons.append("age unknown (no datePublished, no sitemap "
                               "lastmod, no ledger date) and this is the first "
                               "census — judged from the next run on")
            else:
                reasons.append("age %dd < min-age %dd (too young to judge)"
                               % (r["age_days"], min_age_days))
            if r["status"] != 200:
                reasons.append("also: status %s" % r["status"])
            r["verdict"] = "watch"
            r["reasons"] = reasons
            continue

        # 2. broken
        if r["status"] != 200:
            reasons.append("status %s" % r["status"])
            r["verdict"] = "broken"
            r["reasons"] = reasons
            continue
        mismatch = canonical_mismatch(r)
        if mismatch:
            reasons.append(mismatch)
            r["verdict"] = "broken"
            r["reasons"] = reasons
            continue

        # 3. prune
        thin_invisible = (r["impressions_28"] == 0
                          and (r["clicks_prev"] or 0) == 0
                          and r["age_days"] >= PRUNE_AGE_DAYS
                          and r["body_words"] < THIN_WORDS)
        if thin_invisible:
            reasons.append("0 impressions, %d words, %dd old — thin and invisible"
                           % (r["body_words"], r["age_days"]))
        repeat = None
        if r["impressions_28"] == 0:
            for d, old in hist_by_url.get(key, []):
                gap = (today - d).days
                if gap >= PRUNE_REPEAT_GAP_DAYS and old.get("impressions_28") == 0:
                    repeat = (d, gap)
                    break
        if repeat:
            reasons.append("0 impressions here and in the %s census (%dd apart)"
                           % (repeat[0].isoformat(), repeat[1]))
        if thin_invisible or repeat:
            reasons[0] += inbound_suffix(r)
            r["verdict"] = "prune-candidate"
            r["reasons"] = reasons
            continue

        # 4. merge (naive cannibalization)
        if r["impressions_28"] < MERGE_MAX_IMPRESSIONS:
            for stem, members in siblings.items():
                if key not in members:
                    continue
                peers = [m for m in members
                         if m != key
                         and records[m]["impressions_28"] < MERGE_MAX_IMPRESSIONS]
                if not peers:
                    continue
                shown = ", ".join(path_of(records[p]["url"]) for p in peers[:3])
                more = "" if len(peers) <= 3 else " (+%d more)" % (len(peers) - 3)
                reasons.append("shares stem %r with %s%s; both under %d impressions"
                               % (stem, shown, more, MERGE_MAX_IMPRESSIONS))
                break
        if reasons:
            r["verdict"] = "merge-candidate"
            r["reasons"] = reasons
            continue

        # 5. refresh
        pos = r["position_28"]
        # Low CTR is listed before striking distance deliberately: rewriting a
        # title and description is hours, earning a position is months, and a
        # page already getting impressions is being seen and not chosen.
        if (r["impressions_28"] >= CTR_MIN_IMPRESSIONS
                and r["ctr_gap"] is not None and r["ctr_gap"] < LOW_CTR_GAP
                and (r.get("position_28") is None or r["position_28"] <= 20)):
            reasons.append("CTR %.1f%% vs %.1f%% expected at position %.1f on "
                           "%d impressions: title/snippet"
                           % ((r["ctr_28"] or 0) * 100,
                              (r["expected_ctr"] or 0) * 100,
                              pos if pos is not None else 0.0,
                              r["impressions_28"]))
        if (pos is not None and STRIKING_MIN_POS <= pos <= STRIKING_MAX_POS
                and r["impressions_28"] >= STRIKING_MIN_IMPRESSIONS):
            reasons.append("striking distance: position %.1f on %d impressions"
                           % (pos, r["impressions_28"]))
        if (have_prev and r["click_trend"] is not None
                and r["click_trend"] <= DECAY_PCT
                and (r["clicks_prev"] or 0) >= DECAY_MIN_PREV_CLICKS):
            reasons.append("decay: clicks %d -> %d (%+.0f%%)"
                           % (r["clicks_prev"], r["clicks_28"], r["click_trend"]))
        if r["age_days"] >= STALE_AGE_DAYS and r["snapshots"] >= 2:
            hashes = {h.get("content_hash") for _, h in hist_by_url.get(key, [])
                      if h.get("content_hash")}
            if r["content_hash"] and hashes and hashes == {r["content_hash"]}:
                reasons.append("stale: %dd old, unchanged across all %d censuses"
                               % (r["age_days"], r["snapshots"] + 1))
        if reasons:
            r["verdict"] = "refresh"
            r["reasons"] = reasons
            continue

        # 6. invisible
        if (r["impressions_28"] < INVISIBLE_IMPRESSIONS
                and r["age_days"] >= INVISIBLE_AGE_DAYS):
            reasons.append("%d impressions in 28d at %dd old — no demand "
                           "reaching it%s"
                           % (r["impressions_28"], r["age_days"],
                              inbound_suffix(r)))
            r["verdict"] = "invisible"
            r["reasons"] = reasons
            continue

        # 7. keep
        if (pos is not None and pos <= WINNING_POSITION and r["clicks_28"] > 0):
            reasons.append("winning: position %.1f, %d clicks"
                           % (pos, r["clicks_28"]))
        else:
            reasons.append("%d impressions, %d clicks"
                           % (r["impressions_28"], r["clicks_28"]))
        r["verdict"] = "keep"
        r["reasons"] = reasons


# ------------------------------------------------------------------ portfolio

def vitals_stats(records, link_check=None):
    """Speed, CTR and link health for the whole inventory, in one block.

    Each line answers a different 'why isn't this working' — the page is slow,
    the page is seen and not clicked, nothing links to the page — and none of
    them show up in a per-page audit."""
    rows = list(records.values())

    ttfbs = [r["ttfb_ms"] for r in rows
             if isinstance(r.get("ttfb_ms"), (int, float))]
    median_ttfb = int(statistics.median(ttfbs)) if ttfbs else None
    slow_pages = (sum(1 for t in ttfbs if t > SLOW_TTFB_MS) if ttfbs else None)

    total_clicks = sum(r["clicks_28"] for r in rows)
    total_impr = sum(r["impressions_28"] for r in rows)
    site_ctr = round(total_clicks / float(total_impr), 5) if total_impr else None

    scored = [r for r in rows if r.get("ctr_gap") is not None
              and r["impressions_28"] >= CTR_MIN_IMPRESSIONS]
    weight = sum(r["impressions_28"] for r in scored)
    weighted_gap = (round(sum(r["ctr_gap"] * r["impressions_28"] for r in scored)
                          / float(weight), 3) if weight else None)
    low_ctr_pages = sum(1 for r in scored if r["ctr_gap"] < LOW_CTR_GAP
                        and (r.get("position_28") is None or r["position_28"] <= 20))

    known_inbound = [r for r in rows if isinstance(r.get("inbound_links"), int)]
    orphan_pages = (sum(1 for r in known_inbound if r["inbound_links"] == 0)
                    if known_inbound else None)

    return {
        "median_ttfb_ms": median_ttfb,
        "slow_pages": slow_pages,
        "slow_ttfb_ms_threshold": SLOW_TTFB_MS,
        "site_ctr": site_ctr,
        "ctr_weighted_gap": weighted_gap,
        "ctr_scored_pages": len(scored),
        "low_ctr_pages": low_ctr_pages,
        "orphan_pages": orphan_pages,
        "link_check": link_check,
    }


def portfolio_stats(records, min_age_days, link_check=None):
    rows = list(records.values())
    total = len(rows)
    counts = {v: 0 for v in VERDICTS}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    live = [r for r in rows if r["status"] == 200]
    judged = [r for r in live if r["age_days"] >= min_age_days]
    dark = [r for r in judged if r["verdict"] in ("invisible", "prune-candidate")]
    invisible_share = (round(len(dark) / float(len(judged)), 3)
                       if judged else None)
    thin = [r for r in live if r["body_words"] < THIN_WORDS]
    thin_share = round(len(thin) / float(len(live)), 3) if live else None

    ages = [r["age_days"] for r in rows if r["age_days"] is not None]
    median_age = int(statistics.median(ages)) if ages else None
    age_sources = {}
    for r in rows:
        age_sources[r["age_source"]] = age_sources.get(r["age_source"], 0) + 1
    unknown_age = sum(1 for r in rows
                      if r["age_source"] == "first_seen" and r["snapshots"] == 0)

    clicks = sorted((r["clicks_28"] for r in rows), reverse=True)
    total_clicks = sum(clicks)
    top_n = max(1, int(math.ceil(len(clicks) * 0.10))) if clicks else 0
    concentration = (round(sum(clicks[:top_n]) / float(total_clicks), 3)
                     if total_clicks else None)

    prune_share = (counts.get("prune-candidate", 0) / float(total)
                   if total else 0.0)
    gate, reason = False, "portfolio is healthy enough to keep creating"
    if invisible_share is not None and invisible_share > 0.40:
        gate = True
        reason = ("%.0f%% of judged pages are invisible or prune-candidates — "
                  "fix distribution before adding more" % (invisible_share * 100))
    elif prune_share > 0.10:
        gate = True
        reason = ("%.0f%% of pages are prune-candidates — clean up before "
                  "adding more" % (prune_share * 100))

    return {
        "total_pages": total,
        "live_pages": len(live),
        "judged_pages": len(judged),
        "counts": counts,
        "invisible_share": invisible_share,
        "invisible_share_denominator": len(judged),
        "thin_share": thin_share,
        "thin_pages": len(thin),
        "median_age_days": median_age,
        "age_sources": age_sources,
        "unknown_age_pages": unknown_age,
        "total_clicks_28": total_clicks,
        "clicks_concentration_top_decile": concentration,
        "top_decile_pages": top_n,
        "prune_share": round(prune_share, 3),
        "create_gate": gate,
        "create_gate_reason": reason,
        "vitals": vitals_stats(records, link_check),
    }


# --------------------------------------------------------------------- output

def _short(url, width=76):
    s = path_of(url) or url
    return s if len(s) <= width else s[:width - 1] + "…"


def print_report(records, stats, meta, notes, out_path, md_path):
    print("Content census — %s" % (meta.get("base_url") or "(unknown site)"))
    print("  health:   %s" % meta.get("health_path"))
    print("  gsc:      %s%s" % (meta.get("gsc_path"), meta.get("gsc_window", "")))
    print("  gsc prev: %s%s" % (meta.get("gsc_prev_path") or "(none — no "
                                "click_trend, no decay rule)",
                                meta.get("gsc_prev_window", "")))
    print("  history:  %d prior census snapshot(s)" % meta.get("history", 0))
    print("  written:  %s and %s" % (out_path, md_path))
    for n in notes:
        print("  note: %s" % n)
    print("")

    by_verdict = {}
    for r in records.values():
        by_verdict.setdefault(r["verdict"], []).append(r)

    for verdict in VERDICTS:
        rows = by_verdict.get(verdict) or []
        if not rows:
            continue
        rows.sort(key=lambda r: (-r["impressions_28"], r["url"]))
        print("%s (%d)" % (verdict.upper(), len(rows)))
        for r in rows[:25]:
            print("  %-58s %6d imp %4d clk  %s"
                  % (_short(r["url"], 58), r["impressions_28"], r["clicks_28"],
                     r["reasons"][0] if r["reasons"] else ""))
        if len(rows) > 25:
            print("  …and %d more" % (len(rows) - 25))
        print("")

    print("PORTFOLIO")
    print("  total pages          %d (%d live 200s, %d old enough to judge)"
          % (stats["total_pages"], stats["live_pages"], stats["judged_pages"]))
    for v in VERDICTS:
        print("  %-20s %d" % (v, stats["counts"].get(v, 0)))
    print("  invisible_share      %s (invisible+prune over %d judged pages)"
          % (_pct(stats["invisible_share"]), stats["invisible_share_denominator"]))
    print("  thin_share           %s (%d pages under %d words)"
          % (_pct(stats["thin_share"]), stats["thin_pages"], THIN_WORDS))
    print("  median age           %s days (from %s)"
          % (stats["median_age_days"],
             ", ".join("%s=%d" % (k, v)
                       for k, v in sorted(stats["age_sources"].items(),
                                          key=lambda kv: -kv[1]))))
    if stats["unknown_age_pages"]:
        print("  undated pages        %d have no publish date anywhere and no "
              "census history — they are 'watch' by default until the next run"
              % stats["unknown_age_pages"])
    print("  clicks concentration %s of %d clicks from the top %d pages"
          % (_pct(stats["clicks_concentration_top_decile"]),
             stats["total_clicks_28"], stats["top_decile_pages"]))
    print("  create_gate          %s — %s"
          % (stats["create_gate"], stats["create_gate_reason"]))
    print_vitals(stats.get("vitals") or {})
    print("")
    print(summary_line(stats))


def print_vitals(v):
    if not v:
        return
    print("")
    print("  VITALS")
    if v.get("median_ttfb_ms") is None:
        print("    speed:     no TTFB in the health file (re-run health_diff.py)")
    else:
        print("    speed:     median TTFB %d ms, %d page(s) over %d ms"
              % (v["median_ttfb_ms"], v.get("slow_pages") or 0,
                 v.get("slow_ttfb_ms_threshold") or 1000))
    print("    relevance: judged in select (answer owner, intent owner, seeds)")
    if v.get("site_ctr") is None:
        # Three n/a's in a row read as a broken script. They are usually a
        # broken --gsc path instead, so say which.
        print("    ctr:       no Search Console impressions in the window — "
              "nothing to judge (check --gsc)")
    else:
        print("    ctr:       site %s, impression-weighted gap %s, "
              "%d page(s) under %.0f%% of expected"
              % (_ctr(v.get("site_ctr")),
                 "n/a" if v.get("ctr_weighted_gap") is None
                 else "%.2fx" % v["ctr_weighted_gap"],
                 v.get("low_ctr_pages") or 0, LOW_CTR_GAP * 100))
    lc = v.get("link_check") or {}
    if lc:
        print("    links:     %d broken, %d redirecting (of %d off-sitemap "
              "targets), %s orphan page(s)"
              % (lc.get("broken") or 0, lc.get("redirecting") or 0,
                 lc.get("unique_targets") or 0,
                 "unknown" if v.get("orphan_pages") is None
                 else v["orphan_pages"]))
    elif v.get("orphan_pages") is not None:
        print("    links:     %d orphan page(s); no link check in the health "
              "file (run health_diff.py --check-links)" % v["orphan_pages"])
    else:
        print("    links:     not measured (run health_diff.py --check-links)")


def _ctr(v):
    return "n/a" if v is None else "%.2f%%" % (v * 100)


def _pct(v):
    return "n/a" if v is None else "%.0f%%" % (v * 100)


def summary_line(stats):
    c = stats["counts"]
    return ("SUMMARY: %d pages, %d keep, %d refresh, %d merge, %d prune, "
            "%d invisible, %d watch, %d broken; create_gate=%s"
            % (stats["total_pages"], c.get("keep", 0), c.get("refresh", 0),
               c.get("merge-candidate", 0), c.get("prune-candidate", 0),
               c.get("invisible", 0), c.get("watch", 0), c.get("broken", 0),
               str(stats["create_gate"]).lower()))


def write_markdown(path, records, stats, meta):
    rows = [r for r in records.values() if r["verdict"] != "keep"]
    rows.sort(key=lambda r: (VERDICTS.index(r["verdict"]),
                             -r["impressions_28"], r["url"]))
    lines = [
        "# Content census",
        "",
        "> Generated by `census.py` on %s. Every non-`keep` verdict, worst "
        "first. Re-run daily; the dated snapshots in `%s` are what make decay "
        "and staleness visible."
        % (meta.get("generated", "")[:10], meta.get("out_dir", "")),
        "",
        "**%s**" % summary_line(stats).replace("SUMMARY: ", ""),
        "",
        "invisible_share %s · thin_share %s · median age %s days · "
        "top-decile clicks %s · create_gate **%s** (%s)"
        % (_pct(stats["invisible_share"]), _pct(stats["thin_share"]),
           stats["median_age_days"],
           _pct(stats["clicks_concentration_top_decile"]),
           str(stats["create_gate"]).lower(), stats["create_gate_reason"]),
        "",
        "| URL | Verdict | Top reason | Impr 28d | Clicks 28d | Age (d) |",
        "|---|---|---|---:|---:|---:|",
    ]
    for r in rows:
        reason = (r["reasons"][0] if r["reasons"] else "").replace("|", "\\|")
        lines.append("| `%s` | %s | %s | %d | %d | %d |"
                     % (path_of(r["url"]), r["verdict"], reason,
                        r["impressions_28"], r["clicks_28"], r["age_days"]))
    if not rows:
        lines.append("| _(nothing but `keep`)_ | | | | | |")
    lines.append("")
    with open(path, "w") as fh:
        fh.write("\n".join(lines))


# ------------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(
        description="Whole-inventory content census: joins the page inventory "
                    "with Search Console and the content ledger, assigns every "
                    "URL a verdict, and keeps a time series. Always exits 0.")
    ap.add_argument("--health", required=True,
                    help="health_diff.py fingerprint JSON (the inventory)")
    ap.add_argument("--gsc", required=True,
                    help="Search Console page rows for the current 28-day window")
    ap.add_argument("--gsc-prev",
                    help="Search Console page rows for the prior window; "
                         "without it there is no click_trend and no decay rule")
    ap.add_argument("--ledger", help="content ledger markdown (per-slug date/type)")
    ap.add_argument("--out", default=".seo/census",
                    help="census directory; census.md is written to its parent")
    ap.add_argument("--min-age-days", type=int, default=21,
                    help="pages younger than this are 'watch', not judged "
                         "(default 21)")
    ap.add_argument("--json", action="store_true",
                    help="print the census as JSON on stdout (SUMMARY to stderr)")
    args = ap.parse_args()

    notes = []
    today = datetime.date.today()

    health = load_json(args.health, "health file")
    if not isinstance(health.get("pages"), dict):
        raise SystemExit("%s has no 'pages' object — is it a health_diff "
                         "fingerprint?" % args.health)

    gsc, gsc_meta = load_gsc(args.gsc, "gsc", notes)
    gsc_prev, gsc_prev_meta = load_gsc(args.gsc_prev, "gsc-prev", notes)
    if not gsc:
        notes.append("no Search Console rows loaded — every page will look "
                     "invisible; check --gsc")
    ledger = load_ledger(args.ledger, notes)

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)
    today_name = "%s.json" % today.isoformat()
    history = load_history(out_dir, today_name, notes)

    records, hist_by_url = build_records(
        health, gsc, gsc_prev, ledger, history, today, args.min_age_days, notes)
    siblings = sibling_index(records)
    assign_verdicts(records, hist_by_url, siblings, today, args.min_age_days,
                    bool(gsc_prev))
    link_check = health.get("link_check") if isinstance(
        health.get("link_check"), dict) else None
    stats = portfolio_stats(records, args.min_age_days, link_check)

    # Matched-URL sanity: a health inventory that joins to nothing is almost
    # always a hostname or trailing-slash mismatch, not a dead site.
    matched = sum(1 for k in records if k in gsc)
    if gsc and matched == 0:
        notes.append("0 of %d inventory URLs matched a GSC row — hostname "
                     "or property mismatch?" % len(records))
    elif gsc:
        notes.append("%d of %d inventory URLs matched a GSC row; %d GSC URLs are "
                     "not in the sitemap inventory"
                     % (matched, len(records), len(set(gsc) - set(records))))

    meta = {
        "generated": datetime.datetime.now(datetime.timezone.utc)
                     .replace(microsecond=0).isoformat(),
        "base_url": health.get("base_url"),
        "health_path": args.health,
        "health_generated": health.get("generated"),
        "gsc_path": args.gsc,
        "gsc_prev_path": args.gsc_prev,
        "gsc_window": _window(gsc_meta),
        "gsc_prev_window": _window(gsc_prev_meta),
        "ledger_path": args.ledger,
        "ledger_entries": len(ledger),
        "min_age_days": args.min_age_days,
        "history": len(history),
        "out_dir": out_dir,
    }

    out_path = os.path.join(out_dir, today_name)
    doc = {
        "generated": meta["generated"],
        "base_url": meta["base_url"],
        "inputs": meta,
        "notes": notes,
        "portfolio": stats,
        "pages": {r["url"]: r for r in
                  sorted(records.values(), key=lambda x: x["url"])},
    }
    with open(out_path, "w") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)

    md_path = os.path.join(os.path.dirname(os.path.abspath(out_dir)), "census.md")
    write_markdown(md_path, records, stats, meta)

    if args.json:
        print(json.dumps(doc, indent=2, sort_keys=True))
        print(summary_line(stats), file=sys.stderr)
    else:
        print_report(records, stats, meta, notes, out_path, md_path)
    return 0


def _window(meta):
    if not meta:
        return ""
    a, b = meta.get("start_date"), meta.get("end_date")
    if a and b:
        return "  (%s → %s, %d rows)" % (a, b, meta.get("rows", 0))
    return "  (%d rows)" % meta.get("rows", 0)


if __name__ == "__main__":
    sys.exit(main())
