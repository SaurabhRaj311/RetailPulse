# cspell:disable-file
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Configure the page before rendering dashboard elements
st.set_page_config(
    page_title="RetailPulse | Retail Intelligence",
    page_icon="📊",
    layout="wide",
)

# Apply consistent visual styling to the RetailPulse dashboard
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }

    [data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 14px;
        border-radius: 10px;
    }

    h1, h2, h3 {
        letter-spacing: -0.3px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Create sidebar navigation for the RetailPulse dashboard
st.sidebar.title("RetailPulse")
st.sidebar.caption("Retail Analytics Platform")

dashboard_page = st.sidebar.radio(
    "Navigate",
    [
        "Executive Overview",
        "Product & Country Analysis",
        "Customer Intelligence",
        "Business Recommendations",
    ],
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "online_retail_clean.csv"

# Load data function
@st.cache_data
def load_data():
    sales_df = pd.read_csv(DATA_PATH)
    
    # Standardize Date formats
    if 'InvoiceDate' in sales_df.columns:
        sales_df['InvoiceDate'] = pd.to_datetime(sales_df['InvoiceDate'])
        sales_df['YearMonth'] = sales_df['InvoiceDate'].dt.to_period('M').astype(str)

    # Standardize column names for app compatibility
    if 'Invoice' in sales_df.columns and 'InvoiceNo' not in sales_df.columns:
        sales_df['InvoiceNo'] = sales_df['Invoice']
    elif 'InvoiceNo' in sales_df.columns and 'Invoice' not in sales_df.columns:
        sales_df['Invoice'] = sales_df['InvoiceNo']

    # Standardize Revenue / GrossRevenue
    if 'GrossRevenue' not in sales_df.columns:
        if 'TotalAmount' in sales_df.columns:
            sales_df['GrossRevenue'] = sales_df['TotalAmount']
        elif 'UnitPrice' in sales_df.columns and 'Quantity' in sales_df.columns:
            sales_df['GrossRevenue'] = sales_df['Quantity'] * sales_df['UnitPrice']
            
    if 'Revenue' not in sales_df.columns and 'GrossRevenue' in sales_df.columns:
        sales_df['Revenue'] = sales_df['GrossRevenue']

    return sales_df

retail = load_data()

# Sidebar filters
st.sidebar.header("Filter Options")

min_date = retail['InvoiceDate'].min().date()
max_date = retail['InvoiceDate'].max().date()

start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

all_countries = sorted(retail['Country'].dropna().unique().tolist())
selected_countries = st.sidebar.multiselect(
    "Select Countries",
    options=all_countries,
    default=all_countries
)

# Apply filters
filtered_sales = retail[
    (retail['InvoiceDate'].dt.date >= start_date) &
    (retail['InvoiceDate'].dt.date <= end_date) &
    (retail['Country'].isin(selected_countries))
]

# Calculate core metrics
gross_revenue = filtered_sales['Revenue'].sum() if 'Revenue' in filtered_sales.columns else 0
units_sold = filtered_sales['Quantity'].sum() if 'Quantity' in filtered_sales.columns else 0
invoice_count = filtered_sales['InvoiceNo'].nunique() if 'InvoiceNo' in filtered_sales.columns else 0
customer_count = filtered_sales['CustomerID'].dropna().nunique() if 'CustomerID' in filtered_sales.columns else 0
average_order_value = gross_revenue / invoice_count if invoice_count > 0 else 0

# Dashboard Title & Header
st.title("RetailPulse | Executive Sales Dashboard")
st.markdown("Interactive analysis of customer behavior, revenue growth, and geographic expansion.")

# Executive Overview Metrics
st.subheader("Executive Overview")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Gross Revenue", f"£{gross_revenue:,.2f}")
col2.metric("Units Sold", f"{units_sold:,.0f}")
col3.metric("Sales Invoices", f"{invoice_count:,.0f}")
col4.metric("Identified Customers", f"{customer_count:,.0f}")
col5.metric("Revenue per Invoice", f"£{average_order_value:,.2f}")

st.divider()

# Monthly Sales Trend & Comparison
monthly = filtered_sales.groupby('YearMonth').agg(
    GrossRevenue=('Revenue', 'sum'),
    Quantity=('Quantity', 'sum'),
    InvoiceNo=('InvoiceNo', 'nunique')
).reset_index()

# Compare the latest observed month with the preceding observed month
monthly["PreviousMonthRevenue"] = monthly["GrossRevenue"].shift(1)

monthly["RevenueChangePct"] = (
    (
        monthly["GrossRevenue"] - monthly["PreviousMonthRevenue"]
    )
    / monthly["PreviousMonthRevenue"].where(
        monthly["PreviousMonthRevenue"] != 0
    )
    * 100
)

if len(monthly) >= 2:
    latest_month = monthly.iloc[-1]
    previous_month = monthly.iloc[-2]

    change_pct = latest_month["RevenueChangePct"]

    st.subheader("Monthly Revenue Comparison")

    compare_col1, compare_col2, compare_col3 = st.columns(3)

    compare_col1.metric(
        "Latest Month",
        latest_month["YearMonth"],
    )

    compare_col2.metric(
        "Latest Month Revenue",
        f"£{latest_month['GrossRevenue']:,.2f}",
    )

    if pd.notna(change_pct):
        compare_col3.metric(
            "Change vs Previous Observed Month",
            f"{change_pct:+.1f}%",
        )
    else:
        compare_col3.metric(
            "Change vs Previous Observed Month",
            "Not available",
        )

    st.caption(
        f"Comparison: {previous_month['YearMonth']} to "
        f"{latest_month['YearMonth']}. This compares the latest two "
        "months available under the current filters."
    )

# Plot monthly gross sales revenue
monthly_chart = px.line(
    monthly,
    x="YearMonth",
    y="GrossRevenue",
    markers=True,
    title="Gross Sales Revenue by Month",
    labels={
        "YearMonth": "Month",
        "GrossRevenue": "Gross Revenue (£)",
    },
)

st.plotly_chart(monthly_chart)

# Product & Country Performance
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Top 10 Products by Revenue")
    desc_col = 'Description' if 'Description' in filtered_sales.columns else 'StockCode'
    top_products = filtered_sales.groupby(desc_col)['Revenue'].sum().reset_index()
    top_products = top_products.sort_values(by='Revenue', ascending=False).head(10)
    fig_products = px.bar(
        top_products,
        x='Revenue',
        y=desc_col,
        orientation='h',
        title="Top 10 Products",
        labels={'Revenue': 'Revenue (£)', desc_col: 'Product'}
    )
    fig_products.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_products)

with col_right:
    st.subheader("Top 10 Countries by Revenue")
    top_countries = filtered_sales.groupby('Country')['Revenue'].sum().reset_index()
    top_countries = top_countries.sort_values(by='Revenue', ascending=False).head(10)
    fig_countries = px.bar(
        top_countries,
        x='Revenue',
        y='Country',
        orientation='h',
        title="Top 10 Countries",
        labels={'Revenue': 'Revenue (£)', 'Country': 'Country'}
    )
    fig_countries.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_countries)

