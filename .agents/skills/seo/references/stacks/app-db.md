# Stack adapter: content in the application database

<!-- new in v2.2; the read, write and batch contract for sites whose public copy lives in rows, not files -->

Use this adapter when `stack.content_store.type` is `app_db` (`content-stores.md`): the site's pages, posts, FAQ tails, plan descriptions or comparison copy are rows in the app's own database, rendered by templates. `headless_cms` and `wordpress` stores use their API instead, but the write contract and the change record below apply to them too.

The skill's file assumptions break in exactly three places: finding where a claim lives, changing it, and reviewing the change. This file replaces each with a database equivalent. Everything that reads the live site (`health_diff.py`, the census, `link_opportunities.py`, `crawl_check.py`, the SERP and backlink panels, outcomes) already works unchanged.

## Contents

1. What to record in config
2. Read: find every page and every sibling
3. Write: the change contract
4. Correct, refresh, consolidate, prune on rows
5. Programmatic batches as data
6. Verification
7. Rules

## 1. What to record in config

Expand `stack.content_store` with the fields the recipes below need. Detect them from the schema (`db/schema.rb`, migrations, `prisma/schema.prisma`, `models.py`); ask once if two models could be the content table.

```json
"content_store": {
  "type": "app_db",
  "platform": "rails | django | laravel | prisma | sql",
  "read_method": "runner | shell | sql",
  "write_method": "migration | revision | draft_api | manual",
  "model_or_collection": "Post",
  "table": "posts",
  "body_field": "body",
  "body_format": "markdown | html | rich_text_json",
  "title_field": "title",
  "slug_field": "slug",
  "status_field": "status",
  "published_value": "published",
  "updated_at_field": "updated_at",
  "revisions": "PaperTrail | ActionText | none",
  "preview_url_pattern": "https://staging.example.com/blog/{slug}",
  "read_env": "production read replica via bin/rails runner -e production_readonly | staging | local dump",
  "auth_note": "where credentials live, or null if hand-off only"
}
```

`read_env` matters. Reading production is fine on a read replica or through the app's own read path; it is not fine through an ad-hoc SQL client with write credentials. Prefer staging or a fresh dump when either exists, and say which one the run used.

## 2. Read: find every page and every sibling

Two reads, both read-only.

**Inventory.** The sitemap is still the universal list of public URLs and the census works from it. When the sitemap is incomplete (draft pages, unlisted landing pages), list rows with `status = published` and build URLs from `slug_field` and the route.

**Sibling search.** The fix lane's "find every sibling" step is a grep in a file repo. Here it is a body search across every content table, plus the file grep for templates, `llms.txt`, schema `description` strings and marketing copy in code. Search the wrong phrase, the number, and the concept; one query per phrasing.

| Platform | Read-only sibling search |
|---|---|
| Rails | `bin/rails runner 'puts Post.where("body ILIKE ?", "%old phrase%").pluck(:slug)'`; add every model with public copy (`Faq`, `Plan`, `Comparison`) |
| Django | `python manage.py shell -c "from blog.models import Post; print(list(Post.objects.filter(body__icontains='old phrase').values_list('slug', flat=True)))"` |
| Laravel | `php artisan tinker --execute="echo Post::where('body','ilike','%old phrase%')->pluck('slug');"` |
| Prisma / Node | a one-off script with `prisma.post.findMany({ where: { body: { contains: 'old phrase', mode: 'insensitive' } }, select: { slug: true } })` |
| SQL | `SELECT slug FROM posts WHERE body ILIKE '%old phrase%';` against the replica, dump or staging, never a production writer connection |

Rich-text bodies (ActionText, Draft.js JSON, portable text) store markup around the words; search the plain-text projection when the app keeps one, else search the JSON as text and expect false positives. Record the query and the list of hits in the evidence file; the next run re-runs the same query to confirm nothing was missed.

`truth_check.py --from-health` (measure.md §4) covers the rendered side of the same question every run, once `health_diff.py --keep-text` has run. Use both: the rendered check finds copy that a template injects; the row search finds copy in unpublished or unlisted rows.

## 3. Write: the change contract

A file change rides in the PR. A row change does not, so it has to be turned into something that does. The contract, in order of preference:

