"""Tests for channel archive and export endpoints.

Story 39.37: Channel Archive and Export
"""

from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from gao_dev.web.server import create_app


@pytest.fixture
def client():
    """Get test client."""
    app = create_app()
    return TestClient(app)


class TestChannelArchive:
    """Test POST /api/channels/{channel_id}/archive endpoint."""

    def test_archive_active_channel_success(self, client):
        """Test archiving an active channel successfully."""
        # Archive an active channel
        response = client.post("/api/channels/sprint-planning-epic-5/archive")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert data["channelId"] == "sprint-planning-epic-5"
        assert data["status"] == "archived"
        assert "timestamp" in data

        # Verify channel is now archived
        channels_response = client.get("/api/channels")
        channels_data = channels_response.json()
        archived_channel = next(
            (c for c in channels_data["channels"] if c["id"] == "sprint-planning-epic-5"),
            None,
        )
        assert archived_channel is not None
        assert archived_channel["status"] == "archived"

    def test_archive_nonexistent_channel(self, client):
        """Test archiving a channel that doesn't exist."""
        response = client.post("/api/channels/nonexistent-channel/archive")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_archive_already_archived_channel(self, client):
        """Test archiving a channel that is already archived."""
        # Try to archive already archived channel
        response = client.post("/api/channels/sprint-planning-epic-3/archive")

        assert response.status_code == 400
        assert "already archived" in response.json()["detail"].lower()

    def test_send_message_to_archived_channel_fails(self, client):
        """Test that sending messages to archived channels fails."""
        # Try to send message to archived channel
        response = client.post(
            "/api/channels/sprint-planning-epic-3/messages",
            headers={"X-Session-Token": "test-session-token"},
            json={"content": "This should fail"},
        )

        assert response.status_code == 403
        assert "archived" in response.json()["detail"].lower()
        assert "read-only" in response.json()["detail"].lower()


