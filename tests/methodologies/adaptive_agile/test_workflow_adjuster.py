"""Tests for WorkflowAdjuster service (Story 29.4).

Tests cover:
- Quality, process, and architectural learning adjustments
- Dependency cycle detection (C7 fix)
- Adjustment limits (C1 fix)
- Validation and rollback
- Database integration

Story: 29.4 - Workflow Adjustment Logic
Epic: 29 - Self-Learning Feedback Loop
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List

from gao_dev.methodologies.adaptive_agile.workflow_adjuster import (
    WorkflowAdjuster,
    WorkflowStep,
)
from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel
from gao_dev.core.services.learning_application_service import ScoredLearning
from gao_dev.lifecycle.exceptions import (
    WorkflowDependencyCycleError,
)


# Fixtures


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    # Initialize database with required tables
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

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

    # Create epic_state table (required for foreign keys)
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

    # Create learning_index table (required for foreign keys)
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

    # Create workflow_adjustments table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS workflow_adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epic_num INTEGER NOT NULL,
            learning_id INTEGER,
            adjustment_type TEXT NOT NULL CHECK(adjustment_type IN ('add', 'modify', 'remove')),
            workflow_name TEXT NOT NULL,
            reason TEXT,
            applied_at TEXT NOT NULL,
            metadata JSON,
            FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num) ON DELETE CASCADE,
            FOREIGN KEY (learning_id) REFERENCES learning_index(id) ON DELETE SET NULL
        )
        """
    )

    # Insert test epic
    cursor.execute(
        """
        INSERT INTO epic_state (epic_num, epic_title, status, created_at)
        VALUES (29, 'Test Epic', 'in_progress', datetime('now'))
        """
    )

    # Insert test learnings
    for i in range(1, 4):
        cursor.execute(
            """
            INSERT INTO learning_index (topic, category, learning, indexed_at, created_at)
            VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """,
            (f"topic-{i}", "quality", f"Learning {i}")
        )

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup - close any connections first
    import gc
    gc.collect()
    try:
        db_path.unlink()
    except PermissionError:
        pass  # File still in use, will be cleaned up later


@pytest.fixture
def adjuster(temp_db):
    """Create WorkflowAdjuster instance."""
    return WorkflowAdjuster(db_path=temp_db)


@pytest.fixture
def base_workflows() -> List[WorkflowStep]:
    """Base workflow sequence for testing."""
    return [
        WorkflowStep(workflow_name="create-prd", phase="planning"),
        WorkflowStep(workflow_name="create-stories", phase="planning"),
        WorkflowStep(workflow_name="implement-stories", phase="implementation"),
        WorkflowStep(workflow_name="test-feature", phase="testing"),
    ]


@pytest.fixture
def quality_learning() -> ScoredLearning:
    """Quality learning example."""
    return ScoredLearning(
        learning_id=1,
        topic="testing",
        category="quality",
        learning="Low test coverage (<80%) caused production bugs in Epic 27",
        relevance_score=0.85,
        success_rate=0.9,
        confidence_score=0.85,
        application_count=3,
        indexed_at=datetime.utcnow().isoformat(),
        metadata={"epic": 27},
        tags=["testing", "quality"],
    )


@pytest.fixture
def process_learning() -> ScoredLearning:
    """Process learning example."""
    return ScoredLearning(
        learning_id=2,
        topic="ceremonies",
        category="process",
        learning="Daily standups prevented blockers in Epic 25",
        relevance_score=0.75,
        success_rate=0.85,
        confidence_score=0.75,
        application_count=2,
        indexed_at=datetime.utcnow().isoformat(),
        metadata={"epic": 25},
        tags=["standup", "communication"],
    )


@pytest.fixture
def architectural_learning() -> ScoredLearning:
    """Architectural learning example."""
    return ScoredLearning(
        learning_id=3,
        topic="architecture",
        category="architectural",
        learning="Security vulnerabilities discovered in Epic 20 due to missing reviews",
        relevance_score=0.90,
        success_rate=0.95,
        confidence_score=0.90,
        application_count=1,
        indexed_at=datetime.utcnow().isoformat(),
        metadata={"epic": 20},
        tags=["security", "architecture"],
    )


