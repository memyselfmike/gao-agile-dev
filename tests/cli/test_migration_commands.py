"""
Unit tests for migration CLI commands.

Tests all migration commands:
1. migrate - Migrate to hybrid architecture
2. migrate --dry-run - Preview migration
3. consistency-check - Check file-DB consistency
4. consistency-repair - Repair consistency issues

Epic: 27 - Integration & Migration
Story: 27.3 - Create Migration Tools
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from click.testing import CliRunner

from gao_dev.cli.migration_commands import (
    migrate_group,
    migrate_project,
    check_consistency,
    repair_consistency
)
from gao_dev.core.services.git_migration_manager import MigrationResult
from gao_dev.core.services.git_consistency_checker import (
    ConsistencyReport,
    ConsistencyIssue
)


@pytest.fixture
def runner():
    """Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_migration_result():
    """Sample successful migration result."""
    return MigrationResult(
        success=True,
        phase_completed=4,
        epics_count=5,
        stories_count=25,
        checkpoints={
            "phase_1": "abc123",
            "phase_2": "def456",
            "phase_3": "ghi789",
            "phase_4": "jkl012"
        },
        summary="Migration completed successfully"
    )


@pytest.fixture
def sample_failed_migration_result():
    """Sample failed migration result."""
    return MigrationResult(
        success=False,
        phase_completed=2,
        epics_count=0,
        stories_count=0,
        checkpoints={
            "phase_1": "abc123",
            "phase_2": "def456"
        },
        summary="Migration failed at phase 2",
        error="Database connection failed",
        rollback_performed=True
    )


@pytest.fixture
def sample_consistency_report_clean():
    """Sample clean consistency report (no issues)."""
    from datetime import datetime
    return ConsistencyReport(
        timestamp=datetime.now(),
        has_issues=False,
        total_issues=0
    )


@pytest.fixture
def sample_consistency_report_issues():
    """Sample consistency report with issues."""
    from datetime import datetime
    return ConsistencyReport(
        timestamp=datetime.now(),
        has_issues=True,
        total_issues=10,
        uncommitted_changes=["docs/epic-1.md", "docs/story-1.1.md"],
        orphaned_records=[
            ConsistencyIssue(
                issue_type="orphaned_record",
                severity="error",
                description="Epic 2 in DB but file deleted",
                epic_num=2
            )
        ],
        unregistered_files=[
            ConsistencyIssue(
                issue_type="unregistered_file",
                severity="warning",
                description="docs/epic-3.md exists but not in DB",
                file_path=Path("docs/epic-3.md")
            )
        ],
        state_mismatches=[
            ConsistencyIssue(
                issue_type="state_mismatch",
                severity="error",
                description="Story 1.1 state mismatch",
                epic_num=1,
                story_num=1,
                db_state="in_progress",
                git_state="completed"
            )
        ]
    )


# =============================================================================
# TEST: migrate command
# =============================================================================

def test_migrate_success(runner, sample_migration_result, tmp_path):
    """Test successful migration."""
    with patch("gao_dev.cli.migration_commands.GitMigrationManager") as mock_mgr_cls:
        mock_mgr = mock_mgr_cls.return_value
        mock_mgr.migrate_to_hybrid_architecture.return_value = sample_migration_result

        result = runner.invoke(
            migrate_group,
            ["migrate", "--project", str(tmp_path), "--db-path", str(tmp_path / ".gao-dev/documents.db")],
            input="y\n"
        )

        assert result.exit_code == 0
        assert "Migration Status: SUCCESS" in result.output
        assert "Epics Migrated: 5" in result.output
        assert "Stories Migrated: 25" in result.output
        assert "Phase Completed: 4/4" in result.output


