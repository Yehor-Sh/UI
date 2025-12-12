"""Historical data client.

Provides simplified accessors to load OHLCV data either from local storage,
synthetic generation, or the live Binance REST API using python-binance.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd

try:
    from binance.client import Client as SyncClient
except ImportError:  # pragma: no cover - runtime dependency
    SyncClient = None
    logger.warning(
        "python-binance not installed; Binance historical downloads will be unavailable.")

from quant_project.core.utils import ensure_directory


class HistoricalDataClient:
    """Client to load historical OHLCV data."""

    def __init__(self, data_dir: str | Path, binance_config: dict[str, Any] | None = None) -> None:
        self.data_dir = ensure_directory(data_dir)
        self.binance_config = binance_config or {}

    def load(
        self,
        symbol: str,
        interval: str,
        start: str | datetime,
        end: str | datetime,
        source: Literal["binance", "synthetic"] = "synthetic",
        fmt: Literal["csv", "parquet"] = "parquet",
    ) -> pd.DataFrame:
        """Load historical data from disk or fetch from a remote source.

        The implementation favors reproducibility by persisting data locally in
        the configured `data_dir`.
        """

        file_path = self.data_dir / f"{symbol}_{interval}_{source}.{fmt}"
        if file_path.exists():
            logger.info("Loading %s %s data from %s", symbol, interval, file_path)
            if fmt == "csv":
                df = pd.read_csv(file_path, parse_dates=["timestamp"], index_col="timestamp")
            else:
                df = pd.read_parquet(file_path)
            logger.info("Loaded %s rows for %s from cache", len(df), symbol)
            return df

        start_ts = pd.to_datetime(start, utc=True)
        end_ts = pd.to_datetime(end, utc=True)

        logger.info(
            "Fetching %s data for %s from %s to %s via %s",
            interval,
            symbol,
            start_ts,
            end_ts,
            source,
        )

        if source == "binance":
            df = self.load_from_binance(
                symbol, interval, start_ts.to_pydatetime(), end_ts.to_pydatetime()
            )
        elif source == "synthetic":
            df = self._fetch_stub_data(symbol, interval, start_ts, end_ts)
        else:
            raise ValueError(f"Unsupported data source: {source}")

        logger.info("Loaded %s rows for %s via %s", len(df), symbol, source)

        if fmt == "csv":
            df.to_csv(file_path)
        else:
            df.to_parquet(file_path)

        logger.info("Persisted %s rows for %s to %s", len(df), symbol, file_path)
        return df

    def _fetch_stub_data(self, symbol: str, interval: str, start: datetime | str, end: datetime | str) -> pd.DataFrame:
        """Generate synthetic data for demonstration."""

        date_range = pd.date_range(start=start, end=end, freq=interval)
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

    def load_from_binance(
        self,
        symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """
        Load historical OHLCV data from Binance.

        Returns a DataFrame indexed by UTC timestamps with columns:
        ``['open', 'high', 'low', 'close', 'volume']``.
        """

        if SyncClient is None:
            logger.warning(
                "python-binance is required for Binance downloads; install python-binance to proceed."
            )
            raise RuntimeError("Binance client unavailable; install python-binance to enable downloads.")

        api_key = self._resolve_secret(self.binance_config.get("api_key"))
        api_secret = self._resolve_secret(self.binance_config.get("api_secret"))
        base_url = self.binance_config.get("base_url")
        use_testnet = bool(self.binance_config.get("use_testnet", False))

        if not api_key or not api_secret:
            logger.warning(
                "Binance API credentials are missing. Set BINANCE_API_KEY and BINANCE_API_SECRET or update configuration."
            )
            raise RuntimeError("Binance credentials are required to download historical data.")

        client = SyncClient(api_key=api_key, api_secret=api_secret, testnet=use_testnet)
        if base_url:
            client.API_URL = base_url

        start_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)

        logger.info("Requesting Binance klines for %s %s", symbol, interval)
        klines = client.get_historical_klines(symbol=symbol, interval=interval, start_str=start_ms, end_str=end_ms)
        time.sleep(0.2)

        if not klines:
            logger.warning("No data returned from Binance for %s", symbol)
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])  # pragma: no cover

        df = pd.DataFrame(
            klines,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base",
                "taker_buy_quote",
                "ignore",
            ],
        )

        df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        df = df.set_index("timestamp")
        numeric_cols = ["open", "high", "low", "close", "volume"]
        df[numeric_cols] = df[numeric_cols].astype(float)
        result = df[numeric_cols]
        logger.info("Loaded %s rows from Binance for %s", len(result), symbol)
        return result

    @staticmethod
    def _resolve_secret(value: str | None) -> str | None:
        """Resolve environment variable placeholders like ``${VAR}``."""

        if value and value.startswith("${") and value.endswith("}"):
            env_var = value.strip("${}")
            return os.getenv(env_var)
        return value
