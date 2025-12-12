"""Validation utilities following López de Prado's recommendations."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Iterable

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


def deflated_sharpe_ratio(returns: pd.Series, sr: float | None = None) -> float:
    """Simplified placeholder for deflated Sharpe Ratio.

    In production, implement the full formula from López de Prado, accounting for
    number of trials and non-normality. Here we fallback to naive Sharpe to keep
    the interface stable.
    """

    if sr is None:
        sr = returns.mean() / returns.std() * np.sqrt(252)
    logger.warning("Using simplified Sharpe Ratio; replace with deflated SR for production.")
    return sr
