import argparse

from quant_project.interfaces.cli import run_backtest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a backtest")
    parser.add_argument("--config", default="config/backtest.yaml")
    args = parser.parse_args()
    run_backtest(args.config)


if __name__ == "__main__":
    main()
