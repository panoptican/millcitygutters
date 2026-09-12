<!-- sources: aeo/references/offpage.md (verbatim; state + reference paths remapped to .seo/) -->
# Phase 5b: Off-page execution

For findings routed to **trust**. Your site is one input among many. When an engine describes your brand it synthesizes your pages, review platforms, partner pages, comparison articles, directories and community threads. You wrote one of those.

Off-page work is influencing enough of the rest that the consensus reflects your positioning instead of the web's accumulated approximation of it.

**This skill produces assets and stops.** It writes the battlecard, the inventory and the briefs. A human sends them. No emails, no posts, no comments, no review submissions, no edits to anyone else's property, regardless of what tooling is connected.

---

## 1. The battlecard

Before any outreach, one document that tells everyone doing that work what you want said. Without it, outreach produces inconsistency, and inconsistency is the thing answer engines punish most directly.

`.seo/aeo/battlecard.md`, written from `assets/battlecard.template.md`, three sections:

**Ideal positioning.** Who you serve, what you solve, why you win, in the plain words an engine would actually use. Not internal vocabulary, not aspirational copy. If your battlecard says "the operating system for revenue teams," every mention you influence will say that, and no buyer searches for it.

**Attributes to promote.** The specific things you want more visibility for, each with suggested phrasing. Give people the exact sentence to request. Left to paraphrase, five sources produce five different approximations, and five approximations do not corroborate each other.

**Objections to reframe.** Each negative theme with its specific reframe. What you want said instead, and why that framing is more accurate. Not a denial.

The battlecard does two jobs. It aligns anyone doing outreach, and it is the reference you hold every existing mention up against.

---

## 2. Inventory what already exists

Pull every external source that mentions you, from the citation data and from a direct search. For each, work through six questions:

1. **Does the description match the battlecard?** A partner page written two years ago may still carry positioning you abandoned. A directory may have you in the wrong category outright.
2. **Is the language stale?** Broadly accurate and written before your current capabilities, before a rebrand, or before you entered a market. Once-correct language becomes actively misleading.
3. **Does it mention your target attributes?** A source that references you but omits the attribute you are trying to build is the cheapest win available. It is already in the engine's source material. It just needs the right sentence added.
4. **Does it carry an objection?** If so, is the framing accurate, and is there a realistic path to changing it without asking anyone to misrepresent something?
5. **Are the facts right?** Score against `.seo/truth.md`. A wrong price on a widely-cited comparison page is a direct revenue leak and it outranks everything else on this list.
6. **Do you have a relationship?** Partner, affiliate, investor, customer, integration directory. If yes, priority. The ask is low-friction because the relationship exists.

Write `.seo/aeo/mentions.md` from `assets/mentions.template.md`.

---

## 3. Three tiers, in this order

The order follows the friction gradient. Updating something that already mentions you is easier than getting added to something that does not, which is easier than creating a new source and waiting for it to earn enough authority to be cited.

### Tier 1: optimize what already mentions you

The highest-yield and most-skipped work in the whole program.

In link-based SEO, third-party mentions were about the link. Whether the site mentioned you and whether it linked back was the signal; what it actually said was secondary. That has inverted. A partner page that links to you and describes you with abandoned positioning, or files you under the wrong category, is actively feeding a narrative you do not want.

Prioritize by relationship: integration partners, then affiliates, then investors and advisors, then industry associations and analysts. The first three are routine asks between people who already work together. The last is slower and higher authority, and worth running in parallel rather than after.

### Tier 2: get added where you are absent

Stream B told you where competitors are cited and you are not. Those sources are doing influence work for them right now.

- **Comparison articles and listicles.** Effective today. Expect increasing scrutiny over time, the way thin comparison content eventually got discounted in search. Do not build the whole strategy on one format.
- **Category directories** your buyers use for vendor discovery. Absence here is a straightforward gap with a straightforward fix.
- **Integration partner pages.** For every integration you ship, there should be a page on their site describing it accurately. Many do not exist. Many are wrong.
- **Review platforms.** Presence and accuracy both matter. Being listed and described incorrectly is a version of the same problem, and it is often worse than absence because it is authoritative-looking and wrong.

### Tier 3: create new sources

Where coverage is thin, outdated or missing, new content has a real path to being cited. The citation data tells you which topics and formats engines already draw from in your category, so this is targeted rather than speculative.

- **Original research and data.** A dated, sourced, first-party number is a new observation about the world. Models hold effectively unlimited synthesis and have a permanent shortage of new observation, which is why original data is the single most durable asset here. It also earns coverage, which creates further sources.
- **Guest and co-authored content** on domains that already carry citation authority in your category.
- **Genuine community participation.** If community threads are disproportionately cited for your attributes, real participation is a real investment. The word doing the work is genuine.

---

## 4. The line

Non-negotiable, and stated plainly because this is where AEO advice most often goes wrong.

**Never do these:**

- Astroturfing. Sockpuppet accounts, fake community posts, manufactured discussion. It violates every platform's rules, it is detectable, and it poisons the exact signal you are trying to build.
- Incentivized or fabricated reviews. Illegal in many jurisdictions, against every review platform's terms.
- Asking a source to say something untrue, including something merely flattering-but-unsupported.
- Mass unsolicited outreach. Templated volume gets you filtered and remembered badly.
- Paying for a mention without the disclosure the venue requires.

A real answer to a real objection, from a named person who knows the product, outperforms a template, because a template has to stay vague about weaknesses. That vagueness is the tell people scroll past.

The most durable off-page work is upstream of individual citations: do things worth talking about, publish original research, and distribute it properly. Chasing individual placements is whack-a-mole at any real scale. It is a reasonable way to start when you are near zero, and a bad plan to still be running in a year.

---

## 5. The brief

One per ask. The skill writes it, a human sends it.

```markdown
### Brief: [Source name] — [URL]
**Relationship:** integration partner (since 2024) · **Contact:** [who the user knows there]
**Closes:** OPP-04

**Currently says:**
> "[Brand] is a project management tool for small teams."

**Problem:** wrong category and wrong segment. We are not a project management tool,
and the segment is backwards. This page is cited in 11 of 72 discovery responses for
our category, so it is actively shaping the wrong answer.

**Requested:**
> "[Brand] is a client reporting platform for agencies. It connects to [Partner] to
> sync project data into automated client-facing reports."

**Why it is accurate:** matches our positioning, matches the integration as built
(`app/integrations/partner/`), and describes what their users actually use it for.

**Ask:** one-line description update on the integrations page. No link change needed.
**Effort for them:** two minutes.
```

The brief works because it is specific, it is short, it is accurate, and it asks for one small thing. Contrast with "could you update our description," which requires the recipient to do the thinking and therefore does not get done.

---

## 6. Log it

Every brief sent goes into `.seo/aeo/worklog.md` with its date and finding ID. Off-page changes take weeks to reach answers, and without the send date you cannot tell a change that has not landed yet from one that did not work. Those two need very different responses.
