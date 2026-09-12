<!-- merged from seo-content/references/quality-loop.md + seo-sprint/references/quality-bars.md -->

# Quality Loop — critique, revise, gate

A one-shot draft is a first draft. As of 2026, content that ranks and gets cited goes through **critique → revise → re-check**, with the critique done by a perspective separate from the one that wrote the prose. This step replaces "write it, run the word-count script, ship" with a short adversarial loop: a critic panel scores the draft, you revise the weakest dimensions, and hard gates decide whether it ships.

Keep it bounded: **at most two revise rounds.** The goal is a piece that clears every gate, not infinite polishing.

---

## 4a. The critic panel

Run these critics against the draft + the research brief — five always, **plus the visuals critic whenever the piece carries figures or should**, plus the tool-UX critic for a free tool page (added, not substituted). Where the host supports subagents, run them in parallel and as *separate* agents from the writer (a critic invested in the prose will rate it too kindly). Each returns a 1-5 score + the specific, actionable misses.

**Spawn the whole panel in one message, the moment the writer returns — and put the proof lane in that same message.** The proof lane is one leaf agent (or the main thread, if the repo makes it cheap) that runs the deterministic gates from 4c: the test suite, `word_count.py`, `link_audit.py --orphan-check`, `tech_audit.py --schema`, and the rendered screenshots in light and dark at mobile and full width. Critics read the draft; proof reads the rendered page; neither waits for the other. In a measured run the builder did tests and screenshots serially *before* the critics could start — that's ~5 minutes of critics waiting on work they don't consume. The visuals critic is the one exception: it reads the proof lane's screenshots, so spawn it when those land, not before.

**Critics are leaves.** The main thread spawns all of them and nothing else spawns anything. Say so in each critic's prompt — *"You are a leaf agent: do not spawn subagents, do not spawn subagents, do not leave background shells running."* A critic handed this file without that line will read "run them in parallel" as a mandate to fan out its own panel.

| Critic | Asks | Fails when |
|---|---|---|
| **Skeptic / fact-check** | Is every factual claim in the verified ledger? Any assertion without a source? Cross-check the draft's numbers against the ledger; try to refute the load-bearing claims. | An unsourced or unverified claim is stated as fact; a number doesn't match the ledger. |
| **Information-gain** | What's here that's in *none* of the top 10? Is the original element (data / first-hand / expert / framework) real and substantive, or is the piece dressed-up synthesis? Where it's first-party data: does the headline figure re-derive, is the population stated honestly, does every stat carry n + window + as-of date, is the method section real? | The information-gain statement isn't actually delivered in the body; an original figure is undated, un-sized, unattributed, or the piece quotes an external benchmark on a question our own data could have settled. |
| **AEO / extractability** | Lead-with-the-answer? Self-contained quotable claims? Stats attributed + dated? Entity map fully covered? Schema + freshness present? (`lanes/aeo.md`) | The answer is buried; claims need context to parse; entity gaps; no schema/date. |
| **Voice** | Matches `.seo/brand.md` — voice tags, perspective, forbidden words? Reads like the site's existing content? | Forbidden word present; register is off; sounds like generic SaaS. |
| **Completeness / structure** | All table-stakes sections covered? Logical flow? Any thin (<~150-word) section that promises more than it delivers? | A SERP table-stakes section is missing; a heading over-promises. |
| **Visuals** *(when the piece has, or should have, figures)* | Look at the **rendered** page in light and dark, mobile and full width. Does each figure show something the prose can't? Does it look like this site drew it, or like a chart library's default theme? Zero-based axes, units, n + date? Numbers also present as text? Titled/described, or explicitly decorative? And the inverse question: is there a comparison, trend, distribution, or process in this piece that's carrying on in prose where a figure would land it? (`visuals.md`) | A figure is decorative, off-palette, invisible in one theme, clipped, or charts invented data — or the piece explains something with obvious shape and draws nothing. |
| **Tool UX** *(type 10 only)* | Drive the tool like a hostile first-time user. Empty submit, malformed input, boundary and absurd values, negative numbers, pasted whitespace, a failing fetch. Is the default state pre-filled with a realistic example? Is failure copy neutral and explicit? Is the result interpretable without reading the prose? Any gate, anywhere? | It throws, hangs, renders a failure as a pass, gates the result behind an email, or arrives as a blank form the user has to guess their way into. |