def test_migrate_failure(runner, sample_failed_migration_result, tmp_path):
    """Test failed migration with rollback."""
    with patch("gao_dev.cli.migration_commands.GitMigrationManager") as mock_mgr_cls:
        mock_mgr = mock_mgr_cls.return_value
        mock_mgr.migrate_to_hybrid_architecture.return_value = sample_failed_migration_result

        result = runner.invoke(
            migrate_group,
            ["migrate", "--project", str(tmp_path), "--db-path", str(tmp_path / ".gao-dev/documents.db")],
            input="y\n"
        )

        assert result.exit_code == 1
        assert "Migration Status: FAILED" in result.output
        assert "Phase Failed: 2" in result.output
        assert "Database connection failed" in result.output
        assert "Automatic rollback performed" in result.output


def test_migrate_dry_run(runner, tmp_path):
    """Test migration dry run (preview)."""
    # Create sample epic/story files for dry run
    epics_dir = tmp_path / "docs" / "epics"
    epics_dir.mkdir(parents=True)
    (epics_dir / "epic-1.md").write_text("# Epic 1")
    (epics_dir / "epic-2.md").write_text("# Epic 2")

    stories_dir = tmp_path / "docs" / "stories" / "epic-1"
    stories_dir.mkdir(parents=True)
    (stories_dir / "story-1.1.md").write_text("# Story 1.1")
    (stories_dir / "story-1.2.md").write_text("# Story 1.2")

    result = runner.invoke(
        migrate_group,
        ["migrate", "--project", str(tmp_path), "--dry-run"]
    )

    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    assert "Epics found: 2" in result.output
    assert "Stories found: 2" in result.output
    assert "To perform actual migration, run:" in result.output


def test_migrate_cancel(runner, tmp_path):
    """Test migration cancelled by user."""
    result = runner.invoke(
        migrate_group,
        ["migrate", "--project", str(tmp_path)],
        input="n\n"
    )

    assert result.exit_code == 0
    assert "Migration cancelled" in result.output


def test_migrate_with_options(runner, sample_migration_result, tmp_path):
    """Test migration with various options."""
    with patch("gao_dev.cli.migration_commands.GitMigrationManager") as mock_mgr_cls:
        mock_mgr = mock_mgr_cls.return_value
        mock_mgr.migrate_to_hybrid_architecture.return_value = sample_migration_result

        result = runner.invoke(
            migrate_group,
            ["migrate", "--project", str(tmp_path), "--no-branch", "--auto-merge"],
            input="y\n"
        )

        assert result.exit_code == 0
        mock_mgr.migrate_to_hybrid_architecture.assert_called_once_with(
            create_branch=False,
            auto_merge=True
        )


# =============================================================================
# TEST: consistency-check command
# =============================================================================

