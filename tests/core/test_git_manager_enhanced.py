"""Unit tests for enhanced GitManager methods (Epic 23).

Tests for Stories 23.1-23.4:
- Transaction support methods (5 methods, 15 tests)
- Branch management methods (4 methods, 10 tests)
- File history query methods (4 methods, 12 tests)
- Query enhancement methods (2 methods, 8 tests)

Total: 14 methods, 45 unit tests
"""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from gao_dev.core.git_manager import GitManager


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def git_manager(tmp_path):
    """GitManager instance for temporary directory."""
    return GitManager(project_path=tmp_path)


@pytest.fixture
def mock_run_git_command():
    """Mock the _run_git_command method."""
    with patch.object(GitManager, '_run_git_command') as mock:
        yield mock


# ============================================================================
# STORY 23.1: TRANSACTION SUPPORT METHODS (15 tests)
# ============================================================================

class TestTransactionSupportMethods:
    """Test transaction support methods from Story 23.1."""

    def test_is_working_tree_clean_true(self, git_manager, mock_run_git_command):
        """Test is_working_tree_clean returns True for clean tree."""
        mock_run_git_command.return_value = ""  # Empty output = clean

        result = git_manager.is_working_tree_clean()

        assert result is True
        mock_run_git_command.assert_called_once_with(["status", "--porcelain"])

    def test_is_working_tree_clean_false(self, git_manager, mock_run_git_command):
        """Test is_working_tree_clean returns False for dirty tree."""
        mock_run_git_command.return_value = " M file.txt\n"  # Modified file

        result = git_manager.is_working_tree_clean()

        assert result is False

    def test_is_working_tree_clean_untracked(self, git_manager, mock_run_git_command):
        """Test is_working_tree_clean returns False with untracked files."""
        mock_run_git_command.return_value = "?? newfile.txt\n"

        result = git_manager.is_working_tree_clean()

        assert result is False

    def test_add_all_success(self, git_manager, mock_run_git_command):
        """Test add_all stages all changes."""
        mock_run_git_command.return_value = ""

        result = git_manager.add_all()

        assert result is True
        mock_run_git_command.assert_called_once_with(["add", "-A"])

    def test_add_all_empty_repo(self, git_manager, mock_run_git_command):
        """Test add_all on empty repository."""
        mock_run_git_command.return_value = ""

        result = git_manager.add_all()

        assert result is True

    def test_commit_success(self, git_manager, mock_run_git_command):
        """Test successful commit creation."""
        mock_run_git_command.side_effect = [
            "",  # commit command
            "abc1234\n"  # rev-parse --short HEAD
        ]

        sha = git_manager.commit("feat: test commit")

        assert sha == "abc1234"
        assert mock_run_git_command.call_count == 2

    def test_commit_returns_sha(self, git_manager, mock_run_git_command):
        """Validate commit SHA return value is 7 chars."""
        mock_run_git_command.side_effect = [
            "",
            "abc1234\n"
        ]

        sha = git_manager.commit("test: commit")

        assert len(sha) == 7
        assert sha == "abc1234"

    def test_commit_with_allow_empty(self, git_manager, mock_run_git_command):
        """Test empty commit creation."""
        mock_run_git_command.side_effect = ["", "abc1234\n"]

        sha = git_manager.commit("test: empty", allow_empty=True)

        assert sha == "abc1234"
        # Verify --allow-empty flag passed
        call_args = mock_run_git_command.call_args_list[0][0][0]
        assert "--allow-empty" in call_args

    def test_commit_fails_on_error(self, git_manager, mock_run_git_command):
        """Test commit raises exception on failure."""
        mock_run_git_command.side_effect = subprocess.CalledProcessError(
            1, "git commit", stderr="nothing to commit"
        )

        with pytest.raises(subprocess.CalledProcessError):
            git_manager.commit("test: fail")

    def test_reset_hard_success(self, git_manager, mock_run_git_command):
        """Test hard reset to HEAD."""
        mock_run_git_command.return_value = ""

        result = git_manager.reset_hard()

        assert result is True
        mock_run_git_command.assert_called_once_with(["reset", "--hard", "HEAD"])

    def test_reset_hard_to_specific_sha(self, git_manager, mock_run_git_command):
        """Test reset to specific commit."""
        mock_run_git_command.return_value = ""

        result = git_manager.reset_hard("abc1234")

        assert result is True
        mock_run_git_command.assert_called_once_with(["reset", "--hard", "abc1234"])

    def test_reset_hard_warning_logged(self, git_manager, mock_run_git_command):
        """Validate DESTRUCTIVE warning is logged."""
        mock_run_git_command.return_value = ""

        with patch.object(git_manager, '_log') as mock_log:
            git_manager.reset_hard()

            # Check warning was logged
            warning_calls = [call for call in mock_log.call_args_list
                           if call[0][0] == "warning"]
            assert len(warning_calls) > 0

    def test_get_head_sha_short(self, git_manager, mock_run_git_command):
        """Test short SHA retrieval (7 chars)."""
        mock_run_git_command.return_value = "abc1234\n"

        sha = git_manager.get_head_sha(short=True)

        assert sha == "abc1234"
        mock_run_git_command.assert_called_once_with(["rev-parse", "--short", "HEAD"])

    def test_get_head_sha_long(self, git_manager, mock_run_git_command):
        """Test long SHA retrieval (40 chars)."""
        full_sha = "abc1234567890abcdef1234567890abcdef12345"
        mock_run_git_command.return_value = full_sha + "\n"

        sha = git_manager.get_head_sha(short=False)

        assert sha == full_sha
        assert len(sha) == 40
        mock_run_git_command.assert_called_once_with(["rev-parse", "HEAD"])

    def test_transaction_flow_integration(self, git_manager, mock_run_git_command):
        """Test full flow: add_all → commit → get_sha."""
        mock_run_git_command.side_effect = [
            "",  # add -A
            "",  # commit
            "abc1234\n",  # rev-parse (from commit)
            "abc1234\n"   # get_head_sha
        ]

        # Full transaction flow
        git_manager.add_all()
        sha = git_manager.commit("feat: test")
        head_sha = git_manager.get_head_sha()

        assert sha == head_sha == "abc1234"


