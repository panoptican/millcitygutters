---
name: seo
description: "The whole organic stack for a site or app: SEO, answer engines (AEO/GEO), programmatic pages, editorial content, free tools, technical health, claim accuracy, off-page briefs and distribution. Each run measures, ranks every action on one scale, does the best one. Run daily. Use for SEO, AEO, GEO, LLMO, organic traffic, rankings, Search Console, GSC, Bing, IndexNow, indexing, sitemap, robots.txt, llms.txt, AI crawlers, AI citations, AI visibility, 'what does ChatGPT say about us', keyword research, 'what should I publish next', guides, how-tos, listicles, comparisons, alternatives or /compare/ or /for/ pages, programmatic SEO, free tool for leads, striking distance, content decay or refresh, canonical, redirects, schema, JSON-LD, Core Web Vitals, site audit, technical SEO, internal links, orphan pages, backlinks, directories, outreach, competitor teardown, 'why don't we rank', 'we need traffic', or the next best SEO move."
metadata:
  version: 2.2.0
---

# SEO

One skill owns the whole organic stack: classic search, answer engines, programmatic pages, editorial content, free tools, technical health, product-claim accuracy, off-page briefs and distribution. Each run measures first, ranks every kind of action on one scale, does the single best one, verifies it, and writes down what it did and what it did not do. Run it again tomorrow and it picks the next-best thing. `/seo` is a daily operator, not a content quota.

Correcting what is already live (`correct`, `repair`, `refresh`, `consolidate`, `prune`, `verify-product`) is scored against creating something new, and usually wins. A run that ends in "nothing beats the bar today, here is what I measured" is a successful run.

## What matters most

Four things decide whether any of this works. Every run measures all four, every candidate is scored on which of them it moves, and the run record prints them as a vitals block so a month of records reads as a trend.

| Vital | Measured by | Acted on through |
|---|---|---|
| **Speed of the site** | `health_diff.py` records time to first byte and HTML weight per page every run; Lighthouse or PageSpeed on the top pages weekly. | `repair`: heavy pages, slow TTFB, render-blocking assets, image weight. A speed regression on a winning page outranks a new page. |
| **Relevance of keywords and topic** | Every page maps to a radar seed or coverage-map cluster; `answer_owner` and `intent owner` on every candidate; GSC wrong-query state. | `refresh` (retarget) or `prune`. A page off the site's topic is a cost, not a free lottery ticket. |
| **Click rate on Google** | Per-page CTR against the expected CTR at its position, from the saved Search Console pulls; the census flags `low-ctr`. | `refresh` of title and snippet first, because it is the cheapest lever on the site. Site CTR and the impressions-weighted gap are in every run record. |
| **Health of links** | `health_diff.py --check-links`: broken and redirecting internal links, orphans, inbound counts; `depth_check.py` for click depth; backlink spam score monthly. | `repair` for broken and redirecting links and orphans; `offpage-brief` for authority; never buy links. |

These are not four more rules. They are the lens the rubric's `strategic` axis scores against, and the reason `repair` and `refresh` can beat `create`.

## Modes

| Invocation | What happens |
|---|---|
| `/seo` | Daily run. Measure → select across all actions → execute one → verify → register. |
| `/seo measure` | Measure and write the run record. Select nothing. |
| `/seo fix <what>` | Force the fix lane on a named page, claim, or defect. |
| `/seo write [topic]` | Force one editorial piece. |
| `/seo sprint` | Force the programmatic lane, next roadmap phase. |
| `/seo tool [idea]` | Force a free-tool build. |
| `/seo aeo [snapshot\|audit\|plan\|fix]` | Force the answer-engine lane. `snapshot <domain>` needs no foundation. |
| `/seo tech` | Force a site-health pass: run the diff, repair the worst violation. |
| `/seo census` | Whole-inventory review. No create candidates. Execute the best prune, merge or refresh and write the portfolio trend. Runs itself once a month. |
| `/seo offpage` | Write the next outreach or directory brief. |
| `/seo distribute [url]` | Force the distribute lane on the newest undistributed piece, or the named URL. |
| `/seo needs-you` | Print the queue of decisions only the human can make, and nothing else. |
| `/seo setup` | Print what is connected and what each missing connection would unlock, in value order. Nothing else. |
| `/seo upgrade` | Detect the repo's state (fresh, legacy, partial, current), show the migration plan, apply it on confirmation. |

