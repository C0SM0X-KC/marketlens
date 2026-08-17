"""Moving Average Crossover strategy.

Long when the fast SMA is above the slow SMA (i.e. after the fast crosses
above), flat when it is below. Entry/exit therefore occur on the crossover
events described in the specification:

    Entry : SMA_fast crosses above SMA_slow
    Exit  : SMA_fast crosses below SMA_slow
"""
from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

from src.config import CONFIG
from src.strategies.base import Strategy
from src.technical.moving_averages import sma


class MovingAverageCrossover(Strategy):
    name = "Moving Average Crossover"

    def __init__(self, fast: Optional[int] = None, slow: Optional[int] = None):
        sd = CONFIG.strategy
        self.fast = fast or sd.ma_fast
        self.slow = slow or sd.ma_slow
        if self.fast >= self.slow:
            raise ValueError("fast window must be shorter than slow window")

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        price = df["Close"] if "Close" in df.columns else df.iloc[:, 0]
        fast = sma(price, self.fast)
        slow = sma(price, self.slow)
        # Target position: long while fast above slow.
        signal = (fast > slow).astype(float)
        # Undefined MA region -> flat.
        signal[fast.isna() | slow.isna()] = 0.0
        signal.name = "signal"
        return signal

    def params(self) -> Dict[str, object]:
        return {"fast": self.fast, "slow": self.slow}

    def describe(self) -> str:
        return f"{self.name} (SMA{self.fast}/SMA{self.slow})"