st.divider()

# Country Summary Data & Export
st.subheader("Country Summary Data")
country_summary = filtered_sales.groupby('Country').agg({
    'Revenue': 'sum',
    'Quantity': 'sum',
    'InvoiceNo': 'nunique',
    'CustomerID': 'nunique'
}).reset_index()

with st.expander("View country summary data"):
    st.dataframe(country_summary)

st.subheader("Export Data")
csv_data = filtered_sales.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download Filtered Sales CSV",
    data=csv_data,
    file_name="retailpulse_filtered_sales.csv",
    mime="text/csv"
)

# Prepare reusable RFM segmentation and cohort retention calculations
def build_customer_analytics(data):
    # Keep only positive-sales transactions with identifiable customers
    customer_sales = data.loc[
        (data["Quantity"] > 0)
        & (data["UnitPrice"] > 0)
        & data["CustomerID"].notna()
    ].copy()

    if customer_sales.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Aggregate product lines into customer invoices
    invoices = (
        customer_sales.groupby(
            ["CustomerID", "InvoiceNo"], as_index=False
        )
        .agg(
            OrderValue=("Revenue", "sum"),
            OrderDate=("InvoiceDate", "min"),
        )
    )

    # Use one day after the latest dataset transaction as the reference date
    reference_date = data["InvoiceDate"].max().normalize() + pd.Timedelta(days=1)

    # Calculate RFM metrics for each customer
    rfm = (
        invoices.groupby("CustomerID", as_index=False)
        .agg(
            LastPurchaseDate=("OrderDate", "max"),
            Frequency=("InvoiceNo", "nunique"),
            Monetary=("OrderValue", "sum"),
        )
    )

    rfm["Recency"] = (
        reference_date - rfm["LastPurchaseDate"].dt.normalize()
    ).dt.days

    # Assign relative quintile scores, handling tied values
    rfm["R_Score"] = pd.qcut(
        rfm["Recency"].rank(method="first", ascending=True),
        q=5,
        labels=[5, 4, 3, 2, 1],
    ).astype(int)

    rfm["F_Score"] = pd.qcut(
        rfm["Frequency"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    rfm["M_Score"] = pd.qcut(
        rfm["Monetary"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    # Convert RFM scores into actionable business segments
    def assign_segment(row):
        r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]

        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        if r >= 3 and f >= 4:
            return "Loyal Customers"
        if r >= 4 and f >= 2 and m >= 3:
            return "Potential Loyalists"
        if r >= 4 and f == 1:
            return "Recent Customers"
        if r <= 2 and f >= 4 and m >= 3:
            return "At Risk"
        if r <= 2 and f <= 2 and m <= 2:
            return "Lost / Low Engagement"
        if r <= 2:
            return "Needs Attention"
        return "Regular Customers"

    rfm["CustomerSegment"] = rfm.apply(assign_segment, axis=1)

    # Summarize customer counts and revenue by segment
    segment_summary = (
        rfm.groupby("CustomerSegment", as_index=False)
        .agg(
            CustomerCount=("CustomerID", "nunique"),
            TotalRevenue=("Monetary", "sum"),
            AverageRecencyDays=("Recency", "mean"),
            AverageFrequency=("Frequency", "mean"),
        )
    )

    segment_summary["CustomerSharePct"] = (
        segment_summary["CustomerCount"] / len(rfm) * 100
    )
    segment_summary["RevenueSharePct"] = (
        segment_summary["TotalRevenue"] / rfm["Monetary"].sum() * 100
    )

    # Identify each customer's first purchase month
    invoices["InvoiceMonth"] = invoices["OrderDate"].dt.to_period("M")
    first_month = invoices.groupby("CustomerID")["InvoiceMonth"].min()
    invoices["CohortMonth"] = invoices["CustomerID"].map(first_month)

    # Calculate the number of months since cohort entry
    invoices["CohortIndex"] = (
        (invoices["InvoiceMonth"].dt.year - invoices["CohortMonth"].dt.year) * 12
        + invoices["InvoiceMonth"].dt.month
        - invoices["CohortMonth"].dt.month
    )

    # Count unique active customers for each cohort and cohort month
    cohort_counts = invoices.pivot_table(
        index="CohortMonth",
        columns="CohortIndex",
        values="CustomerID",
        aggfunc="nunique",
    )

    # Convert counts into retention percentages
    if 0 in cohort_counts.columns:
        cohort_sizes = cohort_counts[0]
        cohort_retention = cohort_counts.div(cohort_sizes, axis=0) * 100
        cohort_retention = cohort_retention.round(1)
    else:
        cohort_retention = pd.DataFrame()

    return rfm, segment_summary, cohort_retention


# Add RFM customer segmentation and cohort retention views
st.divider()
st.header("Advanced Customer Intelligence")

rfm, segment_summary, cohort_retention = build_customer_analytics(retail)

if rfm.empty:
    st.warning("There are no identifiable positive-sales customers to analyze.")
else:
    # Display high-level customer intelligence metrics
    champion_count = int(
        rfm["CustomerSegment"].eq("Champions").sum()
    )
    at_risk_count = int(
        rfm["CustomerSegment"].isin(
            ["At Risk", "Needs Attention"]
        ).sum()
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Analyzed Customers", f"{len(rfm):,}")
    col2.metric("Champions", f"{champion_count:,}")
    col3.metric("Customers Needing Attention", f"{at_risk_count:,}")

    # Let the user explore individual RFM segments
    st.subheader("RFM Segment Explorer")

    available_segments = sorted(rfm["CustomerSegment"].unique())
    selected_segment = st.selectbox(
        "Choose a customer segment",
        options=available_segments,
    )

    selected_customers = rfm.loc[
        rfm["CustomerSegment"] == selected_segment
    ].sort_values("Monetary", ascending=False)

    segment_metrics = segment_summary.loc[
        segment_summary["CustomerSegment"] == selected_segment
    ]

    if not segment_metrics.empty:
        segment_row = segment_metrics.iloc[0]
        a, b, c = st.columns(3)
        a.metric("Customers", f"{int(segment_row['CustomerCount']):,}")
        b.metric("Revenue", f"£{segment_row['TotalRevenue']:,.2f}")
        c.metric("Revenue Share", f"{segment_row['RevenueSharePct']:.1f}%")

    st.dataframe(
        selected_customers[
            [
                "CustomerID",
                "Recency",
                "Frequency",
                "Monetary",
                "R_Score",
                "F_Score",
                "M_Score",
                "CustomerSegment",
            ]
        ],
        hide_index=True,
    )

    # Plot customer counts by RFM segment
    st.subheader("Customer Segment Distribution")
    segment_chart = px.bar(
        segment_summary.sort_values("CustomerCount", ascending=True),
        x="CustomerCount",
        y="CustomerSegment",
        orientation="h",
        title="Customers by RFM Segment",
        labels={
            "CustomerCount": "Customers",
            "CustomerSegment": "Segment",
        },
    )
    st.plotly_chart(segment_chart)

    # Plot the cohort retention heatmap
    st.subheader("Monthly Cohort Retention")

    if not cohort_retention.empty:
        cohort_display = cohort_retention.copy()
        cohort_display.index = cohort_display.index.astype(str)
        cohort_display.columns = [
            f"Month {int(column)}" for column in cohort_display.columns
        ]

        retention_chart = px.imshow(
            cohort_display,
            text_auto=".0f",
            aspect="auto",
            color_continuous_scale="YlGnBu",
            zmin=0,
            zmax=100,
            labels={
                "x": "Months Since First Purchase",
                "y": "First Purchase Cohort",
                "color": "Retention (%)",
            },
            title="Customer Cohort Retention (%)",
        )
        st.plotly_chart(retention_chart)
        st.caption(
            "Month 0 represents each cohort's initial purchase month. "
            "Blank future periods are unavailable observations, not zero retention."
        )
    else:
        st.info("Cohort retention could not be calculated for this dataset.")

# Generate data-driven business recommendations for the selected dataset
st.divider()
st.header("Business Recommendations")

recommendations = []

# Recommend a product review based on revenue concentration
if not filtered_sales.empty:
    product_revenue = (
        filtered_sales.groupby("StockCode")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    total_product_revenue = product_revenue.sum()

    if total_product_revenue > 0:
        top_product_share = (
            product_revenue.head(5).sum() / total_product_revenue * 100
        )

        if top_product_share >= 50:
            recommendations.append(
                (
                    "Review product concentration",
                    f"The five highest-revenue products contribute "
                    f"{top_product_share:.1f}% of filtered product revenue. "
                    "Review stock availability and investigate the risk of "
                    "depending heavily on a small number of products."
                )
            )
        else:
            recommendations.append(
                (
                    "Maintain product visibility",
                    f"The five highest-revenue products contribute "
                    f"{top_product_share:.1f}% of filtered product revenue. "
                    "Monitor product-level trends to identify changing demand."
                )
            )

# Recommend customer retention action using the full historical RFM results
if "rfm" in globals() and not rfm.empty:
    at_risk_customers = rfm.loc[
        rfm["CustomerSegment"].isin(["At Risk", "Needs Attention"])
    ]

    at_risk_revenue = at_risk_customers["Monetary"].sum()
    total_identified_revenue = rfm["Monetary"].sum()

    at_risk_revenue_share = (
        at_risk_revenue / total_identified_revenue * 100
        if total_identified_revenue > 0
        else 0
    )

    recommendations.append(
        (
            "Prioritize customer retention",
            f"{len(at_risk_customers):,} customers fall into the "
            f"'At Risk' or 'Needs Attention' segments. Together, they "
            f"account for £{at_risk_revenue:,.2f}, or "
            f"{at_risk_revenue_share:.1f}% of identified-customer revenue. "
            "Consider testing targeted re-engagement campaigns."
        )
    )

# Recommend investigation of geographic performance
if not filtered_sales.empty:
    country_revenue = (
        filtered_sales.groupby("Country")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    if len(country_revenue) > 1:
        leading_country = country_revenue.index[0]
        leading_share = (
            country_revenue.iloc[0] / country_revenue.sum() * 100
            if country_revenue.sum() > 0
            else 0
        )

        recommendations.append(
            (
                "Review geographic concentration",
                f"{leading_country} contributes {leading_share:.1f}% of "
                "filtered gross sales revenue. Assess market opportunities "
                "and the business implications of geographic concentration."
            )
        )

# Display recommendations in a readable format
if recommendations:
    for title, description in recommendations:
        with st.container(border=True):
            st.subheader(title)
            st.write(description)

    st.caption(
        "Recommendations are rule-based prompts for investigation, "
        "not proof of causation or guaranteed business outcomes."
    )
else:
    st.info(
        "No recommendations could be generated for the current selection."
    )

# Explain the dataset, metric definitions, and analysis limitations
# cspell:disable
st.divider()
with st.expander("About RetailPulse and its methodology"):
    st.markdown(
        """
        **Project:** RetailPulse — Retail Analytics & Customer Intelligence

        **Dataset:** UCI Online Retail historical transaction data.

        **Sales revenue:** Calculated from positive-quantity lines with
        positive unit prices. It is reported as gross sales revenue,
        not net revenue after returns.

        **Identifiable customers:** Customer metrics exclude rows with
        missing customer IDs.

        **RFM segmentation:** Customers are scored using relative
        quintiles of recency, frequency, and monetary value.

        **Cohort retention:** Measures whether a customer made a
        qualifying purchase during a later calendar month.

        **Limitations:** This is historical data. Patterns indicate
        associations and opportunities for investigation; they do not
        establish the causes of customer behaviour.
        """
    )
# cspell:enable

st.caption("RetailPulse | Historical analysis of the UCI Online Retail dataset")