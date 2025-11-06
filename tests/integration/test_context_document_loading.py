"""
Integration tests for Context System + DocumentLifecycleManager.

Tests the integration between Epic 16 (Context System) and Epic 12
(Document Lifecycle Management). Verifies that WorkflowContext and
AgentContextAPI can load documents from DocumentLifecycleManager.
"""

import tempfile
import uuid
from pathlib import Path
from datetime import datetime

import pytest

from gao_dev.core.context.workflow_context import WorkflowContext
from gao_dev.core.context.context_api import AgentContextAPI
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.models import DocumentType, DocumentState


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create standard directory structure
        feature_dir = workspace / "docs" / "features" / "test-feature"
        feature_dir.mkdir(parents=True, exist_ok=True)

        epics_dir = feature_dir / "epics"
        epics_dir.mkdir(parents=True, exist_ok=True)

        stories_dir = feature_dir / "stories" / "epic-17"
        stories_dir.mkdir(parents=True, exist_ok=True)

        # Create GAO directory
        gao_dir = workspace / ".gao"
        gao_dir.mkdir(parents=True, exist_ok=True)

        yield workspace


@pytest.fixture
def sample_documents(temp_workspace):
    """Create sample documents in workspace."""
    feature_dir = temp_workspace / "docs" / "features" / "test-feature"

    # Create PRD
    prd_path = feature_dir / "PRD.md"
    prd_content = """---
owner: john
reviewer: winston
feature: test-feature
---

# Product Requirements Document

This is a test PRD for integration testing.
"""
    prd_path.write_text(prd_content, encoding='utf-8')

    # Create Architecture
    arch_path = feature_dir / "ARCHITECTURE.md"
    arch_content = """---
owner: winston
reviewer: john
feature: test-feature
---

# Architecture Document

This is a test architecture document.
"""
    arch_path.write_text(arch_content, encoding='utf-8')

    # Create Epic
    epic_path = feature_dir / "epics" / "epic-17.md"
    epic_content = """---
feature: test-feature
epic: 17
---

# Epic 17: Context System Integration

Test epic for integration testing.
"""
    epic_path.write_text(epic_content, encoding='utf-8')

    # Create Story
    story_path = feature_dir / "stories" / "epic-17" / "story-17.1.md"
    story_content = """---
feature: test-feature
epic: 17
story: 17.1
---

# Story 17.1: Document Loading Integration

Test story for integration testing.
"""
    story_path.write_text(story_content, encoding='utf-8')

    return {
        "prd": (prd_path, prd_content),
        "architecture": (arch_path, arch_content),
        "epic": (epic_path, epic_content),
        "story": (story_path, story_content),
    }


@pytest.fixture
def document_registry(temp_workspace):
    """Create DocumentRegistry with sample documents."""
    db_path = temp_workspace / ".gao" / "documents.db"
    registry = DocumentRegistry(db_path)
    yield registry
    registry.close()


@pytest.fixture
def lifecycle_manager(document_registry, temp_workspace):
    """Create DocumentLifecycleManager."""
    archive_dir = temp_workspace / ".gao" / ".archive"
    manager = DocumentLifecycleManager(
        registry=document_registry,
        archive_dir=archive_dir
    )
    return manager


def test_workflow_context_loads_prd_from_registry(
    temp_workspace,
    sample_documents,
    lifecycle_manager,
    monkeypatch
):
    """Test WorkflowContext.prd loads from DocumentLifecycleManager."""
    # Change to temp workspace
    monkeypatch.chdir(temp_workspace)

    # Register PRD in lifecycle manager
    prd_path, prd_content = sample_documents["prd"]
    doc = lifecycle_manager.register_document(
        path=prd_path,
        doc_type=DocumentType.PRD.value,
        author="john",
    )
    lifecycle_manager.transition_state(
        doc.id,
        DocumentState.ACTIVE,
        reason="Ready for use"
    )

    # Create workflow context
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=17,
        story_num=1,
        feature="test-feature",
        workflow_name="test_workflow"
    )

    # Load PRD (should come from registry)
    loaded_prd = context.prd

    # Verify content loaded
    assert loaded_prd is not None
    assert "Product Requirements Document" in loaded_prd
    assert "test PRD" in loaded_prd


def test_workflow_context_loads_architecture_from_registry(
    temp_workspace,
    sample_documents,
    lifecycle_manager,
    monkeypatch
):
    """Test WorkflowContext.architecture loads from DocumentLifecycleManager."""
    # Change to temp workspace
    monkeypatch.chdir(temp_workspace)

    # Register Architecture in lifecycle manager
    arch_path, arch_content = sample_documents["architecture"]
    doc = lifecycle_manager.register_document(
        path=arch_path,
        doc_type=DocumentType.ARCHITECTURE.value,
        author="winston",
    )
    lifecycle_manager.transition_state(
        doc.id,
        DocumentState.ACTIVE,
        reason="Ready for use"
    )

    # Create workflow context
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=17,
        story_num=1,
        feature="test-feature",
        workflow_name="test_workflow"
    )

    # Load architecture (should come from registry)
    loaded_arch = context.architecture

    # Verify content loaded
    assert loaded_arch is not None
    assert "Architecture Document" in loaded_arch
    assert "test architecture document" in loaded_arch


