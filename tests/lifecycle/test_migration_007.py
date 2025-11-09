"""Tests for Migration 007: Workflow Adjustments Tracking.

Tests migration up/down/verify operations for workflow_adjustments table.

Story: 29.4 - Workflow Adjustment Logic
Epic: 29 - Self-Learning Feedback Loop
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime

from gao_dev.lifecycle.migrations.migration_007_workflow_adjustments import (
    Migration007,
    run_migration,
)


@pytest.fixture
def temp_db():
    """Create temporary database with prerequisite tables."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create prerequisite tables
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL,
            description TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS epic_state (
            epic_num INTEGER PRIMARY KEY,
            epic_title TEXT,
            status TEXT,
            created_at TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS learning_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            category TEXT NOT NULL,
            learning TEXT NOT NULL,
            indexed_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # Insert test data
    cursor.execute(
        """
        INSERT INTO epic_state (epic_num, epic_title, status, created_at)
        VALUES (29, 'Test Epic', 'in_progress', datetime('now'))
        """
    )

    cursor.execute(
        """
        INSERT INTO learning_index (topic, category, learning, indexed_at, created_at)
        VALUES ('testing', 'quality', 'Test learning', datetime('now'), datetime('now'))
        """
    )

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    db_path.unlink()


# Tests: Migration Up


def test_migration_up_creates_table(temp_db):
    """Test that migration up creates workflow_adjustments table."""
    conn = sqlite3.connect(str(temp_db))

    # Apply migration
    Migration007.up(conn)

    # Check table exists
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='workflow_adjustments'
        """
    )
    result = cursor.fetchone()

    assert result is not None
    assert result[0] == "workflow_adjustments"

    conn.close()


def test_migration_up_creates_indexes(temp_db):
    """Test that migration up creates all indexes."""
    conn = sqlite3.connect(str(temp_db))

    # Apply migration
    Migration007.up(conn)

    # Check indexes exist
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cursor.fetchall()]

    expected_indexes = [
        "idx_workflow_adjustments_epic",
        "idx_workflow_adjustments_learning",
        "idx_workflow_adjustments_type",
        "idx_workflow_adjustments_applied_at",
        "idx_workflow_adjustments_epic_time",
    ]

    for expected in expected_indexes:
        assert expected in indexes

    conn.close()


def test_migration_up_records_version(temp_db):
    """Test that migration up records version in schema_version."""
    conn = sqlite3.connect(str(temp_db))

    # Apply migration
    Migration007.up(conn)

    # Check version recorded
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM schema_version WHERE version = ?", (Migration007.VERSION,))
    result = cursor.fetchone()

    assert result is not None
    assert result[0] == Migration007.VERSION

    conn.close()


def test_migration_up_table_structure(temp_db):
    """Test that workflow_adjustments table has correct structure."""
    conn = sqlite3.connect(str(temp_db))

    # Apply migration
    Migration007.up(conn)

    # Check columns
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(workflow_adjustments)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    expected_columns = {
        "id": "INTEGER",
        "epic_num": "INTEGER",
        "learning_id": "INTEGER",
        "adjustment_type": "TEXT",
        "workflow_name": "TEXT",
        "reason": "TEXT",
        "applied_at": "TEXT",
        "metadata": "JSON",
    }

    for col_name, col_type in expected_columns.items():
        assert col_name in columns
        assert columns[col_name] == col_type

    conn.close()


def test_migration_up_foreign_keys(temp_db):
    """Test that foreign key constraints work."""
    conn = sqlite3.connect(str(temp_db))
    conn.execute("PRAGMA foreign_keys = ON")

    # Apply migration
    Migration007.up(conn)

    cursor = conn.cursor()

    # Valid insert (should succeed)
    cursor.execute(
        """
        INSERT INTO workflow_adjustments
        (epic_num, learning_id, adjustment_type, workflow_name, reason, applied_at)
        VALUES (29, 1, 'add', 'test-workflow', 'Test reason', datetime('now'))
        """
    )

    # Invalid epic_num (should fail)
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO workflow_adjustments
            (epic_num, learning_id, adjustment_type, workflow_name, reason, applied_at)
            VALUES (999, 1, 'add', 'test-workflow', 'Test reason', datetime('now'))
            """
        )

    conn.close()


def test_migration_up_check_constraint(temp_db):
    """Test that adjustment_type check constraint works."""
    conn = sqlite3.connect(str(temp_db))

    # Apply migration
    Migration007.up(conn)

    cursor = conn.cursor()

    # Valid adjustment_type
    cursor.execute(
        """
        INSERT INTO workflow_adjustments
        (epic_num, adjustment_type, workflow_name, reason, applied_at)
        VALUES (29, 'add', 'test-workflow', 'Test reason', datetime('now'))
        """
    )

    # Invalid adjustment_type
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO workflow_adjustments
            (epic_num, adjustment_type, workflow_name, reason, applied_at)
            VALUES (29, 'invalid_type', 'test-workflow', 'Test reason', datetime('now'))
            """
        )

    conn.close()


# Tests: Migration Down


def test_migration_down_removes_table(temp_db):
    """Test that migration down removes workflow_adjustments table."""
    conn = sqlite3.connect(str(temp_db))

    # Apply migration
    Migration007.up(conn)

    # Rollback migration
    Migration007.down(conn)

    # Check table doesn't exist
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='workflow_adjustments'
        """
    )
    result = cursor.fetchone()

    assert result is None

    conn.close()


