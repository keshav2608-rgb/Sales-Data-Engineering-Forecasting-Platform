# Metric Definitions

| Metric | Definition | Source |
|---|---|---|
| Total Revenue | SUM(revenue) | fact_sales |
| Total Orders | COUNT(DISTINCT order_id) | fact_sales |
| Average Order Value | Total Revenue / Total Orders | sales_daily.avg_order_value |
| Total Customers | COUNT(DISTINCT customer_id) | dim_customer |
| New Customers (period) | customers whose first_order_date falls in period | dim_customer.first_order_date |
| Repeat Customers | customers with order_count > 1 | dim_customer.is_repeat_customer |
| Revenue per Customer | Total Revenue / Total Customers | dim_customer |
| MoM Growth | (this month revenue - last month revenue) / last month revenue | sales_monthly.mom_growth_pct |
| YoY Growth | (this month revenue - same month last year) / same month last year | sales_monthly.yoy_growth_pct |
| Best-Selling Products | products ranked by units_sold desc | dim_product |
| Highest Revenue Products | products ranked by total_revenue desc | dim_product |
| Forecast Accuracy | RMSE/MAE/MAPE of the selected model on the hold-out test set | models/model_comparison.json |

Every metric above is computed by the dbt marts or the forecasting module -
none are hard-coded.
