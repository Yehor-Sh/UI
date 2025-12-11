"""Historical data client.

Provides simplified accessors to load OHLCV data either from local storage or
from Binance REST. For demonstration, REST requests are stubbed; in practice you
would integrate with python-binance or ccxt.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from quant_project.core.utils import ensure_directory

logger = logging.getLogger(__name__)


class HistoricalDataClient:
    """Client to load historical OHLCV data."""

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = ensure_directory(data_dir)

    def load(
        self,
        symbol: str,
        timeframe: str,
        start: str,
        end: str,
        fmt: Literal["csv", "parquet"] = "parquet",
    ) -> pd.DataFrame:
        """Load historical data from disk or fetch from a remote source.

        The implementation favors reproducibility by persisting data locally in
        the configured `data_dir`.
        """

        file_path = self.data_dir / f"{symbol}_{timeframe}.{fmt}"
        if file_path.exists():
            logger.info("Loading %s data from %s", symbol, file_path)
            if fmt == "csv":
                df = pd.read_csv(file_path, parse_dates=["timestamp"], index_col="timestamp")
            else:
                df = pd.read_parquet(file_path)
        else:
            logger.info("Data for %s not found locally. Fetching stub data.", symbol)
            df = self._fetch_stub_data(symbol, timeframe, start, end)
            if fmt == "csv":
                df.to_csv(file_path)
            else:
                df.to_parquet(file_path)
        return df

    def _fetch_stub_data(self, symbol: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
        """Generate synthetic data for demonstration.

        Replace with actual Binance REST calls using python-binance client.
        """

        date_range = pd.date_range(start=start, end=end, freq=timeframe)
        prices = pd.Series(100 + np.random.randn(len(date_range)).cumsum(), index=date_range)
        df = pd.DataFrame(
            {
                "open": prices.shift(1).fillna(method="bfill"),
                "high": prices + 1,
                "low": prices - 1,
                "close": prices,
                "volume": np.random.rand(len(date_range)) * 10,
            }
        )
        df.index.name = "timestamp"
        return df
