"""MarketLens — Global Financial Markets Analysis & Strategy Backtesting Platform.

Entry point for the Streamlit multipage app. Run with:

    streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from datetime import date, datetime

import streamlit as st

from app.components.data import load_selected
from app.components.theme import fmt_num, fmt_pct, setup_page
from src.analysis import returns
from src.config import ASSETS, ASSET_CLASSES, asset_keys

# Page config once, as the first Streamlit call, so it holds under the
# st.navigation router defined at the bottom of this file. The router owns the
# sidebar labels — this is why the home page reads "Home", not "streamlit app".
st.set_page_config(page_title="MarketLens", page_icon="◆", layout="wide")


# ---- Signature: the live market tape --------------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def _tape_rows(start: str, end: str):
    """Last price + daily change per instrument, plus the fetch time (HH:MM)."""
    data, _errors = load_selected(asset_keys(), start, end)
    rows = []
    for k, df in data.items():
        px = df["Adj Close"] if "Adj Close" in df.columns else df["Close"]
        last = float(px.iloc[-1])
        chg = returns.period_return(px, 1)
        rows.append((ASSETS[k].code, last, chg))
    return rows, datetime.now().strftime("%H:%M")


@st.cache_data(ttl=1800, show_spinner=False)
def _hero_spark(start: str, end: str, key: str = "SP500"):
    """A compact 1-year sparkline for the flagship index, for the hero panel."""
    data, _errors = load_selected([key], start, end)
    df = data.get(key)
    if df is None or df.empty:
        return None
    px = (df["Adj Close"] if "Adj Close" in df.columns else df["Close"]).dropna()
    if len(px) < 2:
        return None
    vals = [float(v) for v in px.to_list()]
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    n = len(vals)
    w, h = 260.0, 64.0
    pts = " ".join(
        f"{(i / (n - 1)) * w:.1f},{h - ((v - lo) / rng) * h:.1f}"
        for i, v in enumerate(vals)
    )
    chg = returns.period_return(px, 1)
    return {"last": vals[-1], "chg": chg, "points": pts, "w": w, "h": h,
            "up": chg is None or chg >= 0}


def _hero_panel_html() -> str:
    """Right-hand hero panel: live flagship sparkline. Empty string on failure."""
    today = date.today()
    start = date(today.year - 1, today.month, today.day).isoformat()
    try:
        spark = _hero_spark(start, today.isoformat())
    except Exception:  # noqa: BLE001 - hero decoration, never fatal
        spark = None
    if not spark:
        return ""
    dirn = "up" if spark["up"] else "down"
    chg_txt = fmt_pct(spark["chg"], 2, signed=True) if spark["chg"] is not None else "—"
    return (
        '<div class="ml-hero-panel">'
        '<div class="ml-hero-panel-top">'
        '<span class="ml-hero-panel-code">S&amp;P 500 · SPX</span>'
        '<span class="ml-live"><span class="ml-live-dot"></span>Live</span></div>'
        f'<div class="ml-hero-panel-val">{fmt_num(spark["last"])}</div>'
        f'<div class="ml-hero-panel-chg ml-{dirn}">{chg_txt} · 1D</div>'
        f'<svg class="ml-spark" viewBox="0 0 {spark["w"]:.0f} {spark["h"]:.0f}" '
        'preserveAspectRatio="none" aria-hidden="true">'
        f'<polyline points="{spark["points"]}" fill="none" class="ml-spark-{dirn}" '
        'vector-effect="non-scaling-stroke"/></svg>'
        '<div class="ml-hero-panel-foot">1-year trend · last close</div>'
        '</div>'
    )


def _render_tape() -> None:
    today = date.today()
    start = date(today.year - 1, today.month, today.day).isoformat()
    try:
        with st.spinner("Fetching live prices…"):
            rows, fetched_at = _tape_rows(start, today.isoformat())
    except Exception:  # noqa: BLE001 - the tape is decorative-critical, never fatal
        rows, fetched_at = [], None
    if not rows:
        # Loud-enough, never fatal: the signature element states why it is empty
        # instead of silently vanishing.
        st.markdown(
            '<div class="ml-tape-empty">'
            '<span class="dot"></span>Live prices are unavailable right now — '
            'the rest of the workspace still works. Prices retry automatically when '
            'you reload.</div>',
            unsafe_allow_html=True,
        )
        return
    cells = ""
    for code, last, chg in rows:
        dirn = "up" if (chg is not None and chg >= 0) else "down"
        chg_txt = fmt_pct(chg, 2, signed=True) if chg is not None else "—"
        cells += (
            f'<div class="ml-tape-item {dirn}">'
            f'<div class="ml-tape-code">{code}</div>'
            f'<div class="ml-tape-last">{fmt_num(last)}</div>'
            f'<div class="ml-tape-chg ml-{dirn}">{chg_txt}</div></div>'
        )
    st.markdown(f'<div class="ml-tape">{cells}</div>', unsafe_allow_html=True)
    st.markdown(
        f"<div class='ml-caption' style='margin:8px 2px 0'>Last close vs. prior "
        f"close · 1-day change · as of {fetched_at}. Live from Yahoo Finance, "
        f"cached locally.</div>",
        unsafe_allow_html=True,
    )


def _home() -> None:
    """The landing / home surface. Run by the navigation router below."""
    setup_page("Home", icon="◆")

    # ---- Hero -------------------------------------------------------------
    st.markdown(
        f"""
        <div class="ml-hero">
          <div class="ml-hero-text">
            <div class="ml-hero-eyebrow">Global markets · research terminal</div>
            <div class="ml-hero-title" role="heading" aria-level="1">MarketLens</div>
            <div class="ml-hero-tagline">Read the tape, then <span class="hl">test the thesis</span>.</div>
            <div class="ml-hero-sub">
              MarketLens pulls live prices for equity indices, commodities and FX, then runs the
              analysis a research desk actually uses — returns, volatility, drawdown, correlation,
              macro event studies, and rule-based strategy backtests against a buy-and-hold benchmark.
              It is a research tool, not an autonomous trading system, and it does not predict prices.
            </div>
          </div>
          {_hero_panel_html()}
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_tape()

    # ---- Modules (single CSS grid — uniform gaps, equal-height rows) ------
    # Parallel tools, not a sequence — so no 01/02/03 numbering. Each is a real
    # link to its page, carries the analytical primitive it works in as a mono
    # tag, and glosses that tag on hover for readers still learning the desk
    # vocabulary. Fields: (tag, name, description, page route, plain gloss).
    module_cards = "".join(
        f'<a class="ml-card ml-card-nav" href="/{route}" target="_self">'
        f'<div class="ml-card-code" title="{gloss}">{tag}</div>'
        f'<div class="ml-card-title" role="heading" aria-level="3">{name}</div>'
        f'<div class="ml-card-desc">{desc}</div>'
        f'<span class="ml-card-go">Open<span class="arw" aria-hidden="true">→</span></span></a>'
        for tag, name, desc, route, gloss in MODULES
    )
    st.markdown(
        '<div class="ml-section-label" role="heading" aria-level="2">'
        '<span class="idx" aria-hidden="true">§</span>Workspace</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="ml-grid ml-grid-3">{module_cards}</div>', unsafe_allow_html=True)

    # ---- Coverage (real desk codes as the structural device) --------------
    cov_cards = ""
    for cls in ASSET_CLASSES:
        assets = [a for a in ASSETS.values() if a.asset_class == cls]
        # Show the desk code (SPX) next to the data ticker (^GSPC) so the tape's
        # shorthand and the underlying symbol read as one thing, not two systems.
        items = "".join(
            f'<li>{a.name}<span class="mcode">{a.code}</span>'
            f'<span class="tkr">{a.ticker}</span></li>'
            for a in assets
        )
        cov_cards += (
            f'<div class="ml-card">'
            f'<div class="ml-card-eyebrow" role="heading" aria-level="3">{cls}</div>'
            f'<ul class="ml-cov-list">{items}</ul></div>'
        )
    st.markdown(
        '<div class="ml-section-label" role="heading" aria-level="2">'
        '<span class="idx" aria-hidden="true">§</span>Coverage</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="ml-grid ml-grid-3">{cov_cards}</div>', unsafe_allow_html=True)

    # ---- Closing invitation (peak-end: leave on an action, not fine print) -
    st.markdown(
        '<a class="ml-cta" href="/Market_Overview" target="_self">'
        '<span class="ml-cta-text">'
        '<span class="ml-cta-kicker">Start here</span>'
        '<span class="ml-cta-title">See every market at a glance</span></span>'
        '<span class="ml-cta-go">Open Market Overview<span class="arw" aria-hidden="true">→</span></span></a>',
        unsafe_allow_html=True,
    )

    # ---- Footer -----------------------------------------------------------
    st.markdown(
        '<div class="ml-footer"><b>Disclaimer.</b> MarketLens is an educational research '
        'tool. Nothing here is investment advice, a recommendation, or a guarantee of future '
        'performance. All figures are computed from historical market data. Market data is '
        'sourced from Yahoo Finance and cached locally; choose assets and date ranges from '
        'the sidebar on each page.</div>',
        unsafe_allow_html=True,
    )


