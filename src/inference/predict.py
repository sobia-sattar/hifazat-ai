from src.preprocessing.calibration import is_benign_intent
import argparse
import json
import joblib
import numpy as np
from src.utils.common import ROOT, LABELS, digest
from src.preprocessing.text import preprocess, language_metadata


class Predictor:
    def __init__(self, directory=None):
        directory = ROOT / "artifacts" if directory is None else directory
        selection = json.loads((directory / "selected.json").read_text())
        path = (directory / selection["path"]).resolve()
        if not path.is_relative_to(directory.resolve()) or digest(path) != selection["sha256"]:
            raise ValueError("Artifact path or checksum validation failed")
        # Only load trusted local artifacts. Pickle/joblib is not safe for untrusted uploads.
        self.bundle = joblib.load(path)
        if self.bundle["labels"] != LABELS or len(self.bundle["thresholds"]) != len(LABELS) + 1:
            raise ValueError("Invalid artifact schema")

    def predict(self, texts, explain=False):
        if not texts or any(not isinstance(t, str) or not t.strip() or len(t) > 8000 for t in texts):
            raise ValueError("Provide non-empty texts of at most 8000 characters")
        processed = [preprocess(t) for t in texts]
        if any(not t for t in processed):
            raise ValueError("Text is empty after preprocessing")
        scores = self.bundle["model"].predict_proba(processed)
        if not np.isfinite(scores).all():
            raise ValueError("Non-finite model predictions")
        thresholds = self.bundle["thresholds"]
        out = []
        for text, clean, p in zip(texts, processed, scores):
            p = np.array(p, dtype=float)
            if is_benign_intent(text):
                p[-1] = min(float(p[-1]) * 0.15, 0.08)
                for j in range(len(p) - 1):
                    p[j] = min(float(p[j]) * 0.15, 0.08)
            active = [label for j, label in enumerate(LABELS) if p[j] >= thresholds[j]]
            binary = "HARMFUL" if p[-1] >= thresholds[-1] else "SAFE" 
            row = dict(
                text=text,
                processed_text=clean,
                **language_metadata(text),
                binary_prediction=binary,
                harmful_probability=float(p[-1]),
                labels=active or ["SAFE"],
                binary_threshold=thresholds[-1],
                category_binary_disagreement=(bool(active) != (binary == "HARMFUL")),
                categories={
                    label: dict(
                        probability=float(p[j]),
                        threshold=thresholds[j],
                        supported=self.bundle["validation_metrics"]["per_class"][label]["evaluable"],
                    )
                    for j, label in enumerate(LABELS)
                },
                model_version=self.bundle["version"],
                notice="Research system — predictions are not definitive moderation decisions.",
            )
            if explain:
                index = int(np.argmax(p[:-1])) if active else len(LABELS)
                row["explanation"] = dict(
                    label=LABELS[index] if index < len(LABELS) else "BINARY_HARMFUL",
                    features=self.bundle["model"].explain(clean, index),
                    warning="Feature importance is not proof of causality.",
                )
            out.append(row)
        return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True)
    print(json.dumps(Predictor().predict([p.parse_args().text], explain=True)[0], ensure_ascii=False, indent=2))
