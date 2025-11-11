"""
Tests for GitAwareConsistencyChecker.

Epic: 25 - Git-Integrated State Manager
Story: 25.6 - Implement GitAwareConsistencyChecker
"""

import sqlite3
import tempfile
from pathlib import Path
import importlib.util
import sys

import pytest

from gao_dev.core.state.migrations.migration_001_create_state_schema import Migration001
from gao_dev.core.services.git_consistency_checker import (
    GitAwareConsistencyChecker,
    ConsistencyReport,
    ConsistencyIssue,
)
from gao_dev.core.git_manager import GitManager
from gao_dev.core.state_coordinator import StateCoordinator

# Load migration 005 dynamically
def load_migration_005():
    """Load migration 005 module dynamically."""
    migration_path = (
        Path(__file__).parent.parent.parent.parent
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


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project with git repo, database, and sample data."""
    project_path = tmp_path / "project"
    project_path.mkdir()

    # Initialize git repo
    git = GitManager(project_path=project_path)
    git.init_repo(initial_commit=True)

    # Create .gao-dev directory
    gao_dev_dir = project_path / ".gao-dev"
    gao_dev_dir.mkdir()
    db_path = gao_dev_dir / "documents.db"

    # Create tables (need both migrations for StateCoordinator)
    Migration001.upgrade(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        Migration005.up(conn)

    # Create docs directory
    docs_dir = project_path / "docs"
    docs_dir.mkdir()
    epics_dir = docs_dir / "epics"
    epics_dir.mkdir()
    stories_dir = docs_dir / "stories"
    stories_dir.mkdir()

    # Create epic file
    epic1_file = epics_dir / "epic-1.md"
    epic1_file.write_text("""# Epic 1: User Auth
**Status**: in_progress
**Total Stories**: 2
""", encoding="utf-8")

    # Create story files
    story1_file = stories_dir / "story-1.1.md"
    story1_file.write_text("""# Story 1.1: Login
**Owner**: Amelia
**Priority**: P0
""", encoding="utf-8")

    story2_file = stories_dir / "story-1.2.md"
    story2_file.write_text("""# Story 1.2: Register
**Owner**: Amelia
**Priority**: P1
""", encoding="utf-8")

    # Commit files
    git.add_all()
    git.commit("feat: add epic and story files")

    # Create coordinator and add records
    coordinator = StateCoordinator(db_path=db_path)

    coordinator.create_epic(
        epic_num=1,
        title="User Auth",
        status="in_progress",
        total_stories=2,
        metadata={"file_path": str(epic1_file)}
    )

    coordinator.create_story(
        epic_num=1,
        story_num=1,
        title="Login",
        status="pending",
        metadata={"file_path": str(story1_file)}
    )

    coordinator.create_story(
        epic_num=1,
        story_num=2,
        title="Register",
        status="pending",
        metadata={"file_path": str(story2_file)}
    )

    coordinator.close()

    return {
        "project_path": project_path,
        "db_path": db_path,
        "git": git,
        "epic1_file": epic1_file,
        "story1_file": story1_file,
        "story2_file": story2_file,
    }


# ============================================================================
# CHECK CONSISTENCY TESTS
# ============================================================================


def test_check_consistency_clean_state(temp_project):
    """Test consistency check with clean state (no issues)."""
    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()

    assert report.has_issues is False
    assert report.total_issues == 0
    assert len(report.uncommitted_changes) == 0
    assert len(report.orphaned_records) == 0
    assert len(report.unregistered_files) == 0
    assert len(report.state_mismatches) == 0


def test_check_uncommitted_changes(temp_project):
    """Test detecting uncommitted changes."""
    # Create uncommitted file
    test_file = temp_project["project_path"] / "test.txt"
    test_file.write_text("test", encoding="utf-8")

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()

    assert report.has_issues is True
    assert len(report.uncommitted_changes) == 1
    assert "test.txt" in report.uncommitted_changes[0]


def test_check_orphaned_epic_record(temp_project):
    """Test detecting orphaned epic record (file deleted)."""
    # Delete epic file
    temp_project["epic1_file"].unlink()

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()

    assert report.has_issues is True
    assert len(report.orphaned_records) == 1
    assert report.orphaned_records[0].epic_num == 1
    assert report.orphaned_records[0].issue_type == "orphaned_record"
    assert report.orphaned_records[0].severity == "error"


def test_check_orphaned_story_record(temp_project):
    """Test detecting orphaned story record (file deleted)."""
    # Delete story file
    temp_project["story1_file"].unlink()

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()

    assert report.has_issues is True
    assert len(report.orphaned_records) == 1
    assert report.orphaned_records[0].epic_num == 1
    assert report.orphaned_records[0].story_num == 1
    assert report.orphaned_records[0].issue_type == "orphaned_record"


def test_check_unregistered_epic_file(temp_project):
    """Test detecting unregistered epic file (file exists but not in DB)."""
    # Create new epic file not in database
    epics_dir = temp_project["project_path"] / "docs" / "epics"
    epic2_file = epics_dir / "epic-2.md"
    epic2_file.write_text("""# Epic 2: Dashboard
**Status**: planning
""", encoding="utf-8")

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()

    assert report.has_issues is True
    assert len(report.unregistered_files) == 1
    assert report.unregistered_files[0].epic_num == 2
    assert report.unregistered_files[0].issue_type == "unregistered_file"
    assert report.unregistered_files[0].severity == "warning"


def test_check_unregistered_story_file(temp_project):
    """Test detecting unregistered story file (file exists but not in DB)."""
    # Create new story file not in database
    stories_dir = temp_project["project_path"] / "docs" / "stories"
    story3_file = stories_dir / "story-1.3.md"
    story3_file.write_text("""# Story 1.3: JWT
**Owner**: Amelia
""", encoding="utf-8")

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()

    assert report.has_issues is True
    assert len(report.unregistered_files) == 1
    assert report.unregistered_files[0].epic_num == 1
    assert report.unregistered_files[0].story_num == 3
    assert report.unregistered_files[0].issue_type == "unregistered_file"


def test_check_state_mismatch(temp_project):
    """Test detecting state mismatch (DB state != git-inferred state)."""
    # Update story file and commit with "complete" message
    temp_project["story1_file"].write_text("""# Story 1.1: Login (Done)
**Owner**: Amelia
**Status**: Completed
""", encoding="utf-8")

    temp_project["git"].add_all()
    temp_project["git"].commit("feat(story-1.1): complete login implementation")

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()

    # Should detect mismatch (DB: pending, Git: completed)
    assert report.has_issues is True
    assert len(report.state_mismatches) == 1
    assert report.state_mismatches[0].epic_num == 1
    assert report.state_mismatches[0].story_num == 1
    assert report.state_mismatches[0].db_state == "pending"
    assert report.state_mismatches[0].git_state == "completed"


# ============================================================================
# REPAIR TESTS
# ============================================================================


def test_repair_orphaned_epic_record(temp_project):
    """Test repairing orphaned epic record by removing from DB."""
    # Delete epic file
    temp_project["epic1_file"].unlink()

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()
    assert len(report.orphaned_records) == 1

    # Repair
    checker.repair(report, create_commit=False)

    # Verify epic removed from database
    coordinator = StateCoordinator(db_path=temp_project["db_path"])
    with pytest.raises(Exception):
        coordinator.epic_service.get(1)
    coordinator.close()


def test_repair_orphaned_story_record(temp_project):
    """Test repairing orphaned story record by removing from DB."""
    # Delete story file
    temp_project["story1_file"].unlink()

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()
    assert len(report.orphaned_records) == 1

    # Repair
    checker.repair(report, create_commit=False)

    # Verify story removed from database
    coordinator = StateCoordinator(db_path=temp_project["db_path"])
    with pytest.raises(Exception):
        coordinator.story_service.get(1, 1)
    coordinator.close()


def test_repair_unregistered_epic_file(temp_project):
    """Test repairing unregistered epic file by adding to DB."""
    # Create new epic file
    epics_dir = temp_project["project_path"] / "docs" / "epics"
    epic2_file = epics_dir / "epic-2.md"
    epic2_file.write_text("""# Epic 2: Dashboard
**Status**: planning
""", encoding="utf-8")

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()
    assert len(report.unregistered_files) == 1

    # Repair
    checker.repair(report, create_commit=False)

    # Verify epic added to database
    coordinator = StateCoordinator(db_path=temp_project["db_path"])
    epic = coordinator.epic_service.get(2)
    assert epic is not None
    assert epic["title"] == "Dashboard"
    coordinator.close()


def test_repair_unregistered_story_file(temp_project):
    """Test repairing unregistered story file by adding to DB."""
    # Create new story file
    stories_dir = temp_project["project_path"] / "docs" / "stories"
    story3_file = stories_dir / "story-1.3.md"
    story3_file.write_text("""# Story 1.3: JWT
**Owner**: Amelia
""", encoding="utf-8")

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()
    assert len(report.unregistered_files) == 1

    # Repair
    checker.repair(report, create_commit=False)

    # Verify story added to database
    coordinator = StateCoordinator(db_path=temp_project["db_path"])
    story = coordinator.story_service.get(1, 3)
    assert story is not None
    assert story["title"] == "JWT"
    coordinator.close()


def test_repair_state_mismatch(temp_project):
    """Test repairing state mismatch by updating DB."""
    # Update story file and commit
    temp_project["story1_file"].write_text("""# Story 1.1: Login (Done)
**Status**: Completed
""", encoding="utf-8")

    temp_project["git"].add_all()
    temp_project["git"].commit("feat(story-1.1): complete login")

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()
    assert len(report.state_mismatches) == 1

    # Repair
    checker.repair(report, create_commit=False)

    # Verify story state updated in database
    coordinator = StateCoordinator(db_path=temp_project["db_path"])
    story = coordinator.story_service.get(1, 1)
    assert story["status"] == "completed"
    coordinator.close()


def test_repair_creates_commit(temp_project):
    """Test repair creates git commit."""
    # Create issue
    temp_project["story1_file"].unlink()

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()
    assert report.has_issues is True

    # Get current HEAD
    head_before = temp_project["git"].get_head_sha()

    # Repair with commit
    checker.repair(report, create_commit=True)

    # Verify commit created
    head_after = temp_project["git"].get_head_sha()
    assert head_before != head_after

    # Check commit message
    commits = temp_project["git"].get_commits_since(head_before, head_after)
    assert len(commits) == 1
    assert "consistency" in commits[0]["message"].lower()


def test_repair_no_issues(temp_project):
    """Test repair with no issues does nothing."""
    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    report = checker.check_consistency()
    assert report.has_issues is False

    # Repair should do nothing
    checker.repair(report)


# ============================================================================
# HELPER METHOD TESTS
# ============================================================================


def test_infer_state_completed(temp_project):
    """Test inferring 'completed' state from git."""
    # Create file with "complete" commit
    test_file = temp_project["project_path"] / "test.md"
    test_file.write_text("test", encoding="utf-8")

    temp_project["git"].add_all()
    temp_project["git"].commit("feat: complete test feature")

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    state = checker._infer_state_from_git(test_file)
    assert state == "completed"


def test_infer_state_in_progress(temp_project):
    """Test inferring 'in_progress' state from git."""
    # Create file with "wip" commit
    test_file = temp_project["project_path"] / "test.md"
    test_file.write_text("test", encoding="utf-8")

    temp_project["git"].add_all()
    temp_project["git"].commit("chore: wip test feature")

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    state = checker._infer_state_from_git(test_file)
    assert state == "in_progress"


def test_infer_state_pending(temp_project):
    """Test inferring 'pending' state from git."""
    # Create file with neutral commit
    test_file = temp_project["project_path"] / "test.md"
    test_file.write_text("test", encoding="utf-8")

    temp_project["git"].add_all()
    temp_project["git"].commit("docs: add test file")

    checker = GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    )

    state = checker._infer_state_from_git(test_file)
    assert state == "pending"


# ============================================================================
# CONTEXT MANAGER TESTS
# ============================================================================


def test_context_manager(temp_project):
    """Test GitAwareConsistencyChecker as context manager."""
    with GitAwareConsistencyChecker(
        db_path=temp_project["db_path"],
        project_path=temp_project["project_path"]
    ) as checker:
        report = checker.check_consistency()
        assert report is not None

    # Connections should be closed after context exit
