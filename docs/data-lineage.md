# Data Lineage

```
Source Dataset (synthetic, Kaggle-shaped)
      |  ingestion/download_data.py
      v
Raw Data                           data/raw/sales_raw.csv (immutable)
      |  ingestion/ingest.py (schema validation only)
      v
Data Quality Report                pipeline/quality_checks.py
      |
      v
Cleaned Data                       pipeline/transform.py (in-memory dataframe)
      |  pipeline/load.py
      v
raw.sales_staging                  DuckDB (local) / BigQuery sales_staging (cloud)
      |  dbt/models/staging/stg_sales.sql
      v
dbt Staging (stg_sales)
      |  dbt/models/intermediate/*.sql
      v
dbt Intermediate (int_customer_sales, int_product_sales)
      |  dbt/models/marts/*.sql
      v
Analytics Marts                    dim_customer, dim_product, dim_date,
                                    fact_sales, sales_daily, sales_monthly
      |
      +----------------------------------+
      v                                  v
BigQuery / DuckDB (queryable)     Forecasting Model
      |                                  |  forecasting/prepare_data.py
      |                                  |  forecasting/model_selection.py
      |                                  |  forecasting/predict.py
      |                                  v
      |                           forecast.forecast_results
      |                           data/processed/forecast_results.{csv,parquet}
      |                                  |
      +------------------+---------------+
                          v
                   Looker Studio (BI Dashboard)
```

Every arrow above corresponds to a real file/module in this repo - there is
no step in this diagram that isn't backed by code you can run.
