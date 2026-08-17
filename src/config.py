"""Central configuration for MarketLens.

All tunable parameters, asset metadata, and analysis assumptions live here so
they are not scattered through the codebase. Import ``CONFIG`` or the specific
dataclasses/dicts you need rather than hardcoding values elsewhere.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CACHE_DIR = RAW_DIR / "cache"

for _d in (RAW_DIR, PROCESSED_DIR, CACHE_DIR):
    _d.mkdir(parents=True, exist_ok=True)

MACRO_EVENTS_CSV = DATA_DIR / "macro_events.csv"


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Asset:
    """Metadata describing a tradable/analyzable instrument."""

    key: str            # internal stable identifier
    name: str           # human readable name
    ticker: str         # yfinance ticker symbol
    asset_class: str    # Equity Index | Commodity | FX
    currency: str
    region: str
    code: str = ""      # short desk code shown on the market tape (e.g. SPX, XAU)


# Order here defines default display order in the UI.
ASSETS: Dict[str, Asset] = {
    "SP500": Asset("SP500", "S&P 500", "^GSPC", "Equity Index", "USD", "US", "SPX"),
    "NASDAQ100": Asset("NASDAQ100", "Nasdaq-100", "^NDX", "Equity Index", "USD", "US", "NDX"),
    "NIFTY50": Asset("NIFTY50", "NIFTY 50", "^NSEI", "Equity Index", "INR", "India", "NIFTY"),
    "GOLD": Asset("GOLD", "Gold", "GC=F", "Commodity", "USD", "Global", "XAU"),
    "CRUDE": Asset("CRUDE", "Crude Oil (WTI)", "CL=F", "Commodity", "USD", "Global", "WTI"),
    "USDINR": Asset("USDINR", "USD/INR", "USDINR=X", "FX", "INR", "India", "USDINR"),
}

ASSET_CLASSES: List[str] = ["Equity Index", "Commodity", "FX"]


def assets_by_class(asset_class: str) -> List[Asset]:
    return [a for a in ASSETS.values() if a.asset_class == asset_class]


def asset_keys() -> List[str]:
    return list(ASSETS.keys())


# ---------------------------------------------------------------------------
# Analysis assumptions
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AnalysisConfig:
    trading_days: int = 252
    risk_free_rate: float = 0.02          # annual, decimal
    default_start: str = "2015-01-01"
    default_lookback_years: int = 10

    # Volatility rolling windows (trading days)
    vol_short_window: int = 20
    vol_long_window: int = 60

    # Moving averages
    sma_windows: tuple = (20, 50, 200)
    ema_windows: tuple = (20, 50)

    # Momentum
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # Volatility indicators
    bb_window: int = 20
    bb_std: float = 2.0
    atr_period: int = 14

    # Trend classification (rule based)
    trend_fast_ma: int = 50
    trend_slow_ma: int = 200

    # Regime detection (volatility percentiles)
    regime_low_pct: float = 0.33
    regime_high_pct: float = 0.66
    regime_vol_window: int = 20

    # Correlation
    rolling_corr_window: int = 60


@dataclass(frozen=True)
class BacktestConfig:
    initial_capital: float = 100_000.0
    transaction_cost_bps: float = 5.0     # per trade side, basis points
    slippage_bps: float = 2.0             # per trade side, basis points
    # Default out-of-sample split
    dev_start: str = "2018-01-01"
    dev_end: str = "2023-12-31"
    oos_start: str = "2024-01-01"
    oos_end: str = "2025-12-31"


@dataclass(frozen=True)
class StrategyDefaults:
    ma_fast: int = 50
    ma_slow: int = 200
    rsi_period: int = 14
    rsi_entry: float = 30.0
    rsi_exit: float = 50.0


@dataclass(frozen=True)
class Config:
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    strategy: StrategyDefaults = field(default_factory=StrategyDefaults)
    cache_ttl_hours: float = float(os.getenv("MARKETLENS_CACHE_TTL_HOURS", "12"))


CONFIG = Config()

# Optional API keys (never hardcode secrets)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
