# Setup: connections and what they unlock

<!-- new in v2.2; read on the first run, on `/seo setup`, and whenever detection changes -->

The skill runs with whatever is connected and labels what is not. That is the right behaviour for a daily operator, and the wrong behaviour for a first run, because a user who only ever sees "backlinks: unchecked" never learns that one free connection would have turned on half the measure step. This file is the guide: what each connection is, what it unlocks in this skill's own terms, what the skill does without it, and how to connect it. `tools.md` is the registry of names; this is the sales pitch, honest.

## When to show it

- **First run on a repo** (foundation created this run): the foundation checkpoint (`foundation.md` §9), which already stops once for the brand, shows what is connected and the top three missing connections, and asks whether to connect anything before the run continues. A connection made there is detected again on the spot and used by the first measurement. The full report below then goes in the final message, after "How the run ended". Never a second stop, never a wizard.
- **Every later run**: one line in the final message naming the missing connections that would add the most, until each is declined: `Running without DataForSEO and GA4. Say "skip DataForSEO" to stop seeing this, or run /seo setup for what they unlock.`
- **Detection changed** since the last run (a connection appeared or disappeared): the full report again, once.
- **`/seo setup`**: the full report and nothing else. No measurement, no run record beyond a one-line note.
- **Declined**: when the user says to skip one, write it to `config.tools_declined` with the date and never raise it again unless the user runs `/seo setup`.

## Detection

Fill `config.tools_detected` every run; it is free. `true` means the capability answered a real call this run or the last one, not that a tool with that name exists.

| Key | How to detect |
|---|---|
| `gsc` | `list_properties` returns a property matching `site.domain` |
| `dfs` | any DataForSEO endpoint is callable (a `serp_locations` or `backlinks_bulk_ranks` call with the domain) |
| `openseo` | `list_projects` answers |
| `ga4` | OpenSEO `get_google_analytics_organic_overview` returns rows, or `ga4.property_id` is set and answers |
| `bing_webmaster` | the env var in `bing.api_key_env` is set |
| `psi` | the env var in `speed.psi_api_key_env` is set, or a `lighthouse` CLI is on the path, or DataForSEO is connected |
| `logs` | `logs.path` is set and readable |
| `community_search` | a skill is installed whose description says it returns recent Reddit, Hacker News, X or YouTube threads for a topic |
| `social_posting` | a skill is installed whose description says it drafts or schedules social posts; record its name in `distribute.social_skill` |
| `browser` | the host has a headless browser or screenshot tool |
| `git` | `git rev-parse --is-inside-work-tree` |
| `python3` | `python3 --version` |

## The connections, in order of what they add

Each entry: what it unlocks here, what happens without it, how to connect, what it costs.

### 1. Google Search Console

**Unlocks:** the whole inward half of measurement. Per-page states (winning, close, wrong-query, invisible, decaying, unindexed), striking-distance and CTR-gap candidates, index status per URL, the census verdicts (keep, refresh, merge, prune), the outcomes loop and the priors that make the rubric learn, the branded split, internal link opportunities, the top-query list for the SERP panel, and the demand radar's cheapest signal (new queries). Free, and the only ground truth about your own site.

**Without it:** the skill sees the site only from outside. No verdict can say "this page is close", no action can be scored afterwards, the census can only judge health and word count, and every `create` candidate has to get its demand evidence from a thread instead of a query row.

**Connect:** verify the site in Search Console (a domain property is best). Give the host a Search Console client, usually an MCP server authenticated with a Google account that has at least Full user access to the property. Then run `/seo setup`; the skill stores the exact property string.

### 2. DataForSEO

**Unlocks:** market volume and difficulty, live SERP reads (which decide content type and now feed the SERP-feature and AI Overview theft panel), backlinks (summary, spam score, new and lost, reclamation and inbound-404 candidates), the answer-engine panel through `ai_optimization_llm_response`, AI mention research, Google Trends, historical volume for the seasonality bonus, competitor ranked-keyword gains, and Lighthouse. Nine of the measure panels and every off-page candidate depend on it.

**Without it:** manual-research mode (`research-recipes.md`): SERPs read through web search, no volume numbers, no backlink panel, no seasonality, the answer-engine panel sampled through the host model and labelled as such.

**Connect:** a DataForSEO account (dataforseo.com, pay-as-you-go) and their MCP server or any HTTP client the host can call. **Cost:** cents per call. The skill preflights every paid call, caches market data for 30 days, and caps unattended spend at `config.budget.per_run_usd` (default $2).

### 3. Google Analytics 4

**Unlocks:** the `converting-nothing` page state (traffic that never activates), AI referral attribution (how much traffic and how many signups came from ChatGPT, Perplexity, Copilot, Gemini, Claude), and on-site search queries as radar signals (what visitors searched for and did not find). Without an outcome metric every AEO action's value is a guess.

