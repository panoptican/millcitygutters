<!-- sources: aeo/references/audit.md (verbatim; state + reference paths remapped to .seo/) -->
# Phase 2: Measure

Four independent streams. Run them in parallel if your harness supports subagents, otherwise sequentially. Coverage is identical either way.

Output of this phase: `.seo/aeo/runs/<date>/` holding raw evidence, and `.seo/aeo/scoreboard.md` holding the rollup.

Expect three things, because they happen almost every time. There are more attributes to check than the team assumed. Visibility is lower than the team assumed, often much lower on core category terms. And you are strong somewhere nobody thought to track, which is usually a product or positioning insight wearing an AEO costume.

---

## Storage layout

Set this up before the first call. Raw evidence is the asset. Rollups can always be recomputed; a discarded response cannot be recovered, and the response text is what the Quoted gate depends on.

```
.seo/aeo/runs/2026-08-26/
  meta.json          run config: platforms, models, sampling plan, tool versions, start and end time
  responses.jsonl    one line per response: prompt id, platform, model, sample index, full text, citations, brands found
  citations.json     tallied cited domains and URLs, per attribute and per brand
  crawl.json         per-page output of crawl_check.py
  robots.json        output of robots_check.py
  logs.json          output of log_parse.py
  factcheck.json     each truth-file claim, what each platform said, and the verdict
```

`responses.jsonl` line shape:

```json
{"prompt_id":"disc-crm-agency-01","platform":"chat_gpt","model":"gpt-...","sample":1,
 "text":"...full response...","citations":["https://...","https://..."],
 "brands":["Brand A","Brand B","Brand C"],"self_mentioned":true,"self_position":3}
```

`self_position` is the ordinal position of your brand in the list the response returned, when the response returned an ordered list. Absent when it did not. It is a softer signal than mention rate and worth recording, because moving from last-mentioned to first-mentioned inside a list is real progress that mention rate alone cannot see.

---

## Spend preflight

Before the first paid call, compute and show the arithmetic. Use your harness's structured-question tool.

> Priority 1: 3 attributes, 6 discovery variants, plus capability, head-to-head and perception. 4 platforms, n=3.
> Priority 2: 5 attributes, 3 variants plus capability. 2 platforms, n=2.
> Priority 3: 4 attributes, 1 prompt, 1 platform, n=1, indicative only.
> Fact check: 18 claims, 3 platforms, n=2.
> **Total: 396 calls, roughly $6 to $12.**
> Proceed, trim the tiering, or drop a platform?

A live call with web search enabled costs a low number of cents, varying by engine, model and how long the answer runs. Price one call at the top of the run and multiply, rather than quoting a figure from this file: model pricing moves.

Never skip the preflight because the number seems small. The user is paying, and the arithmetic doubles as a design review. Seeing 396 is often what reveals that priority 1 has eight attributes in it and should have three.

**Unattended, the preflight is still computed but nobody answers it.** Write the arithmetic to the run record, then trim from the bottom — priority 3 first, then priority 2 platforms — until the estimate fits `config.budget.per_run_usd`. If priority 1 alone does not fit, run no paid calls at all and file the budget question in `.seo/needs-you.md`.

---

## Stream A: what the engines say

Run the prompt set. One call per prompt per platform per sample.

**Extraction, per response.** Do this at collection time, not later, because it is cheap now and expensive to redo across hundreds of stored responses.

1. **Brands mentioned.** Match against your brand, your competitor set, and any additional brand-shaped proper nouns. Maintain an alias list per brand in `.seo/config.json`: legal name, product name, common misspellings, the domain. A brand mentioned only by its domain still counts.
2. **Self mentioned, yes or no.** This is the atom of mention rate.
3. **Position in list**, when the response returned an ordered list.
4. **Citations.** Every URL. Keep them raw, including the query string, and normalize to domain separately.
5. **Type-specific scoring.** Discovery: did it return brands at all, and which. Capability: yes, no, or soft yes. Head-to-head: which brand won, or `draw`. Perception: pull the named pros and named cons as short phrases. Fact check: score against `.seo/truth.md` as correct, wrong, outdated or missing.

**Failures are data too.** A prompt that returned tips instead of brands, or an engine that refused, gets recorded with a `failed` flag and the reason. Silently dropping failures inflates every rate computed from the survivors.

---

## Stream B: the citation supply chain

Three questions, in increasing order of usefulness.

