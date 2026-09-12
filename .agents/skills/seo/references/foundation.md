<!-- merged from seo-content/references/foundation-setup.md + aeo/references/foundation.md (§2 truth file, §4 evidence mining, §5 attribute matrix) + seo-sprint/SKILL.md (Initialize steps 1, 4, 5) -->

# Foundation — bootstrap the `.seo/` state directory (Step 0)

Everything downstream inherits this step. A perfectly executed measurement program pointed at the wrong claims produces clean numbers about a question nobody asked.

`/seo` writes against one state directory: `.seo/`. This file is how it **creates that directory itself** on a bare repo — no other skill required. If a previous run (or an older skill) already built part of it, the existing files win: reuse what's there, fill only the gaps, and **never overwrite a foundation file.**

Run this once, at the very start of a run, before measurement and selection. Most of it is auto-detected; only the brand voice needs a short interview.

**Unattended runs never block here.** Every question to the user in this file has the same fallback: take the best-evidenced inference, mark it `inferred` in the file it lands in, write the question to `.seo/needs-you.md`, and carry on. A foundation built from inference and corrected next run beats a daily run that stalls waiting for an answer nobody is there to give. The one thing inference may never do is invent positioning (§2, rule 3) — if the positioning sentence cannot be drafted from the repo, write it as `unsettled` and file it.

**Detect the state first, then act.** Run `python3 <skill>/scripts/upgrade_state.py --root .` (dry run) before anything else. It reports one of four states and the plan for it; `--apply` executes the plan idempotently and writes `.seo/runs/<date>-upgrade.md`. Only after it says `current` does the rest of this file apply, and then only to files that are still missing.

## Contents

