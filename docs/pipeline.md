# Pipeline

## Steps (pipeline/pipeline.py)

1. **Ingest** - `ingestion/download_data.py` generates/refreshes
   `data/raw/sales_raw.csv` + metadata sidecar (source, timestamp, row/col
   count, sha256 checksum). Raw file is never mutated afterward.
2. **Extract** - `pipeline/extract.py` reads the raw CSV as strings and
   validates schema (`ingestion/validators.py`).
3. **Data quality checks** - `pipeline/quality_checks.py` measures
   duplicates, missing fields, invalid quantities/prices/dates, and prints a
   quality report. A **quality gate** aborts the pipeline if more than 50%
   of rows are flagged invalid (`pipeline/pipeline.py::QualityGateError`).
4. **Clean / transform** - `pipeline/transform.py` applies deterministic
   rules: drop unparseable dates, drop missing customer_id, drop invalid
   quantities, impute missing prices from the product-level median,
   normalize text casing, recompute `sales` from
   `quantity * unit_price * (1 - discount)` rather than trusting the raw
   (possibly corrupted) sales column, and winsorize outliers at the 99th
   percentile per category.
5. **Load** - `pipeline/load.py` writes the cleaned dataframe to
   `raw.sales_staging` in DuckDB (local) or BigQuery (cloud, opt-in).
6. **dbt run + test** - builds staging -> intermediate -> marts and runs 32
   schema tests (not_null, unique, accepted_values, relationships).
7. **Forecast** - `forecasting/train.py` prepares the monthly revenue
   series, compares 4 models on a chronological hold-out set, selects the
   best by RMSE, forecasts 6 months forward, and saves results.

## Orchestration DAG (equivalent shape, for reference)

```
ingestion >> quality_checks >> transform >> load >> dbt_run >> dbt_test >> forecast
```

This is exactly what `run_pipeline()` executes in Python. See
`docs/architecture.md` for why Airflow wasn't used to run it.

## Data quality gate example output

```
==================================================
DATA QUALITY REPORT
==================================================
Rows processed:          50,150
Duplicate rows:          150
Duplicate order_ids:     150
Missing customer IDs:    50
Missing region:          100
Missing category:        50
Missing unit_price:      50
Invalid quantities:      25
Invalid unit_price:      50
Invalid sales:           0
Invalid dates:           10
--------------------------------------------------
Rows flagged invalid:    228
Estimated valid rows:    49,922
==================================================
```

(Actual counts vary slightly run to run since the synthetic generator uses
random sampling, but are seeded and stay in this range.)

## Running it

```bash
make setup        # install deps, create .env
make pipeline      # ingest -> quality -> clean -> load -> dbt -> forecast
make test          # run pytest suite (31 tests)
make health        # check warehouse + dbt + config status
```
