# Free Tool Pages (type 10) — the build spec

A free tool page is the highest-leverage piece this engine can ship. It is also the only type with a **build phase**, so it gets its own reference. `content-types.md` entry 10 is the summary; this file is how you actually ship one.

The premise: a working tool is information gain that cannot be copied by a writer. Every other type competes on prose against ten pages of prose. A tool competes on utility, and utility is what earns links, repeat visits, brand searches, and AI citations ("the free X calculator at Y"). One good tool out-earns six good articles over a two-year horizon.

**The two-halves rule.** A tool page has two halves and both must be excellent: the **interactive tool** (the hook and the link magnet) and the **page content** around it (what actually ranks and gets cited). A brilliant tool under a thin page ranks nowhere. A great page with a toy tool earns no links. Ship both or ship a different type.

---

## 1. When to pick this type

Pick it when **all** of these are true:

- The query carries **tool intent**: `[thing] calculator`, `[thing] generator`, `[thing] checker`, `free [thing] tool`, `[thing] converter`, `[thing] template maker`, `check my [thing]`, `[thing] audit`, `[thing] grader`, `[thing] lookup`.
- The top 10 **already contains at least one interactive tool**, or contains only articles *about* a calculation people would obviously rather just run. The second case is the best opportunity in this skill: an article SERP on a tool query is a SERP nobody has built the right page for yet.
- You can build a **genuinely useful v1 inside this run**. Not a roadmap. Not a waitlist. A working thing.
- The tool is **adjacent to the product**: it solves a real problem in the same domain, and using it makes the product's value more obvious, not less.

Do **not** pick it when:

- The math or logic is trivial and the answer is a single sentence. That is a **definition page**, and a tool wrapper on it looks like SEO cosplay.
- The tool needs data you do not have and cannot legally get.
- The build genuinely exceeds one run. Then split it: ship the **resource/template library** (type 7) or the **how-to** (type 2) on that keyword this run, and register the tool as the top backlog candidate with a scoped spec. Do not half-build a tool across runs.
- Per-use vendor cost is real and you cannot cap it (see §4).

---

## 2. Feasibility gate (run this before the selection checkpoint)

Answer these four in one paragraph each, in the checkpoint text. If any answer is "unknown", the honest move is to say so and pick a different candidate.

1. **Capability** — what does the tool actually compute, and where does that capability come from? Existing code in the repo, a public dataset, a documented formula, a fee schedule, or a live fetch. Name it. "We would need to build a scraper first" means the tool is a project, not a piece.
2. **Data freshness** — does the tool state numbers that decay (fees, tax rates, pricing tiers, statutory limits)? If yes, those get **verified this run** with a dated source in the claim ledger, and the page carries a visible "rates checked [date]" stamp. Never ship a number you did not check this run.
3. **Cost and abuse surface** — does each use cost money (an API call, an LLM call, a lookup credit) or hit third-party servers? If yes, §4 applies and is not optional.
4. **Maintenance** — what breaks this in six months, and who notices? A pure-math calculator: nothing. A live-fetch checker: everything. Say which one you are signing up for.

---

## 3. Tool archetypes

| Archetype | Examples | Where it runs | Notes |
|---|---|---|---|
| **Calculator** | ROI, fee/margin math, payback, sizing, pricing estimator | **Fully client-side.** No server round-trip for arithmetic | The default archetype. Cheapest to build, zero abuse surface, instant results, works offline |
| **Generator** | Policy/document/template generator, name generator, config/snippet builder, schema builder | Client-side where possible | Output must be copy-pasteable *and* downloadable. If it generates a legal-ish document, the not-legal-advice line is required |
| **Analyzer / checker** | Site grader, meta-tag checker, accessibility scan, feed validator | Server, with §4 controls | Highest link draw, highest operational risk. Read §4 twice |
| **Tester / preview** | SERP snippet preview, OG-card preview, email-subject preview, contrast checker | Client-side | Renders a faithful preview of something the user cannot otherwise see. Fidelity is the whole product |
| **Lookup / database** | Code lookup, fee schedule, benchmark browser, holiday/deadline finder | Server or static data file | The data *is* the moat. Cite where it came from and when it was pulled |
| **Converter / formatter** | Unit, format, timezone, CSV↔JSON, cron-expression explainer | Client-side | Boring and enormously durable traffic |
| **Interactive quiz / assessment** | Readiness score, maturity model, "which X is right for you" | Client-side | Score must be defensible, not astrology. Publish the rubric |

**Default to client-side.** Every server round-trip you avoid removes a cost line, a rate-limit, an abuse vector, an outage, and a latency complaint. Reach for the server only when the tool genuinely needs something the browser cannot do.

---

## 4. Non-negotiables

