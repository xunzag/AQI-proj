import numpy as np
import pandas as pd

from src.clean import (
    apply_validity,
    city_mean,
    daily_mean_from_hourly,
    flag_stuck_values,
    hour_ending_to_start,
    parse_raw,
)


def _raw(values, stati, sensor="5531", start="2020-01-01 01:00", freq="h"):
    n = len(values)
    return pd.DataFrame({
        "idsensore": [sensor] * n,
        "data": pd.date_range(start, periods=n, freq=freq).strftime("%Y-%m-%dT%H:%M:%S.000"),
        "valore": values,
        "stato": stati,
    })


def test_parse_raw_maps_pollutant_and_types():
    df = parse_raw(_raw(["12.5", "-9999"], ["VA", "NA"]))
    assert df["pollutant"].tolist() == ["NO2", "NO2"]
    assert df["valore"].dtype == float
    assert pd.api.types.is_datetime64_any_dtype(df["data"])


def test_apply_validity_sets_nan_with_reasons():
    df = parse_raw(_raw([10, -9999, -3, 5000, 20], ["VA", "NA", "VA", "VA", "NA"]))
    out = apply_validity(df)
    assert out["valore"].isna().tolist() == [False, True, True, True, True]
    reasons = out["invalid_reason"].fillna("ok").tolist()
    assert reasons == ["ok", "flag_invalid", "negative", "implausible_high", "flag_invalid"]
    assert len(out) == len(df)  # invalid rows are kept, not dropped


def test_flag_stuck_values_only_long_runs():
    vals = [1, 2, 7, 7, 7, 7, 7, 7, 3, 4, 4, 4]
    df = apply_validity(parse_raw(_raw(vals, ["VA"] * len(vals))))
    out = flag_stuck_values(df, min_run=6)
    assert out["valore"].isna().sum() == 6           # the six 7s
    assert out["valore"].iloc[-3:].notna().all()     # a run of three 4s is fine


def test_hour_ending_to_start_moves_midnight_to_previous_day():
    ts = pd.Series(pd.to_datetime(["2020-01-02 00:00", "2020-01-01 01:00"]))
    out = hour_ending_to_start(ts)
    assert out.dt.date.astype(str).tolist() == ["2020-01-01", "2020-01-01"]


def test_daily_mean_requires_min_hours():
    hours = pd.date_range("2020-01-01", periods=48, freq="h")
    vals = np.r_[np.full(24, 10.0), np.full(24, np.nan)]
    vals[24:24 + 17] = 30.0  # day 2 has only 17 valid hours -> rejected
    df = pd.DataFrame({"idsensore": "5531", "data": hours, "valore": vals})
    daily = daily_mean_from_hourly(df, min_hours=18)
    assert daily["valore"].iloc[0] == 10.0
    assert np.isnan(daily["valore"].iloc[1])
    assert daily["n_hours"].tolist() == [24, 17]


def test_city_mean_requires_min_stations():
    wide = pd.DataFrame({"A": [10.0, 10.0, np.nan], "B": [20.0, np.nan, np.nan]})
    out = city_mean(wide, min_stations=2)
    assert out.iloc[0] == 15.0
    assert out.iloc[1:].isna().all()
