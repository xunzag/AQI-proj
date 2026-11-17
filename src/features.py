"""Feature engineering for the next-day PM10 forecast.

Rule that prevents data leakage: every feature for the row dated ``t`` uses only
information available at the end of day ``t``. The target is PM10 on day ``t + 1``.
Calendar features describe the target day, which is known in advance.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TARGET = "pm10_next_day"


def make_features(city: pd.DataFrame) -> pd.DataFrame:
    """Build a feature table from the daily city series.

    Args:
        city: daily DataFrame with columns ``PM10``, ``PM2.5``, ``NO2`` and a complete
            daily DatetimeIndex.

    Returns:
        DataFrame indexed by day ``t`` with lag/rolling/calendar features and the
        target column ``pm10_next_day`` (PM10 on day ``t + 1``).
    """
    c = city.asfreq("D")
    f = pd.DataFrame(index=c.index)

    for lag in (0, 1, 2, 6):  # lag 0 = today, lag 6 = same weekday last week (relative to tomorrow)
        f[f"pm10_lag{lag}"] = c["PM10"].shift(lag)
    f["pm25_lag0"] = c["PM2.5"].shift(0)
    f["no2_lag0"] = c["NO2"].shift(0)
    f["no2_lag1"] = c["NO2"].shift(1)

    f["pm10_mean3"] = c["PM10"].rolling(3, min_periods=2).mean()
    f["pm10_mean7"] = c["PM10"].rolling(7, min_periods=5).mean()
    f["pm10_change1"] = c["PM10"] - c["PM10"].shift(1)

    target_day = c.index + pd.Timedelta(days=1)
    doy = target_day.day_of_year
    f["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)  # sin/cos so 31 Dec and 1 Jan are close
    f["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    f["target_dow"] = target_day.day_of_week
    f["target_is_sunday"] = (target_day.day_of_week == 6).astype(int)

    f[TARGET] = c["PM10"].shift(-1)
    return f


def time_split(df: pd.DataFrame, train_end: str, valid_end: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split chronologically: train < ``train_end`` <= valid < ``valid_end`` <= test.

    No shuffling: the model is always evaluated on days that come after everything
    it was trained on, just like a real forecast.
    """
    train = df[df.index < train_end]
    valid = df[(df.index >= train_end) & (df.index < valid_end)]
    test = df[df.index >= valid_end]
    return train, valid, test


def regression_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict:
    """MAE, RMSE and bias (mean of prediction minus truth), in µg/m³."""
    err = np.asarray(y_pred) - np.asarray(y_true)
    return {"MAE": float(np.mean(np.abs(err))), "RMSE": float(np.sqrt(np.mean(err ** 2))), "bias": float(np.mean(err))}
