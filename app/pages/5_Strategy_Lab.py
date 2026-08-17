"""Strategy Lab — backtest rule-based strategies against buy & hold."""
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
from app.components.theme import fmt_num, fmt_pct, fmt_ratio, page_header, setup_page
from src.analysis.drawdown import drawdown_from_returns
from src.backtesting.engine import run_backtest, split_dev_oos
from src.backtesting.metrics import PerformanceMetrics
from src.backtesting.transaction_costs import CostModel
from src.config import ASSETS, CONFIG
from src.strategies.moving_average import MovingAverageCrossover
from src.strategies.rsi import RSIMeanReversion

setup_page("Strategy Lab", icon="▨")
page_header(
    "Strategy Lab",
    "Backtest a rule-based strategy against a buy-and-hold benchmark. A one-bar "
    "execution lag is applied so signals never trade on same-day information.",
    section="Backtest",
)

start, end, _ = sidebar_dates()
key = single_asset_picker("Asset")
asset = ASSETS[key]

# ---- Strategy configuration ----------------------------------------------
st.markdown("#### Configuration")
cfg = st.columns([2, 2, 2])
strat_name = cfg[0].selectbox("Strategy", ["Moving Average Crossover", "RSI Mean Reversion"])

if strat_name == "Moving Average Crossover":
    fast = cfg[1].number_input("Fast SMA", 5, 150, CONFIG.strategy.ma_fast, 5)
    slow = cfg[2].number_input("Slow SMA", 20, 400, CONFIG.strategy.ma_slow, 10)
    try:
        strategy = MovingAverageCrossover(int(fast), int(slow))
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
else:
    rsi_p = cfg[1].number_input("RSI period", 2, 50, CONFIG.strategy.rsi_period, 1)
    entry = cfg[1].number_input("Entry (RSI <)", 5.0, 50.0, CONFIG.strategy.rsi_entry, 1.0)
    exit_ = cfg[2].number_input("Exit (RSI >)", 20.0, 90.0, CONFIG.strategy.rsi_exit, 1.0)
    try:
        strategy = RSIMeanReversion(int(rsi_p), float(entry), float(exit_))
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

cost_cols = st.columns(4)
capital = cost_cols[0].number_input("Initial capital", 1000, 10_000_000,
                                    int(CONFIG.backtest.initial_capital), 1000)
tc_bps = cost_cols[1].number_input("Transaction cost (bps/side)", 0.0, 100.0,
                                   CONFIG.backtest.transaction_cost_bps, 0.5)
slip_bps = cost_cols[2].number_input("Slippage (bps/side)", 0.0, 100.0,
                                     CONFIG.backtest.slippage_bps, 0.5)
oos = cost_cols[3].checkbox("Out-of-sample split", value=False,
                            help="Split into development and out-of-sample windows")

try:
    df, _fc, stale = get_asset_data(key, start, end)
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load {asset.name}: {exc}")
    st.stop()
if stale:
    st.warning("Live download failed — showing cached snapshot.")

cost_model = CostModel(transaction_cost_bps=tc_bps, slippage_bps=slip_bps)


def metrics_table(bench: PerformanceMetrics, strat: PerformanceMetrics) -> pd.DataFrame:
    rows = [
        ("Total Return", fmt_pct(bench.total_return), fmt_pct(strat.total_return)),
        ("CAGR", fmt_pct(bench.cagr), fmt_pct(strat.cagr)),
        ("Ann. Volatility", fmt_pct(bench.ann_volatility), fmt_pct(strat.ann_volatility)),
        ("Sharpe Ratio", fmt_ratio(bench.sharpe), fmt_ratio(strat.sharpe)),
        ("Max Drawdown", fmt_pct(bench.max_drawdown), fmt_pct(strat.max_drawdown)),
        ("Win Rate", "—", fmt_pct(strat.win_rate) if strat.num_trades else "—"),
        ("Trades", "1", str(strat.num_trades)),
        ("Avg Trade Return", "—", fmt_pct(strat.avg_trade_return) if strat.num_trades else "—"),
        ("Profit Factor", "—", fmt_ratio(strat.profit_factor) if strat.num_trades else "—"),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Buy & Hold", "Strategy"])


def render_result(bt, label: str = ""):
    if label:
        st.markdown(f"##### {label}")
    m = st.columns(4)
    m[0].metric("Strategy Total Return", fmt_pct(bt.metrics.total_return),
                fmt_pct(bt.metrics.total_return - bt.benchmark_metrics.total_return, signed=True))
    m[1].metric("Strategy Sharpe", fmt_ratio(bt.metrics.sharpe))
    m[2].metric("Strategy Max DD", fmt_pct(bt.metrics.max_drawdown))
    m[3].metric("Trades", str(bt.metrics.num_trades))

    st.plotly_chart(
        charts.equity_vs_benchmark(bt.equity, bt.benchmark_equity, "Equity curve"),
        width="stretch",
    )
    dc1, dc2 = st.columns(2)
    with dc1:
        st.plotly_chart(
            charts.area_drawdown(drawdown_from_returns(bt.strategy_returns), "Strategy drawdown"),
            width="stretch",
        )
    with dc2:
        st.plotly_chart(
            charts.area_drawdown(drawdown_from_returns(bt.benchmark_returns), "Buy & Hold drawdown"),
            width="stretch",
        )

    st.markdown("**Performance comparison**")
    st.dataframe(metrics_table(bt.benchmark_metrics, bt.metrics),
                 width="stretch", hide_index=True)

    # Gross vs net note
    st.caption(
        f"Gross strategy total return: {fmt_pct(bt.gross_metrics.total_return)} · "
        f"Net (after {tc_bps:g}bps cost + {slip_bps:g}bps slippage per side): "
        f"{fmt_pct(bt.metrics.total_return)}."
    )

    trades_df = bt.trades_dataframe()
    if not trades_df.empty:
        with st.expander(f"Trade history ({len(trades_df)} trades)"):
            show = trades_df.copy()
            show["entry_date"] = pd.to_datetime(show["entry_date"]).dt.date
            show["exit_date"] = pd.to_datetime(show["exit_date"]).dt.date
            show["return_pct"] = show["return_pct"].map(lambda v: fmt_pct(v, 2, True))
            show["entry_price"] = show["entry_price"].map(lambda v: fmt_num(v))
            show["exit_price"] = show["exit_price"].map(lambda v: fmt_num(v))
            st.dataframe(show, width="stretch", hide_index=True)


st.divider()
st.markdown(f"### Results — {strategy.describe()} on {asset.name}")

if not oos:
    bt = run_backtest(df, strategy, key, capital, cost_model)
    if len(df) < CONFIG.analysis.trend_slow_ma:
        st.warning("Short history relative to strategy windows — results may be unstable.")
    render_result(bt)
else:
    dev, oos_df = split_dev_oos(df)
    if dev.empty or oos_df.empty:
        st.warning("Not enough history for the configured dev/out-of-sample split. "
                   "Showing full-sample results instead.")
        render_result(run_backtest(df, strategy, key, capital, cost_model))
    else:
        st.caption(
            f"Development: {dev.index[0].date()} → {dev.index[-1].date()} · "
            f"Out-of-sample: {oos_df.index[0].date()} → {oos_df.index[-1].date()}"
        )
        render_result(run_backtest(dev, strategy, key, capital, cost_model),
                      "Development period")
        st.divider()
        render_result(run_backtest(oos_df, strategy, key, capital, cost_model),
                      "Out-of-sample period")
