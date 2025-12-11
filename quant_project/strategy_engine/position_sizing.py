"""Position sizing logic."""
from __future__ import annotations

import logging

from quant_project.core.types import PortfolioState, Signal

logger = logging.getLogger(__name__)


def fixed_fractional(signal: Signal, portfolio: PortfolioState, fraction: float, price: float) -> float:
    """Size position as a fraction of portfolio value."""

    equity = portfolio.cash + sum(pos.avg_price * pos.quantity for pos in portfolio.positions.values())
    risk_capital = equity * fraction
    size = risk_capital / price
    logger.debug("Fixed fractional size=%f for equity=%f", size, equity)
    return size
