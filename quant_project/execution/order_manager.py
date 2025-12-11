"""Order manager to convert target positions into orders."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from quant_project.core.types import Order, OrderType, Side
from quant_project.core.utils import generate_order_id

logger = logging.getLogger(__name__)


@dataclass
class TargetPosition:
    symbol: str
    quantity: float


def generate_orders(current_qty: float, target: TargetPosition, price: float) -> List[Order]:
    """Generate market orders to reach target position."""

    delta = target.quantity - current_qty
    if delta == 0:
        return []
    side = Side.BUY if delta > 0 else Side.SELL
    order = Order(id=generate_order_id(), symbol=target.symbol, side=side, quantity=abs(delta), order_type=OrderType.MARKET, price=price)
    logger.debug("Generated order %s to move from %f to %f", order.id, current_qty, target.quantity)
    return [order]
