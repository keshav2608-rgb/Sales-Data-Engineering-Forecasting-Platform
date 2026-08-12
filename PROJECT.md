# PROJECT.md - Quick Summary

**What:** End-to-end retail sales data engineering + forecasting platform.
**Stack:** Python, pandas, DuckDB, dbt-core, BigQuery-ready, statsmodels, Docker.
**Skills demonstrated:** ETL/ELT, data quality/validation, dimensional
modeling, dbt (staging/intermediate/marts + tests), time-series forecasting
with proper chronological validation, automated testing (31 pytest + 32 dbt
tests), containerization, SSH deployment docs.

**One command to run everything:**
```bash
cp .env.example .env && make setup && make pipeline
```

**Verified results (this repo, this run):**
- 50,150 raw rows -> 49,922 cleaned rows
- dbt: 9/9 models built, 32/32 tests passed
- Forecasting: 4 models compared, Exponential Smoothing selected (RMSE 58,524)
- Tests: 31/31 pytest passed

See `README.md` for full documentation.
