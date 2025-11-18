"""Tests for threads API endpoints.

Story 39.34: Message Threading Infrastructure
"""

import json
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from gao_dev.web.server import create_app
from gao_dev.web.config import WebConfig
from gao_dev.core.state.migrations.migration_002_add_threading_support import Migration002


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database with threading schema."""
    db_path = tmp_path / ".gao-dev" / "documents.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create database
    conn = sqlite3.connect(str(db_path))

    # Create schema_version table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now')),
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

    # Apply migration
    Migration002.upgrade(db_path)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def client(temp_db, tmp_path):
    """Create test client with mocked project root."""
    config = WebConfig(
        host="127.0.0.1",
        port=3000,
        frontend_dist_path=str(tmp_path / "frontend" / "dist"),
        auto_open=False
    )
    app = create_app(config)

    # Override project_root to use temp directory
    app.state.project_root = tmp_path

    # Mock event_bus to prevent WebSocket errors
    app.state.event_bus = AsyncMock()
    app.state.event_bus.publish = AsyncMock()

    return TestClient(app)


def _create_test_message(db_path: Path, message_id: str, conversation_id: str = "brian") -> None:
    """Create a test message in the database."""
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        INSERT INTO messages (id, conversation_id, conversation_type, content, role)
        VALUES (?, ?, ?, ?, ?)
        """,
        (message_id, conversation_id, "dm", "Test parent message", "agent")
    )
    conn.commit()
    conn.close()


class TestCreateThread:
    """Tests for POST /api/threads endpoint."""

    def test_create_thread_success(self, client, temp_db):
        """Test creating a thread successfully."""
        # Create parent message
        parent_msg_id = "msg-parent-123"
        _create_test_message(temp_db, parent_msg_id)

        # Create thread
        response = client.post(
            "/api/threads",
            json={
                "parentMessageId": parent_msg_id,
                "conversationId": "brian",
                "conversationType": "dm"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "threadId" in data
        assert data["parentMessageId"] == parent_msg_id
        assert data["conversationId"] == "brian"
        assert data["conversationType"] == "dm"
        assert "createdAt" in data

        # Verify thread in database
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "SELECT * FROM threads WHERE id = ?",
            (data["threadId"],)
        )
        thread = cursor.fetchone()
        conn.close()

        assert thread is not None

    def test_create_thread_duplicate_returns_existing(self, client, temp_db):
        """Test creating duplicate thread returns existing thread."""
        parent_msg_id = "msg-parent-456"
        _create_test_message(temp_db, parent_msg_id)

        # Create thread first time
        response1 = client.post(
            "/api/threads",
            json={
                "parentMessageId": parent_msg_id,
                "conversationId": "brian",
                "conversationType": "dm"
            }
        )
        assert response1.status_code == 200
        thread_id_1 = response1.json()["threadId"]

        # Create thread second time (should return existing)
        response2 = client.post(
            "/api/threads",
            json={
                "parentMessageId": parent_msg_id,
                "conversationId": "brian",
                "conversationType": "dm"
            }
        )
        assert response2.status_code == 200
        thread_id_2 = response2.json()["threadId"]

        # Same thread ID
        assert thread_id_1 == thread_id_2

    def test_create_thread_invalid_conversation_type(self, client, temp_db):
        """Test creating thread with invalid conversation type fails."""
        parent_msg_id = "msg-parent-789"
        _create_test_message(temp_db, parent_msg_id)

        response = client.post(
            "/api/threads",
            json={
                "parentMessageId": parent_msg_id,
                "conversationId": "brian",
                "conversationType": "invalid"  # Invalid type
            }
        )

        assert response.status_code == 400
        assert "Invalid conversation type" in response.json()["detail"]

    def test_create_thread_database_not_found(self, tmp_path):
        """Test creating thread when database doesn't exist."""
        config = WebConfig(
            host="127.0.0.1",
            port=3000,
            frontend_dist_path=str(tmp_path / "frontend" / "dist"),
            auto_open=False
        )
        app = create_app(config)
        app.state.project_root = tmp_path / "nonexistent"
        app.state.event_bus = AsyncMock()

        client = TestClient(app)

        response = client.post(
            "/api/threads",
            json={
                "parentMessageId": "msg-123",
                "conversationId": "brian",
                "conversationType": "dm"
            }
        )

        assert response.status_code == 503
        assert "Database not found" in response.json()["detail"]


class TestGetThread:
    """Tests for GET /api/threads/{thread_id} endpoint."""

    def test_get_thread_success(self, client, temp_db):
        """Test getting thread with replies."""
        # Create parent message
        parent_msg_id = "msg-parent-get"
        _create_test_message(temp_db, parent_msg_id)

        # Create thread
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "INSERT INTO threads (parent_message_id, conversation_id, conversation_type) VALUES (?, ?, ?)",
            (parent_msg_id, "brian", "dm")
        )
        thread_id = cursor.lastrowid

        # Create replies
        conn.execute(
            """
            INSERT INTO messages (id, conversation_id, conversation_type, content, role, thread_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("msg-reply-1", "brian", "dm", "First reply", "user", thread_id)
        )
        conn.execute(
            """
            INSERT INTO messages (id, conversation_id, conversation_type, content, role, thread_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("msg-reply-2", "brian", "dm", "Second reply", "agent", thread_id)
        )
        conn.commit()
        conn.close()

        # Get thread
        response = client.get(f"/api/threads/{thread_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["threadId"] == thread_id
        assert data["conversationId"] == "brian"
        assert data["conversationType"] == "dm"
        assert data["replyCount"] == 2
        assert len(data["replies"]) == 2
        assert data["replies"][0]["id"] == "msg-reply-1"
        assert data["replies"][1]["id"] == "msg-reply-2"

        # Parent message should be included
        assert data["parentMessage"] is not None
        assert data["parentMessage"]["id"] == parent_msg_id

    def test_get_thread_not_found(self, client, temp_db):
        """Test getting non-existent thread returns 404."""
        response = client.get("/api/threads/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_thread_empty_replies(self, client, temp_db):
        """Test getting thread with no replies."""
        parent_msg_id = "msg-parent-empty"
        _create_test_message(temp_db, parent_msg_id)

        # Create thread with no replies
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "INSERT INTO threads (parent_message_id, conversation_id, conversation_type) VALUES (?, ?, ?)",
            (parent_msg_id, "brian", "dm")
        )
        thread_id = cursor.lastrowid
        conn.commit()
        conn.close()

        response = client.get(f"/api/threads/{thread_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["threadId"] == thread_id
        assert data["replyCount"] == 0
        assert len(data["replies"]) == 0


class TestPostThreadReply:
    """Tests for POST /api/threads/{thread_id}/messages endpoint."""

    def test_post_reply_success(self, client, temp_db):
        """Test posting a reply to thread."""
        # Create parent message
        parent_msg_id = "msg-parent-reply"
        _create_test_message(temp_db, parent_msg_id)

        # Create thread
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "INSERT INTO threads (parent_message_id, conversation_id, conversation_type) VALUES (?, ?, ?)",
            (parent_msg_id, "brian", "dm")
        )
        thread_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Post reply
        response = client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "This is my reply"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "messageId" in data
        assert data["threadId"] == thread_id
        assert data["content"] == "This is my reply"
        assert data["role"] == "user"
        assert data["parentMessageId"] == parent_msg_id
        assert "createdAt" in data

        # Verify message in database
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "SELECT * FROM messages WHERE id = ?",
            (data["messageId"],)
        )
        message = cursor.fetchone()
        conn.close()

        assert message is not None

    def test_post_reply_empty_content(self, client, temp_db):
        """Test posting reply with empty content fails."""
        parent_msg_id = "msg-parent-empty-reply"
        _create_test_message(temp_db, parent_msg_id)

        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "INSERT INTO threads (parent_message_id, conversation_id, conversation_type) VALUES (?, ?, ?)",
            (parent_msg_id, "brian", "dm")
        )
        thread_id = cursor.lastrowid
        conn.commit()
        conn.close()

        response = client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": ""}  # Empty content
        )

        assert response.status_code == 400
        assert "cannot be empty" in response.json()["detail"]

    def test_post_reply_thread_not_found(self, client, temp_db):
        """Test posting reply to non-existent thread fails."""
        response = client.post(
            "/api/threads/99999/messages",
            json={"content": "Reply to nowhere"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_post_reply_updates_thread_count(self, client, temp_db):
        """Test posting reply updates parent message thread count."""
        # Create parent message
        parent_msg_id = "msg-parent-count"
        _create_test_message(temp_db, parent_msg_id)

        # Create thread
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "INSERT INTO threads (parent_message_id, conversation_id, conversation_type) VALUES (?, ?, ?)",
            (parent_msg_id, "brian", "dm")
        )
        thread_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Post first reply
        client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "First reply"}
        )

        # Check thread count in threads table
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "SELECT reply_count FROM threads WHERE id = ?",
            (thread_id,)
        )
        thread = cursor.fetchone()
        assert thread[0] == 1

        # Post second reply
        client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "Second reply"}
        )

        # Check thread count updated
        cursor = conn.execute(
            "SELECT reply_count FROM threads WHERE id = ?",
            (thread_id,)
        )
        thread = cursor.fetchone()
        conn.close()

        assert thread[0] == 2


