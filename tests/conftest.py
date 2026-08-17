"""Shared pytest fixtures with deterministic synthetic data."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@pytest.fixture
def dates_250():
    return pd.bdate_range("2020-01-01", periods=250)


@pytest.fixture
def const_growth_prices(dates_250):
    """Price series growing at a constant 0.1% per day (no volatility)."""
    n = len(dates_250)
    prices = 100.0 * (1.001 ** np.arange(n))
    return pd.Series(prices, index=dates_250, name="Close")


@pytest.fixture
def sine_prices(dates_250):
    """Oscillating price series useful for RSI / mean-reversion tests."""
    n = len(dates_250)
    x = np.linspace(0, 8 * np.pi, n)
    prices = 100.0 + 10.0 * np.sin(x)
    return pd.Series(prices, index=dates_250, name="Close")


@pytest.fixture
def ohlcv(dates_250):
    """A simple, valid OHLCV frame derived from a random-walk-free base."""
    n = len(dates_250)
    rng = np.random.default_rng(42)
    close = 100.0 + np.cumsum(rng.normal(0.05, 1.0, n))
    close = np.maximum(close, 1.0)
    open_ = close - rng.normal(0, 0.5, n)
    high = np.maximum(open_, close) + np.abs(rng.normal(0, 0.5, n))
    low = np.minimum(open_, close) - np.abs(rng.normal(0, 0.5, n))
    vol = rng.integers(1_000, 5_000, n)
    df = pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close,
         "Adj Close": close, "Volume": vol},
        index=dates_250,
    )
    df.index.name = "Date"
    return df


@pytest.fixture
def known_returns():
    """A tiny return series with hand-computable statistics."""
    return pd.Series([0.10, -0.05, 0.20, -0.10, 0.05])
