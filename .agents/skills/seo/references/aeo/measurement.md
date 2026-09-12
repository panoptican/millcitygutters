<!-- sources: aeo/references/measurement.md (verbatim; state + reference paths remapped to .seo/) -->
# Measurement

The discipline that separates a program from a dashboard. Most of this file exists to stop you from believing a number that is not there.

---

## 1. The metrics

**Mention rate.** Responses naming your brand, over responses sampled, for one attribute. Always printed with its denominator: `42/60 (70%)`. A bare percentage is not a measurement, it is a claim.

**Rank.** Your position when every brand mentioned across those responses is sorted by mention count.

**Share of voice.** Your mentions over all brand mentions in that set, as a percentage. Rank tells you the ordinal, share of voice tells you the gap. Being second at 30% when the leader is at 32% is a different situation from being second at 30% when the leader is at 61%, and rank alone hides the difference.

**List position.** Where you appear inside an ordered response, averaged over responses that returned one. Softer than the others and worth keeping, because moving from last-named to first-named is real progress that mention rate cannot see.

**Capability recognition.** The share of capability prompts answered yes, with soft yes counted separately. This is a diagnostic input, not a headline metric.

**Accuracy rate.** Truth-file claims answered correctly, over claims tested. The one metric where the target is 100% and anything else is a defect.

**Sentiment themes.** Not a score. A ranked list of the named pros and named cons appearing across perception responses, with their frequency. A blended sentiment number averages a strength and a weakness into "fine" and destroys the only actionable part of the signal.

---

## 2. How much movement is real

Answer engines are non-deterministic. Every rate you compute is an estimate with an interval around it, and reading noise as progress is the fastest way to lose credibility with whoever funds this work.

**Margin of error on a single rate**, 95% confidence, worst case:

| Responses sampled (n) | Margin of error |
|---|---|
| 10 | ±31 points |
| 20 | ±22 points |
| 30 | ±18 points |
| 60 | ±13 points |
| 100 | ±10 points |
| 200 | ±7 points |
| 400 | ±5 points |

**Comparing two runs is harder than reading one.** The interval on a *difference* between two independently sampled rates is roughly 1.4 times the single-rate interval. At n=60 in each run, a change smaller than about 18 points is not distinguishable from noise.

**Which n applies.** A priority 1 attribute at 6 variants times 3 samples gives n=18 per platform and n=72 rolled up across four platforms. So:

- **Per-platform numbers are noisy.** At ±23 points, a per-platform reading supports a qualitative statement ("we are weak on this engine") and not a quantitative one ("we went from 44% to 51% on this engine").
- **The cross-platform rollup is the number to trust**, and it is the number that belongs in the report headline.

**Three rules that follow:**

1. Never call a change real unless it exceeds the difference interval, or it persists across two consecutive runs in the same direction. Persistence is the cheaper test and usually the better one.
2. Never report a priority 3 number without the word **indicative** attached. At n=1 the interval covers essentially the whole range.
3. Hold the sampling plan constant. A rate that rose because you sampled it more carefully this time is the most embarrassing possible finding to have to retract.

---

## 3. Three layers

No single number answers "is this working." Three layers do, and each answers a different question with a different level of confidence.

**Layer 1: Visibility. "Do the engines mention us?"**
Mention rate, rank, share of voice, citation share, accuracy, sentiment themes, crawler hits. Directly measurable, highest confidence, and the leading indicator. Everything in this skill's report lives here.

**Layer 2: Traffic. "Is that turning into people arriving?"**
Referral traffic from answer-engine hosts, organic search traffic, and direct traffic. Referral volume from AI hosts is usually small and will understate the effect badly, because most influence never produces a click. Watch direct traffic alongside it: influence that produces no referral often produces a visit typed straight into the bar days later.

**Layer 3: Revenue. "Is this driving business?"**
Pipeline, conversions, revenue. The least precise layer and the one leadership asks about. Two imperfect instruments used together beat either alone:

- **Self-reported attribution**: a "how did you hear about us" field on the signup or demo form, with the answer engines listed explicitly as options. Imperfect, and it captures what a buyer *remembers influencing them*, which is exactly the thing click data structurally cannot see.
- **Conventional attribution**, as a cross-check.

The honest framing for anyone asking: layer 1 is measured, layer 2 is observed, layer 3 is triangulated. Say which is which. A program that presents all three with equal confidence gets disbelieved on all three the first time one is wrong.

**Visibility is also a diagnostic.** When traffic and revenue fall, layer 1 tells you whether answer engines are the cause or a bystander. Visibility steady while down-funnel metrics drop means the problem is elsewhere: conversion, sales, the product. Visibility falling alongside them means you have found it.

---

## 4. Goals

Split goals into two tiers, because tying a single content change to revenue is a chain that will not hold and everyone will know it.

**Program level.** Overall rank across priority 1 attributes. Combined organic plus AI-referral traffic. Self-reported attribution share. Accuracy rate at 100%.

Do not anchor a program goal to AI referral traffic alone. That number is driven as much by product decisions at the engines, such as whether they render links at all, as by anything you do. A platform change can erase it overnight through no fault of the program.

**Campaign level.** Mention rate and rank for the specific attribute targeted. Citation rate for the specific pages shipped. Movement in a specific named objection.

Keep revenue at the program level and keep campaigns measured on visibility. That separation keeps campaign goals achievable and keeps anyone from drawing a straight line from one page to a pipeline number, which is a line that will not survive scrutiny.

---

## 5. Attribution to inputs

A rate that rose with no record of what changed is a number you cannot repeat, defend, or brief anyone on.

Every run, append to `.seo/aeo/worklog.md`:

```
## 2026-08-26
- [on-page]   Rewrote /pricing lead answer for extraction        closes OPP-03   recheck 2026-09-23
- [on-page]   Added FAQ to /integrations/slack from real prompts  closes OPP-07   recheck 2026-09-23
- [technical] Removed CCBot block from robots.txt                 closes TECH-01  recheck 2026-09-09
- [off-page]  Brief sent to partner: correct category on their integrations page  closes OPP-04  no ack yet
- [off-page]  Requested correction of stated price on [review site]  closes ACC-02  submitted 2026-08-26
```

Then in the next run's report, put inputs and movement side by side, and describe the relationship in the language it deserves:

> Removed the `CCBot` block on 2026-08-26. Crawler hits from three agents began appearing on 2026-09-02. Mention rate for "CRM for agencies" moved 44/72 to 51/72, which is inside the noise interval at this sample size. Consistent with the change having worked, not yet evidence of it. Recheck next run.

That paragraph is more persuasive than a confident causal claim, because a reader can check it. Confident causal claims from one observation get audited once and then discounted forever.

---

## 6. Cadence

- **Measure** every two to four weeks. Daily readings are noise and burn budget.
- **Re-verify a specific attribute** three to four weeks after shipping a change for it. Engines re-crawl and re-form consensus slowly, and off-page changes are slower than on-page ones.
- **Rebuild the prompt set** quarterly, or whenever the product or positioning shifts. New capabilities need new attributes. Retire prompts that have been at ceiling for three runs: they cost budget and tell you nothing.
- **Re-derive the truth file** whenever pricing, plans or the integration list changes. A stale truth file turns accurate answers into false accuracy failures, which wastes a whole cycle chasing a defect that does not exist.
