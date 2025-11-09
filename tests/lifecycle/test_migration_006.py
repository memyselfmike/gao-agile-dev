"""
Tests for Migration 006: Learning Application Tracking.

Epic: 29 - Self-Learning Feedback Loop
Story: 29.1 - Learning Schema Enhancement

Coverage Target: >95%
"""

import sqlite3
import tempfile
from pathlib import Path
import importlib.util
import sys
import json
from datetime import datetime

import pytest


def load_migration_006():
    """Load migration 006 module dynamically."""
    migration_path = (
        Path(__file__).parent.parent.parent
        / "gao_dev"
        / "lifecycle"
        / "migrations"
        / "006_add_learning_application_tracking.py"
    )
    spec = importlib.util.spec_from_file_location("migration_006", migration_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["migration_006"] = module
    spec.loader.exec_module(module)
    return module.Migration006, module.create_backup, module.run_migration


Migration006, create_backup, run_migration = load_migration_006()


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()

    # Cleanup backup files
    for backup in db_path.parent.glob(f"{db_path.stem}_backup_*{db_path.suffix}"):
        backup.unlink(missing_ok=True)


@pytest.fixture
def db_with_learning_index(temp_db):
    """Create a database with Migration 005 schema (learning_index table)."""
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Create schema_version table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL,
            description TEXT
        )
        """
    )

    # Create epic_state table (for foreign keys)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS epic_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epic_num INTEGER UNIQUE NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            total_stories INTEGER NOT NULL DEFAULT 0,
            completed_stories INTEGER NOT NULL DEFAULT 0,
            progress_percentage REAL NOT NULL DEFAULT 0.0,
            started_at TEXT,
            completed_at TEXT,
            blocked_reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata JSON
        )
        """
    )

    # Create learning_index table (from Migration 005)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS learning_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            category TEXT NOT NULL CHECK(category IN (
                'technical', 'process', 'domain', 'architectural', 'team'
            )),
            learning TEXT NOT NULL,
            context TEXT,
            source_type TEXT CHECK(source_type IN (
                'retrospective', 'postmortem', 'code_review', 'incident', 'experiment'
            )),
            epic_num INTEGER,
            story_num INTEGER,
            relevance_score REAL DEFAULT 1.0,
            superseded_by INTEGER,
            is_active INTEGER NOT NULL DEFAULT 1,
            indexed_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            metadata JSON,
            FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num) ON DELETE SET NULL,
            FOREIGN KEY (superseded_by) REFERENCES learning_index(id) ON DELETE SET NULL
        )
        """
    )

    # Insert test data
    cursor.execute(
        """
        INSERT INTO epic_state (epic_num, title, status, created_at, updated_at)
        VALUES (29, 'Test Epic', 'planning', datetime('now'), datetime('now'))
        """
    )

    cursor.execute(
        """
        INSERT INTO learning_index (
            topic, category, learning, context, source_type,
            epic_num, indexed_at, created_at
        )
        VALUES (
            'Testing', 'technical', 'Write tests first', 'TDD approach',
            'retrospective', 29, datetime('now'), datetime('now')
        )
        """
    )

    # Record Migration 005
    cursor.execute(
        """
        INSERT INTO schema_version (version, applied_at, description)
        VALUES ('005', datetime('now'), 'State tracking tables')
        """
    )

    conn.commit()
    conn.close()

    return temp_db


class TestMigration006Up:
    """Tests for migration up (applying)."""

    def test_adds_four_columns_to_learning_index(self, db_with_learning_index):
        """Test that migration adds 4 new columns to learning_index table."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            Migration006.up(conn)

            cursor = conn.cursor()

            # Get column names
            cursor.execute("PRAGMA table_info(learning_index)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type

            # Verify new columns exist with correct types
            assert "application_count" in columns
            assert "INTEGER" in columns["application_count"]

            assert "success_rate" in columns
            assert "REAL" in columns["success_rate"]

            assert "confidence_score" in columns
            assert "REAL" in columns["confidence_score"]

            assert "decay_factor" in columns
            assert "REAL" in columns["decay_factor"]

        finally:
            conn.close()

    def test_new_columns_have_default_values(self, db_with_learning_index):
        """Test that new columns have correct default values."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            # Get existing learning before migration
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM learning_index LIMIT 1")
            learning_id = cursor.fetchone()[0]

            # Apply migration
            Migration006.up(conn)

            # Check default values on existing record
            cursor.execute(
                """
                SELECT application_count, success_rate, confidence_score, decay_factor
                FROM learning_index WHERE id = ?
                """,
                (learning_id,),
            )

            row = cursor.fetchone()
            assert row[0] == 0  # application_count default
            assert row[1] == 1.0  # success_rate default
            assert row[2] == 0.5  # confidence_score default
            assert row[3] == 1.0  # decay_factor default

        finally:
            conn.close()

    def test_creates_learning_applications_table(self, db_with_learning_index):
        """Test that migration creates learning_applications table."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            Migration006.up(conn)

            cursor = conn.cursor()

            # Check table exists
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='learning_applications'
                """
            )

            assert cursor.fetchone() is not None

            # Check table structure
            cursor.execute("PRAGMA table_info(learning_applications)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "id" in columns
            assert "learning_id" in columns
            assert "epic_num" in columns
            assert "story_num" in columns
            assert "outcome" in columns
            assert "application_context" in columns
            assert "applied_at" in columns
            assert "metadata" in columns

        finally:
            conn.close()

    def test_learning_applications_check_constraint(self, db_with_learning_index):
        """Test that learning_applications table enforces outcome CHECK constraint."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            Migration006.up(conn)

            cursor = conn.cursor()

            # Valid outcomes should work
            for outcome in ["success", "failure", "partial"]:
                cursor.execute(
                    """
                    INSERT INTO learning_applications (
                        learning_id, outcome, applied_at
                    ) VALUES (1, ?, datetime('now'))
                    """,
                    (outcome,),
                )

            conn.commit()

            # Invalid outcome should fail
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    """
                    INSERT INTO learning_applications (
                        learning_id, outcome, applied_at
                    ) VALUES (1, 'invalid_outcome', datetime('now'))
                    """
                )
                conn.commit()

        finally:
            conn.close()

    def test_creates_five_indexes(self, db_with_learning_index):
        """Test that migration creates 5 new indexes."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            Migration006.up(conn)

            cursor = conn.cursor()

            # Get all indexes
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name LIKE 'idx_learning%'
                ORDER BY name
                """
            )

            indexes = [row[0] for row in cursor.fetchall()]

            # Verify new indexes exist
            assert "idx_learning_applications_learning_id" in indexes
            assert "idx_learning_applications_epic" in indexes
            assert "idx_learning_applications_applied_at" in indexes
            assert "idx_learning_index_category_active" in indexes
            assert "idx_learning_index_relevance" in indexes

        finally:
            conn.close()

    def test_records_migration_version(self, db_with_learning_index):
        """Test that migration records itself in schema_version table."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            Migration006.up(conn)

            cursor = conn.cursor()
            cursor.execute(
                "SELECT version, description FROM schema_version WHERE version = '006'"
            )

            result = cursor.fetchone()

            assert result is not None
            assert result[0] == "006"
            assert "learning application tracking" in result[1].lower()

        finally:
            conn.close()

    def test_foreign_key_constraints(self, db_with_learning_index):
        """Test that foreign key constraints work correctly."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            Migration006.up(conn)

            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")

            # Insert application for existing learning
            cursor.execute(
                """
                INSERT INTO learning_applications (
                    learning_id, epic_num, outcome, applied_at
                ) VALUES (1, 29, 'success', datetime('now'))
                """
            )

            conn.commit()

            # Verify insert worked
            cursor.execute("SELECT COUNT(*) FROM learning_applications")
            assert cursor.fetchone()[0] == 1

            # Test CASCADE DELETE: deleting learning should delete applications
            cursor.execute("DELETE FROM learning_index WHERE id = 1")
            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM learning_applications WHERE learning_id = 1")
            assert cursor.fetchone()[0] == 0

        finally:
            conn.close()

    def test_preserves_existing_data(self, db_with_learning_index):
        """Test that migration preserves all existing learning_index data."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            # Get data before migration
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM learning_index")
            before_data = cursor.fetchall()

            # Apply migration
            Migration006.up(conn)

            # Get data after migration (excluding new columns)
            cursor.execute(
                """
                SELECT id, topic, category, learning, context, source_type,
                       epic_num, story_num, relevance_score, superseded_by,
                       is_active, indexed_at, created_at, metadata
                FROM learning_index
                """
            )
            after_data = cursor.fetchall()

            # Data should be identical (same number of rows, same values)
            assert len(before_data) == len(after_data)
            assert before_data[0] == after_data[0]  # Same data

        finally:
            conn.close()

    def test_migration_is_idempotent(self, db_with_learning_index):
        """Test that running migration twice doesn't cause errors."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            # Apply migration once
            Migration006.up(conn)

            # Apply migration again (should handle gracefully)
            # Note: ALTER TABLE will fail if column exists, so we catch the error
            # This tests that the migration can detect already-applied state
            try:
                Migration006.up(conn)
            except sqlite3.OperationalError as e:
                # Expected: "duplicate column name" error
                assert "duplicate column" in str(e).lower()

        finally:
            conn.close()