A forced mode still measures first (cheaply) and still registers. It just skips the cross-lane vote.

## The loop

Read the step reference when you reach it. Everything below the table is rules and routing; the mechanics live in `references/`.

| Step | Reference | Runs |
|---|---|---|
| 0. Foundation | `references/foundation.md` | Every run: `upgrade_state.py` (free when current). The interview only once. |
| 1. Measure | `references/measure.md` | Every run. Cheap panels always, paid panels on cadence. |
| 2. Select | `references/select.md` | Every run except forced modes. |
| 3. Execute | `references/lanes/<lane>.md` | The chosen lane. |
| 4. Verify | The lane's Gates section | Every run. Non-waivable. |
| 5. Register | `references/register.md` | Every run, including measure-only. |
| 6. Report | `references/register.md` §6 | Every run. The final message, written for a reader who has not opened a single file. |

### Step 0. Foundation

`.seo/` is the only state directory. Repos arrive in four states: fresh (nothing yet), legacy (state from earlier versions of this skill), partial (an older v2 layout), or current. `scripts/upgrade_state.py` detects which and, with `--apply`, moves, merges and fills without overwriting or duplicating anything, then stamps `config.version`. Run it first, every run; on a current repo it costs nothing. `references/foundation.md` then builds only what is still missing: config, brand and voice contract, the truth ledger, the attribute matrix, link inventory, keyword cache, content ledger, roadmap, radar seeds. Never overwrite a foundation file that exists.

The skill runs with whatever is connected. On the first run the foundation checkpoint, the one stop the skill makes, also shows what is connected and the top three missing connections with what each would unlock (`references/setup.md`), and asks whether to connect anything before continuing. The full report follows in the final message. After that it is one line per run until each item is declined.

### Step 1. Measure

The scoreboard comes before any decision. `references/measure.md` runs the panels, cheap ones every run and paid ones on cadence: Search Console states per page and index status; Bing as its own panel; the site health diff; the content census; the four vitals; the truth check and a claim re-verification sample; the answer-engine panel and AI referrals; the demand radar (communities, news, trends, video, on-site search); product changes in the repo; SERP features and AI Overview theft; internal link opportunities; branded vs non-branded; competitor delta; backlinks new and lost; seasonality; outcomes of past actions rolled into per-action priors; and debt from earlier runs.

Two hard gates come out of measurement. If the last three published pieces are not indexed, this run's job is fixing that, not writing a fourth. If the truth check reports a contradiction, no create action may win until it is corrected or explicitly deferred.

### Step 2. Select

`references/select.md` builds one candidate pool from every panel and every lane's generator, then ranks with one rubric. The action vocabulary:

| Action | Meaning | Lane |
|---|---|---|
| `correct` | A live page says something false or contradicts the truth ledger. | `lanes/fix.md` |
| `repair` | A live artifact is broken: redirect, lastmod, lang, link, orphan, schema, non-200, index regression. | `lanes/technical.md` |
| `refresh` | A page is winning or close and a rewrite, expansion or boost moves it. | `lanes/editorial.md` |
| `consolidate` | Two URLs compete for one intent. Merge and 301. | `lanes/fix.md` |
| `prune` | A page has been invisible for a quarter and earns nothing: remove it, 301 to the nearest owner or 410. | `lanes/fix.md` |
| `verify-product` | A capability, pricing or compliance claim has no dated source. | `lanes/fix.md` |
| `create-editorial` | One new guide, how-to, listicle, comparison, definition, data study, and so on. | `lanes/editorial.md` |
| `create-programmatic` | Ship or extend a pattern batch. | `lanes/programmatic.md` |
| `create-tool` | Build a free interactive tool and its page. | `lanes/tools.md` |
| `aeo-fix` | Reachability, extractability, entity clarity, accuracy at the cited source. | `lanes/aeo.md` |
| `offpage-brief` | A directory, mention or outreach brief. A human sends it. | `lanes/offpage.md` |
| `index-nudge` | A specific URL stuck unindexed. | `lanes/technical.md` |
| `distribute` | A fresh piece gets its first push: IndexNow for the one URL, social drafts held for approval, one third-party brief. | `lanes/distribute.md` |
| `measure-only` | Nothing beats the bar, or the run is a scheduled remeasure. | — |

