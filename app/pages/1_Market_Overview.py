"""Market Overview — cross-asset KPI dashboard."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from app.components import charts
from app.components.controls import sidebar_asset_select, sidebar_dates
from app.components.data import asset_label, load_selected, price_frame
from app.components.theme import (
    color_class,
    fmt_num,
    fmt_pct,
    page_header,
    regime_badge,
    setup_page,
    trend_badge,
)
from src.analysis import regime, returns, trend, volatility
from src.config import ASSETS, CONFIG

setup_page("Market Overview", icon="▨")
page_header(
    "Market Overview",
    "A cross-asset snapshot of returns, volatility, trend and market regime.",
    section="Overview",
)

start, end, _ = sidebar_dates()
selected = sidebar_asset_select(default=list(ASSETS.keys()))

if not selected:
    st.warning("Select at least one asset from the sidebar.")
    st.stop()

data, errors = load_selected(selected, start, end)
for k, msg in errors.items():
    st.warning(f"{asset_label(k)}: {msg}")

if not data:
    st.error("No data could be loaded for the current selection.")
    st.stop()


@st.cache_data(ttl=1800, show_spinner=False)
def build_overview(keys: tuple, start: str, end: str) -> pd.DataFrame:
    rows = []
    d, _ = load_selected(list(keys), start, end)
    for k, df in d.items():
        px = df["Adj Close"] if "Adj Close" in df.columns else df["Close"]
        tr = returns.trailing_returns(px)
        vol20 = volatility.realized_volatility(df["Return"], CONFIG.analysis.vol_short_window)
        rows.append({
            "Asset": ASSETS[k].name,
            "Class": ASSETS[k].asset_class,
            "Price": float(px.iloc[-1]),
            "Daily": tr["daily"],
            "Weekly": tr["weekly"],
            "Monthly": tr["monthly"],
            "YTD": tr["ytd"],
            "Vol20 (ann)": vol20,
            "Trend": trend.current_trend(px),
            "Regime": regime.current_regime(df["Return"]),
            "_key": k,
        })
    return pd.DataFrame(rows)


overview = build_overview(tuple(data.keys()), start, end)

# ---- KPI strip: pick highlight metrics -----------------------------------
st.markdown("#### Snapshot")
cards = st.columns(min(len(overview), 3))
for i, (_, r) in enumerate(overview.head(3).iterrows()):
    with cards[i % 3]:
        st.markdown(
            f'<div class="ml-kpi"><div class="lbl">{r["Asset"]}</div>'
            f'<div class="val">{fmt_num(r["Price"])}</div>'
            f'<div class="sub {color_class(r["Daily"])}">{fmt_pct(r["Daily"], signed=True)} today · '
            f'{fmt_pct(r["YTD"], signed=True)} YTD</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("")

# ---- Overview table -------------------------------------------------------
st.markdown("#### All assets")
tbl = overview.drop(columns=["_key"]).copy()
styled = tbl.style.format({
    "Price": lambda v: fmt_num(v),
    "Daily": lambda v: fmt_pct(v, signed=True),
    "Weekly": lambda v: fmt_pct(v, signed=True),
    "Monthly": lambda v: fmt_pct(v, signed=True),
    "YTD": lambda v: fmt_pct(v, signed=True),
    "Vol20 (ann)": lambda v: fmt_pct(v),
})


def _sign_color(v):
    try:
        return "color:#26c281" if v > 0 else ("color:#ef5b5b" if v < 0 else "")
    except TypeError:
        return ""


styled = styled.map(_sign_color, subset=["Daily", "Weekly", "Monthly", "YTD"])
st.dataframe(styled, width="stretch", hide_index=True)

# ---- Comparative normalised performance ----------------------------------
st.markdown("#### Comparative performance (normalised)")
prices = price_frame(data)
rets = prices.pct_change()
cum = (1 + rets.dropna(how="any")).cumprod() - 1
cum = cum.rename(columns=asset_label)
if not cum.empty:
    st.plotly_chart(charts.line(cum, pct=True, height=420), width="stretch")
else:
    st.info("Not enough overlapping history to compare the selected assets.")

with st.expander("Trend & regime detail"):
    detail = overview[["Asset", "Trend", "Regime"]].copy()
    for _, r in detail.iterrows():
        st.markdown(
            f"**{r['Asset']}** — {trend_badge(r['Trend'])} {regime_badge(r['Regime'])}",
            unsafe_allow_html=True,
        )
    st.caption(
        "Trend = rule-based (Price vs SMA50 vs SMA200). "
        "Regime = volatility percentile classification. Descriptive, not predictive."
    )