def test_workflow_context_loads_epic_from_registry(
    temp_workspace,
    sample_documents,
    lifecycle_manager,
    monkeypatch
):
    """Test WorkflowContext.epic_definition loads from DocumentLifecycleManager."""
    # Change to temp workspace
    monkeypatch.chdir(temp_workspace)

    # Register Epic in lifecycle manager
    epic_path, epic_content = sample_documents["epic"]
    doc = lifecycle_manager.register_document(
        path=epic_path,
        doc_type=DocumentType.EPIC.value,
        author="bob",
    )
    lifecycle_manager.transition_state(
        doc.id,
        DocumentState.ACTIVE,
        reason="Ready for use"
    )

    # Create workflow context
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=17,
        story_num=1,
        feature="test-feature",
        workflow_name="test_workflow"
    )

    # Load epic (should come from registry)
    loaded_epic = context.epic_definition

    # Verify content loaded
    assert loaded_epic is not None
    assert "Epic 17: Context System Integration" in loaded_epic
    assert "Test epic" in loaded_epic


def test_workflow_context_loads_story_from_registry(
    temp_workspace,
    sample_documents,
    lifecycle_manager,
    monkeypatch
):
    """Test WorkflowContext.story_definition loads from DocumentLifecycleManager."""
    # Change to temp workspace
    monkeypatch.chdir(temp_workspace)

    # Register Story in lifecycle manager
    story_path, story_content = sample_documents["story"]
    doc = lifecycle_manager.register_document(
        path=story_path,
        doc_type=DocumentType.STORY.value,
        author="bob",
    )
    lifecycle_manager.transition_state(
        doc.id,
        DocumentState.ACTIVE,
        reason="Ready for use"
    )

    # Create workflow context
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=17,
        story_num=1,
        feature="test-feature",
        workflow_name="test_workflow"
    )

    # Load story (should come from registry)
    loaded_story = context.story_definition

    # Verify content loaded
    assert loaded_story is not None
    assert "Story 17.1: Document Loading Integration" in loaded_story
    assert "Test story" in loaded_story


def test_workflow_context_returns_none_when_document_not_found(
    temp_workspace,
    monkeypatch
):
    """Test WorkflowContext returns None when document not found."""
    # Change to temp workspace
    monkeypatch.chdir(temp_workspace)

    # Create workflow context (no documents registered)
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=99,
        story_num=99,
        feature="nonexistent-feature",
        workflow_name="test_workflow"
    )

    # Try to load documents (should return None, not error)
    assert context.prd is None
    assert context.architecture is None
    assert context.epic_definition is None
    assert context.story_definition is None


def test_workflow_context_falls_back_to_filesystem(
    temp_workspace,
    sample_documents,
    monkeypatch
):
    """Test WorkflowContext falls back to filesystem when registry not available."""
    # Change to temp workspace
    monkeypatch.chdir(temp_workspace)

    # Create workflow context (no registry initialized)
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=17,
        story_num=1,
        feature="test-feature",
        workflow_name="test_workflow"
    )

    # Load documents (should fall back to filesystem)
    loaded_prd = context.prd
    loaded_arch = context.architecture
    loaded_epic = context.epic_definition
    loaded_story = context.story_definition

    # Verify content loaded from filesystem
    assert loaded_prd is not None
    assert "Product Requirements Document" in loaded_prd

    assert loaded_arch is not None
    assert "Architecture Document" in loaded_arch

    assert loaded_epic is not None
    assert "Epic 17" in loaded_epic

    assert loaded_story is not None
    assert "Story 17.1" in loaded_story


def test_workflow_context_caches_documents(
    temp_workspace,
    sample_documents,
    monkeypatch
):
    """Test WorkflowContext caches loaded documents."""
    # Change to temp workspace
    monkeypatch.chdir(temp_workspace)

    # Create workflow context
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=17,
        story_num=1,
        feature="test-feature",
        workflow_name="test_workflow"
    )

    # Load PRD first time
    prd1 = context.prd

    # Load PRD second time (should use cache)
    prd2 = context.prd

    # Should be same object (from cache)
    assert prd1 is prd2
    assert "prd" in context._document_cache


