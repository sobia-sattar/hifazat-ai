# Final project status

Working research implementation with verified classical results; the full multilingual/category research objective remains limited by annotation coverage, Urdu source permission, and CPU-only compute.

## Completed Components

- Explicit source/license registry and schema gates; conservative Unicode/Roman Urdu preprocessing and heuristic language profiles.
- Partial-label supervision, conflict quarantine, MinHash near-duplicate candidates, iterative splits and disjoint-split options.
- Five sparse baseline families, validation-only tuning/thresholds, frozen test predictions, source/language slices, calibration, error records, identity probes and bootstrap intervals.
- Optional XLM-R/mBERT trainer with weighted masked BCE/focal loss, accumulation, early stopping, resume and validation model selection. Transformer inference and Integrated Gradients are implemented but pretrained transformer fine-tuning was not run.
- Versioned artifacts; FastAPI single/CSV endpoints; updated React interface; compatibility adapter preserves YouTube/live/export routes without keyword score overrides.
- External multilabel annotation/evaluation infrastructure rejects overlaps and never trains on gold data.

Verification: {"tests": {"passed": 18, "failed": 0, "command": ".venv/Scripts/python.exe -m pytest -q", "warning": "Starlette httpx integration deprecation"}, "lint": "passed: new src, tests, orchestration, report generator, API and adapter", "editable_install": "passed", "pip_check": "passed: no broken requirements", "frontend_build": "passed; bundle size warning above 500 kB", "api_integration": "passed: real artifact, four input language/script examples, CSV, invalid input and missing artifacts", "browser_visual_check": "BLOCKED by browser admin-policy verification; not passed", "pipeline": "Preparation and baseline training passed; master pipeline completed with --skip-prepare --reuse-trained, preserving frozen test predictions", "transformer": "Tiny random BERT optimization smoke test passed; pretrained fine-tuning NOT COMPLETED", "external_human_evaluation": "NOT COMPLETED"}

## Dataset Summary

Retained records: **95,448**. Splits: {'train': 66813, 'test': 14318, 'validation': 14317}. Sources: {'roman_urdu_toxic': 71231, 'davidson2017': 24217}.

Dataset SHA-256: `d845f0ceaf131d4b3a284b85912ff1a148a9c403e3748fef4c4aac934dc2d63f`.

Urdu spreadsheets are preserved but excluded because license/use permission is unverified. Roman Urdu source metadata declares CC-BY-4.0, but collection and annotation documentation is limited. Language labels are heuristics, not audited ground truth.

## Models Trained

10 recorded selection trials on 66,813 training rows. 4 additional controlled logistic-regression normalization/class-weight ablations. Transformer status: NOT TRAINED in this baseline run.

## Best Validation Model

**hybrid_svm_0**; observed-label validation Macro-F1 **0.6755**.

## Final Test Results

Observed-label Macro-F1: **0.6384**; binary F1: **0.9056**; binary accuracy: **0.9344**.

Macro-F1 bootstrap interval: {'metric': 'observed-label macro_f1', 'resamples': 200, 'seed': 42, 'lower': 0.612934716756241, 'upper': 0.6612657432203102, 'note': 'Row bootstrap conditional on the fitted model and this split; not a significance test.'}.

Only HATE_SPEECH and TOXIC have evaluable positive/negative coverage. This Macro-F1 is not comparable with historical nine-label scores. No real-world accuracy or significance claim is made.

## Per-Class Results

| Label | Positive test support | F1 | Evaluable |
|---|---:|---:|---|
| CYBERBULLYING | 0 | Not validated | False |
| HARASSMENT | 0 | Not validated | False |
| HATE_SPEECH | 208 | 0.3711 | True |
| THREAT | 0 | Not validated | False |
| INSULT | 0 | Not validated | False |
| TOXIC | 4970 | 0.9056 | True |
| SEXUAL_HARASSMENT | 0 | Not validated | False |
| OTHER_HARMFUL | 0 | Not validated | False |

## Language Results

| Heuristic group | Test rows | Binary F1 | Observed-label Macro-F1 |
|---|---:|---:|---:|
| English | 2114 | 0.9557 | 0.6771 |
| English_Roman_Urdu | 4463 | 0.9105 | 0.6184 |
| Roman_Urdu | 6890 | 0.8314 | 0.7490 |
| Unknown | 851 | 0.8847 | 0.6507 |

## Remaining Limitations

- Six categories have no positive supervision and are disabled. No valid Urdu-script performance estimate or independent human gold evaluation.
- No completed pretrained transformer comparison or statistical significance test. CPU-only host; no claim that complex models outperform baselines.
- Probabilistic near-duplicate retrieval may miss variants; no conversation/user grouping metadata is available. Random source mixtures can encourage dataset artifacts.
- SAFE/neutral annotations are assumed to exclude target harms. Missing subtype labels remain unknown. Fully observed subset accuracy mostly reflects neutral comments.
- Browser visual verification was blocked by the browser admin-policy check. Frontend compilation and API integration are separately verified.
- Low free space on C: remains a host risk. Original project ownership/license needs clarification before public redistribution.

## Recommended Future Experiments

Obtain Urdu dataset permission; independently annotate rare harms; audit language identification; run source/language-disjoint evaluations; fine-tune XLM-R and mBERT on GPU; perform paired bootstrap comparisons and annotator agreement studies. Do not tune on the frozen test set.

