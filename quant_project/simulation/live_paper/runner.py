"""Live paper runner."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import pandas as pd

from quant_project.core.types import Order, OrderType, PortfolioState
from quant_project.core.utils import generate_order_id
from quant_project.data_ingestion.live_stream import run_stream
from quant_project.simulation.live_paper.paper_broker import PaperBroker
from quant_project.simulation.live_paper.state import LiveSessionState
from quant_project.risk_management.manager import RiskManager
from quant_project.strategy_engine.base import Strategy
from quant_project.strategy_engine.position_sizing import fixed_fractional

logger = logging.getLogger(__name__)


def _row_from_bar(bar: pd.Series) -> pd.Series:
    return bar


async def _handle_bar(
    bar: pd.Series,
    strategy: Strategy,
    session: LiveSessionState,
    broker: PaperBroker,
    symbol: str,
    risk_manager: RiskManager | None = None,
) -> None:
    row = _row_from_bar(bar)
    signal = strategy.generate_signal(row, session.portfolio)
    price = row["close"]
    if signal:
        signal.size = fixed_fractional(signal, session.portfolio, fraction=0.01, price=price)
        if risk_manager:
            approved_signal = risk_manager.approve(signal, session.portfolio, price, symbol)
            if approved_signal is None:
                if risk_manager.trading_halted:
                    logger.error("Paper trading halted by risk manager; skipping trades for %s", symbol)
                else:
                    logger.info("Signal rejected by risk manager for %s at %s", symbol, bar.name)
                return
            signal = approved_signal
        order = Order(
            id=generate_order_id(),
            symbol=symbol,
            side=signal.side,
            quantity=signal.size,
            order_type=OrderType.MARKET,
        )
        result = broker.execute(order, mark_price=price)
        if result.success and result.trade:
            session.trades.append(result.trade)
            strategy.on_fill(signal)
            session.portfolio.cash -= result.trade.quantity * price if signal.side.value == "BUY" else 0
    logger.info("Live bar handled at %s", bar.name)


async def run_live_paper(
    strategy: Strategy,
    symbol: str,
    timeframe: str,
    poll_interval: float,
    initial_cash: float,
    risk_manager: RiskManager | None = None,
    risk_config: dict | None = None,
) -> LiveSessionState:
    portfolio = PortfolioState(cash=initial_cash, positions={})
    session = LiveSessionState(start_time=datetime.utcnow(), portfolio=portfolio)
    broker = PaperBroker()
    risk_manager = risk_manager or (RiskManager(**risk_config) if risk_config else None)

    async def callback(bar: pd.Series) -> None:
        await _handle_bar(bar, strategy, session, broker, symbol, risk_manager)

    await run_stream(symbol, timeframe, poll_interval, lambda bar: asyncio.create_task(callback(bar)))
    return session
