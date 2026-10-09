-- RetailPulse Analytics Queries

-- 1. Business Overview
SELECT
    COUNT(*) AS SalesLines,
    ROUND(SUM(Quantity * UnitPrice), 2) AS GrossSalesRevenue,
    SUM(Quantity) AS UnitsSold,
    COUNT(DISTINCT InvoiceNo) AS InvoiceCount,
    COUNT(DISTINCT CustomerID) AS IdentifiedCustomers
FROM online_retail
WHERE Quantity > 0 AND UnitPrice > 0;

-- 2. Monthly Revenue Trends
SELECT
    strftime('%Y-%m', InvoiceDate) AS YearMonth,
    ROUND(SUM(Quantity * UnitPrice), 2) AS GrossRevenue,
    COUNT(DISTINCT InvoiceNo) AS InvoiceCount,
    SUM(Quantity) AS UnitsSold
FROM online_retail
WHERE Quantity > 0 AND UnitPrice > 0
GROUP BY strftime('%Y-%m', InvoiceDate)
ORDER BY YearMonth;

-- 3. Top 10 Products
SELECT
    StockCode,
    MAX(Description) AS ProductDescription,
    SUM(Quantity) AS UnitsSold,
    ROUND(SUM(Quantity * UnitPrice), 2) AS GrossRevenue,
    COUNT(DISTINCT InvoiceNo) AS InvoiceCount
FROM online_retail
WHERE Quantity > 0 AND UnitPrice > 0
GROUP BY StockCode
ORDER BY GrossRevenue DESC
LIMIT 10;

-- 4. Country Performance
SELECT
    Country,
    ROUND(SUM(Quantity * UnitPrice), 2) AS GrossRevenue,
    SUM(Quantity) AS UnitsSold,
    COUNT(DISTINCT InvoiceNo) AS InvoiceCount,
    COUNT(DISTINCT CustomerID) AS IdentifiedCustomers
FROM online_retail
WHERE Quantity > 0 AND UnitPrice > 0
GROUP BY Country
ORDER BY GrossRevenue DESC;

-- 5. Top 10 Customers
SELECT
    CustomerID,
    ROUND(SUM(Quantity * UnitPrice), 2) AS TotalRevenue,
    SUM(Quantity) AS UnitsPurchased,
    COUNT(DISTINCT InvoiceNo) AS TotalOrders
FROM online_retail
WHERE Quantity > 0 AND UnitPrice > 0 AND CustomerID IS NOT NULL
GROUP BY CustomerID
ORDER BY TotalRevenue DESC
LIMIT 10;

-- 6. Repeat vs One-Time Customers (CTE)
WITH CustomerOrders AS (
    SELECT
        CustomerID,
        COUNT(DISTINCT InvoiceNo) AS TotalOrders
    FROM online_retail
    WHERE Quantity > 0 AND UnitPrice > 0 AND CustomerID IS NOT NULL
    GROUP BY CustomerID
)
SELECT
    CASE
        WHEN TotalOrders >= 2 THEN 'Repeat Customer'
        ELSE 'One-time Customer'
    END AS CustomerType,
    COUNT(*) AS CustomerCount
FROM CustomerOrders
GROUP BY CustomerType
ORDER BY CustomerCount DESC;
