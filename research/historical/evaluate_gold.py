"""Evaluate the serving model on the manually adjudicated external gold set."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report, cohen_kappa_score, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.infer import _predict_sklearn, analyze_text, get_bundle  # noqa: E402
from app.ml.labels import HARMFUL_LABELS  # noqa: E402
from app.nlp.language import detect_language, preprocess_text  # noqa: E402
from app.nlp.roman_urdu import normalize_roman_urdu  # noqa: E402

GOLD = ROOT / "data" / "gold" / "gold_annotations.csv"


def main() -> None:
    df = pd.read_csv(GOLD).fillna("")
    if df.empty or not df["adjudicated_label"].astype(str).str.strip().any():
        raise SystemExit("Fill adjudicated_label in data/gold/gold_annotations.csv before evaluation.")
    df = df[df["adjudicated_label"].astype(str).str.strip() != ""].copy()
    annotator_rows = df[
        (df["annotator_1"].astype(str).str.strip() != "")
        & (df["annotator_2"].astype(str).str.strip() != "")
    ]
    if not annotator_rows.empty:
        print("annotator_cohen_kappa", cohen_kappa_score(annotator_rows["annotator_1"], annotator_rows["annotator_2"]))
    bundle = get_bundle()
    if bundle is None:
        raise SystemExit("Trained model missing. Run research/train.py before evaluation.")

    model_predictions = []
    production_predictions = []
    for text in df["text"]:
        result = analyze_text(text, include_xai=False)
        production_predictions.append(result.get("primary_category") or result["classification"])
        cleaned = preprocess_text(text)
        lang = detect_language(cleaned)
        normalized = normalize_roman_urdu(cleaned) if lang.script in {"latin", "mixed"} else cleaned
        scores, _ = _predict_sklearn(normalized, bundle["sklearn"])
        harmful = max((scores.get(label, 0.0) for label in HARMFUL_LABELS), default=0.0)
        safe = scores.get("SAFE", 0.0)
        model_predictions.append("SAFE" if safe >= harmful else max(HARMFUL_LABELS, key=lambda label: scores.get(label, 0.0)))
    truth = df["adjudicated_label"].tolist()
    labels = sorted(set(truth) | set(model_predictions) | set(production_predictions))
    for name, predictions in (("model_only", model_predictions), ("production_model_plus_rules", production_predictions)):
        print(name)
        print(classification_report(truth, predictions, labels=labels, zero_division=0))
        print("macro_f1", f1_score(truth, predictions, labels=labels, average="macro", zero_division=0))
        print("confusion_matrix")
        print(confusion_matrix(truth, predictions, labels=labels))
    print("labels", labels)


if __name__ == "__main__":
    main()
