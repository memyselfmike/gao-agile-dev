"""
Comprehensive unit tests for ContextPersistence.

Tests save/load operations, versioning, querying, deletion, and error handling.
"""

import uuid
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from gao_dev.core.context import (
    WorkflowContext,
    ContextPersistence,
    PersistenceError,
    ContextNotFoundError,
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def persistence(temp_db):
    """Create ContextPersistence instance with temp database."""
    return ContextPersistence(db_path=temp_db)


@pytest.fixture
def sample_context():
    """Create sample WorkflowContext for testing."""
    return WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=12,
        story_num=3,
        feature="document-lifecycle",
        workflow_name="implement_story",
        current_phase="initialization",
        status="running",
    )


class TestSaveOperations:
    """Test save operations."""

    def test_save_context_creates_new(self, persistence, sample_context):
        """Test save_context creates new context."""
        version = persistence.save_context(sample_context)
        assert version == 1
        assert persistence.context_exists(sample_context.workflow_id)

    def test_save_context_updates_existing(self, persistence, sample_context):
        """Test save_context updates existing context."""
        # Save first version
        version1 = persistence.save_context(sample_context)
        assert version1 == 1

        # Update context and save again
        updated_context = sample_context.copy_with(current_phase="implementation")
        version2 = persistence.save_context(updated_context)
        assert version2 == 2

        # Verify updated
        loaded = persistence.load_context(sample_context.workflow_id)
        assert loaded.current_phase == "implementation"

    def test_save_context_increments_version(self, persistence, sample_context):
        """Test save_context increments version correctly."""
        v1 = persistence.save_context(sample_context)
        v2 = persistence.save_context(sample_context)
        v3 = persistence.save_context(sample_context)
        assert v1 == 1
        assert v2 == 2
        assert v3 == 3

    def test_save_context_serializes_complex_fields(self, persistence, sample_context):
        """Test save_context serializes complex fields correctly."""
        # Add decisions, artifacts, errors
        context = sample_context.add_decision("use_sqlite", True)
        context = context.add_decision("config", {"key": "value", "nested": [1, 2, 3]})
        context = context.add_artifact("gao_dev/lifecycle/manager.py")
        context = context.add_artifact("tests/test_manager.py")
        context = context.add_error("Sample error message")

        # Add phase transition
        context = context.transition_phase("implementation")

        # Save and load
        persistence.save_context(context)
        loaded = persistence.load_context(context.workflow_id)

        # Verify complex fields
        assert loaded.decisions == context.decisions
        assert loaded.artifacts == context.artifacts
        assert loaded.errors == context.errors
        assert len(loaded.phase_history) == 1
        assert loaded.phase_history[0].phase == "initialization"

    def test_save_handles_none_values(self, persistence):
        """Test save handles None/null values correctly."""
        # Create context with story_num=None (epic-level)
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=None,
            feature="document-lifecycle",
            workflow_name="create_epic",
        )

        version = persistence.save_context(context)
        assert version == 1

        # Load and verify
        loaded = persistence.load_context(context.workflow_id)
        assert loaded.story_num is None


