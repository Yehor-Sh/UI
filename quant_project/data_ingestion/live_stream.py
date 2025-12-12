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
from typing import AsyncIterator, Callable, Iterable, Optional

import numpy as np
from binance import AsyncClient

from quant_project.core.types import Bar

logger = logging.getLogger(__name__)


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
        self.mode = mode
        self.binance_api_key = binance_api_key
        self.binance_api_secret = binance_api_secret
        self.binance_base_url = binance_base_url
        self.reconnect_delay = reconnect_delay

    async def __aiter__(self) -> AsyncIterator[Bar]:
        if self.mode.lower() == "binance":
            async for bar in self._binance_stream():
                yield bar
        else:
            async for bar in self._synthetic_stream():
                yield bar

    async def _synthetic_stream(self) -> AsyncIterator[Bar]:
        while True:
            bar = self._generate_bar()
            logger.debug("Generated synthetic live bar for %s at %s", self.symbol, bar.timestamp)
            yield bar
            await asyncio.sleep(self.poll_interval)

    async def _binance_stream(self) -> AsyncIterator[Bar]:
        client: AsyncClient | None = None
        last_close: Optional[int] = None
        while True:
            try:
                if client is None:
                    client = await AsyncClient.create(
                        api_key=self.binance_api_key,
                        api_secret=self.binance_api_secret,
                        base_url=self.binance_base_url,
                    )
                    logger.info("Connected to Binance for %s %s", self.symbol, self.timeframe)

                klines: Iterable[list] = await client.get_klines(symbol=self.symbol, interval=self.timeframe, limit=2)
                new_bars = []
                for kline in klines:
                    close_time = int(kline[6])
                    if last_close is None or close_time > last_close:
                        bar = self._kline_to_bar(kline)
                        new_bars.append(bar)
                        last_close = close_time if last_close is None else max(last_close, close_time)

                for bar in sorted(new_bars, key=lambda b: b.timestamp):
                    yield bar

                await asyncio.sleep(self.poll_interval)
            except Exception:
                logger.exception("Error while streaming from Binance; reconnecting after %.1fs", self.reconnect_delay)
                if client is not None:
                    try:
                        await client.close_connection()
                    except Exception:
                        logger.debug("Error closing Binance client during reconnect", exc_info=True)
                    client = None
                await asyncio.sleep(self.reconnect_delay)

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
    callback: Callable[[Bar], None],
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
