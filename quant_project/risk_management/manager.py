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

    def __post_init__(self) -> None:
        self.rules = [MaxDailyLossRule(self.max_daily_loss), MaxPositionRule(self.max_position_pct)]

    def approve(self, signal: Signal, portfolio: PortfolioState, price: float) -> Optional[Signal]:
        """Evaluate risk rules for a signal.

        The risk manager may return the original signal, a modified one, or
        ``None`` if the trade should be blocked by the rules.
        """

        current_equity = portfolio.total_value({"asset": price})
        if not self.rules[0].validate(portfolio, current_equity):
            logger.warning("Max daily loss breached; blocking trade")
            return None

        position_rule: MaxPositionRule = self.rules[1]
        if not position_rule.validate(portfolio, "asset", signal.size, price):
            capped_size = position_rule.cap_size(portfolio, "asset", signal.size, price)
            if capped_size == 0:
                logger.warning("Position too large; blocking trade")
                return None
            logger.info(
                "Signal size adjusted by risk manager from %.4f to %.4f to respect position limits",
                signal.size,
                capped_size,
            )
            return replace(signal, size=capped_size)

        return signal


def build_risk_manager_from_config(config: Mapping[str, object]) -> Optional[RiskManager]:
    """Construct a :class:`RiskManager` from a backtest configuration mapping."""

    risk_cfg = config.get("risk") if config else None
    if not isinstance(risk_cfg, Mapping):
        return None

    max_daily_loss = float(risk_cfg.get("max_daily_loss", 0.0))
    max_position_pct = float(risk_cfg.get("max_position_pct", 0.0))
    if max_daily_loss == 0 and max_position_pct == 0:
        return None

    return RiskManager(max_daily_loss=max_daily_loss, max_position_pct=max_position_pct)
