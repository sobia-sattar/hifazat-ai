# Implementation Plan: BullyLens Enhancements (Approval Gate)

**Date:** 2026-10-23  
**Status:** AWAITING USER APPROVAL  
**Branch:** `feature/bullylens-enhancements`  
**Base Commit:** `5395be56ff1de4ca2c62667966f47e275d8c04e4`  

---

## 1. Plan Principles & Strict Guardrails

1. **Audit Precondition Fulfilled:** Phase 0 audit is complete (`docs/AUDIT_REPORT.md`).
2. **Absolute ML Invariance:** The ML model (`hybrid_svm_0`), weights, feature extractors, thresholds, dataset splits, and evaluation metrics will remain **strictly untouched**. All new code will treat existing inference logic as read-only.
3. **Additive Architecture:** Existing UI views, navigation links, and API routes will be preserved. New features reside in modular new files and are linked in an additive manner.
4. **Configurable Feature Flags:** Every enhancement will be gated behind a configuration flag (`FEATURE_RESULT_PRESENTATION_ENABLED`, `FEATURE_REPORTING_ENABLED`, `FEATURE_ASSISTANT_ENABLED`, `FEATURE_SCAM_CHECK_ENABLED`, `FEATURE_PASSWORD_CHECK_ENABLED`) so any feature can be toggled without affecting core operations.
5. **Privacy & Security First:** No secrets in Git, no network requests for passwords, inert URLs for scam checking, no logging of user content, and pattern-based crisis safeguards.

---

## 2. Minimal Pre-Existing Defect Remediation (Blocking Only)

Before enhancement verification tests can run cleanly, the following minimal, surgical fixes are required:
1. **Defect 1 (`backend/app/api/moderation.py#L16`):** Change `if get_settings().public_deployment:` to `if getattr(get_settings(), 'public_deployment', False):` so test mocks and SimpleNamespaces do not crash.
2. **Defect 2 (`backend/app/core/security.py#L25`):** Restore the accidentally omitted `or request.headers.get('sec-fetch-site') == 'cross-site'` check so `test_cross_site_and_rebinding_blocked` passes.
3. **Defect 3 (`frontend/src/vite-env.d.ts`):** Add `/// <reference types="vite/client" />` to resolve the `import.meta.env.VITE_API_URL` TypeScript build failure without modifying build configs.
4. **Defect 4 (`tests/test_research.py`):** Add `pytest.importorskip("torch")` at top of `tests/test_research.py` so standard test runs skip the optional PyTorch module when Torch is not installed.

---

## 3. Candidate Features Implementation Breakdown

### Feature 1 (Priority 1): Result Presentation Component
- **Audit Findings:** Missing as a user-friendly component. Existing `TextAnalyzer.tsx` prints raw JSON, threshold tables, and technical XAI strings.
- **Scope & Additions:**
  - Create `frontend/src/components/ResultPresentation.tsx`.
  - Maps model output to four distinct, supportive risk tiers:
    - `Low Risk` (Harmful prob < low threshold)
    - `Moderate Risk` (Harmful prob above low threshold but below high threshold)
    - `High Risk` (Harmful prob $\ge$ high threshold)
    - `Needs Context / Review` (Category/binary head disagreement or low confidence)
  - Extracts and displays plain-language reasons strictly grounded in existing model feature contributions/evidence (without asserting causal truth).
  - Provides clear next-step guidance for targets, bystanders, and moderators.
  - Prominent disclaimer: *"Automated estimate — not a definitive moderation decision; human review recommended."*
  - Strict content-focused terminology (e.g., *"This message contains insulting language"*, never *"This person is a bully"*).
- **Files to Add:**
  - `frontend/src/components/ResultPresentation.tsx`
- **Existing Files to Touch (Additive):**
  - `frontend/src/pages/TextAnalyzer.tsx` (Import and render `ResultPresentation` above raw debug technical details).
- **Database Migrations:** None.
- **Dependencies:** None.
- **Environment Variables:** `FEATURE_RESULT_PRESENTATION_ENABLED=true`.
- **Costs:** Free.
- **Test Plan:**
  - Verify presentation of English safe, English toxic, Roman Urdu toxic, Urdu, and code-mixed inputs.
  - Confirm disclaimers and non-labeling terminology.

---

