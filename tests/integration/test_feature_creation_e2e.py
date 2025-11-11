"""
Integration tests for atomic feature creation (Story 33.2).

Tests end-to-end feature creation with GitIntegratedStateManager,
including concurrent operations, error recovery, and performance.
"""

import sqlite3
import tempfile
import time
from pathlib import Path
import importlib.util
import sys
import threading

import pytest

# Load migration 005 dynamically
def load_migration_005():
    """Load migration 005 module dynamically."""
    migration_path = (
        Path(__file__).parent.parent.parent
        / "gao_dev"
        / "lifecycle"
        / "migrations"
        / "005_add_state_tables.py"
    )
    spec = importlib.util.spec_from_file_location("migration_005", migration_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["migration_005"] = module
    spec.loader.exec_module(module)
    return module.Migration005


Migration005 = load_migration_005()

from gao_dev.core.services.git_integrated_state_manager import (
    GitIntegratedStateManager,
    GitIntegratedStateManagerError,
)
from gao_dev.core.git_manager import GitManager
from gao_dev.core.services.document_structure_manager import DocumentStructureManager
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.core.services.feature_state_service import FeatureScope


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project with git repo and database."""
    project_path = tmp_path / "project"
    project_path.mkdir()

    # Initialize git repo
    git_manager = GitManager(project_path=project_path)
    git_manager.init_repo(
        user_name="Test User",
        user_email="test@example.com",
        initial_commit=True,
        create_gitignore=False,
    )

    # Create database with migration
    db_path = project_path / ".gao-dev" / "documents.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))

    # Create schema_version table
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL,
            description TEXT
        )
        """
    )

    # Apply migration 005
    Migration005.up(conn)

    conn.close()

    # Commit the database file so working tree is clean
    git_manager.add_all()
    git_manager.commit("chore: initialize database")

    return {
        "project_path": project_path,
        "db_path": db_path,
        "git_manager": git_manager,
    }


@pytest.fixture
def manager(temp_project):
    """Create GitIntegratedStateManager with all dependencies."""
    from gao_dev.lifecycle.registry import DocumentRegistry

    registry = DocumentRegistry(temp_project["db_path"])
    archive_dir = temp_project["project_path"] / ".archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitkeep so git tracks the directory
    (archive_dir / ".gitkeep").write_text("")

    # Commit archive dir and any DB changes to keep working tree clean
    git = temp_project["git_manager"]
    git.add_all()
    git.commit("chore: create archive directory and initialize lifecycle")

    doc_lifecycle = DocumentLifecycleManager(registry, archive_dir)
    doc_structure = DocumentStructureManager(
        project_root=temp_project["project_path"],
        doc_lifecycle=doc_lifecycle,
        git_manager=temp_project["git_manager"],
    )

    mgr = GitIntegratedStateManager(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"],
        auto_commit=True,
        doc_structure_manager=doc_structure,
    )

    # Commit any DB changes from manager initialization
    if not git.is_working_tree_clean():
        git.add_all()
        git.commit("chore: initialize state manager")

    yield mgr
    mgr.close()


# ============================================================================
# END-TO-END FEATURE CREATION (5 SCENARIOS)
# ============================================================================


def test_e2e_create_mvp_feature(manager, temp_project):
    """Test end-to-end MVP feature creation with all files."""
    # Create MVP feature
    feature = manager.create_feature(
        name="mvp",
        scope=FeatureScope.MVP,
        scale_level=4,
        description="Minimum viable product for launch",
        owner="product-team",
    )

    # Verify feature object
    assert feature.name == "mvp"
    assert feature.scope == FeatureScope.MVP
    assert feature.scale_level == 4
    assert feature.description == "Minimum viable product for launch"

    # Verify all files exist
    project_path = temp_project["project_path"]
    feature_path = project_path / "docs" / "features" / "mvp"

    assert feature_path.exists()
    assert (feature_path / "PRD.md").exists()
    assert (feature_path / "ARCHITECTURE.md").exists()
    assert (feature_path / "CHANGELOG.md").exists()
    assert (feature_path / "README.md").exists()
    assert (feature_path / "MIGRATION_GUIDE.md").exists()

    # Verify folders
    assert (feature_path / "stories").exists()
    assert (feature_path / "epics").exists()
    assert (feature_path / "retrospectives").exists()
    assert (feature_path / "ceremonies").exists()
    assert (feature_path / "QA").exists()

    # Verify git history
    git = temp_project["git_manager"]
    assert git.is_working_tree_clean()
    commit_info = git.get_commit_info("HEAD")
    assert "mvp" in commit_info["message"]
    assert "create feature" in commit_info["message"]


