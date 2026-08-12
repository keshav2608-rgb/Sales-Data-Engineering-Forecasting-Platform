# Data Source

## What this project actually uses

This sandbox build environment has **no network access to Kaggle** (its egress
allowlist covers package registries only - pypi, npm, github, etc - not
`kaggle.com`). Rather than faking a download or silently substituting an
unrelated real dataset, `ingestion/download_data.py` **generates a synthetic
retail sales transaction dataset** that:

- Has the exact column shape of a typical Kaggle retail sales dataset
  (order_id, order_date, customer_id, customer_name, product_id,
  product_name, category, quantity, unit_price, sales, discount, region,
  country, segment)
- Contains ~50,000 order lines spanning Jan 2023 - Jun 2026
- Has realistic messiness deliberately injected: duplicate rows, missing
  customer IDs/regions/categories, inconsistent category casing
  ("Electronics" / "electronics" / "ELECTRONICS"), invalid quantities,
  malformed dates, missing prices, and revenue outliers
- Is fully reproducible (seeded RNG) and generated fresh on every
  `make ingest`

This keeps the entire pipeline honest end-to-end: the cleaning, quality,
warehouse, dbt, and forecasting layers all operate on real (if synthetic)
messy data, not a curated toy CSV.

## Using a real Kaggle dataset instead

If you have Kaggle credentials on a machine with internet access:

1. Download one of:
   - [Superstore Sales Dataset](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final)
   - [Store Item Demand Forecasting Challenge](https://www.kaggle.com/c/demand-forecasting-kernels-only)
2. Rename/remap columns to match the schema in `docs/data-dictionary.md`.
3. Save the CSV at `data/raw/sales_raw.csv`.
4. Skip `ingestion/download_data.py` (or point it at your file) and run the
   rest of the pipeline as normal - `pipeline/transform.py` onward is
   dataset-agnostic as long as column names match.

## Why not commit the raw file to git

`data/raw/*.csv` is gitignored. The dataset is regenerated (or
re-downloaded) on demand via `make ingest`, which is the standard practice
for any pipeline where the raw data is either large or reproducible from a
script - committing it would bloat the repo for no benefit.
