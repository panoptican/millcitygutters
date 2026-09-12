# Lane: tools

<!-- sources: seo-content/SKILL.md Step 3a + seo-content/references/free-tool-pages.md §2,§4,§9 + seo-content/references/quality-loop.md 4c gates 8-14 -->

Builds one working free tool and the page around it. The tool is the deliverable; the prose under it is the second half, not the point.

The full build spec is `references/free-tool-pages.md`. This file exists so the orchestrator knows what routes here and what cannot be waived.

---

## Routes here

| Action | Candidate record carries |
|---|---|
| `create-tool` | The tool-intent query and its SERP read · the archetype (`free-tool-pages.md` §3) · the four feasibility answers · what v1 does, in one sentence · whether it is client-side or needs a server round-trip · the axis, if this is a Pattern F batch member (`lanes/programmatic.md`) |

**Tool intent is the one documented override to follow-the-SERP, and it runs *toward* the tool.** A query like "[thing] calculator" whose top 10 are all articles isn't Google asking for an article; it's Google ranking the best of a weak field because nobody built the tool. Ship the tool.

A tool candidate only reaches this lane after clearing two things at select: the **four-question feasibility gate** (capability, data freshness, cost/abuse surface, maintenance) and the **one-run test** — if a working v1 can't ship this run, the prose fallback goes on the slate instead and the tool queues as the top backlog candidate with a scoped spec.

A tool run is the long one. Budget for it and don't try to squeeze a second piece in after.

---

## Read first

1. `references/free-tool-pages.md` — the whole file. §2 feasibility, §3 archetypes, §4 non-negotiables, §5 design recon, §7 build, §8 page content, §9 verify, §10 register. Never skip.
2. `.seo/brand.md` — voice, and the visual language the tool must inherit.
3. `.seo/truth.md` — every constant the tool computes with that describes our product.
4. `references/writing.md` + `references/content-types.md` — the 600–1,200 words below the tool are held to the same craft bar as any other piece.
5. `references/quality-loop.md` 4c — gates 1–7 apply, then gates 8–14 stack on top.
6. `references/visuals.md` — when the tool renders a result that has shape.
7. `lanes/editorial.md` — the research and register steps are shared; this lane only replaces the build half.

---

## Steps

1. **Design recon, 30 minutes, do not skip.** Pull 2–3 concrete interaction references and name what you're taking from each. They inform the **interaction** only — the site's own design system owns the visual language.
2. **Research, scaled to three angles** (SERP teardown, primary sources, first-hand/product angle) and **tighten** verification rather than loosening it. Any number the tool computes with is load-bearing: a wrong constant is a wrong answer for every visitor, forever.
3. **Build the tool** — route at `/tools/<slug>`, handler, view reusing existing components, logic in a service module, `/tools` hub entry, sitemap entry, cite/embed affordances. **Default to fully client-side**; every avoided round-trip removes a cost line, an abuse vector, an outage and a latency complaint.
4. **Write the page** — 600–1,200 words *below* the tool at full craft rigor, following §8: how to read your result → methodology → worked example → related → FAQ. "We built a calculator" is not a content moat if the 800 words under it restate the top 10.
5. **Verify by hand on a running dev server**, exercising every state, and screenshot each one.
6. **Critics + proof in one message**, including the **tool-UX critic**, which drives the *running* tool like a hostile first-time user — empty submit, malformed input, boundary and absurd values, negative numbers, pasted whitespace, a failing fetch. Reading the code is not testing.

---

## Gates

Gates 1–7 from `references/quality-loop.md` 4c apply unchanged. These seven stack on top and **none of them is waivable**:

1. **The tool works, verified by hand** — exercised on a running dev server with real inputs, output checked against the math done independently.
2. **Every state screenshotted and handed to the user** — default/pre-filled, valid result, empty submit, malformed input, boundary value, failure/timeout, kill-switch-off if present.
3. **Ungated** — no email capture anywhere on the path to the result. The only exception is a tool where email *is* the deliverable, and even then the result renders on-page first.
4. **Failure renders neutral** — a check that couldn't run never displays as a pass, and never as a scary red fail.
5. **Cost and abuse controls present** — per-IP/session rate limit, global daily spend or volume ceiling, env-var kill switch, and public-host validation on any live fetch, all in the same commit as the tool. Not "later."
6. **Index posture correct** — the form page is indexable; per-entity result pages are `noindex, follow`; the tool is in the `/tools` hub and the sitemap.
7. **The content half clears its own bar** — 600–1,200 words with a real methodology section, dated constants from the verified ledger, and the tool schema emitted (`SoftwareApplication` or `WebApplication`, plus `BreadcrumbList`).

Two rules override every cost, scope or schedule argument:

- **Don't gate a free tool.** Control cost with scope, caching, rate limits and spend caps — never with an email wall. And never write copy narrating the policy ("no email required!"); just don't ask.
- **No screenshot, no ship.** A tool page ships with pictures of it working, or it does not ship. If there's no screenshot capability, drive it by hand in a real browser, describe each state precisely, and say plainly in the hand-off that verification was manual. Never claim a state works without having triggered it.

Two more that catch real failures: **"couldn't check" never renders as "clean"**, and **every ugly input has defined behavior** before ship — empty, malformed, absurdly large, negative, zero, unicode, pasted-with-whitespace, boundary.

---

## Satellite pages

Each shipped tool may earn **1–6 long-tail child articles** nested under its URL — `/tools/<tool>/<question>` — each answering one question the tool's own users ask, and each linking to the tool above the fold.

**Gate: the tool's output has been verified correct on real inputs before any satellite ships.** Satellites under a tool that computes the wrong answer multiply the wrong answer.

**Why:** on one audited site, 20 satellites under 9 tools were a second acquisition surface, ranking for questions the tool page itself never could.

---

## Register

- `.seo/content-ledger.md` — a `shipped` row with action `create-tool`, type `tool`, the slug, the target keyword, and a seeded **Performance** row.
- `.seo/link-inventory.md` — the tool registered with 4–5 anchor variants. Tools accumulate inbound links for years; the anchors matter more here than anywhere else.
- **Inbound links beyond the required two** — link to the tool from every existing article where it is genuinely the better answer. A tool is the best inbound-link *target* on the site.
- `.seo/briefs/tool-<slug>.md` — the verified claim ledger, kept. When a fee schedule or rate changes next year, this is how you find every number to update.
- `.seo/runs/<date>.md` — the seven gates with their results, the screenshots handed over, the cost controls shipped (or `n/a, client-side`), and the maintenance note.
- `.seo/needs-you.md` — review and merge the branch (a tool is code and stays on the branch until a human merges it) · set the kill-switch env var in production · anything the tool needs an API key for.
- A one-line **maintenance note** in the ledger row for anything with decaying data: what expires, and roughly when.
