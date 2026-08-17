"""Macroeconomic event management.

Events are stored in a user-editable CSV (``data/macro_events.csv``) with the
schema:

    date, country, event, expected, actual, previous

Automatic retrieval of macro surprise numbers from a free, reliable source is
not available, so the app relies on this CSV. A seed of real, publicly-scheduled
event *dates* (FOMC rate decisions) is provided so the event-study tooling works
out of the box. Numeric surprise fields are left blank and can be filled in by
the user — no macro figures are fabricated.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd

from src.config import MACRO_EVENTS_CSV

EVENT_COLUMNS = ["date", "country", "event", "expected", "actual", "previous"]

EVENT_TYPES = [
    "Fed Rate Decision",
    "US CPI",
    "US Employment (NFP)",
    "US GDP",
    "RBI Rate Decision",
    "India CPI",
]

# Publicly-scheduled FOMC rate-decision dates (announcement day). These are a
# matter of public record; surprise figures are intentionally left blank.
_SEED_FOMC_DATES = [
    "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27", "2022-09-21",
    "2022-11-02", "2022-12-14",
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26",
    "2023-09-20", "2023-11-01", "2023-12-13",
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31",
    "2024-09-18", "2024-11-07", "2024-12-18",
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30",
]


def _seed_frame() -> pd.DataFrame:
    rows = [
        {"date": d, "country": "US", "event": "Fed Rate Decision",
         "expected": pd.NA, "actual": pd.NA, "previous": pd.NA}
        for d in _SEED_FOMC_DATES
    ]
    return pd.DataFrame(rows, columns=EVENT_COLUMNS)


def ensure_seed() -> None:
    """Create the events CSV with seed dates if it does not yet exist."""
    if not MACRO_EVENTS_CSV.exists():
        _seed_frame().to_csv(MACRO_EVENTS_CSV, index=False)


def load_events() -> pd.DataFrame:
    """Load and validate the macro events CSV."""
    ensure_seed()
    df = pd.read_csv(MACRO_EVENTS_CSV)
    missing = [c for c in EVENT_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"macro_events.csv missing columns: {missing}")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def add_event(
    date: str,
    country: str,
    event: str,
    expected: Optional[float] = None,
    actual: Optional[float] = None,
    previous: Optional[float] = None,
) -> pd.DataFrame:
    """Append a single event to the CSV and return the updated frame."""
    df = load_events()
    new = pd.DataFrame(
        [{
            "date": pd.to_datetime(date),
            "country": country,
            "event": event,
            "expected": expected if expected is not None else pd.NA,
            "actual": actual if actual is not None else pd.NA,
            "previous": previous if previous is not None else pd.NA,
        }],
        columns=EVENT_COLUMNS,
    )
    df = pd.concat([df, new], ignore_index=True)
    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(MACRO_EVENTS_CSV, index=False)
    return df


def import_events_csv(uploaded: pd.DataFrame, replace: bool = False) -> pd.DataFrame:
    """Merge an uploaded events frame into the store."""
    cols = [c for c in EVENT_COLUMNS if c in uploaded.columns]
    if "date" not in cols or "event" not in cols:
        raise ValueError("Uploaded CSV must contain at least 'date' and 'event'.")
    incoming = uploaded.reindex(columns=EVENT_COLUMNS)
    incoming["date"] = pd.to_datetime(incoming["date"], errors="coerce")
    incoming = incoming.dropna(subset=["date"])
    if replace:
        merged = incoming
    else:
        merged = pd.concat([load_events(), incoming], ignore_index=True)
    merged = (
        merged.drop_duplicates(subset=["date", "event", "country"])
        .sort_values("date")
        .reset_index(drop=True)
    )
    merged.to_csv(MACRO_EVENTS_CSV, index=False)
    return merged
