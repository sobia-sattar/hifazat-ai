# Independent multilabel gold evaluation

External evaluation is NOT COMPLETED. Existing data/gold candidates were sampled from the old internal test set and must not be described as independent external evidence.

Collect up to at least 1,000 legitimately sourced comments, document source/use permission, anonymize handles, and recruit two independent annotators proficient in each language plus an adjudicator. Keep annotators blind to model scores. Provide conversation context where authorized. Use the taxonomy document, allowing multiple labels and explicit uncertainty. Identity mentions alone are not hate speech.

Use data/external/gold.csv: text, annotator_1, annotator_2, adjudicated_labels. Label cells are pipe-separated taxonomy names; SAFE is exclusive. Store annotation rationale and source provenance separately with appropriate access controls. All three annotation columns must be complete before evaluation. Compute per-label raw agreement and Cohen's kappa; undefined kappa for constant labels is reported as null.

External comments must be held out before preparation, including near variants. Never tune models or thresholds on external annotations. Evaluation checks the external texts against the training, validation and internal test corpus and refuses overlapping inputs. Report sample sizes by language and label, and document adjudication and annotator qualifications without exposing personal information.