Score the draft on each axis. **Any axis ≤3 is a revise target.** On a tool page, the tool-UX critic must run against the **running tool**, not against the source. Reading code is not testing.

---

## 4b. Revise

Fix the weakest dimensions first — the panel hands you specific misses, not vibes. Bias toward **adding substance** (a missing source, the under-delivered original-data point, an uncovered entity) over reshuffling words. For the voice axis, the bundled polish pass (`polish-pass.md`) is the tool; run it here.

After revising, re-run only the critics that failed. Stop when all of them are ≥4 **or** you've done two rounds — then go to the gates. If after two rounds a *gate* still fails, that's signal the piece was mis-selected; say so in the hand-off rather than shipping under-spec.

---

## 4c. The hard gates (pass/fail — must all pass to ship)

The critic panel improves the piece; the gates decide if it ships. These are non-negotiable:

1. **Information gain** — the brief's information-gain element is concretely present in the body (original data / first-hand / expert / novel framework). *This is the gate that matters most in 2026.* Dressed-up synthesis fails.
2. **Citation coverage** — every factual claim traces to the verified ledger; no `unverified` claim shipped as fact; high-stakes numbers carry inline attribution. No fabricated statistics.
   - **First-party data hygiene** (whenever the piece carries original data, `proprietary-data.md` §2): aggregates only · every published cell n ≥ 50 · no PII and no segment narrow enough to identify one account · headline figure re-derived a second way · population stated as ours, not as the industry's · the user has seen the actual numbers · query, run date, exclusions, and refresh interval saved to `.seo/briefs/<slug>.md`. This gate fails **closed** — an unapproved or under-sized number comes out of the piece, it doesn't ship with a caveat.
   - **Code provenance** (whenever the piece carries code, commands, config, or API parameters): **every block names the doc it came from** — a URL to the official reference, plus the version the syntax applies to. A snippet with no source is an unverified claim wearing a monospace font, and it is the most confidently wrong thing this skill can publish: prose errors read as opinion, but a hallucinated flag or a renamed method fails for every reader who pastes it. Check each block against the linked doc, not against memory (use the `context7-mcp` skill where the library is covered). No source, no block.
3. **AEO-readiness** — extractable answer up top, self-contained quotable core claims, entity map covered, required schema emitted, date stamped (`lanes/aeo.md`). Original figures are **brand-attributed, not pronoun-attributed** ("[Brand]'s analysis of N…" survives extraction; "our data" doesn't), and `Dataset` schema is emitted when the piece carries a genuine dataset.
4. **Deterministic checks** (the bundled scripts):
   - `python scripts/word_count.py <path> --min <type-floor>` — meets the type's word floor (`content-types.md`).
   - `python scripts/link_audit.py --orphan-check --root .` — not an orphan; then hand-confirm ≥3 in-body + ≥2 inbound links. *(File stores only — `link_audit.py` is filesystem-based. For DB/CMS, confirm the link minimums against the sitemap/API by hand, per `content-stores.md`.)*
   - `python scripts/tech_audit.py --schema <url>` if rendered — schema validates.
5. **Discoverability** (`gsc.md` §7a) — indexing speed is decided *before* deploy, so these are checked on the dev server, not hoped for: **in the sitemap source** with today's `lastmod` (generated sitemaps with hand-maintained route arrays are the classic miss) · **canonical points at itself**, not the layout default · **no inherited `noindex`** in the rendered head or headers · **body text present in server-rendered HTML** (`curl -s localhost:<port>/<path> | grep "<a distinctive sentence>"` — a JS-only shell is what gets soft-404'd) · **returns 200**, not a redirect · **≥1 of the required inbound links comes from a frequently-crawled page** (`crawl_hubs` in config, or the top-traffic pages). Two links from posts Google visits quarterly is close to no discovery signal.
6. **Voice** — brand match confirmed, forbidden-words grep clean.
7. **Visuals** (whenever the piece carries figures, `visuals.md`) — inline SVG themed from the repo's own tokens (no invented hex) · **rendered and looked at in light and dark, mobile and full width** · zero-based axes with units, n, and as-of date · every figure number also present as text · `role="img"` + `<title>`/`<desc>` on meaningful figures, `aria-hidden` on decorative ones · ids namespaced by slug · shipped in the same commit/draft as the prose. No figure ships on the assumption that it renders — the failures here (clipped labels, dark-on-dark axes, colliding gradient ids) are eye-only catches.