Fixed overrides, in order, before any scoring: reachability and index regressions; truth contradictions and accuracy failures; repairs that cause user-facing harm (a wrong address, a wrong medical or legal statement, private data in analytics). Everything else ranks by expected movement divided by effort, with the site's own priors adjusting confidence (a refresh that has beaten the control seven times in nine scores like it), a seasonality bonus on topics that peak in the next eight weeks, and a saturation penalty so the skill does not write the same kind of thing every day. Two portfolio gates from the census sit above the rubric: while the site's invisible share is high, creates cannot win; and a content vein whose cohort went cold is closed to new pages until a refresh in it moves.

In an interactive session, present the top three with numbers and one question to the user. In an unattended run, take the top candidate, write the reasoning to the run record, and proceed. Anything that needs a human decision goes to `needs-you.md` rather than blocking, and is then asked in full in the final message (Step 6).

### Step 3. Execute

Open the lane and follow it. Lanes are self-contained: what routes there, what to read, the steps, the gates, and what to register. Do not read other lanes.

### Step 4. Verify

Every lane ends in gates. Deterministic checks run as scripts (`word_count.py`, `link_audit.py`, `crawl_check.py`, `health_diff.py`, `truth_check.py`). Judgment checks run as a critic panel. A gate that cannot be checked is reported as unchecked, never as passed. Cost never overrides a gate.

### Step 5. Register

`references/register.md` defines the ledger row, the run record at `.seo/runs/<date>.md`, and the `needs-you.md` queue. The run record always carries a "Not done" list. That list is the next run's debt and is how the daily loop remembers.

### Step 6. Report

The run record is for the next run. The final message is for the human, who will not open `.seo/`, the run record, or any other file to understand it. `references/register.md` §6 is the contract. In one line: every decision, question, or item the message mentions is stated in full where it is mentioned. An ID like `NY-3`, a file path, or "see the run record" is never a substitute for saying what the thing is.

The message has five parts, in this order: what was done and why it won; what was verified and what could not be; what was left undone that the next run inherits; the decisions waiting on the human, each written as a complete question with its options and a recommendation; and how the run ended (diff on the tree, commit, or PR).

## Cadence: running it many times a day

The skill is built to be run repeatedly, back to back, a dozen times a day if you like. Three things make that safe and cheap; each is enforced in the step it belongs to.

- **Panels have a freshness window** (`measure.md` §0). Search Console updates once a day with a lag, the live site does not change between two runs an hour apart, and the community sources do not either. Each panel reads its cached file if it is younger than its window and only re-pulls when it is stale. Run twelve, thirteen and fourteen of the day measure for free; only the action costs anything.
- **Targets have a cooldown** (`select.md` §5b). A page or claim acted on in the last 21 days is excluded from the pool unless a new tier-1 or tier-2 signal appears, because the live data cannot yet show whether the last action worked. Without this, run two would pick the same low-CTR page run one just rewrote, since the site still shows the old title.
- **Run records are keyed by time, not day** (`register.md`), and every run starts by reading the previous run's "Not done" and the state of the working tree. A dirty tree from an earlier run is continued or noted, never reverted.

**Parallel runs are not supported.** `.seo/` is a set of append-and-rewrite files and the working tree is shared; two runs editing the ledger or the same data file at once will lose one of them. Run them one after another. If parallelism ever matters, the shape is one worktree per run, a lock file on `.seo/`, and a merge step for the ledger; it is not built.

**The worktree loop is the intended way to run it repeatedly.** Open a fresh worktree from main, run `/seo`, open a PR, merge, repeat. It works because the whole state lives in `.seo/` inside the repo, so every run's ledger row, snapshots, radar signals and run record ride in the same PR as the change they describe, and the next worktree inherits them the moment the PR merges. Three consequences:

