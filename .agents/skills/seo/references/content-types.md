<!-- merged from seo-content/references/content-types.md + seo-sprint/references/patterns/playbooks.md -->

# Content-Type Catalog

Ten types. Each entry: **when to pick it**, the **structure**, the **quality bar** (word floor + must-haves), and the **schema**. The type is chosen in `opportunity-research.md` Step D from intent × SERP shape — this file tells you how to build it once chosen.

Nine of the ten are prose. The tenth — **the free tool (#10)** — is a *build*, and it is the most valuable thing this engine ships when the SERP supports it. It has its own full reference (`free-tool-pages.md`) because it carries a build phase, a safety posture, and a verification gate the prose types don't. Do not treat it as an exotic special case: on any query with tool intent, it is the correct default answer, and shipping an article there is usually the mistake.

Internal-link minimums apply to every type: **≥3 in-body links** (mix of features, tools, sibling content, and ≥1 conversion page like `/pricing` or a relevant `/for/`), and **≥2 inbound** links from existing pages. No orphans.

---

## 1. Pillar guide (the playbook)

**Pick when:** broad commercial-investigation head term; the top 10 are long, comprehensive pages; you want one authoritative hub that gates a cluster. Volume 50-700 is the sweet spot — small head terms where the cluster matters more than the term. Avoid pure informational queries with no buying intent ("what is social media"), brand-direct queries (those are comparison territory), and anything where Wikipedia or a mega-listicle owns the top 5.

**Why it earns its cost:** three jobs no other type does at once. It establishes the author as a practitioner rather than a vendor. It is the highest AI-citation surface in the catalog — long, well-structured guides get lifted into generated answers far more than templated pages. And it draws inbound links: other writers cite a playbook, almost nobody cites an alternatives page. The tradeoff is real — a genuine pillar is days of writing against hours for a templated page — so ship two or three early as anchors, then let the programmatic patterns carry volume.

**Structure:** problem framing (why this topic, why now, why it's hard) → the mental model the rest hangs on → 3-5 "do this" sections with examples → 2-3 "don't do this" / anti-pattern sections → an operational plan (week-by-week or step-by-step) → what success looks like and what to do next. TOC with anchored sections, ordered identically to the sections themselves. Don't copy this shape slavishly if a better one fits, but when stuck, use it.

**Quality bar:** **≥2,500 words of original prose** in the body — strip markup before counting. 8+ sections, none under ~250 words, each with an anchor and a matching TOC entry. Beyond the word floor, four things separate a pillar from 2,500 words of content:

- **Operational sections name actual numbers.** "Week 2: connect monitoring" is a TOC entry, not a plan. Every step needs a measurable "what done looks like" and an "if you're behind" branch.
- **Tooling sections name what NOT to use.** Four good tools is generic; four good tools plus four categories to avoid, with reasons, is differentiated.
- **Vignettes and case studies carry three beats each** — the scenario, the non-obvious thing that surprised them, the lesson. A single paragraph is fine if all three fit.
- **Counter-arguments run inline.** When you make a strong claim, address the obvious objection in the next paragraph. That is what makes it thinking rather than content.

Concrete numbers throughout; where you don't have a source, use a bracketed range and source it before ship, never after. Operator voice — first person plural if the brand uses it elsewhere, lived experience over detached best-practice register. No padding: 2,500 words of real content beats 4,000 of fluff. Read-time displayed honestly (~140 wpm for operator content; 2,500 words ≈ 18 minutes) — readers calibrate trust against it.

**Internal links (in body, not sidebar):** ≥3 feature pages, ≥2 tools, ≥2 `/for/*`, ≥1 `/alternatives/*`, and ≥2 inbound links from existing pages. This is the one type where the in-body minimum is higher than the catalog-wide floor.

**Schema:** `Article` + `BreadcrumbList`, with author, `datePublished`, and `dateModified`. Add `FAQPage` if a Q&A section exists.

**Where it ships:** if the repo already has a `/playbooks/` or equivalent long-form surface, ship there and match that surface's existing structure and metadata shape rather than inventing a second one.

---

## 2. How-to / tutorial

**Pick when:** "how to X" query; top results are step-by-step; clear procedural intent. Often wins a featured snippet.

**Structure:** one-paragraph "what you'll accomplish + prerequisites" → numbered steps, each with what-to-do + what-done-looks-like → common-mistakes section → a worked example end-to-end → short FAQ. Lead with the snippet-able summary (a tight ordered list near the top) so Google can lift it.

**Quality bar:** ≥1,200 words. Every step independently actionable — no "configure it appropriately." Real commands/values/screenshots where the stack allows. If the task has branches (OS, plan tier), handle the top 2, not all of them.

**Schema:** `HowTo` (with `step` items) + `BreadcrumbList`. `FAQPage` for the FAQ.

---

## 3. Listicle / roundup

**Pick when:** "best X" / "X tools" / "top N" / "N ways to" query; top 10 are listicles. Highest-frequency commercial SERP shape.

**Structure:** intro stating the selection criteria (builds trust + differentiates) → the list, each item with a consistent mini-template (name, who it's for, standout strength, one honest limitation, price) → a short "how we picked" / methodology note → a decision-helper closing ("pick X if…, pick Y if…").

**Quality bar:** ≥1,500 words. **Include your own product honestly and in a defensible position** — not artificially #1; readers and Google both punish that. Each entry needs a real limitation (the honesty signal). Consistent fields across all entries. If you can't say something specific about an item, you haven't researched it.

**Schema:** `ItemList` + `BreadcrumbList`. `FAQPage` if present.

---

## 4. Definition / answer page

**Pick when:** "what is X" / "X meaning" / "X definition" query; snippet box present; short authoritative pages rank. Pure informational, top-of-funnel, AI-citation-friendly.

**Structure:** a 40-60 word direct definition in the **first paragraph** (snippet target) → expanded explanation → why it matters / when it applies → a concrete example → related terms (internal links) → short FAQ. Inverted-pyramid: answer first, depth after.

**Quality bar:** ≥600 words (depth signals authority even on short-answer queries, but don't pad). The opening definition must stand alone as a quotable answer. One clear example. This type is your best AI-citation surface — make the core claim quotable and sourced.

**Schema:** `Article` or `DefinedTerm` + `BreadcrumbList` + `FAQPage`.

---

## 5. Comparison

**Pick when:** "X vs Y" or multi-tool decision query; top results weigh options. High commercial intent.

**Structure:** TL;DR verdict up top (who should pick what) → comparison table (consistent dimensions) → dimension-by-dimension prose (don't just dump the table) → "pick X if / pick Y if" → honest note on where each genuinely wins. If it's *your product vs a single competitor*, prefer a programmatic `/compare/` page if the repo has that surface (`patterns/compare.md`). Use this editorial type for **neutral multi-tool** comparisons that don't fit a fixed template.

**Quality bar:** ≥1,200 words. Every compared option gets a fair, specific treatment. **The honesty rule:** name where each option genuinely wins. No straw-man competitors.

**Schema:** `BreadcrumbList` + `FAQPage`. `ItemList` if structured as a ranked set.

---

## 6. Data study / original research

**Pick when:** nobody in the SERP has original numbers; the topic is quantifiable; you want links + citations + AI mentions. The highest link-draw type — other writers cite data they can't get elsewhere.

**Structure:** headline finding up top (the quotable stat) → methodology (how you got the data — credibility gate) → findings, each a chart/table + interpretation → "what this means for you" → methodology footnote + a "cite this" block. The charts are the most-embedded part of this type — draw them well, put `[Brand] · [date]` inside each one, and they earn links from wherever they get re-posted (`visuals.md` §4).

**Quality bar:** ≥1,500 words. **Real data with a real method** — your product's anonymized metrics, a survey you ran, or a defensible aggregation (the hunt, the production-pull contract, and the public-data combine patterns are all in `proprietary-data.md`). If you can't source or generate genuine data, do not write this type (fabricated stats are a trust and ranking disaster). Each finding visualized + interpreted — the visualization is a hand-authored inline SVG styled from the repo's tokens (`visuals.md`), not a placeholder, not a screenshot of a spreadsheet, and its numbers appear as text alongside it. Make it easy to cite (clear stat callouts, a citation line). If a deep-research skill is installed, hand the gathering to it; otherwise fan out the searches inline and verify each figure against a second source.

**Schema:** `Article` + `Dataset` + `BreadcrumbList`.

---

## 7. Resource / template library

**Pick when:** "X template" / "X examples" / "X checklist" / "X swipe file" query; users want a *usable asset*, not prose. ("Library" = a curated, browsable collection — templates, examples, prompts, snippets.)

**Structure:** brief intro on how to use the resource → the asset itself (templates/examples/checklist, copy-pasteable or downloadable) → short usage guidance per item → a CTA tying the resource to the product. The asset is the hero; prose is supporting.

**Quality bar:** ≥800 words of supporting copy *plus* a genuinely useful asset (≥5 examples/templates, or one substantial downloadable). The asset must be real and good — a thin template list loses to the one site that made a proper collection. **Check type 10 first.** If an interactive tool would beat a static library on this query — and on "[thing] calculator/generator/checker" queries it almost always does — pick **#10** instead and ship the tool. Fall back to the library only when the tool genuinely can't be built in one run (`free-tool-pages.md` §1), in which case queue the tool as the top backlog candidate with a scoped spec.

**Schema:** `ItemList` (or `HowTo` if step-templated) + `BreadcrumbList`.

---

## 8. Opinion / POV

**Pick when:** theme-led not keyword-led; low search volume but high authority + AI-citation + shareability value; you have a genuine contrarian or experience-backed thesis.

**Structure:** the thesis stated sharply up front → the conventional wisdom you're countering → your argument in 3-4 beats, each grounded in real experience/data → the strongest counter-argument, addressed honestly → what to do differently. Personal, first-person, opinionated.

**Quality bar:** ≥1,000 words. A real, defensible, non-obvious thesis — "you should do marketing well" is not a POV. Grounded in lived experience or data, not vibes. Addresses the best counter-argument (this is what separates a POV from a rant). This type lives or dies on the strength of the take; if the take is weak, pick a different piece.

**Schema:** `Article` + `BreadcrumbList`.

---

## 9. Case study / teardown

**Pick when:** "how [company] does X" / "[brand] strategy" / teardown intent; readers want a real example dissected.

**Structure:** what the subject does + why it's worth studying → the teardown in beats (what they did, what's clever, what's a mistake) → the extractable principles (the reusable lessons) → "how to apply this to your own [thing]" → tie to product. Use real, verifiable specifics — screenshots, real numbers, quotes.

**Quality bar:** ≥1,200 words. Concrete and verifiable — a teardown of a real thing with real details, not a hypothetical. Each observation yields a transferable lesson (otherwise it's gossip, not content). Fair to the subject. If teardown of a named competitor, keep the honesty rule: credit what they do well.

**Schema:** `Article` + `BreadcrumbList`.

---

## 10. Free tool (interactive)

**Pick when:** the query carries tool intent (`[thing] calculator`, `generator`, `checker`, `converter`, `free [thing] tool`, `grader`, `lookup`) **and** you can ship a working v1 in one run. Strongest signal of all: the top 10 are *articles about a calculation people would rather just run* — that's a SERP nobody has built the right page for yet.

**Why it outranks the prose types:** a working tool is information gain a writer cannot copy. Every other type competes on prose against ten pages of prose; a tool competes on utility, which is what earns links, repeat visits, brand searches, and AI citations ("the free X calculator at Y"). It's the single highest link-draw and longest-compounding type in this catalog — one good tool out-earns six good articles on a two-year horizon.

**Structure:** the tool itself above the fold, pre-filled with a realistic example so it's never blank → H1 + one line on what it does → **how to read your result** (the interpretation layer every competitor skips) → **methodology** (formula, source + date of every constant, honest limits) → one worked example end-to-end → related concepts / next steps → FAQ from the real PAA set.

**Quality bar:** the two-halves rule — the **tool** and the **page content** must both be excellent; a brilliant tool under a thin page ranks nowhere, a great page with a toy tool earns no links. 600-1,200 words of content below the tool, at full craft rigor (shorter than an article, not softer). **Ungated — no email capture anywhere** except where email *is* the deliverable. Every ugly input handled (empty, malformed, boundary, negative, huge). Failed checks render as an explicit neutral state, never as a pass. Per-use cost gets a rate limit, a spend ceiling, and a kill switch in the same commit. Per-entity result pages are `noindex`; the form page is the indexable surface. **Verified by hand with a screenshot of every state — no screenshot, no ship.**

**Schema:** `SoftwareApplication` or `WebApplication` (with `applicationCategory` and `offers` at price 0) + `BreadcrumbList`. Add `FAQPage` for the FAQ, `HowTo` if there's a procedural companion.

**Full build spec:** `free-tool-pages.md` — feasibility gate, archetypes, the non-negotiables, design recon, build shape, verification, and registration. Read it before picking this type, not after.

---

## Optional structure: the scenario page (12 blocks)

Usable by any guide or use-case page whose reader arrived mid-problem. Not a new type — a structure the pillar guide (#1), how-to (#2) and use-case pages can adopt:

1. **Practical answer** — 40–60 words, the first paragraph after the H1
2. **What to do now**
3. **What not to rely on**
4. **What we protect**
5. **What we do not solve**
6. **The problem**
7. **Consequences**
8. **Setup checklist**
9. **Questions this guide answers**
10. **What this is based on** (citations)
11. **FAQ**
12. **Related**

**"What we do not solve" is the block that makes a commercial page citable, and it is the one writers drop first.** A page that names its own limits reads as a source; a page that doesn't reads as a brochure, and extractors treat it as one.

---

## Cross-cutting requirements (all types)

- **Information gain (non-negotiable, every type):** the piece must contain ≥1 original element absent from the top 10 — proprietary data, first-hand testing, expert commentary, a genuinely novel framework, or (type 10) a working tool. **Original data is the strongest of these and the default target on every run** — how to find it, pull it safely, and cross it with public data is in `proprietary-data.md`. This isn't only the data-study's job; it's the bar for *all* types under the 2026 core updates. For a tool page the tool is the primary gain, but the surrounding content still owes one concrete element the SERP lacks. The element comes from the research brief (`research-brief.md`) and is a hard ship gate (`quality-loop.md`).
- **Answer-engine optimization (every type):** lead with the answer, write self-contained quotable core claims, attribute + date every stat, cover the entity map, match the answer-intent bucket (`aeo/intent-buckets.md`). Full layer in `lanes/aeo.md`.
- **Meta title** ≤60 chars, primary keyword near the front. **Meta description** ≤155 chars, keyword + hook. **Canonical** set. **One `<h1>`.**
- **Keyword placement:** in H1, title, first 100 words, and ≥2 H2s — naturally, never stuffed.
- **FAQ section** wherever the SERP shows a People-Also-Ask box; pull the actual PAA questions.
- **Internal links:** ≥3 in-body, ≥2 inbound, varied anchor text (`.seo/link-inventory.md`).
- **Voice:** governed by `.seo/brand.md` — voice tags, perspective, forbidden words.
- **E-E-A-T:** named author + credentials (`.seo/brand.md` Author section), first-hand framing where true, visible date stamp.
- **Figures:** every type gets the §1 test in `visuals.md` — anything with shape (comparison, trend, distribution, process, structure) is drawn as inline SVG matching the repo's own design tokens, in the same commit as the prose. Density guide by type: **data study** ≥1 figure per finding (a data study without figures fails its bar) · **how-to** a diagram of the flow or the finished state · **comparison** one figure carrying the decision, not a re-typed feature table · **pillar guide** 2-4 across the piece · **listicle / definition / opinion** usually 0-1 — a definition page with three figures is trying too hard. Never invent data to have a chart, and never decorate.
- **Schema** per type above; validate with `python scripts/tech_audit.py --schema <url>`.

**Verification note:** enforce the word floor with `python scripts/word_count.py <path> --min <floor>`. Type 10 adds a hand-verification gate the scripts can't cover — exercise every tool state and screenshot it (`free-tool-pages.md` §9). `scripts/link_audit.py` only knows the programmatic A-E page types, so use it with `--orphan-check` (to catch orphans) and count the ≥3 in-body / ≥2 inbound links by hand against the minimums above.
