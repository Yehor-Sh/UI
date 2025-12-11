"""Strategy base interfaces."""
from __future__ import annotations

import abc
from datetime import datetime

import pandas as pd

from quant_project.core.types import PortfolioState, Signal


class Strategy(abc.ABC):
    """Abstract base strategy class."""

    @abc.abstractmethod
    def fit(self, data: pd.DataFrame) -> None:
        """Fit the strategy models from data."""

    @abc.abstractmethod
    def generate_signal(self, row: pd.Series, portfolio: PortfolioState) -> Signal | None:
        """Generate a trading signal for a single observation."""

    @abc.abstractmethod
    def on_fill(self, signal: Signal) -> None:
        """Handle post-fill actions such as state updates."""