- **One run, one PR, one change.** The PR body is the run record. Reviewing the PR is reviewing the decision.
- **Merge before the next run.** Cooldown, freshness windows and debt are read from `.seo/` on main; a run started before the previous PR merged cannot see what that run did. The start-of-run guard in `register.md` fetches main and refuses to proceed if main carries a newer run record than the worktree.
- **The dataset grows by about half a megabyte a day.** `scripts/compact_state.py` thins snapshots older than 30 days to weekly and older than six months to monthly. The register step runs it on the first run of each month; the census keeps working on whatever files remain.

`config.git.mode` decides how a run ends: `none` (show the diff, the default outside a worktree loop), `commit` (commit on the current branch, never push), or `pr` (commit, push the branch, open a pull request against main with the run record as the body, never merge). Merging is always yours; on this repo merging is deploying.

## Rules

Each one was learned by breaking it.

**Publishing and contact**
- Never merge, publish, or deploy. Committing and opening a PR happen only when `config.git.mode` says so; merging is always a human's. On repos where main deploys, a merge is a deploy.
- Never contact anyone. Write briefs and punch lists. A human sends them.
- Never manufacture consensus: no astroturfing, incentivized reviews, sockpuppets, or bot-only content.
- Never serve engines different content than humans. Cloaking is the one shortcut that gets a domain removed.
- Never distribute by posting. Social posts exist only after the human approves them inside the posting skill; every directory, thread or outreach push is a brief.

**Money**
- Never spend without a preflight. State the exact call count and cost shape. Interactive: stop for approval. Unattended: stay under `config.budget.per_run_usd` and record what was skipped.
- Never buy the same fact twice. Market data is cached in `.seo/keyword-research.json` for 30 days. Where DataForSEO and Search Console overlap on your own domain, Search Console is ground truth.
- Live SERP reads (Recipe G) are never cached and never skipped.
- Cost never overrides a gate.

**Measurement**
- Never report a rate from one sample. Answer engines are non-deterministic. Sample size travels with every number.
- Never ask a leading prompt. Measure the question a buyer would ask.
- `web_search: true` always, or you are measuring training data.
- Never claim causation from one correlation.
- The Search Console query table covers a minority of clicks. Classify by page. A missing query is not absent demand.
- Google, Bing, and answer-engine numbers are separate panels. Never sum them.
- Never score confidence from memory when `priors.json` exists; the site has already said how often each action works here.
- Never judge only the pages the ledger remembers. The census reads the sitemap, so every public URL is judged on the same evidence.

**Content**
- If you cannot state the information gain in one concrete sentence, do not write the piece.
- Alternatives pages ship with three honest tradeoffs where the competitor wins.
- Every page is reachable from at least two other pages, one of them a frequently crawled hub.
- Touching a page bumps its `date_modified`. Sitemap `lastmod` is a content date or omitted, never a build date.
- Don't gate a free tool behind an email. No screenshot, no ship.
- Never render "couldn't check" as "clean."
- A page that does not map to a radar seed or a coverage-map cluster is off-topic. It is a `prune` or `consolidate` candidate, never a reason to widen the topic map.
- Every `create-*` candidate carries demand evidence: a Search Console row or a dated thread where someone asked the question. No provenance, no create.
- Removing a page is worth as much as adding one. A page nobody has seen in a quarter is a cost to the domain, and the census scores its removal on the same scale as a new piece. Never prune a page with backlinks, a legal reason to exist, or a hub role without merging it first.
- One canonical owner URL per intent. A second page for an intent that already has an owner is a `refresh` or a `consolidate`, never a create.
- Never self-author `AggregateRating` or review schema on your own product or comparison pages. Never pay for directory listings or buy links.
- Never write a piece out of habit when the health diff or truth check surfaced a defect on a live page. Defects on pages that already rank outrank new pages.
- Never let a daily cadence become a daily article. The cadence is for measurement; the article is earned.
- Never copy a competitor's new page because the delta panel showed it. The panel says where demand moved; information gain decides whether we write.
- Never chase page count. It is almost never the gap.
- Never ship content-ops artifacts: a placeholder heading, an internal label, a positioning note. Add a truth-check rule the first time one does.

