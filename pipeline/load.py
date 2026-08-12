"""
Loads cleaned data into the warehouse.

- LOCAL mode (default, always available): DuckDB file at warehouse/duckdb/sales.duckdb
- CLOUD mode (opt-in): Google BigQuery, activated only when GOOGLE_CLOUD_PROJECT and
  GOOGLE_APPLICATION_CREDENTIALS are set in the environment. Falls back to local
  automatically (with a warning) if cloud isn't configured or the connection fails.

Never silently modifies data/raw/ - this only reads the already-cleaned dataframe.
"""
import os
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = ROOT / "warehouse" / "duckdb" / "sales.duckdb"
SETUP_SQL = ROOT / "warehouse" / "duckdb" / "setup.sql"


def load_local(df: pd.DataFrame, table: str = "raw.sales_staging") -> str:
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute(SETUP_SQL.read_text())
    con.register("df_view", df)
    con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM df_view")
    n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    con.close()
    print(f"[load] LOCAL (DuckDB): wrote {n} rows to {table} in {DUCKDB_PATH}")
    return "local"


def load_cloud(df: pd.DataFrame, table: str = "sales_staging.sales_cleaned") -> str:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not project or not creds:
        print("[load] CLOUD mode requested but GOOGLE_CLOUD_PROJECT / "
              "GOOGLE_APPLICATION_CREDENTIALS not set. Falling back to LOCAL.")
        return load_local(df)
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=project)
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        job = client.load_table_from_dataframe(df, table, job_config=job_config)
        job.result()
        print(f"[load] CLOUD (BigQuery): wrote {len(df)} rows to {table}")
        return "cloud"
    except Exception as e:
        print(f"[load] CLOUD load failed ({e}). Falling back to LOCAL.")
        return load_local(df)


def load(df: pd.DataFrame) -> str:
    environment = os.environ.get("ENVIRONMENT", "local")
    if environment == "cloud":
        return load_cloud(df)
    return load_local(df)


if __name__ == "__main__":
    from pipeline.extract import extract
    from pipeline.transform import clean
    df = clean(extract())
    load(df)
