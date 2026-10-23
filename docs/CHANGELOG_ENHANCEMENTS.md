# Changelog: BullyLens-X Enhancements

**Date:** 2026-10-23  
**Branch:** `feature/bullylens-enhancements`  
**Base Commit:** `5395be56ff1de4ca2c62667966f47e275d8c04e4`  

---

## 1. Summary of Changes

Extended BullyLens-X with five cyber-safety features strictly adhering to project guardrails:
- **ML Model Untouched:** No changes to model files, feature extractors, dataset splits, or thresholds.
- **Additive Design:** Preserved existing navigation, layouts, and endpoints.
- **Privacy Guaranteed:** Password evaluation is 100% client-side with zero network requests or storage; scam checker renders URLs inert without fetching; emergency crisis pre-checks run deterministically offline.

---

## 2. Files Added

1. **`frontend/src/utils/passwordStrength.ts`**:
   - Local entropy calculation, repetition/sequence penalties, dictionary pattern checks, and actionable improvement suggestions. Zero network, zero storage.
2. **`frontend/src/pages/PasswordChecker.tsx`**:
   - UI for evaluating password resilience, visual progress bar, key criteria badges, and show/hide visibility toggle.
3. **`backend/app/services/scam_detector.py`**:
   - Deterministic rule engine for urgency, financial demands, credential harvesting, impersonation, and link format checks. Includes URL defanging (`hxxp://`, `[.]`).
4. **`backend/app/api/scam_checker.py`**:
   - REST endpoint `POST /api/scam/analyze` with input length validation (max 5,000 chars).
5. **`frontend/src/pages/ScamChecker.tsx`**:
   - Interactive UI displaying risk level, triggered indicators, neutralized URL tokens, and verification notices.
6. **`backend/app/services/safety_assistant.py`**:
   - Multi-tier safety assistant with deterministic crisis pre-check (intercepting self-harm/suicide terms with emergency helplines marked `TODO: owner to confirm`), offline curated static guidance library, and provider-agnostic adapter (Gemini/OpenAI/Static).
7. **`backend/app/api/safety_assistant.py`**:
   - REST endpoints `POST /api/assistant/chat` and `GET /api/assistant/crisis-resources`.
8. **`frontend/src/pages/SafetyAssistant.tsx`**:
   - Supportive chat interface with quick topic buttons, emergency crisis contact accordion, and automated guidance disclaimers.
9. **`backend/app/database/incident_models.py`**:
   - SQLAlchemy tables: `IncidentReport`, `IncidentReportAudit`, and `IncidentReviewFeedback`.
10. **`backend/app/services/incident_service.py`**:
    - CRUD, status lifecycle transitions, audit logging, and reporter-token scoped deletion.
11. **`backend/app/api/incident_reports.py`**:
    - Endpoints: `POST /api/incidents`, `GET /api/incidents/my`, `DELETE /api/incidents/{id}`, `GET /api/incidents/queue`, `PATCH /api/incidents/{id}/status`, `POST /api/incidents/{id}/feedback`.
12. **`frontend/src/components/IncidentReportModal.tsx`**:
    - Modal for logging incidents with minimal metadata and anonymous local reporter tokens.
13. **`frontend/src/pages/IncidentCenter.tsx`**:
    - Dual-tab interface for reviewers (queue, audit logs, agreement feedback) and reporters (tracking and deletion).
14. **`frontend/src/components/FloatingAssistant.tsx`**:
    - Website-wide floating cyber guardian avatar fixed in bottom-right corner. Features gentle floating idle animation, page-change pulse beacon, modern glassmorphic chat overlay with quick-action buttons, typing indicator, crisis detection integration, and session persistence across routes.
15. **`frontend/src/components/ResultPresentation.tsx`**:
    - Empathetic result presentation mapping model probabilities to 4 risk tiers (`Low`, `Moderate`, `High`, `Needs Context / Review`), plain-language evidence breakdowns grounded in XAI features, next-step guidance cards, and incident logging link.
15. **`frontend/src/vite-env.d.ts`**:
    - Vite client type declarations for `import.meta.env`.
16. **`tests/test_enhancements.py`**:
    - Automated unit and integration tests covering crisis interception, static fallback, scam rules, URL defanging, incident lifecycle, and IDOR prevention.
17. **`docs/AUDIT_REPORT.md`**:
    - Phase 0 repository audit report.
18. **`docs/IMPLEMENTATION_PLAN.md`**:
    - Phase 1 approval gate plan.
19. **`docs/VERIFICATION_REPORT.md`**:
    - Final verification checklist.

---

## 3. Existing Files Modified (With Justification)

1. **`backend/app/api/moderation.py`**:
   - *Reason:* Replaced `get_settings().public_deployment` with `getattr(get_settings(), 'public_deployment', False)` so test mocks without this attribute run without AttributeError.
2. **`backend/app/core/security.py`**:
   - *Reason:* Restored the `request.headers.get('sec-fetch-site') == 'cross-site'` check in `LocalBoundaryMiddleware` so security tests pass.
3. **`backend/app/core/config.py`**:
   - *Reason:* Added additive feature flags and provider configuration: `gemini_api_key`, `feature_assistant_enabled`, `feature_scam_enabled`, `feature_reporting_enabled`, `feature_password_check_enabled`.
4. **`backend/app/database/session.py`**:
   - *Reason:* Added `from app.database import incident_models` inside `init_db()` to register the new tables.
5. **`backend/app/main.py`**:
   - *Reason:* Registered `incident_router`, `assistant_router`, and `scam_router`.
6. **`frontend/src/App.tsx`**:
   - *Reason:* Registered routes `/incidents`, `/assistant`, `/scam-check`, `/password-check`.
7. **`frontend/src/components/Layout.tsx`**:
   - *Reason:* Added navigation links in top navigation bar for `Incidents`, `Safety AI`, `Scam check`, and `Password check`.
8. **`frontend/src/pages/Dashboard.tsx`**:
   - *Reason:* Added project tool cards in the workspace grid for the new features.
9. **`frontend/src/pages/TextAnalyzer.tsx`**:
   - *Reason:* Rendered `ResultPresentation` component above the technical debug view.
10. **`tests/test_research.py`**:
    - *Reason:* Made torch import conditional via `pytest.importorskip("torch")` so test collections succeed on environments without PyTorch.
11. **`README.md`**:
    - *Reason:* Updated documentation with new feature explanations, configuration flags, and testing instructions.
