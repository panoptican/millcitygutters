# Mill City Gutters — Programmatic SEO Roadmap

> **Canonical document.** Single source of truth for the programmatic-page roadmap and its phase tracker. Lives at `.seo/roadmap.md`. Every worktree or agent picking up programmatic work reads this first.

---

## How to use this document

1. Read this entire roadmap file.
2. Read **Reference Data**, **Conventions**, and the **Keyword Research Appendix** once — shared facts.
3. Find the next `pending` phase in the **Phase Status Tracker**.
4. Read the phase section; it is self-contained.
5. Execute. Verify against the phase gate.
6. In the same commit, flip the tracker row to `completed` and append the PR number.
7. Open the PR. Stop.

**Don't modify** Reference Data, Conventions, or Phases without explicit user instruction.

---

## Phase Status Tracker

| # | Phase | Pattern | Status | PR |
|---|---|---|---|---|
| 0 | Technical foundations | Setup | pending | – |
| 1 | Core service pages (5) | `/services/[service]` | pending | – |
| 2 | Cost & decision guides | `/guides/[topic]` | pending | – |
| 3 | Service-area pages | `/areas/[city]` | pending | – |
| 4 | Off-page starter stack | Directories/citations | pending | – |

**Conventions:** `pending` → `in_progress` → `completed` (same commit as PR). `skipped` needs a one-line reason.

---

## Reference Data (read once per agent)

### 1. Site facts

- **Domain:** https://millcitygutters.com
- **GSC property:** not connected (null in `.seo/config.json`)
- **Bing site:** not connected
- **OpenSEO project:** none
- **Authority / playable bucket:** unknown → `easy` (estimated; no GSC or DFS). Re-derive once GSC is connected.
- **Stack:** plain static HTML at repo root; deployed to Cloudflare Pages (`millcitygutters`); one Pages Function at `functions/api/contact.js`.
- **Brand accent color:** #d76540
- **Hero font / body font:** Montserrat / Source Sans Pro
- **Marketing pages root:** repository root

### 2. Existing programmatic surface (DO NOT DUPLICATE)

| Pattern | Existing pages |
|---|---|
| All | none — one homepage (`index.html`) |

### 3. Critical files

