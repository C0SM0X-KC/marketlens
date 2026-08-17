"""Tests for backtesting performance metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtesting import metrics


def test_total_return():
    equity = pd.Series([100.0, 120.0, 150.0])
    assert metrics.total_return(equity) == pytest.approx(0.5)


def test_cagr_one_year():
    # 253 equity points span exactly 252 return periods => one year; doubling => 100% CAGR.
    equity = pd.Series(np.linspace(100, 200, 253))
    assert metrics.cagr(equity, trading_days=252) == pytest.approx(1.0, rel=1e-6)


def test_sharpe_zero_rf():
    rng = np.random.default_rng(7)
    r = pd.Series(rng.normal(0.001, 0.01, 500))
    expected = (r.mean() / r.std(ddof=1)) * np.sqrt(252)
    assert metrics.sharpe_ratio(r, risk_free_rate=0.0, trading_days=252) == pytest.approx(expected)


def test_sharpe_with_riskfree():
    r = pd.Series([0.0] * 300)  # exactly zero volatility => undefined (nan) Sharpe
    assert np.isnan(metrics.sharpe_ratio(r, risk_free_rate=0.02))


def test_max_drawdown_metric():
    equity = pd.Series([100, 120, 60, 90], dtype=float)
    assert metrics.max_drawdown(equity) == pytest.approx(-0.5)


def test_trade_stats_win_rate_and_profit_factor():
    trades = [0.10, -0.05, 0.20, -0.10]
    ts = metrics.trade_stats(trades)
    assert ts["num_trades"] == 4
    assert ts["win_rate"] == pytest.approx(0.5)
    # gross profit 0.30, gross loss 0.15 => PF 2.0
    assert ts["profit_factor"] == pytest.approx(2.0)
    assert ts["avg_trade_return"] == pytest.approx(np.mean(trades))


def test_trade_stats_empty():
    ts = metrics.trade_stats([])
    assert ts["num_trades"] == 0
    assert np.isnan(ts["win_rate"])


def test_compute_metrics_bundle():
    equity = pd.Series(np.linspace(100, 200, 252))
    ret = equity.pct_change().fillna(0)
    m = metrics.compute_metrics(equity, ret, [0.1, -0.05])
    assert m.total_return == pytest.approx(1.0)
    assert m.num_trades == 2
