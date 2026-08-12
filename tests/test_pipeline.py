"""
Lightweight end-to-end smoke test: extract -> clean -> load into a scratch
DuckDB file, then verify row counts and key invariants. Does not touch the
real warehouse file or re-run dbt (that's covered by running `dbt test`
directly, see docs/pipeline.md).
"""
from pathlib import Path
import duckdb
from pipeline.extract import extract
from pipeline.transform import clean
from pipeline.quality_checks import run_quality_checks

ROOT = Path(__file__).resolve().parents[1]


def test_extract_clean_row_count_shrinks_or_equal():
    raw = extract()
    cleaned = clean(raw)
    assert len(cleaned) <= len(raw)
    assert len(cleaned) > 0


def test_cleaned_data_has_no_nulls_in_key_columns():
    raw = extract()
    cleaned = clean(raw)
    for col in ["order_id", "order_date", "customer_id", "quantity", "unit_price", "sales"]:
        assert cleaned[col].isna().sum() == 0


def test_cleaned_sales_are_non_negative():
    raw = extract()
    cleaned = clean(raw)
    assert (cleaned["sales"] >= 0).all()


def test_load_into_scratch_duckdb():
    raw = extract()
    cleaned = clean(raw)
    scratch_path = ROOT / "data" / "processed" / "_test_scratch.duckdb"
    con = duckdb.connect(str(scratch_path))
    con.register("df_view", cleaned)
    con.execute("CREATE OR REPLACE TABLE test_sales AS SELECT * FROM df_view")
    n = con.execute("SELECT COUNT(*) FROM test_sales").fetchone()[0]
    con.close()
    scratch_path.unlink(missing_ok=True)
    assert n == len(cleaned)


def test_quality_gate_threshold_logic():
    raw = extract()
    report = run_quality_checks(raw)
    invalid_rate = report["rows_flagged_invalid"] / report["rows_processed"]
    assert invalid_rate < 0.5, "Synthetic dataset should never exceed the 50% quality gate"