These are ship-blockers, not preferences.

**Ungated. Always.** No email wall, no "enter your email to see your results", no partial-result teaser. The only exception is a tool where **email is the deliverable itself** (a watch/alert/monitor that must email you later) — and even then the *result* the user came for renders on-page first. Never write copy that narrates the no-gate policy ("no email required!"); just do not ask. Control cost with scope, caching, rate limits, and spend caps, never with a gate.

**"Couldn't check" never renders as "clean."** Any tool that fetches, parses, or looks something up will fail sometimes. A failed check must render as a neutral, explicit third state — not as a pass, and not as a scary red fail. Write that copy deliberately; it is the state most likely to be seen by a first-time visitor and the one most likely to be quoted back at you.

**Handle the ugly inputs.** Empty, malformed, absurdly large, negative, zero, unicode, pasted-with-whitespace, and boundary values all get defined behavior before ship. A tool that throws a stack trace on a blank submit is not shipped.

**Per-use cost gets a hard cap and a kill switch.** Any tool with vendor cost or unbounded outbound fetch volume needs: a per-IP/session rate limit on the action, a global daily spend or volume ceiling, and an environment-variable kill switch that disables the tool with neutral copy. Build all three in the same commit as the tool. Not "later."

**Live-fetch tools guard the fetch.** Validate that the target is a public host before requesting it (no localhost, no private ranges, no redirect-to-internal), set a timeout and a response-size cap, and rate-limit the mutating action. If the repo already has this posture somewhere, reuse that code path rather than writing a second one.

**Per-entity result pages are `noindex`.** If the tool produces a shareable result URL that names a third party or a user's own site, that page is `noindex, follow`. The **form page is the indexable surface**; result pages are for sharing, not for the index. This also keeps a thousand thin pages out of your site quality profile.

**Legal-adjacent output carries the disclaimer.** Anything generating a document, notice, policy, or filing gets a plain not-legal-advice line near the output, not buried in a footer.

**No self-attestation in copy.** The page does not say the tool is powerful, accurate, or best-in-class. It shows the result and states what it checked. Claims about the tool go in the methodology section as verifiable statements.

---

## 5. Design recon (30 minutes, do not skip)

Tools live or die on the first ten seconds. Before building, pull **2-3 concrete interaction references** and name what you are stealing from each.

- If `search_screens` / `search_flows` is available, search the **UI pattern, not the topic**: "calculator", "fee breakdown", "results summary", "scan progress", "report card", "form wizard", "empty state". If it is not available, pull the top 2 ranking tools from the selection SERP read and read their interaction model directly.
- **References inform the interaction only.** The visual language comes from the site's existing design system and components. A tool that looks like a different product is a trust leak.
- Note the moves concretely: "result updates live on input, no submit button", "the breakdown is a stacked bar with a row per fee", "the empty state pre-fills a realistic example so the tool is never blank".

**Pre-fill a real example.** The single highest-return design move for a tool page: the tool arrives with plausible values already in it, showing a real result. Nobody bounces off a blank form they have to imagine their way into.

**Illustrations, not a wall of text.** The content below the tool carries 2-4 visual elements (a diagram of the math, a distribution, a timeline, a worked example callout). Full build spec in `visuals.md` — hand-authored inline SVG themed from the repo's own tokens, so it inherits the site's font, palette, and dark mode instead of arriving in some library's default look. Every number in an illustration also appears in adjacent copy, and decorative SVG is `aria-hidden`. A diagram of *how the calculation works* is the single highest-value figure on a tool page: it's what makes the methodology section credible, and it's what people screenshot.

---

## 6. The brief (the research step, scaled)

Run the standard research fan-out (`research-brief.md`), scaled to three researchers instead of six:

1. **SERP teardown** — the top 3-5 ranking pages. What inputs and outputs the ranking tools expose, what content sits around them, where they are thin, stale, gated, or wrong.
2. **Primary sources** — every number the tool computes with or the page states: fee schedules, rates, statutory requirements, official docs, platform policies. URL plus date per claim. This is where a tool page earns its authority; a calculator built on a stale fee schedule is worse than no calculator.
3. **First-hand / product angle** — what your own data, pipeline, or the tool's own mechanics let you say that nobody in the top 10 can.

Then the **separate verification pass**, same as every other type. Numbers the tool *computes with* are load-bearing: a wrong constant is a wrong answer for every visitor, forever.

**Information gain on a tool page.** The tool itself is the primary information gain — but the surrounding content still needs **one concrete element the SERP lacks**: the verified current numbers, a real methodology section, benchmark data, or the worked example nobody else publishes. "We built a calculator" is not by itself a content moat if the 800 words under it restate the top 10.

---

## 7. Build (Step 3a)

