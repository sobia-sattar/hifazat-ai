"""Predeclared binary experiment. No test-driven tuning or score fabrication."""
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from src.models.baseline import features
from src.models.nb_linear import LogCountRatio
from src.inference.predict import Predictor
from src.evaluation.metrics import binary_metrics
from src.utils.common import ROOT, digest, write_json


def main():
    current = Predictor().bundle
    path = ROOT / 'data/processed/research.csv'
    assert digest(path) == current['dataset_version']
    frame = pd.read_csv(path)
    train = frame[frame.split == 'train']
    val = frame[frame.split == 'validation']
    assert not (set(train.processed_text) & set(val.processed_text))
    version = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder = ROOT / 'experiments' / ('accuracy_' + version)
    folder.mkdir(parents=True)
    protocol = dict(target_accuracy=.96, train_rows=len(train), validation_rows=len(val),
                    selection='Max validation accuracy with recall and F1 at least incumbent validation levels; no test tuning.',
                    candidate='Hybrid TF-IDF 100k features per branch, word bigrams, training-only log-count ratio, logistic regression C=1.',
                    dataset_sha256=digest(path), scope='Binary harmful vs safe only; no new category supervision.')
    write_json(folder / 'protocol.json', protocol)
    print('Training binary challenger on', len(train), 'rows', flush=True)
    model = Pipeline([('features', features('hybrid', max_features=100000, ngram=2)),
                      ('ratio', LogCountRatio()),
                      ('classifier', LogisticRegression(C=1, solver='liblinear', max_iter=2000, random_state=42))])
    model.fit(train.processed_text, train.binary_harmful.to_numpy())
    print('Scoring validation, not test', flush=True)
    scores = model.predict_proba(val.processed_text)[:, 1]
    incumbent_scores = current['model'].predict_proba(val.processed_text)[:, -1]
    incumbent = binary_metrics(val.binary_harmful.to_numpy(), incumbent_scores, current['thresholds'][-1])
    candidates = []
    for threshold in np.linspace(.1, .9, 81):
        metrics = binary_metrics(val.binary_harmful.to_numpy(), scores, threshold)
        candidates.append((float(threshold), metrics))
    eligible = [(t,m) for t,m in candidates if m['recall'] >= incumbent['recall'] and m['f1'] >= incumbent['f1']]
    best = max(eligible, key=lambda pair: pair[1]['accuracy']) if eligible else None
    unconstrained = max(candidates, key=lambda pair: pair[1]['accuracy'])
    report = dict(**protocol, incumbent_validation=incumbent,
                  candidate_validation=best[1] if best else None, selected_threshold=best[0] if best else None,
                  unconstrained_validation=unconstrained[1], unconstrained_threshold=unconstrained[0],
                  target_met_on_validation=bool(best and best[1]['accuracy'] >= .96),
                  deployment='Unchanged: research candidate, not installed into multi-category serving model.',
                  test_evaluation='Not run: target not demonstrated on validation.')
    # Preserve the experiment without changing the app or claiming a new test result.
    joblib.dump(model, folder / 'binary_candidate.joblib')
    np.savez_compressed(folder / 'validation_predictions.npz', scores=scores, record_id=val.record_id.to_numpy(dtype=str))
    if report['target_met_on_validation']:
        test = frame[frame.split == 'test']
        report['test_evaluation'] = binary_metrics(test.binary_harmful.to_numpy(), model.predict_proba(test.processed_text)[:, 1], best[0])
    write_json(folder / 'result.json', report)
    write_json(ROOT / 'reports/accuracy_target_experiment.json', report)
    print(report, flush=True)


if __name__ == '__main__':
    main()
