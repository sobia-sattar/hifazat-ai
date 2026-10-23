"""Train, compare, calibrate, and evaluate models. Test set is used once."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.labels import HARMFUL_LABELS, LABELS  # noqa: E402
from app.nlp.language import detect_language  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"
RESULTS = ROOT / "research" / "results"
SEED = 42
MAX_FEATURES_WORD = 40000
MAX_FEATURES_CHAR = 60000


def load_dataset() -> pd.DataFrame:
    path = PROCESSED / "dataset.csv"
    if not path.exists():
        raise SystemExit("Processed dataset missing. Run research/acquire_data.py then research/prepare_data.py")
    return pd.read_csv(path)


def y_matrix(df: pd.DataFrame) -> np.ndarray:
    return df[LABELS].fillna(0).astype(int).values


def with_cm_tag(texts: pd.Series) -> pd.Series:
    out = []
    for t in texts:
        s = "" if pd.isna(t) else str(t)
        lang = detect_language(s)
        tag = f" __LANG_{lang.language.replace(' ', '_')}__"
        if lang.is_code_mixed:
            tag += " __CODEMIX__"
        out.append(s + tag)
    return pd.Series(out, index=texts.index)


def build_word_lr() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=MAX_FEATURES_WORD, sublinear_tf=True)),
            (
                "clf",
                OneVsRestClassifier(
                    LogisticRegression(max_iter=200, class_weight="balanced", solver="liblinear", random_state=SEED)
                ),
            ),
        ]
    )


def build_word_svm() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=MAX_FEATURES_WORD, sublinear_tf=True)),
            (
                "clf",
                OneVsRestClassifier(
                    CalibratedClassifierCV(
                        LinearSVC(class_weight="balanced", random_state=SEED, max_iter=2000),
                        method="sigmoid",
                        cv=2,
                    )
                ),
            ),
        ]
    )


def build_char_svm() -> Pipeline:
    return Pipeline(
        [
            ("char", TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=3, max_features=MAX_FEATURES_CHAR, sublinear_tf=True)),
            (
                "clf",
                OneVsRestClassifier(
                    CalibratedClassifierCV(
                        LinearSVC(class_weight="balanced", random_state=SEED, max_iter=2000),
                        method="sigmoid",
                        cv=2,
                    )
                ),
            ),
        ]
    )


def build_hybrid_sklearn() -> Pipeline:
    union = FeatureUnion(
        [
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=25000, sublinear_tf=True)),
            ("char", TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=3, max_features=30000, sublinear_tf=True)),
        ]
    )
    return Pipeline(
        [
            ("features", union),
            (
                "clf",
                OneVsRestClassifier(
                    LogisticRegression(max_iter=200, class_weight="balanced", solver="liblinear", random_state=SEED)
                ),
            ),
        ]
    )


def predict_scores(model, texts) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(texts)
        if isinstance(proba, list):
            cols = [np.asarray(p)[:, 1] if np.asarray(p).ndim == 2 else np.asarray(p) for p in proba]
            return np.vstack(cols).T
        return np.asarray(proba)
    pred = model.predict(texts)
    return np.asarray(pred, dtype=float)


def binarize(scores: np.ndarray, thr: float = 0.5) -> np.ndarray:
    return (scores >= thr).astype(int)


def classification_metrics(y_true: np.ndarray, y_prob: np.ndarray, thr: float = 0.5) -> dict:
    y_pred = binarize(y_prob, thr)
    # Binary harmful view for accuracy-style metrics that remain honest under multi-label.
    true_h = (y_true[:, [LABELS.index(k) for k in HARMFUL_LABELS]].max(axis=1) == 1).astype(int)
    pred_h = (y_pred[:, [LABELS.index(k) for k in HARMFUL_LABELS]].max(axis=1) == 1).astype(int)
    fp = int(((pred_h == 1) & (true_h == 0)).sum())
    fn = int(((pred_h == 0) & (true_h == 1)).sum())
    tn = int(((pred_h == 0) & (true_h == 0)).sum())
    tp = int(((pred_h == 1) & (true_h == 1)).sum())
    fpr = fp / (fp + tn) if (fp + tn) else None
    fnr = fn / (fn + tp) if (fn + tp) else None
    per_class = {}
    for i, name in enumerate(LABELS):
        per_class[name] = {
            "precision": float(precision_score(y_true[:, i], y_pred[:, i], zero_division=0)),
            "recall": float(recall_score(y_true[:, i], y_pred[:, i], zero_division=0)),
            "f1": float(f1_score(y_true[:, i], y_pred[:, i], zero_division=0)),
            "support": int(y_true[:, i].sum()),
        }
    return {
        "accuracy": float(accuracy_score(true_h, pred_h)),
        "precision": float(precision_score(true_h, pred_h, zero_division=0)),
        "recall": float(recall_score(true_h, pred_h, zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "binary_harmful_f1": float(f1_score(true_h, pred_h, zero_division=0)),
        "per_class": per_class,
        "confusion_matrix_harmful": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "false_positives": fp,
        "false_negatives": fn,
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "n": int(len(true_h)),
        "note": "Accuracy is binary harmful vs safe. Macro-F1 is multi-label over all taxonomy labels.",
    }


def language_slice_name(lang: str, code_mixed: int) -> str:
    if int(code_mixed) == 1 or lang in {"English-Roman Urdu", "English-Urdu", "Mixed"}:
        return "Code-mixed"
    if lang == "Urdu":
        return "Urdu"
    if lang == "Roman Urdu":
        return "Roman Urdu"
    if lang == "English":
        return "English"
    return lang or "Unknown"


def eval_by_language(df: pd.DataFrame, y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    out = {}
    groups = df.apply(lambda r: language_slice_name(str(r["language"]), int(r.get("is_code_mixed") or 0)), axis=1)
    for name in ["English", "Urdu", "Roman Urdu", "Code-mixed"]:
        idx = np.where(groups.values == name)[0]
        if len(idx) == 0:
            out[name] = {"available": False, "message": "Not available"}
            continue
        out[name] = {"available": True, **classification_metrics(y_true[idx], y_prob[idx])}
    return out


def error_analysis(df: pd.DataFrame, y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    y_pred = binarize(y_prob)
    true_h = (y_true[:, [LABELS.index(k) for k in HARMFUL_LABELS]].max(axis=1) == 1)
    pred_h = (y_pred[:, [LABELS.index(k) for k in HARMFUL_LABELS]].max(axis=1) == 1)
    conf = np.max(y_prob, axis=1)
    records = []
    for i in range(len(df)):
        text = str(df.iloc[i]["original_text"])
        low = text.lower()
        tags = []
        if true_h[i] and not pred_h[i]:
            tags.append("false_negative")
        if pred_h[i] and not true_h[i]:
            tags.append("false_positive")
        if conf[i] < 0.55:
            tags.append("low_confidence")
        lang = language_slice_name(str(df.iloc[i]["language"]), int(df.iloc[i].get("is_code_mixed") or 0))
        if lang == "Roman Urdu":
            tags.append("roman_urdu")
        if lang == "Urdu":
            tags.append("urdu")
        if lang == "Code-mixed":
            tags.append("code_mixing")
        if any(w in low for w in ["not", "nahi", "nai", "never", "don't", "dont"]):
            tags.append("negation")
        if any(w in low for w in ["lol", "lmao", "sarcasm", "yeah right", "sure janab"]):
            tags.append("sarcasm_candidate")
        if any(w in low for w in ["bro", "yaar", "omg", "wtf", "boht", "tm "]):
            tags.append("slang")
        if len(text.split()) > 25:
            tags.append("context_dependent_candidate")
        if not tags:
            continue
        records.append(
            {
                "text": text[:400],
                "language": str(df.iloc[i]["language"]),
                "confidence": float(conf[i]),
                "true_harmful": bool(true_h[i]),
                "pred_harmful": bool(pred_h[i]),
                "tags": tags,
            }
        )
    summary = {}
    for tag in [
        "false_positive",
        "false_negative",
        "low_confidence",
        "roman_urdu",
        "urdu",
        "code_mixing",
        "negation",
        "sarcasm_candidate",
        "slang",
        "context_dependent_candidate",
    ]:
        summary[tag] = int(sum(1 for r in records if tag in r["tags"]))
    return {
        "counts": summary,
        "examples": records[:200],
        "note": "Sarcasm/slang/context tags are heuristic flags for research inspection, not gold labels.",
    }


def calibration_report(y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    true_h = (y_true[:, [LABELS.index(k) for k in HARMFUL_LABELS]].max(axis=1) == 1).astype(int)
    harm_prob = y_prob[:, [LABELS.index(k) for k in HARMFUL_LABELS]].max(axis=1)
    try:
        frac_pos, mean_pred = calibration_curve(true_h, harm_prob, n_bins=10, strategy="uniform")
        curve = [{"mean_predicted": float(m), "fraction_positive": float(f)} for m, f in zip(mean_pred, frac_pos)]
    except Exception:
        curve = []
    correct = (binarize(y_prob)[:, [LABELS.index(k) for k in HARMFUL_LABELS]].max(axis=1) == true_h)
    return {
        "curve": curve,
        "mean_confidence_correct": float(harm_prob[correct].mean()) if correct.any() else None,
        "mean_confidence_incorrect": float(harm_prob[~correct].mean()) if (~correct).any() else None,
        "n_correct": int(correct.sum()),
        "n_incorrect": int((~correct).sum()),
    }


def try_transformer(train_texts, y_train, val_texts, y_val) -> dict:
    try:
        import torch
        from torch import nn
        from torch.utils.data import DataLoader, Dataset
        from transformers import AutoModel, AutoTokenizer
    except Exception as exc:
        return {"available": False, "message": "Not available", "reason": str(exc)}

    model_name = "xlm-roberta-base"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    try:
        tok = AutoTokenizer.from_pretrained(model_name)
        encoder = AutoModel.from_pretrained(model_name)
    except Exception as exc:
        return {"available": False, "message": "Not available", "reason": str(exc)}

    class Txt(Dataset):
        def __init__(self, texts, labels):
            self.texts = list(texts)
            self.labels = np.asarray(labels, dtype=np.float32)

        def __len__(self):
            return len(self.texts)

        def __getitem__(self, i):
            enc = tok(self.texts[i], truncation=True, padding="max_length", max_length=96, return_tensors="pt")
            item = {k: v.squeeze(0) for k, v in enc.items()}
            item["labels"] = torch.tensor(self.labels[i])
            return item

    class Clf(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = encoder
            hidden = encoder.config.hidden_size
            self.head = nn.Linear(hidden, len(LABELS))

        def forward(self, input_ids, attention_mask, labels=None):
            out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
            logits = self.head(out.last_hidden_state[:, 0])
            loss = None
            if labels is not None:
                pos = labels.sum(0)
                neg = labels.shape[0] - pos
                pos_weight = (neg / pos.clamp(min=1.0)).to(logits.device)
                loss = nn.BCEWithLogitsLoss(pos_weight=pos_weight)(logits, labels)
            return logits, loss

    model = Clf().to(device)
    # Cap runtime: subsample if huge
    n_tr = min(len(train_texts), 8000)
    n_va = min(len(val_texts), 1500)
    tr = DataLoader(Txt(list(train_texts)[:n_tr], y_train[:n_tr]), batch_size=8, shuffle=True)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-5)
    model.train()
    steps = 0
    max_steps = 400
    for batch in tr:
        opt.zero_grad()
        ids = batch["input_ids"].to(device)
        mask = batch["attention_mask"].to(device)
        labs = batch["labels"].to(device)
        _, loss = model(ids, mask, labs)
        loss.backward()
        opt.step()
        steps += 1
        if steps >= max_steps:
            break
    model.eval()
    va = DataLoader(Txt(list(val_texts)[:n_va], y_val[:n_va]), batch_size=8)
    probs = []
    with torch.no_grad():
        for batch in va:
            ids = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            logits, _ = model(ids, mask)
            probs.append(torch.sigmoid(logits).cpu().numpy())
    y_prob = np.vstack(probs)
    metrics = classification_metrics(y_val[: len(y_prob)], y_prob)
    ckpt = MODELS / "xlm_roberta.pt"
    torch.save({"state_dict": model.state_dict(), "model_name": model_name}, ckpt)
    return {
        "available": True,
        "name": "xlm-roberta-base",
        "val_metrics": metrics,
        "checkpoint": str(ckpt.relative_to(ROOT)),
        "train_steps": steps,
        "device": str(device),
        "subsampled_train": n_tr,
        "note": "Fine-tuned with a step cap for local feasibility. Validation metrics use the subsampled validation slice used during this run.",
    }


def fit_eval(name, builder, train_x, y_train, val_x, y_val):
    model = builder()
    model.fit(train_x, y_train)
    scores = predict_scores(model, val_x)
    metrics = classification_metrics(y_val, scores)
    return {"name": name, "model": model, "val_metrics": metrics, "val_scores": scores}


def main() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    df = load_dataset()
    train = df[df["split"] == "train"].reset_index(drop=True)
    val = df[df["split"] == "validation"].reset_index(drop=True)
    test = df[df["split"] == "test"].reset_index(drop=True)
    train_cap = int(os.environ.get("BULLYLENS_MAX_TRAIN", "10000"))
    subsample_note = None
    if len(train) > train_cap:
        from sklearn.model_selection import train_test_split as tts

        try:
            train, _ = tts(train, train_size=train_cap, random_state=SEED, stratify=train["binary_harmful"])
        except ValueError:
            train = train.sample(n=train_cap, random_state=SEED)
        train = train.reset_index(drop=True)
        subsample_note = f"Training rows capped at {train_cap} for local compute. Validation and test splits were not used for fitting."
    y_train, y_val, y_test = y_matrix(train), y_matrix(val), y_matrix(test)

    # Ablation texts
    train_raw = train["original_text"].map(lambda v: "" if pd.isna(v) else str(v))
    val_raw = val["original_text"].map(lambda v: "" if pd.isna(v) else str(v))
    test_raw = test["original_text"].map(lambda v: "" if pd.isna(v) else str(v))
    train_norm = train["normalized_text"].map(lambda v: "" if pd.isna(v) else str(v))
    val_norm = val["normalized_text"].map(lambda v: "" if pd.isna(v) else str(v))
    test_norm = test["normalized_text"].map(lambda v: "" if pd.isna(v) else str(v))
    train_cm, val_cm = with_cm_tag(train_norm), with_cm_tag(val_norm)
    test_cm = with_cm_tag(test_norm)

    candidates = []
    print("Training TF-IDF + Logistic Regression (normalized)")
    candidates.append(fit_eval("tfidf_logreg", build_word_lr, train_norm, y_train, val_norm, y_val))
    print("Training TF-IDF + Linear SVM (normalized)")
    candidates.append(fit_eval("tfidf_linear_svm", build_word_svm, train_norm, y_train, val_norm, y_val))
    print("Training char n-gram + Linear SVM (normalized)")
    candidates.append(fit_eval("char_ngram_svm", build_char_svm, train_norm, y_train, val_norm, y_val))
    print("Training hybrid word+char logistic regression")
    candidates.append(fit_eval("hybrid_word_char_logreg", build_hybrid_sklearn, train_norm, y_train, val_norm, y_val))

    comparison = [
        {"model": c["name"], "validation_macro_f1": c["val_metrics"]["macro_f1"], **{k: c["val_metrics"][k] for k in ("accuracy", "precision", "recall", "weighted_f1")}}
        for c in candidates
    ]
    best = max(candidates, key=lambda c: c["val_metrics"]["macro_f1"])
    print(f"Selected by validation Macro-F1: {best['name']} ({best['val_metrics']['macro_f1']:.4f})")

    # Ablations use logistic regression for comparable compute
    print("Ablation: no Roman Urdu normalization")
    ab_raw = fit_eval("logreg_no_norm", build_word_lr, train_raw, y_train, val_raw, y_val)
    print("Ablation: normalization + code-mix tags")
    ab_cm = fit_eval("logreg_norm_codemix", build_word_lr, train_cm, y_train, val_cm, y_val)

    transformer = {"available": False, "message": "Requires training"}
    if os.environ.get("BULLYLENS_TRAIN_TRANSFORMER", "0") == "1":
        transformer = try_transformer(train_norm.tolist(), y_train, val_norm.tolist(), y_val)
    else:
        transformer = {
            "available": False,
            "message": "Requires training",
            "reason": "XLM-RoBERTa fine-tuning is implemented in research/train.py. Set BULLYLENS_TRAIN_TRANSFORMER=1 after installing torch and transformers.",
        }
    if transformer.get("available"):
        comparison.append(
            {
                "model": transformer["name"],
                "validation_macro_f1": transformer["val_metrics"]["macro_f1"],
                **{k: transformer["val_metrics"][k] for k in ("accuracy", "precision", "recall", "weighted_f1")},
            }
        )
        if transformer["val_metrics"]["macro_f1"] > best["val_metrics"]["macro_f1"]:
            # Transformer selected for research tables; sklearn inference bundle remains the serving model
            # unless we also exported a serving pipeline. Serving uses sklearn for reliable XAI + batch CPU.
            selected_research = transformer["name"]
        else:
            selected_research = best["name"]
    else:
        selected_research = best["name"]

    # Final test — once — on the selected sklearn serving model (best validation Macro-F1 among sklearn)
    test_scores = predict_scores(best["model"], test_norm)
    test_metrics = classification_metrics(y_test, test_scores)
    per_lang = eval_by_language(test, y_test, test_scores)
    fairness = {}
    for lang, m in per_lang.items():
        if not m.get("available"):
            fairness[lang] = m
            continue
        fairness[lang] = {
            "precision": m["precision"],
            "recall": m["recall"],
            "f1": m["binary_harmful_f1"],
            "false_positive_rate": m["false_positive_rate"],
            "false_negative_rate": m["false_negative_rate"],
            "n": m["n"],
        }
    langs_ok = [k for k, v in fairness.items() if v.get("n")]
    if langs_ok:
        f1s = [fairness[k]["f1"] for k in langs_ok]
        fairness["gap_max_minus_min_f1"] = float(max(f1s) - min(f1s))
        fairness["note"] = "Gaps are measured differences. This does not imply the model is unbiased."

    errors = error_analysis(test, y_test, test_scores)
    calib = calibration_report(y_test, test_scores)

    ablation = {
        "baseline_tfidf_logreg_no_norm": ab_raw["val_metrics"],
        "tfidf_logreg_with_norm": next(c["val_metrics"] for c in candidates if c["name"] == "tfidf_logreg"),
        "tfidf_logreg_norm_plus_codemix": ab_cm["val_metrics"],
        "best_sklearn_on_validation": {"name": best["name"], **best["val_metrics"]},
        "transformer_on_validation": transformer,
        "note": "Ablations report validation metrics only. The test set was evaluated once for the selected sklearn model.",
    }

    bundle = {"pipeline": best["model"], "labels": LABELS, "text_field": "normalized_text"}
    joblib.dump(bundle, MODELS / "best_sklearn.joblib")
    meta = {
        "selected_model": best["name"],
        "selected_research_name": selected_research,
        "selection_criterion": "validation Macro-F1 among sklearn models used for serving",
        "validation_macro_f1": best["val_metrics"]["macro_f1"],
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "labels": LABELS,
        "never_claim_100": True,
    }
    (MODELS / "model_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    dataset_stats = json.loads((PROCESSED / "dataset_stats.json").read_text(encoding="utf-8"))
    registry = {}
    reg_path = ROOT / "research" / "dataset_registry.json"
    if reg_path.exists():
        registry = json.loads(reg_path.read_text(encoding="utf-8"))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "training_subsample": subsample_note,
        "dataset": dataset_stats,
        "dataset_registry": registry,
        "model_comparison_validation": comparison,
        "selected_serving_model": best["name"],
        "test": test_metrics,
        "per_language_test": per_lang,
        "fairness_test": fairness,
        "ablation_validation": {
            k: (
                {mk: mv for mk, mv in v.items() if mk != "per_class"}
                if isinstance(v, dict) and "macro_f1" in v
                else v
            )
            for k, v in ablation.items()
        },
        "calibration_test": calib,
        "error_analysis_test": {"counts": errors["counts"], "note": errors["note"], "example_count": len(errors["examples"])},
        "confusion_matrix_test": test_metrics["confusion_matrix_harmful"],
        "limitations": (
            "Results are not 100% accurate. Roman Urdu spelling, sarcasm, code-mixing, and context remain error sources. "
            "Demo mode data is excluded from these metrics."
        ),
    }
    (MODELS / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (RESULTS / "latest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (RESULTS / "error_examples.json").write_text(json.dumps(errors, indent=2), encoding="utf-8")
    print("Wrote models/metrics.json and research/results/latest.json")
    print("TEST macro_f1", test_metrics["macro_f1"], "accuracy", test_metrics["accuracy"])


if __name__ == "__main__":
    main()
