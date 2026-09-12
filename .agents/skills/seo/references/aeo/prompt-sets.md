<!-- sources: aeo/references/prompt-sets.md (verbatim; state + reference paths remapped to .seo/) -->
# Phase 1: The prompt set

Prompts are the instrument. A badly built instrument produces clean-looking numbers that mean nothing, and you will not notice for months because the output looks the same either way.

Output of this phase: `.seo/aeo/prompts.json`.

---

## 1. The coverage principle

You cannot enumerate every way a buyer might phrase a question. The same person chasing the same outcome reaches it three different ways: a long multi-turn conversation where earlier turns shape the answer, one dense prompt loaded with constraints, or a personalized exchange where the platform already knows half the context.

You are not trying to match real phrasing word for word. You are trying to get **coverage**: enough varied, representative prompts per attribute that no single phrasing can wreck the read.

**Why this is not optional.** Hold everything constant in a category question and swap only the label for the category, and the set of brands recommended changes substantially. The label selects a different slice of the web, and different slices have different consensus. A program running one prompt per attribute is measuring the label, not the brand.

So: **treat every attribute as a portfolio.** Individual prompts do the measuring. The attribute rollup is the number you act on. Drill into a single prompt only to explain a surprise in the rollup.

---

## 2. The six types

Each type answers a different strategic question, and each has a pass criterion. A response that fails its type's criterion is not weak data, it is not data. Discard it and fix the prompt.

### Discovery

**Asks:** would an engine put you in the consideration set?
**Pass criterion:** the response returns a list of brand names.

```
What are the best [category] [tools|platforms|providers|software|services] for [segment / use case]?
```

The trigger noun is what makes this work. Without it you get advice instead of vendors:

| Prompt | Returns |
|---|---|
| "What are the best 3PL providers for a retail D2C business?" | brands. Good. |
| "What email marketing software would you recommend for a mid-size SaaS?" | brands. Good. |
| "How do I improve my email marketing?" | tips. Not discovery data. |
| "Tell me about 3PL trends this year" | analysis. Not discovery data. |

Discovery is the spine of the audit. It is also the type people over-index on, so build it properly and then build the others.

### Head-to-head

**Asks:** when it comes down to you and one named rival, who wins?
**Pass criterion:** a recommendation, not a hedge.

Three ingredients, all required:

1. a specific use case
2. two named brands
3. an explicit ask for a recommendation

```
I need a [category] for [specific use case with a constraint].
Would you recommend [Brand A] or [Brand B]?
```

"Compare X and Y" is too soft, because it produces a balanced table and a hedge that you cannot score. The use case is what forces a side.

A real buyer arrives at this comparison through a winding conversation rather than typing it. You cannot reproduce that path, and you do not need to: asking the comparison directly gives a clean read on the underlying question, which is whether the accumulated evidence favors you or them for that job.

Track this per platform. Losing on one engine and winning on the others usually points at a specific citation gap, not a positioning problem.

### Capability

**Asks:** does the engine know you do this at all?
**Pass criterion:** a yes or no about your brand.

```
Does [Brand] offer [specific capability]?
```

That is the whole prompt. No comparison, no alternatives, no list.

This is the most under-used type and it is half of the routing diagnostic. When discovery comes back empty for an attribute, the instinct is "the engine has not read enough about us, write more content." That is a guess, and it is wrong roughly half the time. The capability prompt turns the guess into a diagnosis:

- Capability says **yes**, discovery says **absent**: the engine knows and will not recommend you. Content will not fix this. It is a trust problem and the work is off-page.
- Capability says **no**, discovery says **absent**: the engine does not know. It is a comprehension problem and the work is on-page.

Two completely different programs of work, and no other signal separates them.

Watch for the flattering false positive. An engine will sometimes answer "yes" by generalizing from your category rather than from evidence about you. Score a capability response as a real yes only when it names something specific: how it works, where it appears, what it is called. A bare "yes, [Brand] offers that" alongside no specifics is a **soft yes** and should be recorded as such.

### Fact check

**Asks:** is what the engine says about you true?
**Pass criterion:** a checkable claim that can be scored against `.seo/truth.md`.

