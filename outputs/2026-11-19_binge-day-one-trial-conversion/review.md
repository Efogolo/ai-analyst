# Review: Day-one binge and trial conversion

**Verdict: Think on it**

## Mechanics
- It reruns: pass, `poetry run python` finished clean and rewrote every table in `data/`; a small label fix (one chart title) was applied and the script rerun once.
- The checks ran: pass, join fan-out (1,516 of 1,553 rows kept), matured-only on `ends_at`, date boundaries, parts-sum on every split, `converted` against `trials.outcome` (agrees on all 1,516), and a check that no trial cancelled inside the first 3 days.
- No silent rows: pass, 520 unmatured trials dropped by `matured_only`; 37 matured trials have no snapshot and are reported, not hidden; the four pattern groups add to 1,516 trials and 807 conversions.
- Quirks handled: pass, trials mature late (matured by `ends_at`, not by outcome), early cancellations in open trials excluded with them, snapshot coverage named, dates compared as dates.
- Closed periods only: pass, only trials whose 14 days closed by 2026-09-24; last trial start in the analysis set is 2026-09-09.
- Corrections honoured: n/a, `corrections.md` is empty.
- Numbers trace: pass, CLI numbers match `headline_gap.csv`, `conversion_by_pattern.csv`, `gap_by_total_activity.csv` and `matched_gap.csv`.
- Two of twelve check lines read as not ok: the partial-edge note on `started_at` and the intended exclusion of 520 open trials.

## Reasoning
- Answers the question asked: pass, binge then quiet against steady, in percentage points and relative percent, with an interval.
- Comparisons named: pass, overall conversion as the benchmark; no earlier period exists and the brief says so.
- Fair baseline: pass, the groups have similar total activity (13.18 vs 12.08 sessions) and the gap holds within activity bands (-41 to -63 points), so it is not just heavy against light users.
- Causal language: open, this is association. The steady group is defined by having sessions on days two and three, which is itself a sign of interest. A gap this large (-53.78 points) is unlikely to be closed by an email, so it shows who converts, not what a nudge would do.
- Small segments: pass, every pattern, band, country and device group has at least 30 trials; two start weeks are flagged small.
- Not checked is said: pass.

## Findings
1. The result is an association, not evidence that spreading usage would raise conversion: users who return on days two and three differ in intent. Fix: say so in the brief and recommend a randomised test of the email before any rollout.
2. The definition of a "day" in the snapshot is not documented (calendar day or 24 hours from trial start), and the groups depend on it. Fix: list as not verified.
3. The groups were fixed before looking at conversion, but the cut-offs are still a choice. Fix: carry the sensitivity range (-50.19 to -60.03 points) into the brief.
4. Only 1,516 of 1,553 matured trials have a snapshot (the 37 from 2026-09-10 are missing), and the program is 54 days old. Fix: list both as not verified.
5. Nothing is known about how users were acquired or which plan they intended to buy. Fix: list as not verified.

## Not checked
- Whether spreading usage would change conversion (no experiment).
- How the snapshot defines a day.
- Acquisition source and intent.
- Longer-term effects: conversion is the 14 day outcome only.
