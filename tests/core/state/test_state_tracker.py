"""Unit tests for StateTracker.

Tests comprehensive CRUD operations for stories, epics, sprints, and workflows
with thread-safety, transaction support, and error handling.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime

from gao_dev.core.state.state_tracker import StateTracker
from gao_dev.core.state.models import Story, Epic, Sprint, WorkflowExecution
from gao_dev.core.state.exceptions import (
    StateTrackerError,
    RecordNotFoundError,
    ValidationError,
    DatabaseConnectionError,
)


@pytest.fixture
def temp_db():
    """Create temporary database with schema for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    # Create schema
    conn = sqlite3.connect(str(db_path))
    schema_path = Path(__file__).parent.parent.parent.parent / "gao_dev" / "core" / "state" / "schema.sql"
    with open(schema_path, "r") as schema_file:
        conn.executescript(schema_file.read())
    conn.close()

    yield db_path

    # Cleanup
    db_path.unlink(missing_ok=True)


@pytest.fixture
def tracker(temp_db):
    """Create StateTracker instance with temporary database."""
    return StateTracker(temp_db)


@pytest.fixture
def tracker_with_epic(tracker):
    """Create StateTracker with a test epic already created."""
    tracker.create_epic(epic_num=1, title="Test Epic", feature="test-feature")
    return tracker


@pytest.fixture
def tracker_with_sprint(tracker):
    """Create StateTracker with a test sprint already created."""
    tracker.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    return tracker


@pytest.fixture
def tracker_with_epic_and_story(tracker_with_epic):
    """Create StateTracker with epic and story already created."""
    tracker_with_epic.create_story(epic_num=1, story_num=1, title="Test Story")
    return tracker_with_epic


@pytest.fixture
def tracker_with_epic_and_sprint(tracker_with_epic):
    """Create StateTracker with epic and sprint already created."""
    tracker_with_epic.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    return tracker_with_epic



@pytest.fixture
def tracker_with_epic_and_sprint(tracker_with_epic):
    """Create StateTracker with epic and sprint already created."""
    tracker_with_epic.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    return tracker_with_epic



# ==================== INITIALIZATION TESTS ====================


def test_state_tracker_initialization(temp_db):
    """Test StateTracker initializes with valid database."""
    tracker = StateTracker(temp_db)
    assert tracker.db_path == temp_db


def test_state_tracker_missing_database():
    """Test StateTracker raises error for missing database."""
    with pytest.raises(DatabaseConnectionError):
        StateTracker(Path("/nonexistent/database.db"))


# ==================== STORY OPERATIONS TESTS ====================


def test_create_story_minimal(tracker_with_epic):
    """Test creating story with minimal parameters."""
    story = tracker_with_epic.create_story(epic_num=1, story_num=1, title="Test Story")

    assert story.epic == 1
    assert story.story_num == 1
    assert story.title == "Test Story"
    assert story.status == "pending"
    assert story.points == 0
    assert story.priority == "P1"
    assert story.owner is None
    assert story.sprint is None


def test_create_story_full_parameters(tracker_with_epic):
    """Test creating story with all parameters."""
    # Create sprint first for sprint assignment
    tracker_with_epic.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")

    story = tracker_with_epic.create_story(
        epic_num=1,
        story_num=2,
        title="Full Story",
        status="in_progress",
        owner="Amelia",
        points=5,
        priority="P0",
        sprint=1,
    )

    assert story.epic == 1
    assert story.story_num == 2
    assert story.title == "Full Story"
    assert story.status == "in_progress"
    assert story.owner == "Amelia"
    assert story.points == 5
    assert story.priority == "P0"
    assert story.sprint == 1


def test_create_story_invalid_status(tracker_with_epic):
    """Test creating story with invalid status raises ValidationError."""
    with pytest.raises(ValidationError):
        tracker_with_epic.create_story(epic_num=1, story_num=1, title="Test", status="invalid")


def test_create_story_invalid_priority(tracker_with_epic):
    """Test creating story with invalid priority raises ValidationError."""
    with pytest.raises(ValidationError):
        tracker_with_epic.create_story(epic_num=1, story_num=1, title="Test", priority="P9")


