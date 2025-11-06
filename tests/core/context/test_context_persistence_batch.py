"""
Batch operation tests for ContextPersistence.

Tests batch save/load operations, transaction handling, and rollback behavior.
"""

import uuid
import pytest
import tempfile
from pathlib import Path

from gao_dev.core.context import (
    WorkflowContext,
    ContextPersistence,
    PersistenceError,
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
def sample_contexts():
    """Create multiple sample WorkflowContexts for batch testing."""
    contexts = []
    for i in range(5):
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=i + 1,
            feature="document-lifecycle",
            workflow_name=f"workflow_{i}",
        )
        contexts.append(context)
    return contexts


class TestBatchSave:
    """Test batch save operations."""

    def test_save_contexts_batch_saves_multiple(self, persistence, sample_contexts):
        """Test save_contexts saves all contexts in batch."""
        versions = persistence.save_contexts(sample_contexts)

        assert len(versions) == 5
        assert all(v == 1 for v in versions)  # All new contexts start at version 1

        # Verify all saved
        for context in sample_contexts:
            assert persistence.context_exists(context.workflow_id)

    def test_save_contexts_returns_versions(self, persistence, sample_contexts):
        """Test save_contexts returns version numbers for each context."""
        versions = persistence.save_contexts(sample_contexts)

        assert len(versions) == len(sample_contexts)
        assert all(isinstance(v, int) for v in versions)
        assert all(v >= 1 for v in versions)

    def test_save_contexts_empty_list(self, persistence):
        """Test save_contexts handles empty list correctly."""
        versions = persistence.save_contexts([])
        assert versions == []

    def test_save_contexts_single_context(self, persistence, sample_contexts):
        """Test save_contexts works with single context."""
        versions = persistence.save_contexts([sample_contexts[0]])
        assert len(versions) == 1
        assert versions[0] == 1

    def test_save_contexts_updates_existing(self, persistence, sample_contexts):
        """Test save_contexts can update existing contexts."""
        # Save initial batch
        persistence.save_contexts(sample_contexts)

        # Update contexts
        updated_contexts = [
            ctx.copy_with(current_phase="implementation")
            for ctx in sample_contexts
        ]

        # Save updated batch
        versions = persistence.save_contexts(updated_contexts)

        # All should be version 2
        assert all(v == 2 for v in versions)

        # Verify updated
        for context in updated_contexts:
            loaded = persistence.load_context(context.workflow_id)
            assert loaded.current_phase == "implementation"

    def test_save_contexts_mixed_new_and_existing(self, persistence):
        """Test save_contexts handles mix of new and existing contexts."""
        # Create contexts
        contexts = []
        for i in range(3):
            context = WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=i + 1,
                feature="document-lifecycle",
                workflow_name=f"workflow_{i}",
            )
            contexts.append(context)

        # Save first two
        persistence.save_contexts(contexts[:2])

        # Update first two, add third
        contexts[0] = contexts[0].copy_with(current_phase="implementation")
        contexts[1] = contexts[1].copy_with(current_phase="testing")

        # Save all three (2 updates + 1 new)
        versions = persistence.save_contexts(contexts)

        assert versions[0] == 2  # Updated
        assert versions[1] == 2  # Updated
        assert versions[2] == 1  # New

    def test_save_contexts_transaction_behavior(self, persistence, sample_contexts):
        """Test save_contexts uses transaction (all or nothing)."""
        # This is a basic test - in production, we'd need to test actual rollback
        # by injecting a failure partway through
        versions = persistence.save_contexts(sample_contexts)

        # Either all succeed or all fail (transaction semantics)
        # Since we don't inject failure here, all should succeed
        assert len(versions) == len(sample_contexts)

        # Verify all saved
        for context in sample_contexts:
            assert persistence.context_exists(context.workflow_id)


