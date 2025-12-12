import argparse

from quant_project.interfaces.cli import run_train_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Train trading models")
    parser.add_argument("--config", default="config/backtest.yaml")
    args = parser.parse_args()
    run_train_model(args.config)


if __name__ == "__main__":
    main()
