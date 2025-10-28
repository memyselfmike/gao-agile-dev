"""Tests for GitManager functionality."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call
from datetime import datetime

import pytest

from gao_dev.sandbox.git_manager import GitManager
from gao_dev.sandbox.exceptions import ProjectStateError


class TestGitManager:
    """Tests for GitManager class."""

    @pytest.fixture
    def temp_project_path(self, tmp_path):
        """Create temporary project directory."""
        project_path = tmp_path / "test_project"
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path

    @pytest.fixture
    def git_manager(self, temp_project_path):
        """Create GitManager instance for testing."""
        return GitManager(temp_project_path)

    def test_init_sets_project_path(self, temp_project_path):
        """Test that initialization sets project path correctly."""
        manager = GitManager(temp_project_path)
        assert manager.project_path == temp_project_path.resolve()

    def test_init_creates_logger(self, git_manager):
        """Test that initialization creates a logger."""
        assert git_manager.logger is not None

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_init_repo_success(self, mock_run, git_manager, temp_project_path):
        """Test successful git repository initialization."""
        # Mock git commands
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = git_manager.init_repo(
            user_name="Test User",
            user_email="test@example.com",
            initial_commit=False,
        )

        # Verify git init was called
        assert any(
            call_args[0][0] == ["git", "init"]
            for call_args in mock_run.call_args_list
        )

        # Verify user config was set
        assert any(
            call_args[0][0] == ["git", "config", "user.name", "Test User"]
            for call_args in mock_run.call_args_list
        )
        assert any(
            call_args[0][0] == ["git", "config", "user.email", "test@example.com"]
            for call_args in mock_run.call_args_list
        )

        # Verify result
        assert result["initialized"] is True
        assert result["user_name"] == "Test User"
        assert result["user_email"] == "test@example.com"
        assert "timestamp" in result

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_init_repo_with_defaults(self, mock_run, git_manager):
        """Test git init with default user name and email."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = git_manager.init_repo(initial_commit=False)

        # Verify default values used
        assert result["user_name"] == GitManager.DEFAULT_USER_NAME
        assert result["user_email"] == GitManager.DEFAULT_USER_EMAIL

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_init_repo_with_initial_commit(self, mock_run, git_manager):
        """Test git init with initial commit."""
        # Mock git commands
        def mock_git_command(cmd, **kwargs):
            if cmd[1] == "rev-parse":
                return Mock(returncode=0, stdout="abc1234\n", stderr="")
            elif cmd[1] == "diff-tree":
                return Mock(returncode=0, stdout=".gitignore\n", stderr="")
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = mock_git_command

        result = git_manager.init_repo(initial_commit=True)

        # Verify commit was created
        assert any(
            call_args[0][0][:2] == ["git", "commit"]
            for call_args in mock_run.call_args_list
        )

        # Verify result includes commit info
        assert result["initialized"] is True
        assert "commit_hash" in result
        assert result["commit_hash"] == "abc1234"

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_init_repo_creates_gitignore(self, mock_run, git_manager, temp_project_path):
        """Test that .gitignore is created during init."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        git_manager.init_repo(initial_commit=False)

        gitignore_path = temp_project_path / ".gitignore"
        assert gitignore_path.exists()
        content = gitignore_path.read_text()
        assert "__pycache__/" in content
        assert "node_modules/" in content
        assert ".env" in content

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_init_repo_preserves_existing_gitignore(
        self, mock_run, git_manager, temp_project_path
    ):
        """Test that existing .gitignore is not overwritten."""
        # Create existing .gitignore
        gitignore_path = temp_project_path / ".gitignore"
        gitignore_path.write_text("# Custom gitignore\nmy-file.txt\n")

        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        git_manager.init_repo(initial_commit=False)

        # Verify original content preserved
        content = gitignore_path.read_text()
        assert "# Custom gitignore" in content
        assert "my-file.txt" in content

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_init_repo_fails_gracefully(self, mock_run, git_manager):
        """Test that init_repo raises error on git failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["git", "init"], stderr="Git error"
        )

        with pytest.raises(ProjectStateError) as exc_info:
            git_manager.init_repo()

        # Check that ProjectStateError was raised with correct states
        assert exc_info.value.current_state == "uninitialized"
        assert exc_info.value.required_state == "git_initialized"

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_create_commit_success(self, mock_run, git_manager):
        """Test successful commit creation."""
        # Mock git commands
        def mock_git_command(cmd, **kwargs):
            if cmd[1] == "rev-parse":
                return Mock(returncode=0, stdout="abc1234\n", stderr="")
            elif cmd[1] == "diff-tree":
                return Mock(
                    returncode=0, stdout="file1.py\nfile2.py\n", stderr=""
                )
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = mock_git_command

        result = git_manager.create_commit(
            message="feat: add new feature",
            add_all=True,
            allow_empty=False,
        )

        # Verify git add was called
        assert any(
            call_args[0][0] == ["git", "add", "-A"]
            for call_args in mock_run.call_args_list
        )

        # Verify commit was created
        assert any(
            call_args[0][0][:3] == ["git", "commit", "-m"]
            for call_args in mock_run.call_args_list
        )

        # Verify result
        assert result["hash"] == "abc1234"
        assert result["message"] == "feat: add new feature"
        assert result["files_changed"] == ["file1.py", "file2.py"]
        assert "timestamp" in result

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_create_commit_with_allow_empty(self, mock_run, git_manager):
        """Test commit creation with allow_empty flag."""
        mock_run.return_value = Mock(returncode=0, stdout="abc1234\n", stderr="")

        git_manager.create_commit(
            message="chore: empty commit",
            allow_empty=True,
        )

        # Verify --allow-empty flag was used
        commit_calls = [
            call_args[0][0]
            for call_args in mock_run.call_args_list
            if call_args[0][0][1] == "commit"
        ]
        assert any("--allow-empty" in cmd for cmd in commit_calls)

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_create_commit_without_add_all(self, mock_run, git_manager):
        """Test commit creation without staging all files."""
        mock_run.return_value = Mock(returncode=0, stdout="abc1234\n", stderr="")

        git_manager.create_commit(
            message="feat: selective commit",
            add_all=False,
        )

        # Verify git add was NOT called
        assert not any(
            call_args[0][0][:2] == ["git", "add"]
            for call_args in mock_run.call_args_list
        )

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_create_commit_fails_gracefully(self, mock_run, git_manager):
        """Test that create_commit raises error on failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["git", "commit"], stderr="Nothing to commit"
        )

        with pytest.raises(ProjectStateError) as exc_info:
            git_manager.create_commit(message="test")

        # Check that ProjectStateError was raised with correct states
        assert exc_info.value.current_state == "uncommitted"
        assert exc_info.value.required_state == "committed"

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_get_status_not_git_repo(self, mock_run, git_manager):
        """Test get_status when directory is not a git repo."""
        # Mock git rev-parse to fail (not a repo)
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=128, cmd=["git", "rev-parse"], stderr="Not a git repository"
        )

        status = git_manager.get_status()

        assert status["is_repo"] is False
        assert status["has_commits"] is False
        assert status["clean"] is True
        assert status["branch"] is None
        assert status["staged_files"] == []
        assert status["unstaged_files"] == []
        assert status["untracked_files"] == []

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_get_status_clean_repo(self, mock_run, git_manager):
        """Test get_status for clean repository."""
        # Mock git commands for clean repo
        def mock_git_command(cmd, **kwargs):
            if cmd[1] == "rev-parse" and "--git-dir" in cmd:
                return Mock(returncode=0, stdout=".git\n", stderr="")
            elif cmd[1] == "rev-parse" and "--abbrev-ref" in cmd:
                return Mock(returncode=0, stdout="main\n", stderr="")
            elif cmd[1] == "rev-parse" and "HEAD" in cmd:
                return Mock(returncode=0, stdout="abc1234\n", stderr="")
            else:
                # All file status commands return empty
                return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = mock_git_command

        status = git_manager.get_status()

        assert status["is_repo"] is True
        assert status["has_commits"] is True
        assert status["clean"] is True
        assert status["branch"] == "main"
        assert status["staged_files"] == []
        assert status["unstaged_files"] == []
        assert status["untracked_files"] == []

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_get_status_with_changes(self, mock_run, git_manager):
        """Test get_status with staged, unstaged, and untracked files."""
        # Mock git commands
        def mock_git_command(cmd, **kwargs):
            if cmd[1] == "rev-parse" and "--git-dir" in cmd:
                return Mock(returncode=0, stdout=".git\n", stderr="")
            elif cmd[1] == "rev-parse" and "--abbrev-ref" in cmd:
                return Mock(returncode=0, stdout="feature-branch\n", stderr="")
            elif cmd[1] == "rev-parse" and "HEAD" in cmd:
                return Mock(returncode=0, stdout="abc1234\n", stderr="")
            elif cmd[1] == "diff" and "--cached" in cmd:
                # Staged files
                return Mock(returncode=0, stdout="staged.py\n", stderr="")
            elif cmd[1] == "diff" and "--name-only" in cmd:
                # Unstaged files
                return Mock(returncode=0, stdout="modified.py\n", stderr="")
            elif cmd[1] == "ls-files":
                # Untracked files
                return Mock(returncode=0, stdout="new_file.py\n", stderr="")
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = mock_git_command

        status = git_manager.get_status()

        assert status["is_repo"] is True
        assert status["has_commits"] is True
        assert status["clean"] is False
        assert status["branch"] == "feature-branch"
        assert status["staged_files"] == ["staged.py"]
        assert status["unstaged_files"] == ["modified.py"]
        assert status["untracked_files"] == ["new_file.py"]

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_get_status_no_commits_yet(self, mock_run, git_manager):
        """Test get_status when repo has no commits."""
        # Mock git commands
        def mock_git_command(cmd, **kwargs):
            if cmd[1] == "rev-parse" and "--git-dir" in cmd:
                return Mock(returncode=0, stdout=".git\n", stderr="")
            elif cmd[1] == "rev-parse" and "--abbrev-ref" in cmd:
                return Mock(returncode=0, stdout="main\n", stderr="")
            elif cmd[1] == "rev-parse" and "HEAD" in cmd:
                # No commits yet
                raise subprocess.CalledProcessError(
                    returncode=128, cmd=cmd, stderr="unknown revision"
                )
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = mock_git_command

        status = git_manager.get_status()

        assert status["is_repo"] is True
        assert status["has_commits"] is False

    def test_run_git_command_success(self, git_manager):
        """Test _run_git_command with successful execution."""
        with patch("gao_dev.sandbox.git_manager.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="success\n", stderr="")

            result = git_manager._run_git_command(["status"])

            assert result == "success\n"
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0] == ["git", "status"]
            assert call_args[1]["cwd"] == git_manager.project_path

    def test_run_git_command_failure(self, git_manager):
        """Test _run_git_command with failed execution."""
        with patch("gao_dev.sandbox.git_manager.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1, cmd=["git", "status"], stderr="Error"
            )

            with pytest.raises(subprocess.CalledProcessError):
                git_manager._run_git_command(["status"])

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_is_git_repo_true(self, mock_run, git_manager):
        """Test _is_git_repo returns True for git repository."""
        mock_run.return_value = Mock(returncode=0, stdout=".git\n", stderr="")

        assert git_manager._is_git_repo() is True

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_is_git_repo_false(self, mock_run, git_manager):
        """Test _is_git_repo returns False for non-git directory."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=128, cmd=["git", "rev-parse"], stderr="Not a git repository"
        )

        assert git_manager._is_git_repo() is False

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_has_commits_true(self, mock_run, git_manager):
        """Test _has_commits returns True when commits exist."""
        mock_run.return_value = Mock(returncode=0, stdout="abc1234\n", stderr="")

        assert git_manager._has_commits() is True

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_has_commits_false(self, mock_run, git_manager):
        """Test _has_commits returns False with no commits."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=128, cmd=["git", "rev-parse"], stderr="unknown revision"
        )

        assert git_manager._has_commits() is False

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_get_staged_files(self, mock_run, git_manager):
        """Test _get_staged_files returns list of staged files."""
        mock_run.return_value = Mock(
            returncode=0, stdout="file1.py\nfile2.py\n", stderr=""
        )

        files = git_manager._get_staged_files()

        assert files == ["file1.py", "file2.py"]

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_get_unstaged_files(self, mock_run, git_manager):
        """Test _get_unstaged_files returns list of modified files."""
        mock_run.return_value = Mock(
            returncode=0, stdout="modified.py\n", stderr=""
        )

        files = git_manager._get_unstaged_files()

        assert files == ["modified.py"]

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_get_untracked_files(self, mock_run, git_manager):
        """Test _get_untracked_files returns list of untracked files."""
        mock_run.return_value = Mock(
            returncode=0, stdout="new_file.py\nREADME.md\n", stderr=""
        )

        files = git_manager._get_untracked_files()

        assert files == ["new_file.py", "README.md"]

    @patch("gao_dev.sandbox.git_manager.subprocess.run")
    def test_get_changed_files(self, mock_run, git_manager):
        """Test _get_changed_files returns files changed in commit."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="src/main.py\ntests/test_main.py\n",
            stderr="",
        )

        files = git_manager._get_changed_files("abc1234")

        assert files == ["src/main.py", "tests/test_main.py"]
        # Verify correct git command
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == [
            "git",
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "abc1234",
        ]


