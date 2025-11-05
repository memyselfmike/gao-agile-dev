"""Tests for QueryBuilder."""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime

from gao_dev.core.state.query_builder import QueryBuilder
from gao_dev.core.state.state_tracker import StateTracker
from gao_dev.core.state.exceptions import RecordNotFoundError


@pytest.fixture
def db_path(tmp_path):
    """Create temporary database with schema."""
    db_file = tmp_path / "test_state.db"

    # Create schema
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE epics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epic_num INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            feature TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            total_points INTEGER DEFAULT 0,
            completed_points INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epic_num INTEGER NOT NULL,
            story_num INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            owner TEXT,
            points INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'P1',
            content_hash TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(epic_num, story_num),
            FOREIGN KEY (epic_num) REFERENCES epics(epic_num)
        )
    """)

    cursor.execute("""
        CREATE TABLE sprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sprint_num INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE story_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sprint_num INTEGER NOT NULL,
            epic_num INTEGER NOT NULL,
            story_num INTEGER NOT NULL,
            assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(epic_num, story_num),
            FOREIGN KEY (sprint_num) REFERENCES sprints(sprint_num),
            FOREIGN KEY (epic_num, story_num) REFERENCES stories(epic_num, story_num)
        )
    """)

    cursor.execute("""
        CREATE TABLE workflow_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_name TEXT NOT NULL,
            epic_num INTEGER NOT NULL,
            story_num INTEGER NOT NULL,
            status TEXT NOT NULL,
            executor TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            duration_ms INTEGER,
            output TEXT
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX idx_stories_status ON stories(status)")
    cursor.execute("CREATE INDEX idx_stories_epic ON stories(epic_num)")
    cursor.execute("CREATE INDEX idx_epics_status ON epics(status)")

    conn.commit()
    conn.close()

    return db_file


@pytest.fixture
def tracker(db_path):
    """Create StateTracker with test database."""
    return StateTracker(db_path)


@pytest.fixture
def builder(tracker):
    """Create QueryBuilder."""
    return QueryBuilder(tracker)


@pytest.fixture
def sample_data(tracker):
    """Create sample data for testing."""
    now = datetime.now().isoformat()

    # Create epics
    tracker.create_epic(15, "State Tracking Database", "document-lifecycle-system", 20)
    tracker.create_epic(16, "Document Templates", "document-lifecycle-system", 15)

    # Create sprint
    tracker.create_sprint(5, "2025-11-01", "2025-11-15")

    # Create stories for epic 15
    tracker.create_story(15, 1, "Schema Design", status="done", points=3, sprint=5)
    tracker.create_story(15, 2, "StateTracker Implementation", status="done", points=5, sprint=5)
    tracker.create_story(15, 3, "Markdown Syncer", status="done", points=5, sprint=5)
    tracker.create_story(15, 4, "Query Builder", status="in_progress", points=4, sprint=5, owner="Amelia")
    tracker.create_story(15, 5, "Import Existing Data", status="pending", points=5)
    tracker.create_story(15, 6, "CLI Commands", status="blocked", points=3, owner="Bob")

    # Create stories for epic 16
    tracker.create_story(16, 1, "Template Engine", status="pending", points=5)
    tracker.create_story(16, 2, "Variable Substitution", status="in_progress", points=3, owner="Amelia")

    # Update epic points
    tracker.update_epic_points(15, 25, 13)
    tracker.update_epic_points(16, 15, 0)

    return tracker


