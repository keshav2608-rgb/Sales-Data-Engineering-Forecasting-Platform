-- Reference commands for creating the BigQuery datasets this project expects.
-- Run via `bq` CLI or paste into the BigQuery console.

-- bq mk --dataset --location=US $GOOGLE_CLOUD_PROJECT:sales_raw
-- bq mk --dataset --location=US $GOOGLE_CLOUD_PROJECT:sales_staging
-- bq mk --dataset --location=US $GOOGLE_CLOUD_PROJECT:sales_analytics
-- bq mk --dataset --location=US $GOOGLE_CLOUD_PROJECT:sales_forecast

-- Then apply warehouse/bigquery/schema.sql to create the staging/forecast tables.
-- dbt creates the analytics marts itself on `dbt run --target cloud`.
