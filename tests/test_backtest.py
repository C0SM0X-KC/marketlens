"""Tests for the backtesting engine, transaction costs and look-ahead safety."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtesting.engine import run_backtest, split_dev_oos
from src.backtesting.transaction_costs import CostModel
from src.strategies.base import Strategy


class AlwaysLong(Strategy):
    name = "Always Long"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        return pd.Series(1.0, index=df.index)


class AlwaysFlat(Strategy):
    name = "Always Flat"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        return pd.Series(0.0, index=df.index)


def _prices(n=100, drift=0.001):
    idx = pd.bdate_range("2020-01-01", periods=n)
    close = 100.0 * (1 + drift) ** np.arange(n)
    return pd.DataFrame({"Close": close, "Adj Close": close}, index=idx)


def test_always_flat_zero_return():
    df = _prices()
    bt = run_backtest(df, AlwaysFlat(), "X", initial_capital=100_000)
    assert bt.metrics.total_return == pytest.approx(0.0, abs=1e-12)
    assert bt.equity.iloc[-1] == pytest.approx(100_000)


def test_always_long_tracks_buy_hold_without_costs():
    df = _prices()
    no_cost = CostModel(0.0, 0.0)
    bt = run_backtest(df, AlwaysLong(), "X", cost_model=no_cost)
    # The first daily return is NaN->0 for both, and the always-long position is
    # active from the first real return onward, so an uncosted always-long
    # strategy reproduces buy & hold exactly.
    assert bt.metrics.total_return == pytest.approx(bt.benchmark_metrics.total_return)
    assert np.allclose(bt.equity.values, bt.benchmark_equity.values, rtol=1e-9)


def test_execution_lag_prevents_lookahead():
    # A strategy that "knows" the jump day still cannot trade it because of lag.
    df = _prices(n=10, drift=0.0)  # flat at 100
    # A permanent doubling from day 5 onward: the +100% return happens on day 5.
    df.loc[df.index[5:], ["Close", "Adj Close"]] = 200.0

    class KnowsStep(Strategy):
        name = "Knows Step"

        def generate_signals(self, d):
            s = pd.Series(0.0, index=d.index)
            s.iloc[5:] = 1.0  # long from the jump day using same-day info
            return s

    bt = run_backtest(df, KnowsStep(), "X", cost_model=CostModel(0, 0))
    # One-bar lag: position becomes long on day 6, AFTER the day-5 jump return,
    # so the strategy captures none of the +100% move.
    assert bt.position.iloc[5] == 0.0
    assert bt.position.iloc[6] == 1.0
    assert bt.strategy_returns.iloc[5] == pytest.approx(0.0)
    assert bt.metrics.total_return == pytest.approx(0.0, abs=1e-9)


def test_transaction_costs_reduce_return():
    df = _prices(drift=0.002)

    class Flip(Strategy):
        name = "Flip"

        def generate_signals(self, d):
            # Alternate every day to maximise turnover.
            return pd.Series([float(i % 2) for i in range(len(d))], index=d.index)

    gross = run_backtest(df, Flip(), "X", cost_model=CostModel(0, 0))
    net = run_backtest(df, Flip(), "X", cost_model=CostModel(10, 5))
    assert net.metrics.total_return < gross.metrics.total_return


def test_cost_model_fraction():
    cm = CostModel(transaction_cost_bps=10, slippage_bps=5)
    assert cm.cost_fraction() == pytest.approx(15 / 10_000)


def test_split_dev_oos_partitions():
    idx = pd.bdate_range("2018-01-01", "2025-06-30")
    df = pd.DataFrame({"Close": np.arange(len(idx), dtype=float)}, index=idx)
    dev, oos = split_dev_oos(df, "2018-01-01", "2023-12-31", "2024-01-01", "2025-12-31")
    assert dev.index.max() <= pd.Timestamp("2023-12-31")
    assert oos.index.min() >= pd.Timestamp("2024-01-01")
    assert len(dev) > 0 and len(oos) > 0


def test_benchmark_is_buy_and_hold():
    df = _prices(drift=0.001)
    bt = run_backtest(df, AlwaysFlat(), "X")
    expected = df["Close"].iloc[-1] / df["Close"].iloc[0] - 1.0
    assert bt.benchmark_metrics.total_return == pytest.approx(expected)
