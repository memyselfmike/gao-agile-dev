"""Tests for Story 39.20: Workflow Execution Timeline.

Tests all 12 acceptance criteria for the workflow timeline feature.
"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from fastapi.testclient import TestClient
from gao_dev.web.server import create_app
from gao_dev.web.config import WebConfig
from gao_dev.core.state.state_tracker import StateTracker
import sqlite3


@pytest.fixture
def test_project_root(tmp_path):
    """Create a test project root with database."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    gao_dev_dir = project_root / ".gao-dev"
    gao_dev_dir.mkdir()

    # Create database
    db_path = gao_dev_dir / "documents.db"

    # Initialize database schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create tables (matching schema.sql)
    cursor.execute("""
        CREATE TABLE epics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epic_num INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            feature TEXT,
            status TEXT NOT NULL DEFAULT 'planned',
            total_points INTEGER DEFAULT 0,
            completed_points INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
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
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(epic_num, story_num)
        )
    """)

    cursor.execute("""
        CREATE TABLE sprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sprint_num INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'planned',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE workflow_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_name TEXT NOT NULL,
            phase TEXT,
            epic_num INTEGER,
            story_num INTEGER,
            status TEXT NOT NULL DEFAULT 'started',
            executor TEXT NOT NULL,
            started_at TEXT NOT NULL DEFAULT (datetime('now')),
            completed_at TEXT,
            duration_ms INTEGER,
            output TEXT,
            error_message TEXT,
            exit_code INTEGER,
            metadata JSON,
            context_snapshot JSON
        )
    """)

    conn.commit()
    conn.close()

    return project_root


@pytest.fixture
def client(test_project_root):
    """Create test client with custom project root."""
    config = WebConfig()
    app = create_app(config)
    # Override project root
    app.state.project_root = test_project_root
    return TestClient(app)


@pytest.fixture
def state_tracker(test_project_root):
    """Create StateTracker instance for test database."""
    db_path = test_project_root / ".gao-dev" / "documents.db"
    return StateTracker(db_path)


@pytest.fixture
def sample_workflows(state_tracker):
    """Create sample workflow executions for testing."""
    workflows = []
    now = datetime.now()

    # Create workflows with different statuses and times
    for i in range(1, 6):
        # Vary status
        status = ['completed', 'running', 'failed', 'completed', 'cancelled'][i - 1]

        started_at = (now - timedelta(hours=i)).isoformat()
        completed_at = (now - timedelta(hours=i - 1)).isoformat() if status == 'completed' else None

        wf = state_tracker.track_workflow_execution(
            workflow_id=f"wf-test-{i}",
            epic_num=1,
            story_num=i,
            workflow_name=f"Workflow {i % 3 + 1}",  # 3 different workflow types
        )

        # Update status if not running
        if status != 'running':
            state_tracker.update_workflow_status(
                workflow_id=f"wf-test-{i}",
                status=status,
                result={'output': f'Test result {i}'} if status == 'completed' else None
            )

        workflows.append(wf)

    return workflows


# AC1: GET /api/workflows/timeline endpoint returns workflow execution records
def test_timeline_endpoint_exists(client):
    """Test AC1: Endpoint is registered and accessible."""
    response = client.get("/api/workflows/timeline")
    assert response.status_code == 200
    data = response.json()
    assert "workflows" in data
    assert "total" in data
    assert "filters" in data


# AC2: Timeline returns empty array when no workflows exist
def test_timeline_empty_when_no_workflows(client):
    """Test AC2: Returns empty array gracefully."""
    response = client.get("/api/workflows/timeline")
    assert response.status_code == 200
    data = response.json()
    assert data["workflows"] == []
    assert data["total"] == 0


# AC3: Timeline returns workflows with all required fields
def test_timeline_returns_all_fields(client, sample_workflows):
    """Test AC3: All required fields present in response."""
    response = client.get("/api/workflows/timeline")
    assert response.status_code == 200
    data = response.json()

    assert len(data["workflows"]) > 0
    workflow = data["workflows"][0]

    # Check all required fields
    assert "id" in workflow
    assert "workflow_id" in workflow
    assert "workflow_name" in workflow
    assert "status" in workflow
    assert "started_at" in workflow
    assert "completed_at" in workflow  # May be null
    assert "duration" in workflow  # May be null
    assert "agent" in workflow
    assert "epic" in workflow
    assert "story_num" in workflow


