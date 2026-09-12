#!/usr/bin/env python3
"""Mechanical check that the site's live copy agrees with the truth ledger.

A truth ledger only helps if something reads it. This turns each claim in
.seo/truth.md into grep rules and runs them over the pages that make the claim,
so a contradiction ("families pay $9/month" on one landing page while the rest
of the site says free) is caught by a script instead of by a customer.

Two kinds of failure, both fatal:
  CONTRADICTION  a must_not_match pattern matched somewhere. The page says
                 something the ledger says is false.
  MISSING        a must_match pattern matched in zero files (or zero pages).
                 The claim the ledger says we make is not actually made.

Two places the copy can live, checked the same way:
  file mode  --root: the rule's paths globs are expanded over the repo.
  page mode  --from-health: the same rules run over the visible body text of
             every page in a health_diff.py fingerprint written with
             --keep-text. This is the only mode that sees copy stored in a
             database or CMS. A page whose fingerprint has no body_text is
             reported as unchecked, never as clean.

Usage
  truth_check.py --rules .seo/truth-checks.json
  truth_check.py --rules .seo/truth-checks.json --root web --json
  truth_check.py --rules .seo/truth-checks.json --from-health .seo/health/2026-09-10.json
  truth_check.py --rules .seo/truth-checks.json --root web \
      --from-health .seo/health/2026-09-10.json

Rules file: a JSON list of
  {"claim": "Free for families",
   "paths": ["web/app/frontend/pages/**/*.tsx", "web/public/llms.txt"],
   "urls": ["/pricing", "/library/guides/*"],
   "must_not_match": ["families pay", "\\$\\d+ ?(/|per) ?month"],
   "must_match": ["free for families"],
   "flags": "i"}

Globs in paths are relative to --root and support recursive **. In page mode
both paths and urls are matched against each page's URL path (/pricing) and
its full URL. Standard library only.
"""

import argparse
import fnmatch
import glob
import json
import os
import re
import sys
import urllib.parse

MAX_BYTES = 4_000_000
FLAG_MAP = {"i": re.I, "m": re.M, "s": re.S, "x": re.X}
UNCHECKED_REASON = "run health_diff.py --keep-text"


def compile_flags(spec):
    flags = 0
    for ch in (spec or ""):
        flags |= FLAG_MAP.get(ch.lower(), 0)
    return flags


def compile_rule(rule):
    flags = compile_flags(rule.get("flags"))
    must = [(p, re.compile(p, flags)) for p in rule.get("must_match") or []]
    must_not = [(p, re.compile(p, flags))
                for p in rule.get("must_not_match") or []]
    return must, must_not


def expand(paths, root):
    """Resolve globs to a sorted, deduped list of readable files."""
    out, seen = [], set()
    for pattern in paths or []:
        pat = pattern if os.path.isabs(pattern) else os.path.join(root, pattern)
        for hit in sorted(glob.glob(pat, recursive=True)):
            if not os.path.isfile(hit):
                continue
            real = os.path.realpath(hit)
            if real in seen:
                continue
            seen.add(real)
            out.append(hit)
    return out


def read_text(path):
    """None for anything that is not readable text — binaries are not copy."""
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return None
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    if b"\x00" in raw[:4096]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", "replace")


def load_pages(paths):
    """{url: record} merged from one or more health_diff.py fingerprints."""
    pages = {}
    for path in paths:
        with open(path) as fh:
            data = json.load(fh)
        got = data.get("pages") if isinstance(data, dict) else None
        if not isinstance(got, dict):
            raise ValueError("%s has no pages object" % path)
        pages.update(got)
    return pages


def url_matches(url, globs):
    """A glob hits on the URL path (/pricing, with or without a trailing
    slash) or on the full URL, so both '/library/guides/*' and
    'https://example.com/pricing' work as written."""
    try:
        path = urllib.parse.urlsplit(url).path or "/"
    except ValueError:
        path = url
    cands = {url, path}
    if len(path) > 1:
        cands.add(path.rstrip("/"))
    return any(fnmatch.fnmatchcase(c, g) for c in cands for g in globs)


def snippet(text, m, pad=80):
    start, end = max(0, m.start() - pad), min(len(text), m.end() + pad)
    s = text[start:end].strip()
    return (("…" if start else "") + s
            + ("…" if end < len(text) else ""))[:200]


def check_files(claim, must, must_not, files, root, contradictions, missing):
    found = {p: 0 for p, _ in must}
    for path in files:
        text = read_text(path)
        if text is None:
            continue
        rel = os.path.relpath(path, root)
        for pattern, rx in must:
            if rx.search(text):
                found[pattern] += 1
        if not must_not:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for pattern, rx in must_not:
                m = rx.search(line)
                if m:
                    contradictions.append({
                        "kind": "file", "claim": claim, "pattern": pattern,
                        "file": rel, "line": lineno,
                        "text": (m.group(0) or "").strip()[:160],
                        "context": line.strip()[:200],
                    })
    for pattern, _ in must:
        if found[pattern] == 0:
            missing.append({"kind": "file", "claim": claim, "pattern": pattern,
                            "files_scanned": len(files)})


def check_pages(claim, must, must_not, urls, pages, contradictions, missing,
                unchecked):
    found = {p: 0 for p, _ in must}
    scanned = 0
    for url in urls:
        text = (pages.get(url) or {}).get("body_text")
        if not isinstance(text, str):
            unchecked[url] = {"kind": "page", "url": url,
                              "reason": UNCHECKED_REASON}
            continue
        scanned += 1
        for pattern, rx in must:
            if rx.search(text):
                found[pattern] += 1
        for pattern, rx in must_not:
            for m in rx.finditer(text):
                contradictions.append({
                    "kind": "page", "claim": claim, "pattern": pattern,
                    "url": url,
                    "text": (m.group(0) or "").strip()[:160],
                    "context": snippet(text, m),
                })
    # Pages without body_text are unchecked, not clean: a claim cannot be
    # missing from copy nobody read.
    if scanned:
        for pattern, _ in must:
            if found[pattern] == 0:
                missing.append({"kind": "page", "claim": claim,
                                "pattern": pattern, "pages_scanned": scanned})


