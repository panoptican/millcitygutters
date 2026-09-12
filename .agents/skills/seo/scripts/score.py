#!/usr/bin/env python3
"""Roll raw answer-engine responses into a scoreboard, with honest intervals.

  python3 score.py --run .seo/aeo/runs/2026-08-26 --brand "Acme" --out .seo/aeo/scoreboard.md
  python3 score.py --run .seo/aeo/runs/2026-08-26 --prev .seo/aeo/runs/2026-07-29 \
                   --brand "Acme" --prompts .seo/aeo/prompts.json --out .seo/aeo/scoreboard.md

Reads <run>/responses.jsonl, one JSON object per line:

  {"prompt_id":"disc-crm-01","platform":"chat_gpt","sample":1,"type":"discovery",
   "attribute":"CRM for agencies","priority":1,
   "text":"...","citations":["https://..."],"brands":["Acme","Rival"],
   "self_mentioned":true,"self_position":3}

  capability records add: "capability":"yes"|"no"|"soft"
  head-to-head records add: "winner":"Acme"|"Rival"|"draw"

`type`, `attribute` and `priority` may be omitted if --prompts is given; they are
looked up by prompt_id.

Every rate is printed with its sample size and a 95% Wilson interval. Run-over-run
changes are marked real only when the difference exceeds the interval on the
difference. See references/measurement.md.

Standard library only.
"""

import argparse
import collections
import json
import math
import os
import sys

Z = 1.96
DISCOVERY_PRESENT = 0.20   # mention rate at or above this counts as "present"
CAPABILITY_PRESENT = 0.50  # share of capability answers that are a firm yes