class TestChannelExport:
    """Test GET /api/channels/{channel_id}/export endpoint."""

    def test_export_channel_success(self, client):
        """Test exporting channel transcript successfully."""
        response = client.get("/api/channels/sprint-planning-epic-5/export")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"

        # Verify Content-Disposition header
        content_disposition = response.headers.get("content-disposition")
        assert content_disposition is not None
        assert "attachment" in content_disposition
        assert "sprint-planning-epic-5" in content_disposition
        assert ".md" in content_disposition

        # Verify Markdown content structure
        content = response.text
        assert "# Sprint Planning - Epic 5" in content
        assert "**Date**:" in content
        assert "**Participants**:" in content
        assert "---" in content

        # Verify messages are present
        assert "**Brian**" in content
        assert "**Bob**" in content
        assert "**John**" in content
        assert "**Winston**" in content

        # Verify timestamps are formatted
        assert "AM" in content or "PM" in content

    def test_export_channel_with_messages(self, client):
        """Test export includes all messages in correct format."""
        response = client.get("/api/channels/retrospective-epic-4/export")

        assert response.status_code == 200
        content = response.text

        # Verify header
        assert "# Retrospective - Epic 4" in content

        # Verify all messages are present
        assert "Time for our Epic 4 retrospective" in content
        assert "Great collaboration between Winston and Amelia" in content
        assert "Test coverage was excellent thanks to Murat" in content
        assert "We should continue TDD approach" in content

        # Verify message count (should have 4 messages)
        agent_mentions = content.count("**Brian**") + content.count("**Bob**") + \
                        content.count("**Amelia**") + content.count("**Murat**")
        assert agent_mentions == 4

    def test_export_nonexistent_channel(self, client):
        """Test exporting a channel that doesn't exist."""
        response = client.get("/api/channels/nonexistent-channel/export")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_export_channel_with_no_messages(self, client):
        """Test exporting a channel with no messages."""
        # Mock a channel with no messages
        with patch("gao_dev.web.api.channels.MOCK_MESSAGES", {"test-channel": []}):
            with patch(
                "gao_dev.web.api.channels.MOCK_CHANNELS",
                [
                    {
                        "id": "test-channel",
                        "name": "#test-channel-epic-1",
                        "ceremonyType": "daily-standup",
                        "status": "active",
                        "participants": ["brian"],
                        "lastMessageAt": "2025-01-16T09:00:00Z",
                        "lastMessage": "",
                        "messageCount": 0,
                    }
                ],
            ):
                response = client.get("/api/channels/test-channel/export")

                assert response.status_code == 200
                content = response.text

                # Verify header exists
                assert "# Daily Standup - Epic 1" in content
                assert "**Date**:" in content
                assert "**Participants**:" in content

                # Verify no message content (only header and separator)
                lines = [line for line in content.split("\n") if line.strip()]
                # Should have: title, date, participants, separator
                assert len(lines) <= 5

    def test_export_filename_format(self, client):
        """Test export generates correctly formatted filename."""
        response = client.get("/api/channels/sprint-planning-epic-5/export")

        assert response.status_code == 200
        content_disposition = response.headers.get("content-disposition")

        # Verify filename format: {ceremony-type}-epic-{num}-{date}.md
        assert "sprint-planning-epic-5" in content_disposition
        assert ".md" in content_disposition

        # Extract filename from Content-Disposition
        import re
        filename_match = re.search(r'filename="?(.+?)"?$', content_disposition)
        assert filename_match is not None

        filename = filename_match.group(1)
        # Should match pattern: sprint-planning-epic-5-YYYY-MM-DD.md
        assert filename.startswith("sprint-planning-epic-5-")
        assert filename.endswith(".md")

        # Verify date format (YYYY-MM-DD)
        date_part = filename.split("-epic-5-")[1].replace(".md", "")
        datetime.strptime(date_part, "%Y-%m-%d")  # Should not raise

    def test_export_markdown_formatting(self, client):
        """Test export uses correct Markdown formatting."""
        response = client.get("/api/channels/sprint-planning-epic-5/export")

        assert response.status_code == 200
        content = response.text

        # Verify Markdown structure
        lines = content.split("\n")

        # First line should be H1
        assert lines[0].startswith("# ")

        # Should have bold markers for Date and Participants
        assert "**Date**:" in content
        assert "**Participants**:" in content

        # Should have horizontal rule
        assert "---" in content

        # Message format: **AgentName** (HH:MM AM/PM):
        import re
        message_pattern = r'\*\*\w+\*\* \(\d{1,2}:\d{2} (AM|PM)\):'
        assert re.search(message_pattern, content) is not None

    def test_export_handles_large_transcript(self, client):
        """Test export handles channels with many messages (performance)."""
        # Mock channel with 1000 messages
        large_messages = []
        for i in range(1000):
            large_messages.append({
                "id": f"msg-{i}",
                "role": "agent",
                "agentName": "Brian",
                "agentId": "brian",
                "content": f"Message {i} content here",
                "timestamp": datetime(2025, 1, 16, 10, 0).timestamp() * 1000 + (i * 1000),
            })

        with patch("gao_dev.web.api.channels.MOCK_MESSAGES", {"large-channel": large_messages}):
            with patch(
                "gao_dev.web.api.channels.MOCK_CHANNELS",
                [
                    {
                        "id": "large-channel",
                        "name": "#large-channel-epic-1",
                        "ceremonyType": "sprint-planning",
                        "status": "archived",
                        "participants": ["brian"],
                        "lastMessageAt": "2025-01-16T10:00:00Z",
                        "lastMessage": "Last message",
                        "messageCount": 1000,
                    }
                ],
            ):
                import time
                start_time = time.time()
                response = client.get("/api/channels/large-channel/export")
                end_time = time.time()

                # Should complete in <5 seconds (AC requirement)
                assert (end_time - start_time) < 5.0

                assert response.status_code == 200
                content = response.text

                # Verify all messages exported
                assert content.count("**Brian**") == 1000
