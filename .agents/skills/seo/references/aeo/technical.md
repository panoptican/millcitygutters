<!-- sources: aeo/references/technical.md (verbatim; state + reference paths remapped to .seo/) -->
# Technical readiness

This layer is free, deterministic, and it gates everything else. A page an engine cannot fetch or cannot parse contributes nothing, no matter how good it is. Run it every measurement run, because the most common cause of total invisibility is a one-line change somebody made years ago and forgot.

---

## 1. AI user agents

### Two classes, and the distinction decides the advice

| Class | What it does | Blocking it means |
|---|---|---|
| **Retrieval** | Fetches pages at answer time, or builds the index the engine searches when answering | You disappear from that engine's answers. Almost always a mistake. |
| **User-triggered** | Fetches a specific page because a human asked the assistant to read it | "Read this link for me" fails on your site. Usually a mistake. |
| **Training** | Collects content to train future models | A legitimate business decision either way. Blocking it does not remove you from today's answers. |

Getting this backwards is the most consequential error in technical AEO, and it is common in both directions: teams block retrieval agents thinking they are protecting their content from training, and teams block training agents thinking they are opting out of AI answers.

### The agents, grouped

Verify this list against each operator's own published crawler documentation at run time. Agent names change, operators add new ones, and a hardcoded list ages badly. Treat what follows as the starting point for that check, not as the authority.

**OpenAI**
- `OAI-SearchBot` (retrieval, powers ChatGPT search results)
- `ChatGPT-User` (user-triggered)
- `GPTBot` (training)

**Anthropic**
- `ClaudeBot` (retrieval and crawling)
- `Claude-SearchBot` (retrieval)
- `Claude-User` (user-triggered)
- `anthropic-ai` (older name, still seen in the wild)

**Google**
- `Googlebot` (the index AI Overviews and AI Mode draw from). Blocking this removes you from Google entirely, AI surfaces included.
- `Google-Extended` (training and grounding controls for Gemini). Blocking this does **not** remove you from AI Overviews, because AI Overviews works from the regular index.
- `GoogleOther`

**Perplexity**
- `PerplexityBot` (retrieval)
- `Perplexity-User` (user-triggered)

**Microsoft**
- `bingbot` (the index Copilot draws from)

**Broad crawlers whose data flows downstream into many systems**
- `CCBot` (Common Crawl). Blocking it has wide and delayed effects, because many datasets derive from it.
- `Amazonbot`, `Applebot`, `Applebot-Extended` (the `-Extended` variant is the training control), `meta-externalagent`, `Bytespider`, `cohere-ai`, `Diffbot`, `omgilibot`, `YouBot`, `AI2Bot`, `Timpibot`

### What to check

Run `scripts/robots_check.py`. It fetches `robots.txt`, evaluates each agent above against the directives, and reports allow or deny per agent with the matching rule.

Then look for the blocks that do not live in `robots.txt`:

- `X-Robots-Tag` headers set in server config, CDN rules or framework middleware
- WAF or bot-management rules at the CDN, which block by user agent or by behavior and never appear in `robots.txt`
- Rate limiting aggressive enough that a crawler backs off permanently
- Country or ASN blocks that happen to cover a crawler's egress ranges
- `noindex` inherited from a shared layout, which is the classic staging-config-shipped-to-production bug

The CDN bot rule is the nastiest of these because `robots.txt` looks clean and the logs show no hits, which reads as "the engine is not interested" when the real answer is "the engine is being turned away at the door." If Stream D shows zero hits from a major agent while `robots.txt` allows it, check the CDN before concluding anything else.

### Recommending a change

State the tradeoff, do not make the decision. "Blocking `GPTBot` keeps your content out of training and costs you nothing in today's ChatGPT answers. Blocking `OAI-SearchBot` removes you from ChatGPT search results." Then let the user choose. A publisher with a licensing strategy and a SaaS company trying to get discovered have genuinely different correct answers here.

---

## 2. `llms.txt`

A proposed convention: a markdown file at `/llms.txt` that points to the pages you consider most useful, sometimes paired with `/llms-full.txt` carrying expanded content.

**Be honest about its status.** No major answer engine has publicly committed to consuming it, and adoption is uneven. Do not present it as a ranking factor and do not build a gameplan around it.

