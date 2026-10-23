# Security audit and release boundaries

## Implemented in this audit

- Shared loopback-only API boundary, local Host/origin allowlists and cross-site request rejection.
- Request body transport cap of 2.1 MB, including bodies that misstate Content-Length.
- no-store, nosniff, frame denial and no-referrer response headers.
- Spreadsheet formula escaping for video-comment CSV exports.
- Literal escaping of comments and metadata before PDF rendering.
- Unsupported live-chat comments skipped before inference.
- External GenAI explanations require explicit ALLOW_EXTERNAL_EXPLANATIONS=true; adding a provider key alone is insufficient.
- Research paper download on the Research page; manuscript and reproducible PDF builder in the repository.

Existing protections retained: model artifact checksum validation, input URL host restrictions, bounded channel pagination, masked unsupported category heads, human review, distinct comment evidence, owner verification and action audit records.

## Scope and residual risk

This is a single-user local research prototype, not a hardened public service. Keep the backend bound to 127.0.0.1 and do not expose Vite or the API to the public internet. A local attacker can impersonate allowed clients; origin/Host checks are not login authentication. Secrets and SQLite records rely on workstation permissions. No penetration-test certification or dependency CVE clearance is claimed.

Before public deployment: add authenticated users and roles, HTTPS, managed OAuth lifecycle and encrypted token storage, rate/concurrency limits, retention/deletion policy, encrypted backups, monitoring, dependency vulnerability scans, accessibility/browser QA and independent security review. API authorization must be reviewed as a whole before changing allowed hosts or origins.

For stronger AI claims: obtain approved positive examples for six unsupported categories, validate Urdu script separately, create independent human gold data, evaluate domain drift and fairness, and repeat experiments with an untouched external set. The live model remains the category-capable baseline; the newer binary candidate remains separate.

No user comments were deleted and no external moderation actions were sent during this audit. Existing earlier cache-deletion restrictions were not bypassed.

Verification: 37 automated tests passed, frontend production build passed, real local proxy inference and paper download returned 200, and hostile-origin request returned 403. This is regression/smoke verification, not an independent penetration test.
