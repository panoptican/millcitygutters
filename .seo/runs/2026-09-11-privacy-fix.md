# Run record — 2026-09-11 — privacy fix

Follow-up to the 2026-09-11 repair run.

## Incident

PR #6 committed `.seo/` and `.agents/` into the repository root. Because the
Cloudflare Pages project builds and serves from the repo root, both directories
were publicly served by the site, and because the GitHub repo was public, they
were also readable on GitHub and in history.

Exposed without credentials:

- `.seo/config.json`, `.seo/brand.md`, `.seo/truth.md`, `.seo/needs-you.md`
- `.seo/briefs/`, `.seo/runs/`, `.seo/gsc/`, `.seo/census/`
- `.agents/skills/seo/` (the whole skill)
- `.gitignore`

No credentials or customer data were exposed. The leak was internal strategy,
research, business notes and the skill itself.

## Fixes

1. `0df2a0c` — added root `.assetsignore`. **Did not work**; Cloudflare Pages
   Git builds did not honor it. File left in place as harmless defense in depth.
2. `2c0af1f` — added `functions/_middleware.js`, a root Pages Function
   middleware that returns the site's `/404.html` with status 404 for
   `/.seo`, `/.agents`, `/.wrangler`, `/.git`, `/qa`, `/.gitignore`,
   `/.assetsignore`, `/.gitattributes`. This is the working fix.
3. GitHub repo changed from public to **private** (repository setting).

## Verified

- Pages: `/.seo/config.json`, `/.seo/needs-you.md`, `/.seo/brand.md`,
  `/.seo/truth.md`, `/.agents/skills/seo/SKILL.md`, `/.gitignore`,
  `/.assetsignore`, `/.git/` → all 404.
- GitHub unauthenticated: raw `.seo/needs-you.md`, raw `.agents/.../SKILL.md`,
  and the repo page → all 404.
- Site intact: `/` 200, `/gutter-guards` 200.

## Not done

- History was not rewritten. The files are now unreachable because the repo is
  private; if the repo is ever made public again the middleware will not cover
  GitHub and history would resurface the files.
- `.assetsignore` is redundant but retained.
