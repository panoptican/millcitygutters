<!-- sources: aeo/references/diagnose.md (verbatim; state + reference paths remapped to .seo/) -->
# Phase 3: Diagnose

The phase that decides where the work goes. Getting it wrong is how teams spend six weeks writing content to close a gap that content cannot close, then conclude the whole discipline does not work.

Output of this phase: `.seo/aeo/findings.md`, then `.seo/aeo/report.md`.

Every finding gets a stable ID. The gameplan references these IDs, the worklog references them, and the next run's report can say "OPP-03, opened three runs ago, closed." Without stable IDs the program cannot show its own history.

```
TECH-nn   technical readiness failure
ACC-nn    accuracy failure
OPP-nn    opportunity: an attribute where you should be present and are not
OBJ-nn    objection: a recurring negative theme
STR-nn    strength: something working, worth defending
```

---

## 1. The three gates

A page contributes to an answer only by clearing three gates in order. Each failure has a different fix and they are not interchangeable. Diagnose the gate before diagnosing anything else.

### Reachable

**Question:** can the engine fetch and read it?

**Evidence:** crawler hits in the logs, `robots.txt` verdict per agent, server-rendered body text present, status 200, no `noindex`, indexed in Search Console.

**If it fails:** stop. Fix this first, and do not spend a single hour on content or outreach for this page until it clears. Work done above a failed reachability gate is entirely wasted, and it is wasted invisibly, which is worse.

Distinguish the causes, because they have different fixes: blocked by directive, blocked at the CDN, technically reachable but rendering as an empty shell, or reachable and simply never discovered. The last one is a linking and sitemap problem, not a crawler problem.

### Cited

**Question:** does the engine choose it?

**Evidence:** the URL appears in the citation list of stored responses.

**If it fails while Reachable passes:** the page is being read and passed over. Causes, in the order worth checking: the content restates the consensus and adds nothing, the claims are unsourced, the page is thin relative to what else is available on the query, or the domain has not accumulated enough corroboration to be trusted on this topic. The first is the most common and the least comfortable to hear.

### Quoted

**Question:** does the engine lift a claim from it?

**Evidence:** string-match your page's core claims, distinctive phrasings and specific numbers against the stored response text. This is why raw responses are stored.

**If it fails while Cited passes:** the page is a footnote rather than a source. The claims are not self-contained enough to survive extraction. Score the page with the extractability rubric in `references/aeo/technical.md` and fix the specific dimensions that failed. This is usually a structure problem with a cheap fix and a fast payoff.

---

## 2. The routing matrix

For every priority 1 and 2 attribute, cross the discovery result against its paired capability result. The pair is why Phase 1 requires `pairs_with` on every discovery prompt.

| Discovery | Capability | Reachable | Diagnosis | Route |
|---|---|---|---|---|
| any | any | **fail** | Technical | **Fix reachability.** Nothing else counts until it clears. |
| any | any | pass, but facts wrong | Accuracy | **Fix at the source.** Highest priority regardless of rank. |
| absent | **absent** | pass | The engine does not know you do this | **On-page comprehension.** Create or sharpen the page. State the claim so it can be lifted. |
| absent | **present** | pass | It knows and will not recommend you | **Off-page trust.** More of your own content does nothing here. Get corroborated by sources the engines already cite. |
| absent | **soft yes** | pass | It is generalizing, not recalling evidence | **On-page first**, because the specifics do not exist anywhere yet, then off-page. |
| present, low rank | present | pass | You are in the room, not at the front | **Off-page volume**, plus strengthen the pages already being cited. |
| present, always last | present | pass | Named but buried | **Rank the mention, not the presence.** Off-page volume on the sources that order the list. |
| present, rank unresolved | present | pass | The sample cannot separate you from the pack | **Raise n before acting.** Do not spend a quarter on a rank you have not measured. |
| present, high rank | present | pass | Strength | **Defend.** Keep cited pages fresh, watch for erosion, and check whether a competitor is building toward this. |

**Presence is not standing.** A brand named in every answer and listed last in every answer has a 100% mention rate and is losing. Read mention rate together with rank and with mean list position, and remember that a rank is only a standing if the sample can support one: at small n most brands tie, and a tie is not a lead. `scripts/score.py` refuses to call a tie a strength for exactly this reason.

**Why the comprehension and trust split carries the phase.** Both look identical from the outside: you are absent from the answer. The instinct in both cases is to write more. In the trust case, writing more is close to useless, because the engine already knows the fact and is declining to recommend you on it. The only thing that moves it is corroboration from sources it already trusts. A team that cannot tell these apart routes every finding to the content calendar and gets half the results it paid for.

**Worked example.**

> Attribute: "CRM for agencies", priority 1.
> Discovery: 8/72 (11%), rank 14.
> Capability: "Does [Brand] support agency client reporting?" returns yes on 3 of 4 platforms, with specifics.
> Reachable: pass. `/solutions/agencies` is crawled weekly and indexed.
> Cited: fail. `/solutions/agencies` appears in 0 of 72 discovery responses.
> **Diagnosis: trust gap.** The engines know the capability and will not recommend it. Writing a second agency page will not move this.
> **Route: off-page.** Stream B shows the four sources cited most for this attribute. You appear on none. That is the target list.

