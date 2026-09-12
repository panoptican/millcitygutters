# Lane: offpage

<!-- merged from seo-sprint/references/off-page.md (starter stack, Recipe F, phase template, honest caveats) + aeo/references/offpage.md (battlecard, mention inventory, three tiers, the line, brief template — now references/aeo/offpage.md) -->

Produces briefs and target lists. **A human sends everything.** This skill never emails anyone, never posts, never comments, never submits a review, never edits a third-party listing.

Two jobs that share one lane because they share one target list. Link-era off-page asked *did they link to us*. Answer-engine off-page asks *what did they say about us* — and a partner page that links to us while describing us with abandoned positioning is actively feeding a narrative we don't want. Work both from the same inventory.

---

## Routes here

| Action | Candidate record carries |
|---|---|
| `offpage-brief` | The finding id (from `.seo/aeo/findings.md` or the link gap) · the tier (1/2/3) · the source name and URL · the relationship, if any · what it currently says, quoted · what we want it to say · which attribute or keyword gap it closes · the citation or referring-domain evidence |

An `offpage-brief` never ships a page. Where a finding's route is **off-page trust**, more of our own content does not move it — that's the whole reason the route exists (`references/aeo/diagnose.md`).

Two more sources route here from `backlink_diff.py` (measure.md §6e), and they jump the friction order because the recipient already chose to mention us once:

| Source | Brief |
|---|---|
| `lost-link` | **Reclamation.** The linking page and the page it linked, the date the link was last seen, why it is gone if the page shows it (the target moved, the page was rewritten, the link now 404s on our side), and the one-line ask: restore the link to `<current URL>`. If our side broke it, the fix is the technical lane's repair class 8 first, and the brief only if the link does not come back on its own within a crawl. |
| `unlinked-mention` | **Link request.** Fetch the page first and confirm there is no link to our domain. The brief quotes the sentence that names us, asks for the name to link to the one page that best matches the sentence, and offers nothing in return. Skip mentions in the comments of a page, in a listicle that links every other product but us on purpose (that is a Tier 2 listicle ask, different brief), or on a domain with a spam score over 30. |

Both use the §6 template. Both carry the target page's Search Console clicks as their evidence, so the run record can say what a restored link points at.

---

## Read first

1. `.seo/brand.md` — positioning and the "not for" clause. Every ask is checked against it.
2. `.seo/truth.md` — the facts a third party is getting wrong, in our own words. Never skip: the requested wording must match it exactly.
3. `.seo/aeo/battlecard.md` — if it exists. Every off-page ask gets checked against this file.
4. `.seo/aeo/mentions.md` — the existing inventory. Never rebuild it from scratch when it exists; append.
5. `references/aeo/offpage.md` — the battlecard structure (§1), the inventory pass (§2), the three tiers (§3), **the line** (§4), and the brief template (§5). Never skip.
6. `.seo/aeo/findings.md` — the citation evidence behind the ask. A brief that can say "this page is cited in 11 of 72 discovery responses for our category" gets acted on; one that can't, doesn't.
7. `references/research-recipes.md` — Recipe F, when the target list needs regenerating.

---

## Steps

### 1 — Build or refresh the battlecard

`.seo/aeo/battlecard.md` is our positioning in the plain words an engine would use, the attributes we want promoted with suggested phrasing, and each objection with its reframe. Three sections; write it from `assets/battlecard.template.md`, structure explained in `references/aeo/offpage.md` §1. Every ask in every brief traces to a line in this file; an ask that doesn't is an ask nobody agreed to make.

### 2 — Inventory what already exists

Every third-party source that mentions us, each checked against the battlecard, tagged by relationship, with the specific correction to request. Score each on: is it accurate · is it current · does it use our category or someone else's · is it cited by answer engines · **are the facts right** (score against `.seo/truth.md` — a wrong price on a widely-cited comparison page is a direct revenue leak and outranks everything else on the list). Write `.seo/aeo/mentions.md` from `assets/mentions.template.md`.

### 3 — Generate the target list (Recipe F)

For each top-3 competitor:

```
backlinks_referring_domains
target: <competitor-domain>
where: domain_rating >= 30 AND traffic_dofollow >= 100
order_by: domain_rating:desc
limit: 100
```

