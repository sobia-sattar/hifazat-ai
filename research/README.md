# Research Workflow

## Reproduce the dataset and baseline

Run from `D:\BullyDetector`:

```powershell
.\.venv\Scripts\Activate.ps1
python research/acquire_data.py
python research/prepare_data.py
$env:BULLYLENS_MAX_TRAIN="25171"
python research/train.py
```

The training command compares word TF-IDF, character n-gram, hybrid TF-IDF, and calibrated linear models. The serving model is selected by validation Macro-F1. The test split is evaluated once after model selection.

## External evaluation

1. Generate a 1,000-item external annotation queue:

```powershell
python research/build_gold_candidates.py
```

This creates `data/gold/gold_candidates_1000.csv`. It is not a gold set until two annotators and an adjudicator complete it using `research/ANNOTATION_GUIDELINES.md`. Copy the completed file to `data/gold/gold_annotations.csv`.

2. Annotate `data/gold/gold_annotations.csv` using `research/ANNOTATION_GUIDELINES.md`.
3. Fill `annotator_1`, `annotator_2`, and `adjudicated_label`.
4. Remove duplicates against the training data before adding more rows.
5. Run:

```powershell
$env:PYTHONPATH="backend"
python research/evaluate_gold.py
```

Do not report the internal test score as real-world accuracy. Report macro-F1 and per-language/per-class results from the adjudicated external gold set. Include the dataset sources, label mapping, annotation agreement, confidence intervals where possible, and limitations.

## XLM-RoBERTa comparison

Install the transformer dependencies with storage directed to the D drive if needed:

```powershell
$env:PIP_CACHE_DIR="D:\BullyDetector\.pip-cache"
$env:HF_HOME="D:\BullyDetector\.hf-cache"
pip install torch transformers sentencepiece
$env:BULLYLENS_TRAIN_TRANSFORMER="1"
$env:BULLYLENS_MAX_TRAIN="25171"
python research/train.py
```

The script records XLM-R validation metrics and checkpoint metadata in `models/metrics.json` and `research/results/latest.json`. The CPU sklearn model remains the serving model unless a separate transformer serving adapter is implemented and validated.

## Current limitations

- The available Roman Urdu corpus was not downloaded, so Roman Urdu coverage is limited.
- The source corpora use different taxonomies and are mapped conservatively; Davidson offensive text is not labeled as cyberbullying.
- There are no sexual-harassment examples in the current prepared corpus.
- The current model is a CPU-friendly sklearn baseline. A multilingual transformer such as XLM-R should be compared only after the external gold set exists.
- Production keyword/context safeguards are evaluated separately from model-only scores and must not be presented as learned model performance.
