# Step 2. Select

<!-- new in v2; the editorial/programmatic candidate generator is opportunity-research.md, the AEO routing matrix is aeo/diagnose.md -->

Selection is where v2 differs from its predecessors. They asked "what should I write next?" This step asks "what is the single most valuable thing to do to this site today?" and the answer is usually not "write." The pool has to contain every kind of action before ranking means anything.

## Contents

1. Build the pool
2. Fixed overrides
3. The rubric
4. Saturation and exploration
5. Blocked candidates and the needs-you queue
5b. Cooldown
6. The checkpoint
7. measure-only

## 1. Build the pool

Every panel from `measure.md` contributes. Every lane contributes its generator. The pool is a list of candidate records:

```
- action: correct | repair | refresh | consolidate | prune | verify-product | create-editorial | create-programmatic | create-tool | aeo-fix | offpage-brief | index-nudge | distribute
  target: URL, slug, claim, or pattern
  source: which panel or generator produced it
  evidence: one line with the number or the quote
  movement: expected effect, in the panel's own unit (clicks, positions, citations, harm removed)
  effort: S | M | L
  demand: for create-* only: the GSC row, or a dated forum/community thread URL asking the question in the requester's words
  answer_owner: for create-* and refresh: who is the answer to this query today (our product | our content | a .gov or institution | a reference site | a competitor)
  blocked_on: null | a needs-you item
  season_bonus: optional, from seasonality.py (−1, +1, +2), applied to movement
  prior_adjust: optional, from priors.json (−1, 0, +1), applied to confidence
```

`demand` is required on every `create-*` candidate, and so is a `topic` naming the radar seed or coverage-map cluster the page belongs to; a create that fits no seed and no cluster is off-topic by definition and does not enter the pool. No provenance, no create. A keyword-tool volume number alone does not satisfy it; volume says people search, a thread says what they were trying to do. `answer_owner` exists because the strongest pattern on the sites this skill has audited is that traffic concentrates on queries where the product is the answer, and informational pages targeting queries a government or reference site owns sit at position 60 or worse with zero clicks. If the answer owner is not us and cannot become us, do not create; the candidate is a `refresh` of something that can rank or nothing.

Sources, in the order they are generated:

| Source | Produces |
|---|---|
| Truth check contradictions | `correct` |
| Claim re-verification changes | `correct` |
| Health diff violations, census `broken` | `repair` |
| Census `prune-candidate` | `prune` |
| Census `merge-candidate` | `consolidate` |
| Census `refresh` (striking distance, decay, stale) | `refresh` |
| Census `low-ctr` (CTR under half the expected rate at that position) | `refresh` (title and snippet first) |
| Health diff `slow-ttfb`, `heavy-html`, `broken-internal-link`, `redirecting-internal-link`, `orphan-page` | `repair` |
| Relevance: a page mapping to no seed or cluster, or GSC wrong-query with no retarget | `prune` or `consolidate`, or `refresh` (retarget) |
| Unindexed recent pieces | `index-nudge` |
| GSC states close / decaying / wrong-query / converting-nothing | `refresh` |
| GSC state invisible, or two pages sharing a query set | `consolidate` |
| Claims in `truth.md` with no dated source, or marked stale | `verify-product` |
| `opportunity-research.md` (editorial pool, striking-distance boosts) | `create-editorial`, `refresh` |
| `lanes/programmatic.md` (next open roadmap phase) | `create-programmatic` |
| `free-tool-pages.md` feasibility pass on tool-intent queries | `create-tool` |
| `aeo/diagnose.md` findings (OPP, ACC, TECH rows) | `aeo-fix`, `correct` |
| `lanes/offpage.md` (next unsent brief in the punch list) | `offpage-brief` |
| `demand-radar.md` clusters (asked, complained, reacted, trending), including `site-search` signals from GA4 | `create-editorial`, `refresh`, with `demand` pre-filled |
| `outcomes.py` `hurt` verdicts on a refresh or correct | `refresh` (revert or redo, with the before numbers as evidence) |
| `serp_features.py` `theft` and `aio-uncited` rows | `aeo-fix`, movement = clicks at risk |
| `link_opportunities.py` rows, grouped by owner page | `repair` (add the internal links), movement = the owner's impressions |
| `brand_split.py` branded `vs` / `alternative` / `pricing` / `review` queries with no owner page | `create-editorial`, demand = the Search Console row |
| `repo_changes.py` categories (measure.md §4b table) | `create-editorial`, `verify-product`, `correct`, `repair` |
| `competitor_diff.py` gains on queries we have rows for; new competitor pages in a vein we own | `refresh` of our owner page; gains with no row of ours go to the radar as seeds |
| `backlink_diff.py` `lost-link`, `unlinked-mention` | `offpage-brief` (reclamation, link request) |
| `backlink_diff.py` `inbound-404` | `repair` (301 to the nearest owner) |
| `seasonality.py` `rising` / `falling` keywords | not a candidate: a `season_bonus` on every candidate whose topic matches |
| Ledger `create-*` rows younger than `config.distribute.window_days` with no `distribute` row | `distribute` |
| Previous run records' not-done lists | any |

