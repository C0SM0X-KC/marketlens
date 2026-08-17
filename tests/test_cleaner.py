"""Tests for data validation and cleaning."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data.cleaner import DataValidationError, add_returns, clean_ohlcv


def test_clean_removes_duplicates(ohlcv):
    dup = pd.concat([ohlcv, ohlcv.iloc[[-1]]])
    clean, report = clean_ohlcv(dup, "TEST")
    assert report.duplicates_removed >= 1
    assert clean.index.is_unique


def test_clean_sorts_index(ohlcv):
    shuffled = ohlcv.sample(frac=1.0, random_state=1)
    clean, _ = clean_ohlcv(shuffled, "TEST")
    assert clean.index.is_monotonic_increasing


def test_clean_flattens_multiindex_columns(ohlcv):
    mi = ohlcv.copy()
    mi.columns = pd.MultiIndex.from_product([mi.columns, ["TEST"]])
    clean, _ = clean_ohlcv(mi, "TEST")
    assert "Close" in clean.columns


def test_clean_drops_invalid_ohlc():
    idx = pd.bdate_range("2021-01-01", periods=3)
    df = pd.DataFrame(
        {
            "Open": [10, 10, 10.0],
            "High": [11, 5, 12.0],   # row 1 has High < Low (invalid)
            "Low": [9, 9, 9.0],
            "Close": [10, 10, 11.0],
            "Adj Close": [10, 10, 11.0],
            "Volume": [100, 100, 100],
        },
        index=idx,
    )
    clean, report = clean_ohlcv(df, "TEST")
    assert report.invalid_ohlc_rows == 1
    assert len(clean) == 2


def test_clean_empty_raises():
    with pytest.raises(DataValidationError):
        clean_ohlcv(pd.DataFrame(), "TEST")


def test_add_returns_columns(ohlcv):
    clean, _ = clean_ohlcv(ohlcv, "TEST")
    withret = add_returns(clean)
    assert "Return" in withret.columns
    assert "LogReturn" in withret.columns
    assert np.isnan(withret["Return"].iloc[0])


def test_missing_adj_close_filled_from_close():
    idx = pd.bdate_range("2021-01-01", periods=3)
    df = pd.DataFrame(
        {"Open": [1, 2, 3.0], "High": [2, 3, 4.0], "Low": [0.5, 1, 2.0],
         "Close": [1.5, 2.5, 3.5], "Volume": [10, 10, 10]},
        index=idx,
    )
    clean, _ = clean_ohlcv(df, "TEST")
    assert "Adj Close" in clean.columns
    assert (clean["Adj Close"] == clean["Close"]).all()
