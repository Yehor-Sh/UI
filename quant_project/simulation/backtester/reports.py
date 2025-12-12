"""Backtest report generation."""
from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from ml_models.validation import deflated_sharpe_ratio

logger = logging.getLogger(__name__)


def _max_drawdown(equity_curve: pd.Series) -> float:
    """Compute maximum drawdown for an equity curve."""

    running_max = equity_curve.cummax()
    drawdowns = (equity_curve - running_max) / running_max
    return drawdowns.min()


def basic_report(
    equity_curve: pd.Series,
    output_path: str | Path | None = None,
    n_trials: int = 1,
) -> dict[str, object]:
    """Generate basic performance metrics and plot.

    The report now includes a deflated Sharpe ratio to reduce overfitting risk by
    accounting for the number of strategies or trials evaluated.
    """

    returns = equity_curve.pct_change().dropna()
    sharpe = returns.mean() / returns.std() * (252 ** 0.5)
    hit_rate = (returns > 0).mean()
    d_sharpe = deflated_sharpe_ratio(returns, sr=sharpe, n_trials=n_trials, sample_size=len(returns))
    max_dd = _max_drawdown(equity_curve)
    trades_count = len(returns)

    metrics = {
        "sharpe": sharpe,
        "deflated_sharpe": d_sharpe,
        "hit_rate": hit_rate,
        "max_drawdown": max_dd,
        "final_equity": equity_curve.iloc[-1],
    }

    stats: dict[str, object] = {
        "equity_curve": equity_curve,
        "trades_count": trades_count,
        "metrics": metrics,
        # Backward-compatible keys
        "sharpe": sharpe,
        "hit_rate": hit_rate,
        "final_equity": equity_curve.iloc[-1],
    }

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

    logger.info(
        "Backtest metrics -> Trades: %d | Sharpe: %.3f | Deflated Sharpe: %.3f | Hit Rate: %.2f | Max DD: %.2f%%",
        trades_count,
        sharpe,
        d_sharpe,
        hit_rate,
        max_dd * 100,
    )

    return stats
