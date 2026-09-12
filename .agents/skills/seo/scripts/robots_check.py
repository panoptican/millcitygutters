#!/usr/bin/env python3
"""Audit robots.txt and llms.txt for AI crawler access.

  python3 robots_check.py --url https://example.com
  python3 robots_check.py --url https://example.com --path /pricing --out robots.json
  python3 robots_check.py --file ./public/robots.txt --url https://example.com

Reports, per known AI agent, whether it is allowed, which rule decided it, and
what blocking that agent actually costs. Separates retrieval agents (blocking
removes you from answers) from training agents (a business decision).

Also validates llms.txt if one exists: structure, whether the pages it points at
still resolve, and whether they appear in the sitemap. A file of dead links is
worse than no file, and nobody notices because nothing reports on it. llms.txt
remains low priority either way. See references/technical.md section 2.

Standard library only.
"""

import argparse
import collections
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agents import AGENTS  # noqa: E402
import sitemap as sitemap_mod  # noqa: E402

UA = "Mozilla/5.0 (compatible; aeo-skill-robots-check/1.0)"
TIMEOUT = 20
MAX_LLMS_LINKS = 20  # cap on liveness checks, so this stays a cheap free check
MAX_READ = 2 * 1024 * 1024  # llms-full.txt is routinely tens of MB. We only need its shape.


def fetch(url, max_bytes=MAX_READ):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read(max_bytes)
            declared = r.headers.get("Content-Length")
            size = int(declared) if declared and declared.isdigit() else len(raw)
            # A full buffer means the body did not fit, so the size is a floor.
            return r.status, raw.decode("utf-8", "replace"), size, len(raw) >= max_bytes
    except urllib.error.HTTPError as e:
        return e.code, "", 0, False
    except Exception as e:  # noqa: BLE001
        return None, str(e), 0, False


def parse_robots(text):
    """Return [{'agents': [...], 'rules': [(allow_bool, pattern), ...]}, ...]."""
    groups = []
    current = None
    starting_group = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field = field.strip().lower()
        value = value.strip()
        if field == "user-agent":
            if current is None or not starting_group:
                current = {"agents": [], "rules": []}
                groups.append(current)
                starting_group = True
            current["agents"].append(value)
        elif field in ("allow", "disallow"):
            if current is None:
                current = {"agents": ["*"], "rules": []}
                groups.append(current)
            starting_group = False
            current["rules"].append((field == "allow", value))
    return groups


def path_match(pattern, path):
    """robots.txt path matching with * wildcard and $ end anchor."""
    if pattern == "":
        return False
    anchored = pattern.endswith("$")
    pat = pattern[:-1] if anchored else pattern
    parts = pat.split("*")
    pos = 0
    for i, part in enumerate(parts):
        if part == "":
            continue
        if i == 0:
            if not path.startswith(part):
                return False
            pos = len(part)
        else:
            idx = path.find(part, pos)
            if idx == -1:
                return False
            pos = idx + len(part)
    if anchored:
        if parts[-1] == "":
            return True
        return path.endswith(parts[-1]) and pos == len(path)
    return True


def pick_group(groups, agent):
    """Exact case-insensitive match, then prefix match, then the wildcard group.

    The prefix pass refuses to match across a hyphen boundary, so a rule for
    "Applebot" does not silently capture "Applebot-Extended". Those are distinct
    product tokens with distinct meanings and conflating them inverts the advice.
    """
    low = agent.lower()
    for g in groups:
        for a in g["agents"]:
            if a.lower() == low:
                return g, a
    for g in groups:
        for a in g["agents"]:
            al = a.lower()
            if al != "*" and low.startswith(al) and not low[len(al):].startswith("-"):
                return g, a
    for g in groups:
        for a in g["agents"]:
            if a == "*":
                return g, "*"
    return None, None


def evaluate(groups, agent, path):
    group, matched_ua = pick_group(groups, agent)
    if group is None:
        return True, "no matching group, default allow", None
    best = None  # (length, allow_bool, pattern)
    for allow, pattern in group["rules"]:
        if path_match(pattern, path):
            ln = len(pattern.rstrip("$"))
            if best is None or ln > best[0] or (ln == best[0] and allow):
                best = (ln, allow, pattern)
    if best is None:
        return True, "no matching rule, default allow", matched_ua
    verb = "Allow" if best[1] else "Disallow"
    return best[1], "%s: %s" % (verb, best[2]), matched_ua


def head(url):
    """Return a status code for a URL. HEAD first, GET if the server refuses HEAD."""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method=method)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if e.code in (403, 405, 501) and method == "HEAD":
                continue
            return e.code
        except Exception:  # noqa: BLE001
            return None
    return None


