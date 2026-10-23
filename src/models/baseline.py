"""Sparse independent heads support partially observed source taxonomies."""

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC


def features(kind, max_features=40000, ngram=2, min_df=2):
    word = TfidfVectorizer(
        ngram_range=(1, ngram), min_df=min_df, max_features=max_features, sublinear_tf=True, dtype=np.float32
    )
    char = TfidfVectorizer(
        analyzer="char",
        ngram_range=(3, 5),
        min_df=min_df,
        max_features=max_features,
        sublinear_tf=True,
        dtype=np.float32,
    )
    return FeatureUnion([("word", word), ("char", char)]) if kind == "hybrid" else char if kind == "char" else word


class Baseline:
    def __init__(self, kind="word", algorithm="lr", C=1.0, balanced=True, max_features=40000, ngram=2, min_df=2):
        self.parameters = dict(
            kind=kind,
            algorithm=algorithm,
            C=C,
            balanced=balanced,
            max_features=max_features,
            ngram=ngram,
            min_df=min_df,
        )
        self.vectorizer = features(kind, max_features, ngram, min_df)
        self.heads = []

    def fit(self, texts, labels):
        x = self.vectorizer.fit_transform(texts)
        for y in labels.T:
            known = y >= 0
            values, counts = np.unique(y[known], return_counts=True)
            if len(values) < 2:
                head = DummyClassifier(strategy="constant", constant=int(values[0]) if len(values) else 0)
                head.fit(x[:1], [int(values[0]) if len(values) else 0])
            else:
                weight = "balanced" if self.parameters["balanced"] else None
                if self.parameters["algorithm"] == "svm":
                    base = LinearSVC(C=self.parameters["C"], class_weight=weight, random_state=42, max_iter=10000)
                    head = (
                        CalibratedClassifierCV(base, cv=min(3, int(counts.min())), method="sigmoid")
                        if counts.min() >= 2
                        else LogisticRegression(
                            C=self.parameters["C"], class_weight=weight, solver="liblinear", random_state=42
                        )
                    )
                else:
                    head = LogisticRegression(
                        C=self.parameters["C"], class_weight=weight, solver="liblinear", max_iter=1000, random_state=42
                    )
                head.fit(x[known], y[known])
            self.heads.append(head)
        return self

    def predict_proba(self, texts):
        x = self.vectorizer.transform(texts)
        return np.column_stack(
            [
                h.predict_proba(x)[:, list(h.classes_).index(1)] if 1 in h.classes_ else np.zeros(x.shape[0])
                for h in self.heads
            ]
        )

    def explain(self, text, index, limit=12):
        x = self.vectorizer.transform([text])
        head = self.heads[index]
        if hasattr(head, "coef_"):
            weights = head.coef_[0]
        elif hasattr(head, "calibrated_classifiers_"):
            weights = np.mean([c.estimator.coef_[0] for c in head.calibrated_classifiers_], axis=0)
        else:
            return []
        values = x.multiply(weights).tocoo()
        names = self.vectorizer.get_feature_names_out()
        pairs = sorted(zip(values.col, values.data), key=lambda p: abs(p[1]), reverse=True)[:limit]
        return [dict(feature=names[i], contribution=float(v)) for i, v in pairs]