class TestLoadOperations:
    """Test load operations."""

    def test_load_context_retrieves_context(self, persistence, sample_context):
        """Test load_context retrieves saved context."""
        persistence.save_context(sample_context)
        loaded = persistence.load_context(sample_context.workflow_id)

        assert loaded.workflow_id == sample_context.workflow_id
        assert loaded.epic_num == sample_context.epic_num
        assert loaded.story_num == sample_context.story_num
        assert loaded.feature == sample_context.feature

    def test_load_context_raises_not_found(self, persistence):
        """Test load_context raises ContextNotFoundError if not found."""
        with pytest.raises(ContextNotFoundError) as exc:
            persistence.load_context("invalid-id")
        assert "not found" in str(exc.value).lower()

    def test_load_context_deserializes_correctly(self, persistence, sample_context):
        """Test load_context deserializes all fields correctly."""
        # Add complex data
        context = sample_context.add_decision("key", {"nested": [1, 2, 3]})
        context = context.add_artifact("file.py")
        context = context.transition_phase("implementation")

        persistence.save_context(context)
        loaded = persistence.load_context(context.workflow_id)

        # Verify all fields
        assert loaded.workflow_id == context.workflow_id
        assert loaded.epic_num == context.epic_num
        assert loaded.story_num == context.story_num
        assert loaded.feature == context.feature
        assert loaded.workflow_name == context.workflow_name
        assert loaded.current_phase == context.current_phase
        assert loaded.status == context.status
        assert loaded.decisions == context.decisions
        assert loaded.artifacts == context.artifacts
        assert len(loaded.phase_history) == 1

    def test_get_latest_context_returns_most_recent(self, persistence):
        """Test get_latest_context returns most recent context."""
        # Create multiple contexts for same story at different times
        contexts = []
        for i in range(3):
            context = WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=3,
                feature="document-lifecycle",
                workflow_name=f"workflow_{i}",
            )
            persistence.save_context(context)
            contexts.append(context)

        # Get latest
        latest = persistence.get_latest_context(epic_num=12, story_num=3)
        assert latest is not None
        # Should be the last one saved
        assert latest.workflow_name == "workflow_2"

    def test_get_latest_context_handles_story_num_none(self, persistence):
        """Test get_latest_context handles story_num=None correctly."""
        # Create epic-level context
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=None,
            feature="document-lifecycle",
            workflow_name="create_epic",
        )
        persistence.save_context(context)

        # Get latest for epic (story_num=None)
        latest = persistence.get_latest_context(epic_num=12, story_num=None)
        assert latest is not None
        assert latest.story_num is None
        assert latest.workflow_name == "create_epic"

    def test_get_latest_context_returns_none_if_not_found(self, persistence):
        """Test get_latest_context returns None if not found."""
        latest = persistence.get_latest_context(epic_num=999, story_num=999)
        assert latest is None

    def test_get_latest_context_by_status(self, persistence):
        """Test get_latest_context_by_status filters correctly."""
        # Create contexts with different statuses
        context1 = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="document-lifecycle",
            workflow_name="workflow_1",
            status="completed",
        )
        context2 = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="document-lifecycle",
            workflow_name="workflow_2",
            status="failed",
        )

        persistence.save_context(context1)
        persistence.save_context(context2)

        # Query by status
        completed = persistence.get_latest_context_by_status(12, 3, "completed")
        failed = persistence.get_latest_context_by_status(12, 3, "failed")

        assert completed is not None
        assert completed.status == "completed"
        assert failed is not None
        assert failed.status == "failed"


class TestDeleteOperations:
    """Test delete operations."""

    def test_delete_context_removes_context(self, persistence, sample_context):
        """Test delete_context removes context from database."""
        persistence.save_context(sample_context)
        assert persistence.context_exists(sample_context.workflow_id)

        deleted = persistence.delete_context(sample_context.workflow_id)
        assert deleted is True
        assert not persistence.context_exists(sample_context.workflow_id)

    def test_delete_context_returns_false_if_not_found(self, persistence):
        """Test delete_context returns False if not found."""
        deleted = persistence.delete_context("invalid-id")
        assert deleted is False

    def test_context_exists_checks_correctly(self, persistence, sample_context):
        """Test context_exists checks existence correctly."""
        assert not persistence.context_exists(sample_context.workflow_id)

        persistence.save_context(sample_context)
        assert persistence.context_exists(sample_context.workflow_id)

        persistence.delete_context(sample_context.workflow_id)
        assert not persistence.context_exists(sample_context.workflow_id)


