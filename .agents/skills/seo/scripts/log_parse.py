#!/usr/bin/env python3
"""AI crawler hits and AI referral traffic, from server or CDN logs.

  python3 log_parse.py --logs /var/log/nginx/access.log --out logs.json
  python3 log_parse.py --logs ./logs/ --since 2026-08-01 --out logs.json
  python3 log_parse.py --logs access.log --referrals

Handles combined/common log format and JSON-lines CDN logs. Reports crawler hits
by agent, by day and by path, plus referral clicks from answer-engine hosts.

Join the crawler output to your citation data. That join is the diagnostic:
  crawled and cited        working
  crawled and never cited  reachable but not chosen. credibility or relevance.
  never crawled            reachable is failing. fix that before anything else.

Standard library only.
"""

import argparse
import collections
import glob
import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agents import classify, referrer_engine  # noqa: E402

COMBINED = re.compile(
    r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<ts>[^\]]+)\]\s+'
    r'"(?P<method>[A-Z]+)\s+(?P<path>[^"\s]*)(?:\s+[^"]*)?"\s+'
    r'(?P<status>\d{3})\s+(?P<bytes>\S+)'
    r'(?:\s+"(?P<referrer>[^"]*)"\s+"(?P<ua>[^"]*)")?'
)

MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}

JSON_UA_KEYS = ("user_agent", "userAgent", "ua", "ClientRequestUserAgent", "http_user_agent")
JSON_PATH_KEYS = ("path", "uri", "url", "ClientRequestURI", "request_uri", "cs_uri_stem")
JSON_REF_KEYS = ("referer", "referrer", "ClientRequestReferer", "http_referer")
JSON_TS_KEYS = ("timestamp", "time", "datetime", "EdgeStartTimestamp", "@timestamp")
JSON_STATUS_KEYS = ("status", "EdgeResponseStatus", "response_status", "sc_status")


