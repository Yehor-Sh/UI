"""Risk manager applying rules to candidate trades."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

from quant_project.core.types import PortfolioState, Signal
from quant_project.risk_management.rules import MaxDailyLossRule, MaxPositionRule

logger = logging.getLogger(__name__)


@dataclass
class RiskManager:
    max_daily_loss: float
    max_position_pct: float
    rules: List[object] = field(init=False)

    def __post_init__(self) -> None:
        self.rules = [MaxDailyLossRule(self.max_daily_loss), MaxPositionRule(self.max_position_pct)]

    def approve(self, signal: Signal, portfolio: PortfolioState, price: float) -> bool:
        """Evaluate risk rules for a signal."""

        current_equity = portfolio.total_value({"asset": price})
        if not self.rules[0].validate(portfolio, current_equity):
            logger.warning("Max daily loss breached; blocking trade")
            return False
        if not self.rules[1].validate(portfolio, "asset", signal.size, price):
            logger.warning("Position too large; blocking trade")
            return False
        return True