- [The decision: reuse or create](#the-decision-reuse-or-create)
- [Migrating from the old skills](#migrating-from-the-old-skills)
- [§1 — Detect the repo and write `config.json`](#1--detect-the-repo-and-write-configjson)
- [§2 — `brand.md` (the one interactive step)](#2--brandmd-the-one-interactive-step)
- [§3 — `truth.md` and `truth-checks.json` (the claim ledger)](#3--truthmd-and-truth-checksjson-the-claim-ledger)
- [§4 — Mine the evidence](#4--mine-the-evidence)
- [§5 — `attributes.md` (the attribute matrix)](#5--attributesmd-the-attribute-matrix)
- [§6 — `keyword-research.json` (baseline now, rest later)](#6--keyword-researchjson-baseline-now-rest-later)
- [§7 — `link-inventory.md` (generated from git or sitemap)](#7--link-inventorymd-generated-from-git-or-sitemap)
- [§8 — `content-ledger.md`, `roadmap.md`, `needs-you.md`, and the run directories](#8--content-ledgermd-roadmapmd-needs-youmd-and-the-run-directories)
- [§9 — Checkpoint, then proceed](#9--checkpoint-then-proceed)

---

## The decision: reuse or create

Check what exists, act per file. **Never overwrite an existing foundation file** — that is the coexistence guarantee, and it is what lets a repo that has been running the older skills for months lose nothing.

| File | If it exists | If it's missing |
|---|---|---|
| `.seo/config.json` | Reuse | **Create** (§1) |
| `.seo/brand.md` | Reuse | **Create** (§2) — the only step needing user input |
| `.seo/truth.md` | Reuse; re-derive stale rows | **Create** (§3) |
| `.seo/truth-checks.json` | Reuse | **Create** (§3) from `assets/truth-checks.example.json` |
| `.seo/attributes.md` | Reuse | **Create** (§5) from `assets/attributes.template.md` |
| `.seo/keyword-research.json` | Reuse (re-query stale slices as needed) | **Create** a baseline (§6); the rest accretes during selection |
| `.seo/link-inventory.md` | Reuse + append | **Create** from git or the sitemap (§7) |
| `.seo/content-ledger.md` | Reuse | **Create** from `assets/content-ledger-template.md` (§8) |
| `.seo/roadmap.md` | Reuse as the programmatic tracker | **Create** from `assets/roadmap-template.md` (§8) |
| `.seo/needs-you.md` | Reuse + append | **Create** empty (§8) |
| `.seo/radar.md` | Reuse + append | **Create** from `assets/radar-template.md` with the seeds from `config.radar.seeds` |
| `.seo/briefs/`, `.seo/evidence/`, `.seo/health/`, `.seo/gsc/`, `.seo/census/`, `.seo/runs/`, `.seo/aeo/` | Reuse | `mkdir -p` (§8) |
| `docs/seo-sprint.md`, `.aeo/`, flat config keys (legacy) | `upgrade_state.py --apply` (below) | Skip |

If only *some* files exist (a partial or aborted setup), fill the gaps — don't restart from scratch.

State up front which mode you're in: *"Found an existing `.seo/` foundation — reusing it."* or *"No foundation here yet — I'll set one up (one short brand interview), then get to work."*

### Hard prerequisites

Before anything else:

1. **Working directory is a git repo** — `git rev-parse --is-inside-work-tree`. If not, stop and say: "This skill writes persistent state into your repo. Initialize git first, or run from inside an existing repo."
2. **A stack is detectable** — at least one of `package.json`, `Gemfile`, `composer.json`, `requirements.txt`, `astro.config.*`, `next.config.*`, `nuxt.config.*`, `gatsby-config.*`, `_config.yml`, `config.toml`, `pyproject.toml`. If none, ask what stack this is before continuing; unattended, record `stack.kind: "unknown"`, take the markdown fallback in `output-formats.md`, and file the question in `.seo/needs-you.md`.
3. **Data-source check** — look for DataForSEO (market data), ping Search Console's `list_properties` (own-site truth), look for OpenSEO (crawl, rank history, GA4); the capability registry is `tools.md`, and check for a Bing Webmaster API key (`config.bing.api_key_env`). Fill `config.tools_detected` (the detection table in `setup.md`). Any one of them on its own still runs a useful program. With none, the skill works in manual-research mode (`research-recipes.md`, final section). Don't refuse to run; degrade, label it, continue.

   If OpenSEO is present, call `list_projects` and store the project id as `openseo.project_id`. `create_project` makes one if none exists. DFS endpoints take a target domain directly and need no project id.

---

## Migrating from the old skills

Repos arrive in four states. The upgrade script tells them apart so a run never has to guess, and never has to be told which case it is in.

| State | Looks like | What `upgrade_state.py --apply` does |
|---|---|---|
| **fresh** | No `.seo/`, no `.aeo/`, no `docs/seo-sprint.md` | Creates the v2 skeleton from `assets/` (config, truth, truth-checks, attributes, ledger, link inventory, needs-you, radar, the run directories including `competitors/`, `serp/`, `backlinks/`), `version: "2.2"`, `initialized: false`. Leaves `brand.md` and the seeds to §2's interview. |
| **legacy** | Any of: `.aeo/`; `docs/seo-sprint.md`; a `.seo/config.json` with flat keys (`domain`, `gsc_site_url`, `*_path`) and no `version`; `.seo/off-page-status.md`; `.seo/backlink-targets.json` | Moves `.aeo/*` into `.seo/aeo/`, promotes `truth.md` and `attributes.md` to the top level, merges the two brand files into one `.seo/brand.md` (sections the old AEO brand had that the content brand lacked are appended once, under a dated comment), moves the sprint roadmap to `.seo/roadmap.md` with a pointer stub, derives the nested v2 config keys from the flat ones without discarding them, fills every missing v2 file and directory from templates, sets `version`. |
| **partial** | `.seo/config.json` exists with a `version` older than the skill, or nested keys but missing v2.1 pieces (`radar.md`, `gsc/`, `census/`, `truth-checks.json`, `needs-you.md`) or v2.2 pieces (`competitors/`, `serp/`, `backlinks/`, the `repo`, `serp`, `distribute` config blocks and the weekly cadence keys) | Applies only the versioned steps between the detected version and the current one. Never touches a file that exists, and never overwrites a config value that is set. |
| **current** | `version` matches and every file is present | Nothing. Says so. |

Two rules the script obeys and you must too:

- **Nothing is overwritten.** Months of ledger rows, briefs, keyword cache, prompt sets and scoreboards are the asset. Migration moves and appends; it never regenerates.
- **Nothing is duplicated.** One brand file, one truth ledger, one config, one roadmap. When two old files cover the same thing, the richer one is kept and the other's unique sections are appended to it, once.

Run the dry run, read the plan, then `--apply`. If the plan lists a "declined to touch" item you disagree with, fix it by hand; do not re-run with a flag that forces it, because there is none.

When the script reports `legacy` or `partial` and applies its plan, the rest of this file still runs, but every section's "if it exists → reuse" branch will now be taken. The one thing migration cannot do is the brand interview and the radar seeds: if `.seo/brand.md` existed before, confirm its "who we are for" line still holds and add `config.radar.seeds` if empty (see "Radar seeds" at the end of this file).

## §1 — Detect the repo and write `config.json`

Work it out from the files. Ask only for what you genuinely cannot find.

### What kind of repo is this?

| Signal | Reading |
|---|---|
| Auth, database migrations, background jobs, billing code | The application |
| Only content, layouts, a static-generator config | The marketing site |
| Both present in one tree | Both, which is the best case for the truth file |

### The domain

In rough order of reliability: `CNAME`, deployment config (`vercel.json`, `netlify.toml`, `wrangler.toml`, `fly.toml`, Dockerfile labels), framework config (`next.config.*`, `astro.config.*`, `gatsby-config.*`, `nuxt.config.*`, `_config.yml`), `package.json` `homepage`, the sitemap or `robots.txt` contents, canonical tags in layouts, the README, `.env.example`. Confirm at the checkpoint rather than guessing between two candidates.

### The stack and the frontend convention

Read `stacks/detection.md` for the full signal table. Identify:

- **Framework family** — Rails+Inertia, Next.js (App Router vs Pages), Astro, Nuxt, Remix, SvelteKit, Hugo, Jekyll, plain HTML, or "unknown → markdown fallback."
- **Routing convention** — file-based (Next/Astro/Nuxt) or controller-based (Rails/Django/Laravel).
- **Component language** — TSX, JSX, `.astro`, `.svelte`, `.vue`, `.erb`, or plain HTML.
- **Existing marketing pages** — `git ls-files | grep -iE 'marketing|landing|pages/(home|about|pricing)'`. Note what exists; you'll link to it.

Confirm with the user if any signal is ambiguous. Unattended, take the reading with the most file evidence, record it as inferred, and file the confirmation (`stacks/detection.md`, Ambiguity resolution).

### The content surface and the content store

First decide *where published content lives* per `content-stores.md` (files vs headless CMS vs app DB vs WordPress vs builder), then, if it's files, the exact surface per `output-formats.md`. Common shapes: `content/`, `src/content/`, `pages/`, `app/`, `src/pages/`, `posts/`, `_posts/`, `blog/`, `docs/`. For a database or CMS-backed site there is no content surface in the repo — record the CMS and read the sitemap instead.

`content_dir` / `content_layout` / `output_url_prefix` come from finding one existing published post. **The real path always wins over the guess.**

### The technical surface files

`robots.txt`, `llms.txt`, `llms-full.txt`, `sitemap.xml` or its generator, `humans.txt`, any `_headers` or middleware that sets `X-Robots-Tag`. Record the paths — the technical lane diffs them every run.

### The logs

Server access logs, CDN logs, or the config that would produce them: `logs/`, `*.log`, nginx or Caddy config, a Cloudflare or Fastly setup, an analytics config. If none are in the repo, ask once where they can be read from, and record the answer or record `none`. A `none` here means AI-crawler evidence runs on Search Console alone, and any report must say so.

### The competitor set

Comparison pages, `/alternatives/` routes, "vs" pages, marketing copy, pricing-page footnotes, the README. **Propose the list, don't finalize it.** The user knows who they actually lose to, which is often not who they write comparison pages about.

For each competitor, find the sitemap (`/sitemap.xml`, or robots.txt's `Sitemap:` line; `scripts/sitemap.py` discovers it) and record it under `competitors[].sitemap_url`. That one field turns the competitor set into the weekly competitor delta panel (`measure.md` §6d). Leave it `null` when there is none and say so; the ranked-keyword half of the panel still runs.

### The product-change watch list

`repo.watch_paths`: the globs whose commits mean the product changed in a way public pages must follow. Start from the template and replace with this repo's real paths: the changelog or release notes, the routes file, the pricing view or plan config, feature flags, migrations. `scripts/repo_changes.py` reads them every run (`measure.md` §4b). A repo with no changelog should get one line in `needs-you.md` suggesting it, once.

### The brand regex

`site.brand_regex` stays `null` unless the name is a common word. `scripts/brand_split.py` builds the branded-query pattern from `site.name` and `site.aliases`, so put every spelling and misspelling seen in Search Console into `aliases`. A product named after a common word (a stone, a colour, a bird) needs a regex that excludes the generic sense; write it here.

### The search properties

- **GSC** — if Search Console is connected, call `list_properties` and match the domain to a property. Store the **exact** string under `gsc.site_url` (`sc-domain:` and `https://…/` forms are not interchangeable). No match means the site isn't verified in this Google account: store `null`, say it once, and carry on. Details and the subdomain case in `gsc.md` §0.
- **Bing** — optional. If a Bing Webmaster API key is available, record the env var name under `bing.api_key_env` and the site URL under `bing.site_url` (`gsc.md`, Bing Webmaster section). Absent is fine and common.

### Derived config values

- `authority.dr` — one authority read for context, not as a formula input (§6). Store `last_read` alongside it.
- `authority.kd_ceiling` — **derived from GSC, not from DR** (`research-recipes.md` → Difficulty buckets): pull your ranked queries, price the page-1 ones with `dataforseo_labs_google_keyword_overview`, and take the hardest bucket holding 2+ page-1 positions. A brand-new site with no rankings starts at `easy`. Always store which vendor's KD produced it — KD scales are vendor-specific, so a bucket derived from one vendor is meaningless against another. Re-derive every few weeks; it's free.
- `crawl_hubs` — the pages Google crawls most often, and therefore the best inbound-link sources for a new page (`gsc.md` §7a). Derive once by batch-inspecting the top ~10 pages by clicks and reading `last_crawled`; re-derive every few months. Leave `[]` if GSC isn't connected and fall back to the homepage plus the top-traffic page.
- `figure_style` — the result of the visual style recon in `visuals.md` §2 (existing chart component, design tokens, dark-mode mechanism, house stroke/radius conventions). Auto-detected from `tailwind.config.*` / token CSS / existing SVGs; **never ask the user about it.** Cached so later runs draw figures that match the site without re-deriving the palette. Re-derive if the repo's design system visibly changed.
- `priority_pages` — the handful of URLs whose accuracy and reachability matter most (homepage, pricing, the top converting page). The sampling and re-verification cadences key off this list.
- `budget` — `per_run_usd`, plus the cadences that keep expensive work off every run (`ai_panel_cadence_days`, `health_diff_cadence_days`, `claim_reverify_sample`).
- `site.sitemap_url` — the live sitemap or sitemap-index URL. `scripts/health_diff.py --sitemap` reads it every run (`measure.md` §3); `stack.sitemap_path` is the file that *generates* it, and the two are not interchangeable.
- `select.floor` — the rubric score below which `measure-only` wins (`select.md` §7). The template default of 9 is a starting point; raise it on a site where most days genuinely have nothing worth doing.

Write the result from `assets/config.template.json`. If a value can't be auto-detected and isn't essential yet, leave it `null` and fill it on first need.

---

## §2 — `brand.md` (the one interactive step)

This is the quality-critical file. **Read every signal first, draft the file, then ask only about the gaps.** Don't open with a blank questionnaire — an interview that starts from a blank page produces a brand workshop; an interview that starts from a draft produces corrections, which is what you want.

### Read these signals first

- `CLAUDE.md`, `README.md` — product name, one-liner, audience hints
- `package.json` / `Gemfile` — framework (already in config)
- the pricing page (any path) — plan structure, price points, free tier
- homepage / marketing hero (`git ls-files | grep -iE 'index|home|hero|marketing|landing'`) — existing positioning and voice
- **1-2 existing published posts** (`git ls-files | grep -iE 'blog|guides|content|articles'`) — read them closely; this is where the *real* voice lives. Note rhythm, perspective, formality, how they open.
- `tailwind.config.*` / token CSS — accent color and fonts

### The positioning sentence

Draft it from the repo and the site, then make a human confirm it:

> We are a **[product category]** for **[specific audience]** who need **[core capability]**.
> We win because **[specific differentiator]**.
> We are **not** for **[who you are explicitly not for]**.

Three rules for filling it:

1. **"Why do we win" beats "what do we do."** Generated answers are comparative by construction. "Best X for Y" always places you next to alternatives, and what earns the recommendation is fit for a specific situation, not general credibility. A company that can only describe itself at category level gets treated as one option among many, forever.
2. **The last blank is load-bearing.** "We serve everyone" is not caution, it is a decision to be unrecommendable. A product positioned as enterprise on one page and self-serve on another gets described as both, inconsistently, and an engine flattens the inconsistency into a recommendation for nobody. Push for a real answer. If the honest answer is "we genuinely serve both," that's fine — but state it as a deliberate range with a reason, not a blank.
3. **Do not invent positioning here.** If the positioning is unsettled, say so and stop. Teaching the web and the models to describe you as X, then deciding six months later you are Y, creates cleanup work harder than the original problem. This program amplifies a position that has already been chosen.

### Then ask the gaps — one batch of questions to the user (3-4 questions)

Unattended: draft every field from the repo signals above, mark the ones you could not evidence as `inferred — unconfirmed`, and file that list as a single `needs-you` item. Voice tags and forbidden words drafted from existing posts are usable; positioning that cannot be evidenced is written as `unsettled`, not guessed.

Only ask what you couldn't infer. The essentials to end up with:

- **Product one-liner** (≤20 words) — usually inferable; confirm it
- **Primary persona**, and **company size** where the product is B2B
- **3-7 competitors** by name — seeds content-gap research, comparison pages, and the battlecard
- **Brand voice tags** + **forbidden words** — the non-negotiable core. If existing content gives you the voice, propose tags and ask "does this sound right?" rather than asking cold.
- **Free tier?** and **anti-positioning** (what you intentionally don't do, including the adjacent category you keep getting confused with) — for honest comparison and listicle sections
- **Concrete differentiators** — the three things a customer would name if asked why they picked you
- **Forbidden claims** — anything legal, compliance, or accuracy says you must not say. These become hard constraints on every piece of on-page copy and every off-page brief.
- **Proprietary data & first-hand experience** — what original data / testing / lived experience the product can draw on, **how to actually reach it** (the read-replica command, the analytics API key, the dashboard), and **what's off-limits to publish** (churn, exact revenue, per-customer figures). This is the information-gain moat, and the access path decides whether it ever gets used — a listed-but-unreachable dataset gets skipped every run. Ask all three explicitly; see `proprietary-data.md`.
- **Default author + credentials** — who bylines the content and why they're credible. Engines reward attributable expertise; an unsigned page is weaker than a signed one.

Write the result to `.seo/brand.md` from `assets/brand-template.md`.

**Quality bar:** the voice section must be specific enough that a piece written from it is indistinguishable from the site's existing content. Vague tags ("professional, friendly") fail this — push for the specific, e.g. "blunt, technical, allergic to hype, writes like a founder DMing a peer."

---

## §3 — `truth.md` and `truth-checks.json` (the claim ledger)

This is the highest-value thing about running inside the repo, and it takes twenty minutes.

Answer engines and your own pages both make factual claims about the product. Some are wrong. You cannot tell which without a source of truth, and **marketing copy is not one, because marketing copy is what produced the wrong claim.**

Read the code and extract what is actually true:

| Claim class | Where it lives |
|---|---|
| Plans, prices, billing intervals, trial length, seat rules | Pricing config, plan constants, Stripe or billing product definitions, the pricing page's data source |
| Limits and quotas | Rate limiters, plan gates, feature flags, quota constants |
| Features that actually ship | Feature flags with their default state, route definitions, the changelog, release notes |
| Integrations | Dependency manifest, OAuth client configs, webhook handlers, API client wrappers, the integrations page data |
| Platforms and requirements | Build targets, browser-support config, minimum versions, mobile app manifests |
| Compliance and security posture | Security docs, SOC or compliance pages, auth configuration, data-retention settings |
| Company facts | Founded date, location, team size, funding, mailing address — from the About page and the README |

Record each as a checkable claim with its source path and the date you read it:

```
| Claim                                  | Value           | Source                        | Read       |
|----------------------------------------|-----------------|-------------------------------|------------|
| Starting price                         | $29/mo          | src/config/plans.ts:12        | 2026-08-26 |
| Free trial                             | 14 days         | src/config/plans.ts:31        | 2026-08-26 |
| Slack integration                      | yes             | app/integrations/slack/*      | 2026-08-26 |
| Salesforce integration                 | no              | absent from app/integrations/ | 2026-08-26 |
| SSO / SAML                             | Enterprise only | src/config/plans.ts:58        | 2026-08-26 |
```

**Include the negatives.** "We do not integrate with X" is the claim an engine is most likely to get wrong in the flattering direction, and a flattering wrong answer costs you a deal at the demo instead of at the search.

**Flag any claim where the code and the marketing site disagree.** That disagreement is already a finding, and it goes straight into the run record: if your own two surfaces contradict each other, an engine synthesizing both produces a muddle.

Write `.seo/truth.md` from `assets/truth.template.md`, including its HIGH-RISK section — the claims where being wrong is a regulatory, legal, or safety problem rather than an embarrassment. Set a refresh note: re-derive whenever pricing or the integration list changes.

### `truth-checks.json` — the mechanical half

`truth.md` is for humans and for the model. `truth-checks.json` is what `scripts/truth_check.py` can grep on every run without spending a token. Each rule names a claim, the paths to search, and the patterns that must (or must not) appear:

```json
[
  {
    "claim": "Free for families",
    "paths": ["web/app/frontend/pages/**/*.tsx", "web/public/llms.txt"],
    "must_not_match": ["families pay", "\\$\\d+/month"],
    "must_match": []
  }
]
```

Seed it from `assets/truth-checks.example.json` with the handful of claims that would be most damaging to get wrong — pricing, a regulatory posture, a capability the product does not have. Add a rule every time a `correct` action fixes a claim, so the same error can never come back silently.

---

## §4 — Mine the evidence

Attributes come from how buyers talk. Keyword and prompt data **confirm** an attribute you found elsewhere; they don't originate it.

Two axes decide which sources carry weight:

|  | New to the category | Established |
|---|---|---|
| **B2B** | First-party is nearly everything. Public data is thin. Fifty sales calls beat every review site. | First-party spine, plus review platforms, analyst coverage and comparison content. |
| **Consumer** | Public data already fills in. Communities, review platforms and category-level demand data give you patterns without first-party volume. | Public data is abundant enough to build most of the picture. First-party adds nuance. |

### What to extract from each source

**Sales calls and transcripts.** The objections that recur. The words prospects use to frame the problem before they have been exposed to your messaging. The competitors they name unprompted. One mention is noise; the same concern in a third of calls is an attribute.

**Support tickets and docs search logs.** What confuses people. Which features generate the most questions. Where the product and the expectation diverge. Docs search queries are underrated: literal buyer language, already in your possession, and nobody mines them.

**Review platforms.** Track the exact phrasing, not just the sentiment. "Easy to set up" and "intuitive interface" both mean good UX and they are not interchangeable, because the phrasing is what a model learns from. Review platforms are also disproportionately cited by answer engines, which means their language propagates directly into answers.

**Communities and forums.** Unsolicited, unperformed, and often the rawest signal available. Read how people describe their frustration to each other and what they recommend when nobody is selling.

**Competitor positioning.** How rivals frame the same space, which labels they own, and where the framing differs from yours.

**Keyword and prompt volume.** Use it last, as a cross-check on volume and phrasing. The calls are in `research-recipes.md`.

### Triangulate

Find themes inside each source first, then cross-reference. A theme that appears independently in call notes, reviews and community threads is high-confidence: three different kinds of evidence pointing at one thing.

Then weight by volume. For each triangulated theme, ask how many calls mention it, how many reviews reference it, and what the search or prompt volume looks like. A theme in 40% of negative reviews and one in three calls is priority 1 regardless of how the team feels about it. A theme in two reviews and zero calls is priority 3 regardless of how much engineering cares.

Before locking the list, ask the humans who own the surfaces: what does product marketing need answers to say, what does sales wish prospects knew before the first call, what does support wish customers understood. Those three questions surface attributes no data source will.

---

## §5 — `attributes.md` (the attribute matrix)

Group attributes into categories. Start from these and add whatever this business specifically needs:

| Category | The question it answers |
|---|---|
| Product category | What do buyers call a thing like yours? Capture every variant, including the one you dislike. |
| Vertical or segment | Who do you serve, in their own vocabulary? |
| Pain point | What problem makes someone start looking? |
| Use case | What do people actually do with it, which often differs from what you market? |
| Capability or feature | What specific thing do you want to be known to do? |
| Integration or compatibility | What you connect to, which is frequently the deciding factor. |
| Persona | Who decides, and how do they talk? |

Score each attribute on three axes and keep the ones that clear all three:

- **Weight (1-3)** — does this change a purchase decision?
- **Distance (1-3)** — how far is what engines say from what you want them to say? Unknown until you've measured, so estimate now and correct after the first AI panel. This is a loop, not a waterfall.
- **Reach (1-3)** — can you realistically influence it? An attribute owned by a category-defining incumbent with a decade of accumulated mentions is real, and it is not this quarter's work.

Priority 1 is high weight and high distance and workable reach. Priority 3 is real but will not cost you a deal.

**Keep accuracy claims out of the attribute matrix.** Pricing, integrations, compliance certifications and specs are not things you want to be *associated* with, they are things that must be *correct*. They live in `.seo/truth.md` and get tested mechanically. Mixing them in produces a scoreboard that averages "are we known for X" with "is our price right" — different problems, different fixes.

Write `.seo/attributes.md` from `assets/attributes.template.md`.

**Expect the list to be longer than the team assumed.** That's normal, and it's why the priority tiers exist: priority 1 gets measured properly, priority 3 indicatively.

---

## §6 — `keyword-research.json` (baseline now, rest later)

You don't need full keyword research up front — selection does live research every run and persists it here. Establish just the **baseline**:

- Pull an authority score with `backlinks_bulk_ranks` (`rank_scale: one_hundred`), batching your domain and every competitor into one call. Store it as *context*, not as a formula input: targeting runs off the difficulty bucket (`research-recipes.md`), which comes from GSC results rather than authority arithmetic. Estimate it from the SERP when DFS isn't connected at all.
- If no keyword tool is connected at all, write `{"baseline": {"domain_rating": null, "source": "none"}}` and proceed — selection runs in fallback mode and the user can refine later.
- **If GSC is connected, take a site snapshot too** — `get_performance_overview` (90 days). Store clicks, impressions, and average position under `gsc_baseline`. It costs one call, it tells you immediately whether this is an established site or a cold start (a cold start means GSC selection signals will be empty for a while — say so rather than reporting "no opportunities"), and later runs measure growth against it.

Seed shape:

```json
{
  "baseline": { "domain_rank": 18, "rank_scale": "one_hundred", "source": "dfs", "as_of": "<date>" },
  "difficulty": { "playable_bucket": "easy", "kd_source": "dfs", "derived_at": "<date>", "evidence": ["<kw> KD 10 → pos 13.5", "<kw> KD 8 → pos 6.2"] },
  "gsc_baseline": { "clicks_90d": 0, "impressions_90d": 0, "avg_position": null, "as_of": "<date>" },
  "clusters": {},
  "candidates": []
}
```

`clusters` and `candidates` fill in as runs accumulate research. No reduction in quality — the depth lands exactly where it's used.

If DataForSEO is available, the full first-pass sweep (authority baseline, competitor reverse-lookup, use-case sweep, comparison volume, striking distance) is Recipes A-E in `research-recipes.md`. It is not required to finish the foundation; run it when the first programmatic roadmap needs populating.

---

## §7 — `link-inventory.md` (generated from git or sitemap)

The inventory of existing link targets. Every new page picks ≥3 in-body links from here and registers itself here on ship.

- **File-based content** →

  ```
  git ls-files | grep -iE 'features?|tools?|pricing|about|blog|guides|content|articles|index|home'
  ```

  Capture each page's URL plus a title/anchor candidate (read the file's H1 or frontmatter title).
- **DB / CMS content** → source from the **sitemap** (`/sitemap.xml`) or the CMS API instead (see `content-stores.md`, Operation 1). Same template, different source.

Sort the results into the sections of `assets/link-inventory-template.md`: homepage/core marketing, features, tools, existing content, and the empty per-pattern tables the programmatic lane will fill. Every run appends to it.

---

## §8 — `content-ledger.md`, `roadmap.md`, `needs-you.md`, and the run directories

**`.seo/content-ledger.md`** — from `assets/content-ledger-template.md`. The memory of the engine: the `Shipped` table is the dedup record, `Performance` is the scoreboard, `Candidate backlog` is the scored shortlist so each run starts warm. If existing content shipped before the ledger existed, backfill it — a GSC page with no ledger row is a dedup hazard (`gsc.md` §2b).

**`.seo/roadmap.md`** — from `assets/roadmap-template.md`, the programmatic-page tracker. Fill in:

- **Site facts** (domain, authority, stack, brand colors, fonts) from §1-§2
- **Reference data** — the paths to the controllers and page files the skill will edit
- **Keyword Research Appendix** — the curated output from §6, grouped by pattern
- **Phase Status Tracker**, auto-populated from research:
  - Phase 0: technical foundation fixes (whatever the health check found)
  - Phase 1+: one row per page candidate in priority order
  - Group by pattern; within a pattern, order by traffic potential desc, then volume desc, then difficulty asc
  - Striking-distance boosts go near the front — they're the fastest wins on an existing site
  - Off-page checklist (directories + outreach targets) gets one tail-end phase per category

If `config.paths.roadmap` names a different location, write it there instead.

**`.seo/needs-you.md`** — create it empty, with its heading. It is the queue of decisions, logins, and reviews only the human can do; every run appends to it and clears what got done.

**Directories** — `mkdir -p .seo/briefs .seo/evidence .seo/health .seo/runs .seo/aeo`. Per-piece claim ledgers, before/after evidence files for `correct` / `repair` / `consolidate` / `verify-product` actions (`register.md` §4), site-health fingerprints, run records, and the answer-engine working set respectively.

---

## §9 — Checkpoint, then proceed

Stop once, here. Ask the user (a structured question if the host has one, plain text otherwise) and wait. **Unattended, do not stop:** print the same block into the run record, file it as one `needs-you` item, and continue into measurement — the foundation is reviewable at any time and nothing downstream is destructive.

Present, compactly:

- The positioning sentence, including the "not for" clause
- The priority-1 attributes, each with the evidence that put it there
- The competitor set
- **Anything in the truth file where the code and the marketing site disagree** — this is usually the most actionable thing in the whole step
- **The connections block from `setup.md`**: what is connected, and the top three missing connections with one line each on what they unlock. This is the one moment a new user can act on it before it matters: a Search Console connection made now changes what the first measurement can see.

Ask what to change, and whether to connect anything now. If the user connects something at this stop, re-run the detection for that one capability, update `tools_detected`, and continue; do not restart the foundation. The user's instinct about positioning beats your inference from the repo, and the "not for" clause is the one they'll most want to soften. Let them, but note it: a softened clause usually shows up two runs later as a muddled mention rate across two audiences.

**Then continue into the run in the same session.** You've created a foundation, not a plan — there's nothing here that needs a second approval stop. Note in the hand-off that the foundation was bootstrapped and the user can edit `.seo/brand.md` and `.seo/truth.md` anytime.

The full connections report from `setup.md` goes in the final message on a first run (the checkpoint showed the top three; the message carries all of them), and again whenever `tools_detected` differs from the last run. Unattended first runs, which never reach the checkpoint, get it there only.

Report the paths back once:

```
Foundation ready

  Config:          .seo/config.json
  Brand:           .seo/brand.md
  Truth ledger:    .seo/truth.md  (+ .seo/truth-checks.json)
  Attributes:      .seo/attributes.md
  Keyword cache:   .seo/keyword-research.json
  Link inventory:  .seo/link-inventory.md
  Content ledger:  .seo/content-ledger.md
  Roadmap:         .seo/roadmap.md
  Needs you:       .seo/needs-you.md
```


## Radar seeds

Fill `config.radar.seeds` and `config.radar.communities` during the brand interview, right after "who we are for." Seeds are five to fifteen phrases the audience would type or say, not product names: the jobs, fears and moments the product exists for. Communities are the subreddits, forums and groups where that audience already talks. Create `.seo/radar.md` from `assets/radar-template.md` with the seeds listed as `active`. `demand-radar.md` explains what these feed. Ask once; the radar refines the list from what actually produces signals.
