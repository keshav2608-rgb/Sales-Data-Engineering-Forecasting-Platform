#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Health Check =="

echo -n "Python: "; python3 --version
echo -n "dbt: "; dbt --version | head -1

if [ -f warehouse/duckdb/sales.duckdb ]; then
  echo "DuckDB warehouse: found ($(du -h warehouse/duckdb/sales.duckdb | cut -f1))"
  python3 -c "
import duckdb
con = duckdb.connect('warehouse/duckdb/sales.duckdb', read_only=True)
for schema, table in [('raw','sales_staging'), ('main_analytics','fact_sales'), ('forecast','forecast_results')]:
    try:
        n = con.execute(f'SELECT COUNT(*) FROM {schema}.{table}').fetchone()[0]
        print(f'  {schema}.{table}: {n} rows')
    except Exception as e:
        print(f'  {schema}.{table}: NOT FOUND ({e})')
"
else
  echo "DuckDB warehouse: NOT FOUND - run 'make pipeline' first"
fi

if [ -n "${GOOGLE_CLOUD_PROJECT:-}" ]; then
  echo "BigQuery: GOOGLE_CLOUD_PROJECT is set (cloud mode available)"
else
  echo "BigQuery: not configured (local-only mode - this is fine, fully supported)"
fi
