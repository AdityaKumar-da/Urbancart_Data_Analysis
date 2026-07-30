-- analysis_queries.sql
-- Core business-question queries against the UrbanCart database.
-- Demonstrates: JOINs, CTEs, window functions, subqueries, aggregation,
-- date functions, and conditional logic.

-- ============================================================
-- Q1. Monthly revenue trend + month-over-month growth
-- ============================================================
WITH monthly_revenue AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS order_month,
        SUM(oi.quantity * oi.unit_price) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY 1
)
SELECT
    order_month,
    revenue,
    ROUND(revenue - LAG(revenue) OVER (ORDER BY order_month), 2) AS revenue_change,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY order_month))
        / NULLIF(LAG(revenue) OVER (ORDER BY order_month), 0), 1
    ) AS pct_change
FROM monthly_revenue
ORDER BY order_month;


-- ============================================================
-- Q2. Revenue and margin by product category
-- ============================================================
SELECT
    p.category,
    COUNT(DISTINCT oi.order_id) AS orders_containing_category,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
    ROUND(SUM(oi.quantity * (oi.unit_price - oi.unit_cost)), 2) AS gross_profit,
    ROUND(100.0 * SUM(oi.quantity * (oi.unit_price - oi.unit_cost))
          / NULLIF(SUM(oi.quantity * oi.unit_price), 0), 1) AS margin_pct
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN orders o ON o.order_id = oi.order_id
WHERE o.status = 'completed'
GROUP BY p.category
ORDER BY revenue DESC;


-- ============================================================
-- Q3. RFM inputs per customer (Recency, Frequency, Monetary)
--     Recency measured in days before the dataset's last order date.
-- ============================================================
WITH order_value AS (
    SELECT
        o.customer_id,
        o.order_id,
        o.order_date,
        SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY o.customer_id, o.order_id, o.order_date
),
last_date AS (
    SELECT MAX(order_date) AS max_date FROM order_value
)
SELECT
    ov.customer_id,
    CAST(julianday((SELECT max_date FROM last_date)) - julianday(MAX(ov.order_date)) AS INTEGER) AS recency_days,
    COUNT(*) AS frequency,
    ROUND(SUM(ov.order_total), 2) AS monetary
FROM order_value ov
GROUP BY ov.customer_id
ORDER BY monetary DESC;


-- ============================================================
-- Q4. Customer lifetime rank within each region (window function)
-- ============================================================
WITH customer_totals AS (
    SELECT
        c.customer_id,
        c.region,
        SUM(oi.quantity * oi.unit_price) AS lifetime_value
    FROM customers c
    JOIN orders o ON o.customer_id = c.customer_id AND o.status = 'completed'
    JOIN order_items oi ON oi.order_id = o.order_id
    GROUP BY c.customer_id, c.region
),
ranked AS (
    SELECT
        customer_id,
        region,
        lifetime_value,
        RANK() OVER (PARTITION BY region ORDER BY lifetime_value DESC) AS region_rank
    FROM customer_totals
)
-- Some SQL engines (Snowflake, DuckDB, BigQuery) support QUALIFY region_rank <= 5
-- directly instead of this wrapping subquery. Kept portable here for SQLite.
SELECT *
FROM ranked
WHERE region_rank <= 5
ORDER BY region, region_rank;


-- ============================================================
-- Q5. Cohort retention: % of each signup-month cohort still ordering
--     in subsequent months (subquery + self join pattern)
-- ============================================================
WITH cohort AS (
    SELECT
        customer_id,
        strftime('%Y-%m', signup_date) AS cohort_month
    FROM customers
),
activity AS (
    SELECT DISTINCT
        customer_id,
        strftime('%Y-%m', order_date) AS activity_month
    FROM orders
    WHERE status = 'completed'
)
SELECT
    c.cohort_month,
    a.activity_month,
    COUNT(DISTINCT a.customer_id) AS active_customers
FROM cohort c
JOIN activity a ON a.customer_id = c.customer_id
WHERE a.activity_month >= c.cohort_month
GROUP BY c.cohort_month, a.activity_month
ORDER BY c.cohort_month, a.activity_month;


-- ============================================================
-- Q6. Customers who ordered in 2024 but NOT in 2025 (churn candidates)
--     Correlated subquery / NOT EXISTS pattern
-- ============================================================
SELECT DISTINCT c.customer_id, c.region, c.acquisition_channel
FROM customers c
WHERE EXISTS (
    SELECT 1 FROM orders o
    WHERE o.customer_id = c.customer_id
      AND strftime('%Y', o.order_date) = '2024'
      AND o.status = 'completed'
)
AND NOT EXISTS (
    SELECT 1 FROM orders o
    WHERE o.customer_id = c.customer_id
      AND strftime('%Y', o.order_date) = '2025'
      AND o.status = 'completed'
);


-- ============================================================
-- Q7. A/B test raw conversion summary (used as input to Python stats test)
-- ============================================================
SELECT
    grp,
    COUNT(*) AS n,
    SUM(converted) AS conversions,
    ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate_pct,
    ROUND(AVG(order_value), 2) AS avg_order_value_incl_zero
FROM ab_test_campaign
GROUP BY grp;
