"""Cached data-access helpers for the Streamlit app.

Wrap the pure data-loading functions in ``st.cache_data`` so pages share
downloaded data and stay responsive. Returning plain DataFrames (not the
LoadResult dataclass) keeps the cache hashable and simple.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from src.config import ASSETS
from src.data.loader import DataUnavailableError, load_asset


@st.cache_data(ttl=3600, show_spinner=False)
def get_asset_data(
    key: str, start: str, end: str, force_refresh: bool = False
) -> Tuple[pd.DataFrame, bool, bool]:
    """Return (dataframe, from_cache, stale) for one asset."""
    res = load_asset(key, start=start, end=end, force_refresh=force_refresh)
    return res.data, res.from_cache, res.stale


def load_selected(
    keys: List[str], start: str, end: str, force_refresh: bool = False
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, str]]:
    """Load several assets, collecting per-asset errors instead of failing."""
    data: Dict[str, pd.DataFrame] = {}
    errors: Dict[str, str] = {}
    for k in keys:
        try:
            df, _cache, _stale = get_asset_data(k, start, end, force_refresh)
            data[k] = df
        except (DataUnavailableError, Exception) as exc:  # noqa: BLE001
            errors[k] = str(exc)
    return data, errors


def price_frame(
    data: Dict[str, pd.DataFrame], price_col: str = "Adj Close"
) -> pd.DataFrame:
    series = {}
    for k, df in data.items():
        col = price_col if price_col in df.columns else "Close"
        series[k] = df[col]
    return pd.DataFrame(series).sort_index()


def returns_frame(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame({k: df["Return"] for k, df in data.items()}).sort_index()


def asset_label(key: str) -> str:
    return ASSETS[key].name if key in ASSETS else key
