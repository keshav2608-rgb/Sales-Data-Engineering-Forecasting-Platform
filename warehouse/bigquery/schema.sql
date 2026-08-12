-- BigQuery dataset/table layout. Run these once your GCP project + dataset exist.
-- See docs/warehouse.md for full setup instructions.
--
-- Datasets (logical groupings, created via `bq mk` or warehouse/bigquery/setup.sql):
--   sales_raw        (immutable landing zone, not modeled)
--   sales_staging     (cleaned rows land here, loaded by pipeline/load.py)
--   sales_analytics   (dbt marts: fact/dim tables + business metrics)
--   sales_forecast    (forecast output)

CREATE TABLE IF NOT EXISTS `sales_staging.sales_cleaned` (
    order_id      STRING,
    order_date    DATE,
    customer_id   STRING,
    customer_name STRING,
    product_id    STRING,
    product_name  STRING,
    category      STRING,
    quantity      INT64,
    unit_price    FLOAT64,
    sales         FLOAT64,
    discount      FLOAT64,
    region        STRING,
    country       STRING,
    segment       STRING
)
PARTITION BY order_date
CLUSTER BY category, region;

CREATE TABLE IF NOT EXISTS `sales_forecast.forecast_results` (
    forecast_date    DATE,
    predicted_sales  FLOAT64,
    lower_bound      FLOAT64,
    upper_bound      FLOAT64,
    model_name       STRING,
    generated_at     TIMESTAMP
)
PARTITION BY forecast_date;
