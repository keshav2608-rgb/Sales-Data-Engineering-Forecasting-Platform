"""Full forecasting pipeline: prepare -> compare models -> select best -> forecast -> save."""
import json
from pathlib import Path

from forecasting.prepare_data import load_monthly_series
from forecasting.model_selection import compare_models, select_best_model, print_comparison_table
from forecasting.predict import generate_forecast
from forecasting.save_forecast import save_forecast

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"


def run_forecasting_pipeline(horizon: int = 6, test_fraction: float = 0.2):
    series = load_monthly_series()
    print(f"[forecast] Loaded {len(series)} months of history "
          f"({series.index.min().date()} to {series.index.max().date()})")

    if len(series) < 6:
        print("[forecast] Not enough history for a train/test split (<6 months). Skipping.")
        return None

    comparison = compare_models(series, test_fraction=test_fraction)
    best_model = select_best_model(comparison["metrics"], criterion="RMSE")

    print("\nModel comparison (chronological hold-out test set):")
    print_comparison_table(comparison["metrics"], best_model)
    print(f"\n[forecast] Selected best model: {best_model} (lowest RMSE)")

    forecast_df = generate_forecast(series, best_model, horizon=horizon)
    save_forecast(forecast_df)

    MODELS_DIR.mkdir(exist_ok=True)
    with open(MODELS_DIR / "model_comparison.json", "w") as f:
        json.dump({"metrics": comparison["metrics"], "best_model": best_model}, f, indent=2)
    with open(MODELS_DIR / "MODEL_CARD.md", "w") as f:
        f.write(_model_card(comparison["metrics"], best_model, horizon, len(series)))

    print("\nForecast (next {} months):".format(horizon))
    print(forecast_df.to_string(index=False))

    return {"comparison": comparison, "best_model": best_model, "forecast": forecast_df}


def _model_card(metrics, best_model, horizon, n_months) -> str:
    lines = [
        "# Forecast Model Card\n",
        f"- History used: {n_months} months",
        f"- Forecast horizon: {horizon} months",
        f"- Selection criterion: lowest RMSE on chronological hold-out test set",
        f"- Best model: **{best_model}**\n",
        "## Model comparison\n",
        "| Model | MAE | RMSE | MAPE |",
        "|---|---|---|---|",
    ]
    for name, m in metrics.items():
        marker = " **(best)**" if name == best_model else ""
        lines.append(f"| {name}{marker} | {m['MAE']} | {m['RMSE']} | {m['MAPE']}% |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    run_forecasting_pipeline()
