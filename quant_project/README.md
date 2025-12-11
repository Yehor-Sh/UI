# Quant Project

This repository implements a López de Prado–inspired quantitative research and trading system targeting Binance markets. The project emphasizes robust research practices for non-stationary financial data, with clear separation between research (backtesting) and production-like (live paper) workflows.

## Key Principles
- **Non-stationary data**: incorporate fractional differencing to retain memory while achieving stationarity.
- **Robust labeling**: use triple-barrier labeling to define event outcomes and meta-labeling to filter false positives.
- **Anti-overfitting**: purged and embargoed cross-validation; avoid naive backtests.
- **Separation of concerns**: shared core types/utilities, distinct pipelines for backtest vs. live paper, and pluggable execution.

## Components
- **Data ingestion**: historical loading and live streaming from Binance.
- **Data processing**: feature engineering, fractional differencing, and pipelines.
- **Labeling**: triple-barrier labeling and meta-labeling utilities.
- **Models**: training, validation (purged K-fold), and model registry.
- **Strategies**: Prado-style strategy combining primary signals with meta-model decisions.
- **Simulation**: backtester and live-paper runner with virtual broker.
- **Execution & Risk**: exchange abstraction, order management, and risk rules.
- **Monitoring**: logging, metrics, and alert hooks.

## Getting Started
1. Install dependencies: `pip install -e .`
2. Configure YAML files in `config/` and set environment variables for secrets (API keys).
3. Run a backtest:
   ```bash
   python -m quant_project.scripts.run_backtest --config config/backtest.yaml
   ```
4. Run live paper trading:
   ```bash
   python -m quant_project.scripts.run_live_paper --config config/live_paper.yaml
   ```

## Disclaimer
This code is for educational and research purposes. Live trading requires additional hardening, monitoring, and risk controls.
