"""Command line interface for the project."""
from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import timedelta
from pathlib import Path

import pandas as pd

from quant_project.core.utils import load_yaml
from quant_project.data_ingestion.historical_client import HistoricalDataClient
from quant_project.data_processing.pipelines import prepare_offline_features
from quant_project.labeling.triple_barrier import apply_triple_barrier
from quant_project.ml_models.registry import ModelRegistry
from quant_project.ml_models.training import train_meta_model, train_primary_model
from quant_project.monitoring.logging_config import setup_logging
from quant_project.risk_management.manager import RiskManager
from quant_project.simulation.backtester.engine import BacktestEngine
from quant_project.simulation.backtester.reports import basic_report
from quant_project.simulation.live_paper.runner import run_live_paper as run_live_paper_async
from quant_project.strategy_engine.prado_strategy import PradoStrategy

logger = logging.getLogger(__name__)


def _load_settings() -> dict:
    settings_path = Path(__file__).resolve().parent.parent / "config" / "settings.yaml"
    return load_yaml(settings_path) if settings_path.exists() else {}


def _resolve_paths(config: dict) -> tuple[Path, Path]:
    settings = _load_settings()
    paths_cfg = {**settings.get("paths", {}), **config.get("paths", {})}
    data_dir = Path(paths_cfg.get("data_dir", "./data"))
    model_dir = Path(paths_cfg.get("model_dir", "./models"))
    return data_dir, model_dir


def _build_feature_config(features_cfg: dict) -> dict:
    feature_windows = {k: v for k, v in features_cfg.items() if k not in {"fractional_diff_d"}}
    if not feature_windows:
        feature_windows = {
            "sma_short": features_cfg.get("window_short", 12),
            "sma_long": features_cfg.get("window_long", 48),
        }
    return {k: v for k, v in feature_windows.items() if v is not None}


