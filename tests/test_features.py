import numpy as np
import pandas as pd

from src.features import TARGET, make_features, time_split


def _city(n=30):
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    return pd.DataFrame({"PM10": np.arange(n, dtype=float), "PM2.5": 1.0, "NO2": 2.0}, index=idx)


def test_target_is_next_day_and_features_use_past_only():
    f = make_features(_city())
    day = pd.Timestamp("2020-01-10")  # PM10 that day = 9
    assert f.loc[day, TARGET] == 10          # tomorrow's value
    assert f.loc[day, "pm10_lag0"] == 9      # today's value
    assert f.loc[day, "pm10_lag1"] == 8
    assert f.loc[day, "pm10_mean3"] == 8     # mean of 7, 8, 9: no future values


def test_changing_the_future_does_not_change_features():
    city = _city()
    changed = city.copy()
    changed.loc["2020-01-11":, "PM10"] = 999.0
    a = make_features(city).drop(columns=TARGET).loc[:"2020-01-10"]
    b = make_features(changed).drop(columns=TARGET).loc[:"2020-01-10"]
    pd.testing.assert_frame_equal(a, b)


def test_time_split_is_chronological_and_disjoint():
    f = make_features(_city())
    tr, va, te = time_split(f, "2020-01-11", "2020-01-21")
    assert tr.index.max() < va.index.min() and va.index.max() < te.index.min()
    assert len(tr) + len(va) + len(te) == len(f)
