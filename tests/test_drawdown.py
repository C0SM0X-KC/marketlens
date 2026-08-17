"""Tests for drawdown analysis."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis import drawdown


def test_max_drawdown_known_path():
    # Peak 120 at idx1, trough 60 at idx3 => -50%.
    idx = pd.bdate_range("2021-01-01", periods=6)
    prices = pd.Series([100, 120, 90, 60, 80, 130], index=idx, dtype=float)
    stats = drawdown.max_drawdown_stats(prices)
    assert stats.max_drawdown == pytest.approx(-0.5)
    assert stats.peak_date == idx[1]
    assert stats.trough_date == idx[3]
    # Recovers when price exceeds prior peak of 120 (=130 at idx5).
    assert stats.recovery_date == idx[5]
    assert stats.recovered is True


def test_no_drawdown_monotonic(const_growth_prices):
    stats = drawdown.max_drawdown_stats(const_growth_prices)
    assert stats.max_drawdown == pytest.approx(0.0, abs=1e-12)
    assert stats.current_drawdown == pytest.approx(0.0, abs=1e-12)


def test_unrecovered_drawdown():
    idx = pd.bdate_range("2021-01-01", periods=4)
    prices = pd.Series([100, 150, 120, 110], index=idx, dtype=float)
    stats = drawdown.max_drawdown_stats(prices)
    assert stats.max_drawdown == pytest.approx(110 / 150 - 1.0)
    assert stats.recovered is False
    assert stats.recovery_date is None


def test_drawdown_series_non_positive(ohlcv):
    dd = drawdown.drawdown_series(ohlcv["Close"])["Drawdown"]
    assert (dd <= 1e-9).all()


def test_drawdown_from_returns_matches_prices():
    idx = pd.bdate_range("2021-01-01", periods=6)
    prices = pd.Series([100, 120, 90, 60, 80, 130], index=idx, dtype=float)
    ret = prices.pct_change().fillna(0)
    dd_ret = drawdown.drawdown_from_returns(ret)
    dd_px = drawdown.drawdown_series(prices)["Drawdown"]
    assert dd_ret.min() == pytest.approx(dd_px.min())
