"""Day-one binge and trial conversion. Run from the repo root:
poetry run python outputs/2026-11-19_binge-day-one-trial-conversion/analysis.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from helpers import charts, checks  # noqa: E402
from helpers.db import read_sql  # noqa: E402

RUN = Path(__file__).resolve().parent
OUT = RUN / "data"
OUT.mkdir(exist_ok=True)
ASOF = pd.Timestamp("2026-09-24 23:59:59")  # the data ends here; treated as today
SEED = 42
SMALL = 30  # groups with fewer trials than this are flagged small
MAIN = dict(share=0.70, steady_share=0.50, min_total=5)  # set before looking at conversion
BANDS = [(5, 7), (8, 11), (12, 17), (18, 10**6)]
BAND_LABELS = ["5-7", "8-11", "12-17", "18+"]
results = []


def check(res):
    print("CHECK:", res["summary"])
    results.append(res["ok"])


# ---- load (read-only SQL, only the columns needed) ----
trials = read_sql("select trial_id, user_id, started_at, ends_at, outcome, outcome_at from public.trials")
snap = read_sql(
    "select trial_id, user_id, trial_started_at, country, device_type, sessions_day1, sessions_day2, "
    "sessions_day3, listen_sessions_3d, total_minutes_3d, converted from ml.trial_snapshot"
)
print(f"Loaded {len(trials):,} trials and {len(snap):,} snapshot rows.")
check(checks.date_boundaries(trials, "started_at"))

# ---- quirk: only matured trials (ends_at closed by the analysis date) ----
m = checks.matured_only(trials, "ends_at", as_of=ASOF)
check(m)
matured = m["kept"]
print(f"Matured trials: {len(matured):,}; still open or cancelled early: {m['dropped']:,}")
check(checks.join_fan_out(matured, snap[["trial_id"]], "trial_id"))
d = matured.merge(snap, on=["trial_id", "user_id"], how="inner")
print(f"Matured trials with a snapshot: {len(d):,} (matured without one: {len(matured) - len(d):,})")

# converted flag must agree with the trial outcome
agree = ((d.converted == 1) == (d.outcome == "converted")).all() and d.outcome.notna().all()
check({"ok": bool(agree), "summary": f"converted agrees with trials.outcome on all {len(d):,} rows." if agree else "converted and trials.outcome DISAGREE."})
# cancellations must come after the 3 day window, or quiet days could be a cancellation effect
early_cancel = ((d.outcome == "canceled") & (d.outcome_at < d.started_at + pd.Timedelta(days=3))).sum()
check({"ok": early_cancel == 0, "summary": f"{early_cancel} trials cancelled inside the first 3 days (0 means the 3 day features are not cut short)."})

# ---- engagement groups (from day 1 to 3 sessions only, never from the outcome) ----
d["total3"] = d.sessions_day1 + d.sessions_day2 + d.sessions_day3
d["quiet_after"] = d.sessions_day2 + d.sessions_day3
d["share1"] = np.where(d.total3 > 0, d.sessions_day1 / d.total3.where(d.total3 > 0), np.nan)


def group(df, share=MAIN["share"], steady_share=MAIN["steady_share"], min_total=MAIN["min_total"]):
    g = pd.Series("other (mixed pattern)", index=df.index)
    g[df.total3 < min_total] = "light (under minimum sessions)"
    g[(df.total3 >= min_total) & (df.share1 >= share)] = "binge then quiet"
    g[(df.total3 >= min_total) & (df.share1 <= steady_share) & (df.sessions_day2 > 0) & (df.sessions_day3 > 0)] = "steady"
    return g


d["pattern"] = group(d)
ORDER = ["binge then quiet", "steady", "other (mixed pattern)", "light (under minimum sessions)"]
overall = d.converted.mean() * 100


def rates(df, by):
    g = df.groupby(by).agg(trials=("converted", "size"), converted=("converted", "sum")).reset_index()
    g["conv_pct"] = 100 * g.converted / g.trials
    g["small"] = g.trials < SMALL
    return g


pat = rates(d, "pattern").set_index("pattern").loc[ORDER].reset_index()
pat["vs_overall_pp"] = pat.conv_pct - overall
pat.to_csv(OUT / "conversion_by_pattern.csv", index=False)
check(checks.parts_sum_to_total(pat.trials, len(d)))
check(checks.parts_sum_to_total(pat.converted, d.converted.sum()))
print(f"\nOverall conversion of the {len(d):,} matured trials with a snapshot: {overall:.2f}%")
print(pat.round(2).to_string(index=False))


def gap(df, rng):
    b = df[df.pattern == "binge then quiet"].converted.to_numpy()
    s = df[df.pattern == "steady"].converted.to_numpy()
    if len(b) == 0 or len(s) == 0:
        return np.nan, np.nan, np.nan, len(b), len(s), np.nan
    diff = (b.mean() - s.mean()) * 100
    boots = [(rng.choice(b, len(b)).mean() - rng.choice(s, len(s)).mean()) * 100 for _ in range(2000)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    rel = 100 * diff / (s.mean() * 100) if s.mean() else np.nan
    return diff, lo, hi, len(b), len(s), rel


rng = np.random.default_rng(SEED)
diff, lo, hi, nb, ns, rel = gap(d, rng)
headline = pd.DataFrame([dict(
    binge_trials=nb, steady_trials=ns,
    binge_conv_pct=d[d.pattern == "binge then quiet"].converted.mean() * 100,
    steady_conv_pct=d[d.pattern == "steady"].converted.mean() * 100,
    overall_conv_pct=overall, gap_pp=diff, gap_ci95_low_pp=lo, gap_ci95_high_pp=hi, gap_relative_pct=rel)])
headline.to_csv(OUT / "headline_gap.csv", index=False)
print("\nHeadline: binge then quiet vs steady")
print(headline.round(2).to_string(index=False))

# ---- fair comparison: same total activity ----
d["band"] = pd.cut(d.total3, [lo_ - 0.5 for lo_, _ in BANDS] + [10**6], labels=BAND_LABELS, right=False)
d.loc[d.total3 < MAIN["min_total"], "band"] = np.nan
rows = []
for lab in BAND_LABELS:
    sub = d[d.band == lab]
    b, s = sub[sub.pattern == "binge then quiet"], sub[sub.pattern == "steady"]
    rows.append(dict(band=lab, binge_trials=len(b), steady_trials=len(s),
                     binge_conv_pct=b.converted.mean() * 100 if len(b) else np.nan,
                     steady_conv_pct=s.converted.mean() * 100 if len(s) else np.nan,
                     gap_pp=(b.converted.mean() - s.converted.mean()) * 100 if len(b) and len(s) else np.nan,
                     small=(len(b) < SMALL) or (len(s) < SMALL)))
band = pd.DataFrame(rows)
band.to_csv(OUT / "gap_by_total_activity.csv", index=False)
print("\nGap within total activity bands (sessions in first 3 days)")
print(band.round(2).to_string(index=False))
usable = band.dropna(subset=["gap_pp"])
w = usable.binge_trials / usable.binge_trials.sum()
matched_gap = float((w * usable.gap_pp).sum())
check(checks.parts_sum_to_total(band.binge_trials, nb))
check(checks.parts_sum_to_total(band.steady_trials, ns))
mean_total = d.groupby("pattern").total3.mean().reindex(ORDER)
print(f"\nMean sessions in first 3 days by group: {mean_total.round(2).to_dict()}")
print(f"Gap at matched total activity (weighted to the binge group's mix): {matched_gap:.2f} pp")
pd.DataFrame([dict(raw_gap_pp=diff, matched_gap_pp=matched_gap)]).to_csv(OUT / "matched_gap.csv", index=False)

# ---- robustness: other cut-offs ----
rows = []
for share in (0.6, 0.7, 0.8):
    for min_total in (3, 5, 8):
        dd = d.copy()
        dd["pattern"] = group(dd, share=share, min_total=min_total)
        g, glo, ghi, b_n, s_n, r = gap(dd, np.random.default_rng(SEED))
        rows.append(dict(binge_share_cutoff=share, min_sessions=min_total, binge_trials=b_n, steady_trials=s_n,
                         gap_pp=g, gap_ci95_low_pp=glo, gap_ci95_high_pp=ghi))
sens = pd.DataFrame(rows)
sens.to_csv(OUT / "sensitivity_cutoffs.csv", index=False)
print("\nSensitivity to the cut-offs")
print(sens.round(2).to_string(index=False))

# ---- segments: country, device, start week ----
d["start_week"] = pd.to_datetime(d.trial_started_at).dt.to_period("W-SUN").dt.start_time.dt.date.astype(str)
for col, name in [("country", "country"), ("device_type", "device"), ("start_week", "start_week")]:
    rows = []
    for val, sub in d.groupby(col):
        b, s = sub[sub.pattern == "binge then quiet"], sub[sub.pattern == "steady"]
        rows.append({col: val, "trials": len(sub), "binge_trials": len(b), "steady_trials": len(s),
                     "binge_conv_pct": b.converted.mean() * 100 if len(b) else np.nan,
                     "steady_conv_pct": s.converted.mean() * 100 if len(s) else np.nan,
                     "gap_pp": (b.converted.mean() - s.converted.mean()) * 100 if len(b) and len(s) else np.nan,
                     "small": (len(b) < SMALL) or (len(s) < SMALL)})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / f"gap_by_{name}.csv", index=False)
    check(checks.parts_sum_to_total(t.trials, len(d)))
    print(f"\nGap by {name}")
    print(t.round(2).to_string(index=False))

# ---- day-by-day shape of each group (what the groups look like) ----
shape = d.groupby("pattern")[["sessions_day1", "sessions_day2", "sessions_day3"]].mean().reindex(ORDER).round(2).reset_index()
shape.to_csv(OUT / "group_shape.csv", index=False)
print("\nMean sessions per day by group")
print(shape.to_string(index=False))

# ---- charts ----
cmp_ = pat[pat.pattern.isin(["binge then quiet", "steady"])]
fig = charts.bar(
    list(cmp_.pattern), list(cmp_.conv_pct.round(1)),
    f"Binge-then-quiet trials convert {abs(diff):.1f} points {'lower' if diff < 0 else 'higher'} than steady ones",
    highlight="binge then quiet", ylabel="Trial conversion, % of matured trials",
    source=f"ml.trial_snapshot, matured trials only. Overall conversion {overall:.1f}%.",
)
charts.save(fig, RUN / "charts" / "conversion_by_pattern.png")

u = band.dropna(subset=["gap_pp"])
fig = charts.bar(
    list(u.band), list(u.gap_pp.round(1)),
    f"Matching on total activity leaves the gap at {abs(matched_gap):.0f} points",
    highlight=list(u.band), ylabel="Binge minus steady conversion, percentage points",
    source="Bands are total sessions in the first 3 days. Small bands are flagged in the table.",
)
charts.save(fig, RUN / "charts" / "gap_by_total_activity.png")

print(f"\nChecks passed: {sum(results)} of {len(results)}")
