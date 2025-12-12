"""Risk manager applying rules to candidate trades."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from typing import List, Mapping, Optional

from quant_project.core.types import PortfolioState, Signal
from quant_project.risk_management.rules import MaxDailyLossRule, MaxPositionRule

logger = logging.getLogger(__name__)


@dataclass
class RiskManager:
    max_daily_loss: float
    max_position_pct: float
    rules: List[object] = field(init=False)
    trading_halted: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.rules = [MaxDailyLossRule(self.max_daily_loss), MaxPositionRule(self.max_position_pct)]

    def approve(self, signal: Signal, portfolio: PortfolioState, price: float, symbol: str = "asset") -> Signal | None:
        """Evaluate risk rules for a signal.

        Returns an adjusted ``Signal`` if it passes risk checks, or ``None`` if
        the trade should be blocked.
        """

        current_equity = portfolio.total_value({symbol: price})
        if not self.rules[0].validate(portfolio, current_equity):
            self.trading_halted = True
            logger.error("Max daily loss breached; halting paper trading")
            return None

        if self.trading_halted:
            logger.error("Paper trading halted due to previous risk breach")
            return None

        adjusted_signal = self.rules[1].adjust(portfolio, symbol, signal, price)
        if adjusted_signal is None:
            logger.warning("Position too large; blocking trade")
            return None

        if adjusted_signal.size != signal.size:
            logger.info(
                "Signal size adjusted from %.4f to %.4f to satisfy position limits", signal.size, adjusted_signal.size
            )

        return adjusted_signal
