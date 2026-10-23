> HISTORICAL / PROJECT-REPORTED: This paper describes an earlier pipeline. Its scores are not independently reproduced v2 results. See ../reports/EXPERIMENT_SUMMARY.md for current evidence.

# BullyLens-X: Multilingual Cyberbullying and Harmful Content Detection in English, Urdu, Roman Urdu, and Code-Mixed Text

## Abstract

This study presents BullyLens-X, a multilingual machine-learning system for detecting cyberbullying and harmful online comments in English, Urdu, Roman Urdu, and code-mixed text. The dataset combines the Davidson hate-speech corpus with the Urdu Cyberbullying Corpus. After cleaning, normalization, duplicate removal, and label harmonization, the final dataset contains 35,959 comments. A TF-IDF representation with word-level bigrams was combined with a calibrated linear Support Vector Machine using one-versus-rest classification. Four models were compared using validation Macro-F1. The selected model, TF-IDF Linear SVM, achieved a validation Macro-F1 of 0.5988 and an internal test Macro-F1 of 0.5981. For the binary harmful-versus-safe task, it achieved an F1-score of 0.9365, precision of 0.9389, and recall of 0.9342. The results indicate strong performance for broad harmful-content detection but weaker performance for rare and semantically dependent categories such as hate speech and threats. The study highlights the importance of external human-annotated evaluation, especially for low-resource Urdu and Roman Urdu content.

## 1. Introduction

Social-media platforms allow users to communicate quickly across linguistic and cultural boundaries. However, these platforms also enable insults, harassment, hate speech, threats, and cyberbullying to spread rapidly. Automatic harmful-content detection can support content moderation, online safety, and large-scale analysis of abusive communication.

Most existing harmful-content detection systems focus primarily on English text. This creates a significant limitation for multilingual communities where users communicate using Urdu, Roman Urdu, English, and code-mixed language. Roman Urdu is particularly challenging because Urdu is written using the Latin alphabet, spelling is inconsistent, and users frequently combine Urdu and English in the same sentence.

Cyberbullying detection is also different from simple offensive-language detection. A single insult is not necessarily cyberbullying. Cyberbullying normally involves targeted, repeated, socially amplified, or context-dependent abuse. Therefore, a reliable system must distinguish between general toxicity, direct insults, harassment, hate speech, threats, and cyberbullying.

This research develops a multilingual classification pipeline for identifying harmful online comments. The system uses publicly available datasets, conservative label mapping, language and script detection, Roman Urdu normalization, duplicate removal, TF-IDF feature extraction, and calibrated linear classifiers.

The research distinguishes two evaluation tasks:

1. Binary harmful-content detection: harmful versus safe.
2. Detailed category classification: identifying the specific harmful categories.

This distinction is important because a model can perform well at detecting whether content is harmful while still struggling to identify the exact type of harm.

## 2. Research Gap

Existing research has several limitations:

- Many datasets focus only on English.
- Urdu and Roman Urdu resources are smaller and less standardized.
- Offensive language is often treated as equivalent to cyberbullying.
- Code-mixed language is frequently ignored.
- Rare categories such as threats and sexual harassment are underrepresented.
- Reported accuracy can be misleading when the dataset is imbalanced.
- Many studies do not report Macro-F1, per-class recall, or language-specific results.
- Different datasets use different taxonomies, making direct comparison difficult.
- Internal test performance is sometimes reported as real-world performance without an external human-annotated test set.

This study addresses these gaps by combining English and Urdu resources, including language and script metadata, identifying code-mixed comments, separating cyberbullying from general insults and toxicity, using a unified taxonomy, and reporting both aggregate and language-specific results.

## 3. Research Questions

### RQ1

How accurately can a TF-IDF-based machine-learning model detect harmful content in multilingual English, Urdu, Roman Urdu, and code-mixed comments?

### RQ2

Which model performs best for multilingual harmful-content classification when evaluated using validation Macro-F1?

