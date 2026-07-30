"""
03_rfm_segmentation.py
------------------------
Builds an RFM (Recency, Frequency, Monetary) model to segment customers
into actionable groups: Champions, Loyal, At Risk, Hibernating, New, etc.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
OUT = "/home/claude/retail-analytics-project/outputs/"
VIZ = "/home/claude/retail-analytics-project/visuals/"

order_level = pd.read_csv(OUT + "order_level_clean.csv", parse_dates=["order_date"])

snapshot_date = order_level["order_date"].max() + pd.Timedelta(days=1)

rfm = order_level.groupby("customer_id").agg(
    recency=("order_date", lambda x: (snapshot_date - x.max()).days),
    frequency=("order_id", "nunique"),
    monetary=("order_revenue", "sum"),
).reset_index()

# Score each dimension 1 (worst) to 4 (best) using quartiles.
# Recency is inverted: lower days-since-last-order = better score.
rfm["r_score"] = pd.qcut(rfm["recency"], 4, labels=[4, 3, 2, 1]).astype(int)
rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
rfm["m_score"] = pd.qcut(rfm["monetary"], 4, labels=[1, 2, 3, 4]).astype(int)
rfm["rfm_sum"] = rfm[["r_score", "f_score", "m_score"]].sum(axis=1)


def segment(row):
    r, f, m = row["r_score"], row["f_score"], row["m_score"]
    if r >= 3 and f >= 3 and m >= 3:
        return "Champions"
    if r >= 3 and f >= 2:
        return "Loyal Customers"
    if r >= 3 and f <= 2:
        return "Promising / New"
    if r == 2 and f >= 2:
        return "Needs Attention"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 1 and f <= 2:
        return "Hibernating / Lost"
    return "Other"


rfm["segment"] = rfm.apply(segment, axis=1)

summary = (
    rfm.groupby("segment")
    .agg(customers=("customer_id", "count"),
         avg_recency_days=("recency", "mean"),
         avg_frequency=("frequency", "mean"),
         avg_monetary=("monetary", "mean"),
         total_revenue=("monetary", "sum"))
    .round(1)
    .sort_values("total_revenue", ascending=False)
)
summary["pct_of_customers"] = (summary["customers"] / summary["customers"].sum() * 100).round(1)
summary["pct_of_revenue"] = (summary["total_revenue"] / summary["total_revenue"].sum() * 100).round(1)

print("=== RFM Segment Summary ===")
print(summary.to_string())

rfm.to_csv(OUT + "rfm_segments.csv", index=False)
summary.to_csv(OUT + "rfm_segment_summary.csv")

# ---------------------------------------------------------------------------
# CHART: Segment size vs revenue contribution
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

order = summary.index
colors = sns.color_palette("viridis", len(order))

axes[0].barh(order, summary["pct_of_customers"], color=colors)
axes[0].set_title("Share of Customers by Segment", fontweight="bold")
axes[0].set_xlabel("% of customers")
axes[0].invert_yaxis()

axes[1].barh(order, summary["pct_of_revenue"], color=colors)
axes[1].set_title("Share of Revenue by Segment", fontweight="bold")
axes[1].set_xlabel("% of revenue")
axes[1].invert_yaxis()
axes[1].set_yticklabels([])

plt.suptitle("RFM Segmentation: Customer Count vs. Revenue Concentration", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(VIZ + "04_rfm_segments.png", dpi=150)
plt.close()

print(f"\nKey insight: '{summary['pct_of_revenue'].idxmax()}' segment is "
      f"{summary.loc[summary['pct_of_revenue'].idxmax(), 'pct_of_customers']}% of customers "
      f"but drives {summary['pct_of_revenue'].max()}% of revenue.")
