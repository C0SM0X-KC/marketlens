"""Volatility indicators: Bollinger Bands and ATR."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from src.config import CONFIG


def bollinger_bands(
    prices: pd.Series,
    window: Optional[int] = None,
    n_std: Optional[float] = None,
) -> pd.DataFrame:
    """Bollinger Bands: middle (SMA), upper and lower bands, and %B width."""
    ac = CONFIG.analysis
    w = window or ac.bb_window
    k = n_std if n_std is not None else ac.bb_std
    mid = prices.rolling(w, min_periods=w).mean()
    std = prices.rolling(w, min_periods=w).std(ddof=0)
    upper = mid + k * std
    lower = mid - k * std
    width = (upper - lower) / mid
    return pd.DataFrame(
        {"Middle": mid, "Upper": upper, "Lower": lower, "Width": width}
    )


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """True Range component of ATR."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr


def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: Optional[int] = None,
) -> pd.Series:
    """Average True Range using Wilder's smoothing."""
    p = period or CONFIG.analysis.atr_period
    tr = true_range(high, low, close)
    return tr.ewm(alpha=1.0 / p, min_periods=p, adjust=False).mean()
