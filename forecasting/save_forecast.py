"""Persists forecast output: DuckDB forecast schema + local CSV/Parquet (dashboard-ready)."""
import os
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = ROOT / "warehouse" / "duckdb" / "sales.duckdb"
PROCESSED_DIR = ROOT / "data" / "processed"


def save_forecast(forecast_df: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Local artifacts (always produced - dashboard-ready regardless of warehouse mode)
    forecast_df.to_csv(PROCESSED_DIR / "forecast_results.csv", index=False)
    forecast_df.to_parquet(PROCESSED_DIR / "forecast_results.parquet", index=False)

    # DuckDB warehouse table
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS forecast")
    con.register("fc_view", forecast_df)
    con.execute("CREATE OR REPLACE TABLE forecast.forecast_results AS SELECT * FROM fc_view")
    con.close()
    print(f"[save_forecast] Wrote {len(forecast_df)} rows to forecast.forecast_results "
          f"and data/processed/forecast_results.{{csv,parquet}}")

    # Optional cloud mirror
    if os.environ.get("ENVIRONMENT") == "cloud":
        _save_to_bigquery(forecast_df)


def _save_to_bigquery(forecast_df: pd.DataFrame) -> None:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not project or not creds:
        print("[save_forecast] CLOUD mode requested but credentials not set; skipping BigQuery mirror.")
        return
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=project)
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        job = client.load_table_from_dataframe(
            forecast_df, "sales_forecast.forecast_results", job_config=job_config
        )
        job.result()
        print("[save_forecast] Mirrored forecast to BigQuery sales_forecast.forecast_results")
    except Exception as e:
        print(f"[save_forecast] BigQuery mirror failed ({e}); local artifacts are still valid.")
