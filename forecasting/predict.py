"""Generates the actual future forecast using the best model, fit on ALL available history."""
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from forecasting.baseline import naive_forecast, moving_average_forecast, seasonal_naive_forecast


def _future_index(series: pd.Series, horizon: int) -> pd.DatetimeIndex:
    start = series.index.max() + pd.DateOffset(months=1)
    return pd.date_range(start=start, periods=horizon, freq="MS")


def generate_forecast(series: pd.Series, model_name: str, horizon: int, ma_window: int = 3) -> pd.DataFrame:
    future_idx = _future_index(series, horizon)

    if model_name == "Naive":
        preds = naive_forecast(series, horizon)
    elif model_name == "Moving Average":
        preds = moving_average_forecast(series, horizon, window=ma_window)
    elif model_name == "Seasonal Naive":
        preds = seasonal_naive_forecast(series, horizon)
    elif model_name == "Exponential Smoothing":
        seasonal_periods = 12
        use_seasonal = len(series) >= 2 * seasonal_periods
        model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal="add" if use_seasonal else None,
            seasonal_periods=seasonal_periods if use_seasonal else None,
            initialization_method="estimated",
        ).fit()
        preds = model.forecast(horizon).values
    else:
        raise ValueError(f"Unknown model: {model_name}")

    # Simple confidence band: +/- 1.28 std-dev of historical month-over-month
    # residual (roughly an 80% interval), widening slightly with horizon distance.
    residual_std = series.diff().dropna().std()
    widths = np.array([1.28 * residual_std * np.sqrt(i + 1) for i in range(horizon)])

    return pd.DataFrame({
        "forecast_date": future_idx.date,
        "predicted_sales": np.round(preds, 2),
        "lower_bound": np.round(preds - widths, 2),
        "upper_bound": np.round(preds + widths, 2),
        "model_name": model_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })
