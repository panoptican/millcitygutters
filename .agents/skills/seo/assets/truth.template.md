# Source of truth

Derived from the repo. This is what fact-check prompts are scored against.
Re-derive whenever pricing, plans or integrations change. A stale truth file turns
correct answers into false accuracy failures and wastes a whole cycle.

| Claim | Value | Source | Read |
|---|---|---|---|
| Starting price | | src/config/plans.ts:12 | |
| Billing intervals | | | |
| Free trial | | | |
| Seat rules | | | |
| Plan limits | | | |
| SSO / SAML | | | |
| Compliance posture | | | |
| Data retention | | | |
| Founded | | | |

## Integrations

Include the negatives. "We do not integrate with X" is the claim an engine is most
likely to get wrong in the flattering direction, and a flattering wrong answer costs
you the deal at the demo instead of at the search.

| Integration | Status | Source |
|---|---|---|
| | yes | app/integrations/... |
| | no | absent from app/integrations/ |

## Contradictions found

Where the code and the marketing site disagree. Each of these is already a finding:
if your own surfaces contradict each other, an engine synthesizing both produces a muddle.

| Claim | Code says | Site says | Which is right |
|---|---|---|---|
| | | | |
