"""Backtest engine to run strategies on historical data."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

from quant_project.core.types import PortfolioState, Signal, Trade
from quant_project.simulation.backtester.portfolio import SimulatedPortfolio
from quant_project.strategy_engine.base import Strategy
from quant_project.strategy_engine.position_sizing import fixed_fractional

logger = logging.getLogger(__name__)


def _simulate_fill(signal: Signal, price: float) -> Trade:
    qty = abs(signal.size)
    side = signal.side
    return Trade(order_id="sim", symbol="", side=side, quantity=qty, price=price)


@dataclass
class BacktestEngine:
    strategy: Strategy
    initial_cash: float = 10000.0
    slippage: float = 0.0

    def run(self, data: pd.DataFrame) -> PortfolioState:
        """Run backtest over provided data frame."""

        portfolio = SimulatedPortfolio(cash=self.initial_cash)
        equity_series = []

        for ts, row in data.iterrows():
            signal = self.strategy.generate_signal(row, PortfolioState(cash=portfolio.cash, positions=portfolio.positions))
            price = row.get("close", 0.0)
            if signal:
                signal.size = fixed_fractional(signal, portfolio, fraction=0.01, price=price)
                trade = _simulate_fill(signal, price)
                portfolio.update_position(symbol="asset", side=signal.side, qty=signal.size, price=price)
                self.strategy.on_fill(signal)
            equity = portfolio.mark_to_market({"asset": price})
            equity_series.append((ts, equity))
        portfolio.equity_curve = pd.Series(dict(equity_series))
        logger.info("Backtest completed. Final equity: %.2f", portfolio.equity_curve.iloc[-1])
        return PortfolioState(cash=portfolio.cash, positions=portfolio.positions, equity_curve=portfolio.equity_curve)
