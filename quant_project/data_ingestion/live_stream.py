"""Live data streaming utilities.

In production this module is where real-time market data (for example from
Binance) enters the system. The implementation supports both a synthetic
random-walk style generator for development and a Binance-backed stream for
live-paper style runs.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncIterator, Callable, Iterable, Optional

import numpy as np

from quant_project.core.types import Bar

logger = logging.getLogger(__name__)

try:
    from binance import AsyncClient
except ImportError:
    AsyncClient = None
    logger.warning("python-binance not installed; Binance streaming mode will be unavailable.")


class LiveStream:
    """Async iterator yielding live bars.

    The stream can be sourced from Binance (using a polling loop for closed
    klines) or fall back to the synthetic generator. In production this is the
    boundary where real-time market data enters the application.
    """

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        poll_interval: float,
        mode: str = "synthetic",
        binance_api_key: Optional[str] = None,
        binance_api_secret: Optional[str] = None,
        binance_base_url: Optional[str] = None,
        reconnect_delay: float = 5.0,
    ) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.poll_interval = poll_interval
        self.mode = mode.lower()
        self.binance_api_key = binance_api_key
        self.binance_api_secret = binance_api_secret
        self.binance_base_url = binance_base_url
        self.reconnect_delay = reconnect_delay

        if self.mode == "binance" and AsyncClient is None:
            logger.error(
                "python-binance is unavailable; falling back to synthetic streaming mode for %s.",
                self.symbol,
            )
            self.mode = "synthetic"

    async def __aiter__(self) -> AsyncIterator[Bar]:
        if self.mode == "binance":
            logger.info("Starting Binance streaming mode for %s on %s", self.symbol, self.timeframe)
            async for bar in self._binance_stream():
                yield bar
        else:
            if self.mode != "synthetic":
                logger.warning(
                    "Unknown streaming mode '%s' requested; defaulting to synthetic for %s.",
                    self.mode,
                    self.symbol,
                )
            async for bar in self._synthetic_stream():
                yield bar

    async def _synthetic_stream(self) -> AsyncIterator[Bar]:
        while True:
            bar = self._generate_bar()
            logger.debug("Generated synthetic live bar for %s at %s", self.symbol, bar.timestamp)
            yield bar
            await asyncio.sleep(self.poll_interval)

    async def _binance_stream(self) -> AsyncIterator[Bar]:
        if AsyncClient is None:
            logger.error(
                "Binance streaming requested but python-binance is unavailable; using synthetic mode for %s.",
                self.symbol,
            )
            async for bar in self._synthetic_stream():
                yield bar
            return

        client: AsyncClient | None = None
        last_close: Optional[int] = None
        fallback_to_synthetic = False

        try:
            client = await AsyncClient.create(
                api_key=self.binance_api_key,
                api_secret=self.binance_api_secret,
                base_url=self.binance_base_url,
            )
            logger.info("Connected to Binance for %s %s", self.symbol, self.timeframe)

            while True:
                klines: Iterable[list] = await client.get_klines(
                    symbol=self.symbol, interval=self.timeframe, limit=2
                )
                if not klines:
                    logger.debug("No klines returned for %s on %s", self.symbol, self.timeframe)
                    await asyncio.sleep(self.poll_interval)
                    continue

                latest = list(klines)[-1]
                close_time = int(latest[6])
                if last_close is None or close_time > last_close:
                    bar = self._kline_to_bar(latest)
                    last_close = close_time
                    yield bar

                await asyncio.sleep(self.poll_interval)
        except Exception:
            fallback_to_synthetic = True
            logger.exception(
                "Error while streaming from Binance; falling back to synthetic mode for %s.", self.symbol
            )
        finally:
            if client is not None:
                try:
                    await client.close_connection()
                except Exception:
                    logger.debug("Error closing Binance client during shutdown for %s", self.symbol, exc_info=True)

        if fallback_to_synthetic:
            async for bar in self._synthetic_stream():
                yield bar

    def _generate_bar(self) -> Bar:
        now = datetime.utcnow()
        price = 100 + np.random.randn()
        return Bar(
            timestamp=now,
            open=price - 0.1,
            high=price + 0.2,
            low=price - 0.3,
            close=price,
            volume=float(np.random.rand() * 5),
        )

    @staticmethod
    def _kline_to_bar(kline: list) -> Bar:
        close_time = int(kline[6])
        return Bar(
            timestamp=datetime.utcfromtimestamp(close_time / 1000),
            open=float(kline[1]),
            high=float(kline[2]),
            low=float(kline[3]),
            close=float(kline[4]),
            volume=float(kline[5]),
        )


async def run_stream(
    symbol: str,
    timeframe: str,
    poll_interval: float,
    callback: Callable[[Bar], Any],
    *,
    mode: str = "synthetic",
    binance_api_key: Optional[str] = None,
    binance_api_secret: Optional[str] = None,
    binance_base_url: Optional[str] = None,
) -> None:
    """Consume the live stream and invoke a callback for each bar.

    The function keeps the external interface simple: regardless of whether the
    source is synthetic or Binance, it pushes fully-formed :class:`Bar`
    instances into the supplied callback.
    """

    stream = LiveStream(
        symbol,
        timeframe,
        poll_interval,
        mode=mode,
        binance_api_key=binance_api_key,
        binance_api_secret=binance_api_secret,
        binance_base_url=binance_base_url,
    )
    async for bar in stream:
        result = callback(bar)
        if asyncio.iscoroutine(result):
            await result
