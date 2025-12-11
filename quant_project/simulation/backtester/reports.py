"""Backtest report generation."""
from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)


def basic_report(equity_curve: pd.Series, output_path: str | Path | None = None) -> dict[str, float]:
    """Generate basic performance metrics and plot."""

    returns = equity_curve.pct_change().dropna()
    sharpe = returns.mean() / returns.std() * (252 ** 0.5)
    hit_rate = (returns > 0).mean()
    stats = {"sharpe": sharpe, "hit_rate": hit_rate, "final_equity": equity_curve.iloc[-1]}

    plt.figure(figsize=(8, 4))
    equity_curve.plot(title="Equity Curve")
    plt.xlabel("Time")
    plt.ylabel("Equity")
    plt.tight_layout()
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path)
        logger.info("Saved backtest report to %s", output_path)
    plt.close()
    return stats
