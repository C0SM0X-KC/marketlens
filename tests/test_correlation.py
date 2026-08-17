"""Tests for cross-market correlation analysis."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis import correlation


def test_perfect_positive_correlation():
    idx = pd.bdate_range("2021-01-01", periods=50)
    a = pd.Series(np.linspace(0.01, 0.5, 50), index=idx)
    df = pd.DataFrame({"A": a, "B": a * 2.0})
    corr = correlation.correlation_matrix(df)
    assert corr.loc["A", "B"] == pytest.approx(1.0)


def test_perfect_negative_correlation():
    idx = pd.bdate_range("2021-01-01", periods=50)
    a = pd.Series(np.linspace(0.01, 0.5, 50), index=idx)
    df = pd.DataFrame({"A": a, "B": -a})
    corr = correlation.correlation_matrix(df)
    assert corr.loc["A", "B"] == pytest.approx(-1.0)


def test_correlation_matrix_diagonal():
    rng = np.random.default_rng(3)
    df = pd.DataFrame(rng.normal(0, 1, (100, 3)), columns=["A", "B", "C"])
    corr = correlation.correlation_matrix(df)
    assert np.allclose(np.diag(corr.values), 1.0)


def test_rolling_correlation_length_and_range():
    rng = np.random.default_rng(4)
    idx = pd.bdate_range("2021-01-01", periods=200)
    df = pd.DataFrame(
        {"A": rng.normal(0, 1, 200), "B": rng.normal(0, 1, 200)}, index=idx
    )
    roll = correlation.rolling_correlation(df, "A", "B", 60)
    valid = roll.dropna()
    assert valid.between(-1.0, 1.0).all()
    assert roll.iloc[:59].isna().all()


def test_comparative_cumulative_returns_starts_positiveish():
    idx = pd.bdate_range("2021-01-01", periods=10)
    df = pd.DataFrame({"A": [0.01] * 10, "B": [0.02] * 10}, index=idx)
    cum = correlation.comparative_cumulative_returns(df)
    assert cum["B"].iloc[-1] > cum["A"].iloc[-1]