# ============================================================================
# STORY 23.2: BRANCH MANAGEMENT METHODS (10 tests)
# ============================================================================

class TestBranchManagementMethods:
    """Test branch management methods from Story 23.2."""

    def test_create_branch_success(self, git_manager, mock_run_git_command):
        """Test new branch creation without checkout."""
        mock_run_git_command.return_value = ""

        result = git_manager.create_branch("feature/test", checkout=False)

        assert result is True
        mock_run_git_command.assert_called_once_with(["branch", "feature/test"])

    def test_create_branch_and_checkout(self, git_manager, mock_run_git_command):
        """Test branch creation with immediate checkout."""
        mock_run_git_command.return_value = ""

        result = git_manager.create_branch("migration/test", checkout=True)

        assert result is True
        assert mock_run_git_command.call_count == 2
        mock_run_git_command.assert_any_call(["branch", "migration/test"])
        mock_run_git_command.assert_any_call(["checkout", "migration/test"])

    def test_create_branch_already_exists(self, git_manager, mock_run_git_command):
        """Test error when branch already exists."""
        mock_run_git_command.side_effect = subprocess.CalledProcessError(
            1, "git branch", stderr="branch already exists"
        )

        with pytest.raises(subprocess.CalledProcessError):
            git_manager.create_branch("existing-branch")

    def test_checkout_existing_branch(self, git_manager, mock_run_git_command):
        """Test switching to existing local branch."""
        mock_run_git_command.return_value = ""

        result = git_manager.checkout("main")

        assert result is True
        mock_run_git_command.assert_called_once_with(["checkout", "main"])

    def test_checkout_creates_tracking_branch(self, git_manager, mock_run_git_command):
        """Test checkout of remote branch creates tracking branch."""
        # First call fails (local doesn't exist), second succeeds (remote)
        mock_run_git_command.side_effect = [
            subprocess.CalledProcessError(1, "git checkout", stderr="branch not found"),
            ""  # Success on remote tracking
        ]

        result = git_manager.checkout("feature-branch")

        assert result is True
        assert mock_run_git_command.call_count == 2
        # Check remote tracking branch created
        remote_call = mock_run_git_command.call_args_list[1][0][0]
        assert "origin/feature-branch" in remote_call

    def test_checkout_branch_not_found(self, git_manager, mock_run_git_command):
        """Test error when branch doesn't exist locally or remotely."""
        mock_run_git_command.side_effect = subprocess.CalledProcessError(
            1, "git checkout", stderr="branch not found"
        )

        with pytest.raises(subprocess.CalledProcessError):
            git_manager.checkout("nonexistent")

    def test_delete_branch_success(self, git_manager, mock_run_git_command):
        """Test branch deletion."""
        mock_run_git_command.return_value = ""

        result = git_manager.delete_branch("old-branch")

        assert result is True
        mock_run_git_command.assert_called_once_with(["branch", "-d", "old-branch"])

    def test_delete_branch_with_force(self, git_manager, mock_run_git_command):
        """Test forced deletion of unmerged branch."""
        mock_run_git_command.return_value = ""

        result = git_manager.delete_branch("unmerged-branch", force=True)

        assert result is True
        mock_run_git_command.assert_called_once_with(["branch", "-D", "unmerged-branch"])

    def test_delete_branch_not_found(self, git_manager, mock_run_git_command):
        """Test error when branch doesn't exist."""
        mock_run_git_command.side_effect = subprocess.CalledProcessError(
            1, "git branch", stderr="branch not found"
        )

        with pytest.raises(subprocess.CalledProcessError):
            git_manager.delete_branch("nonexistent")

    def test_merge_no_fast_forward(self, git_manager, mock_run_git_command):
        """Test merge with --no-ff flag."""
        mock_run_git_command.return_value = ""

        result = git_manager.merge("feature-branch", no_ff=True, message="Merge feature")

        assert result is True
        call_args = mock_run_git_command.call_args[0][0]
        assert "--no-ff" in call_args
        assert "-m" in call_args
        assert "Merge feature" in call_args


