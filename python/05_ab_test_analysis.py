"""
05_ab_test_analysis.py
------------------------
Analyzes the UrbanCart email subject-line A/B test:
    control  = generic subject line
    variant  = personalized subject line
Tests whether the difference in conversion rate is statistically
significant, and quantifies the revenue impact.
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = "/home/claude/retail-analytics-project/data/"
OUT = "/home/claude/retail-analytics-project/outputs/"
VIZ = "/home/claude/retail-analytics-project/visuals/"

df = pd.read_csv(DATA + "ab_test_campaign.csv")

summary = df.groupby("group").agg(
    n=("customer_id", "count"),
    conversions=("converted", "sum"),
    avg_order_value=("order_value", "mean"),
).reset_index()
summary["conversion_rate"] = summary["conversions"] / summary["n"]
print("=== A/B Test Summary ===")
print(summary.to_string(index=False))

control = df[df["group"] == "control"]
variant = df[df["group"] == "variant"]

# ---------------------------------------------------------------------------
# Two-proportion z-test on conversion rate
# ---------------------------------------------------------------------------
n1, n2 = len(control), len(variant)
x1, x2 = control["converted"].sum(), variant["converted"].sum()
p1, p2 = x1 / n1, x2 / n2
p_pool = (x1 + x2) / (n1 + n2)
se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
z_stat = (p2 - p1) / se
p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

# 95% CI for the difference in proportions
se_diff = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
ci_low = (p2 - p1) - 1.96 * se_diff
ci_high = (p2 - p1) + 1.96 * se_diff

print(f"\nControl conversion rate: {p1:.2%} (n={n1})")
print(f"Variant conversion rate: {p2:.2%} (n={n2})")
print(f"Absolute lift: {(p2 - p1):.2%}  (relative lift: {(p2/p1 - 1):.1%})")
print(f"Z-statistic: {z_stat:.3f}")
print(f"P-value: {p_value:.4f}")
print(f"95% CI for difference: [{ci_low:.2%}, {ci_high:.2%}]")
alpha = 0.05
result = "statistically significant" if p_value < alpha else "not statistically significant"
print(f"Result at alpha=0.05: {result}")

# ---------------------------------------------------------------------------
# Revenue impact estimate (extrapolated to full customer base)
# ---------------------------------------------------------------------------
avg_value_when_converted = df[df["converted"] == 1]["order_value"].mean()
full_base = 4000  # total customer base size
incremental_conversions_per_1000 = (p2 - p1) * 1000
projected_incremental_revenue = (p2 - p1) * full_base * avg_value_when_converted

print(f"\nAvg order value when converted: ${avg_value_when_converted:.2f}")
print(f"Incremental conversions per 1,000 customers emailed: {incremental_conversions_per_1000:.1f}")
print(f"Projected incremental revenue if rolled out to all {full_base:,} customers: "
      f"${projected_incremental_revenue:,.0f}")

# ---------------------------------------------------------------------------
# Save results
# ---------------------------------------------------------------------------
results = pd.DataFrame([{
    "control_n": n1, "variant_n": n2,
    "control_conv_rate": round(p1, 4), "variant_conv_rate": round(p2, 4),
    "absolute_lift": round(p2 - p1, 4), "relative_lift_pct": round((p2/p1 - 1) * 100, 2),
    "z_stat": round(z_stat, 3), "p_value": round(p_value, 4),
    "ci_95_low": round(ci_low, 4), "ci_95_high": round(ci_high, 4),
    "significant_at_05": p_value < alpha,
    "projected_incremental_revenue": round(projected_incremental_revenue, 0),
}])
results.to_csv(OUT + "ab_test_results.csv", index=False)

# ---------------------------------------------------------------------------
# CHART: Conversion rate comparison with CI
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 5.5))
rates = [p1 * 100, p2 * 100]
errs = [1.96 * np.sqrt(p1 * (1 - p1) / n1) * 100, 1.96 * np.sqrt(p2 * (1 - p2) / n2) * 100]
bars = ax.bar(["Control\n(generic subject)", "Variant\n(personalized subject)"], rates,
              yerr=errs, capsize=8, color=["#8d99ae", "#e07a5f"])
ax.set_ylabel("Conversion Rate (%)")
ax.set_title(f"A/B Test: Email Subject Line\np = {p_value:.4f} ({result})",
             fontsize=13, fontweight="bold")
for bar, rate in zip(bars, rates):
    ax.text(bar.get_x() + bar.get_width()/2, rate + 0.4, f"{rate:.2f}%",
            ha="center", fontweight="bold")
plt.tight_layout()
plt.savefig(VIZ + "06_ab_test_conversion.png", dpi=150)
plt.close()

print("\nSaved results to outputs/ab_test_results.csv and chart to visuals/06_ab_test_conversion.png")
