"""March 2026 price increase and retention. Run from the repo root:
poetry run python outputs/2026-11-09_march-2026-price-increase-retention/analysis.py
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from helpers import charts, checks  # noqa: E402

RUN = Path(__file__).resolve().parent
OUT = RUN / "data"
ASOF = pd.Timestamp("2026-09-24")  # the data ends here; treated as today
PRE = ("2025-09", "2026-02")
POST = ("2026-03", "2026-08")
PRE_LY = ("2024-09", "2025-02")  # same months a year earlier (seasonal placebo)
POST_LY = ("2025-03", "2025-08")
results = []


def check(res):
    print("CHECK:", res["summary"])
    results.append(res["ok"])


# ---- load ----
subs = pd.read_csv(ROOT / "data/subscriptions.csv", parse_dates=["start_date", "end_date"])
users = pd.read_csv(ROOT / "data/users.csv", parse_dates=["signup_date"])
pays = pd.read_csv(ROOT / "data/payments.csv", parse_dates=["payment_date"])

check(checks.date_boundaries(subs, "start_date"))
check(checks.date_boundaries(pays, "payment_date"))
check(checks.join_fan_out(subs, users[["user_id", "country", "device_type"]], "user_id"))
check(checks.join_fan_out(pays, subs[["subscription_id", "plan"]], "subscription_id"))

# ---- quirks: free out, scheduled starts out, future end dates stay active ----
n0 = len(subs)
paid = subs[subs.plan != "free"]
print(f"Dropped {n0 - len(paid):,} free subscriptions")
scheduled = paid.start_date.dt.normalize() > ASOF
print(f"Dropped {int(scheduled.sum()):,} paid subscriptions starting after {ASOF.date()}")
paid = paid[~scheduled].copy()
paid["start"] = paid.start_date.dt.normalize()
end = paid.end_date.dt.normalize()
paid["end"] = end.where(end <= ASOF)  # a future end date is still active today
paid = paid.merge(users[["user_id", "country", "device_type", "signup_date"]], on="user_id", how="left")
print(f"Paid subscriptions without a user match: {int(paid.country.isna().sum())}")


def cohort(start):
    if start < pd.Timestamp("2025-09-01"):
        return "1 joined before Sep 2025"
    if start < pd.Timestamp("2025-10-01"):
        return "2 joined Sep 2025 (spike)"
    if start < pd.Timestamp("2026-03-01"):
        return "3 joined Oct 2025 to Feb 2026"
    return "4 joined Mar 2026 or later"


paid["cohort"] = paid.start.map(cohort)

# ---- person-month panel: active at the start of each closed month ----
months = pd.period_range("2024-01", "2026-08", freq="M")  # 2026-09 is open
rows = []
for m in months:
    ms, me = m.start_time, m.end_time.normalize()
    risk = paid[(paid.start < ms) & (paid.end.isna() | (paid.end >= ms))]
    r = risk[["plan", "country", "device_type", "cohort"]].copy()
    r["month"] = str(m)
    days = (ms - risk.start).dt.days
    r["tenure"] = pd.cut(days, [-1, 90, 365, 10**6], labels=["under 3 months", "3 to 12 months", "over 12 months"]).astype(str)
    r["tenure_fine"] = pd.cut(days, [-1, 29, 90, 181, 365, 10**6], labels=["0-1m", "1-3m", "3-6m", "6-12m", "12m+"]).astype(str)
    r["churned"] = (risk.end.notna() & (risk.end <= me)).astype(int).to_numpy()
    rows.append(r)
panel = pd.concat(rows, ignore_index=True)
print(f"Panel: {len(panel):,} subscription-months, {months[0]} to {months[-1]}")


def window(df, w):
    return df[(df.month >= w[0]) & (df.month <= w[1])]


def rate(df, by):
    g = df.groupby(by).agg(at_risk=("churned", "size"), churned=("churned", "sum")).reset_index()
    g["churn_pct"] = 100 * g.churned / g.at_risk
    return g


def compare(df, by, pre=PRE, post=POST):
    a, b = rate(window(df, pre), by), rate(window(df, post), by)
    out = a.merge(b, on=by, how="outer", suffixes=("_pre", "_post"))
    out["change_pp"] = out.churn_pct_post - out.churn_pct_pre
    out["change_rel_pct"] = 100 * out.change_pp / out.churn_pct_pre
    return out


def total_row(df, pre=PRE, post=POST):
    p0, p1 = window(df, pre), window(df, post)
    return p0.churned.mean() * 100, p1.churned.mean() * 100, len(p0), p0.churned.sum(), len(p1), p1.churned.sum()


mon = panel[panel.plan == "monthly"]
ann = panel[panel.plan == "annual"]

# ---- headline: plan ----
rows = []
for name, d in [("monthly", mon), ("annual", ann)]:
    for label, (pre, post) in [("this year", (PRE, POST)), ("year earlier (placebo)", (PRE_LY, POST_LY))]:
        a, b, na, ca, nb, cb = total_row(d, pre, post)
        rows.append(dict(plan=name, comparison=label, pre_pct=a, post_pct=b, change_pp=b - a,
                         change_rel_pct=100 * (b - a) / a, churn_events_pre=ca, churn_events_post=cb))
plan_tbl = pd.DataFrame(rows)
plan_tbl.to_csv(OUT / "churn_by_plan.csv", index=False)
print(plan_tbl.round(2).to_string(index=False))

# ---- by month ----
bym = panel.groupby(["month", "plan"]).churned.mean().mul(100).unstack().reset_index()
bym.to_csv(OUT / "churn_by_month.csv", index=False)

# ---- segments on the monthly plan ----
parts_tot = total_row(mon)
for col, name in [("tenure", "tenure"), ("cohort", "cohort"), ("country", "country"), ("device_type", "device")]:
    t = compare(mon, col)
    t.to_csv(OUT / f"monthly_churn_by_{name}.csv", index=False)
    check(checks.parts_sum_to_total(t.churned_post.fillna(0), parts_tot[5]))
    check(checks.parts_sum_to_total(t.at_risk_pre.fillna(0), parts_tot[2]))
    print(f"\nMonthly plan by {name}")
    print(t[[col, "at_risk_pre", "churn_pct_pre", "churned_pre", "churn_pct_post", "change_pp", "change_rel_pct"]].round(2).to_string(index=False))

# ---- tenure-matched: re-weight post churn to the pre-period tenure mix ----
pre_r, post_r = rate(window(mon, PRE), "tenure_fine"), rate(window(mon, POST), "tenure_fine")
m = pre_r.merge(post_r, on="tenure_fine", suffixes=("_pre", "_post"))
m["pre_mix"] = m.at_risk_pre / m.at_risk_pre.sum()
m["post_mix"] = m.at_risk_post / m.at_risk_post.sum()
m["change_pp"] = m.churn_pct_post - m.churn_pct_pre
m.to_csv(OUT / "tenure_matched_monthly.csv", index=False)
std_post = (m.pre_mix * m.churn_pct_post).sum()
crude_pre, crude_post = parts_tot[0], parts_tot[1]
matched = pd.DataFrame([dict(
    pre_pct=crude_pre, post_pct_crude=crude_post, post_pct_at_pre_tenure_mix=std_post,
    change_pp_crude=crude_post - crude_pre, change_pp_matched=std_post - crude_pre,
    change_rel_pct_matched=100 * (std_post - crude_pre) / crude_pre)])
matched.to_csv(OUT / "tenure_matched_summary.csv", index=False)
print("\nTenure-matched (post churn re-weighted to the pre tenure mix)")
print(matched.round(2).to_string(index=False))
print(m[["tenure_fine", "pre_mix", "post_mix", "churn_pct_pre", "churn_pct_post", "change_pp"]].round(3).to_string(index=False))

# ---- sensitivity: drop the Sep 2025 signup cohort ----
ns = mon[mon.cohort != "2 joined Sep 2025 (spike)"]
a, b, *_ = total_row(ns)
sens = pd.DataFrame([dict(pre_pct=a, post_pct=b, change_pp=b - a, change_rel_pct=100 * (b - a) / a)])
sens.to_csv(OUT / "sensitivity_without_sep_2025_cohort.csv", index=False)
print("\nWithout the Sep 2025 cohort:", sens.round(2).to_dict("records")[0])

# ---- monthly series for the transition ----
tm = mon[(mon.month >= "2025-09")].groupby("month").churned.mean().mul(100)
print("\nMonthly-plan churn by month, %:", tm.round(2).to_dict())
pre_avg, post_rest = crude_pre, window(mon, ("2026-04", "2026-08")).churned.mean() * 100
print(f"March {tm['2026-03']:.2f}% vs pre {pre_avg:.2f}%; Apr-Aug {post_rest:.2f}%")
pd.DataFrame({"month": tm.index, "monthly_churn_pct": tm.values}).to_csv(OUT / "monthly_churn_series.csv", index=False)

# ---- price check: what monthly subscribers paid ----
pm = pays.merge(subs[["subscription_id", "plan"]], on="subscription_id", how="left")
pm = pm[pm.plan == "monthly"].copy()
pm["month"] = pm.payment_date.dt.to_period("M").astype(str)
pm = pm[pm.month <= "2026-08"]
price = pm.groupby("month").amount_usd.agg(payments="size", share_at_12=lambda s: (s == 12).mean(), share_at_10=lambda s: (s == 10).mean()).reset_index()
price.to_csv(OUT / "price_check.csv", index=False)
print("\nMonthly payments at $12 by month:", price[price.month >= "2026-01"][["month", "share_at_10", "share_at_12"]].round(3).to_dict("records"))

# ---- charts ----
x = list(tm.index)
ann_m = ann[ann.month >= "2025-09"].groupby("month").churned.mean().mul(100)
fig = charts.line(x, {"Monthly plan": tm.values, "Annual plan": ann_m.values},
                  "Monthly-plan churn more than doubled after the March 2026 increase; annual did not move",
                  highlight="Monthly plan", ylabel="Monthly churn, % of subscribers active at month start",
                  source="Source: subscriptions.csv, paid plans, closed months. Price rose in March 2026.")
charts.save(fig, RUN / "charts/churn_by_month.png")

t = pd.read_csv(OUT / "monthly_churn_by_tenure.csv").set_index("tenure").loc[["under 3 months", "3 to 12 months", "over 12 months"]]
fig = charts.bar(list(t.index), list(t.change_pp.round(2)),
                 "Newer monthly subscribers lost the most retention after the increase",
                 highlight=["under 3 months"], ylabel="Change in monthly churn, percentage points",
                 source="Mar-Aug 2026 vs Sep 2025-Feb 2026, monthly plan, tenure at month start.")
ax = fig.axes[0]
for tx in list(ax.texts):
    tx.remove()
for bar_, v in zip(ax.patches, t.change_pp):
    ax.annotate(f"+{v:.2f} pp", (bar_.get_x() + bar_.get_width() / 2, bar_.get_height()),
                ha="center", va="bottom", xytext=(0, 3), textcoords="offset points")
charts.save(fig, RUN / "charts/change_by_tenure.png")

print(f"\nChecks passed: {sum(results)} of {len(results)}")
