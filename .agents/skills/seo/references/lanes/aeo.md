# Lane: aeo

<!-- sources: aeo/SKILL.md Phases 1-5 + modes + checkpoints · aeo/references/content-patterns.md §9 (objection reframe, ported) · aeo/references/onpage.md Q2 (placement rule, ported) -->

Owns brand presence **inside generated answers** — what ChatGPT, Claude, Perplexity, Gemini, Google AI Overviews and Copilot say about us, why they say it, and the on-page and technical work that changes it.

The unit of work is not a page and not a keyword. It is an **attribute**: one specific thing we want to be known for, in the words buyers actually use. Every run in this lane moves attributes from where they are to where we want them.

Answer engines do not return a menu. They return a verdict. Ranking makes you eligible for that verdict; this lane decides whether you are in it and what it says.

---

## Cost shape — read this before anything else

This lane has two halves with completely different economics, and conflating them is how a daily run burns a month of budget in a week.

**The AI answer panel — Phase 2 Stream A, the prompt runs — is the expensive half.** It runs only on the `config.budget.ai_panel_cadence_days` cadence, or on an explicit `/seo aeo` invocation. **Never on a plain daily run.** Answer engines move slowly; daily readings are noise dressed as data, and they cost real money to collect.

**The snapshot scripts are free and can run any day.** `robots_check.py`, `crawl_check.py`, `depth_check.py` and `log_parse.py` cost nothing, need no repo state beyond a URL list, and catch the failure that silently zeroes everything else — a `robots.txt` line added years ago by someone being protective. Run them in the daily measure step.

Say what a snapshot is not: it measures whether engines can reach and extract our pages. It does **not** measure what any engine says about us, because it runs no prompts. A site can pass every check and still be absent from every answer. Label the output *technical readiness* and never let it stand in for a panel run.

---

## Routes here

| Action | Candidate record carries |
|---|---|
| `aeo-fix` | The finding id · the attribute it belongs to · which pipeline gate failed (reachable / cited / quoted) · the routing-matrix cell (discovery × capability) · the route it implies (technical · on-page comprehension · off-page trust · defend · fix-at-source) · the exact page or file, and the claim to add |

Two `aeo-fix` sources arrive with a click number attached, from `serp_features.py` (measure.md §3d), and they are the ones most worth taking on a daily run because they need no panel spend: `aio-uncited` (a Google AI Overview answers one of our earning queries and cites other domains; the fix is on-page comprehension and extractability on our owner page, `aeo/onpage.md`, with the cited domains as the bar) and `theft` (a feature appeared and the clicks left while the position held; the fix is usually the lead answer and a structured block the feature can lift, or a defend note when the feature is a video carousel we cannot fill). Both carry `movement` = clicks at risk and re-measure from the next weekly SERP read, not from the AI panel.

An `aeo-fix` whose route is **off-page trust** does not execute here — it becomes an `offpage-brief` (`lanes/offpage.md`). An `aeo-fix` whose route is **fix at the source** and whose error traces to a wrong claim on our own site is a `correct` (`lanes/fix.md`); this lane hands it over with the citation evidence attached. An `aeo-fix` whose route is **technical reachability** executes in `lanes/technical.md` unless it is AI-crawler-specific (`robots.txt` per AI agent, `llms.txt`, render-shell), which stays here.

---

## Read first

In order. Skip where noted.

1. `.seo/attributes.md` — the attribute matrix with priorities. Never skip; everything downstream inherits it. If it doesn't exist, this lane can't run — foundation owns building it (`references/foundation.md`).
2. `.seo/truth.md` — every fact-check prompt is scored against it. Never skip.
3. `.seo/brand.md` — the positioning sentence and the "not for" clause, which is what makes objection work believable.
4. `references/aeo/diagnose.md` — the three pipeline gates and the **Discovery × Capability routing matrix**. Never skip: getting the route wrong is how teams spend six weeks writing content to fix a problem content cannot fix.
5. `references/aeo/technical.md` — AI user agents, `llms.txt`, the rendering check, schema, freshness, the extractability rubric (§7), entity clarity. Read for any technical or extractability finding.
6. `references/aeo/onpage.md` — the extraction rewrite, placement, objection content, accuracy failures. Read for any comprehension finding.
7. `references/aeo/prompt-sets.md` — the six prompt types, portfolio construction, the QA pass. Read only when building or revising the prompt set (Phase 1).
8. `references/aeo/audit.md` — the four measurement streams, sampling plan, storage layout. Read only on a panel run.
9. `references/aeo/measurement.md` — metric definitions and the **margin-of-error table** that says whether a run-over-run change is real. Read before reporting any movement.
10. `references/aeo/platform-notes.md` — how each engine selects and cites. Read when a finding is platform-specific and you're about to conclude something from divergence.
11. `references/aeo/offpage.md` — read when producing the battlecard or a mention brief.
12. `references/writing.md` + `references/aeo/intent-buckets.md` — the block patterns and answer-intent shapes any new or rewritten copy must take.

