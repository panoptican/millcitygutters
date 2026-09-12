# Tools: the capability registry

<!-- new in v2.2; the one place that maps what the skill needs to what a host provides -->

This skill is written for any agent host. Every reference names a *capability* and, where a recipe needs it, the *endpoint or tool name* of the vendor that provides it. It never names a host-specific wrapper. If your host exposes these vendors under different names (an MCP server prefix, a CLI, a plain HTTP client), map them here once and read the rest of the skill as written. Every capability has a fallback, and a missing tool is labelled in the run record, never silently skipped and never reported as clean.

`setup.md` is the companion: what each connection unlocks, in value order, and the report the first run prints.

## Data capabilities

| Capability | Vendor and the names used in this skill | Underlying API | Fallback |
|---|---|---|---|
| **Own-site search truth** | Search Console: `list_properties`, `get_advanced_search_analytics`, `get_search_by_page_query`, `get_performance_overview`, `compare_search_periods`, `inspect_url_enhanced`, `batch_url_inspection`, `check_indexing_issues`, `list_sitemaps_enhanced`, `manage_sitemaps`. These are the tool names of the common Search Console MCP server; any client works. | Google Search Console API: `searchanalytics.query`, `urlInspection.index.inspect`, `sitemaps.*`, `sites.list` | Paste a Search Console export into `.seo/gsc/<date>.json` in the documented shape. |
| **Bing** | Bing Webmaster API key in the env var named by `config.bing.api_key_env` | Bing Webmaster REST: `GetQueryStats`, `GetPageStats`, `GetRankAndTrafficStats` | Skip the panel and say so. |
| **Market data, SERP, backlinks, AI mentions, trends, historical volume** | DataForSEO. Endpoints are named by their DataForSEO API name throughout (`serp_organic_live_advanced`, `backlinks_backlinks`, `dataforseo_labs_google_ranked_keywords`, `ai_optimization_llm_response`, `content_analysis_search`, `kw_data_google_trends_explore`, `dataforseo_labs_google_historical_keyword_data`, and so on). | DataForSEO v3 REST, same names | `research-recipes.md` "No keyword tool": live SERP reads through web search and page fetches, precision drops, capability does not. |
| **Answer-engine responses** | DataForSEO `ai_optimization_llm_response` with `web_search: true` | same | The host model with web search, sampled and labelled as such. |
| **Site crawl, audit, rank tracking, GA4 outcomes** | OpenSEO: `run_site_audit`, `get_audit_issues`, `get_audit_pages`, `get_search_opportunities`, `create_rank_tracker`, `get_rank_tracker`, `get_google_analytics_site_search`, and the other `get_google_analytics_*` reads | OpenSEO API | `scripts/crawl_check.py`, `scripts/health_diff.py`, `scripts/depth_check.py`; outcomes reported as "not connected", never zero. |
| **Page speed** | DataForSEO `on_page_lighthouse`, or PageSpeed Insights with the key named by `config.speed.psi_api_key_env`, or a local `lighthouse` CLI | Lighthouse | Recorded as unchecked. |
| **Design references for tools** | Any UI-pattern search the host has (a screenshot library such as Mobbin) | — | Skip the recon; the tool-UX critic still runs. |
| **Server logs** | The path in `config.logs.path` | — | AI-crawler evidence from Search Console alone, labelled. |
| **Community and social demand** | A community-search skill, if installed: one that returns dated, ranked Reddit, Hacker News, X or YouTube threads for a topic. | — | Web search with `site:reddit.com/r/<community>` and `site:<forum>` restricted to the last month (`demand-radar.md` §2). |
| **Social posting** | A social-media posting skill, if installed: one that drafts per-channel copy for the product's own accounts and schedules it after the user approves. Named in `config.distribute.social_skill`. | — | A social brief in `.seo/briefs/<slug>-social.md` and a `needs-you.md` row. |
| **Library documentation** | A documentation lookup tool, if the host has one, for code-block provenance | — | The library's own docs site, fetched. |

## Host capabilities

| Capability | What the skill does with it | Without it |
|---|---|---|
| **Ask the user a structured question** | The interactive checkpoint in `select.md` §6, the brand interview, the ambiguous-surface confirmations. One question, options carried in full. | Ask in plain text and wait. Unattended: take the documented default and log it in the run record. |
| **Subagents** | Research fan-out, the critic panel, the census by seed. Every spawned agent is a leaf: it spawns nothing and leaves no background process. | Run the same passes sequentially. Same coverage, slower. |
| **Web search** | SERP teardowns, community search, source finding. | A search engine in the browser, results pasted. |
| **Page fetch** | Reading competitor and source pages as text. | `curl`, with a note that JavaScript was not rendered. |
| **Headless browser** | Rendering checks and screenshots for tools and fixes. | `curl` plus a note that the page was not rendered; a tool never ships without a screenshot, so a human takes it. |
| **Temporary directory** | Raw API responses before normalisation. | Any directory outside the repo. |
| **Shell and Python 3** | Every script in `scripts/` is standard-library Python. | Required. There is no fallback for the scripts. |

## Rules

- Name the capability in prose and the vendor endpoint in recipes. Never a host wrapper.
- A capability that is absent is written in the run record's `Unchecked` line with the reason.
- Cost policy for metered vendors is in `research-recipes.md`; it applies whatever client makes the call.
