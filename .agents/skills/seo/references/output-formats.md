<!-- merged from seo-content/references/output-formats.md + seo-sprint/references/stacks/markdown-fallback.md -->

# Output Formats — shipping file-based content into any stack

> **Is the site's content actually in files?** This file covers the **file-based** store — markdown/MDX/content-collection pieces committed to the repo. If content lives in a **database or headless CMS** (WordPress, Sanity, Contentful, Strapi, Payload, Ghost, a Rails/Django/Prisma model, Webflow, Notion-as-CMS…), start from `content-stores.md` instead — it owns the read/write/inbound-link flow for those, and points back here only if the store turns out to be files.

Editorial pieces (guides, how-tos, listicles, etc.) live wherever the site already publishes its blog/content. Your job is to **detect that surface, match its existing shape, and reuse its layout** — never to invent a new content system.

The golden rule: **find one existing published article, copy its file location + frontmatter shape + layout component exactly, and slot the new piece in beside it.** If the repo already publishes content, that existing piece is a more reliable spec than anything below.

---

## Step 1 — Detect the content surface

Run from the repo root. First match wins.

| Signal in the repo | Where editorial content usually lives |
|---|---|
| `astro.config.*` | `src/content/<collection>/*.md(x)` (Content Collections) — schema in `src/content/config.ts` |
| `package.json` has `next` + `app/` | MDX in `content/` or `src/content/`, or a `app/blog/[slug]/page.tsx` route reading from a data dir / CMS |
| `package.json` has `next` + `pages/` | `pages/blog/*.mdx` or a `posts/` markdown dir read at build time |
| `Gemfile` has `rails` (+ maybe `inertia_rails`) | a `Post`/`Article` model + DB, or markdown in `app/views`/`content`, or an Inertia page fed by a controller |
| `_config.yml` (Jekyll) | `_posts/YYYY-MM-DD-slug.md` with Jekyll frontmatter |
| `config.toml`/`hugo.*` (Hugo) | `content/blog/<slug>.md` with Hugo frontmatter |
| `gatsby-config.*` | markdown in `content/` sourced via `gatsby-source-filesystem` |
| `nuxt.config.*` | `content/` (Nuxt Content) markdown |
| `svelte.config.*` (SvelteKit) | `src/routes/blog/<slug>/+page.md(svx)` or a posts dir |
| None / unknown | **Markdown fallback** (below) — emit portable markdown and tell the user where to wire it |

Confirm the guess by actually finding an existing post: `git ls-files | grep -iE 'blog|posts|articles|content|guides'`. If you find one, **its real path and frontmatter win over this table.** Persist the resolved location to `.seo/config.json` (e.g. `"content_dir"`, `"content_layout"`) so the next run starts warm.

If two surfaces are plausible (e.g. both `app/` and `pages/`, or a separate marketing repo), ask the user once rather than guessing. Unattended, take the surface holding the most existing published posts, record the choice in the run record, and file the confirmation in `.seo/needs-you.md`.

---

## Step 2 — Match the frontmatter

