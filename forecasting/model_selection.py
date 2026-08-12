"""
Chronological (never random) train/test split, model comparison, and best-model
selection for the monthly revenue time series.

Leakage prevention: the split index is strictly time-ordered (train = earlier
months, test = later months). No test-period value is ever used to fit or
tune a model - see tests/test_forecasting.py::test_no_leakage.
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from forecasting.baseline import naive_forecast, moving_average_forecast, seasonal_naive_forecast
from forecasting.evaluate import evaluate_all


def chronological_split(series: pd.Series, test_fraction: float = 0.2):
    n = len(series)
    split_idx = max(1, int(n * (1 - test_fraction)))
    train, test = series.iloc[:split_idx], series.iloc[split_idx:]
    assert train.index.max() < test.index.min(), "Leakage: train period overlaps test period"
    return train, test


def _fit_exp_smoothing(train: pd.Series, horizon: int):
    seasonal_periods = 12
    use_seasonal = len(train) >= 2 * seasonal_periods
    model = ExponentialSmoothing(
        train,
        trend="add",
        seasonal="add" if use_seasonal else None,
        seasonal_periods=seasonal_periods if use_seasonal else None,
        initialization_method="estimated",
    ).fit()
    return model.forecast(horizon).values


def compare_models(series: pd.Series, test_fraction: float = 0.2, ma_window: int = 3) -> dict:
    train, test = chronological_split(series, test_fraction)
    horizon = len(test)

    predictions = {
        "Naive": naive_forecast(train, horizon),
        "Moving Average": moving_average_forecast(train, horizon, window=ma_window),
        "Seasonal Naive": seasonal_naive_forecast(train, horizon),
        "Exponential Smoothing": _fit_exp_smoothing(train, horizon),
    }

    results = {}
    for name, preds in predictions.items():
        results[name] = evaluate_all(test.values, preds)

    return {"train": train, "test": test, "predictions": predictions, "metrics": results}


def select_best_model(metrics: dict, criterion: str = "RMSE") -> str:
    return min(metrics.keys(), key=lambda m: metrics[m][criterion])


def print_comparison_table(metrics: dict, best_model: str) -> None:
    print(f"{'Model':<24}{'MAE':>12}{'RMSE':>12}{'MAPE':>12}")
    print("-" * 60)
    for name, m in metrics.items():
        marker = "  <-- best" if name == best_model else ""
        print(f"{name:<24}{m['MAE']:>12}{m['RMSE']:>12}{m['MAPE']:>12}{marker}")
