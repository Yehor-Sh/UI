"""Shared helper utilities."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load YAML configuration file."""

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    logger.debug("Loaded YAML from %s", path)
    return data


def ensure_directory(path: str | Path) -> Path:
    """Create directory if it does not exist."""

    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def generate_order_id(prefix: str = "ord") -> str:
    """Generate a simple time-based order id."""

    return f"{prefix}-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"


def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample OHLCV data to a new timeframe."""

    ohlc_dict = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    return df.resample(rule).agg(ohlc_dict).dropna()
