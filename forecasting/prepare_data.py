"""Pulls the sales_monthly mart from the warehouse and prepares a clean time series."""
from pathlib import Path
import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = ROOT / "warehouse" / "duckdb" / "sales.duckdb"


def load_monthly_series() -> pd.Series:
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute(
        "SELECT month_start, total_revenue FROM main_analytics.sales_monthly ORDER BY month_start"
    ).fetchdf()
    con.close()

    df["month_start"] = pd.to_datetime(df["month_start"])
    df = df.set_index("month_start").asfreq("MS")  # fill any missing calendar months
    df["total_revenue"] = df["total_revenue"].interpolate(limit_direction="both")

    # Drop the current partial (incomplete) month if present, to avoid training on a
    # truncated period that looks like a demand crash.
    last_month = df.index.max()
    today = pd.Timestamp.today().normalize().replace(day=1)
    if last_month >= today:
        df = df.iloc[:-1]

    return df["total_revenue"]


if __name__ == "__main__":
    s = load_monthly_series()
    print(s)
