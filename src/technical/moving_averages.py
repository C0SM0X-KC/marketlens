"""Moving averages: SMA and EMA."""
from __future__ import annotations

import pandas as pd

from src.config import CONFIG


def sma(prices: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return prices.rolling(window=window, min_periods=window).mean()


def ema(prices: pd.Series, span: int) -> pd.Series:
    """Exponential moving average (span-based, standard adjust=False)."""
    return prices.ewm(span=span, adjust=False, min_periods=span).mean()


def moving_average_frame(prices: pd.Series) -> pd.DataFrame:
    """All configured SMAs and EMAs for charting."""
    ac = CONFIG.analysis
    data = {}
    for w in ac.sma_windows:
        data[f"SMA{w}"] = sma(prices, w)
    for w in ac.ema_windows:
        data[f"EMA{w}"] = ema(prices, w)
    return pd.DataFrame(data)
