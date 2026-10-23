"""Figures read saved outputs only; unavailable experiments are explicitly marked."""

import json
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_curve
from sklearn.calibration import calibration_curve
from src.utils.common import ROOT, LABELS


def main():
    out = ROOT / "reports/figures"
    out.mkdir(parents=True, exist_ok=True)
    stats = json.loads((ROOT / "reports/dataset_statistics.json").read_text())
    metrics = json.loads((ROOT / "reports/final_metrics.json").read_text())
    predictions = np.load(ROOT / "reports/test_predictions.npz")
    y, p = predictions["y"], predictions["p"]
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none", "figure.dpi": 120})

    def save(number, title, draw):
        fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
        ax.set_title(title)
        draw(ax)
        for ext in ["png", "svg"]:
            fig.savefig(out / f"{number:02d}.{ext}", dpi=220)
        plt.close(fig)

    def diagram(ax, lines):
        ax.axis("off")
        for i, line in enumerate(lines):
            ax.text(
                0.5,
                0.88 - i * 0.19,
                line,
                ha="center",
                va="center",
                transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=.6", fc="#e5eff8", ec="#285f87"),
            )
            if i < len(lines) - 1:
                ax.annotate(
                    "",
                    xy=(0.5, 0.77 - i * 0.19),
                    xytext=(0.5, 0.83 - i * 0.19),
                    xycoords="axes fraction",
                    arrowprops=dict(arrowstyle="->"),
                )

    save(
        1,
        "System architecture",
        lambda ax: diagram(
            ax,
            [
                "Licensed sources → normalization + deduplication",
                "Train / validation / frozen test",
                "Sparse heads / optional multilingual transformer",
                "Frozen artifacts → FastAPI → research UI",
            ],
        ),
    )
    save(
        2,
        "Dataset construction",
        lambda ax: diagram(
            ax,
            [
                "License + explicit schema gate",
                "Unknown labels retained as -1",
                "Conflict quarantine + MinHash candidates",
                "Iterative multilabel split + audit",
            ],
        ),
    )
    save(
        3,
        "Conservative label mapping",
        lambda ax: diagram(
            ax,
            [
                "Davidson hate → HATE_SPEECH + TOXIC",
                "Davidson offensive → TOXIC; hate negative",
                "Roman Urdu toxic → TOXIC only",
                "Unannotated subtypes → UNKNOWN",
            ],
        ),
    )
    for number, title, field in [
        (4, "Heuristic language distribution", "by_language"),
        (5, "Positive annotation distribution", "positive_counts"),
        (6, "Dataset source distribution", "by_source"),
    ]:
        values = stats[field]
        save(number, title, lambda ax, v=values: (ax.barh(list(v), list(v.values())), ax.set_xlabel("Records")))
    comparison = pd.read_csv(ROOT / "reports/model_comparison.csv")
    save(
        7,
        "Validation observed-label Macro-F1",
        lambda ax: (ax.barh(comparison.model, comparison.validation_macro_f1), ax.set_xlim(0, 1)),
    )
    cm = np.array(metrics["binary"]["confusion_matrix"])

    def confusion(ax):
        ax.imshow(cm, cmap="Blues")
        for (i, j), n in np.ndenumerate(cm):
            ax.text(j, i, str(n), ha="center", va="center")
        ax.set(
            xticks=[0, 1],
            yticks=[0, 1],
            xticklabels=["SAFE", "HARMFUL"],
            yticklabels=["SAFE", "HARMFUL"],
            xlabel="Predicted",
            ylabel="Actual",
        )

    save(8, "Binary confusion matrix", confusion)
    names = ["accuracy", "precision", "recall", "f1"]
    save(
        9,
        "Binary test performance",
        lambda ax: (ax.bar(names, [metrics["binary"][k] for k in names]), ax.set_ylim(0, 1)),
    )
    pc = pd.read_csv(ROOT / "reports/per_class_metrics.csv").set_index("label")
    save(
        10,
        "Per-class test metrics (unknown labels masked)",
        lambda ax: pc[["precision", "recall", "f1"]].plot.barh(ax=ax),
    )
    lang = pd.read_csv(ROOT / "reports/language_metrics.csv").set_index("group")
    save(11, "Performance by heuristic language", lambda ax: lang[["macro_f1", "binary_f1"]].plot.barh(ax=ax))
    save(
        12,
        "Class imbalance: annotation support (not causal impact)",
        lambda ax: (ax.barh(pc.index, pc.support), ax.set_xlabel("Positive test annotations")),
    )
    thresholds = pd.read_csv(ROOT / "reports/thresholds.csv")
    save(
        13,
        "Validation-selected thresholds (>1 disables unsupported labels)",
        lambda ax: (ax.barh(thresholds.label, thresholds.threshold), ax.axvline(0.5, color="gray", ls="--")),
    )

    def curves(ax, roc=False):
        for j, label in enumerate(LABELS):
            mask = y[:, j] >= 0
            if len(np.unique(y[mask, j])) < 2:
                continue
            if roc:
                a, b, _ = roc_curve(y[mask, j], p[mask, j])
            else:
                b, a, _ = precision_recall_curve(y[mask, j], p[mask, j])
            ax.plot(a, b, label=label)
        ax.legend()
        ax.set(xlabel="False-positive rate" if roc else "Recall", ylabel="True-positive rate" if roc else "Precision")

    save(14, "Precision-recall curves", curves)
    save(15, "ROC curves", lambda ax: curves(ax, True))
    histories = list((ROOT / "artifacts/transformers").glob("*/history.json"))

    def transformer_curves(ax):
        if not histories:
            diagram(ax, ["NOT COMPLETED — CPU baseline run", "No transformer learning curve is claimed"])
        else:
            for path in histories:
                rows = json.loads(path.read_text())
                ax.plot([r["epoch"] for r in rows], [r["validation_macro_f1"] for r in rows], label=path.parent.name)
            ax.set(xlabel="Epoch", ylabel="Validation Macro-F1")
            ax.legend()

    save(16, "Transformer training", transformer_curves)
    errors = pd.read_csv(ROOT / "reports/error_analysis.csv")
    save(
        17,
        "Known-label error counts",
        lambda ax: errors.groupby(["label", "error"]).size().unstack(fill_value=0).plot.barh(ax=ax),
    )

    def support(ax):
        valid = pc[pc.evaluable]
        ax.scatter(valid.support, valid.f1)
        for label, row in valid.iterrows():
            ax.annotate(
                label,
                (row.support, row.f1),
                xytext=(-5, 6) if row.support == valid.support.max() else (5, 6),
                textcoords="offset points",
                ha="right" if row.support == valid.support.max() else "left",
            )
        ax.set(xlabel="Positive test support", ylabel="F1", ylim=(0, 1))

    save(18, "Positive annotation support versus F1", support)

    def reliability(ax):
        fraction, mean = calibration_curve(predictions["binary_y"], p[:, -1], n_bins=10)
        ax.plot(mean, fraction, marker="o", label="Binary head")
        ax.plot([0, 1], [0, 1], ls="--", color="gray")
        ax.set(xlabel="Mean predicted probability", ylabel="Observed harmful fraction")
        ax.legend()

    save(19, "Binary reliability diagram", reliability)
    ablation = ROOT / "reports/ablations.csv"
    if ablation.exists():
        rows = pd.read_csv(ablation)
        rows["condition"] = rows.apply(
            lambda row: f"Roman={row.roman_normalization}, weighted={row.balanced}, {row.thresholds}", axis=1
        )
        save(20, "Controlled validation ablations", lambda ax: ax.barh(rows.condition, rows.validation_macro_f1))


if __name__ == "__main__":
    main()