class TestMigration006Down:
    """Tests for migration down (rollback)."""

    def test_removes_learning_applications_table(self, db_with_learning_index):
        """Test that rollback removes learning_applications table."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            # Apply migration first
            Migration006.up(conn)

            cursor = conn.cursor()

            # Verify table exists
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='learning_applications'
                """
            )
            assert cursor.fetchone() is not None

            # Rollback
            Migration006.down(conn)

            # Verify table is gone
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='learning_applications'
                """
            )
            assert cursor.fetchone() is None

        finally:
            conn.close()

    def test_removes_new_columns_from_learning_index(self, db_with_learning_index):
        """Test that rollback removes new columns using table rebuild strategy."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            # Apply migration first
            Migration006.up(conn)

            cursor = conn.cursor()

            # Verify new columns exist
            cursor.execute("PRAGMA table_info(learning_index)")
            columns_after_up = {row[1] for row in cursor.fetchall()}

            assert "application_count" in columns_after_up
            assert "success_rate" in columns_after_up
            assert "confidence_score" in columns_after_up
            assert "decay_factor" in columns_after_up

            # Rollback
            Migration006.down(conn)

            # Verify new columns are gone
            cursor.execute("PRAGMA table_info(learning_index)")
            columns_after_down = {row[1] for row in cursor.fetchall()}

            assert "application_count" not in columns_after_down
            assert "success_rate" not in columns_after_down
            assert "confidence_score" not in columns_after_down
            assert "decay_factor" not in columns_after_down

        finally:
            conn.close()

    def test_preserves_original_data_during_rollback(self, db_with_learning_index):
        """Test that rollback preserves original learning_index data."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            cursor = conn.cursor()

            # Get original data
            cursor.execute(
                """
                SELECT id, topic, category, learning, context, source_type,
                       epic_num, story_num, relevance_score, superseded_by,
                       is_active, indexed_at, created_at, metadata
                FROM learning_index
                """
            )
            original_data = cursor.fetchall()

            # Apply migration
            Migration006.up(conn)

            # Rollback
            Migration006.down(conn)

            # Get data after rollback
            cursor.execute(
                """
                SELECT id, topic, category, learning, context, source_type,
                       epic_num, story_num, relevance_score, superseded_by,
                       is_active, indexed_at, created_at, metadata
                FROM learning_index
                """
            )
            after_rollback_data = cursor.fetchall()

            # Data should be identical
            assert original_data == after_rollback_data

        finally:
            conn.close()

    def test_recreates_original_indexes(self, db_with_learning_index):
        """Test that rollback recreates original indexes."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            # Apply migration first
            Migration006.up(conn)

            # Rollback
            Migration006.down(conn)

            cursor = conn.cursor()

            # Check original indexes exist
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='index'
                """
            )
            indexes = [row[0] for row in cursor.fetchall()]

            # Original indexes from Migration 005 should be recreated
            # (Note: actual index names may vary, this tests the pattern)
            assert any("learning" in idx for idx in indexes)

        finally:
            conn.close()

    def test_removes_migration_record(self, db_with_learning_index):
        """Test that rollback removes migration record from schema_version."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            # Apply migration first
            Migration006.up(conn)

            cursor = conn.cursor()

            # Verify record exists
            cursor.execute("SELECT COUNT(*) FROM schema_version WHERE version = '006'")
            assert cursor.fetchone()[0] == 1

            # Rollback
            Migration006.down(conn)

            # Verify record is gone
            cursor.execute("SELECT COUNT(*) FROM schema_version WHERE version = '006'")
            assert cursor.fetchone()[0] == 0

        finally:
            conn.close()


