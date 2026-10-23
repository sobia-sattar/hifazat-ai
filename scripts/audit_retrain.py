"""One predeclared validation-only challenger; never tune on test scores."""
from datetime import datetime, timezone
import json
import joblib
import numpy as np
import pandas as pd
from src.inference.predict import Predictor
from src.models.baseline import Baseline
from src.evaluation.metrics import evaluate, binary_metrics, optimize_thresholds
from src.utils.common import ROOT, LABELS, digest, write_json


def main():
    current = Predictor().bundle
    source = ROOT / 'data/processed/research.csv'
    frame = pd.read_csv(source)
    assert digest(source) == current['dataset_version'], 'Dataset changed since training'
    assert frame.record_id.is_unique, 'Duplicate record IDs'
    overlaps = {}
    for column in ['key', 'processed_text']:
        overlaps[column] = int((frame.groupby(column).split.nunique() > 1).sum())
    assert not any(overlaps.values()), f'Cross-split overlap: {overlaps}'
    train = frame[frame.split == 'train']
    val = frame[frame.split == 'validation']
    ytrain = np.c_[train[LABELS].values, train.binary_harmful.values]
    yval = np.c_[val[LABELS].values, val.binary_harmful.values]
    version = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    report = {'dataset_sha256': digest(source), 'splits': frame.split.value_counts().to_dict(),
              'exact_cross_split_overlap': overlaps,
              'positive_training_support': {label: int((train[label] == 1).sum()) for label in LABELS},
              'limitations': 'Exact checks do not rule out semantic/source leakage. No independent human gold evaluation. No positive coverage for six heads.',
              'selection_rule': 'Promote only if validation macro F1 improves and validation binary F1 does not decrease.',
              'current_model': current['model_name'], 'current_parameters': current['model'].parameters}
    write_json(ROOT / 'reports/training_audit.json', report)
    params = dict(kind='hybrid', algorithm='svm', C=4.0, balanced=True, max_features=60000, ngram=2)
    print('Split audit passed. Training challenger on', len(train), 'rows:', params, flush=True)
    model = Baseline(**params).fit(train.processed_text, ytrain)
    print('Evaluating validation split only', flush=True)
    p = model.predict_proba(val.processed_text)
    thresholds = optimize_thresholds(yval, p)
    metrics = evaluate(yval[:, :-1], p[:, :-1], thresholds[:-1])
    binary = binary_metrics(yval[:, -1], p[:, -1], thresholds[-1])
    oldp = current['model'].predict_proba(val.processed_text)
    oldmetrics = evaluate(yval[:, :-1], oldp[:, :-1], np.array(current['thresholds'][:-1]))
    oldbinary = binary_metrics(yval[:, -1], oldp[:, -1], current['thresholds'][-1])
    promote = metrics['macro_f1'] > oldmetrics['macro_f1'] and binary['f1'] >= oldbinary['f1']
    bundle = dict(model=model, model_name='hybrid_svm_audit_60k_C4', labels=LABELS,
                  thresholds=thresholds.tolist(), version=version, validation_metrics=metrics,
                  validation_binary=binary, dataset_version=digest(source), train_size=len(train),
                  training_date=datetime.now(timezone.utc).isoformat(), hyperparameters=model.parameters,
                  preprocessing_version='conservative-v2', profile='standard')
    artifact = ROOT / 'artifacts/models' / f'{version}.joblib'
    joblib.dump(bundle, artifact)
    write_json(ROOT / 'artifacts/metadata' / f'{version}.json', {k:v for k,v in bundle.items() if k != 'model'})
    report.update(candidate_parameters=params, candidate_validation_macro_f1=metrics['macro_f1'],
                  candidate_validation_binary=binary, current_validation_macro_f1=oldmetrics['macro_f1'],
                  current_validation_binary=oldbinary, promoted=promote, candidate_artifact=str(artifact))
    if promote:
        write_json(ROOT / 'artifacts' / f'selection_before_{version}.json', json.loads((ROOT / 'artifacts/selected.json').read_text()))
        write_json(ROOT / 'artifacts/selected.json', dict(path=f'models/{version}.joblib', sha256=digest(artifact), version=version))
        write_json(ROOT / 'artifacts/thresholds.json', dict(zip(LABELS + ['BINARY_HARMFUL'], thresholds.tolist())))
    write_json(ROOT / 'reports/training_audit.json', report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
