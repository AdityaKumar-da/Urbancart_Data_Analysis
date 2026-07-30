"""
01_generate_data.py
--------------------
Generates a realistic synthetic e-commerce dataset for "UrbanCart", a
mid-size online retailer. Data spans 18 months and includes seasonality,
customer churn patterns, regional variation, and a marketing A/B test.

Output (all in ../data/):
    customers.csv
    products.csv
    orders.csv
    order_items.csv
    ab_test_campaign.csv
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RNG = np.random.default_rng(42)
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 6, 30)
N_DAYS = (END_DATE - START_DATE).days

# ---------------------------------------------------------------------------
# 1. CUSTOMERS
# ---------------------------------------------------------------------------
N_CUSTOMERS = 4000
REGIONS = ["Northeast", "Midwest", "South", "West"]
CHANNELS = ["Organic Search", "Paid Social", "Email", "Referral", "Direct"]
CHANNEL_WEIGHTS = [0.32, 0.24, 0.14, 0.10, 0.20]

signup_offsets = RNG.integers(0, N_DAYS, size=N_CUSTOMERS)
customers = pd.DataFrame({
    "customer_id": [f"CUST{i:05d}" for i in range(1, N_CUSTOMERS + 1)],
    "signup_date": [START_DATE + timedelta(days=int(d)) for d in signup_offsets],
    "region": RNG.choice(REGIONS, size=N_CUSTOMERS, p=[0.27, 0.22, 0.31, 0.20]),
    "acquisition_channel": RNG.choice(CHANNELS, size=N_CUSTOMERS, p=CHANNEL_WEIGHTS),
})
# assign a latent "loyalty" score that drives purchase frequency & churn risk
customers["loyalty_score"] = np.clip(RNG.normal(0.5, 0.2, N_CUSTOMERS), 0.02, 0.98)
customers = customers.sort_values("signup_date").reset_index(drop=True)

# ---------------------------------------------------------------------------
# 2. PRODUCTS
# ---------------------------------------------------------------------------
CATEGORIES = {
    "Electronics":   (40, 500),
    "Home & Kitchen": (10, 150),
    "Apparel":        (12, 90),
    "Beauty":         (8, 60),
    "Sports & Outdoors": (15, 200),
    "Office":         (5, 80),
}
N_PRODUCTS = 150
prod_rows = []
pid = 1
for cat, (low, high) in CATEGORIES.items():
    n_in_cat = N_PRODUCTS // len(CATEGORIES)
    for _ in range(n_in_cat):
        price = round(RNG.uniform(low, high), 2)
        cost = round(price * RNG.uniform(0.4, 0.65), 2)  # margin 35-60%
        prod_rows.append({
            "product_id": f"PROD{pid:04d}",
            "category": cat,
            "unit_price": price,
            "unit_cost": cost,
        })
        pid += 1
products = pd.DataFrame(prod_rows)
products["product_name"] = products["category"].str.slice(0, 4).str.upper() + "-" + products["product_id"].str.slice(-4)

# ---------------------------------------------------------------------------
# 3. ORDERS + ORDER ITEMS
#    Purchase frequency driven by loyalty_score and seasonality (Nov/Dec spike,
#    July back-to-school bump). Customers churn (stop ordering) at different rates.
# ---------------------------------------------------------------------------
order_rows = []
item_rows = []
order_id_counter = 1

def seasonality_multiplier(date):
    month = date.month
    if month in (11, 12):
        return 1.8          # holiday spike
    if month in (7, 8):
        return 1.15         # back to school
    if month in (1, 2):
        return 0.75         # post-holiday lull
    return 1.0

for _, cust in customers.iterrows():
    days_active = (END_DATE - cust["signup_date"]).days
    if days_active <= 0:
        continue
    # base expected number of orders over lifetime, scaled by loyalty
    expected_orders = max(1, RNG.poisson(2 + cust["loyalty_score"] * 10))
    # simulate a churn point: higher loyalty -> less likely to churn early
    churn_day = RNG.integers(low=30, high=days_active + 30) if RNG.random() > cust["loyalty_score"] else RNG.integers(30, max(60, days_active // 2 + 30))
    active_window = min(days_active, churn_day)

    order_days = sorted(RNG.integers(0, max(active_window, 1), size=expected_orders))
    for od in order_days:
        order_date = cust["signup_date"] + timedelta(days=int(od))
        if order_date > END_DATE:
            continue
        mult = seasonality_multiplier(order_date)
        if RNG.random() > min(mult, 1.0) * 0.55 + 0.25:
            continue  # seasonality thins out orders in low season

        order_id = f"ORD{order_id_counter:06d}"
        order_id_counter += 1
        status = RNG.choice(["completed", "completed", "completed", "returned", "cancelled"],
                             p=[0.86, 0.0, 0.0, 0.08, 0.06])
        order_rows.append({
            "order_id": order_id,
            "customer_id": cust["customer_id"],
            "order_date": order_date.date().isoformat(),
            "status": status,
            "region": cust["region"],
            "acquisition_channel": cust["acquisition_channel"],
        })

        n_items = RNG.integers(1, 5)
        chosen_products = products.sample(n=n_items, random_state=RNG.integers(0, 1_000_000))
        for _, prod in chosen_products.iterrows():
            qty = RNG.integers(1, 4)
            item_rows.append({
                "order_id": order_id,
                "product_id": prod["product_id"],
                "quantity": int(qty),
                "unit_price": prod["unit_price"],
                "unit_cost": prod["unit_cost"],
            })

orders = pd.DataFrame(order_rows)
order_items = pd.DataFrame(item_rows)

# ---------------------------------------------------------------------------
# 4. MARKETING A/B TEST
#    Simulates a subject-line experiment sent to a subset of customers.
#    Variant B (personalized subject line) has a real, modest lift.
# ---------------------------------------------------------------------------
ab_customers = customers.sample(n=1500, random_state=7).copy()
ab_customers["group"] = RNG.choice(["control", "variant"], size=len(ab_customers), p=[0.5, 0.5])

base_conv_rate = 0.084
lift = 0.021  # true lift for variant group
conv_prob = np.where(ab_customers["group"] == "control", base_conv_rate, base_conv_rate + lift)
ab_customers["converted"] = RNG.binomial(1, conv_prob)
ab_customers["order_value"] = np.where(
    ab_customers["converted"] == 1,
    np.round(RNG.gamma(shape=3.0, scale=18, size=len(ab_customers)) + 15, 2),
    0.0
)

ab_test = ab_customers[["customer_id", "group", "converted", "order_value"]].reset_index(drop=True)

# ---------------------------------------------------------------------------
# SAVE
# ---------------------------------------------------------------------------
customers.to_csv("/home/claude/retail-analytics-project/data/customers.csv", index=False)
products.to_csv("/home/claude/retail-analytics-project/data/products.csv", index=False)
orders.to_csv("/home/claude/retail-analytics-project/data/orders.csv", index=False)
order_items.to_csv("/home/claude/retail-analytics-project/data/order_items.csv", index=False)
ab_test.to_csv("/home/claude/retail-analytics-project/data/ab_test_campaign.csv", index=False)

print(f"Customers:   {len(customers):,}")
print(f"Products:    {len(products):,}")
print(f"Orders:      {len(orders):,}")
print(f"Order items: {len(order_items):,}")
print(f"AB test rows:{len(ab_test):,}")
