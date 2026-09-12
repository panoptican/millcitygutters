# Step 1. Measure

<!-- new in v2; GSC mechanics live in gsc.md, answer-engine mechanics in aeo/audit.md and aeo/measurement.md -->

Measurement is what makes the daily run safe to automate. A run that measures nothing can only repeat yesterday's habit. A run that measures everything cheap, and the expensive things on a cadence, can notice that a page it shipped last month now contradicts the pricing page, that a redirect broke, that a guide fell from position 6 to 14, or that an engine started citing a competitor for the brand's own attribute. Every panel below writes to the run record and feeds a candidate into Step 2.

Read `config.json` once. Then run the panels in the order given. Cheap panels always run. Paid panels run when their cadence is due or the mode forces them.

## Contents

0. Freshness windows
1. Own-site search truth (Search Console)
2. Bing panel
3. Site health diff
3b. Content census
3c. Site vitals: speed, click rate, link health
3d. SERP features and AI Overview theft (weekly)
3e. Internal link opportunities (weekly)
3f. Branded vs non-branded (every run)
4. Truth check
4b. Product changes since the last run (every run)
5. Claim re-verification sample
6. Answer-engine panel (cadenced)
6b. AI referral attribution
6c. Demand radar
6d. Competitor delta (weekly, monthly)
6e. Backlinks new and lost (weekly)
6f. Seasonality (monthly)
7. Debt: not-done lists and the needs-you queue
7b. Outcomes of past actions (every run)
8. Gates that come out of measurement
9. What the panel summary looks like

## 0. Freshness windows

Every panel writes a dated file and reads it back before pulling again. This is what makes a dozen runs a day cost the same as one. Windows are in `config.cadence` and default to:

| Panel | Cache file | Window | Why |
|---|---|---|---|
| Search Console pull | `.seo/gsc/<date>.json` | 20 h | Google refreshes once a day, two to three days behind. Two pulls in one day return identical rows. |
| URL inspection | inside the run record | 20 h per URL | Same source, same lag. |
| Health diff | `.seo/health/<date>.json` | 6 h | The site changes on deploy, not on the hour; 217 fetches an hour against production is rude for no information. Force with `/seo tech`. |
| Link check | same file | 20 h | Expensive half of the health diff. |
| Census | `.seo/census/<date>.json` | recompute when either input is newer | It is a join; it costs nothing. |
| Truth check | none | every run | Reads the repo, which the previous run may have changed. |
| Claim re-verification | brief `last_verified` stamps | every run, different sample | The sample rotates, so repeated runs cover more claims. |
| Radar, free tier | `.seo/radar.md` | 20 h per seed | Threads do not appear by the hour. |
| Radar, paid tier | `.seo/radar.md` | `config.radar.cadence_days` | Costs money. |
| AI panel | `.seo/aeo/scoreboard.md` | `config.budget.ai_panel_cadence_days` | Costs real money. |
| Bing | `.seo/gsc/bing-<date>.json` | 20 h | Same shape as Google. |
| Query pull | `.seo/gsc/queries-<date>.json` | 20 h | Same source as the page pull, one extra call. Feeds the brand split, link opportunities, SERP features and the competitor diff. |
| Outcomes | `.seo/outcomes.json` | 20 h | A join over the saved pulls; recompute when a pull is newer. |
| SERP features | `.seo/serp/<date>.json` | 168 h | Paid, and features do not move by the hour. |
| Link opportunities | run record | 168 h | Fetches the site; nothing changes until pages do. |
| Product changes | none | every run | Reads git. Free. |
| Competitor delta | `.seo/competitors/<host>/` | 168 h fingerprint, 720 h ranked keywords | The fingerprint is free; ranked keywords is one paid call per competitor. |
| Backlinks | `.seo/backlinks/<date>.json` | 168 h | Paid; new and lost links land weekly at the source anyway. |
| Seasonality | `.seo/seasonality.json` | 720 h | Monthly volume history changes monthly. |
| On-site search | `.seo/radar.md` | 168 h | Free with GA4, and the signals are slow. |
| Debt | run records | every run | Cheap, and it is what links one run to the next. |

A run inside every window is a legitimate run: it reads the cached panels, re-reads debt and the truth check, and goes straight to select. Say so in the run record ("panels cached from 09:14"). Never pretend a cached panel was pulled fresh.

