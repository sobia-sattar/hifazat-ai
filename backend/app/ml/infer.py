"""Compatibility adapter: all live paths use frozen research predictions, without keyword overrides."""

from functools import lru_cache
import json
from typing import Any
from src.utils.common import ROOT, LABELS as HARMFUL_LABELS
from src.inference.predict import Predictor
from app.ml.labels import LABELS, DISPLAY_CATEGORIES
from app.nlp.language import detect_language
from app.core.runtime import high_threshold, low_threshold


def models_paths():
    directory = ROOT / "models"
    return dict(
        dir=directory,
        sklearn=directory / "best_sklearn.joblib",
        meta=directory / "model_meta.json",
        metrics=directory / "metrics.json",
        research=ROOT / "research/results/latest.json",
    )


def load_research_metrics():
    path = ROOT / "research/results/latest.json"
    if not path.exists():
        return None
    return {
        **json.loads(path.read_text()),
        "provenance": "HISTORICAL / PROJECT-REPORTED. See /api/v2/results for new experiments.",
    }


@lru_cache(maxsize=1)
def _research_predictor():
    return Predictor()


def model_status():
    try:
        bundle = _research_predictor().bundle
        return dict(
            ready=True,
            message="ready",
            selected_model=bundle["model_name"],
            trained_at=bundle["training_date"],
            selection_criterion="Observed-label validation Macro-F1",
            metrics_available=True,
            version=bundle["version"],
        )
    except Exception:
        return dict(
            ready=False,
            message="Research artifact missing or invalid; run training.",
            selected_model=None,
            metrics_available=False,
        )


def get_bundle():
    # Kept for historical analysis tools only; never used by live inference.
    import joblib

    paths = models_paths()
    if not paths["sklearn"].exists():
        return None
    return dict(sklearn=joblib.load(paths["sklearn"]), meta=json.loads(paths["meta"].read_text()))


def _predict_sklearn(text, clf_bundle):
    pipeline = clf_bundle["pipeline"]
    values = pipeline.predict_proba([text])[0]
    return dict(zip(clf_bundle["labels"], map(float, values))), pipeline


def analyze_text(text: str, include_xai: bool = True) -> dict[str, Any]:
    language = detect_language(text)
    status = model_status()
    if not status["ready"]:
        return dict(
            original_text=text,
            normalized_text=text,
            language=language.language,
            language_confidence=language.language_confidence,
            script=language.script,
            is_code_mixed=language.is_code_mixed,
            classification="UNCERTAIN",
            display_status="UNCERTAIN",
            confidence=0.0,
            risk="REVIEW",
            categories={label: 0.0 for label in LABELS},
            active_categories=[],
            code_mix_tokens=[],
            recommendation="Human review required",
            why=status["message"],
            xai={},
            model=status,
            moderation_recommendation="Research model unavailable. No prediction was made.",
        )
    result = _research_predictor().predict([text], explain=include_xai)[0]
    harmful = result["binary_prediction"] == "HARMFUL"
    probability = result["harmful_probability"]
    scores = {label: result["categories"][label]["probability"] for label in HARMFUL_LABELS}
    scores["SAFE"] = 1 - probability
    active = [label for label in result["labels"] if label != "SAFE"]
    # Legacy UI calls broad harmful content BULLYING. Keep wire compatibility and expose exact binary label.
    classification = "BULLYING" if harmful else "SAFE"
    evidence = result.get("explanation", {})
    confidence = probability if harmful else 1 - probability
    risk = 'REVIEW' if result['category_binary_disagreement'] or confidence < low_threshold() else 'HIGH' if harmful and confidence >= high_threshold() else 'MEDIUM' if harmful else 'LOW'
    return dict(
        original_text=text,
        normalized_text=result["processed_text"],
        language=language.language,
        language_confidence=language.language_confidence,
        script=language.script,
        is_code_mixed=language.is_code_mixed,
        code_mix_tokens=[dict(token=t.token, language=t.language) for t in language.tokens],
        language_evidence=language.evidence,
        classification=classification,
        display_status=result["binary_prediction"],
        binary_prediction=result["binary_prediction"],
        confidence=confidence,
        harmful_probability=probability,
        risk=risk,
        categories=scores,
        active_categories=[dict(id=label, label=DISPLAY_CATEGORIES[label], score=scores[label]) for label in active],
        primary_category=max(active, key=lambda label: scores[label]) if active else "SAFE",
        recommendation="Human review before moderation.",
        moderation_recommendation=result["notice"],
        why="Frozen model predictions; no word rules modify scores.",
        xai=dict(
            method="linear_feature_contributions",
            important_features=evidence.get("features", []),
            structured_evidence=dict(summary=evidence.get("warning", "Feature importance is not causal.")),
            highlights=[],
        ),
        model=status,
        thresholds={label: value["threshold"] for label, value in result["categories"].items()},
    )


def analyze_batch(texts, include_xai=True):
    return [analyze_text(text, include_xai) for text in texts]