| File | What lives there |
|---|---|
| `index.html` | the entire site: hero, about, services, contact form, schema, meta |
| `sitemap.xml` | single-URL sitemap, no `lastmod` |
| `robots.txt` | `Allow: /` + sitemap reference |
| `css/overrides.css` | brand overrides (orange #d76540, menu, header, form) |
| `css/main.css` | HTML5 UP "Solid State" base |
| `js/main.js` | menu toggle + contact form fetch to `/api/contact` |
| `functions/api/contact.js` | Cloudflare Pages Function -> Resend |

### 4. Conventions

**URL slugs:** lowercase, hyphenated, never underscored. Extensionless (`/services/seamless-gutters`, not `.html`) — confirm Cloudflare Pages serves pretty URLs for generated files before shipping. If it does not, ship `.html` files and link with the `.html` extension consistently, and update the sitemap to match.

**Every page:** unique `<title>`, meta description, canonical, one `<h1>`, Open Graph + Twitter tags, `RoofingContractor`/`HomeAndConstructionBusiness` JSON-LD, and ≥3 in-body internal links (≥1 back to the homepage).

**Honesty is non-negotiable** on any comparison page: real tradeoffs where the alternative wins.

**Internal-link minimums per page:** ≥3 outbound to sibling/category pages; ≥2 inbound from existing pages (≥1 the homepage).

**Word counts (local-service floors):** service pages ≥600 words; guides ≥1,200; area pages ≥500 with genuinely local content, never a template swap.

**Schema per pattern:** `BreadcrumbList` + `Service` on service pages; `FAQPage` where an FAQ section exists; `Article` on guides; `LocalBusiness`/`HomeAndConstructionBusiness` on area pages only if the page is a real business location — otherwise do **not** fake local schema. Never self-author `AggregateRating`/review schema.

---

## Keyword Research Appendix

> All numbers are placeholders until a keyword source is connected. Re-query when a phase executes >90 days out. Demand evidence for each `create` candidate must come from a dated source (GSC row or thread) per the skill's content rules — no provenance, no create.

### A.1 — `/services/[service]` candidates

| Service | Target keyword | Vol | Bucket | Intent |
|---|---|---|---|---|
| seamless gutters | seamless gutter installation minneapolis | TBD | E | transactional |
| gutter protection | gutter guards minneapolis | TBD | E | transactional |
| copper gutters | copper gutters minneapolis | TBD | E | transactional |
| k-style / half-round | half round gutters minneapolis | TBD | E | transactional |
| oversized gutters | 6 inch gutters minneapolis | TBD | E | transactional |

### A.2 — `/guides/[topic]` candidates

| Topic | Target keyword | Vol | Bucket | Intent |
|---|---|---|---|---|
| cost | gutter replacement cost minneapolis | TBD | E | informational→transactional |
| guards worth it | are gutter guards worth it | TBD | E | informational |
| winter/ice | ice dams and gutters minnesota | TBD | E | informational |
| material comparison | aluminum vs copper gutters | TBD | E | informational |
| seamless vs sectional | seamless vs sectional gutters | TBD | E | informational |

### A.3 — `/areas/[city]` candidates

Minneapolis · Saint Paul · Bloomington · Edina · Richfield · St. Louis Park · Eden Prairie · Minnetonka · Roseville · Woodbury. **Only** after a real, differentiated local angle exists per city; no thin doorway pages.

### A.4 — Striking-distance (positions 5-20 in GSC)

None — no GSC connection.

### A.5 — Out of scope (intentionally excluded)

Roofing, siding, windows, snow removal, commercial-only work. Building a page for an adjacent service we do not offer is off-topic and a trust cost.

---

## Phases

### Phase 0 — Technical foundations

**Why:** the day-0 crawl shapes how Google understands the site for months. Fix before shipping content.

**Scope** (from the first health diff):
1. Sitemap: add `<lastmod>` and any new URLs as they ship.
2. Investigate the JSON-LD `@type` (`RoofingContractor` vs a gutter-accurate type).
3. Add `llms.txt`.
4. Confirm pretty-URL behaviour on Cloudflare Pages. **Done 2026-09-11** — `.html`→pretty and http/www canonicalization are clean single-hop 301/308.
5. Submit sitemap in GSC + Bing once connected.
6. Fix the site-wide soft-404. **Done 2026-09-11** — added `404.html` on branch `seo/repair-indexing` and disabled Cloudflare email obfuscation on the contact mailto; pending deploy verification (NY-9).

**Verification:**
- [ ] `tech_audit.py --domain millcitygutters.com` returns 0 critical findings
- [ ] sitemap parses and every listed URL is 200

### Phase 1 — Core service pages

Five pages, one per service on the homepage. Each: unique metadata, `Service` + `BreadcrumbList` schema, ≥600 words, ≥3 internal links, one real informational-gain element (photo, cost factor, material detail). Build a shared header/footer partial convention for the static stack. **Gate:** one page per PR; a sibling's page must be indexed/healthy before the next ships.

### Phase 2 — Cost & decision guides

`/guides/gutter-replacement-cost-minneapolis` first (highest intent), then guards-worth-it, ice-dams, material comparison, seamless-vs-sectional. This is the editorial lane, not programmatic; it lives here for tracking only.

### Phase 3 — Service-area pages

Only where a differentiated local angle exists. No thin city-swap pages.

### Phase 4 — Off-page starter stack

Local citations and directories (Google Business Profile, Bing Places, Yelp, Angi, Nextdoor, BBB, local chambers) — briefs only, a human submits. Never buy links.

---

## Off-page checklist

- [ ] Google Business Profile — claim/verify + full services
- [ ] Bing Places
- [ ] Yelp for Business
- [ ] Angi / Thumbtack
- [ ] Nextdoor Business
- [ ] BBB
- [ ] Local chamber / neighborhood association listings

---

## Glossary

- **Bucket** — Easy / Medium / Hard winnability read; your playable bucket is the hardest where GSC shows 2+ page-1 positions.
- **Striking distance** — pages ranking position 5-20 in GSC, one push from page 1.
