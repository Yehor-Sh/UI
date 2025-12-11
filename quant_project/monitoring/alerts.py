"""Alerting skeletons."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def send_alert(message: str) -> None:
    """Stub for sending alerts to messaging platforms."""

    logger.warning("ALERT: %s", message)