class TestConvenienceMethods:
    """Test convenience query methods."""

    def test_get_stories_by_status(self, builder, sample_data):
        """Test getting stories by status."""
        # Get all in_progress stories
        stories = builder.get_stories_by_status("in_progress")
        assert len(stories) == 2
        assert all(s.status == "in_progress" for s in stories)

        # Get in_progress stories from epic 15 only
        stories = builder.get_stories_by_status("in_progress", epic_num=15)
        assert len(stories) == 1
        assert stories[0].epic == 15
        assert stories[0].story_num == 4

    def test_get_stories_by_status_with_pagination(self, builder, sample_data):
        """Test pagination in get_stories_by_status."""
        # Get first 2 done stories
        stories = builder.get_stories_by_status("done", limit=2)
        assert len(stories) == 2

        # Get next 1 done story
        stories = builder.get_stories_by_status("done", limit=2, offset=2)
        assert len(stories) == 1

    def test_get_stories_by_status_as_dict(self, builder, sample_data):
        """Test dict output format."""
        stories = builder.get_stories_by_status("done", as_dict=True)
        assert len(stories) > 0
        assert isinstance(stories[0], dict)
        assert "full_id" in stories[0]
        assert "title" in stories[0]
        assert stories[0]["status"] == "done"

    def test_get_epic_progress(self, builder, sample_data):
        """Test epic progress calculation."""
        progress = builder.get_epic_progress(15)

        assert progress["epic_num"] == 15
        assert progress["total"] == 25
        assert progress["completed"] == 13
        assert progress["percentage"] == 52.0
        assert progress["stories_done"] == 3
        assert progress["stories_total"] == 6

    def test_get_epic_progress_not_found(self, builder, sample_data):
        """Test epic progress with non-existent epic."""
        with pytest.raises(RecordNotFoundError):
            builder.get_epic_progress(999)

    def test_get_sprint_velocity(self, builder, sample_data):
        """Test sprint velocity calculation."""
        velocity = builder.get_sprint_velocity(5)
        # Only stories with status='done' count: 3+5+5=13
        assert velocity == 13

    def test_get_sprint_velocity_not_found(self, builder, sample_data):
        """Test sprint velocity with non-existent sprint."""
        with pytest.raises(RecordNotFoundError):
            builder.get_sprint_velocity(999)

    def test_get_blocked_stories(self, builder, sample_data):
        """Test getting blocked stories."""
        blocked = builder.get_blocked_stories()
        assert len(blocked) == 1
        assert blocked[0].status == "blocked"
        assert blocked[0].epic == 15
        assert blocked[0].story_num == 6

    def test_get_blocked_stories_as_dict(self, builder, sample_data):
        """Test blocked stories as dict."""
        blocked = builder.get_blocked_stories(as_dict=True)
        assert len(blocked) == 1
        assert isinstance(blocked[0], dict)
        assert blocked[0]["status"] == "blocked"

    def test_get_stories_needing_review(self, builder, sample_data):
        """Test getting stories needing review."""
        # Stories with status='done' are candidates for review
        review = builder.get_stories_needing_review()
        assert len(review) == 3
        assert all(s.status == "done" for s in review)

    def test_get_stories_needing_review_pagination(self, builder, sample_data):
        """Test review queue with pagination."""
        review = builder.get_stories_needing_review(limit=2)
        assert len(review) == 2


class TestAdvancedQueries:
    """Test advanced query methods."""

    def test_get_sprint_summary(self, builder, sample_data):
        """Test comprehensive sprint summary."""
        summary = builder.get_sprint_summary(5)

        assert summary["sprint_num"] == 5
        assert summary["sprint_name"] == "Sprint 5"
        assert summary["velocity"] == 13  # Completed points
        assert summary["total_points"] == 17  # 3+5+5+4
        assert summary["completed_points"] == 13
        assert summary["remaining_points"] == 4
        assert summary["stories_done"] == 3
        assert summary["stories_total"] == 4
        assert summary["stories_in_progress"] == 1
        assert summary["stories_blocked"] == 0

    def test_get_epic_summary(self, builder, sample_data):
        """Test comprehensive epic summary."""
        summary = builder.get_epic_summary(15)

        assert summary["epic_num"] == 15
        assert summary["title"] == "State Tracking Database"
        assert summary["feature"] == "document-lifecycle-system"
        assert summary["status"] == "active"
        assert summary["progress"] == 52.0
        assert summary["total_points"] == 25
        assert summary["completed_points"] == 13
        assert summary["stories_total"] == 6
        assert summary["stories_done"] == 3
        assert summary["stories_in_progress"] == 1
        assert summary["stories_blocked"] == 1
        assert summary["stories_pending"] == 1
        assert summary["velocity"] == 0.5  # 3/6 stories done

    def test_get_all_active_work(self, builder, sample_data):
        """Test getting all active work."""
        work = builder.get_all_active_work()

        assert len(work["stories_in_progress"]) == 2
        assert len(work["stories_blocked"]) == 1
        assert len(work["active_epics"]) == 2
        assert "current_sprint" in work
        assert work["current_sprint"]["sprint_num"] == 5


