"""
Tests for DocumentLifecycleManager.

This module tests the high-level document lifecycle manager, including:
- Document registration with metadata extraction
- State transitions
- Filesystem operations (archiving)
- Document relationships
- Query operations
"""

import sqlite3
import tempfile
from pathlib import Path
from typing import Optional

import pytest

from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.models import Document, DocumentState, DocumentType, RelationshipType
from gao_dev.lifecycle.exceptions import (
    InvalidStateTransition,
    DocumentNotFoundError,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def db_path(temp_dir):
    """Create temporary database path."""
    return temp_dir / "test_lifecycle.db"


@pytest.fixture
def archive_dir(temp_dir):
    """Create archive directory."""
    archive = temp_dir / ".archive"
    archive.mkdir(parents=True, exist_ok=True)
    return archive


@pytest.fixture
def registry(db_path):
    """Create DocumentRegistry instance."""
    reg = DocumentRegistry(db_path)
    yield reg
    reg.close()


@pytest.fixture
def manager(registry, archive_dir):
    """Create DocumentLifecycleManager instance."""
    return DocumentLifecycleManager(registry, archive_dir)


@pytest.fixture
def sample_doc_path(temp_dir):
    """Create a sample document file."""
    doc_path = temp_dir / "docs" / "PRD.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text("# PRD\n\nThis is a test PRD.", encoding="utf-8")
    return doc_path


@pytest.fixture
def sample_doc_with_frontmatter(temp_dir):
    """Create a sample document with YAML frontmatter."""
    doc_path = temp_dir / "docs" / "features" / "auth" / "PRD.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    content = """---
owner: john
reviewer: winston
feature: authentication
epic: 5
tags:
  - security
  - auth
related_docs:
  - docs/Architecture.md
---

# PRD: Authentication System

This document describes the authentication system.
"""
    doc_path.write_text(content, encoding="utf-8")
    return doc_path


class TestDocumentRegistration:
    """Tests for document registration."""

    def test_register_simple_document(self, manager, sample_doc_path):
        """Test registering a simple document."""
        doc = manager.register_document(
            path=sample_doc_path,
            doc_type="prd",
            author="john",
        )

        assert doc.id is not None
        assert doc.path == str(sample_doc_path)
        assert doc.type == DocumentType.PRD
        assert doc.author == "john"
        assert doc.state == DocumentState.DRAFT

    def test_register_with_metadata(self, manager, sample_doc_path):
        """Test registering document with metadata."""
        doc = manager.register_document(
            path=sample_doc_path,
            doc_type="prd",
            author="john",
            metadata={"version": "1.0", "priority": "high"},
        )

        assert doc.metadata["version"] == "1.0"
        assert doc.metadata["priority"] == "high"

    def test_register_with_frontmatter(self, manager, sample_doc_with_frontmatter):
        """Test registering document with YAML frontmatter."""
        doc = manager.register_document(
            path=sample_doc_with_frontmatter,
            doc_type="prd",
            author="john",
        )

        assert doc.owner == "john"
        assert doc.reviewer == "winston"
        assert doc.feature == "authentication"
        assert doc.epic == 5
        assert "security" in doc.metadata["tags"]
        assert "auth" in doc.metadata["tags"]

    def test_register_extracts_path_metadata(self, manager, temp_dir):
        """Test extracting metadata from file path."""
        doc_path = temp_dir / "docs" / "features" / "user-auth" / "stories" / "epic-3" / "story-3.2.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text("# Story 3.2", encoding="utf-8")

        doc = manager.register_document(
            path=doc_path,
            doc_type="story",
            author="bob",
        )

        assert doc.feature == "user-auth"
        assert doc.epic == 3
        assert doc.story == "3.2"

    def test_register_calculates_content_hash(self, manager, sample_doc_path):
        """Test content hash calculation."""
        doc = manager.register_document(
            path=sample_doc_path,
            doc_type="prd",
            author="john",
        )

        assert doc.content_hash is not None
        assert len(doc.content_hash) == 64  # SHA256 hex digest

    def test_register_nonexistent_file(self, manager, temp_dir):
        """Test registering nonexistent file (should succeed but no hash)."""
        doc_path = temp_dir / "nonexistent.md"

        doc = manager.register_document(
            path=doc_path,
            doc_type="prd",
            author="john",
        )

        assert doc.id is not None
        assert doc.content_hash is None

    def test_provided_metadata_overrides_extracted(self, manager, sample_doc_with_frontmatter):
        """Test that provided metadata takes precedence."""
        doc = manager.register_document(
            path=sample_doc_with_frontmatter,
            doc_type="prd",
            author="john",
            metadata={"feature": "overridden-feature"},
        )

        # Provided metadata should override frontmatter
        assert doc.feature == "overridden-feature"


class TestStateTransitions:
    """Tests for state transitions."""

    def test_transition_to_active(self, manager, sample_doc_path):
        """Test transitioning document to active state."""
        doc = manager.register_document(
            path=sample_doc_path,
            doc_type="prd",
            author="john",
        )

        updated_doc = manager.transition_state(
            doc_id=doc.id,
            new_state=DocumentState.ACTIVE,
            reason="Approved",
        )

        assert updated_doc.state == DocumentState.ACTIVE

    def test_transition_to_archived(self, manager, sample_doc_path):
        """Test transitioning document to archived state."""
        doc = manager.register_document(
            path=sample_doc_path,
            doc_type="prd",
            author="john",
        )

        updated_doc = manager.transition_state(
            doc_id=doc.id,
            new_state=DocumentState.ARCHIVED,
            reason="No longer needed",
        )

        assert updated_doc.state == DocumentState.ARCHIVED

    def test_transition_invalid(self, manager, sample_doc_path):
        """Test invalid state transition."""
        doc = manager.register_document(
            path=sample_doc_path,
            doc_type="prd",
            author="john",
        )

        # Transition to archived
        manager.transition_state(
            doc_id=doc.id,
            new_state=DocumentState.ARCHIVED,
            reason="Archived",
        )

        # Cannot transition from archived to active
        with pytest.raises(InvalidStateTransition):
            manager.transition_state(
                doc_id=doc.id,
                new_state=DocumentState.ACTIVE,
            )

    def test_transition_requires_reason(self, manager, sample_doc_path):
        """Test that certain transitions require reason."""
        doc = manager.register_document(
            path=sample_doc_path,
            doc_type="prd",
            author="john",
        )

        # ARCHIVED requires reason
        with pytest.raises(ValueError, match="Reason required"):
            manager.transition_state(
                doc_id=doc.id,
                new_state=DocumentState.ARCHIVED,
            )

    def test_transition_with_changed_by(self, manager, sample_doc_path):
        """Test recording who made the transition."""
        doc = manager.register_document(
            path=sample_doc_path,
            doc_type="prd",
            author="john",
        )

        manager.transition_state(
            doc_id=doc.id,
            new_state=DocumentState.ACTIVE,
            reason="Approved",
            changed_by="winston",
        )

        # Verify transition recorded with changed_by
        history = manager.state_machine.get_transition_history(doc.id)
        assert len(history) > 0
        assert history[0].changed_by == "winston"


class TestCurrentDocument:
    """Tests for getting current active document."""

    def test_get_current_document(self, manager, sample_doc_path):
        """Test getting current active document."""
        doc = manager.register_document(
            path=sample_doc_path,
            doc_type="prd",
            author="john",
        )
        manager.transition_state(doc.id, DocumentState.ACTIVE, "Approved")

        current = manager.get_current_document(doc_type="prd")

        assert current is not None
        assert current.id == doc.id
        assert current.state == DocumentState.ACTIVE

    def test_get_current_document_with_feature(self, manager, temp_dir):
        """Test getting current document filtered by feature."""
        # Create two PRDs for different features
        prd1_path = temp_dir / "docs" / "features" / "auth" / "PRD.md"
        prd1_path.parent.mkdir(parents=True, exist_ok=True)
        prd1_path.write_text("# PRD 1", encoding="utf-8")

        prd2_path = temp_dir / "docs" / "features" / "billing" / "PRD.md"
        prd2_path.parent.mkdir(parents=True, exist_ok=True)
        prd2_path.write_text("# PRD 2", encoding="utf-8")

        doc1 = manager.register_document(
            path=prd1_path,
            doc_type="prd",
            author="john",
            metadata={"feature": "auth"},
        )
        manager.transition_state(doc1.id, DocumentState.ACTIVE, "Approved")

        doc2 = manager.register_document(
            path=prd2_path,
            doc_type="prd",
            author="john",
            metadata={"feature": "billing"},
        )
        manager.transition_state(doc2.id, DocumentState.ACTIVE, "Approved")

        # Get current for specific feature
        current_auth = manager.get_current_document(doc_type="prd", feature="auth")
        current_billing = manager.get_current_document(doc_type="prd", feature="billing")

        assert current_auth.id == doc1.id
        assert current_billing.id == doc2.id

    def test_get_current_no_active(self, manager):
        """Test getting current when no active document exists."""
        current = manager.get_current_document(doc_type="prd")
        assert current is None


class TestDocumentLineage:
    """Tests for document lineage (ancestors/descendants)."""

    def test_get_lineage_with_ancestors(self, manager, temp_dir):
        """Test getting document lineage with ancestors."""
        # Create PRD -> Architecture -> Epic chain
        prd_path = temp_dir / "PRD.md"
        arch_path = temp_dir / "Architecture.md"
        epic_path = temp_dir / "Epic.md"

        for path in [prd_path, arch_path, epic_path]:
            path.write_text(f"# {path.name}", encoding="utf-8")

        prd_doc = manager.register_document(prd_path, "prd", "john")
        arch_doc = manager.register_document(arch_path, "architecture", "winston")
        epic_doc = manager.register_document(epic_path, "epic", "bob")

        # Create relationships
        manager.registry.add_relationship(prd_doc.id, arch_doc.id, RelationshipType.DERIVED_FROM)
        manager.registry.add_relationship(arch_doc.id, epic_doc.id, RelationshipType.DERIVED_FROM)

        # Get lineage for epic
        ancestors, descendants = manager.get_document_lineage(epic_doc.id)

        assert len(ancestors) == 2
        assert ancestors[0].id == arch_doc.id
        assert ancestors[1].id == prd_doc.id

    def test_get_lineage_with_descendants(self, manager, temp_dir):
        """Test getting document lineage with descendants."""
        # Create Epic -> Story 1, Story 2
        epic_path = temp_dir / "Epic.md"
        story1_path = temp_dir / "Story1.md"
        story2_path = temp_dir / "Story2.md"

        for path in [epic_path, story1_path, story2_path]:
            path.write_text(f"# {path.name}", encoding="utf-8")

        epic_doc = manager.register_document(epic_path, "epic", "bob")
        story1_doc = manager.register_document(story1_path, "story", "amelia")
        story2_doc = manager.register_document(story2_path, "story", "amelia")

        # Create relationships
        manager.registry.add_relationship(epic_doc.id, story1_doc.id, RelationshipType.IMPLEMENTS)
        manager.registry.add_relationship(epic_doc.id, story2_doc.id, RelationshipType.IMPLEMENTS)

        # Get lineage for epic
        ancestors, descendants = manager.get_document_lineage(epic_doc.id)

        assert len(descendants) == 2
        descendant_ids = {d.id for d in descendants}
        assert story1_doc.id in descendant_ids
        assert story2_doc.id in descendant_ids

    def test_get_lineage_no_relationships(self, manager, sample_doc_path):
        """Test getting lineage for document with no relationships."""
        doc = manager.register_document(sample_doc_path, "prd", "john")

        ancestors, descendants = manager.get_document_lineage(doc.id)

        assert len(ancestors) == 0
        assert len(descendants) == 0


class TestArchiveDocument:
    """Tests for archiving documents."""

    def test_archive_document(self, manager, sample_doc_path, archive_dir):
        """Test archiving a document."""
        doc = manager.register_document(sample_doc_path, "prd", "john")

        archive_path = manager.archive_document(doc.id)

        # Verify file moved
        assert not sample_doc_path.exists()
        assert archive_path.exists()
        assert archive_path.parent == archive_dir

        # Verify state updated
        updated_doc = manager.registry.get_document(doc.id)
        assert updated_doc.state == DocumentState.ARCHIVED
        assert updated_doc.path == str(archive_path)

    def test_archive_preserves_directory_structure(self, manager, temp_dir, archive_dir):
        """Test that archiving preserves directory structure."""
        doc_path = temp_dir / "docs" / "features" / "auth" / "PRD.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text("# PRD", encoding="utf-8")

        doc = manager.register_document(doc_path, "prd", "john")

        archive_path = manager.archive_document(doc.id)

        # Verify file archived (for absolute paths, uses filename only)
        assert archive_path.exists()
        assert archive_path.parent == archive_dir or archive_path.name == "PRD.md"

    def test_archive_already_archived(self, manager, sample_doc_path):
        """Test archiving an already archived document."""
        doc = manager.register_document(sample_doc_path, "prd", "john")
        manager.archive_document(doc.id)

        # Try to archive again
        with pytest.raises(ValueError, match="already archived"):
            manager.archive_document(doc.id)

    def test_archive_nonexistent_file(self, manager, temp_dir):
        """Test archiving document with nonexistent file."""
        doc_path = temp_dir / "nonexistent.md"
        doc = manager.register_document(doc_path, "prd", "john")

        # Should not raise error, just update state
        archive_path = manager.archive_document(doc.id)

        updated_doc = manager.registry.get_document(doc.id)
        assert updated_doc.state == DocumentState.ARCHIVED

    def test_archive_records_transition(self, manager, sample_doc_path):
        """Test that archiving records transition in audit trail."""
        doc = manager.register_document(sample_doc_path, "prd", "john")

        manager.archive_document(doc.id)

        history = manager.state_machine.get_transition_history(doc.id)
        assert len(history) > 0
        assert history[0].to_state == DocumentState.ARCHIVED
        assert "Archived by system" in history[0].reason


class TestQueryDocuments:
    """Tests for querying documents."""

    def test_query_by_type(self, manager, temp_dir):
        """Test querying documents by type."""
        # Create documents of different types
        prd_path = temp_dir / "PRD.md"
        arch_path = temp_dir / "Arch.md"

        prd_path.write_text("# PRD", encoding="utf-8")
        arch_path.write_text("# Arch", encoding="utf-8")

        manager.register_document(prd_path, "prd", "john")
        manager.register_document(arch_path, "architecture", "winston")

        prds = manager.query_documents(doc_type="prd")
        archs = manager.query_documents(doc_type="architecture")

        assert len(prds) == 1
        assert len(archs) == 1

    def test_query_by_state(self, manager, sample_doc_path):
        """Test querying documents by state."""
        doc = manager.register_document(sample_doc_path, "prd", "john")
        manager.transition_state(doc.id, DocumentState.ACTIVE, "Approved")

        active_docs = manager.query_documents(state=DocumentState.ACTIVE)
        draft_docs = manager.query_documents(state=DocumentState.DRAFT)

        assert len(active_docs) == 1
        assert len(draft_docs) == 0

    def test_query_by_feature(self, manager, temp_dir):
        """Test querying documents by feature."""
        doc_path = temp_dir / "docs" / "features" / "auth" / "PRD.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text("# PRD", encoding="utf-8")

        manager.register_document(
            doc_path,
            "prd",
            "john",
            metadata={"feature": "auth"},
        )

        auth_docs = manager.query_documents(feature="auth")
        billing_docs = manager.query_documents(feature="billing")

        assert len(auth_docs) == 1
        assert len(billing_docs) == 0

    def test_query_multiple_filters(self, manager, temp_dir):
        """Test querying with multiple filters."""
        doc_path = temp_dir / "PRD.md"
        doc_path.write_text("# PRD", encoding="utf-8")

        doc = manager.register_document(
            doc_path,
            "prd",
            "john",
            metadata={"feature": "auth", "owner": "john"},
        )
        manager.transition_state(doc.id, DocumentState.ACTIVE, "Approved")

        results = manager.query_documents(
            doc_type="prd",
            state=DocumentState.ACTIVE,
            feature="auth",
            owner="john",
        )

        assert len(results) == 1
        assert results[0].id == doc.id


class TestRelationshipCreation:
    """Tests for automatic relationship creation."""

    def test_create_relationships_from_frontmatter(self, manager, temp_dir):
        """Test creating relationships from frontmatter."""
        # Create parent document
        parent_path = temp_dir / "docs" / "Architecture.md"
        parent_path.parent.mkdir(parents=True, exist_ok=True)
        parent_path.write_text("# Architecture", encoding="utf-8")

        parent_doc = manager.register_document(parent_path, "architecture", "winston")

        # Create child with related_docs
        child_path = temp_dir / "docs" / "Epic.md"
        child_content = f"""---
related_docs:
  - {parent_path}
---

# Epic
"""
        child_path.write_text(child_content, encoding="utf-8")

        child_doc = manager.register_document(child_path, "epic", "bob")

        # Verify relationship created
        relationships = manager.registry.get_relationships(child_doc.id)
        assert len(relationships) > 0

        parents = manager.registry.get_parent_documents(child_doc.id)
        assert len(parents) == 1
        assert parents[0].id == parent_doc.id

    def test_infer_relationship_type(self, manager, temp_dir):
        """Test relationship type inference."""
        # Create PRD -> Architecture relationship
        prd_path = temp_dir / "PRD.md"
        arch_path = temp_dir / "Architecture.md"

        prd_path.write_text("# PRD", encoding="utf-8")
        prd_doc = manager.register_document(prd_path, "prd", "john")

        arch_content = f"""---
related_docs:
  - {prd_path}
---

# Architecture
"""
        arch_path.write_text(arch_content, encoding="utf-8")
        arch_doc = manager.register_document(arch_path, "architecture", "winston")

        # Get relationship
        relationships = manager.registry.get_relationships(arch_doc.id)
        assert len(relationships) > 0
        assert relationships[0].relationship_type == RelationshipType.DERIVED_FROM

    def test_skip_nonexistent_related_docs(self, manager, temp_dir):
        """Test that nonexistent related docs are skipped."""
        doc_path = temp_dir / "Epic.md"
        content = """---
related_docs:
  - /nonexistent/path.md
---

# Epic
"""
        doc_path.write_text(content, encoding="utf-8")

        # Should not raise error
        doc = manager.register_document(doc_path, "epic", "bob")

        # No relationships created
        relationships = manager.registry.get_relationships(doc.id)
        assert len(relationships) == 0


class TestIntegration:
    """Integration tests for end-to-end workflows."""

    def test_full_lifecycle(self, manager, sample_doc_path, archive_dir):
        """Test complete document lifecycle: register -> transition -> archive."""
        # Register
        doc = manager.register_document(
            path=sample_doc_path,
            doc_type="prd",
            author="john",
            metadata={"version": "1.0"},
        )
        assert doc.state == DocumentState.DRAFT

        # Transition to active
        doc = manager.transition_state(
            doc_id=doc.id,
            new_state=DocumentState.ACTIVE,
            reason="Approved by team",
        )
        assert doc.state == DocumentState.ACTIVE

        # Transition to obsolete
        doc = manager.transition_state(
            doc_id=doc.id,
            new_state=DocumentState.OBSOLETE,
            reason="Replaced by v2",
        )
        assert doc.state == DocumentState.OBSOLETE

        # Archive
        archive_path = manager.archive_document(doc.id)
        assert archive_path.exists()
        assert not sample_doc_path.exists()

        doc = manager.registry.get_document(doc.id)
        assert doc.state == DocumentState.ARCHIVED

    def test_document_chain_with_lineage(self, manager, temp_dir):
        """Test creating document chain and querying lineage."""
        # Create PRD -> Architecture -> Epic -> Story chain
        prd_path = temp_dir / "PRD.md"
        arch_path = temp_dir / "Architecture.md"
        epic_path = temp_dir / "Epic.md"
        story_path = temp_dir / "Story.md"

        prd_path.write_text("# PRD", encoding="utf-8")
        prd_doc = manager.register_document(prd_path, "prd", "john")

        arch_content = f"""---
related_docs:
  - {prd_path}
---
# Architecture
"""
        arch_path.write_text(arch_content, encoding="utf-8")
        arch_doc = manager.register_document(arch_path, "architecture", "winston")

        epic_content = f"""---
related_docs:
  - {arch_path}
---
# Epic
"""
        epic_path.write_text(epic_content, encoding="utf-8")
        epic_doc = manager.register_document(epic_path, "epic", "bob")

        story_content = f"""---
related_docs:
  - {epic_path}
---
# Story
"""
        story_path.write_text(story_content, encoding="utf-8")
        story_doc = manager.register_document(story_path, "story", "amelia")

        # Get lineage for story
        ancestors, descendants = manager.get_document_lineage(story_doc.id)

        # Verify full chain
        assert len(ancestors) == 3
        ancestor_ids = [d.id for d in ancestors]
        assert epic_doc.id in ancestor_ids
        assert arch_doc.id in ancestor_ids
        assert prd_doc.id in ancestor_ids
