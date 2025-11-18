"""Tests for DM (Direct Message) API endpoints.

Story 39.31: DMs Section - Agent List and Conversation UI
Story 39.32: DM Conversation View and Message Sending
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from gao_dev.web.server import create_app
from gao_dev.web.config import WebConfig


@pytest.fixture
def test_client(tmp_path):
    """Create test client with temporary project."""
    # Create .gao-dev directory
    (tmp_path / ".gao-dev").mkdir(exist_ok=True)

    # Create config with frontend dist path
    frontend_dist = tmp_path / "frontend" / "dist"
    frontend_dist.mkdir(parents=True, exist_ok=True)

    config = WebConfig(
        host="127.0.0.1",
        port=3000,
        auto_open=False,
        frontend_dist_path=str(frontend_dist),
    )

    app = create_app(config)
    app.state.project_root = tmp_path

    return TestClient(app)


def test_get_dms_endpoint_exists(test_client: TestClient):
    """Test that GET /api/dms endpoint exists and returns 200."""
    response = test_client.get("/api/dms")
    assert response.status_code == 200


def test_get_dms_returns_conversations(test_client: TestClient):
    """Test that GET /api/dms returns conversations array."""
    response = test_client.get("/api/dms")
    data = response.json()

    assert "conversations" in data
    assert isinstance(data["conversations"], list)


def test_get_dms_includes_all_agents(test_client: TestClient):
    """Test that GET /api/dms includes all 8 agents."""
    response = test_client.get("/api/dms")
    data = response.json()

    agents = {conv["agent"] for conv in data["conversations"]}
    expected_agents = {
        "brian",
        "mary",
        "john",
        "winston",
        "sally",
        "bob",
        "amelia",
        "murat",
    }

    assert agents == expected_agents


def test_get_dms_conversation_structure(test_client: TestClient):
    """Test that DM conversations have required fields."""
    response = test_client.get("/api/dms")
    data = response.json()

    for conv in data["conversations"]:
        assert "agent" in conv
        assert "lastMessage" in conv
        assert "lastMessageAt" in conv
        assert "messageCount" in conv

        # Validate types
        assert isinstance(conv["agent"], str)
        assert isinstance(conv["lastMessage"], str)
        assert isinstance(conv["lastMessageAt"], str)
        assert isinstance(conv["messageCount"], int)


def test_get_dms_sorted_by_recent_activity(test_client: TestClient):
    """Test that DM conversations are sorted by last message timestamp."""
    response = test_client.get("/api/dms")
    data = response.json()

    conversations = data["conversations"]

    # Check that timestamps are in descending order (most recent first)
    for i in range(len(conversations) - 1):
        current_time = conversations[i]["lastMessageAt"]
        next_time = conversations[i + 1]["lastMessageAt"]
        assert current_time >= next_time, "Conversations not sorted by recency"


def test_get_dm_history_brian(test_client: TestClient):
    """Test that GET /api/dms/brian/history returns Brian's conversation history."""
    response = test_client.get("/api/dms/brian/history")
    assert response.status_code == 200

    data = response.json()
    assert "messages" in data
    assert isinstance(data["messages"], list)


def test_get_dm_history_invalid_agent(test_client: TestClient):
    """Test that GET /api/dms/{invalid}/history returns 404."""
    response = test_client.get("/api/dms/invalid_agent/history")
    assert response.status_code == 404


def test_get_dm_history_max_messages_param(test_client: TestClient):
    """Test that max_messages parameter is respected."""
    # Request with max_messages limit
    response = test_client.get("/api/dms/brian/history?max_messages=10")
    assert response.status_code == 200

    data = response.json()
    assert len(data["messages"]) <= 10


# Story 39.32: Message pagination and sending tests


def test_get_dm_messages_with_pagination(test_client: TestClient):
    """Test GET /api/dms/{agent}/messages with pagination."""
    response = test_client.get("/api/dms/brian/messages?offset=0&limit=20")
    assert response.status_code == 200

    data = response.json()
    assert "messages" in data
    assert "total" in data
    assert "offset" in data
    assert "limit" in data
    assert "hasMore" in data

    # Validate pagination params
    assert data["offset"] == 0
    assert data["limit"] == 20
    assert isinstance(data["hasMore"], bool)
    assert isinstance(data["total"], int)


def test_get_dm_messages_default_pagination(test_client: TestClient):
    """Test GET /api/dms/{agent}/messages with default pagination."""
    response = test_client.get("/api/dms/brian/messages")
    assert response.status_code == 200

    data = response.json()
    # Default limit is 50
    assert data["limit"] == 50
    assert data["offset"] == 0


def test_get_dm_messages_invalid_offset(test_client: TestClient):
    """Test GET /api/dms/{agent}/messages with negative offset."""
    response = test_client.get("/api/dms/brian/messages?offset=-1&limit=10")
    assert response.status_code == 400
    assert "offset" in response.json()["detail"].lower()


def test_get_dm_messages_invalid_limit_high(test_client: TestClient):
    """Test GET /api/dms/{agent}/messages with limit too high."""
    response = test_client.get("/api/dms/brian/messages?offset=0&limit=200")
    assert response.status_code == 400
    assert "limit" in response.json()["detail"].lower()


def test_get_dm_messages_invalid_limit_low(test_client: TestClient):
    """Test GET /api/dms/{agent}/messages with limit too low."""
    response = test_client.get("/api/dms/brian/messages?offset=0&limit=0")
    assert response.status_code == 400
    assert "limit" in response.json()["detail"].lower()


def test_get_dm_messages_invalid_agent(test_client: TestClient):
    """Test GET /api/dms/{agent}/messages with invalid agent."""
    response = test_client.get("/api/dms/invalid_agent/messages")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_send_dm_message_structure(test_client: TestClient):
    """Test POST /api/dms/{agent}/messages with valid message."""
    response = test_client.post(
        "/api/dms/brian/messages",
        json={"content": "Hello Brian, how are you?"},
    )

    # May be 503 if brian_adapter not initialized
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert "success" in data
        assert isinstance(data["success"], bool)


def test_send_dm_message_empty_content(test_client: TestClient):
    """Test POST /api/dms/{agent}/messages with empty content."""
    response = test_client.post(
        "/api/dms/brian/messages",
        json={"content": ""},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_send_dm_message_whitespace_only(test_client: TestClient):
    """Test POST /api/dms/{agent}/messages with whitespace-only content."""
    response = test_client.post(
        "/api/dms/brian/messages",
        json={"content": "   \n\t   "},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_send_dm_message_invalid_agent(test_client: TestClient):
    """Test POST /api/dms/{agent}/messages with invalid agent."""
    response = test_client.post(
        "/api/dms/invalid_agent/messages",
        json={"content": "Hello!"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_send_dm_message_not_implemented_agent(test_client: TestClient):
    """Test POST /api/dms/{agent}/messages for non-Brian agents."""
    # Other agents not yet implemented
    for agent in ["mary", "john", "winston", "sally", "bob", "amelia", "murat"]:
        response = test_client.post(
            f"/api/dms/{agent}/messages",
            json={"content": f"Hello {agent}!"},
        )

        assert response.status_code == 501
        assert "not yet implemented" in response.json()["detail"].lower()