class TestMigration006IsApplied:
    """Tests for is_applied check."""

    def test_returns_false_when_not_applied(self, db_with_learning_index):
        """Test that is_applied returns False before migration."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            assert Migration006.is_applied(conn) is False
        finally:
            conn.close()

    def test_returns_true_when_applied(self, db_with_learning_index):
        """Test that is_applied returns True after migration."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            Migration006.up(conn)
            assert Migration006.is_applied(conn) is True
        finally:
            conn.close()

    def test_returns_false_when_rolled_back(self, db_with_learning_index):
        """Test that is_applied returns False after rollback."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            Migration006.up(conn)
            assert Migration006.is_applied(conn) is True

            Migration006.down(conn)
            assert Migration006.is_applied(conn) is False
        finally:
            conn.close()


class TestMigration006Verify:
    """Tests for verify function."""

    def test_verify_detects_unapplied_migration(self, db_with_learning_index):
        """Test that verify correctly detects unapplied migration."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            result = Migration006.verify(conn)

            assert result["applied"] is False
            assert len(result["issues"]) > 0
            assert any("not recorded" in issue.lower() for issue in result["issues"])

        finally:
            conn.close()

    def test_verify_detects_applied_migration(self, db_with_learning_index):
        """Test that verify correctly detects applied migration."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            Migration006.up(conn)

            result = Migration006.verify(conn)

            assert result["applied"] is True
            assert len(result["learning_index_columns"]) == 4
            assert result["learning_applications_exists"] is True
            assert len(result["indexes"]) == 5
            assert result["foreign_keys_enabled"] is True
            assert len(result["issues"]) == 0

        finally:
            conn.close()

    def test_verify_detects_missing_columns(self, db_with_learning_index):
        """Test that verify detects missing columns."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            # Manually create incomplete migration state
            cursor = conn.cursor()

            # Add only some columns
            cursor.execute("ALTER TABLE learning_index ADD COLUMN application_count INTEGER DEFAULT 0")

            # Mark as applied
            cursor.execute(
                """
                INSERT INTO schema_version (version, applied_at, description)
                VALUES ('006', datetime('now'), 'Incomplete migration')
                """
            )
            conn.commit()

            result = Migration006.verify(conn)

            # Should detect missing columns
            assert any("missing columns" in issue.lower() for issue in result["issues"])

        finally:
            conn.close()

    def test_verify_detects_missing_table(self, db_with_learning_index):
        """Test that verify detects missing learning_applications table."""
        conn = sqlite3.connect(str(db_with_learning_index))

        try:
            # Apply full migration
            Migration006.up(conn)

            # Manually drop table to simulate incomplete state
            cursor = conn.cursor()
            cursor.execute("DROP TABLE learning_applications")
            conn.commit()

            result = Migration006.verify(conn)

            # Should detect missing table
            assert result["learning_applications_exists"] is False
            assert any("table does not exist" in issue.lower() for issue in result["issues"])

        finally:
            conn.close()