def run(rules, root, pages):
    """root=None skips file mode, pages=None skips page mode."""
    contradictions, missing, unresolved, unchecked = [], [], [], {}

    for rule in rules:
        claim = rule.get("claim") or "(unnamed claim)"
        must, must_not = compile_rule(rule)
        files = expand(rule.get("paths"), root) if root is not None else []
        urls = []
        if pages is not None:
            globs = (rule.get("paths") or []) + (rule.get("urls") or [])
            urls = [u for u in sorted(pages) if url_matches(u, globs)]

        if not files and not urls:
            row = {"claim": claim, "paths": rule.get("paths") or [],
                   "urls": rule.get("urls") or []}
            if root is not None:
                unresolved.append(dict(row, kind="file",
                                       reason="no files matched"))
            if pages is not None:
                unresolved.append(dict(row, kind="page",
                                       reason="no pages matched"))
            continue
        if files:
            check_files(claim, must, must_not, files, root,
                        contradictions, missing)
        if urls:
            check_pages(claim, must, must_not, urls, pages,
                        contradictions, missing, unchecked)

    return (contradictions, missing, unresolved,
            [unchecked[u] for u in sorted(unchecked)])


def where(row):
    if row["kind"] == "file":
        return "[file] %s:%d" % (row["file"], row["line"])
    return "[page] %s" % row["url"]


def main():
    ap = argparse.ArgumentParser(
        description="Check live copy against the truth ledger. "
                    "Exits 1 on any contradiction or missing claim.")
    ap.add_argument("--rules", default=".seo/truth-checks.json")
    ap.add_argument("--root",
                    help="glob root for file mode (default: cwd, unless "
                         "--from-health is given without --root)")
    ap.add_argument("--from-health", action="append", default=[],
                    metavar="FINGERPRINT",
                    help="health_diff.py fingerprint JSON written with "
                         "--keep-text; run the rules over each matching "
                         "page's body_text (repeatable)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        with open(args.rules) as fh:
            rules = json.load(fh)
    except Exception as ex:  # noqa: BLE001
        print("could not read rules file %s: %s" % (args.rules, ex),
              file=sys.stderr)
        print("SUMMARY: 0 rules, 0 contradictions, 0 missing")
        return 1
    if isinstance(rules, dict):
        rules = rules.get("rules") or []
    if not isinstance(rules, list):
        print("rules file must be a JSON list of rule objects", file=sys.stderr)
        print("SUMMARY: 0 rules, 0 contradictions, 0 missing")
        return 1

    root = None
    if args.root is not None or not args.from_health:
        root = os.path.abspath(args.root or ".")
    pages = None
    if args.from_health:
        try:
            pages = load_pages(args.from_health)
        except Exception as ex:  # noqa: BLE001
            print("could not read fingerprint: %s" % ex, file=sys.stderr)
            print("SUMMARY: 0 rules, 0 contradictions, 0 missing")
            return 1

    contradictions, missing, unresolved, unchecked = run(rules, root, pages)

    summary = "SUMMARY: %d rules, %d contradictions, %d missing" % (
        len(rules), len(contradictions), len(missing))
    if pages is not None:
        summary += ", %d unchecked" % len(unchecked)

    if args.json:
        print(json.dumps({
            "rules": len(rules), "root": root, "rules_file": args.rules,
            "health_files": args.from_health,
            "contradictions": contradictions, "missing": missing,
            "unresolved_paths": unresolved, "unchecked": unchecked,
            "summary": {"rules": len(rules),
                        "contradictions": len(contradictions),
                        "missing": len(missing),
                        "unchecked": len(unchecked)},
        }, indent=2))
    else:
        if contradictions:
            print("CONTRADICTIONS (%d)" % len(contradictions))
            for c in contradictions:
                print("  %s" % where(c))
                print("    claim:   %s" % c["claim"])
                print("    pattern: %s" % c["pattern"])
                print("    matched: %s" % c["text"])
                if c["kind"] == "page":
                    print("    around:  %s" % c["context"])
            print("")
        if missing:
            print("MISSING (%d)" % len(missing))
            for m in missing:
                if m["kind"] == "file":
                    print("  [file] claim %r: pattern %s matched in 0 of %d files"
                          % (m["claim"], m["pattern"], m["files_scanned"]))
                else:
                    print("  [page] claim %r: pattern %s matched in 0 of %d pages"
                          % (m["claim"], m["pattern"], m["pages_scanned"]))
            print("")
        if unchecked:
            print("UNCHECKED PAGES (%d) — no body_text in the fingerprint, %s"
                  % (len(unchecked), UNCHECKED_REASON))
            for u in unchecked:
                print("  [page] %s" % u["url"])
            print("")
        if unresolved:
            print("UNRESOLVED PATHS (%d) — globs that matched nothing"
                  % len(unresolved))
            for u in unresolved:
                print("  [%s] claim %r: %s"
                      % (u["kind"], u["claim"], ", ".join(u["paths"] + u["urls"])))
            print("")
        if not contradictions and not missing:
            print("No contradictions, no missing claims.")
            print("")

    print(summary, file=sys.stderr if args.json else sys.stdout)
    return 1 if (contradictions or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
