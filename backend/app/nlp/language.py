"""Hybrid language and code-mixing detection.

Does not treat all Latin-script text as English. Combines Unicode script
detection, word-level evidence, Roman Urdu lexicon, English function words,
and character-level cues.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from app.nlp.roman_urdu import ROMAN_URDU_LEXICON, normalize_token, roman_urdu_lexicon

ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
LATIN_RE = re.compile(r"[A-Za-z]")
TOKEN_RE = re.compile(r"[A-Za-z]+|[\u0600-\u06FF]+")

ENGLISH_FUNCTION = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "and", "or", "but", "if", "then", "because", "as", "until", "while",
    "of", "at", "by", "for", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "to", "from",
    "up", "down", "in", "out", "on", "off", "over", "under", "again",
    "this", "that", "these", "those", "i", "you", "he", "she", "it", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "its",
    "our", "their", "what", "which", "who", "whom", "this", "not", "no",
    "do", "does", "did", "doing", "have", "has", "had", "having", "will",
    "would", "can", "could", "should", "may", "might", "must", "just",
    "than", "too", "very", "so", "only", "own", "same", "also", "how",
    "when", "where", "why", "all", "each", "few", "more", "most", "other",
    "some", "such", "video", "content", "really", "stupid", "idiot", "hate",
    "kill", "die", "ugly", "dumb", "trash", "worst", "best", "good", "bad",
    "please", "thanks", "thank", "nice", "great", "love", "like", "comment",
}

# Words that are strongly English even if they appear in mixed text.
ENGLISH_CONTENT = {
    "stupid", "idiot", "dumb", "ugly", "hate", "kill", "die", "trash",
    "garbage", "worst", "disgusting", "pathetic", "loser", "moron", "fool",
    "shut", "up", "fuck", "shit", "bitch", "asshole", "bastard", "retard",
    "video", "content", "channel", "subscribe", "like", "comment", "really",
    "very", "your", "you", "are", "this", "that", "is", "bad", "good",
}

# Roman Urdu tokens that are not English despite Latin script.
RU_STRONG = roman_urdu_lexicon()


@dataclass
class TokenLang:
    token: str
    language: str


@dataclass
class LanguageResult:
    language: str
    language_confidence: float
    script: str
    is_code_mixed: bool
    tokens: list[TokenLang] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)


def _coerce_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value)


def detect_script(text: str) -> str:
    t = _coerce_text(text)
    has_ar = bool(ARABIC_RE.search(t))
    has_la = bool(LATIN_RE.search(t))
    if has_ar and has_la:
        return "mixed"
    if has_ar:
        return "arabic"
    if has_la:
        return "latin"
    return "other"


def _char_cues(text: str) -> dict[str, float]:
    latin = [c.lower() for c in text if c.isalpha() and c.isascii()]
    if not latin:
        return {"ru_char": 0.0, "en_char": 0.0}
    n = len(latin)
    # Roman Urdu informal text often uses q, kh patterns; English more 'the' bigrams handled at word level.
    q = sum(1 for c in latin if c == "q") / n
    vowel_ratio = sum(1 for c in latin if c in "aeiou") / n
    return {"q_ratio": q, "vowel_ratio": vowel_ratio}


def classify_latin_token(tok: str) -> str:
    low = tok.lower()
    norm = normalize_token(low)
    in_ru = low in RU_STRONG or norm in RU_STRONG
    in_en = low in ENGLISH_FUNCTION or low in ENGLISH_CONTENT
    if in_ru and not in_en:
        return "Roman Urdu"
    if in_en and not in_ru:
        return "English"
    if in_ru and in_en:
        # Ambiguous short tokens like "to", "or", "me" — prefer context via length/lexicon strength
        if low in {"to", "or", "me", "he", "us", "no", "so", "hi"}:
            return "Ambiguous"
        return "English" if low in ENGLISH_CONTENT else "Roman Urdu"
    # Heuristic for unseen Latin tokens: missing vowels + informal RU endings
    if re.fullmatch(r"[a-z]{2,}", low):
        vowels = sum(1 for c in low if c in "aeiou")
        if vowels == 0 and len(low) >= 3:
            return "Roman Urdu"
        if low.endswith(("ao", "ein", "ain", "gi", "ga", "ge", "na", "ni")) and low not in ENGLISH_FUNCTION:
            return "Roman Urdu"
    return "Unknown"


def detect_language(text: str) -> LanguageResult:
    safe_text = _coerce_text(text)
    script = detect_script(safe_text)
    raw_tokens = TOKEN_RE.findall(safe_text)
    tokens: list[TokenLang] = []
    for t in raw_tokens:
        if ARABIC_RE.search(t):
            tokens.append(TokenLang(t, "Urdu"))
        else:
            tokens.append(TokenLang(t, classify_latin_token(t)))

    n = max(len(tokens), 1)
    urdu = sum(1 for t in tokens if t.language == "Urdu")
    ru = sum(1 for t in tokens if t.language == "Roman Urdu")
    en = sum(1 for t in tokens if t.language == "English")
    unk = sum(1 for t in tokens if t.language in {"Unknown", "Ambiguous"})

    is_code_mixed = False
    language = "Unknown"
    conf = 0.4

    if script == "arabic" and urdu == n:
        language, conf = "Urdu", min(0.99, 0.85 + 0.02 * n)
    elif script == "mixed":
        is_code_mixed = True
        if ru + en > 0 and urdu > 0:
            language, conf = "English-Urdu", 0.72 + 0.05 * min(urdu, 3) / 3
            if ru > en:
                language = "Mixed"
        else:
            language, conf = "Mixed", 0.7
    elif script == "latin":
        if ru > 0 and en > 0:
            is_code_mixed = True
            language = "English-Roman Urdu"
            conf = min(0.95, 0.65 + 0.08 * min(ru + en, 6) / 6)
        elif ru > 0 and ru >= en and ru >= max(1, unk * 0.5):
            language = "Roman Urdu"
            conf = min(0.94, 0.6 + 0.3 * ru / n)
        elif en > 0 and en >= ru:
            language = "English"
            conf = min(0.94, 0.55 + 0.35 * en / n)
        elif ru > 0:
            language = "Roman Urdu"
            conf = 0.58
        else:
            # Unseen Latin: do not default to English
            cues = _char_cues(text)
            if cues.get("vowel_ratio", 0.5) < 0.28:
                language, conf = "Roman Urdu", 0.52
            else:
                language, conf = "Unknown", 0.45
    else:
        language, conf = "Unknown", 0.3

    if language == "Unknown" and urdu:
        language, conf = "Urdu", 0.7

    evidence = {
        "urdu_tokens": urdu,
        "roman_urdu_tokens": ru,
        "english_tokens": en,
        "unknown_tokens": unk,
        "token_count": n,
    }
    return LanguageResult(
        language=language,
        language_confidence=round(conf, 4),
        script=script,
        is_code_mixed=is_code_mixed or language in {"English-Roman Urdu", "English-Urdu", "Mixed"},
        tokens=tokens,
        evidence=evidence,
    )


def preprocess_text(text: str) -> str:
    text = _coerce_text(text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