### Two gates that apply to every piece

These sit alongside 1–7 and are not waivable either:

- **Answer-first** — the first paragraph after the H1 answers the query in **40–60 words** and stands alone when quoted with no surrounding context. *Why: that paragraph is what an extractor lifts; a preamble means the page gets skipped for one that leads with the answer.*
- **Intent owner** — the piece's intent has **exactly one owner URL** in the ledger coverage map (`.seo/content-ledger.md`), and it is this one. A second owner means this should have been a `refresh` of the existing page, not a new piece. *Why: two pages for one intent split the equity and Google picks the canonical you didn't choose.*

### Additional gates for a free tool page (type 10)

All seven above still apply. These stack on top, and none of them is waivable (`free-tool-pages.md` §4, §9):

8. **The tool works, verified by hand** — exercised on a running dev server with real inputs, output checked against the math done independently. Reading the code is not verification.
9. **Every state screenshotted** — default/pre-filled, valid result, empty submit, malformed input, boundary value, failure/timeout, kill-switch-off if present. Screenshots handed to the user. **No screenshot, no ship.**
10. **Ungated** — no email capture anywhere on the path to the result. (Exception: a tool where email *is* the deliverable, and even then the result renders on-page first.)
11. **Failure renders neutral** — a check that couldn't run never displays as a pass.
12. **Cost and abuse controls present** — for any tool with per-use vendor cost or outbound fetches: rate limit, spend/volume ceiling, kill switch, and public-host validation, all in the same commit as the tool.
13. **Index posture correct** — form page indexable; per-entity result pages `noindex, follow`; tool added to the `/tools` hub and the sitemap.
14. **Content half clears its own bar** — 600-1,200 words with a real methodology section, dated constants from the verified ledger, and the type-10 schema emitted.

A failing gate is information, not blame — it usually points at a thin section, a missing source, or a forgotten schema block. Fix the root cause; don't lower the bar.

---

## 4d. Programmatic pattern minimums

The gates above are written for a single piece. A programmatic page — `/alternatives/*`, `/for/*`, `/compare/*`, a long-form `/playbooks/*` — is verified against a fixed per-pattern spec instead, because the whole point of a pattern is that every page in it clears the same bar. These minimums are enforced mechanically by `scripts/link_audit.py` and `scripts/word_count.py`; nothing here is waivable, and a failing check means fix the page, not lower the number.

### Word floors

| Pattern | Floor |
|---|---|
| `/alternatives/[slug]` | ≥600 |
| `/for/[slug]` (use-case or audience) | ≥800 |
| `/compare/[slug]` | ≥700 |
| `/playbooks/[slug]` | ≥2,500 |

### Internal-link minimums

