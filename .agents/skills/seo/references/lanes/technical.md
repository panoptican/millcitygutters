# Lane: technical

<!-- merged from seo-sprint/references/technical-audit.md + aeo/references/technical.md (now references/aeo/technical.md) + schema-markup/SKILL.md (required-properties table, @graph, validation) + seo-audit/SKILL.md (priority order, schema-detection limitation, CWV thresholds, title/meta lengths) -->

Fixes live artifacts. Not "the site could be faster" — a specific broken thing, named, with a diff.

The day-0 crawl shapes how Google understands a site for months, and retroactive fixes are harder than getting it right the first time. That's why technical work is Phase 0 on a new roadmap and why a reachability or index regression outranks everything else in the select rubric.

**Contents:** Routes here · Read first · Input: `health_diff.py` · Priority order · Steps (repair) · Steps (index-nudge) · The repair classes · Schema · Gates · Register

---

## Routes here

| Action | Candidate record carries |
|---|---|
| `repair` | The artifact and its URL or file path · the rule violated (from `health_diff.py`, the crawl, or GSC) · what it breaks (crawl, index, extraction, privacy, accessibility) · whether it regressed (present in the previous `.seo/health/<date>.json` and not the one before) |
| `index-nudge` | The one URL · its GSC index state verbatim (`unknown to Google` / `discovered–not indexed` / `crawled–not indexed` / `BLOCKED_BY_META_TAG` / a differing `google_canonical`) · days since publish · current inbound-link count and which pages · whether it's in the sitemap with a valid `lastmod` |

A wrong *claim* on a page is not a repair — it's `correct` (`lanes/fix.md`). Two URLs competing for one intent is `consolidate` (`lanes/fix.md`), though the 301 and route-ordering work lands here. An AI-crawler-specific reachability problem (`robots.txt` per AI agent, `llms.txt`, a render shell that only breaks for retrieval bots) stays in `lanes/aeo.md`.

---

## Read first

1. The latest two files in `.seo/health/` — the diff is the finding. Never skip.
2. `references/aeo/technical.md` — the canonical reference for AI user agents (§1), `llms.txt` (§2), the rendering check (§3), reachability basics (§4), schema (§5), freshness (§6), the extractability rubric (§7) and entity clarity (§8). This lane does not restate it; read it there.
3. `references/schema-examples.md` — full JSON-LD examples per type. Read when the repair is a schema one.
4. `references/stacks/<framework>.md` — where the sitemap generator, robots file, route table and meta helper actually live in this repo.
5. `.seo/config.json` — `crawl_hubs`, sitemap path, base URL, detected tools.
6. `references/gsc.md` §3 (index states) and §7a (discoverability) — `index-nudge` only.
7. `references/quality-loop.md` — the meta and schema requirements the repair has to leave the page satisfying.

---

## Input: `scripts/health_diff.py`

This lane's input is a diff, not a crawl. The measure step already ran it — the invocation lives in `references/measure.md` §3 and is not repeated here. Re-run the same command after a fix (gate 2).

It writes a fingerprint to `.seo/health/<date>.json` and prints two things: **the diff against the previous fingerprint**, and **the rule violations** in the current one.

Read them differently. A violation that is present in both files is a standing defect and competes on normal expected-movement-over-effort. A violation that appears in today's file and not yesterday's is a **regression**, and a regression in crawlability or index state jumps the queue — something shipped that broke it, the cause is still fresh, and the fix is cheap right now and expensive in three weeks.

Fingerprints are also the audit trail. When a page falls out of the index, `.seo/health/` is how you find the day its status, canonical, schema or `lastmod` changed.

### Fastest full crawl, when a diff isn't enough

If OpenSEO is connected it runs a real site-wide crawl and finds the two classes of problem a sitemap walk structurally cannot — **orphan pages** (nothing links to them, so a sitemap walk never reaches them) and **broken internal links**. Both need the link graph.

```
run_site_audit
  projectId: <project id from list_projects>
  url:       https://<domain>/
  maxPages:  200                     # 10-10000, default 50. Budget it.
  runLighthouse: false               # true adds several minutes; only for CWV detail
```

Poll `get_audit_status`, then read `get_audit_issues` (severity `critical`, limit 200) and `get_audit_pages` with `fetchClass: "blocked"`.

**Read `fetchClass: "blocked"` before trusting a clean report.** If bot protection challenged the crawler, those pages are flagged blocked rather than silently reported fine. "No issues" across a mostly-blocked crawl means nothing.

