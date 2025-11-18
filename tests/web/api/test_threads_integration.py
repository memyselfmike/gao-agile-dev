"""Integration tests for threading with WebSocket events.

Story 39.34: Message Threading Infrastructure
"""

import asyncio
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call

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


@pytest.fixture
def mock_event_bus():
    """Create mock event bus to track events."""
    event_bus = AsyncMock()
    event_bus.publish = AsyncMock()
    return event_bus


@pytest.fixture
def client_with_events(temp_db, tmp_path, mock_event_bus):
    """Create test client with event tracking."""
    config = WebConfig(
        host="127.0.0.1",
        port=3000,
        frontend_dist_path=str(tmp_path / "frontend" / "dist"),
        auto_open=False
    )
    app = create_app(config)
    app.state.project_root = tmp_path
    app.state.event_bus = mock_event_bus

    return TestClient(app), mock_event_bus


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


class TestWebSocketEvents:
    """Tests for WebSocket event publishing."""

    def test_thread_created_event_published(self, client_with_events, temp_db):
        """Test thread.created event is published when thread created."""
        client, event_bus = client_with_events

        # Create parent message
        parent_msg_id = "msg-parent-ws-1"
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

        # Verify event published
        event_bus.publish.assert_called_once()
        call_args = event_bus.publish.call_args[0][0]

        assert call_args["type"] == "thread.created"
        assert call_args["payload"]["parentMessageId"] == parent_msg_id
        assert call_args["payload"]["conversationId"] == "brian"
        assert call_args["payload"]["conversationType"] == "dm"
        assert "threadId" in call_args["payload"]
        assert "timestamp" in call_args["payload"]

    def test_thread_reply_event_published(self, client_with_events, temp_db):
        """Test thread.reply event is published when reply posted."""
        client, event_bus = client_with_events

        # Create parent message
        parent_msg_id = "msg-parent-ws-2"
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

        # Reset event bus mock
        event_bus.publish.reset_mock()

        # Post reply
        response = client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "Test reply"}
        )

        assert response.status_code == 200

        # Verify events published (thread.reply and thread.updated)
        assert event_bus.publish.call_count == 2

        # First event: thread.reply
        reply_event = event_bus.publish.call_args_list[0][0][0]
        assert reply_event["type"] == "thread.reply"
        assert reply_event["payload"]["threadId"] == thread_id
        assert reply_event["payload"]["content"] == "Test reply"
        assert reply_event["payload"]["role"] == "user"

        # Second event: thread.updated
        updated_event = event_bus.publish.call_args_list[1][0][0]
        assert updated_event["type"] == "thread.updated"
        assert updated_event["payload"]["threadId"] == thread_id
        assert updated_event["payload"]["parentMessageId"] == parent_msg_id
        assert "threadCount" in updated_event["payload"]

    def test_thread_updated_event_has_correct_count(self, client_with_events, temp_db):
        """Test thread.updated event has correct thread count after multiple replies."""
        client, event_bus = client_with_events

        # Create parent message
        parent_msg_id = "msg-parent-ws-3"
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
        event_bus.publish.reset_mock()
        client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "Reply 1"}
        )

        # Check first thread.updated event
        updated_event_1 = event_bus.publish.call_args_list[1][0][0]
        assert updated_event_1["payload"]["threadCount"] == 1

        # Post second reply
        event_bus.publish.reset_mock()
        client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "Reply 2"}
        )

        # Check second thread.updated event
        updated_event_2 = event_bus.publish.call_args_list[1][0][0]
        assert updated_event_2["payload"]["threadCount"] == 2

    def test_event_not_published_on_duplicate_thread(self, client_with_events, temp_db):
        """Test event not published when creating duplicate thread."""
        client, event_bus = client_with_events

        # Create parent message
        parent_msg_id = "msg-parent-ws-4"
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

        # Reset mock
        event_bus.publish.reset_mock()

        # Create thread second time (duplicate)
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

        # Should return same thread
        assert thread_id_1 == thread_id_2

        # Event should NOT be published for duplicate thread
        event_bus.publish.assert_not_called()


