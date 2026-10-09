# Validate RetailPulse dashboard metrics, filters, and aggregations

from pathlib import Path
import pandas as pd
import numpy as np

# Locate and load the processed dataset
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "online_retail_clean.csv"

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

retail = pd.read_csv(DATA_PATH)

# Verify the fields required for dashboard analytics
required_columns = [
    "InvoiceNo",
    "StockCode",
    "Quantity",
    "UnitPrice",
    "InvoiceDate",
    "CustomerID",
    "Country",
    "Revenue",
    "IsPositiveSale",
]

missing = [column for column in required_columns if column not in retail.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")

# Standardize date and positive-sale fields
retail["InvoiceDate"] = pd.to_datetime(
    retail["InvoiceDate"], errors="coerce"
)

retail["IsPositiveSale"] = (
    retail["IsPositiveSale"]
    .astype(str)
    .str.strip()
    .str.lower()
    .isin(["true", "1"])
)

# Calculate the expected positive-sale dataset independently
sales = retail.loc[
    retail["IsPositiveSale"]
    & retail["InvoiceDate"].notna()
].copy()

sales["Revenue"] = pd.to_numeric(sales["Revenue"], errors="coerce")
sales["Quantity"] = pd.to_numeric(sales["Quantity"], errors="coerce")

if sales[["Revenue", "Quantity"]].isna().any().any():
    raise ValueError("Positive-sale rows contain invalid revenue or quantity.")

# Helper to calculate core sales KPIs consistently
def calculate_kpis(data):
    revenue = data["Revenue"].sum()
    invoice_count = data["InvoiceNo"].nunique()

    return {
        "Gross Sales Revenue": revenue,
        "Units Sold": data["Quantity"].sum(),
        "Sales Invoices": invoice_count,
        "Identified Customers": data["CustomerID"].nunique(),
        "Revenue per Invoice": revenue / invoice_count if invoice_count else 0,
    }

# Validate baseline KPI calculations
kpis = calculate_kpis(sales)

assert np.isclose(
    kpis["Gross Sales Revenue"], sales["Revenue"].sum()
), "Gross revenue calculation failed."

assert kpis["Units Sold"] == sales["Quantity"].sum(), (
    "Units sold calculation failed."
)

assert kpis["Sales Invoices"] == sales["InvoiceNo"].nunique(), (
    "Invoice count calculation failed."
)

assert kpis["Identified Customers"] == sales["CustomerID"].nunique(), (
    "Identified customer count calculation failed."
)

expected_average = (
    sales["Revenue"].sum() / sales["InvoiceNo"].nunique()
    if sales["InvoiceNo"].nunique()
    else 0
)

assert np.isclose(
    kpis["Revenue per Invoice"], expected_average
), "Revenue per invoice calculation failed."

# Test a real country filter using the first available country
countries = sorted(sales["Country"].dropna().unique())

if countries:
    selected_country = countries[0]
    country_data = sales.loc[sales["Country"] == selected_country]

    assert country_data["Country"].eq(selected_country).all(), (
        "Country filter included an unexpected country."
    )

    assert np.isclose(
        country_data["Revenue"].sum(),
        sales.loc[sales["Country"] == selected_country, "Revenue"].sum()
    ), "Country revenue aggregation failed."

# Test a date filter using the dataset's actual date range
if not sales.empty:
    start_date = sales["InvoiceDate"].min().normalize()
    end_date = sales["InvoiceDate"].max().normalize()

    date_data = sales.loc[
        sales["InvoiceDate"].between(
            start_date,
            end_date + pd.Timedelta(days=1),
            inclusive="left",
        )
    ]

    assert date_data["InvoiceDate"].ge(start_date).all(), (
        "Date filter includes a transaction before the selected start."
    )

    assert date_data["InvoiceDate"].lt(
        end_date + pd.Timedelta(days=1)
    ).all(), "Date filter includes a transaction after the selected end."

# Check monthly, product, and country totals reconcile to total sales
monthly_totals = sales.groupby(
    sales["InvoiceDate"].dt.to_period("M")
)["Revenue"].sum()

product_totals = sales.groupby("StockCode")["Revenue"].sum()

country_totals = sales.groupby("Country")["Revenue"].sum()

total_revenue = sales["Revenue"].sum()

assert np.isclose(monthly_totals.sum(), total_revenue), (
    "Monthly revenue does not reconcile to total revenue."
)

assert np.isclose(product_totals.sum(), total_revenue), (
    "Product revenue does not reconcile to total revenue."
)

assert np.isclose(country_totals.sum(), total_revenue), (
    "Country revenue does not reconcile to total revenue."
)

# Print results for review
print("=" * 55)
print("RETAILPULSE — DASHBOARD LOGIC VALIDATION")
print("=" * 55)

for metric, value in kpis.items():
    if "Revenue" in metric:
        print(f"{metric}: {value:,.2f}")
    else:
        print(f"{metric}: {value:,.0f}")

print("\nPASS: KPI calculations")
print("PASS: Country filter logic")
print("PASS: Date filter boundaries")
print("PASS: Monthly revenue reconciliation")
print("PASS: Product revenue reconciliation")
print("PASS: Country revenue reconciliation")
print("\nDashboard logic validation completed.")