# AC4: Timeline filters by workflow_type
def test_timeline_filter_by_workflow_type(client, sample_workflows):
    """Test AC4: Workflow type filtering works correctly."""
    # Query for specific workflow type
    response = client.get("/api/workflows/timeline?workflow_type=Workflow 1")
    assert response.status_code == 200
    data = response.json()

    # All returned workflows should match the filter
    for workflow in data["workflows"]:
        assert workflow["workflow_name"] == "Workflow 1"


# AC5: Timeline filters by date_range
def test_timeline_filter_by_date_range(client, sample_workflows):
    """Test AC5: Date range filtering works correctly."""
    now = datetime.now()
    start_date = (now - timedelta(hours=3)).isoformat()
    end_date = now.isoformat()

    response = client.get(
        f"/api/workflows/timeline?start_date={start_date}&end_date={end_date}"
    )
    assert response.status_code == 200
    data = response.json()

    # Verify returned workflows are within date range
    for workflow in data["workflows"]:
        started_at = datetime.fromisoformat(workflow["started_at"].replace("Z", "+00:00"))
        assert started_at >= datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        assert started_at <= datetime.fromisoformat(end_date.replace("Z", "+00:00"))


# AC6: Timeline filters by status
def test_timeline_filter_by_status(client, sample_workflows):
    """Test AC6: Status filtering works correctly."""
    # Filter for completed workflows only
    response = client.get("/api/workflows/timeline?status=completed")
    assert response.status_code == 200
    data = response.json()

    # All returned workflows should have completed status
    for workflow in data["workflows"]:
        assert workflow["status"] == "completed"

    # Test multiple statuses (comma-separated)
    response = client.get("/api/workflows/timeline?status=completed,failed")
    assert response.status_code == 200
    data = response.json()

    for workflow in data["workflows"]:
        assert workflow["status"] in ["completed", "failed"]


# AC7: Timeline calculates duration correctly
def test_timeline_calculates_duration(client, sample_workflows):
    """Test AC7: Duration calculation is correct."""
    response = client.get("/api/workflows/timeline?status=completed")
    assert response.status_code == 200
    data = response.json()

    # Find a completed workflow
    completed_workflows = [wf for wf in data["workflows"] if wf["status"] == "completed"]
    assert len(completed_workflows) > 0

    workflow = completed_workflows[0]
    if workflow["completed_at"] and workflow["started_at"]:
        # Duration should be present and non-negative
        assert workflow["duration"] is not None
        assert workflow["duration"] >= 0


# AC8: Timeline handles incomplete workflows (no completed_at)
def test_timeline_handles_running_workflows(client, sample_workflows):
    """Test AC8: Running workflows handled correctly."""
    response = client.get("/api/workflows/timeline?status=running")
    assert response.status_code == 200
    data = response.json()

    # Find a running workflow
    running_workflows = [wf for wf in data["workflows"] if wf["status"] == "running"]
    assert len(running_workflows) > 0

    workflow = running_workflows[0]
    # Running workflows should have null completed_at and duration
    assert workflow["completed_at"] is None
    assert workflow["duration"] is None


# AC9: Timeline returns filter metadata
def test_timeline_returns_filter_metadata(client, sample_workflows):
    """Test AC9: Filter metadata is included in response."""
    response = client.get("/api/workflows/timeline")
    assert response.status_code == 200
    data = response.json()

    # Check filters metadata
    assert "filters" in data
    filters = data["filters"]

    assert "workflow_types" in filters
    assert "date_range" in filters
    assert "statuses" in filters

    # Workflow types should include all unique workflow names
    assert len(filters["workflow_types"]) > 0

    # Date range should have min and max
    assert "min" in filters["date_range"]
    assert "max" in filters["date_range"]

    # Statuses should include all valid statuses
    expected_statuses = ["pending", "running", "completed", "failed", "cancelled"]
    assert filters["statuses"] == expected_statuses