```
What does [Brand] cost?
What does [Brand] integrate with?
Does [Brand] support [specific requirement]?
What are [Brand]'s plan limits?
```

This is a different discipline from everything else in the set. It has nothing to do with perception and everything to do with whether the sources feeding the answer carry correct information. Score each response against the truth file as `correct`, `wrong`, `outdated` or `missing`, and record the citations, because the citations tell you where the wrong claim came from and therefore whether the fix is on-page or off-page.

Prioritize the claims where a wrong answer costs a deal: price, the integrations you do not have, the compliance posture, the plan gates. A confident wrong answer is more expensive than absence, because the buyer disqualifies you without ever asking.

### Perception

**Asks:** how does the engine characterize you?
**Pass criterion:** an evaluation with named strengths and weaknesses.

```
Evaluate [Brand] as a [category]. What are the pros and cons?
What type of customer is [Brand] best suited for?
What is [Brand] best known for?
```

Tag perception prompts by attribute so you can follow the thread per capability. A single blended sentiment score hides the signal: strong perception on one attribute and weak on another averages to "fine," which is not actionable. Per-attribute perception is.

Read the positive side as carefully as the negative. When an engine consistently praises something the team takes for granted, and the citations trace to reviews and third-party coverage rather than your own marketing, the market values that capability more than your positioning does. That is a positioning finding, not just an AEO one.

### Category framing

**Asks:** is the buying framework built for you?
**Pass criterion:** evaluation criteria for the category, with no brand names required.

```
What is [category] and how should I think about evaluating one?
What should I look for when choosing a [category]?
```

You are not chasing your brand here. You are reading which features the engine treats as table stakes, which it treats as differentiating, and which criteria it hands an undecided buyer.

This catches a failure mode nothing else does. You can be perfectly visible in a category and still lose at the decision, because the criteria the engine gives buyers are the ones your competitors lead on. Category framing is upstream of visibility, and losing there is a brand-level problem with a brand-level fix: content that shapes how the category itself is explained.

---

## 3. Build the portfolio

For every **priority 1** attribute, write 5 to 8 discovery variants that differ along these axes. Vary one or two axes at a time, not all of them at once, or you cannot attribute a swing to anything.

| Axis | Vary it like this |
|---|---|
| **Category label** | Every name for the thing: the buyer's word, the product team's word, the analyst's word, the older word. This axis moves results the most. Always include the label you dislike. |
| **Persona** | Who is asking. A VP of marketing at an enterprise, a solo founder, an agency owner. |
| **Segment** | What kind of company or household. Size, stage, industry, region. |
| **Use case** | The job to be done, stated concretely. |
| **Superlative** | "best" / "top" / "most recommended" / "what should I use" / "who are the leaders in" |
| **Framing** | Product-seeking ("what tools do X") versus job-to-be-done ("I need to do X, what should I use") |
| **Constraint** | One hard filter: budget, team size, a required integration, a compliance requirement, a platform |

Then per attribute add: 1 to 2 head-to-head prompts per main competitor, 1 to 2 capability prompts, and 1 perception prompt. Add category framing prompts once per category, not per attribute.

For **priority 2**, cut discovery to 3 variants and keep one capability prompt. The capability prompt is the one that must survive the cut, because without it the attribute cannot be routed.

For **priority 3**, one discovery prompt. Label every number derived from it **indicative** wherever it appears.

Fact-check prompts scale with the truth file, not with the attribute list. Cover every claim where a wrong answer costs a deal.

---

## 4. QA every prompt before it enters the set

Five minutes here prevents months of building on a broken foundation. Run each new prompt once, read the response, and check three things.

### Intent alignment

Did the engine interpret the question the way you meant it? Did it read a capability prompt as a discovery prompt? Did it resolve a vague term in a way you did not anticipate?

**Alignment is not bias.** Clarifying what you are asking is correct. Steering toward the answer you want is not. "Which AEO platforms named [Brand] have great visibility?" is a leading question and the data it produces is worthless. Ask the question that reflects the intent you are measuring, never the answer you are hoping for.

