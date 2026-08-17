"""Market data acquisition.

Downloads historical OHLCV data via yfinance, caches it on disk, and returns a
cleaned frame. Network failures are handled gracefully: if a download fails but
a cached snapshot exists it is used; otherwise a clear error is raised for the
UI to display rather than crashing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional

import pandas as pd

from src.config import ASSETS, CONFIG, Asset
from src.data import cache
from src.data.cleaner import CleaningReport, DataValidationError, add_returns, clean_ohlcv


class DataUnavailableError(RuntimeError):
    """Raised when data cannot be obtained from the provider or cache."""


@dataclass
class LoadResult:
    key: str
    asset: Asset
    data: pd.DataFrame
    report: CleaningReport
    from_cache: bool
    stale: bool = False


def _default_dates(start: Optional[str], end: Optional[str]) -> tuple[str, str]:
    if end is None:
        end = date.today().isoformat()
    if start is None:
        start = CONFIG.analysis.default_start
    return start, end


def _download(ticker: str, start: str, end: str, interval: str) -> pd.DataFrame:
    """Thin wrapper around yfinance. Imported lazily so tests need no network."""
    import yfinance as yf

    # end is exclusive in yfinance; nudge forward by a day to include today.
    end_inclusive = (pd.Timestamp(end) + pd.Timedelta(days=1)).date().isoformat()
    df = yf.download(
        ticker,
        start=start,
        end=end_inclusive,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    return df


def load_asset(
    key: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    interval: str = "1d",
    use_cache: bool = True,
    force_refresh: bool = False,
) -> LoadResult:
    """Load a single asset by its config key (e.g. ``"SP500"``)."""
    if key not in ASSETS:
        raise KeyError(f"Unknown asset key: {key!r}")
    asset = ASSETS[key]
    start, end = _default_dates(start, end)
    ck = cache.cache_key(asset.ticker, start, end, interval)

    raw: Optional[pd.DataFrame] = None
    from_cache = False
    stale = False

    if use_cache and not force_refresh and cache.is_fresh(ck):
        raw = cache.load(ck)
        from_cache = raw is not None

    if raw is None:
        try:
            raw = _download(asset.ticker, start, end, interval)
            if raw is not None and not raw.empty:
                cache.save(ck, raw)
        except Exception as exc:  # network / provider error
            cached = cache.load(ck)
            if cached is not None and not cached.empty:
                raw = cached
                from_cache = True
                stale = True
            else:
                raise DataUnavailableError(
                    f"Could not download {asset.name} ({asset.ticker}) and no "
                    f"cached data is available. Provider error: {exc}"
                ) from exc

    try:
        clean, report = clean_ohlcv(raw, asset.ticker)
    except DataValidationError as exc:
        raise DataUnavailableError(str(exc)) from exc

    clean = add_returns(clean)
    return LoadResult(
        key=key, asset=asset, data=clean, report=report,
        from_cache=from_cache, stale=stale,
    )


def load_many(
    keys: List[str],
    start: Optional[str] = None,
    end: Optional[str] = None,
    interval: str = "1d",
    use_cache: bool = True,
    force_refresh: bool = False,
) -> Dict[str, LoadResult]:
    """Load several assets. Individual failures are skipped, not fatal."""
    out: Dict[str, LoadResult] = {}
    errors: Dict[str, str] = {}
    for k in keys:
        try:
            out[k] = load_asset(k, start, end, interval, use_cache, force_refresh)
        except Exception as exc:  # noqa: BLE001 - collect and report
            errors[k] = str(exc)
    if not out and errors:
        msg = "; ".join(f"{k}: {v}" for k, v in errors.items())
        raise DataUnavailableError(f"No assets could be loaded. {msg}")
    return out


def close_prices(results: Dict[str, LoadResult], price_col: str = "Adj Close") -> pd.DataFrame:
    """Combine several LoadResults into one aligned price frame (columns=keys)."""
    series = {}
    for k, r in results.items():
        col = price_col if price_col in r.data.columns else "Close"
        series[k] = r.data[col]
    frame = pd.DataFrame(series).sort_index()
    return frame


def returns_frame(results: Dict[str, LoadResult]) -> pd.DataFrame:
    """Combine daily returns of several assets into one aligned frame."""
    series = {k: r.data["Return"] for k, r in results.items()}
    return pd.DataFrame(series).sort_index()
