import argparse
from datetime import datetime, timezone
import json
import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import ParameterSampler
from src.models.baseline import Baseline
from src.evaluation.metrics import evaluate, optimize_thresholds, binary_metrics
from src.utils.common import ROOT, LABELS, digest, write_json


def main(profile="standard"):
    cfg = yaml.safe_load((ROOT / "configs/training.yaml").read_text())["profiles"][profile]
    frame = pd.read_csv(ROOT / "data/processed/research.csv")
    train = frame[frame.split == "train"]
    val = frame[frame.split == "validation"]
    dataset_version = digest(ROOT / "data/processed/research.csv")
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "experiments" / version
    folder.mkdir(parents=True)
    ytr = np.c_[train[LABELS].values, train.binary_harmful.values]
    yva = val[LABELS].values
    best, records = None, []
    grid = list(
        ParameterSampler(
            dict(C=[0.25, 1.0, 4.0], ngram=[1, 2, 3], balanced=[True, False]), n_iter=cfg["trials"], random_state=42
        )
    )
    for kind, algorithm in [("word", "lr"), ("word", "svm"), ("char", "svm"), ("hybrid", "lr"), ("hybrid", "svm")]:
        for trial, params in enumerate(grid):
            name = f"{kind}_{algorithm}_{trial}"
            print("Training", name, params, flush=True)
            model = Baseline(kind=kind, algorithm=algorithm, max_features=cfg["max_features"], **params)
            model.fit(train.processed_text, ytr)
            p = model.predict_proba(val.processed_text)
            threshold = optimize_thresholds(np.c_[yva, val.binary_harmful], p)
            metrics = evaluate(yva, p[:, :-1], threshold[:-1])
            binary = binary_metrics(val.binary_harmful.values, p[:, -1], threshold[-1])
            record = dict(
                experiment_id=version + "_" + name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                model=name,
                features=kind,
                dataset_version=dataset_version,
                train_size=len(train),
                parameters=json.dumps(model.parameters),
                validation_macro_f1=metrics["macro_f1"],
                validation_weighted_f1=metrics["weighted_f1"],
                binary_f1=binary["f1"],
                notes="Partial-label supervision; validation-only thresholds; full training split",
            )
            records.append(record)
            write_json(
                folder / (name + ".json"),
                dict(**record, validation_metrics=metrics, binary=binary, thresholds=threshold.tolist()),
            )
            if best is None or metrics["macro_f1"] > best["validation_metrics"]["macro_f1"]:
                best = dict(
                    model=model,
                    model_name=name,
                    labels=LABELS,
                    thresholds=threshold.tolist(),
                    version=version,
                    validation_metrics=metrics,
                    validation_binary=binary,
                    dataset_version=dataset_version,
                    train_size=len(train),
                    training_date=record["timestamp"],
                    hyperparameters=model.parameters,
                    preprocessing_version="conservative-v2",
                    profile=profile,
                )
                np.savez_compressed(
                    folder / "validation_predictions.npz", y=yva, p=p, record_id=val.record_id.to_numpy(dtype=str)
                )
            pd.DataFrame(records).to_csv(folder / "experiments.csv", index=False)
    artifacts = ROOT / "artifacts"
    (artifacts / "models").mkdir(parents=True, exist_ok=True)
    joblib.dump(best, artifacts / "models" / f"{version}.joblib")
    write_json(
        artifacts / "selected.json",
        dict(
            path=f"models/{version}.joblib", sha256=digest(artifacts / "models" / f"{version}.joblib"), version=version
        ),
    )
    write_json(artifacts / "thresholds.json", dict(zip(LABELS + ["BINARY_HARMFUL"], best["thresholds"])))
    write_json(artifacts / "metadata" / f"{version}.json", {k: v for k, v in best.items() if k != "model"})
    pd.DataFrame(records).to_csv(ROOT / "reports/model_comparison.csv", index=False)
    # Append across runs; retain every experiment instead of silently overwriting history.
    ledger = ROOT / "experiments/experiments.csv"
    pd.DataFrame(records).to_csv(ledger, index=False, mode="a", header=not ledger.exists())
    print("Selected", best["model_name"], best["validation_metrics"]["macro_f1"], flush=True)
    return best


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--profile", choices=["quick", "standard", "research"], default="standard")
    main(p.parse_args().profile)
