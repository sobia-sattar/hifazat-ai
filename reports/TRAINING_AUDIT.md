# Testing and retraining audit

Completed 2026-08-31. All 31 automated tests passed; production frontend build passed; pip check found no broken requirements. Browser visual testing was not completed because of the previously reported browser restriction.

The active model is trained on 66,813 examples. Dataset checksum matches the artifact. Exact normalized keys and processed text have zero overlap across training, validation and test splits; this does not establish the absence of semantic or source leakage. Existing frozen test predictions were re-evaluated without training or tuning on the test set.

## Measured active-model test results

- Harmful/safe accuracy: 93.44% on 14,318 held-out examples.
- Binary F1: 90.56%.
- Observed-category Macro-F1: 63.84%.
- Only HATE_SPEECH and TOXIC have positive and negative evaluation coverage. Six other categories have no positive training examples. Independent gold evaluation and Urdu-script performance are not established.

## New training experiment

Trained a calibrated hybrid word/character SVM on the full training split with C=4, word bigrams and 60,000 features per vectorizer. Thresholds were chosen on validation only. The predeclared promotion rule required improved validation category Macro-F1 and no reduction in binary F1.

| Validation metric | Active model | Candidate |
|---|---:|---:|
| Binary accuracy | 93.65% | 94.15% |
| Binary F1 | 90.88% | 91.39% |
| Harmful recall | 91.17% | 89.39% |
| Category Macro-F1 | 67.55% | 66.09% |

Candidate not promoted: category Macro-F1 declined. Its artifact and machine-readable results are preserved in reports/training_audit.json. Candidate test scores were not used to select the winner. The deployed model remains unchanged. No 100% accuracy claim is supported.

Next substantial improvement requires independently annotated, licensed examples spanning missing harm categories, Urdu script, conversational context, counterexamples and diverse sources. These should include a separate evaluation set never used for tuning. Repeated behavior still requires human-confirmed evidence; a classifier cannot establish a person's habits from isolated comments.
