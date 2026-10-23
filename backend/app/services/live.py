from __future__ import annotations

import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.ml.infer import analyze_text
from app.youtube.client import YouTubeAPIError, fetch_live_chat_page, fetch_video_metadata, resolve_url

LIVE_UNAVAILABLE = "Live chat is unavailable for this video."


class LiveManager:
    def __init__(self) -> None:
        self.status = "offline"
        self.video_id: str | None = None
        self.live_chat_id: str | None = None
        self.page_token: str | None = None
        self.messages: list[dict[str, Any]] = []
        self.alerts: list[dict[str, Any]] = []
        self.seen_ids: set[str] = set()
        self.rate_window: deque[float] = deque()
        self.error: str | None = None
        self.title: str = ""

    def snapshot(self) -> dict[str, Any]:
        now = time.time()
        while self.rate_window and now - self.rate_window[0] > 60:
            self.rate_window.popleft()
        rows = self.messages
        n = len(rows)
        bullying = sum(1 for m in rows if m.get("classification") == "BULLYING")
        return {
            "status": self.status,
            "video_id": self.video_id,
            "title": self.title,
            "live_chat_id": self.live_chat_id,
            "error": self.error,
            "messages_per_minute": len(self.rate_window),
            "total_messages": n,
            "safe": sum(1 for m in rows if m.get("classification") == "SAFE"),
            "bullying": bullying,
            "harassment": sum(1 for m in rows if float((m.get("categories") or {}).get("HARASSMENT") or 0) >= 0.5),
            "threats": sum(1 for m in rows if float((m.get("categories") or {}).get("THREAT") or 0) >= 0.5),
            "high_risk": sum(1 for m in rows if m.get("risk") in {"HIGH", "CRITICAL"}),
            "uncertain": sum(1 for m in rows if m.get("classification") == "UNCERTAIN"),
            "bullying_rate": round(100.0 * bullying / n, 2) if n else None,
            "language_distribution": _count(rows, "language"),
            "confidence_distribution": _conf(rows),
            "messages": rows[-200:],
            "alerts": self.alerts[-50:],
            "trend": [
                {"t": m.get("timestamp"), "bullying": 1 if m.get("classification") == "BULLYING" else 0}
                for m in rows[-200:]
            ],
            "ethics": "AI predictions may contain errors. High-risk content should be reviewed by a human moderator.",
        }

    def start(self, url: str) -> dict[str, Any]:
        if not get_settings().youtube_enabled:
            self.status = "offline"
            self.error = "Live chat requires a YouTube API key. Demo comments are not used as live messages."
            return self.snapshot()
        try:
            vid = resolve_url(url)
            meta = fetch_video_metadata(vid)
        except YouTubeAPIError as exc:
            self.status = "offline"
            self.error = str(exc)
            return self.snapshot()
        chat_id = meta.get("live_chat_id")
        self.video_id = vid
        self.title = meta.get("title") or ""
        if not chat_id:
            self.status = "offline"
            self.live_chat_id = None
            self.error = LIVE_UNAVAILABLE
            return self.snapshot()
        self.live_chat_id = chat_id
        self.status = "live"
        self.error = None
        self.messages.clear()
        self.alerts.clear()
        self.seen_ids.clear()
        self.page_token = None
        self.poll()
        return self.snapshot()

    def pause(self) -> dict[str, Any]:
        if self.status == "live":
            self.status = "paused"
        return self.snapshot()

    def resume(self) -> dict[str, Any]:
        if self.status == "paused" and self.live_chat_id:
            self.status = "live"
        return self.snapshot()

    def stop(self) -> dict[str, Any]:
        self.status = "stopped"
        return self.snapshot()

    def poll(self) -> dict[str, Any]:
        if self.status != "live" or not self.live_chat_id:
            return self.snapshot()
        try:
            data = fetch_live_chat_page(self.live_chat_id, self.page_token)
        except YouTubeAPIError as exc:
            self.error = str(exc)
            self.status = "offline"
            return self.snapshot()
        self.page_token = data.get("nextPageToken")
        now = time.time()
        for item in data.get("items") or []:
            mid = item.get("id")
            if not mid or mid in self.seen_ids:
                continue
            self.seen_ids.add(mid)
            sn = item.get("snippet") or {}
            text = sn.get("displayMessage") or sn.get("textMessageDetails", {}).get("messageText") or ""
            from app.youtube.validation import supported_comments
            if not supported_comments([{'text': text}])[0]:
                continue
            pred = analyze_text(text, include_xai=True)
            msg = {
                "id": mid,
                "timestamp": sn.get("publishedAt") or datetime.now(timezone.utc).isoformat(),
                "original_text": text,
                **{k: pred[k] for k in pred if k != "original_text"},
            }
            self.messages.append(msg)
            self.rate_window.append(now)
            if self._should_alert(msg):
                self.alerts.append(
                    {
                        "alert": "High-risk live message",
                        "message": text,
                        "category": msg.get("primary_category"),
                        "classification": msg.get("classification"),
                        "confidence": msg.get("confidence"),
                        "language": msg.get("language"),
                        "xai": (msg.get("xai") or {}).get("structured_evidence"),
                    }
                )
        return self.snapshot()

    def _should_alert(self, msg: dict[str, Any]) -> bool:
        threat = float((msg.get("categories") or {}).get("THREAT") or 0)
        if threat >= 0.75 and msg.get("confidence", 0) >= 0.75:
            return True
        if msg.get("risk") in {"HIGH", "CRITICAL"} and msg.get("confidence", 0) >= 0.75:
            return True
        recent = self.messages[-30:]
        if len(recent) >= 12:
            rate = sum(1 for m in recent if m.get("classification") == "BULLYING") / len(recent)
            if rate >= 0.45 and msg.get("classification") == "BULLYING":
                return True
        return False


def _count(rows, key):
    out: dict[str, int] = {}
    for r in rows:
        out[r.get(key) or "Unknown"] = out.get(r.get(key) or "Unknown", 0) + 1
    return out


def _conf(rows):
    buckets = {"0-0.4": 0, "0.4-0.55": 0, "0.55-0.75": 0, "0.75-1.0": 0}
    for r in rows:
        c = float(r.get("confidence") or 0)
        if c < 0.4:
            buckets["0-0.4"] += 1
        elif c < 0.55:
            buckets["0.4-0.55"] += 1
        elif c < 0.75:
            buckets["0.55-0.75"] += 1
        else:
            buckets["0.75-1.0"] += 1
    return buckets


manager = LiveManager()
