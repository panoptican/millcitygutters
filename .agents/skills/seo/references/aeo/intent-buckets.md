<!-- extracted from seo-content/references/aeo.md §1 -->

# Answer-intent buckets

Every query an answer engine serves falls into one of four buckets, and the *shape of the answer* a page leads with should match its bucket. This overlaps the page type chosen in `content-types.md`, but it is a narrower question: not "what kind of page is this" but "what does the first screen have to say for an engine to lift it."

| Intent | Lead the page with | Schema |
|---|---|---|
| **Definitional** ("what is X") | A concise 40-60 word plain-language answer in the first paragraph, then expand. | `Article` / `DefinedTerm` + `FAQPage` |
| **Process** ("how to X") | An ordered, liftable workflow near the top; examples, checklist, troubleshooting below. | `HowTo` |
| **Comparison** ("X vs Y", "best X") | A balanced table plus an explicit, scenario-based recommendation ("pick X if…"). | `ItemList` / `FAQPage` |
| **Decision** ("should I X", "is X worth it") | A direct verdict up front, then the reasoning and the conditions under which it flips. | `Article` + `FAQPage` |

Classify the target query into a bucket before writing, and check the lead against the bucket at the gate. A definitional query answered with a 300-word preamble is not a style problem — it is a page that cannot be quoted, which is the only thing that matters here.

The rest of the answer-engine layer — writing for extraction, entity coverage, freshness and credibility signals, and the per-platform notes — lives in `lanes/aeo.md`.
