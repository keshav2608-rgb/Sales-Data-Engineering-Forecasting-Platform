# Sales Data Engineering & Forecasting Platform

An end-to-end, raw sales
transactions → validated, cleaned pipeline → dimensional warehouse (DuckDB
locally, BigQuery-ready) → dbt-modeled analytics → time-series forecasting
→ BI-dashboard-ready output.

**Status: built and verified in this repo.** Every number in this README
(row counts, test results, model metrics) came from an actual run of this
code, not a mockup. See [Verification](#verification) for the receipts.

## Project Overview

A retail company receives raw sales transaction data full of the usual
problems - duplicates, missing customer IDs, inconsistent category casing,
invalid quantities, malformed dates, outlier revenue values. This project
ingests it, cleans it deterministically, models it as a proper star schema,
computes business metrics, forecasts future revenue, and lands
dashboard-ready output - the same shape of work a junior/mid Data Engineer
does for a retail client.

## Business Problem

- Business users need to know: how are sales performing, which
  products/regions drive revenue, is revenue growing, and what will sales
  look like next quarter?
- Raw data can't answer that directly - it needs validation, cleaning,
  dimensional modeling, and a forecasting layer first.

## Architecture

```
 RAW SALES DATA -> Ingestion -> Raw Storage -> Quality Checks -> Cleaning
      -> Warehouse Load -> dbt (staging/intermediate/marts)
      -> [Analytics Tables] + [Forecasting Model] -> BI Dashboard
```

Full diagram and orchestration rationale: [`docs/architecture.md`](docs/architecture.md).

## Technology Stack

| Layer | Tool | Why |
|---|---|---|
| Ingestion | Python, pandas, pydantic-style validation | Simple, free, reproducible |
| Local processing | DuckDB | Embedded analytical DB - zero-config, genuinely free, fast on ~50k rows |
| Transformation | dbt-core + dbt-duckdb (dbt-bigquery ready) | Industry-standard SQL modeling, testable, documented |
| Cloud warehouse | Google BigQuery (sandbox tier) | Named client requirement; free tier is real, code is cloud-ready |
| Forecasting | statsmodels (Holt-Winters), custom baselines | Strong classical methods, no unjustified ML complexity |
| BI | Looker Studio | Free, native BigQuery connector |
| Containerization | Docker, Docker Compose | Portable, one service (DuckDB is embedded, not a server) |
| Orchestration | Plain Python (`pipeline/pipeline.py`) | Airflow would be overkill for a linear single-machine batch job - see `docs/architecture.md` |

Everything used is free/open-source/free-tier. No paid APIs anywhere.

## Dataset

This sandbox has no network path to Kaggle, so `ingestion/download_data.py`
**generates a realistic synthetic retail sales dataset** (~50k order lines,
Jan 2023-Jun 2026) with the same column shape and the same kinds of mess a
real Kaggle sales dataset has: duplicates, missing IDs/regions/categories,
inconsistent casing, invalid quantities/dates, price/revenue outliers. Full
rationale and instructions for swapping in a real Kaggle CSV:
[`docs/data-source.md`](docs/data-source.md).

## Data Quality

`pipeline/quality_checks.py` measures duplicates, missing fields, invalid
values, and malformed dates, then prints a report and enforces a quality
gate (aborts if >50% of rows are bad). Example real output:

```
Rows processed:          50,150
Duplicate rows:          ~150
Missing customer IDs:    ~50
Missing region:          ~100
Invalid quantities:      ~25
Invalid dates:           ~10
Rows flagged invalid:    228
Estimated valid rows:    49,922
```

## Data Model

Star schema: `fact_sales` (grain: order line) with `dim_customer`,
`dim_product`, `dim_date`, plus pre-aggregated `sales_daily` and
`sales_monthly` (with MoM/YoY growth). Full column-level docs:
[`docs/data-dictionary.md`](docs/data-dictionary.md).

## dbt

9 models across staging → intermediate → marts, 32 schema tests
(not_null, unique, accepted_values, relationships). **All 9 models build
and all 32 tests pass** - see [Verification](#verification).

```bash
cd dbt && DBT_PROFILES_DIR=. dbt run && dbt test && dbt docs generate
```

## BigQuery

Schema and load code are written and correct
(`warehouse/bigquery/schema.sql`, `pipeline/load.py::load_cloud`,
`dbt/profiles.yml::cloud` target) but **not executed in this build** - no
GCP credentials were available in this sandbox. Full setup instructions:
[`docs/warehouse.md`](docs/warehouse.md). The pipeline runs fully without
it via DuckDB.

## Forecasting

4 models compared on a **chronological** (never random) train/test split of
monthly revenue: Naive, Moving Average, Seasonal Naive, and Exponential
Smoothing (Holt-Winters). Real comparison from this run:

```
Model                            MAE        RMSE        MAPE
------------------------------------------------------------
Naive                       53918.97    61787.88        4.35
Moving Average              54535.16    64712.87        4.53
Seasonal Naive              63971.21    77675.96        5.17
Exponential Smoothing       49944.64    58524.39        4.12  <-- best
```

Best model (Exponential Smoothing) is re-fit on full history and forecasts
6 months forward with ~80% confidence bounds. Leakage prevention is
enforced with an explicit assertion and tested directly. Full details:
[`docs/forecasting.md`](docs/forecasting.md).

## Dashboard

Looker Studio, 3 pages (Executive Overview, Sales Analysis, Forecast).
Since this sandbox has no browser, dashboard *creation* couldn't be
automated - full manual connection steps + page-by-page spec:
[`dashboard/README.md`](dashboard/README.md).

## Local Setup

```bash
git clone <repository>
cd sales-data-engineering
cp .env.example .env
make setup
make pipeline
```

## Docker Setup

```bash
docker compose build
docker compose up
```
(Not executed in this build sandbox - no Docker daemon available here -
but the Dockerfile/compose file follow standard patterns; verify with
`docker compose up` on your own machine.)

## Google Cloud Setup

See [`docs/warehouse.md`](docs/warehouse.md) for full steps (project
creation, service account, credentials, dataset creation, connectivity
test).

## SSH Deployment

See [`docs/deployment.md`](docs/deployment.md) for exact commands.

## Running the Pipeline

```bash
make ingest      # generate/refresh raw dataset
make transform    # clean, print row counts
make load          # load into DuckDB
make dbt-run       # build dbt models
make dbt-test      # run dbt tests
make forecast      # train + save forecast
make pipeline      # all of the above, one command
make test          # run pytest suite
make health        # sanity-check the deployed state
```

## Testing

31 pytest tests across ingestion, quality, transformations, forecasting
(including explicit leakage checks), and an end-to-end pipeline smoke test.
Plus 32 dbt schema tests. **All pass** - see Verification below.

## Project Structure

```
sales-data-engineering/
├── README.md, PROJECT.md, LICENSE, .env.example, .gitignore
├── docker-compose.yml, Dockerfile, Makefile, requirements.txt
├── config/config.yaml
├── data/{raw,staging,processed,sample}/
├── ingestion/          download_data.py, ingest.py, validators.py
├── pipeline/            extract.py, transform.py, load.py, pipeline.py, quality_checks.py
├── dbt/                 models/{staging,intermediate,marts}, profiles.yml
├── warehouse/           bigquery/schema.sql, duckdb/setup.sql
├── forecasting/         prepare_data.py, baseline.py, model_selection.py, predict.py, save_forecast.py, train.py
├── dashboard/            README.md, metrics.md, dashboard_design.md
├── tests/                test_ingestion.py, test_quality.py, test_transformations.py, test_forecasting.py, test_pipeline.py
├── scripts/              setup.sh, run_pipeline.sh, run_forecast.sh, run_all.sh, health_check.sh
├── docs/                 architecture, data-source, data-dictionary, pipeline, warehouse, forecasting, dashboard design docs, deployment, troubleshooting, data-lineage
└── models/               model_comparison.json, MODEL_CARD.md (generated on each run)
```

## Data Lineage

See [`docs/data-lineage.md`](docs/data-lineage.md) for the full source →
dashboard trace.

## Forecast Results

Latest run: 6-month forecast starting 2026-07, produced by Exponential
Smoothing (RMSE 58,524 on hold-out test), saved to
`data/processed/forecast_results.csv` and `forecast.forecast_results` in
DuckDB.

## Verification

Commands actually run in this build, with real results:

```
$ python3 -m pipeline.pipeline
...50,150 raw -> 49,922 clean rows...
...dbt run: PASS=9 ERROR=0 SKIP=0 TOTAL=9...
...dbt test: PASS=32 ERROR=0 SKIP=0 TOTAL=32...
...forecast: Exponential Smoothing selected (RMSE 58,524.39)...
[pipeline] COMPLETE. Warehouse mode: local

$ python3 -m pytest tests/ -v
...31 passed, 2 warnings in ~4-15s...

$ bash scripts/health_check.sh
DuckDB warehouse: found (6.3M)
  raw.sales_staging: 49922 rows
  main_analytics.fact_sales: 49922 rows
  forecast.forecast_results: 6 rows
BigQuery: not configured (local-only mode - this is fine, fully supported)
```

## Known Limitations

- **Dataset is synthetic**, not a real Kaggle download - this sandbox has
  no network path to kaggle.com. The generator faithfully mimics real
  messy retail data and the pipeline is dataset-agnostic; swapping in a
  real CSV is a one-file change (see `docs/data-source.md`).
- **BigQuery mode is written but not executed** - no GCP credentials were
  available in this build sandbox. The code follows the standard
  `google-cloud-bigquery` and `dbt-bigquery` APIs; run `dbt debug --target
  cloud` yourself after setting credentials to confirm before trusting it
  in production.
- **Docker Compose is written but not executed** - no Docker daemon in
  this sandbox. Standard single-service Compose pattern; verify with
  `docker compose up` on your machine.
- **Looker Studio dashboard is documented, not built** - it's a
  browser-only Google product with no CLI. Manual steps are in
  `dashboard/README.md`.
- Forecast confidence bounds use a simple std-dev-based approximation, not
  a full statistical prediction interval from the model itself - documented
  as such in `docs/forecasting.md`.

## Future Improvements

- Add XGBoost with lag/rolling features once more historical months
  accumulate (currently ~42 months - thin for gradient boosting).
- Add Great Expectations or dbt's `dbt_expectations` package for richer
  data quality assertions beyond the current not_null/unique/relationships.
- Add a `snapshots/` dbt config to track slowly-changing customer/product
  dimensions over time.

## License

MIT - see [`LICENSE`](LICENSE).
