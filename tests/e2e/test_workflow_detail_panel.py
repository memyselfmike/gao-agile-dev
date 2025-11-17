"""End-to-end tests for Workflow Detail Panel.

Story 39.21: Workflow Detail Panel

Tests all 12 acceptance criteria:
- AC1: GET /api/workflows/{workflow_id}/details endpoint
- AC2-12: Frontend functionality (tested via manual validation)
"""

import json
import pytest
import sqlite3
from datetime import datetime
from pathlib import Path
from fastapi.testclient import TestClient
from gao_dev.web.server import create_app
from gao_dev.web.config import WebConfig
from gao_dev.core.state.state_tracker import StateTracker


@pytest.fixture
def test_project_root(tmp_path: Path) -> Path:
    """Create temporary project root with database."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # Create .gao-dev directory
    gao_dev_dir = project_root / ".gao-dev"
    gao_dev_dir.mkdir()

    return project_root


@pytest.fixture
def test_db(test_project_root: Path) -> Path:
    """Create test database with workflow executions."""
    db_path = test_project_root / ".gao-dev" / "documents.db"

    # Create database schema using schema.sql
    schema_path = (
        Path(__file__).parent.parent.parent / "gao_dev" / "core" / "state" / "schema.sql"
    )

    conn = sqlite3.connect(str(db_path))
    with open(schema_path, "r") as schema_file:
        conn.executescript(schema_file.read())
    conn.close()

    state_tracker = StateTracker(db_path)

    # Create prerequisite epics and stories (foreign key requirements)
    state_tracker.create_epic(epic_num=1, title="Test Epic 1", feature="web-interface")
    state_tracker.create_story(epic_num=1, story_num=1, title="Test Story 1.1")

    state_tracker.create_epic(epic_num=2, title="Test Epic 2", feature="web-interface")
    state_tracker.create_story(epic_num=2, story_num=1, title="Test Story 2.1")

    # Create a completed workflow execution
    completed_result = {
        "steps": [
            {
                "name": "Read story file",
                "status": "completed",
                "started_at": "2025-01-16T10:00:00Z",
                "completed_at": "2025-01-16T10:00:05Z",
                "duration": 5,
                "tool_calls": [
                    {
                        "tool": "Read",
                        "args": {"file_path": "docs/stories/story-1.1.md"}
                    }
                ],
                "outputs": ["Successfully read 180 lines"]
            },
            {
                "name": "Implement components",
                "status": "completed",
                "started_at": "2025-01-16T10:00:05Z",
                "completed_at": "2025-01-16T10:30:12Z",
                "duration": 1807,
                "tool_calls": [
                    {
                        "tool": "Write",
                        "args": {"file_path": "src/components/TestComponent.tsx"}
                    }
                ],
                "outputs": ["Created component", "280 lines of code"]
            }
        ],
        "variables": {
            "epic": "1",
            "story_num": "1",
            "feature": "web-interface",
            "prd_location": "docs/PRD.md"
        },
        "artifacts": [
            {
                "path": "src/components/TestComponent.tsx",
                "type": "typescript",
                "size": 3456,
                "created_at": "2025-01-16T10:15:00Z"
            },
            {
                "path": "src/stores/testStore.ts",
                "type": "typescript",
                "size": 2890,
                "created_at": "2025-01-16T10:20:00Z"
            }
        ]
    }

    state_tracker.track_workflow_execution(
        workflow_id="wf-completed-123",
        epic_num=1,
        story_num=1,
        workflow_name="Story Implementation"
    )

    # Manually update with proper JSON result and realistic timestamps (bypassing str() conversion)
    from datetime import timedelta
    start_time = datetime.now() - timedelta(minutes=45)
    end_time = datetime.now()

    conn = sqlite3.connect(str(db_path))
    # Update start time to be 45 minutes ago
    conn.execute(
        "UPDATE workflow_executions SET started_at = ? WHERE executor = ?",
        (start_time.isoformat(), "wf-completed-123")
    )
    # Update completion status and output
    conn.execute(
        "UPDATE workflow_executions SET status = ?, completed_at = ?, output = ? WHERE executor = ?",
        ("completed", end_time.isoformat(), json.dumps(completed_result), "wf-completed-123")
    )
    conn.commit()
    conn.close()

    # Create a failed workflow execution
    failed_result = {
        "steps": [
            {
                "name": "Read story file",
                "status": "completed",
                "started_at": "2025-01-16T11:00:00Z",
                "completed_at": "2025-01-16T11:00:05Z",
                "duration": 5,
                "tool_calls": [
                    {
                        "tool": "Read",
                        "args": {"file_path": "docs/stories/story-2.1.md"}
                    }
                ],
                "outputs": ["Successfully read 150 lines"]
            },
            {
                "name": "Compile TypeScript",
                "status": "failed",
                "started_at": "2025-01-16T11:00:05Z",
                "completed_at": "2025-01-16T11:00:15Z",
                "duration": 10,
                "tool_calls": [],
                "outputs": []
            }
        ],
        "variables": {
            "epic": "2",
            "story_num": "1"
        },
        "artifacts": [],
        "errors": [
            {
                "timestamp": "2025-01-16T11:00:15Z",
                "message": "TypeScript compilation failed",
                "stack_trace": "Error: Cannot find name 'Card'\n  at src/components/TestComponent.tsx:25:10",
                "step": "Compile TypeScript"
            }
        ]
    }

    state_tracker.track_workflow_execution(
        workflow_id="wf-failed-456",
        epic_num=2,
        story_num=1,
        workflow_name="Bug Fix"
    )

    # Manually update with proper JSON result (bypassing str() conversion)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "UPDATE workflow_executions SET status = ?, completed_at = ?, output = ? WHERE executor = ?",
        ("failed", datetime.now().isoformat(), json.dumps(failed_result), "wf-failed-456")
    )
    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def test_client(test_project_root: Path, test_db: Path) -> TestClient:
    """Create FastAPI test client with test database."""
    config = WebConfig()
    app = create_app(config)

    # Override project root for testing
    app.state.project_root = test_project_root

    return TestClient(app)


class TestWorkflowDetailsEndpoint:
    """Test GET /api/workflows/{workflow_id}/details endpoint (AC1)."""

    def test_endpoint_returns_workflow_details(self, test_client: TestClient):
        """AC1: Endpoint returns workflow metadata, steps, variables, artifacts, errors."""
        response = test_client.get("/api/workflows/wf-completed-123/details")

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "workflow" in data
        assert "steps" in data
        assert "variables" in data
        assert "artifacts" in data
        assert "errors" in data

        # Verify workflow metadata
        workflow = data["workflow"]
        assert workflow["workflow_id"] == "wf-completed-123"
        assert workflow["workflow_name"] == "Story Implementation"
        assert workflow["status"] == "completed"
        assert workflow["epic"] == 1
        assert workflow["story_num"] == 1
        assert "started_at" in workflow
        assert "completed_at" in workflow
        assert workflow["duration"] is not None

        # Verify steps
        assert len(data["steps"]) == 2
        assert data["steps"][0]["name"] == "Read story file"
        assert data["steps"][0]["status"] == "completed"
        assert data["steps"][0]["duration"] == 5
        assert len(data["steps"][0]["tool_calls"]) == 1

        # Verify variables
        assert data["variables"]["epic"] == "1"
        assert data["variables"]["story_num"] == "1"
        assert data["variables"]["feature"] == "web-interface"

        # Verify artifacts
        assert len(data["artifacts"]) == 2
        assert data["artifacts"][0]["path"] == "src/components/TestComponent.tsx"
        assert data["artifacts"][0]["type"] == "typescript"
        assert data["artifacts"][0]["size"] == 3456

        # Verify errors (should be None for completed workflow)
        assert data["errors"] is None

    def test_endpoint_returns_404_if_workflow_not_found(self, test_client: TestClient):
        """AC1: Endpoint returns 404 if workflow_id not found."""
        response = test_client.get("/api/workflows/wf-nonexistent/details")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_endpoint_returns_errors_for_failed_workflow(self, test_client: TestClient):
        """AC1: Errors section populated for failed workflows."""
        response = test_client.get("/api/workflows/wf-failed-456/details")

        assert response.status_code == 200
        data = response.json()

        # Verify workflow status
        assert data["workflow"]["status"] == "failed"

        # Verify errors array
        assert data["errors"] is not None
        assert len(data["errors"]) == 1

        error = data["errors"][0]
        assert error["message"] == "TypeScript compilation failed"
        assert error["step"] == "Compile TypeScript"
        assert "stack_trace" in error
        assert "Cannot find name 'Card'" in error["stack_trace"]

    def test_endpoint_calculates_duration_correctly(self, test_client: TestClient):
        """AC1: Duration calculated from started_at and completed_at."""
        response = test_client.get("/api/workflows/wf-completed-123/details")

        assert response.status_code == 200
        data = response.json()

        # Verify duration is present and reasonable
        workflow = data["workflow"]
        assert workflow["duration"] is not None
        assert isinstance(workflow["duration"], int)
        assert workflow["duration"] > 0

    def test_endpoint_handles_missing_database(self, test_project_root: Path):
        """AC1: Endpoint returns 404 if database doesn't exist."""
        # Create client without database
        config = WebConfig()
        app = create_app(config)
        app.state.project_root = test_project_root / "nonexistent"
        client = TestClient(app)

        response = client.get("/api/workflows/wf-123/details")

        assert response.status_code == 404
        assert "database not found" in response.json()["detail"].lower()

    def test_steps_parsed_correctly_from_result(self, test_client: TestClient):
        """AC1: Steps extracted and parsed from workflow result JSON."""
        response = test_client.get("/api/workflows/wf-completed-123/details")

        assert response.status_code == 200
        data = response.json()

        steps = data["steps"]
        assert len(steps) == 2

        # Verify step structure
        step1 = steps[0]
        assert step1["name"] == "Read story file"
        assert step1["status"] == "completed"
        assert step1["started_at"] == "2025-01-16T10:00:00Z"
        assert step1["completed_at"] == "2025-01-16T10:00:05Z"
        assert step1["duration"] == 5
        assert len(step1["tool_calls"]) == 1
        assert step1["tool_calls"][0]["tool"] == "Read"
        assert len(step1["outputs"]) == 1

    def test_variables_extracted_from_result(self, test_client: TestClient):
        """AC1: Variables extracted from workflow execution context."""
        response = test_client.get("/api/workflows/wf-completed-123/details")

        assert response.status_code == 200
        data = response.json()

        variables = data["variables"]
        assert variables["epic"] == "1"
        assert variables["story_num"] == "1"
        assert variables["feature"] == "web-interface"
        assert variables["prd_location"] == "docs/PRD.md"

    def test_artifacts_listed_with_metadata(self, test_client: TestClient):
        """AC1: Artifacts listed with file path, type, size, created_at."""
        response = test_client.get("/api/workflows/wf-completed-123/details")

        assert response.status_code == 200
        data = response.json()

        artifacts = data["artifacts"]
        assert len(artifacts) == 2

        # Verify artifact structure
        artifact = artifacts[0]
        assert "path" in artifact
        assert "type" in artifact
        assert "size" in artifact
        assert "created_at" in artifact

        assert artifact["path"] == "src/components/TestComponent.tsx"
        assert artifact["type"] == "typescript"
        assert artifact["size"] == 3456

    def test_errors_displayed_if_workflow_failed(self, test_client: TestClient):
        """AC1: Errors section displays error messages, stack traces, timestamps."""
        response = test_client.get("/api/workflows/wf-failed-456/details")

        assert response.status_code == 200
        data = response.json()

        errors = data["errors"]
        assert errors is not None
        assert len(errors) == 1

        error = errors[0]
        assert "message" in error
        assert "stack_trace" in error
        assert "timestamp" in error
        assert "step" in error

        assert error["message"] == "TypeScript compilation failed"
        assert "Cannot find name 'Card'" in error["stack_trace"]
        assert error["step"] == "Compile TypeScript"


