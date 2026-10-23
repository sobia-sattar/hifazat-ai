# Initial repository audit

Existing work preserved: FastAPI backend with SQLite analysis history, YouTube/live analysis, exports and XAI; React/Vite frontend; three raw source files; processed data; trained sklearn artifact; research scripts/paper; six hand-rule-oriented tests.

Historical outputs live in models/ and research/results/. The paper's reported 35,959 comments and metrics were not independently reproduced. They remain project-reported historical values.

Problems found: substring/guess-based label mapping, offensive/insult mapped to cyberbullying, weak prefix-only near-duplicate checks, binary-only stratification, incomplete taxonomy coverage, one-threshold evaluation, inference rules changing probabilities and confidence, transformer comparison using a smaller validation slice, no actual external gold set, and an external annotation queue sampled from the internal test split.

The v2 src/ pipeline uses separate artifacts/ and reports/ directories, explicit source schemas, partial-label masks, conflict quarantine, MinHash near-duplicate candidates, iterative stratification, validation thresholds and versioned metrics. The original training scripts are retained for historical inspection only. Live inference uses v2; old model files are not overwritten.

The Windows Store Python interpreter requires execution outside this environment's sandbox. CPU-only hardware was detected. Missing research dependencies were installed. A full C: drive interrupted implementation; the pip download cache was moved, with approval, into D:/BullyDetector/.pip-cache/recovered-system-cache to preserve files and free space.
