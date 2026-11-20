# Frame: Day-one binge and trial conversion

## Question
Among matured trials, do users who binge on day one and then go quiet convert to paying at a lower rate than users who use Beam steadily over the first three days? Data ends 2026-09-24, treated as today.

## Decision
Whether the onboarding emails should push trial users to spread their first week out.

## Audience
The head of growth decides. They need the size of the conversion gap between bingers and steady users, how many trial users fall in each group, and whether the gap is large enough that changing behaviour would plausibly change conversion.

## Metric and comparison
- Metric: trial conversion rate = converted trials divided by matured trials. A trial is matured only when its 14 days have closed by 2026-09-24; open trials are not failures and are left out.
- Engagement groups come from the first three trial days: binge-then-quiet (high day one, little or nothing on days two and three) against steady (use spread across the three days). The exact cut-offs are set from the data in Analyse and shown, with a sensitivity run on stricter and looser cut-offs.
- Comparison: binge-then-quiet vs steady, in percentage points and relative percent, each named. Overall conversion of all matured trials is the benchmark. No earlier period exists: trials only started on 2026-08-01.
- Fairness checks: compare within country and device, and within total first-three-day activity, so a gap is not just heavy users against light ones.

## Segments
- Engagement pattern (binge-then-quiet, steady, other): the decision is about moving users from one to the other.
- Total first-three-day activity (low, medium, high): separates a pattern effect from a how-much effect.
- Country and device: the emails can be targeted by these, and they test whether the gap is the same everywhere.
- Trial start week: guards against a launch-period effect, since the program is under two months old.

## What would change the decision
A clear conversion gap that remains at matched total activity and holds in every country and device points to testing spread-out nudges. A gap that vanishes at matched activity, or a binge group too small to matter, points to leaving the emails alone. Either way this is observational: bingers may differ in ways that spreading would not change, so the result supports a test, not a rollout.

## Tables likely involved
- trial_snapshot: sessions on day one, two and three, converted flag, country and device; the direct source.
- trials: start, scheduled end and outcome; defines which trials have matured and cross-checks the converted flag.
- users: signup date and attributes, if a join is needed.

## Quirks that apply
- Trials mature late: only matured trials count, open ones are not failures.
- Trials launched on 2026-08-01 and last 14 days: a short history, so no seasonality and few trials in later weeks.
- Future start dates: scheduled trial starts after 2026-09-24 excluded.
- Timestamps everywhere: compare on dates.
- Sessions past the data end: only matters if sessions are used directly.

## Out of scope
- Revenue or lifetime value of converted users.
- Which email wording works, or the size of any nudge.
- Paid conversion after the trial window and later churn.
- Causal effect of changing behaviour: this run shows association only.
