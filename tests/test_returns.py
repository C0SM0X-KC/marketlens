"""Tests for return analysis."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis import returns


def test_daily_returns_basic():
    prices = pd.Series([100.0, 110.0, 99.0])
    r = returns.daily_returns(prices)
    assert np.isnan(r.iloc[0])
    assert r.iloc[1] == pytest.approx(0.10)
    assert r.iloc[2] == pytest.approx(-0.10)


def test_cumulative_returns():
    r = pd.Series([0.10, -0.05, 0.20])
    cum = returns.cumulative_returns(r)
    assert cum.iloc[-1] == pytest.approx(1.1 * 0.95 * 1.2 - 1.0)


def test_period_return_constant(const_growth_prices):
    assert returns.period_return(const_growth_prices, 1) == pytest.approx(0.001)


def test_total_return(const_growth_prices):
    p = const_growth_prices
    expected = p.iloc[-1] / p.iloc[0] - 1.0
    assert returns.total_return(p) == pytest.approx(expected)


def test_cagr_constant_growth(const_growth_prices):
    p = const_growth_prices
    years = (len(p) - 1) / 252  # N prices span N-1 periods
    expected = (p.iloc[-1] / p.iloc[0]) ** (1 / years) - 1
    assert returns.cagr(p, trading_days=252) == pytest.approx(expected)


def test_cagr_from_returns_matches_cagr(const_growth_prices):
    r = const_growth_prices.pct_change().dropna()
    c_from_ret = returns.cagr_from_returns(r, trading_days=252)
    c_from_px = returns.cagr(const_growth_prices, trading_days=252)
    assert c_from_ret == pytest.approx(c_from_px, rel=1e-6)


def test_ytd_return_uses_prior_year_close():
    idx = pd.to_datetime(["2022-12-30", "2023-01-03", "2023-06-01"])
    prices = pd.Series([100.0, 101.0, 110.0], index=idx)
    assert returns.ytd_return(prices) == pytest.approx(0.10)


def test_resample_returns_monthly_compounding():
    idx = pd.bdate_range("2023-01-01", periods=40)
    r = pd.Series(0.01, index=idx)
    monthly = returns.resample_returns(r, "ME")
    # First full-ish month should compound ~1.01**k - 1 > 0.
    assert (monthly.dropna() > 0).all()
