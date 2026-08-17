"""Performance metrics for equity curves and trade lists."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Optional

import numpy as np
import pandas as pd

from src.config import CONFIG


def total_return(equity: pd.Series) -> float:
    e = equity.dropna()
    if len(e) < 2:
        return float("nan")
    return float(e.iloc[-1] / e.iloc[0] - 1.0)


def cagr(equity: pd.Series, trading_days: Optional[int] = None) -> float:
    td = trading_days or CONFIG.analysis.trading_days
    e = equity.dropna()
    if len(e) < 2:
        return float("nan")
    # N equity points span N-1 return periods.
    years = (len(e) - 1) / td
    growth = e.iloc[-1] / e.iloc[0]
    if years <= 0 or growth <= 0:
        return float("nan")
    return float(growth ** (1.0 / years) - 1.0)


def annualized_volatility(returns: pd.Series, trading_days: Optional[int] = None) -> float:
    td = trading_days or CONFIG.analysis.trading_days
    r = returns.dropna()
    if len(r) < 2:
        return float("nan")
    return float(r.std(ddof=1) * np.sqrt(td))


def sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: Optional[float] = None,
    trading_days: Optional[int] = None,
) -> float:
    """Annualised Sharpe ratio from a daily return series."""
    td = trading_days or CONFIG.analysis.trading_days
    rf = CONFIG.analysis.risk_free_rate if risk_free_rate is None else risk_free_rate
    r = returns.dropna()
    if len(r) < 2:
        return float("nan")
    daily_rf = rf / td
    excess = r - daily_rf
    sd = excess.std(ddof=1)
    if sd == 0 or np.isnan(sd):
        return float("nan")
    return float(excess.mean() / sd * np.sqrt(td))


def max_drawdown(equity: pd.Series) -> float:
    e = equity.dropna()
    if e.empty:
        return float("nan")
    peak = e.cummax()
    dd = e / peak - 1.0
    return float(dd.min())


@dataclass
class PerformanceMetrics:
    total_return: float
    cagr: float
    ann_volatility: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    avg_trade_return: float
    profit_factor: float

    def as_dict(self) -> dict:
        return asdict(self)


def trade_stats(trade_returns: List[float]) -> dict:
    """Win rate, average trade return, profit factor from per-trade returns."""
    arr = np.array([t for t in trade_returns if t is not None and not np.isnan(t)])
    n = len(arr)
    if n == 0:
        return {
            "win_rate": float("nan"),
            "num_trades": 0,
            "avg_trade_return": float("nan"),
            "profit_factor": float("nan"),
        }
    wins = arr[arr > 0]
    losses = arr[arr < 0]
    gross_profit = wins.sum()
    gross_loss = -losses.sum()
    if gross_loss == 0:
        profit_factor = float("inf") if gross_profit > 0 else float("nan")
    else:
        profit_factor = float(gross_profit / gross_loss)
    return {
        "win_rate": float(len(wins) / n),
        "num_trades": int(n),
        "avg_trade_return": float(arr.mean()),
        "profit_factor": profit_factor,
    }


def compute_metrics(
    equity: pd.Series,
    returns: pd.Series,
    trade_returns: Optional[List[float]] = None,
    risk_free_rate: Optional[float] = None,
) -> PerformanceMetrics:
    ts = trade_stats(trade_returns or [])
    return PerformanceMetrics(
        total_return=total_return(equity),
        cagr=cagr(equity),
        ann_volatility=annualized_volatility(returns),
        sharpe=sharpe_ratio(returns, risk_free_rate),
        max_drawdown=max_drawdown(equity),
        win_rate=ts["win_rate"],
        num_trades=ts["num_trades"],
        avg_trade_return=ts["avg_trade_return"],
        profit_factor=ts["profit_factor"],
    )
