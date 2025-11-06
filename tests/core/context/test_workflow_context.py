"""
Unit tests for WorkflowContext data model.

Tests core functionality including:
- Initialization and validation
- Lazy loading of documents
- Immutable operations (add_decision, add_artifact, add_error, transition_phase)
- Copy-on-write pattern
- Properties (story_id, __repr__)
"""

import uuid
import pytest
from datetime import datetime
from gao_dev.core.context import WorkflowContext, PhaseTransition


class TestPhaseTransitionModel:
    """Test PhaseTransition data model."""

    def test_phase_transition_with_duration(self):
        """Test PhaseTransition repr with duration."""
        transition = PhaseTransition(
            phase="implementation",
            timestamp="2024-01-01T12:00:00",
            duration=123.45
        )
        repr_str = repr(transition)
        assert "PhaseTransition" in repr_str
        assert "implementation" in repr_str
        assert "123.45" in repr_str

    def test_phase_transition_without_duration(self):
        """Test PhaseTransition repr without duration."""
        transition = PhaseTransition(
            phase="initialization",
            timestamp="2024-01-01T12:00:00",
            duration=None
        )
        repr_str = repr(transition)
        assert "PhaseTransition" in repr_str
        assert "initialization" in repr_str
        assert "duration" not in repr_str.lower() or "None" not in repr_str


class TestWorkflowContextInitialization:
    """Test WorkflowContext initialization and validation."""

    def test_create_with_required_fields(self):
        """Test creating WorkflowContext with required fields."""
        workflow_id = str(uuid.uuid4())
        context = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=3,
            feature="document-lifecycle",
            workflow_name="implement_story",
        )

        assert context.workflow_id == workflow_id
        assert context.epic_num == 12
        assert context.story_num == 3
        assert context.feature == "document-lifecycle"
        assert context.workflow_name == "implement_story"

    def test_default_values_set_correctly(self):
        """Test that default values are set correctly."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        assert context.current_phase == "initialization"
        assert context.phase_history == []
        assert context.decisions == {}
        assert context.artifacts == []
        assert context.errors == []
        assert context.status == "running"
        assert context.metadata == {}
        assert context.tags == []
        assert context._document_cache == {}

    def test_timestamps_set_on_creation(self):
        """Test that timestamps are set on creation."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Verify timestamps are valid ISO 8601
        created = datetime.fromisoformat(context.created_at)
        updated = datetime.fromisoformat(context.updated_at)
        assert isinstance(created, datetime)
        assert isinstance(updated, datetime)

    def test_validates_workflow_id_is_uuid(self):
        """Test that workflow_id must be valid UUID."""
        with pytest.raises(ValueError, match="workflow_id must be valid UUID"):
            WorkflowContext(
                workflow_id="not-a-uuid",
                epic_num=12,
                story_num=3,
                feature="test-feature",
                workflow_name="test_workflow",
            )

    def test_validates_epic_num_positive(self):
        """Test that epic_num must be positive."""
        with pytest.raises(ValueError, match="epic_num must be positive"):
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=0,
                story_num=3,
                feature="test-feature",
                workflow_name="test_workflow",
            )

        with pytest.raises(ValueError, match="epic_num must be positive"):
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=-1,
                story_num=3,
                feature="test-feature",
                workflow_name="test_workflow",
            )

    def test_validates_story_num_positive_or_none(self):
        """Test that story_num must be positive or None."""
        # None is valid
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=None,
            feature="test-feature",
            workflow_name="test_workflow",
        )
        assert context.story_num is None

        # Zero is invalid
        with pytest.raises(ValueError, match="story_num must be positive"):
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=0,
                feature="test-feature",
                workflow_name="test_workflow",
            )

        # Negative is invalid
        with pytest.raises(ValueError, match="story_num must be positive"):
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=-1,
                feature="test-feature",
                workflow_name="test_workflow",
            )


