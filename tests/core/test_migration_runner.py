"""
Tests for MigrationRunner.

Story 36.9: Migration Transaction Safety
"""

import pytest
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

from gao_dev.core.migration_runner import MigrationRunner, Migration


class TestMigration:
    """Test Migration dataclass."""

    def test_migration_creation(self):
        """Test creating a Migration."""

        def up_func(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE test (id INTEGER)")

        migration = Migration(version=1, description="Create test table", up=up_func)

        assert migration.version == 1
        assert migration.description == "Create test table"
        assert migration.up == up_func
        assert migration.down is None

    def test_migration_with_down(self):
        """Test creating a Migration with down function."""

        def up_func(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE test (id INTEGER)")

        def down_func(conn: sqlite3.Connection) -> None:
            conn.execute("DROP TABLE test")

        migration = Migration(
            version=1, description="Create test table", up=up_func, down=down_func
        )

        assert migration.down == down_func


class TestMigrationRunner:
    """Test MigrationRunner."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create temporary project with database."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        gaodev_dir = project_path / ".gao-dev"
        gaodev_dir.mkdir()

        # Create database
        db_path = gaodev_dir / "documents.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE dummy (id INTEGER)")
        conn.commit()
        conn.close()

        return project_path

    @pytest.fixture
    def runner(self, temp_project: Path) -> MigrationRunner:
        """Create MigrationRunner instance."""
        return MigrationRunner(temp_project)

    def test_initialization(self, temp_project: Path):
        """Test MigrationRunner initializes correctly."""
        runner = MigrationRunner(temp_project)

        assert runner.project_path == temp_project
        assert runner.gaodev_dir == temp_project / ".gao-dev"
        assert runner.db_path == temp_project / ".gao-dev" / "documents.db"
        assert runner.backup_manager is not None

    def test_initialize_schema_version_table(self, runner: MigrationRunner):
        """Test creating schema_version table."""
        runner.initialize_schema_version_table()

        # Verify table exists
        conn = sqlite3.connect(runner.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        assert cursor.fetchone() is not None

        # Verify schema
        cursor = conn.execute("PRAGMA table_info(schema_version)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "version" in columns
        assert "description" in columns
        assert "applied_at" in columns

        conn.close()

    def test_initialize_schema_version_table_missing_db(self, tmp_path: Path):
        """Test initialize raises FileNotFoundError when database missing."""
        project_path = tmp_path / "no_db_project"
        project_path.mkdir()
        (project_path / ".gao-dev").mkdir()

        runner = MigrationRunner(project_path)

        with pytest.raises(FileNotFoundError):
            runner.initialize_schema_version_table()

    def test_get_current_version_no_migrations(self, runner: MigrationRunner):
        """Test get_current_version returns 0 when no migrations applied."""
        version = runner.get_current_version()

        assert version == 0

    def test_get_current_version_with_migrations(self, runner: MigrationRunner):
        """Test get_current_version returns max version."""
        runner.initialize_schema_version_table()

        # Insert some migrations
        conn = sqlite3.connect(runner.db_path)
        conn.execute(
            "INSERT INTO schema_version (version, description, applied_at) "
            "VALUES (1, 'Migration 1', datetime('now'))"
        )
        conn.execute(
            "INSERT INTO schema_version (version, description, applied_at) "
            "VALUES (2, 'Migration 2', datetime('now'))"
        )
        conn.execute(
            "INSERT INTO schema_version (version, description, applied_at) "
            "VALUES (5, 'Migration 5', datetime('now'))"
        )
        conn.commit()
        conn.close()

        version = runner.get_current_version()

        assert version == 5

    def test_get_applied_migrations_none(self, runner: MigrationRunner):
        """Test get_applied_migrations returns empty list when none applied."""
        applied = runner.get_applied_migrations()

        assert applied == []

    def test_get_applied_migrations_some(self, runner: MigrationRunner):
        """Test get_applied_migrations returns sorted list."""
        runner.initialize_schema_version_table()

        conn = sqlite3.connect(runner.db_path)
        conn.execute(
            "INSERT INTO schema_version (version, description, applied_at) "
            "VALUES (3, 'Migration 3', datetime('now'))"
        )
        conn.execute(
            "INSERT INTO schema_version (version, description, applied_at) "
            "VALUES (1, 'Migration 1', datetime('now'))"
        )
        conn.execute(
            "INSERT INTO schema_version (version, description, applied_at) "
            "VALUES (2, 'Migration 2', datetime('now'))"
        )
        conn.commit()
        conn.close()

        applied = runner.get_applied_migrations()

        assert applied == [1, 2, 3]  # Sorted

    def test_run_migrations_success(self, runner: MigrationRunner):
        """Test running migrations successfully."""

        def migration_1_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")

        def migration_2_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE posts (id INTEGER, title TEXT)")

        migrations = [
            Migration(version=1, description="Create users table", up=migration_1_up),
            Migration(version=2, description="Create posts table", up=migration_2_up),
        ]

        runner.run_migrations(migrations)

        # Verify migrations applied
        assert runner.get_current_version() == 2
        assert runner.get_applied_migrations() == [1, 2]

        # Verify tables created
        conn = sqlite3.connect(runner.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "users" in tables
        assert "posts" in tables

    def test_run_migrations_only_pending(self, runner: MigrationRunner):
        """Test run_migrations only applies pending migrations."""
        # Apply migration 1 manually
        runner.initialize_schema_version_table()
        conn = sqlite3.connect(runner.db_path)
        conn.execute("CREATE TABLE users (id INTEGER)")
        conn.execute(
            "INSERT INTO schema_version (version, description, applied_at) "
            "VALUES (1, 'Create users', datetime('now'))"
        )
        conn.commit()
        conn.close()

        # Define migrations 1 and 2
        def migration_1_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE users (id INTEGER)")

        def migration_2_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE posts (id INTEGER)")

        migrations = [
            Migration(version=1, description="Create users", up=migration_1_up),
            Migration(version=2, description="Create posts", up=migration_2_up),
        ]

        runner.run_migrations(migrations)

        # Should only apply migration 2
        assert runner.get_current_version() == 2
        assert runner.get_applied_migrations() == [1, 2]

    def test_run_migrations_creates_backup(self, runner: MigrationRunner):
        """Test run_migrations creates backup before applying."""

        def migration_1_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE test (id INTEGER)")

        migrations = [Migration(version=1, description="Test", up=migration_1_up)]

        runner.run_migrations(migrations)

        # Verify backup created
        backup_root = runner.project_path / ".gao-dev-backups"
        assert backup_root.exists()

        backups = list(backup_root.iterdir())
        assert len(backups) >= 1

        # Verify backup reason
        latest_backup = runner.backup_manager.get_latest_backup(runner.project_path)
        assert latest_backup is not None
        assert latest_backup.reason == "pre_migration"

    def test_run_migrations_rollback_on_failure(self, runner: MigrationRunner):
        """Test run_migrations rolls back on failure."""

        def migration_1_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE test1 (id INTEGER)")

        def migration_2_up(conn: sqlite3.Connection) -> None:
            # This will fail (invalid SQL)
            conn.execute("INVALID SQL SYNTAX")

        migrations = [
            Migration(version=1, description="Create test1", up=migration_1_up),
            Migration(version=2, description="Invalid", up=migration_2_up),
        ]

        with pytest.raises(Exception) as exc_info:
            runner.run_migrations(migrations)

        assert "Migration failed and was rolled back" in str(exc_info.value)

        # Verify no migrations applied (transaction rolled back)
        assert runner.get_current_version() == 0

        # Verify test1 table not created (transaction rolled back)
        conn = sqlite3.connect(runner.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test1'"
        )
        assert cursor.fetchone() is None
        conn.close()

    def test_run_migrations_restores_backup_on_failure(
        self, runner: MigrationRunner, temp_project: Path
    ):
        """Test run_migrations restores backup on failure."""
        # Add a marker file to .gao-dev
        marker_file = runner.gaodev_dir / "marker.txt"
        marker_file.write_text("ORIGINAL")

        def migration_1_up(conn: sqlite3.Connection) -> None:
            # Modify marker file during migration
            marker_file.write_text("MODIFIED")
            # Then fail
            conn.execute("INVALID SQL")

        migrations = [Migration(version=1, description="Fail", up=migration_1_up)]

        with pytest.raises(Exception):
            runner.run_migrations(migrations)

        # Verify marker file restored to original
        assert marker_file.read_text() == "ORIGINAL"

    def test_run_migrations_no_pending(self, runner: MigrationRunner):
        """Test run_migrations does nothing when no pending migrations."""
        # Mark migration 1 as applied
        runner.initialize_schema_version_table()
        conn = sqlite3.connect(runner.db_path)
        conn.execute(
            "INSERT INTO schema_version (version, description, applied_at) "
            "VALUES (1, 'Migration 1', datetime('now'))"
        )
        conn.commit()
        conn.close()

        def migration_1_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE test (id INTEGER)")

        migrations = [Migration(version=1, description="Migration 1", up=migration_1_up)]

        # Should do nothing
        runner.run_migrations(migrations)

        # Verify still at version 1
        assert runner.get_current_version() == 1

    def test_run_migrations_sorted_by_version(self, runner: MigrationRunner):
        """Test run_migrations applies in version order even if unsorted."""

        order_tracker = []

        def migration_1_up(conn: sqlite3.Connection) -> None:
            order_tracker.append(1)
            conn.execute("CREATE TABLE test1 (id INTEGER)")

        def migration_2_up(conn: sqlite3.Connection) -> None:
            order_tracker.append(2)
            conn.execute("CREATE TABLE test2 (id INTEGER)")

        def migration_3_up(conn: sqlite3.Connection) -> None:
            order_tracker.append(3)
            conn.execute("CREATE TABLE test3 (id INTEGER)")

        # Provide migrations in wrong order
        migrations = [
            Migration(version=3, description="Create test3", up=migration_3_up),
            Migration(version=1, description="Create test1", up=migration_1_up),
            Migration(version=2, description="Create test2", up=migration_2_up),
        ]

        runner.run_migrations(migrations)

        # Should apply in correct order
        assert order_tracker == [1, 2, 3]

    def test_rollback_migration_success(self, runner: MigrationRunner):
        """Test rolling back migrations successfully."""

        def migration_1_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE test1 (id INTEGER)")

        def migration_1_down(conn: sqlite3.Connection) -> None:
            conn.execute("DROP TABLE test1")

        def migration_2_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE test2 (id INTEGER)")

        def migration_2_down(conn: sqlite3.Connection) -> None:
            conn.execute("DROP TABLE test2")

        migrations = [
            Migration(version=1, description="Test1", up=migration_1_up, down=migration_1_down),
            Migration(version=2, description="Test2", up=migration_2_up, down=migration_2_down),
        ]

        # Apply both migrations
        runner.run_migrations(migrations)
        assert runner.get_current_version() == 2

        # Rollback to version 1
        runner.rollback_migration(target_version=1, migrations=migrations)

        # Verify version
        assert runner.get_current_version() == 1
        assert runner.get_applied_migrations() == [1]

        # Verify test2 table dropped
        conn = sqlite3.connect(runner.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test2'"
        )
        assert cursor.fetchone() is None
        conn.close()

    def test_rollback_migration_multiple(self, runner: MigrationRunner):
        """Test rolling back multiple migrations."""

        def create_migration(version: int):
            def up(conn: sqlite3.Connection) -> None:
                conn.execute(f"CREATE TABLE test{version} (id INTEGER)")

            def down(conn: sqlite3.Connection) -> None:
                conn.execute(f"DROP TABLE test{version}")

            return Migration(version=version, description=f"Test{version}", up=up, down=down)

        migrations = [create_migration(i) for i in range(1, 6)]

        # Apply all 5 migrations
        runner.run_migrations(migrations)
        assert runner.get_current_version() == 5

        # Rollback to version 2
        runner.rollback_migration(target_version=2, migrations=migrations)

        assert runner.get_current_version() == 2
        assert runner.get_applied_migrations() == [1, 2]

    def test_rollback_migration_no_down_function(self, runner: MigrationRunner):
        """Test rollback raises error when down() not defined."""

        def migration_1_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE test1 (id INTEGER)")

        migrations = [
            Migration(version=1, description="Test1", up=migration_1_up)  # No down function
        ]

        # Apply migration
        runner.run_migrations(migrations)

        # Try to rollback
        with pytest.raises(ValueError) as exc_info:
            runner.rollback_migration(target_version=0, migrations=migrations)

        assert "has no down() function defined" in str(exc_info.value)

    def test_rollback_migration_creates_backup(self, runner: MigrationRunner):
        """Test rollback creates backup before rolling back."""

        def migration_1_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE test1 (id INTEGER)")

        def migration_1_down(conn: sqlite3.Connection) -> None:
            conn.execute("DROP TABLE test1")

        migrations = [
            Migration(version=1, description="Test1", up=migration_1_up, down=migration_1_down)
        ]

        runner.run_migrations(migrations)

        # Clear backups from migration
        backup_root = runner.project_path / ".gao-dev-backups"
        for backup in backup_root.iterdir():
            import shutil

            shutil.rmtree(backup)

        runner.rollback_migration(target_version=0, migrations=migrations)

        # Verify backup created
        backups = list(backup_root.iterdir())
        assert len(backups) >= 1

        # Verify backup reason
        latest_backup = runner.backup_manager.get_latest_backup(runner.project_path)
        assert latest_backup is not None
        assert latest_backup.reason == "pre_rollback"

    def test_rollback_migration_restores_backup_on_failure(self, runner: MigrationRunner):
        """Test rollback restores backup on failure."""

        def migration_1_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE test1 (id INTEGER)")

        def migration_1_down(conn: sqlite3.Connection) -> None:
            # Invalid SQL - will fail
            conn.execute("INVALID SQL")

        migrations = [
            Migration(version=1, description="Test1", up=migration_1_up, down=migration_1_down)
        ]

        runner.run_migrations(migrations)

        # Should fail and restore backup
        with pytest.raises(Exception) as exc_info:
            runner.rollback_migration(target_version=0, migrations=migrations)

        assert "Rollback failed" in str(exc_info.value)

        # Verify still at version 1 (rollback failed, backup restored)
        assert runner.get_current_version() == 1

    def test_rollback_migration_no_rollback_needed(self, runner: MigrationRunner):
        """Test rollback does nothing when target >= current."""
        runner.initialize_schema_version_table()

        def migration_1_up(conn: sqlite3.Connection) -> None:
            conn.execute("CREATE TABLE test1 (id INTEGER)")

        def migration_1_down(conn: sqlite3.Connection) -> None:
            conn.execute("DROP TABLE test1")

        migrations = [
            Migration(version=1, description="Test1", up=migration_1_up, down=migration_1_down)
        ]

        runner.run_migrations(migrations)

        # Try to rollback to same version
        runner.rollback_migration(target_version=1, migrations=migrations)

        # Should still be at version 1
        assert runner.get_current_version() == 1