# Tests: Quality Learning Adjustments (AC4)


def test_quality_learning_adds_testing_workflows(adjuster, base_workflows, quality_learning):
    """Test that quality learning adds testing workflows."""
    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=[quality_learning],
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        epic_num=29,
    )

    # Should add extended-testing and coverage-report
    assert len(adjusted) == len(base_workflows) + 2
    assert any(wf.workflow_name == "extended-testing" for wf in adjusted)
    assert any(wf.workflow_name == "coverage-report" for wf in adjusted)

    # Check dependencies
    extended_testing = next(wf for wf in adjusted if wf.workflow_name == "extended-testing")
    assert "test-feature" in extended_testing.depends_on

    coverage_report = next(wf for wf in adjusted if wf.workflow_name == "coverage-report")
    assert "extended-testing" in coverage_report.depends_on


def test_quality_learning_no_duplicates(adjuster, base_workflows, quality_learning):
    """Test that quality learnings don't add duplicate workflows."""
    # Add extended-testing manually
    base_workflows.append(
        WorkflowStep(workflow_name="extended-testing", phase="testing", depends_on=["test-feature"])
    )

    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=[quality_learning],
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        epic_num=29,
    )

    # Should only add coverage-report (extended-testing already exists)
    extended_testing_count = sum(1 for wf in adjusted if wf.workflow_name == "extended-testing")
    assert extended_testing_count == 1


# Tests: Process Learning Adjustments (AC5)


def test_process_learning_modifies_standup_frequency(adjuster, base_workflows, process_learning):
    """Test that process learning increases standup frequency."""
    # Add standup ceremony
    base_workflows.append(WorkflowStep(workflow_name="ceremony-standup", phase="planning", interval=3))

    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=[process_learning],
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        epic_num=29,
    )

    # Standup interval should be reduced
    standup = next(wf for wf in adjusted if wf.workflow_name == "ceremony-standup")
    assert standup.interval == 2  # Reduced from 3 to 2


def test_process_learning_adds_ceremony_planning(adjuster, base_workflows, process_learning):
    """Test that process learning adds ceremony planning."""
    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=[process_learning],
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        epic_num=29,
    )

    # Should add ceremony-planning
    assert any(wf.workflow_name == "ceremony-planning" for wf in adjusted)


# Tests: Architectural Learning Adjustments (AC6)


def test_architectural_learning_adds_security_review(
    adjuster, base_workflows, architectural_learning
):
    """Test that architectural learning adds security reviews."""
    # Add architecture workflow
    base_workflows.insert(
        2, WorkflowStep(workflow_name="architecture", phase="solutioning", depends_on=["create-prd"])
    )

    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=[architectural_learning],
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        epic_num=29,
    )

    # Should add security-review and security-testing
    assert any(wf.workflow_name == "security-review" for wf in adjusted)
    assert any(wf.workflow_name == "security-testing" for wf in adjusted)

    # Check dependencies
    security_review = next(wf for wf in adjusted if wf.workflow_name == "security-review")
    assert "architecture" in security_review.depends_on


# Tests: Dependency Cycle Detection (AC2, C7 Fix)


def test_cycle_detection_simple_cycle(adjuster):
    """Test cycle detection for simple A -> B -> A cycle."""
    workflows = [
        WorkflowStep(workflow_name="workflow-a", depends_on=["workflow-b"]),
        WorkflowStep(workflow_name="workflow-b", depends_on=["workflow-a"]),
    ]

    with pytest.raises(WorkflowDependencyCycleError) as exc_info:
        adjuster._detect_dependency_cycles(workflows)

    assert "workflow-a" in str(exc_info.value)
    assert "workflow-b" in str(exc_info.value)