1. **A data migration in the repo** (`write_method: migration`). Rails `db/migrate/<ts>_seo_correct_<slug>.rb`, a Django data migration, a Laravel migration, a Prisma migration script. It updates the specific rows by id, asserts the old value before writing (fail loudly if the row changed since the run read it), bumps `updated_at_field`, and is reversible. It is reviewed in the PR and applied on deploy by the app's normal migration step. This is the default because it keeps one-run-one-PR true.
2. **A draft revision through the app** (`write_method: revision`). When the app keeps revisions or drafts (PaperTrail, a `draft_body` column, a CMS draft state), write the new body as an unpublished revision through the app's own model or admin API, and record the revision id. A human publishes it. Never flip `status_field` to `published_value` from the skill.
3. **A draft through the CMS API** (`write_method: draft_api`), for `headless_cms` and `wordpress`: `content-stores.md` Operation 2, always `status: draft`.
4. **Hand-off** (`write_method: manual`). The change record below plus a precise "replace this with this in row N" list in `needs-you.md`. The default when no write path is configured or the run is unattended and the store has no draft state.

Whatever the method, the run also writes **the change record**: `.seo/evidence/<date>-<slug>.patch.md` (register.md §4) with the table and row ids, the field, the before text, the after text, the source of the truth, the query that found the siblings, and the exact apply step (the migration filename, the revision id, or the paste instructions). The ledger row carries the record path and the revision or migration id. This is what the PR reviews, and it is what lets a later run confirm the change landed by fetching the page.

Never `UPDATE` production from the skill's own connection, never publish, and never change a row the run did not read first.

## 4. Correct, refresh, consolidate, prune on rows

- **Correct.** Sibling search (§2), then one migration or revision covering every hit, with the before-value assertion per row. Template-side siblings (`llms.txt`, schema descriptions, code strings) are file edits in the same PR. Bump `updated_at_field` so the sitemap's `lastmod` and any `dateModified` in the page's schema tell the truth.
- **Refresh.** Same write contract; the new body replaces the row's body in the migration or revision. Title and meta refreshes for low-CTR pages are usually a two-field migration and the cheapest edit on the site.
- **Consolidate.** Two changes in one PR: the 301 in the routes or a `redirects` table (code), and the loser row set to unpublished (migration). Remove the loser from any generated sibling lists by unpublishing, not deleting; deletion loses the evidence. Update `link-inventory.md`.
- **Prune.** Unpublish the row and add the 301 or 410 in code. Keep the row; a pruned page with backlinks or a legal reason to exist was never a prune candidate (fix lane gates).
- **Internal links** (repair class 9, link opportunities): body edits are row edits and follow the same contract. Template-level links (nav, hub lists) are file edits.

## 5. Programmatic batches as data

A pattern phase (`lanes/programmatic.md`) on an app-DB site is rows, not files. The shape that works:

- **One table per pattern, or one `seo_pages` table with `pattern`, `slug`, `payload` (JSON) and `status`.** The template renders the payload; the pattern spec (`patterns/<pattern>.md`) defines the payload keys. A pattern change is a template change, not a rewrite of every page.
- **The batch is a seed file in the repo** (`db/seeds/seo/<pattern>.yml`, a fixtures JSON, a Prisma seed) loaded by an idempotent task keyed on `slug`, and a migration or task invocation in the PR. The seed file is the reviewable artifact and the tracker's "files modified" entry. Rows land as `draft`; the human's deploy publishes the phase.
- **Link spine.** Outbound links live in the payload; inbound links from existing pages are row edits under §3 or template edits when the hub is a template.
- **Sitemap.** Generated from published rows; check the generator includes the new table, and that `lastmod` reads the row's `updated_at_field`.
- **Gates** are identical. `word_count.py` runs on the rendered payload written to a staging file; schema validation runs on the preview URL.

## 6. Verification

- **Preview first.** Fetch `preview_url_pattern` for a changed row (or the local server) and confirm the new text renders and the old text is gone. `tech_audit.py --schema <preview url>` for schema.
- **After deploy**, the next run's `health_diff.py --keep-text` plus `truth_check.py --from-health` confirms the correction on the live site mechanically. Until it does, the ledger row says `applied: pending deploy`, and the cooldown clock starts at deploy, not at the run.
- **Link minimums** come from `health_diff.py --check-links` (inbound counts) and `link_opportunities.py`, both of which read the live site. `link_audit.py` is filesystem-only and does not apply.

## 7. Rules

- Read-only reads: the replica, a dump, staging, or the app's read path. Never a writer connection for a search.
- Every write is a migration, a revision, a draft, or a hand-off. Never a live update, never a publish.
- Assert the before-value in every migration. A row edited by a human between the run's read and the deploy must fail the migration, not be overwritten.
- One change record per action, always, whatever the write method.
- Bump the row's updated timestamp on content changes and leave it alone on link-only edits, the same rule as files.
- The census, cooldown and outcomes key on URLs, so nothing about scoring changes for a database site. Only the write path does.
