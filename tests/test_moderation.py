from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.api import moderation
from app.database.session import Base, get_db
from app.services.moderation import observe


@pytest.fixture
def system(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    app = FastAPI()
    app.include_router(moderation.router)
    app.dependency_overrides[get_db] = lambda: db
    monkeypatch.setattr(
        moderation, "get_settings", lambda: SimpleNamespace(youtube_oauth_access_token="", youtube_owner_channel_id="")
    )
    yield TestClient(app), db
    db.close()
    engine.dispose()


def seed(db, n=1):
    raw = [
        dict(id=f"comment{i}", text="A comment for human review", author_id="author", author_name="Example author")
        for i in range(n)
    ]
    video = dict(video_id="video", channel_id="owner")
    predictions = [{"binary_prediction": "HARMFUL"}] * n
    observe(db, video, raw, predictions)
    return video, raw, predictions


def test_rescanning_and_demo_are_not_strikes(system):
    client, db = system
    args = seed(db, 3)
    observe(db, *args)
    observe(db, args[0], [dict(args[1][0], id="demo")], [args[2][0]], demo=True)
    author = client.get("/authors").json()["authors"][0]
    assert author["total"] == 3 and author["confirmed"] == 0 and not author["repeat"]
    for row in author["comments"]:
        assert client.post(f"/comments/{row['id']}/review", json={"decision": "harmful"}).status_code == 200
    assert client.get("/authors").json()["authors"][0]["repeat"]
    client.post("/comments/1/review", json={"decision": "safe"})
    assert not client.get("/authors").json()["authors"][0]["repeat"]


def test_owner_confirmation_and_origin_required(system):
    client, db = system
    seed(db)
    assert client.post("/comments/1/action", json={"action": "warn"}).status_code == 422
    assert client.post("/comments/1/action", json={"action": "warn", "confirmed": True}).status_code == 409
    client.post("/comments/1/review", json={"decision": "harmful"})
    assert client.post("/comments/1/action", json={"action": "warn", "confirmed": True}).status_code == 403
    assert (
        client.post(
            "/comments/1/review", json={"decision": "safe"}, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )


def test_channel_action_checks_ownership_and_is_idempotent(system, monkeypatch):
    client, db = system
    seed(db, 3)
    for i in [1, 2, 3]:
        client.post(f"/comments/{i}/review", json={"decision": "harmful"})
    monkeypatch.setattr(
        moderation,
        "get_settings",
        lambda: SimpleNamespace(youtube_oauth_access_token="test-only-token", youtube_owner_channel_id="owner"),
    )
    calls = []

    def fake_request(client, method, path, **kwargs):
        calls.append((method, path, kwargs))
        if path == "channels":
            return {"items": [{"id": "owner"}]}
        if path == "videos":
            return {"items": [{"snippet": {"channelId": "owner"}}]}
        if path == "comments" and method == "GET":
            return {
                "items": [
                    {
                        "snippet": {
                            "videoId": "video",
                            "authorChannelId": {"value": "author"},
                            "textOriginal": "A comment for human review",
                        }
                    }
                ]
            }
        return {}

    monkeypatch.setattr(moderation, "youtube_request", fake_request)
    response = client.post("/comments/1/action", json={"action": "ban_author", "confirmed": True})
    assert response.status_code == 200
    assert calls[-1][2]["params"]["banAuthor"] == "true"
    assert calls[-1][2]["params"]["moderationStatus"] == "rejected"
    assert client.post("/comments/1/action", json={"action": "ban_author", "confirmed": True}).status_code == 409
    assert client.get("/authors").json()["actions"][0]["status"] == "succeeded"


def test_block_needs_three_reviews(system, monkeypatch):
    client, db = system
    seed(db)
    client.post("/comments/1/review", json={"decision": "harmful"})
    monkeypatch.setattr(
        moderation,
        "get_settings",
        lambda: SimpleNamespace(youtube_oauth_access_token="test", youtube_owner_channel_id="owner"),
    )
    assert client.post("/comments/1/action", json={"action": "ban_author", "confirmed": True}).status_code == 409
