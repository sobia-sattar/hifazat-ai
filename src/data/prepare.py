"""Strict source schemas, partial labels, duplicate quarantine and multilabel splitting."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
import numpy as np
import pandas as pd
import yaml
from datasketch import MinHash, MinHashLSH
from iterstrat.ml_stratifiers import MultilabelStratifiedShuffleSplit
from src.utils.common import ROOT, LABELS, digest, write_json
from src.preprocessing.text import preprocess, language_metadata


def map_label(source, value, mappings):
    key = str(value).strip()
    if key not in mappings[source]:
        raise ValueError(f"Unknown source label: {source}:{key}")
    mapped = mappings[source][key]
    if mapped.get("SAFE"):
        return [0] * len(LABELS)
    return [mapped.get(label, -1) for label in LABELS]


def key(text):
    return re.sub(r"\W+", " ", preprocess(text), flags=re.UNICODE).strip()


def shingles(text):
    return {text[i : i + 5] for i in range(max(1, len(text) - 4))}


def deduplicate(frame, threshold=0.85):
    frame = frame.copy()
    frame["key"] = frame.processed_text.map(key)
    frame = frame[frame.key.ne("")].reset_index(drop=True)
    # Remove every member of a conflicting exact-label group, never arbitrarily keep a label.
    conflicts = frame.groupby("key")[LABELS].nunique().max(axis=1)
    conflict_keys = set(conflicts[conflicts > 1].index)
    conflict_count = int(frame.key.isin(conflict_keys).sum())
    frame = frame[~frame.key.isin(conflict_keys)].drop_duplicates("key").reset_index(drop=True)
    lsh = MinHashLSH(threshold=0.65, num_perm=64)
    sets, keep = {}, []
    near = 0
    for i, text in enumerate(frame.key):
        grams = shingles(text)
        mh = MinHash(num_perm=64, seed=42)
        mh.update_batch([g.encode("utf-8") for g in sorted(grams)])
        candidates = lsh.query(mh)
        duplicate = any(len(grams & sets[j]) / len(grams | sets[j]) >= threshold for j in candidates)
        # Index removed rows too, so transitive variants never survive into another split.
        lsh.insert(str(i), mh)
        sets[str(i)] = grams
        if duplicate:
            near += 1
        else:
            keep.append(i)
    out = frame.iloc[keep].reset_index(drop=True)
    return out, dict(
        conflicting_exact_rows=conflict_count,
        near_removed=near,
        kept=len(out),
        method="64-permutation MinHash candidates + exact 5-gram Jaccard",
        threshold=threshold,
        limitation="Probabilistic candidate recall; not a proof of no semantic duplicates.",
    )


def split_data(df, mode="iterative", holdout=None):
    df = df.copy().reset_index(drop=True)
    if mode in {"source", "language"}:
        column = "source" if mode == "source" else "language"
        test = np.flatnonzero(df[column].eq(holdout))
        pool = np.flatnonzero(~df[column].eq(holdout))
        if not len(test) or len(pool) < 4:
            raise ValueError("Disjoint split requires a populated holdout and training pool")
        splitter = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=0.17647, random_state=42)
        a, b = next(splitter.split(pool, (df.iloc[pool][LABELS].values == 1).astype(int)))
        train, val = pool[a], pool[b]
    elif mode == "time":
        if "timestamp" not in df or df.timestamp.isna().any():
            raise ValueError("Time split requires complete timestamps")
        order = pd.to_datetime(df.timestamp, utc=True, errors="raise").sort_values().index.to_numpy()
        train, val, test = np.split(order, [int(0.7 * len(df)), int(0.85 * len(df))])
    else:
        y = np.c_[(df[LABELS].values == 1).astype(int), (df[LABELS].values == 0).astype(int)]
        splitter = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=0.3, random_state=42)
        train, rest = next(splitter.split(df, y))
        splitter = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=0.5, random_state=42)
        a, b = next(splitter.split(rest, y[rest]))
        val, test = rest[a], rest[b]
    for name, ids in [("train", train), ("validation", val), ("test", test)]:
        df.loc[ids, "split"] = name
    return df


def main(mode="iterative", holdout=None):
    config = yaml.safe_load((ROOT / "configs/data.yaml").read_text())
    mappings = yaml.safe_load((ROOT / "configs/label_mapping.yaml").read_text())
    rows, registry = [], []
    for source in config["sources"]:
        p = ROOT / source["path"]
        record = dict(source, date_acquired=source.get("date_acquired", "unknown (pre-existing file)"), records=0)
        if not source["approved"] or not p.exists():
            record["status"] = "license_unverified" if not source["approved"] else "missing"
            registry.append(record)
            continue
        if not source.get("license_evidence") or source["id"] not in mappings:
            raise ValueError("Approved source needs license evidence and explicit mapping")
        df = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
        record.update(
            records=len(df),
            sha256=digest(p),
            status="used",
            original_labels=json.dumps(sorted(df[source["label_column"]].dropna().unique().tolist())),
            mapped_labels=json.dumps(mappings[source["id"]]),
        )
        registry.append(record)
        for text, label in zip(df[source["text_column"]], df[source["label_column"]]):
            processed = preprocess(text)
            if not processed:
                continue
            labels = map_label(source["id"], label, mappings)
            row = dict(
                raw_text=text,
                processed_text=processed,
                source=source["id"],
                binary_harmful=int(1 in labels),
                **language_metadata(text),
            )
            row.update(zip(LABELS, labels))
            rows.append(row)
    if not rows:
        raise ValueError("No approved datasets available")
    frame, audit = deduplicate(pd.DataFrame(rows))
    audit["input_rows"] = len(rows)
    # External candidates must be genuinely separate. Existing data/gold came from internal test.
    external = ROOT / "data/external/gold.csv"
    if external.exists():
        ext = pd.read_csv(external)
        combined = pd.concat(
            [ext.assign(processed_text=ext.text.map(preprocess), **{label: -1 for label in LABELS}), frame],
            ignore_index=True,
        )
        cleaned, _ = deduplicate(combined)
        frame = cleaned[cleaned.source.notna()].copy()
    frame = split_data(frame, mode, holdout)
    if frame.groupby("key").split.nunique().max() != 1:
        raise AssertionError("Cross-split normalized duplicate")
    frame["record_id"] = frame.key.map(lambda s: hashlib.sha256(s.encode()).hexdigest())
    out = ROOT / "data/processed/research.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    pd.DataFrame(registry).to_csv(ROOT / "data/dataset_registry.csv", index=False)
    audit.update(normalized_cross_split_duplicates=0, external_evaluation="NOT COMPLETED", split_mode=mode)
    write_json(ROOT / "reports/leakage_report.json", audit)
    stats = dict(
        n=len(frame),
        dataset_version=digest(out),
        by_split=frame.split.value_counts().to_dict(),
        by_language=frame.language.value_counts().to_dict(),
        by_source=frame.source.value_counts().to_dict(),
        positive_counts={label: int((frame[label] == 1).sum()) for label in LABELS},
        known_counts={label: int((frame[label] >= 0).sum()) for label in LABELS},
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    write_json(ROOT / "reports/dataset_statistics.json", stats)
    pd.DataFrame(
        [
            dict(label=label, positive=stats["positive_counts"][label], known=stats["known_counts"][label])
            for label in LABELS
        ]
    ).to_csv(ROOT / "reports/dataset_statistics.csv", index=False)
    print(json.dumps(stats), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["iterative", "source", "language", "time"], default="iterative")
    parser.add_argument("--holdout")
    args = parser.parse_args()
    main(args.split, args.holdout)