## 1. Own-site search truth

Follow `gsc.md` §2 ("Measure what shipped"). One `get_advanced_search_analytics` pull with `dimensions: "page"` for the last 28 days and the 28 before, joined to the ledger's shipped rows. Classify every shipped page:

| State | Definition | Feeds candidate |
|---|---|---|
| winning | clicks up, position ≤ 10 | none (defend) |
| close | position 5–20 with impressions | `refresh` (striking distance) |
| wrong-query | impressions on queries the page did not target | `refresh` (retarget) or `create-editorial` (split) |
| invisible | indexed, near-zero impressions after 21+ days | `consolidate` or `refresh` |
| converting-nothing | traffic but no activation event (signup, tool run, download), when GA4 is connected | `refresh` (intent mismatch) |
| decaying | clicks down ≥ 30% over two windows | `refresh` |
| unindexed | not in index after 3+ days | `index-nudge` |

For unindexed pages, record which bucket URL inspection puts them in. The buckets have different causes and different fixes, and "discovered, currently not indexed" is mostly Google declining to spend a fetch on a URL with no predicted demand, not a crawl-budget problem:

| Inspection says | Cause to suspect | Lane |
|---|---|---|
| URL is unknown to Google | discovery: sitemap, internal links, IndexNow | technical |
| Discovered, currently not indexed | demand: the page targets a query nobody asks | fix (retarget or consolidate) |
| Crawled, currently not indexed | quality or duplication | editorial (refresh) or fix (consolidate) |
| Indexed, no impressions after 21 days | intent mismatch | editorial (refresh) |
| Impressions, no clicks | title and snippet | editorial (boost) |
| Clicks, no activation | page or product fit | editorial, and a needs-you if the product is the gap |

Save the raw page pull to `.seo/gsc/<date>.json` (site, window, rows with page, clicks, impressions, ctr, position) before doing anything else with it. Make one more call with `dimensions: "query,page"` over the same window and save it as `.seo/gsc/queries-<date>.json` (`gsc.md` §1g); the brand split, link opportunities, SERP features and competitor diff all read that file, and it is the only copy of the query table the dataset keeps. Search Console keeps 16 months; the census needs longer, and the saved pull is the only copy. Run `batch_url_inspection` on every page shipped in the last 30 days and any page whose state moved. The query table is supplementary. It covers a minority of clicks (12% on one audited site), so a missing query is not evidence of missing demand.

Write the per-page state table to the run record. Write the two-window totals as a single line, not a paragraph.

## 2. Bing panel

Only if `config.bing.api_key_env` names a variable that is set. Bing Webmaster's API exposes query and page stats; its AI Performance report (citations, grounding queries) is UI-only, so record it in `needs-you.md` as a periodic manual read rather than pretending to have it. On one site Bing produced more clicks over three months than Google in the last month, and its AI report named the grounding queries. Ignoring it means ignoring Copilot.

Record Bing as its own panel. Never add its numbers to Google's.

## 3. Site health diff

Run:

```
python3 <skill>/scripts/health_diff.py --sitemap <config.site.sitemap_url> --out .seo/health --base-url <config.site.domain> --keep-text
```

`--keep-text` stores each page's visible text in the fingerprint so the truth check (§4) can run over the rendered site. It costs disk, not time; drop it only on a site with thousands of pages, and then run it weekly.

It fingerprints every sitemap URL (status, canonical, title, description, lang, h1 count, JSON-LD types, lastmod, body words, content hash) and diffs against the previous fingerprint. It runs in a minute or two on a few hundred URLs and costs nothing, so run it daily (or every `config.budget.health_diff_cadence_days` if the sitemap is large enough that daily is unkind). Its output feeds two things:

- Rule violations become `repair` candidates. Non-200 in sitemap, a sitemap URL that redirects, canonical mismatch, missing `lang`, duplicate titles, a build-date lastmod smell (most URLs sharing one date), noindex in sitemap, h1 count not one, missing schema on pages that should have it.
- Content-hash changes on pages this skill did not touch are a prompt to look. Someone edited the page, or a template changed underneath it. Note them; they are not automatically candidates.

If the sitemap is unreachable, record the panel as unchecked. Do not skip silently.

## 3b. Content census

Once the health fingerprint and the Search Console pull exist, join them:

