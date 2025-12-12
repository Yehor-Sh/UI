import argparse

from quant_project.interfaces.cli import run_live_paper


def main() -> None:
    parser = argparse.ArgumentParser(description="Run live paper trading")
    parser.add_argument("--config", default="config/live_paper.yaml")
    args = parser.parse_args()
    run_live_paper(args.config)


if __name__ == "__main__":
    main()
