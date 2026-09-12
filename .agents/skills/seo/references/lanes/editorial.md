# Lane: editorial

<!-- sources: seo-content/SKILL.md Steps 2-4 + Step 5 (register) + Step 1 boost path · seo-sprint/references/striking-distance.md (boost recipe) · seo-content/references/quality-loop.md 4c (gates) -->

One piece per run. Two paths: **create** (a new guide/how-to/listicle/comparison/definition/data-study/opinion/case-study/resource-library) and **boost** (a rewrite, expansion or retitle of a page that already ranks). Both end at the same gates.

The boost path is not the lesser one. Retitling a page at position 4 with 3,000 impressions routinely beats an eleventh article on expected value, and select.md is allowed to hand this lane a `refresh` because of that.

---

## Routes here

| Action | Candidate record carries |
|---|---|
| `create-editorial` | Target keyword + cluster · chosen content **type** (from `content-types.md`) · the SERP read that chose it · difficulty bucket + volume/KD · the intent bucket · the information-gain hypothesis · exclusion set from the ledger |
| `refresh` (boost path) | The live URL · the target query · current position, impressions, CTR · which of the three opportunity sizes won (recover / CTR / rank, `gsc.md` §2c) · the specific decay or gap that caused it |

A `refresh` whose fix is a *wrong claim* is not this lane — that is `correct`, and it goes to `lanes/fix.md`. A `refresh` whose fix is a broken artifact is `repair` (`lanes/technical.md`). This lane handles refreshes that need **more or better writing**.

---

## Read first

In order. Skip where noted.

1. `.seo/brand.md` — voice tags, perspective, forbidden words, positioning. Never skip.
2. `.seo/truth.md` — every product claim the piece will make comes from here. Never skip.
3. `references/writing.md` — craft spec and the two-lane build. Never skip.
4. `references/content-types.md` — the chosen type's outline, word floor, link minimums, schema. Skip on the boost path (the type is already fixed by the live page).
5. `references/research-brief.md` — fan-out rules, ledger row format, the verifier contract. Skip on a boost whose fix is a title/meta rewrite only.
6. `references/proprietary-data.md` — the first-party hunt and its hard contract. Read whenever the piece could carry a number of ours.
7. `references/visuals.md` — read when the piece has anything with shape (comparison, trend, distribution, process, structure).
8. `references/content-stores.md` + `references/output-formats.md` — where the piece lands. Skip `output-formats.md` for DB/CMS stores.
9. `references/quality-loop.md` — the critic panel and the hard gates. Never skip.
10. `references/polish-pass.md` + `references/ai-writing-detection.md` — read at the revise step, not before.
11. `references/aeo/intent-buckets.md` — the answer-intent bucket the piece must match.
12. `references/gsc.md` §2c (sizing a boost) and §7a (discoverability). §2c on the boost path only.

---

## Steps

### Create path

**1 — Load the pick and the frame.** Read the candidate record, `.seo/content-ledger.md` (exclusion set + backlog), `.seo/link-inventory.md` (link targets and anchors), `.seo/config.json` (`crawl_hubs`, content surface, stack). Decide the slug now — the wiring lane needs it.

**2 — Fan out research and wiring in ONE message.** Seven `Agent` calls in a single response, not one per turn. Six research angles plus the wiring lane:

| Agent | Returns |
|---|---|
| SERP teardown | Table-stakes sections vs the gap, in ledger rows |
| Primary sources / studies | Ledger rows with URLs and dates |
| Statistics | Ledger rows, each with source + as-of date |
| Contrarian / counter-evidence | The best argument against the piece's thesis |
| **Proprietary data / first-hand** | The first-party figure with n, window, method, and the saved query (`proprietary-data.md`) |
| Entity / topical map | The entities the top 10 cover and the ones they miss |
| **Wiring lane** (Step 3a) | Route, controller/registry entry, sitemap + `lastmod`, inbound-link edits, test stub, page frame in the site's existing layout, figure component skeleton |

Every researcher is a **leaf**: no subagents, ≤15 page fetches, no background shells. Put that sentence in each prompt — a researcher that reads the fan-out instruction without it re-runs the fan-out one level down and six agents become ninety.

