# Dashboard Setup (Looker Studio)

Looker Studio can't be configured headlessly from this sandbox (it's a
browser-based Google product with no CLI/API for dashboard creation), so
here are exact manual steps. The dashboard itself is 100% free.

## If using LOCAL (DuckDB) mode

Looker Studio doesn't connect to DuckDB directly. Two options:

**Option A (recommended for a portfolio demo):** Export the marts to CSV
and use Looker Studio's native "File Upload" / "Google Sheets" connector:
```bash
python3 -c "
import duckdb
con = duckdb.connect('warehouse/duckdb/sales.duckdb', read_only=True)
for t in ['sales_daily','sales_monthly','fact_sales','dim_product','dim_customer']:
    con.execute(f\"COPY main_analytics.{t} TO 'data/processed/{t}.csv' (HEADER, DELIMITER ',')\")
"
```
Upload the resulting CSVs (in `data/processed/`) to Google Sheets, then
connect Looker Studio to that Sheet.

**Option B:** Switch to CLOUD mode (see `docs/warehouse.md`) and use
Looker Studio's native BigQuery connector directly - no export step needed.

## Connecting Looker Studio to BigQuery (cloud mode)

1. Go to https://lookerstudio.google.com -> Create -> Data source.
2. Choose the **BigQuery** connector.
3. Select your project -> `sales_analytics` dataset -> pick a table (start
   with `sales_monthly` and `fact_sales`).
4. Click **Connect**, then **Create Report**.

## Pages to build

### Page 1 - Executive Overview
- Scorecards: Total Revenue, Total Orders, Average Order Value, Total
  Customers, Revenue Growth (MoM) - all sourced from `sales_monthly` /
  `dim_customer`.
- Time series: revenue over time (`sales_monthly.total_revenue` by
  `month_start`).
- Bar chart: revenue by category (`dim_product`, grouped by `category`).
- Bar chart: revenue by region (`fact_sales`, grouped by `region`).

### Page 2 - Sales Analysis
- Time series: daily/monthly revenue.
- Table: top products by revenue (`dim_product`, sorted descending).
- Bar chart: top categories.
- Map or bar chart: regional performance.
- Table: customer performance (`dim_customer`, `total_revenue` desc).
- Filters: date range control, region dropdown, category dropdown, product
  search.

### Page 3 - Forecast
- Combo chart: historical `sales_monthly.total_revenue` (line) plus
  `forecast_results.predicted_sales` (dashed line) continuing from the last
  historical point, with `lower_bound`/`upper_bound` as a shaded band.
- Scorecards: forecast horizon (6 months), model used (see
  `models/MODEL_CARD.md`), model accuracy (RMSE from
  `models/model_comparison.json`).

See `dashboard/dashboard_design.md` for layout/style guidance and
`dashboard/metrics.md` for the exact metric definitions used throughout.