### RQ3

How does model performance vary across cyberbullying, harassment, hate speech, threats, insults, toxicity, and other harmful categories?

### RQ4

How does performance differ across English, Urdu, Roman Urdu, and code-mixed text?

### RQ5

What effect do class imbalance, limited Roman Urdu data, missing sexual-harassment examples, and inconsistent source taxonomies have on classification performance?

### RQ6

Can a binary harmful-versus-safe classifier achieve stronger performance than a detailed category-level classifier?

## 4. Dataset

The dataset was constructed from publicly available research corpora.

| Source | Language | Original labels | Records retained |
|---|---|---|---:|
| Davidson et al. hate-speech dataset | English | Hate speech, offensive language, neither | 24,654 |
| Adeeba Urdu Cyberbullying Corpus train | Urdu | Source-provided labels | 9,176 |
| Adeeba Urdu Cyberbullying Corpus test | Urdu | Source-provided labels | 2,129 |
| Roman Urdu Toxic Corpus | Roman Urdu | Toxic and non-toxic | 0 |
| **Total** | Multilingual | Harmonized taxonomy | **35,959** |

The Roman Urdu corpus listed in the project registry was unavailable at acquisition time because the referenced download URL returned HTTP 404. Consequently, Roman Urdu examples in the final dataset are limited and should not be interpreted as a representative Roman Urdu corpus.

### 4.1 Dataset Splits

The final dataset contains 35,959 comments:

| Split | Records | Percentage |
|---|---:|---:|
| Training | 25,171 | 70% |
| Validation | 5,394 | 15% |
| Test | 5,394 | 15% |
| **Total** | **35,959** | **100%** |

The split used random seed 42. Stratification was performed using the binary harmful-versus-safe label. Exact and near duplicates were removed before splitting.

### 4.2 Language Distribution

| Language category | Records |
|---|---:|
| English | 13,325 |
| English-Roman Urdu | 10,240 |
| Urdu | 9,826 |
| Mixed | 1,409 |
| Unknown | 774 |
| Roman Urdu | 319 |
| English-Urdu | 66 |

The English-Roman Urdu, Mixed, and English-Urdu groups were combined into the broader code-mixed evaluation group.

### 4.3 Label Distribution

| Label | Count |
|---|---:|
| SAFE | 11,843 |
| CYBERBULLYING | 3,201 |
| HARASSMENT | 1,006 |
| HATE_SPEECH | 1,422 |
| THREAT | 88 |
| INSULT | 20,546 |
| TOXIC | 23,343 |
| SEXUAL_HARASSMENT | 0 |
| OTHER_HARMFUL | 1,142 |

The label counts can exceed the number of records because harmful labels are represented using multilabel vectors. One comment can therefore receive more than one harmful label, such as CYBERBULLYING and TOXIC.

The final dataset contains 24,116 harmful comments and 11,843 safe comments. The preparation process started with 37,167 records, removed 1,116 exact duplicates and 88 near duplicates, and retained 35,959 records.

## 5. Label Definitions

- **SAFE:** Content without abuse, threats, hate, harassment, sexual harassment, or targeted bullying.
- **INSULT:** A direct insult or name-calling without evidence of repeated or coordinated targeting.
- **HARASSMENT:** Unwanted targeted abuse, humiliation, or persistent hostile contact.
- **CYBERBULLYING:** Repeated, targeted, or socially amplified abuse against a person or group in an online context.
- **HATE_SPEECH:** An attack, dehumanization, or hostile statement directed at a protected group based on identity.
- **THREAT:** A stated or implied intention to cause harm.
- **SEXUAL_HARASSMENT:** Unwanted sexual remarks, sexual requests, or sexualized targeting.
- **OTHER_HARMFUL:** Harmful content that does not fit the other defined categories.
- **TOXIC:** A broad harmful-content category used by source datasets for toxic, offensive, profane, or abusive language.

## 6. Methodology