**Without it:** activation is never measured, AI referrals print as "not measured", and the distribute lane cannot show that a push did anything.

**Connect:** through OpenSEO (below), which bridges a GA4 property, or any GA4 client the host has. Free.

### 4. OpenSEO

**Unlocks:** a real site-wide crawl (orphans and broken links a sitemap walk cannot see), rank tracking with true positions rather than Search Console averages, a site audit with issue lists, the GA4 bridge above, and project memory across runs.

**Without it:** `crawl_check.py`, `health_diff.py` and `depth_check.py` cover the sitemap-visible half; nothing tracks rank; GA4 needs another route.

**Connect:** an OpenSEO account and its MCP server. It can be self-hosted. **Cost:** credits per crawl and per tracked keyword; the skill asks before a batch over 2,000 credits.

### 5. Bing Webmaster Tools

**Unlocks:** the Bing panel, which is the only programmatic view of Copilot's grounding. On one site Bing produced more clicks over three months than Google did in a month.

**Without it:** the panel is skipped and Copilot is measured only through the paid answer-engine panel.

**Connect:** verify the site at bing.com/webmasters, generate an API key in settings, export it as an environment variable, and put the variable's name in `config.bing.api_key_env`. Free.

### 6. A community-search skill

**Unlocks:** the demand radar's best source: dated, ranked Reddit, Hacker News, X and YouTube threads where the ideal customer asked the question in their own words. This is where new topics come from, and it is the `demand` provenance every create candidate needs.

**Without it:** the radar falls back to `site:reddit.com` web searches, which work but miss engagement and recency ranking.

**Connect:** install any skill that searches recent community discussion for a topic. The skill detects it by description. Free tier is enough.

### 7. A social-media posting skill

**Unlocks:** the social step of the distribute lane. A fresh piece gets per-channel drafts for the product's own accounts, held for your approval.

**Without it:** the lane writes a social brief to `.seo/briefs/` and asks you to post.

**Connect:** install any skill that drafts and schedules posts, and put its name in `config.distribute.social_skill`.

### 8. Server or CDN logs

**Unlocks:** AI crawler evidence (which agents fetch which pages, how often), AI referral clicks when GA4 is absent, and 404s with referrers (inbound links landing on dead URLs, a repair candidate).

**Without it:** AI-crawler reachability rests on Search Console and the free snapshot scripts alone.

**Connect:** set `config.logs.path` to a readable access log (combined format or JSON lines) and `config.logs.format`. Free.

### 9. PageSpeed Insights key or a local Lighthouse

**Unlocks:** Core Web Vitals (LCP, INP, CLS) on the top pages weekly, and before-and-after proof on speed repairs.

**Without it:** DataForSEO's Lighthouse endpoint if connected; otherwise speed is time-to-first-byte and HTML weight only, and CWV prints as unchecked.

**Connect:** a free PageSpeed Insights API key in the env var named by `config.speed.psi_api_key_env`, or `npm i -g lighthouse`.

### 10. A headless browser

**Unlocks:** rendered checks on fixed pages and the screenshot a free tool must have before it ships.

**Without it:** `curl` plus a note that JavaScript was not rendered, and a tool build stops at "needs a human screenshot".

**Connect:** whatever browser automation the host offers.

### 11. Subagents

**Unlocks:** speed. Research fan-out, the critic panel and the radar run in parallel.

**Without it:** the same passes run one after another. Same coverage.

## The report

Printed in the final message, in this shape, in the reader's terms. Never a table of booleans.

```
Connections

Connected: Search Console (sc-domain:example.com) · git · Python 3 · headless browser.

Not connected, in the order they would add the most:

1. DataForSEO. Market volume, live SERP reads, backlinks lost and reclaimed, the answer-engine
   panel, seasonality, competitor keyword gains. Without it nine measure panels are skipped and
   research is by hand. Pay-as-you-go, cents per call, capped at $2 a run unattended.
   Connect: an account at dataforseo.com and its MCP server.
2. Google Analytics 4 (through OpenSEO). Whether organic and AI traffic ever signs up, and what
   visitors search for on the site and cannot find. Free.
3. Bing Webmaster. The only programmatic view of Copilot. Free: verify the site, create a key,
   set BING_WEBMASTER_KEY.
4. A community-search skill. Where new topics come from. Free.

Say "skip <name>" for any of these and it will not be raised again. /seo setup prints this list anytime.
```

Keep the order by value for *this* site: a site with no Search Console connection puts it first; a site with no content yet ranks the community-search skill above GA4. One sentence of what it unlocks, one of the cost, one of how to connect. No more.
