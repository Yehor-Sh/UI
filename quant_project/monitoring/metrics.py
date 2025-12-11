"""Runtime metrics collection helpers."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List


class MetricsCollector:
    """Simple in-memory metrics collector."""

    def __init__(self) -> None:
        self.series: Dict[str, List[float]] = defaultdict(list)

    def record(self, name: str, value: float) -> None:
        self.series[name].append(value)

    def get(self, name: str) -> List[float]:
        return self.series.get(name, [])
