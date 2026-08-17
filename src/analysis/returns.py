"""Return analysis: period returns, cumulative returns, CAGR."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from src.config import CONFIG


def daily_returns(prices: pd.Series) -> pd.Series:
    """Simple daily percentage returns."""
    return prices.pct_change()


def cumulative_returns(returns: pd.Series) -> pd.Series:
    """Cumulative growth of 1 unit given a series of simple returns."""
    return (1.0 + returns.fillna(0)).cumprod() - 1.0


def period_return(prices: pd.Series, periods: int) -> float:
    """Total simple return over the last ``periods`` observations."""
    p = prices.dropna()
    if len(p) <= periods:
        return float("nan")
    return float(p.iloc[-1] / p.iloc[-1 - periods] - 1.0)


def trailing_returns(prices: pd.Series) -> dict:
    """Standard trailing returns used on the overview page."""
    return {
        "daily": period_return(prices, 1),
        "weekly": period_return(prices, 5),
        "monthly": period_return(prices, 21),
        "ytd": ytd_return(prices),
    }


def ytd_return(prices: pd.Series) -> float:
    p = prices.dropna()
    if p.empty:
        return float("nan")
    last_date = p.index[-1]
    year_start = pd.Timestamp(year=last_date.year, month=1, day=1)
    prior = p[p.index < year_start]
    if prior.empty:
        # Not enough history before this year: use first obs of the year.
        this_year = p[p.index >= year_start]
        if len(this_year) < 2:
            return float("nan")
        base = this_year.iloc[0]
    else:
        base = prior.iloc[-1]
    return float(p.iloc[-1] / base - 1.0)


def total_return(prices: pd.Series) -> float:
    p = prices.dropna()
    if len(p) < 2:
        return float("nan")
    return float(p.iloc[-1] / p.iloc[0] - 1.0)


def cagr(prices: pd.Series, trading_days: Optional[int] = None) -> float:
    """Compound annual growth rate from a price series."""
    td = trading_days or CONFIG.analysis.trading_days
    p = prices.dropna()
    if len(p) < 2:
        return float("nan")
    # N price observations span N-1 return periods.
    n_years = (len(p) - 1) / td
    if n_years <= 0:
        return float("nan")
    growth = p.iloc[-1] / p.iloc[0]
    if growth <= 0:
        return float("nan")
    return float(growth ** (1.0 / n_years) - 1.0)


def cagr_from_returns(returns: pd.Series, trading_days: Optional[int] = None) -> float:
    td = trading_days or CONFIG.analysis.trading_days
    r = returns.dropna()
    if r.empty:
        return float("nan")
    growth = float((1.0 + r).prod())
    n_years = len(r) / td
    if n_years <= 0 or growth <= 0:
        return float("nan")
    return growth ** (1.0 / n_years) - 1.0


def resample_returns(returns: pd.Series, rule: str) -> pd.Series:
    """Compound daily returns to a lower frequency (e.g. 'W', 'ME', 'YE')."""
    return (1.0 + returns.fillna(0)).resample(rule).prod() - 1.0
