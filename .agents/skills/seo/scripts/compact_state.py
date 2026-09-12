#!/usr/bin/env python3
"""Thin out the dated snapshots in .seo/ so the committed dataset stops growing.

The /seo skill commits its own state into the app repo and runs from a fresh
worktree, one PR per run, possibly a dozen times a day. Three directories carry
a fat file per day and never shed one:

  .seo/health/<date>.json    ~240 KB
  .seo/census/<date>.json    ~230 KB
  .seo/gsc/<date>.json       ~30 KB   (plus bing-<date>.json, its own series)

Left alone that is well over a hundred megabytes a year of history nobody reads
at day-level resolution once it is a few months old. This script keeps recent
days intact and thins older ones to one per week, then one per month.

Policy (all overridable):

  age <= --keep-daily-days (30)     keep every file
  30 < age <= --keep-weekly-days    keep the first file of each ISO week
  age > --keep-weekly-days (180)    keep the first file of each calendar month

Guardrails, in force regardless of the numbers:

  * the newest file of a series is never deleted
  * a series holding one file is never touched
  * only <date>.json / <prefix>-<date>.json names are considered; anything else
    in the directory (.keep, notes, stray files) is left alone
  * runs/, evidence/, briefs/ and aeo/ are never touched at all
  * bing-<date>.json is a separate series from <date>.json in the same folder,
    with the policy applied to each independently

Deleting only ever removes whole snapshots, so census.py's load_history() keeps
working unchanged: it globs whatever <date>.json files survive and reads them
oldest-first. History gets coarser, never broken.

Usage
  compact_state.py                         print the plan, delete nothing
  compact_state.py --apply                 do it
  compact_state.py --root path             somewhere other than cwd
  compact_state.py --json                  machine-readable plan or result
  compact_state.py --keep-daily-days 60 --keep-weekly-days 365
  compact_state.py --verbose               list every date, no truncation
  compact_state.py --today 2026-09-09      pin "now" (testing / reproducibility)

Exit code is always 0 — a housekeeping pass must never fail a /seo run.
Standard library only.
"""

import argparse
import datetime
import json
import os
import re
import sys

# Directories whose dated snapshots this script manages.
MANAGED_DIRS = ("health", "census", "gsc", "serp", "backlinks")

# Named here so the intent survives a future edit: these hold small, individually
# meaningful artifacts (run logs, evidence, briefs, AEO probes). Never compacted.
PROTECTED_DIRS = ("runs", "evidence", "briefs", "aeo")

# <prefix->?<YYYY-MM-DD>.json  ->  ("bing-", "2026-09-07") or ("", "2026-09-09")
SNAPSHOT_RE = re.compile(r"^(?P<prefix>[A-Za-z0-9._-]*?)"
                         r"(?P<date>\d{4}-\d{2}-\d{2})\.json$")

# Steady-state file count the policy retains per series, per the default windows.
WEEKS_IN_WEEKLY_ZONE = 21   # (180 - 30) days / 7, floored
MONTHS_PER_YEAR = 12

DEFAULT_KEEP_DAILY_DAYS = 30
DEFAULT_KEEP_WEEKLY_DAYS = 180

MAX_LISTED = 16             # dates printed per line-group before "+N more"


# ----------------------------------------------------------------- small utils

def human_bytes(n):
    """Bytes as MB with one decimal, the unit the summary line speaks in."""
    return "%.1f MB" % (n / (1024.0 * 1024.0))


def human_kb(n):
    return "%.1f KB" % (n / 1024.0)


def parse_date(text):
    try:
        return datetime.date(int(text[0:4]), int(text[5:7]), int(text[8:10]))
    except (ValueError, IndexError):
        return None


def file_size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def wrap_dates(dates, indent, limit):
    """Dates as wrapped, comma-joined lines under a hanging indent."""
    shown = dates if limit is None or len(dates) <= limit else dates[:limit]
    lines = []
    cur = ""
    for d in shown:
        piece = d if not cur else ", " + d
        if cur and len(cur) + len(piece) > 68:
            lines.append(indent + cur)
            cur = d
        else:
            cur += piece
    if cur:
        lines.append(indent + cur)
    hidden = len(dates) - len(shown)
    if hidden > 0:
        lines.append("%s+%d more (--verbose to list)" % (indent, hidden))
    return lines


# ------------------------------------------------------------------ discovery

def resolve_base(root):
    """Return the .seo directory to operate on, or None.

    Accepts a repo root (has .seo/), the .seo directory itself, or any
    directory that already holds health/ census/ gsc/.
    """
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        return None
    nested = os.path.join(root, ".seo")
    if os.path.isdir(nested):
        return nested
    if any(os.path.isdir(os.path.join(root, d)) for d in MANAGED_DIRS):
        return root
    return None


