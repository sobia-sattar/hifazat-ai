# YouTube moderation and repeat-pattern review

The application does not suspend YouTube accounts. It can post a public warning reply, reject a comment, or reject future comments by an author on an owned channel using YouTube's `banAuthor` option. Live chat observation is separate and does not create comment strikes.

1. Add a read-only `YOUTUBE_API_KEY` to `.env` and analyze real video comments. New scans collect author channel IDs, author display names, video IDs and owner channel IDs. Existing scans without identities and sample data are excluded; no identity is inferred from comment text.
2. The Review center groups observations by owner channel and author. A repeated scan of one YouTube comment never counts twice. AI flags are distinct from confirmed strikes. Confirm or dismiss each comment after reading its context. Three distinct, human-confirmed harmful comments create a repeated-pattern flag. This is a review rule, not proof about the person's general behavior.
3. Warning drafts can be copied without a YouTube connection. Copying never sends anything.
4. To enable external actions, obtain an OAuth access token as the channel owner with scope `https://www.googleapis.com/auth/youtube.force-ssl`. Set `YOUTUBE_OAUTH_ACCESS_TOKEN` and `YOUTUBE_OWNER_CHANNEL_ID` in `.env` and restart the backend. An API key alone is insufficient. See https://developers.google.com/youtube/v3/guides/authentication . Access tokens expire; this local prototype does not implement a refresh-token vault or multi-user sign-in.
5. Every external action requires a reviewed comment and an explicit confirmation dialog. Channel blocking additionally requires three confirmed comments. The server verifies the OAuth identity owns the channel and rechecks the current video/comment/author identity before submitting. Scope is always the owned channel, never an entire YouTube account.

Audit records distinguish pending, succeeded, failed, and uncertain submissions. A network failure after submission can have an unknown outcome; inspect YouTube before attempting another action. Submitted/uncertain actions are not blindly retried. This feature is local-workstation-only, with loopback and origin checks. Do not expose the backend publicly without proper user authentication, authorization, CSRF protection, a secure credential store, retention rules and a concurrency-safe work queue.

No real warning, rejection or block was performed during development. External requests were mocked in tests. Actual operation still requires valid owner credentials, quota and YouTube approval.

Official method references:
- https://developers.google.com/youtube/v3/docs/comments/setModerationStatus
- https://developers.google.com/youtube/v3/docs/comments/insert

The UI styling is inspired by the blue palette and glass-panel treatment of the supplied CyberSafe reference. No Behance artwork, logos, testimonials or performance claims were copied. Research outputs and model artifacts are unchanged.
