"""Simple data storage abstraction."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from quant_project.core.utils import ensure_directory


class DataStorage:
    """Handles saving/loading data for reproducibility."""

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = ensure_directory(base_dir)

    def save(self, df: pd.DataFrame, name: str, fmt: Literal["csv", "parquet"] = "parquet") -> Path:
        path = self.base_dir / f"{name}.{fmt}"
        if fmt == "csv":
            df.to_csv(path)
        else:
            df.to_parquet(path)
        return path

    def load(self, name: str, fmt: Literal["csv", "parquet"] = "parquet") -> pd.DataFrame:
        path = self.base_dir / f"{name}.{fmt}"
        if fmt == "csv":
            return pd.read_csv(path, index_col="timestamp", parse_dates=["timestamp"])
        return pd.read_parquet(path)