```
python3 <skill>/scripts/census.py --health .seo/health/<latest>.json --gsc .seo/gsc/<latest>.json --gsc-prev .seo/gsc/<prior>.json --ledger .seo/content-ledger.md --out .seo/census
```

Every public URL gets a verdict (keep, refresh, merge-candidate, prune-candidate, invisible, watch, broken) and the site gets portfolio numbers: invisible share, thin share, click concentration, and a `create_gate` flag. `census.md` explains the verdicts, the gates, and why this panel is the one that keeps the skill honest. Verdicts feed `prune`, `consolidate`, `refresh` and `repair` candidates; `create_gate` and cold veins are enforced in `select.md`.

## 3c. Site vitals: speed, click rate, link health

The census and the health diff carry these, but they are important enough to read on their own every run and print as a block.

- **Speed.** `health_diff.py` records `ttfb_ms` and `html_bytes` per page on every run and flags `slow-ttfb` (over a second on two consecutive runs) and `heavy-html`. Weekly, or when a winning page slows, run Lighthouse on the top ten pages by clicks: `on_page_lighthouse` when available, else the PageSpeed Insights API with a key in `config.speed.psi_api_key_env`, else a local `lighthouse` CLI. Record LCP, INP, CLS per page in `.seo/health/lighthouse-<date>.json`. Thresholds: LCP under 2.5 s, INP under 200 ms, CLS under 0.1. A 429 or a missing tool is recorded as unchecked, never as a pass.
- **Click rate.** From the saved Search Console pull: per-page CTR against the expected CTR at its position (the table in `gsc.md`), the site CTR, and the impressions-weighted gap. `census.py` computes these and flags `low-ctr` pages. Read the top ten low-CTR pages by impressions every run; they are the cheapest wins on the site.
- **Link health.** `health_diff.py --check-links` on `config.budget.link_check_cadence_days` (default 7, daily is fine on a small site): broken and redirecting internal links per page, orphan pages, inbound link counts. `depth_check.py --url <home>` for click depth. Monthly: `backlinks_summary` and `backlinks_bulk_spam_score` for the domain, so a toxic-link spike is seen the month it happens.
- **Relevance** has no script. It is judged in select through `answer_owner`, `intent owner`, and the `topic` field, and in the census through the coverage map. Print the count of pages that map to no seed or cluster.

## 3d. SERP features and AI Overview theft

Weekly (`config.cadence.serp_hours`). The signature of an AI Overview or a SERP feature taking a query's clicks is position stable, clicks down. Search Console cannot see the feature; only a SERP read can.

