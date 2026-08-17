"""Momentum indicators: RSI and MACD."""
from __future__ import annotations

from typing import Optional

import pandas as pd

from src.config import CONFIG


def rsi(prices: pd.Series, period: Optional[int] = None) -> pd.Series:
    """Relative Strength Index using Wilder's smoothing.

    RSI = 100 - 100 / (1 + RS), where RS is the ratio of average gains to
    average losses over ``period``, smoothed exponentially (Wilder).
    """
    p = period or CONFIG.analysis.rsi_period
    delta = prices.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    # Wilder's smoothing == EMA with alpha = 1/period.
    avg_gain = gain.ewm(alpha=1.0 / p, min_periods=p, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / p, min_periods=p, adjust=False).mean()

    rs = avg_gain / avg_loss
    out = 100.0 - (100.0 / (1.0 + rs))
    # When avg_loss == 0 => RS is inf => RSI 100. When both zero => 50 (neutral).
    out = out.where(avg_loss != 0, 100.0)
    out = out.where(~((avg_gain == 0) & (avg_loss == 0)), 50.0)
    return out


def macd(
    prices: pd.Series,
    fast: Optional[int] = None,
    slow: Optional[int] = None,
    signal: Optional[int] = None,
) -> pd.DataFrame:
    """MACD line, signal line and histogram."""
    ac = CONFIG.analysis
    f = fast or ac.macd_fast
    s = slow or ac.macd_slow
    sig = signal or ac.macd_signal

    ema_fast = prices.ewm(span=f, adjust=False).mean()
    ema_slow = prices.ewm(span=s, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=sig, adjust=False).mean()
    hist = macd_line - signal_line
    return pd.DataFrame(
        {"MACD": macd_line, "Signal": signal_line, "Histogram": hist}
    )
