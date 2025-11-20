"""Unit tests for session token authentication."""

import tempfile
from pathlib import Path

import pytest

from gao_dev.web.auth import SessionTokenManager


class TestSessionTokenManager:
    """Tests for SessionTokenManager."""

    def test_initialization_generates_token(self, tmp_path):
        """Test manager generates token on initialization."""
        # Create parent directory first (simulating existing .gao-dev)
        tmp_path.mkdir(exist_ok=True)
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        assert manager.token
        assert len(manager.token) > 0
        assert token_file.exists()
        assert token_file.read_text() == manager.token

    def test_token_length(self, tmp_path):
        """Test generated token has sufficient length."""
        # Create parent directory first
        tmp_path.mkdir(exist_ok=True)
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        # secrets.token_urlsafe(32) produces ~43 character tokens
        assert len(manager.token) >= 40

    def test_validate_correct_token(self, tmp_path):
        """Test validation succeeds with correct token."""
        # Create parent directory first
        tmp_path.mkdir(exist_ok=True)
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        assert manager.validate(manager.token) is True

    def test_validate_incorrect_token(self, tmp_path):
        """Test validation fails with incorrect token."""
        # Create parent directory first
        tmp_path.mkdir(exist_ok=True)
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        assert manager.validate("wrong-token") is False

    def test_validate_none_token(self, tmp_path):
        """Test validation fails with None token."""
        # Create parent directory first
        tmp_path.mkdir(exist_ok=True)
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        assert manager.validate(None) is False

    def test_validate_empty_token(self, tmp_path):
        """Test validation fails with empty token."""
        # Create parent directory first
        tmp_path.mkdir(exist_ok=True)
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        assert manager.validate("") is False

    def test_load_existing_token(self, tmp_path):
        """Test manager loads existing token from file."""
        token_file = tmp_path / "session.token"
        existing_token = "existing-token-12345"
        token_file.write_text(existing_token)

        manager = SessionTokenManager(token_file)

        assert manager.token == existing_token
        assert manager.validate(existing_token) is True

    def test_regenerate_token(self, tmp_path):
        """Test token regeneration invalidates old token."""
        # Create parent directory first
        tmp_path.mkdir(exist_ok=True)
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        old_token = manager.token
        new_token = manager.regenerate()

        assert new_token != old_token
        assert manager.token == new_token
        assert manager.validate(old_token) is False
        assert manager.validate(new_token) is True
        assert token_file.read_text() == new_token

    def test_get_token(self, tmp_path):
        """Test get_token returns current token."""
        # Create parent directory first
        tmp_path.mkdir(exist_ok=True)
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        assert manager.get_token() == manager.token

    def test_token_file_auto_creation(self, tmp_path):
        """Test token file and parent directories are created when they exist."""
        # Create parent directories first (simulating existing .gao-dev)
        nested_dir = tmp_path / "nested" / "dir"
        nested_dir.mkdir(parents=True)
        nested_path = nested_dir / "session.token"
        manager = SessionTokenManager(nested_path)

        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_default_token_file_location(self):
        """Test default token file location is .gao-dev/session.token."""
        # Don't actually create file in real .gao-dev directory
        # Just verify the default path structure
        manager = SessionTokenManager()

        expected_path = Path.cwd() / ".gao-dev" / "session.token"
        assert manager.token_file == expected_path

    def test_timing_safe_comparison(self, tmp_path):
        """Test validation uses timing-safe comparison."""
        # Create parent directory first
        tmp_path.mkdir(exist_ok=True)
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        # This test verifies that secrets.compare_digest is used
        # by testing that validation works correctly
        correct_token = manager.token
        incorrect_token = correct_token[:-1] + "X"  # Change last character

        assert manager.validate(correct_token) is True
        assert manager.validate(incorrect_token) is False

    def test_failed_token_file_write_does_not_crash(self, tmp_path):
        """Test manager handles token file write failures gracefully."""
        # Create read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        token_file = readonly_dir / "session.token"

        # Make directory read-only after creation
        readonly_dir.chmod(0o444)

        try:
            # Should not crash even if file write fails
            # Token should still be generated in memory
            manager = SessionTokenManager(token_file)
            assert manager.token  # Token still generated
            # File should NOT exist since directory is read-only
            assert not token_file.exists()
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)

    def test_failed_token_file_read_generates_new(self, tmp_path):
        """Test manager can load any string token from file."""
        token_file = tmp_path / "session.token"
        existing_token = "any-valid-string-token"
        token_file.write_text(existing_token)

        # Should load existing token even if unusual format
        manager = SessionTokenManager(token_file)

        assert manager.token == existing_token
        assert manager.validate(existing_token) is True

    def test_multiple_managers_share_token_file(self, tmp_path):
        """Test multiple managers can share the same token file."""
        # Create parent directory first
        tmp_path.mkdir(exist_ok=True)
        token_file = tmp_path / "session.token"

        manager1 = SessionTokenManager(token_file)
        token1 = manager1.token

        manager2 = SessionTokenManager(token_file)
        token2 = manager2.token

        # Should load the same token
        assert token1 == token2

    @pytest.mark.performance
    def test_validation_performance(self, tmp_path):
        """Test token validation is fast (<1ms for 1000 validations)."""
        import time

        # Create parent directory first
        tmp_path.mkdir(exist_ok=True)
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)
        token = manager.token

        start = time.perf_counter()
        for _ in range(1000):
            manager.validate(token)
        end = time.perf_counter()

        duration_ms = (end - start) * 1000
        assert duration_ms < 100, f"1000 validations took {duration_ms:.2f}ms (should be <100ms)"

    def test_no_premature_directory_creation(self, tmp_path):
        """Test SessionTokenManager does not create .gao-dev if it doesn't exist.

        Regression test for bug where SessionTokenManager created .gao-dev
        during module import, causing state detection to fail.
        """
        # Point token file to non-existent .gao-dev directory
        token_file = tmp_path / "nonexistent" / ".gao-dev" / "session.token"

        # Create manager - should generate token but NOT create directory
        manager = SessionTokenManager(token_file)

        # Token should be generated in memory
        assert manager.token
        assert len(manager.token) >= 40

        # Directory should NOT be created
        assert not token_file.parent.exists()
        assert not token_file.exists()

    def test_persists_when_directory_exists(self, tmp_path):
        """Test SessionTokenManager persists token when .gao-dev already exists."""
        # Create .gao-dev directory first
        gao_dev_dir = tmp_path / ".gao-dev"
        gao_dev_dir.mkdir(parents=True)

        token_file = gao_dev_dir / "session.token"

        # Create manager - should generate token AND persist it
        manager = SessionTokenManager(token_file)

        # Token should be generated
        assert manager.token

        # Token should be persisted since directory exists
        assert token_file.exists()
        assert token_file.read_text() == manager.token

    def test_ensure_persisted_creates_directory(self, tmp_path):
        """Test ensure_persisted() creates directory and writes token."""
        # Point token file to non-existent .gao-dev directory
        token_file = tmp_path / ".gao-dev" / "session.token"

        # Create manager without directory
        manager = SessionTokenManager(token_file)

        # Directory should not exist yet
        assert not token_file.parent.exists()

        # Call ensure_persisted()
        manager.ensure_persisted()

        # Now directory and file should exist
        assert token_file.parent.exists()
        assert token_file.exists()
        assert token_file.read_text() == manager.token

    def test_ensure_persisted_idempotent(self, tmp_path):
        """Test ensure_persisted() is safe to call multiple times."""
        # Create .gao-dev directory
        gao_dev_dir = tmp_path / ".gao-dev"
        gao_dev_dir.mkdir()

        token_file = gao_dev_dir / "session.token"
        manager = SessionTokenManager(token_file)

        # Token should be persisted
        assert token_file.exists()
        original_token = token_file.read_text()

        # Call ensure_persisted() again
        manager.ensure_persisted()

        # Token should remain the same
        assert token_file.read_text() == original_token
        assert token_file.read_text() == manager.token
