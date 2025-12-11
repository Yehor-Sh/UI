"""Feature engineering utilities."""
from __future__ import annotations

import logging
from typing import Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_returns(prices: pd.Series) -> pd.Series:
    """Compute log returns."""

    returns = np.log(prices).diff().dropna()
    logger.debug("Computed returns with %d observations", len(returns))
    return returns


def rolling_volatility(returns: pd.Series, window: int) -> pd.Series:
    """Compute rolling volatility."""

    vol = returns.rolling(window).std().dropna()
    logger.debug("Computed rolling volatility window=%d", window)
    return vol


def simple_moving_average(prices: pd.Series, window: int) -> pd.Series:
    """Compute SMA."""

    sma = prices.rolling(window).mean().dropna()
    logger.debug("Computed SMA window=%d", window)
    return sma


def momentum(prices: pd.Series, window: int) -> pd.Series:
    """Compute price momentum as difference between price and rolling mean."""

    mom = prices - prices.rolling(window).mean()
    return mom.dropna()


def build_feature_matrix(prices: pd.Series, config: Dict[str, int]) -> pd.DataFrame:
    """Build a basic feature matrix.

    In research, this would be replaced with richer alpha factors. Here we keep a
    concise set to demonstrate integration with labeling and modeling.
    """

    features = pd.DataFrame(index=prices.index)
    features["returns"] = compute_returns(prices)
    for name, window in config.items():
        if name.startswith("sma"):
            features[name] = simple_moving_average(prices, window)
        elif name.startswith("vol"):
            features[name] = rolling_volatility(features["returns"], window)
        elif name.startswith("mom"):
            features[name] = momentum(prices, window)
    features = features.dropna()
    logger.info("Feature matrix built with shape %s", features.shape)
    return features