Match the repo's stack and conventions; read a comparable existing page before writing a new one. The generic shape:

1. **Route** — `/tools/<slug>` under whatever the repo's public/marketing surface is. Async tools follow a create → show → status shape.
2. **Handler** — a tools controller/route handler for static tools; a dedicated one for async. Heavy logic lives in a service/lib module, not the handler.
3. **View** — reuse the site's layout, components, and type scale. The tool is a new *interaction*, not a new *design language*.
4. **Logic** — reuse capabilities the repo already has rather than forking them. If a namespace is new, run whatever the project's load/lint check is.
5. **Hub and sitemap** — create `/tools` if it does not exist, add the tool to it, and add both to the sitemap.
6. **Embed and cite affordances** — a "cite this tool" line and, where it makes sense, a copyable embed snippet. This is the link-magnet mechanic; a tool nobody can cite cleanly gets fewer links than one that hands over the sentence.

Delegate the multi-file implementation to a subagent if the host supports it, and paste §4 (non-negotiables), the brief, and the design references into that prompt. The subagent is a **leaf**: no further fan-out.

---

## 8. Page content (Step 3b)

600-1,200 words below the tool. Shorter than an article, **identical craft rigor** — every rule in `writing.md` and `lanes/aeo.md` applies at full strength.

Structure:

1. **H1 with the keyword**, then one sentence stating what the tool does and what it needs from you. The tool is above the fold; the prose starts under it.
2. **How to read your result** — the interpretation layer. What a given number or grade actually means and what to do about it. This is the section every competitor skips.
3. **Methodology** — the formula, the source of every constant, the date checked, and the honest limits of the tool. This is the credibility gate and the most-cited section on the page.
4. **The worked example** — one real scenario end-to-end with real numbers.
5. **Related concepts / next steps** — where the internal links live.
6. **FAQ** — from the real People-Also-Ask set, only if it earns its place.

Requirements:
- Voice from `.seo/brand.md`; forbidden words are forbidden.
- Every stat attributed and dated from the verified claim ledger.
- Keyword in H1 and title; variants in H2s. Meta title ≤60, description ≤155.
- **Schema:** `SoftwareApplication` or `WebApplication` (with `applicationCategory`, `offers` at price 0) **plus** `BreadcrumbList`, plus `FAQPage` if there is an FAQ and `HowTo` if the tool has a procedural companion.
- **Internal links:** ≥3 in-body from `.seo/link-inventory.md` with varied anchors, ≥2 inbound from existing pages. Tools are also the best *outbound* internal-link source on the site: every relevant article should link to the tool, so add those inbound links generously.

---

## 9. Verify — no screenshot, no ship

The tool half cannot be verified by reading it. This gate is absolute:

1. Run the project's test suite and linter; add targeted tests for the calculation or parsing logic.
2. Run the tool **by hand** on the local dev server. Real inputs, real output, verified against the math done independently.
3. Exercise **every state**: pre-filled default, valid input, empty submit, malformed input, boundary value, failure/timeout (for fetch tools), and the kill-switch-off state if there is one.
4. **Screenshot every state** and hand them to the user. A tool page ships with pictures of it working, or it does not ship.

---

## 10. Register (Step 5)

Same batch as every other type, plus the tool-specific rows:

- `.seo/content-ledger.md` — a `shipped` row with type `tool`, the slug, and the target keyword.
- `.seo/link-inventory.md` — the tool registered as a link target with 4-5 anchor variants. Tools accumulate inbound links over years; the anchors matter.
- `.seo/briefs/tool-<slug>.md` — the verified claim ledger, kept. When a fee schedule changes next year, this file is how you find every number to update.
- The `/tools` hub and sitemap entries.
- A one-line **maintenance note** in the ledger row for anything with decaying data: what expires, and roughly when.

---

## 11. Anti-patterns

- **The gate.** Covered in §4, repeated here because it is the most common instinct and the most damaging one. An ungated tool that gets linked beats a gated tool that gets 40 emails.
- **The demo in disguise.** A "tool" that is really a product signup form with a calculation on top. Users detect this in seconds and never link to it.
- **The thin wrapper.** A tool page whose content is 300 words of keyword filler under a calculator. It ranks briefly, then does not.
- **The stale constant.** A fee, rate, or limit hardcoded from memory. Verify this run, date it on the page, note the expiry in the ledger.
- **The false clean.** A failed check rendered as a pass. See §4.
- **The infinite index.** Every user result generating an indexable page. See §4.
- **The tool nobody can find.** Shipped with no hub entry, no sitemap row, no inbound links from the articles that should obviously point at it.
- **The half-build.** Two runs to ship one tool. Scope down to a v1 that works, or ship a different type and queue the tool properly.
