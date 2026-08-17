"""Tests for volatility analysis."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis import volatility


def test_annualized_volatility_scaling():
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0, 0.01, 1000))
    daily_std = r.std(ddof=1)
    assert volatility.annualized_volatility(r, 252) == pytest.approx(daily_std * np.sqrt(252))


def test_zero_volatility_constant_returns():
    r = pd.Series([0.001] * 100)
    assert volatility.annualized_volatility(r) == pytest.approx(0.0, abs=1e-12)


def test_rolling_volatility_window_length(const_growth_prices):
    r = const_growth_prices.pct_change()
    vol = volatility.rolling_volatility(r, 20)
    # First 20 (window) values undefined (need 20 non-null returns after the NaN).
    assert vol.iloc[:20].isna().all()
    assert not np.isnan(vol.iloc[-1])


def test_realized_volatility_matches_manual():
    rng = np.random.default_rng(1)
    r = pd.Series(rng.normal(0, 0.02, 300))
    window = 20
    expected = r.iloc[-window:].std(ddof=1) * np.sqrt(252)
    assert volatility.realized_volatility(r, window) == pytest.approx(expected)


def test_realized_volatility_insufficient_data():
    r = pd.Series([0.01, 0.02])
    assert np.isnan(volatility.realized_volatility(r, 20))