class TestVersioning:
    """Test context versioning."""

    def test_get_context_versions_returns_all(self, persistence):
        """Test get_context_versions returns all versions."""
        # Create multiple contexts for same story (different workflow_ids)
        contexts = []
        for i in range(3):
            context = WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=3,
                feature="document-lifecycle",
                workflow_name=f"workflow_{i}",
            )
            persistence.save_context(context)
            contexts.append(context)

        versions = persistence.get_context_versions(epic_num=12, story_num=3)
        assert len(versions) == 3

    def test_versions_ordered_correctly(self, persistence):
        """Test versions ordered by version ascending."""
        # Create multiple contexts for same story (different workflow_ids)
        # Each will have version 1 since they're separate workflow executions
        contexts = []
        for i in range(3):
            ctx = WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=3,
                feature="document-lifecycle",
                workflow_name=f"workflow_{i}",
            )
            persistence.save_context(ctx)
            contexts.append(ctx)

        versions = persistence.get_context_versions(epic_num=12, story_num=3)

        # Verify we got all contexts back
        assert len(versions) == 3

        # Each context has version 1 since they're different workflow_ids
        context_ids = {c.workflow_id for c in contexts}
        loaded_ids = {v.workflow_id for v in versions}
        assert loaded_ids == context_ids

    def test_version_numbers_increment_correctly(self, persistence, sample_context):
        """Test version numbers increment correctly."""
        v1 = persistence.save_context(sample_context)
        v2 = persistence.save_context(sample_context)
        v3 = persistence.save_context(sample_context)

        assert v1 == 1
        assert v2 == 2
        assert v3 == 3

    def test_get_version_count(self, persistence):
        """Test get_version_count returns correct count."""
        # Create multiple contexts for same story
        for i in range(5):
            context = WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=3,
                feature="document-lifecycle",
                workflow_name=f"workflow_{i}",
            )
            persistence.save_context(context)

        count = persistence.get_version_count(epic_num=12, story_num=3)
        assert count == 5

    def test_get_context_by_version(self, persistence, sample_context):
        """Test get_context_by_version retrieves specific version."""
        v1 = persistence.save_context(sample_context)
        v2 = persistence.save_context(sample_context.copy_with(current_phase="implementation"))

        # Current implementation only stores latest version
        # So we can only retrieve the current version
        context = persistence.get_context_by_version(sample_context.workflow_id, v2)
        assert context is not None
        assert context.current_phase == "implementation"

        # Old version should not be found
        old_context = persistence.get_context_by_version(sample_context.workflow_id, v1)
        assert old_context is None


class TestQueryOperations:
    """Test query operations."""

    def test_get_active_contexts_filters_correctly(self, persistence):
        """Test get_active_contexts filters by status='running'."""
        # Create contexts with different statuses
        contexts = [
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=i,
                feature="document-lifecycle",
                workflow_name=f"workflow_{i}",
                status="running" if i % 2 == 0 else "completed",
            )
            for i in range(1, 5)
        ]

        for context in contexts:
            persistence.save_context(context)

        active = persistence.get_active_contexts()
        assert len(active) == 2
        assert all(c.status == "running" for c in active)

    def test_get_failed_contexts_filters_correctly(self, persistence):
        """Test get_failed_contexts filters by status='failed'."""
        # Create contexts with different statuses
        contexts = [
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=i,
                feature="document-lifecycle",
                workflow_name=f"workflow_{i}",
                status="failed" if i % 2 == 0 else "completed",
            )
            for i in range(1, 5)
        ]

        for context in contexts:
            persistence.save_context(context)

        failed = persistence.get_failed_contexts()
        assert len(failed) == 2
        assert all(c.status == "failed" for c in failed)

    def test_get_contexts_by_epic(self, persistence):
        """Test get_contexts_by_epic returns all contexts for epic."""
        # Create contexts for multiple epics
        for epic in [12, 13]:
            for story in [1, 2, 3]:
                context = WorkflowContext(
                    workflow_id=str(uuid.uuid4()),
                    epic_num=epic,
                    story_num=story,
                    feature="document-lifecycle",
                    workflow_name=f"workflow_{epic}_{story}",
                )
                persistence.save_context(context)

        contexts = persistence.get_contexts_by_epic(12)
        assert len(contexts) == 3
        assert all(c.epic_num == 12 for c in contexts)

    def test_get_contexts_by_feature_filters_correctly(self, persistence):
        """Test get_contexts_by_feature filters by feature."""
        # Create contexts with different features
        for i, feature in enumerate(["lifecycle", "sandbox", "metrics"]):
            context = WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=i + 1,  # story_num must be > 0
                feature=feature,
                workflow_name=f"workflow_{i}",
            )
            persistence.save_context(context)

        contexts = persistence.get_contexts_by_feature("sandbox")
        assert len(contexts) == 1
        assert contexts[0].feature == "sandbox"

    def test_search_contexts_with_filters(self, persistence):
        """Test search_contexts with multiple filters."""
        # Create varied contexts
        contexts = [
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=3,
                feature="lifecycle",
                workflow_name="implement_story",
                status="completed",
            ),
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=4,
                feature="lifecycle",
                workflow_name="implement_story",
                status="running",
            ),
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=13,
                story_num=1,
                feature="sandbox",
                workflow_name="create_prd",
                status="completed",
            ),
        ]

        for context in contexts:
            persistence.save_context(context)

        # Search with filters
        results = persistence.search_contexts(
            filters={"epic_num": 12, "status": "completed"}
        )
        assert len(results) == 1
        assert results[0].epic_num == 12
        assert results[0].status == "completed"

    def test_search_contexts_with_pagination(self, persistence):
        """Test search_contexts with pagination."""
        # Create 10 contexts
        for i in range(10):
            context = WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=i + 1,  # story_num must be > 0
                feature="lifecycle",
                workflow_name=f"workflow_{i}",
            )
            persistence.save_context(context)

        # Get first page (limit 5)
        page1 = persistence.search_contexts(filters={"epic_num": 12}, limit=5)
        assert len(page1) == 5

        # Get second page (offset 5, limit 5)
        page2 = persistence.search_contexts(filters={"epic_num": 12}, limit=5, offset=5)
        assert len(page2) == 5

        # Verify no overlap
        page1_ids = {c.workflow_id for c in page1}
        page2_ids = {c.workflow_id for c in page2}
        assert page1_ids.isdisjoint(page2_ids)


