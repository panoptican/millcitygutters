# Lane: programmatic

<!-- sources: seo-sprint/SKILL.md (Initialize/Resume modes, phase table, anti-patterns) + seo-sprint/references/methodology.md (publishing-order inversion, five lessons) + programmatic-seo/SKILL.md (the 12 playbooks, data defensibility, URL structure) -->

Ships or extends a **batch** of templated pages behind one pattern, off a persistent roadmap. The unit of work is a phase, not a page: a phase picks a pattern, generates its pages, wires the internal-link spine, verifies against the pattern's bar, and marks its tracker row done in the same diff.

The roadmap lives at `.seo/roadmap.md` (or wherever `config.paths.roadmap` points). It survives context compaction, fresh sessions, new worktrees and long pauses — which is the entire reason it is a file and not a conversation.

---

## Routes here

| Action | Candidate record carries |
|---|---|
| `create-programmatic` | The pattern (A–F) · the phase number and title from the tracker · the entity list for this batch (competitors, use-cases, pairs, topics, providers/states/insurers) · per-entity keyword data (volume, KD, difficulty bucket) · the data source backing each page's unique value · the link-spine targets |

Two entry shapes:

- **No roadmap yet** → Initialize. Build `.seo/roadmap.md` from research and stop. Do not auto-execute Phase 0; pattern priorities and competitor lists are worth a human pass.
- **Roadmap exists** → Resume. Take the next `pending` phase with the lowest number, or the one the user named.