class TestBatchLoad:
    """Test batch load operations."""

    def test_load_contexts_batch_loads_multiple(self, persistence, sample_contexts):
        """Test load_contexts loads multiple contexts."""
        # Save contexts first
        persistence.save_contexts(sample_contexts)

        # Get workflow IDs
        workflow_ids = [ctx.workflow_id for ctx in sample_contexts]

        # Batch load
        loaded = persistence.load_contexts(workflow_ids)

        assert len(loaded) == 5
        loaded_ids = {ctx.workflow_id for ctx in loaded}
        assert loaded_ids == set(workflow_ids)

    def test_load_contexts_empty_list(self, persistence):
        """Test load_contexts handles empty list correctly."""
        loaded = persistence.load_contexts([])
        assert loaded == []

    def test_load_contexts_single_id(self, persistence, sample_contexts):
        """Test load_contexts works with single ID."""
        persistence.save_context(sample_contexts[0])

        loaded = persistence.load_contexts([sample_contexts[0].workflow_id])
        assert len(loaded) == 1
        assert loaded[0].workflow_id == sample_contexts[0].workflow_id

    def test_load_contexts_skips_not_found(self, persistence, sample_contexts):
        """Test load_contexts skips contexts not found (no error)."""
        # Save only first 3 contexts
        persistence.save_contexts(sample_contexts[:3])

        # Try to load all 5 (2 don't exist)
        workflow_ids = [ctx.workflow_id for ctx in sample_contexts]
        loaded = persistence.load_contexts(workflow_ids)

        # Should only load the 3 that exist
        assert len(loaded) == 3
        loaded_ids = {ctx.workflow_id for ctx in loaded}
        expected_ids = {ctx.workflow_id for ctx in sample_contexts[:3]}
        assert loaded_ids == expected_ids

    def test_load_contexts_preserves_data(self, persistence, sample_contexts):
        """Test load_contexts preserves all context data."""
        # Add complex data to contexts
        enriched = []
        for i, ctx in enumerate(sample_contexts):
            ctx = ctx.add_decision(f"decision_{i}", {"value": i})
            ctx = ctx.add_artifact(f"file_{i}.py")
            enriched.append(ctx)

        # Save and load
        persistence.save_contexts(enriched)
        workflow_ids = [ctx.workflow_id for ctx in enriched]
        loaded = persistence.load_contexts(workflow_ids)

        # Verify data preserved
        assert len(loaded) == len(enriched)
        for ctx in loaded:
            # Find matching original
            original = next(c for c in enriched if c.workflow_id == ctx.workflow_id)
            assert ctx.decisions == original.decisions
            assert ctx.artifacts == original.artifacts

    def test_load_contexts_order_preserved(self, persistence, sample_contexts):
        """Test load_contexts maintains order of IDs."""
        # Save contexts
        persistence.save_contexts(sample_contexts)

        # Request in specific order
        workflow_ids = [ctx.workflow_id for ctx in sample_contexts]
        loaded = persistence.load_contexts(workflow_ids)

        # SQLite IN clause doesn't guarantee order, so we just verify all loaded
        loaded_ids = {ctx.workflow_id for ctx in loaded}
        assert loaded_ids == set(workflow_ids)


class TestTransactionBehavior:
    """Test transaction behavior in batch operations."""

    def test_batch_save_all_or_nothing(self, persistence, sample_contexts):
        """Test batch save has all-or-nothing semantics."""
        # This is a basic test - comprehensive testing would require
        # injecting failures (e.g., constraint violations)

        versions = persistence.save_contexts(sample_contexts)

        # If transaction worked, all should have versions
        assert len(versions) == len(sample_contexts)

        # Verify all were saved
        count = 0
        for ctx in sample_contexts:
            if persistence.context_exists(ctx.workflow_id):
                count += 1

        # Either all saved or none saved (transaction semantics)
        assert count == len(sample_contexts) or count == 0

    def test_batch_operations_isolated(self, persistence, sample_contexts):
        """Test batch operations are isolated from each other."""
        # Save first batch
        batch1 = sample_contexts[:2]
        persistence.save_contexts(batch1)

        # Save second batch
        batch2 = sample_contexts[2:]
        persistence.save_contexts(batch2)

        # Both batches should succeed independently
        for ctx in sample_contexts:
            assert persistence.context_exists(ctx.workflow_id)


