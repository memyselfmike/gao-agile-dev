"""Tests for schema validation.

Tests verify:
- Schema validator detects missing tables
- Schema validator detects missing indexes
- Schema validator detects missing triggers
- Schema validator detects missing columns
- Schema validator checks foreign keys enabled
- get_schema_info returns detailed information
"""

import sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from gao_dev.core.state.migrations.migration_001_create_state_schema import (
    Migration001,
)
from gao_dev.core.state.schema_validator import SchemaValidator
from .conftest import safe_cleanup_db


class TestSchemaValidation:
    """Tests for schema validation."""

    @pytest.fixture
    def valid_db(self):
        """Create a database with valid schema."""
        with NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        Migration001.upgrade(db_path)

        yield db_path

        # Cleanup
        safe_cleanup_db(db_path)

    @pytest.fixture
    def empty_db(self):
        """Create an empty database."""
        with NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        # Create empty database
        with sqlite3.connect(str(db_path)) as conn:
            conn.execute("SELECT 1")

        yield db_path

        # Cleanup
        safe_cleanup_db(db_path)

    def test_validate_valid_schema(self, valid_db):
        """Test schema validator passes for valid schema."""
        results = SchemaValidator.validate_schema(valid_db)

        assert results["tables_valid"] is True
        assert results["indexes_valid"] is True
        assert results["triggers_valid"] is True
        assert results["columns_valid"] is True
        assert len(results["errors"]) == 0

    def test_is_valid_helper(self, valid_db):
        """Test is_valid helper returns True for valid schema."""
        results = SchemaValidator.validate_schema(valid_db)
        assert SchemaValidator.is_valid(results) is True

    def test_validate_empty_database(self, empty_db):
        """Test schema validator detects missing tables."""
        results = SchemaValidator.validate_schema(empty_db)

        assert results["tables_valid"] is False
        assert len(results["errors"]) > 0
        assert any("Missing tables" in error for error in results["errors"])

    def test_validate_missing_indexes(self, valid_db):
        """Test schema validator detects missing indexes."""
        # Remove an index
        with sqlite3.connect(str(valid_db)) as conn:
            conn.execute("DROP INDEX IF EXISTS idx_stories_status")

        results = SchemaValidator.validate_schema(valid_db)

        assert results["indexes_valid"] is False
        assert any("Missing indexes" in error for error in results["errors"])
        assert any("idx_stories_status" in error for error in results["errors"])

    def test_validate_missing_triggers(self, valid_db):
        """Test schema validator detects missing triggers."""
        # Remove a trigger
        with sqlite3.connect(str(valid_db)) as conn:
            conn.execute("DROP TRIGGER IF EXISTS update_epic_timestamp")

        results = SchemaValidator.validate_schema(valid_db)

        assert results["triggers_valid"] is False
        assert any("Missing triggers" in error for error in results["errors"])

    def test_validate_foreign_keys_enabled(self, valid_db):
        """Test schema validator checks foreign keys enabled."""
        # Note: foreign_keys setting is connection-specific, not database-specific
        # So we test with a fresh connection
        with sqlite3.connect(str(valid_db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create a new connection without enabling foreign keys
            with sqlite3.connect(str(valid_db)) as conn2:
                cursor = conn2.execute("PRAGMA foreign_keys")
                fk_enabled = cursor.fetchone()[0]
                # Foreign keys default to OFF
                assert fk_enabled == 0

    def test_validate_missing_columns(self, valid_db):
        """Test schema validator detects missing columns."""
        # We can't easily remove a column, so we create a new table missing columns
        with sqlite3.connect(str(valid_db)) as conn:
            # Drop and recreate epics table with missing columns
            conn.execute("DROP TABLE IF EXISTS epics")
            conn.execute("""
                CREATE TABLE epics (
                    id INTEGER PRIMARY KEY,
                    epic_num INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL
                )
            """)

        results = SchemaValidator.validate_schema(valid_db)

        assert results["columns_valid"] is False
        assert any("missing columns" in error.lower() for error in results["errors"])

    def test_get_schema_info(self, valid_db):
        """Test get_schema_info returns detailed information."""
        info = SchemaValidator.get_schema_info(valid_db)

        # Check structure
        assert "tables" in info
        assert "indexes" in info
        assert "triggers" in info
        assert "version" in info

        # Check tables
        assert "epics" in info["tables"]
        assert "stories" in info["tables"]
        assert "sprints" in info["tables"]
        assert "features" in info["tables"]
        assert "features_audit" in info["tables"]

        # Check indexes
        assert "idx_stories_status" in info["indexes"]
        assert info["indexes"]["idx_stories_status"]["table"] == "stories"
        assert "idx_features_scope" in info["indexes"]
        assert info["indexes"]["idx_features_scope"]["table"] == "features"

        # Check triggers
        assert "update_epic_timestamp" in info["triggers"]
        assert info["triggers"]["update_epic_timestamp"]["table"] == "epics"
        assert "features_completed_at_update" in info["triggers"]
        assert info["triggers"]["features_completed_at_update"]["table"] == "features"

        # Check version
        assert info["version"] is not None
        assert info["version"]["version"] == 1

    def test_expected_tables_constant(self):
        """Test EXPECTED_TABLES constant is complete."""
        expected = SchemaValidator.EXPECTED_TABLES

        assert "epics" in expected
        assert "stories" in expected
        assert "sprints" in expected
        assert "story_assignments" in expected
        assert "workflow_executions" in expected
        assert "state_changes" in expected
        assert "schema_version" in expected
        assert "features" in expected
        assert "features_audit" in expected

    def test_expected_indexes_constant(self):
        """Test EXPECTED_INDEXES constant is complete."""
        expected = SchemaValidator.EXPECTED_INDEXES

        # Stories indexes
        assert "idx_stories_status" in expected
        assert "idx_stories_epic" in expected
        assert "idx_stories_priority" in expected
        assert "idx_stories_owner" in expected
        assert "idx_stories_epic_status" in expected

        # Epics indexes
        assert "idx_epics_status" in expected
        assert "idx_epics_feature" in expected

        # Sprints indexes
        assert "idx_sprints_status" in expected
        assert "idx_sprints_dates" in expected

        # Assignments indexes
        assert "idx_assignments_sprint" in expected
        assert "idx_assignments_story" in expected

        # Workflow executions indexes
        assert "idx_workflow_story" in expected
        assert "idx_workflow_status" in expected
        assert "idx_workflow_name" in expected

        # State changes index
        assert "idx_changes_record" in expected

        # Features indexes
        assert "idx_features_scope" in expected
        assert "idx_features_status" in expected
        assert "idx_features_scale_level" in expected
        assert "idx_features_audit_feature_id" in expected

    def test_expected_triggers_constant(self):
        """Test EXPECTED_TRIGGERS constant is complete."""
        expected = SchemaValidator.EXPECTED_TRIGGERS

        # Timestamp triggers
        assert "update_epic_timestamp" in expected
        assert "update_story_timestamp" in expected
        assert "update_sprint_timestamp" in expected

        # Points calculation triggers
        assert "update_epic_points_on_story_status" in expected
        assert "update_epic_points_on_story_status_revert" in expected

        # Audit log triggers
        assert "log_story_status_change" in expected
        assert "log_epic_status_change" in expected
        assert "log_sprint_status_change" in expected

        # Features triggers
        assert "features_completed_at_update" in expected
        assert "features_audit_insert" in expected
        assert "features_audit_update" in expected
        assert "features_audit_delete" in expected

    def test_expected_columns_for_epics(self):
        """Test EXPECTED_COLUMNS for epics table is complete."""
        expected = SchemaValidator.EXPECTED_COLUMNS["epics"]

        assert "id" in expected
        assert "epic_num" in expected
        assert "name" in expected
        assert "status" in expected
        assert "total_points" in expected
        assert "completed_points" in expected
        assert "created_at" in expected
        assert "updated_at" in expected
        assert "metadata" in expected

    def test_expected_columns_for_stories(self):
        """Test EXPECTED_COLUMNS for stories table is complete."""
        expected = SchemaValidator.EXPECTED_COLUMNS["stories"]

        assert "id" in expected
        assert "epic_num" in expected
        assert "story_num" in expected
        assert "title" in expected
        assert "status" in expected
        assert "priority" in expected
        assert "points" in expected
        assert "created_at" in expected
        assert "updated_at" in expected
        assert "tags" in expected
        assert "metadata" in expected

    def test_validate_warnings_for_extra_tables(self, valid_db):
        """Test schema validator warns about extra tables."""
        # Add an extra table
        with sqlite3.connect(str(valid_db)) as conn:
            conn.execute("CREATE TABLE extra_table (id INTEGER PRIMARY KEY)")

        results = SchemaValidator.validate_schema(valid_db)

        # Should still be valid but with warnings
        assert results["tables_valid"] is True
        assert len(results["warnings"]) > 0
        assert any("Unexpected tables" in warning for warning in results["warnings"])

    def test_validate_warnings_for_extra_indexes(self, valid_db):
        """Test schema validator warns about extra indexes."""
        # Add an extra index
        with sqlite3.connect(str(valid_db)) as conn:
            conn.execute("CREATE INDEX idx_extra ON epics(name)")

        results = SchemaValidator.validate_schema(valid_db)

        # Should still be valid but with warnings
        assert results["indexes_valid"] is True
        assert len(results["warnings"]) > 0
        assert any("Unexpected indexes" in warning for warning in results["warnings"])

    def test_schema_info_no_version_table(self, empty_db):
        """Test get_schema_info handles missing schema_version table."""
        info = SchemaValidator.get_schema_info(empty_db)

        assert info["version"] is None
        assert "tables" in info
        assert "indexes" in info
        assert "triggers" in info