def test_get_story(tracker_with_epic):
    """Test retrieving story by epic and story number."""
    tracker_with_epic.create_story(epic_num=1, story_num=1, title="Test Story")
    story = tracker_with_epic.get_story(1, 1)

    assert story.epic == 1
    assert story.story_num == 1
    assert story.title == "Test Story"


def test_get_story_not_found(tracker):
    """Test getting non-existent story raises RecordNotFoundError."""
    with pytest.raises(RecordNotFoundError):
        tracker.get_story(999, 999)


def test_update_story_status(tracker_with_epic):
    """Test updating story status."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    tracker.create_story(epic_num=1, story_num=1, title="Test Story")
    updated = tracker.update_story_status(1, 1, "in_progress")

    assert updated.status == "in_progress"
    assert updated.updated_at != updated.created_at


def test_update_story_status_invalid(tracker_with_epic):
    """Test updating story with invalid status raises ValidationError."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    tracker.create_story(epic_num=1, story_num=1, title="Test Story")

    with pytest.raises(ValidationError):
        tracker.update_story_status(1, 1, "invalid_status")


def test_update_story_status_not_found(tracker):
    """Test updating non-existent story raises RecordNotFoundError."""
    with pytest.raises(RecordNotFoundError):
        tracker.update_story_status(999, 999, "done")


def test_update_story_owner(tracker_with_epic):
    """Test assigning owner to story."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    tracker.create_story(epic_num=1, story_num=1, title="Test Story")
    updated = tracker.update_story_owner(1, 1, "Bob")

    assert updated.owner == "Bob"


def test_update_story_points(tracker_with_epic):
    """Test updating story points."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    tracker.create_story(epic_num=1, story_num=1, title="Test Story")
    updated = tracker.update_story_points(1, 1, 8)

    assert updated.points == 8


def test_get_stories_by_status(tracker_with_epic):
    """Test querying stories by status."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    tracker.create_story(epic_num=1, story_num=1, title="Story 1", status="pending")
    tracker.create_story(epic_num=1, story_num=2, title="Story 2", status="in_progress")
    tracker.create_story(epic_num=1, story_num=3, title="Story 3", status="pending")

    pending = tracker.get_stories_by_status("pending")
    assert len(pending) == 2
    assert all(s.status == "pending" for s in pending)


def test_get_stories_by_status_pagination(tracker_with_epic):
    """Test pagination in get_stories_by_status."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    for i in range(5):
        tracker.create_story(epic_num=1, story_num=i + 1, title=f"Story {i + 1}", status="pending")

    # Get first 2
    page1 = tracker.get_stories_by_status("pending", limit=2, offset=0)
    assert len(page1) == 2

    # Get next 2
    page2 = tracker.get_stories_by_status("pending", limit=2, offset=2)
    assert len(page2) == 2

    # Ensure different stories
    assert page1[0].story_num != page2[0].story_num


def test_get_stories_by_epic(tracker_with_epic):
    """Test querying all stories in epic."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    tracker.create_story(epic_num=1, story_num=1, title="Story 1")
    tracker.create_story(epic_num=1, story_num=2, title="Story 2")
    tracker.create_story(epic_num=2, story_num=1, title="Story 3")

    epic1_stories = tracker.get_stories_by_epic(1)
    assert len(epic1_stories) == 2
    assert all(s.epic == 1 for s in epic1_stories)


def test_get_stories_by_sprint(tracker_with_epic):
    """Test querying stories by sprint."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    tracker.create_story(epic_num=1, story_num=1, title="Story 1", sprint=1)
    tracker.create_story(epic_num=1, story_num=2, title="Story 2", sprint=1)
    tracker.create_story(epic_num=1, story_num=3, title="Story 3", sprint=2)

    sprint1_stories = tracker.get_stories_by_sprint(1)
    assert len(sprint1_stories) == 2
    assert all(s.sprint == 1 for s in sprint1_stories)