### 6.1 Data Acquisition and Label Harmonization

The system acquired the Davidson hate-speech dataset, the Adeeba Urdu Cyberbullying Corpus training data, and the Adeeba Urdu Cyberbullying Corpus test data. An optional Roman Urdu toxicity dataset was also registered but was unavailable.

Because the source datasets use different taxonomies, their labels were conservatively mapped into the BullyLens-X taxonomy. Davidson hate-speech examples were mapped to HATE_SPEECH and TOXIC. Davidson offensive-language examples were mapped to INSULT and TOXIC. Davidson neutral examples were mapped to SAFE. Urdu bullying examples were mapped to CYBERBULLYING, TOXIC, or other harmful categories according to their source labels.

Offensive language was not automatically mapped to cyberbullying because offensive language and cyberbullying are not equivalent concepts.

### 6.2 Text Preprocessing

The preprocessing pipeline performed the following operations:

1. Removed missing and empty text.
2. Normalized text formatting.
3. Detected language and writing script.
4. Identified code-mixed comments.
5. Applied Roman Urdu normalization to Latin-script Urdu-like text.
6. Generated normalized text keys for duplicate detection.
7. Removed exact duplicates.
8. Removed highly similar near duplicates.
9. Created binary harmful-versus-safe labels.
10. Created multilabel category vectors.

### 6.3 Duplicate Removal and Leakage Control

The pipeline received 37,167 records. It removed 1,116 exact duplicates and 88 near duplicates. Near duplicates were identified using normalized text and fuzzy string similarity with a 93% similarity threshold for the local comparison procedure.

The duplicate-removal process was performed before dataset splitting to reduce the chance that the same or nearly identical comment would appear in both training and evaluation data.

### 6.4 Feature Extraction

The main model used word-level Term Frequency-Inverse Document Frequency, or TF-IDF. The model used unigrams and bigrams, a minimum document frequency of 2, a maximum vocabulary size of 40,000 features, and sublinear term-frequency scaling.

Language and code-mixing tags were appended to the text, including:

- `__LANG_English__`
- `__LANG_Urdu__`
- `__LANG_Roman_Urdu__`
- `__CODEMIX__`

TF-IDF gives greater weight to terms that are important in an individual comment but less common throughout the corpus.

### 6.5 Classification Model

The selected classifier was a calibrated Linear Support Vector Machine. It used one-versus-rest classification, balanced class weights, sigmoid probability calibration, a maximum of 2,000 optimization iterations, and random seed 42.

One-versus-rest classification trains one binary classifier for each label. Each classifier estimates whether a comment belongs to its assigned category.

### 6.6 Compared Models

Four models were compared:

1. Word TF-IDF with Logistic Regression.
2. Word TF-IDF with calibrated Linear SVM.
3. Character n-gram TF-IDF with calibrated Linear SVM.
4. Hybrid word and character TF-IDF with Logistic Regression.

The serving model was selected using validation Macro-F1. The test set was evaluated after model selection.

## 7. Evaluation Metrics

### Accuracy

Accuracy is the proportion of correct predictions:

$$Accuracy = (TP + TN) / (TP + TN + FP + FN)$$

In this project, accuracy refers to the binary harmful-versus-safe task.

### Precision

Precision measures how many predicted harmful comments were actually harmful:

$$Precision = TP / (TP + FP)$$

### Recall

Recall measures how many actual harmful comments were detected:

$$Recall = TP / (TP + FN)$$

### F1-Score

The F1-score is the harmonic mean of precision and recall:

$$F1 = 2 * (Precision * Recall) / (Precision + Recall)$$

### Macro-F1

Macro-F1 calculates F1 separately for each class and gives every class equal importance:

$$Macro-F1 = (1/K) * sum(F1_k)$$

This makes Macro-F1 useful when classes are imbalanced.

### Weighted F1

Weighted F1 weights each class according to its number of examples. It is strongly influenced by common categories such as TOXIC and INSULT.

### Support

