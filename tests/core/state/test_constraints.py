"""Tests for database constraints.

Tests verify:
- UNIQUE constraints prevent duplicates
- CHECK constraints reject invalid values
- NOT NULL constraints reject null values
- DEFAULT values applied correctly
- Foreign key constraints enforced
- CASCADE operations work correctly
"""

import sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from gao_dev.core.state.migrations.migration_001_create_state_schema import (
    Migration001,
)
from .conftest import safe_cleanup_db


class TestConstraints:
    """Tests for database constraints."""

    @pytest.fixture
    def db(self):
        """Create a temporary database with schema."""
        with NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        Migration001.upgrade(db_path)

        yield db_path

        # Cleanup
        safe_cleanup_db(db_path)

    def test_epic_unique_constraint(self, db):
        """Test UNIQUE constraint on epics.epic_num prevents duplicates."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Insert first epic
            conn.execute(
                "INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')"
            )

            # Try to insert duplicate epic_num
            with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint"):
                conn.execute(
                    "INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 2')"
                )

    def test_story_unique_constraint(self, db):
        """Test UNIQUE constraint on (epic_num, story_num) prevents duplicates."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic first
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')")

            # Insert first story
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title) VALUES (1, 1, 'Story 1')"
            )

            # Try to insert duplicate (epic_num, story_num)
            with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint"):
                conn.execute(
                    "INSERT INTO stories (epic_num, story_num, title) VALUES (1, 1, 'Story 2')"
                )

    def test_epic_status_check_constraint(self, db):
        """Test CHECK constraint on epic status rejects invalid values."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Valid statuses should work
            conn.execute(
                "INSERT INTO epics (epic_num, name, status) VALUES (1, 'Epic 1', 'planned')"
            )
            conn.execute(
                "INSERT INTO epics (epic_num, name, status) VALUES (2, 'Epic 2', 'active')"
            )
            conn.execute(
                "INSERT INTO epics (epic_num, name, status) VALUES (3, 'Epic 3', 'completed')"
            )
            conn.execute(
                "INSERT INTO epics (epic_num, name, status) VALUES (4, 'Epic 4', 'cancelled')"
            )

            # Invalid status should fail
            with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
                conn.execute(
                    "INSERT INTO epics (epic_num, name, status) VALUES (5, 'Epic 5', 'invalid')"
                )

    def test_story_status_check_constraint(self, db):
        """Test CHECK constraint on story status rejects invalid values."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')")

            # Valid statuses should work
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, status) VALUES (1, 1, 'Story 1', 'pending')"
            )
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, status) VALUES (1, 2, 'Story 2', 'in_progress')"
            )
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, status) VALUES (1, 3, 'Story 3', 'done')"
            )
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, status) VALUES (1, 4, 'Story 4', 'blocked')"
            )
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, status) VALUES (1, 5, 'Story 5', 'cancelled')"
            )

            # Invalid status should fail
            with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
                conn.execute(
                    "INSERT INTO stories (epic_num, story_num, title, status) VALUES (1, 6, 'Story 6', 'invalid')"
                )

    def test_story_priority_check_constraint(self, db):
        """Test CHECK constraint on story priority rejects invalid values."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')")

            # Valid priorities should work
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, priority) VALUES (1, 1, 'Story 1', 'P0')"
            )
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, priority) VALUES (1, 2, 'Story 2', 'P1')"
            )
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, priority) VALUES (1, 3, 'Story 3', 'P2')"
            )
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title, priority) VALUES (1, 4, 'Story 4', 'P3')"
            )

            # Invalid priority should fail
            with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
                conn.execute(
                    "INSERT INTO stories (epic_num, story_num, title, priority) VALUES (1, 5, 'Story 5', 'P4')"
                )

    def test_sprint_date_check_constraint(self, db):
        """Test CHECK constraint on sprint dates (end > start) rejects invalid dates."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Valid dates should work
            conn.execute(
                "INSERT INTO sprints (sprint_num, name, start_date, end_date) "
                "VALUES (1, 'Sprint 1', '2025-01-01', '2025-01-15')"
            )

            # end_date <= start_date should fail
            with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
                conn.execute(
                    "INSERT INTO sprints (sprint_num, name, start_date, end_date) "
                    "VALUES (2, 'Sprint 2', '2025-01-15', '2025-01-01')"
                )

            # Equal dates should also fail
            with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
                conn.execute(
                    "INSERT INTO sprints (sprint_num, name, start_date, end_date) "
                    "VALUES (3, 'Sprint 3', '2025-01-01', '2025-01-01')"
                )

    def test_default_values(self, db):
        """Test DEFAULT values applied correctly."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Insert epic with minimal data
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')")

            cursor = conn.execute("SELECT status, total_points, completed_points FROM epics WHERE epic_num = 1")
            row = cursor.fetchone()

            assert row[0] == "planned"  # Default status
            assert row[1] == 0  # Default total_points
            assert row[2] == 0  # Default completed_points

    def test_not_null_constraints(self, db):
        """Test NOT NULL constraints reject null values."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # epic_num is NOT NULL
            with pytest.raises(sqlite3.IntegrityError, match="NOT NULL constraint"):
                conn.execute("INSERT INTO epics (name) VALUES ('Epic 1')")

            # name is NOT NULL
            with pytest.raises(sqlite3.IntegrityError, match="NOT NULL constraint"):
                conn.execute("INSERT INTO epics (epic_num) VALUES (1)")

    def test_foreign_key_constraint(self, db):
        """Test foreign key constraints enforced."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Try to insert story without epic
            with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint"):
                conn.execute(
                    "INSERT INTO stories (epic_num, story_num, title) VALUES (999, 1, 'Story 1')"
                )

    def test_cascade_delete_epic_stories(self, db):
        """Test CASCADE DELETE on epic removes associated stories."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic and stories
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')")
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title) VALUES (1, 1, 'Story 1')"
            )
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title) VALUES (1, 2, 'Story 2')"
            )

            # Delete epic
            conn.execute("DELETE FROM epics WHERE epic_num = 1")

            # Verify stories deleted
            cursor = conn.execute("SELECT COUNT(*) FROM stories WHERE epic_num = 1")
            count = cursor.fetchone()[0]
            assert count == 0

    def test_cascade_update_epic_num(self, db):
        """Test CASCADE UPDATE on epic_num propagates to stories."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic and story
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')")
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title) VALUES (1, 1, 'Story 1')"
            )

            # Update epic_num
            conn.execute("UPDATE epics SET epic_num = 2 WHERE epic_num = 1")

            # Verify story epic_num updated
            cursor = conn.execute("SELECT epic_num FROM stories WHERE story_num = 1")
            epic_num = cursor.fetchone()[0]
            assert epic_num == 2

    def test_cascade_delete_sprint_assignments(self, db):
        """Test CASCADE DELETE on sprint removes story_assignments."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create epic, story, sprint, assignment
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Epic 1')")
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title) VALUES (1, 1, 'Story 1')"
            )
            conn.execute(
                "INSERT INTO sprints (sprint_num, name, start_date, end_date) "
                "VALUES (1, 'Sprint 1', '2025-01-01', '2025-01-15')"
            )
            conn.execute(
                "INSERT INTO story_assignments (sprint_num, epic_num, story_num) VALUES (1, 1, 1)"
            )

            # Delete sprint
            conn.execute("DELETE FROM sprints WHERE sprint_num = 1")

            # Verify assignment deleted
            cursor = conn.execute("SELECT COUNT(*) FROM story_assignments WHERE sprint_num = 1")
            count = cursor.fetchone()[0]
            assert count == 0

    def test_workflow_execution_status_check(self, db):
        """Test CHECK constraint on workflow_execution status."""
        with sqlite3.connect(str(db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Valid statuses
            conn.execute(
                "INSERT INTO workflow_executions (workflow_name, executor, status) "
                "VALUES ('test', 'Amelia', 'started')"
            )
            conn.execute(
                "INSERT INTO workflow_executions (workflow_name, executor, status) "
                "VALUES ('test', 'Amelia', 'running')"
            )
            conn.execute(
                "INSERT INTO workflow_executions (workflow_name, executor, status) "
                "VALUES ('test', 'Amelia', 'completed')"
            )
            conn.execute(
                "INSERT INTO workflow_executions (workflow_name, executor, status) "
                "VALUES ('test', 'Amelia', 'failed')"
            )
            conn.execute(
                "INSERT INTO workflow_executions (workflow_name, executor, status) "
                "VALUES ('test', 'Amelia', 'cancelled')"
            )

            # Invalid status should fail
            with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
                conn.execute(
                    "INSERT INTO workflow_executions (workflow_name, executor, status) "
                    "VALUES ('test', 'Amelia', 'invalid')"
                )