**Don't read `warning` as "later."** OpenSEO's `critical` bucket is deliberately narrow (`blocked-page`, `server-error`, `broken-internal-link`, `missing-title`). `redirect-loop`, `canonical-conflict` and `broken-page` sit in `warning` and are all blockers. Triage on what the issue does to indexing, not on the label. Everything in `info` is a nice-to-have that should never block a phase.

**Still run the GSC checks regardless.** A crawler sees what the site serves; only Search Console reports what Google actually *did* with it — index state, and its own canonical choice. Neither substitutes for the other. Without OpenSEO you lose orphan and broken-link detection: say so rather than reporting a clean bill of health.

---

## Priority order

When several repairs are live at once, work them in this order. Each tier invalidates work done in the tiers below it.

1. **Crawlability & indexation** — can Google find and index it?
2. **Technical foundations** — is the site fast and functional?
3. **On-page optimization** — is the content optimized?
4. **Content quality** — does it deserve to rank?
5. **Authority & links** — does it have credibility?

Tiers 4 and 5 leave this lane: 4 goes to `lanes/editorial.md`, 5 to `lanes/offpage.md`.

---

## Steps — `repair`

1. **Reproduce the violation against production**, not against the fingerprint. A stale fingerprint is a real failure mode; confirm the artifact is still broken before writing a diff.
2. **Find the generator, not the symptom.** A wrong `lastmod` on 217 URLs is one bug in the sitemap builder, not 217 edits. A missing `<html lang>` is one layout. Fixing the instance and not the generator guarantees the same candidate tomorrow.
3. **Check the blast radius.** Grep for every other consumer of the thing you're changing — the route table, the sitemap serializer, the meta helper, the layout. Route ordering in particular bites: a collection route declared before a member route shadows it.
4. **Write the fix and a test.** A repair without a regression test is a repair you'll do again. Where the repo has no test surface for it, add the check to `truth-checks.json` or note it as a `health_diff.py` rule.
5. **Verify against the rendered page**, not the source. `curl -sI` for status and headers, `curl -s | grep` for the canonical, the `lang` attribute, the meta tags and a distinctive body sentence. For schema, see the detection limitation below.
6. **Re-run `health_diff.py`** and confirm the violation is gone from the current fingerprint and nothing new appeared.

## Steps — `index-nudge`

The states are not interchangeable and each names a different fix. Read the state, then do the matching thing — submitting a URL that Google has already crawled and declined is a no-op that looks like work.

| GSC state | What it means | Fix |
|---|---|---|
| **unknown to Google** | Discovery problem | Get it in the sitemap with a valid `lastmod`, then add inbound links, ≥1 from a `crawl_hubs` page |
| **discovered – not indexed** | Crawl-priority problem | Link it from stronger pages. Google found it and hasn't prioritized fetching it |
| **crawled – not indexed** | Google is declining on quality or duplication | Not a submission problem. Either the page is thin (→ `refresh`) or it duplicates another URL (→ `consolidate`) |
| **`BLOCKED_BY_META_TAG`** | A `noindex` config bug | Find the inherited `noindex` — usually a layout default or an environment guard leaking into production |
| **`google_canonical` ≠ ours** | Cannibalization, confirmed at the source | The page reads as indexed and earns nothing. → `consolidate` |

**"Discovered, currently not indexed" is mostly Google's predicted-usefulness filter, not a crawl-budget problem.** Before resubmitting anything, check whether the page targets a query with observable demand — GSC impressions on a sibling page, or a dated Reddit/HN/forum thread asking it. If there is no demand artifact, the fix is retargeting or consolidating the page, and resubmission is wasted motion. Route the symptom by what it actually is:

| Symptom | What it is | Where it goes |
|---|---|---|
| Unknown to Google | Discovery | Sitemap, internal links, IndexNow |
| Discovered – not indexed | Demand | Retarget or consolidate the page |
| Crawled – not indexed | Quality / duplication | → `refresh` or `consolidate` |
| Indexed, no impressions | Intent mismatch | Retarget the query |
| Impressions, no clicks | Title / snippet | Rewrite the SERP-visible copy |
| Clicks, no activation | Page / product fit | `lanes/editorial.md` |

Then, in order: confirm the URL returns 200 and isn't a redirect · confirm the body text is in the server-rendered HTML · confirm the canonical is self-referencing · confirm ≥2 inbound links with ≥1 from a frequently-crawled hub · confirm it's in the sitemap with a content-date `lastmod`. Only after all five, submit.