class TestThreadingMigration:
    """Tests for threading database migration."""

    def test_migration_creates_tables(self, tmp_path):
        """Test migration creates threads and messages tables."""
        db_path = tmp_path / "test.db"

        # Create database with schema_version table
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now')),
                description TEXT
            )
        """)
        conn.commit()
        conn.close()

        # Apply migration
        result = Migration002.upgrade(db_path)
        assert result is True

        # Verify tables exist
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "threads" in tables
        assert "messages" in tables
        assert "schema_version" in tables

    def test_migration_creates_indexes(self, tmp_path):
        """Test migration creates indexes."""
        db_path = tmp_path / "test.db"

        # Create database
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now')),
                description TEXT
            )
        """)
        conn.commit()
        conn.close()

        # Apply migration
        Migration002.upgrade(db_path)

        # Verify indexes exist
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        )
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "idx_threads_parent_message" in indexes
        assert "idx_threads_conversation" in indexes
        assert "idx_messages_conversation" in indexes
        assert "idx_messages_thread" in indexes

    def test_migration_idempotent(self, tmp_path):
        """Test migration can be applied multiple times safely."""
        db_path = tmp_path / "test.db"

        # Create database
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now')),
                description TEXT
            )
        """)
        conn.commit()
        conn.close()

        # Apply migration twice
        result1 = Migration002.upgrade(db_path)
        result2 = Migration002.upgrade(db_path)

        assert result1 is True
        assert result2 is True

    def test_migration_downgrade(self, tmp_path):
        """Test migration downgrade removes tables."""
        db_path = tmp_path / "test.db"

        # Create database
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now')),
                description TEXT
            )
        """)
        conn.commit()
        conn.close()

        # Apply migration
        Migration002.upgrade(db_path)

        # Verify tables exist
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('threads', 'messages')"
        )
        tables_before = [row[0] for row in cursor.fetchall()]
        conn.close()
        assert len(tables_before) == 2

        # Downgrade migration
        result = Migration002.downgrade(db_path)
        assert result is True

        # Verify tables removed
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('threads', 'messages')"
        )
        tables_after = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert len(tables_after) == 0