def test_agent_context_api_loads_from_registry(
    temp_workspace,
    sample_documents,
    lifecycle_manager,
    monkeypatch
):
    """Test AgentContextAPI loads documents from DocumentLifecycleManager."""
    # Change to temp workspace
    monkeypatch.chdir(temp_workspace)

    # Register all documents
    prd_path, _ = sample_documents["prd"]
    prd_doc = lifecycle_manager.register_document(
        path=prd_path,
        doc_type=DocumentType.PRD.value,
        author="john",
    )
    lifecycle_manager.transition_state(
        prd_doc.id,
        DocumentState.ACTIVE,
        reason="Ready"
    )

    arch_path, _ = sample_documents["architecture"]
    arch_doc = lifecycle_manager.register_document(
        path=arch_path,
        doc_type=DocumentType.ARCHITECTURE.value,
        author="winston",
    )
    lifecycle_manager.transition_state(
        arch_doc.id,
        DocumentState.ACTIVE,
        reason="Ready"
    )

    epic_path, _ = sample_documents["epic"]
    epic_doc = lifecycle_manager.register_document(
        path=epic_path,
        doc_type=DocumentType.EPIC.value,
        author="bob",
    )
    lifecycle_manager.transition_state(
        epic_doc.id,
        DocumentState.ACTIVE,
        reason="Ready"
    )

    story_path, _ = sample_documents["story"]
    story_doc = lifecycle_manager.register_document(
        path=story_path,
        doc_type=DocumentType.STORY.value,
        author="bob",
    )
    lifecycle_manager.transition_state(
        story_doc.id,
        DocumentState.ACTIVE,
        reason="Ready"
    )

    # Create workflow context and API
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=17,
        story_num=1,
        feature="test-feature",
        workflow_name="test_workflow"
    )
    api = AgentContextAPI(context)

    # Load all documents
    prd = api.get_prd()
    arch = api.get_architecture()
    epic = api.get_epic_definition()
    story = api.get_story_definition()

    # Verify all loaded
    assert prd is not None
    assert "Product Requirements Document" in prd

    assert arch is not None
    assert "Architecture Document" in arch

    assert epic is not None
    assert "Epic 17" in epic

    assert story is not None
    assert "Story 17.1" in story


def test_agent_context_api_returns_none_when_not_found(
    temp_workspace,
    monkeypatch
):
    """Test AgentContextAPI returns None when documents not found."""
    # Change to temp workspace
    monkeypatch.chdir(temp_workspace)

    # Create workflow context and API (no documents)
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=99,
        story_num=99,
        feature="nonexistent-feature",
        workflow_name="test_workflow"
    )
    api = AgentContextAPI(context)

    # Try to load documents (should return None, not error)
    assert api.get_prd() is None
    assert api.get_architecture() is None
    assert api.get_epic_definition() is None
    assert api.get_story_definition() is None


def test_workflow_context_with_custom_document_loader(
    temp_workspace,
    monkeypatch
):
    """Test WorkflowContext with custom document loader."""
    # Change to temp workspace
    monkeypatch.chdir(temp_workspace)

    # Custom loader that returns test content
    def custom_loader(doc_type: str) -> str:
        return f"Custom content for {doc_type}"

    # Create workflow context with custom loader
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=17,
        story_num=1,
        feature="test-feature",
        workflow_name="test_workflow"
    )
    context._document_loader = custom_loader

    # Load documents (should use custom loader)
    prd = context.prd
    arch = context.architecture

    # Verify custom content
    assert prd == "Custom content for prd"
    assert arch == "Custom content for architecture"


def test_workflow_context_preserves_cache_on_copy(
    temp_workspace,
    sample_documents,
    monkeypatch
):
    """Test WorkflowContext preserves document cache on copy_with."""
    # Change to temp workspace
    monkeypatch.chdir(temp_workspace)

    # Create workflow context
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=17,
        story_num=1,
        feature="test-feature",
        workflow_name="test_workflow"
    )

    # Load a document (populates cache)
    _ = context.prd

    # Copy context
    new_context = context.copy_with(current_phase="implementation")

    # Verify cache preserved
    assert "prd" in new_context._document_cache
    # Should use cached value (no file access)
    prd = new_context.prd
    assert prd is not None


def test_integration_with_epic_12_full_workflow(
    temp_workspace,
    sample_documents,
    lifecycle_manager,
    monkeypatch
):
    """
    Full integration test: Register documents, transition states, load via context.
    """
    # Change to temp workspace
    monkeypatch.chdir(temp_workspace)

    # Step 1: Register PRD as DRAFT
    prd_path, _ = sample_documents["prd"]
    prd_doc = lifecycle_manager.register_document(
        path=prd_path,
        doc_type=DocumentType.PRD.value,
        author="john",
    )
    assert prd_doc.state == DocumentState.DRAFT

    # Step 2: Transition PRD to ACTIVE
    lifecycle_manager.transition_state(
        prd_doc.id,
        DocumentState.ACTIVE,
        reason="Approved by team"
    )

    # Step 3: Create workflow context
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=17,
        story_num=1,
        feature="test-feature",
        workflow_name="test_workflow"
    )

    # Step 4: Load PRD via context (should get ACTIVE version)
    loaded_prd = context.prd
    assert loaded_prd is not None
    assert "Product Requirements Document" in loaded_prd

    # Step 5: Transition PRD to OBSOLETE
    lifecycle_manager.transition_state(
        prd_doc.id,
        DocumentState.OBSOLETE,
        reason="Superseded by new version"
    )

    # Step 6: Clear cache and reload (should not find ACTIVE document)
    context._document_cache.clear()
    loaded_prd_after_obsolete = context.prd
    # Should fall back to filesystem since no ACTIVE document in registry
    assert loaded_prd_after_obsolete is not None
