# Architecture

```
 RAW SALES DATA (synthetic, Kaggle-shaped)
        |
        v
 Data Ingestion Layer        ingestion/download_data.py, ingestion/ingest.py
        |
        v
 Raw Data Storage            data/raw/sales_raw.csv (immutable, checksummed)
        |
        v
 Data Quality Checks         pipeline/quality_checks.py -> quality report
        |
        v
 Data Cleaning / ETL         pipeline/transform.py (deterministic rules)
        |
        v
 Warehouse Load              pipeline/load.py -> DuckDB (local) or BigQuery (cloud)
        |
        v
 dbt Transformations         dbt/models/{staging,intermediate,marts}
        |
        v
 Cloud/Local Data Warehouse  DuckDB file OR BigQuery dataset
        |
   +----+----+
   v         v
Analytics   Forecasting      forecasting/{prepare_data,model_selection,predict}.py
 Tables      Model
   |         |
   +----+----+
        v
 BI Dashboard                Looker Studio (docs/dashboard.md)
```

## Orchestration choice: plain Python, not Airflow

This pipeline is a short, linear, single-machine batch job. `pipeline/pipeline.py`
chains ingest -> quality -> clean -> load -> dbt -> forecast as ordinary
Python function calls with clear logging and a quality gate. Airflow's
scheduler + webserver + metadata database stack is real operational weight
(another Postgres, more Docker services, DAG-parsing overhead) that buys
nothing here - there's no fan-out, no cross-pipeline dependency, no
multi-team scheduling need. If this were serving many pipelines with SLAs
and retries across teams, Airflow would earn its place. A DAG-shaped
equivalent is documented for reference but not deployed - see
`docs/pipeline.md`.

## Local vs. Cloud mode

The entire pipeline runs end-to-end on **DuckDB** (an embedded, file-based
analytical database - not a server) with zero external dependencies or
credentials. Setting `ENVIRONMENT=cloud` plus the three `GOOGLE_*`
environment variables switches `pipeline/load.py`, `dbt/profiles.yml`
(`target: cloud`), and `forecasting/save_forecast.py` to write to BigQuery
instead - the code paths exist and are correct, but were not exercised in
this build since no GCP project/credentials are available in this sandbox.
If cloud loading fails or isn't configured, the pipeline automatically and
loudly falls back to local rather than silently failing.

## Why not Kubernetes / Kafka / Spark / Terraform

None of them are justified at this scale: single dataset, single machine,
batch (not streaming) workload, no multi-service fan-out. Adding them would
be resume-padding, not engineering - see section 33 of the original spec
("do not overengineer"). Docker Compose with a single service is enough to
make the project portable.
