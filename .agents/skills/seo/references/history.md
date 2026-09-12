# History

<!-- not loaded by any step; background for anyone who wonders why the rules are shaped the way they are -->

## Why correcting beats creating

Earlier versions of this skill could only add: a new piece, a new page batch, a new AEO fix. An outside audit of a site they had been running found that the highest-value work was correcting what was already live. A clinical-trial finder listed an unrelated study on a cancer page. A records-request page pre-filled the wrong mailing address. Five pages disagreed about pricing. A guide stated a regulatory rule that was false. An internal drafting phrase had shipped into public copy. IndexNow was resubmitting the whole sitemap on every deploy. An analytics beacon was leaking private record IDs. Not one of those would ever have been found by a skill whose only move was "write the next piece."

So v2 treats `correct`, `repair`, `refresh`, `consolidate` and `verify-product` as first-class actions, scored against `create`. A run that ends in "nothing beats the bar today, here is what I measured" is a legitimate, successful run.

Version 2.2 closed the loop and widened the pool. It scores every past action against the site-wide control and feeds the result back into the rubric's confidence axis (`priors.json`), so the skill learns which actions work on *this* site. It adds nine cheap recurring panels that were missing: what competitors shipped and gained, which of our queries an AI Overview or SERP feature is eating, backlinks lost and inbound links landing on 404s, unlinked brand mentions, what the product itself changed since the last run, internal links the site already has the words for, branded demand as a trend, seasonality eight weeks out, and what visitors searched for on the site and did not find. And it adds one action, `distribute`, because a piece that ships and is never mentioned anywhere launches into silence.

## Field notes behind specific rules

- **Page count is almost never the gap.** A competitor with "15,000 pages" turned out to be 236 pages in 32 locales, and the site being compared already had 240.
- **Traffic concentrates where the product is the answer.** Informational pages targeting queries a government, institution or reference site already owns sat at position 60 or worse with zero clicks on every site audited.
- **Content-ops artifacts ship.** A placeholder heading, a "UGC video hook" label and an internal positioning note all reached production on an actively managed site. The truth check and the health diff exist to catch these.
- **IndexNow receipts are not indexing.** One site logged "217 URLs indexed via IndexNow" on every deploy. None of that was index state.
- **Bought links.** A competitor audited for this skill spiked to 200 referring domains in a month; 28 of them were link sellers.
- **Claims decay.** A post-hoc review reframed or removed 72 of 151 sampled claims on pages that had shipped through this skill's predecessor. Hence claim re-verification.
- **The query table is a minority of clicks.** On one audited site it covered 12%. Hence classify by page.
