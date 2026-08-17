"""Shared sidebar controls (date range, asset selection, refresh)."""
from __future__ import annotations

from datetime import date
from typing import List, Optional, Tuple

import streamlit as st

from src.config import ASSETS, CONFIG, asset_keys


def sidebar_dates(default_years: Optional[int] = None) -> Tuple[str, str, bool]:
    """Render date-range + refresh controls. Returns (start, end, force_refresh)."""
    st.sidebar.markdown("### Data range")
    years = default_years or CONFIG.analysis.default_lookback_years
    today = date.today()
    default_start = date(today.year - years, today.month, today.day)

    start = st.sidebar.date_input(
        "Start", value=default_start, min_value=date(2000, 1, 1), max_value=today,
        key="ml_start",
    )
    end = st.sidebar.date_input(
        "End", value=today, min_value=date(2000, 1, 1), max_value=today, key="ml_end",
    )
    force = st.sidebar.button("↻ Refresh data", help="Bypass cache and re-download")
    if force:
        st.cache_data.clear()
    st.sidebar.caption("Data via Yahoo Finance (yfinance). Cached locally.")
    return str(start), str(end), force


def sidebar_asset_select(
    label: str = "Assets", default: Optional[List[str]] = None, multi: bool = True
):
    keys = asset_keys()
    fmt = lambda k: ASSETS[k].name
    if multi:
        return st.sidebar.multiselect(
            label, keys, default=default or keys, format_func=fmt, key="ml_assets"
        )
    return st.sidebar.selectbox(label, keys, format_func=fmt, key="ml_asset_single")


def single_asset_picker(label: str = "Asset", key: str = "ml_single") -> str:
    keys = asset_keys()
    return st.selectbox(label, keys, format_func=lambda k: ASSETS[k].name, key=key)
