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
    timestamps: pd.Series,
    embargo_pct: float = 0.01,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Generate purged and embargoed folds for time series cross-validation.

    The folds follow López de Prado's *Advances in Financial Machine Learning*
    chapter on **Cross-Validation in the presence of overlapping samples**.
    Each validation slice is contiguous in time, while training samples are
    "purged" (removed) if their timestamps overlap the validation window. An
    **embargo** interval on both sides of the validation window further removes
    temporally adjacent observations, reducing look-ahead bias from near-future
    information leaks.

    Parameters
    ----------
    n_splits : number of folds
    timestamps : pd.Series indexed like the samples (or aligned index) with datetime values
    embargo_pct : size of the embargo around validation segments, as fraction of total samples

    Returns
    -------
    List of (train_idx, test_idx) index arrays that:
    - are non-overlapping in time,
    - have purging: training samples that overlap in time with validation are removed,
    - have embargo: training samples within an embargo window around the validation fold are removed.
    """

    if n_splits < 2:
        raise ValueError("n_splits must be at least 2 for cross-validation")

    timestamps = pd.Series(timestamps)
    if timestamps.empty:
        return []

    n_samples = len(timestamps)
    embargo = int(np.ceil(n_samples * embargo_pct)) if embargo_pct > 0 else 0

    # Build contiguous time-based folds using positional indices to preserve order.
    fold_sizes = np.full(n_splits, n_samples // n_splits, dtype=int)
    fold_sizes[: n_samples % n_splits] += 1

    splits: List[Tuple[np.ndarray, np.ndarray]] = []
    start = 0
    for fold_size in fold_sizes:
        stop = start + fold_size
        test_pos = np.arange(start, stop)
        test_idx = timestamps.index[test_pos].to_numpy()

        test_start_ts = timestamps.iloc[test_pos[0]]
        test_end_ts = timestamps.iloc[test_pos[-1]]

        # Purge any training observation whose timestamp overlaps the validation interval.
        purge_mask = (timestamps >= test_start_ts) & (timestamps <= test_end_ts)

        # Apply an embargo window around the validation slice using positional indices.
        embargo_start = max(0, test_pos[0] - embargo)
        embargo_end = min(n_samples, test_pos[-1] + embargo + 1)
        embargo_mask = np.zeros(n_samples, dtype=bool)
        embargo_mask[embargo_start:embargo_end] = True

        train_mask = ~(purge_mask | embargo_mask)
        train_idx = timestamps.index[train_mask].to_numpy()

        splits.append((train_idx, test_idx))
        start = stop

    logger.info(
        "Generated %d purged folds with embargo_pct=%.4f (embargo=%d samples)",
        n_splits,
        embargo_pct,
        embargo,
    )
    return splits


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
