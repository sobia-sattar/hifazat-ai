"""Controlled validation-only preprocessing and imbalance comparison; never inspects test labels."""

import pandas as pd
import numpy as np
from src.models.baseline import Baseline
from src.preprocessing.text import preprocess
from src.evaluation.metrics import evaluate, optimize_thresholds
from src.utils.common import ROOT, LABELS


def main():
    frame = pd.read_csv(ROOT / "data/processed/research.csv")
    train, val = frame[frame.split == "train"], frame[frame.split == "validation"]
    results = []
    for roman, balanced in [(False, False), (False, True), (True, False), (True, True)]:
        x = train.raw_text.map(lambda text: preprocess(text, roman=roman))
        vx = val.raw_text.map(lambda text: preprocess(text, roman=roman))
        model = Baseline(balanced=balanced).fit(x, train[LABELS].values)
        scores = model.predict_proba(vx)
        thresholds = optimize_thresholds(val[LABELS].values, scores)
        for name, t in [("default", np.full(len(LABELS), 0.5)), ("optimized", thresholds)]:
            metrics = evaluate(val[LABELS].values, scores, t)
            results.append(
                dict(
                    roman_normalization=roman,
                    balanced=balanced,
                    thresholds=name,
                    validation_macro_f1=metrics["macro_f1"],
                    validation_weighted_f1=metrics["weighted_f1"],
                )
            )
    pd.DataFrame(results).to_csv(ROOT / "reports/ablations.csv", index=False)


if __name__ == "__main__":
    main()
