"""Assemble a status report from saved evidence; never invent results."""

import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    stats = json.loads((ROOT / "reports/dataset_statistics.json").read_text())
    metrics = json.loads((ROOT / "reports/final_metrics.json").read_text())
    checks = json.loads((ROOT / "reports/verification.json").read_text())
    selected = json.loads((ROOT / "artifacts/selected.json").read_text())
    metadata = json.loads((ROOT / "artifacts/metadata" / f"{selected['version']}.json").read_text())
    trials = pd.read_csv(ROOT / "reports/model_comparison.csv")
    ablations = pd.read_csv(ROOT / "reports/ablations.csv")
    per_class = pd.read_csv(ROOT / "reports/per_class_metrics.csv")
    languages = pd.read_csv(ROOT / "reports/language_metrics.csv")
    lines = [
        "# Final project status",
        "",
        "Working research implementation with verified classical results; the full multilingual/category research objective remains limited by annotation coverage, Urdu source permission, and CPU-only compute.",
        "",
        "## Completed Components",
        "",
        "- Explicit source/license registry and schema gates; conservative Unicode/Roman Urdu preprocessing and heuristic language profiles.",
        "- Partial-label supervision, conflict quarantine, MinHash near-duplicate candidates, iterative splits and disjoint-split options.",
        "- Five sparse baseline families, validation-only tuning/thresholds, frozen test predictions, source/language slices, calibration, error records, identity probes and bootstrap intervals.",
        "- Optional XLM-R/mBERT trainer with weighted masked BCE/focal loss, accumulation, early stopping, resume and validation model selection. Transformer inference and Integrated Gradients are implemented but pretrained transformer fine-tuning was not run.",
        "- Versioned artifacts; FastAPI single/CSV endpoints; updated React interface; compatibility adapter preserves YouTube/live/export routes without keyword score overrides.",
        "- External multilabel annotation/evaluation infrastructure rejects overlaps and never trains on gold data.",
        "",
        "Verification: " + json.dumps(checks, ensure_ascii=False),
        "",
        "## Dataset Summary",
        "",
        f"Retained records: **{stats['n']:,}**. Splits: {stats['by_split']}. Sources: {stats['by_source']}.",
        "",
        f"Dataset SHA-256: `{stats['dataset_version']}`.",
        "",
        "Urdu spreadsheets are preserved but excluded because license/use permission is unverified. Roman Urdu source metadata declares CC-BY-4.0, but collection and annotation documentation is limited. Language labels are heuristics, not audited ground truth.",
        "",
        "## Models Trained",
        "",
        f"{len(trials)} recorded selection trials on {metadata['train_size']:,} training rows. {len(ablations[['roman_normalization', 'balanced']].drop_duplicates())} additional controlled logistic-regression normalization/class-weight ablations. Transformer status: {metrics['transformer']}.",
        "",
        "## Best Validation Model",
        "",
        f"**{metrics['model_name']}**; observed-label validation Macro-F1 **{metrics['validation']['macro_f1']:.4f}**.",
        "",
        "## Final Test Results",
        "",
        f"Observed-label Macro-F1: **{metrics['test']['macro_f1']:.4f}**; binary F1: **{metrics['binary']['f1']:.4f}**; binary accuracy: **{metrics['binary']['accuracy']:.4f}**.",
        "",
        f"Macro-F1 bootstrap interval: {metrics['confidence_interval']}.",
        "",
        "Only HATE_SPEECH and TOXIC have evaluable positive/negative coverage. This Macro-F1 is not comparable with historical nine-label scores. No real-world accuracy or significance claim is made.",
        "",
        "## Per-Class Results",
        "",
        "| Label | Positive test support | F1 | Evaluable |",
        "|---|---:|---:|---|",
    ]
    for row in per_class.itertuples():
        score = f"{row.f1:.4f}" if row.evaluable else "Not validated"
        lines.append(f"| {row.label} | {row.support} | {score} | {row.evaluable} |")
    lines += [
        "",
        "## Language Results",
        "",
        "| Heuristic group | Test rows | Binary F1 | Observed-label Macro-F1 |",
        "|---|---:|---:|---:|",
    ]
    for row in languages.itertuples():
        lines.append(f"| {row.group} | {row.n} | {row.binary_f1:.4f} | {row.macro_f1:.4f} |")
    lines += [
        "",
        "## Remaining Limitations",
        "",
        "- Six categories have no positive supervision and are disabled. No valid Urdu-script performance estimate or independent human gold evaluation.",
        "- No completed pretrained transformer comparison or statistical significance test. CPU-only host; no claim that complex models outperform baselines.",
        "- Probabilistic near-duplicate retrieval may miss variants; no conversation/user grouping metadata is available. Random source mixtures can encourage dataset artifacts.",
        "- SAFE/neutral annotations are assumed to exclude target harms. Missing subtype labels remain unknown. Fully observed subset accuracy mostly reflects neutral comments.",
        "- Browser visual verification was blocked by the browser admin-policy check. Frontend compilation and API integration are separately verified.",
        "- Low free space on C: remains a host risk. Original project ownership/license needs clarification before public redistribution.",
        "",
        "## Recommended Future Experiments",
        "",
        "Obtain Urdu dataset permission; independently annotate rare harms; audit language identification; run source/language-disjoint evaluations; fine-tune XLM-R and mBERT on GPU; perform paired bootstrap comparisons and annotator agreement studies. Do not tune on the frozen test set.",
        "",
        "## Exact Commands to Reproduce Results",
        "",
        "```powershell",
        ".venv/Scripts/python.exe -m pip install -e .",
        ".venv/Scripts/python.exe -m src.data.acquire",
        ".venv/Scripts/python.exe run_pipeline.py --profile standard",
        ".venv/Scripts/python.exe -m src.training.ablations",
        ".venv/Scripts/python.exe -m src.visualization.generate_figures",
        ".venv/Scripts/python.exe -m pytest -q",
        "cd frontend",
        "npm ci",
        "npm run build",
        "```",
        "",
        "This run executed preparation and baseline training first, then the master pipeline with `--skip-prepare --reuse-trained`; those flags reuse the verified dataset/model rather than refit. Frozen prediction files make report regeneration repeatable. Package versions are recorded in environment_report.json and requirements-lock.txt.",
    ]
    (ROOT / "FINAL_PROJECT_STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
