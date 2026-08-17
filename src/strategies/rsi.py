"""RSI Mean Reversion strategy.

Enter long when RSI falls below the entry threshold (oversold); exit when RSI
rises above the exit threshold. The position is *stateful*: once long, it is
held while RSI is between the thresholds, until the exit level is reached.

    Entry : RSI < entry (default 30)
    Exit  : RSI > exit  (default 50)
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd

from src.config import CONFIG
from src.strategies.base import Strategy
from src.technical.momentum import rsi


class RSIMeanReversion(Strategy):
    name = "RSI Mean Reversion"

    def __init__(
        self,
        period: Optional[int] = None,
        entry: Optional[float] = None,
        exit: Optional[float] = None,
    ):
        sd = CONFIG.strategy
        self.period = period or sd.rsi_period
        self.entry = sd.rsi_entry if entry is None else entry
        self.exit = sd.rsi_exit if exit is None else exit
        if self.entry >= self.exit:
            raise ValueError("entry threshold must be below exit threshold")

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        price = df["Close"] if "Close" in df.columns else df.iloc[:, 0]
        r = rsi(price, self.period)

        position = np.zeros(len(r), dtype=float)
        state = 0
        values = r.to_numpy()
        for i, val in enumerate(values):
            if np.isnan(val):
                position[i] = 0.0
                continue
            if state == 0 and val < self.entry:
                state = 1
            elif state == 1 and val > self.exit:
                state = 0
            position[i] = state

        return pd.Series(position, index=r.index, name="signal")

    def params(self) -> Dict[str, object]:
        return {"period": self.period, "entry": self.entry, "exit": self.exit}

    def describe(self) -> str:
        return f"{self.name} (RSI{self.period} <{self.entry:g}/>{self.exit:g})"
