# Research → Verified Brief (the research step inside a lane)

The quality of a piece is decided here, before a word of prose is written. As of the **March 2026 core update**, the dominant ranking signal is *information gain* — how much genuinely new knowledge a page adds versus what already ranks. Pure synthesis of the top 10 is invisible. This step exists to manufacture information gain and to ground every claim in a verified source.

Two principles drive the design:

1. **Generate ≠ verify.** The agent that gathers a fact must not be the only one that confirms it. Research and verification are separate passes — **both spawned by the main thread**, and there is **one** verifier for the whole ledger, not one per researcher.
2. **The writer consumes facts, not raw notes.** The research step's output is a structured **research brief** — a claim ledger, an entity map, the information-gain statement, the angle. Step 3 writes *from* the brief.

---

## 2a. Fan out the research

Run these six angles. **If the host supports subagents (see `tools.md`, Host capabilities), spawn them in parallel** — each returns a structured packet and your main context stays clean. If not, run them sequentially in-context. Either way, all six get covered.

**Free tool pages (type 10) scale this down to three researchers** — SERP teardown, primary sources, first-hand/product angle — because the tool is the primary information gain. Everything else in this file applies unchanged, and the verification pass gets *stricter*, not looser: any number the tool **computes with** is load-bearing, and a wrong constant is a wrong answer for every visitor forever. Full spec in `free-tool-pages.md` §6.

### Fan-out rules (read before spawning anything)

**The fan-out is one level deep. The main thread is the only spawner.** Six researchers, then one verifier. That is the entire agent budget for the research step — seven, not seventy.

This has to be enforced *in the researcher's own prompt*, because a researcher carrying this file's context reads "spawn them in parallel" and "research and verification are separate subagents" as instructions addressed to **it**, and re-runs the whole fan-out one level down. Depth 3 turns 6 agents into ~90 and burns thousands of fetches. Paste this verbatim into every researcher prompt:

> You are a **leaf** agent. Do not spawn subagents — do the research yourself. Budget: **≤15 page fetches**. Do not start background shells; if you background anything, wait for it and confirm it exited before you return. Return the structured findings block below and nothing else.

Then, as the orchestrator:

- **Spawn all six in ONE message — the same response, not six consecutive turns.** This is a hard rule, not a preference: each separate spawn costs ~30s of orchestrator thinking and serializes the start. The Step 3a **wiring agent** goes in that same message (it needs only the repo and the slug — see `writing.md` → Two lanes), so a file-store run issues seven `Agent` calls at once. Don't spawn an eighth mid-flight because a packet looks thin — a thin packet is a finding (the angle is dry), not a reason to fan out again.
- **Don't have researchers talk to each other.** No `SendMessage`, no "wait for the other agent to finish" polling. Each returns to you; you're the only one merging.
- **Expect the proprietary-data researcher to be the long pole** — 2-3× the others is normal, because building a real first-party figure (a bulk-data download, a database aggregate, a re-derivation) is real work. Do not wait for it before starting the verifier or the writer; see 2b and 2d.
- **If a researcher returns junk, re-run that one angle once.** Cap total research agents at ~10 including retries. Past that, the problem is the topic selection (`select.md`), not the research depth.

| Researcher | Goal | Tools |
|---|---|---|
| **SERP teardown** | Scrape the top 5-10 ranking pages. Capture the *union* of their sections (your table-stakes coverage) and what they **all miss** (the gap your angle lives in). Note their depth + heading shape so you out-cover them. | page fetch and web search; `serp_organic_live_advanced` |
| **Primary sources & studies** | Find authoritative *primary* sources — original studies, datasets, official docs, standards, filings. Not aggregator blogs. | web search, page fetch, DataForSEO |
| **Statistics & data points** | Pull real, citable numbers — each with attribution, a URL, and a date. These are what LLMs lift and what earns links. | web search, page fetch |
| **Contrarian / counter-evidence** | Actively hunt evidence *against* the obvious thesis. Surfaces the strongest counter-argument (which a great piece addresses head-on) and stops you shipping a one-sided take. | web search, page fetch |
| **Proprietary data / first-hand** | The information-gain moat, and the angle with the highest ceiling. **Hunt, don't just re-read the inventory**: `.seo/brand.md` (Proprietary data + Author), own analytics, the repo, support/issue counts, and the app database — production included, under the read-only/aggregate-only/user-approved contract. Then look for the **combine**: your number as the missing dimension on a public dataset. Full method — hunt, safety contract, combine patterns, freshness, packaging — in `proprietary-data.md`. | repo + schema, brand.md, app DB (read-only), GSC/analytics MCP, public datasets |
| **Entity / topical map** | The concepts, entities, and questions that *must* appear for topical authority + semantic completeness. Pull the real People-Also-Ask set and related entities. | `dataforseo_labs_google_related_keywords`, PAA scrape, `serp_organic_live_advanced` |

