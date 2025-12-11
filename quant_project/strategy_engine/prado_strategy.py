"""Prado-style strategy combining primary and meta models."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd
from sklearn.pipeline import Pipeline

from quant_project.core.types import PortfolioState, Side, Signal
from quant_project.strategy_engine.base import Strategy

logger = logging.getLogger(__name__)


def _side_from_prediction(pred: int) -> Side:
    return Side.BUY if pred > 0 else Side.SELL


@dataclass
class PradoStrategy(Strategy):
    """Primary + meta-model strategy.

    The primary model predicts direction; the meta-model decides whether to act
    on the primary signal (abstention). This mirrors López de Prado's
    meta-labeling approach to reduce false positives.
    """

    primary_model: Pipeline
    meta_model: Pipeline | None = None
    threshold: float = 0.5

    def fit(self, data: pd.DataFrame) -> None:  # pragma: no cover - simplified
        logger.info("Strategy fit called; in this template models are pre-trained.")

    def generate_signal(self, row: pd.Series, portfolio: PortfolioState) -> Signal | None:
        features = row.values.reshape(1, -1)
        primary_pred = self.primary_model.predict(features)[0]
        side = _side_from_prediction(primary_pred)

        if self.meta_model is not None:
            proba = self.meta_model.predict_proba(features)[0][1]
            logger.debug("Meta probability: %.3f", proba)
            if proba < self.threshold:
                return None
        return Signal(timestamp=row.name, side=side, confidence=1.0, size=0.0)

    def on_fill(self, signal: Signal) -> None:
        logger.info("Executed signal: %s", signal)
