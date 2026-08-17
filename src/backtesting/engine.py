"""Event-agnostic vectorised backtesting engine.

Design choices that prevent look-ahead bias and unrealistic execution:

  * A strategy produces a target position from data up to day t.
  * The engine applies a one-bar lag: the position held *during* day t is the
    signal generated on day t-1. Returns for day t are therefore earned on a
    decision made with only prior information.
  * Transaction costs and slippage are charged on the turnover incurred when
    the executed position changes.

The engine returns an equity curve, a buy-&-hold benchmark, a trade log and a
full set of performance metrics (gross and net of costs).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
import pandas as pd

from src.backtesting.metrics import PerformanceMetrics, compute_metrics
from src.backtesting.transaction_costs import CostModel
from src.config import CONFIG
from src.strategies.base import Strategy


@dataclass
class Trade:
    entry_date: pd.Timestamp
    exit_date: Optional[pd.Timestamp]
    entry_price: float
    exit_price: Optional[float]
    bars_held: int
    return_pct: float          # net per-trade return


@dataclass
class BacktestResult:
    strategy_name: str
    asset_key: str
    equity: pd.Series              # net-of-cost strategy equity
    gross_equity: pd.Series        # gross (no costs) strategy equity
    benchmark_equity: pd.Series    # buy & hold
    strategy_returns: pd.Series    # net daily returns
    benchmark_returns: pd.Series
    position: pd.Series            # executed position (0/1) each day
    trades: List[Trade]
    metrics: PerformanceMetrics
    gross_metrics: PerformanceMetrics
    benchmark_metrics: PerformanceMetrics
    params: dict = field(default_factory=dict)

    def trades_dataframe(self) -> pd.DataFrame:
        if not self.trades:
            return pd.DataFrame(
                columns=[
                    "entry_date", "exit_date", "entry_price",
                    "exit_price", "bars_held", "return_pct",
                ]
            )
        return pd.DataFrame([t.__dict__ for t in self.trades])


def _extract_trades(
    executed_pos: pd.Series,
    price: pd.Series,
    net_returns: pd.Series,
) -> List[Trade]:
    """Reconstruct round-trip trades from the executed position series."""
    trades: List[Trade] = []
    pos = executed_pos.to_numpy()
    idx = executed_pos.index
    in_trade = False
    entry_i = 0
    for i in range(len(pos)):
        if not in_trade and pos[i] == 1:
            in_trade = True
            entry_i = i
        # Close when position returns to flat, or on the final bar.
        exiting = in_trade and (pos[i] == 0 or i == len(pos) - 1)
        if exiting:
            exit_i = i
            # Net return over the holding period (inclusive of costs already in
            # net_returns for the days the position was held, entry bar .. exit).
            span = net_returns.iloc[entry_i : exit_i + 1]
            trade_ret = float((1.0 + span.fillna(0)).prod() - 1.0)
            trades.append(
                Trade(
                    entry_date=idx[entry_i],
                    exit_date=idx[exit_i],
                    entry_price=float(price.iloc[entry_i]),
                    exit_price=float(price.iloc[exit_i]),
                    bars_held=exit_i - entry_i,
                    return_pct=trade_ret,
                )
            )
            in_trade = False
    return trades


def run_backtest(
    df: pd.DataFrame,
    strategy: Strategy,
    asset_key: str = "",
    initial_capital: Optional[float] = None,
    cost_model: Optional[CostModel] = None,
    risk_free_rate: Optional[float] = None,
) -> BacktestResult:
    """Run a single-asset long/flat backtest."""
    capital = initial_capital or CONFIG.backtest.initial_capital
    costs = cost_model or CostModel.from_config()

    data = df.dropna(subset=["Close"]).copy()
    price = data["Close"]
    asset_ret = price.pct_change().fillna(0.0)

    # Signals from the strategy, then a one-bar execution lag.
    raw_signal = strategy.generate_signals(data).reindex(data.index).fillna(0.0)
    executed_pos = raw_signal.shift(1).fillna(0.0)

    # Turnover and cost drag.
    turnover = executed_pos.diff().abs().fillna(executed_pos.abs())
    cost_drag = turnover * costs.cost_fraction()

    gross_ret = executed_pos * asset_ret
    net_ret = gross_ret - cost_drag

    gross_equity = capital * (1.0 + gross_ret).cumprod()
    equity = capital * (1.0 + net_ret).cumprod()
    benchmark_equity = capital * (1.0 + asset_ret).cumprod()

    trades = _extract_trades(executed_pos, price, net_ret)
    trade_returns = [t.return_pct for t in trades]

    metrics = compute_metrics(equity, net_ret, trade_returns, risk_free_rate)
    gross_metrics = compute_metrics(gross_equity, gross_ret, trade_returns, risk_free_rate)
    benchmark_metrics = compute_metrics(benchmark_equity, asset_ret, None, risk_free_rate)

    return BacktestResult(
        strategy_name=strategy.describe(),
        asset_key=asset_key,
        equity=equity,
        gross_equity=gross_equity,
        benchmark_equity=benchmark_equity,
        strategy_returns=net_ret,
        benchmark_returns=asset_ret,
        position=executed_pos,
        trades=trades,
        metrics=metrics,
        gross_metrics=gross_metrics,
        benchmark_metrics=benchmark_metrics,
        params=strategy.params(),
    )


def split_dev_oos(
    df: pd.DataFrame,
    dev_start: Optional[str] = None,
    dev_end: Optional[str] = None,
    oos_start: Optional[str] = None,
    oos_end: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a frame into development and out-of-sample windows.

    Falls back gracefully when the requested ranges exceed available history.
    """
    bt = CONFIG.backtest
    ds = pd.Timestamp(dev_start or bt.dev_start)
    de = pd.Timestamp(dev_end or bt.dev_end)
    os_ = pd.Timestamp(oos_start or bt.oos_start)
    oe = pd.Timestamp(oos_end or bt.oos_end)

    dev = df[(df.index >= ds) & (df.index <= de)]
    oos = df[(df.index >= os_) & (df.index <= oe)]
    return dev, oos
