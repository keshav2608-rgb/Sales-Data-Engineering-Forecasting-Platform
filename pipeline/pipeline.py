"""
End-to-end pipeline orchestrator.

Orchestration choice: a plain Python function chain, not Airflow.
Rationale (see docs/architecture.md): this project's pipeline is a short,
linear, single-machine batch job (ingest -> quality -> clean -> load -> dbt
-> forecast). Airflow's scheduler/webserver/metadata-DB stack adds real
operational weight (Postgres, Docker services, DAG-parsing overhead) for no
benefit at this scale, and makes the project harder to run on a bare SSH
box. If this pipeline needed multi-team scheduling, retries-with-SLAs, or
cross-pipeline dependencies, Airflow would earn its place - it doesn't here.
A DAG-shaped equivalent (ingestion >> quality >> transform >> load >>
forecasting) is documented in airflow/dags/sales_pipeline.py.dag_spec.md
for reference.
"""
import subprocess
import sys
from pathlib import Path

from ingestion.download_data import download_data
from pipeline.extract import extract
from pipeline.quality_checks import run_quality_checks, print_quality_report
from pipeline.transform import clean
from pipeline.load import load

ROOT = Path(__file__).resolve().parents[1]


class QualityGateError(Exception):
    pass


def run_pipeline(run_dbt: bool = True, run_forecast: bool = True):
    print("\n### STEP 1/7: INGEST ###")
    download_data()

    print("\n### STEP 2/7: EXTRACT ###")
    raw_df = extract()

    print("\n### STEP 3/7: DATA QUALITY CHECKS ###")
    report = run_quality_checks(raw_df)
    print_quality_report(report)

    # Quality gate: fail the pipeline if data is catastrophically bad
    invalid_rate = report["rows_flagged_invalid"] / max(report["rows_processed"], 1)
    if invalid_rate > 0.5:
        raise QualityGateError(
            f"{invalid_rate:.1%} of rows flagged invalid - exceeds 50% threshold. Aborting."
        )

    print("\n### STEP 4/7: CLEAN / TRANSFORM ###")
    clean_df = clean(raw_df)
    print(f"[pipeline] {len(raw_df)} raw -> {len(clean_df)} clean rows "
          f"({len(raw_df) - len(clean_df)} dropped)")

    print("\n### STEP 5/7: LOAD TO WAREHOUSE ###")
    mode = load(clean_df)

    if run_dbt:
        print("\n### STEP 6/7: DBT RUN + TEST ###")
        _run_dbt()
    else:
        print("\n### STEP 6/7: DBT (skipped) ###")

    if run_forecast:
        print("\n### STEP 7/7: FORECASTING ###")
        from forecasting.train import run_forecasting_pipeline
        run_forecasting_pipeline()
    else:
        print("\n### STEP 7/7: FORECASTING (skipped) ###")

    print(f"\n[pipeline] COMPLETE. Warehouse mode: {mode}")
    return {"quality_report": report, "warehouse_mode": mode, "clean_rows": len(clean_df)}


def _run_dbt():
    dbt_dir = ROOT / "dbt"
    env = {"DBT_PROFILES_DIR": str(dbt_dir)}
    import os
    full_env = {**os.environ, **env}
    for cmd in (["dbt", "run"], ["dbt", "test"]):
        print(f"[pipeline] $ {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=dbt_dir, env=full_env, capture_output=True, text=True)
        print(result.stdout[-4000:])
        if result.returncode != 0:
            print(result.stderr[-4000:])
            raise RuntimeError(f"dbt command failed: {' '.join(cmd)}")


if __name__ == "__main__":
    run_pipeline()