Generate the cheap sources always. Run the editorial generator (which may buy market data) only after the fixed overrides below have not already decided the run. There is no point buying keyword data on a day a live page has the wrong mailing address.

## 2. Fixed overrides

Applied in order, before scoring. The first non-empty tier wins and the run proceeds with its top candidate.

1. **Reachability and index regressions.** A page that was indexed and now is not. robots or `llms.txt` newly blocking an engine. A sitemap URL now returning non-200. The index gate from `measure.md`.
2. **Truth contradictions and accuracy failures.** Public copy contradicting `truth.md`. A re-verified claim whose source changed. An answer engine stating something false about the product where the cited page is ours.
3. **Repairs with user-facing harm.** Wrong address, phone or form on a page people act on. A medical, legal or financial statement now known to be wrong. Private identifiers reaching analytics. A leaked internal phrase.

Everything below tier 3 goes to the rubric, subject to two portfolio gates from the census:

- **create_gate.** While the census reports invisible share above 40% or prune-candidates above 10% of pages, no `create-*` candidate may win. The site has more pages than demand; the run prunes, merges or refreshes instead. Log the gate in the run record so the month's trend is visible.
- **Cold vein.** A content type, pattern or cluster whose shipped cohort shows under 10 clicks total after 90 days is marked cold in the ledger's coverage map. `create-*` candidates in a cold vein score zero until a `refresh` in that vein moves at the next read. This, not the saturation penalty, is what stops a fourteenth page in a vein the first thirteen already proved dead. Within a tier, take the candidate touching the page with the most impressions.

The reason for fixed tiers rather than a weight: on a normal scoring scale a fresh guide with a big keyword will always outscore fixing one wrong sentence, and that is exactly the bias that let the wrong-address page and the false regulatory claim survive for months on an actively managed site.

## 3. The rubric

For everything not decided by an override, score each candidate 1–5 on:

| Axis | Meaning |
|---|---|
| movement | How much the panel's number moves if this works, relative to the site's current scale. A refresh on a page at position 8 with 3,600 impressions moves more than a new page in a 200-impression cluster. |
| confidence | How sure we are the action causes the movement. A `repair` is near-certain. A `create-editorial` at the DR ceiling is a bet. Cap at 2 when `answer_owner` is a government, institutional or reference site. |
| strategic | Which of the four vitals it moves (speed, relevance, click rate, link health), and whether it serves the roadmap or positioning. 5 when it moves a vital on a winning page; 1 when it moves none. |
| freshness of evidence | Is the evidence from this run or carried debt. Carried debt decays unless re-confirmed. |
| effort | Inverted: S scores 5, L scores 1. |

Score = movement × confidence + strategic + freshness + effort. Ties go to the smaller effort.

Two adjustments are applied before the multiplication, and both are written into the top-ten table so the decision stays auditable:

- **Priors.** `.seo/priors.json` (measure.md §7b) carries `confidence_adjust` per action, and per content type for `create-editorial`. Add it to `confidence`, clamped to 1–5. On a site where seven of nine refreshes beat the control, a refresh is a 4 before anyone looks at it; on a site where two of eight guides ever earned a click, a guide is a 2. No priors file, or a group under three decided verdicts, means no adjustment.
- **Season bonus.** Add `season_bonus` (measure.md §6f) to `movement`, clamped to 1–5, for any candidate whose topic or target query is `rising` or `falling`. A page has to be live and indexed weeks before the peak to own it.

A `distribute` candidate scores movement 3 when the piece is under 7 days old and 2 under 14, confidence 4 (the first links and referrals are near-certain if the piece is good), effort S. It never outranks a tier-1 to tier-3 override and it needs no demand field: the piece already carries it. Use `opportunity-research.md`'s rubric for the editorial-specific sub-scoring (winnability, traffic, intent, data angle) to fill in `movement` and `confidence` for `create-editorial` candidates, so the two rubrics compose rather than compete.

Write the top ten with scores to the run record. That table is how the next run, and the human, audit the decision.

## 4. Saturation and exploration

Any operator that ranks on a fixed rubric ends up doing the same kind of thing every day, because the kind that scored well yesterday still scores well today. Two guards:

- **Saturation penalty.** If the last five executed runs share an action, subtract 2 from every candidate of that action today. If the last five share a lane and a content type, subtract 3 from that type. This is the cross-lane guard. `opportunity-research.md` §C.5 runs a finer type/vein penalty *inside* the editorial sub-score; apply each once, at its own level, not both to the same number.
- **Explore slot.** At least one of the top three presented at the checkpoint must be from a different action than the top candidate. In unattended mode, one run in five takes the best explore candidate over the top candidate, and says so in the run record.

## 5. Blocked candidates

A candidate whose execution needs something only the human can provide (a pricing decision, a qualified reviewer's sign-off, a console login, an API key, a budget over the per-run cap, a judgment about a competitor claim) is scored normally, marked `blocked_on`, and written to `needs-you.md` with the exact question. It is never silently dropped and never silently unblocked. When the human answers in `needs-you.md`, the next run picks it up as fresh evidence.

A candidate blocked on a verification the skill itself must still do (a competitor's current feature set, a tool's correctness on real inputs) is held, not dropped: keep it in the pool with `blocked_on: verify:<what>` and let a future run do the verification as its own action.

Do the parts that do not depend on the answer. A `verify-product` for pricing can still assemble the page list and the diff; only the fact it stamps waits.

## 5b. Cooldown

A target acted on in the last 21 days is out of the pool. The live data cannot show whether the last action worked for about that long (index refresh takes days, Search Console lags three more, and a CTR read needs a few hundred impressions), so re-selecting it means acting on the same evidence twice. The ledger row from the last action is the record; check it before scoring.

Exceptions, and only these: a tier-1 or tier-2 override signal that is new since the last action (the page went unindexed, a truth contradiction appeared on it, the fix itself is what the health diff now flags). A `refresh` whose ledger row says "uncommitted" is treated as done for cooldown purposes; the site not yet showing it is exactly why it is on cooldown.

Cooldown is per target, not per action. Rewriting a page's title puts the page on cooldown for everything, including a second refresh with a different idea. Write the second idea to the candidate backlog with a date instead.

One more exception: `distribute` acts on a page that is on cooldown by definition (it was just created), and adding an internal link *to* a page from elsewhere (`link_opportunities.py`) does not touch the page itself. Neither resets or is blocked by the target's cooldown, and neither counts as an action on the target for the 21-day read.

## 6. The checkpoint

Interactive session: present the top three as a table with action, target, evidence, score, and effort, then one question to the user. The human may pick, redirect, or say "measure only."

Unattended run (no human in the loop, or the invocation said so): take the top candidate, write the top-three table and a two-sentence reason to the run record, and proceed. If the top candidate is blocked, take the next unblocked one.

## 7. measure-only

`measure-only` wins when the best unblocked candidate scores below `config.select.floor` (default 9 of a possible 20), or when every candidate is blocked, or when the mode is `/seo measure`. It is a successful run. Register it like any other, with the panel summary and the top-ten table, so tomorrow inherits today's reading. The one thing a measure-only run must not do is buy market data it did not use.