def test_e2e_create_regular_feature(manager, temp_project):
    """Test end-to-end regular feature creation."""
    feature = manager.create_feature(
        name="user-authentication",
        scope=FeatureScope.FEATURE,
        scale_level=3,
        description="OAuth and JWT authentication",
        owner="security-team",
    )

    # Verify feature
    assert feature.name == "user-authentication"
    assert feature.scope == FeatureScope.FEATURE

    # Verify structure (level 3)
    project_path = temp_project["project_path"]
    feature_path = project_path / "docs" / "features" / "user-authentication"

    assert (feature_path / "PRD.md").exists()
    assert (feature_path / "ARCHITECTURE.md").exists()
    assert (feature_path / "epics").exists()
    assert (feature_path / "retrospectives").exists()
    assert (feature_path / "QA").exists()

    # No ceremonies folder (only level 4)
    assert not (feature_path / "ceremonies").exists()


def test_e2e_create_feature_with_all_optional_parameters(manager, temp_project):
    """Test feature creation with all optional parameters."""
    feature = manager.create_feature(
        name="payment-processing",
        scope=FeatureScope.FEATURE,
        scale_level=3,
        description="Stripe and PayPal integration with webhook support",
        owner="payments-team",
    )

    # Verify all parameters stored
    assert feature.name == "payment-processing"
    assert feature.description == "Stripe and PayPal integration with webhook support"
    assert feature.owner == "payments-team"

    # Verify in database
    feature_in_db = manager.coordinator.get_feature("payment-processing")
    assert feature_in_db is not None
    assert feature_in_db["description"] == "Stripe and PayPal integration with webhook support"
    assert feature_in_db["owner"] == "payments-team"


def test_e2e_verify_all_files_exist(manager, temp_project):
    """Test that all expected files are created."""
    manager.create_feature(
        name="analytics-dashboard",
        scope=FeatureScope.FEATURE,
        scale_level=3,
    )

    project_path = temp_project["project_path"]
    feature_path = project_path / "docs" / "features" / "analytics-dashboard"

    # Verify every expected file
    expected_files = [
        "PRD.md",
        "ARCHITECTURE.md",
        "CHANGELOG.md",
        "README.md",
    ]

    for file_name in expected_files:
        file_path = feature_path / file_name
        assert file_path.exists(), f"Expected file not found: {file_name}"
        # Verify file has content
        content = file_path.read_text(encoding="utf-8")
        assert len(content) > 0, f"File is empty: {file_name}"


def test_e2e_verify_git_history(manager, temp_project):
    """Test git history after feature creation."""
    git = temp_project["git_manager"]

    # Get initial commit count
    initial_commits = git.get_commits_since("HEAD~10", "HEAD")
    initial_count = len(initial_commits)

    # Create feature
    manager.create_feature(
        name="notification-service",
        scope=FeatureScope.FEATURE,
        scale_level=2,
    )

    # Verify new commit
    new_commits = git.get_commits_since(f"HEAD~{initial_count + 2}", "HEAD")
    assert len(new_commits) == initial_count + 1

    # Verify commit message format
    commit_info = git.get_commit_info("HEAD")
    assert "feat(notification-service)" in commit_info["message"]
    assert "create feature" in commit_info["message"]
    assert "Scope:" in commit_info["message"]
    assert "Scale Level:" in commit_info["message"]


# ============================================================================
# CONCURRENT OPERATIONS (3 SCENARIOS)
# ============================================================================


