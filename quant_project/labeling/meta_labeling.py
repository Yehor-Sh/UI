"""Meta-labeling utilities."""
from __future__ import annotations

import logging
import pandas as pd

logger = logging.getLogger(__name__)


def build_meta_labels(primary_labels: pd.Series, outcomes: pd.Series) -> pd.Series:
    """Generate meta-labels indicating whether to act on primary signals.

    Meta-label is 1 when the primary signal's direction is correct, 0 otherwise.
    """

    aligned_outcomes = outcomes.loc[primary_labels.index]
    meta = (primary_labels == aligned_outcomes).astype(int)
    logger.info("Meta-labels generated with hit rate %.2f", meta.mean())
    return meta
