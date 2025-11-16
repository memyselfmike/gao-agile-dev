"""Unit tests for SessionLock."""

import json
import os
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from gao_dev.core.session_lock import SessionLock


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project directory."""
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir()
    return tmp_path


@pytest.fixture
def session_lock(temp_project):
    """Create SessionLock instance."""
    return SessionLock(temp_project)


class TestSessionLockBasics:
    """Test basic lock acquisition and release."""

    def test_init(self, session_lock, temp_project):
        """Test SessionLock initialization."""
        assert session_lock.project_root == temp_project
        assert session_lock.lock_file == temp_project / ".gao-dev" / "session.lock"
        assert session_lock.current_mode == "none"

    def test_read_lock_always_succeeds(self, session_lock):
        """Test read lock always succeeds."""
        result = session_lock.acquire("cli", mode="read")
        assert result is True
        assert session_lock.current_mode == "read"

    def test_write_lock_succeeds_when_no_lock_exists(self, session_lock):
        """Test write lock acquisition when no lock exists."""
        result = session_lock.acquire("cli", mode="write")
        assert result is True
        assert session_lock.current_mode == "write"
        assert session_lock.lock_file.exists()

    def test_write_lock_creates_correct_lock_file(self, session_lock):
        """Test write lock creates correct lock file format."""
        session_lock.acquire("cli", mode="write")

        lock_data = json.loads(session_lock.lock_file.read_text())
        assert lock_data["interface"] == "cli"
        assert lock_data["mode"] == "write"
        assert lock_data["pid"] == os.getpid()
        assert "timestamp" in lock_data

    def test_release_removes_lock_file(self, session_lock):
        """Test release removes lock file."""
        session_lock.acquire("cli", mode="write")
        assert session_lock.lock_file.exists()

        session_lock.release()
        assert not session_lock.lock_file.exists()
        assert session_lock.current_mode == "none"

    def test_release_when_no_lock_held(self, session_lock):
        """Test release is safe when no lock held."""
        # Should not raise
        session_lock.release()
        assert session_lock.current_mode == "none"

    def test_invalid_interface(self, session_lock):
        """Test invalid interface raises ValueError."""
        with pytest.raises(ValueError, match="Invalid interface"):
            session_lock.acquire("invalid", mode="write")

    def test_invalid_mode(self, session_lock):
        """Test invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid mode"):
            session_lock.acquire("cli", mode="invalid")


class TestWriteLockExclusivity:
    """Test write lock exclusivity."""

    def test_write_lock_denied_when_held_by_other(self, session_lock):
        """Test write lock denied when held by another process."""
        # Create lock file with different PID
        lock_data = {
            "interface": "web",
            "mode": "write",
            "pid": 99999,  # Different PID
            "timestamp": "2025-01-01T00:00:00",
        }
        session_lock.lock_file.write_text(json.dumps(lock_data))

        # Mock pid_exists to return True (process alive)
        with patch("psutil.pid_exists", return_value=True):
            result = session_lock.acquire("cli", mode="write")
            assert result is False
            assert session_lock.current_mode == "none"

    def test_write_lock_succeeds_when_same_process(self, session_lock):
        """Test write lock succeeds when already held by same process."""
        session_lock.acquire("cli", mode="write")

        # Try to acquire again
        result = session_lock.acquire("cli", mode="write")
        assert result is True
        assert session_lock.current_mode == "write"

    def test_stale_lock_removed(self, session_lock):
        """Test stale lock is automatically removed."""
        # Create lock file with dead process PID
        lock_data = {
            "interface": "web",
            "mode": "write",
            "pid": 99999,  # Dead process
            "timestamp": "2025-01-01T00:00:00",
        }
        session_lock.lock_file.write_text(json.dumps(lock_data))

        # Mock pid_exists to return False (process dead)
        with patch("psutil.pid_exists", return_value=False):
            result = session_lock.acquire("cli", mode="write")
            assert result is True
            assert session_lock.current_mode == "write"

            # Verify new lock data
            new_lock_data = json.loads(session_lock.lock_file.read_text())
            assert new_lock_data["interface"] == "cli"
            assert new_lock_data["pid"] == os.getpid()

    def test_corrupted_lock_file_removed(self, session_lock):
        """Test corrupted lock file is removed."""
        # Create corrupted lock file
        session_lock.lock_file.write_text("invalid json{{{")

        result = session_lock.acquire("cli", mode="write")
        assert result is True
        assert session_lock.current_mode == "write"


class TestLockStateQueries:
    """Test lock state query methods."""

    def test_is_write_locked_by_other_no_lock(self, session_lock):
        """Test is_write_locked_by_other when no lock exists."""
        result = session_lock.is_write_locked_by_other()
        assert result is False

    def test_is_write_locked_by_other_same_process(self, session_lock):
        """Test is_write_locked_by_other when we hold lock."""
        session_lock.acquire("cli", mode="write")
        result = session_lock.is_write_locked_by_other()
        assert result is False

    def test_is_write_locked_by_other_different_process(self, session_lock):
        """Test is_write_locked_by_other when another process holds lock."""
        lock_data = {
            "interface": "web",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=True):
            result = session_lock.is_write_locked_by_other()
            assert result is True

    def test_get_lock_state_no_lock(self, session_lock):
        """Test get_lock_state when no lock exists."""
        state = session_lock.get_lock_state()
        assert state["mode"] == "write"
        assert state["holder"] is None
        assert state["timestamp"] is None

    def test_get_lock_state_we_hold_lock(self, session_lock):
        """Test get_lock_state when we hold lock."""
        session_lock.acquire("cli", mode="write")
        state = session_lock.get_lock_state()
        assert state["mode"] == "write"
        assert state["holder"] == "cli"
        assert state["timestamp"] is not None

    def test_get_lock_state_other_holds_lock(self, session_lock):
        """Test get_lock_state when another process holds lock."""
        lock_data = {
            "interface": "web",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=True):
            state = session_lock.get_lock_state()
            assert state["mode"] == "read"
            assert state["holder"] == "web"
            assert state["timestamp"] == "2025-01-01T00:00:00"

    def test_get_lock_state_stale_lock(self, session_lock):
        """Test get_lock_state with stale lock."""
        lock_data = {
            "interface": "web",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=False):
            state = session_lock.get_lock_state()
            assert state["mode"] == "write"
            assert state["holder"] is None


