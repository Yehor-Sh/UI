"""Live paper state classes."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from quant_project.core.types import PortfolioState, Trade


@dataclass
class LiveSessionState:
    """Tracks live paper session state."""

    start_time: datetime
    portfolio: PortfolioState
    trades: list[Trade] = field(default_factory=list)
    metrics: pd.DataFrame | None = None