def test_cycle_detection_complex_cycle(adjuster):
    """Test cycle detection for A -> B -> C -> A cycle."""
    workflows = [
        WorkflowStep(workflow_name="workflow-a", depends_on=["workflow-b"]),
        WorkflowStep(workflow_name="workflow-b", depends_on=["workflow-c"]),
        WorkflowStep(workflow_name="workflow-c", depends_on=["workflow-a"]),
    ]

    with pytest.raises(WorkflowDependencyCycleError) as exc_info:
        adjuster._detect_dependency_cycles(workflows)

    assert "workflow-a" in str(exc_info.value)
    assert "workflow-b" in str(exc_info.value)
    assert "workflow-c" in str(exc_info.value)


def test_cycle_detection_no_cycle(adjuster, base_workflows):
    """Test that valid workflows pass cycle detection."""
    # Add dependencies without cycles
    base_workflows[1].depends_on = ["create-prd"]
    base_workflows[2].depends_on = ["create-stories"]
    base_workflows[3].depends_on = ["implement-stories"]

    # Should not raise
    adjuster._detect_dependency_cycles(base_workflows)


def test_cycle_detection_missing_dependency(adjuster):
    """Test that missing dependencies are caught."""
    workflows = [WorkflowStep(workflow_name="workflow-a", depends_on=["non-existent"])]

    with pytest.raises(WorkflowDependencyCycleError) as exc_info:
        adjuster._detect_dependency_cycles(workflows)

    assert "non-existent" in str(exc_info.value)


# Tests: Adjustment Limits (AC3, C1 Fix)


def test_max_workflows_added_enforced(adjuster, base_workflows, quality_learning, temp_db):
    """Test that max 3 workflows can be added per adjustment."""
    # Insert more learnings into database
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    for i in range(4, 14):  # IDs 4-13 (1-3 already exist)
        cursor.execute(
            """
            INSERT INTO learning_index (topic, category, learning, indexed_at, created_at)
            VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """,
            (f"topic-{i}", "quality", f"test coverage integration issues {i}")
        )

    conn.commit()
    conn.close()

    # Create multiple learnings that would add >3 workflows
    learnings = [
        ScoredLearning(
            learning_id=i,
            topic="testing",
            category="quality",
            learning=f"test coverage integration issues {i}",
            relevance_score=0.85,
            success_rate=0.9,
            confidence_score=0.85,
            application_count=1,
            indexed_at=datetime.utcnow().isoformat(),
            metadata={},
            tags=[],
        )
        for i in range(1, 11)  # Use existing IDs 1-10
    ]

    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=learnings,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        epic_num=29,
    )

    # Should add max 3 workflows
    workflows_added = len(adjusted) - len(base_workflows)
    assert workflows_added <= 3


