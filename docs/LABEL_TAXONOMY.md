# Label taxonomy and annotation masks

The eight harmful categories are independent sigmoid/binary heads. SAFE is derived when no category crosses its validation-frozen threshold. Task A also has an independent harmful-vs-safe head; disagreements are exposed for review.

| Category | Required source semantics |
|---|---|
| CYBERBULLYING | Explicit bullying annotation with targeting/context; generic profanity is insufficient |
| HARASSMENT | Harassment annotation, not merely negative sentiment |
| HATE_SPEECH | Identity-directed hate annotation |
| THREAT | Threat annotation |
| INSULT | Insult annotation; broad offensive labels alone are insufficient |
| TOXIC | Explicit broad abusive, offensive or toxic annotation |
| SEXUAL_HARASSMENT | Explicit unwanted sexual targeting; sexual vocabulary alone is insufficient |
| OTHER_HARMFUL | Harm with no justified more specific category |

`configs/label_mapping.yaml` is the executable mapping. Davidson hate maps to HATE_SPEECH and TOXIC. Davidson offensive maps to TOXIC, with a negative hate annotation reflecting the source's mutually exclusive taxonomy. We do not infer INSULT from every offensive example. Roman Urdu Toxic=1 maps to TOXIC alone. Source-neutral/non-toxic maps to SAFE, represented as all-zero harm labels.

Unknown cells use -1 and are excluded from each head's loss and metrics. SAFE mappings assume the source's neutral/non-toxic annotation excludes the target harms; this assumption needs independent validation. Unsupported heads with no positive training/validation examples are disabled, not advertised as accurate.

The primary Macro-F1 averages labels having positive and negative validation annotations. The set of evaluable labels is stored in every result. This is NOT the historical nine-label Macro-F1, and must not be presented as an improvement over it. Subset accuracy is restricted to fully observed rows; current fully observed data largely comprise neutral examples, so it is not a complete multilabel benchmark.

Taxonomy harmonization cannot create annotations. The current accepted corpus cannot answer every category research question. Add explicitly licensed and annotated sources, or collect a genuine independent gold set, before claiming full taxonomy performance.
