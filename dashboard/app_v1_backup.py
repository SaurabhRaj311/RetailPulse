import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Set page configuration
st.set_page_config(
    page_title="RetailPulse Dashboard",
    page_icon="📊",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "online_retail_clean.csv"

# Load data function
@st.cache_data
def load_data():
    sales_df = pd.read_csv(DATA_PATH)
    
    # Handle Date parsing
    if 'InvoiceDate' in sales_df.columns:
        sales_df['InvoiceDate'] = pd.to_datetime(sales_df['InvoiceDate'])
        sales_df['YearMonth'] = sales_df['InvoiceDate'].dt.to_period('M').astype(str)
    
    # Handle GrossRevenue missing column
    if 'GrossRevenue' not in sales_df.columns:
        if 'TotalAmount' in sales_df.columns:
            sales_df['GrossRevenue'] = sales_df['TotalAmount']
        elif 'UnitPrice' in sales_df.columns and 'Quantity' in sales_df.columns:
            sales_df['GrossRevenue'] = sales_df['Quantity'] * sales_df['UnitPrice']
        elif 'Price' in sales_df.columns and 'Quantity' in sales_df.columns:
            sales_df['GrossRevenue'] = sales_df['Quantity'] * sales_df['Price']

    # Ensure StockCode/Invoice/Country exist under expected names
    if 'InvoiceNo' in sales_df.columns and 'Invoice' not in sales_df.columns:
        sales_df['Invoice'] = sales_df['InvoiceNo']
        
    return sales_df

sales = load_data()

# Sidebar filters
st.sidebar.header("Filter Options")

min_date = sales['InvoiceDate'].min().date()
max_date = sales['InvoiceDate'].max().date()

start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

all_countries = sorted(sales['Country'].dropna().unique().tolist())
selected_countries = st.sidebar.multiselect(
    "Select Countries",
    options=all_countries,
    default=all_countries
)

# Apply filters
filtered_sales = sales[
    (sales['InvoiceDate'].dt.date >= start_date) &
    (sales['InvoiceDate'].dt.date <= end_date) &
    (sales['Country'].isin(selected_countries))
]

# Calculate core metrics
gross_revenue = filtered_sales['GrossRevenue'].sum() if 'GrossRevenue' in filtered_sales.columns else 0
units_sold = filtered_sales['Quantity'].sum() if 'Quantity' in filtered_sales.columns else 0
invoice_col = 'Invoice' if 'Invoice' in filtered_sales.columns else 'InvoiceNo'
invoice_count = filtered_sales[invoice_col].nunique() if invoice_col in filtered_sales.columns else 0
customer_count = filtered_sales['CustomerID'].dropna().nunique() if 'CustomerID' in filtered_sales.columns else 0
average_order_value = gross_revenue / invoice_count if invoice_count > 0 else 0

# Dashboard Title & Header
st.title("RetailPulse | Executive Sales Dashboard")
st.markdown("Interactive analysis of customer behavior, revenue growth, and geographic expansion.")

# Executive Overview Metrics
st.subheader("Executive Overview")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Gross Revenue", f"${gross_revenue:,.2f}")
col2.metric("Units Sold", f"{units_sold:,.0f}")
col3.metric("Sales Invoices", f"{invoice_count:,.0f}")
col4.metric("Identified Customers", f"{customer_count:,.0f}")
col5.metric("Revenue per Invoice", f"${average_order_value:,.2f}")

st.divider()

# Monthly Sales Trend
st.subheader("Monthly Sales Trend")
monthly_trend = filtered_sales.groupby('YearMonth').agg({
    'GrossRevenue': 'sum',
    'Quantity': 'sum',
    invoice_col: 'nunique'
}).reset_index()

fig_monthly = px.line(
    monthly_trend,
    x='YearMonth',
    y='GrossRevenue',
    title="Gross Sales Revenue by Month",
    labels={'YearMonth': 'Month', 'GrossRevenue': 'Revenue ($)'},
    markers=True
)
st.plotly_chart(fig_monthly, use_container_width=True)

# Product & Country Performance
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Top 10 Products by Revenue")
    desc_col = 'Description' if 'Description' in filtered_sales.columns else 'StockCode'
    top_products = filtered_sales.groupby(desc_col)['GrossRevenue'].sum().reset_index()
    top_products = top_products.sort_values(by='GrossRevenue', ascending=False).head(10)
    fig_products = px.bar(
        top_products,
        x='GrossRevenue',
        y=desc_col,
        orientation='h',
        title="Top 10 Products",
        labels={'GrossRevenue': 'Revenue ($)', desc_col: 'Product'}
    )
    fig_products.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_products, use_container_width=True)

with col_right:
    st.subheader("Top 10 Countries by Revenue")
    top_countries = filtered_sales.groupby('Country')['GrossRevenue'].sum().reset_index()
    top_countries = top_countries.sort_values(by='GrossRevenue', ascending=False).head(10)
    fig_countries = px.bar(
        top_countries,
        x='GrossRevenue',
        y='Country',
        orientation='h',
        title="Top 10 Countries",
        labels={'GrossRevenue': 'Revenue ($)', 'Country': 'Country'}
    )
    fig_countries.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_countries, use_container_width=True)

st.divider()

# Customer Intelligence
st.subheader("Customer Intelligence")
if 'CustomerID' in filtered_sales.columns:
    cust_data = filtered_sales.dropna(subset=['CustomerID']).copy()
    cust_orders = cust_data.groupby('CustomerID')[invoice_col].nunique().reset_index()
    cust_orders['CustomerType'] = cust_orders[invoice_col].apply(
        lambda x: 'Repeat Customer' if x >= 2 else 'One-time Customer'
    )
    cust_summary = cust_orders['CustomerType'].value_counts().reset_index()
    cust_summary.columns = ['CustomerType', 'Count']

    fig_cust = px.bar(
        cust_summary,
        x='CustomerType',
        y='Count',
        title="Customer Frequency (One-time vs. Repeat)",
        color='CustomerType'
    )
    st.plotly_chart(fig_cust, use_container_width=True)

# Data Export & Table
st.divider()
st.subheader("Country Summary Data")
country_summary = filtered_sales.groupby('Country').agg({
    'GrossRevenue': 'sum',
    'Quantity': 'sum',
    invoice_col: 'nunique',
    'CustomerID': 'nunique'
}).reset_index()

with st.expander("View country summary data"):
    st.dataframe(country_summary, use_container_width=True)

st.subheader("Export Data")
csv_data = filtered_sales.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download Filtered Sales CSV",
    data=csv_data,
    file_name="retailpulse_filtered_sales.csv",
    mime="text/csv"
)

st.caption("RetailPulse | Historical analysis of the UCI Online Retail dataset")