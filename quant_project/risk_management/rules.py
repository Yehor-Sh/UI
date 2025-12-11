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
