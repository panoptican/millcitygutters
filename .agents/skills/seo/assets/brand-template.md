# {{PRODUCT_NAME}} — Brand Context

> The voice contract. Read at the start of every `/seo` run — **everything written is governed by this file**, in every lane. Section headings match what the older `seo-content` and `seo-sprint` skills wrote, so a brand doc from either is readable as-is. If the file already exists, reuse it; never overwrite it.

## Product

- **Name:** {{PRODUCT_NAME}}
- **One-liner (≤20 words):** {{ONE_LINER}}
- **What we do:** {{LONG_DESCRIPTION}}
- **Pricing structure:** {{PRICING_SUMMARY}}
- **Free tier?** {{FREE_TIER_YN}} — {{FREE_TIER_DETAILS}}

## Audience

- **Primary persona:** {{PERSONA_PRIMARY}}
- **Secondary personas:** {{PERSONA_SECONDARY}}
- **Industries we target:** {{INDUSTRIES}}
- **Company size we target:** {{COMPANY_SIZE}}
- **Jobs to be done (top 3):**
  1. {{JTBD_1}}
  2. {{JTBD_2}}
  3. {{JTBD_3}}

## Competitors

(Who you're compared against and who ranks for your terms — seeds the content-gap research in `research-recipes.md`, the `/alternatives/*` and `/compare/*` patterns, and the honest treatment in comparison and listicle pieces. Order by perceived market share.)

| Brand | URL | Tier (head / mid / niche) | Notes |
|---|---|---|---|
{{COMPETITORS_TABLE}}

## Brand voice

**This section is the heart of the file.** Get it specific.

- **Voice tags:** {{VOICE_TAGS}} — e.g. "honest, technical, no-jargon, dry-witty, founder-led"
- **Person/perspective:** {{PERSPECTIVE}} — e.g. "we" (team), "I" (founder-led), "you-focused"
- **Forbidden words/phrases:** {{FORBIDDEN}} — hard ban, grepped before every piece ships. e.g. "seamlessly," "revolutionary," "synergy"
- **Forbidden claims:** {{FORBIDDEN_CLAIMS}} — anything legal, compliance, or accuracy says we must not say. A hard constraint on every page of on-page copy and every off-page brief, not a style preference. e.g. "never say HIPAA-compliant," "never imply a BAA we don't have"
- **Reference brands for tone:** {{TONE_REFERENCES}} — e.g. "Linear's docs, Buttondown's homepage"
- **Existing content to match:** {{EXISTING_CONTENT_NOTE}} — 1-2 published pieces whose rhythm new content should match (so a reader can't tell it was written in a different session)

## Anti-positioning (where we don't compete)

(Used for honest comparison/listicle sections — naming what you intentionally don't do is a trust + ranking signal. List ≥5.)

1. {{ANTI_POS_1}}
2. {{ANTI_POS_2}}
3. {{ANTI_POS_3}}
4. {{ANTI_POS_4}}
5. {{ANTI_POS_5}}

## Concrete differentiators

(Things you DO that competitors don't — used to weave the product into a piece where it genuinely helps the reader, not bolt it on at the end.)

1. {{DIFF_1}}
2. {{DIFF_2}}
3. {{DIFF_3}}
4. {{DIFF_4}}

## Proprietary data & first-hand experience

(The information-gain moat, and the section that most changes what this engine can produce. As of the 2026 core updates the pieces that win contain something the top 10 *can't* — original data, first-hand testing, lived experience — and answer engines reach hardest for fresh first-party observation, because synthesis is the one input they already have in unlimited supply. List what this product can legitimately draw on, **plus how to actually reach it**, so every run can attempt ≥1 original element. Method: `references/proprietary-data.md`.)

- **Product/usage data we can anonymize & cite:** {{PROPRIETARY_DATA}} — e.g. "aggregate send volumes, deliverability rates across N accounts, feature-adoption curves"
- **How to get at it (access path):** {{DATA_ACCESS}} — the actual command or connection, e.g. "read replica via `bin/rails dbconsole -e replica`", "`psql $DATABASE_REPLICA_URL`", "PostHog API key in 1Password", "GSC via * (property sc-domain:example.com)". Without this line the data angle gets skipped every run for want of five minutes' setup.
- **Off-limits — never publish:** {{DATA_OFF_LIMITS}} — e.g. "churn, exact MRR, per-customer volumes, anything identifying a named account". Standing instruction, not a per-run judgment call.
- **First-hand experience / things we've actually done:** {{FIRST_HAND}} — e.g. "ran X for 3 years, migrated N customers off Y, tested every tool in the category"
- **Original research we can run:** {{ORIGINAL_RESEARCH}} — e.g. "survey our user base, benchmark competitors hands-on, teardown analyses"
- **Internal experts we can attribute/quote:** {{INTERNAL_EXPERTS}}

## Author / E-E-A-T

(Verifiable authorship is a 2026 ranking + AI-citation signal. Who bylines the content and why they're credible.)

- **Default author:** {{AUTHOR_NAME}} — {{AUTHOR_TITLE}}
- **Credentials / why-credible:** {{AUTHOR_CREDENTIALS}}
- **Author bio URL / profile:** {{AUTHOR_URL}}

## Links to existing surfaces

- Domain: {{DOMAIN}}
- Homepage: {{HOMEPAGE_URL}}
- Pricing: {{PRICING_URL}}
- Existing blog/content: {{BLOG_URL}}
- Existing features list: {{FEATURES_URL}}

## Visual brand

> Editorial pieces reuse the site's existing layout components, which already carry styling, so an editorial run doesn't need this section. **Programmatic pages do** — they render their own hero, tables and cards. Auto-fill from `tailwind.config.*` or the design-token CSS; never interview the user about colors.

- **Accent color (primary):** {{ACCENT_PRIMARY}}
- **Accent color (secondary):** {{ACCENT_SECONDARY}}
- **Ink color:** {{INK_COLOR}}
- **Surface color:** {{SURFACE_COLOR}}
- **Hero font family:** {{FONT_HERO}}
- **Body font family:** {{FONT_BODY}}
- **Icon set:** {{ICON_SET}}
