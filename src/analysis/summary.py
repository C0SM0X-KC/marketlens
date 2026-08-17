"""Data-driven research snapshot generation.

Produces a small set of factual observations about an asset strictly from
computed metrics. It never gives advice, recommendations, or forecasts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from src.analysis import drawdown, regime, returns, trend, volatility
from src.config import CONFIG
from src.technical import momentum


@dataclass
class Snapshot:
    trend: str
    regime: str
    rsi: float
    ytd: float
    max_drawdown: float
    current_drawdown: float
    ann_vol: float
    observations: List[str]


def _pct(x: float, signed: bool = False) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "n/a"
    return f"{x*100:+.1f}%" if signed else f"{x*100:.1f}%"


def build_snapshot(df: pd.DataFrame, name: str = "the asset") -> Snapshot:
    px = df["Adj Close"] if "Adj Close" in df.columns else df["Close"]
    ret = df["Return"]

    cur_trend = trend.current_trend(px)
    cur_regime = regime.current_regime(ret)
    rsi_val = float(momentum.rsi(px).iloc[-1])
    ytd = returns.ytd_return(px)
    dd_stats = drawdown.max_drawdown_stats(px)
    ann_vol = volatility.realized_volatility(ret, CONFIG.analysis.vol_short_window)

    obs: List[str] = []

    # Trend
    if cur_trend == "Bullish":
        obs.append(f"{name} is in a rule-based **bullish** structure (price above SMA50, SMA50 above SMA200).")
    elif cur_trend == "Bearish":
        obs.append(f"{name} is in a rule-based **bearish** structure (price below SMA50, SMA50 below SMA200).")
    else:
        obs.append(f"{name} shows a **neutral** trend structure (mixed alignment of price and moving averages).")

    # Volatility regime
    obs.append(
        f"Volatility regime is **{cur_regime}**, with 20-day annualised volatility around {_pct(ann_vol)}."
    )

    # Momentum
    if rsi_val >= 70:
        obs.append(f"14-day RSI is **{rsi_val:.0f}**, in overbought territory (>70).")
    elif rsi_val <= 30:
        obs.append(f"14-day RSI is **{rsi_val:.0f}**, in oversold territory (<30).")
    else:
        obs.append(f"14-day RSI is **{rsi_val:.0f}**, in a neutral momentum range.")

    # Drawdown
    if not pd.isna(dd_stats.current_drawdown):
        if dd_stats.current_drawdown <= -0.001:
            obs.append(
                f"Currently **{_pct(dd_stats.current_drawdown)}** below its running peak; "
                f"the largest historical drawdown in the window was {_pct(dd_stats.max_drawdown)}."
            )
        else:
            obs.append(
                f"Trading at or near its running peak; the largest historical drawdown in the "
                f"window was {_pct(dd_stats.max_drawdown)}."
            )

    # YTD
    if not pd.isna(ytd):
        obs.append(f"Year-to-date change is **{_pct(ytd, signed=True)}**.")

    return Snapshot(
        trend=cur_trend,
        regime=cur_regime,
        rsi=rsi_val,
        ytd=ytd,
        max_drawdown=dd_stats.max_drawdown,
        current_drawdown=dd_stats.current_drawdown,
        ann_vol=ann_vol,
        observations=obs[:5],
    )
