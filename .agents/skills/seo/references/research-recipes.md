<!-- merged from seo-sprint/references/dfs-recipes.md + seo-content/references/research-recipes.md + seo-sprint/references/manual-research.md -->

# Research Recipes — the exact market-data calls

Every research task maps to a specific MCP tool call, or a short pipeline of them. Results swing wildly on `location_name`, `language_code`, and the `filters` you pass, so these recipes are the working set to reuse rather than re-derive.

**Three sources, three jobs. Never buy the same fact twice.**

| Source | Owns | Never use it for |
|---|---|---|
| **DataForSEO** | Keyword, backlink, and SERP research. The outside world. | Your own positions or clicks |
| **Search Console** | Ground truth on your own site: real queries, positions, CTR, index state | Anything about a competitor |
| **OpenSEO** | Site crawl, rank history, GA4 outcomes, project memory | Keyword/backlink/SERP research |

**Why research stays on direct DFS:** OpenSEO wraps the same DataForSEO account, but its research tools expose no `filters` or `order_by`. Every recipe below depends on server-side filtering by dotted field path, so routing them through OpenSEO means paying for rows you would have filtered out. Use OpenSEO for what DFS-direct genuinely cannot do.

Where DFS and GSC overlap on your own domain, **GSC is ground truth and DFS is an estimate.** Everything about your own site — the queries you already get impressions for, real positions, real CTR, index status, whether the last thing you shipped worked — lives in `gsc.md`. Run both; they answer different questions.

Config lives in `.seo/config.json`. GSC needs the exact property string (`gsc.site_url`); DFS endpoints take a `target` domain directly and need no project id.

## Contents

