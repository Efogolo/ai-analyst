from pathlib import Path
import pandas as pd
R = Path(__file__).resolve().parent
b = (R / "brief.md").read_text()
d = lambda n: pd.read_csv(R / "data" / n)
f = lambda v: f"{v:.2f}"
plan = d("churn_by_plan.csv")
m = plan[(plan.plan == "monthly") & (plan.comparison == "this year")].iloc[0]
a = plan[(plan.plan == "annual") & (plan.comparison == "this year")].iloc[0]
pl = plan[(plan.plan == "monthly") & (plan.comparison != "this year")].iloc[0]
ten = d("monthly_churn_by_tenure.csv").set_index("tenure")
cty = d("monthly_churn_by_country.csv").set_index("country")
dev = d("monthly_churn_by_device.csv").set_index("device_type")
coh = d("monthly_churn_by_cohort.csv").set_index("cohort")
ser = d("monthly_churn_series.csv").set_index("month").monthly_churn_pct
want = [f(m.pre_pct), f(m.post_pct), f(m.change_pp), f(m.change_rel_pct), f(a.pre_pct), f(a.post_pct), f(pl.change_pp),
        f(d("tenure_matched_summary.csv").change_pp_matched[0]), f(d("sensitivity_without_sep_2025_cohort.csv").change_pp[0]),
        f(ser["2026-04"]), f(ser["2026-03"]), f(ser["2026-08"]), f(ser["2026-07"]), f(coh.loc["4 joined Mar 2026 or later", "churn_pct_post"]),
        str(int(coh.loc["3 joined Oct 2025 to Feb 2026", "churned_pre"]))]
for t in ten.index: want += [f(ten.loc[t, "churn_pct_pre"]), f(ten.loc[t, "churn_pct_post"]), f(ten.loc[t, "change_pp"])]
for t in cty.index: want.append(f(cty.loc[t, "change_pp"]))
for t in dev.index: want.append(f(dev.loc[t, "change_pp"]))
bad = [w for w in want if w not in b]
for w in want: print(("OK  " if w in b else "MISSING ") + w)
print("em dash:", "—" in b, "| mismatches:", bad)
