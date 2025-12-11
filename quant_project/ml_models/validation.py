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


def purged_kfold(n_splits: int, embargo: int, index: Iterable[pd.Timestamp]) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate purged and embargoed folds.

    Parameters
    ----------
    n_splits : int
        Number of folds.
    embargo : int
        Embargo period in index units (e.g., hours) to avoid leakage across
        adjacent folds.
    index : Iterable[pd.Timestamp]
        Sorted timestamps.
    """

    index = pd.Index(index)
    fold_sizes = len(index) // n_splits
    folds = []
    for k in range(n_splits):
        start = k * fold_sizes
        end = start + fold_sizes if k < n_splits - 1 else len(index)
        test_idx = index[start:end]
        embargo_start = max(0, start - embargo)
        embargo_end = min(len(index), end + embargo)
        train_idx = index.delete(np.arange(embargo_start, embargo_end))
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
