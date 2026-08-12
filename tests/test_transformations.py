import pandas as pd
from pipeline.transform import clean

COLS = ["order_id", "order_date", "customer_id", "customer_name", "product_id",
        "product_name", "category", "quantity", "unit_price", "sales",
        "discount", "region", "country", "segment"]


def _row(**overrides):
    base = dict(order_id="O1", order_date="2024-01-01", customer_id="C1",
                customer_name="  ALICE  ", product_id="P1", product_name="Widget",
                category="electronics", quantity="2", unit_price="10.0",
                sales="999.0", discount=None, region="north america",
                country="usa", segment="Consumer")
    base.update(overrides)
    return base


def test_removes_duplicate_rows():
    df = pd.DataFrame([_row(), _row()])
    out = clean(df)
    assert len(out) == 1


def test_drops_missing_customer_id():
    df = pd.DataFrame([_row(customer_id=None), _row(order_id="O2")])
    out = clean(df)
    assert len(out) == 1
    assert out.iloc[0]["order_id"] == "O2"


def test_drops_invalid_quantity():
    df = pd.DataFrame([_row(quantity="-5"), _row(order_id="O2")])
    out = clean(df)
    assert len(out) == 1


def test_drops_unparseable_dates():
    df = pd.DataFrame([_row(order_date="not-a-date"), _row(order_id="O2")])
    out = clean(df)
    assert len(out) == 1


def test_normalizes_category_casing():
    df = pd.DataFrame([_row(category="ELECTRONICS"), _row(order_id="O2", category="electronics")])
    out = clean(df)
    assert set(out["category"]) == {"Electronics"}


def test_recomputes_sales_from_quantity_price_discount():
    df = pd.DataFrame([_row(quantity="3", unit_price="10.0", discount="0.1", sales="999999")])
    out = clean(df)
    # 3 * 10.0 * (1 - 0.1) = 27.0, NOT the corrupted input value 999999
    assert out.iloc[0]["sales"] == 27.0


def test_missing_discount_filled_with_zero():
    df = pd.DataFrame([_row(discount=None)])
    out = clean(df)
    assert out.iloc[0]["discount"] == 0
