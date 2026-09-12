# Polish Pass — strip the AI tells without flattening the voice

The last thing you do before verification: read the finished draft as a human would and remove the fingerprints that make prose read like a model wrote it — *without* sanding the personality out of it. The failure mode here is over-correction: turning a piece with a spark into safe, voiceless paste. You're removing the robot, not the human.

(This is bundled from the standalone `polish` skill, scoped to a single editorial piece. If that skill is installed and the run also touched UI strings, emails, or a broader diff, run it afterward for a wider sweep — see the note at the bottom.)

Two jobs: **strip the tells** (below) and **match the voice** (`.seo/brand.md`). Then the skeptical pass decides what actually gets applied.

---

## The tells — a smell list, not a kill list

Each item *often* signals AI authorship, but a deliberate, on-brand line may use one and be perfect. Read for a rhythm a human would never produce, not for keyword matches. When `.seo/brand.md` and this list disagree, the brand doc wins.

### Sentence construction (the loudest tells)
- **"It's not just X — it's Y."** Plus the whole family: "not only… but also," "more than just a," "X isn't just Y, it's Z." The antithesis-reveal is the single most reliable cadence tell.
- **Rule of three as a reflex** — "fast, simple, and powerful," "organize, find, and remember." Real writing varies its rhythm; AI defaults to the tricolon.
- **"Whether you're a X or a Y…"** — the everyone-is-included opener.
- **Throat-clearing openers** — "In today's fast-paced world," "In an age of," "When it comes to," "Let's dive in," "Let's take a look."
- **"That's where [Product] comes in."** / **"From X to Y, we've got you covered."**
- **Restate-the-obvious closers** — "In summary," "Ultimately," "At the end of the day," a final paragraph that re-summarizes what was just said.
- **Suspiciously perfect parallelism** — every list item the same length and shape; every bullet a bolded lead-in + colon.
- **A heading phrased as a question, answered immediately** in a formulaic beat.

### Diction (the model word-hoard)
Flag when used as filler (some have legitimate literal uses):
> seamless / seamlessly · robust · leverage (verb) · elevate · unlock · supercharge · effortless · game-changing · revolutionary · cutting-edge · world-class · powerful · delve · harness · foster · streamline · empower · tailored · bespoke · holistic · synergy · "treasure trove" · "a plethora of" · "a myriad of" · boasts · navigate (figurative)

Plus conversational filler: cheerful exclamation openers ("Great!", "Welcome aboard!"), **"simply" / "just"** as minimizers, "It's worth noting that," "Keep in mind that."

### Hedging
- "It depends," "there are many factors," "results may vary." Commit to a take — a piece with no point of view doesn't outrank anything.

### Punctuation & typography
- Decorative emoji leading headings or bullets (🎉 🚀 ✨ ✅).
- Title Case On Every Heading, or sentence-case and Title Case mixed at random across siblings.
- "Smart" curly quotes in only the new span while the rest of the site uses straight quotes (or vice versa) — match the site.

### Bracketed-letter quote alterations

"[r]esponding to [n]on-[s]ubstantive [o]ffice [a]ctions" is the legal-brief convention for marking a changed capital inside a quotation. It is correct in a court filing and wrong on every web page. Quote plainly with the capitalization that reads naturally in the sentence, or paraphrase without quotation marks. Grep for `\[[A-Za-z]\][a-z]` before returning; zero is the only passing count. (Caught by the user on a shipped page, 2026-09-05, after ten instances passed four critics.)

### The em-dash, specifically
The most over-corrected mark in both directions. It's legitimate and useful — the tell is **density and mechanical rhythm**, not the character itself. A model reaches for `—` as an all-purpose connector two or three times a paragraph, often in an appositive ("Acme — the vault that reads your docs — files them"). Decision tree when you find one:
- Two clauses that could stand alone, hard break? → **period.**
- A list or soft aside? → **comma or parentheses.**
- A setup landing on a payoff? → **colon.**
- A genuine sharp pivot, used *once*, where the dash is the best mark for the beat? → **keep it.** That's the human use.

The goal isn't zero em-dashes. It's a count low enough that no reader clocks a pattern.

### Don't narrate the interface
If the piece references the product UI, a label should name *what a thing is or does*, not where it lives: cut "click the gear icon in the top-right to edit billing" down to "edit billing." Directional scaffolding ("via the… / from the… / found under…") belongs only in genuinely instructional how-to steps, not in passing prose.

---

## The voice pass

Separately from the tells, hold each passage against `.seo/brand.md`:
- **Forbidden words** → replace, every time. Non-negotiable.
- **Wrong register** → a corporate, hedgy, or hype-y line in a "direct, calm, founder-led" product gets rewritten to match; a flat line in a punchy product gets sharpened.
- **Wrong person** → "users can" when the product says "you"; "we" when the product never uses it. Match the perspective consistently.
- **Wrong vocabulary** → if the product calls it a "Vault," don't call it a "document repository." Match the site's existing terms.

State which reference governed the pass (almost always `.seo/brand.md`) so the calls are auditable.

---

## The skeptical pass — before you apply

This is the most important step. You're about to rewrite lines, and your rewrites have a real chance of being *worse* — blander, longer, or subtly off-meaning. Before applying each one, bet $100:

1. **Is my version actually better, or just different?** "Different and equally fine" → leave the original. Don't churn.
2. **Did I flatten the voice?** If the original had a spark and my rewrite is safe and dead, I lost. Revert toward the original.
3. **Did I change the meaning?** Never edit a number, a claim, a stat, or a promise to read nicer — copy often encodes a real fact ("up to 25 documents" is billing, not vibe).
4. **Am I steamrolling a deliberate choice?** A single on-brand em-dash, a fragment used for punch, an intentional repeat — read it in context before "correcting" it.
5. **Would the founder recognize their product in this line?** If it now sounds like every other SaaS, undo it.

Apply only what survives all five. A polish that changes four lines and makes them sing beats one that touches forty and averages them out. **If the draft is already clean, say so and change nothing** — manufacturing edits to look busy is just the AI-slop instinct wearing a different hat.

---

## Don't *perform* humanness

There's popular advice to "humanize" AI content by injecting sentence fragments, rhetorical questions, typos, or extra em-dashes to beat AI detectors. **Don't.** Two reasons:

1. **It's a new layer of tells.** Mechanically-added imperfection reads as mechanically-added — and em-dash padding is the *single most common* tell this pass exists to strip. You'd be re-introducing the fingerprint.
2. **The premise is wrong.** Google rewards helpful content regardless of how it's produced and does not rank on third-party "AI-detector" scores (which are unreliable anyway). Optimizing for detectors is wasted effort.

Real voice comes from the *substance* layer — specificity, named examples, shown experience (`writing.md`'s "Show the experience"), a genuine point of view — not from cosmetic roughening. Remove the robot; don't costume it.

---

## When to reach for the standalone `polish` skill instead

This bundled pass covers the *article prose*. The full `polish` skill (if installed) is diff-scoped and goes wider — it classifies and fixes user-facing strings across an entire PR (JSX/ERB labels, error/toast/email copy, i18n values), updates the tests that assert those strings, and handles duplicated-string drift. If this run touched more than the article (e.g. you edited UI components or added flash messages while wiring in links), run `polish` afterward for that broader sweep. For a normal "write one piece" run, this pass is enough.
