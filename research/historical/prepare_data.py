"""Build a leakage-aware multilingual multi-label training table from acquired sources."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.labels import HARMFUL_LABELS, LABELS, apply_harmful, empty_label_vector, mark_safe  # noqa: E402
from app.nlp.language import detect_language, preprocess_text  # noqa: E402
from app.nlp.roman_urdu import normalize_roman_urdu  # noqa: E402

RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
SEED = 42


def _norm_key(text: str) -> str:
    t = preprocess_text(str(text)).lower()
    t = re.sub(r"[^a-z0-9\u0600-\u06ff]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _row(text: str, labels: dict[str, int], source: str, source_lang_hint: str | None = None) -> dict:
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return {}
    original = str(text).strip()
    if not original or original.lower() in {"nan", "none", "null"}:
        return {}
    cleaned = preprocess_text(original)
    if not cleaned:
        return {}
    lang = detect_language(cleaned)
    normalized = normalize_roman_urdu(cleaned) if lang.script in {"latin", "mixed"} else cleaned
    language = lang.language
    if source_lang_hint == "Urdu" and lang.script == "arabic":
        language = "Urdu"
    rec = {
        "original_text": original,
        "normalized_text": normalized,
        "language": language,
        "language_confidence": lang.language_confidence,
        "script": lang.script,
        "is_code_mixed": int(lang.is_code_mixed),
        "source": source,
        "key": _norm_key(normalized),
    }
    rec.update(labels)
    rec["binary_harmful"] = int(any(labels.get(k, 0) for k in HARMFUL_LABELS))
    return rec


def map_davidson() -> list[dict]:
    path = RAW / "davidson_labeled_data.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path)
    text_col = "tweet" if "tweet" in df.columns else df.columns[-1]
    rows = []
    for _, r in df.iterrows():
        cls = int(r.get("class", 2))
        if cls == 0:
            # Davidson provides hate-speech/offensive/neutral labels, not a
            # cyberbullying label. Do not manufacture a stronger class.
            labels = apply_harmful(empty_label_vector(), "HATE_SPEECH", "TOXIC")
        elif cls == 1:
            labels = apply_harmful(empty_label_vector(), "INSULT", "TOXIC")
        else:
            labels = mark_safe()
        rec = _row(str(r[text_col]), labels, "davidson2017", "English")
        if rec:
            rows.append(rec)
    return rows


def _guess_text_col(df: pd.DataFrame) -> str:
    for c in df.columns:
        cl = str(c).lower()
        if cl in {"text", "tweet", "comment", "sentence", "content", "message", "urdu", "tweets"}:
            return c
    # longest string average
    best, best_n = df.columns[0], -1
    for c in df.columns:
        s = df[c].astype(str)
        n = s.str.len().mean()
        if n > best_n:
            best, best_n = c, n
    return best


def _guess_label_col(df: pd.DataFrame, text_col: str) -> str | None:
    for c in df.columns:
        if c == text_col:
            continue
        cl = str(c).lower()
        if cl in {"label", "labels", "class", "category", "type", "tag", "cyberbullying", "cb"}:
            return c
    for c in df.columns:
        if c != text_col:
            return c
    return None


def map_urdu_label(value: object) -> dict[str, int]:
    raw = str(value).strip().lower()
    if raw in {"", "nan", "none", "0", "safe", "not bullying", "non-bullying", "non_bullying", "no"}:
        return mark_safe()
    mapping = {
        "insult": ("INSULT", "CYBERBULLYING", "TOXIC"),
        "offensive": ("TOXIC", "CYBERBULLYING", "HARASSMENT"),
        "profane": ("TOXIC", "OTHER_HARMFUL"),
        "name-calling": ("INSULT", "CYBERBULLYING"),
        "name calling": ("INSULT", "CYBERBULLYING"),
        "threat": ("THREAT", "CYBERBULLYING", "HARASSMENT"),
        "curse": ("TOXIC", "OTHER_HARMFUL", "CYBERBULLYING"),
        "hate": ("HATE_SPEECH", "TOXIC", "CYBERBULLYING"),
        "harassment": ("HARASSMENT", "CYBERBULLYING"),
        "bullying": ("CYBERBULLYING", "TOXIC"),
        "cyberbullying": ("CYBERBULLYING", "TOXIC"),
        "abusive": ("TOXIC", "HARASSMENT", "CYBERBULLYING"),
        "toxic": ("TOXIC",),
        "1": ("CYBERBULLYING", "TOXIC"),
        "yes": ("CYBERBULLYING", "TOXIC"),
    }
    for key, labs in mapping.items():
        if key in raw:
            return apply_harmful(empty_label_vector(), *labs)
    if raw in {"positive", "neg", "negative"}:
        # ambiguous sentiment-style labels are skipped later if needed
        if "pos" in raw and "neg" not in raw:
            return mark_safe()
        return apply_harmful(empty_label_vector(), "TOXIC", "CYBERBULLYING")
    return apply_harmful(empty_label_vector(), "OTHER_HARMFUL", "CYBERBULLYING")


def map_urdu_excel(filename: str, source: str) -> list[dict]:
    path = RAW / filename
    if not path.exists():
        return []
    df = pd.read_excel(path)
    text_col = _guess_text_col(df)
    label_col = _guess_label_col(df, text_col)
    schema = {"columns": list(map(str, df.columns)), "text_col": str(text_col), "label_col": str(label_col)}
    (PROCESSED / f"{source}_schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    rows = []
    for _, r in df.iterrows():
        text = r[text_col]
        labels = map_urdu_label(r[label_col] if label_col else "none")
        rec = _row(str(text), labels, source, "Urdu")
        if rec:
            rows.append(rec)
    return rows


def map_roman_urdu_csv() -> list[dict]:
    path = RAW / "roman_urdu_toxic_corpus.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path)
    text_col = _guess_text_col(df)
    label_col = _guess_label_col(df, text_col)
    rows = []
    for _, r in df.iterrows():
        val = str(r[label_col]).strip().lower() if label_col else "0"
        toxic = val in {"1", "true", "yes", "toxic", "abusive", "hate", "offensive"}
        labels = apply_harmful(empty_label_vector(), "TOXIC", "CYBERBULLYING", "INSULT") if toxic else mark_safe()
        rec = _row(str(r[text_col]), labels, "roman_urdu_toxic_hf")
        if rec:
            rows.append(rec)
    return rows


def drop_duplicates(rows: list[dict]) -> tuple[list[dict], dict]:
    by_key: dict[str, dict] = {}
    exact_dropped = 0
    for r in rows:
        k = r["key"]
        if not k:
            continue
        if k in by_key:
            exact_dropped += 1
            continue
        by_key[k] = r
    unique = list(by_key.values())
    unique.sort(key=lambda x: x["key"])
    kept: list[dict] = []
    near_dropped = 0
    for r in unique:
        dup = False
        for prev in kept[-40:]:
            if r["key"][:24] == prev["key"][:24] and fuzz.ratio(r["key"], prev["key"]) >= 93:
                dup = True
                break
        if dup:
            near_dropped += 1
            continue
        kept.append(r)
    stats = {
        "input": len(rows),
        "exact_duplicates_removed": exact_dropped,
        "near_duplicates_removed": near_dropped,
        "kept": len(kept),
    }
    return kept, stats


def assign_splits(df: pd.DataFrame) -> pd.DataFrame:
    # Preserve Adeeba provided test files as test candidates but still re-split globally
    # after de-duplication so the same text cannot appear in train and test.
    y = df["binary_harmful"].astype(int)
    try:
        train_df, rest = train_test_split(df, test_size=0.30, random_state=SEED, stratify=y)
        y_rest = rest["binary_harmful"].astype(int)
        val_df, test_df = train_test_split(rest, test_size=0.50, random_state=SEED, stratify=y_rest)
    except ValueError:
        train_df, rest = train_test_split(df, test_size=0.30, random_state=SEED)
        val_df, test_df = train_test_split(rest, test_size=0.50, random_state=SEED)
    train_df = train_df.copy()
    val_df = val_df.copy()
    test_df = test_df.copy()
    train_df["split"] = "train"
    val_df["split"] = "validation"
    test_df["split"] = "test"
    # Leakage guard: drop any test/val key present in train
    train_keys = set(train_df["key"])
    val_df = val_df[~val_df["key"].isin(train_keys)]
    test_df = test_df[~test_df["key"].isin(train_keys | set(val_df["key"]))]
    return pd.concat([train_df, val_df, test_df], ignore_index=True)


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    parts = {
        "davidson2017": map_davidson(),
        "adeeba2024_train": map_urdu_excel("urdu_train_bullying.xlsx", "adeeba2024_train"),
        "adeeba2024_test": map_urdu_excel("urdu_test_bullying.xlsx", "adeeba2024_test"),
        "roman_urdu_toxic_hf": map_roman_urdu_csv(),
    }
    for name, part in parts.items():
        print(f"{name}: {len(part)} rows after mapping")
        rows.extend(part)
    kept, dup_stats = drop_duplicates(rows)
    if not kept:
        raise SystemExit("No training rows could be prepared. Acquire datasets first.")
    df = pd.DataFrame(kept)
    df = df.dropna(subset=["original_text", "normalized_text"]).reset_index(drop=True)
    df = assign_splits(df)
    csv_out = PROCESSED / "dataset.csv"
    df.to_csv(csv_out, index=False)
    dist = {
        "n": int(len(df)),
        "by_split": df["split"].value_counts().to_dict(),
        "by_language": df["language"].value_counts().to_dict(),
        "by_source": df["source"].value_counts().to_dict(),
        "class_counts": {k: int(df[k].sum()) for k in LABELS if k in df.columns},
        "binary_harmful": int(df["binary_harmful"].sum()),
        "binary_safe": int((df["binary_harmful"] == 0).sum()),
        "duplicates": dup_stats,
        "seed": SEED,
        "note": "Demo comments are not included. Do not treat demo mode as research evidence.",
    }
    (PROCESSED / "dataset_stats.json").write_text(json.dumps(dist, indent=2), encoding="utf-8")
    print(json.dumps(dist, indent=2))


if __name__ == "__main__":
    main()
