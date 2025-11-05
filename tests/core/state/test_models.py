"""Unit tests for state tracking data models.

Tests dataclass functionality, computed properties, and data validation.
"""

import pytest
from gao_dev.core.state.models import Story, Epic, Sprint, WorkflowExecution


# ==================== STORY MODEL TESTS ====================


def test_story_creation():
    """Test Story dataclass creation with all fields."""
    story = Story(
        id=1,
        epic=10,
        story_num=5,
        title="Test Story",
        status="in_progress",
        owner="Amelia",
        points=8,
        priority="P0",
        sprint=3,
        created_at="2025-01-01T10:00:00",
        updated_at="2025-01-01T11:00:00",
    )

    assert story.id == 1
    assert story.epic == 10
    assert story.story_num == 5
    assert story.title == "Test Story"
    assert story.status == "in_progress"
    assert story.owner == "Amelia"
    assert story.points == 8
    assert story.priority == "P0"
    assert story.sprint == 3
    assert story.created_at == "2025-01-01T10:00:00"
    assert story.updated_at == "2025-01-01T11:00:00"


def test_story_minimal():
    """Test Story with minimal required fields."""
    story = Story(
        id=1,
        epic=10,
        story_num=5,
        title="Test Story",
        status="pending",
    )

    assert story.id == 1
    assert story.epic == 10
    assert story.story_num == 5
    assert story.owner is None
    assert story.points == 0
    assert story.priority == "P1"
    assert story.sprint is None


def test_story_full_id():
    """Test Story.full_id property."""
    story = Story(id=1, epic=12, story_num=3, title="Test", status="pending")
    assert story.full_id == "12.3"


def test_story_full_id_single_digit():
    """Test Story.full_id with single digit numbers."""
    story = Story(id=1, epic=1, story_num=1, title="Test", status="pending")
    assert story.full_id == "1.1"


def test_story_full_id_large_numbers():
    """Test Story.full_id with large numbers."""
    story = Story(id=1, epic=999, story_num=999, title="Test", status="pending")
    assert story.full_id == "999.999"


# ==================== EPIC MODEL TESTS ====================


def test_epic_creation():
    """Test Epic dataclass creation with all fields."""
    epic = Epic(
        id=1,
        epic_num=10,
        title="Test Epic",
        feature="feature-awesome",
        status="active",
        total_points=100,
        completed_points=50,
        progress=50.0,
        created_at="2025-01-01T10:00:00",
        updated_at="2025-01-01T11:00:00",
    )

    assert epic.id == 1
    assert epic.epic_num == 10
    assert epic.title == "Test Epic"
    assert epic.feature == "feature-awesome"
    assert epic.status == "active"
    assert epic.total_points == 100
    assert epic.completed_points == 50
    assert epic.progress == 50.0


def test_epic_progress_calculation():
    """Test Epic progress is calculated in __post_init__."""
    epic = Epic(
        id=1,
        epic_num=10,
        title="Test Epic",
        feature="feature-a",
        status="active",
        total_points=100,
        completed_points=50,
    )

    assert epic.progress == 50.0


def test_epic_progress_zero_total():
    """Test Epic progress with zero total points."""
    epic = Epic(
        id=1,
        epic_num=10,
        title="Test Epic",
        feature="feature-a",
        status="active",
        total_points=0,
        completed_points=0,
    )

    assert epic.progress == 0.0


def test_epic_progress_full_completion():
    """Test Epic progress at 100% completion."""
    epic = Epic(
        id=1,
        epic_num=10,
        title="Test Epic",
        feature="feature-a",
        status="completed",
        total_points=100,
        completed_points=100,
    )

    assert epic.progress == 100.0


def test_epic_progress_partial():
    """Test Epic progress with partial completion."""
    epic = Epic(
        id=1,
        epic_num=10,
        title="Test Epic",
        feature="feature-a",
        status="active",
        total_points=80,
        completed_points=20,
    )

    assert epic.progress == 25.0


def test_epic_minimal():
    """Test Epic with minimal required fields."""
    epic = Epic(
        id=1,
        epic_num=10,
        title="Test Epic",
        feature="feature-a",
        status="planned",
    )

    assert epic.total_points == 0
    assert epic.completed_points == 0
    assert epic.progress == 0.0


# ==================== SPRINT MODEL TESTS ====================


def test_sprint_creation():
    """Test Sprint dataclass creation with all fields."""
    sprint = Sprint(id=1, sprint_num=5, name="Sprint 5", start_date="2025-01-01",
        end_date="2025-01-14",
        status="active",
        created_at="2025-01-01T10:00:00",
    )

    assert sprint.id == 1
    assert sprint.sprint_num == 5
    assert sprint.start_date == "2025-01-01"
    assert sprint.end_date == "2025-01-14"
    assert sprint.status == "active"
    assert sprint.created_at == "2025-01-01T10:00:00"


def test_sprint_minimal():
    """Test Sprint with minimal required fields."""
    sprint = Sprint(id=1, sprint_num=5, name="Sprint 5", start_date="2025-01-01",
        end_date="2025-01-14",
        status="planned",
    )

    assert sprint.created_at == ""