**Privacy**
- Nothing in acquisition analytics may carry private identifiers: record IDs, private slugs, tokens, filenames, diagnoses. No session replay on private routes.
- First-party data in content is aggregate only, n ≥ 50, never derived from the contents of users' private records.

**Foundation**
- Never overwrite a foundation file, and never keep two files for one purpose: migration moves and appends, it does not regenerate. Never refuse for a missing tool: degrade, label the degradation in the run record, continue.
- Never build a second tracker, ledger or scoreboard beside `.seo/`. There is one state directory.
- Never read the whole ledger, the whole roadmap and every reference at the start of a run. Read the step you are on.

## Tools and environment

All optional. The skill degrades and labels the degradation.

The skill is host-agnostic. `references/tools.md` is the capability registry: what each panel and lane needs, the vendor and endpoint names the references use, and the fallback when it is missing. In short:

| Need | Preferred | Fallback |
|---|---|---|
| Own-site search truth | Search Console | Paste an export |
| Bing | Bing Webmaster API key in env (`config.bing.api_key_env`) | Skip the panel |
| Market data, SERP, backlinks, AI mentions, trends | DataForSEO | `references/research-recipes.md` "No keyword tool" |
| Answer-engine responses | DataForSEO `ai_optimization_llm_response` | Host model with web search, labeled as such |
| Site crawl, rank tracking, GA4 outcomes, on-site search | OpenSEO | `scripts/crawl_check.py`, `scripts/health_diff.py`; outcomes "not connected," never zero |
| Community demand | A community-search skill, if installed | `site:` web searches |
| Social drafts | A social posting skill, if installed (approval-gated) | A social brief in `needs-you.md` |
| Product changes | `git log` via `scripts/repo_changes.py` | Skip when not a git repo |
| Rendering check | The host's headless browser | `curl` + a note that JS was not rendered |
| Page content | The host's page fetch | `curl` |

## File map

```
seo/
├── SKILL.md
├── references/
│   ├── tools.md · setup.md · foundation.md · measure.md · select.md · register.md   the loop, in step order
│   ├── demand-radar.md · census.md · gsc.md · research-recipes.md         panels and data recipes
│   ├── lanes/       editorial, programmatic, tools, aeo, technical, fix, offpage, distribute
│   ├── aeo/         prompt-sets, audit, diagnose, measurement, technical, onpage, offpage, platform-notes
│   ├── patterns/    alternatives, use-case, compare      stacks/   detection, app-db, rails-inertia, nextjs, astro
│   ├── opportunity-research.md · content-types.md · research-brief.md · writing.md · visuals.md
│   ├── quality-loop.md · polish-pass.md · ai-writing-detection.md · proprietary-data.md
│   ├── content-stores.md · output-formats.md · free-tool-pages.md · pseo-playbooks.md · schema-examples.md
│   └── methodology.md · history.md
├── scripts/         standard-library Python, every one a report that exits 0
│   ├── measure:     health_diff.py  census.py  truth_check.py  outcomes.py  repo_changes.py  serp_features.py
│   │                link_opportunities.py  brand_split.py  competitor_diff.py  backlink_diff.py  seasonality.py
│   ├── aeo:         score.py  crawl_check.py  robots_check.py  depth_check.py  log_parse.py  agents.py
│   ├── gates:       word_count.py  link_audit.py  tech_audit.py  sitemap.py
│   └── state:       upgrade_state.py  compact_state.py
└── assets/          templates for every .seo/ file
```

State in the repo:

```
.seo/
  config.json  brand.md  truth.md  truth-checks.json  attributes.md
  keyword-research.json  backlink-targets.json  link-inventory.md
  content-ledger.md  roadmap.md  needs-you.md  radar.md
  outcomes.json  priors.json  seasonality.json
  census.md  briefs/  evidence/  health/  gsc/  census/  runs/
  competitors/<host>/  serp/  backlinks/
  aeo/  prompts.json scoreboard.md findings.md gameplan.md report.md
       battlecard.md mentions.md worklog.md runs/<date>/
```