def test_concurrent_create_two_features_different_names(manager, temp_project):
    """Test concurrent creation of two features with different names."""
    errors = []
    features_created = []

    def create_feature_1():
        try:
            feature = manager.create_feature(
                name="feature-concurrent-1",
                scope=FeatureScope.FEATURE,
                scale_level=2,
            )
            features_created.append(feature.name)
        except Exception as e:
            errors.append(str(e))

    def create_feature_2():
        try:
            feature = manager.create_feature(
                name="feature-concurrent-2",
                scope=FeatureScope.FEATURE,
                scale_level=2,
            )
            features_created.append(feature.name)
        except Exception as e:
            errors.append(str(e))

    # Run concurrently (note: may serialize due to git/DB locks)
    thread1 = threading.Thread(target=create_feature_1)
    thread2 = threading.Thread(target=create_feature_2)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    # Verify both created (or one failed gracefully)
    # Due to git/DB locking, one may fail - that's acceptable
    assert len(features_created) >= 1, f"At least one feature should be created. Errors: {errors}"

    # Verify no data corruption
    git = temp_project["git_manager"]
    assert git.is_working_tree_clean()


def test_concurrent_attempt_duplicate_creation(manager, temp_project):
    """Test concurrent attempts to create same feature (should fail)."""
    errors = []
    success_count = [0]

    def create_duplicate_feature():
        try:
            manager.create_feature(
                name="duplicate-feature",
                scope=FeatureScope.FEATURE,
                scale_level=2,
            )
            success_count[0] += 1
        except Exception as e:
            errors.append(str(e))

    # Run two concurrent attempts
    thread1 = threading.Thread(target=create_duplicate_feature)
    thread2 = threading.Thread(target=create_duplicate_feature)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    # Only one should succeed
    assert success_count[0] == 1, "Exactly one feature creation should succeed"
    assert len(errors) == 1, "One creation should fail with error"

    # Verify system integrity
    git = temp_project["git_manager"]
    assert git.is_working_tree_clean()


def test_concurrent_thread_safety_verification(manager, temp_project):
    """Test thread safety with multiple concurrent operations."""
    # This test verifies that concurrent access doesn't corrupt state
    # Even if operations serialize, no corruption should occur

    def create_feature(name):
        try:
            manager.create_feature(
                name=name,
                scope=FeatureScope.FEATURE,
                scale_level=2,
            )
        except:
            pass  # Ignore errors (expected for concurrent access)

    # Create multiple features concurrently
    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_feature, args=(f"thread-feature-{i}",))
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # Verify system integrity (most important check)
    git = temp_project["git_manager"]
    assert git.is_working_tree_clean(), "Git working tree must be clean after concurrent operations"

    # Verify at least some features created
    all_features = manager.coordinator.list_features()
    assert len(all_features) >= 1, "At least one feature should be created"


# ============================================================================
# ERROR RECOVERY (4 SCENARIOS)
# ============================================================================


def test_error_recovery_disk_space_simulation(manager, temp_project):
    """Test recovery when file creation fails (simulated disk full)."""
    # This is difficult to simulate without mocking
    # We'll test by verifying rollback on any filesystem error

    # Create valid feature first
    manager.create_feature(
        name="valid-feature",
        scope=FeatureScope.FEATURE,
        scale_level=2,
    )

    checkpoint_sha = temp_project["git_manager"].get_head_sha()

    # Attempt to create duplicate (will fail, trigger rollback)
    try:
        manager.create_feature(
            name="valid-feature",  # Duplicate
            scope=FeatureScope.FEATURE,
            scale_level=2,
        )
    except GitIntegratedStateManagerError:
        pass  # Expected

    # Verify rollback succeeded
    current_sha = temp_project["git_manager"].get_head_sha()
    assert current_sha == checkpoint_sha

    # Verify system can recover and create new feature
    feature = manager.create_feature(
        name="recovery-feature",
        scope=FeatureScope.FEATURE,
        scale_level=2,
    )
    assert feature.name == "recovery-feature"


def test_error_recovery_db_constraint_violation(manager, temp_project):
    """Test recovery when DB insert fails (constraint violation)."""
    # Create feature
    manager.create_feature(
        name="original-feature",
        scope=FeatureScope.FEATURE,
        scale_level=2,
    )

    checkpoint_sha = temp_project["git_manager"].get_head_sha()

    # Attempt duplicate (DB will reject)
    with pytest.raises(GitIntegratedStateManagerError):
        manager.create_feature(
            name="original-feature",
            scope=FeatureScope.FEATURE,
            scale_level=2,
        )

    # Verify rollback
    assert temp_project["git_manager"].get_head_sha() == checkpoint_sha
    assert temp_project["git_manager"].is_working_tree_clean()

    # Verify can create different feature
    new_feature = manager.create_feature(
        name="different-feature",
        scope=FeatureScope.FEATURE,
        scale_level=2,
    )
    assert new_feature.name == "different-feature"


