# Proprietary Data — the element the top 10 can't copy

Everything else in a piece can be reproduced by anyone with a browser and a weekend. A number that exists only inside your product cannot. This file is the method for finding that number, getting it out safely, combining it with public data so it says something neither source says alone, and packaging it so search engines and LLMs actually lift it.

**Why this got more important, not less.** Models are trained on the open web and then re-read it every day looking for what changed. Synthesis is the one thing they already have infinite supply of — it is the commodity input, and a page made of it adds nothing to retrieve. A dated, sourced, first-party figure is the opposite: it is a *new observation about the world*, retrievable nowhere else, and it is exactly what an answer engine reaches for when a user asks a question the training data can't settle. Original data is now the highest-citation-rate asset on a content site, and the citation is durable — a stat gets quoted, re-quoted, and linked for years after the post that carried it stopped ranking.

---

## The rule

> **Every piece attempts an original-data element, and the attempt is real work, not a box-tick.** Run the §1 hunt on every run. If a legitimate angle exists — from product data, analytics, or a test you can run today — the piece carries it. If, after the §6 ladder, no honest angle exists, say so explicitly in the brief and fall back to the other information-gain forms. **Never invent one.** A fabricated first-party stat is worse than no stat: it's unverifiable by definition, which is precisely why it would have been valuable if true.

"Attempts" is the operative word. Most topics have a data angle that isn't obvious until you go looking, and the default failure mode of this engine is citing someone else's benchmark while sitting on a database that could have settled the question directly.

---

## §1 — The hunt: where the data actually is

Work down this list every run, cheapest first. Stop when you have one solid, defensible element — you need one, not five.

| Source | What it yields | How to get it |
|---|---|---|
| **`.seo/brand.md` — Proprietary data section** | The standing inventory: what this product can legitimately draw on, plus the access path and the off-limits list | Read it first, every run. It's the map, not the territory — it goes stale, so treat it as a starting point |
| **Own analytics** | Traffic, query, and behavior data about your own space; often the fastest real number | **Search Console direct** (real queries, positions, CTR — see `gsc.md` §4 for the shapes that make publishable numbers), or a Plausible/PostHog/Fathom API in the repo |
| **The application database** | The richest source by far — usage distributions, adoption curves, real-world value ranges, error rates, "how people actually configure X" | §2. Read-only, aggregate-only, user-approved |
| **The repo itself** | Changelog cadence, feature timelines, benchmark scripts already written, fixture data that reveals real-world shapes | `git log`, `db/schema.rb` / migrations / Prisma schema, `test/fixtures`, any `benchmarks/` dir |
| **Support, sales, and community artifacts** | The frequency ranking nobody else has: which problems actually occur, in what proportion | Help-desk exports, a Slack/Discord search, issue-label counts (`gh issue list --label`), sales-call notes |
| **A test you run today** | First-hand benchmarking, a hands-on teardown of every competitor, a reproducible measurement | Run it in this run and publish the method. Small-n is fine if the method is honest and stated |

**Read the schema before you write a query.** For an app DB, `db/schema.rb`, `schema.prisma`, `migrations/`, or `\d+` gets you the shape and the column names, and the interesting aggregate is usually visible from the schema alone. Guessing at column names against production is how you write six failing queries in a row.

---

## §2 — Pulling from production: the safety contract

**Yes, pull from production when that's where the truth lives.** It usually is. Staging data is synthetic and answers nothing. But the pull runs under a contract, and every clause is a hard rule.

**Before the query:**

1. **Ask the user first, every time.** Show the exact query and what you intend to publish from it before running anything. This is an a question to the user moment, not a judgment call you make alone — it's their data and their customers. **Unattended, the answer is no:** don't run the query, drop the first-party slot, fall back to the §6 ladder, and file the approval request in `.seo/needs-you.md` so the next run can pick it up. Never publish a number the user has not seen.
2. **Prefer a read replica or a recent backup** if one exists (`DATABASE_REPLICA_URL`, a `db:*_replica` config, a dump in `tmp/`). Fall back to production read-only only when that's the only real data available.
3. **Read-only, always.** `SELECT` only. Never `INSERT`/`UPDATE`/`DELETE`/`ALTER`, never a migration, never a task with side effects. Where the tooling supports it, connect as a read-only role or open a transaction you roll back.
4. **Don't hurt the box.** Add a `LIMIT`, set a statement timeout, avoid unindexed scans on hot tables, and run heavy aggregates off-peak. A content run must never be the cause of a latency page.