# ==================== WORKFLOW EXECUTION MODEL TESTS ====================


def test_workflow_execution_creation():
    """Test WorkflowExecution dataclass creation with all fields."""
    workflow = WorkflowExecution(
        id=1,
        workflow_id="wf-12345",
        epic=10,
        story_num=5,
        workflow_name="implement_story",
        status="completed",
        started_at="2025-01-01T10:00:00",
        completed_at="2025-01-01T10:30:00",
        result='{"success": true}',
    )

    assert workflow.id == 1
    assert workflow.workflow_id == "wf-12345"
    assert workflow.epic == 10
    assert workflow.story_num == 5
    assert workflow.workflow_name == "implement_story"
    assert workflow.status == "completed"
    assert workflow.started_at == "2025-01-01T10:00:00"
    assert workflow.completed_at == "2025-01-01T10:30:00"
    assert workflow.result == '{"success": true}'


def test_workflow_execution_minimal():
    """Test WorkflowExecution with minimal required fields."""
    workflow = WorkflowExecution(
        id=1,
        workflow_id="wf-12345",
        epic=10,
        story_num=5,
        workflow_name="test_workflow",
        status="running",
        started_at="2025-01-01T10:00:00",
    )

    assert workflow.completed_at is None
    assert workflow.result is None


def test_workflow_execution_running():
    """Test WorkflowExecution in running state."""
    workflow = WorkflowExecution(
        id=1,
        workflow_id="wf-12345",
        epic=10,
        story_num=5,
        workflow_name="test_workflow",
        status="running",
        started_at="2025-01-01T10:00:00",
    )

    assert workflow.status == "running"
    assert workflow.completed_at is None


def test_workflow_execution_failed():
    """Test WorkflowExecution in failed state."""
    workflow = WorkflowExecution(
        id=1,
        workflow_id="wf-12345",
        epic=10,
        story_num=5,
        workflow_name="test_workflow",
        status="failed",
        started_at="2025-01-01T10:00:00",
        completed_at="2025-01-01T10:05:00",
        result='{"error": "Something went wrong"}',
    )

    assert workflow.status == "failed"
    assert workflow.result == '{"error": "Something went wrong"}'


# ==================== MODEL EQUALITY TESTS ====================


def test_story_equality():
    """Test Story equality comparison."""
    story1 = Story(id=1, epic=10, story_num=5, title="Test", status="pending")
    story2 = Story(id=1, epic=10, story_num=5, title="Test", status="pending")

    assert story1 == story2


def test_epic_equality():
    """Test Epic equality comparison."""
    epic1 = Epic(
        id=1, epic_num=10, title="Test", feature="feature-a", status="active"
    )
    epic2 = Epic(
        id=1, epic_num=10, title="Test", feature="feature-a", status="active"
    )

    assert epic1 == epic2


def test_sprint_equality():
    """Test Sprint equality comparison."""
    sprint1 = Sprint(id=1, sprint_num=5, name="Sprint 5", start_date="2025-01-01", end_date="2025-01-14", status="active"
    )
    sprint2 = Sprint(id=1, sprint_num=5, name="Sprint 5", start_date="2025-01-01", end_date="2025-01-14", status="active"
    )

    assert sprint1 == sprint2


def test_workflow_execution_equality():
    """Test WorkflowExecution equality comparison."""
    wf1 = WorkflowExecution(
        id=1,
        workflow_id="wf-123",
        epic=10,
        story_num=5,
        workflow_name="test",
        status="running",
        started_at="2025-01-01T10:00:00",
    )
    wf2 = WorkflowExecution(
        id=1,
        workflow_id="wf-123",
        epic=10,
        story_num=5,
        workflow_name="test",
        status="running",
        started_at="2025-01-01T10:00:00",
    )

    assert wf1 == wf2


# ==================== MODEL STRING REPRESENTATION TESTS ====================


def test_story_repr():
    """Test Story string representation."""
    story = Story(id=1, epic=10, story_num=5, title="Test Story", status="pending")
    repr_str = repr(story)

    assert "Story" in repr_str
    assert "epic=10" in repr_str
    assert "story_num=5" in repr_str


def test_epic_repr():
    """Test Epic string representation."""
    epic = Epic(
        id=1, epic_num=10, title="Test Epic", feature="feature-a", status="active"
    )
    repr_str = repr(epic)

    assert "Epic" in repr_str
    assert "epic_num=10" in repr_str


def test_sprint_repr():
    """Test Sprint string representation."""
    sprint = Sprint(id=1, sprint_num=5, name="Sprint 5", start_date="2025-01-01", end_date="2025-01-14", status="active"
    )
    repr_str = repr(sprint)

    assert "Sprint" in repr_str
    assert "sprint_num=5" in repr_str


def test_workflow_execution_repr():
    """Test WorkflowExecution string representation."""
    wf = WorkflowExecution(
        id=1,
        workflow_id="wf-123",
        epic=10,
        story_num=5,
        workflow_name="test",
        status="running",
        started_at="2025-01-01T10:00:00",
    )
    repr_str = repr(wf)

    assert "WorkflowExecution" in repr_str
    assert "workflow_id='wf-123'" in repr_str