class TestWorkflowDetailPanelIntegration:
    """Integration tests for frontend detail panel (AC2-12).

    Note: These are primarily validated through manual E2E testing.
    Backend tests above ensure API contract is correct.
    """

    def test_endpoint_supports_panel_opening(self, test_client: TestClient):
        """AC2: Detail panel can fetch data when workflow is clicked."""
        # Verify endpoint is accessible and returns correct data
        response = test_client.get("/api/workflows/wf-completed-123/details")

        assert response.status_code == 200
        data = response.json()

        # Verify all sections needed for panel are present
        assert "workflow" in data
        assert "steps" in data
        assert "variables" in data
        assert "artifacts" in data

    def test_workflow_metadata_complete(self, test_client: TestClient):
        """AC4: Metadata section has all required fields."""
        response = test_client.get("/api/workflows/wf-completed-123/details")

        assert response.status_code == 200
        workflow = response.json()["workflow"]

        # Verify all metadata fields present
        required_fields = [
            "id", "workflow_id", "workflow_name", "status",
            "started_at", "completed_at", "duration", "agent",
            "epic", "story_num"
        ]

        for field in required_fields:
            assert field in workflow, f"Missing required field: {field}"

    def test_steps_structure_supports_accordion(self, test_client: TestClient):
        """AC5-6: Steps have structure needed for accordion display."""
        response = test_client.get("/api/workflows/wf-completed-123/details")

        assert response.status_code == 200
        steps = response.json()["steps"]

        for step in steps:
            # Verify step header fields
            assert "name" in step
            assert "status" in step
            assert "duration" in step

            # Verify expandable content fields
            assert "tool_calls" in step
            assert "outputs" in step
            assert "started_at" in step
            assert "completed_at" in step

    def test_variables_structure_supports_table(self, test_client: TestClient):
        """AC7: Variables structure supports key-value table."""
        response = test_client.get("/api/workflows/wf-completed-123/details")

        assert response.status_code == 200
        variables = response.json()["variables"]

        # Verify it's a dictionary (key-value pairs)
        assert isinstance(variables, dict)
        assert len(variables) > 0

    def test_artifacts_structure_supports_file_links(self, test_client: TestClient):
        """AC8: Artifacts have file path for linking to Files tab."""
        response = test_client.get("/api/workflows/wf-completed-123/details")

        assert response.status_code == 200
        artifacts = response.json()["artifacts"]

        for artifact in artifacts:
            assert "path" in artifact
            assert "type" in artifact
            assert "size" in artifact

            # Verify path is a valid file path
            assert isinstance(artifact["path"], str)
            assert len(artifact["path"]) > 0

    def test_errors_structure_supports_error_display(self, test_client: TestClient):
        """AC9: Errors have all fields needed for Alert display."""
        response = test_client.get("/api/workflows/wf-failed-456/details")

        assert response.status_code == 200
        errors = response.json()["errors"]

        assert errors is not None
        assert len(errors) > 0

        for error in errors:
            # Verify all error fields present
            assert "timestamp" in error
            assert "message" in error
            assert "stack_trace" in error
            assert "step" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
