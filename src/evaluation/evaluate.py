import json
import numpy as np
import pandas as pd
import yaml
from src.inference.predict import Predictor
from src.evaluation.metrics import evaluate, binary_metrics, bootstrap
from src.utils.common import ROOT, LABELS, digest, write_json


def main():
    predictor = Predictor()
    bundle = predictor.bundle
    source = ROOT / "data/processed/research.csv"
    if digest(source) != bundle["dataset_version"]:
        raise ValueError("Dataset differs from fitted model")
    folder = ROOT / "reports/metrics" / bundle["version"]
    folder.mkdir(parents=True, exist_ok=True)
    # Cache frozen test evaluation; rerunning reports does not fit or retune anything.
    cached = folder / "final_metrics.json"
    frame = pd.read_csv(source)
    test = frame[frame.split == "test"].reset_index(drop=True)
    y = test[LABELS].values
    if cached.exists():
        frozen = np.load(folder / "test_predictions.npz")
        if not np.array_equal(frozen["record_id"], test.record_id.to_numpy(dtype=str)):
            raise ValueError("Frozen test record IDs changed")
        p = frozen["p"]
        print("Reusing frozen test predictions; regenerating reports", flush=True)
    else:
        p = bundle["model"].predict_proba(test.processed_text)
    thresholds = np.asarray(bundle["thresholds"])
    metrics = evaluate(y, p[:, :-1], thresholds[:-1])
    binary = binary_metrics(test.binary_harmful.values, p[:, -1], thresholds[-1])
    cfg = yaml.safe_load((ROOT / "configs/training.yaml").read_text())["profiles"][bundle["profile"]]
    ci = (
        json.loads(cached.read_text())["confidence_interval"]
        if cached.exists()
        else bootstrap(y, p[:, :-1], thresholds[:-1], cfg["bootstrap"])
    )
    payload = dict(
        model_name=bundle["model_name"],
        version=bundle["version"],
        dataset_version=bundle["dataset_version"],
        validation=bundle["validation_metrics"],
        test=metrics,
        binary=binary,
        confidence_interval=ci,
        external_evaluation="NOT COMPLETED",
        transformer="See versioned transformer validation records"
        if list((ROOT / "artifacts/transformers").glob("*/validation.json"))
        else "NOT TRAINED in this baseline run",
    )
    np.savez_compressed(
        folder / "test_predictions.npz",
        y=y,
        p=p,
        thresholds=thresholds,
        binary_y=test.binary_harmful.values,
        record_id=test.record_id.to_numpy(dtype=str),
    )
    np.savez_compressed(
        ROOT / "reports/test_predictions.npz", y=y, p=p, thresholds=thresholds, binary_y=test.binary_harmful.values
    )
    per_class = pd.DataFrame(metrics["per_class"]).T.rename_axis("label").reset_index()
    per_class.to_csv(ROOT / "reports/per_class_metrics.csv", index=False)
    for column, filename in [("language", "language_metrics.csv"), ("source", "source_performance.csv")]:
        records = []
        for name, group in test.groupby(column):
            idx = group.index.to_numpy()
            m = evaluate(y[idx], p[idx, :-1], thresholds[:-1])
            b = binary_metrics(group.binary_harmful.values, p[idx, -1], thresholds[-1])
            records.append(
                dict(
                    group=name,
                    n=len(group),
                    macro_f1=m["macro_f1"],
                    weighted_f1=m["weighted_f1"],
                    binary_f1=b["f1"],
                    accuracy=b["accuracy"],
                    precision=b["precision"],
                    recall=b["recall"],
                    warning="Small support: interpret cautiously" if len(group) < 100 else "",
                    selection_labels="|".join(m["selection_labels"]),
                )
            )
        pd.DataFrame(records).to_csv(ROOT / "reports" / filename, index=False)
    predicted = p[:, :-1] >= thresholds[:-1]
    errors = []
    for j, label in enumerate(LABELS):
        ids = np.flatnonzero((y[:, j] >= 0) & (predicted[:, j] != y[:, j]))
        for i in ids:
            errors.append(
                dict(
                    record_id=test.record_id[i],
                    language=test.language[i],
                    source=test.source[i],
                    label=label,
                    error="false_positive" if predicted[i, j] else "false_negative",
                    probability=float(p[i, j]),
                    threshold=float(thresholds[j]),
                    high_confidence_wrong=bool(p[i, j] > 0.9 or p[i, j] < 0.1),
                )
            )
    # Raw harmful examples deliberately stay in local data, joined by record_id when needed.
    pd.DataFrame(
        errors,
        columns=[
            "record_id",
            "language",
            "source",
            "label",
            "error",
            "probability",
            "threshold",
            "high_confidence_wrong",
        ],
    ).to_csv(ROOT / "reports/error_analysis.csv", index=False)
    pd.DataFrame(dict(label=LABELS + ["BINARY_HARMFUL"], threshold=thresholds)).to_csv(
        ROOT / "reports/thresholds.csv", index=False
    )
    identities = ["Muslim", "Christian", "Hindu", "Pakistani", "Indian", "woman", "man", "Punjabi", "Pashtun"]
    probes = [f"My friend is {identity}." for identity in identities]
    outputs = predictor.predict(probes)
    text = "# Neutral identity probe audit\n\nSmall constructed diagnostic, not a fairness benchmark.\n\n"
    text += "| Identity | Binary result | Harmful probability |\n|---|---|---|\n"
    text += "\n".join(
        f"| {identity} | {row['binary_prediction']} | {row['harmful_probability']:.4f} |"
        for identity, row in zip(identities, outputs)
    )
    (ROOT / "reports/bias_audit.md").write_text(text, encoding="utf-8")
    write_json(cached, payload)
    write_json(ROOT / "reports/final_metrics.json", payload)
    metadata = {k: v for k, v in bundle.items() if k != "model"}
    metadata["test_metrics"] = metrics
    metadata["binary_test_metrics"] = binary
    write_json(ROOT / "artifacts/metadata" / f"{bundle['version']}.json", metadata)
    summary = f"# Experiment summary\n\nModel: {bundle['model_name']}\n\nDataset version: {bundle['dataset_version']}\n\nFull training rows: {bundle['train_size']}\n\nValidation observed-label Macro-F1: {bundle['validation_metrics']['macro_f1']:.4f}\n\nTest observed-label Macro-F1: {metrics['macro_f1']:.4f}\n\nBinary test F1: {binary['f1']:.4f}\n\nEvaluable labels: {', '.join(metrics['selection_labels'])}. Missing categories are not validated.\n\nUnknown source annotations are masked. SAFE is the absence of predicted harmful categories; the independently trained binary head may disagree and that disagreement is reported.\n\nNo external gold evaluation or transformer result is claimed. Urdu-script source excluded pending license verification. Heuristic language detection is not validated. Historical nine-label scores are not directly comparable.\n"
    (ROOT / "reports/EXPERIMENT_SUMMARY.md").write_text(summary, encoding="utf-8")
    print(summary, flush=True)


if __name__ == "__main__":
    main()
