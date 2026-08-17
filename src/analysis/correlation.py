"""Cross-market analysis: correlation matrices and rolling correlation."""
from __future__ import annotations

from typing import List, Optional

import pandas as pd

from src.config import CONFIG


def correlation_matrix(returns: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    """Full-sample correlation matrix of asset returns."""
    return returns.dropna(how="all").corr(method=method)


def rolling_correlation(
    returns: pd.DataFrame, asset_a: str, asset_b: str, window: Optional[int] = None
) -> pd.Series:
    """Rolling correlation between two return columns."""
    w = window or CONFIG.analysis.rolling_corr_window
    a = returns[asset_a]
    b = returns[asset_b]
    return a.rolling(w).corr(b)


def comparative_cumulative_returns(returns: pd.DataFrame) -> pd.DataFrame:
    """Cumulative return of each asset, aligned from the common start date."""
    aligned = returns.dropna(how="any")
    return (1.0 + aligned).cumprod() - 1.0


def volatility_comparison(
    returns: pd.DataFrame, window: Optional[int] = None
) -> pd.DataFrame:
    """Rolling annualised volatility for each asset (for comparison charts)."""
    import numpy as np

    from src.config import CONFIG as _C

    w = window or _C.analysis.vol_short_window
    td = _C.analysis.trading_days
    return returns.rolling(w).std(ddof=1) * np.sqrt(td)