Contrast:

> Attribute: "SOC 2 compliant CRM", priority 2.
> Discovery: 0/24.
> Capability: "Is [Brand] SOC 2 compliant?" returns no or uncertain on all platforms.
> Truth file: SOC 2 Type II, completed, per `docs/security.md`.
> **Diagnosis: comprehension.** The fact is true and exists nowhere an engine can read it. There is no security page, and the trust center is behind a form.
> **Route: on-page.** Publish it. This is a one-afternoon fix on a fact you already own.

---

## 3. Opportunities

An opportunity is an attribute where you should be present and are not, with its route attached. An opportunity without a route is not a finding, it is a complaint.

Order by **weight times distance, divided by effort**, then apply two hard overrides: technical failures first, accuracy failures second.

Each one records:

```
OPP-03  "CRM for agencies"                              priority 1
  Now:        8/72 (11%), rank 14, SoV 2%
  Target:     top 5 by rank, mention rate above 40%
  Gate:       Reachable pass · Cited fail · Quoted n/a
  Route:      off-page trust
  Evidence:   capability yes on 3/4 platforms with specifics; 0 citations of /solutions/agencies
              across 72 discovery responses; the 4 most-cited sources for this attribute
              carry 3 competitors and not us
  Effort:     M
  Expected:   rank into the top 8 within two runs if two of the four sources land
```

**Do not rank opportunities by how easy they are to write about.** The bias in every content-led program is toward findings that route on-page, because those are the ones the team can act on alone. Notice it and correct for it explicitly.

---

## 4. Objections

Recurring negative themes across perception responses. Four questions per objection, and the last one is the one people skip.

1. **Is it broad or specific?** Appearing across many attributes is a brand-level problem. Appearing on one attribute is a content problem.
2. **Is it trending?** Compare against prior runs. A new objection has a source you can often find in the citations.
3. **Where does it come from?** Read the citations on the responses carrying it. An objection sourced to one comparison article is a different problem from one sourced to forty reviews.
4. **Is it true?**

That last question decides everything downstream.

**If it is false:** counter it with evidence. Publish the specifics, get the correct information into the sources carrying the error, and note that engines will lag the correction by weeks.

**If it is true:** own it and reframe it. Do not deny it. Denial is the failure mode here and it makes things worse: an engine encounters the objection in third-party sources and your denial on your own site, reads the inconsistency, and the inconsistency itself becomes a signal. If you are genuinely the expensive option, the reframe is what the money buys, not "we are not expensive."

**The reframe is a shift of frame, never a rebuttal.** A page opening with "we do not have a steep learning curve" signals fragility and repeats the objection in your own voice, which is how you end up cited as a source for it. "Most teams are running their first workflow within an hour" makes the same argument by demonstration and gives an engine something quotable that is not the objection.

**Read positive themes too.** When engines consistently praise something the team takes for granted, and the citations trace to reviews rather than your own marketing, the market values that thing more than your positioning does. That is a positioning finding worth surfacing, and it is often the most valuable single line in the report.

---

## 5. Strengths

Never ship a report that is only problems. It reads as alarmism, it gets discounted, and it hides the two useful things strengths tell you.

- **What to defend.** A high-rank attribute erodes if the pages holding it go stale or a competitor invests. Strengths carry maintenance actions, not zero actions.
- **What you underestimated.** An attribute you rank well on and never tracked deliberately is the market telling you something about your product.

```
STR-02  "Email deliverability"                          priority 2
  Now:      54/60 (90%), rank 1, SoV 34%
  Holding:  /guides/deliverability cited in 41 of 60 responses
  Risk:     the guide's benchmark data is dated last year
  Action:   refresh the figures, keep the URL, bump dateModified honestly
```

---

## 6. Two checks people skip

**Pull the full brand list.** Not just you and your named competitors: every brand appearing across your discovery responses, ranked. This routinely surfaces two things. Brands you do not consider competitors are being recommended in your space, which means either the category is being framed more broadly than you think or those brands are winning attributes you have not tracked. And your assumed rival may be absent, which is worth knowing before you spend a quarter on head-to-head content.

**Look for unexpected strength.** Attributes where you appear well and did not plan to. Ask why. The answer is usually a specific page or a specific third-party source doing more work than anyone realized, and it is repeatable once you find it.

---

## 7. Write it

`.seo/aeo/findings.md` holds every finding with its ID, evidence and route. It is the working file.

`.seo/aeo/report.md` is the durable artifact and it is written for a reader who was not here. Format in `references/register.md`.

Carry forward from prior runs: findings that closed, findings still open with how long they have been open, and findings that reopened. A finding open for four runs with no movement is itself a finding, and it usually means it was routed wrong the first time.
