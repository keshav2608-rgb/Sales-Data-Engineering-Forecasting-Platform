from pathlib import Path
from ingestion.ingest import load_raw
from ingestion.validators import REQUIRED_COLUMNS, validate_schema, SchemaValidationError
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_raw_file_exists():
    assert (ROOT / "data" / "raw" / "sales_raw.csv").exists(), \
        "Run `python -m ingestion.download_data` first"


def test_expected_columns_exist():
    df = load_raw()
    for col in REQUIRED_COLUMNS:
        assert col in df.columns


def test_dataset_not_empty():
    df = load_raw()
    assert len(df) > 0


def test_validate_schema_raises_on_missing_columns():
    bad_df = pd.DataFrame({"order_id": [1]})
    with pytest.raises(SchemaValidationError):
        validate_schema(bad_df)


def test_validate_schema_raises_on_empty():
    empty_df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    with pytest.raises(SchemaValidationError):
        validate_schema(empty_df)
