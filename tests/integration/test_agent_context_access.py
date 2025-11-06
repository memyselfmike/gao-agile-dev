"""
Integration tests for agent context access via AgentContextAPI.

These tests verify that agents can successfully access project context
through the AgentContextAPI, including epic definitions, architecture,
PRDs, story definitions, and coding standards.

Tests cover:
- Setting and retrieving WorkflowContext
- Using AgentContextAPI to access documents
- Verifying cache behavior
- Verifying usage tracking
- Thread-local context isolation
"""

import uuid
import tempfile
from pathlib import Path
from typing import Generator
import pytest

from gao_dev.core.context.context_api import (
    set_workflow_context,
    get_workflow_context,
    clear_workflow_context,
    AgentContextAPI,
    _reset_global_instances,
)
from gao_dev.core.context.workflow_context import WorkflowContext
from gao_dev.core.context.context_usage_tracker import ContextUsageTracker


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """
    Create a temporary project directory with sample documents.

    Creates directory structure:
    - docs/features/test-feature/
      - PRD.md
      - ARCHITECTURE.md
      - epics/epic-1.md
      - stories/epic-1/story-1.1.md
    - docs/CODING_STANDARDS.md
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Create directory structure
        feature_dir = tmp_path / "docs" / "features" / "test-feature"
        epics_dir = feature_dir / "epics"
        stories_dir = feature_dir / "stories" / "epic-1"

        feature_dir.mkdir(parents=True)
        epics_dir.mkdir(parents=True)
        stories_dir.mkdir(parents=True)

        # Create PRD
        prd = feature_dir / "PRD.md"
        prd.write_text("# Product Requirements Document\n\nTest PRD content.")

        # Create Architecture
        arch = feature_dir / "ARCHITECTURE.md"
        arch.write_text("# System Architecture\n\nTest architecture content.")

        # Create Epic
        epic = epics_dir / "epic-1.md"
        epic.write_text("# Epic 1: Test Epic\n\nTest epic definition.")

        # Create Story
        story = stories_dir / "story-1.1.md"
        story.write_text(
            "# Story 1.1: Test Story\n\n"
            "## Acceptance Criteria\n\n"
            "- [ ] Criterion 1\n"
            "- [ ] Criterion 2\n"
        )

        # Create Coding Standards
        standards = tmp_path / "docs" / "CODING_STANDARDS.md"
        standards.parent.mkdir(parents=True, exist_ok=True)
        standards.write_text("# Coding Standards\n\nTest standards content.")

        yield tmp_path


@pytest.fixture
def workflow_context() -> WorkflowContext:
    """Create a test WorkflowContext."""
    return WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=1,
        story_num=1,
        feature="test-feature",
        workflow_name="test_workflow"
    )


@pytest.fixture(autouse=True)
def reset_context():
    """Reset global context instances before and after each test."""
    _reset_global_instances()
    clear_workflow_context()
    yield
    _reset_global_instances()
    clear_workflow_context()


class TestWorkflowContextAccess:
    """Test setting and retrieving WorkflowContext."""

    def test_set_and_get_workflow_context(self, workflow_context: WorkflowContext):
        """Test setting and getting workflow context."""
        # Initially no context
        assert get_workflow_context() is None

        # Set context
        set_workflow_context(workflow_context)

        # Retrieve context
        retrieved = get_workflow_context()
        assert retrieved is not None
        assert retrieved.workflow_id == workflow_context.workflow_id
        assert retrieved.epic_num == workflow_context.epic_num
        assert retrieved.story_num == workflow_context.story_num
        assert retrieved.feature == workflow_context.feature

    def test_clear_workflow_context(self, workflow_context: WorkflowContext):
        """Test clearing workflow context."""
        # Set context
        set_workflow_context(workflow_context)
        assert get_workflow_context() is not None

        # Clear context
        clear_workflow_context()
        assert get_workflow_context() is None

    def test_workflow_context_thread_local(self, workflow_context: WorkflowContext):
        """Test that workflow context is thread-local."""
        import threading

        # Set context in main thread
        set_workflow_context(workflow_context)

        # Verify context in main thread
        assert get_workflow_context() is not None

        # Check context in different thread
        context_in_thread = None

        def thread_func():
            nonlocal context_in_thread
            context_in_thread = get_workflow_context()

        thread = threading.Thread(target=thread_func)
        thread.start()
        thread.join()

        # Context should be None in different thread
        assert context_in_thread is None


class TestAgentContextAPIDocumentAccess:
    """Test AgentContextAPI document access methods."""

    def test_get_epic_definition(
        self,
        workflow_context: WorkflowContext,
        temp_project_dir: Path,
        monkeypatch
    ):
        """Test getting epic definition via API."""
        # Change to temp directory
        monkeypatch.chdir(temp_project_dir)

        # Set workflow context
        set_workflow_context(workflow_context)

        # Create API
        api = AgentContextAPI(workflow_context)

        # Get epic definition
        epic_def = api.get_epic_definition()

        assert epic_def is not None
        assert "Epic 1: Test Epic" in epic_def
        assert "Test epic definition" in epic_def

    def test_get_architecture(
        self,
        workflow_context: WorkflowContext,
        temp_project_dir: Path,
        monkeypatch
    ):
        """Test getting architecture via API."""
        monkeypatch.chdir(temp_project_dir)
        set_workflow_context(workflow_context)

        api = AgentContextAPI(workflow_context)
        architecture = api.get_architecture()

        assert architecture is not None
        assert "System Architecture" in architecture
        assert "Test architecture content" in architecture

    def test_get_prd(
        self,
        workflow_context: WorkflowContext,
        temp_project_dir: Path,
        monkeypatch
    ):
        """Test getting PRD via API."""
        monkeypatch.chdir(temp_project_dir)
        set_workflow_context(workflow_context)

        api = AgentContextAPI(workflow_context)
        prd = api.get_prd()

        assert prd is not None
        assert "Product Requirements Document" in prd
        assert "Test PRD content" in prd

    def test_get_story_definition(
        self,
        workflow_context: WorkflowContext,
        temp_project_dir: Path,
        monkeypatch
    ):
        """Test getting story definition via API."""
        monkeypatch.chdir(temp_project_dir)
        set_workflow_context(workflow_context)

        api = AgentContextAPI(workflow_context)
        story_def = api.get_story_definition()

        assert story_def is not None
        assert "Story 1.1: Test Story" in story_def
        assert "Acceptance Criteria" in story_def

    def test_get_coding_standards(
        self,
        workflow_context: WorkflowContext,
        temp_project_dir: Path,
        monkeypatch
    ):
        """Test getting coding standards via API."""
        monkeypatch.chdir(temp_project_dir)
        set_workflow_context(workflow_context)

        api = AgentContextAPI(workflow_context)
        standards = api.get_coding_standards()

        assert standards is not None
        assert "Coding Standards" in standards
        assert "Test standards content" in standards

    def test_get_acceptance_criteria(
        self,
        workflow_context: WorkflowContext,
        temp_project_dir: Path,
        monkeypatch
    ):
        """Test getting acceptance criteria via API."""
        monkeypatch.chdir(temp_project_dir)
        set_workflow_context(workflow_context)

        api = AgentContextAPI(workflow_context)
        criteria = api.get_acceptance_criteria()

        # Acceptance criteria is in story definition
        assert criteria is not None
        assert "Acceptance Criteria" in criteria


class TestAgentContextAPICaching:
    """Test AgentContextAPI caching behavior."""

    def test_document_caching(
        self,
        workflow_context: WorkflowContext,
        temp_project_dir: Path,
        monkeypatch
    ):
        """Test that documents are cached after first access."""
        monkeypatch.chdir(temp_project_dir)
        set_workflow_context(workflow_context)

        api = AgentContextAPI(workflow_context)

        # First access - cache miss
        epic_def_1 = api.get_epic_definition()
        stats_1 = api.get_cache_statistics()

        # Second access - cache hit
        epic_def_2 = api.get_epic_definition()
        stats_2 = api.get_cache_statistics()

        # Content should be identical
        assert epic_def_1 == epic_def_2

        # Cache hits should increase
        assert stats_2["hits"] > stats_1["hits"]

    def test_cache_clear(
        self,
        workflow_context: WorkflowContext,
        temp_project_dir: Path,
        monkeypatch
    ):
        """Test clearing cache."""
        monkeypatch.chdir(temp_project_dir)
        set_workflow_context(workflow_context)

        api = AgentContextAPI(workflow_context)

        # Access document
        api.get_epic_definition()

        # Clear cache
        api.clear_cache()

        # Stats should be reset
        stats = api.get_cache_statistics()
        assert stats["size"] == 0


class TestAgentContextAPIUsageTracking:
    """Test AgentContextAPI usage tracking."""

    def test_usage_tracking(
        self,
        workflow_context: WorkflowContext,
        temp_project_dir: Path,
        monkeypatch,
        tmp_path: Path
    ):
        """Test that document access is tracked."""
        monkeypatch.chdir(temp_project_dir)
        set_workflow_context(workflow_context)

        # Create tracker with temp DB
        db_path = tmp_path / "usage.db"
        tracker = ContextUsageTracker(db_path)

        api = AgentContextAPI(
            workflow_context,
            tracker=tracker
        )

        # Access documents
        api.get_epic_definition()
        api.get_architecture()

        # Check usage history
        history = api.get_usage_history()

        assert len(history) >= 2

        # Check that epic_definition and architecture were accessed
        context_keys = [record["context_key"] for record in history]
        assert "epic_definition" in context_keys
        assert "architecture" in context_keys

    def test_usage_tracking_with_cache_hit(
        self,
        workflow_context: WorkflowContext,
        temp_project_dir: Path,
        monkeypatch,
        tmp_path: Path
    ):
        """Test that cache hits are tracked separately."""
        monkeypatch.chdir(temp_project_dir)
        set_workflow_context(workflow_context)

        # Create tracker with temp DB
        db_path = tmp_path / "usage.db"
        tracker = ContextUsageTracker(db_path)

        api = AgentContextAPI(
            workflow_context,
            tracker=tracker
        )

        # First access - cache miss
        api.get_epic_definition()

        # Second access - cache hit
        api.get_epic_definition()

        # Check usage history
        history = api.get_usage_history(context_key="epic_definition")

        assert len(history) >= 2

        # Check cache_hit flags
        cache_hits = [record["cache_hit"] for record in history]
        assert False in cache_hits  # First access is miss
        assert True in cache_hits   # Second access is hit


class TestAgentContextAPICustomContext:
    """Test AgentContextAPI custom context values."""

    def test_set_and_get_custom(self, workflow_context: WorkflowContext):
        """Test setting and getting custom context values."""
        api = AgentContextAPI(workflow_context)

        # Set custom values
        api.set_custom("project_name", "MyApp")
        api.set_custom("version", "1.0.0")

        # Get custom values
        assert api.get_custom("project_name") == "MyApp"
        assert api.get_custom("version") == "1.0.0"
        assert api.get_custom("nonexistent") is None
        assert api.get_custom("nonexistent", "default") == "default"


class TestAgentContextAPIIntegration:
    """Integration tests simulating real agent usage."""

    def test_bob_agent_workflow(
        self,
        temp_project_dir: Path,
        monkeypatch
    ):
        """Test Bob (Scrum Master) accessing context for story creation."""
        monkeypatch.chdir(temp_project_dir)

        # Simulate Bob's workflow
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=1,
            story_num=1,
            feature="test-feature",
            workflow_name="create_story"
        )

        set_workflow_context(context)
        api = AgentContextAPI(context)

        # Bob needs epic definition to create story
        epic_def = api.get_epic_definition()
        assert epic_def is not None

        # Bob might also check architecture
        architecture = api.get_architecture()
        assert architecture is not None

        # Verify usage was tracked
        history = api.get_usage_history()
        assert len(history) >= 2

    def test_amelia_agent_workflow(
        self,
        temp_project_dir: Path,
        monkeypatch
    ):
        """Test Amelia (Developer) accessing context for implementation."""
        monkeypatch.chdir(temp_project_dir)

        # Simulate Amelia's workflow
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=1,
            story_num=1,
            feature="test-feature",
            workflow_name="implement_story"
        )

        set_workflow_context(context)
        api = AgentContextAPI(context)

        # Amelia needs multiple documents for implementation
        epic_def = api.get_epic_definition()
        architecture = api.get_architecture()
        story_def = api.get_story_definition()
        coding_standards = api.get_coding_standards()

        assert all([
            epic_def is not None,
            architecture is not None,
            story_def is not None,
            coding_standards is not None,
        ])

        # Verify all accesses tracked
        history = api.get_usage_history()
        assert len(history) >= 4

    def test_murat_agent_workflow(
        self,
        temp_project_dir: Path,
        monkeypatch
    ):
        """Test Murat (Test Architect) accessing context for validation."""
        monkeypatch.chdir(temp_project_dir)

        # Simulate Murat's workflow
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=1,
            story_num=1,
            feature="test-feature",
            workflow_name="validate_story"
        )

        set_workflow_context(context)
        api = AgentContextAPI(context)

        # Murat needs story and acceptance criteria for validation
        story_def = api.get_story_definition()
        acceptance_criteria = api.get_acceptance_criteria()
        coding_standards = api.get_coding_standards()

        assert all([
            story_def is not None,
            acceptance_criteria is not None,
            coding_standards is not None,
        ])

        # Verify accesses tracked
        history = api.get_usage_history()
        assert len(history) >= 3
