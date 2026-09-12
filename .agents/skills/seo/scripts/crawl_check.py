#!/usr/bin/env python3
"""Per-page reachability and extractability checks.

  python3 crawl_check.py --url https://example.com/pricing
  python3 crawl_check.py --urls pages.txt --out crawl.json
  python3 crawl_check.py --urls pages.txt --out crawl.json --delay 1.0

Fetches each page WITHOUT executing JavaScript, which is how a meaningful share of
retrieval agents see it. Reports status and redirects, canonical, meta robots,
schema types, server-rendered text volume, the lead answer, heading shape and a
mechanical extractability sub-score.

Also segments the page into heading-delimited passages and scores each one, because
an engine quotes a passage, not a page: a page average hides one quotable block among
thirty that are not. Use --blocks to print the weakest passages per page.

The sub-score covers the seven dimensions a script can judge. Three dimensions
(claim independence, text-not-image, substance) need a human or model read and
are reported as null, never as a pass. See references/technical.md.

Standard library only.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; aeo-skill-crawl-check/1.0)"
TIMEOUT = 30
SKIP_TEXT = {"script", "style", "noscript", "svg", "template", "iframe"}
QUESTION_STARTS = ("how", "what", "why", "when", "where", "which", "who", "can",
                   "does", "do", "is", "are", "should", "will")

# Block-level extraction. These four dimensions are the ones a script can judge
# honestly. Substance is not among them and is never scored here: a passage can
# take 8/8 and still say nothing worth citing. See references/technical.md.
MIN_BLOCK_WORDS = 25
PRONOUN_OPEN = ("it", "its", "this", "that", "they", "them", "these", "those",
                "he", "she", "his", "her", "there", "here", "we", "you")
PRONOUNS = re.compile(r"\b(it|its|they|them|their|this|that|these|those|he|she|his|her)\b", re.I)
ATTRIBUTION = re.compile(
    r"(according to|per\s+[A-Z]|source:|reported by|survey|studies|study|analysis|research|benchmark)", re.I)
FIGURE = re.compile(
    r"(\$\s?\d|\b\d[\d,]*(\.\d+)?\s*"
    r"(%|percent|million|billion|bn|k\b|x\b|hours?|minutes?|days?|seconds?|users?|customers?|teams?)?)", re.I)
YEAR = re.compile(r"\b(19|20)\d{2}\b")


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.text = []
        self.title = None
        self._in_title = False
        self.h1 = []
        self.h2 = []
        self.h3 = []
        self._heading = None
        self._heading_buf = []
        self.canonical = None
        self.meta_robots = None
        self.description = None
        self.jsonld_raw = []
        self._in_jsonld = False
        self._jsonld_buf = []
        self.times = []
        self.seen_h1 = False
        self._in_lead = False
        self._lead_done = False
        self.lead_paras = []
        self._p_buf = None
        self.images = 0
        self.tables = 0
        self.lists = 0
        self.body_start = False
        self.blocks = []
        self._blk_head = None
        self._blk_buf = []
        self._blk_lists = 0
        self._blk_tables = 0

    def close_block(self):
        """Push the passage accumulated since the last h1/h2/h3 and start a new one."""
        txt = " ".join("".join(self._blk_buf).split())
        if txt or self._blk_head:
            self.blocks.append({"heading": self._blk_head, "text": txt,
                                "lists": self._blk_lists, "tables": self._blk_tables})
        self._blk_buf = []
        self._blk_lists = 0
        self._blk_tables = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in SKIP_TEXT:
            if tag == "script" and a.get("type", "").lower() == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_buf = []
            self.skip += 1
            return
        if tag == "body":
            self.body_start = True
        if tag == "title":
            self._in_title = True
        elif tag == "link" and "canonical" in (a.get("rel") or "").lower():
            self.canonical = a.get("href")
        elif tag == "meta":
            name = (a.get("name") or "").lower()
            if name == "robots":
                self.meta_robots = a.get("content")
            elif name == "description":
                self.description = a.get("content")
        elif tag == "time" and a.get("datetime"):
            self.times.append(a["datetime"])
        elif tag in ("h1", "h2", "h3", "h4"):
            if tag != "h4":
                self.close_block()
            self._heading = tag if tag != "h4" else None
            self._heading_buf = []
            if tag == "h1" and not self.seen_h1:
                self.seen_h1 = True
                self._in_lead = True
                self._lead_done = False
            elif self._in_lead:
                # a following heading closes the lead region
                self._in_lead = False
                self._lead_done = True
                self._p_buf = None
        elif tag == "p" and self._in_lead:
            self._p_buf = []
        elif tag == "img":
            self.images += 1
        elif tag == "table":
            self.tables += 1
            self._blk_tables += 1
        elif tag in ("ul", "ol"):
            self.lists += 1
            self._blk_lists += 1

    def handle_endtag(self, tag):
        if tag in SKIP_TEXT:
            if tag == "script" and self._in_jsonld:
                self.jsonld_raw.append("".join(self._jsonld_buf))
                self._in_jsonld = False
            if self.skip:
                self.skip -= 1
            return
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3") and self._heading == tag:
            txt = " ".join("".join(self._heading_buf).split())
            if txt:
                getattr(self, tag).append(txt)
            self._blk_head = txt or None
            self._heading = None
        elif tag == "p" and self._p_buf is not None:
            para = " ".join("".join(self._p_buf).split())
            if para:
                self.lead_paras.append(para)
            self._p_buf = None


    def handle_data(self, data):
        if self._in_jsonld:
            self._jsonld_buf.append(data)
            return
        if self.skip:
            return
        if self._in_title:
            self.title = (self.title or "") + data
            return
        if self._heading:
            self._heading_buf.append(data)
            return
        if self._p_buf is not None:
            self._p_buf.append(data)
        self.text.append(data)
        self._blk_buf.append(data)


class Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.chain = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.chain.append((code, newurl))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url):
    handler = Redirects()
    opener = urllib.request.build_opener(handler)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    started = time.time()
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            body = r.read().decode("utf-8", "replace")
            return {
                "status": r.status, "final_url": r.geturl(), "body": body,
                "headers": dict(r.headers), "redirects": handler.chain,
                "ttfb_ms": int((time.time() - started) * 1000), "error": None,
            }
    except urllib.error.HTTPError as e:
        return {"status": e.code, "final_url": url, "body": "", "headers": dict(e.headers or {}),
                "redirects": handler.chain, "ttfb_ms": int((time.time() - started) * 1000),
                "error": "HTTP %s" % e.code}
    except Exception as e:  # noqa: BLE001
        return {"status": None, "final_url": url, "body": "", "headers": {},
                "redirects": handler.chain, "ttfb_ms": int((time.time() - started) * 1000),
                "error": str(e)}


def jsonld_types(blobs):
    types = []

    def walk(node):
        if isinstance(node, dict):
            t = node.get("@type")
            if isinstance(t, str):
                types.append(t)
            elif isinstance(t, list):
                types.extend(x for x in t if isinstance(x, str))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    dates = {}
    for blob in blobs:
        try:
            data = json.loads(blob)
        except Exception:  # noqa: BLE001
            continue
        walk(data)
        for key in ("datePublished", "dateModified"):
            found = re.search(r'"%s"\s*:\s*"([^"]+)"' % key, blob)
            if found:
                dates.setdefault(key, found.group(1))
    return sorted(set(types)), dates


def is_question(h):
    low = h.strip().lower()
    return low.endswith("?") or low.split(" ")[0] in QUESTION_STARTS


def first_sentence(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)
    return parts[0] if parts else ""


def score_block(block):
    """Score one passage out of 8. Not a grade for the writing.

    A flag for passages that cannot survive being lifted out of the page, which is
    the only way an engine ever uses them.
    """
    text = block["text"]
    words = text.split()
    wc = len(words)
    score, notes = 0, []

    first = first_sentence(text)
    head_word = first.split(" ")[0] if first else ""
    opener = re.sub(r"[^a-z]", "", head_word.lower())

    # 1. Opening independence. The first sentence has to mean something alone.
    if opener in PRONOUN_OPEN:
        notes.append('opens with "%s", so a quote loses its subject' % head_word)
    elif re.search(r"\b[A-Z][a-z]{2,}", first[1:]) or FIGURE.search(first):
        score += 2
    else:
        score += 1
        notes.append("opening sentence names nothing specific")

    # 2. Pronoun density. How hard the passage leans on its surroundings.
    ratio = len(PRONOUNS.findall(text)) / wc if wc else 1.0
    if ratio < 0.02:
        score += 2
    elif ratio < 0.04:
        score += 1
    else:
        notes.append("pronoun density %.0f%%, the passage depends on what came before"
                     % (ratio * 100))

    # 3. Quotable length. Short enough to lift whole, long enough to say something.
    if 40 <= wc <= 120:
        score += 2
    elif 25 <= wc <= 200:
        score += 1
    elif wc < 25:
        notes.append("%d words, too thin to quote" % wc)
    else:
        notes.append("%d words, an engine will not lift this whole" % wc)

    # 4. Attributed specifics. A figure with a source or a date beside it.
    has_figure = bool(FIGURE.search(text))
    has_source = bool(ATTRIBUTION.search(text) or YEAR.search(text))
    if has_figure and has_source:
        score += 2
    elif has_figure:
        score += 1
        notes.append("figures carry no source or date")
    else:
        notes.append("no specific figures")

    heading = block["heading"]
    return {
        "heading": heading,
        "heading_is_question": bool(heading and is_question(heading)),
        "word_count": wc,
        "score": score,
        "max": 8,
        "notes": notes,
        "has_table_or_list": bool(block["tables"] or block["lists"]),
        "preview": " ".join(words[:24]) + ("..." if wc > 24 else ""),
    }


def analyse(url, res):
    out = {
        "url": url, "status": res["status"], "final_url": res["final_url"],
        "error": res["error"], "ttfb_ms": res["ttfb_ms"],
        "redirect_count": len(res["redirects"]),
        "redirect_chain": [{"code": c, "to": u} for c, u in res["redirects"]],
        "x_robots_tag": res["headers"].get("X-Robots-Tag"),
    }
    if not res["body"]:
        out["reachable"] = False
        return out

    p = Page()
    try:
        p.feed(res["body"])
    except Exception as e:  # noqa: BLE001
        out["parse_error"] = str(e)
    p.close_block()

    body_text = " ".join("".join(p.text).split())
    # The lead answer is the first substantial paragraph between the H1 and the next
    # heading. Short paragraphs before it are bylines, labels or nav, and they count
    # against the page: they are what an extractor hits first.
    lead_text, lead_skipped = "", 0
    for i, para in enumerate(p.lead_paras):
        if len(para.split()) >= 20:
            lead_text, lead_skipped = para, i
            break
    schema, ld_dates = jsonld_types(p.jsonld_raw)
    headings = p.h2 + p.h3
    q_headings = [h for h in headings if is_question(h)]

    out.update({
        "reachable": res["status"] == 200,
        "title": (p.title or "").strip() or None,
        "title_len": len((p.title or "").strip()),
        "meta_description_len": len(p.description or "") if p.description else 0,
        "h1": p.h1,
        "h2_count": len(p.h2),
        "h3_count": len(p.h3),
        "question_heading_ratio": round(len(q_headings) / len(headings), 2) if headings else 0.0,
        "canonical": p.canonical,
        "canonical_self": (p.canonical or "").rstrip("/") == res["final_url"].rstrip("/") if p.canonical else None,
        "meta_robots": p.meta_robots,
        "noindex": bool(p.meta_robots and "noindex" in p.meta_robots.lower())
                   or bool(out["x_robots_tag"] and "noindex" in out["x_robots_tag"].lower()),
        "nosnippet": bool(p.meta_robots and "nosnippet" in p.meta_robots.lower()),
        "html_bytes": len(res["body"]),
        "rendered_text_chars": len(body_text),
        "rendered_word_count": len(body_text.split()),
        "text_to_html_ratio": round(len(body_text) / max(len(res["body"]), 1), 3),
        "schema_types": schema,
        "dates": {"time_tags": p.times[:5], **ld_dates},
        "lead_answer_words": len(lead_text.split()),
        "lead_answer": lead_text[:400] or None,
        "lead_paragraphs_total": len(p.lead_paras),
        "lead_paragraphs_skipped": lead_skipped,
        "tables": p.tables, "lists": p.lists, "images": p.images,
    })

    # JS-shell heuristic: very little text relative to a large HTML payload.
    out["likely_js_only"] = (out["rendered_word_count"] < 120 and out["html_bytes"] > 15000)

    # Passage-level extraction, sorted worst first: the list of sections to rewrite.
    scored = sorted((score_block(b) for b in p.blocks
                     if len(b["text"].split()) >= MIN_BLOCK_WORDS),
                    key=lambda x: x["score"])
    median = None
    if scored:
        vals = sorted(x["score"] for x in scored)
        mid = len(vals) // 2
        median = vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2
        if median == int(median):
            median = int(median)
    out["blocks"] = {
        "segmented": len(p.blocks),
        "scored": len(scored),
        "skipped_thin": len(p.blocks) - len(scored),
        "median": median,
        "max": 8,
        "passages": scored,
    }

    # Mechanical extractability sub-score. Seven dimensions, 2 points each, max 14.
    s, notes = 0, []
    lw = out["lead_answer_words"]
    if 40 <= lw <= 80 and lead_skipped == 0:
        s += 2
    elif lw >= 20:
        s += 1
        if lead_skipped:
            notes.append("lead answer is %d words but %d shorter paragraph(s) come first"
                         % (lw, lead_skipped))
        else:
            notes.append("lead answer is %d words, aim for 40-80" % lw)
    else:
        notes.append("no usable lead answer after the H1 (%d paragraphs scanned)"
                     % out["lead_paragraphs_total"])

    r = out["question_heading_ratio"]
    if r >= 0.5:
        s += 2
    elif r >= 0.25:
        s += 1
        notes.append("only %d%% of headings are phrased as questions" % int(r * 100))
    else:
        notes.append("headings are not phrased as questions")

    if out["dates"].get("dateModified") or out["dates"].get("datePublished") or p.times:
        s += 2
    else:
        notes.append("no date signal found")

    if schema:
        s += 2
    else:
        notes.append("no JSON-LD schema")

    if out["tables"] or out["lists"] >= 2:
        s += 2
    elif out["lists"]:
        s += 1
    else:
        notes.append("no structured blocks (tables or lists)")

    if out["rendered_word_count"] >= 300:
        s += 2
    elif out["rendered_word_count"] >= 120:
        s += 1
        notes.append("thin: %d server-rendered words" % out["rendered_word_count"])
    else:
        notes.append("very thin or JS-only: %d server-rendered words" % out["rendered_word_count"])

    if len(p.h1) == 1 and out["title"]:
        s += 2
    else:
        notes.append("H1 count is %d, title %s" % (len(p.h1), "present" if out["title"] else "missing"))

    out["extractability_mechanical"] = {"score": s, "max": 14, "notes": notes}
    out["extractability_needs_human"] = ["claim independence", "text not image", "substance"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", action="append", default=[], help="a URL (repeatable)")
    ap.add_argument("--urls", help="file with one URL per line")
    ap.add_argument("--out", help="write JSON here")
    ap.add_argument("--delay", type=float, default=0.5, help="seconds between fetches")
    ap.add_argument("--blocks", action="store_true",
                    help="print the weakest passages per page")
    args = ap.parse_args()

    urls = list(args.url)
    if args.urls:
        with open(args.urls, "r", encoding="utf-8") as fh:
            urls += [l.strip() for l in fh if l.strip() and not l.startswith("#")]
    if not urls:
        ap.error("give --url or --urls")

    results = []
    for i, u in enumerate(urls):
        if i:
            time.sleep(args.delay)
        results.append(analyse(u, fetch(u)))

    print("%-48s %5s %5s %5s %5s %5s %s"
          % ("URL", "STAT", "WORDS", "SCORE", "BLK", "LEAD", "FLAGS"))
    for r in results:
        flags = []
        if r.get("likely_js_only"):
            flags.append("JS-ONLY")
        if r.get("noindex"):
            flags.append("NOINDEX")
        if r.get("nosnippet"):
            flags.append("NOSNIPPET")
        if r.get("canonical_self") is False:
            flags.append("CANONICAL-OFF")
        if r.get("redirect_count", 0) > 1:
            flags.append("REDIR-%d" % r["redirect_count"])
        if r.get("error"):
            flags.append(r["error"])
        sc = r.get("extractability_mechanical", {})
        bl = r.get("blocks") or {}
        print("%-48s %5s %5s %5s %5s %5s %s" % (
            r["url"][:48], r.get("status") or "-", r.get("rendered_word_count", "-"),
            "%s/%s" % (sc.get("score", "-"), sc.get("max", "-")) if sc else "-",
            "%s/8" % bl["median"] if bl.get("median") is not None else "-",
            r.get("lead_answer_words", "-"), " ".join(flags)))

    js = [r["url"] for r in results if r.get("likely_js_only")]
    if js:
        print("\nJS-only shells (invisible to agents that do not run scripts):")
        for u in js:
            print("  %s" % u)

    if args.blocks:
        for r in results:
            bl = r.get("blocks") or {}
            weak = (bl.get("passages") or [])[:3]
            if not weak:
                continue
            print("\nweakest passages on %s  (median %s/8 over %d scored, %d too thin to score)"
                  % (r["url"], bl.get("median"), bl.get("scored", 0), bl.get("skipped_thin", 0)))
            for b in weak:
                print("  %d/8  %-40s  %s" % (
                    b["score"], (b["heading"] or "(no heading)")[:40],
                    "; ".join(b["notes"])[:90]))
        print("\nPassage scores flag structure, never substance. A block can take 8/8 "
              "and still\nrestate the consensus, which is the failure no script can see.")

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"pages": results}, fh, indent=2)
        print("\nwrote %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
