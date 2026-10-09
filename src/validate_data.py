# Validate the RetailPulse processed dataset and key business calculations

from pathlib import Path
import pandas as pd
import numpy as np

# Locate the project folder and processed dataset
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "online_retail_clean.csv"

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Processed dataset not found: {DATA_PATH}\n"
        "Run the data-cleaning notebook first."
    )

# Load the cleaned dataset
retail = pd.read_csv(DATA_PATH)

print("=" * 60)
print("RETAILPULSE — DATA QUALITY VALIDATION")
print("=" * 60)
print(f"Dataset rows: {len(retail):,}")
print(f"Dataset columns: {len(retail.columns)}")

# Define the columns required for the core analysis
required_columns = [
    "InvoiceNo",
    "StockCode",
    "Quantity",
    "UnitPrice",
    "InvoiceDate",
    "CustomerID",
    "Country",
    "Revenue",
    "IsCancellationInvoice",
    "IsNegativeQuantity",
    "IsPositiveSale",
]

# Collect validation results
results = []

def record_check(name, passed, detail):
    results.append((name, bool(passed), detail))
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}: {detail}")

# Check that all required columns exist
missing_columns = [
    column for column in required_columns
    if column not in retail.columns
]

record_check(
    "Required columns",
    len(missing_columns) == 0,
    "All required columns exist"
    if not missing_columns
    else f"Missing columns: {missing_columns}"
)

# Continue only if the dataset has the columns needed for validation
if missing_columns:
    raise SystemExit(
        "\nValidation stopped because required columns are missing."
    )

# Check exact duplicate rows
duplicate_count = int(retail.duplicated().sum())

record_check(
    "Exact duplicate rows",
    duplicate_count == 0,
    f"{duplicate_count:,} duplicate rows found"
)

# Check critical missing values
critical_columns = ["InvoiceNo", "Quantity", "UnitPrice", "InvoiceDate"]
missing_critical = int(retail[critical_columns].isna().sum().sum())

record_check(
    "Missing critical values",
    missing_critical == 0,
    f"{missing_critical:,} missing values across critical columns"
)

# Check that transaction dates can be parsed
parsed_dates = pd.to_datetime(retail["InvoiceDate"], errors="coerce")
invalid_dates = int(parsed_dates.isna().sum())

record_check(
    "Valid transaction dates",
    invalid_dates == 0,
    f"{invalid_dates:,} invalid or missing dates"
)

# Check numeric transaction fields
quantity = pd.to_numeric(retail["Quantity"], errors="coerce")
unit_price = pd.to_numeric(retail["UnitPrice"], errors="coerce")
revenue = pd.to_numeric(retail["Revenue"], errors="coerce")

numeric_values_valid = (
    quantity.notna().all()
    and unit_price.notna().all()
    and revenue.notna().all()
)

record_check(
    "Numeric transaction fields",
    numeric_values_valid,
    "Quantity, UnitPrice, and Revenue contain valid numeric values"
    if numeric_values_valid
    else "One or more numeric fields contain missing or invalid values"
)

# Verify that Revenue equals Quantity multiplied by UnitPrice
if numeric_values_valid:
    expected_revenue = quantity * unit_price
    revenue_matches = np.isclose(
        revenue.to_numpy(dtype=float),
        expected_revenue.to_numpy(dtype=float),
        rtol=1e-7,
        atol=1e-6,
        equal_nan=True,
    )
    revenue_mismatches = int((~revenue_matches).sum())
else:
    revenue_mismatches = -1

record_check(
    "Revenue calculation",
    revenue_mismatches == 0,
    "Revenue matches Quantity × UnitPrice on every row"
    if revenue_mismatches == 0
    else f"{revenue_mismatches:,} mismatched rows"
    if revenue_mismatches > 0
    else "Cannot verify until numeric fields are valid"
)

# Verify the positive-sale flag used in business analytics
if numeric_values_valid:
    expected_positive_sale = (quantity > 0) & (unit_price > 0)
    actual_positive_sale = (
        retail["IsPositiveSale"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1"])
    )
    positive_sale_mismatches = int(
        (expected_positive_sale != actual_positive_sale).sum()
    )
else:
    positive_sale_mismatches = -1

record_check(
    "Positive-sale flag",
    positive_sale_mismatches == 0,
    "IsPositiveSale matches the documented rule"
    if positive_sale_mismatches == 0
    else f"{positive_sale_mismatches:,} mismatched rows"
    if positive_sale_mismatches > 0
    else "Cannot verify until numeric fields are valid"
)

# Report important data characteristics without treating them as errors
print("\nDATA PROFILE")
print("-" * 60)
print(f"Missing CustomerID: {retail['CustomerID'].isna().sum():,}")
print(f"Negative-quantity rows: {(quantity < 0).sum():,}")
print(f"Nonpositive-price rows: {(unit_price <= 0).sum():,}")
print(f"Positive-sale rows: {(quantity.gt(0) & unit_price.gt(0)).sum():,}")
print(f"Distinct countries: {retail['Country'].nunique():,}")

# Summarize the validation outcome
failed_checks = [result for result in results if not result[1]]

print("\nVALIDATION SUMMARY")
print("-" * 60)
print(f"Checks passed: {len(results) - len(failed_checks)}/{len(results)}")

if failed_checks:
    print("Please investigate the failed checks before proceeding.")
    raise SystemExit(1)

print("All validation checks passed.")