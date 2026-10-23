import re
from urllib.parse import parse_qs, urlparse

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


class YouTubeURLError(ValueError):
    pass


def extract_video_id(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        raise YouTubeURLError("YouTube URL is required.")
    if VIDEO_ID_RE.fullmatch(raw):
        return raw
    if not re.match(r"^https?://", raw, re.I):
        raw = "https://" + raw
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if host not in YOUTUBE_HOSTS:
        raise YouTubeURLError("Invalid YouTube URL.")
    if parsed.path.startswith(('/@', '/channel/', '/user/', '/c/')):
        raise YouTubeURLError('This is a channel link. Use Channel scan for this URL, or paste a video watch, Shorts, or youtu.be link here.')
    if host.endswith("youtu.be"):
        vid = parsed.path.lstrip("/").split("/")[0]
        if VIDEO_ID_RE.fullmatch(vid):
            return vid
        raise YouTubeURLError("Could not extract a video ID from this URL.")
    if parsed.path.startswith("/watch"):
        vid = parse_qs(parsed.query).get("v", [""])[0]
        if VIDEO_ID_RE.fullmatch(vid):
            return vid
    if parsed.path.startswith(("/embed/", "/shorts/", "/live/")):
        vid = parsed.path.strip("/").split("/")[1] if "/" in parsed.path.strip("/") else ""
        if VIDEO_ID_RE.fullmatch(vid):
            return vid
    raise YouTubeURLError("Could not extract a video ID from this URL.")
