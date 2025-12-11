"""Logging configuration."""
from __future__ import annotations

import logging
from logging.config import dictConfig


def setup_logging(level: str = "INFO", filename: str | None = None) -> None:
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": level,
        }
    }
    if filename:
        handlers["file"] = {
            "class": "logging.FileHandler",
            "formatter": "standard",
            "filename": filename,
            "level": level,
        }
    config = {
        "version": 1,
        "formatters": {"standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"}},
        "handlers": handlers,
        "root": {"handlers": list(handlers.keys()), "level": level},
    }
    dictConfig(config)
