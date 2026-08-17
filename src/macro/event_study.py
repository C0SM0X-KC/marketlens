"""Event-study analysis around macroeconomic events.

For a given event date and asset, measures market behaviour over an event window
(default T-5 .. T+5) using actual market data. This is a descriptive study of
what markets did around events; it makes no causal claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.config import CONFIG


def _nearest_trading_index(index: pd.DatetimeIndex, date: pd.Timestamp) -> Optional[int]:
    """Position of the trading day on or immediately before ``date``."""
    pos = index.searchsorted(date, side="right") - 1
    if pos < 0 or pos >= len(index):
        return None
    return int(pos)


def event_window(
    data: pd.DataFrame,
    event_date: pd.Timestamp,
    pre: int = 5,
    post: int = 5,
    price_col: str = "Adj Close",
) -> Optional[pd.DataFrame]:
    """Return the price/return window around an event, indexed by offset T-n..T+n."""
    col = price_col if price_col in data.columns else "Close"
    index = data.index
    t0 = _nearest_trading_index(index, pd.Timestamp(event_date))
    if t0 is None:
        return None
    lo = t0 - pre
    hi = t0 + post
    if lo < 0 or hi >= len(index):
        # Partial window: clip to what is available.
        lo = max(lo, 0)
        hi = min(hi, len(index) - 1)
    window = data.iloc[lo : hi + 1].copy()
    offsets = list(range(lo - t0, hi - t0 + 1))
    window["Offset"] = offsets
    base_price = data[col].iloc[t0]
    window["CumReturnFromT0"] = window[col] / base_price - 1.0
    window["Return"] = window[col].pct_change()
    return window.set_index("Offset")


@dataclass
class EventStudyRow:
    asset_key: str
    ret_t0: float
    ret_pre: float          # cumulative return T-5..T-1
    ret_post: float         # cumulative return T0..T+5
    vol_pre: float          # std of returns before event
    vol_post: float         # std of returns after event
    price_move: float       # T-5 -> T+5 total move


def study_event(
    data_by_asset: Dict[str, pd.DataFrame],
    event_date: pd.Timestamp,
    pre: int = 5,
    post: int = 5,
    price_col: str = "Adj Close",
) -> pd.DataFrame:
    """Run the event study across several assets for a single event date."""
    rows: List[EventStudyRow] = []
    for key, data in data_by_asset.items():
        w = event_window(data, event_date, pre, post, price_col)
        if w is None or w.empty:
            continue
        col = price_col if price_col in w.columns else "Close"
        pre_slice = w[w.index < 0]["Return"]
        post_slice = w[w.index > 0]["Return"]
        ret_t0 = float(w.loc[0, "Return"]) if 0 in w.index else float("nan")
        first_price = w[col].iloc[0]
        last_price = w[col].iloc[-1]
        price_move = float(last_price / first_price - 1.0)
        ret_pre = float((1 + pre_slice.fillna(0)).prod() - 1.0)
        ret_post = float((1 + post_slice.fillna(0)).prod() - 1.0)
        rows.append(
            EventStudyRow(
                asset_key=key,
                ret_t0=ret_t0,
                ret_pre=ret_pre,
                ret_post=ret_post,
                vol_pre=float(pre_slice.std(ddof=1)) if len(pre_slice) > 1 else float("nan"),
                vol_post=float(post_slice.std(ddof=1)) if len(post_slice) > 1 else float("nan"),
                price_move=price_move,
            )
        )
    if not rows:
        return pd.DataFrame(
            columns=[
                "asset_key", "ret_t0", "ret_pre", "ret_post",
                "vol_pre", "vol_post", "price_move",
            ]
        )
    return pd.DataFrame([r.__dict__ for r in rows]).set_index("asset_key")


def average_event_path(
    data: pd.DataFrame,
    event_dates: List[pd.Timestamp],
    pre: int = 5,
    post: int = 5,
    price_col: str = "Adj Close",
) -> pd.DataFrame:
    """Average cumulative-return path across many events of the same type."""
    paths = []
    for d in event_dates:
        w = event_window(data, d, pre, post, price_col)
        if w is None or w.empty:
            continue
        paths.append(w["CumReturnFromT0"].rename(pd.Timestamp(d)))
    if not paths:
        return pd.DataFrame(columns=["mean", "count"])
    merged = pd.concat(paths, axis=1)
    out = pd.DataFrame(
        {"mean": merged.mean(axis=1), "count": merged.notna().sum(axis=1)}
    )
    return out