### Ambiguity

If a term can mean different things in different contexts, the engine will pick one, or blend several, and you will not know which. Acronyms are the main offender because you know what you mean by them.

| Ambiguous | Resolves to | Fix |
|---|---|---|
| "best GEO platforms" | geographic information systems, geothermal energy, or generative engine optimization | Expand on first use: "GEO (Generative Engine Optimization) tools" |
| "best CRO tools" | conversion rate optimization, or tools for a Chief Revenue Officer | Name the discipline explicitly |
| "best attribution platforms" | marketing attribution, or security attribution | Add the domain |
| "content management platform" | CMS, headless CMS, or digital asset management | Name the category precisely |

In a real conversation the ambiguity self-resolves on the next turn. In a tracked prompt there is no next turn, so whatever the engine parsed on the first read is the data you collected. Resolve it up front. This is disambiguation, not steering.

### Format match

The response format has to match the type. When it does not, the prompt drifted, even if the answer reads as reasonable. This is a different failure from ambiguity: here the engine understood the question and answered it as a different type.

| Symptom | Cause | Fix |
|---|---|---|
| Discovery returns tips instead of brands | missing trigger noun | Add "tools", "software", "platforms", "providers" |
| Head-to-head returns "it depends" | missing use case | Add the specific scenario that forces a side |
| Capability returns a list of alternatives | not direct enough | Reframe as a yes-or-no about the named brand |
| Perception returns a brand list | acting as discovery | Ask explicitly for an evaluation with pros and cons |
| Category framing returns brands only | asked "who" not "what" | Ask what the category is and how to evaluate it |
| Fact check returns a hedge | the claim is not specific enough | Ask for the specific number, plan or integration |

Record QA status per prompt in `.seo/aeo/prompts.json`. A prompt that fails QA twice gets cut, not carried.

---

## 5. Sampling

Answer engines are non-deterministic. The same prompt on the same platform on the same day returns different brand sets. Sample size is therefore part of the prompt set design, not an afterthought.

| Tier | Variants | Platforms | Samples per prompt per platform |
|---|---|---|---|
| Priority 1 | 5 to 8 discovery + capability + head-to-head + perception | every reachable one | 3 |
| Priority 2 | 3 discovery + capability | 2 | 2 |
| Priority 3 | 1 discovery | 1 | 1, labelled indicative |

Hold the sampling plan constant across runs. A rate that "improved" because you sampled it more thoroughly this time is the easiest way to mislead yourself and your leadership. If you change the plan, say so in the report's method section and treat the prior baseline as broken for that attribute.

`references/aeo/measurement.md` has the margin-of-error table that says whether a run-over-run difference is real.

---

## 6. Storage

Write `.seo/aeo/prompts.json`:

```json
{
  "version": 1,
  "generated": "2026-08-26",
  "sampling": { "p1": {"platforms": 4, "n": 3}, "p2": {"platforms": 2, "n": 2}, "p3": {"platforms": 1, "n": 1} },
  "prompts": [
    {
      "id": "disc-crm-agency-01",
      "attribute": "CRM for agencies",
      "priority": 1,
      "type": "discovery",
      "text": "What are the best CRM platforms for a 20-person marketing agency that needs client reporting?",
      "axes": { "label": "CRM", "persona": "agency owner", "segment": "20-person agency", "constraint": "client reporting" },
      "qa": { "status": "pass", "checked": "2026-08-26", "note": "returns brands on all four platforms" }
    },
    {
      "id": "cap-crm-agency-01",
      "attribute": "CRM for agencies",
      "priority": 1,
      "type": "capability",
      "text": "Does [Brand] support client reporting for agencies?",
      "pairs_with": "disc-crm-agency-01",
      "qa": { "status": "pass", "checked": "2026-08-26" }
    }
  ]
}
```

`pairs_with` is what lets Phase 3 build the routing matrix automatically. Every priority 1 and 2 discovery prompt needs a paired capability prompt. A discovery prompt with no pair cannot be routed, and an unroutable finding turns into "write more content" by default, which is the thing this whole design exists to prevent.
