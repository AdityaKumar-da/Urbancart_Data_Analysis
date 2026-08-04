[README.md](https://github.com/user-attachments/files/30704874/README.md)
# UrbanCart Analytics — End-to-End Retail Data Analysis

![Python](https://img.shields.io/badge/Python-pandas%20%7C%20numpy%20%7C%20scipy-blue)
![SQL](https://img.shields.io/badge/SQL-SQLite-lightgrey)
![Dashboard](https://img.shields.io/badge/Dashboard-Chart.js-orange)

A complete data-analyst portfolio project built on an 18-month synthetic e-commerce dataset (4,000 customers, 21.6K orders, 150 products). It walks through the full analyst workflow — data generation & cleaning, SQL analysis, statistical testing, customer segmentation, retention analysis, and an executive-facing interactive dashboard.

**[Open the interactive dashboard →](dashboard/index.html)**

---

## Contents

- [Why this project](#why-this-project)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [How to run it yourself](#how-to-run-it-yourself)
- [Key findings](#key-findings)
- [Notes on the data](#notes-on-the-data)

---

## Why this project

Most portfolio projects stop at "I made a chart." This one is built around five real business questions a retail analytics team gets asked, and answers each one with the right tool for the job — SQL for data extraction, Python for statistics and modeling, and a dashboard for communicating results to a non-technical stakeholder.

| Business question | Method | Skill demonstrated |
|---|---|---|
| Is revenue growing, and where's the seasonality? | SQL window functions + Python/matplotlib | Trend analysis, time-series aggregation |
| Which customers matter most? | RFM segmentation (SQL + Python) | Customer segmentation, quartile scoring |
| Are we losing customers, and when? | Cohort retention analysis | Cohort modeling, retention curves |
| Did the new email subject line actually work? | Two-proportion z-test | Hypothesis testing, statistical rigor |
| Which regions/channels underperform? | Pivot + heatmap | Cross-tabulation, data visualization |

---

## Tech stack

- **Python** (pandas, numpy, scipy, matplotlib, seaborn) — data generation, cleaning, statistics, charts
- **SQL** (SQLite) — schema design, joins, CTEs, window functions, subqueries
- **HTML/CSS/JS + Chart.js** — interactive dashboard
- **Statistics** — quartile-based segmentation, two-proportion z-test, confidence intervals

---

## Project structure

```
Urbancart_Data_Analysis/
├── data/
│   ├── customers.csv, products.csv, orders.csv, order_items.csv
│   ├── ab_test_campaign.csv
│   └── urbancart.db              # SQLite database (all tables loaded)
├── sql/
│   ├── schema.sql                 # table definitions + indexes
│   └── analysis_queries.sql       # 7 business-question queries
├── python/
│   ├── 01_generate_data.py        # synthetic data generator (seeded, reproducible)
│   ├── 02_data_cleaning_eda.py    # data quality checks + EDA charts
│   ├── 03_rfm_segmentation.py     # RFM customer segmentation
│   ├── 04_cohort_retention.py     # cohort retention analysis
│   └── 05_ab_test_analysis.py     # A/B test significance testing
├── visuals/                       # exported PNG charts (6 total)
├── outputs/                       # analysis result CSVs
└── dashboard/
    └── index.html                 # interactive dashboard (open directly in browser)
```

## How to run it yourself

```bash
pip install -r requirements.txt
cd python
python 01_generate_data.py          # generates data/*.csv
python 02_data_cleaning_eda.py      # cleans + produces charts 1-3
python 03_rfm_segmentation.py       # produces chart 4 + segment CSVs
python 04_cohort_retention.py       # produces chart 5 + retention CSV
python 05_ab_test_analysis.py       # produces chart 6 + test results CSV
```

To explore the SQL layer, open `data/urbancart.db` with any SQLite client (or run `sqlite3 data/urbancart.db < sql/schema.sql` to rebuild it) and run the queries in `sql/analysis_queries.sql`.

---

## Key findings

**1. Revenue grew ~17x over 18 months** — from $68K (Jan 2024) to a peak of $1.18M (Jun 2025) — driven mainly by the compounding repeat-customer base rather than seasonality alone, though Nov/Dec still runs ~24% above the rest of the year on average.

**2. Revenue is heavily concentrated in a small segment.** Champions (20% of customers) generate 31.7% of revenue. Combined with "Needs Attention" and "At Risk" customers — those who were valuable but have gone quiet — roughly 30% of the customer base sits on retention risk that's currently undifferentiated, since everyone gets the same lifecycle emails regardless of where they sit in the RFM matrix.

| Segment | % of customers | % of revenue | Avg. days since last order |
|---|---|---|---|
| Champions | 20.0% | 31.7% | 61 |
| Needs Attention | 19.0% | 22.4% | 214 |
| At Risk | 11.5% | 17.0% | 354 |
| Loyal Customers | 18.3% | 13.5% | 64 |
| Hibernating / Lost | 13.4% | 8.1% | 364 |
| Promising / New | 11.9% | 5.0% | 68 |

**3. Retention drops off sharply after month 1.** On average, ~64% of a signup cohort returns in month 1, falling to ~29% by month 3 and under 10% by month 8. The steepest drop is between month 1 and month 2 — the highest-leverage fix is likely a second-purchase incentive rather than long-term loyalty perks.

**4. The email subject-line A/B test was directionally positive but not statistically significant.** Personalized subject lines lifted conversion from 8.96% to 11.27% (+25.7% relative), but at n=1,500 (781 control / 719 variant) that's p=0.14 — above the 0.05 threshold, with a 95% CI of [-0.76%, +5.36%] that still includes zero.

**Recommendation:** extend the test to reach the ~3,000–4,000 customers per arm needed for adequate power before rolling out. Acting on this now risks shipping a change that doesn't actually move the needle.

**5. "Organic Search" and "Paid Social" are the strongest channels across every region**, while "Referral" consistently underperforms — a candidate for a referral-incentive redesign rather than more spend.

---

## Notes on the data

This is **synthetic data** generated with a seeded random process (see `python/01_generate_data.py`), so results are fully reproducible. It's designed to behave like real retail data — including messy, inconclusive results like the underpowered A/B test above — rather than being tuned to produce clean, impressive-looking numbers.

A hiring manager reading this should take the statistical honesty as the point: not every test wins, and knowing when *not* to act on a result is as much a part of the job as finding the lift in the first place.