**What can leave the database:**

5. **Aggregates only.** Counts, means, medians, percentiles, distributions, rates, time series. **Never row-level records, never a raw export.**
6. **A minimum cell size of n ≥ 50.** Suppress or merge any published bucket below it. A "average for teams of 200+" computed from four accounts isn't a statistic, it's four customers' private numbers with a percentage sign on them.
7. **No re-identification, including by inference.** If one account dominates a bucket (say >30% of its weight), that bucket describes that account — merge it or drop it. Segment cuts multiply this risk: three narrow filters stacked together identify one customer even when each filter alone looks safe.
8. **Zero PII.** No names, emails, domains, IPs, org names, free-text fields, or IDs that join back to a person. Not in the piece, not in the brief, not in a screenshot of a query result.
9. **No named customer without written permission** — logos, case-study figures, and "one of our customers" anecdotes specific enough to identify are all the same rule.
10. **Flag the self-harming cuts rather than deciding them.** Churn, exact revenue, account counts, and growth rates are legitimate data and often terrible publishing. Surface the tradeoff to the user at the checkpoint and let them choose; default to the metric that helps the reader without printing the business's vitals.

**After the query:**

11. **Show the user the numbers before they ship.** They know which figure is misleading, seasonal, or contractually off-limits in a way the data doesn't show.
12. **Save the query verbatim in `.seo/briefs/<slug>.md`.** Query text, run date, row counts, filters, and every exclusion. This is what makes the number reproducible next year, defensible if challenged, and updatable when someone asks "is this still true?"

**Sanity-check the result before it becomes a claim.** A first-party number is uniquely dangerous because nobody outside can catch the error: your users are not the market, your instrumentation has gaps, deleted and test accounts skew everything, and a number that surprises you is more likely a bad `JOIN` than a discovery. Re-derive any headline figure a second way. State the population honestly — "across N [product] accounts," never "across the industry."

---

## §3 — Combine: make external data say something it can't say alone

The highest-leverage move isn't publishing a raw internal number. It's **using the internal number as the missing dimension on data everyone already has.** Public data is table stakes and everyone quotes it identically; your data is scarce but narrow. Crossed, they produce a claim that exists in exactly one place on the internet. These patterns, roughly in order of citation value:

1. **Ground-truth the received number.** Take the benchmark the whole SERP repeats — usually a vendor report from 2019 that everyone cites without checking — and hold it against what you actually observe. *"The figure quoted everywhere is 21%; across n=3,400 accounts in the last 12 months we see 9%."* This is the single most-cited shape in this file, because it's a correction, and corrections propagate. It also earns links from the pages you're correcting.
2. **Fill the cell nobody can fill.** Identify the number every article in the top 10 gestures at and none of them has, because you need operator visibility to compute it. Publish it with its method. That page becomes the citation for a question, and questions don't go out of fashion.
3. **Cross with a public dimension.** Join your metric to a public dataset — census/BLS geography, GitHub or npm/PyPI download stats, SEC filings, government price or rate tables, a public API's published limits — and produce the per-capita, per-region, per-cohort, or per-price-tier cut neither side has. Neither dataset is proprietary on its own; the join is.
4. **Enrich the external set.** Take the public list everyone links to and add the column only you can compute — real observed performance next to advertised specs, actual adoption next to claimed market share. You inherit the demand for the original list and outrank it on usefulness.
5. **Publish the time series.** Re-cut the same measurement each quarter with a stable URL. A one-off stat is cited once; a maintained series becomes the reference — and it converts your page into a destination people return to and a natural, repeatable update that keeps the freshness signal alive.
6. **Segment what's only published in aggregate.** Public sources report one national average; you can break the same measure by company size, industry, plan tier, or setup — the cut readers actually need to know where they stand.

**Every combine ships with its seams visible.** Name both sources, both dates, both populations, and say plainly where they don't line up ("our accounts skew to teams under 50, so this over-represents small deployments"). A stated limitation makes the number more citable, not less — it's what lets another writer quote you without risk.

---

## §4 — Freshness: the kicker

