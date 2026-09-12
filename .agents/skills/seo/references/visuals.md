# Visuals — figures the repo would have drawn itself

Charts, diagrams, and small illustrations are the one asset class this engine can genuinely *produce* rather than stub out, because an SVG is markup and this is a code tool. That changes the old default. "Leave a placeholder and let the user supply the image" is still right for photography and hero/OG art — it is **wrong** for a bar chart of your own data, a flow diagram of a process you just explained in eight paragraphs, or a labelled sketch of a thing that's hard to describe in words. Those get authored, inline, in the piece.

**Why it's worth the effort.** The figure is the part that gets screenshotted into Slack, embedded in someone else's post, and lifted into a slide deck — which is how a piece earns referring domains without asking for them. It's also the part that survives skimming: a reader who bounces off 2,000 words will still read one chart. And for a piece carrying original data (`proprietary-data.md`), the chart is where the information gain becomes *visible* instead of buried mid-paragraph.

**The rule in one line:** when a piece contains something with shape — a comparison, a trend, a distribution, a process, a structure — draw it as inline SVG that matches the repo's own design language. When it doesn't, don't decorate.

---

## §1 — Does this piece earn a visual?

A figure earns its place when it does something prose can't. Run the test honestly; a decorative chart is worse than no chart, because it costs load, review time, and reader trust.

**Yes — draw it:**

| The content has… | Draw |
|---|---|
| Numbers being compared across categories | Horizontal bar chart (labels stay readable, no rotated text) |
| A number changing over time | Line or column chart, with the axis starting at zero |
| A distribution ("most teams cluster at…") | Histogram or a simple dot/strip plot — this is where averages lie and the picture doesn't |
| Parts of a whole, ≤4 parts | Stacked bar. **Not a pie chart** |
| A multi-step process or pipeline | Flow diagram, left-to-right, boxes and arrows |
| A structure, hierarchy, or relationship | Node diagram or a nested-box sketch |
| A before/after or with/without | Side-by-side panels sharing one scale |
| A concept that's hard to describe in words | A small labelled illustration — the "what this actually looks like" sketch |
| A worked example with several moving values | An annotated callout figure, values labelled in place |

**No — write the sentence instead:**

- Three numbers. A sentence carries three numbers better than a chart does.
- One number. That's a stat callout (styled text), not a figure.
- Anything you'd have to invent data for. **Never draw a chart of illustrative numbers.** A plausible-looking trend line with no data behind it is fabrication with extra steps, and it's the fastest of all the fabrication modes to get caught — someone will ask for the underlying figures.
- Pure decoration: abstract shapes, a "hero graphic," an icon row that says nothing. Skip it.
- Anything the repo already has a component for that you'd be duplicating.

**Density:** roughly one figure per major finding, and no more than one per ~400-500 words. A data study with no figures fails its type bar (`content-types.md`). A definition page with three is trying too hard.

---

## §2 — Style recon: match the repo (the step everyone skips)

**The figure must look like the site drew it, not like a chart library's default theme landed on the page.** Spend five minutes here before drawing anything. This is the same principle as reusing the existing layout component instead of inventing a template.

Look for, in order:

1. **An existing chart or figure component** — `git ls-files | grep -iE 'chart|graph|figure|diagram|viz|sparkline'`, plus `package.json` for `recharts`, `chart.js`, `d3`, `visx`, `nivo`, `apexcharts`. **If the repo already renders charts, use that component.** Matching the site beats hand-rolling, and adding a second charting approach to a codebase is a real cost. Never add a charting dependency for one blog figure.
2. **Existing SVGs in the repo** — `git ls-files '*.svg' | head -20`. Read two. They tell you the house stroke width, corner radius, whether icons are stroked or filled, and whether they hardcode colors or use `currentColor`.
3. **Design tokens** — `tailwind.config.*`, a `:root` block of CSS custom properties, a `tokens.*`/`theme.*` file. Harvest: accent + secondary colors, the neutral ramp, border radius, border color, font stack, and the spacing scale.
4. **Dark mode** — `grep -rn "dark:" --include="*.tsx" --include="*.html" | head`, or a `prefers-color-scheme` / `[data-theme]` block. **If the site has dark mode, the figure must work in both.** A chart with hardcoded `#1a1a1a` text vanishes on a dark background, and that's the single most common way a hand-authored figure ships broken.
5. **One existing published post** with a figure in it, if there is one. Its markup is a better spec than everything above.

