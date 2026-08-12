"""Loads the immutable raw file and validates it. Never mutates data/raw/."""
from pathlib import Path
import pandas as pd
from ingestion.validators import validate_schema

ROOT = Path(__file__).resolve().parents[1]


def load_raw() -> pd.DataFrame:
    raw_path = ROOT / "data" / "raw" / "sales_raw.csv"
    if not raw_path.exists():
        raise FileNotFoundError(
            f"{raw_path} not found. Run `python -m ingestion.download_data` first."
        )
    df = pd.read_csv(raw_path, dtype=str)  # read as str first; typing happens in cleaning
    validate_schema(df)
    return df


if __name__ == "__main__":
    df = load_raw()
    print(f"[ingest] Loaded {len(df)} raw rows, {df.shape[1]} columns. Schema OK.")
