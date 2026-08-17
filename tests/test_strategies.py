"""Tests for strategy signal generation."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.strategies.moving_average import MovingAverageCrossover
from src.strategies.rsi import RSIMeanReversion


def _frame(prices: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({"Close": prices})


def test_ma_crossover_signals_binary():
    idx = pd.bdate_range("2020-01-01", periods=300)
    prices = pd.Series(np.linspace(100, 200, 300), index=idx)
    strat = MovingAverageCrossover(20, 50)
    sig = strat.generate_signals(_frame(prices))
    assert set(sig.dropna().unique()).issubset({0.0, 1.0})


def test_ma_crossover_long_in_uptrend():
    idx = pd.bdate_range("2020-01-01", periods=300)
    prices = pd.Series(np.linspace(100, 300, 300), index=idx)
    strat = MovingAverageCrossover(20, 50)
    sig = strat.generate_signals(_frame(prices))
    # Sustained uptrend: fast SMA above slow SMA at the end => long.
    assert sig.iloc[-1] == 1.0


def test_ma_crossover_flat_in_downtrend():
    idx = pd.bdate_range("2020-01-01", periods=300)
    prices = pd.Series(np.linspace(300, 100, 300), index=idx)
    strat = MovingAverageCrossover(20, 50)
    sig = strat.generate_signals(_frame(prices))
    assert sig.iloc[-1] == 0.0


def test_ma_crossover_rejects_bad_windows():
    with pytest.raises(ValueError):
        MovingAverageCrossover(50, 20)


def test_rsi_strategy_state_machine():
    # Construct RSI to be low then recover: V-shaped prices.
    down = np.linspace(100, 60, 40)
    up = np.linspace(60, 140, 60)
    prices = pd.Series(np.concatenate([down, up]))
    prices.index = pd.bdate_range("2020-01-01", periods=len(prices))
    strat = RSIMeanReversion(14, 30, 50)
    sig = strat.generate_signals(_frame(prices))
    assert set(sig.unique()).issubset({0.0, 1.0})
    # It should enter long at some point during/after the oversold dip.
    assert sig.max() == 1.0
    # And exit (return to 0) once RSI climbs above 50 in the recovery.
    assert sig.iloc[-1] == 0.0


def test_rsi_rejects_bad_thresholds():
    with pytest.raises(ValueError):
        RSIMeanReversion(14, 60, 40)


def test_rsi_no_signal_when_never_oversold():
    idx = pd.bdate_range("2020-01-01", periods=200)
    prices = pd.Series(np.linspace(100, 300, 200), index=idx)  # only rising
    strat = RSIMeanReversion(14, 30, 50)
    sig = strat.generate_signals(_frame(prices))
    assert sig.max() == 0.0