def test_consistency_check_clean(runner, sample_consistency_report_clean, tmp_path):
    """Test consistency check with no issues."""
    db_path = tmp_path / ".gao-dev" / "documents.db"
    db_path.parent.mkdir(parents=True)
    db_path.touch()

    with patch("gao_dev.cli.migration_commands.GitAwareConsistencyChecker") as mock_checker_cls:
        mock_checker = mock_checker_cls.return_value
        mock_checker.check_consistency.return_value = sample_consistency_report_clean

        result = runner.invoke(
            migrate_group,
            ["consistency-check", "--project", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "No consistency issues found" in result.output


def test_consistency_check_with_issues(runner, sample_consistency_report_issues, tmp_path):
    """Test consistency check with issues."""
    db_path = tmp_path / ".gao-dev" / "documents.db"
    db_path.parent.mkdir(parents=True)
    db_path.touch()

    with patch("gao_dev.cli.migration_commands.GitAwareConsistencyChecker") as mock_checker_cls:
        mock_checker = mock_checker_cls.return_value
        mock_checker.check_consistency.return_value = sample_consistency_report_issues

        result = runner.invoke(
            migrate_group,
            ["consistency-check", "--project", str(tmp_path), "--verbose"]
        )

        assert result.exit_code == 1
        assert "Found 5 consistency issues" in result.output  # 2+1+1+1 = 5 total
        assert "Uncommitted Changes: 2" in result.output
        assert "Orphaned DB Records: 1" in result.output
        assert "Unregistered Files: 1" in result.output
        assert "State Mismatches: 1" in result.output


def test_consistency_check_no_database(runner, tmp_path):
    """Test consistency check when database doesn't exist."""
    result = runner.invoke(
        migrate_group,
        ["consistency-check", "--project", str(tmp_path)]
    )

    assert result.exit_code == 0
    assert "Database does not exist" in result.output
    assert "Project may not be migrated" in result.output


# =============================================================================
# TEST: consistency-repair command
# =============================================================================

def test_consistency_repair_success(runner, sample_consistency_report_issues, tmp_path):
    """Test successful consistency repair."""
    db_path = tmp_path / ".gao-dev" / "documents.db"
    db_path.parent.mkdir(parents=True)
    db_path.touch()

    with patch("gao_dev.cli.migration_commands.GitAwareConsistencyChecker") as mock_checker_cls:
        mock_checker = mock_checker_cls.return_value
        mock_checker.check_consistency.return_value = sample_consistency_report_issues
        mock_checker.repair.return_value = None

        result = runner.invoke(
            migrate_group,
            ["consistency-repair", "--project", str(tmp_path)],
            input="y\n"
        )

        assert result.exit_code == 0
        assert "Consistency issues repaired successfully" in result.output
        assert "Git commit created" in result.output
        mock_checker.repair.assert_called_once()


def test_consistency_repair_no_issues(runner, sample_consistency_report_clean, tmp_path):
    """Test consistency repair when no issues exist."""
    db_path = tmp_path / ".gao-dev" / "documents.db"
    db_path.parent.mkdir(parents=True)
    db_path.touch()

    with patch("gao_dev.cli.migration_commands.GitAwareConsistencyChecker") as mock_checker_cls:
        mock_checker = mock_checker_cls.return_value
        mock_checker.check_consistency.return_value = sample_consistency_report_clean

        result = runner.invoke(
            migrate_group,
            ["consistency-repair", "--project", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "No consistency issues found" in result.output
        assert "Nothing to repair" in result.output


def test_consistency_repair_dry_run(runner, sample_consistency_report_issues, tmp_path):
    """Test consistency repair dry run."""
    db_path = tmp_path / ".gao-dev" / "documents.db"
    db_path.parent.mkdir(parents=True)
    db_path.touch()

    with patch("gao_dev.cli.migration_commands.GitAwareConsistencyChecker") as mock_checker_cls:
        mock_checker = mock_checker_cls.return_value
        mock_checker.check_consistency.return_value = sample_consistency_report_issues

        result = runner.invoke(
            migrate_group,
            ["consistency-repair", "--project", str(tmp_path), "--dry-run"]
        )

        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "Would repair the above issues" in result.output
        mock_checker.repair.assert_not_called()


def test_consistency_repair_cancel(runner, sample_consistency_report_issues, tmp_path):
    """Test consistency repair cancelled by user."""
    db_path = tmp_path / ".gao-dev" / "documents.db"
    db_path.parent.mkdir(parents=True)
    db_path.touch()

    with patch("gao_dev.cli.migration_commands.GitAwareConsistencyChecker") as mock_checker_cls:
        mock_checker = mock_checker_cls.return_value
        mock_checker.check_consistency.return_value = sample_consistency_report_issues

        result = runner.invoke(
            migrate_group,
            ["consistency-repair", "--project", str(tmp_path)],
            input="n\n"
        )

        assert result.exit_code == 0
        assert "Repair cancelled" in result.output


def test_consistency_repair_no_database(runner, tmp_path):
    """Test consistency repair when database doesn't exist."""
    result = runner.invoke(
        migrate_group,
        ["consistency-repair", "--project", str(tmp_path)]
    )

    assert result.exit_code == 1
    assert "Database does not exist" in result.output
    assert "Nothing to repair" in result.output
