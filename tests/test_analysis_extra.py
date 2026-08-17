"""Tests for trend classification, regime detection and event study."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis import regime, trend
from src.analysis.summary import build_snapshot
from src.data.cleaner import add_returns
from src.macro import event_study


def test_trend_bullish_uptrend():
    idx = pd.bdate_range("2019-01-01", periods=300)
    prices = pd.Series(np.linspace(100, 300, 300), index=idx)
    assert trend.current_trend(prices, 50, 200) == "Bullish"


def test_trend_bearish_downtrend():
    idx = pd.bdate_range("2019-01-01", periods=300)
    prices = pd.Series(np.linspace(300, 100, 300), index=idx)
    assert trend.current_trend(prices, 50, 200) == "Bearish"


def test_trend_labels_valid(sine_prices):
    s = trend.trend_series(sine_prices, 10, 30)
    assert set(s.unique()).issubset({"Bullish", "Bearish", "Neutral"})


def test_regime_labels_and_share_sum():
    rng = np.random.default_rng(11)
    idx = pd.bdate_range("2018-01-01", periods=600)
    # Mix calm and turbulent segments.
    calm = rng.normal(0, 0.005, 300)
    wild = rng.normal(0, 0.03, 300)
    ret = pd.Series(np.concatenate([calm, wild]), index=idx)
    df = regime.regime_series(ret)
    assert set(df["Regime"].unique()).issubset({"Low", "Normal", "High"})
    perf = regime.performance_by_regime(ret)
    assert perf["Share"].sum() == pytest.approx(1.0, rel=1e-6)


def test_event_window_offsets():
    idx = pd.bdate_range("2021-01-01", periods=40)
    prices = pd.Series(np.linspace(100, 140, 40), index=idx)
    df = add_returns(pd.DataFrame({"Close": prices, "Adj Close": prices}))
    event_date = idx[20]
    w = event_study.event_window(df, event_date, pre=5, post=5)
    assert 0 in w.index
    assert w.index.min() == -5
    assert w.index.max() == 5
    # Cumulative return at T0 is zero by construction.
    assert w.loc[0, "CumReturnFromT0"] == pytest.approx(0.0)


def test_event_study_multi_asset():
    idx = pd.bdate_range("2021-01-01", periods=40)
    a = pd.Series(np.linspace(100, 140, 40), index=idx)
    b = pd.Series(np.linspace(200, 180, 40), index=idx)
    da = add_returns(pd.DataFrame({"Close": a, "Adj Close": a}))
    dbf = add_returns(pd.DataFrame({"Close": b, "Adj Close": b}))
    res = event_study.study_event({"A": da, "B": dbf}, idx[20], 5, 5)
    assert set(res.index) == {"A", "B"}
    assert res.loc["A", "price_move"] > 0
    assert res.loc["B", "price_move"] < 0


def test_snapshot_produces_observations():
    idx = pd.bdate_range("2019-01-01", periods=300)
    prices = pd.Series(np.linspace(100, 300, 300), index=idx)
    df = add_returns(pd.DataFrame({"Close": prices, "Adj Close": prices}))
    snap = build_snapshot(df, "TestAsset")
    assert 1 <= len(snap.observations) <= 5
    assert snap.trend in {"Bullish", "Bearish", "Neutral"}
    assert 0 <= snap.rsi <= 100