def test_max_adjustments_per_epic_enforced(adjuster, base_workflows, quality_learning, temp_db):
    """Test that max 3 adjustments per epic are enforced."""
    # Manually insert 3 adjustment records to hit the limit
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    for i in range(3):
        cursor.execute(
            """
            INSERT INTO workflow_adjustments
            (epic_num, learning_id, adjustment_type, workflow_name, reason, applied_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (29, 1, "add", f"workflow-{i}", "Test", datetime.utcnow().isoformat()),
        )

    conn.commit()
    conn.close()

    # Try to adjust (should return original due to limit)
    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=[quality_learning],
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        epic_num=29,
    )

    # Should return original workflows unchanged
    assert len(adjusted) == len(base_workflows)


# Tests: Validation (AC7)


def test_validation_rejects_duplicate_workflows(adjuster):
    """Test that duplicate workflow names are rejected."""
    workflows = [
        WorkflowStep(workflow_name="workflow-a"),
        WorkflowStep(workflow_name="workflow-a"),  # Duplicate
    ]

    with pytest.raises(WorkflowDependencyCycleError) as exc_info:
        adjuster._validate_workflows(workflows)

    assert "Duplicate" in str(exc_info.value)


def test_validation_checks_max_depth(adjuster):
    """Test that excessive workflow depth is rejected."""
    # Create chain of 12 workflows (exceeds limit of 10)
    workflows = [
        WorkflowStep(
            workflow_name=f"workflow-{i}",
            depends_on=[f"workflow-{i-1}"] if i > 0 else [],
        )
        for i in range(12)
    ]

    with pytest.raises(WorkflowDependencyCycleError) as exc_info:
        adjuster._validate_workflows(workflows)

    assert "depth" in str(exc_info.value).lower()
    assert "10" in str(exc_info.value)


def test_validation_rollback_on_failure(adjuster, base_workflows, quality_learning):
    """Test that workflows rollback to original on validation failure."""
    # Monkey-patch _apply_quality_learnings to create invalid workflows
    original_apply = adjuster._apply_quality_learnings

    def create_cycle(workflows, learnings):
        # Create a cycle
        workflows.append(WorkflowStep(workflow_name="bad-workflow-a", depends_on=["bad-workflow-b"]))
        workflows.append(WorkflowStep(workflow_name="bad-workflow-b", depends_on=["bad-workflow-a"]))
        return [workflows[-2], workflows[-1]]

    adjuster._apply_quality_learnings = create_cycle

    # Adjust should detect cycle and rollback
    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=[quality_learning],
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        epic_num=29,
    )

    # Should return original workflows
    assert len(adjusted) == len(base_workflows)

    # Restore original method
    adjuster._apply_quality_learnings = original_apply


# Tests: Database Integration (AC9)


def test_adjustments_recorded_in_database(adjuster, base_workflows, quality_learning, temp_db):
    """Test that adjustments are recorded in database."""
    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=[quality_learning],
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        epic_num=29,
    )

    # Check database for records
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM workflow_adjustments WHERE epic_num = ?",
        (29,),
    )
    count = cursor.fetchone()[0]

    # Should have records for added workflows
    workflows_added = len(adjusted) - len(base_workflows)
    assert count == workflows_added

    conn.close()


def test_adjustment_count_tracking(adjuster, base_workflows, quality_learning, temp_db):
    """Test that adjustment count is tracked correctly."""
    # First adjustment
    adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=[quality_learning],
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        epic_num=29,
    )

    # Check count
    count = adjuster._get_adjustment_count_for_epic(29)
    assert count == 1


# Tests: Edge Cases


def test_empty_learnings_returns_original(adjuster, base_workflows):
    """Test that empty learnings returns original workflows."""
    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=[],
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        epic_num=29,
    )

    assert len(adjusted) == len(base_workflows)


def test_no_epic_num_skips_limit_check(adjuster, base_workflows, quality_learning):
    """Test that adjustment works without epic_num (skips limit check)."""
    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=[quality_learning],
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        epic_num=None,  # No epic tracking
    )

    # Should still add workflows
    assert len(adjusted) > len(base_workflows)


def test_multiple_learning_categories(
    adjuster, base_workflows, quality_learning, process_learning, architectural_learning
):
    """Test that multiple learning categories are applied together."""
    base_workflows.insert(
        2, WorkflowStep(workflow_name="architecture", phase="solutioning", depends_on=["create-prd"])
    )

    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=[quality_learning, process_learning, architectural_learning],
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        epic_num=29,
    )

    # Should add workflows from all categories (up to limit)
    assert len(adjusted) > len(base_workflows)


# Tests: WorkflowStep Dataclass


def test_workflow_step_validation():
    """Test WorkflowStep validation."""
    # Valid step
    step = WorkflowStep(workflow_name="test-workflow", phase="testing")
    assert step.workflow_name == "test-workflow"

    # Empty name should raise
    with pytest.raises(ValueError):
        WorkflowStep(workflow_name="", phase="testing")

    # Invalid interval should raise
    with pytest.raises(ValueError):
        WorkflowStep(workflow_name="test", phase="testing", interval=0)


def test_workflow_step_default_values():
    """Test WorkflowStep default values."""
    step = WorkflowStep(workflow_name="test-workflow")
    assert step.phase == "implementation"
    assert step.depends_on == []
    assert step.interval is None
    assert step.metadata == {}
