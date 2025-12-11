"""Portfolio simulation utilities."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pandas as pd

from quant_project.core.types import Position, Side

logger = logging.getLogger(__name__)


@dataclass
class SimulatedPortfolio:
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
    equity_curve: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))

    def update_position(self, symbol: str, side: Side, qty: float, price: float) -> None:
        pos = self.positions.get(symbol, Position(symbol, 0.0, price))
        if side == Side.BUY:
            total_cost = pos.avg_price * pos.quantity + qty * price
            pos.quantity += qty
            pos.avg_price = total_cost / pos.quantity
            self.cash -= qty * price
        else:
            pos.quantity -= qty
            self.cash += qty * price
            if pos.quantity <= 0:
                pos.quantity = 0
        self.positions[symbol] = pos
        logger.debug("Updated position %s: %s", symbol, pos)

    def mark_to_market(self, marks: dict[str, float]) -> float:
        value = self.cash
        for sym, pos in self.positions.items():
            value += pos.quantity * marks.get(sym, pos.avg_price)
        return value
