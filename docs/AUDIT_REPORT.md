# Comprehensive Repository Audit Report: BullyLens-X

**Audit Date:** 2026-10-23  
**Auditor:** Antigravity AI Coding Assistant  
**Git Branch Created:** `feature/bullylens-enhancements`  
**Base Commit Recorded:** `5395be56ff1de4ca2c62667966f47e275d8c04e4` (`Prepare BullyLens-X for deployment`)  

---

## 1. Executive Summary

A comprehensive Phase 0 audit of the **BullyLens-X** repository was conducted against the enhancement requirements and the unverified assumptions in `BullyLens_PRD.md`. 

BullyLens-X is an AI-assisted cyberbullying and toxic content detection research platform designed for multilingual text (English, Urdu script, Roman Urdu, and code-mixed). It currently operates as a local single-workstation research tool consisting of a FastAPI backend, a React/Vite single-page application (SPA), an SQLite database (`bullylens.db`), and frozen classical machine learning model artifacts (`hybrid_svm_0`).

All existing models, datasets, UI token systems, and database structures have been verified. Crucially, **no code modifications** have been made during Phase 0.

---

## 2. Technology Stack & Environment Versions

| Component | Technology | Version | Location / Manifest |
|---|---|---|---|
| **Operating System** | Windows 11 Pro / PowerShell | 10.0.26100 | Host environment |
| **Python Runtime** | CPython | 3.14.3 | `C:\Program Files\Python314\python.exe` / `.venv` |
| **Node.js** | Node.js | v24.21.0 | `C:\Program Files\nodejs\node.exe` |
| **Package Manager** | npm | 11.19.0 | `C:\Program Files\nodejs\npm.cmd` |
| **Backend Framework** | FastAPI | 0.141.1 | `backend/pyproject.toml`, `requirements.txt` |
| **ASGI Server** | Uvicorn | 0.52.4 | `requirements.txt` |
| **Database ORM** | SQLAlchemy | 2.0.52 | `backend/app/database/session.py` |
| **Data Validation** | Pydantic / Pydantic-Settings | 2.13.4 / 2.15.0 | `backend/app/schemas/`, `backend/app/core/config.py` |
| **ML & Data Science** | scikit-learn, pandas, numpy, scipy | 1.9.0 / 3.0.5 / 2.5.2 / 1.18.0 | `requirements.txt`, `src/` |
| **Model Serialization**| joblib | 1.5.3 | `src/inference/predict.py`, `backend/app/ml/infer.py` |
| **HTTP Client** | httpx | 0.28.1 | `backend/app/youtube/client.py`, `backend/app/genai/explain.py` |
| **PDF Generation** | ReportLab | 5.0.0 | `backend/app/services/reports.py` |
| **Frontend Framework** | React | 18.3.1 | `frontend/package.json` |
| **Frontend Tooling** | Vite | 6.4.3 | `frontend/package.json`, `frontend/vite.config.ts` |
| **Language (Frontend)**| TypeScript | 5.8.3 | `frontend/tsconfig.json` |
| **Routing** | React Router DOM | 6.30.0 | `frontend/src/App.tsx` |
| **Styling** | TailwindCSS | 3.4.17 | `frontend/tailwind.config.js`, `frontend/src/index.css` |
| **Visualization** | Recharts | 2.15.2 | `frontend/src/components/Charts.tsx` |

---

## 3. Architecture & Entry Points

