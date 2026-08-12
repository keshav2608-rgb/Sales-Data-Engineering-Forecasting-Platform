# Data Dictionary

## raw.sales_staging (loaded by pipeline/load.py, post-cleaning, pre-dbt)

| Column | Type | Description | Nullable | Example |
|---|---|---|---|---|
| order_id | STRING | Unique order line identifier | No | ORD-100042 |
| order_date | DATE | Date the order was placed | No | 2024-03-15 |
| customer_id | STRING | Unique customer identifier | No | C-10231 |
| customer_name | STRING | Customer display name, Title Case | No | John Smith |
| product_id | STRING | Unique product identifier | No | P-1004 |
| product_name | STRING | Product display name | No | Wireless Mouse |
| category | STRING | Product category, Title Case, "Unknown" if missing | No | Electronics |
| quantity | INT64 | Units purchased, always > 0 | No | 3 |
| unit_price | FLOAT64 | Price per unit at time of sale | No | 24.99 |
| sales | FLOAT64 | Recomputed as quantity * unit_price * (1 - discount) | No | 67.47 |
| discount | FLOAT64 | Discount fraction, 0.0-0.9 | No | 0.10 |
| region | STRING | Sales region, Title Case, "Unknown" if missing | No | North America |
| country | STRING | Country within region | No | USA |
| segment | STRING | Customer segment | No | Consumer |

## dbt marts (main_analytics schema in DuckDB / sales_analytics dataset in BigQuery)

### fact_sales
Grain: one row per order line (`sale_id`).

| Column | Type | Description |
|---|---|---|
| sale_id | BIGINT | Surrogate key |
| order_id | STRING | Natural key from source |
| date_key | DATE | FK to dim_date |
| customer_key | BIGINT | FK to dim_customer |
| product_key | BIGINT | FK to dim_product |
| region, country | STRING | Denormalized geography |
| quantity, unit_price, discount | numeric | Transaction detail |
| revenue | DOUBLE | Line revenue |

### dim_customer
Grain: one row per customer_id. Includes `order_count`, `total_revenue`,
`is_repeat_customer` (order_count > 1).

### dim_product
Grain: one row per product_id. Includes `units_sold`, `total_revenue`.

### dim_date
Grain: one row per calendar day present in the data. Includes day/month/
quarter/year/week/day_of_week/is_weekend.

### sales_daily
Grain: one row per order_date. `total_orders`, `total_units`,
`total_revenue`, `avg_order_value`.

### sales_monthly
Grain: one row per calendar month. `total_orders`, `total_revenue`,
`mom_growth_pct`, `yoy_growth_pct`.

## forecast.forecast_results

| Column | Type | Description |
|---|---|---|
| forecast_date | DATE | First day of the forecasted month |
| predicted_sales | DOUBLE | Point forecast |
| lower_bound / upper_bound | DOUBLE | ~80% confidence interval |
| model_name | STRING | Winning model (e.g. "Exponential Smoothing") |
| generated_at | TIMESTAMP | Run timestamp (UTC) |