# ---- Analytical primitive each Workspace card links to --------------------
# Fields: (tag, name, description, page route, plain-language gloss).
MODULES = [
    ("returns · vol · regime", "Market Overview",
     "Cross-asset KPIs — returns, volatility, trend and regime at a glance.",
     "Market_Overview",
     "Regime = whether volatility is currently low, normal, or high."),
    ("price · momentum · risk", "Asset Analysis",
     "Price structure, moving averages, momentum, volatility bands and drawdowns.",
     "Asset_Analysis",
     "Momentum = the speed and strength of a price trend (e.g. RSI, MACD)."),
    ("ρ · co-movement", "Cross-Market",
     "Correlation matrix, rolling correlation and comparative performance.",
     "Cross_Market",
     "ρ (rho) = correlation, from −1 (opposite) through 0 (unrelated) to +1 (in step)."),
    ("event study", "Macro Events",
     "Market behaviour around macro releases, window T−5 to T+5.",
     "Macro_Events",
     "Event study = average market behaviour in a window around an event; "
     "T−5…T+5 = five trading days before to five after."),
    ("backtest · P&L", "Strategy Lab",
     "Backtest MA-crossover and RSI mean-reversion against buy & hold.",
     "Strategy_Lab",
     "Backtest = replay a rule on historical data to see how it would have done; "
     "P&L = profit and loss."),
    ("auto summary", "Research Summary",
     "An automatically generated, data-driven market summary.",
     "Research_Summary",
     "Built only from computed metrics — descriptive, never advice."),
]