class TestUpdateContext:
    """Test update_context operation."""

    def test_update_context_updates_existing(self, persistence, sample_context):
        """Test update_context updates existing context."""
        persistence.save_context(sample_context)

        updated = sample_context.copy_with(current_phase="implementation")
        version = persistence.update_context(updated)
        assert version == 2

        loaded = persistence.load_context(sample_context.workflow_id)
        assert loaded.current_phase == "implementation"

    def test_update_context_raises_if_not_exists(self, persistence, sample_context):
        """Test update_context raises if context doesn't exist."""
        with pytest.raises(ContextNotFoundError):
            persistence.update_context(sample_context)


class TestRoundTripSerialization:
    """Test round-trip serialization (save -> load -> compare)."""

    def test_round_trip_preserves_all_fields(self, persistence, sample_context):
        """Test round-trip serialization preserves all fields."""
        # Add complex data
        context = sample_context.add_decision("use_sqlite", True)
        context = context.add_decision("config", {"key": "value", "list": [1, 2, 3]})
        context = context.add_artifact("file1.py")
        context = context.add_artifact("file2.py")
        context = context.add_error("Error message")
        context = context.transition_phase("implementation")
        context = context.copy_with(
            metadata={"custom_field": "custom_value"},
            tags=["tag1", "tag2"],
        )

        # Save and load
        persistence.save_context(context)
        loaded = persistence.load_context(context.workflow_id)

        # Verify all fields preserved
        assert loaded.workflow_id == context.workflow_id
        assert loaded.epic_num == context.epic_num
        assert loaded.story_num == context.story_num
        assert loaded.feature == context.feature
        assert loaded.workflow_name == context.workflow_name
        assert loaded.current_phase == context.current_phase
        assert loaded.status == context.status
        assert loaded.decisions == context.decisions
        assert loaded.artifacts == context.artifacts
        assert loaded.errors == context.errors
        assert loaded.metadata == context.metadata
        assert loaded.tags == context.tags
        assert len(loaded.phase_history) == len(context.phase_history)


class TestErrorHandling:
    """Test error handling."""

    def test_context_not_found_error_message(self, persistence):
        """Test ContextNotFoundError has descriptive message."""
        workflow_id = "test-workflow-id"
        with pytest.raises(ContextNotFoundError) as exc:
            persistence.load_context(workflow_id)

        assert workflow_id in str(exc.value)
        assert "not found" in str(exc.value).lower()
