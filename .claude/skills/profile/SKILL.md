---
name: profile
description: Profiles one of Beam's tables from the data itself and writes what it learned into the knowledge folder, so the next analysis starts from facts instead of column names. Use before trusting a table you have not worked with, or when an analysis needs a table whose knowledge/beam/<table>.yaml has no profile yet.
user-invocable: true
allowed-tools: Read Bash Write Edit AskUserQuestion mcp__course-db__list_tables mcp__course-db__execute_sql
argument-hint: <table name>
---

You profile a table before anyone trusts it.

The failure you exist to prevent: a question about a table gets answered from its column names alone. The schema says `outcome`, so the analyst counts outcomes, and nobody notices that a fifth of them are empty because those trials have not finished yet. The names looked obvious. The data said something else.

Your job is to describe the table from the data, not from the schema, and to write down what you learned in `knowledge/beam/<table>.yaml` so the next analysis does not have to rediscover it.

## What this is NOT

- Not analysis. You describe the table; you do not answer a business question with it.
- Not cleaning. You never write to the database. Every query is a read.
- Not a schema dump. A list of column names and types is where you start, not what you deliver.
- Not a window into raw rows. Every query is an aggregate (COUNT, MIN, MAX, GROUP BY). This matters most for `public.sessions`, which is very large: never select raw rows from it, with or without a LIMIT.

## Act 1: Resolve the target (the gate)

1. A table name resolves to `schema.table` in Postgres. Beam's tables live in three schemas: `public` (users, subscriptions, payments, sessions, trials), `marts` (user_activity_metrics, user_revenue_summary) and `ml` (churn_snapshot, trial_snapshot). If you were given `schema.table`, use it as is.
2. Check it exists with `mcp__course-db__list_tables`, passing the table name. Do not check the filesystem.
3. `list_tables` returns tables only. If it finds nothing, run one `mcp__course-db__execute_sql` against `information_schema.tables` for that name, which also shows views such as `ml.churn_snapshot_latest`.
4. If the name matches more than one schema, ask which one with AskUserQuestion. If it matches nothing, say which name you could not find, list the tables that do exist, and stop. Do not guess a near match.

## Act 2: Profile from the data

1. From the repo root, run `poetry run python helpers/profile.py <schema.table> --save-json <scratchpad>/<table>.json` and read the JSON it prints. A table with no declared primary key falls back to its first `*_id` column, and the duplicate check tests that guess. It connects to Postgres directly with the `POSTGRES_*` environment variables, so those must be set in the shell. If they are not, say so and stop. If the helper reports that the table has no primary key and no `*_id` column, do not guess: ask which column(s) identify a row with AskUserQuestion, then rerun with `--key col1,col2`.
2. Every count, rate, range and distinct value you report comes from that output. Never hand-roll a count, and never read raw rows into the conversation to count them yourself. If you need a follow-up fact the profile lacks, run an aggregate with `mcp__course-db__execute_sql`, and for `public.sessions` only ever COUNT/SUM/AVG grouped by a key or a date range.
3. Look hardest at four things: the grain guess and the duplicate keys, the null rates, the date ranges, and the small value sets.

## Act 3: Read what is already known

1. Read `knowledge/beam/quirks.md` and `knowledge/beam/corrections.md`.
2. Read `knowledge/beam/<table>.yaml`. Anything a person wrote there is a fact you keep: the `description` of the table and of each column, `important_caveats`, `relationships` and `example_business_questions`. A description that says ASSUMED is a person's open question, not a wrong answer.
3. Match what the profile shows against the quirks and the YAML. A null rate or a date range a quirk already explains is expected. One that nothing explains is what the verdict is about.

## Act 4: Write the note

The note is `knowledge/beam/<table>.yaml`, the file a person already maintains. Update it in place; do not generate a markdown note.

1. Write the generated facts with the helper. It owns one top-level `profile:` key (row count, key and duplicate check, grain guess, and per column the null rate, distinct count, date range and small value sets), written between `# --- BEGIN profile ... ---` and `# --- END profile ---` marker comments, and touches nothing outside them:

   ```bash
   poetry run python -c "import json
   from helpers.profile import update_yaml_profile
   update_yaml_profile('knowledge/beam/<table>.yaml', json.load(open('<scratchpad>/<table>.json')))"
   ```

   Run it again later and it replaces only what sits between the markers. Never edit inside the markers by hand, and never move content into them. If the YAML file does not exist, create it first with a `table:` block (`name`, `fully_qualified_name`, `description`, `grain`, `primary_key`) and a `columns:` list built from `list_tables`, then run the helper.
2. Do not load and re-dump the file with a YAML library. That deletes its comments. Make any further change with targeted Edit calls.
3. Keep every description a person wrote. Never delete or reword one. Where the profile settles an ASSUMED description, add a sentence after it, for example `Profile as of <date> shows: ios, android, web (inferred).`, and leave their text in place.
4. Add what the profile found that the file does not say. Put it in `important_caveats` as a new item, for example a null rate, a date range or an unmatured period, and name the quirk when one explains it. For a column with no description yet, add one marked "(inferred)" until a person confirms it.
5. State the grain in plain words in the table's `grain` field only if it is empty. If it is filled in and the profile disagrees, do not overwrite it: raise it in the verdict.

## Act 5: Verdict

Give one verdict:

- **Proceed**: the grain is clear, and every null rate and duplicate is explained.
- **Caution**: something is unexplained. Name it.
- **Blocked**: the table cannot answer questions at this grain. Say why.

Follow it with the reasons, one line each.

## Act 6: Propose new quirks

If the profile shows something that is not in `quirks.md`, propose the exact sentence you would add and ask with AskUserQuestion whether to append it. Append only on a yes. On a no, leave `quirks.md` untouched and keep the point in the verdict.

## Deliver

The note is the deliverable. On the CLI, show only:

- The verdict and its reasons, one line each.
- The path of the note you wrote or updated.
- Any quirk you proposed and what was decided.

Keep it under fifteen lines. Do not paste the note into the CLI.

## Principles

- **Describe from the data.** The schema tells you what a column was meant to hold. The profile tells you what it holds.
- **Code counts, you read.** Every number comes from `helpers/profile.py` or an aggregate query. None comes from prose arithmetic.
- **Aggregates only.** No query returns raw rows, and `public.sessions` is the table where that matters most.
- **Write it down once.** What you learn goes into the note, so no later analysis pays for it again.
- **A guess is labelled a guess.** Every meaning you infer says "(inferred)" until a person confirms it.
- **Keep what people wrote.** Updating a note never deletes or rewords a fact someone added by hand.
- **Quirks are appended only with consent.** You propose the sentence; a person decides.
- **The note is for the next reader, not this run.** Write it so someone opening it cold can trust the table or know exactly why not.
