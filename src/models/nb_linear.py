"""Binary sparse text challenger; feature weighting is fitted on training only."""
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


class LogCountRatio(BaseEstimator, TransformerMixin):
    def fit(self, x, y):
        positive = np.asarray(x[y == 1].sum(axis=0)).ravel() + 1
        negative = np.asarray(x[y == 0].sum(axis=0)).ravel() + 1
        self.ratio_ = np.log((positive / positive.sum()) / (negative / negative.sum()))
        return self

    def transform(self, x):
        return x.multiply(self.ratio_).tocsr()
