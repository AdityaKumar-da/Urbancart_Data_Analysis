"""
04_cohort_retention.py
------------------------
Builds a monthly cohort retention table: of the customers who first
purchased in month M, what % were still active in month M, M+1, M+2, ...
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

OUT = "/home/claude/retail-analytics-project/outputs/"
VIZ = "/home/claude/retail-analytics-project/visuals/"

order_level = pd.read_csv(OUT + "order_level_clean.csv", parse_dates=["order_date"])

order_level["order_month"] = order_level["order_date"].values.astype("datetime64[M]")
first_purchase = order_level.groupby("customer_id")["order_month"].min().rename("cohort_month")
order_level = order_level.merge(first_purchase, on="customer_id")

order_level["period_number"] = (
    (order_level["order_month"].dt.year - order_level["cohort_month"].dt.year) * 12
    + (order_level["order_month"].dt.month - order_level["cohort_month"].dt.month)
)

cohort_data = (
    order_level.groupby(["cohort_month", "period_number"])["customer_id"]
    .nunique()
    .reset_index()
)
cohort_pivot = cohort_data.pivot(index="cohort_month", columns="period_number", values="customer_id")
cohort_sizes = cohort_pivot.iloc[:, 0]
retention = cohort_pivot.divide(cohort_sizes, axis=0).round(3)

retention.to_csv(OUT + "cohort_retention.csv")

print("=== Retention Table (first 6 periods, %) ===")
print((retention.iloc[:, :6] * 100).round(1).to_string())

# Average retention curve across all cohorts
avg_retention = retention.mean(axis=0) * 100
print("\n=== Average retention by month-since-signup ===")
print(avg_retention.head(6).round(1).to_string())

# ---------------------------------------------------------------------------
# CHART: Cohort retention heatmap
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(13, 7))
sns.heatmap(retention.iloc[:, :12] * 100, annot=True, fmt=".0f", cmap="Blues",
            ax=ax, cbar_kws={"label": "% Retained"}, vmin=0, vmax=100)
ax.set_title("Monthly Cohort Retention (%)", fontsize=14, fontweight="bold")
ax.set_xlabel("Months Since First Purchase")
ax.set_ylabel("Signup Cohort (Month)")
plt.tight_layout()
plt.savefig(VIZ + "05_cohort_retention_heatmap.png", dpi=150)
plt.close()

m1_retention = avg_retention.get(1, np.nan)
m3_retention = avg_retention.get(3, np.nan)
print(f"\nKey insight: on average, {m1_retention:.0f}% of a cohort returns in month 1, "
      f"dropping to {m3_retention:.0f}% by month 3.")