Each researcher returns findings as **ledger rows, not prose** — the exact shape the brief's claim ledger uses, so the brief is a concatenation and no one has to re-read six packets to build it. Number rows with the angle prefix (`SERP-1`, `PRI-4`, `DATA-2`…) so the verifier can address them:

```
- id: PRI-4
  claim/fact: "<the specific thing>"
  source: <URL or "product data: <which metric>">
  tier: primary | secondary | tertiary        # primary = original source/data; tertiary = blog citing a blog
  date: <when the data is from>                # freshness matters for AEO
  confidence: high | medium | low
  status: unverified                          # the verifier flips this; researchers never mark their own rows verified
```

The two packets that carry more than rows — the SERP teardown (table-stakes vs gap, heading shapes) and the entity map — return those blocks *after* their rows, under fixed headings (`## Table stakes`, `## Gap`, `## Entity map`), so the main thread lifts them into the brief verbatim.

---

## 2b. Verify — the separate pass, started at five packets

Verification runs **before** the brief is assembled, not after, and it starts as soon as five of the six packets are in — in practice that means everything except the proprietary-data packet. Full method in 2c below. Its output is the **corrected merged ledger**: every row from every packet, status flipped, corrections applied, a named list of cut claims that must not be reintroduced. That ledger is the brief's spine.

When the sixth packet lands, **send it to the same verifier agent** (resume it with the late rows) so it checks only the delta with the ledger already in context. Don't spawn a second verifier and don't re-run the pass.

---

## 2c. Assemble the brief — main thread, no synthesis agent

Assembling the brief is a **merge the main thread does in a few minutes**, not a stage that re-reads six packets. A synthesis agent doing that from scratch is a serial 15-20 minute step that adds nothing the packets didn't already contain. The verifier's merged ledger is part 1; parts 2-3 are lifted verbatim from the SERP and entity packets' fixed headings; parts 4-5 are the only prose you write. Save it to `.seo/briefs/<slug>.md` for auditability and reuse.

The brief has five parts:

1. **Claim ledger** — every factual claim the piece will make, each with its source(s), tier, date, and verification status (set by the verifier in 2b). This is the spine; if a claim isn't in the ledger, it doesn't go in the piece.
2. **Entity / topical-coverage map** — the must-cover concepts, entities, and PAA questions. The piece is "complete" only when it covers this set.
3. **Table-stakes vs. gap** — what every top-10 page covers (you must match) and what they all miss (your opening).
4. **Information-gain statement** — the explicit, specific thing this piece contains that is in **none** of the top 10. Must be ≥1 of: *original/proprietary data · first-hand testing or experience · expert commentary · a genuinely novel framework or synthesis.* **If you cannot write this sentence concretely, stop and loop back to selection** — the piece will not rank and is not worth writing. ("Restates the consensus more clearly" is not information gain.) **Original data is the strongest of the four and the default target** — every run attempts it before settling for the others, and if the `proprietary-data.md` §6 ladder came up dry, this section says so explicitly so the Step 4 gate judges the piece on the right axis.

   Where the element is first-party data, this section also carries its **provenance block**: source, the exact query, run date, population, n, time window, exclusions, and the refresh interval. That block is what makes the number reproducible next year, defensible if challenged, and cheap to re-cut — and it's the second half of the reason to save the brief at all.
