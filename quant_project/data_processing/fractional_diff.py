"""Fractional differencing implementation.

Following López de Prado, fractional differencing retains long-memory properties
while achieving stationarity. This implementation computes fixed-width
fractional differences using binomial series coefficients.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def _get_weights(d: float, size: int) -> np.ndarray:
    """Compute fractional differencing weights."""

    w = [1.0]
    for k in range(1, size):
        w.append(-w[-1] * (d - k + 1) / k)
    w = np.array(w[::-1]).reshape(-1, 1)
    return w


def frac_diff(series: pd.Series, d: float, thresh: float = 1e-4) -> pd.Series:
    """Apply fractional differencing with fixed-width window.

    Parameters
    ----------
    series : pd.Series
        Price series to difference.
    d : float
        Order of differencing (non-integer).
    thresh : float
        Minimum weight magnitude to include. Helps truncate infinite series.
    """

    series = series.dropna()
    weights = _get_weights(d, series.shape[0])
    weights = weights[weights[:, 0].cumsum() > thresh]
    width = len(weights)
    logger.debug("Using %d fractional diff weights for d=%.3f", width, d)

    diffed = []
    for i in range(width, len(series)):
        window = series.iloc[i - width : i]
        diffed.append(np.dot(weights.T, window)[0])
    result = pd.Series(diffed, index=series.index[width:])
    return result


def frac_diff_ffd(series: pd.Series, d: float, thresh: float = 1e-4) -> pd.Series:
    """Fractional differencing with fixed-width window as in López de Prado.

    This variant preserves a fixed number of observations, which is useful for
    online settings where expanding windows are not feasible.
    """

    series = series.dropna()
    w = _get_weights(d, series.shape[0])
    w_cumsum = np.cumsum(abs(w))
    w = w[w_cumsum <= w_cumsum[-1] - thresh]
    width = len(w)
    logger.debug("FFD width=%d for d=%.3f", width, d)

    diffed = pd.Series(dtype=float)
    for i in range(width, len(series)):
        window = series.iloc[i - width : i]
        diffed.loc[series.index[i]] = np.dot(w.T, window)[0]
    return diffed
