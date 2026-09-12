# Step 5. Register

<!-- new in v2; ledger row format from seo-content's content-ledger-template, run record from the audit's evidence files -->

Registration is how a stateless daily run remembers. The old skills registered wins: a shipped row in a ledger. They never registered what was not done, what could not be checked, or what needed a human, so that debt vanished at the end of every session. Every run of v2, including measure-only, writes three things.

## Contents

1. The ledger row
2. The run record
2b. Hand-off
3. The needs-you queue
4. Evidence files
5. What never gets registered

## 1. The ledger row

`.seo/content-ledger.md` keeps the shipped log, the Performance table, the candidate backlog, and the coverage map, in the shape of `assets/content-ledger-template.md`. Append a row for any action that changed a public page:

```
| <date> | <action> | <slug or URL> | <type or pattern> | <lane> | <one-line what changed> | <commit or "uncommitted"> |
```

`create-*` rows also seed a Performance row as `unmeasured` and register link targets and anchors in `link-inventory.md`. A `distribute` row records what was queued, never what was published: the posting skill's draft ids or the path of the social brief, the single URL submitted to IndexNow with its receipt code, and the directory or thread brief filed in `needs-you.md`. `refresh`, `correct`, `consolidate` and `repair` rows carry the pre-state (position, impressions, the wrong text) so the Performance table can show whether the action moved anything at the 21-day read.

Measure-only runs write no ledger row.

**Verdicts are not hand-written.** `scripts/outcomes.py` (measure.md §7b) reads this ledger and the saved Search Console pulls and writes `.seo/outcomes.json` and `.seo/priors.json`. Never edit those two files by hand, and never fill the Performance table's State column with a verdict the script did not produce; copy the script's verdict in when a row is read. The ledger row's job is to carry the date, the action and the target accurately enough for the script to find the page later. A row with no URL or path cannot be scored, so `repair` and `correct` rows name the page they touched.

**Cold veins.** When the census or the 90-day read shows a cohort under 10 clicks total, mark its type, pattern or cluster `cold` in the coverage map with the date and the numbers. A later refresh that moves re-opens it; write that too.

**Cohorts.** When a batch ships (a programmatic phase, a set of refreshes), freeze it as a cohort in the ledger's Performance section: the exact URL list and the ship date. Every later read reports against that fixed denominator. Adding pages to a cohort after the fact, or dropping the ones that failed, turns a measurement into a story.

## 2. The run record

Write `.seo/runs/<YYYY-MM-DD>-<HHMM>.md` from `assets/run-record.template.md`. The time is the run id; a dozen runs a day get a dozen records, and "the previous run" always means the newest file in the directory. Sections, all required:

- **Measured.** The panel summary block from `measure.md` §9, verbatim.
- **Candidates.** The top-ten table with scores, and which override tier decided the run if one did.
- **Chose.** Action, target, two-sentence reason. In unattended mode, say it was unattended.
- **Did.** What changed, file paths, the diff summary, the gate results (passed, failed, unchecked).
- **Not done.** Every part of the chosen action left incomplete, every gate left unchecked, every candidate deferred with a one-line reason. This is the section the next run reads first.
- **Needs you.** Items added to `needs-you.md` this run, by id.
- **Spend.** Paid calls made, count and cost shape, and what was skipped for budget.
- **Portfolio.** On census runs only: the verdict counts and invisible share against the previous month, what was pruned or merged, which veins are cold, and whether `create_gate` is set.

The "Not done" section exists because a fix that is 80% done and undocumented is worse than one not started: the next run sees a page that looks handled and moves on. On the audit that motivated v2, every work package wrote its own not-done list, and that is the only reason the follow-up packages knew where to start.

### Starting the next run: the fresh-main guard

In the worktree loop every run starts on a branch cut from main. Before measuring, fetch:

```
git fetch origin main
git diff --name-only HEAD origin/main -- .seo/runs
```

If origin/main has a run record this worktree does not, the previous run merged after this worktree was cut. Stop and say so; the fix is a new worktree (or a rebase), not a run that cannot see its predecessor's cooldowns and ledger rows. If the fetch fails (offline), continue and note it.

### Starting the next run: the dirty-tree rule

Before measuring, read the newest run record and `git status`. If the tree has uncommitted changes:

- and the newest record's "Not done" names them, this run may continue that work as its action if it still scores highest, or leave it and say so;
- and nothing explains them, note the files in this run's record and do not touch them. They belong to someone.

Never revert, stash, or check out over another run's changes. In `commit` or `pr` mode the previous run committed its own work, so the tree is clean at the start of every run.

## 2b. Hand-off

How a run ends is `config.git.mode`:

| Mode | What the run does at the end |
|---|---|
| `none` | Shows the diff (code plus `.seo/` changes) and stops. The default. |
| `commit` | Commits everything the run touched, code and `.seo/` together, subject `seo: <action> <target> (<run id>)`, body the run record. Never pushes. |
| `pr` | As `commit`, then pushes the branch and opens a pull request against main (`gh pr create --base main`) with the same title and the run record as the body. Never merges. |