Sort each candidate domain into a bucket:

| Bucket | Signal |
|---|---|
| **Directory candidates** | Site name matches "[category] directory", "best of [category]", "[category] tools", "alternatives to [tool]" |
| **Listicle candidates** | Posts titled "Top X [category] in YYYY" — pitch for inclusion |
| **Guest-post candidates** | Reads like a blog (`*.com/blog/...`), DR 30+, posts on our niche |
| **Skip** | PR wires, paid networks, irrelevant niches, and sites that link to *everyone* in the space |

Save to `.seo/backlink-targets.json`:

```json
{
  "generated_at": "2026-MM-DD",
  "directories": [
    { "domain": "g2.com", "dr": 88, "url_to_submit": "https://www.g2.com/products/new", "competitor_uses": ["competitor-a", "competitor-b"] }
  ],
  "listicles": [
    { "domain": "example.com", "dr": 65, "url": "https://...", "topic": "Best [category] tools", "competitor_listed": "competitor-a" }
  ],
  "guest_posts": [
    { "domain": "example.com/blog", "dr": 81, "topic_fit": "founder-led marketing" }
  ]
}
```

Cross it against Stream B from the AEO panel: where competitors are **cited** and we aren't is a data-generated target list, not a guessed one, and it's usually a different list than the referring-domain sweep produces.

### 4 — Order by friction, not by authority

Three tiers, in this order. The order follows the friction gradient: updating something that already mentions us is easier than getting added to something that doesn't, which is easier than creating a new source and waiting for it to earn enough authority to be cited.

**Tier 1 — optimize what already mentions us.** The highest-yield and most-skipped work in the whole program. Prioritize by relationship: integration partners, then affiliates, then investors and advisors, then industry associations and analysts. The first three are routine asks between people who already work together; the last is slower and higher authority, and worth running in parallel rather than after.

