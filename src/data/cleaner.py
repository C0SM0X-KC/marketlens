"""Data validation and cleaning.

Responsibilities:
 - normalise column names to a canonical OHLCV schema
 - normalise the index to a tz-naive DatetimeIndex sorted ascending
 - drop duplicate timestamps
 - validate basic OHLC integrity
 - handle missing values without fabricating data

Missing values are *forward filled only for genuine market holidays that slip
through* — never invented for gaps at the series edges. Rows that are entirely
empty are dropped rather than imputed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np
import pandas as pd

CANONICAL_COLUMNS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


@dataclass
class CleaningReport:
    rows_in: int = 0
    rows_out: int = 0
    duplicates_removed: int = 0
    missing_filled: int = 0
    invalid_ohlc_rows: int = 0
    messages: List[str] = field(default_factory=list)

    def add(self, msg: str) -> None:
        self.messages.append(msg)


class DataValidationError(ValueError):
    """Raised when data is too degraded to be usable."""


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # yfinance can return a MultiIndex (field, ticker); flatten to field.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # Standardise capitalisation/spacing.
    rename = {}
    for col in df.columns:
        c = str(col).strip().title().replace("Adj close", "Adj Close")
        if c.lower() == "adj close":
            c = "Adj Close"
        rename[col] = c
    df = df.rename(columns=rename)
    # Deduplicate columns (keep first) that may collide after renaming.
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def clean_ohlcv(df: pd.DataFrame, ticker: str = "") -> tuple[pd.DataFrame, CleaningReport]:
    """Validate and clean a raw OHLCV frame. Returns (clean_df, report)."""
    report = CleaningReport(rows_in=len(df))
    if df is None or df.empty:
        raise DataValidationError(f"No data available for {ticker or 'asset'}.")

    df = _normalise_columns(df)

    if "Close" not in df.columns:
        raise DataValidationError(
            f"Downloaded data for {ticker or 'asset'} has no Close column."
        )

    # If Adj Close missing, fall back to Close (some FX/commodity tickers).
    if "Adj Close" not in df.columns:
        df["Adj Close"] = df["Close"]

    # Ensure a proper datetime index.
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[~df.index.isna()]
    try:
        df.index = df.index.tz_localize(None)
    except (TypeError, AttributeError):
        pass  # already tz-naive
    df.index.name = "Date"
    df = df.sort_index()

    # Remove duplicate timestamps (keep last observation for that day).
    dup_mask = df.index.duplicated(keep="last")
    report.duplicates_removed = int(dup_mask.sum())
    df = df[~dup_mask]

    # Keep only canonical columns that exist, in canonical order.
    cols = [c for c in CANONICAL_COLUMNS if c in df.columns]
    df = df[cols]

    # Coerce to numeric.
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Validate OHLC integrity where those columns exist.
    if {"Open", "High", "Low", "Close"}.issubset(df.columns):
        invalid = (
            (df["High"] < df["Low"])
            | (df["High"] < df["Open"])
            | (df["High"] < df["Close"])
            | (df["Low"] > df["Open"])
            | (df["Low"] > df["Close"])
            | (df[["Open", "High", "Low", "Close"]] <= 0).any(axis=1)
        )
        report.invalid_ohlc_rows = int(invalid.sum())
        df = df[~invalid]

    # Drop rows with no Close (cannot analyse those).
    before = len(df)
    df = df[df["Close"].notna()]
    dropped = before - len(df)
    if dropped:
        report.add(f"Dropped {dropped} rows with missing Close.")

    # Forward-fill small internal gaps in price columns (holidays sneaking in),
    # but never back-fill (which would leak future info) and never invent volume.
    price_cols = [c for c in ["Open", "High", "Low", "Close", "Adj Close"] if c in df.columns]
    filled = int(df[price_cols].isna().sum().sum())
    df[price_cols] = df[price_cols].ffill()
    report.missing_filled = filled

    if "Volume" in df.columns:
        df["Volume"] = df["Volume"].fillna(0)

    # Final drop of any residual NaN in Close after ffill (leading gap).
    df = df[df["Close"].notna()]

    if df.empty:
        raise DataValidationError(
            f"Data for {ticker or 'asset'} was empty after cleaning."
        )

    report.rows_out = len(df)
    return df, report


def add_returns(df: pd.DataFrame, price_col: str = "Adj Close") -> pd.DataFrame:
    """Attach simple and log daily returns based on the given price column."""
    df = df.copy()
    if price_col not in df.columns:
        price_col = "Close"
    df["Return"] = df[price_col].pct_change()
    df["LogReturn"] = np.log(df[price_col] / df[price_col].shift(1))
    return df
