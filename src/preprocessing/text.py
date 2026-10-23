import html
import re
import unicodedata
from src.preprocessing.roman_urdu import normalize_roman_urdu
from app.nlp.language import detect_language


def preprocess(text, roman=True, diacritics=False):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKC", html.unescape(text))
    text = re.sub(r"<[^>]*>", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " URLTOKEN ", text)
    text = re.sub(r"(?<!\w)@[\w]+", " USERTOKEN ", text)
    text = text.translate(str.maketrans({"ك": "ک", "ي": "ی", "ى": "ی", "\u0640": ""}))
    if diacritics:
        text = re.sub(r"[\u064b-\u065f\u0670]", "", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return normalize_roman_urdu(text) if roman else text


def language_metadata(text):
    result = detect_language(text)
    language = result.language.replace("-", "_").replace(" ", "_")
    return dict(
        language=language,
        script=result.script,
        code_mixed=result.is_code_mixed,
        language_confidence=result.language_confidence,
    )