Read an existing post's frontmatter and reproduce its exact keys. Don't add fields the site's schema doesn't have (it'll fail the build), and don't drop ones it requires. Typical editorial fields:

```yaml
---
title: "..."                 # the H1 / display title
slug: "..."                  # lowercase, hyphenated, 2-5 words
description: "..."           # meta description, ≤155 chars
date: 2026-01-15             # published date (match the site's key: date / pubDate / publishedAt)
updated: 2026-01-15          # if the site tracks it
author: "..."                # if the site has authors
tags: ["..."]                # if the site uses them
canonical: "https://..."     # canonical URL
image: "..."                 # OG/hero image (see images note below)
---
```

Whatever the site's existing schema is, **match it.** If it uses `pubDate`, use `pubDate`. If posts carry a `category` enum, pick a valid value. The build is the test — a frontmatter mismatch is a hard failure, not a style nit.

---

## Step 3 — Reuse the layout, emit the SEO surface

- **Layout:** render through the **existing** blog/article layout component. Do not create a new template. If the layout already emits `<title>`, meta description, canonical, and OG tags from frontmatter, just populate those fields. If it doesn't, add the meta/canonical/OG and JSON-LD `<script type="application/ld+json">` block inline in the content or via the layout's head slot — match how other pages do it.
- **Schema (JSON-LD):** emit the type the piece requires (`Article`, `HowTo`, `FAQPage`, `ItemList`, `Dataset`, `BreadcrumbList` — per `content-types.md`). Validate with `scripts/tech_audit.py --schema <url>` once rendered.
- **TOC / anchors:** if the layout auto-generates a TOC from headings, just write clean `##`/`###` structure. If not and the piece is ≥1,500 words, add an anchored TOC the way existing long posts do.
- **Figures (charts, diagrams, illustrations):** **author them, inline, in this commit** — see `visuals.md`. Inline `<svg>` in the body for markdown/MDX (both pass raw HTML through); a component beside the site's existing components for Astro/Next/Nuxt/SvelteKit; the repo's existing chart component if it has one. Never `<img src="chart.svg">` — an SVG loaded that way is cut off from page CSS, so `currentColor` and CSS variables stop resolving and dark mode breaks. If the site's markdown pipeline strips raw HTML, move the figure into a component and note it.
- **Raster images (hero / OG / photography):** specify what's needed (1200×630) but don't fabricate them. Hand off to `og-image` / `feature-image` if installed; otherwise leave a clearly-marked placeholder path and note it in the handoff so the user supplies the asset. This is the *only* image category that stays a placeholder.

---

## Markdown fallback (no detectable content surface)

If the stack has no content system yet, emit portable markdown with complete frontmatter and **tell the user where to wire it in.** Don't try to build a CMS. The user wires the directory into their templating layer once; every run after that is just another file.

### Editorial pieces

```
content/blog/<slug>.md
```

```yaml
---
title: "..."
slug: "..."
description: "..."
date: 2026-01-15
canonical: "https://example.com/blog/<slug>"
schema: [Article, FAQPage]      # which JSON-LD the renderer should emit
---

# <H1 with primary keyword>

...body...
```

### Programmatic pages

Pattern pages carry their whole rendered payload in frontmatter, so the renderer is a template rather than a prose pipeline:

```
content/seo/
├── alternatives/
│   ├── hootsuite.md
│   └── ...
├── for/
│   ├── agencies.md
│   └── ...
├── compare/
│   ├── buffer-vs-hootsuite.md
│   └── ...
└── playbooks/
    └── b2b-social-media-strategy.mdx
```

**`content/seo/alternatives/<slug>.md`** — the full alternatives payload as frontmatter; the body is optional because the frontmatter carries everything rendered:

```yaml
---
slug: hootsuite
competitor_name: Hootsuite
meta_title: "Hootsuite Alternative — ExampleCo (free, $25/mo Pro)"
meta_description: "Looking for a Hootsuite alternative? ExampleCo is the lightweight social monitoring tool with a free tier."
canonical: "https://example.com/alternatives/hootsuite"
hero_eyebrow: "Hootsuite alternative"
hero_h1: "Looking for a Hootsuite alternative?"
hero_lede: "..."
table_h2: "Best Hootsuite alternatives in 2026"
table_lede: "..."
comparison_rows:
  - feature: "Free plan"
    yours: { state: yes, note: "Free forever for 1 X account" }
    theirs: { state: no, note: "Discontinued in 2023" }
  # ... ≥10 rows total
switch_reasons:
  - icon: bolt
    title: "Reply in 30 seconds, not 5 minutes"
    body: "..."            # ≥40 words
  # ... 4 total
honesty_rows:
  - feature: "Multi-platform scheduling"
    body: "..."            # ≥30 words
  # ... 3-4 total
faqs:
  - question: "Why did Hootsuite end its free plan?"
    answer: "..."          # ≥40 words
  # ... 4-6 total
cta_h2: "..."
cta_lede: "..."
related_internal_links:
  alternatives: [buffer, sprout-social]
  features: [twitter-monitoring]
  tools: [reply-templates]
schemas: [FAQPage, SoftwareApplication, BreadcrumbList]
---
```

**`content/seo/for/<slug>.md`** — the same idea with the use-case shape: `slug`, `name`, meta fields, `hero_*`, `pain_h2` + `pains[]`, `solution_h2` + `solutions[]`, `faqs[]`, and `related_internal_links` with `features` / `tools` / `siblings`.

**`content/seo/playbooks/<slug>.mdx`** — the one pattern where the body carries the work: frontmatter holds metadata (`slug`, `title`, `meta_title`, `meta_description`, `date_published`, `date_modified`, `read_time_min`, `related_internal_links`), and the MDX body holds the 2,500+ words of prose under `##` sections.

### Sitemap, when the framework doesn't generate one

Most static-site frameworks emit a sitemap automatically once content is in the right collection. If yours doesn't, keep a generated data file and have the build step render `/sitemap.xml` from it:

```yaml
# content/seo/sitemap-data.yaml — alphabetical, regenerated on ship
last_modified: 2026-MM-DD
urls:
  - loc: https://example.com/alternatives/hootsuite
    changefreq: monthly
    priority: 0.8
```

`lastmod` must be a content date, never a build date.

### Hand-off note to include

> I wrote this as portable markdown under `content/`. Your site doesn't have a content pipeline I could detect, so it needs wiring once — **Hugo:** drop the files in a content dir with a layout per type · **Jekyll:** collections configured in `_config.yml` · **Eleventy:** a `_data/` directory or collection frontmatter · **Gatsby:** `gatsby-source-filesystem` plus `createPages` · **Next/Astro/Nuxt:** point a content loader at the folder · **VitePress/Docusaurus:** treat as MDX pages · **WordPress:** a custom theme that parses these, or import as posts. After that first wiring, every future run is just another file in the same directory.

### Markdown-mode checklist for any shipped page

- [ ] New file at the right path for its type
- [ ] Frontmatter validates against the schema the renderer expects
- [ ] Sibling files updated with the new slug under `related_internal_links` (≥2 spots)
- [ ] `sitemap-data.yaml` updated, if used
- [ ] The build ran successfully and the HTML output exists
- [ ] `grep -c '<h1' <build-output>/<path>/index.html` — exactly 1
- [ ] Ledger row and, for a pattern page, the `.seo/roadmap.md` tracker row updated in the same commit

---

## Verify the output rendered

After writing, confirm the page actually builds and emits one H1:

- Rebuild the site (or run the dev server) and load the new URL.
- `grep -c '<h1' <build-output path>` → must be exactly 1.
- **Look at every figure** on the rendered page — light and dark, mobile width and full width. Clipped labels, overlapping text, and axes that vanish on a dark background are only catchable by eye (`visuals.md` §3).
- Run the schema check: `python scripts/tech_audit.py --schema <url>`.

A piece that doesn't render is not shipped. Don't report success on an unbuilt draft.
