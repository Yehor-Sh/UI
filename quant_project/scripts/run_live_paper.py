from quant_project.interfaces.cli import run_live_paper


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    run_live_paper(args.config)