In every mode the commit or diff includes the `.seo/` changes. A code change without its ledger row and run record is the one thing the next run cannot recover from, because it will re-derive the same candidate from unchanged live data and do it again.

On the first run of each month, or when `.seo/health` holds more than 60 files, run `python3 <skill>/scripts/compact_state.py --apply` before the hand-off so the thinning rides in the same PR.

## 3. The needs-you queue

`.seo/needs-you.md` from `assets/needs-you-template.md`. One row per item:

```
| id | opened | blocks | question | answer | closed |
```

`id` is `NY-<n>`, monotonically increasing. `blocks` names the candidate or lane waiting on it. `question` is exactly what the human must decide or provide, phrased so a one-line answer suffices. The human writes in `answer`; the next run reads any row with an answer and no `closed`, acts on it, and stamps `closed`.

At the end of every run, whatever the mode, every open row is restated in full in the final message, in the format of §6. Never print an id on its own, a count ("4 open"), or a pointer to this file: the human reads the message, not the queue. `/seo needs-you` prints the same block and does nothing else.

Things that belong here: a pricing or positioning decision; a clinical, legal or financial reviewer's sign-off; a console setting or verification that needs a login; a key or budget; a competitor claim the skill cannot verify; a page removal. Things that do not: anything the skill can find out by reading the repo or the web.

## 4. Evidence files

A `correct`, `repair`, `consolidate` or `verify-product` action writes `.seo/evidence/<date>-<slug>.json` with what was checked and the before/after: the URL, the HTTP evidence, the claim and its source, the test that now covers it.

**The change record for non-file stores.** When the copy lives in a database or CMS, the content change does not ride in the PR as a diff, so every `correct`, `refresh`, `consolidate`, `prune` and link edit on a row also writes `.seo/evidence/<date>-<slug>.patch.md`: table and row ids, the field, the before text, the after text, the source of the truth, the sibling-search query and its hits, and the exact apply step (migration filename, revision id, or paste instructions). The ledger row carries the record path and the migration or revision id, and `applied: pending deploy` until the next run's rendered truth check sees the change live. `stacks/app-db.md` §3 is the write contract. This is what lets a future run, or a human, confirm the fix held without redoing the investigation. Editorial pieces already have their brief; do not duplicate it.

## 5. What never gets registered

- A merge or a deploy. The skill commits or opens a PR only when `config.git.mode` says so, and never merges.
- A 200 or 202 from IndexNow, or a sitemap submission, as "indexed."
- A gate as passed when it was not run.
- An answer-engine rate without its sample size.
- Anything containing a private identifier from the product's data.

## 6. The final message

The run record is written for the next run. The final message is written for the human, and it has to stand alone: the reader has not opened `.seo/`, will not open the run record, and does not know what `NY-3`, `create_gate`, `tier 2`, or a candidate table mean. Everything the message mentions is stated in full where it is mentioned. Internal ids, file paths, and "see X" are allowed only as an aside after the plain statement, never instead of it.

Five parts, in this order, plain headings or bold leads, no candidate table, no scores:

1. **What this run did.** One paragraph: the action, the target in the reader's terms (page titles or URLs, not slugs or file paths), what was wrong or missing, what it says or does now, and the one-sentence reason it beat everything else. A measure-only run says "nothing beat the bar" and gives the reason.
2. **Verified.** Each gate as a short line: what was checked and the result. Anything not checked is listed as not checked with the reason, in the same list. Never "all gates passed."
3. **Left for the next run.** The "Not done" items that matter to the reader, each one sentence, each saying why it was not done now.
4. **Decisions waiting on you.** Every open row of `needs-you.md`, whether opened this run or earlier. Each item is a complete question the reader can answer from the message alone:
   - one line naming what is stuck without it, in product terms ("the answer-engine remeasure", not "the aeo lane");
   - the question in full, with the concrete options lettered when there is more than one, and the cost, quota, or risk attached to each option if there is one;
   - the skill's recommendation and one clause of why;
   - how to answer: reply in chat with the letter or the value, and the next run records it and acts on it. The reader never has to edit a file.
   Write the id in parentheses at the end of the item so the answer can be filed, not at the start as its name. If there are no open items, say "Nothing is waiting on you."
5. **How the run ended.** Diff on the working tree with the file count, a commit with its subject, or a PR with its link, per `config.git.mode`, and where the run record lives, in one line.
6. **Connections.** On a first run, or when detection changed, the full report from `setup.md`. Otherwise one line naming the missing connections that would add the most, until each is declined. Omit entirely when nothing worth adding is missing.

Example of a decision item, the shape every item takes:

> **The answer-engine remeasure is waiting on budget.** The last measurement of what ChatGPT, Claude, Perplexity and Gemini say about the product was on 2026-08-26, and the 14-day remeasure is due. Options: (a) full remeasure on 2026-09-23, about $33, after the fixes shipped since have had time to land; (b) a reduced sample of the top prompts now, about $10; (c) skip until asked. Recommend (a): the deployed fixes are what we want to measure, and they need the crawl time. Reply with a letter. (NY-3)

The same rule applies to the interactive checkpoint in Step 2: the three candidates are described in the reader's terms with the evidence in words, and the question's options carry the whole choice, not a label.

