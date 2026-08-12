-- DuckDB local warehouse schema (mirrors BigQuery schema in warehouse/bigquery/schema.sql)

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS forecast;

-- raw.sales_staging holds the cleaned-but-not-yet-modeled rows, loaded by pipeline/load.py.
-- dbt then builds staging -> intermediate -> marts on top of this.
