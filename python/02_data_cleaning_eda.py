"""
02_data_cleaning_eda.py
------------------------
Loads raw CSVs, performs data-quality checks & cleaning, and produces
exploratory visualizations of revenue trends, category mix, and
regional performance.
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", palette="deep")
DATA = "/home/claude/retail-analytics-project/data/"
VIZ = "/home/claude/retail-analytics-project/visuals/"

orders = pd.read_csv(DATA + "orders.csv", parse_dates=["order_date"])
order_items = pd.read_csv(DATA + "order_items.csv")
products = pd.read_csv(DATA + "products.csv")
customers = pd.read_csv(DATA + "customers.csv", parse_dates=["signup_date"])

# ---------------------------------------------------------------------------
# DATA QUALITY CHECKS
# ---------------------------------------------------------------------------
print("=== Data Quality Report ===")
for name, df in [("orders", orders), ("order_items", order_items),
                  ("products", products), ("customers", customers)]:
    nulls = df.isnull().sum().sum()
    dupes = df.duplicated().sum()
    print(f"{name:15s} | rows={len(df):>7,} | nulls={nulls:>4} | dupes={dupes:>4}")

# sanity check: negative prices / zero quantities
bad_prices = (order_items["unit_price"] <= 0).sum()
bad_qty = (order_items["quantity"] <= 0).sum()
print(f"\nInvalid prices: {bad_prices}, invalid quantities: {bad_qty}")

# ---------------------------------------------------------------------------
# JOIN INTO AN ANALYSIS-READY TABLE
# ---------------------------------------------------------------------------
completed = orders[orders["status"] == "completed"].copy()
line_level = completed.merge(order_items, on="order_id").merge(
    products[["product_id", "category", "product_name"]], on="product_id"
)
line_level["line_revenue"] = line_level["quantity"] * line_level["unit_price"]

order_level = (
    line_level.groupby(["order_id", "customer_id", "order_date", "region", "acquisition_channel"])
    .agg(order_revenue=("line_revenue", "sum"))
    .reset_index()
)
order_level.to_csv("/home/claude/retail-analytics-project/outputs/order_level_clean.csv", index=False)

print(f"\nCompleted orders: {len(completed):,} / {len(orders):,} "
      f"({len(completed)/len(orders):.1%})")
print(f"Total revenue: ${order_level['order_revenue'].sum():,.0f}")
print(f"Average order value: ${order_level['order_revenue'].mean():.2f}")

# ---------------------------------------------------------------------------
# CHART 1: Monthly revenue trend
# ---------------------------------------------------------------------------
monthly = order_level.set_index("order_date").resample("MS")["order_revenue"].sum()
fig, ax = plt.subplots(figsize=(10, 5))
monthly.plot(ax=ax, marker="o", linewidth=2, color="#2b6777")
ax.set_title("Monthly Revenue Trend — UrbanCart (2024–2025)", fontsize=14, fontweight="bold")
ax.set_xlabel("")
ax.set_ylabel("Revenue ($)")
ax.yaxis.set_major_formatter(lambda x, _: f"${x/1000:.0f}K")
plt.tight_layout()
plt.savefig(VIZ + "01_monthly_revenue_trend.png", dpi=150)
plt.close()

# ---------------------------------------------------------------------------
# CHART 2: Revenue by category
# ---------------------------------------------------------------------------
cat_rev = line_level.groupby("category")["line_revenue"].sum().sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(9, 5))
cat_rev.plot(kind="barh", ax=ax, color="#c94277")
ax.set_title("Total Revenue by Product Category", fontsize=14, fontweight="bold")
ax.set_xlabel("Revenue ($)")
ax.xaxis.set_major_formatter(lambda x, _: f"${x/1000:.0f}K")
plt.tight_layout()
plt.savefig(VIZ + "02_revenue_by_category.png", dpi=150)
plt.close()

# ---------------------------------------------------------------------------
# CHART 3: Revenue by region and acquisition channel (heatmap)
# ---------------------------------------------------------------------------
pivot = order_level.pivot_table(
    index="region", columns="acquisition_channel", values="order_revenue", aggfunc="sum"
)
fig, ax = plt.subplots(figsize=(9, 5))
sns.heatmap(pivot / 1000, annot=True, fmt=".0f", cmap="YlGnBu", ax=ax,
            cbar_kws={"label": "Revenue ($K)"})
ax.set_title("Revenue ($K) by Region × Acquisition Channel", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(VIZ + "03_region_channel_heatmap.png", dpi=150)
plt.close()

print("\nSaved 3 charts to /visuals and cleaned order-level table to /outputs.")
