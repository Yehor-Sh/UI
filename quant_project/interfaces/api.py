"""FastAPI app skeleton."""
from __future__ import annotations

import logging
from fastapi import FastAPI

from quant_project.monitoring.logging_config import setup_logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Quant Project API", version="0.1.0")


@app.on_event("startup")
async def startup_event() -> None:
    setup_logging()
    logger.info("API started")


@app.get("/status")
async def status() -> dict[str, str]:
    return {"status": "ok"}