1. `python3 <skill>/scripts/serp_features.py --top-queries <config.serp.top_queries> --gsc-queries .seo/gsc/queries-<date>.json --domain <domain>` lists the queries that earn the clicks.
2. Preflight the cost (one `serp_organic_live_advanced` call per query, `depth: 20`, the site's locale), fetch each, and save the raw responses in a temporary directory.
3. `serp_features.py --ingest <raw...> --domain <domain> --out .seo/serp/<date>.json` normalises them: the features present, our position, whether an AI Overview is present, and whether it cites us.
4. `serp_features.py --diff --serp-dir .seo/serp --gsc-queries <cur> --gsc-prev <prev>` emits candidates: `theft` (a feature appeared, clicks down 20% or more, position within 1.5) with the clicks at risk, and `aio-uncited` (an AI Overview answers the query and does not cite us) with the domains it cites instead.

Both are `aeo-fix` candidates whose `movement` is the clicks at risk, which is what makes them comparable with a refresh. An `aio-cited` row is a defend note. Print the feature counts as one line so a month of records shows AI Overviews spreading across the site's queries.

## 3e. Internal link opportunities

Weekly (`config.cadence.link_opportunities_hours`), and whenever a striking-distance page is the top candidate. `health_diff.py --check-links` finds links that are broken; this finds links that are missing.

```
python3 <skill>/scripts/link_opportunities.py --gsc-queries .seo/gsc/queries-<date>.json --sitemap <config.site.sitemap_url> --domain <config.site.domain> --top 30
```

Page A owns query Q at position 3 to 25. Page B's body contains the phrase Q and does not link to A. Each row is a `repair` candidate (one link from B to A with that phrase as the anchor) whose movement is A's impressions. A page at position 8 with 3,000 impressions and one inbound link is the first row on the site. Several rows pointing at one A are one candidate: wire them all in one edit.

## 3f. Branded vs non-branded

Every run, free, one line:

```
python3 <skill>/scripts/brand_split.py --gsc-queries .seo/gsc/queries-<date>.json --prev .seo/gsc/queries-<prior>.json --config .seo/config.json
```

Branded impressions are the outcome metric for answer-engine and off-page work: someone who read about the product in a ChatGPT answer or a listicle then searches the name. Print the line. A branded query tagged `vs`, `alternative`, `pricing` or `review` with no owner page is a `create-editorial` candidate with the Search Console row as its demand. A branded misspelling with impressions is a new entry for `config.site.aliases`.

## 4. Truth check

Run:

```
python3 <skill>/scripts/truth_check.py --rules .seo/truth-checks.json --root . --from-health .seo/health/<latest>.json
```

`--root` greps the repo; `--from-health` applies the same rules to the rendered text of every page in the latest fingerprint, which needs `health_diff.py --keep-text` (§3). Run both. The file side catches copy in templates, `llms.txt` and code; the rendered side catches copy that lives in a database or CMS, or that a template injects, and it is the only truth check a database-backed site has. A page without stored text is reported as unchecked, never clean.

`truth.md` is the human-readable claim ledger. `truth-checks.json` is its mechanical shadow: for each high-risk claim, a set of paths to scan and regexes that must or must not appear. This is deliberately dumb. The audit that motivated v2 found five pages disagreeing about whether families pay, a `llms.txt` denying a feature two other pages advertised, and a competitor page denying a capability the competitor's own product page listed. Every one of those is a grep.

Any contradiction is a `correct` candidate with the fixed-override priority described in `select.md`. When you add a claim to `truth.md`, add its check here in the same edit. When the truth changes (pricing, a feature launch), update both and let the next run find every page that lags.

## 4b. Product changes since the last run

Every run, free:

```
python3 <skill>/scripts/repo_changes.py --root . --config .seo/config.json
```

It lists the commits since the newest run record that touched `config.repo.watch_paths`: changelog entries, routes, pricing views, feature flags, migrations. The repo is the freshest demand signal the site owns and the one no competitor has. Read it as:

| Change | Candidate |
|---|---|
| A changelog entry or flag for a capability with no owner page | `create-editorial` (a how-to on the capability) with the changelog line as `demand`, plus an `attributes.md` update |
| A pricing or plan file touched | `verify-product` on the pricing claim; then `correct` on every page `truth_check.py` finds lagging once `truth.md` is updated |
| A route removed or renamed | `repair`: a 301 from the old path; check the sitemap and internal links |
| A migration or schema change that alters a public fact (a limit, a format, a supported type) | `verify-product` |

When a fact changed, update `truth.md` and `truth-checks.json` in the same run. That is what lets the next run find every lagging page mechanically instead of by memory.

## 5. Claim re-verification sample

Each shipped piece left a claim ledger in `.seo/briefs/<slug>.md`. Those claims were true when written. Sources move: a regulation is amended, a provider changes its records-request address, a competitor ships the feature you said it lacked. A post-hoc review on one site reframed or removed 72 of 151 sampled claims on pages that had shipped through this skill's predecessor.

Each run, pick `config.budget.claim_reverify_sample` claims (default 3) from the briefs with the oldest `last_verified` date, weighted toward claims marked high-risk (medical, legal, financial, competitor, pricing). Re-open the primary source. Outcomes:

- Still supported: stamp `last_verified` today.
- Source changed: a `correct` candidate with the page, the old claim, the new evidence.
- Source gone: a `correct` candidate to reframe or remove.

Write the sample and outcomes to the run record so the next run does not re-check the same ones.

## 6. Answer-engine panel

Expensive, so cadenced. Run it when any of these hold:

- `config.budget.ai_panel_cadence_days` have passed since `.seo/aeo/scoreboard.md` was last updated.
- The mode is `/seo aeo`.
- A prior run left an `aeo-fix` candidate that needs a remeasure to confirm.

The mechanics are in `aeo/audit.md` (four streams) and `aeo/measurement.md` (metric definitions, margin of error). The preflight rule applies: state the call count and cost, get approval interactively, or stay under budget unattended and record what was sampled.

On days the panel does not run, the free snapshot scripts still can: `robots_check.py` (AI user agents and `llms.txt`), `crawl_check.py` on priority pages (extractability), `depth_check.py` (click depth and orphans). They cost nothing and catch reachability regressions the same day.

## 6b. AI referral attribution

Once per run, one line: how much traffic and how many activation events came from answer-engine referrers (chatgpt.com, perplexity.ai, copilot, gemini, claude.ai) in the last 28 days, from GA4 when connected or from `scripts/log_parse.py --referrals` when logs are configured. If neither exists, write "AI referrals: not measured" and add a needs-you item once. Without this line every AEO action's value is a guess.

## 6c. Demand radar

The one outward-looking panel. Everything above measures our own pages and queries; this one reads what the ideal customer asked, complained about, or reacted to in the last 30 days on Reddit, Hacker News, forums, news, YouTube and Trends, and turns it into `create-editorial` and `refresh` candidates that already carry their demand provenance. Free tier daily, paid tier on `config.radar.cadence_days`. Mechanics, sources and guards: `demand-radar.md`. State: `.seo/radar.md`.

## 6d. Competitor delta

Weekly for the fingerprint and monthly for keywords (`config.cadence.competitor_hours`; ranked keywords sit on the 30-day market-data cache). For each entry in `config.competitors` with a `sitemap_url`:

```
python3 <skill>/scripts/health_diff.py --sitemap <competitor sitemap_url> --out .seo/competitors/<host>/ --limit 500
python3 <skill>/scripts/competitor_diff.py --dir .seo/competitors/<host> --gsc-queries .seo/gsc/queries-<date>.json
```

The first fingerprint is a baseline. From the second, the diff reports new pages, retitled pages, added schema and pages that grew. Monthly, preflight and save the raw `dataforseo_labs_google_ranked_keywords` response for the competitor's domain (`limit: 1000`, one call per competitor) as `.seo/competitors/<host>/ranked-<date>.json`; the same script then reports the keywords they gained. A gain on a query we already have a row for is a `refresh` of our owner page, with the competitor's page as the bar to beat. A gain on a query we have no row for is a lead, not a candidate: it still needs a thread or a Search Console row for `demand`, so it becomes a radar seed. A new competitor page in a vein we own is a `refresh` prompt for our owner page.

Never copy a competitor page. The diff says where demand moved. The information-gain rule still decides what we write.

## 6e. Backlinks new and lost

Weekly (`config.cadence.backlinks_hours`) when DataForSEO is connected; the monthly spam score stays in 3c. Three preflighted calls: `backlinks_backlinks` for the domain filtered to `is_lost` or `is_new` in the last 30 days (`order_by` rank descending, `limit: 100`); `backlinks_backlinks` filtered to `url_to_status_code` not 200; `content_analysis_search` for `config.site.name` and each alias with `date_from` 30 days ago. Save the raw responses, then:

```
python3 <skill>/scripts/backlink_diff.py --backlinks <raw> --new-lost <raw> --mentions <raw> --gsc .seo/gsc/<date>.json --domain <domain> --brand <name> --out .seo/backlinks/<date>.json
```

Candidates: a lost link to a page that earns clicks is an `offpage-brief` (reclamation: the page moved, the link broke, or the author pruned it, and the brief asks for one restore); an inbound link landing on a non-200 URL is a `repair` (a 301 to the nearest owner, the cheapest link-building there is); an unlinked mention is an `offpage-brief` asking for the link, after fetching the page to confirm no link exists. A new link with a high spam score is a watch note, never a disavow. The skill does not file disavows.

## 6f. Seasonality

Monthly (`config.cadence.seasonality_hours`). One preflighted `dataforseo_labs_google_historical_keyword_data` call for the radar seeds plus the top 50 queries by impressions, saved raw to `.seo/seasonality.json`. Then:

```
python3 <skill>/scripts/seasonality.py --data .seo/seasonality.json --lead-weeks 8
```

A keyword whose volume eight weeks out is 1.3 times today's is `rising`, and its candidates carry `season_bonus: +1` (+2 at twice today's) into the movement axis in `select.md` §3, because a page has to be live and indexed weeks before the peak to own it. `falling` carries −1. The bonus expires with the file.

