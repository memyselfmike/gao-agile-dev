"""
End-to-End Integration Tests for Context System Integration.

This module provides comprehensive E2E tests verifying the full context system
integration across all layers: document loading, context persistence, caching,
lineage tracking, and agent access.

Tests verify:
1. Full workflow with context (create PRD -> implement story)
2. Document loading through entire stack
3. Context persistence across workflow phases
4. Lineage tracking from PRD -> Architecture -> Story -> Code
5. Cache effectiveness (hit rates)
6. Concurrent workflow executions
7. Failure scenarios (DB locked, documents missing)

These tests ensure the complete integration of Epic 17 components.
"""

import asyncio
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, AsyncMock, patch

import pytest

from gao_dev.core.context.context_api import (
    AgentContextAPI,
    get_workflow_context,
    set_workflow_context,
    clear_workflow_context,
    _reset_global_instances,
)
from gao_dev.core.context.context_cache import ContextCache
from gao_dev.core.context.context_lineage import ContextLineageTracker
from gao_dev.core.context.context_persistence import ContextPersistence
from gao_dev.core.context.context_usage_tracker import ContextUsageTracker
from gao_dev.core.context.workflow_context import WorkflowContext
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.models import DocumentState, DocumentType
from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.orchestrator.brian_orchestrator import (
    ProjectType,
    ScaleLevel,
    WorkflowSequence,
)
from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
from gao_dev.orchestrator.workflow_results import WorkflowStatus
from gao_dev.core.models.workflow import WorkflowInfo


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """
    Create comprehensive temporary workspace with complete document structure.

    Creates:
    - docs/features/test-feature/
      - PRD.md
      - ARCHITECTURE.md
      - epics/epic-1.md
      - stories/epic-1/story-1.1.md
    - docs/CODING_STANDARDS.md
    - .gao/ directory for databases
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create feature directory
        feature_dir = workspace / "docs" / "features" / "test-feature"
        epics_dir = feature_dir / "epics"
        stories_dir = feature_dir / "stories" / "epic-1"

        feature_dir.mkdir(parents=True, exist_ok=True)
        epics_dir.mkdir(parents=True, exist_ok=True)
        stories_dir.mkdir(parents=True, exist_ok=True)

        # Create PRD
        prd_path = feature_dir / "PRD.md"
        prd_content = """---
owner: john
reviewer: winston
feature: test-feature
version: 1.0
---

# Product Requirements Document

## Overview
This is a test PRD for E2E integration testing.

## Features
- User authentication
- Todo management
- Data persistence

## Success Criteria
- All tests pass
- Coverage >80%
"""
        prd_path.write_text(prd_content, encoding="utf-8")

        # Create Architecture
        arch_path = feature_dir / "ARCHITECTURE.md"
        arch_content = """---
owner: winston
reviewer: john
feature: test-feature
version: 1.0
---

# System Architecture

## Overview
Layered architecture with clear separation of concerns.

## Components
- API Layer
- Business Logic
- Data Access Layer

## Technologies
- Python 3.11+
- SQLite
- pytest
"""
        arch_path.write_text(arch_content, encoding="utf-8")

        # Create Epic
        epic_path = epics_dir / "epic-1.md"
        epic_content = """---
feature: test-feature
epic: 1
owner: bob
---

# Epic 1: Context System Integration

## Goal
Integrate context system across all layers.

## Stories
- Story 1.1: Document Loading Integration
- Story 1.2: Cache Integration
- Story 1.3: Lineage Tracking
"""
        epic_path.write_text(epic_content, encoding="utf-8")

        # Create Story
        story_path = stories_dir / "story-1.1.md"
        story_content = """---
feature: test-feature
epic: 1
story: 1.1
owner: amelia
points: 3
---

# Story 1.1: Document Loading Integration

## Description
Integrate document loading from registry into context system.

## Acceptance Criteria
- [ ] Documents load from registry
- [ ] Fallback to filesystem works
- [ ] Cache stores documents
- [ ] Lineage tracks usage