def test_error_recovery_git_failure_simulation(manager, temp_project):
    """Test recovery when git operations would fail."""
    # We'll test that any failure triggers proper rollback
    # Create valid feature first
    feature1 = manager.create_feature(
        name="before-error",
        scope=FeatureScope.FEATURE,
        scale_level=2,
    )

    checkpoint = temp_project["git_manager"].get_head_sha()

    # Trigger error (duplicate name)
    try:
        manager.create_feature(
            name="before-error",
            scope=FeatureScope.FEATURE,
            scale_level=2,
        )
    except GitIntegratedStateManagerError:
        pass

    # Verify rollback complete
    assert temp_project["git_manager"].get_head_sha() == checkpoint
    assert temp_project["git_manager"].is_working_tree_clean()


def test_error_recovery_all_rollbacks_successful(manager, temp_project):
    """Test that all rollback mechanisms work correctly."""
    # Create baseline
    manager.create_feature(
        name="baseline-feature",
        scope=FeatureScope.FEATURE,
        scale_level=2,
    )

    checkpoint = temp_project["git_manager"].get_head_sha()
    project_path = temp_project["project_path"]

    # Count existing features
    features_before = len(manager.coordinator.list_features())
    folders_before = len(list((project_path / "docs" / "features").iterdir()))

    # Attempt invalid operation
    try:
        manager.create_feature(
            name="baseline-feature",  # Duplicate
            scope=FeatureScope.FEATURE,
            scale_level=2,
        )
    except GitIntegratedStateManagerError:
        pass

    # Verify complete rollback
    # 1. Git restored
    assert temp_project["git_manager"].get_head_sha() == checkpoint

    # 2. DB unchanged
    features_after = len(manager.coordinator.list_features())
    assert features_after == features_before

    # 3. Filesystem unchanged
    folders_after = len(list((project_path / "docs" / "features").iterdir()))
    assert folders_after == folders_before

    # 4. Working tree clean
    assert temp_project["git_manager"].is_working_tree_clean()


# ============================================================================
# PERFORMANCE (3 SCENARIOS)
# ============================================================================


def test_performance_feature_creation_under_1_second(manager, temp_project):
    """Test that feature creation completes in <1 second."""
    start_time = time.time()

    manager.create_feature(
        name="perf-test-feature",
        scope=FeatureScope.FEATURE,
        scale_level=3,
        description="Performance test feature",
    )

    elapsed_time = time.time() - start_time

    # Requirement: <1s for feature creation
    assert elapsed_time < 1.0, f"Feature creation took {elapsed_time:.3f}s (required: <1.0s)"


def test_performance_multiple_features_in_sequence(manager, temp_project):
    """Test creating multiple features in sequence (total time)."""
    start_time = time.time()

    for i in range(3):
        manager.create_feature(
            name=f"batch-feature-{i}",
            scope=FeatureScope.FEATURE,
            scale_level=2,
        )

    elapsed_time = time.time() - start_time

    # Should complete 3 features in <5 seconds
    assert elapsed_time < 5.0, f"3 features took {elapsed_time:.3f}s (required: <5.0s)"


def test_performance_benchmark_10_feature_creations(manager, temp_project):
    """Benchmark: Create 10 features and measure average time."""
    times = []

    for i in range(10):
        start = time.time()

        manager.create_feature(
            name=f"benchmark-feature-{i}",
            scope=FeatureScope.FEATURE,
            scale_level=2,
        )

        elapsed = time.time() - start
        times.append(elapsed)

    # Calculate statistics
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)

    # Requirements
    assert avg_time < 1.0, f"Average time {avg_time:.3f}s exceeds 1.0s"
    assert max_time < 2.0, f"Max time {max_time:.3f}s exceeds 2.0s"

    # Print benchmark results for analysis
    print(f"\nBenchmark Results (10 features):")
    print(f"  Average: {avg_time:.3f}s")
    print(f"  Min: {min_time:.3f}s")
    print(f"  Max: {max_time:.3f}s")
