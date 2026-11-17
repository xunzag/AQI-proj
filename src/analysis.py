"""Small analysis helpers: annual means with coverage, robust trends, calendar windows."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, theilslopes


def annual_means(daily: pd.DataFrame, min_coverage: float = 0.75) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Annual mean of each column, set to NaN when fewer than ``min_coverage`` of days are valid.

    Args:
        daily: DataFrame indexed by date (one column per series).
        min_coverage: required share of valid days in the year.

    Returns:
        (annual means, coverage share) — both indexed by year.
    """
    year = daily.index.year
    coverage = daily.notna().groupby(year).mean()
    means = daily.groupby(year).mean().where(coverage >= min_coverage)
    return means, coverage


def theil_sen_trend(series: pd.Series) -> dict:
    """Robust linear trend of a yearly series (index = year).

    Theil–Sen takes the median of the slopes between every pair of points, so one
    unusual year cannot drag the line the way it can with ordinary least squares.
    The Kendall tau test tells us whether the series moves consistently in one direction.

    Returns:
        dict with slope (units/year), 95% CI bounds, Kendall tau and its p-value.
    """
    s = series.dropna()
    slope, intercept, lo, hi = theilslopes(s.values, s.index.values, alpha=0.95)
    tau, p = kendalltau(s.index.values, s.values)
    return {"slope_per_year": slope, "ci_low": lo, "ci_high": hi, "kendall_tau": tau, "p_value": p}


def window_mean(daily: pd.Series, year: int, start_md: str, end_md: str) -> float:
    """Mean of a daily series between two month-day strings (inclusive) in a given year.

    Example: ``window_mean(s, 2020, "03-09", "05-03")`` is the mean over 9 March – 3 May 2020.
    """
    start = pd.Timestamp(f"{year}-{start_md}")
    end = pd.Timestamp(f"{year}-{end_md}")
    return float(daily.loc[start:end].mean())


def window_table(daily: pd.DataFrame, years: list[int], start_md: str, end_md: str) -> pd.DataFrame:
    """Window means for every column and every year: rows = years, columns = series."""
    return pd.DataFrame(
        {y: {c: window_mean(daily[c], y, start_md, end_md) for c in daily.columns} for y in years}
    ).T.rename_axis("year")


def pct_change(new: float | pd.Series, base: float | pd.Series):
    """Percentage change from ``base`` to ``new`` (works on numbers and on aligned pandas objects)."""
    return 100 * (new / base - 1)
