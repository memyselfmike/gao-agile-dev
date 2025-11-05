"""Tests for database migration system.

Tests verify:
- Migration applies successfully on fresh database
- Migration is idempotent (can run multiple times safely)
- Migration rollback works correctly
- schema_version table tracks migrations
"""

import sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from gao_dev.core.state.migrations import get_all_migrations
from gao_dev.core.state.migrations.migration_001_create_state_schema import (
    Migration001,
)


class TestMigrations:
    """Tests for migration system."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        # Cleanup
        if db_path.exists():
            db_path.unlink()

    def test_migration_001_upgrade(self, temp_db):
        """Test Migration001 applies successfully."""
        result = Migration001.upgrade(temp_db)
        assert result is True

        # Verify tables created
        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='epics'"
            )
            assert cursor.fetchone()[0] == 1

    def test_migration_001_downgrade(self, temp_db):
        """Test Migration001 rollback works correctly."""
        # Apply migration
        Migration001.upgrade(temp_db)

        # Rollback
        result = Migration001.downgrade(temp_db)
        assert result is True

        # Verify tables removed
        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='epics'"
            )
            assert cursor.fetchone()[0] == 0

    def test_migration_idempotent(self, temp_db):
        """Test migration is idempotent (can run multiple times)."""
        # Apply migration twice
        result1 = Migration001.upgrade(temp_db)
        result2 = Migration001.upgrade(temp_db)

        assert result1 is True
        assert result2 is True

        # Verify only one version record
        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM schema_version WHERE version = 1"
            )
            assert cursor.fetchone()[0] == 1

    def test_schema_version_tracking(self, temp_db):
        """Test schema_version table tracks migrations."""
        Migration001.upgrade(temp_db)

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute(
                "SELECT version, description FROM schema_version WHERE version = 1"
            )
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == Migration001.version
            assert row[1] == Migration001.description

    def test_get_all_migrations(self):
        """Test get_all_migrations returns all migration classes."""
        migrations = get_all_migrations()

        assert len(migrations) >= 1
        assert Migration001 in migrations

    def test_migration_version_attribute(self):
        """Test migration has version attribute."""
        assert hasattr(Migration001, "version")
        assert Migration001.version == 1

    def test_migration_description_attribute(self):
        """Test migration has description attribute."""
        assert hasattr(Migration001, "description")
        assert len(Migration001.description) > 0

    def test_migration_upgrade_method(self):
        """Test migration has upgrade method."""
        assert hasattr(Migration001, "upgrade")
        assert callable(Migration001.upgrade)

    def test_migration_downgrade_method(self):
        """Test migration has downgrade method."""
        assert hasattr(Migration001, "downgrade")
        assert callable(Migration001.downgrade)

    def test_migration_creates_schema_version_table(self, temp_db):
        """Test migration creates schema_version table."""
        Migration001.upgrade(temp_db)

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            assert cursor.fetchone() is not None

    def test_migration_rollback_removes_version(self, temp_db):
        """Test migration rollback removes version record."""
        # Apply migration
        Migration001.upgrade(temp_db)

        # Verify version exists
        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM schema_version WHERE version = 1"
            )
            assert cursor.fetchone()[0] == 1

        # Rollback
        Migration001.downgrade(temp_db)

        # Verify version removed
        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM schema_version WHERE version = 1"
            )
            assert cursor.fetchone()[0] == 0

    def test_migration_applies_on_fresh_database(self, temp_db):
        """Test migration applies successfully on fresh database."""
        # Database file exists but is empty
        assert temp_db.exists()

        # Apply migration
        result = Migration001.upgrade(temp_db)
        assert result is True

        # Verify all expected tables created
        expected_tables = {
            "epics",
            "stories",
            "sprints",
            "story_assignments",
            "workflow_executions",
            "state_changes",
            "schema_version",
        }

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            actual_tables = {row[0] for row in cursor.fetchall()}

        actual_tables.discard("sqlite_sequence")
        assert actual_tables == expected_tables

    def test_migration_rollback_order(self, temp_db):
        """Test migration rollback removes tables in correct order (reverse dependencies)."""
        # Apply migration
        Migration001.upgrade(temp_db)

        # Rollback
        Migration001.downgrade(temp_db)

        # Verify all tables removed
        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
                "('epics', 'stories', 'sprints', 'story_assignments', 'workflow_executions', 'state_changes')"
            )
            assert len(cursor.fetchall()) == 0
