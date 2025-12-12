"""Validation utilities following López de Prado's recommendations."""
from __future__ import annotations

import logging
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.metrics import accuracy_score

logger = logging.getLogger(__name__)


def purged_kfold(
    n_splits: int,
    embargo: int | None = None,
    index: Iterable[pd.Timestamp] | None = None,
    *,
    timestamps: Iterable[pd.Timestamp] | None = None,
    embargo_pct: float | None = None,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate purged and embargoed folds following López de Prado.

    Parameters
    ----------
    n_splits : int
        Number of folds.
    embargo : int, optional
        Embargo period in index units (e.g., hours) to avoid leakage across
        adjacent folds. Kept for backward compatibility. If provided alongside
        ``embargo_pct``, the percentage-based value takes precedence.
    index : Iterable[pd.Timestamp], optional
        Sorted timestamps. Kept for backward compatibility; ``timestamps`` is
        preferred.
    timestamps : Iterable[pd.Timestamp], optional
        Sorted timestamps aligned to the feature set; if omitted, ``index`` is
        used.
    embargo_pct : float, optional
        Fraction of samples to embargo on each side of a validation fold. When
        not provided, defaults to zero or ``embargo`` if passed.
    """

    source_index = timestamps if timestamps is not None else index
    if source_index is None:
        raise ValueError("Either timestamps or index must be provided for purged_kfold.")

    idx = pd.Index(source_index)
    if idx.is_monotonic_increasing is False:
        idx = idx.sort_values()

    embargo = int(len(idx) * (embargo_pct or 0)) if embargo_pct is not None else int(embargo or 0)
    fold_sizes = len(idx) // n_splits
    folds = []
    for k in range(n_splits):
        start = k * fold_sizes
        end = start + fold_sizes if k < n_splits - 1 else len(idx)
        test_idx = idx[start:end]
        embargo_start = max(0, start - embargo)
        embargo_end = min(len(idx), end + embargo)
        train_idx = idx.delete(np.arange(embargo_start, embargo_end))
        folds.append((train_idx.values, test_idx.values))
    logger.info("Generated %d purged folds with embargo=%d", n_splits, embargo)
    return folds


def evaluate_model(model: BaseEstimator, X: pd.DataFrame, y: pd.Series) -> float:
    preds = model.predict(X)
    return accuracy_score(y, preds)


def compute_hit_rate(preds: pd.Series, y_true: pd.Series) -> float:
    return (preds == y_true).mean()


def deflated_sharpe_ratio(
    returns: pd.Series,
    sr: float | None = None,
    n_trials: int = 1,
    sample_size: int | None = None,
) -> float:
    """Approximate deflated Sharpe Ratio (DSR).

    This approximation follows the intuition from López de Prado's *The Deflated
    Sharpe Ratio* paper, but makes simplified assumptions to avoid extra
    dependencies:

    * Returns are approximately independent and identically distributed with
      near-normal behaviour (skewness and excess kurtosis close to zero).
    * The variance of the estimated Sharpe ratio is approximated by
      ``(1 + 0.5 * SR**2) / (T - 1)`` where ``T`` is the sample size.
    * The penalty for multiple testing is derived from the expected maximum of
      ``n_trials`` Sharpe ratios drawn from the same distribution, approximated
      by a Gaussian quantile.

    Parameters
    ----------
    returns : pd.Series
        Series of strategy returns.
    sr : float | None, default None
        Pre-computed Sharpe ratio (annualised). If ``None``, it will be computed
        from the provided returns.
    n_trials : int, default 1
        Number of strategies or trials evaluated. Higher values increase the
        multiple-testing penalty.
    sample_size : int | None, default None
        Number of return observations. Defaults to ``len(returns)``.

    Notes
    -----
    This function returns a "deflated" Sharpe ratio that penalises multiple
    testing. It is an approximation intended for diagnostics and should not be
    treated as a statistically rigorous replacement for the full formulation.
    """

    from scipy.stats import norm

    if sr is None:
        sr = returns.mean() / returns.std() * np.sqrt(252)

    sample_size = sample_size or len(returns)
    if sample_size <= 1 or n_trials < 1:
        logger.info("Insufficient data for deflation; returning raw Sharpe ratio.")
        return sr

    # Variance of the Sharpe estimate under near-normal returns (Lopez de Prado, simplified)
    sr_variance = (1 + 0.5 * sr**2) / max(sample_size - 1, 1)
    sr_std = np.sqrt(sr_variance)

    # Multiple-testing penalty: expected maximum Sharpe across n_trials draws from N(0, sr_std)
    # Assumes zero true Sharpe under null; conservative for diagnostics.
    quantile = norm.ppf(1 - 1 / max(n_trials, 1))
    penalty = quantile * sr_std

    adjusted_sr = sr - penalty
    logger.debug(
        "Deflated SR computed with sr=%.4f, penalty=%.4f, n_trials=%d, sample_size=%d",
        sr,
        penalty,
        n_trials,
        sample_size,
    )
    return adjusted_sr
