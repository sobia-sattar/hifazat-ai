from types import SimpleNamespace
import httpx
import pytest
from app.api import channel_scan as scan


@pytest.mark.parametrize('value', ['https://evil.test/@person', 'https://youtube.com/watch?v=abc', 'a name', 'https://youtube.com.evil.test/@person'])
def test_reject_non_channel_inputs(value):
    with pytest.raises(ValueError):
        scan.channel_filter(value)


def test_resolve_handle_tabs_and_ids():
    assert scan.channel_filter('https://www.youtube.com/@example/videos') == {'forHandle': '@example'}
    assert scan.channel_filter('UC' + 'a'*22) == {'id': 'UC' + 'a'*22}
    assert scan.channel_filter('youtube.com/user/example') == {'forUsername': 'example'}


def test_channel_pagination_deduplication_and_scope(monkeypatch):
    requests = []
    def handle(request):
        requests.append(request)
        if request.url.path.endswith('/channels'):
            return httpx.Response(200, json={'items': [{'id': 'channel', 'snippet': {'title': 'Example'}}]})
        assert request.url.params['allThreadsRelatedToChannelId'] == 'channel'
        assert 'videoId' not in request.url.params
        second = 'pageToken' in request.url.params
        def comment(id):
            return {'snippet': {'videoId': 'video', 'topLevelComment': {'id': id, 'snippet': {
                'textOriginal': 'Public comment', 'authorChannelId': {'value': 'person'}, 'authorDisplayName': 'Person'}}}}
        return httpx.Response(200, json={'items': [comment('one'), comment('two')] if second else [comment('one')], 'nextPageToken': 'page3' if second else 'page2'})
    real_client = httpx.Client
    monkeypatch.setattr(scan, '_key', lambda: 'test-key')
    monkeypatch.setattr(scan.httpx, 'Client', lambda **kw: real_client(transport=httpx.MockTransport(handle), **kw))
    channel, comments, more = scan.collect_channel('@example', 2)
    assert channel['id'] == 'channel'
    assert [c['id'] for c in comments] == ['one', 'two']
    assert comments[0]['author_id'] == 'person' and more
    assert len(requests) == 3


def test_scan_persists_evidence_without_auto_reviews(monkeypatch):
    comments = [{'id': 'c', 'video_id': 'v', 'author_id': 'p', 'text': 'text'},
                {'text': ' '}, {'text': 'x' * 8001}, {'text': None}]
    monkeypatch.setattr(scan, 'collect_channel', lambda *args: ({'id': 'owner', 'name': 'Owner'}, comments, False))
    monkeypatch.setattr(scan, 'analyze_batch', lambda texts, include_xai: [{'binary_prediction': 'HARMFUL', 'confidence': .9}])
    observations = []
    monkeypatch.setattr(scan, 'observe', lambda *args: observations.append(args))
    result = scan.scan(scan.ChannelScan(channel='@owner'), SimpleNamespace())
    assert result['comments'][0]['harmful']
    assert len(result['comments']) == 1 and result['skipped'] == 3
    assert observations[0][1] == {'channel_id': 'owner', 'video_id': 'v'}
    assert 'decision' not in result['comments'][0]


def test_all_unsupported_comments_return_empty_scan(monkeypatch):
    monkeypatch.setattr(scan, 'collect_channel', lambda *args: ({'id': 'owner'}, [{'text': ''}], False))
    monkeypatch.setattr(scan, 'analyze_batch', lambda *args, **kwargs: pytest.fail('Must not predict empty inputs'))
    result = scan.scan(scan.ChannelScan(channel='@owner'), SimpleNamespace())
    assert result['comments'] == [] and result['skipped'] == 1


def test_channel_link_in_video_form_has_actionable_error():
    from app.youtube.url import extract_video_id, YouTubeURLError
    with pytest.raises(YouTubeURLError, match='Use Channel scan'):
        extract_video_id('https://youtube.com/@example')
    assert extract_video_id('https://youtu.be/abcdefghijk?si=share') == 'abcdefghijk'
