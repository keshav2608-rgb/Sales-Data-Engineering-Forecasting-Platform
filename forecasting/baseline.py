"""Baseline forecasting models: naive and moving average."""
import numpy as np
import pandas as pd


def naive_forecast(train: pd.Series, horizon: int) -> np.ndarray:
    """Repeats the last observed value for the whole horizon."""
    last_value = train.iloc[-1]
    return np.full(horizon, last_value)


def moving_average_forecast(train: pd.Series, horizon: int, window: int = 3) -> np.ndarray:
    """Repeats the mean of the last `window` observations for the whole horizon."""
    avg = train.iloc[-window:].mean()
    return np.full(horizon, avg)


def seasonal_naive_forecast(train: pd.Series, horizon: int, season_length: int = 12) -> np.ndarray:
    """Repeats the value from the same period last season, if enough history exists."""
    if len(train) < season_length:
        return naive_forecast(train, horizon)
    seasonal_values = train.iloc[-season_length:].values
    reps = int(np.ceil(horizon / season_length))
    return np.tile(seasonal_values, reps)[:horizon]
