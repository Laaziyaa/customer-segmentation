"""
Tests for AI Assistant chat endpoint, intent parsing, planning,
natural language synthesis, and status endpoints.
"""

from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


def test_chat_status():
    resp = client.get("/api/chat/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "configured" in data
    assert "active_mode" in data
    assert "provider" in data
    assert "model" in data
    assert data["provider"] == "Groq"


def test_chat_greeting():
    resp = client.post("/api/chat", json={"query": "hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert "retail banking" in data["response"].lower() or "assistant" in data["response"].lower()
    assert len(data["execution_plan"]) >= 1


def test_chat_customer_explainability():
    resp = client.post("/api/chat", json={"query": "why is customer 104 in this cluster?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "104" in data["response"]
    assert "Segment" in data["response"] or "cluster" in data["response"].lower()
    assert len(data["execution_plan"]) >= 2


def test_chat_segments_overview():
    resp = client.post("/api/chat", json={"query": "show segments overview"})
    assert resp.status_code == 200
    data = resp.json()
    assert "segments" in data["response"].lower()
    assert "Segment 0" in data["response"] or "Cluster 0" in data["response"]


def test_chat_retention_risk():
    resp = client.post("/api/chat", json={"query": "show at-risk customers needing retention"})
    assert resp.status_code == 200
    data = resp.json()
    assert "retention" in data["response"].lower() or "risk" in data["response"].lower()


def test_chat_feature_pipeline():
    resp = client.post("/api/chat", json={"query": "how was the data prepared for clustering?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "pipeline" in data["response"].lower() or "features" in data["response"].lower()


def test_chat_invalid_key_handling():
    resp = client.post("/api/chat/key", json={"api_key": "invalid_fake_key_12345"})
    assert resp.status_code == 400
    assert "Invalid Groq API Key" in resp.json()["detail"] or "failed" in resp.json()["detail"].lower()
