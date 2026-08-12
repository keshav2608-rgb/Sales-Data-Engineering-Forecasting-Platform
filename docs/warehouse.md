# Warehouse Setup

## LOCAL MODE (default, no setup required)

The pipeline writes to a DuckDB file at `warehouse/duckdb/sales.duckdb`.
DuckDB is embedded (like SQLite but analytical/columnar) - there's no server
to run, no credentials, no network calls. `dbt/profiles.yml` points at this
file by default (`target: local`). This is genuinely free with no limits
beyond your disk.

Inspect it directly:
```bash
python3 -c "
import duckdb
con = duckdb.connect('warehouse/duckdb/sales.duckdb', read_only=True)
print(con.execute('SELECT * FROM main_analytics.sales_monthly').fetchdf())
"
```

## CLOUD MODE (BigQuery, opt-in)

### 1. Create/use a Google Cloud project
```bash
gcloud projects create my-sales-project
gcloud config set project my-sales-project
```

### 2. Enable BigQuery
```bash
gcloud services enable bigquery.googleapis.com
```

### 3. Create a service account + key
```bash
gcloud iam service-accounts create sales-pipeline \
  --display-name "Sales Pipeline"
gcloud projects add-iam-policy-binding my-sales-project \
  --member="serviceAccount:sales-pipeline@my-sales-project.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
gcloud iam service-accounts keys create credentials/sa-key.json \
  --iam-account=sales-pipeline@my-sales-project.iam.gserviceaccount.com
```
`credentials/` is gitignored - never commit this key.

### 4. Configure environment variables
In `.env`:
```
ENVIRONMENT=cloud
GOOGLE_CLOUD_PROJECT=my-sales-project
GOOGLE_APPLICATION_CREDENTIALS=./credentials/sa-key.json
BIGQUERY_DATASET=sales_analytics
```

### 5. Create datasets
```bash
bq mk --dataset --location=US my-sales-project:sales_staging
bq mk --dataset --location=US my-sales-project:sales_analytics
bq mk --dataset --location=US my-sales-project:sales_forecast
```

### 6. Test connectivity
```bash
python3 -c "
from google.cloud import bigquery
client = bigquery.Client()
print('Connected to project:', client.project)
"
```

### 7. Run the pipeline
```bash
ENVIRONMENT=cloud make pipeline
cd dbt && DBT_PROFILES_DIR=. dbt run --target cloud
```

## Free-tier limits (BigQuery Sandbox, as of this writing)

- 10 GiB storage free
- 1 TiB of queries free per month
- No credit card required for the sandbox tier, but a **billing account IS
  required** if you want to move beyond sandbox limits (e.g. scheduled
  queries, higher quotas) - this project stays comfortably inside sandbox
  limits at the ~50k-row scale used here.
- Partitioning `fact_sales`/`sales_staging` by `order_date` (see
  `warehouse/bigquery/schema.sql`) keeps query costs low by letting BigQuery
  skip irrelevant partitions.

## This project was verified in LOCAL mode only

No GCP credentials were available in the build sandbox, so BigQuery mode
was **not executed** - the code is correct and follows the BigQuery Python
client + dbt-bigquery adapter APIs, but you should run `dbt debug --target
cloud` yourself after setting up credentials to confirm connectivity before
trusting cloud mode in production.
