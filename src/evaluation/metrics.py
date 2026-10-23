import numpy as np
from sklearn.metrics import (
    precision_recall_fscore_support,
    f1_score,
    accuracy_score,
    average_precision_score,
    roc_auc_score,
    confusion_matrix,
    brier_score_loss,
)
from src.utils.common import LABELS


def optimize_thresholds(y, p):
    thresholds = []
    for j in range(y.shape[1]):
        known = y[:, j] >= 0
        truth, scores = y[known, j], p[known, j]
        if not len(truth) or not np.any(truth == 1):
            thresholds.append(1.01)  # Disable unsupported heads; never manufacture positives.
            continue
        grid = np.linspace(0.05, 0.95, 37)
        scores_f1 = [f1_score(truth, scores >= t, zero_division=0) for t in grid]
        best = np.flatnonzero(np.isclose(scores_f1, max(scores_f1)))
        thresholds.append(float(grid[best[np.argmin(abs(grid[best] - 0.5))]]))
    return np.asarray(thresholds)


def evaluate(y, p, thresholds):
    pred = p >= thresholds
    per_class, supported = {}, []
    for j, label in enumerate(LABELS):
        known = y[:, j] >= 0
        truth = y[known, j]
        support = int((truth == 1).sum())
        row = dict(known=int(known.sum()), support=support, evaluable=bool(support and (truth == 0).any()))
        if len(truth):
            precision, recall, f1, _ = precision_recall_fscore_support(
                truth, pred[known, j], average="binary", zero_division=0
            )
            row.update(
                precision=float(precision),
                recall=float(recall),
                f1=float(f1),
                pr_auc=float(average_precision_score(truth, p[known, j])) if support else None,
                roc_auc=float(roc_auc_score(truth, p[known, j])) if len(np.unique(truth)) == 2 else None,
                brier=float(brier_score_loss(truth, p[known, j])),
            )
        else:
            row.update(precision=None, recall=None, f1=None, pr_auc=None, roc_auc=None, brier=None)
        if row["evaluable"]:
            supported.append(row)
        per_class[label] = row
    known = y >= 0
    complete = known.all(axis=1)
    micro = f1_score(y[known], pred[known], zero_division=0) if known.any() else None
    weights = np.array([r["support"] for r in supported])
    return dict(
        macro_f1=float(np.mean([r["f1"] for r in supported])) if supported else None,
        macro_precision=float(np.mean([r["precision"] for r in supported])) if supported else None,
        macro_recall=float(np.mean([r["recall"] for r in supported])) if supported else None,
        weighted_f1=float(np.average([r["f1"] for r in supported], weights=weights)) if len(weights) else None,
        micro_f1=float(micro) if micro is not None else None,
        hamming_loss=float((pred[known] != y[known]).mean()) if known.any() else None,
        subset_accuracy=float((pred[complete] == y[complete]).all(axis=1).mean()) if complete.any() else None,
        fully_observed_rows=int(complete.sum()),
        per_class=per_class,
        n=len(y),
        selection_labels=[k for k, r in per_class.items() if r["evaluable"]],
        note="Macro metrics cover labels with positive and negative annotations; unknown cells excluded. Not comparable to historical nine-label Macro-F1.",
    )


def binary_metrics(y, p, threshold):
    pred = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    pr, re, f1, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    return dict(
        accuracy=float(accuracy_score(y, pred)),
        precision=float(pr),
        recall=float(re),
        f1=float(f1),
        roc_auc=float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
        pr_auc=float(average_precision_score(y, p)) if np.any(y) else None,
        specificity=float(tn / (tn + fp)) if tn + fp else None,
        false_positive_rate=float(fp / (tn + fp)) if tn + fp else None,
        false_negative_rate=float(fn / (fn + tp)) if fn + tp else None,
        brier=float(brier_score_loss(y, p)),
        confusion_matrix=[[int(tn), int(fp)], [int(fn), int(tp)]],
        n=len(y),
    )


def bootstrap(y, p, thresholds, n=200):
    rng = np.random.default_rng(42)
    values = []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        score = evaluate(y[idx], p[idx], thresholds)["macro_f1"]
        if score is not None:
            values.append(score)
    return (
        dict(
            metric="observed-label macro_f1",
            resamples=n,
            seed=42,
            lower=float(np.quantile(values, 0.025)),
            upper=float(np.quantile(values, 0.975)),
            note="Row bootstrap conditional on the fitted model and this split; not a significance test.",
        )
        if values
        else None
    )
