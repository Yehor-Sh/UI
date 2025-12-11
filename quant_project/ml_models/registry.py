"""Model registry for saving/loading models with versioning."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import joblib

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Simple versioned model registry."""

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str, version: Optional[str]) -> Path:
        suffix = f"_{version}" if version else ""
        return self.base_dir / f"{name}{suffix}.pkl"

    def save(self, model, name: str, version: Optional[str] = None) -> Path:
        path = self._path(name, version)
        joblib.dump(model, path)
        logger.info("Saved model %s", path)
        return path

    def load(self, name: str, version: Optional[str] = None):
        path = self._path(name, version)
        logger.info("Loading model %s", path)
        return joblib.load(path)
