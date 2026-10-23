# BullyLens-X Annotation Protocol

## Purpose

Create a human-verified evaluation set for multilingual cyberbullying research. This set must remain separate from `data/processed/dataset.csv` and must never be used for training.

## Labels

Use exactly one primary label for each comment:

- `SAFE`: no abuse, threat, hate, harassment, sexual harassment, or targeted bullying.
- `INSULT`: a direct insult or name-calling without evidence of repeated or coordinated targeting.
- `HARASSMENT`: unwanted targeted abuse, humiliation, or persistent hostile contact.
- `CYBERBULLYING`: repeated, targeted, or socially amplified abuse against a person or group in an online context. Do not use this label for every offensive sentence.
- `HATE_SPEECH`: attacks or dehumanizes a protected group based on identity.
- `THREAT`: a stated or implied intent to cause harm.
- `SEXUAL_HARASSMENT`: unwanted sexual remarks, requests, or sexualized targeting.
- `OTHER_HARMFUL`: harmful content that does not fit the labels above.

## Language fields

Record `language` as `English`, `Urdu`, `Roman Urdu`, or `Mixed`. Record `script` as `latin`, `arabic`, or `mixed`.

## Annotation rules

1. Label the meaning of the complete comment, not isolated keywords.
2. Negation matters: `no hate`, praise, grief, and ordinary engagement are normally `SAFE`.
3. Roman Urdu spelling variants should be interpreted by context, not by a word list alone.
4. If context is insufficient, use `SAFE` only when no harmful meaning is present; otherwise record the closest harmful label and explain the ambiguity.
5. Annotators must not use the model prediction as evidence.
6. Record a short rationale for every harmful label.

## Agreement procedure

Two independent annotators label every item. A third adjudicator resolves disagreements. Report raw agreement and Cohen's kappa for the primary label. Publish the final label, not individual annotator identities.

## Required split policy

Keep this gold set as an external test set. Do not sample it from the training corpus. Remove exact and near duplicates against training data before reporting results.