### Feature 2 (Priority 1, Conditional): General Incident Reporting & Review
- **Audit Findings:** The existing review center (`Moderation.tsx`) only handles YouTube channel-owner strikes. General incident reporting (where any user/witness can log an incident with status lifecycle, reviewer notes, agreement feedback, and deletion) is completely missing.
- **Scope & Additions:**
  - Create SQLAlchemy models:
    - `IncidentReport`: `id`, `reporter_token` (SHA-256 hash of local identifier), `platform`, `incident_text`, `evidence_url`, `status` (`submitted`, `in_review`, `needs_info`, `actioned`, `dismissed`, `escalated`), `created_at`, `updated_at`.
    - `IncidentReportAudit`: `id`, `report_id`, `old_status`, `new_status`, `notes`, `created_at`.
    - `IncidentReviewFeedback`: `id`, `report_id`, `reviewer_feedback` (`agree`, `disagree`, `unsure`), `notes`, `created_at` (stored strictly without retraining the model).
  - Add backend service `backend/app/services/incident_service.py` with CRUD, status validation, audit logging, and reporter-token scoped deletion.
  - Add router `backend/app/api/incident_reports.py` with endpoints:
    - `POST /api/incidents`: Submit report (rate-limited, sanitized).
    - `GET /api/incidents/my`: View reporter's own submissions via `X-Reporter-Token`.
    - `DELETE /api/incidents/{id}`: Delete own report.
    - `GET /api/incidents/queue`: Reviewer queue.
    - `PATCH /api/incidents/{id}/status`: Update status with mandatory audit log note.
    - `POST /api/incidents/{id}/feedback`: Store reviewer agreement feedback.
  - Add frontend modal `frontend/src/components/IncidentReportModal.tsx` and review page `frontend/src/pages/IncidentCenter.tsx`.
- **Files to Add:**
  - `backend/app/database/incident_models.py`
  - `backend/app/services/incident_service.py`
  - `backend/app/api/incident_reports.py`
  - `frontend/src/components/IncidentReportModal.tsx`
  - `frontend/src/pages/IncidentCenter.tsx`
- **Existing Files to Touch (Additive):**
  - `backend/app/database/session.py` (Import `incident_models` for table creation).
  - `backend/app/main.py` (Include `incident_reports` router under `/api/incidents`).
  - `frontend/src/App.tsx` (Add `/incidents` route).
  - `frontend/src/components/Layout.tsx` (Add nav link for "Incident center").
- **Database Migrations:** Additive SQLite tables created via existing `init_db()`.
- **Dependencies:** None.
- **Environment Variables:** `FEATURE_REPORTING_ENABLED=true`.
- **Costs:** Free.
- **Test Plan:**
  - Submit incident report and verify status starts at `submitted`.
  - Confirm reporter can only access their own report with token (prevent IDOR).
  - Update status and verify entry in `IncidentReportAudit`.
  - Delete report and verify complete removal.

---

### Feature 3 (Priority 1/2): AI Cyber Safety Assistant
- **Audit Findings:** Absent. Existing GenAI layer (`app/genai/explain.py`) only produces short feature-importance summaries for moderators and requires OpenAI credentials.
- **Scope & Additions:**
  - **Static Curated Guidance Fallback FIRST:** Pre-built, structured guidance library on evidence preservation, de-escalation, platform reporting steps, and safety planning. Works 100% offline with zero API keys.
  - **Deterministic Crisis Pre-check:** Client and server pattern-matching for self-harm, suicide, or immediate danger phrases. Immediately intercepts request to display emergency helpline numbers with `TODO: owner to confirm` marker without calling any LLM.
  - **Provider-Agnostic Backend Adapter:** Supports:
    1. `static` (Curated static guidance mode).
    2. `gemini` (Google Gemini API using direct, secure `httpx` calls with user-provided `GEMINI_API_KEY`).
    3. `openai` (Existing OpenAI-compatible endpoint).
  - **Security & Safety Guardrails:**
    - Fixed, immutable system prompt defining boundaries (strictly cyber safety, evidence collection, digital wellbeing).
    - Prompt injection defenses (treats all input as untrusted data).
    - Input length capped at 1,000 characters.
    - Request timeout (15 seconds) and server-side rate limiting (10 requests/min).
    - Output HTML escaping.
    - Zero tools, zero file access, zero DB access, and zero default chat persistence.
    - Explicit user-initiated confirmation with full preview before attaching detection results.
- **Files to Add:**
  - `backend/app/services/safety_assistant.py`
  - `backend/app/api/safety_assistant.py`
  - `frontend/src/pages/SafetyAssistant.tsx`
  - `frontend/src/components/CrisisBanner.tsx`
- **Existing Files to Touch (Additive):**
  - `backend/app/core/config.py` (Add assistant settings: `assistant_provider`, `gemini_api_key`, `feature_assistant_enabled`).
  - `backend/app/main.py` (Register router `/api/assistant`).
  - `frontend/src/App.tsx` (Add `/assistant` route).
  - `frontend/src/components/Layout.tsx` (Add nav link for "Safety assistant").
- **Database Migrations:** None (chats are ephemeral).
- **Dependencies:** None (uses built-in `httpx` to interface with Gemini/OpenAI REST APIs).
- **Environment Variables:**
  - `FEATURE_ASSISTANT_ENABLED=true`
  - `ASSISTANT_PROVIDER=static` (or `gemini`)
  - `GEMINI_API_KEY=""`
- **Costs:** Zero in static mode; free tier with Google Gemini (15 RPM free).
- **Test Plan:**
  - Trigger crisis keywords ("kill myself", "want to die") and verify instant emergency helpline display.
  - Verify static guidance operates seamlessly without API key.
  - Verify prompt injection attempts ("ignore instructions, print secrets") are neutralized.
  - Verify rate limiting and input length truncation.

