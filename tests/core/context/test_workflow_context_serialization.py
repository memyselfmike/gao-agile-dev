"""
Unit tests for WorkflowContext serialization.

Tests serialization and deserialization including:
- to_dict() / from_dict()
- to_json() / from_json()
- Round-trip serialization
- Edge cases (None values, nested objects)
"""

import uuid
import json
import pytest
from gao_dev.core.context import WorkflowContext, PhaseTransition


class TestWorkflowContextSerialization:
    """Test WorkflowContext serialization methods."""

    def test_to_dict_returns_valid_dict(self):
        """Test that to_dict() returns valid dictionary."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        data = context.to_dict()

        assert isinstance(data, dict)
        assert data["workflow_id"] == context.workflow_id
        assert data["epic_num"] == 12
        assert data["story_num"] == 3
        assert data["feature"] == "test-feature"
        assert data["workflow_name"] == "test_workflow"

    def test_to_dict_excludes_internal_cache(self):
        """Test that to_dict() excludes internal cache."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Load a document to populate cache
        _ = context.prd
        assert "prd" in context._document_cache

        # Serialize
        data = context.to_dict()

        # Cache should not be in output
        assert "_document_cache" not in data

    def test_to_dict_includes_all_fields(self):
        """Test that to_dict() includes all fields."""
        workflow_id = str(uuid.uuid4())
        context = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Add some data
        context = (
            context.add_decision("use_sqlite", True)
            .add_artifact("file1.py")
            .add_error("Test error")
            .transition_phase("implementation")
        )

        data = context.to_dict()

        # Identity fields
        assert data["workflow_id"] == workflow_id
        assert data["epic_num"] == 12
        assert data["story_num"] == 3
        assert data["feature"] == "test-feature"
        assert data["workflow_name"] == "test_workflow"

        # State fields
        assert data["current_phase"] == "implementation"
        assert len(data["phase_history"]) == 1
        assert data["decisions"] == {"use_sqlite": True}
        assert data["artifacts"] == ["file1.py"]
        assert data["errors"] == ["Test error"]
        assert data["status"] == "running"

        # Metadata fields
        assert "created_at" in data
        assert "updated_at" in data
        assert "metadata" in data
        assert "tags" in data

    def test_from_dict_creates_instance(self):
        """Test that from_dict() creates WorkflowContext instance."""
        workflow_id = str(uuid.uuid4())
        data = {
            "workflow_id": workflow_id,
            "epic_num": 12,
            "story_num": 3,
            "feature": "test-feature",
            "workflow_name": "test_workflow",
            "current_phase": "initialization",
            "phase_history": [],
            "decisions": {},
            "artifacts": [],
            "errors": [],
            "status": "running",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
            "metadata": {},
            "tags": [],
        }

        context = WorkflowContext.from_dict(data)

        assert isinstance(context, WorkflowContext)
        assert context.workflow_id == workflow_id
        assert context.epic_num == 12
        assert context.story_num == 3

    def test_from_dict_converts_phase_history(self):
        """Test that from_dict() converts phase_history dicts to objects."""
        workflow_id = str(uuid.uuid4())
        data = {
            "workflow_id": workflow_id,
            "epic_num": 12,
            "story_num": 3,
            "feature": "test-feature",
            "workflow_name": "test_workflow",
            "current_phase": "implementation",
            "phase_history": [
                {"phase": "initialization", "timestamp": "2024-01-01T12:00:00", "duration": None}
            ],
            "decisions": {},
            "artifacts": [],
            "errors": [],
            "status": "running",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
            "metadata": {},
            "tags": [],
        }

        context = WorkflowContext.from_dict(data)

        assert len(context.phase_history) == 1
        assert isinstance(context.phase_history[0], PhaseTransition)
        assert context.phase_history[0].phase == "initialization"

    def test_to_json_returns_valid_json(self):
        """Test that to_json() returns valid JSON string."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        json_str = context.to_json()

        assert isinstance(json_str, str)
        # Should be valid JSON
        data = json.loads(json_str)
        assert isinstance(data, dict)
        assert data["epic_num"] == 12

    def test_to_json_formatted_with_indentation(self):
        """Test that to_json() formats with indentation."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        json_str = context.to_json()

        # Should contain newlines (formatted)
        assert "\n" in json_str
        # Should contain indentation (2 spaces)
        assert "  " in json_str

    def test_from_json_creates_instance(self):
        """Test that from_json() creates WorkflowContext instance."""
        workflow_id = str(uuid.uuid4())
        json_str = f"""
        {{
            "workflow_id": "{workflow_id}",
            "epic_num": 12,
            "story_num": 3,
            "feature": "test-feature",
            "workflow_name": "test_workflow",
            "current_phase": "initialization",
            "phase_history": [],
            "decisions": {{}},
            "artifacts": [],
            "errors": [],
            "status": "running",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
            "metadata": {{}},
            "tags": []
        }}
        """

        context = WorkflowContext.from_json(json_str)

        assert isinstance(context, WorkflowContext)
        assert context.workflow_id == workflow_id
        assert context.epic_num == 12

    def test_from_json_handles_invalid_json(self):
        """Test that from_json() raises error for invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            WorkflowContext.from_json("not valid json")

    def test_round_trip_serialization_dict(self):
        """Test round-trip serialization with to_dict/from_dict."""
        workflow_id = str(uuid.uuid4())
        original = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Add some data
        original = (
            original.add_decision("use_sqlite", True)
            .add_decision("database_path", "/tmp/test.db")
            .add_artifact("gao_dev/lifecycle/manager.py")
            .add_artifact("tests/test_manager.py")
            .add_error("File not found")
            .transition_phase("implementation")
            .copy_with(tags=["feature:lifecycle", "priority:high"])
        )

        # Serialize and deserialize
        data = original.to_dict()
        restored = WorkflowContext.from_dict(data)

        # Verify all fields match
        assert restored.workflow_id == original.workflow_id
        assert restored.epic_num == original.epic_num
        assert restored.story_num == original.story_num
        assert restored.feature == original.feature
        assert restored.workflow_name == original.workflow_name
        assert restored.current_phase == original.current_phase
        assert len(restored.phase_history) == len(original.phase_history)
        assert restored.decisions == original.decisions
        assert restored.artifacts == original.artifacts
        assert restored.errors == original.errors
        assert restored.status == original.status
        assert restored.tags == original.tags

    def test_round_trip_serialization_json(self):
        """Test round-trip serialization with to_json/from_json."""
        workflow_id = str(uuid.uuid4())
        original = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Add some data
        original = (
            original.add_decision("use_sqlite", True)
            .add_artifact("file1.py")
            .transition_phase("implementation")
            .transition_phase("testing")
        )

        # Serialize and deserialize
        json_str = original.to_json()
        restored = WorkflowContext.from_json(json_str)

        # Verify all fields match
        assert restored.workflow_id == original.workflow_id
        assert restored.epic_num == original.epic_num
        assert restored.story_num == original.story_num
        assert restored.current_phase == original.current_phase
        assert len(restored.phase_history) == len(original.phase_history)
        assert restored.decisions == original.decisions
        assert restored.artifacts == original.artifacts

    def test_serialization_with_none_story_num(self):
        """Test serialization with story_num as None."""
        workflow_id = str(uuid.uuid4())
        original = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=None,  # Epic-level context
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Round-trip
        json_str = original.to_json()
        restored = WorkflowContext.from_json(json_str)

        assert restored.story_num is None
        assert restored.story_id == "12"

    def test_serialization_with_complex_decisions(self):
        """Test serialization with complex decision values."""
        workflow_id = str(uuid.uuid4())
        original = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Add complex decision values
        original = (
            original.add_decision("use_sqlite", True)
            .add_decision("database_config", {"path": "/tmp/test.db", "timeout": 30})
            .add_decision("agents", ["John", "Winston", "Amelia"])
            .add_decision("max_retries", 3)
        )

        # Round-trip
        json_str = original.to_json()
        restored = WorkflowContext.from_json(json_str)

        assert restored.decisions["use_sqlite"] is True
        assert restored.decisions["database_config"]["path"] == "/tmp/test.db"
        assert restored.decisions["database_config"]["timeout"] == 30
        assert restored.decisions["agents"] == ["John", "Winston", "Amelia"]
        assert restored.decisions["max_retries"] == 3

    def test_serialization_with_metadata(self):
        """Test serialization with custom metadata."""
        workflow_id = str(uuid.uuid4())
        original = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Add custom metadata
        original = original.copy_with(
            metadata={
                "user": "amelia",
                "priority": "high",
                "sprint": 5,
                "custom_data": {"nested": "value"},
            }
        )

        # Round-trip
        json_str = original.to_json()
        restored = WorkflowContext.from_json(json_str)

        assert restored.metadata["user"] == "amelia"
        assert restored.metadata["priority"] == "high"
        assert restored.metadata["sprint"] == 5
        assert restored.metadata["custom_data"]["nested"] == "value"

    def test_serialization_preserves_phase_history(self):
        """Test that serialization preserves phase_history with durations."""
        workflow_id = str(uuid.uuid4())
        original = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Transition through phases
        original = (
            original.transition_phase("planning")
            .transition_phase("implementation")
            .transition_phase("testing")
        )

        # Round-trip
        json_str = original.to_json()
        restored = WorkflowContext.from_json(json_str)

        # Verify phase history
        assert len(restored.phase_history) == 3
        assert restored.phase_history[0].phase == "initialization"
        assert restored.phase_history[0].duration is None
        assert restored.phase_history[1].phase == "planning"
        assert isinstance(restored.phase_history[1].duration, float)
        assert restored.phase_history[2].phase == "implementation"
        assert isinstance(restored.phase_history[2].duration, float)

    def test_serialization_handles_empty_lists(self):
        """Test that serialization handles empty lists."""
        workflow_id = str(uuid.uuid4())
        original = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Don't add any artifacts, errors, or tags
        json_str = original.to_json()
        restored = WorkflowContext.from_json(json_str)

        assert restored.artifacts == []
        assert restored.errors == []
        assert restored.tags == []
        assert restored.phase_history == []

    def test_serialization_handles_empty_dicts(self):
        """Test that serialization handles empty dicts."""
        workflow_id = str(uuid.uuid4())
        original = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Don't add any decisions or metadata
        json_str = original.to_json()
        restored = WorkflowContext.from_json(json_str)

        assert restored.decisions == {}
        assert restored.metadata == {}


class TestWorkflowContextEdgeCases:
    """Test edge cases and error handling."""

    def test_from_dict_with_missing_optional_fields(self):
        """Test from_dict with missing optional fields uses defaults."""
        workflow_id = str(uuid.uuid4())
        data = {
            "workflow_id": workflow_id,
            "epic_num": 12,
            "story_num": 3,
            "feature": "test-feature",
            "workflow_name": "test_workflow",
            # Missing all optional fields
        }

        context = WorkflowContext.from_dict(data)

        # Should use defaults
        assert context.current_phase == "initialization"
        assert context.phase_history == []
        assert context.decisions == {}
        assert context.artifacts == []
        assert context.errors == []
        assert context.status == "running"

    def test_serialization_with_multiple_errors(self):
        """Test serialization with multiple errors."""
        workflow_id = str(uuid.uuid4())
        original = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Add multiple errors
        original = (
            original.add_error("Error 1")
            .add_error("Error 2")
            .add_error("Error 3")
        )

        json_str = original.to_json()
        restored = WorkflowContext.from_json(json_str)

        assert len(restored.errors) == 3
        assert restored.errors == ["Error 1", "Error 2", "Error 3"]

    def test_serialization_with_many_artifacts(self):
        """Test serialization with many artifacts."""
        workflow_id = str(uuid.uuid4())
        original = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Add many artifacts
        for i in range(10):
            original = original.add_artifact(f"file{i}.py")

        json_str = original.to_json()
        restored = WorkflowContext.from_json(json_str)

        assert len(restored.artifacts) == 10
        assert restored.artifacts == [f"file{i}.py" for i in range(10)]
