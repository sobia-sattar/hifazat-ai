"""Strict independent multilabel gold evaluation; no training or tuning."""

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from datasketch import MinHash, MinHashLSH
from src.data.prepare import key, shingles
from src.inference.predict import Predictor
from src.evaluation.metrics import evaluate, binary_metrics
from src.utils.common import ROOT, LABELS, write_json


def parse_labels(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("All annotation fields must be complete")
    labels = set(value.split("|"))
    if not labels.issubset(set(LABELS) | {"SAFE"}) or ("SAFE" in labels and len(labels) > 1):
        raise ValueError("Invalid annotation or SAFE/harmful conflict")
    return [int(label in labels) for label in LABELS]


def overlap_audit(internal, external):
    lsh = MinHashLSH(threshold=0.65, num_perm=64)
    sets = {}
    exact = set()
    for i, text in enumerate(internal):
        normalized = key(text)
        grams = shingles(normalized)
        exact.add(normalized)
        mh = MinHash(num_perm=64, seed=42)
        mh.update_batch([g.encode() for g in sorted(grams)])
        lsh.insert(str(i), mh)
        sets[str(i)] = grams
    overlaps = []
    for i, text in enumerate(external):
        normalized = key(text)
        grams = shingles(normalized)
        mh = MinHash(num_perm=64, seed=42)
        mh.update_batch([g.encode() for g in sorted(grams)])
        if normalized in exact or any(len(grams & sets[j]) / len(grams | sets[j]) >= 0.85 for j in lsh.query(mh)):
            overlaps.append(i)
    return overlaps


def main():
    path = ROOT / "data/external/gold.csv"
    if not path.exists():
        write_json(
            ROOT / "reports/external_evaluation.json",
            {"status": "NOT COMPLETED", "reason": "Independent human annotations unavailable"},
        )
        print("External evaluation NOT COMPLETED")
        return
    frame = pd.read_csv(path)
    required = {"text", "annotator_1", "annotator_2", "adjudicated_labels"}
    if not required.issubset(frame.columns) or frame.empty:
        raise ValueError("External annotation schema invalid")
    first = np.array([parse_labels(x) for x in frame.annotator_1])
    second = np.array([parse_labels(x) for x in frame.annotator_2])
    truth = np.array([parse_labels(x) for x in frame.adjudicated_labels])
    internal = pd.read_csv(ROOT / "data/processed/research.csv")
    overlaps = overlap_audit(internal.raw_text, frame.text)
    if overlaps:
        raise ValueError(f"External set overlaps internal corpus: {len(overlaps)} rows")
    predictor = Predictor()
    from src.preprocessing.text import preprocess

    p = predictor.bundle["model"].predict_proba(frame.text.map(preprocess))
    thresholds = np.array(predictor.bundle["thresholds"])
    agreement = {}
    for j, label in enumerate(LABELS):
        a, b = first[:, j], second[:, j]
        kappa = cohen_kappa_score(a, b) if len(np.unique(np.r_[a, b])) > 1 else None
        agreement[label] = dict(
            raw_agreement=float((a == b).mean()),
            cohen_kappa=float(kappa) if kappa is not None and np.isfinite(kappa) else None,
        )
    write_json(
        ROOT / "reports/external_evaluation.json",
        dict(
            status="COMPLETED",
            n=len(frame),
            agreement=agreement,
            raw_exact_agreement=float((first == second).all(axis=1).mean()),
            metrics=evaluate(truth, p[:, :-1], thresholds[:-1]),
            binary=binary_metrics(truth.max(axis=1), p[:, -1], thresholds[-1]),
        ),
    )


if __name__ == "__main__":
    main()
