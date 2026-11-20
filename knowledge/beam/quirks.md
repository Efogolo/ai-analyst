# Beam data quirks

Things we know about our own tables. Check this list before reading a number as a finding.

- **Monthly price change.** The monthly plan price rose from $10 to $12 in March 2026. Monthly payments before and after that point differ for that reason, not because of a data problem.
- **Trials mature late.** Trials launched on 2026-08-01 and last 14 days. A trial's outcome is only known once it matures, so recent trials show `outcome` empty. Those are still open and must not be counted as failures.
- **Free plans never end.** Rows with `subscriptions.plan = 'free'` have no `end_date`. Exclude them from any churn or retention calculation.
- **Future end dates.** `subscriptions.end_date` can be in the future for scheduled cancellations. A subscription with a future end date is still active today.
- **Future start dates.** A few subscriptions have a `start_date` after today: they are scheduled starts, mostly trials that will convert when they mature. Exclude rows that start after the analysis date from any count of what has happened.
- **September 2025 spike.** September 2025 shows a signup spike of roughly five times a normal month, with a matching jump in the active base and in monthly actives. The daily-to-monthly active ratio falls from about .25 to about .21 at that point. Treat it as a known anomaly and say so whenever it enters a comparison.
- **Timestamps everywhere.** Dates in the exports are timestamps. Many `users.signup_date` and subscription dates carry midnight times, others carry real times; compare on dates, not on timestamps, unless the time of day matters.
- **Coarse country buckets.** `users.country` holds only US, EU, India and Rest. Rest is a catch-all, not a country, so never name it as one in a finding.
- **Sessions past the data end.** `sessions.session_date` runs to 2026-09-26, two days after the data ends on 2026-09-24 (273 rows). Filter sessions to the analysis date or earlier before counting what has happened.
- **One subscription per user.** `subscriptions.user_id` is unique: each user has at most one row, so plan changes and re-subscriptions are not kept as history. COUNT(*) per user is 0 or 1, and plan history cannot be rebuilt from this table.
- **Payments are paid plans only.** `payments` has no rows for `plan = 'free'` subscriptions, and 235 started paid subscriptions (mostly expired) have no payment. Count paying users from payments, not from subscriptions with a paid plan.
- **Early cancellations in open trials.** Trials cancel mid-trial, so a trial that has not reached ends_at can already show outcome = canceled (102 trials started 2026-09-11 or later). Define matured by ends_at on or before the analysis date, never by outcome being filled in.
- **Trial snapshot covers part of the matured trials.** ml.trial_snapshot holds trials started 2026-08-01 to 2026-09-09 only (1,516 rows); the 37 matured trials that started on 2026-09-10 are missing.
