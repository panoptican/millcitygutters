<!-- merged from seo-content/references/gsc.md + seo-sprint/references/striking-distance.md -->

# Search Console — own-site truth

Direct Search Console access (the tools in `tools.md`) is the only source of **ground truth about your own site**: the real queries Google already shows you for, the real positions, the real CTR, and the real index status. DFS estimates the market from the outside. GSC reports what actually happened. When they disagree about your own site, GSC wins.

This file covers: property resolution, the six selection signals, the post-publish measurement loop, how to scope and write a boost (§2d), index verification, how to get new content indexed faster (§7), Bing Webmaster as an optional second panel (§8), and the traps. Market-side recipes (competitor gaps, volume, KD, SERP shape) stay in `research-recipes.md` — GSC cannot answer those.

**GSC changes the engine from open-loop to closed-loop.** Without it, this skill ships a piece and never learns whether it worked. With it, every run starts by reading the scoreboard for what it already shipped, and that read is allowed to change what it ships next.

## Contents

- [§0 — Resolve the property](#0--resolve-the-property-once-per-repo-cached)
- [§1 — Selection signals](#1--selection-signals-step-2-select-source-b2)
- [§2 — Measure what shipped](#2--measure-what-shipped-step-1-measure-the-closed-loop)
- [§2b — First GSC run on an existing library (the backfill)](#2b--first-gsc-run-on-an-existing-library-the-backfill)
- [§2c — Size the boost: three levers, biggest one wins](#2c--size-the-boost-three-levers-biggest-one-wins)
- [§2d — Scope the boost: what a boost run actually changes](#2d--scope-the-boost-what-a-boost-run-actually-changes)
- [§3 — Index verification](#3--index-verification)
- [§4 — GSC as first-party data](#4--gsc-as-first-party-data-information-gain)
- [§5 — Traps](#5--traps)
- [§6 — Fast reference](#6--fast-reference)
- [§7 — Get new content indexed faster](#7--get-new-content-indexed-faster-ship-time)
- [§8 — Bing Webmaster (optional second panel)](#8--bing-webmaster-optional-second-panel)

---

## §0 — Resolve the property (once per repo, cached)

```
list_properties            # returns site_url + permission_level for every verified property
```

Match the repo's `domain` from `.seo/config.json` to a property and store the exact string as `gsc.site_url` in `.seo/config.json` (the code blocks below write it as `<gsc_site_url>`). Two forms exist and they are not interchangeable:

- `sc-domain:example.com` — domain property. Covers every subdomain and both protocols. Prefer it.
- `https://example.com/` — URL-prefix property. Exact prefix only, trailing slash included.

If the repo's site is a subdomain (`blog.example.com`) and only the domain property exists, use the domain property and add a page filter: `{"dimension":"page","operator":"contains","expression":"blog.example.com"}`.

No matching property means the site is not verified in this Google account. Say that once, skip every GSC step, and run the rest of the skill on market data. Do not stop.

An authenticated property with near-zero rows means a new site, not a broken tool. Skip §1–§3 (there is nothing to measure yet) and select from market data alone. Note it at the checkpoint: *"GSC is connected but the property has almost no data yet, so selection is running on market signals."*

---

## §1 — Selection signals (Step 2 Select, source B2)

1a-1e run off `get_advanced_search_analytics`; 1f pairs that pull with one DFS call. Use a **90-day window** for selection (enough volume to be stable, recent enough to reflect the current site) and `dimensions: "query,page"` unless noted. Pull sorted by impressions, then filter locally.

### 1a. Striking distance — the highest-yield signal in the skill

Queries you already rank 5–20 for, with real impressions, where **no dedicated page exists**.

```
get_advanced_search_analytics
  site_url: <gsc_site_url>
  start_date: <90 days ago>   end_date: <today>
  dimensions: "query,page"
  row_limit: 1000
  sort_by: impressions   sort_direction: descending
```

Filter the returned rows: `position >= 5 AND position <= 20 AND impressions >= 50`. **The API has no position filter** (`filters` accepts only query, page, country, device), so this happens after the fetch, not in the call.

Then split the survivors:

- The ranking page is the **homepage, a hub, or an unrelated post** → the site has proven demand and no page that deserves it. This is a **new piece**, and it is the best kind of candidate this engine can find: demand is confirmed, not estimated.
- A **dedicated page already exists** → this is a **boost**, not a new piece. Route it to §2.

Record real impressions on the candidate row. A GSC-sourced candidate carries measured demand, so it outranks an equal candidate whose volume came from a keyword tool's estimate.

### 1b. Unowned demand (impressions, no clicks)

Same pull, filter `impressions >= 100 AND clicks <= 2 AND position > 10`. These are queries Google thinks you are relevant for and nobody clicks, because the ranking page is not about that query. High-signal, low-competition topic seeds that keyword tools never surface, because many carry no measurable global volume at all.

### 1c. CTR gap (a boost candidate that competes with writing anything)

Pull `dimensions: "page"`, then per suspicious page pull `get_search_by_page_query`. Flag any row where **position ≤ 10 but CTR is well under the positional norm** — and **quantify the gap in clicks** rather than calling it "bad" (§2c: `impressions × expected_ctr(position) − actual clicks`).

A page at position 4 with 3,000 impressions and 1.2% CTR does not need more content. It needs a better title and description, and that is a fifteen-minute edit that beats a new 1,800-word piece on expected value. Carry the estimate to the checkpoint so the comparison is numeric, not rhetorical.

### 1d. Cannibalization (an exclusion signal, not a candidate)

From the `query,page` pull, group by query. Any query where **3+ pages** take impressions is a query the site already splits itself on. Writing a fourth page makes it worse. Add these queries to the Step A exclusion set — and **name the owner**: the page with the best position on that query is the one that should hold it. Don't stop at "this is cannibalized"; convert it into a specific instruction (boost the owner, de-optimize or consolidate the losers, redirect the weakest), because an exclusion with no owner named comes back as a candidate on the next run. This is a signal the content ledger structurally cannot provide — the ledger knows what you shipped, not what Google did with it.

### 1e. Decay (refresh candidates)

```
compare_search_periods
  site_url: <gsc_site_url>
  period1_start/end: <the 90 days before last>
  period2_start/end: <the last 90 days>
  dimensions: "page"   limit: 25
```

Pages down **>30% in clicks or 3+ average positions** are refresh candidates. A refresh re-cuts an existing URL for a fraction of a new run's cost and answer engines reward the update, so a badly decaying page beats a mid-tier new candidate. Cross-check the `Refresh due` column in the ledger: a piece with stale original data **and** measured decay is the single cheapest high-value run available.

### 1f. Calibrate the difficulty bucket (free, do it every few weeks)

The same ranked-query pull answers *"which difficulty bucket do we actually play in?"* — the question that replaced the old `KD ≤ DR + 10` cap. Take the queries where you rank **page 1**, price them with `dataforseo_labs_google_keyword_overview` (up to 700 keywords in one call), and read off the hardest bucket holding 2+ page-1 positions. That's your playable bucket; store it in `.seo/config.json` under `difficulty`. Bucket boundaries and how to use them are in `research-recipes.md`.

This is the empirical answer, and it beats any DR heuristic because it's your own results. It also tells you when you've *moved up* — a site that keeps targeting the bucket it qualified for six months ago is leaving winnable keywords on the table.

### 1g. Save the query pull (every run, free)

The page pull in §2 is the dataset's backbone, but four panels need the query table joined to pages: the brand split (`measure.md` §3f), internal link opportunities (§3e), SERP features (§3d) and the competitor diff (§6d). Make one more call over the same 28-day window and save it verbatim:

```
get_advanced_search_analytics
  site_url: <gsc_site_url>
  start_date: <28 days ago>   end_date: <today>
  dimensions: "query,page"
  row_limit: 5000            # paginate on pagination.has_more
  sort_by: impressions   sort_direction: descending
```

Write it to `.seo/gsc/queries-<date>.json` in the same `{site_url, start_date, end_date, rows:[{keys:[query, page], clicks, impressions, ctr, position}]}` shape as the page pull. Search Console keeps 16 months; the saved file is the only copy older than that, and it is what lets `brand_split.py` show branded demand as a trend instead of a number.

---

## §2 — Measure what shipped (Step 1 Measure, the closed loop)

**One call covers the whole library. Do not loop per page.**

```
get_advanced_search_analytics
  site_url: <gsc_site_url>
  start_date: <90 days ago>   end_date: <today>
  dimensions: "page"
  row_limit: 1000            # paginate on pagination.has_more
  sort_by: impressions   sort_direction: descending
```

That returns clicks, impressions, CTR, and average position for every page on the site. Join it to the ledger's URL column locally. **A ledger row with no matching page row got zero impressions** — that is the invisible set, and it is the only set that needs URL inspection (§3).

Drill down per page only where the site-wide pull leaves a real question:

```
get_search_by_page_query
  site_url: <gsc_site_url>   page_url: <full URL>   days: 28   row_limit: 50
```

Use it to confirm a **wrong-query** piece (which queries did it actually attract?) and to read a **CTR gap** at query level. Two or three calls a run, not one per piece.

Classify each piece into one of four states and write the result back to the ledger's `Performance` table (date, clicks, impressions, best position, state). The ledger is the only memory between runs, so an unwritten measurement is a measurement that never happened.

| State | Read | Action |
|---|---|---|
| **Winning** | Ranks 1–5 for the target keyword, taking clicks | Nothing. Mine the vein — note which vein worked, it is a live signal for selection |
| **Close** | Position 5–15, impressions climbing | **Boost beats a new piece.** Offer it at the checkpoint |
| **Wrong query** | Gets impressions, but for queries the piece does not target | The angle missed. The queries it *did* attract are a free candidate list |
| **Invisible** | No impressions after 21+ days | Index problem first (§3), thin/mis-targeted second. Never write a sibling piece until you know which |

**Index status runs on a faster clock than this table.** Sweep anything published in the last 30 days and not yet confirmed indexed with `batch_url_inspection` (§3) — that is readable ~3 days after deploy, where performance needs three weeks. A piece that shipped `noindex` should be caught on day 4, not diagnosed on day 21 after two more runs were built on it.

### Read at fixed checkpoints, against a control

Two rules make rows comparable instead of anecdotal:

1. **Read at ~28 and ~56 days after publish** (or after a boost lands), not "whenever the skill next runs." A piece read at day 22 and again at day 90 produces two numbers that cannot be compared to any other piece's. Pin the checkpoints; note the actual read date in the row.
2. **Record site-wide clicks and impressions for the same dates**, in the same row. Without that control, a Google-wide lift reads as your edit working and a sitewide slump reads as your edit failing. `get_performance_overview` for the window costs one call, and it is the difference between measurement and flattering yourself.

State the delta both ways: *"+180 clicks at 28d; blog-wide was up 12% over the same window, so call it real but smaller than it looks."*

Then feed the aggregate back into selection. Three "invisible" pieces in a row on one vein is the engine telling you the vein is dead, and no amount of keyword-tool scoring will say that.

**Do not skip this because the last piece shipped an hour ago.** GSC lags 2–3 days and a new URL needs weeks. If nothing in the ledger is 21+ days old, say so in one line and move on to selection.

---

## §2b — First GSC run on an existing library (the backfill)

The common case: a repo that has been running this skill for months, with a full `Shipped` table, no `Performance` table, no `gsc.site_url`, and **zero measurement history on anything**. Every piece is unmeasured and unchecked at once.

Run the backfill **once**, before selection, and say what you're doing: *"First GSC-aware run here. You have 14 pieces with no measurement history, so I'm backfilling the scoreboard before picking anything — this changes what's worth writing."*

### The order

1. **Resolve and store the property** (§0). Add `gsc.site_url` to `.seo/config.json` **in that file's own shape.** Real configs drift hard from the template — nested `stack` objects, extra keys, different naming. Add the key where it fits the file you found; never reshape or reformat an existing config to match the template.
2. **Add a `## Performance` section to the ledger, in the ledger's own style.** Same drift applies, and worse: a months-old ledger will have renamed columns (`URL` not `Slug / URL`), dropped template columns, and added sections of its own (a "Considered, dropped, with reason" log is common and load-bearing). **Append the new section; never rewrite, reorder, or "normalize" what's there.** Match the file's existing column conventions and heading depth. Read the ledger's actual URL column name and join on that — do not assume the template's.
3. **One site-wide pull** (§2 above, 90-day window — longer than the steady-state 28 because you're establishing history, not watching a trend). **Join it in both directions:**
   - *Ledger row with no GSC row* → zero impressions. The invisible set, and the only set needing inspection.
   - *GSC page with no ledger row* → **content that exists and the ledger doesn't know about.** Extremely common on a months-old repo: pieces shipped by hand, by another skill, or by a run that never registered. Every one of these is a dedup hazard, because Step A's exclusion set is built from the ledger. Add them as `Shipped` rows (mark them backfilled, and honestly — you don't know their target keyword) before selecting anything.
   - *Subdomain pages you didn't expect* → a `sc-domain:` property covers every subdomain, so a marketing repo's pull will include `shop.` and `business.` pages that belong to other repos. Filter by page prefix before joining or the numbers describe a site you aren't writing for.
4. **Inspect only two sets** (§3): rows with **zero impressions**, and anything published in the last 30 days. On a 40-piece library that's usually 5–10 URLs, or one `batch_url_inspection` call. Never inspect the whole library because it's there.
5. **Run the meta hygiene sweep while you're here.** Grep every published page for a **missing, empty, or duplicated** meta title or description (file repos: the frontmatter or the layout's head; CMS/DB: the field map in `content-stores.md`). This is unglamorous and it is often the single highest-yield finding on an older library — a page ranking at position 6 with no description at all is losing clicks to a snippet Google wrote for it. Report the count, list the worst offenders by impressions, and offer to fix them as a batch. **A library where dozens of pages have empty SEO fields is not a content-volume problem, and shipping piece #15 into it is the wrong run.**
6. **Write every row**, then mark the section done (`Backfilled: <date>`) so later runs do the incremental sweep instead.

### What the backfill will turn up, and how to handle it

A first backfill on months of content surfaces a **pile** — decayed pages, wrong-query pieces, a cannibalized cluster, a couple never indexed. **Do not dump forty findings on the user.** The ledger absorbs the detail; the checkpoint gets counts plus the three most actionable items:

> *"Backfilled 14 pieces: 3 winning, 4 close (boost candidates), 2 wrong-query, 1 crawled–not-indexed, 4 no data. Biggest thing: [piece] sits at position 6.6 with 3,644 impressions and 3.3% CTR — a title rewrite is worth more than anything new on the slate."*

**Be willing to let the backfill cancel the run's original job.** If it turns up four boost candidates and an index problem, writing piece #15 is the wrong move and you should say so plainly. This is the one moment where the engine has months of unexamined feedback arriving at once, and it is usually worth more than the next new piece.

### Backfill-specific traps

- **GSC holds ~16 months.** Pieces older than that have no history and are not "invisible" — mark them `no-data (pre-window)` and move on.
- **A migrated slug is a ledger bug, not an index bug.** If a URL in the ledger 404s or redirects (site moved framework, slugs changed, a type prefix was introduced), inspection reports the redirect and the *new* URL holds the data. Fix the ledger row; don't file it as an indexing failure.
- **Check you matched the right property.** Sites often have several (`example.com`, `shop.example.com`, `business.example.com` as separate properties). A whole library reading as invisible almost always means the wrong property, not a dead site.
- **Pre-verification pieces have no data by definition.** If the property was verified after some pieces shipped, their early history does not exist. Say so rather than reporting a drop.
- **Zero impressions on a piece published four days ago is normal.** The 30-day inspection window catches it; the performance verdict waits.

---

## §2c — Size the boost: three levers, biggest one wins

A boost candidate that arrives as *"the CTR looks bad"* loses every argument against a new piece, because the new piece arrives with a traffic estimate. Fix that by **estimating the clicks each lever would return**, then comparing the winner against the new piece's projection. Same units, honest comparison.

Score every measured page on three levers and let the largest decide both whether to boost and **what kind of fix to write**:

| Lever | Estimate | The fix it implies |
|---|---|---|
| **Recover** | clicks in the prior 28-day window − clicks now (only when positive) | Something regressed. Find what changed: decay, a SERP-feature shift, a competitor's new page, an edit that backfired |
| **CTR** | `impressions × expected_ctr(position) − actual clicks` | Title + meta description rewrite. No new body content |
| **Rank** | `impressions × (expected_ctr(target_position) − expected_ctr(current))`, for a page-2 post reaching page 1 | Depth, entity coverage, internal links, information gain — a real content edit |

### The expected-CTR curve

**Derive it from your own GSC data, don't import a stranger's constants.** Pull `dimensions: "query"` over 90 days, bucket by rounded position, and average CTR per bucket. That curve reflects your SERPs, your brand strength, and the AI Overviews and SERP features that actually sit above your results. It's also a publishable first-party asset (§4).

Use this band table as the fallback when the site has too little data to bucket (fewer than ~30 queries per position band), and mark any estimate built on it as approximate:

| Position | Expected CTR |
|---|---|
| 1 | 28-32% |
| 2 | 14-17% |
| 3 | 9-11% |
| 4 | 6-8% |
| 5 | 5-6% |
| 6-10 | 2-4% |
| 11-15 | 1-2% |
| 16-20 | <1% |

Read it as arithmetic, not as a promise: a keyword at position 14 with 1,000 monthly impressions currently earns ~10 clicks/month, and at position 3 it would earn ~100 — a 10x return on one piece of work. These are ballpark figures from aggregate industry data, not measurements of your site. Brand queries run far higher, queries under an AI Overview run far lower, and a position-1 result below four ads is not a position-1 result. Treat a gap under ~2× as noise.

### Two honest caveats

- **Average position over-counts headroom.** A page at "average position 8" is often position 4 for its head term and 30 for a long tail, so the modelled gain from "reaching page 1" is optimistic. Re-pull borderline candidates by device and country (§5) before committing a run, and present the estimate as a range.
- **An estimate is not a promise.** Put the number on the checkpoint as *"~95 clicks/mo if the CTR closes to the positional norm"*, never as *"this will add 95 clicks."*

---

## §2d — Scope the boost: what a boost run actually changes

A boost is **not writing a new page.** It is amplifying one that already ranks, and it is usually 1-3 hours against 4-8 for a new page, on existing link equity, with measurable movement in 7-21 days. Front-load boosts over new pages whenever both are on the slate.

Skip a candidate when:

- Impressions are under ~50/month — not enough signal to act on
- The top 3 are all established sites with deep, well-optimized content — you won't displace them
- The page already carries 1,500+ words on the topic — it's out of easy depth-adds, so the lever is CTR or links, not more prose

### The four moves

1. **Add 200-400 words of depth** to the section where the target query appears. The amplifiers that work: an FAQ if one is missing (a `FAQPage` block is a featured-snippet magnet), a worked example inside a thin section, a counter-argument paragraph where the page is one-sided, a how-to subsection where the query is procedural.
2. **Add 3-5 new internal links pointing at the page.** The best sources: other pages already ranking for related queries (find them in the same `query,page` pull), sibling pattern pages, and recent long-form on the same topic.
3. **Rewrite the meta title and description** if the target query isn't prominent. Move the query toward the front of the title.
4. **Bump `lastmod`** to today so the recrawl picks up the edit. Use a content date, never a build date.

### Boost template

```markdown
### Boost /<existing-url> for "<target keyword>"

**Why:** currently position 14 for "<target keyword>" (vol 500, KD 18). Position 3 captures an
estimated +40 clicks/month from content depth plus 3 new internal links.

**Scope:**

1. Add a 250-word FAQ section answering "<related question>"
2. Add `FAQPage` JSON-LD covering the new FAQ
3. Add internal links from:
   - `/<related-page-1>` (anchor: "<anchor text>")
   - `/<related-page-2>` (anchor: "<anchor text>")
   - `/<related-page-3>` (anchor: "<anchor text>")
4. Rewrite the meta title to lead with "<target keyword>"
5. Bump `lastmod` to today

**Verification:**
- [ ] New FAQ section present (200+ words)
- [ ] `FAQPage` JSON-LD validates
- [ ] 3 new inbound links from named pages
- [ ] Meta title leads with the target keyword and is ≤60 chars
- [ ] Re-read position at 14 days (`compare_search_periods`)
```

### Re-run the sweep on a clock

GSC is a lagging indicator, so re-run the striking-distance pull every ~30 days. New queries enter position 5-20 every cycle as pages ship, and old ones either graduate to page 1 or fall off. **A query that was position 8 last month and is 12 now is a regression, not a boost candidate** — find out what changed (usually a competitor shipped something fresh) before spending a run on it.

Greenfield sites with no rankings have no striking distance to find. Skip the sweep and say so rather than reporting an empty result as a finding.

---

## §3 — Index verification

Performance data answers *"is it working?"* and needs weeks. Index status answers *"does Google even have it?"* and is readable in days. **They run on two different clocks, and conflating them wastes a fortnight** — a piece that shipped `noindex` by accident is diagnosable on day 4, and waiting until day 21 to look means the next two runs were built on a broken assumption.

| Check | Earliest useful | Cadence |
|---|---|---|
| **Index status** (this section) | ~3 days after deploy | Every run, on anything published in the last 30 days that is not yet confirmed indexed |
| **Performance** (§2) | ~21 days after deploy | Every run, on anything live 21+ days and unmeasured in 30 |

It needs a **live** URL, so it never applies to the piece written this run — that one is still on a branch. It applies to what is already deployed.

```
inspect_url_enhanced     site_url: <gsc_site_url>   page_url: <url>       # diagnosis, one URL
batch_url_inspection     site_url: <gsc_site_url>   urls: <up to 10>      # the routine sweep
check_indexing_issues    site_url: <gsc_site_url>   urls: <list>          # quick triage across a set
```

Use `batch_url_inspection` for the routine sweep of recent pieces, then `inspect_url_enhanced` on anything that comes back wrong, because the single-URL call carries the detail (canonicals, referring URLs, rich results) that names the fix.

### 3a. Read the verdict, then the coverage state

The MCP flattens Google's response to snake_case, so the keys you actually read are:

```json
{ "verdict": "PASS", "coverage_state": "Submitted and indexed", "last_crawled": "2026-08-24 17:43",
  "page_fetch_state": "SUCCESSFUL", "robots_txt_state": "ALLOWED", "indexing_state": "INDEXING_ALLOWED",
  "google_canonical": "https://…", "user_canonical": "https://…", "crawled_as": "MOBILE",
  "referring_urls": ["https://…"], "rich_results": null,
  "inspection_result_link": "https://search.google.com/search-console/inspect?…" }
```

`verdict` is `PASS` / `NEUTRAL` / `FAIL` — and **`NEUTRAL` means excluded, not "fine"**. `coverage_state` is a **human-readable string, not an enum**, and Google rewords it: match it loosely (substring, case-insensitive), never on exact equality. `rich_results: null` means none were detected. `inspection_result_link` opens the same inspection in the GSC UI, so put it in the hand-off whenever you report a problem — it saves the user finding the page themselves.

| What comes back | What it means | The actual fix |
|---|---|---|
| **"Submitted and indexed" / "Indexed, not submitted in sitemap"** | Live in the index | Nothing. If it is not in the sitemap, that is a sitemap bug worth one line in the hand-off |
| **"URL is unknown to Google"** | Never discovered | A **discovery** problem, not a quality one. Is it in the sitemap? Does it have the ≥2 internal inbound links this skill requires? Read `referring_urls` — that is Google's own list of the links it found pointing at the page, and it is the only real audit of the orphan gate. Fix the links, then submit the sitemap |
| **"Discovered – currently not indexed"** | Known, not crawled | Crawl priority. More words will not help. Link to it from higher-authority existing pages (the homepage, the hub, the best-performing post) |
| **"Crawled – currently not indexed"** | Google looked and declined | **The damning one, and the most important signal in this file.** It is a quality or duplication verdict on the piece. One is a miss; three on the same vein means the vein itself reads as low-value and the engine must stop writing into it. Never ship a sibling piece into this state |
| `indexing_state: BLOCKED_BY_META_TAG` / `BLOCKED_BY_HTTP_HEADER` | `noindex` in the meta tag or `X-Robots-Tag` | A config bug and the fastest win here. Usually a CMS draft default, a staging header that shipped, or this skill's own per-entity `noindex` rule applied one level too broadly. Fix the template |
| `robots_txt_state: DISALLOWED` | robots.txt blocks the crawl | A `/tools` or `/blog` path caught by a broad disallow. Fix robots.txt |
| `page_fetch_state` ≠ `SUCCESSFUL` | Google could not fetch it | `SOFT_404` on a real page usually means a JS-rendered shell with no server-side content. `REDIRECT_ERROR` and `SERVER_ERROR` are infrastructure, not content |
| **`google_canonical` ≠ `user_canonical`** | Google folded this page into a different one | Cannibalization, confirmed at the source. The page can read as "indexed" and still earn zero impressions forever, so this is invisible in the performance report. Either differentiate the two pages hard, or consolidate. It also means writing anything adjacent will fold too |

### 3b. Confirm the schema actually registered

Inspection reports the **rich results Google detected**. That is Google's own parse, which outranks `tech_audit.py`'s local one: local validation proves the JSON-LD is well-formed, this proves Google accepted it. Use it on earlier pieces to confirm the `FAQPage` / `HowTo` / `SoftwareApplication` block the skill emitted did register. Silence here on a piece that shipped schema is a real finding.

### 3c. Sitemap health, when discovery is the problem

```
list_sitemaps_enhanced   site_url: <gsc_site_url>      # errors, warnings, last downloaded
```

If the sitemap has not been downloaded in weeks, or throws errors, nothing new on the site is being discovered on schedule, and that outranks every content decision this run. Say it at the checkpoint.

### 3d. Quota and etiquette

Google caps URL Inspection at **2,000 queries per day and 600 per minute, per property** (10M/day per project). Generous for this skill's use, and still not a licence to sweep a 5,000-page site: inspect **recent pieces and the invisible ones**, not the whole library. Batch ten at a time.

Never call `manage_sitemaps` delete, `add_site`, or `delete_site` from this skill. Submitting a sitemap after adding a `/tools` hub is reasonable, but ask first.

### 3e. The stop rule

Index checks are not a ship gate — the piece being written this run has no URL to inspect. They are a **loop gate**. Ship gates protect the quality of one piece; this protects the assumption the whole engine rests on, which is that publishing puts pages in the index.

So: **if the last three published pieces are not indexed, the next run's job is not a fourth piece.** Say that plainly, name the state, and fix the cause. Writing more into a site Google is declining to index is the single most expensive way this skill can fail, because every run looks productive and none of it exists.

---

## §4 — GSC as first-party data (information gain)

GSC query data is **your own data**, which makes it a legitimate original-data source under `proprietary-data.md`. It is often the fastest real number in the building and it needs no database access.

Shapes that work:

- **Demand distribution** — "Across N queries that reached our site over 90 days, X% were phrased as questions." One pull, real number, nobody else can publish it for your niche.
- **The CTR-by-position table for your own space** — every article on the internet cites the same 2019 third-party CTR study. Yours is current, first-party, and dated.
- **Query-language evidence** — how real people phrase a thing, drawn from queries rather than from a keyword tool's cleaned corpus. Strong for definition and how-to pieces.
- **The missing dimension** — cross your GSC demand curve with a public dataset per `proprietary-data.md` §3.

The same contract applies: aggregates only, n ≥ 50 per published cell, date every figure with its window and as-of date, and state the population honestly ("across N queries reaching [site] between [dates]", never "across the industry"). GSC query rows are already anonymized by Google, so PII risk is low, but the honest-population rule is not optional — a single-site GSC sample is a single-site sample.

---

## §5 — Traps

Every one of these has produced a confidently wrong conclusion.

- **Average position is an average.** A query at "position 8" can be 3 on desktop and 18 on mobile. Before acting on a borderline striking-distance row, re-pull it with `dimensions: "query,device"` or `"query,country"`. A US-position-6 query that reads as 14 because of international impressions is a different piece of work than it looks like.
- **Missing queries are normal.** Google drops rare queries for privacy, so per-query clicks never sum to site totals. Never present a query-level total as a site total.
- **Data lags 2–3 days.** `data_state: "all"` (default) matches the GSC dashboard and includes fresh partial data. `"final"` is confirmed only. Use `"final"` for anything you publish as a number, `"all"` for exploration.
- **There is no position filter.** Filter positions after the fetch. Sending an unsupported filter dimension throws or silently returns nothing.
- **Row limits.** `get_advanced_search_analytics` goes to 25,000 with `start_row` pagination; the simpler tools cap at 500. Read `pagination.has_more` in the response instead of assuming a pull was complete.
- **`sc-domain:` covers subdomains.** Docs, app, and marketing subdomains land in the same property. Filter by page when the repo is only one of them, or the numbers describe a site you are not writing for.
- **GSC only knows queries you already appear for.** It cannot see a keyword you have never ranked for, has no volume or KD for the open market, and knows nothing about competitors. Combine it with DFS; do not substitute it.
- **Correlation is not the piece.** A page's clicks rising the month after you shipped a sibling article is not proof the sibling caused it. Report what changed and by how much, and leave the attribution honest.

---

## §6 — Fast reference

| Need | Call |
|---|---|
| Exact property string | `list_properties` |
| Striking distance, unowned demand, cannibalization | `get_advanced_search_analytics` (`query,page`, 90d, filter locally) |
| Per-page query list, CTR gap read | `get_search_by_page_query` |
| Site snapshot for the foundation baseline | `get_performance_overview` |
| Decay detection | `compare_search_periods` (`page`, 90d vs prior 90d) |
| Device or country split on a borderline query | `get_advanced_search_analytics` (`query,device` / `query,country`) |
| Is it indexed, does the schema register | `inspect_url_enhanced`, `batch_url_inspection` |
| Why a new piece is not being discovered | `list_sitemaps_enhanced` |
| Which pages Google crawls often (pick inbound links from these) | `batch_url_inspection` → read `last_crawled`, cache as `crawl_hubs` (§7a) |
| Getting the piece you just shipped indexed faster | §7 — it's decided pre-deploy, not by anything you push after |
| Scoping the boost once you've picked one | §2d — depth, links, meta, `lastmod` |
| Bing clicks, and Bing's AI citations | §8 — separate panel, never summed with Google |

---

## §7 — Get new content indexed faster (ship-time)

Indexing speed is mostly decided **before** you deploy, by discoverability and page posture — not by anything you can push afterwards. The levers below are ordered by real effect. Everything in §7b is folklore or officially unsupported; don't spend a run on it.

### 7a. What actually works

**1. Link from pages Google crawls often — this is the biggest lever.** The skill already requires ≥2 inbound internal links. Upgrade the rule: **at least one must come from a page Google visits frequently.** Two links from posts that get crawled quarterly is close to no discovery signal at all; one link from the homepage or a top-traffic hub is discovery within days.

You can now measure this instead of guessing. Batch-inspect your top-traffic pages once and read `last_crawled`:

```
batch_url_inspection   site_url: <gsc_site_url>   urls: <top 10 pages by clicks>
```

Cache the frequently-crawled ones in `.seo/config.json` as `crawl_hubs` and reuse them every run. Re-derive every few months. When you ship a piece, one of its inbound links comes from that list.

**2. Verify the sitemap entry, don't assume it.** The new URL must be in the sitemap source with a `lastmod` of today. On generated sitemaps this is a manual edit that gets forgotten (a Next.js `app/sitemap.ts` with a hand-maintained `ROUTES` array is the classic case, and the repo's own config often documents the step). Check the file, not your memory of having done it.

**3. Ship the page crawlable and self-canonical.** Four checks on the dev server, each cheap, each silently costing weeks when wrong:

- **Server-rendered body text** — `curl -s localhost:<port>/<path> | grep "<a distinctive sentence>"`. A JS-only shell is what produces `SOFT_404` and long delays.
- **Canonical points at itself**, not at the layout's default or the homepage. A template-inherited canonical is why a page can look fine and never index as itself.
- **No inherited `noindex`** in the rendered head or headers — CMS draft defaults and staging `X-Robots-Tag` rules both leak into production.
- **200, not a redirect chain.**

**4. After deploy, use the one sanctioned accelerant.** GSC's **Request Indexing** (in URL Inspection) is the only Google-supported way to push a single ordinary page, and it is UI-only and daily-quota-limited. The MCP already hands you `inspection_result_link` from any inspection — that deep-links to the exact page with the button on it, so **put the link in the hand-off** rather than telling the user to go find the URL in Search Console.

**5. Submit a sitemap only when it's genuinely new.** `manage_sitemaps` submit is worth calling when the run *created* a sitemap (a `/tools` sitemap shipping with the first tool). Resubmitting one Google already has does not speed anything up. Ask before submitting either way.

**6. IndexNow is Bing-family, not Google.** Participating engines per indexnow.org are **Bing, Yandex, Naver, Seznam, Amazon, and Yep — Google does not participate.** It's one HTTP GET plus a key file. Worth mentioning once if answer-engine coverage matters to the user (some AI answer surfaces draw on non-Google indexes); ignore it if the goal is Google rankings. Not something this skill sets up on its own.

### 7b. What does not work

- **The Google Indexing API.** Google documents it as usable "only to crawl pages with either `JobPosting` or `BroadcastEvent` embedded in a `VideoObject`." Using it for articles is unsupported. Don't build it in and don't recommend it, whatever a blog post claims.
- **Re-requesting indexing on the same URL.** It doesn't stack.
- **Ping services and auto-submit directories.** Google retired its own sitemap ping endpoint; third-party pingers were never a signal.
- **Publishing more to "build crawl budget"** on a site that isn't indexing what it already has. That's the §3e stop rule, and it's the most expensive mistake available here.

### 7c. The precondition

If `list_sitemaps_enhanced` shows the sitemap hasn't been fetched in weeks, or recent pieces aren't indexing, **none of 7a helps** and fixing that is the run's real job. Say so at the checkpoint instead of shipping into a site Google isn't reading.

---

## §8 — Bing Webmaster (optional second panel)

Google is not the only index that feeds an answer engine. Copilot and several AI surfaces draw on Bing, so where a Bing Webmaster API key exists it is worth a small, separate read. Treat it as optional: absent is the normal case, and nothing in this skill blocks on it.

Configure it once in `.seo/config.json` under `bing` (`api_key_env` naming the environment variable that holds the key, plus `site_url`). Never hardcode the key.

The API is plain JSON over HTTPS, one endpoint per report, key on the query string:

```
https://ssl.bing.com/webmaster/api.svc/json/GetQueryStats?apikey=<key>&siteUrl=<site>
https://ssl.bing.com/webmaster/api.svc/json/GetPageStats?apikey=<key>&siteUrl=<site>
https://ssl.bing.com/webmaster/api.svc/json/GetRankAndTrafficStats?apikey=<key>&siteUrl=<site>
```

- **`GetQueryStats`** — impressions, clicks, average position per query. The Bing analogue of §1.
- **`GetPageStats`** — the same per URL. The Bing analogue of §2.
- **`GetRankAndTrafficStats`** — the site-level trend, useful as the control series when reading a delta.

**The AI Performance report — citations and grounding queries — is UI-only today.** There is no API for it. If the user cares about AI citations from the Bing family, the honest instruction is to read it in the Bing Webmaster Tools UI and paste the numbers; do not synthesize them, and do not claim coverage the API can't provide.

**Record Bing and Google as separate panels, and never sum them.** They index different corpora, sample and round differently, and define "position" differently; one added total is a number with no referent. Report *"Google: 412 clicks / Bing: 38 clicks"*, never *"450 clicks."* When the two disagree about a page, say so — a page indexed in one and not the other is itself the finding.
