"""Integration tests for GitManager enhanced methods (Story 23.6).

These tests use real git operations (no mocks) on temporary repositories
to validate end-to-end functionality.

Total: 10 integration tests
"""

import subprocess
import tempfile
from pathlib import Path
import pytest

from gao_dev.core.git_manager import GitManager


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_git_repo():
    """Create temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Initialize git repo with main as default branch
        subprocess.run(["git", "init", "-b", "main"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

        yield repo_path
        # Cleanup automatic


@pytest.fixture
def git_manager(temp_git_repo):
    """GitManager instance for temporary repo."""
    return GitManager(project_path=temp_git_repo)


@pytest.fixture
def commit_test_file(temp_git_repo, git_manager):
    """Helper to create and commit a test file."""
    def _commit(filename, content, message):
        file_path = temp_git_repo / filename
        file_path.write_text(content)
        git_manager.add_all()
        return git_manager.commit(message)
    return _commit


# ============================================================================
# INTEGRATION TESTS (10 tests)
# ============================================================================

def test_transaction_workflow_complete(git_manager, temp_git_repo):
    """Test complete transaction workflow: add → commit → get SHA."""
    # Create test file
    test_file = temp_git_repo / "test.txt"
    test_file.write_text("Hello World")

    # Verify dirty tree
    assert not git_manager.is_working_tree_clean()

    # Stage changes
    assert git_manager.add_all()

    # Commit changes
    sha = git_manager.commit("test: add test file")
    assert sha
    assert len(sha) == 7  # Short SHA

    # Verify clean tree
    assert git_manager.is_working_tree_clean()

    # Verify SHA matches HEAD
    head_sha = git_manager.get_head_sha()
    assert sha == head_sha

    # Verify commit info
    commit_info = git_manager.get_commit_info()
    assert commit_info["sha"] == sha
    assert commit_info["message"] == "test: add test file"


def test_atomic_commit_rollback(git_manager, temp_git_repo, commit_test_file):
    """Test rollback on commit failure."""
    # Create initial commit
    commit_test_file("initial.txt", "initial", "initial commit")

    # Verify clean start
    assert git_manager.is_working_tree_clean()

    # Make changes to TRACKED file (reset_hard only works on tracked files)
    (temp_git_repo / "initial.txt").write_text("modified")

    # Verify dirty
    assert not git_manager.is_working_tree_clean()

    # Rollback changes
    git_manager.reset_hard()

    # Verify clean again (untracked files don't count as dirty for reset)
    # But tracked files should be restored
    tracked_content = (temp_git_repo / "initial.txt").read_text()
    assert tracked_content == "initial"


def test_branch_create_checkout_merge(git_manager, temp_git_repo, commit_test_file):
    """Test complete branch workflow."""
    # Create initial commit on main
    commit_test_file("main.txt", "main content", "initial commit")

    # Create and checkout feature branch
    git_manager.create_branch("feature/test", checkout=True)

    # Verify on feature branch
    current_branch = git_manager.get_current_branch()
    assert current_branch == "feature/test"

    # Create commit on feature branch
    commit_test_file("feature.txt", "feature content", "feat: add feature")

    # Checkout main
    git_manager.checkout("main")

    # Merge feature branch
    git_manager.merge("feature/test", no_ff=True, message="Merge feature")

    # Verify merge successful
    assert (temp_git_repo / "feature.txt").exists()


def test_branch_delete_after_merge(git_manager, temp_git_repo, commit_test_file):
    """Test branch cleanup after merge."""
    # Create initial commit
    commit_test_file("initial.txt", "initial", "initial commit")

    # Create feature branch
    git_manager.create_branch("feature/cleanup", checkout=True)
    commit_test_file("feature.txt", "feature", "feat: feature")

    # Merge to main
    git_manager.checkout("main")
    git_manager.merge("feature/cleanup")

    # Delete merged branch
    git_manager.delete_branch("feature/cleanup")

    # Verify branch deleted (would raise if trying to checkout)
    with pytest.raises(subprocess.CalledProcessError):
        git_manager.checkout("feature/cleanup")


def test_file_history_after_commits(git_manager, temp_git_repo, commit_test_file):
    """Test get_last_commit_for_file with real commits."""
    # Create file with multiple commits
    commit_test_file("history.txt", "version 1", "feat: v1")
    (temp_git_repo / "history.txt").write_text("version 2")
    git_manager.add_all()
    sha2 = git_manager.commit("feat: v2")

    # Get last commit for file
    commit_info = git_manager.get_last_commit_for_file(Path("history.txt"))

    assert commit_info is not None
    assert commit_info["sha"] == sha2
    assert "v2" in commit_info["message"]


def test_file_status_changes(git_manager, temp_git_repo, commit_test_file):
    """Test get_file_status through modify/stage/commit cycle."""
    file_path = Path("status.txt")

    # File doesn't exist - untracked
    (temp_git_repo / file_path).write_text("content")
    status = git_manager.get_file_status(file_path)
    assert status == "untracked"

    # Stage file - staged
    git_manager.add_all()
    status = git_manager.get_file_status(file_path)
    assert status == "staged"

    # Commit file - clean
    git_manager.commit("feat: add file")
    status = git_manager.get_file_status(file_path)
    assert status == "clean"

    # Modify file - modified
    (temp_git_repo / file_path).write_text("modified content")
    status = git_manager.get_file_status(file_path)
    assert status == "modified"


def test_multiple_commits_query(git_manager, temp_git_repo, commit_test_file):
    """Test get_commits_since with commit range."""
    # Create initial commit
    sha1 = commit_test_file("file1.txt", "content1", "feat: first")
    sha2 = commit_test_file("file2.txt", "content2", "feat: second")
    sha3 = commit_test_file("file3.txt", "content3", "feat: third")

    # Get commits since first
    commits = git_manager.get_commits_since(sha1, "HEAD")

    # Should get second and third commits (since is exclusive)
    assert len(commits) == 2
    assert commits[0]["sha"] == sha3  # Most recent first
    assert commits[1]["sha"] == sha2


def test_reset_hard_undoes_changes(git_manager, temp_git_repo, commit_test_file):
    """Test reset_hard rollback."""
    # Create initial commit
    commit_test_file("initial.txt", "initial", "initial commit")
    initial_sha = git_manager.get_head_sha()

    # Make more changes
    (temp_git_repo / "temp.txt").write_text("temporary")
    git_manager.add_all()
    git_manager.commit("temp: temporary commit")

    # Verify different SHA
    assert git_manager.get_head_sha() != initial_sha

    # Reset hard to initial
    git_manager.reset_hard(initial_sha)

    # Verify back to initial state
    assert git_manager.get_head_sha() == initial_sha
    assert not (temp_git_repo / "temp.txt").exists()


def test_dirty_tree_detection(git_manager, temp_git_repo, commit_test_file):
    """Test is_working_tree_clean with various states."""
    # Initial - clean (no commits yet)
    assert git_manager.is_working_tree_clean()

    # Create file - dirty
    (temp_git_repo / "file.txt").write_text("content")
    assert not git_manager.is_working_tree_clean()

    # Stage file - still dirty (staged changes)
    git_manager.add_all()
    assert not git_manager.is_working_tree_clean()

    # Commit - clean
    git_manager.commit("feat: add file")
    assert git_manager.is_working_tree_clean()

    # Modify - dirty
    (temp_git_repo / "file.txt").write_text("modified")
    assert not git_manager.is_working_tree_clean()


def test_cross_method_integration(git_manager, temp_git_repo, commit_test_file):
    """Test using multiple methods together in realistic workflow."""
    # Setup: Create initial state
    commit_test_file("main.txt", "main", "initial commit")

    # Create migration branch
    git_manager.create_branch("migration/test", checkout=True)

    # Phase 1: Migration step 1
    assert git_manager.is_working_tree_clean()
    (temp_git_repo / "migration1.txt").write_text("phase 1")
    git_manager.add_all()
    sha1 = git_manager.commit("migration: phase 1")

    # Phase 2: Migration step 2
    (temp_git_repo / "migration2.txt").write_text("phase 2")
    git_manager.add_all()
    sha2 = git_manager.commit("migration: phase 2")

    # Verify commits
    commits = git_manager.get_commits_since(sha1, "HEAD")
    assert len(commits) == 1  # Only phase 2 (since is exclusive)

    # Merge back to main
    git_manager.checkout("main")
    git_manager.merge("migration/test", no_ff=True, message="Complete migration")

    # Verify files exist
    assert (temp_git_repo / "migration1.txt").exists()
    assert (temp_git_repo / "migration2.txt").exists()

    # Check file tracking
    assert git_manager.is_file_tracked(Path("migration1.txt"))
    assert git_manager.is_file_tracked(Path("migration2.txt"))

    # Delete migration branch
    git_manager.delete_branch("migration/test")

    # Verify clean state
    assert git_manager.is_working_tree_clean()