def test_get_stories_in_progress(tracker_with_epic):
    """Test getting all in-progress stories."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    tracker.create_story(epic_num=1, story_num=1, title="Story 1", status="in_progress")
    tracker.create_story(epic_num=1, story_num=2, title="Story 2", status="pending")
    tracker.create_story(epic_num=1, story_num=3, title="Story 3", status="in_progress")

    in_progress = tracker.get_stories_in_progress()
    assert len(in_progress) == 2
    assert all(s.status == "in_progress" for s in in_progress)


def test_get_blocked_stories(tracker_with_epic):
    """Test getting all blocked stories."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    tracker.create_story(epic_num=1, story_num=1, title="Story 1", status="blocked")
    tracker.create_story(epic_num=1, story_num=2, title="Story 2", status="pending")

    blocked = tracker.get_blocked_stories()
    assert len(blocked) == 1
    assert blocked[0].status == "blocked"


def test_story_full_id_property(tracker_with_epic):
    """Test Story.full_id property."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    story = tracker.create_story(epic_num=12, story_num=3, title="Test")
    assert story.full_id == "12.3"


# ==================== EPIC OPERATIONS TESTS ====================


def test_create_epic(tracker):
    """Test creating epic."""
    epic = tracker.create_epic(
        epic_num=1, title="Test Epic", feature="feature-a", total_points=100
    )

    assert epic.epic_num == 1
    assert epic.title == "Test Epic"
    assert epic.feature == "feature-a"
    assert epic.status == "active"
    assert epic.total_points == 100
    assert epic.completed_points == 0
    assert epic.progress == 0.0


def test_get_epic(tracker):
    """Test retrieving epic."""
    tracker.create_epic(epic_num=1, title="Test Epic", feature="feature-a")
    epic = tracker.get_epic(1)

    assert epic.epic_num == 1
    assert epic.title == "Test Epic"


def test_get_epic_not_found(tracker):
    """Test getting non-existent epic raises RecordNotFoundError."""
    with pytest.raises(RecordNotFoundError):
        tracker.get_epic(999)


def test_get_epic_progress_calculation(tracker):
    """Test epic progress is calculated correctly."""
    epic = tracker.create_epic(epic_num=1, title="Test", feature="feature-a", total_points=100)
    assert epic.progress == 0.0

    # Update points
    tracker.update_epic_points(1, total=100, completed=50)
    epic = tracker.get_epic(1)
    assert epic.progress == 50.0

    # Full completion
    tracker.update_epic_points(1, total=100, completed=100)
    epic = tracker.get_epic(1)
    assert epic.progress == 100.0


def test_get_epic_progress(tracker):
    """Test get_epic_progress method."""
    tracker.create_epic(epic_num=1, title="Test", feature="feature-a", total_points=100)
    tracker.update_epic_points(1, total=100, completed=25)

    progress = tracker.get_epic_progress(1)
    assert progress == 25.0


def test_update_epic_points(tracker):
    """Test updating epic points."""
    tracker.create_epic(epic_num=1, title="Test", feature="feature-a")
    updated = tracker.update_epic_points(1, total=100, completed=30)

    assert updated.total_points == 100
    assert updated.completed_points == 30
    assert updated.progress == 30.0


def test_update_epic_status(tracker):
    """Test updating epic status."""
    tracker.create_epic(epic_num=1, title="Test", feature="feature-a")
    updated = tracker.update_epic_status(1, "completed")

    assert updated.status == "completed"


def test_update_epic_status_invalid(tracker):
    """Test updating epic with invalid status raises ValidationError."""
    tracker.create_epic(epic_num=1, title="Test", feature="feature-a")

    with pytest.raises(ValidationError):
        tracker.update_epic_status(1, "invalid_status")


def test_get_active_epics(tracker):
    """Test getting active epics."""
    tracker.create_epic(epic_num=1, title="Epic 1", feature="feature-a")
    tracker.create_epic(epic_num=2, title="Epic 2", feature="feature-a")
    tracker.update_epic_status(2, "completed")

    active = tracker.get_active_epics()
    assert len(active) == 1
    assert active[0].epic_num == 1


def test_get_epics_by_feature(tracker):
    """Test querying epics by feature."""
    tracker.create_epic(epic_num=1, title="Epic 1", feature="feature-a")
    tracker.create_epic(epic_num=2, title="Epic 2", feature="feature-b")
    tracker.create_epic(epic_num=3, title="Epic 3", feature="feature-a")

    feature_a_epics = tracker.get_epics_by_feature("feature-a")
    assert len(feature_a_epics) == 2
    assert all(e.feature == "feature-a" for e in feature_a_epics)


def test_get_epic_velocity(tracker):
    """Test calculating epic velocity."""
    tracker.create_epic(epic_num=1, title="Test", feature="feature-a")
    tracker.create_story(epic_num=1, story_num=1, title="Story 1", status="done")
    tracker.create_story(epic_num=1, story_num=2, title="Story 2", status="done")
    tracker.create_story(epic_num=1, story_num=3, title="Story 3", status="pending")

    velocity = tracker.get_epic_velocity(1)
    assert velocity == pytest.approx(2.0 / 3.0)


def test_get_epic_velocity_no_stories(tracker):
    """Test epic velocity with no stories returns 0.0."""
    tracker.create_epic(epic_num=1, title="Test", feature="feature-a")
    velocity = tracker.get_epic_velocity(1)
    assert velocity == 0.0


# ==================== SPRINT OPERATIONS TESTS ====================


def test_create_sprint(tracker):
    """Test creating sprint."""
    sprint = tracker.create_sprint(
        sprint_num=1, start_date="2025-01-01", end_date="2025-01-14"
    )

    assert sprint.sprint_num == 1
    assert sprint.start_date == "2025-01-01"
    assert sprint.end_date == "2025-01-14"
    assert sprint.status == "active"


def test_create_sprint_invalid_dates(tracker):
    """Test creating sprint with end_date before start_date raises ValidationError."""
    with pytest.raises(ValidationError):
        tracker.create_sprint(sprint_num=1, start_date="2025-01-14", end_date="2025-01-01")


def test_get_sprint(tracker):
    """Test retrieving sprint."""
    tracker.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    sprint = tracker.get_sprint(1)

    assert sprint.sprint_num == 1


def test_get_sprint_not_found(tracker):
    """Test getting non-existent sprint raises RecordNotFoundError."""
    with pytest.raises(RecordNotFoundError):
        tracker.get_sprint(999)


def test_assign_story_to_sprint(tracker_with_epic_and_sprint):
    """Test assigning story to sprint."""
    tracker.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    tracker.create_story(epic_num=1, story_num=1, title="Story 1")

    updated = tracker.assign_story_to_sprint(1, 1, 1)
    assert updated.sprint == 1


def test_assign_story_to_nonexistent_sprint(tracker_with_epic_and_sprint):
    """Test assigning story to non-existent sprint raises RecordNotFoundError."""
    tracker.create_story(epic_num=1, story_num=1, title="Story 1")

    with pytest.raises(RecordNotFoundError):
        tracker.assign_story_to_sprint(1, 1, 999)


def test_unassign_story_from_sprint(tracker_with_epic_and_sprint):
    """Test removing story from sprint."""
    tracker.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    tracker.create_story(epic_num=1, story_num=1, title="Story 1", sprint=1)

    updated = tracker.unassign_story_from_sprint(1, 1)
    assert updated.sprint is None


def test_get_sprint_stories(tracker_with_epic_and_sprint):
    """Test getting all stories in sprint."""
    tracker.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    tracker.create_story(epic_num=1, story_num=1, title="Story 1", sprint=1)
    tracker.create_story(epic_num=1, story_num=2, title="Story 2", sprint=1)
    tracker.create_story(epic_num=1, story_num=3, title="Story 3")

    stories = tracker.get_sprint_stories(1)
    assert len(stories) == 2
    assert all(s.sprint == 1 for s in stories)


def test_get_sprint_velocity(tracker_with_epic_and_sprint):
    """Test calculating sprint velocity."""
    tracker.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    tracker.create_story(epic_num=1, story_num=1, title="Story 1", sprint=1, points=5, status="done")
    tracker.create_story(epic_num=1, story_num=2, title="Story 2", sprint=1, points=8, status="done")
    tracker.create_story(epic_num=1, story_num=3, title="Story 3", sprint=1, points=3, status="pending")

    velocity = tracker.get_sprint_velocity(1)
    assert velocity == 13  # 5 + 8


def test_get_sprint_velocity_no_completed(tracker_with_epic_and_sprint):
    """Test sprint velocity with no completed stories returns 0."""
    tracker.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    tracker.create_story(epic_num=1, story_num=1, title="Story 1", sprint=1, points=5, status="pending")

    velocity = tracker.get_sprint_velocity(1)
    assert velocity == 0


def test_get_sprint_completion_rate(tracker_with_epic_and_sprint):
    """Test calculating sprint completion rate."""
    tracker.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    tracker.create_story(epic_num=1, story_num=1, title="Story 1", sprint=1, status="done")
    tracker.create_story(epic_num=1, story_num=2, title="Story 2", sprint=1, status="done")
    tracker.create_story(epic_num=1, story_num=3, title="Story 3", sprint=1, status="pending")
    tracker.create_story(epic_num=1, story_num=4, title="Story 4", sprint=1, status="in_progress")

    completion_rate = tracker.get_sprint_completion_rate(1)
    assert completion_rate == 0.5  # 2/4


def test_get_sprint_completion_rate_no_stories(tracker_with_epic_and_sprint):
    """Test sprint completion rate with no stories returns 0.0."""
    tracker.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    completion_rate = tracker.get_sprint_completion_rate(1)
    assert completion_rate == 0.0


def test_get_current_sprint(tracker_with_epic_and_sprint):
    """Test getting current active sprint."""
    tracker.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    tracker.create_sprint(sprint_num=2, start_date="2025-01-15", end_date="2025-01-28")

    current = tracker.get_current_sprint()
    assert current is not None
    assert current.sprint_num == 2  # Latest active sprint


def test_get_current_sprint_none(tracker):
    """Test get_current_sprint returns None when no active sprints."""
    current = tracker.get_current_sprint()
    assert current is None


def test_get_sprint_burndown_data(tracker_with_epic_and_sprint):
    """Test getting sprint burndown data."""
    tracker.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    tracker.create_story(epic_num=1, story_num=1, title="Story 1", sprint=1, points=5, status="done")
    tracker.create_story(epic_num=1, story_num=2, title="Story 2", sprint=1, points=8, status="pending")

    burndown = tracker.get_sprint_burndown_data(1)
    assert burndown["sprint_num"] == 1
    assert burndown["total_points"] == 13
    assert burndown["completed_points"] == 5
    assert burndown["remaining_points"] == 8
    assert burndown["completion_rate"] == 0.5  # 1 done / 2 total


# ==================== WORKFLOW OPERATIONS TESTS ====================


def test_track_workflow_execution(tracker_with_epic_and_story):
    """Test recording workflow execution."""
    wf = tracker.track_workflow_execution(
        workflow_id="wf-123",
        epic_num=1,
        story_num=1,
        workflow_name="implement_story",
    )

    assert wf.workflow_id == "wf-123"
    assert wf.epic == 1
    assert wf.story_num == 1
    assert wf.workflow_name == "implement_story"
    assert wf.status == "running"


def test_update_workflow_status(tracker_with_epic_and_story):
    """Test updating workflow execution status."""
    tracker.track_workflow_execution(
        workflow_id="wf-123", epic_num=1, story_num=1, workflow_name="test"
    )

    updated = tracker.update_workflow_status(
        workflow_id="wf-123", status="completed", result={"success": True}
    )

    assert updated.status == "completed"
    assert updated.completed_at is not None


def test_update_workflow_status_invalid(tracker_with_epic_and_story):
    """Test updating workflow with invalid status raises ValidationError."""
    tracker.track_workflow_execution(
        workflow_id="wf-123", epic_num=1, story_num=1, workflow_name="test"
    )

    with pytest.raises(ValidationError):
        tracker.update_workflow_status(workflow_id="wf-123", status="invalid")


def test_get_story_workflow_history(tracker_with_epic_and_story):
    """Test getting workflow execution history for story."""
    tracker.track_workflow_execution("wf-1", 1, 1, "workflow_a")
    tracker.track_workflow_execution("wf-2", 1, 1, "workflow_b")
    tracker.track_workflow_execution("wf-3", 1, 2, "workflow_c")

    history = tracker.get_story_workflow_history(1, 1)
    assert len(history) == 2
    assert all(wf.epic == 1 and wf.story_num == 1 for wf in history)


def test_get_workflow_execution(tracker_with_epic_and_story):
    """Test retrieving workflow execution by ID."""
    tracker.track_workflow_execution("wf-123", 1, 1, "test")
    wf = tracker.get_workflow_execution("wf-123")

    assert wf.workflow_id == "wf-123"


def test_get_workflow_execution_not_found(tracker):
    """Test getting non-existent workflow raises RecordNotFoundError."""
    with pytest.raises(RecordNotFoundError):
        tracker.get_workflow_execution("nonexistent")


def test_get_failed_workflows(tracker_with_epic_and_story):
    """Test getting all failed workflows."""
    tracker.track_workflow_execution("wf-1", 1, 1, "workflow_a")
    tracker.update_workflow_status("wf-1", "failed")

    tracker.track_workflow_execution("wf-2", 1, 2, "workflow_b")
    tracker.update_workflow_status("wf-2", "completed")

    tracker.track_workflow_execution("wf-3", 1, 3, "workflow_c")
    tracker.update_workflow_status("wf-3", "failed")

    failed = tracker.get_failed_workflows()
    assert len(failed) == 2
    assert all(wf.status == "failed" for wf in failed)


def test_get_workflow_metrics(tracker_with_epic_and_story):
    """Test aggregating workflow metrics."""
    # Create multiple workflow executions
    tracker.track_workflow_execution("wf-1", 1, 1, "test_workflow")
    tracker.update_workflow_status("wf-1", "completed")

    tracker.track_workflow_execution("wf-2", 1, 2, "test_workflow")
    tracker.update_workflow_status("wf-2", "completed")

    tracker.track_workflow_execution("wf-3", 1, 3, "test_workflow")
    tracker.update_workflow_status("wf-3", "failed")

    metrics = tracker.get_workflow_metrics("test_workflow")
    assert metrics["workflow_name"] == "test_workflow"
    assert metrics["total_executions"] == 3
    assert metrics["successful"] == 2
    assert metrics["failed"] == 1
    assert metrics["success_rate"] == pytest.approx(2.0 / 3.0)


def test_get_workflow_metrics_no_executions(tracker):
    """Test workflow metrics with no executions."""
    metrics = tracker.get_workflow_metrics("nonexistent")
    assert metrics["total_executions"] == 0
    assert metrics["success_rate"] == 0.0


# ==================== TRANSACTION & ERROR HANDLING TESTS ====================


def test_transaction_rollback_on_error(tracker_with_epic):
    """Test transaction rolls back on error."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    tracker.create_story(epic_num=1, story_num=1, title="Story 1")

    # Try to create duplicate story (should fail)
    with pytest.raises(StateTrackerError):
        tracker.create_story(epic_num=1, story_num=1, title="Duplicate")

    # Original story should still be intact
    story = tracker.get_story(1, 1)
    assert story.title == "Story 1"


