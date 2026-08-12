"""
Data quality layer: schema, completeness, uniqueness, validity checks.
Produces a structured quality report (dict) alongside the raw dataframe.
Does NOT mutate data - only measures it. Cleaning happens in transform.py.
"""
import pandas as pd


def run_quality_checks(df: pd.DataFrame) -> dict:
    report = {}
    report["rows_processed"] = int(len(df))

    # Uniqueness: duplicate order_id (full-row duplicates too)
    report["duplicate_rows"] = int(df.duplicated().sum())
    report["duplicate_order_ids"] = int(df["order_id"].duplicated().sum())

    # Completeness
    report["missing_customer_id"] = int(df["customer_id"].isna().sum())
    report["missing_region"] = int(df["region"].isna().sum())
    report["missing_category"] = int(df["category"].isna().sum())
    report["missing_unit_price"] = int(df["unit_price"].isna().sum())

    # Validity
    qty_numeric = pd.to_numeric(df["quantity"], errors="coerce")
    report["invalid_quantities"] = int(((qty_numeric <= 0) | qty_numeric.isna()).sum())

    price_numeric = pd.to_numeric(df["unit_price"], errors="coerce")
    report["invalid_unit_price"] = int(((price_numeric < 0) | price_numeric.isna()).sum())

    sales_numeric = pd.to_numeric(df["sales"], errors="coerce")
    report["invalid_sales"] = int(((sales_numeric < 0) | sales_numeric.isna()).sum())

    parsed_dates = pd.to_datetime(df["order_date"], errors="coerce")
    report["invalid_dates"] = int(parsed_dates.isna().sum())

    # Rough estimate of rows that will survive cleaning (any critical field bad)
    bad_mask = (
        df.duplicated()
        | df["customer_id"].isna()
        | (qty_numeric <= 0) | qty_numeric.isna()
        | (price_numeric < 0) | price_numeric.isna()
        | parsed_dates.isna()
    )
    report["rows_flagged_invalid"] = int(bad_mask.sum())
    report["estimated_valid_rows"] = int((~bad_mask).sum())

    return report


def print_quality_report(report: dict) -> None:
    print("=" * 50)
    print("DATA QUALITY REPORT")
    print("=" * 50)
    print(f"Rows processed:          {report['rows_processed']:,}")
    print(f"Duplicate rows:          {report['duplicate_rows']:,}")
    print(f"Duplicate order_ids:     {report['duplicate_order_ids']:,}")
    print(f"Missing customer IDs:    {report['missing_customer_id']:,}")
    print(f"Missing region:          {report['missing_region']:,}")
    print(f"Missing category:        {report['missing_category']:,}")
    print(f"Missing unit_price:      {report['missing_unit_price']:,}")
    print(f"Invalid quantities:      {report['invalid_quantities']:,}")
    print(f"Invalid unit_price:      {report['invalid_unit_price']:,}")
    print(f"Invalid sales:           {report['invalid_sales']:,}")
    print(f"Invalid dates:           {report['invalid_dates']:,}")
    print("-" * 50)
    print(f"Rows flagged invalid:    {report['rows_flagged_invalid']:,}")
    print(f"Estimated valid rows:    {report['estimated_valid_rows']:,}")
    print("=" * 50)
