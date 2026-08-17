"""Drawdown analysis: running peak, drawdown series, max drawdown stats."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


def drawdown_series(prices: pd.Series) -> pd.DataFrame:
    """Return a frame with running peak and drawdown (fraction, <= 0)."""
    p = prices.dropna()
    peak = p.cummax()
    dd = p / peak - 1.0
    return pd.DataFrame({"Price": p, "Peak": peak, "Drawdown": dd})


def drawdown_from_returns(returns: pd.Series) -> pd.Series:
    """Drawdown series built from a return stream (equity curve based)."""
    equity = (1.0 + returns.fillna(0)).cumprod()
    peak = equity.cummax()
    return equity / peak - 1.0


@dataclass
class DrawdownStats:
    max_drawdown: float
    peak_date: Optional[pd.Timestamp]
    trough_date: Optional[pd.Timestamp]
    recovery_date: Optional[pd.Timestamp]
    current_drawdown: float
    recovered: bool


def max_drawdown_stats(prices: pd.Series) -> DrawdownStats:
    """Locate the maximum drawdown and its peak/trough/recovery dates."""
    frame = drawdown_series(prices)
    dd = frame["Drawdown"]
    if dd.empty:
        return DrawdownStats(float("nan"), None, None, None, float("nan"), False)

    trough_date = dd.idxmin()
    max_dd = float(dd.loc[trough_date])

    # Peak = last date at/above prior high before the trough.
    pre = frame.loc[:trough_date]
    peak_date = pre["Price"].idxmax()
    peak_price = frame.loc[peak_date, "Price"]

    # Recovery = first date after trough where price regains the peak.
    post = frame.loc[trough_date:]
    recovered_mask = post["Price"] >= peak_price
    recovery_date = post.index[recovered_mask.argmax()] if recovered_mask.any() else None
    recovered = recovery_date is not None

    current_dd = float(dd.iloc[-1])
    return DrawdownStats(
        max_drawdown=max_dd,
        peak_date=peak_date,
        trough_date=trough_date,
        recovery_date=recovery_date,
        current_drawdown=current_dd,
        recovered=recovered,
    )


def max_drawdown(prices: pd.Series) -> float:
    """Convenience: maximum drawdown as a negative fraction."""
    return max_drawdown_stats(prices).max_drawdown