## 7. Debt

Read the "Not done" section of the last three run records in `.seo/runs/` and the open items in `needs-you.md`. Not-done items are candidates again today. Needs-you items are not candidates; they are printed at the end of the run so the human sees them, and any candidate blocked on one is scored as blocked, not dropped.

## 7b. Outcomes of past actions

Every run, free:

```
python3 <skill>/scripts/outcomes.py --ledger .seo/content-ledger.md --gsc-dir .seo/gsc --out .seo/outcomes.json --priors .seo/priors.json
```

Every ledger row older than 28 days gets a verdict from the saved Search Console pulls: the target's change against the site-wide change over the same windows. `worked` beats the site by 20 points, `hurt` trails it by 20, `flat` sits between; a create is `worked` at 5 clicks or 200 impressions and `invisible` after 45 days with nothing. Verdicts roll up into `priors.json`: per action, and per content type for editorial, how often the action worked on this site, and a `confidence_adjust` of +1, 0 or −1 that `select.md` §3 applies to the confidence axis. Print the newly decided verdicts and the priors lines. A `hurt` verdict on a refresh is itself a `refresh` candidate (revert or redo), and a run of `invisible` creates in one type is what marks a vein cold.

This is the loop the old skills never closed. Without it the rubric guesses the same confidence on every site forever.

