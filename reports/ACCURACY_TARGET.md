# Accuracy target experiment

Target: 96% binary harmful/safe accuracy. The measured result did not reach that target.

A new binary classifier was trained on all 66,813 training examples using hybrid word/character TF-IDF, training-only log-count feature weighting and logistic regression. The validation threshold was selected to maximize accuracy while preserving at least the incumbent validation recall and F1. The selected threshold (0.34) was frozen before one held-out test evaluation. No test-based tuning was performed.

| Metric | Active model | Research candidate |
|---|---:|---:|
| Validation accuracy | 93.65% | 95.30% |
| Test accuracy | 93.44% | 94.64% |
| Test binary F1 | 90.56% | 92.12% |
| Test harmful recall | 90.64% | 90.30% |

Candidate test size: 14,318 examples. This is internal held-out performance, not guaranteed real-world performance. No improvement in category coverage is claimed. The candidate is saved as a separate binary research model; it has not replaced the multi-category application model. Dashboard metrics remain those of the active model. All 31 existing tests passed.

Artifacts, exact metrics and provenance: accuracy_target_experiment.json and its referenced experiment directory. Achieving a stronger defensible result requires better annotated data and further independent validation, not generating a requested percentage.
