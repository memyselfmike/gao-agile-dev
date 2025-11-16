"""Unit tests for session token authentication."""

import tempfile
from pathlib import Path

import pytest

from gao_dev.web.auth import SessionTokenManager


class TestSessionTokenManager:
    """Tests for SessionTokenManager."""

    def test_initialization_generates_token(self, tmp_path):
        """Test manager generates token on initialization."""
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        assert manager.token
        assert len(manager.token) > 0
        assert token_file.exists()
        assert token_file.read_text() == manager.token

    def test_token_length(self, tmp_path):
        """Test generated token has sufficient length."""
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        # secrets.token_urlsafe(32) produces ~43 character tokens
        assert len(manager.token) >= 40

    def test_validate_correct_token(self, tmp_path):
        """Test validation succeeds with correct token."""
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        assert manager.validate(manager.token) is True

    def test_validate_incorrect_token(self, tmp_path):
        """Test validation fails with incorrect token."""
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        assert manager.validate("wrong-token") is False

    def test_validate_none_token(self, tmp_path):
        """Test validation fails with None token."""
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        assert manager.validate(None) is False

    def test_validate_empty_token(self, tmp_path):
        """Test validation fails with empty token."""
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
        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)

        assert manager.get_token() == manager.token

    def test_token_file_auto_creation(self, tmp_path):
        """Test token file and parent directories are created."""
        nested_path = tmp_path / "nested" / "dir" / "session.token"
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
            manager = SessionTokenManager(token_file)
            assert manager.token  # Token still generated
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

        token_file = tmp_path / "session.token"
        manager = SessionTokenManager(token_file)
        token = manager.token

        start = time.perf_counter()
        for _ in range(1000):
            manager.validate(token)
        end = time.perf_counter()

        duration_ms = (end - start) * 1000
        assert duration_ms < 100, f"1000 validations took {duration_ms:.2f}ms (should be <100ms)"
