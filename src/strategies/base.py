"""Strategy base class.

A strategy consumes a price/indicator DataFrame and produces a *target
position* series taking values in {0, 1} (flat or long). The signal for day t
must depend only on information available up to and including day t; the
backtesting engine applies a one-bar execution lag so signals generated from
day t's close are acted on at day t+1, preventing look-ahead bias.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd


class Strategy(ABC):
    name: str = "Strategy"

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Return a target-position series (0 or 1) aligned to df.index."""
        raise NotImplementedError

    def params(self) -> Dict[str, object]:
        """Return the strategy's configurable parameters (for display)."""
        return {}

    def describe(self) -> str:
        return self.name
