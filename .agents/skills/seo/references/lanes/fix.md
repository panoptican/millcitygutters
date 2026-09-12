# Lane: fix

<!-- new in v2; distilled from a 2026-09 outside audit's work packages and editorial runbook -->

## Routes here

`correct`, `consolidate`, `prune`, `verify-product`. The candidate record carries the target page or claim, the evidence (a truth-check hit with file and line, a re-verified claim with old and new source, two URLs with overlapping query sets, or a claim in `truth.md` with no dated source), and the panel that produced it.

`repair` and `index-nudge` go to `lanes/technical.md`. A `refresh` that turns out to need a factual correction stays in `lanes/editorial.md` but reads this lane's "Correcting a claim" steps.

## Read first

- `.seo/truth.md` and `.seo/truth-checks.json`. Always. The fix has to agree with the ledger, and the ledger has to be updated if the fix teaches it something.
- `.seo/brand.md` "Forbidden claims" and voice sections. A correction is still public copy.
- `content-stores.md` if you do not yet know where the page's copy lives in this stack.
- `quality-loop.md` only for the gates section; a correction does not go through the full critic panel.

## Steps

### Correcting a claim

1. **Reproduce.** Open the live page (or the local render) and confirm the wrong text is there. Quote it in the run record with the URL. If it is not there, the candidate is stale: close it and say so.
2. **Establish the truth.** If `truth.md` has the fact with a dated source, use it. If it does not, this is a `verify-product` first: find the source (the repo, the billing config, the feature flag, the primary document), record it in `truth.md` with today's date, and add a mechanical check to `truth-checks.json`. Never guess. Never resolve a product fact by picking the page that sounds most confident.
3. **Find every sibling.** The same wrong claim almost always lives in more than one place: FAQ tails on comparison pages, `llms.txt`, a schema `description`, a homepage trust block, an alternatives page, the pricing page, an App Store or marketing copy file. Grep for the wrong phrasing, the number, and the concept. When the copy lives in a database or CMS (`stack.content_store.type` is not `files`), the grep covers only templates and code; run the row search in `stacks/app-db.md` §2 as well, and record the query in the evidence file. The audit that built this lane found the pricing claim in five pages and twenty FAQ tails. Fix all of them in one change, or list the ones left in "Not done."
4. **Rewrite at the source.** Change the claim on the page, in the page's own voice. On a database or CMS store the rewrite is a migration, a draft revision, or a hand-off per `stacks/app-db.md` §3, never a live update; the change record replaces the file diff as what the PR reviews. Don't append a correction; replace the sentence. If the page cited a source, update the citation. If a competitor claim is being corrected, state what the competitor does, not what it lacks, unless you have their current page open to prove the lack.
5. **Bump the date.** Set the page's `date_modified` (or equivalent) so the sitemap and any Article schema tell the truth about the change.
6. **Test.** If the claim is generated from data (a provider address, a trial list, a price), add or extend a test that asserts the corrected value and fails on the old one. A one-off blacklist of the bad value is not a fix; fix the rule that produced it.
7. **Record.** Evidence file per `register.md` §4 with the before text, the after text, the source, and the test.

### Consolidating two URLs

1. Confirm the overlap with the GSC page × query data: both URLs receive impressions on substantially the same queries, or one is invisible while the other ranks.
2. Choose the owner by current evidence (the URL with more clicks and the better position), not by which one is prettier.
3. Move any unique, useful content from the loser into the owner. Preserve the owner's fragment ids and publication date.
4. 301 the loser to the owner in one hop. In stacks with parameterized routes, declare the redirect before the parameterized route or it will never match.
5. Remove the loser from the sitemap, breadcrumbs, internal links and any generated sibling lists. Update `link-inventory.md`.
6. Verify: loser returns 301 with the expected Location; owner returns 200 and self-canonical; no loop; only the owner in the sitemap.
7. Do not claim Google has consolidated anything. Reinspect both after a later crawl.

### Pruning a page

Removal is as much a part of managing the site as writing, and the census is the only thing that proposes it. The gates here are strict on purpose: a wrong prune loses a page that was quietly earning links or answering a legal requirement, and there is no undo once Google drops it.

1. Confirm the census evidence with your own eyes: zero or near-zero impressions for 90+ days across two snapshots, thin or duplicated content, age past the judgement window. Quote the numbers in the run record.
2. Check what the page still does: referring domains (`backlinks_referring_domains` or the backlink cache), inbound internal links (`link_audit.py --orphan-check`), a role in a hub or a pattern set, a legal or compliance reason to exist (privacy, terms, accessibility), answer-engine citations in the AEO findings. Any of these means merge, not delete.
3. Choose the exit. If another page owns the intent or covers the useful part, fold the unique content in and 301 to it (this is `consolidate`). If nothing does and the page has no value, 410. Never 301 a dead page to the homepage; that is a soft 404 with extra steps.
4. Remove it from the sitemap, navigation, generated sibling lists, internal links and `link-inventory.md`. Update the ledger coverage map so the intent shows no owner, or the new owner.
5. If the page was generated from data (a provider, a state, a pattern row), remove the data row and add a test that the URL now returns the intended status, so a regenerate cannot resurrect it.
6. Keep the redirect or 410 in place for at least a year.
7. Evidence file with the census verdict, the checks in step 2, the exit chosen, and the HTTP proof.

### Verifying a product claim

1. Name the claim exactly as it would appear on a page.
2. Find its source of truth in the repo or the running product: a config value, a feature flag, a billing plan, a route, a test. If the truth is a business decision that is not encoded anywhere (are we free forever? do we plan a paid tier?), it goes to `needs-you.md` as a question with the exact wording options, and this candidate is blocked.
3. Record in `truth.md`: claim, value, source, read date, risk level. Add the mechanical check.
4. Then run "Correcting a claim" for every page that disagrees.

## Gates

- The wrong text no longer appears anywhere in the public content sources (`truth_check.py` passes, or the specific rule you added passes).
- `truth.md` has the fact with a dated source. `truth-checks.json` has the rule.
- Every page touched has its `date_modified` bumped.
- For data-generated claims: a test covers the corrected value.
- For consolidations: the HTTP evidence (301, Location, 200, canonical) is in the evidence file.
- For prunes: no referring domains, no legal role, no hub role, no answer-engine citation, or each one has been merged somewhere; the exit is 301 to an owner or 410, never the homepage; the URL is out of the sitemap and all internal links.
- No competitor is named outside the pages allowed to name them, per `brand.md`.
- Nothing invented HIPAA, BAA, encryption, clinical-outcome or regulatory language while rewriting.
- Rendered check of at least one corrected page in a headless browser or the local server, not just the source file.

## Register

Ledger row with action, target, the before text (truncated), the after text (truncated), and the source. Evidence file. Any sibling page left uncorrected goes in "Not done." Any business decision goes to `needs-you.md`.
