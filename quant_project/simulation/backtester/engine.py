"""Backtest engine to run strategies on historical data."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from quant_project.core.types import PortfolioState, Signal, Trade
from quant_project.risk_management.manager import RiskManager
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
    risk_manager: Optional[RiskManager] = None

    def run(self, data: pd.DataFrame) -> PortfolioState:
        """Run backtest over provided data frame."""

        portfolio = SimulatedPortfolio(cash=self.initial_cash)
        equity_series = []

        for ts, row in data.iterrows():
            portfolio_state = PortfolioState(cash=portfolio.cash, positions=portfolio.positions, equity_curve=portfolio.equity_curve)
            signal = self.strategy.generate_signal(row, portfolio_state)
            price = row.get("close", 0.0)
            if signal:
                approved_signal = signal
                if self.risk_manager:
                    approved_signal = self.risk_manager.approve(signal, portfolio_state, price)
                    if approved_signal is None:
                        logger.info("Signal rejected by risk manager at %s", ts)
                        equity = portfolio.mark_to_market({"asset": price})
                        equity_series.append((ts, equity))
                        continue
                    if approved_signal is not signal:
                        logger.info("Signal modified by risk manager prior to sizing at %s", ts)

                approved_signal.size = fixed_fractional(approved_signal, portfolio, fraction=0.01, price=price)

                if self.risk_manager:
                    sized_signal = self.risk_manager.approve(approved_signal, portfolio_state, price)
                    if sized_signal is None:
                        logger.info("Sized signal rejected by risk manager at %s", ts)
                        equity = portfolio.mark_to_market({"asset": price})
                        equity_series.append((ts, equity))
                        continue
                    if sized_signal is not approved_signal or sized_signal.size != approved_signal.size:
                        logger.info(
                            "Signal modified by risk manager after sizing at %s (%.4f -> %.4f)",
                            ts,
                            approved_signal.size,
                            sized_signal.size,
                        )
                    approved_signal = sized_signal

                trade = _simulate_fill(approved_signal, price)
                portfolio.update_position(symbol="asset", side=approved_signal.side, qty=approved_signal.size, price=price)
                self.strategy.on_fill(approved_signal)
            equity = portfolio.mark_to_market({"asset": price})
            equity_series.append((ts, equity))
        portfolio.equity_curve = pd.Series(dict(equity_series))
        logger.info("Backtest completed. Final equity: %.2f", portfolio.equity_curve.iloc[-1])
        return PortfolioState(cash=portfolio.cash, positions=portfolio.positions, equity_curve=portfolio.equity_curve)
