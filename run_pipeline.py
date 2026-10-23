"""One command runs licensed data preparation, baselines, frozen evaluation and figures."""

import argparse
import importlib.metadata
import platform
import subprocess
import sys
import torch
from src.utils.common import ROOT, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["quick", "standard", "research"], default="standard")
    parser.add_argument("--skip-prepare", action="store_true")
    parser.add_argument(
        "--reuse-trained", action="store_true", help="Reuse an existing artifact; evaluation verifies the dataset hash"
    )
    args = parser.parse_args()
    env = dict(
        python=sys.version,
        platform=platform.platform(),
        packages={d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
        cuda=torch.version.cuda,
        gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        seed=42,
    )
    write_json(ROOT / "environment_report.json", env)
    commands = []
    if not args.skip_prepare:
        commands.append(["src.data.prepare"])
    if not args.reuse_trained:
        commands.append(["src.training.train_baselines", "--profile", args.profile])
    if torch.cuda.is_available() and not args.reuse_trained:
        for model in ["xlm-roberta-base", "bert-base-multilingual-cased"]:
            commands.append(["src.training.train_transformer", "--model", model])
    commands.extend(
        [
            ["src.training.select_model"],
            ["src.evaluation.evaluate"],
            ["src.evaluation.external"],
            ["src.visualization.generate_figures"],
        ]
    )
    for command in commands:
        subprocess.run([sys.executable, "-m", *command], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