Write what you found into one line — *"Tailwind, tokens `--accent`/`--muted`, dark mode via `dark:` classes, icons are 1.5px stroked `currentColor`, no chart lib"* — so the drawing step has a palette instead of a guess. **Persist it to `.seo/config.json` as `figure_style`** (`foundation.md` §1) so later runs start with the palette instead of re-deriving it; re-run the recon only if the repo's design system visibly changed.

---

## §3 — The build: SVG-first

**Inline SVG, hand-authored.** Not a raster export, not a chart library, not an AI-generated image. Inline is the format because it's the only one that inherits the page's CSS — which is the entire mechanism by which the figure matches the site and survives a theme switch.

**Non-negotiables:**

- **Inline in the page, not `<img src="chart.svg">`.** An SVG loaded through `<img>` is sandboxed from page CSS: `currentColor` resolves to black, your CSS variables resolve to nothing, and dark mode breaks. Inline or it doesn't theme.
- **Color comes from the page, never from a hex you invented.** Use `currentColor` for axes, gridlines, labels, and strokes. Use the repo's token for series color — `fill="var(--accent, #2563eb)"`, or in a Tailwind repo put utility classes straight on the SVG elements (`class="fill-slate-900 dark:fill-slate-100"`), which is the most repo-native option available and gets dark mode for free.
- **Don't set `font-family`.** Inline SVG `<text>` inherits the page's font. Setting it is how figures end up in Helvetica on a site that uses something else. Set `font-size` in relative terms and let the rest cascade.
- **Responsive:** `viewBox="0 0 640 360"`, `width="100%"`, `height="auto"`, no fixed pixel `width`/`height` attributes. It then scales to any column width and any screen density with no srcset, no build step, and no layout shift.
- **Text stays text.** Real `<text>` elements — never converted to outlines, never baked into a path. Selectable, searchable, translatable, and readable by anything parsing the page.
- **Namespace your ids.** Prefix every `id` (gradients, clipPaths, markers, `aria-labelledby` targets) with the piece's slug. Two figures on one page with a shared `id="grad"` is a genuine, silently-wrong bug — the second figure quietly renders with the first one's fill.
- **No JavaScript, no `<foreignObject>`, no external font or image references.** The figure is static markup that works in an RSS reader, an email client, and a CMS preview pane.
- **Keep it hand-sized.** A hand-authored chart is a few dozen elements and a couple of KB. If you're producing 200KB of path data, you exported something instead of drawing it.

**Chart honesty** (these are correctness rules, not taste):

- Bar and column charts **start at zero.** Truncating the axis to make a difference look bigger is the oldest lie in the format.
- Label the axes with **units**, and put **n** and the **as-of date** in the figure or its caption.
- One y-axis. Dual-axis charts manufacture correlations that aren't there.
- No 3D, no drop shadows on data marks, no gradient fills that encode nothing. Every visual property should carry information.
- Sort bars by value unless the categories have a natural order (time, size buckets). An alphabetical bar chart wastes the strongest signal the format has.
- If a chart needs a paragraph to explain how to read it, the chart is wrong.

---

## §4 — Accessibility and extraction

Both audiences that matter — screen readers and answer engines — read markup, not pixels. Same fix serves both.