### 3.1 Architecture Overview
BullyLens-X employs a decoupled client-server architecture:
- **Backend (`backend/app`)**: Built with FastAPI. Enforces strict boundary middleware (`LocalBoundaryMiddleware` in `backend/app/core/security.py`) allowing requests only from loopback IP (`127.0.0.1`, `::1`) and recognized origins (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://127.0.0.1:8011`). Exposes RESTful endpoints for single/batch text analysis, YouTube channel scanning, YouTube video analysis, live chat observation, review moderation, and research results.
- **Frontend (`frontend/src`)**: Single-page React application bundled with Vite. Styled with custom cyberpunk/blue-glass tokens (`ambient-scene`, `stat-box`, `card`, `notice`). Proxies `/api` requests to `http://127.0.0.1:8011`.
- **Database (`bullylens.db`)**: SQLite database stored in the project root, managed via SQLAlchemy ORM. Initialized automatically at application startup in `backend/app/main.py` (`init_db()`).
- **ML Artifacts (`artifacts/models/hybrid_svm_0/` and `models/`)**: Versioned model bundles containing calibrated scikit-learn pipelines with TF-IDF word (1-3 ngrams) and character (2-5 ngrams) feature extractors and linear SVM heads with Platt calibration.

### 3.2 Real Entry Points

1. **Backend Server Startup:**
   ```powershell
   .venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8011
   ```
   *File:* `backend/app/main.py#L1-L42`

2. **Frontend Development Server:**
   ```powershell
   $env:VITE_API_TARGET = "http://127.0.0.1:8011"
   Set-Location frontend
   npm.cmd run dev:frontend
   ```
   *Listens on:* `http://localhost:5173`
   *File:* `frontend/vite.config.ts`, `frontend/package.json#L8`

3. **Combined Developer Launcher Script:**
   ```powershell
   ./start-dev.ps1
   ```
   *File:* `start-dev.ps1#L1-L20` (starts backend process on port 8011 and Vite frontend).

4. **Master Research Pipeline:**
   ```powershell
   .venv\Scripts\python.exe run_pipeline.py --profile standard
   ```
   *File:* `run_pipeline.py#L1-L60`

---

## 4. Complete API Endpoints Audit

All endpoints inspected across `backend/app/main.py`, `backend/app/api/routes.py`, `backend/app/api/channel_scan.py`, `backend/app/api/moderation.py`, and `backend/app/api/research_v2.py`:

| Method | Full Path | Auth / Restrictions | Request Body / Params | Response Summary | Source File |
|---|---|---|---|---|---|
| `GET` | `/health` / `/api/health` | Local boundary | None | Health status, YouTube config, GenAI config, model status | `backend/app/api/routes.py#L22` |
| `POST` | `/api/analyze/text` | Local boundary | `TextAnalyzeRequest` (`text`: 1-8000 chars, `include_genai`: bool, `safer_rephrase`: bool) | Detailed prediction, risk level, confidence, XAI linear feature contributions, optional GenAI explanation | `backend/app/api/routes.py#L33` |
| `POST` | `/api/youtube/analyze` | Local boundary | `YouTubeAnalyzeRequest` (`url`: str, `max_comments`: int, `include_genai_summary`: bool) | Scraped & predicted comments list, summary statistics, video metadata | `backend/app/api/routes.py#L52` |
| `GET` | `/api/youtube/latest` | Local boundary | None | Latest saved video analysis from database | `backend/app/api/routes.py#L60` |
| `GET` | `/api/youtube/{analysis_id}`| Local boundary | `analysis_id`: int | Serialized analysis with comments and predictions | `backend/app/api/routes.py#L68` |
| `GET` | `/api/comments/{prediction_id}`| Local boundary| `prediction_id`: int | Single comment detail with on-demand XAI computation and GenAI | `backend/app/api/routes.py#L76` |
| `POST` | `/api/comments/{prediction_id}/review` | Local boundary | `ReviewRequest` (`decision`: `correct`\|`incorrect`\|`needs_review`, `notes`: str) | Review confirmation | `backend/app/api/routes.py#L116` |
| `GET` | `/api/dashboard` | Local boundary | None | Overview statistics, recent high-risk comments, model status | `backend/app/api/routes.py#L127` |
| `GET` | `/api/research/metrics` | Local boundary | None | Historical research metrics (`research/results/latest.json`) | `backend/app/api/routes.py#L142` |
| `GET` | `/api/research/errors` | Local boundary | None | Error analysis examples (`research/results/error_examples.json`)| `backend/app/api/routes.py#L150` |
| `POST` | `/api/live/start` | Local boundary | `LiveStartRequest` (`url`: str) | Live monitor initialization | `backend/app/api/routes.py#L161` |
| `POST` | `/api/live/pause` | Local boundary | None | Pause live polling | `backend/app/api/routes.py#L166` |
| `POST` | `/api/live/resume` | Local boundary | None | Resume live polling | `backend/app/api/routes.py#L171` |
| `POST` | `/api/live/stop` | Local boundary | None | Terminate live polling | `backend/app/api/routes.py#L176` |
| `GET` | `/api/live/status` | Local boundary | `poll`: bool query param | Live stream status, metrics, recent chat messages | `backend/app/api/routes.py#L181` |
| `GET` | `/api/export/{id}/csv` | Local boundary | `id`: int | Download CSV with formula injection sanitization | `backend/app/api/routes.py#L188` |
| `GET` | `/api/export/{id}/json`| Local boundary | `id`: int | Download JSON analysis payload | `backend/app/api/routes.py#L194` |
| `GET` | `/api/export/{id}/pdf` | Local boundary | `id`: int | Download PDF report with sanitized literal text | `backend/app/api/routes.py#L200` |
| `GET` | `/api/settings` | Local boundary | None | YouTube, GenAI, and threshold configuration | `backend/app/api/routes.py#L206` |
| `POST` | `/api/settings` | Local boundary | `SettingsUpdate` (`high_confidence_threshold`, `low_confidence_threshold`) | Updated runtime review thresholds | `backend/app/api/routes.py#L219` |
| `POST` | `/api/youtube/channel/scan` | Local boundary | `ChannelScan` (`channel`: str, `max_comments`: int 1-500) | Public channel comments, commenter grouping, AI flags | `backend/app/api/channel_scan.py#L19`|
| `GET` | `/api/moderation/status` | Local boundary | None | Channel moderation configuration and warning template | `backend/app/api/moderation.py#L32` |
| `GET` | `/api/moderation/authors`| Local boundary | None | Commenters grouped by author with strikes and audit log | `backend/app/api/moderation.py#L44` |
| `POST` | `/api/moderation/comments/{id}/review` | Local boundary + origin check | `Review` (`decision`: `harmful`\|`safe`\|`pending`)| Saves reviewer verdict on a moderation comment | `backend/app/api/moderation.py#L89` |
| `POST` | `/api/moderation/comments/{id}/action` | Local boundary + origin check + OAuth check | `Action` (`action`: `warn`\|`reject`\|`ban_author`, `confirmed`: bool, `message`: str) | Executes moderation action via YouTube OAuth API | `backend/app/api/moderation.py#L99` |
| `GET` | `/api/v2/health` | Local boundary | None | Health status (`{"status": "ready"}`) | `backend/app/api/research_v2.py#L48` |
| `GET` | `/api/v2/labels` | Local boundary | None | Supported labels and safe definition | `backend/app/api/research_v2.py#L57` |
| `GET` | `/api/v2/model/info` | Local boundary | None | Model name, version, training date, threshold bundle | `backend/app/api/research_v2.py#L62` |
| `POST` | `/api/v2/predict` | Local boundary | `TextRequest` (`text`: 1-8000 chars) | Frozen model predictions, binary decision, category scores | `backend/app/api/research_v2.py#L67` |
| `POST` | `/api/v2/predict/batch` | Local boundary | Multipart CSV file (`file`, max 2MB, max 1000 rows) | Batch CSV prediction download with formula escaping | `backend/app/api/research_v2.py#L75` |
| `GET` | `/api/v2/results` | Local boundary | None | Full validation and test evaluation metrics JSON | `backend/app/api/research_v2.py#L24` |
| `GET` | `/api/v2/paper` | Local boundary | None | PDF download of the research paper | `backend/app/api/research_v2.py#L16` |

---

## 5. Database Schema & Tables

All tables inspected in `bullylens.db` via SQLite schema and `backend/app/database/models.py` / `backend/app/services/moderation.py`:

1. **`videos`**: Cached YouTube video metadata (`id`, `video_id`, `title`, `channel`, `published_at`, `thumbnail_url`, `is_demo`, `created_at`).
2. **`comments`**: Video comments (`id`, `video_id`, `youtube_comment_id`, `original_text`, `normalized_text`, `published_at`, `is_demo`, `created_at`).
3. **`predictions`**: Per-comment ML inference results (`id`, `comment_id`, `analysis_id`, `model_name`, `language`, `language_confidence`, `script`, `is_code_mixed`, `classification`, `confidence`, `risk`, `categories` [JSON], `code_mix_tokens` [JSON], `xai` [JSON], `genai_explanation`, `created_at`).
4. **`analyses`**: Aggregate analysis runs (`id`, `video_id`, `source`, `demo_mode`, `model_name`, `status`, `stats` [JSON], `created_at`).
5. **`reviews`**: Internal feedback on predictions (`id`, `comment_id`, `prediction_id`, `decision` [`correct`|`incorrect`|`needs_review`], `notes`, `created_at`).
6. **`experiments`**: Historical model experiment tracking (`id`, `name`, `config` [JSON], `status`, `created_at`).
7. **`model_metrics`**: Evaluation metrics per split/language (`id`, `experiment_id`, `model_name`, `split`, `language`, `metrics` [JSON], `created_at`).
8. **`live_sessions`**: Livestream monitoring sessions (`id`, `video_id`, `live_chat_id`, `status`, `stats` [JSON], `created_at`, `updated_at`).
9. **`moderation_comments`**: Channel scan commenter tracking (`id`, `youtube_comment_id` [UNIQUE], `video_id`, `channel_id`, `author_id`, `author_name`, `text`, `flagged`, `decision`, `created_at`).
10. **`moderation_actions`**: Owner moderation actions audit log (`id`, `comment_id`, `action`, `message`, `status`, `created_at`).

---

## 6. Machine Learning Pipeline & Artifacts

### 6.1 Inference Pipeline
- **Input:** Raw text (1 to 8,000 characters).
- **Language Detection & Normalization (`app/nlp/language.py` & `src/data/prepare.py`):**
  - Unicode normalization (NFKC).
  - Script identification (`latin`, `arabic`, `other`).
  - Heuristic lexicon lookup identifying `English`, `Urdu`, `Roman_Urdu`, or `English_Roman_Urdu` (code-mixed).
  - Code-mixed token-level annotation and confidence calculation.
- **Model Bundle (`artifacts/models/hybrid_svm_0/model_bundle.joblib`):**
  - Evaluated on validation set observed-label Macro-F1 (0.6755).
  - Feature Union: Word TF-IDF (1-3 n-grams) + Character TF-IDF (2-5 n-grams).
  - Binary Classifier: Calibrated LinearSVC (`SAFE` vs `HARMFUL`, threshold: 0.45).
  - Multilabel Head: Independent calibrated classifiers for 8 categories.
  - **Supervision status:** Only `TOXIC` (threshold: 0.45) and `HATE_SPEECH` (threshold: 0.50) have training supervision. The remaining 6 categories (`CYBERBULLYING`, `HARASSMENT`, `THREAT`, `INSULT`, `SEXUAL_HARASSMENT`, `OTHER_HARMFUL`) have threshold `1.01` (`supported: False`), ensuring they never trigger false positive predictions.
- **Explainability (XAI):**
  - Linear feature contribution attribution (`src/inference/predict.py`).
  - Calculates token and n-gram weights contributing positively or negatively to the prediction.
  - Accompanied by strict disclaimer: *"Feature importance is not proof of causality."*

### 6.2 Pretrained Transformer Status
- Code exists in `src/training/train_transformer.py` supporting XLM-RoBERTa and mBERT with focal loss.
- **No pretrained transformer models were fine-tuned or deployed** due to CPU-only execution constraints during baseline creation. The production model is purely `hybrid_svm_0`.

---

## 7. Baseline Behavior for Regression Comparison

Live API predictions were executed on the running backend (`http://127.0.0.1:8011/predict`) across all language and boundary test cases. These outputs serve as the exact baseline for regression verification:

| Test Case | Input Text | Detected Language | Binary Decision | Harmful Probability | Active Labels | Primary Contributing Features |
|---|---|---|---|---|---|---|
| **English Safe** | `"Have a wonderful day ahead!"` | `English` (0.69) | `SAFE` | 0.1716 | `["SAFE"]` | `word__day` (-0.13), `word__ahead` (-0.05), `word__wonderful` (-0.05) |
| **English Toxic** | `"You are an idiot and nobody likes you"` | `English` (0.81) | `HARMFUL` | 0.8613 | `["TOXIC"]` | `word__idiot` (+0.27), `word__an` (+0.12), `word__you` (+0.12) |
| **Urdu Safe** | `"آپ کا دن اچھا گزرے"` | `Urdu` (0.99) | `SAFE` | 0.0332 | `["SAFE"]` | Character n-grams (negative contribution) |
| **Urdu Toxic** | `"تم ایک جاہل اور بدتمیز انسان ہو"` | `Urdu` (0.99) | `SAFE` | 0.1014 | `["SAFE"]` | *Note: Urdu datasets excluded from training pending license; model conservatively predicts SAFE.* |
| **Roman Urdu Safe**| `"Aap ka din acha guzray"` | `Roman_Urdu` (0.81) | `SAFE` | 0.1051 | `["SAFE"]` | `word__acha` (-0.15), `word__din` (-0.09) |
| **Roman Urdu Toxic**| `"Tum bohot gande aur jahil insan ho"`| `Roman_Urdu` (0.81) | `HARMFUL` | 0.9966 | `["TOXIC"]` | `word__jahil` (+0.62), `word__insan` (+0.31), `char__gand` (+0.10) |
| **Code-mixed Safe**| `"Great video bhai, keep it up bohot acha kaam hai"` | `English_Roman_Urdu` (0.71) | `SAFE` | 0.1420 | `["SAFE"]` | `word__great` (-0.11), `word__acha` (-0.08) |
| **Code-mixed Toxic**| `"Stop talking nonsense bakwas band karo loser"` | `English_Roman_Urdu` (0.70) | `HARMFUL` | 0.9891 | `["TOXIC"]` | `word__bakwas` (+0.25), `word__stop` (+0.12), `word__band` (+0.08) |
| **Empty Input** | `""` | N/A | HTTP 422 | N/A | Rejected with `"String should have at least 1 character"` |
| **Oversize Input** | 150 repetitions of long sentence (6,000 chars) | `English` (0.78) | `SAFE` | 0.2538 | `["SAFE"]` | Processed successfully without truncation error (< 8000 max) |

---

## 8. Audit Categories & Findings

### Category 1: Fully Implemented and Working
- **Single text analysis API (`/api/analyze/text` and `/api/v2/predict`)**: Multilingual language detection, script classification, binary classification, category probabilities, XAI linear feature contributions.
- **Batch CSV prediction (`/api/v2/predict/batch`)**: File size bounding (2 MB), row limit (1,000 rows), CSV formula escaping against injection.
- **Public channel scan (`/api/youtube/channel/scan`)**: Scrapes up to 500 public comments, groups commenters, flags repeated harmful comments, exports scan JSON.
- **YouTube single video analysis (`/api/youtube/analyze`)**: Fetches comments, computes stats, persists to database, exports CSV/JSON/PDF.
- **Live stream monitor (`/api/live/start`, `/pause`, `/resume`, `/stop`, `/status`)**: Polling architecture for live YouTube chats.
- **YouTube owner moderation center (`/api/moderation/...`)**: 3-strike rule per commenter, OAuth-checked warning drafts, comment rejection, channel-level commenter blocking, action audit logs.
- **Research results & metrics (`/api/v2/results`, `/api/v2/paper`)**: Final evaluation metrics reporting and paper PDF download.
- **Security middleware (`LocalBoundaryMiddleware`)**: Restricts requests to local loopback and trusted origin headers, rejects cross-site requests, caps body size at 2.1 MB.

### Category 2: Implemented but Incomplete or Erroring
- **Existing Pytest suite in `tests/test_moderation.py` and `tests/test_security_boundary.py`**:
  - `tests/test_moderation.py` (4 tests failing): Mock `SimpleNamespace` does not include `public_deployment` attribute introduced in uncommitted changes.
  - `tests/test_security_boundary.py` (1 test failing): Uncommitted change in `backend/app/core/security.py#L25` omitted the check for `request.headers.get('sec-fetch-site') == 'cross-site'`.
- **`tests/test_research.py`**: Cannot run because `import torch` raises `ModuleNotFoundError: No module named 'torch'`. PyTorch is not part of the standard dependencies.
- **Frontend production build (`npm run build`)**: Fails with TypeScript error `src/services/api.ts(1,36): error TS2339: Property 'env' does not exist on type 'ImportMeta'` because `vite/client` type reference is missing.
- **GenAI explanation layer (`backend/app/genai/explain.py`)**: Only supports OpenAI-compatible endpoints; disabled by default unless both `ALLOW_EXTERNAL_EXPLANATIONS=true` and `GENAI_API_KEY` are provided.

### Category 3: In the Paper / Docs but Not in Code
- **Pretrained Multilingual Transformers (XLM-RoBERTa, mBERT)**: Described in research papers and docs, but no fine-tuned weights exist. Training code exists in `src/training/train_transformer.py`, but baseline runs used classical hybrid SVM (`hybrid_svm_0`).
- **Urdu-Script Supervised Model**: Discussed in research taxonomy, but positive Urdu datasets were excluded due to unverified licensing.
- **Six Harm Categories (`CYBERBULLYING`, `HARASSMENT`, `THREAT`, `INSULT`, `SEXUAL_HARASSMENT`, `OTHER_HARMFUL`)**: Discussed in documentation taxonomy, but deliberately disabled (threshold 1.01) due to lack of positive supervision in the approved dataset.

### Category 4: Missing Entirely (Candidate Features F1–F5)
- **F1 (P1) Dedicated Result Presentation Component**: The frontend currently displays raw JSON and basic tables. Missing an empathetic, tier-based risk presentation component that provides plain-language reasons, next-step guidance, and notices that predictions are automated estimates without labeling individuals.
- **F2 (P1, conditional) General Incident Reporting & Review**: The existing review center is strictly for YouTube channel-owner strikes. There is no general incident reporting system allowing users/reporters to submit incidents, track statuses (`submitted`, `in_review`, `needs_info`, `actioned`, `dismissed`, `escalated`), record reviewer notes and agreement feedback, or delete reports.
- **F3 (P1/P2) AI Cyber Safety Assistant**: No conversational cyber-safety assistant exists. F3 requires a backend adapter with a static curated guidance fallback, crisis pre-check (local regex/pattern matching for self-harm/danger with vetted helplines), rate limiting, topic limits, and prompt-injection defenses.
- **F4 (P2) Scam / Phishing Text Check**: No scam or phishing detection exists. Requires deterministic heuristic checks (urgency, financial requests, credential theft, impersonation), inert URL rendering (never fetching or resolving links), and clear risk levels without false guarantees.
- **F5 (P3) Password-Strength Checker**: No password strength evaluation exists. Requires client-only local computation with zero network/backend requests, pattern feedback, and show/hide toggles.

### Category 5: Already Present, Must NOT Be Duplicated
- **Text Analysis Backend**: `/api/analyze/text` and `/api/v2/predict`. Do NOT duplicate or replace these prediction routes.
- **YouTube Channel Scanner & Video Scraper**: Fully implemented in `app/api/channel_scan.py`, `app/youtube/client.py`, and `ChannelScan.tsx`.
- **Channel Owner YouTube Strike System**: Fully implemented in `app/services/moderation.py` and `Moderation.tsx`.
- **XAI Feature Importance Engine**: Fully implemented in `src/inference/predict.py`.
- **Export Engine**: CSV, JSON, and PDF generation in `app/services/reports.py`.

---

## 9. Security & Privacy Observations

1. **Loopback Binding**: Backend is bound to `127.0.0.1` and protected by `LocalBoundaryMiddleware`.
2. **CORS and Origin Filtering**: Origin checks prevent unauthorized cross-origin requests.
3. **No Secret Leaks**: No API keys are bundled into frontend code or logged in backend output. `.env.example` contains only placeholder variables.
4. **Formula Injection Sanitization**: CSV export properly prefixes dangerous characters (`=`, `+`, `-`, `@`) with a single quote `'` in `backend/app/services/reports.py#L22-L24`.
5. **No Model Overrides**: Keyword-based score tampering was previously excised; all predictions strictly reflect frozen model outputs.

---

## 10. Updated PRD Unverified-Assumptions Register

| PRD Assumption | Codebase Verification Finding | Status |
|---|---|---|
| User authentication (login/signup) exists | No authentication tables, user models, or login routes exist. The app is a local workstation tool. | **Contradicted** |
| All 8 harm categories are actively predicted with validated F1 | Only `TOXIC` and `HATE_SPEECH` have supervision. 6 categories are masked with threshold 1.01. | **Contradicted** |
| General incident reporting workflow exists | Existing moderation is channel-specific YouTube owner review only; no incident reports table exists. | **Contradicted** |
| Interactive AI assistant / chatbot exists | Only single-turn LLM explanation for XAI exists in `app/genai/explain.py`. No assistant exists. | **Contradicted** |
| Alembic database migrations exist | Database tables are created via SQLAlchemy `Base.metadata.create_all()`; no Alembic directory. | **Contradicted** |
| YouTube scanner analyzes global commenter history | Channel scanner only accesses public comments on the specific input channel via YouTube API. | **Contradicted** |
| Pretrained transformer models are running in production | Baseline hybrid linear SVM (`hybrid_svm_0`) is the active deployed artifact. | **Contradicted** |
| Urdu script has validated training coverage | Urdu spreadsheets were excluded pending license verification; Urdu input is supported by char n-grams but has no positive training supervision. | **Contradicted** |

---

## 11. Existing Defects Found (Not Silently Fixed)

1. **Defect 1 (`backend/app/api/moderation.py#L16`):**
   `local_mutation` checks `if get_settings().public_deployment:`. In `tests/test_moderation.py`, `get_settings` is mocked with `SimpleNamespace(youtube_oauth_access_token="", youtube_owner_channel_id="")`, triggering `AttributeError: 'types.SimpleNamespace' object has no attribute 'public_deployment'`.
2. **Defect 2 (`backend/app/core/security.py#L25`):**
   Uncommitted modification replaced the middleware check `if (origin and origin not in ORIGINS) or request.headers.get('sec-fetch-site') == 'cross-site':` with `allowed_origins = set(get_settings().cors_origin_list) | ORIGINS; if origin and origin not in allowed_origins:`, inadvertently dropping the `sec-fetch-site == 'cross-site'` check and causing `test_cross_site_and_rebinding_blocked` to fail.
3. **Defect 3 (`frontend/src/services/api.ts#L1`):**
   `import.meta.env.VITE_API_URL` fails TypeScript compilation (`npm run build`) because Vite client types (`vite/client`) are not referenced in `frontend/src/vite-env.d.ts` or `frontend/tsconfig.json`.
4. **Defect 4 (`tests/test_research.py#L5`):**
   Unconditionally imports `torch`, which is not in `requirements.txt` or the standard installation, breaking test collection if PyTorch is absent.