Support is the number of true examples belonging to a class.

### False Positive and False Negative

A false positive occurs when safe content is classified as harmful. A false negative occurs when harmful content is classified as safe.

## 8. Results

### 8.1 Model Comparison

| Model | Validation Macro-F1 | Accuracy | Precision | Recall | Weighted F1 |
|---|---:|---:|---:|---:|---:|
| Word TF-IDF Logistic Regression | 0.5711 | 0.8626 | 0.8470 | 0.9704 | 0.8580 |
| Word TF-IDF Linear SVM | **0.5988** | 0.9105 | 0.9324 | 0.9342 | 0.8693 |
| Character n-gram Linear SVM | 0.5782 | 0.9118 | 0.9383 | 0.9295 | 0.8700 |
| Hybrid word-character Logistic Regression | 0.5905 | 0.8856 | 0.8748 | 0.9679 | 0.8704 |

The Word TF-IDF Linear SVM was selected because it achieved the highest validation Macro-F1 of 0.5988.

### 8.2 Overall Internal Test Results

The selected model was evaluated on 5,394 internal test comments.

| Metric | Result |
|---|---:|
| Binary accuracy | 0.9151 |
| Binary precision | 0.9389 |
| Binary recall | 0.9342 |
| Binary harmful F1 | **0.9365** |
| Multilabel Macro-F1 | **0.5981** |
| Multilabel weighted F1 | 0.8720 |

The binary harmful-content recall was 93.42%. The confusion matrix was:

| | Predicted Safe | Predicted Harmful |
|---|---:|---:|
| Actual Safe | 1,557 | 220 |
| Actual Harmful | 238 | 3,379 |

The model produced 220 false positives and 238 false negatives. The false-positive rate was 12.38%, and the false-negative rate was 6.58%.

### 8.3 Per-Class Results

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| SAFE | 0.8542 | 0.8869 | 0.8702 | 1,777 |
| CYBERBULLYING | 0.8077 | 0.6402 | 0.7143 | 492 |
| HARASSMENT | 0.7722 | 0.4178 | 0.5422 | 146 |
| HATE_SPEECH | 0.6863 | 0.1509 | 0.2473 | 232 |
| THREAT | 0.8000 | 0.3636 | 0.5000 | 11 |
| INSULT | 0.9127 | 0.8954 | 0.9040 | 3,060 |
| TOXIC | 0.9477 | 0.9201 | 0.9337 | 3,504 |
| SEXUAL_HARASSMENT | 0.0000 | 0.0000 | 0.0000 | 0 |
| OTHER_HARMFUL | 0.8160 | 0.5698 | 0.6711 | 179 |

The strongest categories were TOXIC, INSULT, and SAFE. The weakest category with available test examples was HATE_SPEECH, with an F1-score of 0.2473 and recall of 0.1509. SEXUAL_HARASSMENT had no test examples, so its zero score does not measure actual classification capability.

### 8.4 Language-Specific Results

| Language group | Accuracy | Precision | Recall | Binary F1 | Macro-F1 |
|---|---:|---:|---:|---:|---:|
| English | 0.9452 | 0.9595 | 0.9773 | 0.9683 | 0.3302 |
| Urdu | 0.8575 | 0.8414 | 0.7135 | 0.7722 | 0.4821 |
| Roman Urdu | 0.9245 | 0.9512 | 0.9512 | 0.9512 | 0.3754 |
| Code-mixed | 0.9315 | 0.9439 | 0.9656 | 0.9546 | 0.4879 |

The English group produced the highest binary F1. Urdu produced lower recall, indicating that harmful Urdu comments were missed more frequently. Roman Urdu results should be interpreted cautiously because only 53 Roman Urdu examples were available in the test slice.

## 9. Discussion

The results show that the system is effective at broad harmful-content detection. The binary harmful F1-score of 0.9365 demonstrates that the model can distinguish harmful comments from safe comments with relatively high precision and recall.

