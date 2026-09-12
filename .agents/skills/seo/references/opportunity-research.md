# Opportunity Research — deciding what to write next

This is the skill's core job. By the end of this step you have **one chosen topic, one chosen type, and the data to justify both** — ready for the Step 2 selection checkpoint (`select.md`).

Don't skip to writing. A mediocre topic written brilliantly loses to a great topic written adequately. Selection is where the leverage is.

---

## Step A — Build the exclusion set (what NOT to write)

Before generating ideas, know what's off the table:

1. **Shipped pieces** — read the `## Shipped` table in `.seo/content-ledger.md`.
2. **Programmatic pages** — `git ls-files | grep -iE 'alternatives|compare|/for/|playbooks'` (and read the `.seo/roadmap.md` tracker *if it exists*). Editorial content must not duplicate a templated page targeting the same keyword. (No roadmap yet? The git scan alone is enough.)
3. **Existing content** — for file-based sites, `git ls-files | grep -iE 'blog|guides|content|articles|docs'`. For **DB/CMS sites, there are no files to scan** — list existing content from the sitemap (`/sitemap.xml`) or the CMS API instead (see `content-stores.md` Operation 1). Read titles/slugs either way.

4. **Cannibalized queries** (GSC connected) — any query where 3+ of your pages already take impressions (`gsc.md` §1d). A fourth page makes the split worse. Exclude the query and note the consolidation fix in the hand-off.

Anything matching the exclusion set is dead. If the strongest opportunity is already covered but *thin*, that's a striking-distance **boost**, not a new piece — this file generates new-piece candidates. Put the boost on the slate as a `refresh` candidate instead (`lanes/editorial.md` boost path, scoped by `gsc.md` §2d), unless the user wants a fresh companion piece. **The exception is a boost with measured numbers behind it** (the measure step, `gsc.md` §2): a page at position 5-15 with real impressions, or ranking well with a CTR far under its positional norm, goes on the selection slate as a genuine option against the three new candidates. Sometimes it's the better run, and the engine should be willing to say so.

---

## Step B — Regenerate the opportunity pool

Pull from five signal sources. Market-side calls (DFS by default) are in `research-recipes.md`; own-site calls are in `gsc.md`.

**Free vs paid, and it changes the order you work in.** GSC (B2) costs nothing — re-pull it every run and start there. Market data (B1, B3, B5) is metered, so **read `.seo/keyword-research.json` first and query only what's missing or older than 30 days**. Working GSC-first also means the paid sweeps run against a shortlist you've already narrowed, instead of the other way round.

**Know which difficulty bucket you play in before you score anything** (`research-recipes.md` → Difficulty buckets). It's Easy / Medium / Hard, and it's derived from GSC — the hardest bucket where you already hold 2+ page-1 positions — not from DR arithmetic. Most picks sit in that bucket; one in four may stretch one bucket up.