def collect_series(dir_path):
    """{prefix: [(date, name, size)]} sorted oldest-first, for one directory."""
    series = {}
    try:
        names = sorted(os.listdir(dir_path))
    except OSError:
        return series
    for name in names:
        path = os.path.join(dir_path, name)
        if not os.path.isfile(path):
            continue
        m = SNAPSHOT_RE.match(name)
        if not m:
            continue
        d = parse_date(m.group("date"))
        if d is None:
            continue
        series.setdefault(m.group("prefix"), []).append(
            (d, name, file_size(path)))
    for files in series.values():
        files.sort(key=lambda t: (t[0], t[1]))
    return series


def dir_total_bytes(dir_path):
    total = 0
    try:
        names = os.listdir(dir_path)
    except OSError:
        return 0
    for name in names:
        path = os.path.join(dir_path, name)
        if os.path.isfile(path):
            total += file_size(path)
    return total


# --------------------------------------------------------------------- policy

def zone_for(age_days, keep_daily, keep_weekly):
    if age_days <= keep_daily:
        return "daily"
    if age_days <= keep_weekly:
        return "weekly"
    return "monthly"


def plan_series(files, today, keep_daily, keep_weekly):
    """Decide keep/delete for one series.

    files: [(date, name, size)] oldest-first. Returns [(date, name, size,
    action, zone, reason)] in the same order.
    """
    if len(files) <= 1:
        return [(d, n, s, "keep", "only", "only file of its series")
                for d, n, s in files]

    newest_name = files[-1][1]
    seen_week = set()
    seen_month = set()
    out = []
    for d, name, size in files:
        age = (today - d).days
        if age < 0:                       # dated ahead of "now"; never guess
            out.append((d, name, size, "keep", "daily", "not yet aged"))
            continue
        zone = zone_for(age, keep_daily, keep_weekly)
        if zone == "daily":
            out.append((d, name, size, "keep", zone, "within daily window"))
            continue
        if zone == "weekly":
            key = d.isocalendar()[:2]
            if key not in seen_week:
                seen_week.add(key)
                out.append((d, name, size, "keep", zone, "first of ISO week"))
            else:
                out.append((d, name, size, "delete", zone, "later in ISO week"))
            continue
        key = (d.year, d.month)
        if key not in seen_month:
            seen_month.add(key)
            out.append((d, name, size, "keep", zone, "first of month"))
        else:
            out.append((d, name, size, "delete", zone, "later in month"))

    # Guardrail: the newest file always survives, whatever the arithmetic said.
    out = [(d, n, s, "keep" if n == newest_name else a, z,
            "newest snapshot" if n == newest_name and a == "delete" else r)
           for d, n, s, a, z, r in out]
    return out


def build_plan(base, today, keep_daily, keep_weekly):
    dirs = []
    for dname in MANAGED_DIRS:
        dpath = os.path.join(base, dname)
        if not os.path.isdir(dpath):
            continue
        series_files = collect_series(dpath)
        entry = {
            "dir": dname,
            "path": dpath,
            "bytes_before": dir_total_bytes(dpath),
            "series": [],
        }
        for prefix in sorted(series_files):
            files = series_files[prefix]
            decided = plan_series(files, today, keep_daily, keep_weekly)
            entry["series"].append({
                "prefix": prefix,
                "label": (prefix + "<date>.json") if prefix else "<date>.json",
                "files": decided,
                "newest_bytes": files[-1][2],
            })
        dirs.append(entry)
    return dirs


# --------------------------------------------------------------------- growth