| Pattern | Outbound from this page | Inbound to this page |
|---|---|---|
| `/alternatives/[slug]` | ≥2 sibling `/alternatives/*`, ≥1 `/features/*`, ≥1 `/tools/*` (or stack equivalent) | ≥2 existing pages — commonly the homepage, sibling alts, related feature pages |
| `/for/[slug]` | ≥2 `/features/*`, ≥2 `/tools/*`, ≥1 sibling `/for/*` | ≥2 existing pages |
| `/compare/[slug]` | `/alternatives/[a]`, `/alternatives/[b]`, ≥1 relevant `/for/*`, `/pricing` | both `/alternatives/[a]` and `/alternatives/[b]` link here |
| `/playbooks/[slug]` | in body, not sidebar: ≥3 `/features/*`, ≥2 `/tools/*`, ≥2 `/for/*`, ≥1 `/alternatives/*` | ≥2 existing pages, commonly other playbooks plus a related `/for/*` |

**Every page must be reachable from ≥2 other pages, and at least one of those must be a frequently-crawled hub** (`crawl_hubs` in config). No orphans:

```bash
python scripts/link_audit.py --orphan-check
python scripts/link_audit.py --slug <slug> --pattern <A|B|C|D|E>
```

### Schema minimums

| Surface | Required JSON-LD |
|---|---|
| Homepage | `SoftwareApplication` (or `Product`), `Organization` |
| `/alternatives/[slug]` | `SoftwareApplication`, `BreadcrumbList`, `FAQPage` |
| `/for/[slug]` | `SoftwareApplication`, `BreadcrumbList`, `FAQPage` |
| `/compare/[slug]` | `BreadcrumbList`, `FAQPage` |
| `/playbooks/[slug]` | `Article`, `BreadcrumbList` |
| `/tools/[slug]` | `SoftwareApplication` or `WebApplication`, `BreadcrumbList` |

Validate on the rendered URL with `python scripts/tech_audit.py --schema <url>`, or at https://validator.schema.org/. A local parse proves the JSON-LD is well-formed; only URL inspection (`gsc.md` §3b) proves Google accepted it.

### Meta-tag requirements (every page)

- Unique `<title>`, 30-60 chars
- Unique `<meta name="description">`, 100-155 chars
- `<link rel="canonical">` set to the absolute URL — no query params, and no trailing slash if the site's convention is slashless
- `<meta property="og:type">`, `og:title`, `og:description`, `og:image`, `og:url`
- `<meta name="twitter:card">` (`summary_large_image` is standard)
- Exactly one `<h1>` per page

### Honesty section (alternatives pages only)

Verify presence visually. The section must have:

- An eyebrow + H2 labelling it (e.g. "Honest tradeoffs" / "Where [competitor] still wins")
- 3-4 rows, each with a feature/dimension and a 30+ word body
- Concrete: each row references a specific feature, not a vague "they're more polished"
- Honest: each row should be a real strength of the competitor, not a fake weakness in you

If the honesty section is missing or thin, the page fails the quality gate. Rewrite before shipping.

### Verification flow for a pattern page

1. `python scripts/word_count.py <output-path>` — meets the pattern minimum
2. `python scripts/link_audit.py --slug <slug> --pattern <A|B|C|D|E>` — passes
3. `python scripts/tech_audit.py --schema <url>` — validates, where the page is rendered
4. Verify the honesty section by eye (alternatives only)
5. Load the URL and view source: full server-rendered HTML, title + description + canonical present, JSON-LD blocks rendering
6. **Only after all of these pass**, update the roadmap row to `completed` and write the summary

---

## Degradation

- **No subagents** → run the critics as sequential clean-slate passes (review the draft fresh against each lens, hardest on yourself). The separation is conceptual: read as a critic trying to reject the piece, not as its author.
- **A deep-research skill installed** → useful for the skeptic/fact-check critic's independent cross-checks.
- **No browser/screenshot capability** → drive the tool by hand in a real browser and describe each state precisely, and say plainly in the hand-off that the visual verification was manual. Never claim a state works without having triggered it.
- **No way to render the page at all** → figures still ship (the SVG is correct or it isn't), but say plainly in the hand-off that they were **not** visually verified and name the two things the user should check: dark mode and mobile width.
- The gates run identically regardless of host — they're the floor.
