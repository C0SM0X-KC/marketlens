"""Volatility analysis: rolling and annualised volatility."""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from src.config import CONFIG


def rolling_volatility(
    returns: pd.Series, window: int, annualize: bool = True,
    trading_days: Optional[int] = None,
) -> pd.Series:
    """Rolling standard deviation of returns, optionally annualised."""
    td = trading_days or CONFIG.analysis.trading_days
    vol = returns.rolling(window).std(ddof=1)
    if annualize:
        vol = vol * np.sqrt(td)
    return vol


def annualized_volatility(
    returns: pd.Series, trading_days: Optional[int] = None
) -> float:
    """Annualised volatility over the full sample."""
    td = trading_days or CONFIG.analysis.trading_days
    r = returns.dropna()
    if len(r) < 2:
        return float("nan")
    return float(r.std(ddof=1) * np.sqrt(td))


def realized_volatility(
    returns: pd.Series, window: int, trading_days: Optional[int] = None
) -> float:
    """Latest annualised realised volatility over a trailing window."""
    td = trading_days or CONFIG.analysis.trading_days
    r = returns.dropna()
    if len(r) < window:
        return float("nan")
    return float(r.iloc[-window:].std(ddof=1) * np.sqrt(td))


def volatility_frame(returns: pd.Series) -> pd.DataFrame:
    """Both configured rolling windows as one frame for charting."""
    ac = CONFIG.analysis
    return pd.DataFrame(
        {
            f"Vol {ac.vol_short_window}d": rolling_volatility(returns, ac.vol_short_window),
            f"Vol {ac.vol_long_window}d": rolling_volatility(returns, ac.vol_long_window),
        }
    )
