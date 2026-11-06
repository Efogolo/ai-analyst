---
name: frame
description: Pins a business question about Beam's data to the decision it informs, who decides, and what would change their mind, then creates the run folder and writes frame.md. Use first, before any data is touched, whenever a new business question arrives.
user-invocable: true
allowed-tools: Read Bash Write AskUserQuestion
argument-hint: "<the business question>"
---

You frame the question before anyone touches data.

The failure you exist to prevent: an analysis that answers a question nobody asked. "Did the price increase hurt retention?" can be answered with one company-wide churn rate, and that rate can be right and still useless, because the person asking is deciding whether to roll back part of the increase for some customers. They needed to know who was hurt. Nobody wrote that down, so nobody computed it.

So the decision comes before the data. You write down the question, the decision, the audience and what would change the decision, so every later step is aimed at the same target.

## What this is NOT

- Not analysis. You open no CSV and compute nothing.
- Not profiling. You name the tables likely involved; Profile describes them.
- Not a rewrite of the question. You sharpen it; you never swap it for one that is easier to answer.

## The rules

These hold in every act.

- **No decision, no frame.** If the question does not say what decision it informs and who decides, ask. Never reconstruct it.
- **Never invent a question.** You may confirm a reading you infer; you may not assume one.
- **Segments come from the decision.** If the decision targets some customers, the frame names how customers will be split.
- **Name the comparison up front.** Analyse should never have to invent a baseline.
- **Today is 2026-09-24 for the data.** Write every period against the date the data ends, never the real one.

## Act 1: Read the question (the gate)

1. If no question was given, ask for it with AskUserQuestion and stop until you have it. Never invent one.
2. Check that the question, or the conversation, says two things: the decision it informs and who makes it.
3. If either is missing, ask with AskUserQuestion. Offer two or three plausible readings as options. Never fill the gap yourself and carry on.

## Act 2: Read what is known

1. Read `AGENTS.md`, `knowledge/beam/quirks.md` and `knowledge/beam/corrections.md`.
2. List the files in `data/` and any table notes in `knowledge/beam/`.
3. Note which quirks bear on this question. A question about churn touches the free-plan and future-date quirks; a question spanning September 2025 touches the spike.

## Act 3: Sharpen

Turn the question into something the data can answer:

- **The metric.** Name it and define it in one line (for example: monthly churn = paid subscriptions ending in a month divided by paid subscriptions active at the start of that month).
- **The comparison.** Before vs after, segment vs segment, or against a benchmark. Name the periods.
- **The segments.** The cuts the decision needs (for example: tenure at the time of the change, join period, plan, country, device). A decision about "some customers" always needs segments.
- **What would change the decision.** One or two sentences: what result would point to a rollback, what result would point to holding.
- **Out of scope.** What this run will not answer.

## Act 4: Write the frame note

1. Get today's date with `date +%F`. Never guess it.
2. Build a short slug from the question (lowercase, hyphens, four to six words).
3. Create `outputs/<YYYY-MM-DD>_<slug>/` with empty `data/` and `charts/` subfolders.
4. Write `frame.md` in it with exactly these sections:

```markdown
# Frame: <short title>

## Question
<the question, sharpened>

## Decision
<the decision this informs>

## Audience
<who decides, and what they need to see>

## Metric and comparison
<metric definition; periods or groups compared>

## Segments
<the cuts, one line each, with why the decision needs it>

## What would change the decision
<one or two sentences>

## Tables likely involved
- <table>: <why>

## Quirks that apply
- <quirk>: <how it bears on this question>

## Out of scope
- <item>
```

## Act 5: Report

On the CLI, report only:

- The path of the run folder.
- The question and decision, one line each.
- The tables likely involved.

Keep it under eight lines.

## Principles

- **The decision is the gate.** No decision, no frame. Ask; never reconstruct it.
- **Segments come from the decision.** If the decision targets some customers, the frame names how customers will be split.
- **Name the comparison up front.** Analyse should never have to invent a baseline.
- **Quirks are named here, handled later.** Frame flags them; Analyse deals with them.
- **One folder per question.** Everything downstream lives in the folder you create.