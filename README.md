# RetailPulse — Retail Analytics & Customer Intelligence Platform

RetailPulse is an end-to-end retail analytics project that transforms online transaction data into actionable business insights. It combines data cleaning, exploratory data analysis, SQL analytics, customer segmentation, cohort retention analysis, and an interactive Streamlit dashboard.

The project is designed to help retail teams understand sales performance, identify valuable customers, evaluate product and geographic performance, and explore potential customer-retention opportunities.

## Project Overview

RetailPulse analyzes historical online retail transactions and presents the results through an interactive, four-page dashboard.

### Dashboard Pages
* **Executive Overview:** Revenue KPIs, monthly sales trends, and month-over-month comparisons.
* **Product & Country Analysis:** Top-performing products, country-level sales performance, and revenue concentration.
* **Customer Intelligence:** RFM customer segmentation, customer-level analytics, and cohort retention.
* **Business Recommendations:** Data-driven observations, potential retention actions, and metric definitions.

## Business Questions

RetailPulse explores questions such as:
* How does sales revenue change over time?
* Which products and countries contribute the most revenue?
* How many invoices and units are associated with positive sales?
* Which identified customers have high purchase value or repeat-purchase behavior?
* Which customers may require retention attention?
* How does customer activity change across acquisition cohorts?
* Where might the business investigate opportunities to improve performance?

## Technology Stack

* **Python** — data processing and analytics
* **Pandas and NumPy** — data cleaning, transformation, and calculations
* **Matplotlib and Seaborn** — exploratory analysis and visualizations
* **Plotly** — interactive charts
* **SQL and SQLite** — relational queries and business analytics
* **Streamlit** — interactive dashboard
* **Jupyter Notebook** — analysis workflow and documentation
* **Git and GitHub** — version control and project sharing

## Dataset

**Source:** UCI Machine Learning Repository — Online Retail

The dataset contains historical transactions from a UK-based online retailer between December 2010 and December 2011.

The original dataset contains 541,909 transaction rows. The cleaning workflow removed 5,268 exact duplicate rows, leaving 536,641 rows before any analysis-specific filtering.

Important data characteristics include missing customer identifiers, cancellation invoices, negative quantities, and nonpositive unit prices. These are handled carefully rather than being indiscriminately removed.

## Data Processing and Analytics

The workflow includes:
1. Data inspection and quality assessment.
2. Duplicate removal and data-type standardization.
3. Transaction-level feature engineering and revenue calculation.
4. Exploratory analysis of monthly, product, and country performance.
5. SQL-based business analysis.
6. Customer-level purchase aggregation.
7. RFM scoring and rule-based customer segmentation.
8. Cohort-based customer retention analysis.
9. Interactive dashboard development.
10. Data-quality and dashboard-logic validation.

## Customer Intelligence

RFM analysis uses three dimensions:
* **Recency:** Time since a customer's most recent qualifying purchase.
* **Frequency:** Number of distinct qualifying purchase invoices.
* **Monetary:** Total value of qualifying purchases.

Customers are assigned rule-based segments such as Champions, Loyal Customers, Potential Loyalists, At Risk, and Needs Attention.

Cohort analysis groups customers by their first purchase month and tracks subsequent purchasing activity.

These segments are analytical indicators, not guaranteed predictions of future customer behavior.

## Data Definitions and Limitations

For the main sales analysis, a positive sale is defined as a transaction line with positive quantity and positive unit price.

Line revenue is calculated as:
$$\text{Revenue} = \text{Quantity} \times \text{UnitPrice}$$

Gross sales revenue is calculated from qualifying positive-sale lines. Revenue per invoice is calculated using qualifying positive-sale revenue divided by the number of distinct qualifying invoices.

Customer-level analysis excludes transactions without an identified CustomerID because individual purchase histories cannot be reliably attributed to unidentified customers.

Negative-quantity transactions may represent returns or other adjustments. They should not automatically be interpreted as confirmed customer returns, and gross sales revenue should not be confused with fully reconciled accounting revenue.

RFM and cohort results depend on the available historical data and the definitions used in the analysis.

## Project Structure

```text
RetailPulse/
├── dashboard/
│   └── app.py
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
│   ├── 01_data_understanding.ipynb
│   ├── 02_data_cleaning.ipynb
│   └── 03_exploratory_data_analysis.ipynb
├── reports/
├── sql/
│   └── 02_retail_analytics.sql
├── src/
│   ├── validate_data.py
│   └── validate_dashboard.py
├── .gitignore
├── requirements.txt
└── README.md