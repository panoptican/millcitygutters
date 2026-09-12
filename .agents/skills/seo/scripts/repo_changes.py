#!/usr/bin/env python3
"""List what changed in the product since the last /seo run.

The repo is the freshest demand signal the site owns. A feature shipped with
no page is a `create`; a price change is a `verify-product` plus a `correct`
on every page that still says the old price; a removed route is a `repair`
(redirect). This walks git history since the last run, keeps only the files
that matter (changelog, routes, pricing, flags, schema, content), and groups
them so the model can turn them into candidates.

Usage
  repo_changes.py
  repo_changes.py --since 2026-09-01 --json
  repo_changes.py --since v1.4.0 --watch 'app/views/**' --watch CHANGELOG.md
  repo_changes.py --root ../app --max-commits 50

--since takes an ISO date/time or a git ref (ref..HEAD). Default: the newest
.seo/runs/YYYY-MM-DD[-HHMM].md, else 14 days ago. Watch globs are fnmatch
style with ** across directories; with none given, .seo/config.json
repo.watch_paths is used, then the built-in list. Always exits 0.
"""

import argparse
import json
import os
import re
import subprocess
import sys

DEFAULT_WATCH = [
    "CHANGELOG.md", "CHANGELOG*", "docs/changelog/**", "config/routes.rb",
    "**/routes*.{ts,js,rb}", "**/pricing*", "config/features*",
    "**/feature_flags*", "db/migrate/**", "db/schema.rb",
    "prisma/schema.prisma",
]
CATEGORIES = ["changelog", "routes", "pricing", "flags", "schema", "content",
              "other"]
PRICING_RX = re.compile(r"\b(pricing|prices?|plans?|billing)\b", re.I)
REMOVAL_RX = re.compile(r"\b(remov|delet|deprecat|renam)", re.I)
DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}")
RUN_RX = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:-(\d{2})(\d{2}))?\.md$")
MAX_CHANGELOG_LINES = 20


def git(root, *args):
    """stdout of a git command, or None on any failure."""
    try:
        r = subprocess.run(["git", "-C", root] + list(args),
                           capture_output=True, text=True, check=False)
    except OSError:
        return None
    return r.stdout if r.returncode == 0 else None


def glob_to_regex(pattern):
    """fnmatch-style glob with ** across '/' and {a,b} alternation."""
    out = ""
    for part in re.split(r"(\*\*/|\*\*|\*|\?|\{[^}]*\})", pattern):
        if part == "**/":
            out += "(?:.*/)?"
        elif part == "**":
            out += ".*"
        elif part == "*":
            out += "[^/]*"
        elif part == "?":
            out += "[^/]"
        elif part.startswith("{") and part.endswith("}"):
            alts = [re.escape(a) for a in part[1:-1].split(",")]
            out += "(?:" + "|".join(alts) + ")"
        else:
            out += re.escape(part)
    return re.compile("^" + out + "$")


def matches(path, patterns):
    """True if a glob matches the path, any ancestor dir, or (for slashless
    patterns) the basename, so **/pricing* catches app/views/pricing/x.erb."""
    parts = path.split("/")
    cands = ["/".join(parts[:i]) for i in range(1, len(parts) + 1)]
    for pat, rx in patterns:
        if any(rx.match(c) for c in cands) or \
                ("/" not in pat and rx.match(parts[-1])):
            return True
    return False


def categorise(path, subject):
    p, base = path.lower(), os.path.basename(path).lower()
    if (base.startswith("changelog") or "docs/changelog" in p
            or "release-notes" in p or "release_notes" in p):
        return "changelog"
    if base.startswith("routes") or "/routes/" in p:
        return "routes"
    if "feature_flags" in p or "feature-flags" in p or "flipper" in p \
            or re.search(r"(^|/)config/features", p):
        return "flags"
    if re.search(r"(^|/)(db/migrate|migrations)/", p) or base in (
            "schema.rb", "schema.prisma", "structure.sql"):
        return "schema"
    if PRICING_RX.search(p.replace("_", " ").replace("-", " ")):
        return "pricing"
    if re.search(r"(^|/)(content|pages|posts|blog|docs|views|articles)/", p):
        return "content"
    if PRICING_RX.search(subject):
        return "pricing"
    return "other"


