"""Transaction cost and slippage model.

Costs are expressed in basis points applied per trade side to the traded
notional. Slippage is modelled as an adverse price move of the configured bps
on entry and exit.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.config import CONFIG


@dataclass(frozen=True)
class CostModel:
    transaction_cost_bps: float
    slippage_bps: float

    @classmethod
    def from_config(
        cls,
        transaction_cost_bps: Optional[float] = None,
        slippage_bps: Optional[float] = None,
    ) -> "CostModel":
        bt = CONFIG.backtest
        return cls(
            transaction_cost_bps=(
                bt.transaction_cost_bps if transaction_cost_bps is None else transaction_cost_bps
            ),
            slippage_bps=bt.slippage_bps if slippage_bps is None else slippage_bps,
        )

    @property
    def total_bps_per_side(self) -> float:
        return self.transaction_cost_bps + self.slippage_bps

    def cost_fraction(self) -> float:
        """Combined cost as a fraction of notional, per trade side."""
        return self.total_bps_per_side / 10_000.0

    def apply_execution_price(self, price: float, side: int) -> float:
        """Adjust an execution price for slippage.

        side = +1 for a buy (price slips up), -1 for a sell (price slips down).
        """
        slip = self.slippage_bps / 10_000.0
        return price * (1.0 + side * slip)
