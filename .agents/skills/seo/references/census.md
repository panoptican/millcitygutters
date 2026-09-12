# The content census

<!-- new in v2.1; the answer to "how does this not go stale" -->

The previous content skill drifted because it only ever looked at the piece it was about to write and the pieces it had just written. Nothing looked at the whole site and asked what should still be there. Over a year that produces a site that is 30% pages nobody has seen in six months, and Google reads a portfolio like that as a signal about the whole domain, not just the dead pages.

The census is the whole-inventory review. Every run takes the temperature of every public URL, not just the ledger's recent rows, assigns each one a verdict, and keeps the result as a dated snapshot. The snapshots are the dataset: after three months you can see decay, after a year you can see which veins went cold. Removing and merging pages come out of the census as candidates on the same footing as writing new ones.

## Contents

1. What the census reads
2. Verdicts
3. Portfolio gates
4. Cadence and the forced census run
5. The dataset
6. How this stops the skill rehashing itself

## 1. What the census reads

Three inputs, joined by URL:

- **Inventory**: the latest `.seo/health/<date>.json` from `health_diff.py`. Every sitemap URL with status, canonical, word count, dates, schema, content hash. This is the site as it is, not as the ledger remembers it.
- **Search Console**: the per-page pull from measure §1, saved as `.seo/gsc/<date>.json` (last 28 days) and the prior window. Saving the pull is what makes the dataset outlive Search Console's own 16-month retention.
- **Ledger**: `.seo/content-ledger.md` for type, ship date, cohort, and intent owner.

Run:

```
python3 <skill>/scripts/census.py --health .seo/health/<latest>.json --gsc .seo/gsc/<latest>.json --gsc-prev .seo/gsc/<prior>.json --ledger .seo/content-ledger.md --out .seo/census
```

It writes `.seo/census/<date>.json` and rewrites `.seo/census.md` (the current non-keep verdicts). Previous census files in the directory give it the time series.

## 2. Verdicts

Every URL gets exactly one, with reasons:

| Verdict | Means | Becomes |
|---|---|---|
| `watch` | Too young to judge (under `min-age-days`, default 21) | nothing |
| `broken` | Non-200, redirecting in the sitemap, canonical mismatch | `repair` |
| `prune-candidate` | Invisible for 90+ days and thin, or invisible across two census snapshots 90 days apart | `prune` |
| `merge-candidate` | Two URLs with the same title stem and neither getting impressions | `consolidate` |
| `refresh` | Striking distance, decaying (clicks down 30%+), or a year old with no content change on record | `refresh` |
| `invisible` | Under 10 impressions after 90 days, no other flag yet | watch list; becomes `prune-candidate` or `consolidate` next quarter |
| `keep` | Earning its place; `winning` noted when in the top 10 with clicks | nothing, defend |

Verdicts are candidates, not decisions. A `prune-candidate` with a backlink, a legal reason to exist, or a role in a hub still gets a human look through `lanes/fix.md` "Pruning a page" before anything is removed.

## 3. Portfolio gates

The census reports the shape of the whole site, and two of those numbers gate creation:

- **Invisible share** above 40% of judgeable pages, or prune-candidates above 10%, sets `create_gate`. While it is set, `create-*` candidates cannot win selection. The run's job is pruning, merging and refreshing until the share drops. New pages on a site Google has stopped fetching are not indexed; they are added to the pile.
- **Cold vein**: a content type, pattern, or topic cluster whose shipped cohort shows under 10 clicks total after 90 days is marked cold in the ledger's coverage map. Further creates in a cold vein are blocked until a refresh in that vein moves. This is the direct answer to the old skill's habit of writing a fourteenth decoder because the first thirteen scored well on paper.

Also reported, not gating: thin share, median page age, and click concentration (what share of clicks the top 10% of pages carry). A site where 5% of pages earn 90% of clicks is not necessarily wrong, but the number should be in every run record so the trend is visible.

## 4. Cadence and the forced census run

The census runs every day the health diff and the Search Console pull both ran, because the join is free once the inputs exist. Most days it changes little, and that is fine; the value is the snapshot.

Once a month, or on `/seo census`, the run is a census run: no create candidates are generated at all. The run reads the full verdict list, executes the highest-value prune, merge or refresh, and writes a "Portfolio" section in the run record with the trend against the previous month. This is the deliberate "hold up, let's look at what we have" the skill's predecessor never did.

## 5. The dataset

Everything dated, everything kept:

```
.seo/health/<date>.json   inventory fingerprints          daily
.seo/gsc/<date>.json      Search Console page pulls        daily
.seo/gsc/queries-<date>.json  Search Console query×page    daily
.seo/outcomes.json        verdict on every past action     rewritten daily
.seo/priors.json          per-action worked/flat/hurt      rewritten daily
.seo/serp/<date>.json     top-query SERP features          weekly
.seo/backlinks/<date>.json  lost/new links, mentions       weekly
.seo/competitors/<host>/  competitor fingerprints, ranked  weekly, monthly
.seo/seasonality.json     monthly volume history           monthly
.seo/census/<date>.json   per-URL verdicts + portfolio     daily
.seo/census.md            current non-keep verdicts        rewritten daily
.seo/radar.md             outside-in demand signals        cumulative
.seo/runs/<date>.md       what was measured, chosen, done  daily
.seo/evidence/*.json      before/after for every fix       per action
```

Prune nothing from these except radar rows older than 90 days. Disk is cheap and the questions that matter ("when did this cluster start decaying", "did the January prunes move anything") need the history. If the directory grows past a few thousand files, roll monthly files into one, do not delete.

## 6. How this stops the skill rehashing itself

Four mechanisms, and they compound:

1. **Every URL is judged on evidence every run**, including the ones the ledger never knew about. A page cannot hide by being old.
2. **Removal is a first-class action** (`prune`) with the same scoring as creation. A dead page costs the site something; deleting it can score higher than writing a new one.
3. **Portfolio gates block creation** when the site's own numbers say it has more pages than demand. The skill cannot outrun its dead weight by writing faster.
4. **Cold veins close.** The saturation penalty slows repetition; the cold-vein rule stops it once the cohort's own performance says the vein is exhausted.

The radar is the fifth: it supplies new directions from outside the site, so "stop doing this" has a "do this instead" beside it.
