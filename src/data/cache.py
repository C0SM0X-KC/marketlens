"""Simple on-disk parquet/CSV cache for downloaded market data.

Caching avoids repeated network calls to the data provider and lets the app
work when the provider is temporarily unavailable (falling back to the last
good snapshot). Each asset/date-range request maps to a deterministic file.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config import CACHE_DIR, CONFIG


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.parquet"


def _meta_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.meta"


def cache_key(ticker: str, start: str, end: str, interval: str) -> str:
    safe_ticker = (
        ticker.replace("^", "IDX_")
        .replace("=", "_")
        .replace("/", "_")
        .replace(".", "_")
    )
    return f"{safe_ticker}__{start}__{end}__{interval}"


def is_fresh(key: str, ttl_hours: Optional[float] = None) -> bool:
    """Return True if a cache entry exists and is younger than the TTL."""
    ttl = CONFIG.cache_ttl_hours if ttl_hours is None else ttl_hours
    meta = _meta_path(key)
    if not (_cache_path(key).exists() and meta.exists()):
        return False
    try:
        saved_at = float(meta.read_text().strip())
    except (ValueError, OSError):
        return False
    age_hours = (time.time() - saved_at) / 3600.0
    return age_hours <= ttl


def load(key: str) -> Optional[pd.DataFrame]:
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        return pd.read_parquet(path)
    except Exception:
        return None


def save(key: str, df: pd.DataFrame) -> None:
    try:
        df.to_parquet(_cache_path(key))
        _meta_path(key).write_text(str(time.time()))
    except Exception:
        # Cache write failures must never break the pipeline.
        pass


def clear() -> int:
    """Delete all cache files. Returns number of files removed."""
    removed = 0
    for p in CACHE_DIR.glob("*"):
        try:
            p.unlink()
            removed += 1
        except OSError:
            pass
    return removed
