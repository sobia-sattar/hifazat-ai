"""Comprehensive automated tests for BullyLens Enhancements (F1-F5)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.main import app
from app.services.safety_assistant import check_crisis, ask_assistant
from app.services.scam_detector import analyze_scam_text, defang_url


@pytest.fixture
def test_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    yield client
    db.close()
    engine.dispose()
    app.dependency_overrides.clear()


# ============================================================================
# F3: AI Cyber Safety Assistant Tests
# ============================================================================

def test_crisis_detector_triggers_on_self_harm():
    assert check_crisis("I want to kill myself") is True
    assert check_crisis("thinking about suicide") is True
    assert check_crisis("main khudkushi karna chahta hoon") is True
    assert check_crisis("Just asking how to block a harasser") is False


def test_assistant_returns_emergency_resources_on_crisis():
    res = ask_assistant("I feel like I want to end my life")
    assert res["is_crisis"] is True
    assert "crisis_resources" in res
    assert len(res["crisis_resources"]) > 0
    # Must contain owner confirmation marker
    assert any("TODO: owner to confirm" in r["confirmation_status"] for r in res["crisis_resources"])


def test_assistant_static_curated_guidance_fallback():
    # In absence of API key, static mode must function smoothly
    res = ask_assistant("How do I save screenshots of abusive comments?")
    assert res["is_crisis"] is False
    assert res["source"] in {"static_curated", "static_fallback"}
    assert "Screenshots" in res["reply"] or "Evidence" in res["reply"] or "Preserving" in res["reply"]
    assert "AI assistant guidance" in res["notice"]


def test_assistant_api_endpoint(test_client):
    res = test_client.post("/api/assistant/chat", json={"message": "How do I report harassment?"})
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "notice" in data


def test_assistant_crisis_resources_endpoint(test_client):
    res = test_client.get("/api/assistant/crisis-resources")
    assert res.status_code == 200
    data = res.json()
    assert "resources" in data
    assert len(data["resources"]) >= 2


# ============================================================================
# F4: Scam / Phishing Detection Tests
# ============================================================================

def test_url_defanging():
    assert defang_url("http://example.com/login") == "hxxp://example[.]com/login"
    assert defang_url("https://secure-bank.xyz/verify") == "hxxps://secure-bank[.]xyz/verify"


def test_scam_detector_identifies_urgency_and_credentials():
    suspicious = "URGENT: Your account is suspended. Enter your password immediately at http://verify-account.top"
    result = analyze_scam_text(suspicious)
    assert result["risk_class"] in {"MEDIUM", "HIGH"}
    assert any(r["id"] == "urgency" for r in result["triggered_rules"])
    assert any(r["id"] == "credentials" for r in result["triggered_rules"])
    assert len(result["defanged_urls"]) > 0
    assert "hxxp" in result["defanged_urls"][0]["defanged"]


def test_scam_detector_clean_message():
    clean = "Hey, are we still meeting tomorrow for coffee?"
    result = analyze_scam_text(clean)
    assert result["risk_level"] == "No strong warning signs found"
    assert result["score"] == 0
    assert len(result["triggered_rules"]) == 0


def test_scam_api_endpoint(test_client):
    res = test_client.post("/api/scam/analyze", json={"text": "Act now or legal action within 24 hours. Send crypto."})
    assert res.status_code == 200
    data = res.json()
    assert data["risk_class"] in {"MEDIUM", "HIGH"}
    assert "notice" in data


# ============================================================================
# F2: Incident Reporting & Review Tests
# ============================================================================

def test_incident_reporting_lifecycle_and_isolation(test_client):
    reporter_token = "test_reporter_token_123"
    headers = {"X-Reporter-Token": reporter_token}

    # 1. Submit incident report
    res = test_client.post(
        "/api/incidents",
        headers=headers,
        json={
            "platform": "youtube",
            "incident_text": "Targeted hateful harassment comment",
            "evidence_url": "https://youtube.com/watch?v=123",
            "reporter_notes": "Repeated across three videos",
        },
    )
    assert res.status_code == 200
    report_id = res.json()["id"]

    # 2. View my reports
    res = test_client.get("/api/incidents/my", headers=headers)
    assert res.status_code == 200
    my_list = res.json()
    assert len(my_list) == 1
    assert my_list[0]["id"] == report_id
    assert my_list[0]["status"] == "submitted"

    # 3. Queue view for reviewers
    res = test_client.get("/api/incidents/queue")
    assert res.status_code == 200
    queue = res.json()
    assert any(item["id"] == report_id for item in queue)

    # 4. Status update with audit entry
    res = test_client.patch(
        f"/api/incidents/{report_id}/status",
        json={"status": "in_review", "notes": "Investigating platform evidence"},
    )
    assert res.status_code == 200
    assert res.json()["new_status"] == "in_review"

    # 5. Reviewer agreement feedback (stored only, does not affect model)
    res = test_client.post(
        f"/api/incidents/{report_id}/feedback",
        json={"feedback": "agree", "notes": "Confirmed targeted violation"},
    )
    assert res.status_code == 200
    assert res.json()["feedback"] == "agree"

    # 6. Delete report by owner
    res = test_client.delete(f"/api/incidents/{report_id}", headers=headers)
    assert res.status_code == 200

    # Verify deleted
    res = test_client.get("/api/incidents/my", headers=headers)
    assert len(res.json()) == 0


def test_incident_deletion_rejects_unauthorized_token(test_client):
    # Reporter A creates report
    res = test_client.post(
        "/api/incidents",
        headers={"X-Reporter-Token": "token_a"},
        json={"platform": "instagram", "incident_text": "Abusive DM"},
    )
    report_id = res.json()["id"]

    # Reporter B tries to delete Reporter A's report
    res = test_client.delete(f"/api/incidents/{report_id}", headers={"X-Reporter-Token": "token_b"})
    assert res.status_code == 403


# ============================================================================
# F5: Password Check Security & Privacy Architecture Tests
# ============================================================================

def test_password_backend_isolation(test_client):
    # Passwords must NEVER have backend analysis or storage routes
    res = test_client.post("/api/password/analyze", json={"password": "SecretPassword123!"})
    assert res.status_code in {404, 405}

    res = test_client.get("/api/password")
    assert res.status_code in {404, 405}
