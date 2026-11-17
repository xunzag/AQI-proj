"""Cleaning functions: validity flags, sensor errors, timestamps and daily aggregation.

Design principle: invalid values are turned into NaN (missing), never silently
dropped and never filled in. Gaps stay visible, and every later step decides
explicitly how to handle them (e.g. the 75% completeness rule for daily means).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import SENSORS

INVALID_CODE = -9999          # ARPA's code for "no valid measurement"
VALID_FLAG = "VA"             # stato = VA (valid); NA = not valid
# Upper plausibility limits (µg/m³). Far above anything recorded in Milan, so they
# only catch obvious instrument glitches (e.g. 9999), not real pollution episodes.
PLAUSIBLE_MAX = {"PM10": 1000.0, "PM2.5": 1000.0, "NO2": 1000.0}
STUCK_RUN_HOURS = 6           # >= 6 identical consecutive hourly values = stuck sensor
MIN_HOURS_PER_DAY = 18        # 75% of 24 h, the usual EU completeness criterion


def parse_raw(df: pd.DataFrame) -> pd.DataFrame:
    """Convert raw API columns to proper types and attach pollutant/station names.

    Args:
        df: raw measurements with columns ``idsensore, data, valore, stato``.

    Returns:
        Copy with ``idsensore`` as str, ``data`` as datetime, ``valore`` as float,
        plus ``pollutant`` and ``station`` columns looked up from ``config.SENSORS``.
    """
    out = df.copy()
    out["idsensore"] = out["idsensore"].astype(str)
    out["data"] = pd.to_datetime(out["data"])
    out["valore"] = pd.to_numeric(out["valore"], errors="coerce")
    out["pollutant"] = out["idsensore"].map(lambda s: SENSORS.get(s, (None, None))[0])
    out["station"] = out["idsensore"].map(lambda s: SENSORS.get(s, (None, None))[1])
    return out


def apply_validity(df: pd.DataFrame) -> pd.DataFrame:
    """Set values to NaN where the measurement is not valid, and record why.

    Rules, in order:
      1. ``stato != "VA"`` (ARPA marked it invalid)       -> reason ``flag_invalid``
      2. ``valore == -9999`` (ARPA's missing-value code)   -> reason ``error_code``
      3. ``valore < 0`` (concentrations cannot be negative) -> reason ``negative``
      4. ``valore > PLAUSIBLE_MAX[pollutant]``              -> reason ``implausible_high``

    Returns:
        Copy with ``valore`` cleaned and a new ``invalid_reason`` column (None if valid).
    """
    out = df.copy()
    reason = pd.Series(None, index=out.index, dtype="object")
    max_allowed = out["pollutant"].map(PLAUSIBLE_MAX).fillna(np.inf)
    rules = [
        ("implausible_high", out["valore"] > max_allowed),
        ("negative", out["valore"] < 0),
        ("error_code", out["valore"] == INVALID_CODE),
        ("flag_invalid", out["stato"] != VALID_FLAG),
    ]
    # Apply in reverse priority so the most fundamental reason wins.
    for name, mask in rules:
        reason[mask] = name
    out["invalid_reason"] = reason
    out.loc[reason.notna(), "valore"] = np.nan
    return out


def flag_stuck_values(df: pd.DataFrame, min_run: int = STUCK_RUN_HOURS) -> pd.DataFrame:
    """Set to NaN runs of ``min_run`` or more identical consecutive values per sensor.

    A real hourly NO2 signal changes almost every hour; a flat line usually means the
    analyser is frozen. Only meaningful for hourly data, so call it on hourly sensors.

    Returns:
        Copy with stuck values set to NaN and ``invalid_reason = "stuck"``.
    """
    out = df.sort_values(["idsensore", "data"]).copy()
    if "invalid_reason" not in out:
        out["invalid_reason"] = None
    v = out["valore"]
    new_run = (v != v.groupby(out["idsensore"]).shift()) | v.isna()
    run_id = new_run.cumsum()
    run_len = v.groupby(run_id).transform("size")
    stuck = (run_len >= min_run) & v.notna()
    out.loc[stuck, "invalid_reason"] = "stuck"
    out.loc[stuck, "valore"] = np.nan
    return out


def hour_ending_to_start(ts: pd.Series) -> pd.Series:
    """Convert hour-ending timestamps to hour-starting ones.

    ARPA labels an hourly average by the END of the hour: the value stamped 01:00 is
    the average over 00:00-01:00, and 00:00 is the last hour of the previous day.
    Subtracting one hour puts every value on the day and hour it was measured.
    """
    return ts - pd.Timedelta(hours=1)


def daily_mean_from_hourly(df: pd.DataFrame, min_hours: int = MIN_HOURS_PER_DAY) -> pd.DataFrame:
    """Aggregate hourly values to daily means, keeping only sufficiently complete days.

    Args:
        df: hourly data with columns ``idsensore, data`` (hour-START timestamps), ``valore``.
        min_hours: minimum number of valid hours for a day to count (default 18 = 75%).

    Returns:
        DataFrame ``idsensore, date, valore, n_hours``; days with fewer than
        ``min_hours`` valid hours get ``valore = NaN``.
    """
    d = df.assign(date=df["data"].dt.normalize())
    g = d.groupby(["idsensore", "date"])["valore"]
    daily = g.agg(valore="mean", n_hours="count").reset_index()
    daily.loc[daily["n_hours"] < min_hours, "valore"] = np.nan
    return daily


def to_daily_wide(daily: pd.DataFrame, pollutant: str) -> pd.DataFrame:
    """Pivot daily long data for one pollutant to a date x station table (complete calendar)."""
    sub = daily[daily["pollutant"] == pollutant]
    wide = sub.pivot_table(index="date", columns="station", values="valore", dropna=False)
    full_index = pd.date_range(wide.index.min(), wide.index.max(), freq="D", name="date")
    return wide.reindex(full_index)


def city_mean(wide: pd.DataFrame, min_stations: int = 2) -> pd.Series:
    """Average across stations per day, requiring at least ``min_stations`` valid stations.

    Requiring several stations stops one station's gap from changing what "Milan" means
    on that day; days with too few stations become NaN instead.
    """
    n = wide.notna().sum(axis=1)
    return wide.mean(axis=1).where(n >= min_stations)