class TestGitManagerIntegration:
    """Integration tests for GitManager with real git operations."""

    @pytest.fixture
    def real_project_path(self, tmp_path):
        """Create real project directory for integration tests."""
        project_path = tmp_path / "integration_test"
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path

    @pytest.fixture
    def real_git_manager(self, real_project_path):
        """Create GitManager with real project path."""
        return GitManager(real_project_path)

    def test_full_workflow_integration(self, real_git_manager, real_project_path):
        """Test complete git workflow: init, commit, status."""
        # Initialize repository
        init_result = real_git_manager.init_repo(initial_commit=True)
        assert init_result["initialized"] is True
        assert "commit_hash" in init_result

        # Verify .git directory exists
        assert (real_project_path / ".git").exists()

        # Verify .gitignore exists
        assert (real_project_path / ".gitignore").exists()

        # Check status
        status = real_git_manager.get_status()
        assert status["is_repo"] is True
        assert status["has_commits"] is True
        assert status["clean"] is True
        # Branch could be 'main' or 'master' depending on git version
        assert status["branch"] in ["main", "master"]

        # Create a new file
        test_file = real_project_path / "test.py"
        test_file.write_text("print('hello')\n")

        # Check status shows untracked file
        status = real_git_manager.get_status()
        assert not status["clean"]
        assert "test.py" in status["untracked_files"]

        # Create commit
        commit_result = real_git_manager.create_commit(
            message="feat: add test file",
            add_all=True,
        )
        assert commit_result["hash"]
        assert "test.py" in commit_result["files_changed"]

        # Verify clean status after commit
        status = real_git_manager.get_status()
        assert status["clean"] is True
        assert status["has_commits"] is True
        # Branch could be 'main' or 'master' depending on git version
        assert status["branch"] in ["main", "master"]