def _prepare_features(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    features_cfg = config.get("features", {})
    feature_matrix = prepare_offline_features(
        df["close"], _build_feature_config(features_cfg), d=features_cfg.get("fractional_diff_d", 0.5)
    )
    feature_matrix["close"] = df.loc[feature_matrix.index, "close"]
    return feature_matrix


def _build_labels(features: pd.DataFrame, prices: pd.Series, labeling_cfg: dict) -> pd.Series:
    events = features["returns"].apply(lambda r: 1 if r >= 0 else -1)
    pt_sl = tuple(labeling_cfg.get("pt_sl", (1.0, 1.0)))
    max_holding_hours = labeling_cfg.get("max_holding_hours", 24)
    labels_df = apply_triple_barrier(
        prices=prices,
        events=events,
        pt_sl=(float(pt_sl[0]), float(pt_sl[1])),
        max_holding=timedelta(hours=max_holding_hours),
    )
    aligned = labels_df.loc[features.index.intersection(labels_df.index)]
    return aligned["label"]


def run_train_model(config_path: str) -> None:
    logger.info("Starting training with config %s", config_path)
    config = load_yaml(config_path)
    logging_cfg = config.get("logging", {})
    setup_logging(logging_cfg.get("level", "INFO"), logging_cfg.get("file"))
    data_dir, model_dir = _resolve_paths(config)

    data_cfg = config.get("data", {})
    hist_client = HistoricalDataClient(data_dir, binance_config=config.get("binance", {}))
    df = hist_client.load(
        data_cfg["symbol"],
        data_cfg["interval"],
        data_cfg.get("start"),
        data_cfg.get("end"),
        source=data_cfg.get("source", "synthetic"),
        fmt=data_cfg.get("storage_format", "parquet"),
    )

    features = _prepare_features(df, config)
    labels = _build_labels(features, df["close"], config.get("labeling", {}))
    aligned_features = features.loc[labels.index]
    timestamps = aligned_features.index

    logger.info("Training primary model with %d samples", len(aligned_features))
    primary_model = train_primary_model(
        aligned_features,
        labels,
        timestamps=timestamps,
        n_splits=config.get("models", {}).get("cv_folds", 5),
        embargo_pct=config.get("risk", {}).get("embargo_hours", 0) / 24 if config.get("risk") else 0.01,
    )

    meta_labels = (labels != 0).astype(int)
    logger.info("Training meta model with %d samples", meta_labels.sum())
    meta_model = train_meta_model(
        aligned_features,
        meta_labels,
        timestamps=timestamps,
        n_splits=config.get("models", {}).get("cv_folds", 5),
        embargo_pct=config.get("risk", {}).get("embargo_hours", 0) / 24 if config.get("risk") else 0.01,
    )

    registry = ModelRegistry(model_dir)
    registry.save(primary_model, "primary")
    registry.save(meta_model, "meta")
    logger.info("Models saved to %s", model_dir)


def run_backtest(config_path: str) -> None:
    logger.info("Starting backtest with config %s", config_path)
    config = load_yaml(config_path)
    logging_cfg = config.get("logging", {})
    setup_logging(logging_cfg.get("level", "INFO"), logging_cfg.get("file"))
    data_dir, model_dir = _resolve_paths(config)

    data_cfg = config.get("data", {})
    hist_client = HistoricalDataClient(data_dir, binance_config=config.get("binance", {}))
    df = hist_client.load(
        data_cfg["symbol"],
        data_cfg["interval"],
        data_cfg.get("start"),
        data_cfg.get("end"),
        source=data_cfg.get("source", "synthetic"),
        fmt=data_cfg.get("storage_format", "parquet"),
    )

    features = _prepare_features(df, config)
    registry = ModelRegistry(model_dir)
    primary_model = registry.load("primary")
    meta_model = registry.load("meta")

    strategy = PradoStrategy(
        primary_model=primary_model,
        meta_model=meta_model,
        threshold=config.get("strategy", {}).get("meta_threshold", 0.5),
    )

    risk_manager = None
    if "risk" in config:
        risk_manager = RiskManager(**config["risk"])

    engine = BacktestEngine(
        strategy=strategy,
        initial_cash=config.get("portfolio", {}).get("initial_cash", 10000.0),
        risk_manager=risk_manager,
    )
    portfolio = engine.run(features)
    report = basic_report(portfolio.equity_curve)
    logger.info("Backtest report: %s", report)


def run_live_paper(config_path: str) -> None:
    logger.info("Starting live-paper with config %s", config_path)
    config = load_yaml(config_path)
    logging_cfg = config.get("logging", {})
    setup_logging(logging_cfg.get("level", "INFO"), logging_cfg.get("file"))
    _, model_dir = _resolve_paths(config)

    streaming_cfg = config.get("streaming", {}) or config.get("data", {})
    symbol = streaming_cfg.get("symbol")
    interval = streaming_cfg.get("interval") or streaming_cfg.get("timeframe")
    poll_interval = float(streaming_cfg.get("poll_interval", streaming_cfg.get("poll_interval_seconds", 5.0)))
    streaming_mode = streaming_cfg.get("mode", "synthetic")

    registry = ModelRegistry(model_dir)
    primary_model = registry.load("primary")
    meta_model = registry.load("meta")

    strategy = PradoStrategy(
        primary_model=primary_model,
        meta_model=meta_model,
        threshold=config.get("strategy", {}).get("meta_threshold", 0.5),
    )

    risk_manager = None
    risk_cfg = config.get("risk")
    if risk_cfg:
        risk_manager = RiskManager(**risk_cfg)

    binance_cfg = config.get("binance", {})
    asyncio.run(
        run_live_paper_async(
            strategy,
            symbol,
            interval,
            poll_interval,
            config.get("portfolio", {}).get("initial_cash", 10000.0),
            risk_manager=risk_manager,
            risk_config=risk_cfg,
            mode=streaming_mode,
            binance_config=binance_cfg,
        )
    )


def main() -> None:
    setup_logging()
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
