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

    def validate(self, portfolio: PortfolioState, symbol: str, proposed_qty: float, price: float) -> bool:
        equity = portfolio.total_value({symbol: price})
        exposure = abs(proposed_qty * price) / equity if equity else 0
        return exposure <= self.max_pct

    def cap_size(self, portfolio: PortfolioState, symbol: str, proposed_qty: float, price: float) -> float:
        """Return the capped quantity that adheres to the max position percentage."""

        equity = portfolio.total_value({symbol: price})
        if equity <= 0 or price <= 0:
            return 0.0

        max_qty = (self.max_pct * equity) / price
        capped_qty = min(abs(proposed_qty), max_qty)
        return capped_qty if proposed_qty >= 0 else -capped_qty