---

## Steps

### Phase 1 — Prompt set (once, then quarterly)

Attributes become prompts. Prompts are the instrument, and a badly built instrument produces clean-looking garbage.

Six types, six jobs, each with a pass criterion — **Discovery** ("Best X for Y?" → a list of brand names), **Head-to-head** (→ a verdict, not a hedge), **Capability** ("Does [brand] do X?" → yes or no), **Fact check** (→ a checkable claim), **Perception** (→ an opinion with themes), **Category framing** (→ buying criteria, no brands). A prompt that fails its own criterion is not data.

**Discovery plus Capability is the diagnostic pair.** Running one without the other is why most AEO work routes to the wrong fix; their cross-product is the routing matrix.

**Build a portfolio, not a prompt.** Swapping only the category label in an otherwise identical question moves mention rates by tens of points, because the label selects a different slice of the web. For every priority-1 attribute generate 5–8 discovery variants across: category-label synonyms (the team's term and the buyer's term), persona/segment/use-case, "best"/"top"/"recommended"/"what should I use", product-seeking vs job-to-be-done framing, and one hard constraint (budget, company size, integration, vertical, region). Read the **rolled-up attribute number**, not individual prompts.

QA every prompt before it enters the set. Write `.seo/aeo/prompts.json`. Full method: `references/aeo/prompt-sets.md`.

### Phase 2 — Measure (panel run: on cadence or explicit invocation only)

Four independent streams, run in parallel where subagents exist, sequentially otherwise. Same coverage either way. Full method in `references/aeo/audit.md`.

- **Stream A — what the engines say.** Run the prompt set across reachable platforms at the sample size the priority tier calls for. Capture full response text, cited URLs, brands mentioned. Store raw under `.seo/aeo/runs/<date>/` — raw text is the asset; it's what you re-read when a number surprises you and what makes the next run comparable. **This is the paid half.**
- **Stream B — the citation supply chain.** Which domains and pages feed answers in the category, which of ours get cited, and where competitors are cited and we are not. That last set is the off-page target list, generated from data instead of guessed.
- **Stream C — the site itself.** Free, any day: `robots.txt` per AI user agent, `llms.txt`, server-rendered body vs a JavaScript shell, status and redirect chains, canonical, schema, freshness, per-page extractability.
  ```bash
  python3 scripts/robots_check.py --url https://<domain> --out .seo/aeo/runs/<date>/robots.json
  python3 scripts/crawl_check.py  --urls <file>            --out .seo/aeo/runs/<date>/crawl.json
  python3 scripts/depth_check.py  --url https://<domain>
  ```
- **Stream D — crawl and traffic.** AI crawler hits from server or CDN logs joined to citations, AI referral traffic by landing page, Search Console index state.
  ```bash
  python3 scripts/log_parse.py --logs <path> --out .seo/aeo/runs/<date>/logs.json
  ```

Then roll up: `python3 scripts/score.py --run .seo/aeo/runs/<date> --prev .seo/aeo/runs/<prior> --out .seo/aeo/scoreboard.md`.

**Two numbers per attribute per platform, both carrying n.** *Mention rate* — responses naming us over responses sampled, printed as `42/60 (70%)`. *Rank* — our position when brands are sorted by mention count, plus share of voice. Read them together: high rank with low mention rate means the engines haven't settled the category yet, the cheapest thing to move. High on both means defend. Low rank with high mention rate means buying authority, slowly.

**Model agreement is a confidence signal, not an optimization target.** Divergence means the evidence base is mixed, which means the attribute is still winnable. Don't build platform-specific tactics on divergence you can't explain.

