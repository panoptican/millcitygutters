#!/usr/bin/env python3
"""Score past ledger actions against Search Console and roll them into priors.

The ledger records every action the skill took. Nothing scores whether those
actions worked, so the selection rubric's `confidence` axis (select.md §3)
never learns. This script gives each past ledger row a verdict from the dated
GSC page pulls around it, then groups verdicts by action (and by type for
create-editorial) into a confidence adjustment the next selection can apply.

It is a report, not a gate. It always exits 0.

Usage
  outcomes.py
  outcomes.py --ledger .seo/content-ledger.md --gsc-dir .seo/gsc
  outcomes.py --today 2026-09-09 --min-days 28 --json

Inputs
  --ledger   markdown; every table row whose first cell is YYYY-MM-DD is read.
             The Shipped table (template shape) and register.md §1 append rows
             (| date | action | slug | type | lane | what | commit |) both work.
  --gsc-dir  dated page pulls YYYY-MM-DD.json, each covering the 28 days that
             end on the file date. queries-* and bing-* files are ignored.

Verdicts
  before = newest pull dated on or before the action; after = oldest pull dated
  at least --min-days after it. Target change minus site-wide change is the
  excess: worked at +20%, hurt at -20%, flat between. create-* rows have no
  before read and are judged on the after read alone.

Standard library only.
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse

ACTIONS = ["correct", "repair", "refresh", "consolidate", "prune",
           "verify-product", "create-editorial", "create-programmatic",
           "create-tool", "aeo-fix", "offpage-brief", "index-nudge",
           "distribute"]
EDITORIAL_TYPES = ["guide", "how-to", "listicle", "definition", "comparison",
                   "data-study", "resource", "opinion", "case-study"]
DATE_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_RE = re.compile(r"https?://[^\s)\]>]+")

EXCESS = 0.20
CREATE_WORKED_CLICKS, CREATE_WORKED_IMPR = 5, 200
CREATE_INVISIBLE_MIN_DAYS = 45
LOW_CLICKS_TARGET, LOW_CLICKS_SITE, LOW_IMPR = 10, 50, 30
EMPTY = {"clicks": 0, "impressions": 0, "position": None}


# ---------------------------------------------------------------- url helpers

def normalise(url):
    """Lowercase scheme+host, drop fragment and utm_* params, one trailing slash."""
    try:
        p = urllib.parse.urlsplit((url or "").strip())
    except ValueError:
        return (url or "").strip()
    query = "&".join(kv for kv in p.query.split("&")
                     if kv and not kv.lower().startswith("utm_"))
    return urllib.parse.urlunsplit(
        (p.scheme.lower(), p.netloc.lower(), path_of(url), query, ""))


def path_of(url):
    try:
        p = urllib.parse.urlsplit(url).path or "/"
    except ValueError:
        return "/"
    return p if len(p) == 1 else p.rstrip("/")


def parse_date(s):
    try:
        return datetime.date.fromisoformat(str(s).strip()[:10])
    except ValueError:
        return None


# ------------------------------------------------------------------- loading

def _row_page(row):
    page = row.get("page") or row.get("url") or row.get("Page")
    if page:
        return str(page)
    keys = row.get("keys")
    return str(keys[0]) if isinstance(keys, list) and keys else None


def find_rows(node, depth=0):
    """The page-row list, under rows/results/data/pages or anywhere shallow."""
    if depth > 6:
        return None
    if isinstance(node, list) and node:
        head = [r for r in node[:5] if isinstance(r, dict)]
        if head and all(_row_page(r) and ("clicks" in r or "impressions" in r)
                        for r in head):
            return node
    if isinstance(node, dict):
        children = [node[k] for k in ("rows", "results", "data", "pages")
                    if k in node] + list(node.values())
    else:
        children = node if isinstance(node, list) else []
    for v in children:
        got = find_rows(v, depth + 1) if isinstance(v, (dict, list)) else None
        if got:
            return got
    return None


def load_pull(path):
    """{"by_url": {norm: rec}, "by_path": {path: rec}, "site": rec}."""
    with open(path) as fh:
        rows = find_rows(json.load(fh)) or []
    by_url, by_path, site = {}, {}, {"clicks": 0, "impressions": 0}
    for row in rows:
        page = _row_page(row) if isinstance(row, dict) else None
        if not page:
            continue
        clicks, impr = int(row.get("clicks") or 0), int(row.get("impressions") or 0)
        for table, key in ((by_url, normalise(page)), (by_path, path_of(page))):
            rec = table.setdefault(key, dict(EMPTY))
            rec["clicks"] += clicks
            rec["impressions"] += impr
            if rec["position"] is None and row.get("position") is not None:
                rec["position"] = round(float(row["position"]), 1)
        site["clicks"] += clicks
        site["impressions"] += impr
    return {"by_url": by_url, "by_path": by_path, "site": site}


def load_pulls(gsc_dir, notes):
    """[(date, pull)] oldest first. Non-dated names (queries-*, bing-*) skipped."""
    if not os.path.isdir(gsc_dir):
        notes.append("gsc dir not found: %s" % gsc_dir)
        return []
    out = []
    for name in sorted(os.listdir(gsc_dir)):
        m = DATE_FILE_RE.match(name)
        if not m:
            continue
        try:
            out.append((parse_date(m.group(1)), load_pull(os.path.join(gsc_dir, name))))
        except Exception as ex:  # noqa: BLE001
            notes.append("skipped unreadable pull %s (%s)" % (name, ex))
    return out


def load_ledger(path, notes):
    """[{date, action, type, target}] from every dated table row."""
    if not os.path.isfile(path):
        notes.append("ledger not found: %s" % path)
        return []
    out, skipped = [], 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip().strip("`").strip() for c in line.strip("|").split("|")]
            date = parse_date(cells[0]) if DATE_RE.match(cells[0]) else None
            if date is None:
                continue
            lowered = [c.lower() for c in cells[1:]]
            action = next((c for c in lowered if c in ACTIONS), None)
            kind = next((c for c in lowered if c in EDITORIAL_TYPES + ["tool"]), None)
            if action is None and kind:
                action = "create-tool" if kind == "tool" else "create-editorial"
            if action is None:
                skipped += 1
                continue
            target = None
            for c in cells[1:]:
                m = URL_RE.search(c)
                if m or re.match(r"^/\S*$", c):
                    target = m.group(0).rstrip(".,") if m else c
                    break
            out.append({"date": date, "action": action, "type": kind, "target": target})
    if skipped:
        notes.append("%d dated ledger row(s) had no recognisable action" % skipped)
    return out


# ------------------------------------------------------------------- verdicts

def lookup(pull, date, target):
    rec = pull["by_url"].get(normalise(target)) if target.startswith("http") else None
    rec = dict(rec or pull["by_path"].get(path_of(target)) or EMPTY)
    rec["pull"] = date.isoformat()
    return rec


def rel_change(before, after):
    if before == 0:
        return 1.0 if after > 0 else 0.0
    return round((after - before) / float(before), 3)


def judge(row, pulls, min_days):
    out = {"date": row["date"].isoformat(), "action": row["action"],
           "type": row["type"], "target": row["target"], "verdict": None,
           "before": None, "after": None, "control_change": None,
           "excess": None, "note": ""}
    if not row["target"]:
        out["verdict"], out["note"] = "n/a", "no target URL"
        return out
    before = next(((d, p) for d, p in reversed(pulls) if d <= row["date"]), None)
    cutoff = row["date"] + datetime.timedelta(days=min_days)
    after = next(((d, p) for d, p in pulls if d >= cutoff), None)
    if after is None:
        out["verdict"] = "too-new"
        out["note"] = "no pull dated %s or later" % cutoff.isoformat()
        return out
    a = out["after"] = lookup(after[1], after[0], row["target"])
    age = (after[0] - row["date"]).days

    if row["action"].startswith("create-"):
        if a["clicks"] >= CREATE_WORKED_CLICKS or a["impressions"] >= CREATE_WORKED_IMPR:
            out["verdict"] = "worked"
        elif a["impressions"] > 0:
            out["verdict"] = "flat"
        else:
            out["verdict"] = "too-new" if age < CREATE_INVISIBLE_MIN_DAYS else "invisible"
        out["note"] = "%d clicks, %d impressions %dd after publish" % (
            a["clicks"], a["impressions"], age)
        return out
    if before is None:
        out["verdict"], out["note"] = "no-data", "no pull on or before the action date"
        return out

    b = out["before"] = lookup(before[1], before[0], row["target"])
    b_site, a_site = before[1]["site"], after[1]["site"]
    sm = "clicks" if b_site["clicks"] >= LOW_CLICKS_SITE else "impressions"
    out["control_change"] = rel_change(b_site[sm], a_site[sm])
    out["control"] = {"metric": sm, "before": b_site[sm], "after": a_site[sm]}
    if b["impressions"] < LOW_IMPR and a["impressions"] < LOW_IMPR:
        out["verdict"] = "no-data"
        out["note"] = "under %d impressions in both windows" % LOW_IMPR
        return out
    m = "clicks" if b["clicks"] >= LOW_CLICKS_TARGET else "impressions"
    change = rel_change(b[m], a[m])
    out["excess"] = round(change - out["control_change"], 3)
    if out["excess"] >= EXCESS and a[m] >= b[m]:
        out["verdict"] = "worked"
    elif out["excess"] <= -EXCESS:
        out["verdict"] = "hurt"
    else:
        out["verdict"] = "flat"
    out["note"] = "%s %d -> %d (%+.0f%%) vs site %+.0f%%" % (
        m, b[m], a[m], change * 100, out["control_change"] * 100)
    return out


# --------------------------------------------------------------------- priors

def build_priors(rows, today):
    """Per action (and per type for create-editorial): n, worked, flat, hurt.

    too-new, n/a and no-data are not evidence and stay out of n. invisible is
    a create that produced nothing, so it counts as hurt."""
    groups = {}
    for r in rows:
        bucket = {"worked": "worked", "flat": "flat", "hurt": "hurt",
                  "invisible": "hurt"}.get(r["verdict"])
        if bucket is None:
            continue
        keys = [r["action"]]
        if r["action"] == "create-editorial" and r["type"]:
            keys.append("create-editorial/%s" % r["type"])
        for k in keys:
            g = groups.setdefault(k, {"n": 0, "worked": 0, "flat": 0, "hurt": 0})
            g[bucket] += 1
            g["n"] += 1
    for k, g in groups.items():
        rate = g["worked"] / float(g["n"])
        adjust = 1 if g["n"] >= 3 and rate >= 0.6 else (
            -1 if g["n"] >= 3 and rate <= 0.25 else 0)
        g["confidence_adjust"] = adjust
        g["reading"] = "%s: %d of %d worked (%+d)" % (k, g["worked"], g["n"], adjust)
    return {"generated": today.isoformat(),
            "groups": {k: groups[k] for k in sorted(groups)}}


# ------------------------------------------------------------------------ main

def row_key(r):
    return (r["date"], r["action"], r.get("target") or "")


def main():
    ap = argparse.ArgumentParser(
        description="Score past ledger actions against GSC pulls and write "
                    "per-action priors. Always exits 0.")
    ap.add_argument("--ledger", default=".seo/content-ledger.md")
    ap.add_argument("--gsc-dir", default=".seo/gsc")
    ap.add_argument("--out", default=".seo/outcomes.json")
    ap.add_argument("--priors", default=".seo/priors.json")
    ap.add_argument("--today", help="YYYY-MM-DD override (tests)")
    ap.add_argument("--min-days", type=int, default=28,
                    help="days after the action before an after-read is "
                         "attempted (default 28)")
    ap.add_argument("--json", action="store_true",
                    help="print {outcomes, priors} as JSON on stdout")
    args = ap.parse_args()

    notes = []
    today = parse_date(args.today) if args.today else datetime.date.today()
    if today is None:
        raise SystemExit("--today must be YYYY-MM-DD")
    pulls = load_pulls(args.gsc_dir, notes)
    ledger = load_ledger(args.ledger, notes)
    if not pulls:
        notes.append("no dated pulls loaded — every row is too-new")

    previous = {}
    if os.path.isfile(args.out):
        try:
            with open(args.out) as fh:
                previous = {row_key(r): r["verdict"]
                            for r in json.load(fh).get("rows") or []}
        except Exception as ex:  # noqa: BLE001
            notes.append("could not read previous %s (%s)" % (args.out, ex))

    rows = [judge(r, pulls, args.min_days) for r in ledger]
    outcomes = {"generated": today.isoformat(), "ledger": args.ledger,
                "gsc_dir": args.gsc_dir, "pulls": len(pulls),
                "notes": notes, "rows": rows}
    priors = build_priors(rows, today)
    for path, doc in ((args.out, outcomes), (args.priors, priors)):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as fh:
            json.dump(doc, fh, indent=2)

    if args.json:
        print(json.dumps({"outcomes": outcomes, "priors": priors}, indent=2))
        return 0

    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print("Outcomes — %d ledger action(s), %d GSC pull(s)" % (len(rows), len(pulls)))
    print("  written: %s and %s" % (args.out, args.priors))
    for n in notes:
        print("  note: %s" % n)
    print("  verdicts: %s" % ", ".join("%d %s" % (v, k) for k, v in sorted(counts.items())))
    new = [r for r in rows if previous.get(row_key(r)) != r["verdict"]]
    print("\nNEWLY DECIDED (%d)" % len(new))
    if not new:
        print("  none since the last run")
    for r in new:
        label = r["action"]
        if r["action"] == "create-editorial" and r["type"]:
            label += "/" + r["type"]
        print("  %s  %-24s %-9s %-40s %s" % (
            r["date"], label, r["verdict"], (r["target"] or "(no target)")[:40], r["note"]))
    print("\nPRIORS")
    for g in priors["groups"].values():
        print("  " + g["reading"])
    if not priors["groups"]:
        print("  none yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