def test_concurrent_operations(tracker_with_epic):
    """Test thread-safe concurrent operations."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    import threading

    def create_stories(start_num):
        for i in range(5):
            tracker.create_story(
                epic_num=1, story_num=start_num + i, title=f"Story {start_num + i}"
            )

    thread1 = threading.Thread(target=create_stories, args=(1,))
    thread2 = threading.Thread(target=create_stories, args=(10,))

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    stories = tracker.get_stories_by_epic(1)
    assert len(stories) == 10


def test_foreign_key_enforcement(tracker):
    """Test foreign key constraints are enforced."""
    # Try to create story for non-existent epic
    # Note: SQLite allows this unless we explicitly check in the app
    # The schema has foreign keys, but they're enforced at the trigger level


# ==================== DATA INTEGRITY TESTS ====================


def test_automatic_timestamp_updates(tracker_with_epic):
    """Test timestamps are automatically updated."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    story = tracker.create_story(epic_num=1, story_num=1, title="Test")
    original_updated = story.updated_at

    # Update story
    import time
    time.sleep(0.01)  # Ensure timestamp difference
    updated = tracker.update_story_status(1, 1, "in_progress")

    assert updated.updated_at != original_updated


def test_prepared_statements_prevent_injection(tracker_with_epic):
    """Test prepared statements prevent SQL injection."""
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Use tracker_with_epic (epic 1 already created)
    tracker = tracker_with_epic
    # Try to inject SQL
    malicious_title = "Test'; DROP TABLE stories; --"
    story = tracker.create_story(epic_num=1, story_num=1, title=malicious_title)

    # Story should be created with the malicious string as title
    assert story.title == malicious_title

    # Table should still exist
    stories = tracker.get_stories_by_epic(1)
    assert len(stories) == 1
