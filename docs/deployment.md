# SSH Deployment

Assumes a fresh Ubuntu 22.04+ server you can SSH into.

```bash
ssh user@SERVER_IP

# Install Docker (skip if already installed)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Install git if needed
sudo apt-get update && sudo apt-get install -y git

# Clone
git clone <your-repository-url> sales-data-engineering
cd sales-data-engineering

# Configure environment
cp .env.example .env
# edit .env if you want BigQuery cloud mode; local mode needs no edits

# Option A: run natively (no Docker)
python3 -m venv .venv && source .venv/bin/activate
make setup
make pipeline
make test

# Option B: run via Docker
docker compose build
docker compose up
```

## What `make pipeline` does on the server

Exactly what it does locally: generates/refreshes the dataset, runs quality
checks, cleans, loads into DuckDB (or BigQuery if `ENVIRONMENT=cloud`), runs
dbt, and trains + saves the forecast. No server-specific configuration is
required beyond the `.env` file - DuckDB is just a file on disk.

## Verifying the deployment

```bash
bash scripts/health_check.sh
```

This reports Python/dbt versions, warehouse table row counts, and whether
cloud mode is configured.