### B1. Keyword / topic gaps (the main source)
- **Content gap** — keywords your competitors rank for and you don't:
  `dataforseo_labs_google_domain_intersection` with `intersections: false` (Recipe 1). Filter to your bucket and volume ≥ 30 — then run the **relevance gate**, which usually removes most of the list: incidental junk first (person names, navigational, anything you can't explain), then keywords that are real but sit in the competitor's territory rather than yours.
- **Question sweep** — `dataforseo_labs_google_keyword_suggestions` seeded with your clusters, filtered to question modifiers (how, what, why, best, vs, for). Questions map cleanly to how-to / definition / listicle types.
- **Related terms** — `dataforseo_labs_google_related_keywords` around your best-ranking existing page. Run it only when the two above come back thin.

### B2. GSC own-site signals (existing sites — run this first, it's the highest-yield source)
Exact calls in `gsc.md` §1. These are *measured* demand, not estimated, so a GSC-sourced candidate beats an equally-scored keyword-tool candidate at the tie-break.

- **Striking distance** — positions 5-20, impressions ≥ 50, where **no dedicated page exists**. A focused new piece can capture a query your homepage is accidentally ranking for. (Dedicated page already there? Boost, not a new piece — Step A.)
- **Unowned demand** — impressions ≥ 100 with ~zero clicks and position > 10. Google already thinks you're relevant and no page of yours deserves the click. Many of these carry no measurable global volume, so a keyword tool will never surface them.
- **CTR gap** — a page ranking top-10 with CTR far under its positional norm. That's a title/description problem, and the fix is minutes, not a new piece. Carry it to the checkpoint as an option.
- **Decay** — pages down >30% in clicks or 3+ positions over the last 90 days vs the prior 90. A refresh of a decaying page usually beats a mid-tier new candidate on expected value.
- **Wrong-query pieces** (from the measure step) — a shipped piece pulling impressions for queries it doesn't target hands you a free, pre-validated candidate list.

No GSC property for this site? Say so once, then run B1/B3/B4/B5 and note that selection is estimate-only.

### B3. AI-citation gaps
- Where do LLMs answer questions in your space without citing you? `ai_opt_llm_ment_search` / `ai_opt_llm_ment_top_pages` / `ai_optimization_llm_response`. A piece that becomes the canonical answer to an uncited question is disproportionately valuable — LLMs cite structured, sourced, definitive content.

### B4. Freshness / timely
- Seasonal demand (`kw_data_google_trends_explore`), a just-launched feature worth a piece, or a recent shift in the space (a competitor pricing change, a platform API change). Timely pieces age slower and earn shares.

### B5. Tool demand (run this sweep every time)
The highest-value candidates this engine can find are **tool queries**, and they never show up if you only sweep article modifiers. Run an explicit pass for them:

- **Modifier sweep** — `dataforseo_labs_google_keyword_suggestions` seeded with your clusters and filtered to tool intent: `calculator`, `generator`, `checker`, `check my`, `converter`, `tool`, `free tool`, `template maker`, `audit`, `grader`, `analyzer`, `lookup`, `estimator`, `simulator`, `preview`, `validator`, `tester`. **No volume floor on this sweep** — tool candidates are routinely low-volume with high link-draw, and a shared floor deletes them before anyone sees them. (No keyword tool: autocomplete scrapes of `[cluster] + <modifier>`.)
- **The article-on-a-tool-query tell** — for each tool-intent keyword with volume, check what actually ranks. **If the top 10 are articles explaining a calculation people would rather just run, that is the strongest opportunity in this skill.** Flag it loudly; a working tool on that SERP wins on utility, not on word count.
- **Competitor tool audit** — pull competitors' `/tools`, `/calculators`, `/free` paths (`dataforseo_labs_google_relevant_pages`, or a sitemap scan) and read which of their pages earn the most referring domains. Tools usually top that list, which tells you both what the space links to and what you can beat.
- **Link-magnet read** — tool pages are judged on referring domains as much as traffic. A 100/mo keyword whose ranking tool has 200 referring domains is a *better* candidate than a 2,000/mo article keyword with none.

Merge into one candidate list. Dedup against Step A.

---

## Step C — Score the candidates

Score each on six axes. Keep it lightweight — a 1-5 per axis, summed, is enough to rank. Don't build a spreadsheet; build a ranked shortlist.

| Axis | What it measures | High score when |
|---|---|---|
| **Winnability** | Are we in this keyword's league? | It's in our playable bucket; top-10 SERP has weak/thin pages or forums. The live SERP overrides the bucket in both directions |
| **Traffic potential** | Size of the cluster, not just the head term | TP ≥ 500; one keyword gates many long-tail variants |
| **Conversion intent** | How close to buying | Commercial/transactional > informational; "best X tool" > "what is X" |
| **Strategic value** | Authority / links / AI-citation draw | Original data, contrarian POV, or fills an AI-citation gap |
| **Data angle** | Can *our own* data settle this? | We hold a first-party number on the topic, or ours crosses with a public dataset to make a claim nobody else can make (`proprietary-data.md` §1, §3) |
| **Effort** | Inverse — cheaper is better at equal value | Reusable structure, data already in hand (penalize 3-day data studies unless value is high) |

**Tie-breakers, in order:** measured demand → conversion intent → winnability → traffic potential. A commercial keyword beats an informational one at the same bucket almost every time — and a candidate carrying real GSC impressions beats one carrying a tool's volume estimate, because the demand is confirmed and the site already has a foothold in the SERP. Score winnability off your actual average position when GSC has one; KD is a proxy for exactly this and you have the real thing.

**The data-angle axis is a real axis, not a bonus point.** A topic your own database can settle is a piece the top 10 structurally cannot match — that's a durable ranking and citation advantage that survives core updates, where a keyword-difficulty edge doesn't. Answer engines have unlimited synthesis and a permanent shortage of new observation; a candidate you hold data on is you selling into that shortage. So at equal score, take the one with the data angle, and note in the shortlist row *which* number or combine you'd use — a data angle nobody can name isn't one. Run the §1 hunt against the shortlist, not after the pick, or you'll discover the good angle one step too late.

**Scoring tool candidates (type 10).** The rubric under-rates tools by default: the effort axis penalizes them for a build, and the traffic axis misses that a tool compounds instead of decaying. Correct for it explicitly:

- **Strategic value: score 5 by default.** A tool is the highest link-draw, longest-compounding, most AI-citable asset in the catalog. It also earns repeat visits and brand searches, which no article does.
- **Effort: score it honestly, then apply the one-run test.** A client-side calculator is often *cheaper* than a 2,000-word researched guide — score it accordingly, don't reflex-penalize "code." A live-fetch analyzer with vendor cost is genuinely expensive; score that low and mean it.
- **The one-run test is a gate, not an axis.** If a working v1 can't ship in this run, the tool doesn't go on the shortlist as a tool at all — it goes on as its prose fallback (type 7 or 2) with the tool queued as the top backlog candidate plus a scoped spec.
- **Volume matters less here.** Judge tool candidates on referring-domain potential and repeat use, not on monthly search volume alone.

### Step C.5 — Saturation penalty (the anti-monoculture guard)

The five axes reward the same proven vein every run — same type, same template, same cluster shape — because it's maximally winnable, on-positioning, and low-effort once the recipe exists, so it out-scores every first-of-its-kind piece. Left unchecked, the engine ships **one vein forever**: a fragile monoculture (a single core update aimed at that template hits the whole library at once) that never ships the types a climbing-DR site needs most — data studies, comparisons, opinion — the linkable, AI-citable ones. This is explore/exploit collapse, and nothing else in the rubric prevents it (type-follows-SERP *can't*: a saturated vein's queries all share one SERP shape, so "correct type" stays constant — type diversity is downstream of topic diversity).

Before ranking, read the **last 6 `Shipped` rows** and classify each by **type** and **vein** (the topical template — e.g. "how to read [document]", "how to organize [thing]"). Then:

1. **Penalize the saturated group.** If a candidate's type OR vein already covers **≥3 of the last 6** shipped pieces, subtract **−2**; **≥5 of the last 6, or 4+ consecutive**, subtract **−4**. This lets a genuinely different piece win at lower raw winnability — which is the entire point.
2. **Reserve an explore slot.** The selection shortlist MUST include **≥1 explore candidate**: a different *type* AND a different *vein* than the last 3 pieces, even if its raw score is lower. Surface it at the checkpoint as the explicit alternative, with an honest read of its winnability (don't dress up a doomed pick to look diverse).
3. **Escalate after a long run.** Once the same vein has shipped **4 in a row**, the explore candidate becomes the **recommended** pick (#1), not just an option. The user can still choose to keep mining — their positioning instinct overrides — but the default flips from exploit to explore.

**Tools and the guard, both directions.** A **tool is a type like any other** — nine tools in a row is a monoculture too, and it gets the same penalty. But the far more common failure is the opposite: an engine that has shipped **nine prose pieces and zero tools** while tool-intent keywords sat in the pool unbuilt. So: if **no tool has shipped in the last 6 pieces** and B5 surfaced any viable tool candidate, that candidate takes the explore slot. If **no tool has shipped in the last 10**, it becomes the recommended #1. A content library with no tool in it has no link magnet, and DR stops climbing.

The vein is not wrong to mine; it's good SEO. This rule only stops it from becoming the *only* thing, and forces the higher-leverage types onto the slate before the vein exhausts itself.

Write the **full scored shortlist** to the `## Candidate backlog` section of `.seo/content-ledger.md` — including the saturation penalty applied to each row and which candidate is the explore slot. Next run reads this first and only re-scores if it's >30 days old or the user says "re-research." This is what makes each run start warm instead of cold.

---

## Step D — Choose the TYPE

The type is **not** a free choice. It's dictated by intent × SERP shape × goal. Run a live SERP read on the chosen keyword (`serp_organic_live_advanced`, or fetch the top 10 as text) and read what's actually ranking.

Quick selection logic (full catalog + structure in `content-types.md`):

| Signal in the SERP / query | Type to write |
|---|---|
| Query is "how to X"; top results are step-by-step | **How-to / tutorial** |
| Query is "best X" / "X tools" / "N ways"; top results are listicles | **Listicle / roundup** |
| Query is "what is X" / "X meaning"; snippet box present, short pages rank | **Definition / answer page** |
| Broad commercial-investigation head term; top results are long pillar pages | **Pillar guide** |
| "X vs Y" or multi-tool decision; top results compare options | **Comparison** |
| Nobody in the top 10 has original numbers; topic is data-shaped | **Data study / original research** |
| "X calculator" / "X generator" / "X checker" / "free X tool"; people want to *run* something | **Free tool (interactive)** — see `free-tool-pages.md` |
| Tool-intent query where the top 10 are only *articles about* the calculation | **Free tool (interactive)** — the best opportunity in this skill |
| "X template" / "X examples" / "X checklist"; people want a usable asset | **Resource / template library** (but check the tool row first) |
| Theme-led, low keyword volume, high authority/AI-citation value | **Opinion / POV** |
| "How [company] does X" / teardown intent | **Case study / teardown** |

**The override rule:** when the SERP format and the query phrasing disagree, follow the SERP. Google has already decided what it rewards for that query. Writing a tutorial into a listicle SERP is a losing bet no matter how good the tutorial is.

**The one exception — tool intent.** Follow-the-SERP has a single documented override, and it runs *toward* type 10, never away from it. If the query has tool intent and the top 10 are all articles, that is not Google saying "it wants an article" — it's Google ranking the best of a weak field because nobody built the tool. Ship the tool. (Follow-the-SERP still holds in the other direction: a tool-shaped *idea* on a query whose SERP is genuinely informational is a tool nobody will search for.)

**Feasibility gate for type 10.** Before a tool goes on the shortlist, answer the four questions in `free-tool-pages.md` §2 — capability, data freshness, cost/abuse surface, maintenance — and carry those answers into the checkpoint. Any "unknown" means it isn't ready to be this run's piece.

If two types both fit (e.g. a guide *with* an embedded data study), pick the primary type for structure/schema and fold the secondary in as a section.

---

## Output of this step

Hand the Step 2 selection checkpoint (`select.md` §6):
- **The measurement line** (GSC connected) — one line summarizing the measure step: how many shipped pieces are winning / close / wrong-query / invisible, and any index problem found. Boring is fine; silence is not.
- **Top 3 candidates**, each with: title, target keyword, volume, **difficulty bucket** (and whether it's your playable bucket or a stretch), measured GSC impressions + current position where they exist (better than any estimate), intent, SERP-format read, proposed type + one-line why.
- **The boost option**, when the measure step found one worth more than a new piece — with its measured position, impressions, and CTR, and an honest call on which is the better use of the run.
- **The tool state** — one line: how many of the last 6/10 pieces were tools, whether B5 surfaced a viable tool candidate, and (if a tool is on the slate) the four feasibility answers plus what v1 does in one sentence.
- **The data angle per candidate** — one line each: the first-party number or combine that piece would carry, and whether getting it needs a production query the user has to approve. "None found" is a legitimate answer and worth saying out loud.
- **The saturation state** — one line naming the dominant recent type/vein and how many of the last 6 pieces it covers, so the user sees *why* an explore candidate is on the slate.
- **At least one explore candidate** among the three (per Step C.5) — a different type AND vein than the last 3 pieces. After a 4-in-a-row vein, mark it as the recommended #1.
- Your recommended pick clearly marked.

Then let the user confirm or redirect. Their positioning instinct is a legitimate tie-breaker the data can't see — including the instinct to keep mining a vein the guard would rotate away from.
