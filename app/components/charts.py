"""Plotly chart builders with a consistent professional style."""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go

from app.components.theme import PALETTE


_FONT = "'IBM Plex Sans', -apple-system, 'Segoe UI', Roboto, sans-serif"


def _base_layout(fig: go.Figure, height: int = 380, title: str = "") -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=8, r=12, t=48 if title else 18, b=8),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.0, x=0,
            font=dict(size=11, family=_FONT, color=PALETTE["muted"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=PALETTE["panel"], bordercolor=PALETTE["grid"],
            font=dict(family=_FONT, size=12, color=PALETTE["text"]),
        ),
        font=dict(color=PALETTE["muted"], size=11, family=_FONT),
        colorway=PALETTE["series"],
    )
    # Only set a title when there is one. Passing title=None to Plotly renders a
    # literal "undefined" label where the title would be, so never emit the key
    # for an untitled chart.
    if title:
        fig.update_layout(
            title=dict(
                text=f"<span style='color:{PALETTE['text']}'>{title}</span>",
                font=dict(size=14, family=_FONT), x=0, xanchor="left", y=0.98,
            )
        )
    axis_common = dict(
        showgrid=True, gridcolor=PALETTE["grid"], gridwidth=1, zeroline=False,
        showline=False, ticks="outside", ticklen=4, tickcolor=PALETTE["grid"],
        tickfont=dict(color=PALETTE["muted"], size=10.5, family=_FONT),
        showspikes=True, spikethickness=1, spikedash="dot",
        spikecolor=PALETTE["muted"], spikemode="across",
    )
    fig.update_xaxes(**axis_common)
    fig.update_yaxes(**{**axis_common, "showspikes": False})
    return fig


def line(
    df: pd.DataFrame,
    title: str = "",
    height: int = 380,
    pct: bool = False,
    colors: Optional[List[str]] = None,
) -> go.Figure:
    fig = go.Figure()
    cols = list(df.columns)
    palette = colors or PALETTE["series"]
    single = len(cols) == 1
    for i, col in enumerate(cols):
        # A single-series line needs no legend box — the title names it.
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df[col], name=str(col), mode="lines",
                line=dict(width=2, color=palette[i % len(palette)], shape="linear"),
                showlegend=not single,
            )
        )
    _base_layout(fig, height, title)
    if pct:
        fig.update_yaxes(tickformat=".0%")
    return fig


def price_with_mas(
    price: pd.Series, mas: pd.DataFrame, title: str = "", height: int = 460
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=price.index, y=price, name="Price", mode="lines",
                   line=dict(width=2, color=PALETTE["text"]))
    )
    for i, col in enumerate(mas.columns):
        fig.add_trace(
            go.Scatter(x=mas.index, y=mas[col], name=col, mode="lines",
                       line=dict(width=1.5, color=PALETTE["series"][i % len(PALETTE["series"])]))
        )
    return _base_layout(fig, height, title)


def candlestick(df: pd.DataFrame, title: str = "", height: int = 460) -> go.Figure:
    fig = go.Figure(
        go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            increasing_line_color=PALETTE["up"], decreasing_line_color=PALETTE["down"],
            name="OHLC",
        )
    )
    fig.update_layout(xaxis_rangeslider_visible=False)
    return _base_layout(fig, height, title)


def area_drawdown(dd: pd.Series, title: str = "", height: int = 320) -> go.Figure:
    # Single series: no legend box; area fill is a ~10% wash, not a saturated block.
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dd.index, y=dd, name="Drawdown", mode="lines", showlegend=False,
            line=dict(width=2, color=PALETTE["down"]),
            fill="tozeroy", fillcolor="rgba(239,83,80,0.12)",
        )
    )
    _base_layout(fig, height, title)
    fig.update_yaxes(tickformat=".0%")
    return fig


# Diverging scale for correlation: −1 red · 0 neutral gray · +1 blue.
_CORR_SCALE = [
    [0.0, PALETTE["div_neg"]],
    [0.5, PALETTE["div_mid"]],
    [1.0, PALETTE["div_pos"]],
]


def heatmap_corr(corr: pd.DataFrame, labels: Dict[str, str], title: str = "", height: int = 460) -> go.Figure:
    disp = [labels.get(c, c) for c in corr.columns]
    fig = go.Figure(
        go.Heatmap(
            z=corr.values, x=disp, y=disp,
            zmin=-1, zmax=1, zmid=0, colorscale=_CORR_SCALE,
            xgap=2, ygap=2,  # 2px surface gap between cells
            text=corr.round(2).values, texttemplate="%{text}",
            textfont=dict(size=11, family=_FONT, color=PALETTE["text_strong"]),
            colorbar=dict(
                title=dict(text="ρ", font=dict(color=PALETTE["muted"])),
                outlinewidth=0, tickfont=dict(color=PALETTE["muted"], size=10),
                thickness=12, len=0.9,
            ),
            hovertemplate="%{y} · %{x}<br>ρ = %{z:.2f}<extra></extra>",
        )
    )
    return _base_layout(fig, height, title)


def bars(
    series: pd.Series, title: str = "", height: int = 320, pct: bool = False,
    color_by_sign: bool = True,
) -> go.Figure:
    # Sign-coloured columns use the reserved up/down status hues; 4px rounded caps,
    # square at the baseline, with air between columns (bargap).
    if color_by_sign:
        colors = [PALETTE["up"] if v >= 0 else PALETTE["down"] for v in series]
    else:
        colors = PALETTE["accent"]
    fig = go.Figure(
        go.Bar(
            x=[str(i) for i in series.index], y=series.values,
            marker=dict(color=colors, cornerradius=4),
            hovertemplate="%{x}<br>%{y:.2%}<extra></extra>" if pct else "%{x}<br>%{y:.2f}<extra></extra>",
        )
    )
    _base_layout(fig, height, title)
    fig.update_layout(bargap=0.35)
    if pct:
        fig.update_yaxes(tickformat=".0%")
    return fig