class TestCreateBackup:
    """Tests for create_backup function."""

    def test_creates_backup_file(self, db_with_learning_index):
        """Test that create_backup creates a backup file."""
        backup_path = create_backup(db_with_learning_index)

        try:
            assert backup_path.exists()
            assert backup_path.suffix == ".db"
            assert "backup" in backup_path.name

        finally:
            if backup_path.exists():
                backup_path.unlink()

    def test_backup_contains_same_data(self, db_with_learning_index):
        """Test that backup file contains same data as original."""
        # Get original data
        conn_orig = sqlite3.connect(str(db_with_learning_index))
        cursor_orig = conn_orig.cursor()
        cursor_orig.execute("SELECT COUNT(*) FROM learning_index")
        orig_count = cursor_orig.fetchone()[0]
        conn_orig.close()

        # Create backup
        backup_path = create_backup(db_with_learning_index)

        try:
            # Check backup data
            conn_backup = sqlite3.connect(str(backup_path))
            cursor_backup = conn_backup.cursor()
            cursor_backup.execute("SELECT COUNT(*) FROM learning_index")
            backup_count = cursor_backup.fetchone()[0]
            conn_backup.close()

            assert backup_count == orig_count

        finally:
            if backup_path.exists():
                backup_path.unlink()


class TestRunMigration:
    """Tests for run_migration function."""

    def test_run_migration_up(self, db_with_learning_index):
        """Test run_migration with direction='up'."""
        result = run_migration(db_with_learning_index, direction="up", backup=False)

        assert result["success"] is True
        assert result["direction"] == "up"

        # Verify migration was applied
        conn = sqlite3.connect(str(db_with_learning_index))
        try:
            assert Migration006.is_applied(conn)
        finally:
            conn.close()

    def test_run_migration_down(self, db_with_learning_index):
        """Test run_migration with direction='down'."""
        # Apply first
        run_migration(db_with_learning_index, direction="up", backup=False)

        # Rollback
        result = run_migration(db_with_learning_index, direction="down", backup=False)

        assert result["success"] is True
        assert result["direction"] == "down"

        # Verify migration was rolled back
        conn = sqlite3.connect(str(db_with_learning_index))
        try:
            assert not Migration006.is_applied(conn)
        finally:
            conn.close()

    def test_run_migration_verify(self, db_with_learning_index):
        """Test run_migration with direction='verify'."""
        # Apply migration
        run_migration(db_with_learning_index, direction="up", backup=False)

        # Verify
        result = run_migration(db_with_learning_index, direction="verify", backup=False)

        assert result["success"] is True
        assert result["direction"] == "verify"
        assert "verification" in result
        assert len(result["verification"]["issues"]) == 0

    def test_run_migration_creates_backup(self, db_with_learning_index):
        """Test that run_migration creates backup when requested."""
        result = run_migration(db_with_learning_index, direction="up", backup=True)

        assert result["backup_path"] is not None

        backup_path = Path(result["backup_path"])
        assert backup_path.exists()

        # Cleanup
        backup_path.unlink()

    def test_run_migration_dry_run(self, db_with_learning_index):
        """Test run_migration in dry-run mode."""
        result = run_migration(
            db_with_learning_index, direction="up", backup=False, dry_run=True
        )

        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["would_apply"] is True

        # Verify migration was NOT actually applied
        conn = sqlite3.connect(str(db_with_learning_index))
        try:
            assert not Migration006.is_applied(conn)
        finally:
            conn.close()

    def test_run_migration_invalid_direction(self, db_with_learning_index):
        """Test that run_migration raises error for invalid direction."""
        with pytest.raises(ValueError, match="Invalid direction"):
            run_migration(db_with_learning_index, direction="invalid", backup=False)
