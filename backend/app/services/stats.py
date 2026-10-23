from __future__ import annotations

from typing import Any


def compute_comment_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {
            "total": 0,
            "safe": 0,
            "bullying": 0,
            "harassment": 0,
            "threats": 0,
            "hate": 0,
            "insult": 0,
            "high_risk": 0,
            "uncertain": 0,
            "bullying_rate": None,
            "message": "No comments analyzed.",
        }

    def has_cat(row, key):
        cats = row.get("categories") or {}
        return float(cats.get(key, 0)) >= 0.5

    safe = sum(1 for r in rows if r.get("classification") == "SAFE")
    bullying = sum(1 for r in rows if r.get("classification") == "BULLYING")
    uncertain = sum(1 for r in rows if r.get("classification") == "UNCERTAIN")
    harassment = sum(1 for r in rows if has_cat(r, "HARASSMENT") or has_cat(r, "SEXUAL_HARASSMENT"))
    threats = sum(1 for r in rows if has_cat(r, "THREAT"))
    hate = sum(1 for r in rows if has_cat(r, "HATE_SPEECH"))
    insult = sum(1 for r in rows if has_cat(r, "INSULT"))
    high_risk = sum(1 for r in rows if r.get("risk") in {"HIGH", "CRITICAL"})

    lang_counts: dict[str, int] = {}
    risk_counts: dict[str, int] = {}
    conf_buckets = {"0-0.4": 0, "0.4-0.55": 0, "0.55-0.75": 0, "0.75-1.0": 0}
    cat_counts = {
        "CYBERBULLYING": 0,
        "HARASSMENT": 0,
        "HATE_SPEECH": 0,
        "THREAT": 0,
        "INSULT": 0,
        "TOXIC": 0,
        "SEXUAL_HARASSMENT": 0,
        "OTHER_HARMFUL": 0,
    }
    trend = []
    for r in rows:
        lang_counts[r.get("language") or "Unknown"] = lang_counts.get(r.get("language") or "Unknown", 0) + 1
        risk_counts[r.get("risk") or "LOW"] = risk_counts.get(r.get("risk") or "LOW", 0) + 1
        c = float(r.get("confidence") or 0)
        if c < 0.4:
            conf_buckets["0-0.4"] += 1
        elif c < 0.55:
            conf_buckets["0.4-0.55"] += 1
        elif c < 0.75:
            conf_buckets["0.55-0.75"] += 1
        else:
            conf_buckets["0.75-1.0"] += 1
        for k in cat_counts:
            if has_cat(r, k):
                cat_counts[k] += 1
        if r.get("published_at"):
            trend.append(
                {
                    "t": r["published_at"],
                    "bullying": 1 if r.get("classification") == "BULLYING" else 0,
                    "toxic": 1 if has_cat(r, "TOXIC") else 0,
                }
            )

    return {
        "total": n,
        "safe": safe,
        "bullying": bullying,
        "harassment": harassment,
        "threats": threats,
        "hate": hate,
        "insult": insult,
        "high_risk": high_risk,
        "uncertain": uncertain,
        "bullying_rate": round(100.0 * bullying / n, 2),
        "language_distribution": lang_counts,
        "risk_distribution": risk_counts,
        "confidence_distribution": conf_buckets,
        "category_distribution": cat_counts,
        "trend": trend,
    }