class TestPerformance:
    """Test query performance and optimization."""

    def test_query_uses_indexes(self, builder, sample_data, db_path):
        """Test that queries use indexes (EXPLAIN QUERY PLAN)."""
        # Connect to database and check query plan
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check that status query uses index
        cursor.execute("""
            EXPLAIN QUERY PLAN
            SELECT * FROM stories WHERE status = 'done'
        """)
        plan = cursor.fetchall()
        plan_text = " ".join(str(row) for row in plan)

        # Should use idx_stories_status index
        assert "idx_stories_status" in plan_text or "USING INDEX" in plan_text

        conn.close()

    def test_pagination_limits_results(self, builder, sample_data):
        """Test that pagination properly limits results."""
        # Get limited results
        stories = builder.get_stories_by_status("done", limit=2)
        assert len(stories) == 2

        # Get with offset
        stories = builder.get_stories_by_status("done", limit=1, offset=1)
        assert len(stories) == 1


class TestHelperMethods:
    """Test helper methods for result formatting."""

    def test_story_to_dict(self, builder, sample_data):
        """Test Story to dict conversion."""
        story = sample_data.get_story(15, 1)
        story_dict = builder._story_to_dict(story)

        assert story_dict["id"] == story.id
        assert story_dict["epic"] == 15
        assert story_dict["story_num"] == 1
        assert story_dict["full_id"] == "15.1"
        assert story_dict["title"] == "Schema Design"
        assert story_dict["status"] == "done"
        assert story_dict["points"] == 3

    def test_epic_to_dict(self, builder, sample_data):
        """Test Epic to dict conversion."""
        epic = sample_data.get_epic(15)
        epic_dict = builder._epic_to_dict(epic)

        assert epic_dict["id"] == epic.id
        assert epic_dict["epic_num"] == 15
        assert epic_dict["title"] == "State Tracking Database"
        assert epic_dict["feature"] == "document-lifecycle-system"
        assert epic_dict["status"] == "active"
        assert epic_dict["progress"] == 52.0

    def test_sprint_to_dict(self, builder, sample_data):
        """Test Sprint to dict conversion."""
        sprint = sample_data.get_sprint(5)
        sprint_dict = builder._sprint_to_dict(sprint)

        assert sprint_dict["id"] == sprint.id
        assert sprint_dict["sprint_num"] == 5
        assert sprint_dict["name"] == "Sprint 5"
        assert sprint_dict["status"] == "active"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_status_query(self, builder, sample_data):
        """Test query with status that has no results."""
        stories = builder.get_stories_by_status("cancelled")
        assert len(stories) == 0

    def test_epic_with_no_stories(self, builder, tracker):
        """Test epic summary with no stories."""
        # Create epic with no stories
        tracker.create_epic(99, "Empty Epic", "test-feature", 0)

        summary = builder.get_epic_summary(99)
        assert summary["stories_total"] == 0
        assert summary["stories_done"] == 0
        assert summary["velocity"] == 0.0

    def test_sprint_with_no_stories(self, builder, tracker):
        """Test sprint summary with no stories."""
        # Create sprint with no stories
        tracker.create_sprint(99, "2025-12-01", "2025-12-15")

        summary = builder.get_sprint_summary(99)
        assert summary["stories_total"] == 0
        assert summary["velocity"] == 0

    def test_no_active_epics(self, builder, tracker):
        """Test all active work with no active epics."""
        # Create only completed epic
        tracker.create_epic(99, "Completed Epic", "test", 10)
        tracker.update_epic_status(99, "completed")

        work = builder.get_all_active_work()
        assert len(work["active_epics"]) == 0

    def test_no_current_sprint(self, builder, tracker):
        """Test all active work with no current sprint."""
        # Create only completed sprint
        tracker.create_sprint(99, "2025-12-01", "2025-12-15")

        # Mark as completed (need to access DB directly for this)
        with tracker._get_connection() as conn:
            conn.execute("UPDATE sprints SET status = 'completed' WHERE sprint_num = ?", (99,))

        work = builder.get_all_active_work()
        assert "current_sprint" not in work or work["current_sprint"] is None