- [Cost control](#cost-control)
- [Difficulty buckets — the winnability model](#difficulty-buckets--the-winnability-model)
- [Recipe A — Baseline: where are we starting?](#recipe-a--baseline-where-are-we-starting)
- [Recipe B — Competitor reverse-lookup (the main candidate source)](#recipe-b--competitor-reverse-lookup-the-main-candidate-source)
- [Recipe C — Use-case, audience, and tool-intent sweeps](#recipe-c--use-case-audience-and-tool-intent-sweeps)
- [Recipe D — Comparison volume check](#recipe-d--comparison-volume-check)
- [Recipe E — Striking-distance audit (GSC, always)](#recipe-e--striking-distance-audit-gsc-always)
- [Recipe F — Backlink target research](#recipe-f--backlink-target-research)
- [Recipe G — SERP read (never cached, never skipped)](#recipe-g--serp-read-never-cached-never-skipped)
- [Recipe H — Rank tracking](#recipe-h--rank-tracking)
- [Recipe I — AI-citation gaps](#recipe-i--ai-citation-gaps)
- [No keyword tool at all](#no-keyword-tool-at-all)

---

## Cost control

DFS bills prepaid, per call. There is no monthly unit quota and no cliff at zero, so the discipline is about not buying rows you will never read rather than about surviving a cap.

Five rules, in order of how much they save:

1. **Filter server-side in `filters`** so the rows you pay for are rows you can use (bucket-appropriate KD, `search_volume >= 30`). Filtering after the fetch means paying for everything you throw away.
2. **Cut `limit` to what you'll actually read.** Cost is linear in rows. Nothing downstream looks past the top ~30 winnable candidates per competitor.
3. **Two-stage pulls, not smaller pulls.** Sweep wide on a cheap discovery call, then enrich *only the shortlist* with the expensive per-keyword detail. The rubric keeps every input it had; you just stop pricing 140 candidates nobody reads.
4. **Batch instead of looping.** `dataforseo_labs_google_keyword_overview` takes up to 700 keywords per call and `backlinks_bulk_ranks` up to 1000 targets. One batched call beats fifty single ones — Recipes A and D are written to exploit this.
5. **Cache, and honor the 30-day rule.** `.seo/keyword-research.json` holds every prior result. Re-running a content-gap sweep that ran nine days ago costs full price for near-identical data. **Do not re-query a slice under 30 days old** unless the user explicitly asks to re-research; read it from cache and query only the delta you lack.

Two more that only apply where the tools are connected:

- **Read `get_project_context` before buying research.** It carries a log of what OpenSEO already pulled for this project. Checking it is free; re-buying a sweep someone ran last week is not.
- **Rank trackers bill on a schedule, not per call.** They are the only recurring cost here. Audit them when a push ends: a tracker left on daily for a finished phase bills forever.

**Never cache the SERP.** Volume and KD move slowly, so a 30-day cache is honest. SERP composition is the fastest-moving input in the skill and it decides the content type — re-run Recipe G live on the chosen keyword, every run, no exceptions. A cached SERP is how you write a listicle into a SERP that turned into tools last month.

**Cost never overrides a gate.** These rules exist to stop the skill buying data it won't read, not to make it ship something thinner. If a decision or a ship gate needs a number, **buy it, or tell the user you couldn't and why.** Silently deciding on worse data to save a few calls is the one failure mode that costs more than the calls ever did.

---

## Difficulty buckets — the winnability model

**There is no KD ceiling any more, and no `KD ≤ DR + 10` arithmetic.** That formula implied a precision nobody has: KD is a vendor-specific score rather than a physical quantity, and on a young site the whole picture turns over in a few months. False precision produced confident, wrong rejections.

Sort candidates into three buckets and ask one question: *are we even remotely in this bucket's league?*

| Bucket | DFS KD | Fallback signal — avg `referring_domains` of ranking pages | Who plays here |
|---|---|---|---|
| **Easy** | 0-14 | < 20 | A new site. DR 0-10 |
| **Medium** | 15-29 | 20-100 | An establishing site. DR ~10-25 |
| **Hard** | 30+ | 100+ | DR 25+, or don't bother yet |

**The fallback signal matters.** DFS omits `keyword_difficulty` on a meaningful share of keywords (2 of 7 in a live sample). When KD is missing, bucket on `avg_backlinks_info.referring_domains` from the same response instead — it's arguably the truer signal, since it's what the ranking pages actually had to accumulate. **Never drop a candidate just because KD came back null.**

### Which bucket are we in? Ask GSC, not DR

Derive the playable bucket empirically from results you already have — free, and it beats any heuristic:

1. Pull your ranked queries from GSC (`gsc.md` §1, or Recipe E below).
2. Price the ones you rank **page 1** for with `dataforseo_labs_google_keyword_overview`.
3. **The hardest bucket where you hold two or more page-1 positions is your playable bucket.**

Live examples, both real: a DR 0 site sat at position 13.5 on a **KD 10** keyword and 34.8 on a **KD 18** one — playing in **Easy**, not yet in Medium. A DR 14 site ranked 6.6 on a **KD 27** keyword — genuinely playing in **Medium**.

### How to use the buckets

- **Target your playable bucket.** That's the default, and most picks should sit there.
- **Allow one stretch pick in four** into the next bucket up. A site that only ever targets its current bucket never finds out it has moved, and DR climbs faster than any cache notices.
- **Skip the bucket above that entirely.** Hard candidates for an Easy site aren't ambitious, they're a wasted run.
- **Re-derive every few weeks** from steps 1-3, not from a stored number. It's free and it's the only reading that reflects reality.
- **Never reject on KD alone.** The SERP read (Recipe G) outranks the bucket in both directions: three thin forum results in the top 10 beats a KD score, and a bucket is a prior, not a verdict.

Store `difficulty_bucket` on every candidate row instead of a bare KD number, alongside the vendor that produced it. **Never mix KD scores from different vendors in one comparison** — if a cached row predates the current tool, re-price it before ranking it against a fresh row.

---

## Recipe A — Baseline: where are we starting?

**Goal:** know the domain's authority and ranking baseline before doing anything. Authority is context for the bucket read, not a formula input.

```
1. backlinks_bulk_ranks
   targets: ["<user-domain>", "<competitor-1>", "<competitor-2>", ...]   # up to 1000 per call
   rank_scale: one_hundred
   → rank for you AND every competitor in a single call

2. dataforseo_labs_google_domain_rank_overview
   target: <user-domain>
   location_name: "United States"
   language_code: en
   → organic keyword count, estimated traffic value (etv), position distribution

3. dataforseo_labs_google_ranked_keywords
   target: <user-domain>
   location_name: "United States"
   language_code: en
   limit: 100
   order_by: ["ranked_serp_element.serp_item.etv,desc"]
   → what the site already ranks for (the baseline for striking distance)
```

Save under `baseline.*` in `.seo/keyword-research.json`. Print a summary back: "Your domain scores N/100 on authority with M keywords ranking. Highest-traffic page is /<path> for [keyword] at position Y."

> **Scale warning.** DFS `rank` is its own authority index. Any authority score stored in `.seo/` that came from a different tool is stale — re-baseline rather than comparing across the two. On `rank_scale: one_hundred` the numbers land in a familiar range (a live check returned buffer.com 81, hootsuite.com 73, later.com 62), but **only `backlinks_bulk_ranks` accepts `rank_scale`** — every other backlinks endpoint returns 0-1000. Always record which scale a stored number came from. `backlinks_timeseries_summary` gives the history when you need the trend.

---

## Recipe B — Competitor reverse-lookup (the main candidate source)

**Goal:** find which keywords each named competitor ranks for that you could also target. Most `/alternatives/[competitor]` candidates come from here, plus a lot of `/for/[use-case]` ideas and most editorial candidates.

The sharpest version is the content gap — what they rank for and you do not:

```
dataforseo_labs_google_domain_intersection
  target1: <competitor-domain>       # repeat per competitor from .seo/brand.md
  target2: <user-domain>
  intersections: false               # ← keywords target1 ranks for and target2 does NOT
  location_name: "United States"
  language_code: en
  limit: 50
  filters: [["keyword_data.keyword_info.search_volume", ">", 30], "and",
            ["keyword_data.keyword_properties.keyword_difficulty", "<", 30]]
  order_by: ["keyword_data.keyword_info.search_volume,desc"]
```

Each row carries volume, KD, 12 months of history, trend, classified search intent, and the average referring domains of the ranking pages — everything the rubric needs, in one call. Bucket each row per the table above.

Then, to read which page templates they invested in:

```
dataforseo_labs_google_relevant_pages
  target: <competitor-domain>
  location_name: "United States"
  language_code: en
  limit: 30
```

If they have 50 `/integrations/*` pages and that pattern matches your product, consider adding it.

**Apply a relevance gate before anything else, and expect to cut most of the list.** Raw content-gap output is noisy in a specific way: big competitors with millions of user-generated pages rank incidentally for enormous off-topic queries — person names, navigational junk, anything sharing a word with their brand. A live run of this exact call (a health-community site vs a small records product) returned `wayback burgers` at 301,000/mo, plus `kt johnson`, `jarvisqq`, and `bridges and cameron funeral home`.

Two gates, in order:

1. **Is this a real query in our space?** Drop navigational, brand, and person-name junk. A high-volume row you can't explain is noise, not an opportunity.
2. **Is it *our* space, or just theirs?** In the same run the genuinely strong rows — `what to write in a sympathy card` (22,200, KD 2), `what to say to someone who lost a loved one` (12,100, KD 2) — were real keywords belonging to the competitor's **sympathy-content** territory, while the site is a medical-records organizer. Winnable and off-positioning is still a no. Check every survivor against the positioning and anti-positioning in `.seo/brand.md`.

**Output to capture per competitor:**

- Brand-term volume + KD (the keyword that is just their brand)
- Top 20 non-brand keywords (skip brand variations like `[brand] login` unless pricing volume is high)
- Top 10 pages by traffic (informs which patterns to copy)
- `primary_seo_territory` — the slice of their footprint that is actually relevant, written down once so later runs skip the noise

Save under `competitors.<name>.*`.

---

## Recipe C — Use-case, audience, and tool-intent sweeps

**Goal:** find `/for/[use-case]` and `/for/[audience]` candidates, question-shaped editorial candidates, and the free-tool candidates that are the highest-value output this engine has.

```
# Pull A — use-case, audience, and question sweeps
dataforseo_labs_google_keyword_suggestions
  keyword: "<seed>"             # one call per seed
  location_name: "United States"
  language_code: en
  limit: 100
  filters: [["keyword_info.search_volume", ">", 30]]
  order_by: ["keyword_info.search_volume,desc"]
```

Seed strategy:

- Take the product one-liner: e.g. "social media monitoring tool"
- Use-case seeds: `["social media monitoring", "twitter monitoring", "social listening", "brand monitoring", "competitor monitoring"]`
- Audience seeds: `["[category] for agencies", "[category] for ecommerce", "[category] for freelancers"]`

Run one pass per seed set, then filter to question modifiers (how, what, why, best, vs, for) for the editorial candidates.

```
# Pull B — tool intent. Keep it SEPARATE from Pull A.
dataforseo_labs_google_keyword_suggestions
  keyword: "<cluster seed> calculator" | "... generator" | "... checker" | "... template"
  limit: 50
  # NO volume floor
```

**Pull B takes no volume floor.** Tool candidates are routinely low-volume with high link-draw, and a shared volume filter is exactly how they get deleted before anyone sees them. Judge them on referring domains and repeat use, per `opportunity-research.md`.

**There is no `traffic_potential` or `parent_topic` field** — those were vendor-proprietary composites. Replace them with intent classification plus hand clustering:

```
dataforseo_labs_search_intent
  keywords: [...]               # informational / commercial / navigational / transactional
  language_code: en
```

Cluster by hand on shared head terms and intent class. Each cluster is roughly one `/for/*` page candidate. Rank clusters by **summed volume across the cluster**, which is the honest version of what traffic potential estimated.

When a sweep comes back thin: `dataforseo_labs_google_keyword_ideas` casts wider, and `dataforseo_labs_google_related_keywords` expands off a term you already rank for (`keyword: "<your best-ranking term>", limit: 30`). Both are expansion, not a per-run necessity. `dataforseo_labs_google_keyword_overview` (700 keywords per call) is the cheapest way to price a list you already have — use it to bucket a shortlist rather than re-running a discovery sweep.

Save under `use_cases.*` and `audiences.*`.

---

## Recipe D — Comparison volume check

**Goal:** validate `/compare/[a]-vs-[b]` candidates. Run before adding any comparison row to the roadmap.

Batch every candidate pair into one call — this endpoint takes up to 700 keywords:

```
dataforseo_labs_google_keyword_overview
  keywords: ["<a> vs <b>", "<b> vs <a>", "<a> vs <c>", "<c> vs <a>", ...]
  location_name: "United States"
  language_code: en
```

Capture `search_volume` and `cpc` (a strong commercial-intent proxy here) plus the returned `search_intent_info`. Comparison volumes are typically 30-500; anything ≥30 is worth a page since intent is so high. **Build one page per canonical pair** (alphabetical: `a-vs-b`) — both directional searches rank for the same URL.

Save under `comparisons.*`.

---

## Recipe E — Striking-distance audit (GSC, always)

**Goal:** find pages ranking position 5-20 that a push moves to top-5. Often the highest-leverage work available on any existing site.

**This is a GSC job, not a market-data job.** It is free, exact, and it includes the long-tail queries no keyword vendor indexes. There is no market-data substitute worth paying for.

```
get_advanced_search_analytics
  site_url:       <gsc_site_url>
  start_date:     <90-days-ago>     # YYYY-MM-DD
  end_date:       <today>           # YYYY-MM-DD
  dimensions:     "query,page"      # comma-separated STRING, not an array
  row_limit:      1000              # max 25000; paginate with start_row
  sort_by:        impressions
  sort_direction: descending
```

Use `get_advanced_search_analytics`, not `get_search_analytics` — the plain one takes a `days` integer instead of a date range and caps at 500 rows.

Filter locally to `position >= 5 AND position <= 20 AND impressions >= 50`, then sort by impressions descending. Requesting both dimensions in one call returns the (page, keyword) pairing directly — there is no cross-referencing step.

Cross-check which page owns the query. If a **dedicated page already exists**, this is a `refresh`, not a new piece — scope it with `gsc.md` §2d. If the ranking page is the homepage, a hub, or something unrelated, the site has proven demand and no page that deserves it, which is the best candidate this engine can find.

`get_search_by_page_query` drills into the full query set behind one URL. `compare_search_periods` shows whether a boost worked after it ships.

**If OpenSEO is connected with GA4 attached, add this as a prioritiser (not a replacement):**

```
get_search_opportunities
  projectId: <project id>
  startDate / endDate: YYYY-MM-DD   (optional)
  limit: 100                        # max 100 — this is the catch
```

It runs the same positions-4-20 join but scores each row by demand, business value, and reachability from GA4 outcomes, so a position-8 page that converts beats a position-6 page that doesn't. Read-only, no OpenSEO credits.

**Two verified limits, both load-bearing:**

1. **It caps at 100 rows** against `get_advanced_search_analytics`'s 25,000. Use GSC for the full sweep and this for the prioritised shortlist. It is not a substitute.
2. **Without a GA4 connection every `score` comes back `null`** — a live run returned 50 rows from 716 candidates with `0 candidates matched GA4 landing pages` and a null score on every one. Unmatched rows stay visible and carry the raw GSC clicks/impressions/position, so the call still works; it just ranks nothing. **If `score` is null across the board, GA4 isn't wired — say so and fall back to the GSC sort rather than presenting an unranked list as a prioritised one.**

**Output** per candidate: URL, keyword, current position, 90-day impressions, estimated traffic at position 3 (CTR bands in `gsc.md` §2c), and the boost strategy — depth, FAQ, new H2, or new internal links.

Save under `striking_distance.*`. **Front-load these** — they're faster than new pages and they use existing link equity.

---

## Recipe F — Backlink target research

**Goal:** find directories, guest-post candidates, and link-trade prospects ranking in the niche. Feeds the off-page briefs; a human does the sending.

Start with the link gap — domains linking to competitors but not to you:

```
backlinks_domain_intersection
  targets: ["<competitor-1>", "<competitor-2>"]     # array, up to 20
  exclude_targets: ["<user-domain>"]                # up to 10
  limit: 100
  filters: [["1.rank", ">", 200]]                   # 1./2. prefixes map to targets by position
  order_by: ["1.rank,desc"]
```

Or per competitor:

```
backlinks_referring_domains
  target: <competitor-domain>
  limit: 100
  filters: [["rank", ">", 200], "and", ["backlinks_spam_score", "<", 30]]
  order_by: ["rank,desc"]
```

> **Scale gotcha, verified live.** The backlinks endpoints return `rank` on a **0-1000** scale and take no `rank_scale` parameter — only `backlinks_bulk_ranks` lets you ask for 0-100. A threshold like `rank > 30` therefore filters out almost nothing here. Sort by `rank` descending and take the top N rather than trusting a hard cutoff; treat any threshold below ~200 as decoration.

`backlinks_spam_score` filters server-side, so junk never reaches your shortlist. (There is no `dofollow` filter field on this endpoint — the nofollow counts live under `referring_links_attributes.nofollow` and `referring_domains_nofollow`.) To score a list you already have from elsewhere:

```
backlinks_bulk_spam_score
  targets: [<candidate domains>]        # up to 1000
```

Filter results manually for:

- **Directory candidates** — site name matches "[category] directory", "[category] tools", "alternatives", "list", "vs"
- **Guest post candidates** — looks like a blog (`*.com/blog/...` paths), decent rank
- **Tool roundup candidates** — sites ranking for "best [category]" keywords
- **Skip** — generic press-release sites, paid-link networks, irrelevant niches, anything with a high spam score

`backlinks_competitors` surfaces domains with backlink profiles similar to yours, which is a good source of prospects nobody thought of. Per candidate capture: domain, rank, spam score, and what they link to about the competitor (that informs the pitch angle).

Save to `.seo/backlink-targets.json` and use it to populate the off-page checklist in `.seo/roadmap.md`.

---

## Recipe G — SERP read (never cached, never skipped)

**Goal:** before targeting a keyword, look at who ranks and whether you can realistically displace them. This one call decides the single highest-leverage choice in a run: the page type.

```
serp_organic_live_advanced
  keyword: "<target keyword>"
  location_name: "United States"
  language_code: en
  depth: 10
```

A **live** SERP, not a cached snapshot, which is what this decision needs. Read the top 10:

- Most of the top 10 are substantive pages from established sites → skip, or downgrade the bucket read; you're likely out of your league.
- 3+ of the top 10 are thin → strong signal you can rank regardless of KD.
- The top 3 are Reddit/Quora threads → strong signal; a real page outranks them.
- The top 1-2 are direct brand pages (buffer.com for "buffer") → table stakes; the question is about positions 4-10.
- The **format** of the top 10 dictates the page type. Listicles ranking means write a listicle; a SERP full of articles about a calculation people would rather just run means build the tool (`content-types.md`).

**Run this before starting work on any candidate.** It catches doomed work early, and the SERP read outranks the difficulty bucket in both directions.

---

## Recipe H — Rank tracking (proving something worked)

**Goal:** position history for the keywords a piece of work targeted. GSC gives average position for queries you already surface for, but it cannot track a keyword you do not yet rank for, and it will not tell you where you sat last Tuesday.

Requires OpenSEO. Create the tracker once per project, then add keywords per phase:

```
1. get_rank_tracker      projectId          # check first — avoid duplicates
2. create_rank_tracker   projectId          # empty tracker costs nothing
     # domain defaults to project domain, market to project market,
     # devices to mobile, depth 40, schedule "manual"
3. estimate_rank_tracker_cost   projectId, trackerId
4. add_rank_tracking_keywords   projectId, trackerId, keywords: [...]
```

**Always run `estimate_rank_tracker_cost` before adding keywords to a scheduled tracker.** An empty tracker on a manual schedule costs nothing, but daily/weekly/monthly schedules spend credits on every check, forever, and the cost scales with keywords × devices × checks per month. The estimate returns `monthlyCostUsd` per interval — quote it and let the user pick. **Never silently create a daily tracker.**

**Track the target keywords only.** A tracker holding every keyword the research surfaced is a recurring bill for data nobody reads. Ten to thirty keywords per phase is the useful range.

Record `trackerId` in `.seo/config.json` so later runs add to the same tracker instead of creating a second one.

---

## Recipe I — AI-citation gaps

**Goal:** questions in your space that answer engines answer without citing you. Filling these is high-leverage AI surface area, and it is a different question from "what ranks."

```
ai_opt_llm_ment_search            # who gets mentioned for a prompt
ai_opt_llm_ment_top_pages         # which pages get cited
ai_opt_llm_ment_top_domains       # which domains get cited
ai_optimization_llm_response      # the answer itself, for a specific prompt
```

**Rankings and AI citations are separate outcomes with separate inputs.** Don't assume the best-ranking pages are the most-cited ones — measure the two separately (GSC for rankings, these calls for citations) and record them as separate columns rather than one blended score.

---

## No keyword tool at all

No DataForSEO connection? The skill still works — precision drops, capability doesn't. Be honest up front: *"No keyword tool is connected, so volume and KD will be estimates. We can still pick and ship something strong; refine the numbers later with a tool."*

**Check GSC before assuming this mode.** If Search Console is connected, only the *market* half is missing: striking distance, real positions, real CTR, index state, and cannibalization are all still exact and free (`gsc.md` §1). What's genuinely absent is volume and KD for queries you don't rank for, competitor gaps, and per-result authority in the SERP. Say it that precisely instead of "no data."

### 1. The user pastes data from their own tool

If they have Semrush, Mangools, Ubersuggest, or anything similar, ask them to paste:

- Their domain's DR / DA / authority score
- A competitor organic-keyword export (CSV)
- Comparison-keyword volumes for the pairs under consideration
- Striking-distance keywords (position 5-20) — **only if the GSC MCP is also unavailable**

Parse into the same `.seo/keyword-research.json` shape you'd build from DFS. Validate the columns; warn about missing KD or volume rather than silently defaulting them.

### 2. Web-search-based reverse-lookup

1. **Identify competitors** — ask, or read their pricing and about pages.
2. **Search for each** — `"<competitor> alternatives"`, `"<competitor> vs"`, `"<topic> guide"` via web search. Read Google autocomplete, the **People-Also-Ask** box, and "related searches" (fetch `google.com/search?q=...` as text with the host's page fetch).
3. **Scrape the top 3-5 ranking pages** for the target topic — capture their H1/H2 structure and depth. This is the table-stakes-plus-gap read that Recipe G would have given you.
4. **Estimate volume crudely** from Google Trends relative interest. A comparison keyword with steady interest score 10+ is probably worth ≥30 monthly searches. Record as a **range**, and mark `"source": "estimated"`.

### 3. Structured interview (last resort)

Ask the user: who are your 3-5 best-known direct competitors? What problems do customers describe at signup? What tools did they try before yours? What does the ideal customer's title and industry look like? Unattended, this recipe does not run — take the competitor set already in `.seo/config.json` and `.seo/brand.md`, and file the interview in `.seo/needs-you.md` rather than blocking the run on it.

Turn the answers into hypothesis candidates — competitor names into `/alternatives/*`, stated problems into `/for/[use-case]`, industries and personas into `/for/[audience]` — mark them all unvalidated, and suggest validating volumes with a free tool (Google Keyword Planner, the Mangools KWFinder free tier, Keywords Everywhere) before deep work.

### What's degraded

| Capability | Full mode | Fallback mode |
|---|---|---|
| Keyword volume | precise monthly searches | range estimate, marked `estimated` |
| Difficulty bucket | DFS KD, or avg referring domains | read the SERP: thin/forum results = Easy, established pages everywhere = Hard |
| Cluster value / traffic potential | summed volume across a cluster | volume × CTR estimate |
| Striking distance | **GSC MCP (exact, unaffected by this mode)** | GSC MCP if connected, else the user pastes GSC data |
| Own-site positions / CTR / index status | **GSC MCP (exact, unaffected by this mode)** | same — GSC is free and independent of any keyword tool |
| Backlink target research | competitor referring domains | manual: who links to the top-3 competitor results? |
| SERP overview | live top 10 with per-result metrics | fetch the SERP page as text |

### Effect on the roadmap

In fallback mode, `.seo/roadmap.md` should front-load a "validate this volume" step on every phase, label each row `high` / `medium` / `estimated`, and carry a top-of-doc note: *"Fallback research mode — refine when a keyword tool is connected."*

When a tool becomes available later, run a refresh pass to upgrade `estimated` rows to real numbers.
