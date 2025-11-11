"""Tests for database triggers.

Tests verify:
- updated_at timestamp auto-updated on UPDATE
- epic.completed_points auto-calculated when story status changes
- state_changes audit log records status changes
- Triggers don't fire on INSERT inappropriately
- Trigger performance overhead <5ms
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


class TestTriggers:
    """Tests for database triggers."""

    @pytest.fixture
    def db(self):
        """Create a temporary database with schema."""
        with NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        Migration001.upgrade(db_path)

        yield db_path

        # Cleanup
        safe_cleanup_db(db_path)

    def test_epic_updated_at_trigger(self, db):
        """Test updated_at timestamp auto-updated on epic UPDATE."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Insert epic
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')")

            # Get initial updated_at
            cursor = conn.execute("SELECT updated_at FROM epics WHERE epic_num = 1")
            initial_updated_at = cursor.fetchone()[0]

            # Wait to ensure timestamp changes (SQLite datetime('now') has 1-second precision)
            time.sleep(1.01)

            # Update epic
            conn.execute("UPDATE epics SET name = 'Epic 1 Updated' WHERE epic_num = 1")

            # Get new updated_at
            cursor = conn.execute("SELECT updated_at FROM epics WHERE epic_num = 1")
            new_updated_at = cursor.fetchone()[0]

            # Verify updated_at changed
            assert new_updated_at > initial_updated_at

    def test_story_updated_at_trigger(self, db):
        """Test updated_at timestamp auto-updated on story UPDATE."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic and story
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')")
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title) VALUES (1, 1, 'Story 1')"
            )

            # Get initial updated_at
            cursor = conn.execute("SELECT updated_at FROM stories WHERE story_num = 1")
            initial_updated_at = cursor.fetchone()[0]

            # Wait to ensure timestamp changes (SQLite datetime('now') has 1-second precision)
            time.sleep(1.01)

            # Update story
            conn.execute(
                "UPDATE stories SET title = 'Story 1 Updated' WHERE story_num = 1"
            )

            # Get new updated_at
            cursor = conn.execute("SELECT updated_at FROM stories WHERE story_num = 1")
            new_updated_at = cursor.fetchone()[0]

            # Verify updated_at changed
            assert new_updated_at > initial_updated_at

    def test_sprint_updated_at_trigger(self, db):
        """Test updated_at timestamp auto-updated on sprint UPDATE."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Insert sprint
            conn.execute(
                "INSERT INTO sprints (sprint_num, name, start_date, end_date) "
                "VALUES (1, 'Sprint 1', '2025-01-01', '2025-01-15')"
            )

            # Get initial updated_at
            cursor = conn.execute("SELECT updated_at FROM sprints WHERE sprint_num = 1")
            initial_updated_at = cursor.fetchone()[0]

            # Wait to ensure timestamp changes (SQLite datetime('now') has 1-second precision)
            time.sleep(1.01)

            # Update sprint
            conn.execute("UPDATE sprints SET name = 'Sprint 1 Updated' WHERE sprint_num = 1")

            # Get new updated_at
            cursor = conn.execute("SELECT updated_at FROM sprints WHERE sprint_num = 1")
            new_updated_at = cursor.fetchone()[0]

            # Verify updated_at changed
            assert new_updated_at > initial_updated_at

    def test_epic_points_calculated_on_story_done(self, db):
        """Test epic.completed_points auto-calculated when story status changes to done."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic and stories
            conn.execute("INSERT INTO epics (epic_num, name, total_points) VALUES (1, 'Epic 1', 15)")
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, points, status) "
                "VALUES (1, 1, 'Story 1', 5, 'pending')"
            )
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, points, status) "
                "VALUES (1, 2, 'Story 2', 3, 'pending')"
            )
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, points, status) "
                "VALUES (1, 3, 'Story 3', 7, 'pending')"
            )

            # Initially, completed_points should be 0
            cursor = conn.execute("SELECT completed_points FROM epics WHERE epic_num = 1")
            assert cursor.fetchone()[0] == 0

            # Mark first story as done
            conn.execute("UPDATE stories SET status = 'done' WHERE story_num = 1")

            # completed_points should be 5
            cursor = conn.execute("SELECT completed_points FROM epics WHERE epic_num = 1")
            assert cursor.fetchone()[0] == 5

            # Mark second story as done
            conn.execute("UPDATE stories SET status = 'done' WHERE story_num = 2")

            # completed_points should be 8 (5 + 3)
            cursor = conn.execute("SELECT completed_points FROM epics WHERE epic_num = 1")
            assert cursor.fetchone()[0] == 8

            # Mark third story as done
            conn.execute("UPDATE stories SET status = 'done' WHERE story_num = 3")

            # completed_points should be 15 (5 + 3 + 7)
            cursor = conn.execute("SELECT completed_points FROM epics WHERE epic_num = 1")
            assert cursor.fetchone()[0] == 15

    def test_epic_points_recalculated_on_story_revert(self, db):
        """Test epic.completed_points recalculated when story changes from done to other status."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic and stories
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')")
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, points, status) "
                "VALUES (1, 1, 'Story 1', 5, 'done')"
            )
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, points, status) "
                "VALUES (1, 2, 'Story 2', 3, 'done')"
            )

            # Initially, completed_points should be 8
            cursor = conn.execute("SELECT completed_points FROM epics WHERE epic_num = 1")
            assert cursor.fetchone()[0] == 8

            # Revert first story to in_progress
            conn.execute("UPDATE stories SET status = 'in_progress' WHERE story_num = 1")

            # completed_points should be 3
            cursor = conn.execute("SELECT completed_points FROM epics WHERE epic_num = 1")
            assert cursor.fetchone()[0] == 3

            # Revert second story to pending
            conn.execute("UPDATE stories SET status = 'pending' WHERE story_num = 2")

            # completed_points should be 0
            cursor = conn.execute("SELECT completed_points FROM epics WHERE epic_num = 1")
            assert cursor.fetchone()[0] == 0

    def test_story_status_change_logged(self, db):
        """Test state_changes audit log records story status changes."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic and story
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')")
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, status) "
                "VALUES (1, 1, 'Story 1', 'pending')"
            )

            # Get story id
            cursor = conn.execute("SELECT id FROM stories WHERE story_num = 1")
            story_id = cursor.fetchone()[0]

            # Change status
            conn.execute("UPDATE stories SET status = 'in_progress' WHERE story_num = 1")

            # Check audit log
            cursor = conn.execute(
                "SELECT field_name, old_value, new_value, changed_by FROM state_changes "
                "WHERE table_name = 'stories' AND record_id = ? AND field_name = 'status'",
                (story_id,)
            )
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == "status"
            assert row[1] == "pending"
            assert row[2] == "in_progress"
            assert row[3] == "system"

    def test_epic_status_change_logged(self, db):
        """Test state_changes audit log records epic status changes."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic
            conn.execute("INSERT INTO epics (epic_num, name, status) VALUES (1, 'Epic 1', 'planned')")

            # Get epic id
            cursor = conn.execute("SELECT id FROM epics WHERE epic_num = 1")
            epic_id = cursor.fetchone()[0]

            # Change status
            conn.execute("UPDATE epics SET status = 'active' WHERE epic_num = 1")

            # Check audit log
            cursor = conn.execute(
                "SELECT field_name, old_value, new_value FROM state_changes "
                "WHERE table_name = 'epics' AND record_id = ? AND field_name = 'status'",
                (epic_id,)
            )
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == "status"
            assert row[1] == "planned"
            assert row[2] == "active"

    def test_sprint_status_change_logged(self, db):
        """Test state_changes audit log records sprint status changes."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create sprint
            conn.execute(
                "INSERT INTO sprints (sprint_num, name, start_date, end_date, status) "
                "VALUES (1, 'Sprint 1', '2025-01-01', '2025-01-15', 'planned')"
            )

            # Get sprint id
            cursor = conn.execute("SELECT id FROM sprints WHERE sprint_num = 1")
            sprint_id = cursor.fetchone()[0]

            # Change status
            conn.execute("UPDATE sprints SET status = 'active' WHERE sprint_num = 1")

            # Check audit log
            cursor = conn.execute(
                "SELECT field_name, old_value, new_value FROM state_changes "
                "WHERE table_name = 'sprints' AND record_id = ? AND field_name = 'status'",
                (sprint_id,)
            )
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == "status"
            assert row[1] == "planned"
            assert row[2] == "active"

    def test_audit_log_not_triggered_on_insert(self, db):
        """Test triggers don't fire on INSERT (only UPDATE)."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic
            conn.execute("INSERT INTO epics (epic_num, name, status) VALUES (1, 'Epic 1', 'active')")

            # Get epic id
            cursor = conn.execute("SELECT id FROM epics WHERE epic_num = 1")
            epic_id = cursor.fetchone()[0]

            # Check audit log - should be empty for INSERT
            cursor = conn.execute(
                "SELECT COUNT(*) FROM state_changes WHERE table_name = 'epics' AND record_id = ?",
                (epic_id,)
            )
            count = cursor.fetchone()[0]

            assert count == 0

    def test_trigger_performance(self, db):
        """Test trigger performance overhead <5ms."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic and story
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')")
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, points, status) "
                "VALUES (1, 1, 'Story 1', 5, 'pending')"
            )

            # Measure time for status update (triggers timestamp update, points calculation, audit log)
            start_time = time.perf_counter()
            conn.execute("UPDATE stories SET status = 'done' WHERE story_num = 1")
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Should complete in <5ms
            assert duration_ms < 5, f"Trigger overhead {duration_ms:.2f}ms (expected <5ms)"

    def test_multiple_status_changes_logged(self, db):
        """Test multiple status changes create multiple audit entries."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic and story
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')")
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, status) "
                "VALUES (1, 1, 'Story 1', 'pending')"
            )

            # Get story id
            cursor = conn.execute("SELECT id FROM stories WHERE story_num = 1")
            story_id = cursor.fetchone()[0]

            # Multiple status changes
            conn.execute("UPDATE stories SET status = 'in_progress' WHERE story_num = 1")
            conn.execute("UPDATE stories SET status = 'blocked' WHERE story_num = 1")
            conn.execute("UPDATE stories SET status = 'in_progress' WHERE story_num = 1")
            conn.execute("UPDATE stories SET status = 'done' WHERE story_num = 1")

            # Check audit log count
            cursor = conn.execute(
                "SELECT COUNT(*) FROM state_changes "
                "WHERE table_name = 'stories' AND record_id = ? AND field_name = 'status'",
                (story_id,)
            )
            count = cursor.fetchone()[0]

            # Should have 4 entries
            assert count == 4

            # Verify sequence
            cursor = conn.execute(
                "SELECT old_value, new_value FROM state_changes "
                "WHERE table_name = 'stories' AND record_id = ? AND field_name = 'status' "
                "ORDER BY changed_at",
                (story_id,)
            )
            changes = cursor.fetchall()

            assert changes[0] == ("pending", "in_progress")
            assert changes[1] == ("in_progress", "blocked")
            assert changes[2] == ("blocked", "in_progress")
            assert changes[3] == ("in_progress", "done")
