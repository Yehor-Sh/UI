"""Command line interface for the project."""
from __future__ import annotations

import argparse
import asyncio
import logging

from quant_project.core.utils import load_yaml
from quant_project.data_ingestion.historical_client import HistoricalDataClient
from quant_project.data_processing.pipelines import prepare_offline_features
from quant_project.labeling.triple_barrier import apply_triple_barrier
from quant_project.ml_models.training import train_meta_model, train_primary_model
from quant_project.ml_models.registry import ModelRegistry
from quant_project.monitoring.logging_config import setup_logging
from quant_project.simulation.backtester.engine import BacktestEngine
from quant_project.simulation.backtester.reports import basic_report
from quant_project.strategy_engine.prado_strategy import PradoStrategy

logger = logging.getLogger(__name__)


def run_backtest(config_path: str) -> None:
    config = load_yaml(config_path)
    setup_logging(config.get("logging", {}).get("level", "INFO"))
    data_cfg = config["data"]
    hist_client = HistoricalDataClient(config.get("paths", {}).get("data_dir", "./data"))
    df = hist_client.load(data_cfg["symbol"], data_cfg["timeframe"], data_cfg["start"], data_cfg["end"])
    features = prepare_offline_features(df["close"], {"sma_short": 12, "sma_long": 48}, d=config["features"]["fractional_diff_d"])
    labels = (features["returns"] > 0).astype(int)
    primary_model = train_primary_model(features, labels)
    meta_model = train_meta_model(features, labels)
    strategy = PradoStrategy(primary_model=primary_model, meta_model=meta_model)
    engine = BacktestEngine(strategy=strategy, initial_cash=10000)
    portfolio = engine.run(features)
    report = basic_report(portfolio.equity_curve)
    logger.info("Backtest report: %s", report)


def run_live_paper(config_path: str) -> None:
    config = load_yaml(config_path)
    setup_logging(config.get("logging", {}).get("level", "INFO"))
    # In a full implementation this would start asyncio loop and streaming
    logger.info("Live paper mode would start here with config %s", config)
    asyncio.get_event_loop().run_forever()


def run_train_model(config_path: str) -> None:
    config = load_yaml(config_path)
    setup_logging(config.get("logging", {}).get("level", "INFO"))
    data_cfg = config["data"]
    hist_client = HistoricalDataClient(config.get("paths", {}).get("data_dir", "./data"))
    df = hist_client.load(data_cfg["symbol"], data_cfg["timeframe"], data_cfg.get("start", "2022-01-01"), data_cfg.get("end", "2022-02-01"))
    features = prepare_offline_features(df["close"], {"sma_short": 12, "sma_long": 48}, d=config.get("features", {}).get("fractional_diff_d", 0.5))
    labels = (features["returns"] > 0).astype(int)
    primary_model = train_primary_model(features, labels)
    meta_model = train_meta_model(features, labels)
    registry = ModelRegistry(config.get("paths", {}).get("model_dir", "./models"))
    registry.save(primary_model, "primary")
    registry.save(meta_model, "meta")


def main() -> None:
    parser = argparse.ArgumentParser(description="Quant project CLI")
    parser.add_argument("command", choices=["backtest", "live-paper", "train-model"])
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    if args.command == "backtest":
        run_backtest(args.config)
    elif args.command == "live-paper":
        run_live_paper(args.config)
    elif args.command == "train-model":
        run_train_model(args.config)


if __name__ == "__main__":
    main()