def test_migration_down_removes_indexes(temp_db):
    """Test that migration down removes all indexes."""
    conn = sqlite3.connect(str(temp_db))

    # Apply migration
    Migration007.up(conn)

    # Rollback migration
    Migration007.down(conn)

    # Check indexes don't exist
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cursor.fetchall()]

    migration_indexes = [
        "idx_workflow_adjustments_epic",
        "idx_workflow_adjustments_learning",
        "idx_workflow_adjustments_type",
        "idx_workflow_adjustments_applied_at",
        "idx_workflow_adjustments_epic_time",
    ]

    for idx in migration_indexes:
        assert idx not in indexes

    conn.close()


def test_migration_down_removes_version(temp_db):
    """Test that migration down removes version from schema_version."""
    conn = sqlite3.connect(str(temp_db))

    # Apply migration
    Migration007.up(conn)

    # Rollback migration
    Migration007.down(conn)

    # Check version not recorded
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM schema_version WHERE version = ?", (Migration007.VERSION,))
    result = cursor.fetchone()

    assert result is None

    conn.close()


# Tests: is_applied


def test_is_applied_returns_false_before_migration(temp_db):
    """Test is_applied returns False before migration."""
    conn = sqlite3.connect(str(temp_db))

    assert Migration007.is_applied(conn) is False

    conn.close()


def test_is_applied_returns_true_after_migration(temp_db):
    """Test is_applied returns True after migration."""
    conn = sqlite3.connect(str(temp_db))

    Migration007.up(conn)

    assert Migration007.is_applied(conn) is True

    conn.close()


def test_is_applied_returns_false_after_rollback(temp_db):
    """Test is_applied returns False after rollback."""
    conn = sqlite3.connect(str(temp_db))

    Migration007.up(conn)
    Migration007.down(conn)

    assert Migration007.is_applied(conn) is False

    conn.close()


# Tests: verify


def test_verify_before_migration(temp_db):
    """Test verify before migration shows not applied."""
    conn = sqlite3.connect(str(temp_db))

    result = Migration007.verify(conn)

    assert result["applied"] is False
    assert result["table_exists"] is False

    conn.close()


def test_verify_after_migration(temp_db):
    """Test verify after migration shows no issues."""
    conn = sqlite3.connect(str(temp_db))

    Migration007.up(conn)

    result = Migration007.verify(conn)

    assert result["applied"] is True
    assert result["table_exists"] is True
    assert len(result["columns"]) == 8
    assert len(result["indexes"]) == 5
    assert len(result["issues"]) == 0

    conn.close()


def test_verify_detects_missing_table(temp_db):
    """Test verify detects missing table."""
    conn = sqlite3.connect(str(temp_db))

    # Record version but don't create table (simulating partial migration)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO schema_version (version, applied_at, description)
        VALUES (?, datetime('now'), ?)
        """,
        (Migration007.VERSION, Migration007.DESCRIPTION),
    )
    conn.commit()

    result = Migration007.verify(conn)

    assert result["applied"] is True
    assert result["table_exists"] is False
    assert any("table does not exist" in issue.lower() for issue in result["issues"])

    conn.close()


# Tests: run_migration


def test_run_migration_up_direction(temp_db):
    """Test run_migration with up direction."""
    result = run_migration(db_path=temp_db, direction="up", backup=False)

    assert result["success"] is True
    assert result["direction"] == "up"


def test_run_migration_down_direction(temp_db):
    """Test run_migration with down direction."""
    # Apply migration first
    conn = sqlite3.connect(str(temp_db))
    Migration007.up(conn)
    conn.close()

    # Rollback
    result = run_migration(db_path=temp_db, direction="down", backup=False)

    assert result["success"] is True
    assert result["direction"] == "down"


def test_run_migration_verify_direction(temp_db):
    """Test run_migration with verify direction."""
    # Apply migration first
    conn = sqlite3.connect(str(temp_db))
    Migration007.up(conn)
    conn.close()

    # Verify
    result = run_migration(db_path=temp_db, direction="verify", backup=False)

    assert result["success"] is True
    assert result["direction"] == "verify"
    assert "verification" in result
    assert len(result["verification"]["issues"]) == 0


def test_run_migration_dry_run(temp_db):
    """Test run_migration with dry_run."""
    result = run_migration(db_path=temp_db, direction="up", backup=False, dry_run=True)

    assert result["success"] is True
    assert result["dry_run"] is True
    assert result["would_apply"] is True

    # Migration should not actually be applied
    conn = sqlite3.connect(str(temp_db))
    assert Migration007.is_applied(conn) is False
    conn.close()


def test_run_migration_invalid_direction(temp_db):
    """Test run_migration with invalid direction."""
    with pytest.raises(ValueError):
        run_migration(db_path=temp_db, direction="invalid", backup=False)


def test_run_migration_nonexistent_db():
    """Test run_migration with nonexistent database."""
    with pytest.raises(FileNotFoundError):
        run_migration(db_path=Path("/nonexistent/db.sqlite"), direction="up")


# Tests: Idempotency


def test_migration_up_idempotent(temp_db):
    """Test that applying migration twice is safe."""
    conn = sqlite3.connect(str(temp_db))

    # Apply twice
    Migration007.up(conn)
    Migration007.up(conn)  # Should not raise

    # Should still be valid
    result = Migration007.verify(conn)
    assert len(result["issues"]) == 0

    conn.close()


def test_migration_down_idempotent(temp_db):
    """Test that rolling back twice is safe."""
    conn = sqlite3.connect(str(temp_db))

    # Apply migration
    Migration007.up(conn)

    # Rollback twice
    Migration007.down(conn)
    Migration007.down(conn)  # Should not raise

    # Should not be applied
    assert Migration007.is_applied(conn) is False

    conn.close()
