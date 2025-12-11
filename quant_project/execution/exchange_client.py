"""Exchange client abstraction."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from binance.client import Client

from quant_project.core.types import Order, OrderType, Side

logger = logging.getLogger(__name__)


class BaseExchangeClient(ABC):
    """Abstract exchange client for placing and querying orders."""

    @abstractmethod
    def place_order(self, order: Order) -> Any:
        ...

    @abstractmethod
    def get_price(self, symbol: str) -> float:
        ...


class BinanceExchangeClient(BaseExchangeClient):
    """Thin wrapper around python-binance.

    In live paper mode, this is unused. Real trading should instantiate this
    client with API keys from environment variables.
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str | None = None) -> None:
        self.client = Client(api_key=api_key, api_secret=api_secret, base_url=base_url)

    def place_order(self, order: Order) -> Any:  # pragma: no cover - external dependency
        side = Client.SIDE_BUY if order.side == Side.BUY else Client.SIDE_SELL
        if order.order_type == OrderType.MARKET:
            response = self.client.create_order(symbol=order.symbol, side=side, type=Client.ORDER_TYPE_MARKET, quantity=order.quantity)
        else:
            response = self.client.create_order(
                symbol=order.symbol,
                side=side,
                type=Client.ORDER_TYPE_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=order.quantity,
                price=str(order.price),
            )
        logger.info("Placed Binance order %s", response)
        return response

    def get_price(self, symbol: str) -> float:
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