A partial state (`.seo/config.json` exists, roadmap doesn't) is neither: ask the user, they may have started and aborted. Never wipe. In unattended mode, don't ask and don't guess — build the roadmap into the gap (Initialize step 4 onward, reusing the existing config) and file the "is this a resumed or abandoned sprint?" question in `.seo/needs-you.md`.

---

## Read first

1. `.seo/roadmap.md` — the full doc, including the Phase Status Tracker and the Keyword Research Appendix. Never skip on Resume.
2. `.seo/brand.md` — positioning and, critically, **anti-positioning**. The honest-tradeoff sections are written from it.
3. `.seo/truth.md` — every capability, price and integration claim on a templated page. A wrong claim replicated across 40 pages is 40 `correct` candidates later.
4. `references/methodology.md` — the publishing-order inversion and the five field lessons. Read on Initialize, and whenever a phase order is being argued.
5. `references/patterns/<pattern>.md` — the spec, data shape, quality bar and worked example for the pattern this phase ships. One file, not all of them.
6. `references/pseo-playbooks.md` — read when the pattern isn't one of A–E, or when choosing which playbook a new axis belongs to.
7. `references/free-tool-pages.md` — Pattern F only.
8. `references/stacks/<framework>.md` (detected via `references/stacks/detection.md`) — native output for this repo. Falls back to portable markdown per `references/output-formats.md`.
9. `references/quality-loop.md` — **the per-pattern word floors, internal-link minimums and schema requirements live here.** Never skip; the gates read from it.
10. `references/research-recipes.md` — Initialize, or any phase whose commercial-intent data is over 60 days old.
11. `.seo/link-inventory.md` — the link targets and anchor variants the spine is wired from.

---

## Why the order is what it is

The instinct is to write educational content first to build "authority," then add product pages later. That is backwards. The order that actually performs:

| Order | Pattern | Why |
|---|---|---|
| 1 | **A** — `/alternatives/[competitor]` | Highest conversion intent. Someone typing "[tool] alternative" wants to switch today. |
| 2 | **D** — `/compare/[a]-vs-[b]` | High intent. The user is deciding between two known tools — be the third option. |
| 3 | **B/C** — `/for/[use-case]`, `/for/[audience]` | Mid intent. A job-to-be-done with no tool chosen yet. |
| 4 | **E** — `/playbooks/[topic]` long-form | Brand authority plus AI-citation surface. Lower direct conversion, far higher inbound-link draw. Almost nobody cites an alternatives page. |
| 5 | **F** — `/tools/[axis]` free tools | Best inbound-link target on the site, and the only pattern that keeps earning links without asking. Ships through `lanes/tools.md`. |

Phase 0 is technical foundations (`lanes/technical.md`) and comes before all of it. Striking-distance boosts front-load ahead of new-page phases on any existing site — they're 1–3 hours against 4–8, they use link equity that already exists, and they show movement in 7–21 days.

Full theory and the five field lessons in `references/methodology.md`. The three that break phases most often:

- **Capture singular and plural in one URL.** `[brand] alternatives` usually carries 2–3× the volume of the singular. One URL ranks for both if the H2 reads "Best [Brand] alternatives in 2026" and the meta title hints plural. Bake it in from page 1; retrofitting cost an entire phase on a real project.
- **The honesty section is non-negotiable.** Every alternatives page lists 3–4 things where the competitor genuinely wins. Pages without it measurably underperform on both ranking and conversion.
- **Internal-link minimums are quality bars, not nice-to-haves.** Verify them mechanically. Every page reachable from ≥2 other pages, ≥1 of them a frequently-crawled hub.

---

## Steps

### Initialize (no roadmap yet)

1. **Stack, config and brand come from Step 0, not from here.** `.seo/config.json` and `.seo/brand.md` are foundation files: `references/foundation.md` §1 detects the stack and frontend convention, §2 builds the brand and anti-positioning. Read them; never re-derive them and never overwrite them. If either is missing, the run is in the wrong step — go back to foundation.
2. **Run keyword research** — `references/research-recipes.md`. Recipes A (authority baseline) through E (striking distance). Winnability comes from the difficulty bucket derived from your own GSC page-1 positions, not from authority arithmetic. Run the relevance gate on every content-gap result: raw output is mostly a big competitor's incidental rankings. Cache to `.seo/keyword-research.json` (30-day rule) and put the decision-ready summary in the roadmap's Keyword Research Appendix.
3. **Run the technical foundations audit** — `lanes/technical.md`. Whatever it finds becomes **Phase 0**. Don't gloss over it: the day-0 crawl shapes Google's understanding of the site for months, and retroactive fixes are harder.
4. **Generate the roadmap** from `assets/roadmap-template.md` at `config.paths.roadmap` (default `.seo/roadmap.md`): site facts, reference data (the exact controller/page-file paths later phases will edit), the Keyword Research Appendix, and the **Phase Status Tracker** — Phase 0 first, then one row per page candidate grouped by pattern, ordered within a pattern by traffic potential desc, then volume desc, then KD asc. Striking-distance boosts near the front. Off-page phases get one tail-end phase per category (`lanes/offpage.md`).
5. **Generate `.seo/link-inventory.md`** from the assets template, pre-populated with every URL the skill might link to.
6. **Stop.** Print the roadmap path and recommend a review before Phase 0.

### Resume (execute one phase)

1. **Read state** — the roadmap, `.seo/brand.md`, `.seo/truth.md`, `.seo/link-inventory.md`, `.seo/config.json`. Locate the tracker, take the next `pending` phase, print it plus the two after it.
2. **Confirm scope** — one question to the user: continue with Phase N / pick a different phase / re-audit (refresh research and regenerate the tracker) / just show the tracker. In unattended mode, take the lowest pending phase and write the decision into the run record.
3. **Re-research what decays.** Current competitor pricing, feature changes, plan names. Don't trust 60-day-old cached data on commercial-intent terms. Volumes and KD are fine for 30 days (the cache rule); *claims about a competitor* are not.
4. **Generate the page payload** per `references/patterns/<pattern>.md`, output shaped by `references/stacks/<framework>.md`. When the content store is a database, the batch is a seed file plus a load task, rows land as drafts, and `references/stacks/app-db.md` §5 is the shape. Fan out per-entity generation across subagents when the batch is more than three pages; the main thread keeps the shared frame, the link spine and the tracker.
5. **Wire the link spine in the same phase.** Outbound links per the pattern minimums, and ≥2 inbound links from existing pages with ≥1 from a `crawl_hubs` page. A batch that links only to itself is a closed loop Google reads as a doorway cluster.
6. **Verify against the gates below.** Fix failures; don't ship under-spec.
7. **Update `.seo/link-inventory.md`** with every new page plus anchor variants.
8. **Update the tracker row** in `.seo/roadmap.md` — status `completed`, with the PR ref or commit SHA. **This edit lands in the same edit batch as the page work**, never after, so one diff carries both the code and the status change and the tracker never drifts from `main`.

---

## The patterns

| Pattern | Route shape | Spec |
|---|---|---|
| **A** | `/alternatives/[competitor]` | `references/patterns/alternatives.md` |
| **B/C** | `/for/[use-case]`, `/for/[audience]` | `references/patterns/use-case.md` |
| **D** | `/compare/[a]-vs-[b]` | `references/patterns/compare.md` |
| **E** | `/playbooks/[topic]` (long-form pillar) | `references/content-types.md` (type 1, pillar guide; the 2,500-word bar lives there) |
| **F** | `/tools/[axis]` free tools at scale | `references/free-tool-pages.md` + `lanes/tools.md` |

### Pattern F — free tools as a programmatic axis

A tool is Pattern F when the same tool template is worth instantiating across a real-world entity axis, so each page carries a different answer rather than a different noun. The axes that work carry data that genuinely differs per entity:

- **Provider** — per-vendor/per-carrier/per-platform lookups where each provider's rules, fees or formats differ.
- **State / jurisdiction** — anything with a statutory table behind it: rates, deadlines, thresholds, filing rules.
- **Insurer / payer** — coverage, formulary, prior-auth and appeal rules that vary by payer.

The axis is only legitimate if the *answer* changes per entity. A calculator that returns the same number with the state name swapped in the H1 is a doorway page and will be treated as one. Run the four-question feasibility gate (`free-tool-pages.md` §2: capability, data freshness, cost/abuse surface, maintenance) **per axis, once**, then the one-run test per batch. Every Pattern F page inherits the seven non-waivable tool gates in `lanes/tools.md` — the batch does not dilute them.

Index posture for the axis: the **form/hub page and each entity page are indexable**; per-*result* URLs (a specific user's computed output) are `noindex, follow`. A thousand thin result URLs in the index is exactly the site-quality profile this pattern is trying to avoid.

### Generator: one fear × who × what × moment

Pages that descend from a **schema list** — every field, every document type, every enum value — are exactly what Google refuses to fetch. Nothing in a field list corresponds to something a person types.

Pages that descend from **one fear the audience actually has**, factored as `{who is asking} × {what document or situation} × {the moment}`, index. Pick the fear first, then factor it.

Worked example, generic product, fear = "I will lose the paperwork I need":

| Who | What | Moment | Page |
|---|---|---|---|
| New hire | Offer letter | First week | `/for/new-hire-offer-letter-checklist` |
| Freelancer | Client contract | Chasing an unpaid invoice | `/for/freelancer-contract-unpaid-invoice` |
| Executor | Insurance policy | Settling an estate | `/for/executor-finding-insurance-policies` |

Two requirements on the batch:

1. **Every generated page carries a demand artifact in its data entry** — a GSC row (query + impressions) or a dated forum thread asking it. No artifact, no page.
2. **Exactly one canonical owner URL per intent.** A second page for the same intent fails the batch; merge them before generating.

**Why:** an audited competitor's 6,500-URL site was 236 real pages × 32 locales. Page count was never the gap.

### Beyond A–F: the 12 playbooks

When the pattern isn't one of the six above, pick from the 12 in `references/pseo-playbooks.md`: **Templates · Curation · Conversions · Comparisons · Examples · Locations · Personas · Integrations · Glossary · Translations · Directory · Profiles.** That file carries the per-playbook data requirements, keyword pattern, template design and indexation strategy. Playbooks layer — "best coworking spaces in San Diego" is Curation × Locations.

**Choose by what data you hold**, not by what pattern looks fun. The hierarchy of data defensibility, quoted verbatim:

> 1. Proprietary (you created it)
> 2. Product-derived (from your users)
> 3. User-generated (your community)
> 4. Licensed (exclusive access)
> 5. Public (anyone can use—weakest)

A batch built on level 5 alone is a batch anyone can replicate this afternoon. If the only available data is public, the phase's unique value has to come from somewhere else — a real editorial layer, a first-party benchmark laid over the public rows, or a genuinely better interface — and if it can't, the phase should not ship.

**Subfolders, not subdomains.** `yoursite.com/templates/resume/`, never `templates.yoursite.com/resume/`. Subfolders consolidate domain authority; subdomains split it.

---

## Gates

Non-waivable. Cost never overrides a gate. The per-pattern **word floors, internal-link minimums and required schema** are the tables in `references/quality-loop.md` — read them there, and run them mechanically rather than eyeballing:

```bash
python3 scripts/word_count.py <path> --min <pattern-floor>
python3 scripts/link_audit.py --slug <slug> --pattern <A|B|C|D|E>
python3 scripts/link_audit.py --orphan-check --root .
python3 scripts/tech_audit.py --schema <url>
```

On top of the shared bar, this lane adds:

1. **Unique value per page.** Each page answers something specific to its entity. Swapped variables in a shared template is a doorway page. If two pages in the batch would satisfy the same searcher equally, they should be one page.
2. **Honesty section on every Pattern A page** — 3–4 rows, each naming a specific feature or dimension where the competitor genuinely wins, each 30+ words, each concrete. Missing or thin fails the phase.
3. **Truth agreement across the whole batch.** Every claim about our capability, pricing or compliance matches `.seo/truth.md`; every claim about a competitor is dated and sourced this run.
4. **Singular and plural captured in one URL** where the keyword pair exists.
5. **Inbound links wired in the same phase** — ≥2 per page, ≥1 from a `crawl_hubs` page. No orphans; `--orphan-check` clean.
6. **Schema emitted and validating** per the pattern's requirement.
7. **Meta uniqueness across the batch** — no two pages share a `<title>` or a `<meta name="description">`; title ≤60, description ≤155; exactly one `<h1>`; self-referencing canonical.
8. **SSR body present.** View-source on a rendered page shows the copy. A JS-only shell gets soft-404'd, and a batch of them gets soft-404'd all at once.
9. **Sitemap `lastmod` is a content date**, never a build date (`lanes/technical.md`).
10. **The tracker row is updated in the same edit batch** as the page work.

### Anti-patterns

- **Don't target head terms at low authority.** Stick to KD ≤ bucket ceiling while the domain is still climbing. The roadmap should refuse to hold doomed phases.
- **Don't ship pages with no inbound links.** A new page nobody links to is an island.
- **Don't ship an alternatives page without the honesty section.**
- **Don't skip the schema.** It's a gate, not a garnish.
- **Don't ship 10,000 thin pages.** 100 pages that answer something beat 10,000 that don't, and the thin ones drag the good ones down with them.
- **Don't merge or deploy.** End the run per `config.git.mode` (diff, commit, or PR) and hand it over.
- **Don't restart Initialize over a partial state.** Prompt instead.
- **Don't fan out across 20 unrelated themes.** Topical depth beats topical breadth: own a niche slice, then widen.

---

## Register

- `.seo/roadmap.md` — the tracker row flipped to `completed` with PR ref or SHA, in the same edit batch as the page work. On Initialize, the whole roadmap.
- `.seo/content-ledger.md` — one `shipped` row per page in the batch (date · action `create-programmatic` · pattern · slug · target keyword · primary internal links) plus a seeded **Performance** row per page (`state: unmeasured`, `indexed: unchecked`). A batch of 8 writes 8 rows; the measure step reads them individually, because a pattern's failure is usually 2 of 8 pages, not the pattern.
- `.seo/link-inventory.md` — every new page as a link target with 4–5 anchor variants.
- `.seo/keyword-research.json` — any freshly-bought rows, with the fetch date, so the 30-day cache rule holds next run.
- `.seo/runs/<date>.md` — the phase executed, why this phase over the alternatives, the entities shipped, the gate results, the DFS call count and cost (and how many rows came from cache), and **what was not done**.
- `.seo/needs-you.md` — review and merge the branch · submit the updated sitemap · anything in the phase that needs a login or an external submission.
