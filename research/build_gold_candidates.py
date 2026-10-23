"""Create an INTERNAL reannotation queue from the historical held-out test split.

This is NOT an independent external test set. The output is a candidate queue, not a gold set. Human annotators must complete
both annotations and adjudication before it is used for research metrics.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "dataset.csv"
OUTPUT = ROOT / "data" / "gold" / "gold_candidates_1000.csv"


def main() -> None:
    df = pd.read_csv(PROCESSED).fillna("")
    held_out = df[df["split"] == "test"].copy()
    if len(held_out) < 1000:
        raise SystemExit("The held-out split contains fewer than 1,000 comments.")
    held_out["language_group"] = held_out.apply(
        lambda row: "Code-mixed" if int(row.get("is_code_mixed") or 0) else str(row.get("language") or "Unknown"),
        axis=1,
    )
    # Stratified sample by language group and binary harmful status.
    groups = held_out["language_group"] + "|" + held_out["binary_harmful"].astype(str)
    sampled = held_out.groupby(groups, group_keys=False).apply(
        lambda part: part.sample(n=max(1, round(1000 * len(part) / len(held_out))), random_state=42)
    ).drop_duplicates(subset=["key"])
    if len(sampled) < 1000:
        remaining = held_out[~held_out["key"].isin(sampled["key"])].sample(
            n=1000 - len(sampled), random_state=42
        )
        sampled = pd.concat([sampled, remaining], ignore_index=True)
    sampled = sampled.head(1000)
    output = pd.DataFrame(
        {
            "id": [f"G{index:04d}" for index in range(1, len(sampled) + 1)],
            "text": sampled["original_text"].tolist(),
            "primary_label": "",
            "language": sampled["language"].tolist(),
            "script": sampled["script"].tolist(),
            "annotator_1": "",
            "annotator_2": "",
            "adjudicated_label": "",
            "rationale": "",
        }
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT, index=False)
    print(f"Wrote {len(output)} unlabeled candidates to {OUTPUT}")
    print("Do not report metrics until annotators and an adjudicator complete the labels.")


if __name__ == "__main__":
    main()