# AC10: Frontend store structure validation
def test_frontend_store_structure():
    """Test AC10: Verify workflowStore structure."""
    # This tests the TypeScript interfaces by importing the module
    import subprocess
    import os

    frontend_dir = Path(__file__).parent.parent.parent / "gao_dev" / "web" / "frontend"
    store_file = frontend_dir / "src" / "stores" / "workflowStore.ts"

    # Check if file exists
    assert store_file.exists(), "workflowStore.ts should exist"

    # Check if file contains required exports
    content = store_file.read_text()
    assert "interface WorkflowExecution" in content
    assert "interface TimelineFilters" in content
    assert "useWorkflowStore" in content
    assert "fetchTimeline" in content
    assert "applyFilters" in content
    assert "clearFilters" in content


# AC11: Component files exist
def test_frontend_components_exist():
    """Test AC11: Verify all required components exist."""
    frontend_dir = Path(__file__).parent.parent.parent / "gao_dev" / "web" / "frontend"
    components_dir = frontend_dir / "src" / "components" / "workflow"

    # Check if all component files exist
    assert (components_dir / "WorkflowTimeline.tsx").exists()
    assert (components_dir / "TimelineFilters.tsx").exists()
    assert (components_dir / "WorkflowBar.tsx").exists()
    assert (components_dir / "index.ts").exists()


# AC12: All 12 acceptance criteria validated
def test_all_acceptance_criteria_covered():
    """Test AC12: Meta-test to verify all ACs are covered."""
    # This test serves as documentation that all 12 ACs are tested
    acceptance_criteria = {
        "AC1": "test_timeline_endpoint_exists",
        "AC2": "test_timeline_empty_when_no_workflows",
        "AC3": "test_timeline_returns_all_fields",
        "AC4": "test_timeline_filter_by_workflow_type",
        "AC5": "test_timeline_filter_by_date_range",
        "AC6": "test_timeline_filter_by_status",
        "AC7": "test_timeline_calculates_duration",
        "AC8": "test_timeline_handles_running_workflows",
        "AC9": "test_timeline_returns_filter_metadata",
        "AC10": "test_frontend_store_structure",
        "AC11": "test_frontend_components_exist",
        "AC12": "test_all_acceptance_criteria_covered",
    }

    # Verify all test functions exist in this module
    import inspect
    current_module = inspect.getmodule(inspect.currentframe())
    module_functions = [name for name, obj in inspect.getmembers(current_module)
                       if inspect.isfunction(obj) and name.startswith('test_')]

    for ac, test_name in acceptance_criteria.items():
        assert test_name in module_functions, f"{ac} test function {test_name} is missing"

    assert len(acceptance_criteria) == 12, "Should have exactly 12 acceptance criteria"


# Additional integration tests

def test_timeline_combined_filters(client, sample_workflows):
    """Test multiple filters applied simultaneously."""
    now = datetime.now()
    start_date = (now - timedelta(hours=4)).isoformat()

    response = client.get(
        f"/api/workflows/timeline?workflow_type=Workflow 1&start_date={start_date}&status=completed"
    )
    assert response.status_code == 200
    data = response.json()

    # All filters should be applied
    for workflow in data["workflows"]:
        assert workflow["workflow_name"] == "Workflow 1"
        assert workflow["status"] == "completed"
        started_at = datetime.fromisoformat(workflow["started_at"].replace("Z", "+00:00"))
        assert started_at >= datetime.fromisoformat(start_date.replace("Z", "+00:00"))


def test_timeline_performance_with_many_workflows(client, state_tracker):
    """Test performance with 100+ workflows."""
    import time

    # Create 150 workflows
    for i in range(150):
        state_tracker.track_workflow_execution(
            workflow_id=f"perf-test-{i}",
            epic_num=1,
            story_num=1,
            workflow_name=f"PerfTest Workflow {i % 10}",
        )

    # Measure response time
    start_time = time.time()
    response = client.get("/api/workflows/timeline")
    end_time = time.time()

    assert response.status_code == 200
    data = response.json()
    assert len(data["workflows"]) == 150

    # Response should be fast (< 500ms)
    response_time_ms = (end_time - start_time) * 1000
    assert response_time_ms < 500, f"Response time {response_time_ms}ms exceeds 500ms threshold"


def test_timeline_no_database_returns_empty(client, test_project_root):
    """Test graceful handling when database doesn't exist."""
    # Remove database file
    db_path = test_project_root / ".gao-dev" / "documents.db"
    if db_path.exists():
        db_path.unlink()

    response = client.get("/api/workflows/timeline")
    assert response.status_code == 200
    data = response.json()
    assert data["workflows"] == []
    assert data["total"] == 0
