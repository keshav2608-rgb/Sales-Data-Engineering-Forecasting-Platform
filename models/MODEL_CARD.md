# Forecast Model Card

- History used: 42 months
- Forecast horizon: 6 months
- Selection criterion: lowest RMSE on chronological hold-out test set
- Best model: **Exponential Smoothing**

## Model comparison

| Model | MAE | RMSE | MAPE |
|---|---|---|---|
| Naive | 53918.97 | 61787.88 | 4.35% |
| Moving Average | 54535.16 | 64712.87 | 4.53% |
| Seasonal Naive | 63971.21 | 77675.96 | 5.17% |
| Exponential Smoothing **(best)** | 49944.64 | 58524.39 | 4.12% |
