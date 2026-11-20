# Review: March 2026 price increase and retention

**Verdict: Think on it**

## Mechanics
- It reruns: pass, `poetry run python` finished clean twice and rewrote every table in `data/`. All tables match the 2026-11-09 run (same filters, now read from Postgres); `price_check.csv` has 56 months instead of 20 because the database reaches further back, and the overlapping months are identical.
- The checks ran: pass, join fan-out on both joins (30,747 of 30,747 and 144,065 of 144,065 rows kept), date boundaries on both date columns, parts-sum on every segment split.
- No silent rows: pass, 18,234 free and 582 scheduled-start paid subscriptions dropped by explicit filters; segments sum to 1,697 post-period churn events and 30,518 pre-period subscription-months.
- Quirks handled: pass, free plans out, future end dates counted as active, starts after 2026-09-24 out, Sep 2025 cohort named and tested without it, dates compared as dates, one subscription per user (one row is one subscriber).
- Closed periods only: pass, panel stops at 2026-08; September 2026 excluded.
- Corrections honoured: n/a, `corrections.md` is empty.
- Numbers trace: pass, CLI numbers match `churn_by_plan.csv`, the segment tables, `tenure_matched_summary.csv` and `monthly_churn_series.csv`.
- Two of twelve check lines read as not ok: both are partial-edge notes on columns whose edges the script does not use.

## Reasoning
- Answers the question asked: pass, split by plan, tenure, join cohort, country and device, as the decision needs.
- Comparisons named: pass, percentage points and relative percent both stated; annual plan and the year-earlier months as benchmarks.
- Fair baseline: pass, tenure-matched result (+3.34 pp) is close to the crude one (+3.03 pp); without the Sep 2025 cohort it is +2.95 pp.
- Causal language: open, this is before and after. The year-earlier placebo (-0.11 pp) and the flat annual plan (0.00 pp) argue against seasonality and a general trend, but nothing else that changed in March 2026 was tested.
- Small segments: pass, the script now flags segments with fewer than 30 churn events; the Oct 2025 to Feb 2026 cohort (29 events) and the Mar 2026 or later cohort (no pre-period) are flagged.
- Not checked is said: pass.

## Findings
1. The rise is broad, so a targeted rollback would leave most of the loss: every tenure, country and device moved up by 2 pp or more (smallest: iOS +2.17 pp, over 12 months +1.88 pp). Fix: state it plainly in the brief as the answer to "for whom".
2. The effect shows from April, not March: churn was 2.62% in March against 5.53% in April. Payments were at $12 for every monthly payer from March, so this looks like a one-cycle lag. Fix: say so in the brief; it is not tested.
3. Nothing else that changed in March 2026 (product, marketing, acquisition mix) is tested, and the data has no cancellation reason. Fix: list both as not verified and avoid "because of the price" wording; say "followed".
4. Plan switchers are invisible because each user has one subscription row. Fix: list as not verified.

## Not checked
- Whether churn is a price decision versus involuntary or other cancellation (no reason field).
- Other changes in the March 2026 window.
- Plan switches, since the table keeps no history.
- Revenue effect, which is out of scope.
