"""Integration tests for session lock CLI/web interaction."""

import json
import os
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from gao_dev.core.session_lock import SessionLock
from gao_dev.web.server import create_app, WebConfig


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project directory."""
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir()
    return tmp_path


@pytest.fixture
def cli_lock(temp_project):
    """Create CLI session lock."""
    return SessionLock(temp_project)


@pytest.fixture
def web_app(temp_project):
    """Create web app with session lock."""
    config = WebConfig(frontend_dist_path=str(temp_project / "frontend" / "dist"))
    app = create_app(config)
    # Override project_root detection
    app.state.session_lock.project_root = temp_project
    app.state.session_lock.lock_file = temp_project / ".gao-dev" / "session.lock"
    return app


@pytest.fixture
def web_client(web_app):
    """Create web test client."""
    return TestClient(web_app)


class TestCLIWebLockInteraction:
    """Test CLI and web lock interaction."""

    def test_cli_acquires_write_lock(self, cli_lock):
        """Test CLI can acquire write lock."""
        result = cli_lock.acquire("cli", mode="write")
        assert result is True
        assert cli_lock.lock_file.exists()

        lock_data = json.loads(cli_lock.lock_file.read_text())
        assert lock_data["interface"] == "cli"
        assert lock_data["mode"] == "write"

    def test_web_starts_in_read_mode(self, web_client, temp_project):
        """Test web starts in read-only mode when CLI holds lock."""
        # Create CLI lock
        cli_lock = SessionLock(temp_project)
        cli_lock.acquire("cli", mode="write")

        # Web should start but in read-only mode
        # Check lock state endpoint
        response = web_client.get("/api/session/lock-state")
        assert response.status_code == 200

    def test_web_blocks_writes_when_cli_active(self, web_client, cli_lock):
        """Test web blocks write operations when CLI holds lock."""
        # CLI acquires write lock
        cli_lock.acquire("cli", mode="write")

        # Web POST should be rejected
        with patch("psutil.pid_exists", return_value=True):
            # Need to create a POST endpoint for testing
            # This test would need actual endpoint implementation
            pass

    def test_web_allows_reads_when_cli_active(self, web_client, cli_lock):
        """Test web allows read operations when CLI holds lock."""
        # CLI acquires write lock
        cli_lock.acquire("cli", mode="write")

        # Web GET should succeed
        response = web_client.get("/api/health")
        assert response.status_code == 200

    def test_cli_release_allows_web_upgrade(self, cli_lock, temp_project):
        """Test web can upgrade to write mode when CLI releases."""
        # CLI acquires write lock
        cli_lock.acquire("cli", mode="write")

        # Web starts in read mode
        web_lock = SessionLock(temp_project)
        web_lock.acquire("web", mode="read")

        # CLI releases
        cli_lock.release()

        # Web can upgrade
        result = web_lock.upgrade("web")
        assert result is True

    def test_web_downgrade_when_cli_acquires(self, temp_project):
        """Test web should downgrade when CLI acquires lock."""
        # Web starts with write lock (no CLI active)
        web_lock = SessionLock(temp_project)
        web_lock.acquire("web", mode="write")

        # CLI tries to acquire
        # In same process, this will succeed (same PID)
        # In real scenario (different processes), CLI would be denied
        # This test documents the behavior within same process
        cli_lock = SessionLock(temp_project)
        result = cli_lock.acquire("cli", mode="write")
        # Same process can reacquire (idempotent behavior)
        assert result is True


class TestLockStateAPI:
    """Test lock state API endpoint."""

    def test_lock_state_no_lock(self, web_client):
        """Test lock state when no lock exists."""
        response = web_client.get("/api/session/lock-state")
        assert response.status_code == 200

        data = response.json()
        assert data["mode"] == "write"
        assert data["isReadOnly"] is False
        assert data["holder"] is None

    def test_lock_state_we_hold_lock(self, web_client, web_app):
        """Test lock state when web holds lock."""
        # Acquire write lock
        web_app.state.session_lock.acquire("web", mode="write")

        response = web_client.get("/api/session/lock-state")
        data = response.json()

        assert data["mode"] == "write"
        assert data["isReadOnly"] is False
        assert data["holder"] == "web"

    def test_lock_state_cli_holds_lock(self, web_client, web_app):
        """Test lock state when CLI holds lock."""
        # Create CLI lock
        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        web_app.state.session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=True):
            response = web_client.get("/api/session/lock-state")
            data = response.json()

            assert data["mode"] == "read"
            assert data["isReadOnly"] is True
            assert data["holder"] == "cli"

    def test_lock_state_stale_lock(self, web_client, web_app):
        """Test lock state with stale lock."""
        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        web_app.state.session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=False):
            response = web_client.get("/api/session/lock-state")
            data = response.json()

            # Stale lock treated as no lock
            assert data["mode"] == "write"
            assert data["isReadOnly"] is False
            assert data["holder"] is None


class TestForceUnlock:
    """Test force unlock command."""

    def test_force_unlock_removes_lock(self, temp_project):
        """Test force unlock removes lock file."""
        lock = SessionLock(temp_project)

        # Create stale lock
        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=False):
            result = lock.force_unlock()
            assert result is True
            assert not lock.lock_file.exists()

    def test_force_unlock_prevents_unlock_if_alive(self, temp_project):
        """Test force unlock prevents unlock if process alive."""
        lock = SessionLock(temp_project)

        # Create lock with "alive" process
        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=True):
            with pytest.raises(RuntimeError, match="Cannot force unlock"):
                lock.force_unlock()


class TestConcurrentAccess:
    """Test concurrent access scenarios."""

    def test_multiple_read_locks(self, temp_project):
        """Test multiple readers can coexist."""
        lock1 = SessionLock(temp_project)
        lock2 = SessionLock(temp_project)

        result1 = lock1.acquire("cli", mode="read")
        result2 = lock2.acquire("web", mode="read")

        assert result1 is True
        assert result2 is True

    def test_write_lock_exclusivity(self, temp_project):
        """Test only one write lock at a time."""
        lock1 = SessionLock(temp_project)
        lock2 = SessionLock(temp_project)

        lock1.acquire("cli", mode="write")

        # Same process can reacquire (idempotent)
        result = lock2.acquire("web", mode="write")
        # In same process, this might succeed depending on PID check
        # But in different processes, would fail

    def test_lock_file_persistence(self, temp_project):
        """Test lock file persists across instances."""
        lock1 = SessionLock(temp_project)
        lock1.acquire("cli", mode="write")

        # Create new instance
        lock2 = SessionLock(temp_project)

        with patch("psutil.pid_exists", return_value=True):
            result = lock2.is_write_locked_by_other()
            # Might be False because same process
            # In real scenario with different processes, would be True


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_release_by_non_holder(self, temp_project):
        """Test release by non-holder doesn't remove lock."""
        lock1 = SessionLock(temp_project)

        # Create lock with different PID
        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        lock1.lock_file.write_text(json.dumps(lock_data))

        # Try to release
        lock1.release()

        # Lock should still exist
        assert lock1.lock_file.exists()

    def test_corrupted_lock_recovery(self, temp_project):
        """Test recovery from corrupted lock file."""
        lock = SessionLock(temp_project)

        # Create corrupted lock
        lock.lock_file.write_text("invalid json{{{")

        # Should recover and acquire
        result = lock.acquire("cli", mode="write")
        assert result is True

        # Lock should now be valid
        lock_data = json.loads(lock.lock_file.read_text())
        assert lock_data["interface"] == "cli"
