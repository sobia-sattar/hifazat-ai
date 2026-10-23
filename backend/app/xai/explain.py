"""Model-grounded XAI: linear coefficient attribution and token occlusion.

Does not invent important words. Tokens with near-zero contribution are omitted.
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np

TOKEN_RE = re.compile(r"[A-Za-z]+|[\u0600-\u06FF]+")


def _tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def linear_token_contributions(pipeline, text: str, class_index: int, top_k: int = 12) -> list[dict[str, Any]]:
    """Use TF-IDF feature weights × coefficients for a linear model."""
    vec = pipeline.named_steps.get("tfidf") or pipeline.named_steps.get("char")
    clf = pipeline.named_steps.get("clf")
    if vec is None or clf is None:
        return []
    X = vec.transform([text])
    feature_names = np.array(vec.get_feature_names_out())
    if hasattr(clf, "estimators_") and len(clf.estimators_) > class_index:
        coef = clf.estimators_[class_index].coef_.ravel()
    elif hasattr(clf, "coef_"):
        coef = np.array(clf.coef_)
        if coef.ndim == 2:
            coef = coef[min(class_index, coef.shape[0] - 1)]
        else:
            coef = coef.ravel()
    else:
        return []
    data = X.toarray().ravel()
    contrib = data * coef[: len(data)] if len(coef) >= len(data) else data[: len(coef)] * coef
    order = np.argsort(np.abs(contrib))[::-1]
    out = []
    for i in order:
        if len(out) >= top_k:
            break
        if abs(float(contrib[i])) < 1e-9 or data[i] == 0:
            continue
        out.append(
            {
                "feature": str(feature_names[i]),
                "contribution": round(float(contrib[i]), 6),
                "direction": "harmful" if contrib[i] > 0 else "protective",
            }
        )
    return out


def occlusion_importance(predict_proba_fn, text: str, class_index: int) -> list[dict[str, Any]]:
    """Leave-one-token-out change in predicted probability (model evidence)."""
    tokens = _tokenize(text)
    if not tokens:
        return []
    base = float(predict_proba_fn(text)[class_index])
    scored: list[dict[str, Any]] = []
    seen = set()
    for i, tok in enumerate(tokens):
        key = tok.lower()
        if key in seen:
            continue
        seen.add(key)
        masked = " ".join(t for j, t in enumerate(tokens) if j != i)
        if not masked.strip():
            continue
        p = float(predict_proba_fn(masked)[class_index])
        delta = base - p
        if abs(delta) < 1e-6:
            continue
        scored.append(
            {
                "token": tok,
                "contribution": round(delta, 6),
                "direction": "harmful" if delta > 0 else "protective",
            }
        )
    scored.sort(key=lambda x: abs(x["contribution"]), reverse=True)
    return scored[:16]


def explain_prediction(
    *,
    text: str,
    normalized: str,
    probabilities: dict[str, float],
    primary_label: str,
    pipeline=None,
    predict_proba_fn=None,
    class_index: int = 0,
    method: str = "auto",
) -> dict[str, Any]:
    linear = []
    occlusion = []
    if pipeline is not None:
        try:
            linear = linear_token_contributions(pipeline, normalized or text, class_index)
        except Exception:
            linear = []
    if predict_proba_fn is not None:
        try:
            occlusion = occlusion_importance(predict_proba_fn, normalized or text, class_index)
        except Exception:
            occlusion = []

    used = "token_occlusion"
    important = occlusion
    if linear:
        used = "linear_tfidf_coefficients"
        important = linear
    if method == "occlusion" and occlusion:
        used = "token_occlusion"
        important = occlusion

    why = structured_why(primary_label, probabilities, important)
    return {
        "method": used,
        "prediction": primary_label,
        "probabilities": probabilities,
        "important_features": important,
        "structured_evidence": why,
        "highlights": [
            {"term": f.get("feature") or f.get("token"), "contribution": f["contribution"], "direction": f["direction"]}
            for f in important[:10]
        ],
    }


def structured_why(label: str, probabilities: dict[str, float], features: list[dict[str, Any]]) -> dict[str, Any]:
    harmful_terms = [f.get("feature") or f.get("token") for f in features if f.get("direction") == "harmful"][:8]
    protective = [f.get("feature") or f.get("token") for f in features if f.get("direction") == "protective"][:5]
    return {
        "label": label,
        "top_harmful_terms": [t for t in harmful_terms if t],
        "top_protective_terms": [t for t in protective if t],
        "summary": _evidence_summary(label, harmful_terms),
    }


def _evidence_summary(label: str, terms: list[str]) -> str:
    terms = [t for t in terms if t]
    if label in {"SAFE", "UNCERTAIN"} and not terms:
        return "No strong harmful lexical evidence was attributed by the model."
    if not terms:
        return "The model assigned this label from overall feature patterns without a single dominant token."
    shown = ", ".join(f"“{t}”" for t in terms[:5])
    return f"Model attribution highlights {shown} as influential for the {label} decision."