The wiring agent needs only the repo and the slug, so it never waits for the brief. It never writes prose; the writer never touches routes.

**3 — Verify, starting at five packets.** One verifier for the whole ledger, spawned by the main thread. It cross-checks every claim against a second source and returns the **corrected merged ledger**. The proprietary-data packet is routinely the long pole (a real run: 31 minutes against ~10) — don't hold the pass for it. When it lands, resume the *same* verifier with the delta.

**4 — Assemble the brief in the main thread.** No synthesis agent. The verifier's merged ledger is the spine; add four short sections it doesn't carry: the entity-coverage map, table-stakes vs gap, the **information-gain statement**, and the angle. Write `.seo/briefs/<slug>.md`.

> **If you can't state the information gain concretely, stop and go back to select.** The piece won't rank. Say so in the run record rather than writing it anyway.

Every piece **attempts** an original-data element, and the attempt is real work. The highest-value shape is our data as the missing dimension on public data, not a raw internal number. If `proprietary-data.md` §6's ladder comes up dry, say so in the brief and fall back to the other information-gain forms. Never invent one.

**5 — Write the prose lane into the wired frame.** Starts when the brief exists, with `[[FIRST-PARTY FIGURE — pending]]` still marked if the data packet is late; the figure lands in the slot when it arrives. Write from the brief, not from memory. Deliver: the information gain in the body · voice from `.seo/brand.md` · the type's structure · the answer-intent bucket and lead-with-the-answer shape · on-page (H1/title/slug/meta ≤60 and ≤155/TOC/FAQ from the real PAA set) · schema for the type · E-E-A-T (named author, first-hand framing, visible date) · in-body internal links at the type's minimum with varied anchors · figures drawn as hand-authored inline SVG using the repo's own tokens.

**6 — Critics and proof in ONE message, the moment the writer returns.** Critic panel (skeptic/fact-check, information-gain, AEO/extractability, voice, completeness, plus visuals when the piece has figures) reads the draft. The proof lane reads the *rendered* page: test suite, `scripts/word_count.py`, `scripts/link_audit.py --orphan-check`, `scripts/tech_audit.py --schema <url>`, screenshots in light and dark at mobile and full width. Neither waits for the other. Critics are leaves too. Full panel in `quality-loop.md`.

**7 — Revise, bounded to two rounds.** Bias toward adding substance over reshuffling words. Run `polish-pass.md` for the voice axis and `ai-writing-detection.md` before the last read. Re-run only the critics that failed. If a **gate** still fails after two rounds, the piece was mis-selected — say so instead of shipping under-spec.

### Boost path (`refresh`)

**1 — Size it before touching anything.** `gsc.md` §2c: the largest of recover / CTR / rank decides both the value and the kind of fix. Put it in clicks, not adjectives. "The CTR looks bad" is not a size.

**2 — Pick the fix from the size.**
- **CTR gap** (ranks fine, nobody clicks) → meta title and description rewrite, keyword toward the front, title ≤60. Often the whole job.
- **Rank gap** (position 5–20, `striking-distance` shape) → 200–400 words of real depth in the section holding the target query, plus 3–5 new internal links *into* the page from related pages that already rank, plus an FAQ with `FAQPage` JSON-LD if one is missing.
- **Recover** (decay, position dropped >30%) → find what changed. Usually a competitor shipped fresher content or the piece's dated facts expired. Re-verify every dated claim against the brief in `.seo/briefs/<slug>.md`, then expand where the SERP moved.

**3 — Skip the candidate when the boost can't land.** Impressions <50/month · top 3 are all high-authority with deep content you won't displace · the page already carries 1,500+ words on the topic and is out of easy depth-adds. Say which one and move to the next candidate.

**4 — Bump `date_modified` and the sitemap lastmod to the content date.** Touching a page bumps its `date_modified`. Sitemap `lastmod` must be a content date, never a build date (`lanes/technical.md`).

**5 — Same critics, same gates.** A boost is a smaller diff, not a lower bar. The panel runs against the changed sections plus the whole rendered page.