class TestWorkflowContextLazyLoading:
    """Test lazy loading of documents."""

    def test_prd_property_lazy_loads(self):
        """Test that PRD property loads on first access."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Cache should be empty initially
        assert "prd" not in context._document_cache

        # Access property triggers load
        prd = context.prd

        # Cache should now contain prd
        assert "prd" in context._document_cache
        # Currently returns None (placeholder implementation)
        assert prd is None

    def test_architecture_property_lazy_loads(self):
        """Test that architecture property loads on first access."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        assert "architecture" not in context._document_cache
        arch = context.architecture
        assert "architecture" in context._document_cache
        assert arch is None

    def test_epic_definition_property_lazy_loads(self):
        """Test that epic_definition property loads on first access."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        assert "epic_definition" not in context._document_cache
        epic = context.epic_definition
        assert "epic_definition" in context._document_cache
        assert epic is None

    def test_story_definition_returns_none_if_story_num_none(self):
        """Test that story_definition returns None if story_num is None."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=None,  # Epic-level context
            feature="test-feature",
            workflow_name="test_workflow",
        )

        story = context.story_definition
        assert story is None
        # Cache should not be populated
        assert "story_definition" not in context._document_cache

    def test_story_definition_loads_if_story_num_set(self):
        """Test that story_definition loads if story_num is set."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        assert "story_definition" not in context._document_cache
        story = context.story_definition
        assert "story_definition" in context._document_cache
        assert story is None

    def test_documents_cached_after_first_load(self):
        """Test that documents are cached after first load."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Access PRD multiple times
        prd1 = context.prd
        prd2 = context.prd
        prd3 = context.prd

        # Should all be the same object (cached)
        assert prd1 is prd2
        assert prd2 is prd3

    def test_documents_only_loaded_once(self):
        """Test that documents are only loaded once."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Access all documents
        _ = context.prd
        _ = context.architecture
        _ = context.epic_definition
        _ = context.story_definition

        # All should be in cache
        assert len(context._document_cache) == 4
        assert "prd" in context._document_cache
        assert "architecture" in context._document_cache
        assert "epic_definition" in context._document_cache
        assert "story_definition" in context._document_cache


class TestWorkflowContextImmutableOperations:
    """Test immutable operations (copy-on-write pattern)."""

    def test_add_decision_returns_new_instance(self):
        """Test that add_decision returns new instance."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        new_context = context.add_decision("use_sqlite", True)

        assert new_context is not context
        assert new_context.decisions["use_sqlite"] is True

    def test_add_decision_does_not_modify_original(self):
        """Test that add_decision does not modify original."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        original_decisions = context.decisions.copy()
        new_context = context.add_decision("use_sqlite", True)

        # Original should be unchanged
        assert context.decisions == original_decisions
        assert "use_sqlite" not in context.decisions

        # New context should have decision
        assert "use_sqlite" in new_context.decisions

    def test_add_artifact_returns_new_instance(self):
        """Test that add_artifact returns new instance."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        new_context = context.add_artifact("gao_dev/lifecycle/manager.py")

        assert new_context is not context
        assert "gao_dev/lifecycle/manager.py" in new_context.artifacts

    def test_add_artifact_does_not_modify_original(self):
        """Test that add_artifact does not modify original."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        original_artifacts = context.artifacts.copy()
        new_context = context.add_artifact("gao_dev/lifecycle/manager.py")

        assert context.artifacts == original_artifacts
        assert len(context.artifacts) == 0
        assert len(new_context.artifacts) == 1

    def test_add_error_returns_new_instance(self):
        """Test that add_error returns new instance."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        new_context = context.add_error("File not found")

        assert new_context is not context
        assert "File not found" in new_context.errors

    def test_add_error_does_not_modify_original(self):
        """Test that add_error does not modify original."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        original_errors = context.errors.copy()
        new_context = context.add_error("File not found")

        assert context.errors == original_errors
        assert len(context.errors) == 0
        assert len(new_context.errors) == 1

    def test_transition_phase_returns_new_instance(self):
        """Test that transition_phase returns new instance."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        new_context = context.transition_phase("implementation")

        assert new_context is not context
        assert new_context.current_phase == "implementation"

    def test_transition_phase_updates_phase_history(self):
        """Test that transition_phase updates phase_history."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Initial state
        assert context.current_phase == "initialization"
        assert len(context.phase_history) == 0

        # Transition to implementation
        context2 = context.transition_phase("implementation")
        assert context2.current_phase == "implementation"
        assert len(context2.phase_history) == 1
        assert context2.phase_history[0].phase == "initialization"

        # Transition to testing
        context3 = context2.transition_phase("testing")
        assert context3.current_phase == "testing"
        assert len(context3.phase_history) == 2
        assert context3.phase_history[0].phase == "initialization"
        assert context3.phase_history[1].phase == "implementation"

    def test_transition_phase_calculates_duration(self):
        """Test that transition_phase calculates duration."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # First transition has no duration
        context2 = context.transition_phase("implementation")
        assert context2.phase_history[0].duration is None

        # Second transition has duration
        context3 = context2.transition_phase("testing")
        assert context3.phase_history[1].duration is not None
        assert isinstance(context3.phase_history[1].duration, float)
        assert context3.phase_history[1].duration >= 0

    def test_copy_with_returns_new_instance(self):
        """Test that copy_with returns new instance."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        new_context = context.copy_with(status="completed")

        assert new_context is not context
        assert new_context.status == "completed"
        assert context.status == "running"

    def test_copy_with_updates_updated_at(self):
        """Test that copy_with updates updated_at."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        original_updated_at = context.updated_at
        new_context = context.copy_with(status="completed")

        assert new_context.updated_at != original_updated_at

    def test_copy_with_preserves_document_cache(self):
        """Test that copy_with preserves document cache."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Load a document
        _ = context.prd
        assert "prd" in context._document_cache

        # Copy with changes
        new_context = context.copy_with(status="completed")

        # Cache should be preserved
        assert "prd" in new_context._document_cache

    def test_multiple_operations_chained(self):
        """Test that multiple operations can be chained."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        # Chain multiple operations
        final_context = (
            context.add_decision("use_sqlite", True)
            .add_artifact("gao_dev/lifecycle/manager.py")
            .add_artifact("tests/test_manager.py")
            .transition_phase("implementation")
            .add_error("Test failed")
        )

        # Original unchanged
        assert len(context.decisions) == 0
        assert len(context.artifacts) == 0
        assert len(context.errors) == 0
        assert context.current_phase == "initialization"

        # Final context has all changes
        assert len(final_context.decisions) == 1
        assert len(final_context.artifacts) == 2
        assert len(final_context.errors) == 1
        assert final_context.current_phase == "implementation"


class TestWorkflowContextProperties:
    """Test WorkflowContext properties."""

    def test_story_id_with_story_num(self):
        """Test story_id property with story_num set."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        assert context.story_id == "12.3"

    def test_story_id_without_story_num(self):
        """Test story_id property without story_num."""
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=None,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        assert context.story_id == "12"

    def test_repr_includes_key_info(self):
        """Test __repr__ includes key information."""
        workflow_id = str(uuid.uuid4())
        context = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=3,
            feature="test-feature",
            workflow_name="test_workflow",
        )

        repr_str = repr(context)

        assert "WorkflowContext" in repr_str
        assert workflow_id[:8] in repr_str
        assert "12.3" in repr_str
        assert "initialization" in repr_str
        assert "running" in repr_str