def validate_llmstxt(text):
    """Structural check of an llms.txt against the convention's shape."""
    lines = text.splitlines()
    stripped = [l.strip() for l in lines]
    links = []
    for line in stripped:
        m = re.match(r"^[-*]\s*\[([^\]]*)\]\(([^)]+)\)\s*:?\s*(.*)$", line)
        if m:
            links.append({"title": m.group(1).strip(), "url": m.group(2).strip(),
                          "description": m.group(3).strip() or None})

    out = {
        "has_title": bool(stripped and stripped[0].startswith("# ")),
        "title": stripped[0][2:].strip() if stripped and stripped[0].startswith("# ") else None,
        "has_summary": any(l.startswith("> ") for l in stripped[:10]),
        "sections": [l[3:].strip() for l in stripped if l.startswith("## ")],
        "links": links,
        "links_without_description": sum(1 for l in links if not l["description"]),
        "issues": [],
    }
    if not out["has_title"]:
        out["issues"].append("no '# Name' title on the first line")
    if not out["has_summary"]:
        out["issues"].append("no '> one-sentence summary' blockquote near the top")
    if not out["sections"]:
        out["issues"].append("no '## Section' headings, so the file has no shape")
    if not links:
        out["issues"].append("no '- [Title](url): description' links, which is the whole point of the file")
    elif out["links_without_description"]:
        out["issues"].append(
            "%d of %d links carry no description, which is the part that tells a reader "
            "what the page covers" % (out["links_without_description"], len(links)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="site root, e.g. https://example.com")
    ap.add_argument("--file", help="read robots.txt from a local path instead of fetching")
    ap.add_argument("--path", default="/", help="path to test access for (default /)")
    ap.add_argument("--out", help="write JSON here")
    ap.add_argument("--no-llms-links", action="store_true",
                    help="skip liveness and sitemap checks on llms.txt links")
    args = ap.parse_args()

    root = args.url.rstrip("/")

    if args.file:
        with open(args.file, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        status, source = 200, args.file
    else:
        status, text, _size, _trunc = fetch(root + "/robots.txt")
        source = root + "/robots.txt"

    result = {
        "site": root,
        "path_tested": args.path,
        "robots_source": source,
        "robots_status": status,
        "robots_present": status == 200,
        "agents": [],
        "llms_txt": {},
        "notes": [],
    }

    if status != 200:
        result["notes"].append(
            "No robots.txt found (status %s). Everything is allowed by default, "
            "which is fine for AEO. Check for blocks at the CDN or in headers instead." % status
        )
        groups = []
    else:
        groups = parse_robots(text)
        if not groups:
            result["notes"].append("robots.txt fetched but contains no parseable groups.")

    for name, vendor, kind, desc in AGENTS:
        allowed, rule, matched_ua = evaluate(groups, name, args.path) if groups else (True, "no robots.txt", None)
        result["agents"].append({
            "agent": name, "vendor": vendor, "kind": kind, "purpose": desc,
            "allowed": allowed, "matched_rule": rule, "matched_user_agent": matched_ua,
        })

    known = {n.lower() for n, _v, _k, _d in AGENTS} | {"*"}
    declared = []
    for g in groups:
        for a in g["agents"]:
            if a.lower() not in known and a not in declared:
                declared.append(a)
    result["unrecognised_user_agents"] = declared
    if declared:
        result["notes"].append(
            "robots.txt names user agents not in this list: %s. Look them up before "
            "assuming they are irrelevant, and check for typos in agent names, which "
            "silently do nothing." % ", ".join(declared)
        )

    for fname in ("llms.txt", "llms-full.txt"):
        st, body, size, truncated = fetch(root + "/" + fname)
        info = {"present": st == 200, "status": st, "bytes": size if st == 200 else 0,
                "read_truncated": bool(st == 200 and truncated)}
        if st == 200 and fname == "llms.txt":
            info.update(validate_llmstxt(body))
            links = info["links"]
            if args.no_llms_links or not links:
                info["link_check"] = None
            else:
                checked = links[:MAX_LLMS_LINKS]
                dead, offsite = [], []
                for link in checked:
                    target = urllib.parse.urljoin(root + "/", link["url"])
                    code = head(target)
                    link["status"] = code
                    if code != 200:
                        dead.append({"url": target, "status": code})
                    if urllib.parse.urlsplit(target).netloc.lower() != \
                            urllib.parse.urlsplit(root).netloc.lower():
                        offsite.append(target)
                sm = sitemap_mod.collect(root)
                sm_set = {sitemap_mod.normalise(u) for u in sm["urls"]}
                root_host = urllib.parse.urlsplit(root).netloc.lower()
                sm_hosts = collections.Counter(
                    urllib.parse.urlsplit(u).netloc.lower() for u in sm_set)
                sm_same_host = sm_hosts.get(root_host, 0)

                # Three ways the cross-reference is not trustworthy, each reported as
                # UNKNOWN rather than as a finding. A false orphan reads as a real one.
                unknown = None
                if not sm_set:
                    unknown = "no sitemap URLs read"
                elif sm["truncated"]:
                    unknown = "sitemap read was truncated, so an absent link may simply be unread"
                elif sm_same_host == 0:
                    unknown = ("the sitemap lists %s, not %s, so the two files describe "
                               "different hosts" % (sm_hosts.most_common(1)[0][0], root_host))

                missing = None
                if unknown is None:
                    missing = [sitemap_mod.normalise(urllib.parse.urljoin(root + "/", l["url"]))
                               for l in checked
                               if sitemap_mod.normalise(urllib.parse.urljoin(root + "/", l["url"]))
                               not in sm_set]

                info["link_check"] = {
                    "checked": len(checked),
                    "total": len(links),
                    "dead": dead,
                    "offsite": offsite,
                    "sitemap_urls_read": len(sm_set),
                    "sitemap_same_host": sm_same_host,
                    "sitemap_notes": sm["notes"],
                    "absent_from_sitemap": missing,
                    "sitemap_comparison_unknown": unknown,
                }
                if dead:
                    info["issues"].append(
                        "%d of %d checked links do not return 200. A file of dead links is "
                        "worse than no file." % (len(dead), len(checked)))
                if unknown:
                    info["issues"].append(
                        "sitemap cross-reference is UNKNOWN, not clean: %s" % unknown)
                elif missing:
                    info["issues"].append(
                        "%d of %d checked link(s) are not in the sitemap, so the two files "
                        "disagree about what matters." % (len(missing), len(checked)))
        result["llms_txt"][fname] = info

    blocked_retrieval = [a for a in result["agents"] if a["kind"] == "retrieval" and not a["allowed"]]
    blocked_user = [a for a in result["agents"] if a["kind"] == "user" and not a["allowed"]]
    blocked_training = [a for a in result["agents"] if a["kind"] == "training" and not a["allowed"]]

    result["summary"] = {
        "retrieval_blocked": [a["agent"] for a in blocked_retrieval],
        "user_triggered_blocked": [a["agent"] for a in blocked_user],
        "training_blocked": [a["agent"] for a in blocked_training],
        "verdict": "FAIL" if blocked_retrieval else ("REVIEW" if blocked_user else "PASS"),
    }
    if blocked_retrieval:
        result["notes"].append(
            "Retrieval agents blocked: %s. These remove you from those engines' answers."
            % ", ".join(a["agent"] for a in blocked_retrieval)
        )
    if blocked_training:
        result["notes"].append(
            "Training agents blocked: %s. Legitimate business decision. Does not affect today's answers."
            % ", ".join(a["agent"] for a in blocked_training)
        )
    if result["llms_txt"]["llms.txt"]["present"]:
        result["notes"].append(
            "llms.txt findings are low priority. No major answer engine has publicly "
            "committed to consuming it. Fix dead links because they are cheap to fix, "
            "not because the file is a lever.")
    result["notes"].append(
        "robots.txt is not the only place access is denied. Check CDN bot rules, WAF rules, "
        "X-Robots-Tag headers and rate limiting. If logs show zero hits from an agent this "
        "report says is allowed, the block is somewhere else."
    )

    width = max(len(a["agent"]) for a in result["agents"])
    print("robots.txt: %s (%s)" % (source, status))
    print("path tested: %s\n" % args.path)
    for kind in ("retrieval", "user", "training"):
        rows = [a for a in result["agents"] if a["kind"] == kind]
        print("[%s]" % kind)
        for a in rows:
            print("  %-*s  %-7s  %-28s  %s" % (
                width, a["agent"],
                "ALLOW" if a["allowed"] else "BLOCK",
                a["matched_rule"][:28], a["purpose"]))
        print()
    for fname, info in result["llms_txt"].items():
        if info["present"]:
            state = "present (%s%d bytes%s)" % (
                ">= " if info["read_truncated"] else "", info["bytes"],
                ", read capped" if info["read_truncated"] else "")
        else:
            state = "absent"
        print("%-14s %s" % (fname, state))
        for issue in info.get("issues", []):
            print("%-14s   issue: %s" % ("", issue))
        lc = info.get("link_check")
        if lc:
            print("%-14s   %d/%d links checked, %d dead, %s"
                  % ("", lc["checked"], lc["total"], len(lc["dead"]),
                     "%d absent from sitemap" % len(lc["absent_from_sitemap"])
                     if lc["absent_from_sitemap"] is not None else "sitemap UNKNOWN"))
            for d in lc["dead"][:5]:
                print("%-14s     %-6s %s" % ("", d["status"], d["url"]))
    print("\nverdict: %s" % result["summary"]["verdict"])
    for n in result["notes"]:
        print("  note: %s" % n)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        print("\nwrote %s" % args.out)

    return 1 if result["summary"]["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
