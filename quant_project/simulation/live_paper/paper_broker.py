"""Paper broker simulating order fills."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from quant_project.core.types import ExecutionResult, Order, Trade

logger = logging.getLogger(__name__)


@dataclass
class PaperBroker:
    latency_ms: int = 0
    fee_rate: float = 0.0005
    trades: list[Trade] = field(default_factory=list)

    def execute(self, order: Order, mark_price: float) -> ExecutionResult:
        fee = abs(order.quantity) * mark_price * self.fee_rate
        trade = Trade(order_id=order.id, symbol=order.symbol, side=order.side, quantity=order.quantity, price=mark_price, fee=fee)
        self.trades.append(trade)
        logger.debug("Paper fill for order %s at %f", order.id, mark_price)
        return ExecutionResult(success=True, trade=trade)
