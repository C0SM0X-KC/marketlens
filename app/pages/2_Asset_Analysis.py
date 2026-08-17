"""Asset Analysis — single-asset technical, risk and volatility deep dive."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from app.components import charts
from app.components.controls import sidebar_dates, single_asset_picker
from app.components.data import get_asset_data
from app.components.theme import (
    color_class,
    fmt_num,
    fmt_pct,
    page_header,
    regime_badge,
    setup_page,
    trend_badge,
)
from src.analysis import drawdown, regime, returns, trend, volatility
from src.config import ASSETS, CONFIG
from src.technical import momentum
from src.technical import moving_averages as ma
from src.technical import volatility_indicators as vi

setup_page("Asset Analysis", icon="▨")
page_header(
    "Asset Analysis",
    "A single-asset breakdown of price structure, momentum, volatility and drawdowns.",
    section="Analysis",
)

start, end, _ = sidebar_dates()
key = single_asset_picker("Asset")
asset = ASSETS[key]
st.markdown(
    f"<span class='ml-caption'>{asset.name} · {asset.ticker} · {asset.asset_class} "
    f"· quoted in {asset.currency}</span>",
    unsafe_allow_html=True,
)

try:
    df, from_cache, stale = get_asset_data(key, start, end)
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load {asset.name}: {exc}")
    st.stop()

if stale:
    st.warning("Live download failed — showing the most recent cached snapshot.")

px = df["Adj Close"] if "Adj Close" in df.columns else df["Close"]
tr = returns.trailing_returns(px)
vol20 = volatility.realized_volatility(df["Return"], CONFIG.analysis.vol_short_window)
dd_stats = drawdown.max_drawdown_stats(px)
cur_trend = trend.current_trend(px)
cur_regime = regime.current_regime(df["Return"])

# ---- KPI row (responsive grid — comfortable width, wraps on narrow screens) -
kpis = [
    ("Last Price", fmt_num(px.iloc[-1]), "ml-flat"),
    ("Daily", fmt_pct(tr["daily"], signed=True), color_class(tr["daily"])),
    ("YTD", fmt_pct(tr["ytd"], signed=True), color_class(tr["ytd"])),
    ("Vol 20d (ann)", fmt_pct(vol20), "ml-flat"),
    ("Max Drawdown", fmt_pct(dd_stats.max_drawdown), "ml-down"),
    ("CAGR", fmt_pct(returns.cagr(px)), "ml-flat"),
]
kpi_html = "".join(
    f'<div class="ml-kpi"><div class="lbl">{lbl}</div>'
    f'<div class="val {cls}">{val}</div></div>'
    for lbl, val, cls in kpis
)
st.markdown(f'<div class="ml-kpi-grid">{kpi_html}</div>', unsafe_allow_html=True)

st.markdown(
    f"Trend {trend_badge(cur_trend)} &nbsp; Regime {regime_badge(cur_regime)}",
    unsafe_allow_html=True,
)

tabs = st.tabs(["Price & MAs", "Momentum", "Volatility", "Drawdown", "Returns"])

# ---- Price & moving averages ---------------------------------------------
with tabs[0]:
    view = st.radio("View", ["Line + MAs", "Candlestick"], horizontal=True, key="pv")
    if view == "Candlestick":
        st.plotly_chart(charts.candlestick(df, asset.name), width="stretch")
    else:
        mas = ma.moving_average_frame(px)
        st.plotly_chart(
            charts.price_with_mas(px, mas, asset.name), width="stretch"
        )
    st.caption(
        "SMA 20/50/200 and EMA 20/50. Rule-based trend uses SMA50 vs SMA200."
    )

# ---- Momentum: RSI + MACD -------------------------------------------------
with tabs[1]:
    rsi = momentum.rsi(px)
    macd_df = momentum.macd(px)
    st.plotly_chart(charts.rsi_chart(rsi), width="stretch")
    st.plotly_chart(charts.macd_chart(macd_df), width="stretch")
    st.caption(f"Latest RSI: {fmt_num(rsi.iloc[-1], 1)} · MACD histogram: "
               f"{fmt_num(macd_df['Histogram'].iloc[-1], 2)}")

# ---- Volatility indicators + regime --------------------------------------
with tabs[2]:
    bb = vi.bollinger_bands(px)
    st.plotly_chart(charts.bollinger_chart(px, bb), width="stretch")
    vol_frame = volatility.volatility_frame(df["Return"]).dropna(how="all")
    st.plotly_chart(charts.line(vol_frame, "Rolling annualised volatility", pct=True),
                    width="stretch")
    reg = regime.regime_series(df["Return"])
    if not reg.empty:
        st.plotly_chart(charts.regime_timeline(reg), width="stretch")
        perf = regime.performance_by_regime(df["Return"])
        if not perf.empty:
            disp = perf.copy()
            disp["AvgDailyReturn"] = disp["AvgDailyReturn"].map(lambda v: fmt_pct(v, 3, True))
            disp["AnnVol"] = disp["AnnVol"].map(lambda v: fmt_pct(v))
            disp["Share"] = disp["Share"].map(lambda v: fmt_pct(v, 1))
            st.markdown("**Performance by regime**")
            st.dataframe(disp, width="stretch")

# ---- Drawdown -------------------------------------------------------------
with tabs[3]:
    dd = drawdown.drawdown_series(px)
    st.plotly_chart(charts.area_drawdown(dd["Drawdown"], "Drawdown from running peak"),
                    width="stretch")
    m = st.columns(4)
    m[0].metric("Max Drawdown", fmt_pct(dd_stats.max_drawdown))
    m[1].metric("Peak", dd_stats.peak_date.date().isoformat() if dd_stats.peak_date is not None else "—")
    m[2].metric("Trough", dd_stats.trough_date.date().isoformat() if dd_stats.trough_date is not None else "—")
    m[3].metric(
        "Recovery",
        dd_stats.recovery_date.date().isoformat() if dd_stats.recovery_date is not None else "Not recovered",
    )
    st.metric("Current Drawdown", fmt_pct(dd_stats.current_drawdown))

# ---- Returns distribution -------------------------------------------------
with tabs[4]:
    monthly = returns.resample_returns(df["Return"], "ME").dropna()
    monthly.index = monthly.index.strftime("%Y-%m")
    st.plotly_chart(
        charts.bars(monthly.tail(24), "Monthly returns (last 24 months)", pct=True),
        width="stretch",
    )
    stats = pd.DataFrame({
        "Metric": ["Total return", "CAGR", "Ann. volatility", "Best day", "Worst day"],
        "Value": [
            fmt_pct(returns.total_return(px)),
            fmt_pct(returns.cagr(px)),
            fmt_pct(volatility.annualized_volatility(df["Return"])),
            fmt_pct(df["Return"].max(), signed=True),
            fmt_pct(df["Return"].min(), signed=True),
        ],
    })
    st.dataframe(stats, width="stretch", hide_index=True)