class TestThreadCountDenormalization:
    """Tests for thread count denormalization."""

    def test_thread_count_updates_on_reply(self, client_with_events, temp_db):
        """Test parent message thread_count updates when reply added."""
        client, event_bus = client_with_events

        # Create parent message
        parent_msg_id = "msg-parent-count-1"
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

        # Initial thread count should be 0
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "SELECT thread_count FROM messages WHERE id = ?",
            (parent_msg_id,)
        )
        row = cursor.fetchone()
        initial_count = row[0] if row else 0
        conn.close()

        assert initial_count == 0

        # Post reply
        client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "First reply"}
        )

        # Thread count should be 1
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "SELECT thread_count FROM messages WHERE id = ?",
            (parent_msg_id,)
        )
        row = cursor.fetchone()
        count_after_first = row[0] if row else 0
        conn.close()

        assert count_after_first == 1

    def test_thread_reply_count_increments(self, client_with_events, temp_db):
        """Test threads.reply_count increments correctly."""
        client, event_bus = client_with_events

        # Create parent message
        parent_msg_id = "msg-parent-count-2"
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

        # Post 3 replies
        for i in range(3):
            client.post(
                f"/api/threads/{thread_id}/messages",
                json={"content": f"Reply {i+1}"}
            )

        # Check thread reply_count
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "SELECT reply_count FROM threads WHERE id = ?",
            (thread_id,)
        )
        row = cursor.fetchone()
        conn.close()

        assert row[0] == 3


class TestEndToEndThreading:
    """End-to-end threading workflow tests."""

    def test_complete_threading_workflow(self, client_with_events, temp_db):
        """Test complete workflow: create thread, post replies, fetch thread."""
        client, event_bus = client_with_events

        # Step 1: Create parent message
        parent_msg_id = "msg-e2e-parent"
        _create_test_message(temp_db, parent_msg_id)

        # Step 2: Create thread
        response = client.post(
            "/api/threads",
            json={
                "parentMessageId": parent_msg_id,
                "conversationId": "brian",
                "conversationType": "dm"
            }
        )
        assert response.status_code == 200
        thread_id = response.json()["threadId"]

        # Step 3: Post multiple replies
        reply_ids = []
        for i in range(5):
            response = client.post(
                f"/api/threads/{thread_id}/messages",
                json={"content": f"Reply {i+1}"}
            )
            assert response.status_code == 200
            reply_ids.append(response.json()["messageId"])

        # Step 4: Fetch thread
        response = client.get(f"/api/threads/{thread_id}")
        assert response.status_code == 200
        data = response.json()

        # Verify thread structure
        assert data["threadId"] == thread_id
        assert data["replyCount"] == 5
        assert len(data["replies"]) == 5
        assert data["parentMessage"]["id"] == parent_msg_id
        assert data["parentMessage"]["threadCount"] == 5

        # Verify replies are in order
        for i, reply in enumerate(data["replies"]):
            assert reply["content"] == f"Reply {i+1}"
            assert reply["id"] == reply_ids[i]

    def test_thread_with_100_replies(self, client_with_events, temp_db):
        """Test thread with 100+ replies (pagination edge case)."""
        client, event_bus = client_with_events

        # Create parent message
        parent_msg_id = "msg-large-thread"
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
        thread_id = response.json()["threadId"]

        # Post 100 replies (using direct DB for speed)
        conn = sqlite3.connect(str(temp_db))
        for i in range(100):
            conn.execute(
                """
                INSERT INTO messages (id, conversation_id, conversation_type, content, role, thread_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (f"msg-reply-{i}", "brian", "dm", f"Reply {i}", "user", thread_id)
            )
        conn.commit()
        conn.close()

        # Fetch thread
        response = client.get(f"/api/threads/{thread_id}")
        assert response.status_code == 200
        data = response.json()

        # Verify all replies fetched
        assert data["replyCount"] == 100
        assert len(data["replies"]) == 100
