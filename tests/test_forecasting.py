import numpy as np
import pandas as pd
import pytest

from forecasting.baseline import naive_forecast, moving_average_forecast, seasonal_naive_forecast
from forecasting.evaluate import mae, rmse, mape, evaluate_all
from forecasting.model_selection import chronological_split, compare_models, select_best_model
from forecasting.predict import generate_forecast


def _make_series(n=30, start="2023-01-01"):
    idx = pd.date_range(start=start, periods=n, freq="MS")
    values = 1000 + np.arange(n) * 20 + np.sin(np.arange(n) / 2) * 50
    return pd.Series(values, index=idx)


def test_chronological_split_no_overlap():
    s = _make_series()
    train, test = chronological_split(s, test_fraction=0.2)
    assert train.index.max() < test.index.min()
    assert len(train) + len(test) == len(s)


def test_no_future_leakage_train_before_test():
    s = _make_series()
    train, test = chronological_split(s, test_fraction=0.25)
    # explicit invariant required by spec: training_date < test_date
    assert all(t < test.index.min() for t in train.index)


def test_naive_forecast_shape():
    s = _make_series()
    preds = naive_forecast(s, horizon=6)
    assert len(preds) == 6
    assert np.all(preds == s.iloc[-1])


def test_moving_average_forecast_shape():
    s = _make_series()
    preds = moving_average_forecast(s, horizon=6, window=3)
    assert len(preds) == 6
    assert np.isclose(preds[0], s.iloc[-3:].mean())


def test_seasonal_naive_forecast_shape():
    s = _make_series(n=30)
    preds = seasonal_naive_forecast(s, horizon=6, season_length=12)
    assert len(preds) == 6


def test_metrics_calculate_correctly():
    y_true = [100, 200, 300]
    y_pred = [110, 190, 300]
    assert mae(y_true, y_pred) == pytest.approx(6.67, abs=0.01)
    assert rmse(y_true, y_pred) > 0
    assert mape(y_true, y_pred) > 0
    m = evaluate_all(y_true, y_pred)
    assert set(m.keys()) == {"MAE", "RMSE", "MAPE"}


def test_compare_models_returns_all_models():
    s = _make_series(n=30)
    result = compare_models(s, test_fraction=0.2)
    assert set(result["metrics"].keys()) == {
        "Naive", "Moving Average", "Seasonal Naive", "Exponential Smoothing"
    }
    for name, preds in result["predictions"].items():
        assert len(preds) == len(result["test"])


def test_select_best_model_picks_lowest_rmse():
    metrics = {
        "A": {"MAE": 10, "RMSE": 20, "MAPE": 5},
        "B": {"MAE": 5, "RMSE": 8, "MAPE": 3},
    }
    assert select_best_model(metrics, criterion="RMSE") == "B"


def test_generate_forecast_future_dates_after_history():
    s = _make_series(n=24)
    fc = generate_forecast(s, "Naive", horizon=6)
    assert len(fc) == 6
    assert pd.to_datetime(fc["forecast_date"]).min() > s.index.max()
    assert (fc["upper_bound"] >= fc["lower_bound"]).all()
