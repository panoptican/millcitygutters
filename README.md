# Mill City Gutters

Static marketing website for Mill City Gutters, a Minneapolis seamless-gutter company.

## Local development

Run a static file server from the repo root:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

Cloudflare Pages serves extensionless URLs (`/gutter-guards` for
`gutter-guards.html`); a plain static server does not, so use the `.html`
paths locally.

## Project structure

- `index.html` - homepage
- `gutter-guards.html` - gutter guards guide
- `404.html` - not-found page
- `css/main.css`, `css/overrides.css` - theme and site overrides
- `js/main.js` - menu toggle and contact form
- `img/` - photos, logo, and the hero image
- `functions/api/contact.js` - Cloudflare Pages Function that emails the contact form (Resend)
- `functions/_middleware.js` - blocks internal paths from static serving
- `robots.txt`, `sitemap.xml` - crawler directives and sitemap

## Deployment

Deployed to Cloudflare Pages from the `main` branch via Git integration -
pushing to `main` is deploying. Live at `https://millcitygutters.com`.

Set these environment variables in the Pages project:

- `RESEND_API_KEY` - required by the contact form function
- `CONTACT_EMAIL` - optional recipient; defaults to `info@millcitygutters.com`
