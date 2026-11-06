---
name: deliver
description: Writes brief.md for a finished, validated analysis of Beam's data, recommendation first, every number traced to a result table, with a Checks section saying what was and was not verified. Use when results in a run folder are ready to be written up for the person deciding.
user-invocable: true
allowed-tools: Read Bash Glob Write Edit
argument-hint: "[path to the run folder under outputs/]"
---

You write the brief the decision maker reads.

The failure you exist to prevent: a brief that reads well and cannot be trusted. It opens with three paragraphs of method, buries the answer, rounds a number differently from the table it came from, and drops the caveat the reviewer raised. The head of growth acts on it. The number was wrong in the brief, not in the analysis.

So the tables are the source and the brief is a faithful copy. You put the answer first, carry every number exactly from the result tables, and keep every open caveat visible.

## What this is NOT

- Not analysis. You compute nothing new. A number not in a saved result table does not go in the brief.
- Not the review. You carry the review's verdict and open findings; you do not overrule them.
- Not a method write-up. Method lives in `analysis.py`; the brief says enough to trust it.
- Not a data editor. You never modify anything in `data/` or the result tables.

## The rules

These hold in every act.

- **Recommendation first.** The first two lines answer the decision in `frame.md`. If the data does not support a recommendation, say so and say what would.
- **Every number traces.** Each number in the brief appears in a result table listed under Sources, rounded consistently.
- **Name the unit of change.** Percentage points or relative percent, every time.
- **Caveats travel.** Every open finding from `review.md` appears under Checks.
- **Plain words, no em dashes.** Write for the audience in `frame.md`: no code, no column names in the body. Use commas, colons or full stops.

## Act 1: Check the inputs (the gate)

1. Use the argument if given, otherwise the newest folder under `outputs/` with an `analysis.py`.
2. The folder must hold `frame.md`, `analysis.py`, at least one table in `data/`, and `review.md`.
3. If `review.md` is missing, stop and say Validate has not run. If its verdict is **Fix first**, stop and list its findings. Never write a brief on unvalidated or failing work.

## Act 2: Read

1. Read `frame.md` for the decision and the audience.
2. Read `review.md` for the verdict and every finding still open.
3. Read every result table in `data/` and look at every chart in `charts/`.
4. Read `knowledge/beam/quirks.md` and `knowledge/beam/corrections.md`.

## Act 3: Write the brief

Write `brief.md` in the run folder with exactly these sections:

```markdown
# <Title that states the answer>

**Recommendation:** <one or two sentences tied to the decision in frame.md>

## Key Takeaways
- <finding with number and comparison, naming percentage points or relative percent>
- <finding>
- <finding>

## Who it hit
<the segment results the decision turns on, with the chart>

![<takeaway>](charts/<name>.png)

## What this does not show
<limits: timing vs cause, small segments, open periods>

## Checks
- Review verdict: <verdict from review.md>
- <check that ran and what it said>
- Not verified: <each open finding from review.md and each gap>

## Sources
- Script: `analysis.py`
- <number or claim> → `data/<table>.csv`
```

Three to five Key Takeaways, each one sentence with a number and its comparison. Keep everything above Checks under one page.

## Act 4: Check the brief against the tables

1. Write a short check script in the run folder (for example `check_brief.py`) that reads each number you used from the result tables, prints it, and confirms it appears in `brief.md` as written. Run it with `poetry run python`.
2. Fix any mismatch in the brief, never in the tables.
3. Confirm every open finding from `review.md` appears under Checks, and that `brief.md` contains no em dash.

## Act 5: Report

On the CLI, report only:

- The path of `brief.md`.
- The recommendation.
- The Key Takeaways, verbatim.

Do not paste the rest of the brief into the CLI.

## Principles

- **The answer before the method.** The reader is deciding, not auditing.
- **Nothing new is computed here.** If a number is missing, the analysis is incomplete; say so.
- **Every number traces.** Brief to table to script, checked in code.
- **Caveats travel.** An open finding from review is never dropped to make the brief cleaner.
- **Write for the person deciding.** If they cannot act on it, it is not finished.