**Submitting is the last step and the smallest one.** For a single URL, the only Google-sanctioned push is "Request indexing" in the URL Inspection UI — hand the user the `inspection_result_link`; it's UI-only and daily-quota'd. For IndexNow, see the repair class below.

**The loop gate applies here.** If the last three published pieces aren't indexed, this run's job is fixing that, not writing a fourth.

---

## The repair classes

These are the ones learned in the field, on live sites. Each has a specific right answer that is not the obvious one.

### 1. Sitemap `lastmod` set to the build date

The generator stamps every URL with the deploy timestamp, so all 217 URLs change `lastmod` on every deploy and the signal carries zero information. Crawlers learn to ignore it, and then a genuinely-updated page gets no freshness signal when it needs one.

**Fix:** `lastmod` must be the **content date** — the page's real `date_modified` — or **omitted entirely**. Omitted is better than wrong. Tie it to the content record, never to a build constant. Related standing checks: no `lastmod` in the future (a crawler red flag), and no `lastmod` stale past ~180 days on a page that is actually being updated.

### 2. Missing `<html lang>`

One attribute, one layout file, and it's missing on a surprising number of otherwise-clean sites. It affects extraction, translation and assistive tech. **Fix:** set it on the root layout, and set it per-locale if the site is localized.

### 3. Duplicate natural-key pages

Two URLs serve the same entity — usually a legacy slug and a canonical one, or a natural-key route and an id route. They split link equity and Google picks a canonical you didn't choose.

**Fix:** consolidate the content into one URL and 301 the other. **Declare the 301 before the parameterized route** in the route table. A parameterized route pattern like `:slug` or `:id` matches the legacy path too, so a redirect declared after it never fires — the framework matches the first pattern, serves the duplicate, and the redirect sits there looking correct in the diff. Test the redirect with `curl -sI` after the change; don't infer it from the route file.

### 4. IndexNow resubmitting the whole sitemap

The integration pushes every URL in the sitemap on every run. That's not a submission, it's noise, and it burns whatever trust the endpoint extends.

**Fix:** submit **only URLs whose content changed since the last submission** — diff against the previous `.seo/health/<date>.json`, or track a submitted-set. And: **never record a 200 or 202 response as "indexed."** The endpoint acknowledging receipt says nothing about whether anything got crawled, let alone indexed. Index state comes from GSC, from `batch_url_inspection`, and from nowhere else. A run record that logs "217 URLs indexed via IndexNow" is reporting a fiction.

### 5. Analytics beacons injected into private routes

An edge worker, CDN feature or tag manager injects a script into every response, including authenticated and private routes. The beacon then carries record ids, private slugs, tokens, filenames or diagnoses in the URL or referrer.

**Fix:** stop the injection on private routes — `Cache-Control: no-transform` on those responses is the standard lever where a CDN is doing the injecting, or scope the tag to public routes explicitly. **Nothing in analytics may carry private identifiers, and no session replay runs on private routes.** This is a repair with user-facing harm, so it jumps the queue above ordinary repairs regardless of its SEO value — its SEO value is roughly zero and it ships first anyway.

### 6. `dateModified` equal to `datePublished` while the sitemap disagrees

Check this by hand until the script covers every case: an `Article` whose `dateModified` equals its `datePublished` while the sitemap's `lastmod` says a later date means the freshness signal contradicts itself — one artifact says the page was never updated and the other says it was. **Fix:** make the JSON-LD dates and the `lastmod` read from the same content record. `health_diff.py` flags the common shape as `freshness-contradiction`.

### 7. Scrollable tables that aren't keyboard-focusable