def pick(d, keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def day_from_clf(ts):
    # 26/Aug/2026:13:45:01 +0000
    try:
        d, mon, rest = ts.split("/", 2)
        year = rest.split(":", 1)[0]
        return "%s-%02d-%02d" % (year, MONTHS[mon], int(d))
    except Exception:  # noqa: BLE001
        return None


def day_from_any(value):
    if value is None:
        return None
    s = str(value)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return "%s-%s-%s" % m.groups()
    if "/" in s:
        return day_from_clf(s)
    if s.isdigit():
        import datetime
        n = int(s)
        for div in (1, 1000, 1000000, 1000000000):
            try:
                dt = datetime.datetime.utcfromtimestamp(n / div)
                if 2000 < dt.year < 2100:
                    return dt.strftime("%Y-%m-%d")
            except Exception:  # noqa: BLE001
                continue
    return None


def parse_line(line):
    line = line.strip()
    if not line:
        return None
    if line.startswith("{"):
        try:
            d = json.loads(line)
        except Exception:  # noqa: BLE001
            return None
        return {
            "ua": pick(d, JSON_UA_KEYS) or "",
            "path": pick(d, JSON_PATH_KEYS) or "",
            "referrer": pick(d, JSON_REF_KEYS) or "",
            "status": str(pick(d, JSON_STATUS_KEYS) or ""),
            "day": day_from_any(pick(d, JSON_TS_KEYS)),
        }
    m = COMBINED.match(line)
    if not m:
        return None
    g = m.groupdict()
    return {
        "ua": g.get("ua") or "",
        "path": g.get("path") or "",
        "referrer": g.get("referrer") or "",
        "status": g.get("status") or "",
        "day": day_from_clf(g.get("ts") or ""),
    }


def iter_lines(paths):
    for path in paths:
        opener = gzip.open if path.endswith(".gz") else open
        try:
            with opener(path, "rt", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    yield line
        except Exception as e:  # noqa: BLE001
            print("skip %s: %s" % (path, e), file=sys.stderr)


def expand(spec):
    out = []
    for s in spec:
        if os.path.isdir(s):
            for ext in ("*.log", "*.log.gz", "*.json", "*.jsonl", "*.txt"):
                out += sorted(glob.glob(os.path.join(s, "**", ext), recursive=True))
        else:
            out += sorted(glob.glob(s)) or [s]
    return [p for p in out if os.path.isfile(p)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", nargs="+", required=True, help="file, directory or glob")
    ap.add_argument("--since", help="YYYY-MM-DD, ignore earlier lines")
    ap.add_argument("--referrals", action="store_true", help="show referral detail too")
    ap.add_argument("--top", type=int, default=25, help="rows per table")
    ap.add_argument("--out", help="write JSON here")
    args = ap.parse_args()

    paths = expand(args.logs)
    if not paths:
        print("no log files matched", file=sys.stderr)
        return 2

    bot_hits = collections.Counter()          # agent
    bot_by_day = collections.defaultdict(collections.Counter)
    bot_paths = collections.defaultdict(collections.Counter)
    bot_status = collections.defaultdict(collections.Counter)
    ref_hits = collections.Counter()          # engine
    ref_paths = collections.defaultdict(collections.Counter)
    ref_by_day = collections.defaultdict(collections.Counter)
    total = parsed = 0

    for line in iter_lines(paths):
        total += 1
        rec = parse_line(line)
        if not rec:
            continue
        parsed += 1
        if args.since and rec["day"] and rec["day"] < args.since:
            continue
        hit = classify(rec["ua"])
        if hit:
            name, _vendor, _kind = hit
            bot_hits[name] += 1
            if rec["day"]:
                bot_by_day[name][rec["day"]] += 1
            bot_paths[name][rec["path"].split("?")[0]] += 1
            bot_status[name][rec["status"]] += 1
        eng = referrer_engine(rec["referrer"])
        if eng:
            ref_hits[eng] += 1
            ref_paths[eng][rec["path"].split("?")[0]] += 1
            if rec["day"]:
                ref_by_day[eng][rec["day"]] += 1

    result = {
        "files": paths,
        "lines_read": total,
        "lines_parsed": parsed,
        "since": args.since,
        "crawlers": {
            name: {
                "hits": n,
                "by_day": dict(sorted(bot_by_day[name].items())),
                "top_paths": bot_paths[name].most_common(args.top),
                "status_codes": dict(bot_status[name]),
            } for name, n in bot_hits.most_common()
        },
        "referrals": {
            eng: {
                "clicks": n,
                "by_day": dict(sorted(ref_by_day[eng].items())),
                "top_landing_pages": ref_paths[eng].most_common(args.top),
            } for eng, n in ref_hits.most_common()
        },
    }

    print("files: %d · lines read: %d · parsed: %d (%.0f%%)"
          % (len(paths), total, parsed, 100.0 * parsed / max(total, 1)))
    if parsed < total * 0.5:
        print("WARNING: under half the lines parsed. The log format may be unsupported.")
        print("         Check a sample line and adapt, rather than trusting these counts.")

    print("\nAI crawler hits")
    if not bot_hits:
        print("  none found. That is a finding: either the logs do not cover a period")
        print("  with crawler activity, or the agents are being turned away before")
        print("  they reach the app. Check CDN and WAF rules.")
    for name, n in bot_hits.most_common():
        days = len(bot_by_day[name])
        errs = sum(v for k, v in bot_status[name].items() if k and not k.startswith("2"))
        print("  %-22s %8d hits · %3d days · %d non-2xx" % (name, n, days, errs))

    print("\nAI referral clicks")
    if not ref_hits:
        print("  none found. Small or zero volume is normal. Most influence never")
        print("  produces a click. Read direct traffic alongside this.")
    for eng, n in ref_hits.most_common():
        print("  %-22s %8d clicks" % (eng, n))

    if args.referrals:
        for eng, n in ref_hits.most_common():
            print("\n  %s landing pages" % eng)
            for path, c in ref_paths[eng].most_common(args.top):
                print("    %6d  %s" % (c, path))

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        print("\nwrote %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
