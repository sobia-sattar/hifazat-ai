from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.youtube.url import YouTubeURLError, extract_video_id

API = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(RuntimeError):
    def __init__(self, message: str, code: str = "youtube_error"):
        super().__init__(message)
        self.code = code


def _key() -> str:
    key = get_settings().youtube_api_key.strip()
    if not key:
        raise YouTubeAPIError("YouTube API key is not configured.", "missing_key")
    return key


def fetch_video_metadata(video_id: str) -> dict[str, Any]:
    params = {"part": "snippet,statistics,status,liveStreamingDetails", "id": video_id, "key": _key()}
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(f"{API}/videos", params=params)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 403:
            raise YouTubeAPIError("YouTube API quota exceeded or access denied.", "quota") from exc
        raise YouTubeAPIError("YouTube API request failed.", "network") from exc
    except httpx.HTTPError as exc:
        raise YouTubeAPIError("Network failure while contacting YouTube.", "network") from exc

    items = data.get("items") or []
    if not items:
        raise YouTubeAPIError("Video is private, deleted, or does not exist.", "not_found")
    item = items[0]
    sn = item.get("snippet") or {}
    thumbs = sn.get("thumbnails") or {}
    thumb = (thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url", "")
    live = item.get("liveStreamingDetails") or {}
    return {
        "video_id": video_id,
        "title": sn.get("title") or "",
        "channel": sn.get("channelTitle") or "",
        "channel_id": sn.get("channelId") or "",
        "published_at": sn.get("publishedAt"),
        "thumbnail_url": thumb,
        "live_chat_id": live.get("activeLiveChatId"),
        "statistics": item.get("statistics") or {},
    }


def fetch_comments(video_id: str, max_comments: int = 200) -> list[dict[str, Any]]:
    comments: list[dict[str, Any]] = []
    page = None
    try:
        with httpx.Client(timeout=25.0) as client:
            while len(comments) < max_comments:
                params = {
                    "part": "snippet",
                    "videoId": video_id,
                    "maxResults": min(100, max_comments - len(comments)),
                    "textFormat": "plainText",
                    "order": "time",
                    "key": _key(),
                }
                if page:
                    params["pageToken"] = page
                r = client.get(f"{API}/commentThreads", params=params)
                if r.status_code == 403:
                    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                    reason = str(body)
                    if "commentsDisabled" in reason or "disabled" in reason.lower():
                        raise YouTubeAPIError("Comments are disabled for this video.", "disabled")
                    if "quota" in reason.lower():
                        raise YouTubeAPIError("YouTube API quota exceeded.", "quota")
                    raise YouTubeAPIError("YouTube API access denied.", "forbidden")
                r.raise_for_status()
                data = r.json()
                for item in data.get("items") or []:
                    sn = ((item.get("snippet") or {}).get("topLevelComment") or {}).get("snippet") or {}
                    comments.append(
                        {
                            "id": (item.get("snippet") or {}).get("topLevelComment", {}).get("id"),
                            "text": sn.get("textDisplay") or sn.get("textOriginal") or "",
                            "published_at": sn.get("publishedAt"),
                            "author_id": (sn.get("authorChannelId") or {}).get("value"),
                            "author_name": sn.get("authorDisplayName") or "",
                        }
                    )
                    if len(comments) >= max_comments:
                        break
                page = data.get("nextPageToken")
                if not page:
                    break
    except YouTubeAPIError:
        raise
    except httpx.HTTPError as exc:
        raise YouTubeAPIError("Network failure while retrieving comments.", "network") from exc
    return [c for c in comments if (c.get("text") or "").strip()]


def fetch_live_chat_page(live_chat_id: str, page_token: str | None = None) -> dict[str, Any]:
    params = {
        "part": "snippet,authorDetails",
        "liveChatId": live_chat_id,
        "maxResults": 200,
        "key": _key(),
    }
    if page_token:
        params["pageToken"] = page_token
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(f"{API}/liveChat/messages", params=params)
            if r.status_code == 403:
                raise YouTubeAPIError("Live chat is unavailable or API access was denied.", "live_unavailable")
            r.raise_for_status()
            return r.json()
    except YouTubeAPIError:
        raise
    except httpx.HTTPError as exc:
        raise YouTubeAPIError("Network failure while reading live chat.", "network") from exc


def resolve_url(url: str) -> str:
    try:
        return extract_video_id(url)
    except YouTubeURLError as exc:
        raise YouTubeAPIError(str(exc), "invalid_url") from exc