However, the detailed multilabel Macro-F1 score was only 0.5981. This difference occurs because broad harmful detection is easier than identifying the exact category of harm. The model performed strongly on frequent classes such as TOXIC and INSULT but struggled with HATE_SPEECH, THREAT, and HARASSMENT.

The low HATE_SPEECH recall may be caused by limited examples, semantic dependence on identity and context, overlap between hate speech and toxicity, differences between English and Urdu taxonomies, and the limited contextual capacity of TF-IDF features.

The Urdu binary F1-score was lower than the English score. This suggests that normalization and language tags alone are insufficient for resolving all Urdu linguistic variation, spelling differences, and context-dependent meanings.

The system should therefore be described as a strong CPU-friendly baseline rather than a complete production moderation solution.

## 10. Limitations

1. The external 1,000-item annotation set has not yet been completed.
2. The current scores are internal test results, not real-world accuracy.
3. The datasets originate from different taxonomies.
4. The Davidson dataset is English-only.
5. Roman Urdu coverage is limited.
6. The external Roman Urdu corpus was unavailable.
7. There are no sexual-harassment examples in the prepared corpus.
8. Threat examples are extremely rare.
9. The split is random rather than fully source-disjoint.
10. Binary stratification does not guarantee equal representation for every detailed class.
11. TF-IDF does not fully capture sarcasm, negation, implied meaning, or conversational context.
12. The multilabel mappings created from source labels may introduce label noise.
13. Keyword and context safeguards must not be reported as learned model performance.

## 11. Future Work

Future work should complete the independent external annotation set, use two annotators and one adjudicator, report Cohen's kappa and raw agreement, remove duplicates between training and external evaluation data, add more Roman Urdu and Urdu examples, add sexual-harassment and threat examples, compare the baseline against XLM-RoBERTa, perform source-disjoint and time-based evaluation, investigate class-specific threshold optimization, and report confidence intervals for all major metrics.

## 12. References

[1] Davidson, T., Warmsley, D., Macy, M., and Weber, I. "Automated Hate Speech Detection and the Problem of Offensive Language." *Proceedings of the International AAAI Conference on Web and Social Media*, vol. 11, 2017, pp. 512-515. doi:10.1609/icwsm.v11i1.14955.

[2] Adeeba. "Urdu Cyberbullying Corpus." Public research corpus, 2024. Available through the project repository: https://github.com/farahadeeba/cyberbullyingcorpus. Verify the final dataset citation and license before publication.

[3] Salton, G., and Buckley, C. "Term-Weighting Approaches in Automatic Text Retrieval." *Information Processing & Management*, vol. 24, no. 5, 1988, pp. 513-523.

[4] Cortes, C., and Vapnik, V. "Support-Vector Networks." *Machine Learning*, vol. 20, 1995, pp. 273-297.

[5] Sokolova, M., and Lapalme, G. "A Systematic Analysis of Performance Measures for Classification Tasks." *Information Processing & Management*, vol. 45, no. 4, 2009, pp. 427-437.

[6] Pedregosa, F., et al. "Scikit-learn: Machine Learning in Python." *Journal of Machine Learning Research*, vol. 12, 2011, pp. 2825-2830.

## Project Evidence

- [Dataset statistics](../data/processed/dataset_stats.json)
- [Evaluation results](results/latest.json)
- [Training methodology](train.py)
- [Data preparation](prepare_data.py)
- [Label definitions](../backend/app/ml/labels.py)
- [Annotation protocol](ANNOTATION_GUIDELINES.md)

## Final Reported Metrics

The principal internal-test results are:

- Binary harmful F1: **0.9365**
- Binary precision: **0.9389**
- Binary recall: **0.9342**
- Binary accuracy: **0.9151**
- Multilabel Macro-F1: **0.5981**
- Multilabel weighted F1: **0.8720**

The binary accuracy and F1-score must not be described as general real-world accuracy until the external human-annotated gold set has been completed.

