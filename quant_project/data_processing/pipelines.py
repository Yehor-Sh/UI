"""Data preparation pipelines for offline and online modes."""
from __future__ import annotations

import logging
from typing import Dict

import pandas as pd

from quant_project.data_processing.fractional_diff import frac_diff_ffd
from quant_project.data_processing.features import build_feature_matrix

logger = logging.getLogger(__name__)


def prepare_offline_features(prices: pd.Series, config: Dict[str, int], d: float) -> pd.DataFrame:
    """Prepare features for offline research.

    Applies fractional differencing to combat non-stationarity, then builds
    derived features.
    """

    diffed = frac_diff_ffd(prices, d=d)
    aligned_prices = prices.loc[diffed.index]
    features = build_feature_matrix(aligned_prices, config)
    features["frac_diff"] = diffed
    features = features.dropna()
    logger.info("Offline features prepared with shape %s", features.shape)
    return features


def prepare_online_features(prices: pd.Series, config: Dict[str, int], d: float) -> pd.DataFrame:
    """Prepare features in a streaming context.

    Uses the same transformations but assumes `prices` is the most recent slice
    of data. In production this would maintain rolling buffers.
    """

    return prepare_offline_features(prices, config, d)
