.PHONY: setup ingest transform load dbt-run dbt-test pipeline forecast test dashboard clean docker-build docker-up health

PY := python3

setup:
	pip install --break-system-packages -r requirements.txt
	@echo "Setup complete. Run 'make pipeline' to execute the full pipeline."

ingest:
	$(PY) -m ingestion.download_data

transform:
	$(PY) -c "from pipeline.extract import extract; from pipeline.transform import clean; \
	raw = extract(); c = clean(raw); print(f'{len(raw)} raw -> {len(c)} clean rows')"

load:
	$(PY) -m pipeline.load

dbt-run:
	cd dbt && DBT_PROFILES_DIR=. dbt run

dbt-test:
	cd dbt && DBT_PROFILES_DIR=. dbt test

dbt-docs:
	cd dbt && DBT_PROFILES_DIR=. dbt docs generate

forecast:
	$(PY) -m forecasting.train

pipeline:
	$(PY) -m pipeline.pipeline

test:
	$(PY) -m pytest tests/ -v

dashboard:
	@echo "Dashboard data is ready in DuckDB (main_analytics schema) and data/processed/."
	@echo "See dashboard/README.md for Looker Studio connection instructions."

health:
	bash scripts/health_check.sh

docker-build:
	docker compose build

docker-up:
	docker compose up

clean:
	rm -rf dbt/target dbt/logs dbt/dbt_packages .pytest_cache
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned build artifacts. Data and warehouse files preserved (use 'make clean-all' to wipe those too)."

clean-all: clean
	rm -f warehouse/duckdb/sales.duckdb data/raw/sales_raw.csv data/raw/sales_raw.metadata.json
	rm -rf data/processed/*