## Exact Commands to Reproduce Results

```powershell
.venv/Scripts/python.exe -m pip install -e .
.venv/Scripts/python.exe -m src.data.acquire
.venv/Scripts/python.exe run_pipeline.py --profile standard
.venv/Scripts/python.exe -m src.training.ablations
.venv/Scripts/python.exe -m src.visualization.generate_figures
.venv/Scripts/python.exe -m pytest -q
cd frontend
npm ci
npm run build
```

This run executed preparation and baseline training first, then the master pipeline with `--skip-prepare --reuse-trained`; those flags reuse the verified dataset/model rather than refit. Frozen prediction files make report regeneration repeatable. Package versions are recorded in environment_report.json and requirements-lock.txt.

## Interface and moderation update

The local app now uses a CyberSafe-inspired blue/glass visual system and a simplified analysis/review workflow. Repeated charts and unsupported-category counters were removed from the main YouTube/live screens. Research results remain available separately. Comment filtering resets pagination, feedback buttons show save/error states, live controls reflect actual stream state, and settings validate threshold order.

The Review center counts distinct real YouTube comments per author and owner channel, keeps model flags separate from human-confirmed strikes, and excludes sample data. Warnings/rejections/channel-level author blocking require owner OAuth, current identity/text checks and explicit confirmation. The implementation cannot ban an entire YouTube account. Real external actions were not executed during development. See docs/YOUTUBE_MODERATION.md for setup and scope.

Validation: frontend production build passed; full test suite expanded to 22 passing tests, including mocked authorization/idempotency tests. Local frontend and moderation endpoints respond. No visual-browser verification claim is made.

## Channel dashboard update — 2026-08-31

Added the animated channel dashboard, @handle/channel URL resolution, bounded public top-level comment extraction, commenter search, flagged-only filtering, pagination and JSON export. Preserved single-video analysis, review center and owner-only moderation. Updated launcher to port 8011. Frontend build passed; 29 tests passed. Real channel extraction was verified with the configured API key: @example returned 50 public comments. No external moderation actions were sent. Cache cleanup was blocked by environment policy; no bulk deletions completed. See docs/CHANNEL_SCANNING.md.

## Simplified overview — 2026-08-31

The home route now opens /overview: one black-and-blue dashboard with a locally bundled Creepster headline font (OFL license included under frontend/public/fonts), animated shield, saved review counts and four tool links. Regular UI text retains readable sans-serif typography. Removed duplicate decorative scanner panels and repeated workflow banners. All scanner, text analysis, moderation, live monitoring, settings and research routes remain available. Motion can be disabled in the footer and respects OS reduced-motion settings. Frontend production build and HTTP checks for overview, font and evidence endpoint passed. Browser visual verification remains unavailable under the earlier localhost browser restriction.

## Testing and controlled retraining audit

31 tests passed, production build passed, dependency check passed. Retrained one larger hybrid SVM on all 66,813 training examples. Validation binary accuracy improved to 94.15%, but category Macro-F1 declined to 66.09% versus 67.55%; the candidate was not promoted. Active-model test accuracy remains 93.44% and binary F1 90.56%. Zero exact cross-split overlaps were found; six categories remain without positive supervision. Details: reports/TRAINING_AUDIT.md and reports/training_audit.json. No 100% accuracy guarantee is supported.

## Additional accuracy-target experiment

New binary research candidate: 95.30% validation accuracy, 94.64% held-out test accuracy, 92.12% test binary F1. Target of 96% was not achieved. Model artifact saved separately; active multi-category model unchanged. See reports/ACCURACY_TARGET.md and reports/accuracy_target_experiment.json. Existing 31 tests passed.

## Security review and research paper

Added local API boundary controls, actual body-size limits, safe CSV/PDF exports, live-input validation, and explicit external-explanation privacy opt-in. The original multi-category serving model remains selected. Read docs/SECURITY_AUDIT.md for implemented controls and deployment blockers.

Professional research report: research/paper/BullyLens_X_Research_Paper.md (editable source) and output/pdf/BullyLens_X_Research_Paper.pdf (six-page rendered report). Download is available on /research via /api/v2/paper. The report includes checked references and measured results, not invented accuracy or publication claims. Rendered page layout was inspected.

Final verification for this audit: 37 tests passed (one existing Starlette/httpx deprecation warning); production frontend build passed; actual frontend-proxied inference and PDF download returned 200; hostile-origin inference returned 403. PDF has six A4 pages, no JavaScript, and all rendered pages were inspected. Public-deployment and annotation limitations remain documented rather than represented as completed.

Paper version 1.2 preserves the requested five-section outline and adds six numbered figures: architecture, moderation workflow, partition/label coverage, binary test comparison, confusion matrices and supported-category F1. Figures are generated from saved metrics by scripts/build_paper_figures.py and retained as PNG/SVG under research/paper/figures. The rebuilt PDF has eight pages; rendered layouts and corrected figure labels were inspected.

Professor-requested revision completed: removed the subtitle, date/version line, project-status disclaimer, questioned workstation/UI wording and dataset hash; replaced contribution wording; named the expanded hybrid-SVM and log-count-ratio logistic-regression experiments; removed the Quantitative Results subheading; added a figure-description opening and Table 1 caption; expanded Related Work and References to 15 verified sources. All other paper structure, measurements and figures were retained. Rebuilt nine-page PDF visually inspected without clipping.
