"""
ingestion/download_data.py

Produces the raw source dataset under data/raw/, with an immutable copy
and a metadata sidecar (source, download_time, row/col counts, checksum).

NOTE ON DATA SOURCE:
This sandbox environment has no network access to Kaggle (kaggle.com is not
on the allowed egress list). Rather than faking a "download" or silently
using a different real dataset, this script generates a realistic synthetic
retail sales transaction dataset with the same shape, column semantics, and
realistic messiness (nulls, duplicates, bad types, inconsistent casing,
outliers) that a real Kaggle retail sales dataset would have. This keeps the
entire pipeline honest end-to-end while remaining 100% free and reproducible.

To use a real Kaggle dataset instead (e.g. "Superstore Sales" or the
"Store Item Demand Forecasting" dataset), download the CSV manually on a
machine with internet + Kaggle credentials, drop it at
data/raw/sales_raw.csv, and skip running this script. The rest of the
pipeline (ingestion/ingest.py onward) is dataset-agnostic as long as the
column names in docs/data-dictionary.md are respected.

See docs/data-source.md for full details.
"""
import hashlib
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load_config():
    with open(ROOT / "config" / "config.yaml") as f:
        return yaml.safe_load(f)


def _generate_clean_base(cfg) -> pd.DataFrame:
    rng = np.random.default_rng(cfg["dataset"]["seed"])
    random.seed(cfg["dataset"]["seed"])

    n = cfg["dataset"]["n_orders"]
    start = pd.Timestamp(cfg["dataset"]["start_date"])
    end = pd.Timestamp(cfg["dataset"]["end_date"])
    days_range = (end - start).days

    categories = {
        "Electronics": ["Wireless Mouse", "USB-C Hub", "Bluetooth Speaker", "Laptop Stand", "Webcam"],
        "Furniture": ["Office Chair", "Standing Desk", "Bookshelf", "Filing Cabinet", "Desk Lamp"],
        "Office Supplies": ["Notebook Pack", "Stapler", "Printer Paper", "Sticky Notes", "Pen Set"],
        "Apparel": ["T-Shirt", "Hoodie", "Cap", "Socks Pack", "Jacket"],
        "Home & Kitchen": ["Blender", "Coffee Maker", "Cutlery Set", "Toaster", "Air Fryer"],
    }
    regions = {
        "North America": ["USA", "Canada", "Mexico"],
        "Europe": ["Germany", "France", "UK"],
        "Asia": ["India", "Japan", "Singapore"],
    }
    segments = ["Consumer", "Corporate", "Home Office"]

    n_customers = max(500, n // 12)
    n_products = sum(len(v) for v in categories.values())

    product_rows = []
    pid = 1000
    for cat, items in categories.items():
        for item in items:
            pid += 1
            product_rows.append({
                "product_id": f"P-{pid}",
                "product_name": item,
                "category": cat,
                "unit_price": round(rng.uniform(8, 450), 2),
            })
    products_df = pd.DataFrame(product_rows)

    customer_ids = [f"C-{10000+i}" for i in range(n_customers)]
    customer_names = [f"Customer {i}" for i in range(n_customers)]

    rows = []
    for i in range(n):
        order_date = start + timedelta(days=int(rng.integers(0, days_range + 1)))
        # seasonal bump: Nov/Dec higher volume (simulated by resampling more orders near year end downstream)
        prod = products_df.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        cust_idx = int(rng.integers(0, n_customers))
        region = random.choice(list(regions.keys()))
        country = random.choice(regions[region])
        quantity = int(rng.integers(1, 8))
        discount = round(random.choice([0, 0, 0, 0.05, 0.1, 0.15, 0.2]), 2)
        unit_price = prod["unit_price"]
        sales = round(quantity * unit_price * (1 - discount), 2)

        rows.append({
            "order_id": f"ORD-{100000+i}",
            "order_date": order_date.strftime("%Y-%m-%d"),
            "customer_id": customer_ids[cust_idx],
            "customer_name": customer_names[cust_idx],
            "product_id": prod["product_id"],
            "product_name": prod["product_name"],
            "category": prod["category"],
            "quantity": quantity,
            "unit_price": unit_price,
            "sales": sales,
            "discount": discount,
            "region": region,
            "country": country,
            "segment": random.choice(segments),
        })

    return pd.DataFrame(rows)


def _inject_realistic_mess(df: pd.DataFrame, cfg) -> pd.DataFrame:
    rng = np.random.default_rng(cfg["dataset"]["seed"] + 1)
    df = df.copy()
    n = len(df)

    # 1. Duplicate transactions (~0.3%)
    dupe_idx = rng.choice(n, size=int(n * 0.003), replace=False)
    df = pd.concat([df, df.iloc[dupe_idx]], ignore_index=True)

    # 2. Missing customer_id (~0.1%)
    miss_cust = rng.choice(df.index, size=int(len(df) * 0.001), replace=False)
    df.loc[miss_cust, "customer_id"] = None

    # 3. Missing region (~0.2%)
    miss_region = rng.choice(df.index, size=int(len(df) * 0.002), replace=False)
    df.loc[miss_region, "region"] = None

    # 4. Missing category (~0.1%)
    miss_cat = rng.choice(df.index, size=int(len(df) * 0.001), replace=False)
    df.loc[miss_cat, "category"] = None

    # 5. Inconsistent category casing (~2%)
    case_idx = rng.choice(df.index, size=int(len(df) * 0.02), replace=False)
    variants = [str.upper, str.lower, str.title]
    for i in case_idx:
        cat = df.at[i, "category"]
        if isinstance(cat, str):
            df.at[i, "category"] = random.choice(variants)(cat)

    # 6. Invalid quantities (negative or zero) (~0.05%)
    bad_qty = rng.choice(df.index, size=max(1, int(len(df) * 0.0005)), replace=False)
    df.loc[bad_qty, "quantity"] = -1

    # 7. Invalid / malformed dates (~0.02%)
    bad_date = rng.choice(df.index, size=max(1, int(len(df) * 0.0002)), replace=False)
    df.loc[bad_date, "order_date"] = "not-a-date"

    # 8. Missing / bad unit_price (~0.1%)
    bad_price = rng.choice(df.index, size=int(len(df) * 0.001), replace=False)
    df.loc[bad_price, "unit_price"] = None

    # 9. Outliers in sales (~0.05%) - fat-fingered quantity entries
    out_idx = rng.choice(df.index, size=max(1, int(len(df) * 0.0005)), replace=False)
    df.loc[out_idx, "sales"] = df.loc[out_idx, "sales"] * 50

    # 10. Whitespace / casing mess in customer_name
    ws_idx = rng.choice(df.index, size=int(len(df) * 0.01), replace=False)
    for i in ws_idx:
        name = df.at[i, "customer_name"]
        if isinstance(name, str):
            df.at[i, "customer_name"] = f"  {name.upper()}  "

    return df.sample(frac=1, random_state=cfg["dataset"]["seed"]).reset_index(drop=True)


def download_data():
    cfg = _load_config()
    raw_dir = ROOT / cfg["paths"]["raw_dir"]
    raw_dir.mkdir(parents=True, exist_ok=True)

    print("[ingestion] Generating source dataset (synthetic retail sales, Kaggle-shaped)...")
    base = _generate_clean_base(cfg)
    messy = _inject_realistic_mess(base, cfg)

    out_path = raw_dir / "sales_raw.csv"
    messy.to_csv(out_path, index=False)

    checksum = hashlib.sha256(out_path.read_bytes()).hexdigest()
    metadata = {
        "source": "synthetic_generator (Kaggle-shaped substitute; see docs/data-source.md)",
        "download_time": datetime.utcnow().isoformat() + "Z",
        "filename": out_path.name,
        "row_count": int(len(messy)),
        "column_count": int(messy.shape[1]),
        "checksum_sha256": checksum,
    }
    with open(raw_dir / "sales_raw.metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"[ingestion] Wrote {metadata['row_count']} rows, {metadata['column_count']} cols -> {out_path}")
    print(f"[ingestion] checksum={checksum[:16]}...")
    return out_path, metadata


if __name__ == "__main__":
    download_data()