def wilson(k, n):
    """95% Wilson score interval for k successes in n trials. Returns (low, high)."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / d
    half = (Z / d) * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def diff_is_real(k1, n1, k2, n2):
    """True when the difference between two rates exceeds its own 95% interval."""
    if n1 == 0 or n2 == 0:
        return False, 0.0
    p1, p2 = k1 / n1, k2 / n2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    if se == 0:
        return (p2 != p1), abs(p2 - p1)
    return abs(p2 - p1) > Z * se, Z * se


def load_prompts(path):
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {p["id"]: p for p in data.get("prompts", [])}


def load_run(run_dir, index):
    path = os.path.join(run_dir, "responses.jsonl")
    if not os.path.exists(path):
        sys.exit("no responses.jsonl in %s" % run_dir)
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception as e:  # noqa: BLE001
                print("skip %s:%d %s" % (path, lineno, e), file=sys.stderr)
                continue
            meta = index.get(rec.get("prompt_id"), {})
            rec.setdefault("type", meta.get("type", "discovery"))
            rec.setdefault("attribute", meta.get("attribute", "unassigned"))
            rec.setdefault("priority", meta.get("priority", 3))
            if rec.get("failed"):
                continue
            out.append(rec)
    return out


def tally(records, brand):
    """Return {attribute: {...}} with discovery, capability and platform detail."""
    attrs = collections.defaultdict(lambda: {
        "priority": 3,
        "disc_n": 0, "disc_k": 0,
        "platforms": collections.defaultdict(lambda: {"n": 0, "k": 0}),
        "brand_counts": collections.Counter(),
        "positions": [],
        "cap_yes": 0, "cap_soft": 0, "cap_no": 0,
        "h2h": collections.Counter(),
        "citations": collections.Counter(),
    })
    blow = brand.lower()
    for r in records:
        a = attrs[r["attribute"]]
        a["priority"] = min(a["priority"], r.get("priority", 3))
        for url in r.get("citations", []) or []:
            a["citations"][url] += 1
        t = r.get("type")
        if t == "discovery":
            a["disc_n"] += 1
            pf = a["platforms"][r.get("platform", "unknown")]
            pf["n"] += 1
            hit = r.get("self_mentioned")
            if hit is None:
                hit = any(blow in str(b).lower() for b in r.get("brands", []))
            if hit:
                a["disc_k"] += 1
                pf["k"] += 1
                if r.get("self_position"):
                    a["positions"].append(r["self_position"])
            for b in r.get("brands", []) or []:
                a["brand_counts"][str(b)] += 1
        elif t == "capability":
            v = (r.get("capability") or "").lower()
            if v == "yes":
                a["cap_yes"] += 1
            elif v == "soft":
                a["cap_soft"] += 1
            elif v == "no":
                a["cap_no"] += 1
        elif t in ("head-to-head", "competitor", "h2h"):
            a["h2h"][r.get("winner") or "draw"] += 1
    return attrs


def rank_and_sov(counts, brand):
    """Competition ranking: tied brands share a rank. Insertion order is not a result.

    Returns (rank, share_of_voice, ordered_counts, tied_with). A rank reported without
    its tie count reads as a standing you do not have.
    """
    if not counts:
        return None, 0.0, [], 0
    ordered = counts.most_common()
    total = sum(counts.values())
    blow = brand.lower()
    mine = None
    for name, n in ordered:
        if blow in name.lower():
            mine = n
            break
    if mine is None:
        return None, 0.0, ordered, 0
    rank = 1 + sum(1 for _name, n in ordered if n > mine)
    tied = sum(1 for name, n in ordered if n == mine and blow not in name.lower())
    return rank, (mine / total if total else 0.0), ordered, tied


def route(disc_rate, disc_n, cap_yes, cap_soft, cap_no, rank=None, tied=0, mean_pos=None):
    cap_total = cap_yes + cap_soft + cap_no
    if disc_n == 0:
        return "no discovery data", "measure it"
    present = disc_rate >= DISCOVERY_PRESENT
    if cap_total == 0:
        return ("strength" if present else "unroutable"), (
            "defend" if present else "PAIR A CAPABILITY PROMPT. cannot route without it")
    cap_rate = cap_yes / cap_total
    cap_known = cap_rate >= CAPABILITY_PRESENT
    cap_softish = (cap_yes + cap_soft) / cap_total >= CAPABILITY_PRESENT and not cap_known
    # A rank is only a standing if the sample can support one. At small n most
    # brands tie, and a tie is not a lead.
    rank_is_meaningful = disc_n >= 20 and tied < 3
    top = rank is not None and rank <= 3 and rank_is_meaningful
    buried = mean_pos is not None and mean_pos > 5
    if present and disc_rate >= 0.5 and top and not buried:
        return "strength", "defend: keep cited pages fresh, watch for erosion"
    if present and buried:
        return "named but buried", (
            "you are listed last. rank the mention, not just the presence: "
            "off-page volume on the sources that order the list")
    if present and not rank_is_meaningful:
        return "present, rank unresolved", (
            "sample cannot separate you from the pack. raise n before acting on rank")
    if present:
        return ("in the room, low rank" if not top else "in the room"), (
            "off-page volume, plus strengthen already-cited pages")
    if cap_known:
        return "trust gap", "OFF-PAGE. the engine knows and will not recommend you. more of your own content will not move this"
    if cap_softish:
        return "soft recognition", "on-page first (the specifics do not exist anywhere), then off-page"
    return "comprehension gap", "ON-PAGE. the engine does not know you do this"


def pct(k, n):
    return "%d/%d (%.0f%%)" % (k, n, 100.0 * k / n) if n else "0/0 (n/a)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="run directory holding responses.jsonl")
    ap.add_argument("--prev", help="prior run directory, for the diff")
    ap.add_argument("--brand", required=True, help="your brand name")
    ap.add_argument("--prompts", help=".seo/aeo/prompts.json, for type/attribute lookup")
    ap.add_argument("--out", help="write markdown here")
    args = ap.parse_args()

    index = load_prompts(args.prompts)
    cur = tally(load_run(args.run, index), args.brand)
    prev = tally(load_run(args.prev, index), args.brand) if args.prev else {}

    run_label = os.path.basename(os.path.normpath(args.run))
    prev_label = os.path.basename(os.path.normpath(args.prev)) if args.prev else None

    lines = ["# Scoreboard: %s" % args.brand, "",
             "**Run:** %s%s" % (run_label, " · **Prior:** %s" % prev_label if prev_label else ""), "",
             "Every rate carries its sample size and a 95% interval. A change is marked",
             "`real` only when it exceeds the interval on the difference.", "",
             "| Attribute | Pri | Mention rate | 95% CI | Rank | SoV | Capability | Route | vs prior |",
             "|---|---|---|---|---|---|---|---|---|"]

    detail = []
    for name in sorted(cur, key=lambda k: (cur[k]["priority"], -cur[k]["disc_n"])):
        a = cur[name]
        n, k = a["disc_n"], a["disc_k"]
        rate = k / n if n else 0.0
        lo, hi = wilson(k, n)
        rank, sov, ordered, tied = rank_and_sov(a["brand_counts"], args.brand)
        cap_total = a["cap_yes"] + a["cap_soft"] + a["cap_no"]
        cap_txt = ("%d yes / %d soft / %d no" % (a["cap_yes"], a["cap_soft"], a["cap_no"])
                   if cap_total else "not measured")
        mean_pos = (sum(a["positions"]) / len(a["positions"])) if a["positions"] else None
        verdict, action = route(rate, n, a["cap_yes"], a["cap_soft"], a["cap_no"],
                                rank, tied, mean_pos)

        delta = ""
        if name in prev and prev[name]["disc_n"]:
            pk, pn = prev[name]["disc_k"], prev[name]["disc_n"]
            real, band = diff_is_real(pk, pn, k, n)
            change = rate - pk / pn
            delta = "%+.0f pts, %s" % (100 * change, "real" if real else "noise (±%.0f)" % (100 * band))

        lines.append("| %s | %d | %s | %.0f-%.0f%% | %s | %.0f%% | %s | %s | %s |" % (
            name, a["priority"], pct(k, n), 100 * lo, 100 * hi,
            ("%d (tied with %d)" % (rank, tied)) if rank and tied else (rank if rank else "absent"),
            100 * sov, cap_txt, verdict, delta or "first run"))

        d = ["", "### %s" % name, "",
             "- **Route:** %s. %s" % (verdict, action),
             "- **Discovery:** %s across %d responses" % (pct(k, n), n)]
        if a["positions"]:
            d.append("- **Mean list position when present:** %.1f (n=%d)"
                     % (sum(a["positions"]) / len(a["positions"]), len(a["positions"])))
        if n and n < 30:
            d.append("- **Caution:** n=%d. The interval is %.0f points wide. Treat this as "
                     "qualitative." % (n, 100 * (hi - lo)))
        d.append("- **Per platform:**")
        for pf, s in sorted(a["platforms"].items()):
            plo, phi = wilson(s["k"], s["n"])
            d.append("    - %s: %s (95%% CI %.0f-%.0f%%)" % (pf, pct(s["k"], s["n"]), 100 * plo, 100 * phi))
        if ordered:
            d.append("- **Brands mentioned (top 10):** " +
                     ", ".join("%s %d" % (b, c) for b, c in ordered[:10]))
        if a["h2h"]:
            d.append("- **Head to head:** " + ", ".join("%s %d" % (w, c) for w, c in a["h2h"].most_common()))
        if a["citations"]:
            d.append("- **Most cited sources:** " +
                     ", ".join("%s (%d)" % (u, c) for u, c in a["citations"].most_common(5)))
        detail.append("\n".join(d))

    unroutable = [n for n in cur if route(
        cur[n]["disc_k"] / cur[n]["disc_n"] if cur[n]["disc_n"] else 0,
        cur[n]["disc_n"], cur[n]["cap_yes"], cur[n]["cap_soft"], cur[n]["cap_no"],
        rank_and_sov(cur[n]["brand_counts"], args.brand)[0],
        rank_and_sov(cur[n]["brand_counts"], args.brand)[3])[0] == "unroutable"]
    if unroutable:
        lines += ["", "> **%d attribute(s) cannot be routed** because they have no paired capability"
                  % len(unroutable),
                  "> prompt: %s. Without the pair, a gap defaults to \"write more content\","
                  % ", ".join(unroutable),
                  "> which is wrong about half the time. Add the pairs before the next run."]

    lines += ["", "## Detail"] + detail
    md = "\n".join(lines) + "\n"

    print(md)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(md)
        print("wrote %s" % args.out, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