- **Meaningful figures get a name and a description:** `role="img"` with `<title id="…-t">` and `<desc id="…-d">` referenced by `aria-labelledby="…-t …-d"`. The title is the finding ("Retention-window changes by team size"), not the format ("Bar chart").
- **Decorative figures get `aria-hidden="true"` and `focusable="false"`** and no title. If it says nothing, say nothing about it.
- **Every number in a figure also appears as text nearby** — in the caption, the surrounding paragraph, or a paired table. This is the same rule as `proprietary-data.md` §5 and it's the one with real SEO consequence: a stat that exists only inside a graphic is invisible to every extractor, and the citation you were trying to earn goes to whoever published the number as text.
- **Caption every figure**, and make the caption the *finding* rather than a restatement of the axis labels. "Teams over 50 change the default 4× more often (n=3,400, March 2026)" beats "Chart: retention settings by team size."
- **Put attribution inside the figure** — a small `[Brand] · [date]` or the URL in the corner. Figures travel without their page; the ones that carry their source earn the link when they land somewhere else.

---

## §5 — Where the figure goes, per content store

| Store | How to ship it |
|---|---|
| **Markdown / MDX in the repo** | Inline the `<svg>` directly in the body (MDX and most markdown renderers pass raw HTML through). If the site's markdown pipeline strips HTML, extract it into a small component next to the existing layout components and use that. |
| **Astro / Next / Nuxt / SvelteKit content** | A component in the repo's component dir, imported by the piece — matches how the site already handles reusable blocks. |
| **A repo that already has a chart component** | Use it. Pass the data. Don't hand-author SVG next to a perfectly good `<BarChart>`. |
| **WordPress / headless CMS** | Sanitizers frequently strip `<svg>` from post bodies. Test with one small figure before building five. If it's stripped: upload the SVG as a media asset and reference it (accepting the loss of theming), or use the store's native table/embed block. Note the constraint in the hand-off. |
| **No detectable pipeline (markdown fallback)** | Inline the SVG in the markdown file and say in the hand-off that it needs raw-HTML passthrough enabled. |

Whatever the store: the figure ships **in the same commit/draft as the piece**, never as a follow-up. A published piece with a "figure TBD" comment in it is a piece that ships without figures.

**Raster is still a hand-off.** Hero images, OG cards, photography, and screenshots of things that don't exist yet are not this rule — specify them (1200×630 for OG) and leave a marked placeholder, or hand to `og-image`/`feature-image` if installed. The line is simple: **if it's drawable as markup, draw it; if it needs a camera or a rendering pipeline, hand it off.**

---

## §6 — Anti-patterns

- **Don't chart three numbers.** Write the sentence.
- **Don't invent data to have a figure.** No illustrative trend lines, no "representative" distributions. Same sin as a fabricated statistic, and more conspicuous.
- **Don't add a charting library** for a blog figure. If the repo has one, use it; if it doesn't, hand-author the SVG.
- **Don't hardcode colors.** A hex that isn't in the repo's palette is a figure that looks like it came from somewhere else — and breaks the moment the theme changes.
- **Don't ship a figure you haven't looked at, in both themes.** Render the page and *look*. Overlapping labels, clipped text at the viewBox edge, and invisible-on-dark axes are all silent failures that only the eye catches.
- **Don't put load-bearing numbers only inside the graphic.** They must exist as text too.
- **Don't decorate.** An icon row, an abstract header graphic, and a stock-looking illustration add weight and say nothing. The bar is "does this show something the prose can't," and most decoration fails it.
- **Don't invent a figure style** when the repo already has one. Same rule as never inventing a layout component.

---

## §7 — Checklist

- [ ] Ran the §1 test — each figure shows something the prose can't, and nothing decorative shipped
- [ ] Style recon done: reused the repo's chart component if one exists, otherwise harvested tokens, palette, radius, stroke, and font stack
- [ ] Inline SVG with `viewBox`, `width="100%"`, no fixed pixel dimensions, no `font-family`
- [ ] Color via `currentColor` / repo tokens / repo utility classes — zero invented hex values
- [ ] Ids namespaced by slug; no collisions between figures on the page
- [ ] Axes start at zero; units labelled; n + as-of date present; no dual axis
- [ ] `role="img"` + `<title>`/`<desc>` on meaningful figures; `aria-hidden` on decorative ones
- [ ] Every figure number also present as text; caption states the finding; attribution inside the figure
- [ ] Rendered and **looked at** in light and dark, at mobile width and full width
- [ ] Shipped in the same commit/draft as the piece
