# Troubleshooting

**`FileNotFoundError: data/raw/sales_raw.csv not found`**
Run `make ingest` (or `python -m ingestion.download_data`) before anything
else - the pipeline expects the raw file to already exist and never
generates it implicitly except via `make pipeline`.

**`dbt: command not found`**
`dbt-core` and `dbt-duckdb` aren't installed - run `make setup` or
`pip install -r requirements.txt`.

**dbt error: `Binder Error: Referenced column "X" not found`**
The columns in `raw.sales_staging` don't match what `stg_sales.sql`
expects. This happens if you swap in your own dataset (see
`docs/data-source.md`) without updating `pipeline/transform.py` and
`dbt/models/staging/stg_sales.sql` to match your column names. Run
`DESCRIBE raw.sales_staging` in DuckDB to inspect actual columns.

**`QualityGateError: X% of rows flagged invalid - exceeds 50% threshold`**
Your source data is badly broken (or you changed the synthetic generator's
mess-injection rates too high in `ingestion/download_data.py`). Either fix
the source or intentionally lower `run_pipeline`'s 0.5 threshold if that's
expected for your use case.

**Forecasting: `Not enough history for a train/test split`**
Needs at least 6 months of data in `sales_monthly`. If you swapped in a
smaller custom dataset, either wait for more data or lower
`test_fraction`/rethink monthly vs. daily granularity.

**BigQuery: `403 Forbidden` or `Could not automatically determine credentials`**
`GOOGLE_APPLICATION_CREDENTIALS` isn't pointing at a valid service account
key, or the service account lacks `roles/bigquery.dataEditor`. See
`docs/warehouse.md` step 3-4. The pipeline automatically falls back to
local DuckDB mode if this happens, so it should never hard-crash your run.

**Docker: `permission denied while trying to connect to the Docker daemon`**
Your user isn't in the `docker` group yet - run
`sudo usermod -aG docker $USER && newgrp docker` and retry.

**pytest: `ModuleNotFoundError: No module named 'pipeline'`**
Run pytest from the project root (`sales-data-engineering/`), not from
inside `tests/` - the modules are imported with absolute paths relative to
the repo root.
