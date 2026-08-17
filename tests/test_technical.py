"""Tests for technical indicators."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.technical import momentum
from src.technical import moving_averages as ma
from src.technical import volatility_indicators as vi


def test_sma_known_values():
    prices = pd.Series([1, 2, 3, 4, 5], dtype=float)
    s = ma.sma(prices, 3)
    assert np.isnan(s.iloc[1])
    assert s.iloc[2] == pytest.approx(2.0)
    assert s.iloc[4] == pytest.approx(4.0)


def test_ema_first_value_and_recursion():
    prices = pd.Series([1, 2, 3, 4, 5], dtype=float)
    e = ma.ema(prices, 3)
    # pandas ewm(adjust=False) recursion from x0: y_t = y_{t-1} + a*(x_t - y_{t-1}).
    # a = 2/(3+1) = 0.5. y0=1, y1=1.5, y2=2.25, y3=3.125.
    # min_periods=3 masks indices 0,1 as NaN; index 2 onward are defined.
    assert e.iloc[2] == pytest.approx(2.25)
    assert e.iloc[3] == pytest.approx(3.125)


def test_rsi_all_gains_is_100():
    prices = pd.Series(np.arange(1, 40, dtype=float))  # strictly increasing
    r = momentum.rsi(prices, 14).dropna()
    assert (r > 99.9).all()


def test_rsi_all_losses_is_zero():
    prices = pd.Series(np.arange(40, 1, -1, dtype=float))  # strictly decreasing
    r = momentum.rsi(prices, 14).dropna()
    assert (r < 0.1).all()


def test_rsi_bounds(sine_prices):
    r = momentum.rsi(sine_prices, 14).dropna()
    assert r.between(0, 100).all()


def test_macd_zero_for_constant_series():
    prices = pd.Series([50.0] * 100)
    m = momentum.macd(prices)
    assert m["MACD"].abs().max() == pytest.approx(0.0, abs=1e-9)
    assert m["Histogram"].abs().max() == pytest.approx(0.0, abs=1e-9)


def test_macd_histogram_identity(sine_prices):
    m = momentum.macd(sine_prices)
    assert (m["Histogram"] - (m["MACD"] - m["Signal"])).abs().max() == pytest.approx(0.0, abs=1e-12)


def test_bollinger_band_ordering_and_middle(ohlcv):
    bb = vi.bollinger_bands(ohlcv["Close"], 20, 2.0).dropna()
    assert (bb["Upper"] >= bb["Middle"]).all()
    assert (bb["Middle"] >= bb["Lower"]).all()
    # Middle equals 20-day SMA.
    sma20 = ma.sma(ohlcv["Close"], 20)
    assert (bb["Middle"] - sma20.loc[bb.index]).abs().max() == pytest.approx(0.0, abs=1e-9)


def test_bollinger_width_matches_std():
    prices = pd.Series(np.arange(1, 60, dtype=float))
    bb = vi.bollinger_bands(prices, 20, 2.0).dropna()
    width = bb["Upper"] - bb["Lower"]
    std = prices.rolling(20).std(ddof=0)
    assert (width - 4 * std.loc[bb.index]).abs().max() == pytest.approx(0.0, abs=1e-9)


def test_atr_positive_and_bounded(ohlcv):
    a = vi.atr(ohlcv["High"], ohlcv["Low"], ohlcv["Close"], 14).dropna()
    assert (a > 0).all()
    tr = vi.true_range(ohlcv["High"], ohlcv["Low"], ohlcv["Close"]).dropna()
    assert a.max() <= tr.max() + 1e-9


def test_true_range_components():
    high = pd.Series([10.0, 12.0])
    low = pd.Series([8.0, 9.0])
    close = pd.Series([9.0, 11.0])
    tr = vi.true_range(high, low, close)
    # Second bar: max(12-9, |12-9|, |9-9|) = 3.
    assert tr.iloc[1] == pytest.approx(3.0)
