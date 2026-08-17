"""Cross-Market — correlation, rolling correlation and comparative performance."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.components import charts
from app.components.controls import sidebar_asset_select, sidebar_dates
from app.components.data import asset_label, load_selected, returns_frame
from app.components.theme import page_header, setup_page
from src.analysis import correlation
from src.config import ASSETS, CONFIG

setup_page("Cross-Market", icon="▨")
page_header(
    "Cross-Market Analysis",
    "Correlations are computed from daily returns; comparative performance is "
    "normalised to a common start date.",
    section="Cross-Market",
)

start, end, _ = sidebar_dates()
selected = sidebar_asset_select(default=list(ASSETS.keys()))

if len(selected) < 2:
    st.warning("Select at least two assets to compare.")
    st.stop()

data, errors = load_selected(selected, start, end)
for k, msg in errors.items():
    st.warning(f"{asset_label(k)}: {msg}")
if len(data) < 2:
    st.error("Need at least two assets with data.")
    st.stop()

rets = returns_frame(data)
labels = {k: ASSETS[k].name for k in data}

# ---- Correlation matrix ---------------------------------------------------
st.markdown("#### Correlation matrix (daily returns)")
corr = correlation.correlation_matrix(rets)
st.plotly_chart(charts.heatmap_corr(corr, labels), width="stretch")

# ---- Rolling correlation --------------------------------------------------
st.markdown("#### Rolling correlation")
cc = st.columns(3)
pair_a = cc[0].selectbox("Asset A", list(data.keys()), format_func=asset_label, key="ra")
pair_b = cc[1].selectbox(
    "Asset B", [k for k in data.keys() if k != pair_a],
    format_func=asset_label, key="rb",
)
window = cc[2].slider("Window (days)", 20, 180, CONFIG.analysis.rolling_corr_window, 10)

roll = correlation.rolling_correlation(rets, pair_a, pair_b, window).dropna()
if not roll.empty:
    roll_df = roll.rename(f"{asset_label(pair_a)} vs {asset_label(pair_b)}").to_frame()
    st.plotly_chart(charts.line(roll_df, height=340), width="stretch")
    st.caption(f"Latest {window}-day correlation: {roll.iloc[-1]:.2f}")
else:
    st.info("Not enough overlapping data for the chosen window.")

# ---- Comparative cumulative returns + volatility --------------------------
st.markdown("#### Comparative cumulative returns")
cum = correlation.comparative_cumulative_returns(rets).rename(columns=labels)
if not cum.empty:
    st.plotly_chart(charts.line(cum, pct=True, height=420), width="stretch")

st.markdown("#### Rolling volatility comparison")
volcmp = correlation.volatility_comparison(rets).dropna(how="all").rename(columns=labels)
if not volcmp.empty:
    st.plotly_chart(charts.line(volcmp, pct=True, height=380), width="stretch")
