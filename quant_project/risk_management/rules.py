"""Risk rules implementations."""
from __future__ import annotations

from dataclasses import dataclass

from quant_project.core.types import PortfolioState, Signal


@dataclass
class MaxDailyLossRule:
    max_loss_pct: float

    def validate(self, portfolio: PortfolioState, current_equity: float) -> bool:
        if portfolio.equity_curve is None or portfolio.equity_curve.empty:
            return True
        start_equity = portfolio.equity_curve.iloc[0]
        drawdown = (start_equity - current_equity) / start_equity
        return drawdown < self.max_loss_pct


@dataclass
class MaxPositionRule:
    max_pct: float

    def adjust(self, portfolio: PortfolioState, symbol: str, signal: Signal, price: float) -> Signal | None:
        equity = portfolio.total_value({symbol: price})
        if price <= 0 or equity <= 0:
            return None

        max_quantity = (self.max_pct * equity) / price
        proposed_quantity = abs(signal.size)

        if proposed_quantity == 0:
            return signal

        if proposed_quantity <= max_quantity:
            return signal

        if max_quantity <= 0:
            return None

        adjusted_size = max_quantity
        return Signal(
            timestamp=signal.timestamp,
            side=signal.side,
            confidence=signal.confidence,
            size=adjusted_size,
        )