---

## Discoverability wiring (both paths, non-negotiable)

How fast a page indexes is decided *before* deploy, not after. Verify on the dev server:

- **In the sitemap source** with today's `lastmod`. Generated sitemaps with hand-maintained route arrays are the classic miss.
- **Canonical points at itself**, not at the layout default.
- **No inherited `noindex`** in the rendered head or the response headers.
- **Body text present in the server-rendered HTML** — `curl -s localhost:<port>/<path> | grep "<a distinctive sentence>"`. A JS-only shell gets soft-404'd.
- **Returns 200**, not a redirect.
- **≥2 inbound links, and ≥1 from a frequently-crawled hub** — pick it from `crawl_hubs` in `.seo/config.json` or the top-traffic pages, not by convenience. Two links from posts Google visits quarterly is close to no discovery signal; one from the homepage or a live hub is discovery in days.
- **Test stub** present for the new route (the wiring lane writes it).

On a DB/CMS store the link edits become an inbound-link **punch-list** (2 named pages + anchors) unless a write path is configured, and the sitemap check runs against the store's generator.

---

## Gates

All must pass. Cost never overrides a gate. Full text in `quality-loop.md` 4c.

1. **Information gain** present concretely in the body. Dressed-up synthesis fails.
2. **Citation coverage** — every claim traces to the verified ledger; no `unverified` claim as fact; no fabricated statistics. **Code, commands and config carry provenance**: each block names the official doc and the version it applies to, checked against that doc rather than from memory.
3. **First-party data hygiene** (when the piece carries original data) — aggregates only · n ≥ 50 per published cell · no PII and no segment narrow enough to identify one account · headline figure re-derived a second way · population stated as ours · the user has seen the actual numbers · query, run date, exclusions and refresh interval saved to the brief. This gate fails **closed** — an unapproved or under-sized number comes out of the piece.
4. **Truth agreement** — every product, pricing or compliance claim matches `.seo/truth.md`. A contradiction here is a `correct` candidate, not a copy edit.
5. **AEO-readiness** — extractable answer up top, self-contained quotable claims, entity map covered, schema emitted, date stamped. Original figures are brand-attributed, not pronoun-attributed.
6. **Deterministic** — `word_count.py --min <type-floor>` · `link_audit.py --orphan-check` (plus hand-confirmed ≥3 in-body / ≥2 inbound) · `tech_audit.py --schema <url>` if rendered.
7. **Discoverability** — the seven checks above, verified, not assumed.
8. **Voice** — brand match confirmed, forbidden-words grep clean.
9. **Visuals** (when the piece carries figures) — inline SVG on the repo's tokens · **looked at rendered in light and dark, mobile and full width** · zero-based axes with units, n and as-of date · every figure number also present as text · `role="img"` + `<title>`/`<desc>` or explicitly decorative · shipped in the same commit as the prose.

Never auto-publish. On a file store the piece lands on a branch; on a CMS it lands as a **draft** or as a hand-off with a field map.

---

## Register

Writes to the ledger and run record (formats in `references/register.md`):

- `.seo/content-ledger.md` — a `shipped` row (date · action `create-editorial` or `refresh` · type · title · slug/URL · target keyword · primary internal links) and a seeded **Performance** row (`state: unmeasured`, `indexed: unchecked`). A boost logs as a `boost` row against the existing slug, not a new one.
- `.seo/link-inventory.md` — the new page registered as a link target with 4–5 anchor-text variants.
- `.seo/briefs/<slug>.md` — the verified claim ledger, kept. It is the citation record, the reuse basis for a later refresh, and the maintenance record for anything with decaying data.
- `.seo/runs/<date>.md` — what was measured, why this candidate won, the information-gain statement, the gate results, the API call count and cost, **what was not done** (the runners-up and why), and the next-up backlog.
- `.seo/needs-you.md` — anything only the human can do: review and merge the branch, approve a first-party figure, send the inbound-link punch-list to the CMS, hit "Request indexing" on the inspection link after deploy.
- Ledger row gets a one-line **expiry note** for anything with decaying data (a fee schedule, a rate, a year in the title).