Answer engines are structurally hungry for recent, first-hand observation, because that's the gap in what they already hold. Fresh original data is the most direct way to be the thing they retrieve rather than the thing they've already absorbed. So:

- **Date every original figure at the point of use** — as-of date, window, and n, inline: *"as of March 2026, across n=3,400 accounts over the trailing 12 months."* An undated stat is unciteable; a dated one is quotable forever.
- **Prefer the recent window** when both are defensible. Trailing 12 months beats all-time; "since the 2026 API change" beats "historically."
- **Set a refresh interval** in the `.seo/content-ledger.md` row (quarterly for volatile metrics, annually for structural ones) with the query saved in the brief. A refreshed stat is the cheapest high-value content run this engine has: same URL, new numbers, renewed freshness, no new research.
- **Say when it was last checked**, and update the visible date when you re-run it — not the publish date, the data date. Readers and models both weigh them separately.

---

## §5 — Package it so it actually gets lifted

Data nobody can extract is data nobody cites. Format for the lift:

- **One named, self-contained stat sentence** near the top, written to survive being quoted with zero surrounding context: *"[Brand]'s analysis of 3,400 accounts found that 9% of teams ever change the default retention window (March 2026)."* Subject, number, population, date, all in one sentence.
- **Attribute it to the brand, not to "we."** Pronouns lose their referent the moment a model lifts the sentence. `[Brand]'s data` survives extraction; `our data` becomes anonymous.
- **A real methodology section** — population, n, time window, how it was measured, what's excluded, known bias. This is what separates a citable statistic from a marketing claim, and it's the section skeptical writers check before linking to you.
- **Emit `Dataset` schema** alongside the type's usual schema when the piece carries a genuine dataset (`name`, `description`, `creator`, `temporalCoverage`, `datePublished`, `license`). See `lanes/aeo.md`.
- **Draw the finding.** Original data is the strongest case for an actual figure — build spec in `visuals.md`: hand-authored inline SVG styled from the repo's tokens, zero-based axes, n and as-of date on the figure, and `[Brand] · [date]` inside it so it carries attribution when someone screenshots it into a deck or a post. That travelling figure is one of the cheapest link sources this engine has. **The numbers still appear as text alongside it** — a stat that exists only inside a graphic is invisible to every extractor, and the citation goes to whoever published it as text.
- **Add a citation line** — "Cite this: [Brand], *[Title]*, [date], [URL]" — which lowers the friction on the link you're trying to earn.
- **Keep the URL stable.** Every citation you earn points at it; a re-slug throws away the whole asset.

---

## §6 — When there's no honest angle: the ladder

Work down. Only after all five come up dry does the piece ship without an original-data element:

1. **A production aggregate** that speaks to this topic (§2).
2. **Own analytics** — search, traffic, or behavior data about this topic area.
3. **A test you can run in this run** — a benchmark, a hands-on teardown, a reproducible measurement. Small-n with a stated method beats no data.
4. **An internal expert** — a named colleague's specific, attributable observation from doing the work (`.seo/brand.md` Author + Internal experts sections). Quote them, don't paraphrase into anonymity.
5. **Original analysis of public data** — a novel cut, join, or visualization of data that already exists. The analysis is yours even when the inputs aren't.

Dry on all five is real signal about the *topic*, not just the research: it usually means the piece sits outside where this product has any claim to authority. Consider looping back to selection (`select.md`). If you write it anyway, the brief must state plainly that the information gain rests on framework or first-hand experience rather than data, so the Step 4 gate judges it on the right axis.

---

## §7 — Checklist

Before the brief is done:

- [ ] Ran the §1 hunt this run — not just re-read the brand.md list
- [ ] Named the one original element, or documented the §6 ladder coming up dry
- [ ] Any production pull: user-approved, read-only, aggregate-only, n ≥ 50 per published cell, no PII, no re-identifiable segment
- [ ] Headline figure re-derived a second way; population stated honestly
- [ ] At least one §3 combine considered — is there a public dataset this crosses with?
- [ ] Every original figure carries n, window, and as-of date
- [ ] Query + method + exclusions saved to `.seo/briefs/<slug>.md`
- [ ] Refresh interval written into the ledger row
- [ ] Stat sentence is self-contained and brand-attributed; method section present; `Dataset` schema emitted if warranted
- [ ] User has seen the actual numbers before publish