**Add it anyway, at low priority.** It is a small file, it costs nothing to maintain, some agents and tools do read it, and it forces a useful exercise: writing down which twenty pages actually represent your product. Treat it as a cheap option with an uncertain payoff, and say exactly that in the report so nobody quotes you later claiming it was a proven lever.

A reasonable shape: an H1 with the product name, a blockquote of one-sentence positioning, then linked sections for docs, pricing, integrations and key guides, each link followed by a short description of what it covers.

`robots_check.py` validates an existing file against that shape, then checks the two things nobody checks: whether the pages it points at still return 200, and whether those pages appear in the sitemap. A file of dead links is worse than no file, and it rots silently because nothing reports on it. Fix what it finds because the fixes are cheap, not because the file is a lever. Where the sitemap cannot be read, or lives on a different host, the cross-reference reports UNKNOWN rather than inventing a disagreement.

---

## 3. Rendering: the silent killer

Fetch each page with plain `curl`, no JavaScript. Compare the visible text in that response against what the page shows in a browser.

- **Body text present in the raw HTML**: fine.
- **Raw HTML is a shell and the content arrives via JavaScript**: the page is invisible to a meaningful share of retrieval agents. Several fetch and parse HTML without executing scripts.

This failure is silent, which is what makes it dangerous. The page is perfect in a browser, ranks acceptably in Google because Googlebot renders, and contributes nothing to answers from engines that do not.

`crawl_check.py` reports raw body text length per page. A content page under roughly 500 characters of extractable raw text is a red flag worth opening by hand.

The fix is server-side rendering, static generation, or at minimum ensuring the core claims and the lead answer exist in the initial HTML. Interactive enhancement on top is fine. Content that only exists after hydration is not.

---

## 4. Reachability basics

Per page in the audit list:

| Check | Fail condition |
|---|---|
| Status | Anything other than 200 for a page that should be cited |
| Redirect chain | More than one hop, or a chain ending in a soft 404 |
| Canonical | Missing, cross-domain, or pointing at a different page than intended. A layout-default canonical pointing every page at the homepage is a real and common bug. |
| Meta robots | Any `noindex` or `nosnippet` on a page you want cited. `nosnippet` in particular tells engines not to use your text. |
| `max-snippet` | A restrictive value limits how much of your page can be quoted, which is exactly backwards for AEO |
| Sitemap membership | The page is in the sitemap with an accurate `lastmod` |
| Index state | Confirmed indexed in Search Console. Not indexed means Google's AI surfaces cannot use it. |
| Response time | Slow enough that crawlers time out or back off. Measure time to first byte, not full page load. |
| Click depth | More than three links from the homepage. Depth is also a proxy for how much the rest of your own site thinks a page matters. |
| Orphan | In the sitemap, fine when you request it directly, and linked from nowhere. A page an engine can fetch but cannot find contributes nothing. |

`depth_check.py` measures the last two. It walks internal links from the homepage without executing JavaScript, so navigation that only exists after hydration is invisible to it, exactly as it is to a retrieval agent that does not run scripts. That makes a reported orphan worth opening rather than worth trusting: the page may be linked from a menu that never rendered, which is the more serious version of the same finding. When the crawl hits its page cap it reports orphan state as UNKNOWN, because an uncrawled page and an unlinked one are not distinguishable from a partial walk.

---

## 5. Schema

Structured data does not guarantee citation. It does make the entity and the claims unambiguous, which is cheap insurance.

| Page type | Emit |
|---|---|
| Every page | `Organization` on the site, `BreadcrumbList` on nested pages |
| Product or service page | `Product` or `SoftwareApplication`, with `offers` carrying the real price |
| Pricing page | `Offer` per plan, matching `.seo/truth.md` exactly |
| Article or guide | `Article` with `datePublished`, `dateModified` and a real named `author` |
| Procedure | `HowTo` with ordered steps |
| Question set | `FAQPage`, only where the questions are real |
| Comparison | `ItemList` |
| Original data | `Dataset` with `creator`, `temporalCoverage` and `datePublished` |

Two rules. **Schema must match visible content**, because a mismatch is a quality signal in the wrong direction and, taken far enough, a policy violation. And **`Organization` needs `sameAs`** pointing at your real profiles, which is one of the cleanest ways to make an engine confident that the several ways your brand is named all refer to one entity.

---

## 6. Freshness