**Spend preflight before the first paid call** — see Checkpoints.

### Phase 3 — Diagnose

Full method in `references/aeo/diagnose.md`.

**The pipeline.** A page contributes to an answer only if it clears three gates in order, and each failure has a different fix: **Reachable** (can the engine fetch and read it — fix this first, nothing downstream matters) → **Cited** (does the engine pick it — credibility or relevance) → **Quoted** (does the engine lift a claim from it — structure; the claim isn't self-contained enough to survive extraction). String-match the page's core claims against stored response text: a page crawled and cited but never quoted is being used as a footnote instead of a source.

**The routing matrix** — cross discovery against capability for every priority-1 and -2 attribute. Preserved in full in `references/aeo/diagnose.md`; the two rows that override everything are *facts wrong* → fix at the source (highest priority regardless of rank: a confident wrong answer costs more than absence) and *not reachable* → fix reachability first (everything else is wasted until it clears).

**Three outputs, always all three** — opportunities (ranked by priority × distance, each carrying its route), objections (recurring negative themes, tagged broad vs attribute-specific and true vs false), and strengths (never ship only problems; strengths tell you what to defend and often reveal the market values something the positioning underweights). Write `.seo/aeo/findings.md`.

### Phase 4 — Gameplan

Findings become an ordered list of things a person can do on a Tuesday. Order by **expected movement ÷ effort**, with two hard overrides on top: anything failing the Reachable gate first, any accuracy failure second. Both are cheap and both invalidate work done above them.

Every item carries the action, the finding it closes, the route, the effort, the expected effect, and the exact location. **An item you cannot write a location for is not ready to be an item.** Write `.seo/aeo/gameplan.md` from `assets/gameplan.template.md`, grouped Now / Next / Later / Done, with Done carrying ship date and observed effect.

### Phase 5 — Execute

**On-page and technical.** Real work in the repo per `references/aeo/onpage.md` and `references/aeo/technical.md`: fix crawl blocks, add missing schema, restructure a page so its claim survives extraction, write the FAQ from questions the prompts actually revealed, create the missing page.

The extraction rewrite, in order: a self-contained 40–80 word answer immediately after the H1 that makes sense quoted alone with no pronouns pointing at the heading · H2s rewritten as the questions people ask, each answered in the first sentence beneath it · every topic sentence able to survive being quoted with nothing around it · every number attributed and dated inline · any fact living only in a screenshot or chart also present as text · the schema the page type calls for, matching visible content · a visible date.

**Placement rule — add the claim to already-cited pages first.** An association strong enough to change an answer comes from a claim appearing in several credible contexts across the site, not from one dedicated page. Once the dedicated page exists, reinforce it in this order:

1. **Pages already appearing in our citations.** Highest-leverage placement there is — the engine already reads and trusts that page, so the claim inherits credibility we'd otherwise spend months building. Stream B gives the list.
2. **Our most-cited pages generally**, even where the attribute is only adjacent. Citation volume is a reasonable proxy for how much an engine weights a page.
3. **The definitional pages** — homepage, pricing, about, comparison pages. Heavy crawl attention, and where engines look for what a company fundamentally is. A claim absent from all four reads as peripheral no matter how many blog posts carry it.

The test for a woven-in claim: **would a human editor who knows nothing about this program find the sentence strange?** If yes, it's forced, and forced additions don't perform.

**Objection reframe — the block pattern.** The rule is *reframe, do not defend*. A page opening with "we do not have a steep learning curve" restates the objection in our own voice, on our own domain, in an extractable position — we've just made ourselves the citable source for it.

```markdown
## [The real question behind the objection]

[Direct, honest answer to the underlying concern, stated without repeating the
objection's framing.]

[Specific evidence: a number, a timeline, a named example.]

[Where it genuinely does not fit, stated plainly.]
```

Never restate the objection in your own voice on your own domain in an extractable position.

| Fails | Works |
|---|---|
| "## Is [Product] hard to learn?" | "## How long until a team is productive on [Product]?" |
| "We do not have a steep learning curve." | "Most teams run their first workflow within an hour of signing up." |
| "[Product] is not expensive." | "[Product] starts at $X. Teams typically replace [N] tools with it, which is where the math works." |

The final line, naming where we do not fit, is what makes the rest believable, and it answers the "not for" clause in `.seo/brand.md`. **Some objections should be owned rather than countered** — if we're genuinely the expensive option, make clear what the money buys. Denying something third-party sources confirm reads as evasion and makes the objection stickier.

**Off-page** produces assets and stops — hand to `lanes/offpage.md`.

---

## Checkpoints

Three, and none of them can be guessed. Use a question to the user; in unattended mode, take the documented default and write the decision into the run record.

| Checkpoint | Phase | Why it can't be guessed |
|---|---|---|
| **Identity and attributes** | 0 (foundation) | Everything downstream inherits it. A wrong attribute list produces a perfectly measured answer to the wrong question. |
| **Spend preflight** | 2 | The user pays per call. Show the arithmetic first: *"Priority 1: 3 attributes, 6 variants, 4 platforms, n=3 = 216 calls. Priority 2: 5 attributes, 3 variants, 2 platforms, n=2 = 60 calls. Total 276 calls at roughly $X. Proceed, trim, or change the tiering?"* Unattended: stay under `config.budget.per_run_usd` and trim the priority-3 tier first. |
| **Gameplan approval** | 4 → 5 | Which items to execute now is a resourcing call, not a data call. Unattended default: execute the top Now item only; everything else stays in the gameplan. |

Everywhere else, decide and move. Never ask permission to run a free check.

Default sampling: priority 1 gets the full portfolio on every reachable platform at n=3; priority 2 gets 3 variants on 2 platforms at n=2; priority 3 gets one prompt, one platform, n=1, and is labelled **indicative** everywhere it appears.

---

## Gates

Non-waivable. Cost never overrides a gate.

1. **Never report a rate from one sample.** Sample size travels with every number printed. Check a run-over-run change against the margin-of-error table in `references/aeo/measurement.md` before calling it movement.
2. **Never ask a leading prompt.** "Which tools are best, like [Brand]?" produces a worthless number. Measure the question a buyer would ask.
3. **Never claim causation from one correlation.** A page update followed by a rate rise is a hypothesis. Log the input and let the next run test it.
4. **Never present a degraded run as a full one.** If a platform was unreachable or a tool was missing, the method section says so.
5. **Never fabricate a source, a statistic or a quote.** Print `unknown` and say what would resolve it.
6. **Never serve engines different content than humans.** Cloaking is the one technical shortcut here that can get a domain removed outright.
7. **Every shipped claim is stated in `.seo/truth.md` language**, so the several places it appears corroborate rather than compete.
8. **Server-rendered body still contains the new claim** after the edit. A framework change can silently move content behind hydration.
9. **Re-run `scripts/crawl_check.py` on every page touched** and confirm the extractability score actually moved.
10. **Schema present and matching visible content**; visible date; accurate `dateModified`.
11. **No FAQ walls.** Build the FAQ from questions that actually appeared in prompt responses, support tickets or docs search. Invented questions answered for a crawler are the current form of keyword stuffing.
12. **The two AI bot classes are not confused.** Blocking a training crawler is a legitimate business decision; blocking an answer-time retrieval crawler removes us from that engine's answers. Verify current agent names against the operator's own published documentation, not a hardcoded list.

---

## Register

- `.seo/aeo/scoreboard.md` — the run appended as a new dated column, so the history reads in one table. Panel runs only.
- `.seo/aeo/findings.md` — every finding with its id, evidence and route.
- `.seo/aeo/gameplan.md` — Now / Next / Later / Done, with items moved to Done carrying ship date and observed effect.
- `.seo/aeo/report.md` — the dated durable artifact, with an explicit method section saying what was measured, at what sample size, and what was not.
- `.seo/aeo/worklog.md` — every shipped input, dated, with its finding id and a recheck date. Without the input record, a later rate change is a number with no explanation.
- `.seo/aeo/runs/<date>/` — raw responses, citations and crawl output. Never summarize away the raw.
- `.seo/content-ledger.md` — an `aeo-fix` row for each page touched (date · finding id · route · page · the claim added).
- `.seo/runs/<date>.md` — whether the panel ran or only the free snapshot, the cadence decision and why, the gate results, the cost, and **what was not done**.
- `.seo/needs-you.md` — gameplan items routed off-page · anything needing a platform login · the recheck date for this run's inputs.