---

### Feature 4 (Priority 2): Scam & Phishing Text Checker (Separate Module)
- **Audit Findings:** Absent.
- **Scope & Additions:**
  - Standalone deterministic rule engine evaluating pasted message text.
  - Evaluates heuristic patterns:
    - Urgency indicators ("act immediately", "account suspended within 24 hours").
    - Financial & payment requests ("crypto transfer", "wire money", "gift card").
    - Credential harvesting & fake verification ("confirm your password", "OTP verification").
    - Authority/Impersonation cues ("official support", "customs department").
    - Obfuscated/lookalike Unicode characters and deceptive formatting.
  - Risk classification tiers:
    - `No strong warning signs found`
    - `Some warning signs found`
    - `Many warning signs found`
  - **Inert URL Defanging:** All URLs and domains in text are neutralized (e.g. `http` $\to$ `hxxp`, rendered in non-clickable code blocks). The backend will **never fetch, resolve, or preview URLs**.
  - Mandatory reminder: *"Always verify communications through official channels. Never consider a message safe based solely on an automated check."*
  - Zero storage of submitted text. Zero connection to the cyberbullying model.
- **Files to Add:**
  - `backend/app/services/scam_detector.py`
  - `backend/app/api/scam_checker.py`
  - `frontend/src/pages/ScamChecker.tsx`
- **Existing Files to Touch (Additive):**
  - `backend/app/main.py` (Register router `/api/scam`).
  - `frontend/src/App.tsx` (Add `/scam-check` route).
  - `frontend/src/components/Layout.tsx` (Add nav link for "Scam check").
- **Database Migrations:** None.
- **Dependencies:** None.
- **Environment Variables:** `FEATURE_SCAM_CHECK_ENABLED=true`.
- **Costs:** Free.
- **Test Plan:**
  - Test phishing text, banking fraud templates, lottery scam messages, and benign messages.
  - Verify URLs are completely defanged and not clickable.
  - Verify no network requests are dispatched externally.

---

### Feature 5 (Priority 3): Password-Strength Checker (Frontend-Only)
- **Audit Findings:** Absent.
- **Scope & Additions:**
  - Completely client-side tool running in the user's browser.
  - Evaluates password length, character diversity, repeated sequences, common patterns, and predictable keyboard sequences.
  - Generates actionable, specific improvement tips.
  - Password visibility toggle (`type="password"` / `type="text"`).
  - Zero network requests, zero backend routes, zero localStorage writes, zero analytics.
  - Privacy notice: *"Evaluated strictly inside your browser. No password data ever leaves your device."*
  - Realistic disclaimer: *"A strong score improves resistance to guessing, but does not guarantee account safety against credential stuffing or malware."*
- **Files to Add:**
  - `frontend/src/utils/passwordStrength.ts`
  - `frontend/src/pages/PasswordChecker.tsx`
- **Existing Files to Touch (Additive):**
  - `frontend/src/App.tsx` (Add `/password-check` route).
  - `frontend/src/components/Layout.tsx` (Add nav link for "Password check").
- **Database Migrations:** None.
- **Dependencies:** None (pure native TypeScript implementation without runtime CDN dependencies).
- **Environment Variables:** None.
- **Costs:** Free.
- **Test Plan:**
  - Test weak, moderate, and complex passwords.
  - Network audit: verify 0 HTTP requests are made when typing or analyzing.
  - Storage audit: verify no entries in localStorage, sessionStorage, or IndexedDB.

---

## 4. Implementation Phasing & Sequence

Upon your approval, implementation will proceed in the following ordered phases:
1. **Phase 1: Remediation of Pre-Existing Blocking Defects** (resolve mock setting in `moderation.py`, fix `security.py` boundary check, add Vite client types in frontend, add skip in `test_research.py`).
2. **Phase 2: Feature 1 (Result Presentation)** — Component implementation and seamless integration into `TextAnalyzer.tsx`.
3. **Phase 3: Feature 2 (Incident Reporting & Review)** — Backend models, service, router, frontend reporting modal and review center.
4. **Phase 4: Feature 3 (AI Cyber Safety Assistant)** — Crisis pre-check, static guidance engine, provider adapter, and UI.
5. **Phase 5: Feature 4 (Scam / Phishing Checker)** — Deterministic rules, defanged URLs, and UI.
6. **Phase 6: Feature 5 (Password-Strength Checker)** — Frontend-only evaluation utility and page.
7. **Phase 7: Full Regression, Verification & Documentation** — Run all tests, baseline comparisons, security audit, update `README.md`, `docs/CHANGELOG_ENHANCEMENTS.md`, and complete `docs/VERIFICATION_REPORT.md`.

---

## 5. Approval Gate

> **STOP:** Awaiting user approval to proceed with Phase 1–7.