def equity_vs_benchmark(
    strategy_equity: pd.Series, benchmark_equity: pd.Series,
    title: str = "", height: int = 420,
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=strategy_equity.index, y=strategy_equity, name="Strategy (net)",
                   mode="lines", line=dict(width=2, color=PALETTE["accent"]))
    )
    fig.add_trace(
        go.Scatter(x=benchmark_equity.index, y=benchmark_equity, name="Buy & Hold",
                   mode="lines", line=dict(width=1.6, color=PALETTE["muted"], dash="dot"))
    )
    return _base_layout(fig, height, title)


def rsi_chart(rsi: pd.Series, height: int = 220) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=rsi.index, y=rsi, name="RSI", mode="lines", showlegend=False,
                             line=dict(width=2, color=PALETTE["accent"])))
    fig.add_hline(y=70, line=dict(color=PALETTE["down"], width=1, dash="dash"),
                  annotation_text="70", annotation_position="right",
                  annotation_font=dict(color=PALETTE["muted"], size=10))
    fig.add_hline(y=30, line=dict(color=PALETTE["up"], width=1, dash="dash"),
                  annotation_text="30", annotation_position="right",
                  annotation_font=dict(color=PALETTE["muted"], size=10))
    _base_layout(fig, height, "RSI (14)")
    fig.update_yaxes(range=[0, 100])
    return fig


def macd_chart(macd_df: pd.DataFrame, height: int = 240) -> go.Figure:
    fig = go.Figure()
    hist_colors = [PALETTE["up"] if v >= 0 else PALETTE["down"] for v in macd_df["Histogram"]]
    fig.add_trace(go.Bar(x=macd_df.index, y=macd_df["Histogram"], name="Histogram",
                         marker=dict(color=hist_colors, cornerradius=2), opacity=0.55))
    fig.add_trace(go.Scatter(x=macd_df.index, y=macd_df["MACD"], name="MACD",
                             line=dict(width=2, color=PALETTE["accent"])))
    fig.add_trace(go.Scatter(x=macd_df.index, y=macd_df["Signal"], name="Signal",
                             line=dict(width=1.6, color=PALETTE["neutral"])))
    return _base_layout(fig, height, "MACD (12, 26, 9)")


def bollinger_chart(price: pd.Series, bb: pd.DataFrame, height: int = 380) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bb.index, y=bb["Upper"], name="Upper", mode="lines",
                             line=dict(width=1, color=PALETTE["muted"])))
    fig.add_trace(go.Scatter(x=bb.index, y=bb["Lower"], name="Lower", mode="lines",
                             line=dict(width=1, color=PALETTE["muted"]),
                             fill="tonexty", fillcolor="rgba(57,135,229,0.10)"))
    fig.add_trace(go.Scatter(x=bb.index, y=bb["Middle"], name="Middle (SMA 20)", mode="lines",
                             line=dict(width=1.4, color=PALETTE["neutral"], dash="dot")))
    fig.add_trace(go.Scatter(x=price.index, y=price, name="Price", mode="lines",
                             line=dict(width=2, color=PALETTE["text_strong"])))
    return _base_layout(fig, height, "Bollinger Bands (20, 2σ)")


def regime_timeline(regime_df: pd.DataFrame, height: int = 300) -> go.Figure:
    """Volatility line coloured by regime bands."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=regime_df.index, y=regime_df["Volatility"], name="Ann. Volatility",
                   mode="lines", line=dict(width=1.4, color=PALETTE["accent"]))
    )
    fig.add_trace(
        go.Scatter(x=regime_df.index, y=regime_df["LowThresh"], name="Low/Normal",
                   mode="lines", line=dict(width=1, color=PALETTE["up"], dash="dash"))
    )
    fig.add_trace(
        go.Scatter(x=regime_df.index, y=regime_df["HighThresh"], name="Normal/High",
                   mode="lines", line=dict(width=1, color=PALETTE["down"], dash="dash"))
    )
    _base_layout(fig, height, "Volatility Regime")
    fig.update_yaxes(tickformat=".0%")
    return fig


def event_paths(paths: pd.DataFrame, title: str = "", height: int = 360) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=paths.index, y=paths["mean"], name="Avg cumulative return",
            mode="lines+markers", showlegend=False,
            line=dict(width=2, color=PALETTE["accent"]),
            # markers >= 8px with a 2px surface ring so they stay legible on the line
            marker=dict(size=8, color=PALETTE["accent"],
                        line=dict(width=2, color=PALETTE["bg"])),
        )
    )
    fig.add_vline(x=0, line=dict(color=PALETTE["muted"], width=1, dash="dash"),
                  annotation_text="event (T=0)", annotation_position="top",
                  annotation_font=dict(color=PALETTE["muted"], size=10))
    fig.add_hline(y=0, line=dict(color=PALETTE["axis"], width=1))
    _base_layout(fig, height, title)
    fig.update_yaxes(tickformat=".1%")
    fig.update_xaxes(title=dict(text="Trading days relative to event (T)",
                                font=dict(color=PALETTE["muted"], size=11)))
    return fig
