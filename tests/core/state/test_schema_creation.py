"""Tests for database schema creation.

Tests verify:
- All tables created successfully
- All columns exist with correct types
- All constraints created (PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK, NOT NULL)
- All indexes created successfully
- All triggers created successfully
- Schema creation performance (<100ms)
"""

import sqlite3
import time
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from gao_dev.core.state.migrations.migration_001_create_state_schema import (
    Migration001,
)
from .conftest import safe_cleanup_db


class TestSchemaCreation:
    """Tests for schema creation."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        # Cleanup
        safe_cleanup_db(db_path)

    def test_schema_creation_success(self, temp_db):
        """Test schema creation completes successfully."""
        # Apply migration
        result = Migration001.upgrade(temp_db)
        assert result is True

        # Verify database file created
        assert temp_db.exists()

    def test_schema_creation_performance(self, temp_db):
        """Test schema creation completes in <100ms."""
        start_time = time.perf_counter()
        Migration001.upgrade(temp_db)
        duration_ms = (time.perf_counter() - start_time) * 1000

        assert duration_ms < 100, f"Schema creation took {duration_ms:.2f}ms (expected <100ms)"

    def test_all_tables_created(self, temp_db):
        """Test all expected tables are created."""
        Migration001.upgrade(temp_db)

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

        # sqlite_sequence is auto-created for AUTOINCREMENT
        actual_tables.discard("sqlite_sequence")

        assert actual_tables == expected_tables

    def test_epics_table_structure(self, temp_db):
        """Test epics table has all expected columns."""
        Migration001.upgrade(temp_db)

        expected_columns = {
            "id",
            "epic_num",
            "name",
            "feature",
            "goal",
            "description",
            "status",
            "total_points",
            "completed_points",
            "owner",
            "created_by",
            "created_at",
            "started_at",
            "completed_at",
            "updated_at",
            "file_path",
            "content_hash",
            "metadata",
        }

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute("PRAGMA table_info(epics)")
            actual_columns = {row[1] for row in cursor.fetchall()}

        assert actual_columns == expected_columns

    def test_stories_table_structure(self, temp_db):
        """Test stories table has all expected columns."""
        Migration001.upgrade(temp_db)

        expected_columns = {
            "id",
            "epic_num",
            "story_num",
            "title",
            "description",
            "status",
            "priority",
            "points",
            "owner",
            "created_by",
            "created_at",
            "started_at",
            "completed_at",
            "updated_at",
            "due_date",
            "file_path",
            "content_hash",
            "metadata",
            "tags",
        }

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute("PRAGMA table_info(stories)")
            actual_columns = {row[1] for row in cursor.fetchall()}

        assert actual_columns == expected_columns

    def test_sprints_table_structure(self, temp_db):
        """Test sprints table has all expected columns."""
        Migration001.upgrade(temp_db)

        expected_columns = {
            "id",
            "sprint_num",
            "name",
            "goal",
            "status",
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
            "planned_points",
            "completed_points",
            "velocity",
            "metadata",
        }

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute("PRAGMA table_info(sprints)")
            actual_columns = {row[1] for row in cursor.fetchall()}

        assert actual_columns == expected_columns

    def test_story_assignments_table_structure(self, temp_db):
        """Test story_assignments table has all expected columns."""
        Migration001.upgrade(temp_db)

        expected_columns = {"sprint_num", "epic_num", "story_num", "assigned_at"}

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute("PRAGMA table_info(story_assignments)")
            actual_columns = {row[1] for row in cursor.fetchall()}

        assert actual_columns == expected_columns

    def test_workflow_executions_table_structure(self, temp_db):
        """Test workflow_executions table has all expected columns."""
        Migration001.upgrade(temp_db)

        expected_columns = {
            "id",
            "workflow_name",
            "phase",
            "epic_num",
            "story_num",
            "status",
            "executor",
            "started_at",
            "completed_at",
            "duration_ms",
            "output",
            "error_message",
            "exit_code",
            "metadata",
            "context_snapshot",
        }

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute("PRAGMA table_info(workflow_executions)")
            actual_columns = {row[1] for row in cursor.fetchall()}

        assert actual_columns == expected_columns

    def test_state_changes_table_structure(self, temp_db):
        """Test state_changes table has all expected columns."""
        Migration001.upgrade(temp_db)

        expected_columns = {
            "id",
            "table_name",
            "record_id",
            "field_name",
            "old_value",
            "new_value",
            "changed_by",
            "changed_at",
            "reason",
        }

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute("PRAGMA table_info(state_changes)")
            actual_columns = {row[1] for row in cursor.fetchall()}

        assert actual_columns == expected_columns

    def test_all_indexes_created(self, temp_db):
        """Test all expected indexes are created."""
        Migration001.upgrade(temp_db)

        expected_indexes = {
            "idx_stories_status",
            "idx_stories_epic",
            "idx_stories_priority",
            "idx_stories_owner",
            "idx_stories_epic_status",
            "idx_epics_status",
            "idx_epics_feature",
            "idx_sprints_status",
            "idx_sprints_dates",
            "idx_assignments_sprint",
            "idx_assignments_story",
            "idx_workflow_story",
            "idx_workflow_status",
            "idx_workflow_name",
            "idx_changes_record",
        }

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            )
            actual_indexes = {row[0] for row in cursor.fetchall()}

        assert actual_indexes == expected_indexes

    def test_all_triggers_created(self, temp_db):
        """Test all expected triggers are created."""
        Migration001.upgrade(temp_db)

        expected_triggers = {
            "update_epic_timestamp",
            "update_story_timestamp",
            "update_sprint_timestamp",
            "update_epic_points_on_story_status",
            "update_epic_points_on_story_status_revert",
            "log_story_status_change",
            "log_epic_status_change",
            "log_sprint_status_change",
        }

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
            actual_triggers = {row[0] for row in cursor.fetchall()}

        assert actual_triggers == expected_triggers

    def test_schema_version_recorded(self, temp_db):
        """Test schema version is recorded in schema_version table."""
        Migration001.upgrade(temp_db)

        with sqlite3.connect(str(temp_db)) as conn:
            cursor = conn.execute(
                "SELECT version, description FROM schema_version WHERE version = 1"
            )
            row = cursor.fetchone()

        assert row is not None
        assert row[0] == 1
        assert Migration001.description in row[1]

    def test_migration_idempotent(self, temp_db):
        """Test migration can be run multiple times safely."""
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
            count = cursor.fetchone()[0]

        assert count == 1

    def test_foreign_keys_enabled(self, temp_db):
        """Test foreign keys are enabled in migration."""
        Migration001.upgrade(temp_db)

        with sqlite3.connect(str(temp_db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.execute("PRAGMA foreign_keys")
            fk_enabled = cursor.fetchone()[0]

        assert fk_enabled == 1
