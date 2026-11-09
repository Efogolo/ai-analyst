# Review: March 2026 price increase and retention

**Verdict: Think on it**

## Mechanics
- It reruns: pass, finished clean with `poetry run python` and rewrote every table in `data/`.
- The checks ran: pass, join fan-out on both joins (30,747 of 30,747 and 100,914 of 100,914 rows kept), date boundaries on both date columns, parts-sum on every segment split.
- No silent rows: pass, 18,234 free and 582 scheduled-start subscriptions dropped by explicit filters; segments sum to 1,697 post-period churn events and 30,518 pre-period subscription-months.
- Quirks handled: pass, free plans out, future end dates counted as active, starts after 2026-09-24 out, Sep 2025 cohort named and tested without it, dates compared as dates.
- Closed periods only: pass, panel stops at 2026-08; September 2026 is excluded.
- Corrections honoured: n/a, `corrections.md` is empty.
- Numbers trace: pass, the CLI numbers match `churn_by_plan.csv`, the segment tables and `monthly_churn_series.csv`.
- Two of twelve check lines read as not ok: both are the partial-edge notes on columns whose edges the script does not use (scheduled starts are dropped; the last payment month is not in any window).

## Reasoning
- Answers the question asked: pass, split by tenure, join cohort, country and device, as the decision needs.
- Comparisons named: pass, percentage points and relative percent both stated; annual plan and the year-earlier months as benchmarks.
- Fair baseline: pass, tenure-matched result (+3.34 pp) is close to the crude one (+3.03 pp), so the post-period mix is not driving it.
- Causal language: open, this is before and after. Nothing else known to have changed in the window, but it was not tested.
- Small segments: open, subscribers who joined Oct 2025 to Feb 2026 have 29 churn events in the pre period, and those who joined from March 2026 have no pre-period baseline.
- Not checked is said: pass.

## Findings
1. The rise is broad, so segment differences are in size, not in kind: every tenure, country and device moved up by 2 pp or more. A rollback aimed at one group would leave most of the loss. Fix: carry as a plain statement in the brief.
2. Churn jumped in April (5.53%), not March (2.62%). The script does not show whether March payers were billed at $12 straight away (the price check says they were) or whether cancellations lag one billing cycle. Fix: say in the brief that the effect shows from April.
3. Small segments are not flagged in the tables. Fix: note the 29-event and no-baseline cases in the brief.
4. No test of what else changed in March 2026 (product, marketing, acquisition mix). Fix: list it as not verified.

## Not checked
- Whether churn means "chose to leave because of price" versus involuntary or other cancellation; the data has no reason field.
- Revenue effect of the increase, including whether higher price offsets lost subscribers.
- Statistical uncertainty on the segment differences (no confidence intervals).
- September 2026, which has not closed.
