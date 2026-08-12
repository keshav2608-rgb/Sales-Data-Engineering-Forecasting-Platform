"""Schema validation for raw ingested data."""
import pandas as pd

REQUIRED_COLUMNS = [
    "order_id", "order_date", "customer_id", "customer_name",
    "product_id", "product_name", "category", "quantity",
    "unit_price", "sales", "discount", "region", "country", "segment",
]


class SchemaValidationError(Exception):
    pass


def validate_schema(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise SchemaValidationError(f"Missing required columns: {missing}")
    if df.empty:
        raise SchemaValidationError("Dataset is empty")


def validate_not_empty(df: pd.DataFrame) -> None:
    if len(df) == 0:
        raise SchemaValidationError("Dataset has zero rows")
