"""Macro Events — event-study analysis around macroeconomic releases."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from app.components import charts
from app.components.controls import sidebar_dates
from app.components.data import asset_label, load_selected
from app.components.theme import fmt_pct, page_header, setup_page
from src.config import ASSETS
from src.macro import event_study, events

setup_page("Macro Events", icon="▨")
page_header(
    "Macroeconomic Event Study",
    "A descriptive look at how markets behaved around macro releases — no causal "
    "claims. Event dates come from an editable CSV; surprise figures are never fabricated.",
    section="Macro",
)

start, end, _ = sidebar_dates()

try:
    ev = events.load_events()
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load macro events: {exc}")
    st.stop()

with st.expander("Manage events (add / import)"):
    st.markdown("**Add a single event**")
    fc = st.columns(6)
    a_date = fc[0].date_input("Date", key="ev_date")
    a_country = fc[1].text_input("Country", "US", key="ev_country")
    a_event = fc[2].selectbox("Event", events.EVENT_TYPES, key="ev_event")
    a_exp = fc[3].text_input("Expected", "", key="ev_exp")
    a_act = fc[4].text_input("Actual", "", key="ev_act")
    a_prev = fc[5].text_input("Previous", "", key="ev_prev")
    if st.button("Add event"):
        try:
            events.add_event(
                str(a_date), a_country, a_event,
                float(a_exp) if a_exp else None,
                float(a_act) if a_act else None,
                float(a_prev) if a_prev else None,
            )
            st.success("Event added.")
            st.cache_data.clear()
            ev = events.load_events()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not add event: {exc}")

    st.markdown("**Import events CSV** (columns: date, country, event, expected, actual, previous)")
    up = st.file_uploader("Upload CSV", type=["csv"], key="ev_upload")
    if up is not None:
        try:
            incoming = pd.read_csv(up)
            merged = events.import_events_csv(incoming)
            st.success(f"Imported. Store now has {len(merged)} events.")
            ev = merged
        except Exception as exc:  # noqa: BLE001
            st.error(f"Import failed: {exc}")

# ---- Event selection ------------------------------------------------------
st.markdown("#### Select an event")
sc = st.columns([2, 3])
event_type = sc[0].selectbox("Event type", ["All"] + sorted(ev["event"].unique().tolist()))
subset = ev if event_type == "All" else ev[ev["event"] == event_type]
subset = subset.sort_values("date", ascending=False)

if subset.empty:
    st.info("No events of this type.")
    st.stop()

date_options = subset["date"].dt.date.tolist()
sel_date = sc[1].selectbox(
    "Event date", date_options,
    format_func=lambda d: f"{d} · {subset[subset['date'].dt.date == d]['event'].iloc[0]}",
)
event_row = subset[subset["date"].dt.date == sel_date].iloc[0]

pre = st.slider("Pre-event window (T-n)", 1, 10, 5)
post = st.slider("Post-event window (T+n)", 1, 10, 5)

# ---- Load data for all assets and run the study ---------------------------
study_keys = list(ASSETS.keys())
data, errors = load_selected(study_keys, start, end)
for k, msg in errors.items():
    st.warning(f"{asset_label(k)}: {msg}")

if not data:
    st.error("No market data available for the event study.")
    st.stop()

result = event_study.study_event(data, pd.Timestamp(sel_date), pre, post)

st.markdown(f"#### Market behaviour around {event_row['event']} — {sel_date}")
if result.empty:
    st.info("The selected event date falls outside the available price history for these assets.")
else:
    disp = result.copy()
    disp.index = [ASSETS[k].name for k in disp.index]
    fmt_map = {c: (lambda v: fmt_pct(v, 2, True)) for c in
               ["ret_t0", "ret_pre", "ret_post", "price_move"]}
    fmt_map["vol_pre"] = lambda v: fmt_pct(v, 2)
    fmt_map["vol_post"] = lambda v: fmt_pct(v, 2)
    disp = disp.rename(columns={
        "ret_t0": "Return T0", "ret_pre": "Cum. T-n..T-1",
        "ret_post": "Cum. T0..T+n", "vol_pre": "Vol pre",
        "vol_post": "Vol post", "price_move": "Move T-n..T+n",
    })
    st.dataframe(
        disp.style.format({
            "Return T0": lambda v: fmt_pct(v, 2, True),
            "Cum. T-n..T-1": lambda v: fmt_pct(v, 2, True),
            "Cum. T0..T+n": lambda v: fmt_pct(v, 2, True),
            "Move T-n..T+n": lambda v: fmt_pct(v, 2, True),
            "Vol pre": lambda v: fmt_pct(v, 2),
            "Vol post": lambda v: fmt_pct(v, 2),
        }),
        width="stretch",
    )

# ---- Average path across all events of this type --------------------------
if event_type != "All":
    st.markdown(f"#### Average path across all '{event_type}' events")
    asset_for_path = st.selectbox(
        "Asset", study_keys, format_func=asset_label, key="path_asset"
    )
    if asset_for_path in data:
        dates = subset["date"].tolist()
        path = event_study.average_event_path(data[asset_for_path], dates, pre, post)
        if not path.empty:
            st.plotly_chart(
                charts.event_paths(path, f"{asset_label(asset_for_path)} · avg of {int(path['count'].max())} events"),
                width="stretch",
            )
            st.caption("Averaged cumulative return relative to each event day (T=0).")
        else:
            st.info("No usable event windows for this asset.")
