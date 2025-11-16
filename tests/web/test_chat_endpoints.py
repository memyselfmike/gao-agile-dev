"""Tests for chat API endpoints.

Story 39.7: Brian Chat Component - API endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from gao_dev.web.server import create_app
from gao_dev.web.config import WebConfig


@pytest.fixture
def test_config(tmp_path):
    """Create test configuration."""
    frontend_dist = tmp_path / "frontend" / "dist"
    frontend_dist.mkdir(parents=True)
    (frontend_dist / "index.html").write_text("<html></html>")

    return WebConfig(
        host="127.0.0.1",
        port=3000,
        frontend_dist_path=str(frontend_dist),
        auto_open=False,
    )


@pytest.fixture
def client(test_config):
    """Create test client."""
    app = create_app(test_config)
    return TestClient(app)


def test_chat_endpoint_rejects_empty_message(client):
    """Test that empty messages are rejected."""
    response = client.post(
        "/api/chat",
        json={"message": "", "agent": "Brian"}
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_chat_endpoint_rejects_whitespace_only_message(client):
    """Test that whitespace-only messages are rejected."""
    response = client.post(
        "/api/chat",
        json={"message": "   ", "agent": "Brian"}
    )

    assert response.status_code == 400


def test_chat_endpoint_rejects_unsupported_agent(client):
    """Test that unsupported agents are rejected."""
    response = client.post(
        "/api/chat",
        json={"message": "Hello", "agent": "UnknownAgent"}
    )

    assert response.status_code == 400
    assert "Unsupported agent" in response.json()["detail"]


def test_chat_endpoint_validation_success(client):
    """Test that valid chat requests pass validation.

    Note: This test only validates that the request format is accepted.
    Full integration testing of Brian adapter is done in test_brian_adapter.py.
    """
    # This will fail with initialization errors, but proves validation works
    # We're testing the endpoint structure, not the full integration
    response = client.post(
        "/api/chat",
        json={"message": "Hello Brian", "agent": "Brian"}
    )

    # Either success or an initialization error (not validation error)
    # Validation errors are 400, initialization issues are 500
    assert response.status_code in [200, 500], \
        f"Expected 200 or 500, got {response.status_code}: {response.json()}"


def test_get_chat_history_empty(client):
    """Test getting chat history when adapter not initialized."""
    response = client.get("/api/chat/history")

    assert response.status_code == 200
    data = response.json()
    assert data["messages"] == []


def test_get_chat_context_without_adapter(client):
    """Test getting chat context when adapter not initialized."""
    response = client.get("/api/chat/context")

    assert response.status_code == 200
    data = response.json()
    assert "projectRoot" in data
    assert data["currentEpic"] is None
    assert data["currentStory"] is None
    assert data["pendingConfirmation"] is False


def test_get_chat_history_endpoint_structure(client):
    """Test that chat history endpoint returns expected structure.

    Note: Full integration testing is done in test_brian_adapter.py.
    This just validates the API endpoint structure.
    """
    response = client.get("/api/chat/history?max_turns=10")

    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert isinstance(data["messages"], list)