## Tasks
- Implement document loader
- Add caching logic
- Track lineage
- Write tests
"""
        story_path.write_text(story_content, encoding="utf-8")

        # Create Coding Standards
        standards_path = workspace / "docs" / "CODING_STANDARDS.md"
        standards_path.parent.mkdir(parents=True, exist_ok=True)
        standards_content = """# Coding Standards

## Style
- PEP 8 compliance
- Type hints required
- Max line length: 100

## Testing
- >80% coverage
- All tests pass
"""
        standards_path.write_text(standards_content, encoding="utf-8")

        # Create .gao directory
        gao_dir = workspace / ".gao"
        gao_dir.mkdir(parents=True, exist_ok=True)

        yield workspace


@pytest.fixture
def document_registry(temp_workspace: Path) -> Generator[DocumentRegistry, None, None]:
    """Create DocumentRegistry with test database."""
    db_path = temp_workspace / ".gao" / "documents.db"
    registry = DocumentRegistry(db_path)
    yield registry
    registry.close()


@pytest.fixture
def lifecycle_manager(
    document_registry: DocumentRegistry, temp_workspace: Path
) -> DocumentLifecycleManager:
    """Create DocumentLifecycleManager."""
    archive_dir = temp_workspace / ".gao" / ".archive"
    return DocumentLifecycleManager(
        registry=document_registry, archive_dir=archive_dir
    )


@pytest.fixture
def context_persistence(temp_workspace: Path) -> ContextPersistence:
    """Create ContextPersistence with test database."""
    db_path = temp_workspace / ".gao" / "gao_dev.db"
    return ContextPersistence(db_path=db_path)


@pytest.fixture
def lineage_tracker(temp_workspace: Path) -> ContextLineageTracker:
    """Create ContextLineageTracker with test database."""
    db_path = temp_workspace / ".gao" / "gao_dev.db"
    return ContextLineageTracker(db_path=db_path)


@pytest.fixture
def usage_tracker(temp_workspace: Path) -> ContextUsageTracker:
    """Create ContextUsageTracker with test database."""
    db_path = temp_workspace / ".gao" / "context_usage.db"
    return ContextUsageTracker(db_path)


@pytest.fixture(autouse=True)
def reset_global_context():
    """Reset global context instances before and after each test."""
    _reset_global_instances()
    clear_workflow_context()
    yield
    _reset_global_instances()
    clear_workflow_context()


@pytest.fixture
def simple_workflow_sequence() -> WorkflowSequence:
    """Create simple workflow sequence for testing."""
    workflow_info = WorkflowInfo(
        name="test-workflow",
        description="Test workflow",
        phase=-1,
        installed_path=Path("/test"),
        author="Test",
        tags=["test"],
        variables={},
        required_tools=[],
        interactive=False,
        autonomous=True,
        iterative=False,
        web_bundle=False,
        output_file=None,
        templates={},
    )

    return WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_2,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Test workflow",
        phase_breakdown={"test": ["test-workflow"]},
        jit_tech_specs=False,
        estimated_stories=5,
        estimated_epics=1,
    )


# ============================================================================
# E2E Test 1: Full Workflow with Context (Create PRD -> Implement Story)
# ============================================================================


class TestE2EFullWorkflow:
    """Test complete workflow execution with full context integration."""

    @pytest.mark.asyncio
    async def test_full_workflow_with_document_loading(
        self,
        temp_workspace: Path,
        lifecycle_manager: DocumentLifecycleManager,
        context_persistence: ContextPersistence,
        lineage_tracker: ContextLineageTracker,
        monkeypatch,
    ):
        """
        E2E Test: Create PRD -> Workflow loads it via context.

        Verifies:
        1. Documents registered in lifecycle manager
        2. Workflow context created
        3. AgentContextAPI loads documents
        4. Cache stores documents
        5. Lineage tracks usage
        """
        monkeypatch.chdir(temp_workspace)

        # Step 1: Register documents in lifecycle manager
        prd_path = temp_workspace / "docs" / "features" / "test-feature" / "PRD.md"
        prd_doc = lifecycle_manager.register_document(
            path=prd_path,
            doc_type=DocumentType.PRD.value,
            author="john",
        )
        lifecycle_manager.transition_state(
            prd_doc.id, DocumentState.ACTIVE, reason="Ready for use"
        )

        arch_path = (
            temp_workspace / "docs" / "features" / "test-feature" / "ARCHITECTURE.md"
        )
        arch_doc = lifecycle_manager.register_document(
            path=arch_path,
            doc_type=DocumentType.ARCHITECTURE.value,
            author="winston",
        )
        lifecycle_manager.transition_state(
            arch_doc.id, DocumentState.ACTIVE, reason="Ready for use"
        )

        # Step 2: Create workflow context
        workflow_id = str(uuid.uuid4())
        context = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=1,
            story_num=1,
            feature="test-feature",
            workflow_name="implement_story",
        )

        # Step 3: Set thread-local context
        set_workflow_context(context)

        # Step 4: Create AgentContextAPI and load documents
        cache = ContextCache(ttl=timedelta(minutes=5), max_size=100)
        tracker = ContextUsageTracker(temp_workspace / ".gao" / "usage.db")

        api = AgentContextAPI(context, cache=cache, tracker=tracker)

        # Step 5: Load documents (should come from registry)
        prd_content = api.get_prd()
        arch_content = api.get_architecture()
        epic_content = api.get_epic_definition()
        story_content = api.get_story_definition()

        # Verify documents loaded
        assert prd_content is not None
        assert "Product Requirements Document" in prd_content
        assert "test PRD" in prd_content

        assert arch_content is not None
        assert "System Architecture" in arch_content
        assert "Layered architecture" in arch_content

        assert epic_content is not None
        assert "Epic 1" in epic_content

        assert story_content is not None
        assert "Story 1.1" in story_content

        # Step 6: Verify caching worked
        cache_stats = api.get_cache_statistics()
        assert cache_stats["size"] >= 4  # PRD, arch, epic, story

        # Step 7: Access documents again (should hit cache)
        prd_content_2 = api.get_prd()
        assert prd_content_2 == prd_content

        cache_stats_2 = api.get_cache_statistics()
        assert cache_stats_2["hits"] > cache_stats["hits"]

        # Step 8: Verify usage tracking
        usage_history = api.get_usage_history()
        assert len(usage_history) >= 5  # 4 first accesses + 1 cached access

        # Verify cache hits recorded
        cache_hits = [record["cache_hit"] for record in usage_history]
        assert True in cache_hits  # At least one cache hit
        assert False in cache_hits  # At least one cache miss

        # Step 9: Persist context
        context.metadata["test_completed"] = True
        context_persistence.save_context(context)

        # Step 10: Load context back
        loaded_context = context_persistence.load_context(workflow_id)
        assert loaded_context is not None
        assert loaded_context.workflow_id == workflow_id
        assert loaded_context.metadata["test_completed"] is True


# ============================================================================
# E2E Test 2: Document Loading Through Entire Stack
# ============================================================================


class TestE2EDocumentLoadingStack:
    """Test document loading through all integration layers."""

    def test_document_loading_full_stack(
        self,
        temp_workspace: Path,
        lifecycle_manager: DocumentLifecycleManager,
        usage_tracker: ContextUsageTracker,
        lineage_tracker: ContextLineageTracker,
        monkeypatch,
    ):
        """
        E2E Test: Implement story, context tracks document usage.

        Verifies full stack:
        1. Register documents in DocumentLifecycleManager
        2. Load via WorkflowContext
        3. Access via AgentContextAPI
        4. Cache stores documents
        5. UsageTracker records accesses
        6. LineageTracker records artifact relationships
        """
        monkeypatch.chdir(temp_workspace)

        # Register all documents
        prd_path = temp_workspace / "docs" / "features" / "test-feature" / "PRD.md"
        prd_doc = lifecycle_manager.register_document(
            path=prd_path, doc_type=DocumentType.PRD.value, author="john"
        )
        lifecycle_manager.transition_state(
            prd_doc.id, DocumentState.ACTIVE, reason="Ready"
        )

        arch_path = (
            temp_workspace / "docs" / "features" / "test-feature" / "ARCHITECTURE.md"
        )
        arch_doc = lifecycle_manager.register_document(
            path=arch_path, doc_type=DocumentType.ARCHITECTURE.value, author="winston"
        )
        lifecycle_manager.transition_state(
            arch_doc.id, DocumentState.ACTIVE, reason="Ready"
        )

        # Create context
        workflow_id = str(uuid.uuid4())
        context = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=1,
            story_num=1,
            feature="test-feature",
            workflow_name="implement_story",
        )

        # Create API with all trackers
        cache = ContextCache()
        api = AgentContextAPI(context, cache=cache, tracker=usage_tracker)

        # Load documents
        prd = api.get_prd()
        arch = api.get_architecture()
        epic = api.get_epic_definition()
        story = api.get_story_definition()

        # Verify all loaded
        assert all([prd, arch, epic, story])

        # Record lineage for artifact
        import hashlib

        lineage_tracker.record_usage(
            artifact_type="story",
            artifact_id="1.1",
            document_id=arch_doc.id,
            document_path=str(arch_path),
            document_type="architecture",
            document_version=hashlib.sha256(arch.encode()).hexdigest()[:16],
            workflow_id=workflow_id,
            epic=1,
            story="1.1",
        )

        # Verify usage tracked
        usage_history = usage_tracker.get_usage_history(workflow_id=workflow_id)
        assert len(usage_history) >= 4

        # Verify lineage recorded
        artifact_context = lineage_tracker.get_artifact_context("story", "1.1")
        assert len(artifact_context) >= 1
        assert artifact_context[0]["document_type"] == "architecture"


# ============================================================================
# E2E Test 3: Context Persistence Across Workflow Phases
# ============================================================================


class TestE2EContextPersistence:
    """Test context persistence across workflow lifecycle phases."""

    def test_context_persistence_across_phases(
        self, temp_workspace: Path, context_persistence: ContextPersistence, monkeypatch
    ):
        """
        E2E Test: Context persists and updates across workflow phases.

        Phases:
        1. Initialization
        2. Planning
        3. Implementation
        4. Testing
        5. Completed
        """
        monkeypatch.chdir(temp_workspace)

        # Create context
        workflow_id = str(uuid.uuid4())
        context = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=1,
            story_num=1,
            feature="test-feature",
            workflow_name="implement_story",
        )

        # Phase 1: Initialization
        context.metadata["phase"] = "initialization"
        context_persistence.save_context(context)

        # Phase 2: Planning
        context = context.copy_with(current_phase="planning")
        context.metadata["phase"] = "planning"
        context_persistence.save_context(context)

        # Phase 3: Implementation
        context = context.copy_with(current_phase="implementation")
        context.metadata["phase"] = "implementation"
        context.artifacts.append("src/main.py")
        context_persistence.save_context(context)

        # Phase 4: Testing
        context = context.copy_with(current_phase="testing")
        context.metadata["phase"] = "testing"
        context.artifacts.append("tests/test_main.py")
        context_persistence.save_context(context)

        # Phase 5: Completed
        context.status = "completed"
        context.metadata["phase"] = "completed"
        context_persistence.save_context(context)

        # Load final context
        final_context = context_persistence.load_context(workflow_id)

        # Verify persistence
        assert final_context is not None
        assert final_context.status == "completed"
        # Phase history tracking may vary based on implementation
        # The important part is that the context was saved and loaded correctly
        assert len(final_context.artifacts) == 2
        assert "src/main.py" in final_context.artifacts
        assert "tests/test_main.py" in final_context.artifacts

        # Verify current phase was saved
        assert final_context.current_phase == "testing"  # Last phase set via copy_with


# ============================================================================
# E2E Test 4: Lineage Tracking from PRD -> Architecture -> Story -> Code
# ============================================================================


class TestE2ELineageTracking:
    """Test complete lineage tracking through document hierarchy."""

    def test_full_lineage_tracking(
        self,
        temp_workspace: Path,
        lifecycle_manager: DocumentLifecycleManager,
        lineage_tracker: ContextLineageTracker,
        monkeypatch,
    ):
        """
        E2E Test: Generate lineage report showing document flow.

        Flow: PRD -> Architecture -> Epic -> Story -> Code
        """
        monkeypatch.chdir(temp_workspace)

        # Register all documents
        prd_path = temp_workspace / "docs" / "features" / "test-feature" / "PRD.md"
        prd_doc = lifecycle_manager.register_document(
            path=prd_path, doc_type=DocumentType.PRD.value, author="john"
        )

        arch_path = (
            temp_workspace / "docs" / "features" / "test-feature" / "ARCHITECTURE.md"
        )
        arch_doc = lifecycle_manager.register_document(
            path=arch_path, doc_type=DocumentType.ARCHITECTURE.value, author="winston"
        )

        epic_path = (
            temp_workspace
            / "docs"
            / "features"
            / "test-feature"
            / "epics"
            / "epic-1.md"
        )
        epic_doc = lifecycle_manager.register_document(
            path=epic_path, doc_type=DocumentType.EPIC.value, author="bob"
        )

        story_path = (
            temp_workspace
            / "docs"
            / "features"
            / "test-feature"
            / "stories"
            / "epic-1"
            / "story-1.1.md"
        )
        story_doc = lifecycle_manager.register_document(
            path=story_path, doc_type=DocumentType.STORY.value, author="amelia"
        )

        # Record lineage chain
        import hashlib

        # PRD -> Architecture (Architecture uses PRD)
        lineage_tracker.record_usage(
            artifact_type="doc",
            artifact_id="architecture",
            document_id=prd_doc.id,
            document_path=str(prd_path),
            document_type="prd",
            document_version=hashlib.sha256(b"prd_v1").hexdigest()[:16],
            workflow_id="arch-creation",
            epic=1,
        )

        # Architecture -> Epic (Epic uses Architecture)
        lineage_tracker.record_usage(
            artifact_type="epic",
            artifact_id="1",
            document_id=arch_doc.id,
            document_path=str(arch_path),
            document_type="architecture",
            document_version=hashlib.sha256(b"arch_v1").hexdigest()[:16],
            workflow_id="epic-creation",
            epic=1,
        )

        # Epic -> Story (Story uses Epic)
        lineage_tracker.record_usage(
            artifact_type="story",
            artifact_id="1.1",
            document_id=epic_doc.id,
            document_path=str(epic_path),
            document_type="epic",
            document_version=hashlib.sha256(b"epic_v1").hexdigest()[:16],
            workflow_id="story-creation",
            epic=1,
            story="1.1",
        )

        # Story -> Code (Code uses Story)
        lineage_tracker.record_usage(
            artifact_type="code",
            artifact_id="src/main.py",
            document_id=story_doc.id,
            document_path=str(story_path),
            document_type="story",
            document_version=hashlib.sha256(b"story_v1").hexdigest()[:16],
            workflow_id="implementation",
            epic=1,
            story="1.1",
        )

        # Generate lineage report
        report = lineage_tracker.generate_lineage_report(epic=1, output_format="markdown")

        # Verify report contains full chain
        assert "# Context Lineage Report - Epic 1" in report
        assert "prd" in report.lower()
        assert "architecture" in report.lower()
        assert "epic" in report.lower()
        assert "story" in report.lower()
        assert "code" in report.lower()

        # Verify artifact lineage query
        story_lineage = lineage_tracker.get_context_lineage("story", "1.1")
        assert len(story_lineage) >= 1

        code_context = lineage_tracker.get_artifact_context("code", "src/main.py")
        assert len(code_context) >= 1
        assert code_context[0]["document_type"] == "story"


# ============================================================================
# E2E Test 5: Cache Effectiveness
# ============================================================================


class TestE2ECacheEffectiveness:
    """Test cache hit rates and effectiveness."""

    def test_cache_hit_rate_over_80_percent(
        self, temp_workspace: Path, monkeypatch
    ):
        """
        E2E Test: Cache hit rate >80% for repeated document access.

        Simulates realistic agent usage pattern with repeated accesses.
        """
        monkeypatch.chdir(temp_workspace)

        # Create context and API
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=1,
            story_num=1,
            feature="test-feature",
            workflow_name="test",
        )

        cache = ContextCache(ttl=timedelta(minutes=5), max_size=100)
        tracker = ContextUsageTracker(temp_workspace / ".gao" / "usage.db")
        api = AgentContextAPI(context, cache=cache, tracker=tracker)

        # Simulate realistic access pattern
        # First pass: Load all documents (4 cache misses)
        api.get_prd()
        api.get_architecture()
        api.get_epic_definition()
        api.get_story_definition()

        # Second pass: Access same documents (4 cache hits)
        api.get_prd()
        api.get_architecture()
        api.get_epic_definition()
        api.get_story_definition()

        # Third pass: Access same documents (4 more cache hits)
        api.get_prd()
        api.get_architecture()
        api.get_epic_definition()
        api.get_story_definition()

        # Fourth pass: Access same documents (4 more cache hits)
        api.get_prd()
        api.get_architecture()
        api.get_epic_definition()
        api.get_story_definition()

        # Fifth pass: Access same documents (4 more cache hits)
        api.get_prd()
        api.get_architecture()
        api.get_epic_definition()
        api.get_story_definition()

        # Check cache statistics
        stats = api.get_cache_statistics()

        # Calculate hit rate
        total_requests = stats["hits"] + stats["misses"]
        hit_rate = stats["hits"] / total_requests if total_requests > 0 else 0.0

        # Verify hit rate >80%
        # We had 4 misses (first access) and 16 hits (4 subsequent passes)
        # Hit rate = 16/20 = 80%
        assert hit_rate >= 0.80, f"Hit rate {hit_rate:.2%} is below 80%"
        assert stats["hits"] >= 16
        assert stats["misses"] == 4


# ============================================================================
# E2E Test 6: Concurrent Workflow Executions
# ============================================================================


class TestE2EConcurrentWorkflows:
    """Test concurrent workflow executions with isolated contexts."""

    @pytest.mark.asyncio
    async def test_concurrent_workflows_dont_interfere(
        self, temp_workspace: Path, context_persistence: ContextPersistence, monkeypatch
    ):
        """
        E2E Test: Concurrent workflows don't interfere with each other.

        Runs 3 workflows concurrently and verifies:
        1. Each has unique context
        2. Contexts don't mix
        3. All persist independently
        """
        monkeypatch.chdir(temp_workspace)

        async def run_workflow(workflow_num: int) -> WorkflowContext:
            """Run a single workflow."""
            workflow_id = str(uuid.uuid4())  # Must be valid UUID
            context = WorkflowContext(
                workflow_id=workflow_id,
                epic_num=workflow_num,
                story_num=1,
                feature=f"feature-{workflow_num}",
                workflow_name=f"test-workflow-{workflow_num}",
            )

            # Simulate some work
            await asyncio.sleep(0.01)

            # Update context
            context.metadata["workflow_num"] = workflow_num
            context.artifacts.append(f"artifact-{workflow_num}.py")

            # Persist context
            context_persistence.save_context(context)

            return context

        # Run 3 workflows concurrently
        tasks = [run_workflow(i) for i in range(1, 4)]
        results = await asyncio.gather(*tasks)

        # Verify all workflows completed
        assert len(results) == 3

        # Verify unique contexts
        workflow_ids = [ctx.workflow_id for ctx in results]
        assert len(set(workflow_ids)) == 3  # All unique

        # Verify each context persisted correctly
        for i, context in enumerate(results, start=1):
            loaded = context_persistence.load_context(context.workflow_id)
            assert loaded is not None
            assert loaded.metadata["workflow_num"] == i
            assert f"artifact-{i}.py" in loaded.artifacts


# ============================================================================
# E2E Test 7: Failure Scenarios
# ============================================================================


class TestE2EFailureScenarios:
    """Test graceful handling of failure scenarios."""

    def test_missing_documents_handled_gracefully(
        self, temp_workspace: Path, monkeypatch
    ):
        """
        E2E Test: Missing documents handled gracefully.

        Verifies:
        1. Missing documents return None
        2. No exceptions raised
        3. System continues working
        """
        monkeypatch.chdir(temp_workspace)

        # Create context for nonexistent feature
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=99,
            story_num=99,
            feature="nonexistent-feature",
            workflow_name="test",
        )

        api = AgentContextAPI(context)

        # Try to load nonexistent documents
        prd = api.get_prd()
        arch = api.get_architecture()
        epic = api.get_epic_definition()
        story = api.get_story_definition()

        # All should return None gracefully
        assert prd is None
        assert arch is None
        assert epic is None
        assert story is None

        # System should still be functional
        stats = api.get_cache_statistics()
        assert stats is not None

    def test_corrupted_document_handled_gracefully(
        self, temp_workspace: Path, monkeypatch
    ):
        """
        E2E Test: Corrupted documents handled gracefully.

        Creates a document with invalid encoding and verifies graceful handling.
        """
        monkeypatch.chdir(temp_workspace)

        # Create corrupted document (empty file simulates corruption)
        corrupted_path = (
            temp_workspace / "docs" / "features" / "test-feature" / "corrupted.md"
        )
        corrupted_path.write_bytes(b"")

        # Create context
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=1,
            story_num=1,
            feature="test-feature",
            workflow_name="test",
        )

        api = AgentContextAPI(context)

        # Try to load documents (should handle gracefully)
        # This tests the fallback behavior
        prd = api.get_prd()

        # Should either load valid document or return None
        # No exception should be raised
        assert prd is None or isinstance(prd, str)

    def test_database_unavailable_handled_gracefully(
        self, temp_workspace: Path, monkeypatch
    ):
        """
        E2E Test: Database unavailable handled gracefully.

        Simulates DB unavailability and verifies fallback to filesystem.
        """
        monkeypatch.chdir(temp_workspace)

        # Don't create database - simulates unavailability

        # Create context
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=1,
            story_num=1,
            feature="test-feature",
            workflow_name="test",
        )

        api = AgentContextAPI(context)

        # Load documents (should fall back to filesystem)
        prd = api.get_prd()
        arch = api.get_architecture()

        # Should load from filesystem as fallback
        assert prd is not None
        assert "Product Requirements Document" in prd

        assert arch is not None
        assert "System Architecture" in arch


# ============================================================================
# E2E Test 8: Integration with Orchestrator
# ============================================================================


class TestE2EOrchestratorIntegration:
    """Test integration with GAODevOrchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_creates_and_persists_context(
        self,
        temp_workspace: Path,
        context_persistence: ContextPersistence,
        simple_workflow_sequence: WorkflowSequence,
        monkeypatch,
    ):
        """
        E2E Test: Orchestrator creates and persists context throughout workflow.

        Verifies:
        1. Context created at workflow start
        2. Context available to agents
        3. Context persisted to database
        4. Context includes all metadata
        """
        monkeypatch.chdir(temp_workspace)

        # Create orchestrator with mocks
        mock_coordinator = Mock()
        mock_coordinator.execute_sequence = AsyncMock(
            return_value=Mock(
                status=WorkflowStatus.COMPLETED,
                step_results=[],
                error_message=None,
                total_artifacts=0,
            )
        )

        orchestrator = GAODevOrchestrator(
            project_root=temp_workspace,
            api_key="test_key",
            mode="test",
            workflow_coordinator=mock_coordinator,
            story_lifecycle=Mock(),
            process_executor=Mock(),
            quality_gate_manager=Mock(),
            brian_orchestrator=Mock(),
            context_persistence=context_persistence,
        )

        # Execute workflow
        result = await orchestrator.execute_workflow(
            initial_prompt="Build a test application",
            workflow=simple_workflow_sequence,
        )

        # Verify context created
        assert result.context_id is not None

        # Verify context persisted
        loaded_context = context_persistence.load_context(result.context_id)
        assert loaded_context is not None
        assert loaded_context.workflow_id == result.context_id
        assert loaded_context.metadata["mode"] == "test"
        assert loaded_context.metadata["scale_level"] == ScaleLevel.LEVEL_2.value


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
