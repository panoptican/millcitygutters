# Mill City Gutters — Content Ledger

> The memory of the engine. Read first on every `/seo` run: **Shipped** is the dedup record, **Performance** is the scoreboard, **Candidate backlog** is the scored shortlist. Updated in the same edit batch as every piece shipped.

---

## Shipped

| Date | Title | Type | Slug / URL | Target keyword | Vol | Bucket | Original data (source · n · as-of) | Refresh due | Primary internal links | Commit / PR |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-11 | Are Gutter Guards Worth It in Minneapolis? | guide (decision) | /gutter-guards | gutter guards minneapolis | n/a (no DFS) | easy | none — framework/expert; third-party market price ranges (public competitor pages, 2026-09) | 2027-03-11 | /#services, /#costs, / | PR #6 (merged) |
| 2026-09-11 | Site-wide soft-404: unknown paths served the homepage with HTTP 200 | repair | /404.html | — | — | — | — | — | — | seo/repair-indexing |

<!-- One page exists (the homepage) and it predates this ledger. Backfill it as a row when GSC is connected. -->
<!-- Type ∈ guide | how-to | listicle | definition | comparison | data-study | resource | opinion | case-study | tool -->

---

## Performance

> Baselines now from a **manual GSC export** (28 days, 2026-08-13 → 2026-09-09): site totals 7 clicks · 1,409 impressions · 0.5% CTR · avg pos 26.19; **0 branded impressions**. A live GSC client is still not connected — these are snapshots the user supplied.

| Slug / URL | Published | Indexed? (state · checked) | Read @28d (clicks · impr · pos) | Read @56d (clicks · impr · pos) | Site-wide same window (clicks · impr) | Best lever (recover/CTR/rank · est. clicks) | State | Note / next action |
|---|---|---|---|---|---|---|---|---|
| / | pre-ledger | indexed (GSC coverage 2026-09-11) | 7 · 1,409 · 26.19 | — | 7 · 1,409 | rank (avg pos 26; "gutters twin cities" pos 12, install/replacement pos 21–30) | watch | Only page with impressions; 0 branded. The homepage can't own the install/replacement cluster above pos 21 — a dedicated service page is the fix |
| /gutter-guards | 2026-09-11 | not yet crawled (published today) | — | — | 7 · 1,409 | — | unmeasured | New decision guide; re-read after 28 days. Target of the homepage's guard links |

---

## Candidate backlog

> Scored shortlist from the last selection run. Re-score when this is >30 days old.

| Rank | Candidate | Proposed type | Target keyword | Vol | Bucket (E/M/H · src) | Intent | Data angle | Score | Notes / angle |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Seamless gutter cost in Minneapolis | guide (decision) | seamless gutters cost minneapolis | TBD | easy (est.) | commercial/informational | market ranges + our per-foot model (no first-party price) | 27 | Runner-up this run. Competitor Owl Roofing owns a 2026 cost page; gap is a local per-foot explanation. |
| 2 | Repair site-wide soft-404 (unknown paths return homepage, HTTP 200) | repair | — | — | — | — | — | 22 | **IN PROGRESS 2026-09-11** — `404.html` added on branch `seo/repair-indexing`; also disabled Cloudflare email obfuscation on the contact mailto. Verify post-deploy. |
| 3 | Measure-only | — | — | — | — | — | — | — | No GSC/DFS; nothing else cleared the bar. |

<!-- Score = winnability + traffic-potential + conversion-intent + strategic-value + data-angle + (6 - effort), each 1-5. -->

---

## Coverage map (optional)

| Cluster / theme | Pieces shipped | Gaps still open |
|---|---|---|
| Seamless gutter installation | 0 | everything — no service page |
| Gutter protection / guards | 1 | guide shipped 2026-09-11; still no dedicated service/installation page |
| Gutters & Minnesota winter / ice dams | 0 | no page |
| Gutter cost & pricing | 0 | no page; strongest informational intent |
| Copper / half-round / specialty | 0 | no page |
| Local service areas (Minneapolis, St. Paul, suburbs) | 0 | no pages |

---

## Notes

- **Difficulty buckets, not a KD cap:** playable bucket currently `easy` (estimated — no GSC yet). Re-derive from page-1 GSC positions once connected.
- **No duplication:** check against `.seo/roadmap.md` before adding a candidate.
- **One piece per run.**
- **This is a cold start.** The site has one page, no content, no connected analytics. Early runs are about building the spine (service + location pages, schema, internal links), not optimizing a library that does not exist yet.
