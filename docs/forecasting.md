# Forecasting

## Target
Monthly total revenue (`sales_monthly.total_revenue` from the dbt mart).
Monthly was chosen over daily because the dataset spans ~42 months - plenty
for monthly seasonality, but daily series would be noisy with only ~50k
total transactions spread across it.

## Models compared

| Model | Description |
|---|---|
| Naive | Repeats the last observed month's value |
| Moving Average | Repeats the mean of the last 3 months |
| Seasonal Naive | Repeats the same month from last year (12-month lag) |
| Exponential Smoothing | Holt-Winters with additive trend + seasonality (statsmodels) |

XGBoost/Prophet were considered but not added: the series is short (~42
monthly points), so a gradient-boosted model has little to learn from and
Prophet's extra dependency weight isn't justified when Holt-Winters already
captures trend + seasonality well. This is a deliberate "don't blindly add
complex ML" choice, not a limitation.

## Train/test split - chronological, not random

`forecasting/model_selection.py::chronological_split` takes the **first**
80% of months as train and the **last** 20% as test - never a random
shuffle, since shuffling would leak future information into the training
set for a time series. This is enforced with an explicit assertion
(`train.index.max() < test.index.min()`) and covered by
`tests/test_forecasting.py::test_no_future_leakage_train_before_test`.

## Evaluation

MAE, RMSE, and MAPE are computed on the chronological hold-out test set for
every model. The model with the **lowest RMSE** is selected
(`select_best_model`). Example run on the synthetic dataset:

```
Model                            MAE        RMSE        MAPE
------------------------------------------------------------
Naive                       53918.97    61787.88        4.35
Moving Average              54535.16    64712.87        4.53
Seasonal Naive              63971.21    77675.96        5.17
Exponential Smoothing       49944.64    58524.39        4.12  <-- best
```

The winning model is re-fit on **all** available history (not just the
training split) before generating the actual future forecast - the
train/test split is only used to pick which model to trust, per standard
practice.

## Forecast horizon

Default 6 months (`config/config.yaml::forecasting.horizon`, overridable via
`FORECAST_HORIZON` env var). Confidence bounds are a simple +/-1.28 std-dev
band (approx. 80% interval) of historical month-over-month change, widening
with `sqrt(horizon distance)` to reflect growing uncertainty further out.

## Data leakage prevention

- Chronological split only (see above).
- The future forecast is generated from `series` (all history) using
  `forecasting/predict.py::generate_forecast`, called *after* model
  selection is already locked in from the held-out comparison - the winning
  model's hyperparameters aren't re-tuned using the forecast period.
- `tests/test_forecasting.py` explicitly asserts `train.index.max() <
  test.index.min()` for every split.

## Output

Saved to:
- `forecast.forecast_results` table in DuckDB (or BigQuery in cloud mode)
- `data/processed/forecast_results.csv` and `.parquet` (dashboard-ready,
  warehouse-mode-independent)
- `models/model_comparison.json` and `models/MODEL_CARD.md` (full metrics +
  narrative writeup, regenerated on every run)