A wide table wrapped in an `overflow-x: auto` container scrolls with a mouse or trackpad and is unreachable by keyboard. **Fix:** give the scroll container `tabindex="0"` plus an accessible name (`role="region"` with `aria-label`, or `aria-labelledby` pointing at the table's caption). It's a two-attribute change and it's a real WCAG failure, not a nicety.

### 8. An inbound backlink landing on a 404

`backlink_diff.py` (measure.md §6e) lists live links from other sites whose target on our site is not a 200: a renamed slug, a pruned page, a trailing-slash rule that changed. **Fix:** a 301 from the dead path to the page that now owns that intent (never the homepage unless nothing else fits), in the route layer, not a meta refresh. Then confirm with `curl -I` that the chain is one hop. This is the cheapest link-building on the site: the link already exists and is earning nothing. Register the before and after status codes in the evidence file.

### 9. A missing internal link the site already has the words for

`link_opportunities.py` (measure.md §3e) finds pages whose body contains the exact query another page owns, with no link between them. **Fix:** link the phrase, in the body where it already appears, to the owner page; one anchor per page, the owner's target query or a natural variant as the text, never a bolted-on "related links" block. Do every opportunity pointing at the same owner in one edit. Bump nothing: adding a link is not a content change, and `date_modified` stays. Verify with `health_diff.py --check-links` that the new link resolves to a 200 and that the owner's inbound count rose (`link_audit.py` is filesystem-only; on a database or CMS store the body edit follows `stacks/app-db.md` §3).

---

## AI plumbing checklist

Cheap, one-time, and verified with `curl` — not scored from your own HTML. Run it once per site, fix what's missing, move on.

- **`robots.txt` names the AI user agents explicitly** (the list is in `scripts/agents.py`) and blocks none of them unless `.seo/brand.md` policy says so.
- **`Content-Signal` response header** if the site wants to state a training policy — e.g. `search=yes, ai-input=yes, ai-train=no`.
- **`llms.txt` valid** per `python3 scripts/robots_check.py`, plus an `llms-full.txt`.
- **RSS/Atom feed** on the editorial surface.
- **IndexNow key file** served at the site root.
- **`Link:` response headers** (RFC 8288) carrying canonical/alternate on non-HTML assets, which have no `<head>` to put them in.

Speculative, ship only if free: `/.well-known/mcp.json`, and `Accept: text/markdown` content negotiation.

**Why:** this is the useful half of the popular geo-seo-claude checklist. The rest of that pack scores proxies computed from your own HTML and never queries an engine, so it reports a grade nobody outside the repo can see.

---

## Schema

The reference for what to emit per page type is `references/quality-loop.md` (the per-pattern table) and `references/schema-examples.md` (the full JSON-LD). What belongs here is detection, required properties, and combination.

### The detection limitation — quote this, don't paraphrase it

> **`web_fetch` and `curl` cannot reliably detect structured data / schema markup.**
>
> Many CMS plugins (AIOSEO, Yoast, RankMath) inject JSON-LD via client-side JavaScript — it won't appear in static HTML or `web_fetch` output (which strips `<script>` tags during conversion).
>
> **To accurately check for schema markup, use one of these methods:**
> 1. **Browser tool** — render the page and run: `document.querySelectorAll('script[type="application/ld+json"]')`
> 2. **Google Rich Results Test** — https://search.google.com/test/rich-results
> 3. **Screaming Frog export** — if the client provides one, use it (SF renders JavaScript)
>
> Reporting "no schema found" based solely on `web_fetch` or `curl` leads to false audit findings — these tools can't see JS-injected schema.

Never render "couldn't check" as "clean."

### Required properties

| Type | Use for | Required properties |
|---|---|---|
| `Organization` | Company homepage / about | `name`, `url` |
| `WebSite` | Homepage (search box) | `name`, `url` |
| `Article` / `BlogPosting` | Blog posts, news, playbooks | `headline`, `image`, `datePublished`, `author` |
| `Product` | Product pages | `name`, `image`, `offers` |
| `SoftwareApplication` | SaaS / app pages | `name`, `offers` |
| `FAQPage` | FAQ content | `mainEntity` (Q&A array) |
| `HowTo` | Tutorials | `name`, `step` |
| `BreadcrumbList` | Any page with breadcrumbs | `itemListElement` (position, name, item) |
| `LocalBusiness` | Local business pages | `name`, `address` |
| `Event` | Events, webinars | `name`, `startDate`, `location` |

Recommended-but-worth-adding: `logo` + `sameAs` + `contactPoint` on `Organization`; `dateModified` + `publisher` + `description` on `Article`; `sku` + `brand` + `aggregateRating` on `Product`.

Two more worth emitting: **`speakable`** with a `cssSelector` pointed at the page's answer-first paragraph, and **`citation[]`** on any `Article` that cites sources. Both tell an extractor which sentences to lift and where they came from.

**Anti-pattern: never self-author `AggregateRating` on your own product or comparison pages.** A rating you wrote about yourself is the schema-content mismatch that gets a site penalized rather than ignored. Ratings come from a review platform's markup, not from you.

### Combining types on one page — `@graph`

```json
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Organization", "...": "..." },
    { "@type": "WebSite", "...": "..." },
    { "@type": "BreadcrumbList", "...": "..." }
  ]
}
```

One `<script type="application/ld+json">` block with an `@graph` array beats several sibling blocks: it's one thing to validate, one thing to keep in sync, and it lets the types reference each other by `@id`.

### Validation

Validate the **rendered URL**, not the template. `https://validator.schema.org/` and Google's Rich Results Test, plus `python scripts/tech_audit.py --schema <url>` for the deterministic pass. The three errors that recur: **missing required properties** · **invalid values** (dates must be ISO 8601, URLs fully qualified, enumerations exact) · **mismatch with page content** — schema asserting something the visible page doesn't say. The third is the one that gets a site penalized rather than merely ignored.

If the repo has no schema helper, building one is itself a repair. A helper saves rewriting the same JSON-LD boilerplate thirty times, and it means the next fix is one edit rather than thirty.

---

## Repair classes for the four vitals

**Speed.** Order of attack, because each is a one-line fix before it is a project: uncompressed or oversized images (serve WebP or AVIF, set width and height, lazy-load below the fold); render-blocking scripts and fonts (defer, preload the one font that paints the H1, `font-display: swap`); third-party tags on public pages (every one is a request; the analytics beacon that leaked private IDs was also the slowest thing on the page); server time to first byte (cache the marketing pages at the edge or in the app; a 1 s TTFB on an SSR page is a missing cache, not a slow server). Verify with Lighthouse before and after on the same page, same device profile; record both in the evidence file.

**Links.** Broken internal links get fixed at the source, not redirected. Redirecting internal links get repointed to the final URL (every hop is a wasted crawl and a diluted signal). Orphans get at least two inbound links from pages that already rank, or get pruned. External links returning 404 get replaced with the current source or removed; never leave a citation pointing at a dead page on a medical or legal claim.

**Click rate.** Not this lane. A low-CTR page is a `refresh` of the title and meta description in the editorial lane, with the query the page actually ranks for in the first 60 characters. Rewrite one, wait 21 days, read.

**Relevance.** Not this lane either. Off-topic pages go to the fix lane as `prune` or `consolidate`.

## Gates

Non-waivable. Cost never overrides a gate.

1. **The fix is verified against the rendered production-shaped page**, not the source and not the template. `curl -sI` for status, redirects and headers; `curl -s | grep` for canonical, `lang`, meta and a distinctive body sentence; a rendering browser or the Rich Results Test for schema.
2. **`health_diff.py` re-run and clean on the fixed rule**, with nothing new introduced.
3. **The generator is fixed, not the instance** — or the run record says explicitly why only the instance was fixed and files the generator fix as a candidate.
4. **Redirects tested, not inferred.** Every 301 written this run confirmed with `curl -sI`, and confirmed to be declared ahead of any parameterized route that would shadow it. No chains, no loops.
5. **Sitemap `lastmod` is a content date or omitted.** Never a build date, never in the future.
6. **Nothing in analytics carries private identifiers** — no record ids, private slugs, tokens, filenames or diagnoses in any URL, referrer or event payload; no session replay on private routes.
7. **No submission recorded as an indexing outcome.** IndexNow / sitemap-ping 200s and 202s are receipts. Index state comes from GSC only.
8. **Meta and heading floor holds on every page touched** — unique `<title>` at 50–60 characters (the SERP-visible range) · unique `<meta name="description">` at 150–160 · self-referencing absolute canonical · exactly one `<h1>` · `og:type`/`og:title`/`og:description`/`og:image`/`og:url` and `twitter:card` present.
9. **Core Web Vitals stay inside the thresholds** on any page whose rendering path changed — **LCP < 2.5s · INP < 200ms · CLS < 0.1**. This is a *don't regress* gate, not a mandate to optimize: chasing CWV during a foundations pass is how a technical phase sprawls into a month-long performance project. Schedule performance work as its own candidate.
10. **Never serve engines different content than humans.** Cloaking is the one shortcut here that can get a domain removed outright.
11. **Never auto-deploy.** Show the diff and hand it over.

---

## Register

- `.seo/health/<date>.json` — this run's fingerprint (written by `health_diff.py`, kept as the audit trail).
- `.seo/content-ledger.md` — a `repair` or `index-nudge` row: date · action · the artifact · the rule violated · whether it was a regression · the generator fixed · the commit or branch.
- `.seo/roadmap.md` — the Phase 0 tracker row flipped to `completed`, in the same edit batch as the fix, when the repair came out of a roadmap phase.
- `.seo/runs/<date>.md` — the fingerprint diff summary, the violations found and their tier, which one was chosen and why, the verification commands and their output, and **the violations left standing** with the reason each lost.
- `.seo/needs-you.md` — submit the sitemap in GSC and Bing Webmaster · hit "Request indexing" at `<inspection_result_link>` after deploy · anything needing a CDN, DNS or hosting-panel login · a performance pass filed as its own candidate.