# ============================================================================
# STORY 23.3: FILE HISTORY QUERY METHODS (12 tests)
# ============================================================================

class TestFileHistoryQueryMethods:
    """Test file history query methods from Story 23.3."""

    def test_get_last_commit_for_file_success(self, git_manager, mock_run_git_command):
        """Test commit info retrieval for tracked file."""
        commit_output = "abc1234567890abcdef|feat: update file|John Doe|2025-11-09 10:30:00\n"
        mock_run_git_command.return_value = commit_output

        info = git_manager.get_last_commit_for_file(Path("docs/file.md"))

        assert info is not None
        assert info["sha"] == "abc1234"
        assert info["full_sha"] == "abc1234567890abcdef"
        assert info["message"] == "feat: update file"
        assert info["author"] == "John Doe"

    def test_get_last_commit_for_file_not_found(self, git_manager, mock_run_git_command):
        """Test None return for non-existent file."""
        mock_run_git_command.return_value = ""  # Empty = not tracked

        info = git_manager.get_last_commit_for_file(Path("nonexistent.md"))

        assert info is None

    def test_get_last_commit_for_file_untracked(self, git_manager, mock_run_git_command):
        """Test None return for untracked file."""
        mock_run_git_command.return_value = ""

        info = git_manager.get_last_commit_for_file(Path("untracked.md"))

        assert info is None

    def test_get_last_commit_info_structure(self, git_manager, mock_run_git_command):
        """Validate returned dict structure."""
        commit_output = "abc1234|feat: test|Author|2025-11-09 10:30:00\n"
        mock_run_git_command.return_value = commit_output

        info = git_manager.get_last_commit_for_file(Path("file.md"))

        assert info is not None
        assert "sha" in info
        assert "full_sha" in info
        assert "message" in info
        assert "author" in info
        assert "date" in info

    def test_file_deleted_in_history_true(self, git_manager, mock_run_git_command):
        """Test detection of deleted file."""
        mock_run_git_command.return_value = "commit abc1234\nDeleted file\n"

        result = git_manager.file_deleted_in_history(Path("deleted.md"))

        assert result is True

    def test_file_deleted_in_history_false(self, git_manager, mock_run_git_command):
        """Test False for existing file."""
        mock_run_git_command.return_value = ""  # No deletions

        result = git_manager.file_deleted_in_history(Path("existing.md"))

        assert result is False

    def test_is_file_tracked_true(self, git_manager, mock_run_git_command):
        """Test True for tracked file."""
        mock_run_git_command.return_value = "docs/file.md\n"

        result = git_manager.is_file_tracked(Path("docs/file.md"))

        assert result is True

    def test_is_file_tracked_false(self, git_manager, mock_run_git_command):
        """Test False for untracked file."""
        mock_run_git_command.return_value = ""

        result = git_manager.is_file_tracked(Path("untracked.md"))

        assert result is False

    def test_get_file_status_clean(self, git_manager, mock_run_git_command):
        """Test 'clean' for committed, unchanged file."""
        mock_run_git_command.side_effect = [
            "",  # status --porcelain (empty)
            "file.md\n"  # ls-files (tracked)
        ]

        status = git_manager.get_file_status(Path("file.md"))

        assert status == "clean"

    def test_get_file_status_modified(self, git_manager, mock_run_git_command):
        """Test 'modified' for changed tracked file."""
        mock_run_git_command.return_value = " M file.md\n"

        status = git_manager.get_file_status(Path("file.md"))

        assert status == "modified"

    def test_get_file_status_staged(self, git_manager, mock_run_git_command):
        """Test 'staged' for added file."""
        mock_run_git_command.return_value = "A  newfile.md\n"

        status = git_manager.get_file_status(Path("newfile.md"))

        assert status == "staged"

    def test_get_file_status_untracked(self, git_manager, mock_run_git_command):
        """Test 'untracked' for new file."""
        mock_run_git_command.side_effect = [
            "?? newfile.md\n",  # status
        ]

        status = git_manager.get_file_status(Path("newfile.md"))

        assert status == "untracked"


