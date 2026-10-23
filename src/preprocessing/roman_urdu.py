"""Conservative spelling normalization; ambiguous English words remain unchanged."""

import re
from src.utils.common import ROOT  # noqa: F401
from app.nlp.roman_urdu import VARIANT_MAP

AMBIGUOUS = {"he", "hey", "hen", "men", "me", "main", "or", "per", "fir", "kiya", "ap", "ni", "q"}
NORMALIZATION = {k: v for k, v in VARIANT_MAP.items() if k not in AMBIGUOUS}
NORMALIZATION.update({"bhot": "bohat", "kr": "kar"})


def normalize_roman_urdu(text, phonetic=False):
    # Preserve whitespace, punctuation, Urdu characters and emoji exactly.
    def replace(match):
        token = match.group(0).lower()
        if token in AMBIGUOUS:
            return token
        reduced = re.sub(r"([a-z])\1{2,}", r"\1\1", token)
        if phonetic and reduced not in NORMALIZATION:
            reduced = re.sub("aa", "a", reduced)
        return NORMALIZATION.get(token, NORMALIZATION.get(reduced, token))

    return re.sub(r"[A-Za-z]+", replace, text)
