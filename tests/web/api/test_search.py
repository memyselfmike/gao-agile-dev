"""Tests for search API endpoints.

Story 39.36: Message Search Across DMs and Channels
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from gao_dev.web.server import create_app


@pytest.fixture
def test_db(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a test database with sample messages."""
    # Create .gao-dev directory structure
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir()
    db_path = gao_dev_dir / "documents.db"

    # Initialize database
    conn = sqlite3.connect(str(db_path))

    # Create messages table (migration_002)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            conversation_type TEXT NOT NULL CHECK(conversation_type IN ('dm', 'channel')),
            content TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'agent')),
            agent_id TEXT,
            agent_name TEXT,
            thread_id INTEGER,
            reply_to_message_id TEXT,
            thread_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            metadata JSON
        )
    """)

    # Insert sample messages
    now = datetime.now()
    messages = [
        # DM messages with Brian
        (
            "msg-1",
            "brian",
            "dm",
            "Let's create a PRD for user authentication",
            "agent",
            "brian",
            "Brian",
            (now - timedelta(days=1)).isoformat(),
        ),
        (
            "msg-2",
            "brian",
            "dm",
            "I can help with that. What features do you need?",
            "agent",
            "brian",
            "Brian",
            (now - timedelta(days=1, hours=1)).isoformat(),
        ),
        # DM messages with John
        (
            "msg-3",
            "john",
            "dm",
            "Working on the authentication PRD now",
            "agent",
            "john",
            "John",
            (now - timedelta(days=2)).isoformat(),
        ),
        # Channel messages
        (
            "msg-4",
            "sprint-planning-epic-5",
            "channel",
            "Let's plan the authentication epic",
            "agent",
            "bob",
            "Bob",
            (now - timedelta(days=3)).isoformat(),
        ),
        (
            "msg-5",
            "sprint-planning-epic-5",
            "channel",
            "We need PRD review before implementation",
            "agent",
            "brian",
            "Brian",
            (now - timedelta(days=3, hours=1)).isoformat(),
        ),
        # Old message (for date range testing)
        (
            "msg-6",
            "brian",
            "dm",
            "This is an old message about authentication",
            "agent",
            "brian",
            "Brian",
            (now - timedelta(days=35)).isoformat(),
        ),
    ]

    for msg in messages:
        conn.execute(
            """
            INSERT INTO messages
            (id, conversation_id, conversation_type, content, role, agent_id, agent_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            msg,
        )

    conn.commit()
    conn.close()

    yield tmp_path

    # Cleanup - On Windows, let pytest handle cleanup to avoid permission errors


@pytest.fixture
def client(test_db: Path) -> TestClient:
    """Create test client with test database."""
    app = create_app()

    # Override project root to point to test directory
    app.state.project_root = test_db

    return TestClient(app)


def test_search_basic(client: TestClient) -> None:
    """Test basic search functionality."""
    response = client.get("/api/search/messages?q=authentication")

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert "total" in data
    assert data["total"] > 0

    # Should find messages containing "authentication"
    for result in data["results"]:
        assert "authentication" in result["content"].lower()


def test_search_empty_query(client: TestClient) -> None:
    """Test search with empty query returns error."""
    response = client.get("/api/search/messages?q=")

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_search_filter_by_type_dm(client: TestClient) -> None:
    """Test filtering by DM type."""
    response = client.get("/api/search/messages?q=authentication&type=dm")

    assert response.status_code == 200
    data = response.json()

    # All results should be DMs
    for result in data["results"]:
        assert result["conversationType"] == "dm"


def test_search_filter_by_type_channel(client: TestClient) -> None:
    """Test filtering by channel type."""
    response = client.get("/api/search/messages?q=PRD&type=channel")

    assert response.status_code == 200
    data = response.json()

    # All results should be channels
    for result in data["results"]:
        assert result["conversationType"] == "channel"


def test_search_filter_by_agent(client: TestClient) -> None:
    """Test filtering by specific agent."""
    response = client.get("/api/search/messages?q=authentication&agent=brian")

    assert response.status_code == 200
    data = response.json()

    # All results should be from Brian
    for result in data["results"]:
        assert result["sender"] == "brian"


def test_search_filter_by_date_range_7d(client: TestClient) -> None:
    """Test filtering by 7 day date range."""
    response = client.get("/api/search/messages?q=authentication&date_range=7d")

    assert response.status_code == 200
    data = response.json()

    # Should not include the 35-day old message
    cutoff = datetime.now() - timedelta(days=7)
    for result in data["results"]:
        result_date = datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
        assert result_date >= cutoff


def test_search_filter_by_date_range_30d(client: TestClient) -> None:
    """Test filtering by 30 day date range."""
    response = client.get("/api/search/messages?q=authentication&date_range=30d")

    assert response.status_code == 200
    data = response.json()

    # Should not include the 35-day old message
    cutoff = datetime.now() - timedelta(days=30)
    for result in data["results"]:
        result_date = datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
        assert result_date >= cutoff


def test_search_highlights(client: TestClient) -> None:
    """Test that search results include highlights."""
    response = client.get("/api/search/messages?q=authentication")

    assert response.status_code == 200
    data = response.json()

    assert len(data["results"]) > 0

    # Check that highlights are present
    for result in data["results"]:
        assert "highlights" in result
        assert isinstance(result["highlights"], list)


def test_search_result_structure(client: TestClient) -> None:
    """Test that search results have correct structure."""
    response = client.get("/api/search/messages?q=authentication")

    assert response.status_code == 200
    data = response.json()

    assert len(data["results"]) > 0

    result = data["results"][0]
    assert "messageId" in result
    assert "conversationId" in result
    assert "conversationType" in result
    assert "content" in result
    assert "sender" in result
    assert "timestamp" in result
    assert "highlights" in result


def test_search_combined_filters(client: TestClient) -> None:
    """Test search with multiple filters combined."""
    response = client.get(
        "/api/search/messages?q=authentication&type=dm&agent=brian&date_range=7d"
    )

    assert response.status_code == 200
    data = response.json()

    # Results should match all filters
    cutoff = datetime.now() - timedelta(days=7)
    for result in data["results"]:
        assert result["conversationType"] == "dm"
        assert result["sender"] == "brian"
        result_date = datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
        assert result_date >= cutoff


def test_search_no_results(client: TestClient) -> None:
    """Test search with no matching results."""
    response = client.get("/api/search/messages?q=nonexistentquery12345")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert len(data["results"]) == 0


def test_search_limit(client: TestClient) -> None:
    """Test search result limit."""
    response = client.get("/api/search/messages?q=authentication&limit=2")

    assert response.status_code == 200
    data = response.json()

    # Should return at most 2 results
    assert len(data["results"]) <= 2


def test_search_limit_validation(client: TestClient) -> None:
    """Test that limit is validated."""
    # Test limit > 100
    response = client.get("/api/search/messages?q=authentication&limit=200")
    assert response.status_code == 422  # Validation error

    # Test limit < 1
    response = client.get("/api/search/messages?q=authentication&limit=0")
    assert response.status_code == 422  # Validation error