5. **The angle** — the one differentiated thesis, now backed by the gap + the information-gain element.

---

### The verifier's method (referenced from 2b)

Do this as **one distinct pass over the merged ledger** — a single subagent spawned by the main thread if the host allows (leaf rules apply: no subagents, no background shells), otherwise a clean-slate review that treats the ledger adversarially. Pretend a fact-checker is trying to get the piece retracted. One verifier for the whole ledger — not one per researcher, and never spawned *by* a researcher. Hand it the packets' raw rows; it returns the merged, corrected ledger (2b), not a list of notes for someone else to apply.

For every claim in the ledger:

- **Cross-check against an independent second source.** A claim sourced once is "single-source," not "verified." Mark each: `verified` (≥2 independent sources or one primary), `single-source`, or `unverified`.
- **Tier-up where possible.** If a stat traces back to a primary source, cite the primary, not the blog that quoted it.
- **Refute the high-stakes claims.** For any number, named comparison, or load-bearing assertion, actively try to prove it wrong. Claims that survive a real refutation attempt are the ones worth featuring.
- **First-party numbers get verified differently — and harder.** There is no second source for your own data, so cross-checking is impossible and the usual `verified` test doesn't apply. Instead: **re-derive the figure a second way** (a different query shape, or a spot-check against analytics), confirm the population is stated honestly, confirm every published cell clears n ≥ 50 with no re-identifiable segment, and confirm the user has seen the number. A surprising internal stat is more often a bad `JOIN` than a discovery. Mark these `first-party` in the ledger, never `single-source` — the failure mode is different and so is the fix (`proprietary-data.md` §2).

Then resolve every non-`verified` claim — no exceptions carried silently into the draft:

- **`unverified`** → re-research it, or **cut it**. Never ship an unverifiable factual claim as fact.
- **`single-source` but plausible** → keep with explicit inline attribution ("according to <source>"), or down-rank to a bracketed range flagged for the user.
- **Fabrication is the cardinal sin.** A wrong number gets the page penalized and destroys trust faster than anything else. Real sources or clearly-bracketed estimates — never an invented statistic.

The verified ledger (claims + final status + sources) is what Step 3 writes from and what gets persisted at Step 5 as the citation record.

---

## 2d. Hand the writer a brief with a pending slot — don't wait for the long pole

If the proprietary-data packet is still out when the other five are verified, **the brief goes to the writer now** with the information-gain section carrying a marked slot:

```
[[FIRST-PARTY FIGURE — pending: <what the researcher is computing, e.g. "office-action rate, USPTO 2017 cohort">]]
```

The writer drafts everything else — the answer lead, table stakes, the gap sections, the FAQ — and leaves the data section and the figure as the last things it fills. When the packet lands: verifier checks the delta (2b), main thread appends the provenance block to the brief, and the writer (still running, or resumed) fills the slot. Only the figure and one section ever depended on it. What you must **not** do is let a 30-minute cohort computation hold an idle writer, an idle wiring lane, and an idle verifier — that is the single largest avoidable delay this skill has.

If the data packet comes back dry (the §6 ladder found nothing), the slot is removed, the information-gain section names the fallback form explicitly, and the Step 4 gate judges on that axis. The writer never invents a number to fill a slot.

---

## Degradation & escalation

- **No subagents in the host** → run the six angles sequentially. Slower, same coverage. Don't skip angles.
- **A deep-research skill installed** → hand 2a + 2b to it for heavier multi-source fan-out and verification, then resume at 2c to assemble the brief.
- **User opted into a workflow** → the six researchers + the verify pass map cleanly onto a `pipeline()` (researchers → verify → assemble, with the wiring lane as a parallel branch). Only do this if the user explicitly asked for a workflow.
- **No keyword/AEO tools** → the SERP teardown via web search and page fetches still carries this step; see the no-tool fallback in `research-recipes.md`.

The output of the research step is always the same: a verified brief. How you produce it flexes to the environment; the bar does not.
