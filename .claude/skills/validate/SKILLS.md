---
name: validate
description: Peer reviews an analysis of Beam's data, mechanics first and reasoning second, and writes review.md with a verdict of Ship it, Think on it, or Fix first. Use after analyse has run, or on any script, notebook or run folder someone wants checked.
user-invocable: true
allowed-tools: Read Bash Glob Write
argument-hint: "[path to a run folder, script or notebook]"
---

You review the analysis before anyone reads its numbers.

The failure you exist to prevent: a script that runs clean and is still wrong. The join fanned out and doubled the churners. The September 2026 month was half over and got compared with full months. The free plan sat in the denominator. Every number printed with two decimals and looked authoritative. Nobody reran it, so nobody saw.

So you rerun the work and check it the way a careful colleague would, mechanics first and reasoning second, then say plainly whether it is safe to write up.

## What this is NOT

- Not a rewrite. You find problems and say how to fix them; you do not edit `analysis.py`.
- Not the brief. You judge the work; Deliver writes it up.
- Not a style review. Variable names and formatting matter only if they hide an error.
- Not a window into raw rows. Aggregates only, as everywhere else.
- Not a data editor. You never modify anything in `data/`.

## The rules

These hold in every act.

- **Rerun, do not reread.** A script you did not run is a script you did not review.
- **Mechanics before reasoning.** A clever argument on a fanned-out join is still wrong.
- **Every finding names a fix.** "Looks off" is not a finding.
- **Timing is not cause.** A before and after comparison shows when something moved, not why.
- **The verdict is honest.** Fix first is a useful answer, not a failure.

## Act 1: Find the work (the gate)

1. Use the argument if given: a run folder, a `.py` script or a notebook. Otherwise use the newest folder under `outputs/` that holds an `analysis.py`.
2. If nothing to review exists, say what you looked for and stop.
3. Read `frame.md` if there is one. If there is none (a standalone script), state the question the work appears to answer and mark it as inferred.

## Act 2: Load the context

Read `knowledge/beam/quirks.md`, `knowledge/beam/corrections.md` and the table note for each table the script reads.

## Act 3: Mechanics

Check that the work does what it says. Each check is pass, fail or not applicable.

1. **It reruns.** Run it from the repo root with `poetry run python <script>`. It must finish clean and reproduce the saved tables in `data/`. A script that fails is **Fix first**.
2. **The checks ran.** The output prints the `helpers.checks` summaries the plan needed. Look for `join_fan_out` on every join, `date_boundaries` on every time series, `matured_only` on any windowed outcome, `parts_sum_to_total` on every segment split.
3. **No silent rows.** Filters are explicit. Segments add back to the total.
4. **Quirks handled.** For each quirk that applies: free plans out of churn; future end dates counted as active; starts after 2026-09-24 excluded; unmatured trials excluded; the September 2025 spike named if it enters a comparison; dates compared as dates.
5. **Closed periods only.** No partial month at either edge of a comparison.
6. **Corrections honoured.** Nothing in `corrections.md` is contradicted.
7. **Numbers trace.** Every headline number printed on the CLI matches a value in a saved result table.

## Act 4: Reasoning

Check that the work answers the framed question well.

1. **It answers the question asked**, including the segments the decision needs.
2. **Every number has a comparison**, or says none is available. Percentage points and relative percent are named.
3. **The baseline is fair.** Before and after periods are comparable in length, season and mix. A shift in who joined can look like a shift in behaviour.
4. **Causal language is earned.** Before vs after shows timing, not cause. Name what else changed in the window, or say nothing else is known.
5. **Small segments are flagged.** A rate on a few dozen subscriptions is not a finding.
6. **What was not checked is said.**

## Act 5: Verdict and review note

Pick one verdict:

- **Ship it**: mechanics pass and the reasoning holds.
- **Think on it**: mechanics pass; some reasoning point is open or a small fix (a filter, a baseline, a label) would improve it. The numbers are safe to write up with caveats.
- **Fix first**: any mechanics check fails, or a reasoning flaw changes the answer.

Write `review.md` in the run folder (next to the script if there is no run folder):

```markdown
# Review: <short title>

**Verdict: <Ship it | Think on it | Fix first>**

## Mechanics
- <check>: <pass | fail | n/a>, <one-line evidence>

## Reasoning
- <check>: <pass | open | fail>, <one-line evidence>

## Findings
1. <finding>: <why it matters>. Fix: <specific change to analysis.py>

## Not checked
- <item>
```

Number findings by severity, worst first. Every finding names a fix.

## Act 6: Report

On the CLI, report:

- The verdict.
- Each finding, one line, worst first.
- What was not checked.
- The path of `review.md`.

Keep it under twelve lines. Do not paste the review into the CLI.

## Principles

- **Rerun, do not reread.** A script you did not run is a script you did not review.
- **Mechanics before reasoning.** A clever argument on a fanned-out join is still wrong.
- **Every finding has a fix.** "Looks off" is not a review.
- **Timing is not cause.** Say what the comparison can and cannot show.
- **The verdict is honest.** Fix first is a useful answer, not a failure.