**Tier 2 — get added where we're absent.** Comparison articles and listicles (effective today; expect increasing scrutiny over time, so don't build the whole strategy on one format) · category directories our buyers use for vendor discovery · integration partner pages (for every integration we ship there should be a page on their site describing it accurately — many don't exist, many are wrong) · review platforms, where presence *and* accuracy both matter and being listed incorrectly is often worse than absence because it's authoritative-looking and wrong.

**Tier 3 — create new sources.** Original research and data first: a dated, sourced, first-party number is a new observation about the world, and models hold unlimited synthesis and have a permanent shortage of new observation. It's the most durable asset here and it earns coverage, which creates further sources. Then guest and co-authored content on domains that already carry citation authority in the category. Then genuine community participation — the word doing the work is *genuine*.

### 5 — The directory starter stack

A one-time sweep, worth a phase of its own. Most are free; all are worth a single submission.

**Directories:** Product Hunt (biggest launch-day backlink and traffic source) · G2 · Capterra / GetApp / Software Advice (Gartner Digital Markets, one submission flow) · SaaSHub · AlternativeTo (list as an alternative to the top 5 competitors) · Betalist (pre-launch or recently launched) · Indie Hackers products · TopAlternatives / SimilarSiteSearch / Slant · Crunchbase (even a free profile passes DR).

**Community surfaces, selective:** niche subreddits only — find them by running `serp_organic_live_advanced` on the target keywords and noting which subreddits surface; engage genuinely, never just post a link. Slack/Discord communities for the audience — join 3–5 and contribute for two weeks before mentioning the product. Hacker News for technical products, and only with a real launch story.

**Founder outreach, the slow-burn channel:** link trades with complementary non-competitive products (mutual blog mentions, "tools we love" pages, guest posts) and guest posts on DR 30+ blogs found via Recipe F. One to two strong pitches a month.

### 6 — Write one brief per ask

The skill writes it, a human sends it. **The template is in `references/aeo/offpage.md` §5 — use it verbatim, it is not restated here.** Every brief carries: source name and URL · relationship and the contact the user knows there · the finding id it closes · what the page currently says, quoted · the problem, with the citation evidence and its n · the exact requested wording · why that wording is accurate · the one-sentence ask · the effort for the recipient.

The brief works because it is specific, short, accurate, and asks for one small thing. Contrast with "could you update our description," which requires the recipient to do the thinking and therefore does not get done.

### 7 — Off-page phase templates (for the roadmap)

Two tail-end phases in `.seo/roadmap.md`, both explicitly external work with no files modified:

```markdown
### Phase N — Directory submissions (starter stack)

**Why:** baseline presence and links from high-DR directories. Cap at 2-3 hours of submission work.

**Scope:**
- [ ] Product Hunt — schedule launch (separate launch work)
- [ ] G2 — submit product page
- [ ] Capterra — submit product page
- [ ] SaaSHub
- [ ] AlternativeTo — list as an alternative to: <top 5 competitors>
- [ ] Indie Hackers — claim product page
- [ ] Crunchbase — basic profile

**Files modified:** none — external work. Track status in `.seo/needs-you.md`.
```

```markdown
### Phase N+1 — Listicle outreach (top 10 targets)

**Why:** "Top X [category]" listicles already rank for our target keywords. Getting added is
faster than displacing them.

**Targets (from .seo/backlink-targets.json):** <ranked list with DR and current competitor listed>

**Action:**
- [ ] For each, find the author via the byline or about page
- [ ] Send the brief (one per target, written by this lane)
- [ ] Track reply status in `.seo/needs-you.md`

**Verification:** 3+ listicles update to include the product within 60 days.
```

---

## Gates

Non-waivable. Cost never overrides a gate. **The line** (`references/aeo/offpage.md` §4) is the first five.

1. **Never contact anyone.** Briefs and punch lists only. No emails, no posts, no comments, no review submissions, no third-party listing edits — regardless of how routine the ask looks.
2. **Never astroturf.** No sockpuppet accounts, fake community posts or manufactured discussion. It violates every platform's rules, it's detectable, and it poisons the exact signal we're trying to build.
3. **Never solicit incentivized or fabricated reviews.** Illegal in many jurisdictions and against every review platform's terms.
4. **Never ask a source to say something untrue** — including something merely flattering-but-unsupported.
5. **No mass unsolicited outreach, and no paid mention without the disclosure the venue requires.** Templated volume gets you filtered and remembered badly.
6. **Every requested wording matches `.seo/truth.md`** exactly, so the several places it appears corroborate rather than compete.
7. **Every brief names its finding id, the source URL, the current wording quoted, the requested wording, and the effort for the recipient.** A brief missing any of those isn't ready to send.
8. **Every claim of citation impact carries its numbers with n.** "This page is cited in 11 of 72 discovery responses" is evidence; "this page matters" is not.
9. **Never auto-submit.** Submission flows need real human review — G2 wants a screenshot, a URL and a verification email; Product Hunt needs a launch coordinator.
10. **Never claim causation from one correlation.** Off-page changes take weeks to reach answers.

**Honest caveat, stated in the hand-off:** off-page work is slower and more uncertain than on-page work. A great alternatives page ranks within 30–90 days. A great outreach campaign might produce three useful links in the first month and ten in three months. **Don't gate the on-page work on off-page progress** — ship pages, queue outreach in parallel. And the most durable off-page work is upstream of individual citations: do things worth talking about, publish original research, distribute it properly. Chasing individual placements is whack-a-mole at any real scale — a reasonable way to start from near zero, a bad plan to still be running in a year.

---

## Register

- `.seo/aeo/battlecard.md` — created or refreshed.
- `.seo/aeo/mentions.md` — the inventory, appended, each row tagged by relationship and carrying its specific correction.
- `.seo/backlink-targets.json` — the Recipe F output with `generated_at`, so the next run knows how stale it is.
- `.seo/aeo/worklog.md` — every brief **written**, dated, with its finding id; and every brief the user reports **sent**, with its send date. Without the send date you cannot tell a change that hasn't landed yet from one that didn't work, and those two need very different responses.
- `.seo/roadmap.md` — the off-page phase rows, checked off only when the user confirms the external action happened.
- `.seo/content-ledger.md` — an `offpage-brief` row: date · tier · source · finding id closed · status `drafted`.
- `.seo/runs/<date>.md` — the tier worked, the briefs produced, the targets deferred and why, and the recheck date.
- `.seo/needs-you.md` — **this is the lane's real output.** Every brief, with the source, the contact the user knows there, the one-line ask, and the effort estimate for the recipient. Ordered by friction, Tier 1 first.
