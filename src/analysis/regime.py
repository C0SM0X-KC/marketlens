"""Volatility-based market regime detection.

Regimes are classified by comparing current rolling volatility against its own
historical distribution using configurable percentile thresholds. This is a
descriptive classification of market conditions, not a forecast.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from src.analysis.volatility import rolling_volatility
from src.config import CONFIG

REGIME_LABELS = ["Low", "Normal", "High"]


def regime_series(
    returns: pd.Series,
    vol_window: Optional[int] = None,
    low_pct: Optional[float] = None,
    high_pct: Optional[float] = None,
) -> pd.DataFrame:
    """Classify each date into Low/Normal/High volatility regime.

    Thresholds are computed from the *expanding* historical distribution of
    volatility up to each point, so the classification uses only information
    available at that time (no look-ahead).
    """
    ac = CONFIG.analysis
    vw = vol_window or ac.regime_vol_window
    lo = ac.regime_low_pct if low_pct is None else low_pct
    hi = ac.regime_high_pct if high_pct is None else high_pct

    vol = rolling_volatility(returns, vw, annualize=True)
    vol = vol.dropna()
    if vol.empty:
        return pd.DataFrame(columns=["Volatility", "LowThresh", "HighThresh", "Regime"])

    low_thr = vol.expanding(min_periods=vw).quantile(lo)
    high_thr = vol.expanding(min_periods=vw).quantile(hi)

    regime = pd.Series(index=vol.index, dtype="object")
    regime[vol <= low_thr] = "Low"
    regime[(vol > low_thr) & (vol < high_thr)] = "Normal"
    regime[vol >= high_thr] = "High"
    regime = regime.fillna("Normal")

    return pd.DataFrame(
        {
            "Volatility": vol,
            "LowThresh": low_thr,
            "HighThresh": high_thr,
            "Regime": regime,
        }
    )


def current_regime(returns: pd.Series, **kwargs) -> str:
    df = regime_series(returns, **kwargs)
    if df.empty:
        return "Unknown"
    return str(df["Regime"].iloc[-1])


def performance_by_regime(returns: pd.Series, **kwargs) -> pd.DataFrame:
    """Average daily return and annualised volatility grouped by regime."""
    df = regime_series(returns, **kwargs)
    if df.empty:
        return pd.DataFrame(columns=["Days", "AvgDailyReturn", "AnnVol", "Share"])
    joined = df.join(returns.rename("Return"), how="inner")
    td = CONFIG.analysis.trading_days
    out = joined.groupby("Regime")["Return"].agg(
        Days="count",
        AvgDailyReturn="mean",
        AnnVol=lambda s: s.std(ddof=1) * np.sqrt(td),
    )
    out["Share"] = out["Days"] / out["Days"].sum()
    # Order Low, Normal, High.
    out = out.reindex([r for r in REGIME_LABELS if r in out.index])
    return out