class TestLockUpgradeDowngrade:
    """Test lock upgrade and downgrade operations."""

    def test_upgrade_from_read_to_write(self, session_lock):
        """Test upgrade from read lock to write lock."""
        session_lock.acquire("web", mode="read")
        assert session_lock.current_mode == "read"

        result = session_lock.upgrade("web")
        assert result is True
        assert session_lock.current_mode == "write"
        assert session_lock.lock_file.exists()

    def test_upgrade_fails_when_other_holds_write(self, session_lock):
        """Test upgrade fails when another process holds write lock."""
        # Create lock file with different PID
        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=True):
            result = session_lock.upgrade("web")
            assert result is False

    def test_downgrade_from_write_to_read(self, session_lock):
        """Test downgrade from write lock to read lock."""
        session_lock.acquire("cli", mode="write")
        assert session_lock.current_mode == "write"

        result = session_lock.downgrade("cli")
        assert result is True
        assert session_lock.current_mode == "read"
        assert not session_lock.lock_file.exists()

    def test_downgrade_fails_when_not_write_mode(self, session_lock):
        """Test downgrade fails when not in write mode."""
        session_lock.acquire("web", mode="read")

        result = session_lock.downgrade("web")
        assert result is False
        assert session_lock.current_mode == "read"


class TestForceUnlock:
    """Test force unlock operations."""

    def test_force_unlock_no_lock(self, session_lock):
        """Test force unlock when no lock exists."""
        result = session_lock.force_unlock()
        assert result is True

    def test_force_unlock_dead_process(self, session_lock):
        """Test force unlock with dead process."""
        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=False):
            result = session_lock.force_unlock()
            assert result is True
            assert not session_lock.lock_file.exists()

    def test_force_unlock_live_process_raises(self, session_lock):
        """Test force unlock raises when process is alive."""
        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch.object(SessionLock, "is_process_alive", return_value=True):
            with pytest.raises(RuntimeError, match="Cannot force unlock"):
                session_lock.force_unlock()

    def test_force_unlock_corrupted_lock(self, session_lock):
        """Test force unlock with corrupted lock file."""
        session_lock.lock_file.write_text("invalid json{{{")

        result = session_lock.force_unlock()
        assert result is True
        assert not session_lock.lock_file.exists()


class TestThreadSafety:
    """Test thread safety of lock operations."""

    def test_concurrent_write_lock_acquisition(self, session_lock):
        """Test concurrent write lock acquisition (race condition)."""
        results = []

        def acquire_lock(interface):
            result = session_lock.acquire(interface, mode="write")
            results.append(result)

        # Create threads trying to acquire lock simultaneously
        threads = [
            threading.Thread(target=acquire_lock, args=("cli",)),
            threading.Thread(target=acquire_lock, args=("web",)),
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Only one should succeed (either both True if same process, or one True one False)
        # Since both threads are same process, both might succeed
        assert any(results)

    def test_release_only_by_holder(self, session_lock):
        """Test lock can only be released by holder."""
        session_lock.acquire("cli", mode="write")

        # Simulate another process trying to release
        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,  # Different PID
            "timestamp": "2025-01-01T00:00:00",
        }
        session_lock.lock_file.write_text(json.dumps(lock_data))

        session_lock.release()

        # Lock should still exist (we didn't hold it)
        assert session_lock.lock_file.exists()


class TestProcessDetection:
    """Test process detection logic."""

    def test_is_process_alive_with_psutil(self, session_lock):
        """Test is_process_alive uses psutil when available."""
        with patch("psutil.pid_exists", return_value=True) as mock_pid:
            result = SessionLock.is_process_alive(12345)
            assert result is True
            mock_pid.assert_called_once_with(12345)

    def test_is_process_alive_current_process(self, session_lock):
        """Test is_process_alive for current process."""
        result = SessionLock.is_process_alive(os.getpid())
        assert result is True

    def test_is_process_alive_nonexistent_process(self, session_lock):
        """Test is_process_alive for nonexistent process."""
        # Use a very high PID unlikely to exist
        result = SessionLock.is_process_alive(999999)
        assert result is False


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_lock_file_directory_created(self, tmp_path):
        """Test .gao-dev directory is created if not exists."""
        # Don't create .gao-dev directory
        session_lock = SessionLock(tmp_path)
        assert (tmp_path / ".gao-dev").exists()

    def test_atomic_write_on_windows(self, session_lock):
        """Test atomic write works on Windows."""
        # This test verifies the Windows-specific rename logic
        with patch("os.name", "nt"):
            result = session_lock.acquire("cli", mode="write")
            assert result is True
            assert session_lock.lock_file.exists()

    def test_lock_persistence_across_instances(self, temp_project):
        """Test lock persists across SessionLock instances."""
        lock1 = SessionLock(temp_project)
        lock1.acquire("cli", mode="write")

        lock2 = SessionLock(temp_project)
        # lock2 should see lock1's lock
        # But since both are same process (same PID), lock2 will think it holds the lock
        # This test verifies the lock file persists
        assert lock2.lock_file.exists()
        lock_data = json.loads(lock2.lock_file.read_text())
        assert lock_data["interface"] == "cli"
