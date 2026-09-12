# Demand radar

<!-- new in v2.1; the outside-in half of candidate generation -->

Everything else in the measure step looks inward: our pages, our queries, our claims. The radar looks outward at what the ideal customer is talking about right now, in the places they actually talk, and turns that into create and refresh candidates that already carry the demand provenance `select.md` requires. Without it the skill only ever finds demand near keywords it already has, and the site slowly becomes an archive of last year's questions.

The radar is cheap enough to run daily in its free tier and is the main source of *new* topics. It is not a news feed. A signal is only a candidate when the product is the answer, or when the audience's question is one we can answer better than whoever ranks today.

## Contents

1. What counts as a signal
2. Sources, cheapest first
3. Running the radar
4. From signal to candidate
5. State
6. Guards

## 1. What counts as a signal

A signal is a thing the ideal customer said, asked, or reacted to in the last 30 days, with a URL and a date. Four kinds, in order of value:

| Kind | Example | Why it ranks first |
|---|---|---|
| Asked | A Reddit or forum thread where someone asks how to do the thing our product does, in their own words | It is the query before it becomes a keyword. Answer it and you own the term when it does. |
| Complained | A thread or review venting about the incumbent way of doing it | Tells you the fear the one-fear page factory should descend from. |
| Reacted | A news event, rule change, product launch, or recall that the audience is discussing | Demand exists for about six weeks; the page that is live in week one owns it. |
| Trending | A query rising in Google Trends or YouTube for a seed topic | Confirms the first three with volume direction. Weakest alone, because it has no words. |

A signal that names our product or a competitor also goes to the AEO lane's mention inventory, but that is a side effect, not the purpose.

## 2. Sources, cheapest first

All optional. Run what exists, label what did not.

| Tier | Source | How | Cost |
|---|---|---|---|
| Free, daily | Search Console new queries | `compare_search_periods` on the last 28 vs prior 28; queries with impressions now and none before. This is the cheapest fresh-demand signal on earth and the old skills only used it for page classification. | none |
| Free, daily | Reddit, Hacker News, and the open web | A community-search skill, if the host has one installed (`tools.md`): invoke it with each seed topic and take its dated, ranked threads with engagement. Follow that skill's own contract. Without one, the community-search row below is the whole free tier. | free tier |
| Free, daily | Community search | web search with `site:reddit.com/r/<community>` and `site:<forum>` per `config.radar.communities`, restricted to the last month. | none |
| Cheap, weekly | News and blog mentions | `content_analysis_search` per seed with a `date_from` of 30 days ago; `content_analysis_phrase_trends` for the direction. | cents per call |
| Cheap, weekly | Trends | `kw_data_google_trends_explore` for the seeds and the top three asked-phrases; rising related queries are the output. | cents per call |
| Cheap, weekly | Video demand | `serp_youtube_organic_live_advanced` per seed. Recent uploads with high views on a question-shaped title are demand with a date. | cents per call |
| Cheap, monthly | AI mentions | `ai_opt_llm_ment_search` for the seeds, to see which topics answer engines are already being asked about. | per call |
| Free, weekly | On-site search | `get_google_analytics_site_search` for the last 30 days when GA4 is connected (`config.cadence.site_search_hours`). A query with zero results, or results and no click, is an `asked` signal in the visitor's own words, with `source: site-search` and the site as the URL. These people were already on the site and could not find the answer; they are the warmest demand the radar sees. | none |
| Free, monthly | Competitor gains | `competitor_diff.py` (measure.md §6d) keywords a competitor gained where we have no Search Console row. They enter here as seeds, not candidates, because a competitor ranking is not a person asking. | none |

Seeds come from `config.radar.seeds` (five to fifteen short topic phrases in the audience's language, not product names) and `config.radar.communities` (subreddits, forums, groups where the ideal customer talks). Foundation collects them; the radar refines them by adding any seed that produced three or more signals in a month and retiring any that produced none in three months.

## 3. Running the radar

Daily: the free tier, every seed, in one fan-out (one subagent per seed, or one community-search invocation per seed). Weekly, or when `config.radar.cadence_days` says so: the cheap tier. The preflight rule applies to the cheap tier: state the call count before spending.

Each source returns a list. Normalize to:

```
- date: YYYY-MM-DD
  kind: asked | complained | reacted | trending
  source: reddit | hn | x | youtube | news | trends | gsc | forum | site-search | competitor
  url:
  quote: the question or complaint in the poster's words, under 200 chars
  engagement: upvotes, comments, views, or impressions, as a number
  seed: which seed produced it
```

Dedupe against `.seo/radar.md` (§5) so a thread seen yesterday is not proposed again.

## 4. From signal to candidate

Cluster signals by the underlying job (three threads asking the same thing are one intent, not three). For each cluster with two or more signals, or one signal with high engagement:

1. **Intent owner check.** Does the ledger coverage map already have an owner URL for this intent? If yes, the candidate is a `refresh` of that page with a new section that answers the fresh question, dated. A refresh on a page that already ranks beats a new page nine times out of ten, and it keeps one owner per intent.
2. **Answer owner check.** Who is the answer to this today? If the product or our content can be, continue. If a government, hospital, or news outlet owns it and the product has no angle, drop it. Record the drop in the run record so the next run does not re-derive it.
3. **Fit check.** Against `brand.md`'s "who we are for" and "not for", and the forbidden-claims list. A trending topic that does not touch the audience's job is noise, whatever its volume.
4. **Type.** Reacted signals become a dated explainer or a section on the owner page. Asked signals become a how-to or definition. Complained signals feed the one-fear generator in the programmatic lane or a comparison. Trending alone never becomes a page by itself; it only raises the score of a candidate the other kinds produced.
5. **Emit** a `create-editorial` or `refresh` candidate with `demand` set to the best signal URL and quote, `freshness` scored 5, and `movement` estimated from engagement and any GSC or Trends number. Reacted signals expire: if not executed within 21 days, drop them from the pool and note it.

## 5. State

`.seo/radar.md`, from `assets/radar-template.md`. Two tables:

- **Signals**: date seen, kind, source, url, quote, engagement, seed, status (`proposed` | `used:<slug>` | `dropped:<reason>` | `expired`).
- **Seeds**: seed, communities, signals in last 30 days, last hit, status (`active` | `retired`).

Keep it under a few hundred rows by pruning `dropped` and `expired` rows older than 90 days. This file is what makes the radar cumulative rather than a daily rediscovery.

## 6. Guards

- Recency is a score input, not an override. A fresh signal still loses to a truth contradiction or a broken redirect.
- Never quote a private individual's post verbatim on a public page, and never attribute a quote by handle. Paraphrase the question; cite the thread as a source only when it is a public community and the paraphrase carries no identifying detail.
- No first-party data from the product's private records is ever a "signal." The radar reads the public web only.
- A signal is evidence that people asked, not evidence that the answer is safe to give. Medical, legal and financial answers still go through the fix lane's citation rules and the brand's reviewer policy.
- Three seeds producing nothing for a month is information. Retire them and write it down rather than widening the search until something matches.
