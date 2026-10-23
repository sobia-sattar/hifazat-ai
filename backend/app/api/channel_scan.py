"""Bounded public channel scans; never a user's global commenting history."""
import re
from urllib.parse import urlparse, unquote
from collections import defaultdict

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.youtube.client import API, _key, YouTubeAPIError
from app.ml.infer import analyze_batch
from app.services.moderation import observe
from app.youtube.validation import supported_comments

router = APIRouter()


class ChannelScan(BaseModel):
    channel: str = Field(min_length=2, max_length=500)
    max_comments: int = Field(default=100, ge=1, le=500)


def channel_filter(value):
    value = value.strip()
    if value.startswith(('http://', 'https://', 'www.', 'youtube.com/')):
        parsed = urlparse(value if '://' in value else 'https://' + value)
        if parsed.hostname not in {'youtube.com', 'www.youtube.com', 'm.youtube.com'}:
            raise ValueError('Use a youtube.com channel URL or @handle.')
        value = unquote(parsed.path).strip('/')
        parts = value.split('/')
        if parts[0] == 'channel' and len(parts) >= 2:
            value = parts[1]
        elif parts[0] == 'user' and len(parts) >= 2:
            return {'forUsername': parts[1]}
        elif parts[0].startswith('@'):
            value = parts[0]
        else:
            raise ValueError('Use the channel @handle or /channel/UC… link, not a video link.')
    if re.fullmatch(r'UC[\w-]{22}', value):
        return {'id': value}
    if value.startswith('@') and len(value) > 1 and not any(c.isspace() or c in '/?#' for c in value):
        return {'forHandle': value}
    raise ValueError('Enter a channel @handle or a YouTube channel URL.')


def collect_channel(value, limit):
    selector = channel_filter(value)
    key = _key()
    with httpx.Client(timeout=25) as client:
        response = client.get(API + '/channels', params={'part': 'snippet', **selector, 'key': key})
        response.raise_for_status()
        items = response.json().get('items', [])
        if not items:
            raise ValueError('Channel not found. Check its @handle.')
        channel = {'id': items[0]['id'], 'name': items[0]['snippet']['title']}
        comments, seen, page = [], set(), None
        # Bound requests even if YouTube returns empty or duplicate pages.
        for _ in range(5):
            params = {'part': 'snippet', 'allThreadsRelatedToChannelId': channel['id'],
                      'maxResults': min(100, limit-len(comments)), 'textFormat': 'plainText',
                      'order': 'time', 'key': key}
            if page:
                params['pageToken'] = page
            response = client.get(API + '/commentThreads', params=params)
            response.raise_for_status()
            payload = response.json()
            for item in payload.get('items', []):
                thread = item.get('snippet', {})
                top = thread.get('topLevelComment', {})
                sn = top.get('snippet', {})
                if not top.get('id') or top['id'] in seen:
                    continue
                seen.add(top['id'])
                comments.append({'id': top['id'], 'video_id': thread.get('videoId') or sn.get('videoId', ''),
                                 'text': sn.get('textOriginal') or sn.get('textDisplay', ''),
                                 'author_id': sn.get('authorChannelId', {}).get('value'),
                                 'author_name': sn.get('authorDisplayName', 'Unknown commenter')})
                if len(comments) == limit:
                    break
            page = payload.get('nextPageToken')
            if not page or len(comments) >= limit:
                break
    return channel, comments, bool(page)


@router.post('/youtube/channel/scan')
def scan(body: ChannelScan, db: Session = Depends(get_db)):
    chan_str = body.channel.strip().lower()
    if chan_str in ('demo', '@demo', 'sample', '@sample', 'demo channel') or chan_str.startswith(('demo', '@demo')):
        from app.services.analysis import load_demo_bundle
        video, raw_comments = load_demo_bundle()
        channel = {'id': 'DEMO_CHANNEL_01', 'name': 'HIFAZAT AI Demo Channel'}
        comments = []
        for i, c in enumerate(raw_comments[:body.max_comments]):
            comments.append({
                'id': c.get('id', f'demo_{i}'),
                'video_id': video.get('video_id', 'DEMO0000000'),
                'text': c.get('text', ''),
                'author_id': f'user_{i % 5}',
                'author_name': f'Demo User {i % 5 + 1}',
            })
        has_more = False
    else:
        try:
            channel, comments, has_more = collect_channel(body.channel, body.max_comments)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        except YouTubeAPIError as exc:
            raise HTTPException(503, 'Connect a YouTube API key in server settings to scan real channels. No sample comments were substituted.') from exc
        except httpx.HTTPError as exc:
            raise HTTPException(502, 'YouTube could not return comments. Check API quota, access, and channel availability, then retry.') from exc
    comments, skipped = supported_comments(comments)
    predictions = analyze_batch([c['text'] for c in comments], include_xai=False) if comments else []
    grouped = defaultdict(list)
    for raw, pred in zip(comments, predictions):
        grouped[raw['video_id']].append((raw, pred))
    for video_id, pairs in grouped.items():
        observe(db, {'channel_id': channel['id'], 'video_id': video_id},
                [p[0] for p in pairs], [p[1] for p in pairs])
    return {'channel': channel, 'has_more': has_more, 'limit': body.max_comments, 'skipped': skipped,
            'comments': [{**c, 'harmful': p.get('binary_prediction') == 'HARMFUL',
                          'confidence': p.get('confidence')} for c, p in zip(comments, predictions)]}
