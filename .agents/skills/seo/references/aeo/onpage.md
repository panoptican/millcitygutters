<!-- sources: aeo/references/onpage.md (verbatim; state + reference paths remapped to .seo/) -->
# Phase 5a: On-page execution

For findings routed to **comprehension**. Also the supporting half of objection work, and the maintenance half of strengths.

The mental model to drop first: in keyword SEO the unit of work was a page, and one page carried one target. Here, an association strong enough to change an answer comes from a claim appearing in **several credible contexts across the site**, corroborated from different angles. One dedicated page is where you start, not where you finish.

---

## Question 1: is there a page for this?

**If no, create one.** For an opportunity, a page focused on the attribute. For a strength currently buried inside a general feature list, give it a standalone page so there is something concrete to extract.

**If yes, read it through an extraction lens, not a ranking lens.** The question is not whether it ranks. The question is whether a claim can be lifted from it and used in a sentence. Score it with the rubric in `references/aeo/technical.md` and fix the dimensions that failed.

The most common failure by far is dimension 1. The page has the information and buries it under a paragraph of context-setting, so the first extractable thing an engine finds is throat-clearing. Move the answer to the top. Everything else about the page can stay.

**The extraction rewrite**, in order:

1. Put a self-contained 40 to 80 word answer immediately after the H1. It must make sense quoted alone, with no pronouns pointing at the heading.
2. Rewrite H2s as the questions people actually ask, and answer each in the first sentence beneath it.
3. Make each topic sentence survive being quoted with nothing around it. The test is real: cut the sentence out, read it cold, and see whether it still says something.
4. Attribute and date every number, inline.
5. Move any fact currently living only inside a screenshot or a chart into text as well.
6. Add the schema the page type calls for, matching the visible content.
7. Add a visible date.

**For an objection, the page usually does not exist**, because companies do not build content about their weaknesses. Silence is not neutral: it means the engine is taking the narrative from wherever it found it, with nothing of yours in the mix. Enter the conversation.

---

## Question 2: where else should this claim appear?

Once the dedicated page exists, reinforce the association elsewhere. Not everywhere. The right pages, in this order:

**1. Pages already appearing in your citations.** The highest-leverage placement there is. The engine already reads and trusts that page, so adding a claim there inherits credibility you would otherwise spend months building. Stream B gives you the list.

**2. Your most-cited pages generally**, even where the attribute is only adjacent. Citation volume is a reasonable proxy for how much an engine weights a page.

**3. The definitional pages.** Homepage, pricing, about, comparison pages. These get heavy crawl attention and are where engines look for what a company fundamentally is. A claim absent from all four reads as peripheral no matter how many blog posts carry it.

---

## Question 3: how do you add it without wrecking the page?

Two methods.

**Weave it into existing content.** Higher effort, holds up better. If a post is already cited for something adjacent, add a reference to the target attribute where it genuinely fits the argument.

The test: **would a human editor who knows nothing about this program find the sentence strange?** If yes, it is forced, and forced additions do not perform. They also make the page worse for readers, which eventually shows up as a real signal.

**Add an FAQ.** More mechanical, and fine within limits. A few well-placed questions on a product or pricing page are genuinely useful to readers and give engines a clean extractable format.

The limit is real and worth stating plainly. A wall of questions that exist only to hit attributes is the current form of keyword stuffing. Readers recognize it, and it is reasonable to expect engines to discount it the same way search engines learned to discount its predecessor. **Build the FAQ from questions that actually appeared** in your prompt responses, in support tickets, or in docs search. Those exist. Invented ones do not need to.

---

## Fixing an accuracy failure

Read the citations on the wrong answer. They tell you where the fix goes.

- **The error traces to your own page:** fix the page. Fastest fix in the whole program.
- **The error traces to a third-party source:** on-page work will not fix it. You cannot out-publish a wrong answer an engine keeps finding somewhere else. Route it off-page and treat it as top priority.
- **The error traces to nothing specific:** the engine inferred it. Publish the correct fact somewhere unmissable and stated plainly, then re-test. Inference fills vacuums.
- **Your own surfaces contradict each other:** fix that first, always. If the code says one price and the marketing site says another, no amount of external work will produce a consistent answer.

Every corrected fact gets stated in the same words as `.seo/truth.md`, so the several places it appears corroborate rather than compete.

---

## Objection content

The rule: **reframe, do not defend.**

A page that opens with "we do not have a steep learning curve" restates the objection in your own voice, on your own domain, in an extractable position. You have just made yourself a citable source for it.

"Most teams run their first workflow within an hour" makes the same argument by demonstration and gives an engine something quotable that is not the objection.

**Some objections should be owned rather than countered.** If you are genuinely the expensive option and that surfaces as a negative theme, the move is to make clear what the money buys. Denying something third-party sources confirm creates an inconsistency between your site and the rest of the web, and inconsistency is itself a signal. It reads as evasion and it makes the objection stickier.

**Distribute the reframe.** A single page addressing an objection is better than nothing and will not shift a broad theme. The reframe needs the same multi-surface spread as any other attribute: about page, case studies, onboarding content, comparison pages.

---

## Before you call it done

- The claim is stated in `.seo/truth.md` language, so every instance corroborates the others.
- Schema present and matching visible content.
- Visible date, accurate `dateModified`.
- Re-run `scripts/crawl_check.py` on every page touched and confirm the extractability score moved.
- Server-rendered body still contains the new claim. A framework change can silently move content behind hydration.
- The page still reads well to a human. Every rule here is a formatting nudge on top of something worth reading, never a substitute for it.
- Append to `.seo/aeo/worklog.md` with the finding ID and a recheck date.

Then hand off. Do not commit, do not deploy.
