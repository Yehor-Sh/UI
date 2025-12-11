"""Shared dataclasses and enums used across the system.

The types here represent a thin abstraction over market data, orders, trades,
and portfolio state. They are kept deliberately lightweight so that both the
research (backtest) and production-like (live paper) paths can share the same
interfaces.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import pandas as pd


class Side(str, Enum):
    """Order or signal side."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Supported order types.

    Real implementations would include more exotic types, but we limit to
    market and limit for clarity.
    """

    MARKET = "MARKET"
    LIMIT = "LIMIT"


@dataclass
class Bar:
    """Single OHLCV bar."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Signal:
    """Signal emitted by a strategy prior to risk checks."""

    timestamp: datetime
    side: Side
    confidence: float = 1.0
    size: float = 0.0


@dataclass
class Order:
    """Order to be sent to an exchange or paper broker."""

    id: str
    symbol: str
    side: Side
    quantity: float
    order_type: OrderType = OrderType.MARKET
    price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Trade:
    """Executed trade."""

    order_id: str
    symbol: str
    side: Side
    quantity: float
    price: float
    fee: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Position:
    """Represents an open position for a symbol."""

    symbol: str
    quantity: float
    avg_price: float

    def market_value(self, mark_price: float) -> float:
        """Compute mark-to-market value."""

        return self.quantity * mark_price


@dataclass
class PortfolioState:
    """State of the portfolio used by both backtests and live trading."""

    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
    equity_curve: pd.Series | None = None

    def total_value(self, marks: dict[str, float]) -> float:
        """Compute total portfolio value given current marks."""

        position_value = sum(pos.market_value(marks.get(sym, pos.avg_price)) for sym, pos in self.positions.items())
        return self.cash + position_value


@dataclass
class ExecutionResult:
    """Result from attempting to execute an order."""

    success: bool
    trade: Optional[Trade] = None
    message: str = ""