# ---- Navigation router ----------------------------------------------------
# st.navigation owns the sidebar: real titles (so the home page is "Home", not
# "streamlit app"), Material icons, and a fixed order. Page paths are relative
# to this entrypoint; url_path keeps the deep links used by the Workspace cards.
_PAGES = [
    st.Page(_home, title="Home", icon=":material/home:", default=True),
    st.Page("pages/1_Market_Overview.py", title="Market Overview",
            icon=":material/dashboard:", url_path="Market_Overview"),
    st.Page("pages/2_Asset_Analysis.py", title="Asset Analysis",
            icon=":material/candlestick_chart:", url_path="Asset_Analysis"),
    st.Page("pages/3_Cross_Market.py", title="Cross-Market",
            icon=":material/hub:", url_path="Cross_Market"),
    st.Page("pages/4_Macro_Events.py", title="Macro Events",
            icon=":material/event:", url_path="Macro_Events"),
    st.Page("pages/5_Strategy_Lab.py", title="Strategy Lab",
            icon=":material/query_stats:", url_path="Strategy_Lab"),
    st.Page("pages/6_Research_Summary.py", title="Research Summary",
            icon=":material/summarize:", url_path="Research_Summary"),
]
pg = st.navigation(_PAGES)
pg.run()

# ---- Sidebar footer: brand + provenance, shared across every page ----------
# Rendered after the page so it sits below any page controls, anchored to the
# bottom of the sidebar so the nav no longer trails off into empty space.
with st.sidebar:
    st.markdown(
        '<div class="ml-side-foot">'
        '<div class="ml-side-brand"><span class="dmd">◆</span>MarketLens</div>'
        '<div class="ml-side-tag">Global markets · research terminal</div>'
        '<div class="ml-side-note">Live prices from Yahoo Finance, cached locally. '
        'An educational research tool — not investment advice, and it does not '
        'predict prices.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