**What kinds of sources shape this category?** Tally cited domains across all discovery responses, then classify: review platforms, comparison articles and listicles, community threads, video, documentation, news and analyst coverage, competitor-owned pages, your own pages. The distribution is the strategy input. A category where no single domain holds a meaningful share of citations is fragmented, which means nobody has built durable authority and the position is available. A category dominated by three review platforms tells you exactly where the work is.

**Which of your pages get cited, and for which attributes?** If only product pages appear, engines treat you as a product source rather than a category authority, and you will lose category framing prompts. If nothing of yours appears for a priority 1 attribute, either the content cannot be reached or it is not being chosen, and Stream C plus the pipeline gates in Phase 3 tell you which.

**Where are competitors cited and you are not?** Run the tally per competitor and diff. This output becomes the off-page target list in Phase 5, generated from evidence instead of guessed.

**One methodological guard: scope citation analysis to discovery prompts.** When a brand name is already in the prompt, the engine pulls disproportionately from that brand's own pages, which skews the picture toward owned sources. Discovery prompts, where no brand is named, give the clean read of what is actually shaping the category.

---

## Stream C: the site itself

Full detail in `references/aeo/technical.md`. In this phase you are collecting, not fixing.

Build the page list first. It should include: the homepage, pricing, the About page, every page that maps to a priority 1 or 2 attribute, every page already appearing in citations, and the top pages by organic traffic from Search Console. Twenty to sixty pages is a normal audit. Do not crawl the whole site.

Then run:

```
python3 scripts/robots_check.py --url https://example.com --out .seo/aeo/runs/<date>/robots.json
python3 scripts/crawl_check.py --urls <file> --out .seo/aeo/runs/<date>/crawl.json
```

`robots_check.py` reports per AI user agent whether it is allowed, and separates retrieval agents from training agents. `crawl_check.py` reports per page: status and redirect chain, server-rendered body length versus total HTML, title and H1, canonical, meta robots, schema types present, word count, heading structure, a lead-answer read, and a date stamp read.

The single most important line in `crawl.json` is the server-rendered body length. A page whose content only exists after JavaScript executes is invisible to a meaningful share of retrieval agents, and this failure is silent: the page looks perfect in a browser.

---

## Stream D: crawl and traffic

**AI crawler hits.** Parse server or CDN logs:

```
python3 scripts/log_parse.py --logs <path> --out .seo/aeo/runs/<date>/logs.json
```

You get hits per agent per path per day. Join it to Stream B. That join is the diagnostic:

- Crawled and cited: working.
- Crawled and never cited: reachable but not chosen. Credibility or relevance.
- Never crawled: reachable is failing. Fix that first.

**AI referral traffic.** Same script, `--referrals`. Referrers from the answer-engine hosts, by landing page. Volume will be small. Read it as confirmation rather than as a channel: when a page gets AI referrals and maps to an attribute you are tracking, the full chain is confirmed end to end, which is rare and worth saying out loud in the report.

**Search Console.** Index state for every page in the audit list, plus the query side. A page that is not indexed is a page the Google surfaces cannot use. Pull it in one call over pages rather than looping per URL, then inspect only the rows that look wrong.

---

## Roll up

```
python3 scripts/score.py --run .seo/aeo/runs/<date> --prev .seo/aeo/runs/<prior> --out .seo/aeo/scoreboard.md
```

Two numbers per attribute per platform, each carrying its sample size.

**Mention rate** = responses naming your brand, over responses sampled. Print it as `42/60 (70%)`, never as a bare percentage. The denominator is what tells a reader whether to believe it.

**Rank** = your position when every brand mentioned across those responses is sorted by mention count. Report share of voice alongside it: your mentions over all brand mentions.

Read them together:

| Pattern | Reading | What it implies |
|---|---|---|
| High rank, high mention rate | The engines have a settled, favorable view | Defend. Keep the cited pages fresh and watch for erosion. |
| High rank, low mention rate | You lead when you appear and you do not appear reliably | No consensus yet. The cheapest attribute to move. Consistency and citation volume. |
| Low rank, high mention rate | You are in the conversation, behind established leaders | Slow authority work. Real, but not this quarter's quick win. |
| Platforms agree | One strong finding confirmed several ways | Take it seriously in either direction. |
| Platforms disagree | The evidence base is still mixed | Still winnable. Focused early effort has the most leverage here. |

**Model agreement is a confidence check, not an optimization target.** Do not build platform-specific tactics on divergence you cannot explain. The honest reading of "one engine likes us and three do not" is that the underlying evidence is thin, not that one engine has a preference you can exploit.

Write `.seo/aeo/scoreboard.md`, appending this run as a new dated column so the history is readable in one table.

Then go to `references/aeo/diagnose.md`.
