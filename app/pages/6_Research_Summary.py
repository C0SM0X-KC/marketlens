"""Research Summary — auto-generated, data-driven market snapshot."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.components.controls import sidebar_dates, single_asset_picker
from app.components.data import get_asset_data
from app.components.theme import (
    fmt_num,
    fmt_pct,
    page_header,
    regime_badge,
    setup_page,
    trend_badge,
)
from src.analysis.summary import build_snapshot
from src.config import ASSETS

setup_page("Research Summary", icon="▨")
page_header(
    "Research Summary",
    "An automatically generated summary built strictly from calculated metrics. "
    "It is descriptive only and is not investment advice.",
    section="Summary",
)

start, end, _ = sidebar_dates()
key = single_asset_picker("Asset")
asset = ASSETS[key]

try:
    df, _fc, stale = get_asset_data(key, start, end)
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load {asset.name}: {exc}")
    st.stop()
if stale:
    st.warning("Live download failed — showing cached snapshot.")

snap = build_snapshot(df, asset.name)

st.markdown(f"### {asset.name}")
st.markdown(
    f"Trend {trend_badge(snap.trend)} &nbsp; Regime {regime_badge(snap.regime)}",
    unsafe_allow_html=True,
)

cols = st.columns(5)
cols[0].metric("RSI (14)", fmt_num(snap.rsi, 1))
cols[1].metric("YTD", fmt_pct(snap.ytd, signed=True))
cols[2].metric("Vol 20d (ann)", fmt_pct(snap.ann_vol))
cols[3].metric("Current Drawdown", fmt_pct(snap.current_drawdown))
cols[4].metric("Max Drawdown", fmt_pct(snap.max_drawdown))

st.markdown("#### Observations")
for o in snap.observations:
    st.markdown(f"- {o}")

st.divider()
st.markdown(
    "<span class='ml-caption'>These observations are descriptive summaries of historical "
    "and current calculated metrics. They do not constitute buy/sell recommendations, "
    "forecasts, or guarantees of future performance.</span>",
    unsafe_allow_html=True,
)
