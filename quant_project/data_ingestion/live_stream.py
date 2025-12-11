"""Live data streaming utilities.

For Binance this would typically use WebSockets. Here we present a minimal
polling-based implementation for readability, but the interface leaves room for
real streaming integrations.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import AsyncIterator, Callable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class LiveStream:
    """Async iterator yielding simulated live bars."""

    def __init__(self, symbol: str, timeframe: str, poll_interval: float) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.poll_interval = poll_interval

    async def __aiter__(self) -> AsyncIterator[pd.Series]:
        while True:
            bar = self._generate_bar()
            logger.debug("Generated live bar for %s at %s", self.symbol, bar.name)
            yield bar
            await asyncio.sleep(self.poll_interval)

    def _generate_bar(self) -> pd.Series:
        now = datetime.utcnow()
        price = 100 + np.random.randn()
        bar = pd.Series(
            {
                "open": price - 0.1,
                "high": price + 0.2,
                "low": price - 0.3,
                "close": price,
                "volume": np.random.rand() * 5,
            }
        )
        bar.name = now
        return bar


async def run_stream(symbol: str, timeframe: str, poll_interval: float, callback: Callable[[pd.Series], None]) -> None:
    """Consume the live stream and invoke a callback for each bar."""

    stream = LiveStream(symbol, timeframe, poll_interval)
    async for bar in stream:
        callback(bar)
