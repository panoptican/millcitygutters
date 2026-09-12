# Stack Detection

Goal: pick the right adapter reference file before generating any pages.

## Signal table

Run from the repo root. First match wins; if none match, fall back to the markdown fallback in `output-formats.md`.

| Signal | Adapter |
|---|---|
| `Gemfile` contains `inertia_rails` | `rails-inertia.md` |
| `Gemfile` contains `rails` (no inertia) | `rails-erb.md` (or the markdown fallback in `output-formats.md` if not present) |
| `package.json` has `next` in deps + `app/` directory present | `nextjs.md` (App Router) |
| `package.json` has `next` in deps + `pages/` directory present | `nextjs-pages.md` (or `nextjs.md` with a Pages-router note) |
| `astro.config.*` exists | `astro.md` |
| `package.json` has `@remix-run/*` | `remix.md` (or the markdown fallback in `output-formats.md`) |
| `nuxt.config.*` exists | `nuxt.md` (or the markdown fallback in `output-formats.md`) |
| `svelte.config.*` exists + SvelteKit deps | `sveltekit.md` (or the markdown fallback in `output-formats.md`) |
| `_config.yml` (Jekyll) | the markdown fallback in `output-formats.md` with Jekyll frontmatter notes |
| `config.toml` + Hugo signals | the markdown fallback in `output-formats.md` with Hugo frontmatter notes |
| `gatsby-config.*` | the markdown fallback in `output-formats.md` (Gatsby's prog-page API works with markdown) |
| None of the above | the markdown fallback in `output-formats.md` |

The table picks the *page* adapter. If `content-stores.md` resolved the content store to `app_db` (a `Post`/`Article`/`Page` model with a body column and no content directory), `app-db.md` applies **on top of** the framework adapter: the framework file says how a page is routed and rendered, `app-db.md` says how its copy is read, changed and reviewed. `headless_cms` and `wordpress` stores use `content-stores.md` Operation 2 for writes and `app-db.md` §3 for the change record.

## What to capture once detected

Add to the `stack` block of `.seo/config.json` (shape in `assets/config.template.json`):

```json
{
  "stack": {
    "kind": "nextjs-app",
    "language": "tsx",
    "marketing_controller": null,
    "pages_dir": "src/app/(marketing)",
    "data_dir": "src/data/seo",
    "routes_file": "src/app/(marketing)/layout.tsx",
    "sitemap_path": "src/app/sitemap.ts",
    "robots_path": "public/robots.txt",
    "llms_txt_path": "public/llms.txt",
    "header_component": "src/components/marketing/Header.tsx",
    "footer_component": "src/components/marketing/Footer.tsx"
  },
  "gsc": { "site_url": null },
  "openseo": { "project_id": null, "tracker_id": null },
  "paths": { "roadmap": ".seo/roadmap.md" }
}
```

`marketing_controller` is for controller-routed stacks (Rails, Django, Laravel); file-routed stacks leave it null and use `pages_dir`.

This config is read by every phase. If a value is null, the phase asks once and persists.

## Ambiguity resolution

When two adapters could match (e.g. Next.js with both `app/` AND `pages/` directories, common during migrations), ask the user via a question to the user:

- "I see both `app/` and `pages/` directories. Which is the active marketing surface?"

Never assume. Use the answer to pick the adapter and write it to `.seo/config.json`. Unattended, don't stall the run: pick the directory that actually holds the live marketing routes (the one the sitemap's URLs resolve into), label the choice as inferred in the run record, and file the confirmation in `.seo/needs-you.md`.

## Marketing-pages-in-app vs marketing-pages-in-separate-repo

Both are valid. Ask if there's ambiguity:

- **In-app marketing** (this skill's reference repo): marketing controller/pages live alongside the product. `/alternatives/*` is served by the same Rails app as the product dashboard.
- **Separate marketing site**: a different repo (`marketing.example.com`) shipped to a different host (Vercel, Netlify, Cloudflare Pages). Often a static-site generator.

For separate marketing sites, this skill should be run *from the marketing-site repo*, not from the product app repo. Confirm if there's any doubt.
