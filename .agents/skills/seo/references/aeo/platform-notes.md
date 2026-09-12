<!-- sources: aeo/references/platform-notes.md (verbatim; state + reference paths remapped to .seo/) -->
# Platform notes

How each engine reaches an answer, and what that implies. Read this to interpret your results, not to build per-platform tactics.

**The warning first.** Platform behavior changes without notice and without documentation. Anything in this file that reads like a specific tactic is a hypothesis with a short shelf life. The parts worth relying on are structural: which index an engine draws from, and whether it retrieves at answer time or leans on training data. Those change slowly. Everything downstream of them changes fast.

**Do not over-fit.** When your results differ across platforms, the honest reading is almost always that the evidence about you is thin, not that one engine has a preference you can exploit. Use agreement as a confidence check. Use divergence as a signal that an attribute is still winnable.

---

## Google: AI Overviews and AI Mode

**Draws from:** the regular Google index. This is the single most important structural fact about Google's AI surfaces, and it is the one most often got wrong.

**What follows from it:**

- Traditional search work pays forward directly. A page that cannot be crawled, indexed or rendered by Googlebot cannot appear in an AI Overview, no matter what else you do.
- `Google-Extended` controls training and grounding for Gemini. Blocking it does **not** remove you from AI Overviews, because AI Overviews works from the index Googlebot built.
- Blocking `Googlebot` removes you from Google entirely, AI surfaces included.

**Reading your results:** Google's surfaces produce different answers for the same prompt often enough that per-surface optimization is unreliable. The tractable approach is making pages that already rank well also easy to extract from. That serves both surfaces and it is work you can actually verify.

Google is also folding these experiences together over time, which means anything you build on the current boundary between them is temporary. Build on the index, not on the boundary.

---

## ChatGPT

**Draws from:** live web retrieval when search is engaged, plus the model's own knowledge when it is not. Which one you get depends on the query and on settings you cannot control, and the two produce meaningfully different answers.

**What follows from it:**

- `OAI-SearchBot` is the retrieval agent. Blocking it removes you from ChatGPT search results.
- `GPTBot` is the training crawler. Blocking it is a business decision that does not affect today's answers.
- `ChatGPT-User` fetches when a person asks the assistant to read a specific link. Blocking it breaks that flow on your site.
- **Always measure with web search enabled.** Measuring without it tells you about training data, which is a different and much less actionable question.

**Reading your results:** ChatGPT does not carry two decades of accumulated ranking heuristics. Content types that search engines learned to discount over time, such as thin comparison pages and promotional listicles, can carry more weight here. That cuts both ways: it is an opening if those sources describe you well, and a liability if they describe you badly and you are not watching them.

---

## Perplexity

**Draws from:** live retrieval, always, with visible citations on every answer.

**What follows from it:**

- Citation is the product, which makes Perplexity the cleanest read on which sources actually shape answers in your category. Even if it is not a priority engine for you, it is a useful instrument.
- Original data and clearly attributed sources do disproportionately well here, which follows directly from an engine that has to show its work.
- `PerplexityBot` retrieves; `Perplexity-User` fetches on a person's request.

**Reading your results:** Perplexity diverges from the other engines more often than they diverge from each other, without a clean explanation. Treat a Perplexity-only result as interesting rather than as a mandate, and do not build a program on a pattern you cannot explain.

---

## Claude

**Draws from:** web search when enabled, plus training knowledge.

**What follows from it:** `ClaudeBot` and `Claude-SearchBot` retrieve. `Claude-User` fetches on request. Longer coherent passages with clear reasoning and supporting evidence tend to be used well, so do not fragment a page into disconnected snippets on this engine's account.

---

## Microsoft Copilot

**Draws from:** the Bing index.

**What follows from it:** Bing indexing is the prerequisite, and Bing Webmaster Tools is the free instrument for checking it. Sites focused entirely on Google sometimes have real Bing coverage gaps and have never looked. Copilot is not reachable through the common programmatic paths, so if it matters, collect it by hand and label the sample size accordingly.

---

## Gemini

**Draws from:** Google's index plus Google's knowledge graph, with training controls under `Google-Extended`.

**What follows from it:** entity clarity matters more here than elsewhere. `Organization` schema with accurate `sameAs`, a parseable About page, and consistent naming across your own surfaces all feed the knowledge-graph side rather than the retrieval side.

---

## What actually transfers across all of them

The structural facts, in rough order of durability:

1. **Reachable beats everything.** Every engine on this page needs to fetch and parse the page. Blocked, unrendered or unindexed content contributes nothing anywhere.
2. **Third-party sources carry more weight than your own pages.** Every engine is synthesizing a consensus, and your site is one voice in it. This is the fact that makes off-page work non-optional.
3. **Self-contained passages get quoted. Dependent ones do not.** True of every extraction system and unlikely to change.
4. **Attributed, dated specifics beat confident vagueness.** True for models and for careful readers, for the same reason.
5. **Consistency across sources is what builds an association.** Contradiction between your own surfaces is the cheapest failure to fix and a common one.

Everything else on this page is weather.
