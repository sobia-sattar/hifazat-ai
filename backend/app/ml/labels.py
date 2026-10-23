"""Multi-label taxonomy used across training, inference, and UI."""

from __future__ import annotations

LABELS = [
    "SAFE",
    "CYBERBULLYING",
    "HARASSMENT",
    "HATE_SPEECH",
    "THREAT",
    "INSULT",
    "TOXIC",
    "SEXUAL_HARASSMENT",
    "OTHER_HARMFUL",
]

HARMFUL_LABELS = [l for l in LABELS if l != "SAFE"]

PRIMARY_DISPLAY = {
    "SAFE": "SAFE",
    "CYBERBULLYING": "BULLYING",
    "HARASSMENT": "HARASSMENT",
    "HATE_SPEECH": "HATE/ABUSIVE",
    "THREAT": "THREAT",
    "INSULT": "INSULT",
    "TOXIC": "OTHER HARMFUL",
    "SEXUAL_HARASSMENT": "HARASSMENT",
    "OTHER_HARMFUL": "OTHER HARMFUL",
    "UNCERTAIN": "UNCERTAIN",
}

DISPLAY_CATEGORIES = {
    "CYBERBULLYING": "Cyberbullying",
    "HARASSMENT": "Harassment",
    "HATE_SPEECH": "Hate speech",
    "THREAT": "Threat",
    "INSULT": "Insult",
    "TOXIC": "Toxic",
    "SEXUAL_HARASSMENT": "Sexual harassment",
    "OTHER_HARMFUL": "Other harmful",
    "SAFE": "Safe",
}


def empty_label_vector() -> dict[str, int]:
    return {k: 0 for k in LABELS}


def apply_harmful(vec: dict[str, int], *names: str) -> dict[str, int]:
    out = dict(vec)
    out["SAFE"] = 0
    for n in names:
        if n in out:
            out[n] = 1
    if not any(out[k] for k in HARMFUL_LABELS):
        out["SAFE"] = 1
    return out


def mark_safe(vec: dict[str, int] | None = None) -> dict[str, int]:
    out = empty_label_vector() if vec is None else dict(vec)
    for k in HARMFUL_LABELS:
        out[k] = 0
    out["SAFE"] = 1
    return out
