from pathlib import Path
import pandas as pd
R = Path(__file__).resolve().parent
b = (R / "brief.md").read_text()
d = lambda n: pd.read_csv(R / "data" / n)
f = lambda v: f"{v:.2f}"
h = d("headline_gap.csv").iloc[0]
pat = d("conversion_by_pattern.csv").set_index("pattern")
band = d("gap_by_total_activity.csv")
sens = d("sensitivity_cutoffs.csv")
shape = d("group_shape.csv").set_index("pattern")
cty = d("gap_by_country.csv").set_index("country")
dev = d("gap_by_device.csv").set_index("device_type")
want = [f(h.binge_conv_pct), f(h.steady_conv_pct), f(abs(h.gap_pp)), f(abs(h.gap_ci95_low_pp)), f(abs(h.gap_ci95_high_pp)),
        f(abs(h.gap_relative_pct)), f(h.overall_conv_pct), f(abs(pat.loc["binge then quiet", "vs_overall_pp"])),
        f(pat.loc["steady", "vs_overall_pp"]), f(pat.loc["light (under minimum sessions)", "conv_pct"]),
        f(d("matched_gap.csv").matched_gap_pp[0] * -1), f(sens.gap_pp.max() * -1), f(sens.gap_pp.min() * -1),
        f(shape.loc["binge then quiet", "sessions_day1"]), f(shape.loc["binge then quiet", "sessions_day2"]),
        f(shape.loc["binge then quiet", "sessions_day3"]), str(int(h.binge_trials)), str(int(h.steady_trials)),
        "1,516", "13.18", "12.08"]
for v in band.gap_pp: want.append(f(abs(v)))
want += [f(abs(cty.gap_pp.max())), f(abs(cty.gap_pp.min())), f(abs(dev.gap_pp.max())), f(abs(dev.gap_pp.min()))]
bad = [w for w in want if w not in b]
for w in want: print(("OK  " if w in b else "MISSING ") + w)
print("em dash:", "—" in b, "| mismatches:", bad)