- A visible published or updated date on the page, not only in the markup.
- `dateModified` accurate. Bumping it without changing content is a lie that eventually costs trust.
- Any figure with a year in it carries the year, and gets a refresh note in `.seo/aeo/worklog.md`.

Stale-looking pages get skipped by engines that weight recency, and by humans.

---

## 7. Extractability scoring

Score each priority page out of 20. Two points each. This is the per-page number that tells you whether it can clear the Quoted gate.

| # | Dimension | 2 points | 0 points |
|---|---|---|---|
| 1 | **Lead answer** | A self-contained 40 to 80 word answer immediately after the H1 | Throat-clearing, a story, or an inline call to action before any substance |
| 2 | **Question headings** | H2s phrased the way a person would ask, answered in the first sentence beneath | Clever or abstract headings that carry no query |
| 3 | **Claim independence** | Topic sentences survive being quoted with no surrounding paragraph | Sentences that need their neighbors to mean anything |
| 4 | **Attribution and dating** | Every statistic carries a source and a date inline | Bare numbers, or "studies show" |
| 5 | **Text not image** | Key facts, prices and comparisons exist as text | Facts locked inside screenshots, charts or PDFs |
| 6 | **Entity clarity** | Brand and product named consistently, terms defined on first use | Pronouns, internal shorthand, undefined jargon |
| 7 | **Structured blocks** | Tables, ordered lists or an FAQ where the content warrants it | Undifferentiated prose where a table belongs |
| 8 | **Schema match** | Correct type present and matching the visible content | Absent, wrong type, or contradicting the page |
| 9 | **Freshness** | Visible date, accurate `dateModified` | No date, or an obviously stale one |
| 10 | **Substance** | Says something the rest of the results do not: original data, first-hand experience, a specific worked example | Restates the consensus |

**16 to 20**: quotable. **10 to 15**: cited but rarely quoted. **Under 10**: fix this page before writing a new one.

**Score passages, not only pages.** An engine quotes a passage, so a page average hides one quotable block among thirty that are not, and the rewrite you actually want is per-section. `crawl_check.py --blocks` splits the page at every h1, h2 and h3 and scores each passage out of 8 on the four dimensions a script can judge honestly: whether the opening sentence stands alone, pronoun density, quotable length, and whether figures carry a source or a date beside them. It prints the three weakest passages per page, which is the list of sections to rewrite, in order. Everything else in the table above still needs a read.

Dimension 10 is the one that actually decides long-run outcomes, and it is the one no script can score. A page that scores 18 on structure and 0 on substance is a well-formatted page nobody has a reason to cite. Judge it honestly, by reading.

**The quotability test**, applied to the page's three to five core claims: would an engine lift this exact sentence as its answer? If a sentence needs its neighbors to make sense, tighten it until it does not.

---

## 8. Entity clarity

Engines have to be confident that the several ways your brand appears across the web refer to one thing.

- One canonical brand name, used consistently. Note every variant in `.seo/config.json` so extraction can match all of them.
- An About page that states plainly what the company is, who it serves and when it was founded, in parseable prose.
- `Organization` schema with `sameAs` linking your real profiles.
- Consistent naming across your own surfaces first. Your own site contradicting itself is the cheapest possible fix and a surprisingly common finding.

---

## 9. Output

Write the whole layer as a checklist into the report, with three states only: pass, fail, or **unknown**. Unknown is a real state and it must never be rendered as a pass. "We could not read the logs" and "the logs show no problem" are different findings, and collapsing them is how a report becomes untrustworthy.

```
Technical readiness
  Retrieval agents allowed        PASS   all 6 checked agents allowed
  Training agents                 INFO   GPTBot blocked (deliberate, per user)
  CDN bot rules                   UNKNOWN  no CDN access provided
  Server-rendered content         FAIL   4 of 22 pages ship an empty shell (list in appendix)
  Click depth                     PASS   median 2, deepest content page at 3
  Orphans                         FAIL   4 sitemap pages linked from nowhere
  Canonical                       PASS
  Index state                     FAIL   3 pages crawled and not indexed
  Schema                          PARTIAL  Organization present, Product missing on 6 pages
  llms.txt                        ABSENT   low priority, see note
  Extractability median           12/20    6 pages under 10
  Weakest passages                INFO     11 blocks under 4/8, listed by page
```