## 8. Gates that come out of measurement

Two, and they are the reason measurement runs first.

**Index gate.** If the last three published pieces are not indexed, this run's job is fixing that, not writing a fourth. Route to `lanes/technical.md` with an `index-nudge` candidate per page.

**Truth gate.** If the truth check reports a contradiction, no `create-*` candidate may win selection until the contradiction is corrected in this run or the user explicitly defers it (interactive) or it is logged as blocked with a reason (unattended). Publishing new pages while live pages lie about the product compounds the lie.

## 9. Panel summary

Write this block to the run record before selection. Keep it to what changed.

```
## Measured
GSC 28d: <clicks> / <impressions> (prev <clicks> / <impressions>). Pages: <n> winning, <n> close, <n> wrong-query, <n> invisible, <n> decaying, <n> unindexed.
Bing: <panel or "no key">.
Health: <n> pages, <n> changed, <n> violations. Worst: <one line>.
Truth: <n> rules, <n> contradictions. <first contradiction or "clean">.
Claims re-verified: <n> ok, <n> changed, <n> gone.
AI panel: <ran / due in N days / skipped: reason>.
AI referrals: <sessions> / <activations> or "not measured".
Census: <n> pages; <n> keep, <n> refresh, <n> merge, <n> prune, <n> invisible, <n> broken. Invisible share <pct>. create_gate=<bool>. Cold veins: <list or none>.
Vitals: speed median TTFB <ms>, <n> slow, LCP/INP/CLS <top-10 medians or unchecked> | relevance <n> pages off-topic | CTR site <pct>, weighted gap <x>, <n> low-ctr | links <n> broken, <n> redirecting, <n> orphans, backlinks <n> domains / spam <score or unchecked>.
Radar: <n> new signals from <n> seeds, <n> clusters proposed, <n> dropped (answer owner / fit). Top: <one line>.
SERP: <n> tracked queries; AI Overview on <n> (cites us <n>), snippet <n>, video <n>. Theft: <n> queries, <clicks> at risk. Top: <one line>. | or "due in N days"
Links+: <n> internal link opportunities; top owner <url> (<impr> impr, <n> inbound). | or "due in N days"
Brand: <impr> / <clicks> (prev <impr> / <clicks>) · non-brand <impr> / <clicks> · share of clicks <pct>.
Product: <n> commits touching <categories> since <last run>. <one line or "none">.
Competitors: <host>: <n> new pages, <n> retitled, <n> keyword gains (<n> on our queries). <one line, or "baseline" / "due in N days">.
Backlinks±: +<n> / −<n> links; <n> lost to earning pages, <n> inbound-404, <n> unlinked mentions. | or "due in N days"
Seasonality: <n> rising (top: <kw, kw>), <n> falling. | or "due in N days"
Outcomes: <n> decided (<n> worked, <n> flat, <n> hurt, <n> invisible). Priors: <refresh 7/9 (+1), create-editorial 2/8 (−1), ...>.
Debt: <n> not-done items carried, <n> needs-you open.
Unchecked: <panels that could not run and why>.
```

An unchecked panel is listed as unchecked. It is never omitted and never reported as clean.