def growth_projection(dirs, keep_daily, keep_weekly):
    """What a year costs uncompacted vs. under this policy.

    Uses each series' newest file as the stand-in for "one day's snapshot",
    which is the only honest estimate available from disk alone.
    """
    weekly_slots = max(0, (keep_weekly - keep_daily) // 7)
    first_year_files = keep_daily + weekly_slots + MONTHS_PER_YEAR
    per_day = 0
    uncompacted = 0
    first_year = 0
    steady = 0
    for d in dirs:
        for s in d["series"]:
            size = s["newest_bytes"]
            per_day += size
            uncompacted += size * 365
            first_year += size * first_year_files
            steady += size * MONTHS_PER_YEAR
    return {
        "daily_bytes": per_day,
        "uncompacted_bytes_per_year": uncompacted,
        "compacted_first_year_bytes": first_year,
        "compacted_bytes_per_year_after": steady,
        "retained_files_first_year_per_series": first_year_files,
        "daily_slots": keep_daily,
        "weekly_slots": weekly_slots,
        "monthly_slots_per_year": MONTHS_PER_YEAR,
    }


# --------------------------------------------------------------------- execute

def apply_plan(dirs):
    errors = []
    for d in dirs:
        for s in d["series"]:
            for i, (dt, name, size, action, zone, reason) in enumerate(s["files"]):
                if action != "delete":
                    continue
                path = os.path.join(d["path"], name)
                try:
                    os.remove(path)
                except OSError as ex:
                    errors.append("could not delete %s (%s)" % (path, ex))
                    s["files"][i] = (dt, name, size, "keep", zone,
                                     "delete failed")
        d["bytes_after"] = dir_total_bytes(d["path"])
    return errors


# ---------------------------------------------------------------------- report

def series_report_lines(s, verbose):
    limit = None if verbose else MAX_LISTED
    lines = []
    groups = [("keep", "daily"), ("keep", "weekly"), ("keep", "monthly"),
              ("keep", "only"), ("delete", "weekly"), ("delete", "monthly")]
    for action, zone in groups:
        picked = [f for f in s["files"] if f[3] == action and f[4] == zone]
        if not picked:
            continue
        dates = [f[0].isoformat() for f in picked]
        size = sum(f[2] for f in picked)
        lines.append("    %-6s %-8s %4d file%s  %s"
                     % (action, zone, len(picked),
                        " " if len(picked) == 1 else "s", human_bytes(size)))
        lines.extend(wrap_dates(dates, "             ", limit))
    ahead = [f for f in s["files"] if f[5] == "not yet aged"]
    if ahead:
        lines.append("    keep   future   %4d file(s)  %s"
                     % (len(ahead), ", ".join(f[0].isoformat() for f in ahead)))
    return lines


def print_report(base, dirs, growth, applied, errors, verbose, keep_daily,
                 keep_weekly, today):
    print(".seo state compaction  (%s)" % base)
    print("policy: keep every file <= %dd, first-of-ISO-week to %dd, "
          "first-of-month beyond; anchored at %s"
          % (keep_daily, keep_weekly, today.isoformat()))
    print("")
    if not dirs:
        print("no managed snapshot directories found "
              "(looked for %s)" % "/ ".join(MANAGED_DIRS))
    for d in dirs:
        n_files = sum(len(s["files"]) for s in d["series"])
        n_del = sum(1 for s in d["series"] for f in s["files"]
                    if f[3] == "delete")
        print("%s/  %d snapshot file%s, %d to delete"
              % (d["dir"], n_files, "" if n_files == 1 else "s", n_del))
        if not d["series"]:
            print("    (no dated snapshots)")
        for s in d["series"]:
            span = ""
            if s["files"]:
                span = "  %s .. %s" % (s["files"][0][0].isoformat(),
                                       s["files"][-1][0].isoformat())
            print("  series %s%s" % (s["label"], span))
            for line in series_report_lines(s, verbose):
                print(line)
        print("")
    print("protected, never touched: %s"
          % ", ".join(p + "/" for p in PROTECTED_DIRS))
    print("")
    print("GROWTH: %s/day of new snapshots across %d series"
          % (human_kb(growth["daily_bytes"]),
             sum(len(d["series"]) for d in dirs)))
    print("  uncompacted: %s/yr" % human_bytes(
        growth["uncompacted_bytes_per_year"]))
    print("  compacted:   %s in year one (%d daily + %d weekly + %d monthly "
          "per series), then +%s/yr"
          % (human_bytes(growth["compacted_first_year_bytes"]),
             growth["daily_slots"], growth["weekly_slots"],
             growth["monthly_slots_per_year"],
             human_bytes(growth["compacted_bytes_per_year_after"])))
    for e in errors:
        print("ERROR: %s" % e)


def summary_line(dirs, applied):
    total = sum(len(s["files"]) for d in dirs for s in d["series"])
    to_delete = sum(1 for d in dirs for s in d["series"] for f in s["files"]
                    if f[3] == "delete")
    before = sum(d["bytes_before"] for d in dirs)
    after = sum(d.get("bytes_after", d["bytes_before"] -
                      sum(f[2] for s in d["series"] for f in s["files"]
                          if f[3] == "delete"))
                for d in dirs)
    return ("SUMMARY: %d files, %d to delete, %s -> %s (%s)"
            % (total, to_delete, human_bytes(before), human_bytes(after),
               "applied" if applied else "dry run"))


def json_payload(base, dirs, growth, applied, errors, keep_daily, keep_weekly,
                 today):
    out_dirs = []
    for d in dirs:
        out_dirs.append({
            "dir": d["dir"],
            "path": d["path"],
            "bytes_before": d["bytes_before"],
            "bytes_after": d.get(
                "bytes_after",
                d["bytes_before"] - sum(f[2] for s in d["series"]
                                        for f in s["files"] if f[3] == "delete")),
            "series": [{
                "prefix": s["prefix"],
                "label": s["label"],
                "keep": [{"date": f[0].isoformat(), "file": f[1],
                          "bytes": f[2], "zone": f[4], "reason": f[5]}
                         for f in s["files"] if f[3] == "keep"],
                "delete": [{"date": f[0].isoformat(), "file": f[1],
                            "bytes": f[2], "zone": f[4], "reason": f[5]}
                           for f in s["files"] if f[3] == "delete"],
            } for s in d["series"]],
        })
    before = sum(d["bytes_before"] for d in out_dirs)
    after = sum(d["bytes_after"] for d in out_dirs)
    return {
        "base": base,
        "today": today.isoformat(),
        "applied": applied,
        "keep_daily_days": keep_daily,
        "keep_weekly_days": keep_weekly,
        "protected_dirs": list(PROTECTED_DIRS),
        "dirs": out_dirs,
        "growth": growth,
        "errors": errors,
        "totals": {
            "files": sum(len(s["keep"]) + len(s["delete"])
                         for d in out_dirs for s in d["series"]),
            "to_delete": sum(len(s["delete"])
                             for d in out_dirs for s in d["series"]),
            "bytes_before": before,
            "bytes_after": after,
        },
    }


# ------------------------------------------------------------------------ main

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Thin dated .seo/ snapshots: daily, then weekly, "
                    "then monthly. Dry run unless --apply.")
    ap.add_argument("--root", default=".",
                    help="repo root, or the .seo directory itself (default: .)")
    ap.add_argument("--apply", action="store_true",
                    help="actually delete; without it nothing is touched")
    ap.add_argument("--json", action="store_true",
                    help="print the plan/result as JSON (SUMMARY to stderr)")
    ap.add_argument("--keep-daily-days", type=int,
                    default=DEFAULT_KEEP_DAILY_DAYS,
                    help="keep every file this recent (default: %d)"
                         % DEFAULT_KEEP_DAILY_DAYS)
    ap.add_argument("--keep-weekly-days", type=int,
                    default=DEFAULT_KEEP_WEEKLY_DAYS,
                    help="beyond the daily window and up to here, keep one "
                         "file per ISO week (default: %d)"
                         % DEFAULT_KEEP_WEEKLY_DAYS)
    ap.add_argument("--verbose", action="store_true",
                    help="list every date instead of truncating long groups")
    ap.add_argument("--today", default=None, metavar="YYYY-MM-DD",
                    help="pin the reference date instead of using today (UTC)")
    args = ap.parse_args(argv)

    keep_daily = max(0, args.keep_daily_days)
    keep_weekly = max(keep_daily, args.keep_weekly_days)

    today = (parse_date(args.today) if args.today
             else datetime.datetime.now(datetime.timezone.utc).date())
    if today is None:
        print("ERROR: --today must be YYYY-MM-DD", file=sys.stderr)
        return 0

    base = resolve_base(args.root)
    if base is None:
        msg = ("no .seo state directory under %s — nothing to compact"
               % os.path.abspath(args.root))
        if args.json:
            print(json.dumps({"base": None, "applied": False, "dirs": [],
                              "errors": [msg], "totals": {
                                  "files": 0, "to_delete": 0,
                                  "bytes_before": 0, "bytes_after": 0}},
                             indent=2, sort_keys=True))
            print("SUMMARY: 0 files, 0 to delete, 0.0 MB -> 0.0 MB (dry run)",
                  file=sys.stderr)
        else:
            print(msg)
            print("SUMMARY: 0 files, 0 to delete, 0.0 MB -> 0.0 MB (dry run)")
        return 0

    dirs = build_plan(base, today, keep_daily, keep_weekly)
    growth = growth_projection(dirs, keep_daily, keep_weekly)

    errors = []
    if args.apply:
        errors = apply_plan(dirs)

    line = summary_line(dirs, args.apply)
    if args.json:
        print(json.dumps(json_payload(base, dirs, growth, args.apply, errors,
                                      keep_daily, keep_weekly, today),
                         indent=2, sort_keys=True))
        print(line, file=sys.stderr)
    else:
        print_report(base, dirs, growth, args.apply, errors, args.verbose,
                     keep_daily, keep_weekly, today)
        print(line)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as ex:  # noqa: BLE001 — housekeeping never fails a run
        print("ERROR: compact_state failed (%s: %s)"
              % (type(ex).__name__, ex), file=sys.stderr)
        sys.exit(0)
