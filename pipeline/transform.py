"""
Deterministic cleaning pipeline.

Business rules (documented):
- order_date must parse to a valid date; unparseable rows are dropped.
- customer_id missing -> row dropped (can't attribute revenue to a customer).
- region/category missing -> filled as "Unknown" (kept, not dropped - revenue is still real).
- category text -> normalized to Title Case, trimmed.
- customer_name -> trimmed, normalized to Title Case.
- quantity <= 0 -> row dropped (data entry error, not a valid transaction).
- unit_price missing/negative -> imputed with the median unit_price for that product_id;
  if no product-level median exists, the row is dropped.
- sales is recomputed as quantity * unit_price * (1 - discount) to guarantee consistency
  with the other fields (rather than trusting a possibly-corrupted `sales` column).
- discount missing -> filled with 0 (no discount applied).
- full-row duplicates -> dropped, keep first occurrence.
- outliers: sales capped at the 99th percentile *within each category* (winsorized,
  not dropped) so a handful of fat-fingered rows don't distort aggregates.
"""
import numpy as np
import pandas as pd


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Drop exact duplicate rows
    df = df.drop_duplicates(keep="first")

    # 2. Parse dates; drop rows with unparseable dates
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df = df[df["order_date"].notna()]

    # 3. Numeric typing
    for col in ["quantity", "unit_price", "sales", "discount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4. Drop rows with missing customer_id (can't attribute revenue)
    df = df[df["customer_id"].notna()]

    # 5. Drop invalid quantities
    df = df[df["quantity"] > 0]

    # 6. Impute missing/negative unit_price with product-level median; drop if impossible
    med_price = df.groupby("product_id")["unit_price"].transform("median")
    bad_price = df["unit_price"].isna() | (df["unit_price"] < 0)
    df.loc[bad_price, "unit_price"] = med_price[bad_price]
    df = df[df["unit_price"].notna() & (df["unit_price"] >= 0)]

    # 7. Fill missing discount with 0, clip to [0, 0.9]
    df["discount"] = df["discount"].fillna(0).clip(0, 0.9)

    # 8. Normalize text fields
    df["category"] = df["category"].fillna("Unknown").astype(str).str.strip().str.title()
    df["region"] = df["region"].fillna("Unknown").astype(str).str.strip().str.title()
    df["customer_name"] = df["customer_name"].astype(str).str.strip().str.title()
    df["product_name"] = df["product_name"].astype(str).str.strip()
    df["country"] = df["country"].astype(str).str.strip().str.title()
    df["segment"] = df["segment"].fillna("Consumer").astype(str).str.strip().str.title()

    # 9. Recompute sales deterministically from quantity/price/discount
    df["sales"] = (df["quantity"] * df["unit_price"] * (1 - df["discount"])).round(2)

    # 10. Winsorize outliers: cap sales at 99th percentile per category
    category_caps = df.groupby("category")["sales"].transform(lambda s: s.quantile(0.99))
    df["sales"] = df["sales"].clip(upper=category_caps)

    # 11. Final dtypes
    df["order_date"] = pd.to_datetime(df["order_date"]).dt.date
    df = df.reset_index(drop=True)

    return df


if __name__ == "__main__":
    from pipeline.extract import extract
    raw = extract()
    cleaned = clean(raw)
    print(f"[transform] {len(raw)} raw rows -> {len(cleaned)} cleaned rows")
