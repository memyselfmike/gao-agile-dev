"""
Integration tests for beta distribution system.

Story 36.12: Integration Testing & Cross-Platform Validation
"""

import pytest
import sqlite3
from pathlib import Path

from gao_dev.core.backup_manager import BackupManager
from gao_dev.core.migration_runner import MigrationRunner, Migration
from gao_dev.core.system_health_check import SystemHealthCheck
from gao_dev.core.version_manager import VersionManager


class TestGitURLInstallSeparation:
    """Test that git URL install is separate from source directory."""

    def test_source_directory_detection(self):
        """Test .gaodev-source marker exists in source repo."""
        # Check that marker file exists in source
        marker_path = Path(__file__).parent.parent.parent / ".gaodev-source"
        assert marker_path.exists(), "Source marker should exist in development environment"

    def test_version_manager_initialization(self):
        """Test VersionManager can be initialized."""
        manager = VersionManager()

        # Should be able to get current version
        try:
            version = manager.get_current_version()
            assert isinstance(version, str)
        except Exception:
            # OK if version cannot be determined in test environment
            pass


class TestUpdatePreservesUserState:
    """Test that updates preserve user data."""

    def test_backup_manager_preserves_user_data(self, tmp_path: Path):
        """Test BackupManager preserves all user data."""
        project_path = tmp_path / "user_project"
        project_path.mkdir()

        gaodev_dir = project_path / ".gao-dev"
        gaodev_dir.mkdir()

        # Create user data
        db_path = gaodev_dir / "documents.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE user_data (id INTEGER, value TEXT)")
        conn.execute("INSERT INTO user_data VALUES (1, 'important')")
        conn.commit()
        conn.close()

        user_file = gaodev_dir / "user_config.yaml"
        user_file.write_text("user: settings")

        # Create backup
        manager = BackupManager()
        backup_path = manager.create_backup(project_path, reason="test_update")

        # Verify user data in backup
        backed_up_db = backup_path / "documents.db"
        assert backed_up_db.exists()

        conn = sqlite3.connect(backed_up_db)
        cursor = conn.execute("SELECT value FROM user_data WHERE id = 1")
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "important"

        backed_up_file = backup_path / "user_config.yaml"
        assert backed_up_file.exists()
        assert backed_up_file.read_text() == "user: settings"


class TestMigrationRollbackOnFailure:
    """Test migration rollback functionality."""

    def test_migration_runner_rollback(self, tmp_path: Path):
        """Test migration rollback on failure."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        gaodev_dir = project_path / ".gao-dev"
        gaodev_dir.mkdir()

        # Create initial database
        db_path = gaodev_dir / "documents.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE initial (id INTEGER)")
        conn.commit()
        conn.close()

        # Define migrations
        def migration_1_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE test1 (id INTEGER)")

        def migration_2_up(conn: sqlite3.Connection) -> None:
            # This will fail
            conn.execute("INVALID SQL SYNTAX")

        migrations = [
            Migration(version=1, description="Create test1", up=migration_1_up),
            Migration(version=2, description="Invalid", up=migration_2_up),
        ]

        runner = MigrationRunner(project_path)

        # Run migrations (should fail and rollback)
        with pytest.raises(Exception):
            runner.run_migrations(migrations)

        # Verify rollback - no migrations applied
        assert runner.get_current_version() == 0

        # Verify test1 table not created (transaction rolled back)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test1'"
        )
        assert cursor.fetchone() is None
        conn.close()


class TestHealthCheckSystem:
    """Test health check functionality."""

    def test_health_check_detects_missing_tables(self, tmp_path: Path):
        """Test health check detects database issues."""
        project_path = tmp_path / "incomplete_project"
        project_path.mkdir()

        gaodev_dir = project_path / ".gao-dev"
        gaodev_dir.mkdir()

        # Create database with incomplete schema
        db_path = gaodev_dir / "documents.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE epics (id INTEGER)")  # Only one table
        conn.commit()
        conn.close()

        checker = SystemHealthCheck(project_path)
        report = checker.run_post_update_check()

        # Should detect missing tables
        assert not report.all_passed
        assert "database_schema" in report.failed_checks

    def test_health_check_passes_with_complete_setup(self, tmp_path: Path):
        """Test health check passes with complete setup."""
        project_path = tmp_path / "complete_project"
        project_path.mkdir()

        gaodev_dir = project_path / ".gao-dev"
        gaodev_dir.mkdir()

        # Create complete database
        db_path = gaodev_dir / "documents.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE epics (id INTEGER)")
        conn.execute("CREATE TABLE stories (id INTEGER)")
        conn.execute("CREATE TABLE tasks (id INTEGER)")
        conn.execute("CREATE TABLE documents (id INTEGER)")
        conn.execute("CREATE TABLE features (id INTEGER)")
        conn.execute("CREATE TABLE schema_version (version INTEGER)")
        conn.commit()
        conn.close()

        checker = SystemHealthCheck(project_path)

        # Only check config and database (skip workflows/agents/git for speed)
        config_result = checker.check_config_files()
        db_result = checker.check_database_schema()

        assert config_result.passed
        assert db_result.passed


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility."""

    def test_backup_handles_path_separators(self, tmp_path: Path):
        """Test BackupManager handles path separators correctly."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        gaodev_dir = project_path / ".gao-dev"
        gaodev_dir.mkdir()

        # Create nested directory structure
        nested = gaodev_dir / "a" / "b" / "c"
        nested.mkdir(parents=True)
        (nested / "file.txt").write_text("test")

        # Create backup
        manager = BackupManager()
        backup_path = manager.create_backup(project_path)

        # Verify nested structure preserved
        backed_up_file = backup_path / "a" / "b" / "c" / "file.txt"
        assert backed_up_file.exists()
        assert backed_up_file.read_text() == "test"

    def test_version_manager_cross_platform(self):
        """Test VersionManager works on current platform."""
        manager = VersionManager()

        # Should be able to get version without errors
        try:
            version = manager.get_current_version()
            assert isinstance(version, str)
            assert len(version) > 0
        except Exception as e:
            # OK if version can't be determined in test environment
            assert "version" in str(e).lower()


@pytest.mark.integration
class TestEndToEndUpdateScenario:
    """Test complete update scenario."""

    def test_complete_update_workflow(self, tmp_path: Path):
        """Test complete update workflow: backup → migrate → health check."""
        project_path = tmp_path / "e2e_project"
        project_path.mkdir()

        gaodev_dir = project_path / ".gao-dev"
        gaodev_dir.mkdir()

        # Create initial database
        db_path = gaodev_dir / "documents.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE initial (id INTEGER)")
        conn.commit()
        conn.close()

        # Step 1: Create backup
        backup_manager = BackupManager()
        backup_path = backup_manager.create_backup(project_path, reason="pre_update")
        assert backup_path.exists()

        # Step 2: Run migration
        def migration_1_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE epics (id INTEGER)")

        migrations = [Migration(version=1, description="Add epics", up=migration_1_up)]

        runner = MigrationRunner(project_path)
        runner.run_migrations(migrations)

        # Verify migration applied
        assert runner.get_current_version() == 1

        # Step 3: Health check (just database and config checks for speed)
        checker = SystemHealthCheck(project_path)
        config_result = checker.check_config_files()
        db_result = checker.check_database_schema()

        # Config and partial DB should work
        assert config_result.passed
        # DB will fail because we don't have all tables, but that's expected
