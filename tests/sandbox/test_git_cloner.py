"""Tests for GitCloner functionality."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from gao_dev.sandbox import (
    GitCloner,
    GitCloneError,
    GitNotInstalledError,
    InvalidGitUrlError,
)


class TestGitCloner:
    """Tests for GitCloner class."""

    @pytest.fixture
    def git_cloner(self):
        """Create GitCloner instance with mocked git check."""
        with patch("gao_dev.sandbox.git_cloner.subprocess.run") as mock_run:
            # Mock git --version check
            mock_run.return_value = Mock(returncode=0, stdout="git version 2.40.0")
            cloner = GitCloner()
        return cloner

    @pytest.fixture
    def temp_dest(self, tmp_path):
        """Create temporary destination directory."""
        return tmp_path / "test_repo"

    def test_init_checks_git_installed(self):
        """Test that initialization checks for git."""
        with patch("gao_dev.sandbox.git_cloner.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="git version 2.40.0")
            cloner = GitCloner()
            assert cloner is not None
            mock_run.assert_called_once()

    def test_init_raises_if_git_not_installed(self):
        """Test that initialization raises error if git not found."""
        with patch("gao_dev.sandbox.git_cloner.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            with pytest.raises(GitNotInstalledError):
                GitCloner()

    def test_validate_https_url(self, git_cloner):
        """Test validation of HTTPS URLs."""
        valid_urls = [
            "https://github.com/user/repo.git",
            "https://github.com/user/repo",
            "https://gitlab.com/user/project.git",
            "http://example.com/repo.git",
        ]
        for url in valid_urls:
            assert git_cloner.validate_git_url(url), f"URL should be valid: {url}"

    def test_validate_ssh_url(self, git_cloner):
        """Test validation of SSH URLs."""
        valid_urls = [
            "git@github.com:user/repo.git",
            "git@gitlab.com:user/project.git",
            "ssh://git@github.com/user/repo.git",
        ]
        for url in valid_urls:
            assert git_cloner.validate_git_url(url), f"URL should be valid: {url}"

    def test_validate_invalid_url(self, git_cloner):
        """Test validation rejects invalid URLs."""
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://example.com/repo.git",
            "javascript:alert(1)",
            None,
            123,
        ]
        for url in invalid_urls:
            assert not git_cloner.validate_git_url(url), f"URL should be invalid: {url}"

    @patch("gao_dev.sandbox.git_cloner.subprocess.run")
    def test_clone_repository_success(self, mock_run, git_cloner, temp_dest):
        """Test successful repository cloning."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Cloning into 'test_repo'...",
            stderr="",
        )

        result = git_cloner.clone_repository(
            "https://github.com/test/repo.git",
            temp_dest,
        )

        assert result is True
        mock_run.assert_called()

        # Verify clone command was constructed correctly
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "clone" in call_args
        assert "--depth" in call_args
        assert "https://github.com/test/repo.git" in call_args

    @patch("gao_dev.sandbox.git_cloner.subprocess.run")
    def test_clone_repository_with_branch(self, mock_run, git_cloner, temp_dest):
        """Test cloning specific branch."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Cloning into 'test_repo'...",
            stderr="",
        )

        result = git_cloner.clone_repository(
            "https://github.com/test/repo.git",
            temp_dest,
            branch="develop",
        )

        assert result is True

        # Verify branch argument was included
        call_args = mock_run.call_args[0][0]
        assert "--branch" in call_args
        assert "develop" in call_args

    @patch("gao_dev.sandbox.git_cloner.subprocess.run")
    def test_clone_repository_invalid_url_raises(self, mock_run, git_cloner, temp_dest):
        """Test that invalid URL raises InvalidGitUrlError."""
        with pytest.raises(InvalidGitUrlError):
            git_cloner.clone_repository(
                "not-a-valid-url",
                temp_dest,
            )

        # Should not call git at all
        assert not mock_run.called

    @patch("gao_dev.sandbox.git_cloner.subprocess.run")
    @patch("gao_dev.sandbox.git_cloner.time.sleep")
    def test_clone_repository_retries_on_network_error(
        self, mock_sleep, mock_run, git_cloner, temp_dest
    ):
        """Test that clone retries on network errors."""
        # First call is get_default_branch, then two clone attempts fail, third succeeds
        mock_run.side_effect = [
            Mock(returncode=0, stdout="ref: refs/heads/main\tHEAD\n", stderr=""),  # get_default_branch
            Mock(returncode=1, stderr="fatal: unable to access 'https://...'", stdout=""),
            Mock(returncode=1, stderr="fatal: could not resolve host", stdout=""),
            Mock(returncode=0, stdout="Cloning...", stderr=""),
        ]

        result = git_cloner.clone_repository(
            "https://github.com/test/repo.git",
            temp_dest,
        )

        assert result is True
        assert mock_run.call_count == 4  # 1 for get_default_branch, 3 for clone attempts
        assert mock_sleep.call_count == 2  # Sleep between retries

    @patch("gao_dev.sandbox.git_cloner.subprocess.run")
    @patch("gao_dev.sandbox.git_cloner.time.sleep")
    def test_clone_repository_fails_after_max_retries(
        self, mock_sleep, mock_run, git_cloner, temp_dest
    ):
        """Test that clone raises error after max retries."""
        # All attempts fail (including get_default_branch call)
        mock_run.return_value = Mock(
            returncode=1,
            stderr="fatal: network error",
            stdout="",
        )

        with pytest.raises(GitCloneError) as exc_info:
            git_cloner.clone_repository(
                "https://github.com/test/repo.git",
                temp_dest,
            )

        assert "Failed after 3 attempts" in str(exc_info.value)
        assert mock_run.call_count == 4  # 1 for get_default_branch, 3 for clone attempts

    @patch("gao_dev.sandbox.git_cloner.subprocess.run")
    def test_clone_repository_fails_on_non_retryable_error(
        self, mock_run, git_cloner, temp_dest
    ):
        """Test that non-retryable errors fail immediately."""
        mock_run.return_value = Mock(
            returncode=1,
            stderr="fatal: repository not found",
            stdout="",
        )

        with pytest.raises(GitCloneError):
            git_cloner.clone_repository(
                "https://github.com/test/nonexistent.git",
                temp_dest,
            )

        # Should call twice: once for get_default_branch, once for clone attempt
        assert mock_run.call_count == 2

    @patch("gao_dev.sandbox.git_cloner.subprocess.run")
    def test_clone_repository_cleans_up_on_failure(
        self, mock_run, git_cloner, temp_dest
    ):
        """Test that failed clone cleans up partial directory."""
        # Create destination directory to simulate partial clone
        temp_dest.mkdir(parents=True)
        (temp_dest / "test_file").write_text("test")

        mock_run.return_value = Mock(
            returncode=1,
            stderr="fatal: authentication failed",
            stdout="",
        )

        with pytest.raises(GitCloneError):
            git_cloner.clone_repository(
                "https://github.com/test/repo.git",
                temp_dest,
            )

        # Directory should be cleaned up
        assert not temp_dest.exists()

    @patch("gao_dev.sandbox.git_cloner.subprocess.run")
    def test_clone_repository_timeout(self, mock_run, git_cloner, temp_dest):
        """Test timeout handling during clone."""
        # First call is get_default_branch (succeeds), then clone times out
        mock_run.side_effect = [
            Mock(returncode=0, stdout="ref: refs/heads/main\tHEAD\n", stderr=""),  # get_default_branch
            subprocess.TimeoutExpired(cmd="git clone", timeout=300),
            subprocess.TimeoutExpired(cmd="git clone", timeout=300),
            subprocess.TimeoutExpired(cmd="git clone", timeout=300),
        ]

        with pytest.raises(GitCloneError) as exc_info:
            git_cloner.clone_repository(
                "https://github.com/test/repo.git",
                temp_dest,
            )

        error_message = str(exc_info.value).lower()
        assert "timeout" in error_message or "timed out" in error_message

    @patch("gao_dev.sandbox.git_cloner.subprocess.run")
    def test_get_default_branch_success(self, mock_run, git_cloner):
        """Test getting default branch from repository."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="ref: refs/heads/main\tHEAD\n",
            stderr="",
        )

        branch = git_cloner.get_default_branch("https://github.com/test/repo.git")

        assert branch == "main"

    @patch("gao_dev.sandbox.git_cloner.subprocess.run")
    def test_get_default_branch_master(self, mock_run, git_cloner):
        """Test detecting 'master' as default branch."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="ref: refs/heads/master\tHEAD\n",
            stderr="",
        )

        branch = git_cloner.get_default_branch("https://github.com/test/repo.git")

        assert branch == "master"

    @patch("gao_dev.sandbox.git_cloner.subprocess.run")
    def test_get_default_branch_falls_back_to_main(self, mock_run, git_cloner):
        """Test fallback to 'main' when detection fails."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",  # Empty output
            stderr="",
        )

        branch = git_cloner.get_default_branch("https://github.com/test/repo.git")

        assert branch == "main"

    @patch("gao_dev.sandbox.git_cloner.subprocess.run")
    def test_get_default_branch_error(self, mock_run, git_cloner):
        """Test error handling when querying default branch."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="fatal: could not read from remote repository",
        )

        with pytest.raises(GitCloneError):
            git_cloner.get_default_branch("https://github.com/test/repo.git")

    def test_is_retryable_error(self, git_cloner):
        """Test identification of retryable errors."""
        retryable_errors = [
            "connection timeout",
            "network is unreachable",
            "could not resolve host",
            "failed to connect",
            "temporary failure in name resolution",
        ]

        for error in retryable_errors:
            assert git_cloner._is_retryable_error(error), f"Should be retryable: {error}"

    def test_is_not_retryable_error(self, git_cloner):
        """Test identification of non-retryable errors."""
        non_retryable_errors = [
            "repository not found",
            "authentication failed",
            "permission denied",
            "does not exist",
        ]

        for error in non_retryable_errors:
            assert not git_cloner._is_retryable_error(
                error
            ), f"Should not be retryable: {error}"

    @patch("gao_dev.sandbox.git_cloner.subprocess.run")
    def test_clone_creates_parent_directories(self, mock_run, git_cloner, tmp_path):
        """Test that clone creates parent directories if needed."""
        deep_dest = tmp_path / "a" / "b" / "c" / "repo"

        mock_run.return_value = Mock(
            returncode=0,
            stdout="Cloning...",
            stderr="",
        )

        git_cloner.clone_repository(
            "https://github.com/test/repo.git",
            deep_dest,
        )

        # Parent directories should be created
        assert deep_dest.parent.exists()


class TestGitClonerIntegration:
    """Integration tests for GitCloner with real git operations."""

    @pytest.fixture
    def git_cloner(self):
        """Create GitCloner instance (requires git installed)."""
        try:
            return GitCloner()
        except GitNotInstalledError:
            pytest.skip("Git not installed")

    @pytest.mark.integration
    def test_clone_real_repository(self, git_cloner, tmp_path):
        """
        Test cloning a real public repository.

        NOTE: This is an integration test that requires network access.
        Uses a small, reliable public repository.
        """
        test_repo = "https://github.com/webventurer/simple-nextjs-starter"
        dest = tmp_path / "real_repo"

        result = git_cloner.clone_repository(test_repo, dest)

        assert result is True
        assert dest.exists()
        assert (dest / ".git").exists()
        assert (dest / "package.json").exists()

    @pytest.mark.integration
    def test_clone_real_repository_specific_branch(self, git_cloner, tmp_path):
        """Test cloning a specific branch from real repository."""
        test_repo = "https://github.com/webventurer/simple-nextjs-starter"
        dest = tmp_path / "real_repo_branch"

        result = git_cloner.clone_repository(test_repo, dest, branch="main")

        assert result is True
        assert dest.exists()

    @pytest.mark.integration
    def test_clone_nonexistent_repository(self, git_cloner, tmp_path):
        """Test that cloning non-existent repository fails appropriately."""
        fake_repo = "https://github.com/this-user-definitely-does-not-exist-12345/repo.git"
        dest = tmp_path / "fake_repo"

        with pytest.raises(GitCloneError):
            git_cloner.clone_repository(fake_repo, dest)

        # Directory should be cleaned up
        assert not dest.exists()

    @pytest.mark.integration
    def test_get_default_branch_real_repository(self, git_cloner):
        """Test getting default branch from real repository."""
        test_repo = "https://github.com/webventurer/simple-nextjs-starter"

        branch = git_cloner.get_default_branch(test_repo)

        assert branch in ["main", "master"]  # Accept either


class TestGitClonerExceptions:
    """Tests for GitCloner exception handling."""

    def test_git_clone_error_attributes(self):
        """Test GitCloneError has correct attributes."""
        error = GitCloneError("https://example.com/repo.git", "network error")

        assert error.repo_url == "https://example.com/repo.git"
        assert error.reason == "network error"
        assert "https://example.com/repo.git" in str(error)
        assert "network error" in str(error)

    def test_invalid_git_url_error_attributes(self):
        """Test InvalidGitUrlError has correct attributes."""
        error = InvalidGitUrlError("not-a-url", "invalid format")

        assert error.url == "not-a-url"
        assert error.reason == "invalid format"
        assert "not-a-url" in str(error)

    def test_git_not_installed_error_message(self):
        """Test GitNotInstalledError has helpful message."""
        error = GitNotInstalledError()

        assert "git" in str(error).lower()
        assert "install" in str(error).lower()
