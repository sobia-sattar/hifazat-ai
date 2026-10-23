"""Compare full-validation transformer checkpoints to the selected baseline, never test results."""

from datetime import datetime, timezone
import json
import joblib
import pandas as pd
from src.inference.predict import Predictor
from src.models.transformer import TransformerModel
from src.utils.common import ROOT, LABELS, digest, write_json


def main():
    best = Predictor().bundle
    table = pd.read_csv(ROOT / "reports/model_comparison.csv")
    for path in sorted((ROOT / "artifacts/transformers").glob("*/validation.json")):
        candidate = json.loads(path.read_text())
        if candidate["dataset_version"] != best["dataset_version"]:
            continue
        args = candidate["arguments"]
        name = f"{args['model']}_{args['length']}"
        table = pd.concat(
            [
                table,
                pd.DataFrame(
                    [
                        dict(
                            model=name,
                            validation_macro_f1=candidate["metrics"]["macro_f1"],
                            validation_weighted_f1=candidate["metrics"]["weighted_f1"],
                            parameters=json.dumps(args),
                        )
                    ]
                ),
            ],
            ignore_index=True,
        )
        if candidate["metrics"]["macro_f1"] > best["validation_metrics"]["macro_f1"]:
            version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            best = {
                **best,
                "model": TransformerModel(path.parent / "best", args["length"]),
                "model_name": name,
                "version": version,
                "thresholds": candidate["thresholds"],
                "validation_metrics": candidate["metrics"],
                "validation_binary": candidate.get("binary"),
                "training_date": datetime.now(timezone.utc).isoformat(),
                "hyperparameters": args,
            }
            destination = ROOT / "artifacts/models" / f"{version}.joblib"
            joblib.dump(best, destination)
            write_json(
                ROOT / "artifacts/selected.json",
                dict(path=f"models/{version}.joblib", sha256=digest(destination), version=version),
            )
            write_json(ROOT / "artifacts/thresholds.json", dict(zip(LABELS + ["BINARY_HARMFUL"], best["thresholds"])))
            write_json(ROOT / "artifacts/metadata" / f"{version}.json", {k: v for k, v in best.items() if k != "model"})
    table.drop_duplicates(subset=["model"], keep="last").to_csv(ROOT / "reports/model_comparison.csv", index=False)
    print("Selected across available full-validation models:", best["model_name"])


if __name__ == "__main__":
    main()