# ============================================================================
# STORY 23.4: QUERY ENHANCEMENT METHODS (8 tests)
# ============================================================================

class TestQueryEnhancementMethods:
    """Test query enhancement methods from Story 23.4."""

    def test_get_commit_info_head(self, git_manager, mock_run_git_command):
        """Test retrieving HEAD commit info."""
        commit_output = (
            "abc1234567890|abc1234|feat: test|John Doe|john@example.com|2025-11-09 10:30:00\n"
            "\n"
            "file1.py\n"
            "file2.md\n"
        )
        mock_run_git_command.return_value = commit_output

        info = git_manager.get_commit_info("HEAD")

        assert info["sha"] == "abc1234"
        assert info["message"] == "feat: test"
        assert info["author"] == "John Doe"
        assert info["email"] == "john@example.com"
        assert len(info["files_changed"]) == 2

    def test_get_commit_info_specific_sha(self, git_manager, mock_run_git_command):
        """Test retrieving specific commit by SHA."""
        commit_output = (
            "def5678|def5678|fix: bug|Jane|jane@example.com|2025-11-08 15:00:00\n"
            "\n"
            "bugfix.py\n"
        )
        mock_run_git_command.return_value = commit_output

        info = git_manager.get_commit_info("def5678")

        assert info["sha"] == "def5678"
        assert info["message"] == "fix: bug"

    def test_get_commit_info_invalid_sha(self, git_manager, mock_run_git_command):
        """Test error handling for invalid SHA."""
        mock_run_git_command.side_effect = subprocess.CalledProcessError(
            1, "git show", stderr="invalid commit"
        )

        with pytest.raises(subprocess.CalledProcessError):
            git_manager.get_commit_info("invalid")

    def test_get_commit_info_structure(self, git_manager, mock_run_git_command):
        """Validate returned dict has all required keys."""
        commit_output = (
            "abc|abc|msg|author|email|date\n"
            "\n"
            "file.py\n"
        )
        mock_run_git_command.return_value = commit_output

        info = git_manager.get_commit_info()

        required_keys = ["sha", "full_sha", "message", "author", "email", "date", "files_changed"]
        for key in required_keys:
            assert key in info

    def test_get_commits_since_date(self, git_manager, mock_run_git_command):
        """Test commit range query by date."""
        commits_output = (
            "abc1234|abc1234|feat: first|John|john@example.com|2025-11-09\n"
            "def5678|def5678|fix: second|Jane|jane@example.com|2025-11-08\n"
        )
        mock_run_git_command.return_value = commits_output

        commits = git_manager.get_commits_since("2025-11-07", "HEAD")

        assert len(commits) == 2
        assert commits[0]["sha"] == "abc1234"
        assert commits[1]["sha"] == "def5678"

    def test_get_commits_since_sha(self, git_manager, mock_run_git_command):
        """Test commit range query by SHA."""
        commits_output = "abc1234|abc1234|feat: commit|Author|email|date\n"
        mock_run_git_command.return_value = commits_output

        commits = git_manager.get_commits_since("start-sha", "end-sha")

        assert len(commits) == 1
        assert commits[0]["sha"] == "abc1234"

    def test_get_commits_since_with_file_filter(self, git_manager, mock_run_git_command):
        """Test filtering commits by file path."""
        commits_output = "abc1234|abc1234|feat: update|Author|email|date\n"
        mock_run_git_command.return_value = commits_output

        commits = git_manager.get_commits_since(
            "start",
            "HEAD",
            file_path=Path("docs/file.md")
        )

        assert len(commits) == 1
        # Verify file path passed to git log
        call_args = mock_run_git_command.call_args[0][0]
        assert "--" in call_args

    def test_get_commits_since_empty_range(self, git_manager, mock_run_git_command):
        """Test empty result for no commits in range."""
        mock_run_git_command.return_value = ""

        commits = git_manager.get_commits_since("abc", "def")

        assert len(commits) == 0
        assert commits == []
