import pandas as pd
from pipeline.quality_checks import run_quality_checks

COLS = ["order_id", "order_date", "customer_id", "customer_name", "product_id",
        "product_name", "category", "quantity", "unit_price", "sales",
        "discount", "region", "country", "segment"]


def _row(**overrides):
    base = dict(order_id="O1", order_date="2024-01-01", customer_id="C1",
                customer_name="Alice", product_id="P1", product_name="Widget",
                category="Electronics", quantity="2", unit_price="10.0",
                sales="20.0", discount="0", region="North America",
                country="USA", segment="Consumer")
    base.update(overrides)
    return base


def test_detects_duplicate_rows():
    df = pd.DataFrame([_row(), _row()])
    report = run_quality_checks(df)
    assert report["duplicate_rows"] == 1


def test_detects_missing_customer_id():
    df = pd.DataFrame([_row(customer_id=None), _row(order_id="O2")])
    report = run_quality_checks(df)
    assert report["missing_customer_id"] == 1


def test_detects_invalid_quantity():
    df = pd.DataFrame([_row(quantity="-1"), _row(order_id="O2")])
    report = run_quality_checks(df)
    assert report["invalid_quantities"] == 1


def test_detects_invalid_date():
    df = pd.DataFrame([_row(order_date="not-a-date"), _row(order_id="O2")])
    report = run_quality_checks(df)
    assert report["invalid_dates"] == 1


def test_clean_data_has_zero_flagged_rows():
    df = pd.DataFrame([_row(order_id=f"O{i}") for i in range(5)])
    report = run_quality_checks(df)
    assert report["rows_flagged_invalid"] == 0
    assert report["estimated_valid_rows"] == 5