def default_since(root):
    """Newest .seo/runs note as ISO time, else 14 days ago."""
    runs = os.path.join(root, ".seo", "runs")
    best = None
    try:
        for name in os.listdir(runs):
            m = RUN_RX.match(name)
            if m:
                stamp = m.group(1) + "T" + (m.group(2) or "00") + ":" + \
                    (m.group(3) or "00")
                if best is None or stamp > best[0]:
                    best = (stamp, name)
    except OSError:
        pass
    if best:
        return best[0], ".seo/runs/" + best[1]
    return "14 days ago", "default"


def log_args(root, since):
    """Translate --since into git log arguments: a date or a ref range."""
    if not DATE_RX.match(since) and git(root, "rev-parse", "--verify",
                                        "--quiet", since + "^{commit}"):
        return [since + "..HEAD"]
    return ["--since=" + since]


def changelog_lines(root, sha, path):
    out = git(root, "show", sha, "--format=", "--", path) or ""
    lines = []
    for line in out.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            text = line[1:].rstrip()
            if text.strip():
                lines.append(text)
            if len(lines) >= MAX_CHANGELOG_LINES:
                break
    return lines


def collect(root, since, watch, exclude, max_commits):
    out = git(root, "log", "--name-only", "--no-merges",
              "-n", str(max_commits),
              "--format=%H%x1f%an%x1f%aI%x1f%s", *log_args(root, since))
    commits, cur = [], None
    for line in (out or "").splitlines():
        if "\x1f" in line:
            sha, author, date, subject = (line.split("\x1f") + [""] * 4)[:4]
            cur = {"sha": sha, "author": author, "date": date,
                   "subject": subject, "files": [], "changelog_lines": [],
                   "removal_hint": bool(REMOVAL_RX.search(subject))}
            commits.append(cur)
        elif line.strip() and cur is not None:
            path = line.strip()
            if matches(path, watch) and not matches(path, exclude):
                cat = categorise(path, cur["subject"])
                cur["files"].append({"path": path, "category": cat})
                if cat == "changelog":
                    cur["changelog_lines"] += changelog_lines(
                        root, cur["sha"], path)
    return [c for c in commits if c["files"]]


def main():
    ap = argparse.ArgumentParser(
        description="Product changes in the repo since the last /seo run, "
                    "grouped by category.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--since", help="ISO date/time or git ref")
    ap.add_argument("--watch", action="append", help="glob, repeatable")
    ap.add_argument("--exclude", action="append", help="glob, repeatable")
    ap.add_argument("--config", default=".seo/config.json")
    ap.add_argument("--max-commits", type=int, default=200)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    top = git(root, "rev-parse", "--show-toplevel")
    if not top:
        note = "not a git repository: %s" % root
        print(json.dumps({"since": None, "root": root, "commits": [],
                          "by_category": {}, "note": note}, indent=2)
              if args.json else "NOTE: " + note + " (nothing to report)")
        return 0

    since, since_source = (args.since, "arg") if args.since \
        else default_since(root)

    watch = args.watch
    if not watch:
        try:
            with open(os.path.join(root, args.config)) as fh:
                watch = json.load(fh).get("repo", {}).get("watch_paths")
        except (OSError, ValueError, AttributeError):
            watch = None
    watch = watch or DEFAULT_WATCH
    exclude = (args.exclude or []) + [".seo/**"]
    watch_rx = [(p, glob_to_regex(p)) for p in watch]
    exclude_rx = [(p, glob_to_regex(p)) for p in exclude]

    commits = collect(root, since, watch_rx, exclude_rx, args.max_commits)
    by_category = {}
    for c in commits:
        for f in c["files"]:
            by_category[f["category"]] = by_category.get(f["category"], 0) + 1

    if args.json:
        print(json.dumps({"since": since, "since_source": since_source,
                          "root": root, "commits": commits,
                          "by_category": by_category}, indent=2))
        return 0

    print("since %s (%s), %d commits touched watched paths"
          % (since, since_source, len(commits)))
    if not commits:
        print("No product changes in watched paths.")
        return 0
    for cat in CATEGORIES:
        hits = [c for c in commits if any(f["category"] == cat
                                          for f in c["files"])]
        if not hits:
            continue
        print("\n%s: %d files in %d commits" % (cat, by_category[cat],
                                                 len(hits)))
        for c in hits:
            print("  %s %s %s%s" % (c["sha"][:7], c["date"][:10],
                                    c["subject"],
                                    "  [removal?]" if c["removal_hint"]
                                    else ""))
            for f in c["files"]:
                if f["category"] == cat:
                    print("    %s" % f["path"])
            if cat == "changelog":
                for line in c["changelog_lines"]:
                    print("      + %s" % line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
