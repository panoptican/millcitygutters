# Source of truth

Derived from the repo on 2026-09-11. This is what fact-check prompts and `scripts/truth_check.py` are scored against. Re-derive whenever services, pricing, contact details or the service area change. A stale truth file turns correct answers into false accuracy failures.

| Claim | Value | Source | Read |
|---|---|---|---|
| Business name | Mill City Gutters | index.html:70 | 2026-09-11 |
| Phone | (612) 390-7483 | index.html:44, index.html:230 | 2026-09-11 |
| Email | info@millcitygutters.com | index.html:45, index.html:231 | 2026-09-11 |
| Street address | 5237 34th Avenue South, Minneapolis, MN 55417 | index.html:48-51, index.html:227-228 | 2026-09-11 |
| Service area | Minneapolis, Saint Paul, Twin Cities | index.html:54-58 (schema areaServed) | 2026-09-11 |
| Primary service | Seamless gutter installation (fabricated on site) | index.html:150-153 | 2026-09-11 |
| Aluminum gutters | 5-inch and 6-inch, seamless, rust-immune | index.html:159-161 | 2026-09-11 |
| Oversized gutters | 6-inch aluminum for larger homes/commercial | index.html:189-193 | 2026-09-11 |
| Gutter protection | Debris-blocking systems for gutters/downspouts | index.html:164-169 | 2026-09-11 |
| Copper gutters | Offered; develops protective patina | index.html:171-177 | 2026-09-11 |
| K-style & half-round | Offered; half-round suited to turret rooms | index.html:179-185 | 2026-09-11 |
| Tear-off of old gutters | Offered (separate per-foot rate) | index.html:139-140 | 2026-09-11 |
| Pricing model | One per-foot rate for installed gutter+downspout, one for tear-off; no fees for miters, drop-downs, screws, hangers, labor | index.html:137-141 | 2026-09-11 |
| Published prices | None — no dollar figures anywhere on the site | index.html (whole page) | 2026-09-11 |
| Years in business | Not stated numerically; page says "decades of experience" | index.html:106 | 2026-09-11 |
| Licensing / insurance | Not stated anywhere on the site | absent | 2026-09-11 |
| Warranty | Not stated anywhere on the site | absent | 2026-09-11 |
| Contact form delivery | Cloudflare Pages Function -> Resend API, to info@millcitygutters.com | functions/api/contact.js:39-59 | 2026-09-11 |
| Schema type | `RoofingContractor` (not a gutter-specific type) | index.html:40 | 2026-09-11 |
| Social profiles | facebook.com/millcitygutters, instagram.com/millcitygutters, twitter.com/millcitygutters | index.html:59-63, 232-234 | 2026-09-11 |

## Services we do NOT offer

Include the negatives. An engine synthesizing the web will happily attribute adjacent services to a contractor; a wrong "yes" cost you a wasted estimate.

| Service | Status | Source |
|---|---|---|
| Roofing / roof replacement | No | absent from services; only "RoofingContractor" schema type used as a container |
| Siding | No | absent |
| Windows | No | absent |
| Gutter cleaning as a standalone paid service | Not stated | absent (protection is sold, cleaning is not mentioned) |
| Solar / awnings / exterior painting | No | absent |

## Contradictions found

Where the code and the marketing site disagree. Each is already a finding.

| Claim | Code says | Site says | Which is right |
|---|---|---|---|
| Business category | `functions/` + services describe a gutter contractor | JSON-LD `@type` is `RoofingContractor` | Gutter contractor. `RoofingContractor` is a weak/adjacent fit and may route the wrong entity understanding into answer engines. Consider `HomeAndConstructionBusiness` with `knowsAbout: ["Seamless gutters", ...]`. |
| Contact subject line | `contact.js` sets subject "New website inquiry from {name}" + unique `X-Entity-Ref-ID` | No site surface describes delivery | Code is right; no user-facing claim. |