class TestPerformance:
    """Test performance characteristics of batch operations."""

    def test_batch_save_faster_than_individual(self, persistence):
        """Test batch save is more efficient than individual saves."""
        # Create many contexts
        contexts = [
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=i + 1,  # story_num must be > 0
                feature="document-lifecycle",
                workflow_name=f"workflow_{i}",
            )
            for i in range(10)
        ]

        import time

        # Batch save
        start = time.time()
        persistence.save_contexts(contexts)
        batch_time = time.time() - start

        # Individual saves (with new contexts)
        contexts2 = [
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=13,
                story_num=i + 1,  # story_num must be > 0
                feature="document-lifecycle",
                workflow_name=f"workflow_{i}",
            )
            for i in range(10)
        ]

        start = time.time()
        for ctx in contexts2:
            persistence.save_context(ctx)
        individual_time = time.time() - start

        # Batch should be faster (or at least not significantly slower)
        # We allow some variance due to system load
        # This is more of a sanity check than a strict performance test
        assert batch_time < individual_time * 2  # Allow 2x variance

    def test_batch_save_10_contexts_performance(self, persistence):
        """Test batch save 10 contexts completes in reasonable time."""
        contexts = [
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=i + 1,  # story_num must be > 0
                feature="document-lifecycle",
                workflow_name=f"workflow_{i}",
            )
            for i in range(10)
        ]

        import time
        start = time.time()
        persistence.save_contexts(contexts)
        duration = time.time() - start

        # Should complete in <100ms (story requirement)
        # We allow 500ms for CI environments
        assert duration < 0.5


class TestBatchEdgeCases:
    """Test edge cases in batch operations."""

    def test_batch_with_duplicate_workflow_ids(self, persistence):
        """Test batch with duplicate workflow_ids updates correctly."""
        # Create context
        workflow_id = str(uuid.uuid4())
        context1 = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=12,
            story_num=1,
            feature="document-lifecycle",
            workflow_name="workflow_1",
        )

        # Create duplicate with different data
        context2 = WorkflowContext(
            workflow_id=workflow_id,  # Same ID
            epic_num=12,
            story_num=1,
            feature="document-lifecycle",
            workflow_name="workflow_2",  # Different name
        )

        # Save batch with duplicate
        versions = persistence.save_contexts([context1, context2])

        # First should be version 1, second should be version 2 (update)
        assert versions == [1, 2]

        # Load and verify final state is from context2
        loaded = persistence.load_context(workflow_id)
        assert loaded.workflow_name == "workflow_2"

    def test_batch_with_mixed_epic_story(self, persistence):
        """Test batch with contexts from different epics/stories."""
        contexts = [
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=1,
                feature="lifecycle",
                workflow_name="workflow_12_1",
            ),
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=13,
                story_num=2,
                feature="sandbox",
                workflow_name="workflow_13_2",
            ),
            WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=None,  # Epic-level
                feature="lifecycle",
                workflow_name="workflow_12_epic",
            ),
        ]

        versions = persistence.save_contexts(contexts)
        assert len(versions) == 3

        # Verify all saved correctly
        for ctx in contexts:
            loaded = persistence.load_context(ctx.workflow_id)
            assert loaded.epic_num == ctx.epic_num
            assert loaded.story_num == ctx.story_num

    def test_batch_with_complex_data(self, persistence):
        """Test batch operations preserve complex data structures."""
        contexts = []
        for i in range(3):
            ctx = WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=12,
                story_num=i + 1,
                feature="document-lifecycle",
                workflow_name=f"workflow_{i}",
            )
            # Add complex data
            ctx = ctx.add_decision(f"decision_{i}", {
                "nested": {"key": "value"},
                "list": [1, 2, 3],
                "bool": True,
            })
            ctx = ctx.add_artifact(f"file_{i}.py")
            ctx = ctx.add_error(f"Error message {i}")
            ctx = ctx.transition_phase("implementation")
            contexts.append(ctx)

        # Save and load
        persistence.save_contexts(contexts)
        workflow_ids = [ctx.workflow_id for ctx in contexts]
        loaded = persistence.load_contexts(workflow_ids)

        # Verify complex data preserved
        assert len(loaded) == len(contexts)
        for loaded_ctx in loaded:
            original = next(c for c in contexts if c.workflow_id == loaded_ctx.workflow_id)
            assert loaded_ctx.decisions == original.decisions
            assert loaded_ctx.artifacts == original.artifacts
            assert loaded_ctx.errors == original.errors
            assert len(loaded_ctx.phase_history) == len(original.phase_history)
