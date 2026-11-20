# Frame: March 2026 price increase and retention

## Question
Did the March 2026 monthly price increase ($10 to $12) hurt retention of paying monthly subscribers, and which groups were hurt most? Data ends 2026-09-24, treated as today.

## Decision
Whether to roll back part of the increase for some customers.

## Audience
The head of growth decides. They need to see which customer groups lost retention beyond what was normal before the increase, how large the gap is, and whether the affected groups are big enough to matter.

## Metric and comparison
- Metric: monthly churn = paid subscriptions ending in a month divided by paid subscriptions active at the start of that month.
- Comparison: the six closed months after the increase (2026-03 to 2026-08) against the six closed months before it (2025-09 to 2026-02). The annual plan (not repriced) is the benchmark for the general trend. The same calendar months a year earlier (2024-09 to 2025-02 vs 2025-03 to 2025-08) are the seasonality placebo.
- Fairness checks: churn at matched tenure (so the July and August 2026 signup surge does not drive the result), and a run without the September 2025 signup cohort.
- Timing: churn by month, to show whether the effect starts in March or lags a billing cycle to April.
- Changes are reported in percentage points and in relative percent, always named. Segments with fewer than 30 churn events in either period are flagged as small.

## Segments
- Plan (monthly vs annual): the increase hit monthly only, so annual is the control.
- Tenure at the start of the month (under 3 months, 3 to 12 months, over 12 months): a rollback may target new or loyal customers.
- Join period: before Sep 2025, Sep 2025 (spike), Oct 2025 to Feb 2026, from Mar 2026 (new price from day one).
- Country and device: common ways to target a partial rollback.

## What would change the decision
A churn increase after March concentrated in one or two segments, above the pre-change trend, the annual benchmark and last year's seasonality, points to rolling back for those segments. A rise of the same size in every segment, or one that disappears at matched tenure or against last year's seasonality, points to holding or to a rollback for everyone rather than a targeted one.

## Tables likely involved
- subscriptions: plan, start and end dates; the base for churn and tenure.
- users: country, device and signup date for segments.
- payments: confirms the price each monthly subscriber paid before and after March 2026.

## Quirks that apply
- Monthly price change: marks the break.
- Free plans never end: excluded.
- Future end dates: still active at the analysis date.
- Future start dates: rows starting after 2026-09-24 excluded.
- September 2025 spike: sits in the before period; sensitivity run without it.
- One subscription per user: one row is one subscriber; no plan history, so plan switchers are not visible.
- Timestamps everywhere: compare on dates.
- Trials mature late: not the metric here.

## Out of scope
- Revenue effect of the price change.
- Which price to set or the size of any rollback.
- Trial conversion and acquisition effects.
- September 2026, which has not closed.
