"""Rule-based trend classification.

This is an explicit, transparent set of rules over moving averages. It is NOT a
prediction model — it summarises the current price structure relative to its
moving averages.

    Bullish : Price > SMA_fast AND SMA_fast > SMA_slow
    Bearish : Price < SMA_fast AND SMA_fast < SMA_slow
    Neutral : otherwise
"""
from __future__ import annotations

from typing import Optional

import pandas as pd

from src.config import CONFIG
from src.technical.moving_averages import sma


def trend_series(
    prices: pd.Series,
    fast: Optional[int] = None,
    slow: Optional[int] = None,
) -> pd.Series:
    """Classify each date as Bullish / Bearish / Neutral."""
    ac = CONFIG.analysis
    f = fast or ac.trend_fast_ma
    s = slow or ac.trend_slow_ma
    sma_f = sma(prices, f)
    sma_s = sma(prices, s)

    out = pd.Series("Neutral", index=prices.index, dtype="object")
    bullish = (prices > sma_f) & (sma_f > sma_s)
    bearish = (prices < sma_f) & (sma_f < sma_s)
    out[bullish] = "Bullish"
    out[bearish] = "Bearish"
    # Where MAs are undefined, mark Neutral (default already set).
    out[sma_f.isna() | sma_s.isna()] = "Neutral"
    return out


def current_trend(
    prices: pd.Series, fast: Optional[int] = None, slow: Optional[int] = None
) -> str:
    s = trend_series(prices, fast, slow)
    return str(s.iloc[-1]) if len(s) else "Neutral"
