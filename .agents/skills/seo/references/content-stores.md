# Content Stores — where content lives and how to publish to it

The skill's default mental model is "content = a file in the repo." That's only one storage model. Many sites keep content in a **database or headless CMS** — there's no file to write and no git history to scan. This file generalizes the skill across every store. `output-formats.md` handles the *file* case in detail (frontmatter, layout); this is the umbrella that decides which case you're in and how the file-assuming steps adapt.

Whatever the store, the skill needs three operations: **read existing content** (for dedup + voice-matching + link targets), **write the new piece**, and **wire inbound links**. Resolve the store type once at setup (`.seo/config.json` → `stack.content_store`), then each step branches off it.

Two unlocks make this work on *any* site:
- **The sitemap is a universal read path** — every CMS publishes `/sitemap.xml`, so you can always discover existing content even with no file or API access.
- **A portable artifact + field map is a universal write path** — when there's no programmatic write, produce the finished piece plus an exact "paste this here" map and hand it off.

---

## Detect the store (and persist it)

| Store type | Signals | `content_store.type` |
|---|---|---|
| **Files** | a content dir (`src/content`, `content/`, `_posts/`, MDX), Astro/Next/Hugo/Jekyll content config | `files` |
| **Headless CMS** | deps like `@sanity/*`, `contentful`, `@strapi/*`, `payload`, `@prismicio/*`, `@storyblok/*`, `@ghost/*`; config files (`sanity.config.*`, `strapi`, `payload.config.*`) | `headless_cms` |
| **App DB** | a `Post`/`Article`/`BlogPost` model + migrations (Rails/Django/Laravel) or a Prisma schema with a posts table, and **no** content dir | `app_db` |
| **WordPress** | `wp-config.php`, `wp-content/`, or `/wp-json` reachable on the live domain | `wordpress` |
| **Builder / doc-CMS** | Webflow/Wix/Squarespace (proprietary, no repo content), or Notion/Airtable as CMS | `builder` |
| **Unknown / none** | none of the above | `manual` |

Write the resolved store to `.seo/config.json` under `stack.content_store`, expanding the template's placeholder string into this object:

```json
"content_store": {
  "type": "wordpress",
  "platform": "wordpress",
  "base_url": "https://example.com",
  "read_method": "rest_api | sitemap | git | mcp",
  "write_method": "rest_api | cli | mcp | console_script | file | manual",
  "model_or_collection": "post",          // table/model/collection name where relevant
  "body_format": "html | markdown | portable_text",
  "auth_note": "where creds live, or null if hand-off only"
}
```

**When ambiguous, ask once**: *"Where does your published content live, and should I write directly (via [detected method]) or hand you a ready-to-paste piece?"* Never assume you have write access to a production CMS. **Unattended, don't block:** take the safe branch — treat the store as hand-off only, produce the portable artifact plus the field map, and file the question in `.seo/needs-you.md`.

---

## Operation 1 — READ existing content

Needed for the exclusion set (dedup), internal-link targets, and reading 1-2 real posts to match voice.

- **`files`** → `git ls-files | grep -iE 'blog|guides|content|articles'` (the current path).
- **everything else** → **the sitemap is the universal fallback.** Fetch `/sitemap.xml` (or `/sitemap_index.xml` → the content sitemap), filter to content URLs, fetch the blog index, and fetch 1-2 existing posts (page fetch) to read voice and capture link targets.
- **richer metadata when an API/MCP exists** → list entries through it (WordPress `GET /wp/v2/posts`, Sanity GROQ, a Notion query via the Notion MCP) for titles, slugs, dates, and tags without scraping.

The sitemap path means dedup and link discovery work on a live site you have *no* code access to.

---

## Operation 2 — WRITE the new piece

**Default: produce a complete, portable artifact + a field map, and only push it when a write path is configured — always as a DRAFT.** Never auto-publish (same ethos as never auto-committing files; writing to live content is outward-facing and hard to reverse).

- **`files`** → write the file per `output-formats.md`.
- **API / CLI / MCP configured & authorized** → create a **draft** entry, mapping the piece's fields to the store's schema:

  | Piece field | Maps to |
  |---|---|
  | title, slug, body, excerpt/meta description, author, publish date, canonical, JSON-LD | the store's equivalent fields |

  Examples: WordPress → `wp post create --post_status=draft --post_title=… --post_content=…` or `POST /wp/v2/posts` with `status:"draft"`. Sanity → client `create` (or a draft doc). Strapi/Payload/Ghost → their REST/admin API with a draft/unpublished status. Convert the **body to the store's format** (`body_format`): HTML for WordPress/most CMS, markdown if accepted, portable text for Sanity.
- **no write path (the safe default)** → hand off: the rendered body + a precise field map ("paste into Title / Slug / Body / Meta description / Author / Published date") + the JSON-LD block to add. Tell them exactly where each piece goes.

Schema (JSON-LD) still ships either way — embedded in the body if the CMS has no head-control, or via the theme's SEO plugin/field (Yoast, RankMath, Sanity SEO field).

**Figures need a compatibility check on non-file stores.** CMS sanitizers frequently strip `<svg>` out of post bodies. Push **one small figure first** and look at the draft preview before authoring five. If it survives, inline the rest (`visuals.md`). If it's stripped: upload the SVG as a media asset and reference it — accepting that it loses page-CSS theming and won't follow dark mode — or fall back to the store's native table/embed block. Either way, say which happened in the hand-off; a silently-stripped figure looks identical to a piece that shipped without one.

---

## Operation 3 — WIRE inbound links (no orphans)

The ≥2-inbound-links requirement holds for every store; only the mechanism changes.

- **`files`** → edit ≥2 existing files to add the link (current path).
- **DB / CMS** → default to an **inbound-link punch-list** rather than programmatically editing live content: *"Add a link to [new piece] from these 2 existing posts — [url-1] (anchor: '…'), [url-2] (anchor: '…')."* Safer and reviewable. If a write path is configured and the user wants it, update those entries via API as drafts/revisions.

---

## Verification for non-file stores

- **`word_count.py`** → run on the draft saved to a local staging file (e.g. alongside the brief in `.seo/briefs/`). The script doesn't care where the content ultimately lands.
- **`link_audit.py --orphan-check`** → filesystem-only; **skip for DB/CMS.** `health_diff.py --check-links` (inbound counts and orphans from the live site) and `link_opportunities.py` (missing links) replace it; both read the rendered site and need no repo access.
- **`truth_check.py --from-health`** → the truth check over rendered pages, after `health_diff.py --keep-text`. This is the only truth check a DB/CMS store has; `measure.md` §4 runs it every run.
- **Fixes, refreshes, consolidations and prunes on rows** → the write contract and change record in `stacks/app-db.md`; the same file covers programmatic batches as seed data.
- **`tech_audit.py --schema <url>`** → works great — point it at the draft/preview URL the CMS gives you. Schema validation is *easier* on a rendered store than on a not-yet-built file.

---

## Foundation + link inventory for non-file stores

`foundation.md` §7 builds `.seo/link-inventory.md` from `git ls-files` for file repos. For DB/CMS, build the same inventory from the **sitemap (or API)** instead — same template, different source. And in `foundation.md` §1, detect and persist `stack.content_store` (above) at the same time as the rest of the config.
