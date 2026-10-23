# Channel scanning

Open http://localhost:5173/youtube. Enter a public channel URL or @handle and choose up to 500 comments. The scanner resolves the channel through channels.list and requests commentThreads.list using allThreadsRelatedToChannelId. Requests are bounded to five comment pages, ordered by time. Only top-level comments are analyzed; replies, private/deleted comments and global commenting histories are excluded. An API key is required; this route never substitutes demo comments.

Results show commenters, their comments and AI harmful flags. Search, flagged-only filtering, pagination, JSON download and links to YouTube context are available. Review center stores human decisions. Three distinct human-confirmed harmful comments in one channel indicate repeated behavior in the collected evidence. Rescans do not add strikes, and changed text resets review. This is not a definitive label that someone is a cyberbully or habitual offender. The model's validated category coverage is limited; see the research page.

Read-only scans can examine public comments associated with another channel. Posting warnings and channel-level blocks still require owner OAuth, ownership verification and explicit human confirmation. The app cannot suspend YouTube accounts. No warnings or blocks were sent during implementation.

The dashboard includes a decorative rotating radar, route entrances, modal transitions and hover effects. Radar dots are decorative, not detected people or threats. Counts stay empty until a real scan completes. Operating-system reduced-motion preferences disable animations.

Verification: 29 automated tests passed and frontend production build passed on 2026-08-31. Public API pagination was tested with mocked YouTube responses. A live scan of @example returned 50 real comments through the configured API key; no warnings or blocks were sent. In-app browser visual inspection was unavailable due to its localhost access policy.

Cleanup: deletion of regenerable .pip-cache, .pytest_cache and .ruff_cache directories was attempted but blocked by environment policy. No successful bulk cleanup is claimed. Datasets, models, source, research reports, database and backup remain intact.

API reference: https://developers.google.com/youtube/v3/docs/commentThreads/list
