"""
Unit Tests for DocumentRegistry.

This module provides comprehensive unit tests for the DocumentRegistry class,
covering CRUD operations, query interface, relationship management, and error handling.
"""

import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.models import (
    Document,
    DocumentState,
    DocumentType,
    RelationshipType,
)
from gao_dev.lifecycle.exceptions import (
    DocumentNotFoundError,
    DocumentAlreadyExistsError,
    ValidationError,
    RelationshipError,
    DatabaseError,
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def registry(temp_db):
    """Create DocumentRegistry instance for testing."""
    reg = DocumentRegistry(temp_db)
    yield reg
    # Cleanup: close connections
    reg.close()


@pytest.fixture
def sample_doc_data():
    """Sample document data for testing."""
    return {
        "path": "docs/features/test/PRD.md",
        "doc_type": "prd",
        "author": "John",
        "feature": "test-feature",
        "epic": 1,
        "metadata": {"tags": ["test", "sample"]},
    }


# CRUD Tests


class TestRegisterDocument:
    """Tests for register_document()."""

    def test_register_document_creates_document(self, registry, sample_doc_data):
        """Test that register_document creates a new document."""
        doc = registry.register_document(**sample_doc_data)

        assert doc.id is not None
        assert doc.path == sample_doc_data["path"]
        assert doc.type == DocumentType.PRD
        assert doc.state == DocumentState.DRAFT
        assert doc.author == sample_doc_data["author"]
        assert doc.feature == sample_doc_data["feature"]
        assert doc.epic == sample_doc_data["epic"]
        assert doc.metadata == sample_doc_data["metadata"]
        assert doc.created_at is not None
        assert doc.modified_at is not None

    def test_register_document_with_duplicate_path_raises_error(
        self, registry, sample_doc_data
    ):
        """Test that registering duplicate path raises error."""
        registry.register_document(**sample_doc_data)

        with pytest.raises(DocumentAlreadyExistsError) as exc_info:
            registry.register_document(**sample_doc_data)

        assert sample_doc_data["path"] in str(exc_info.value)
        assert exc_info.value.path == sample_doc_data["path"]

    def test_register_document_with_invalid_type_raises_error(
        self, registry, sample_doc_data
    ):
        """Test that invalid document type raises error."""
        sample_doc_data["doc_type"] = "invalid_type"

        with pytest.raises(ValidationError) as exc_info:
            registry.register_document(**sample_doc_data)

        assert "Invalid document type" in str(exc_info.value)
        assert exc_info.value.field == "doc_type"

    def test_register_document_with_custom_state(self, registry, sample_doc_data):
        """Test registering document with custom state."""
        doc = registry.register_document(
            **sample_doc_data, state=DocumentState.ACTIVE
        )

        assert doc.state == DocumentState.ACTIVE

    def test_register_document_with_governance_fields(self, registry, sample_doc_data):
        """Test registering document with governance fields."""
        doc = registry.register_document(
            **sample_doc_data, owner="Alice", reviewer="Bob"
        )

        assert doc.owner == "Alice"
        assert doc.reviewer == "Bob"

    def test_register_document_with_no_metadata(self, registry):
        """Test registering document without metadata."""
        doc = registry.register_document(
            path="docs/test.md", doc_type="prd", author="John"
        )

        assert doc.metadata == {}


class TestGetDocument:
    """Tests for get_document()."""

    def test_get_document_retrieves_correct_document(self, registry, sample_doc_data):
        """Test that get_document retrieves the correct document."""
        created_doc = registry.register_document(**sample_doc_data)
        retrieved_doc = registry.get_document(created_doc.id)

        assert retrieved_doc.id == created_doc.id
        assert retrieved_doc.path == created_doc.path
        assert retrieved_doc.type == created_doc.type
        assert retrieved_doc.author == created_doc.author

    def test_get_document_with_invalid_id_raises_error(self, registry):
        """Test that invalid ID raises DocumentNotFoundError."""
        with pytest.raises(DocumentNotFoundError) as exc_info:
            registry.get_document(99999)

        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.doc_id == 99999


class TestGetDocumentByPath:
    """Tests for get_document_by_path()."""

    def test_get_document_by_path_works_correctly(self, registry, sample_doc_data):
        """Test that get_document_by_path retrieves document."""
        created_doc = registry.register_document(**sample_doc_data)
        retrieved_doc = registry.get_document_by_path(sample_doc_data["path"])

        assert retrieved_doc is not None
        assert retrieved_doc.id == created_doc.id
        assert retrieved_doc.path == sample_doc_data["path"]

    def test_get_document_by_path_returns_none_for_nonexistent(self, registry):
        """Test that nonexistent path returns None."""
        doc = registry.get_document_by_path("nonexistent/path.md")
        assert doc is None


class TestUpdateDocument:
    """Tests for update_document()."""

    def test_update_document_modifies_fields(self, registry, sample_doc_data):
        """Test that update_document modifies fields correctly."""
        doc = registry.register_document(**sample_doc_data)
        original_modified_at = doc.modified_at

        # Small delay to ensure timestamp changes
        import time
        time.sleep(0.01)

        updated_doc = registry.update_document(
            doc.id, state=DocumentState.ACTIVE, author="Jane", owner="Alice"
        )

        assert updated_doc.state == DocumentState.ACTIVE
        assert updated_doc.author == "Jane"
        assert updated_doc.owner == "Alice"
        assert updated_doc.modified_at >= original_modified_at

    def test_update_document_updates_modified_at_timestamp(
        self, registry, sample_doc_data
    ):
        """Test that modified_at is updated."""
        doc = registry.register_document(**sample_doc_data)
        original_modified_at = doc.modified_at

        # Small delay to ensure timestamp changes
        import time
        time.sleep(0.01)

        updated_doc = registry.update_document(doc.id, author="Jane")

        assert updated_doc.modified_at >= original_modified_at

    def test_update_document_with_invalid_id_raises_error(self, registry):
        """Test that updating nonexistent document raises error."""
        with pytest.raises(DocumentNotFoundError):
            registry.update_document(99999, author="Jane")

    def test_update_document_with_no_valid_fields_raises_error(
        self, registry, sample_doc_data
    ):
        """Test that no valid fields raises ValidationError."""
        doc = registry.register_document(**sample_doc_data)

        with pytest.raises(ValidationError) as exc_info:
            registry.update_document(doc.id, invalid_field="value")

        assert "No valid fields to update" in str(exc_info.value)

    def test_update_document_metadata(self, registry, sample_doc_data):
        """Test updating metadata field."""
        doc = registry.register_document(**sample_doc_data)

        new_metadata = {"tags": ["updated"], "custom": "value"}
        updated_doc = registry.update_document(doc.id, metadata=new_metadata)

        assert updated_doc.metadata == new_metadata


class TestDeleteDocument:
    """Tests for delete_document()."""

    def test_delete_document_soft_delete(self, registry, sample_doc_data):
        """Test soft delete marks document as archived."""
        doc = registry.register_document(**sample_doc_data)

        registry.delete_document(doc.id, soft=True)

        # Document should still exist but be archived
        deleted_doc = registry.get_document(doc.id)
        assert deleted_doc.state == DocumentState.ARCHIVED

    def test_delete_document_hard_delete(self, registry, sample_doc_data):
        """Test hard delete removes document."""
        doc = registry.register_document(**sample_doc_data)

        registry.delete_document(doc.id, soft=False)

        # Document should not exist
        with pytest.raises(DocumentNotFoundError):
            registry.get_document(doc.id)

    def test_delete_document_with_invalid_id_raises_error(self, registry):
        """Test deleting nonexistent document raises error."""
        with pytest.raises(DocumentNotFoundError):
            registry.delete_document(99999)


# Query Tests


class TestQueryDocuments:
    """Tests for query_documents()."""

    @pytest.fixture
    def multiple_docs(self, registry):
        """Create multiple documents for query testing."""
        docs = []
        docs.append(
            registry.register_document(
                path="docs/prd1.md",
                doc_type="prd",
                author="John",
                feature="feature-a",
                epic=1,
                state=DocumentState.DRAFT,
            )
        )
        docs.append(
            registry.register_document(
                path="docs/prd2.md",
                doc_type="prd",
                author="Jane",
                feature="feature-b",
                epic=1,
                state=DocumentState.ACTIVE,
            )
        )
        docs.append(
            registry.register_document(
                path="docs/arch1.md",
                doc_type="architecture",
                author="John",
                feature="feature-a",
                epic=2,
                state=DocumentState.ACTIVE,
            )
        )
        docs.append(
            registry.register_document(
                path="docs/story1.md",
                doc_type="story",
                author="Alice",
                feature="feature-a",
                epic=1,
                owner="Bob",
                metadata={"tags": ["backend", "api"]},
            )
        )
        return docs

    def test_query_by_doc_type(self, registry, multiple_docs):
        """Test querying by document type."""
        results = registry.query_documents(doc_type="prd")

        assert len(results) == 2
        assert all(doc.type == DocumentType.PRD for doc in results)

    def test_query_by_state(self, registry, multiple_docs):
        """Test querying by state."""
        results = registry.query_documents(state=DocumentState.ACTIVE)

        assert len(results) == 2
        assert all(doc.state == DocumentState.ACTIVE for doc in results)

    def test_query_by_feature(self, registry, multiple_docs):
        """Test querying by feature."""
        results = registry.query_documents(feature="feature-a")

        assert len(results) == 3
        assert all(doc.feature == "feature-a" for doc in results)

    def test_query_by_epic(self, registry, multiple_docs):
        """Test querying by epic."""
        results = registry.query_documents(epic=1)

        assert len(results) == 3
        assert all(doc.epic == 1 for doc in results)

    def test_query_by_owner(self, registry, multiple_docs):
        """Test querying by owner."""
        results = registry.query_documents(owner="Bob")

        assert len(results) == 1
        assert results[0].owner == "Bob"

    def test_query_by_tags(self, registry, multiple_docs):
        """Test querying by tags."""
        results = registry.query_documents(tags=["backend"])

        assert len(results) == 1
        assert "backend" in results[0].metadata["tags"]

    def test_query_with_multiple_filters(self, registry, multiple_docs):
        """Test combining multiple filters (AND logic)."""
        results = registry.query_documents(
            feature="feature-a", state=DocumentState.ACTIVE
        )

        assert len(results) == 1
        assert results[0].feature == "feature-a"
        assert results[0].state == DocumentState.ACTIVE

    def test_query_returns_empty_list_when_no_matches(self, registry, multiple_docs):
        """Test query returns empty list when no matches."""
        results = registry.query_documents(feature="nonexistent-feature")

        assert results == []

    def test_query_with_no_filters_returns_all(self, registry, multiple_docs):
        """Test query with no filters returns all documents."""
        results = registry.query_documents()

        assert len(results) == 4


class TestSpecializedQueries:
    """Tests for specialized query methods."""

    @pytest.fixture
    def setup_docs(self, registry):
        """Setup documents for specialized query testing."""
        registry.register_document(
            path="docs/prd_active.md",
            doc_type="prd",
            author="John",
            feature="auth",
            state=DocumentState.ACTIVE,
        )
        registry.register_document(
            path="docs/prd_draft.md",
            doc_type="prd",
            author="Jane",
            feature="auth",
            state=DocumentState.DRAFT,
        )
        registry.register_document(
            path="docs/arch.md",
            doc_type="architecture",
            author="John",
            feature="auth",
            epic=5,
            state=DocumentState.ACTIVE,
        )

    def test_get_active_document(self, registry, setup_docs):
        """Test get_active_document returns correct document."""
        doc = registry.get_active_document("prd", feature="auth")

        assert doc is not None
        assert doc.type == DocumentType.PRD
        assert doc.state == DocumentState.ACTIVE
        assert doc.feature == "auth"

    def test_get_active_document_returns_none_if_not_found(self, registry, setup_docs):
        """Test get_active_document returns None if not found."""
        doc = registry.get_active_document("story")

        assert doc is None

    def test_get_documents_by_state(self, registry, setup_docs):
        """Test get_documents_by_state returns all in state."""
        docs = registry.get_documents_by_state(DocumentState.ACTIVE)

        assert len(docs) == 2
        assert all(doc.state == DocumentState.ACTIVE for doc in docs)

    def test_get_feature_documents(self, registry, setup_docs):
        """Test get_feature_documents returns all for feature."""
        docs = registry.get_feature_documents("auth")

        assert len(docs) == 3
        assert all(doc.feature == "auth" for doc in docs)

    def test_get_epic_documents(self, registry, setup_docs):
        """Test get_epic_documents returns all for epic."""
        docs = registry.get_epic_documents(5)

        assert len(docs) == 1
        assert docs[0].epic == 5


# Relationship Tests


class TestRelationshipManagement:
    """Tests for relationship management."""

    @pytest.fixture
    def docs_with_relationships(self, registry):
        """Create documents for relationship testing."""
        prd = registry.register_document(
            path="docs/prd.md", doc_type="prd", author="John"
        )
        arch = registry.register_document(
            path="docs/arch.md", doc_type="architecture", author="Jane"
        )
        story = registry.register_document(
            path="docs/story.md", doc_type="story", author="Alice"
        )
        return {"prd": prd, "arch": arch, "story": story}

    def test_add_relationship_creates_relationship(
        self, registry, docs_with_relationships
    ):
        """Test add_relationship creates relationship."""
        prd = docs_with_relationships["prd"]
        arch = docs_with_relationships["arch"]

        rel = registry.add_relationship(
            prd.id, arch.id, RelationshipType.DERIVED_FROM
        )

        assert rel.parent_id == prd.id
        assert rel.child_id == arch.id
        assert rel.relationship_type == RelationshipType.DERIVED_FROM

    def test_add_relationship_with_nonexistent_parent_raises_error(
        self, registry, docs_with_relationships
    ):
        """Test adding relationship with nonexistent parent raises error."""
        arch = docs_with_relationships["arch"]

        with pytest.raises(DocumentNotFoundError):
            registry.add_relationship(99999, arch.id, RelationshipType.DERIVED_FROM)

    def test_add_relationship_with_nonexistent_child_raises_error(
        self, registry, docs_with_relationships
    ):
        """Test adding relationship with nonexistent child raises error."""
        prd = docs_with_relationships["prd"]

        with pytest.raises(DocumentNotFoundError):
            registry.add_relationship(prd.id, 99999, RelationshipType.DERIVED_FROM)

    def test_add_duplicate_relationship_raises_error(
        self, registry, docs_with_relationships
    ):
        """Test adding duplicate relationship raises error."""
        prd = docs_with_relationships["prd"]
        arch = docs_with_relationships["arch"]

        registry.add_relationship(prd.id, arch.id, RelationshipType.DERIVED_FROM)

        with pytest.raises(RelationshipError) as exc_info:
            registry.add_relationship(prd.id, arch.id, RelationshipType.DERIVED_FROM)

        assert "already exists" in str(exc_info.value).lower()

    def test_get_relationships_returns_all_relationships(
        self, registry, docs_with_relationships
    ):
        """Test get_relationships returns all relationships."""
        prd = docs_with_relationships["prd"]
        arch = docs_with_relationships["arch"]
        story = docs_with_relationships["story"]

        registry.add_relationship(prd.id, arch.id, RelationshipType.DERIVED_FROM)
        registry.add_relationship(prd.id, story.id, RelationshipType.IMPLEMENTS)

        relationships = registry.get_relationships(prd.id)

        assert len(relationships) == 2

    def test_get_parent_documents_returns_parents(
        self, registry, docs_with_relationships
    ):
        """Test get_parent_documents returns parent documents."""
        prd = docs_with_relationships["prd"]
        arch = docs_with_relationships["arch"]

        registry.add_relationship(prd.id, arch.id, RelationshipType.DERIVED_FROM)

        parents = registry.get_parent_documents(arch.id)

        assert len(parents) == 1
        assert parents[0].id == prd.id

    def test_get_parent_documents_with_type_filter(
        self, registry, docs_with_relationships
    ):
        """Test get_parent_documents with relationship type filter."""
        prd = docs_with_relationships["prd"]
        arch = docs_with_relationships["arch"]

        registry.add_relationship(prd.id, arch.id, RelationshipType.DERIVED_FROM)
        registry.add_relationship(prd.id, arch.id, RelationshipType.REFERENCES)

        parents = registry.get_parent_documents(
            arch.id, rel_type=RelationshipType.DERIVED_FROM
        )

        assert len(parents) == 1

    def test_get_child_documents_returns_children(
        self, registry, docs_with_relationships
    ):
        """Test get_child_documents returns child documents."""
        prd = docs_with_relationships["prd"]
        arch = docs_with_relationships["arch"]
        story = docs_with_relationships["story"]

        registry.add_relationship(prd.id, arch.id, RelationshipType.DERIVED_FROM)
        registry.add_relationship(prd.id, story.id, RelationshipType.IMPLEMENTS)

        children = registry.get_child_documents(prd.id)

        assert len(children) == 2
        assert {child.id for child in children} == {arch.id, story.id}

    def test_get_child_documents_with_type_filter(
        self, registry, docs_with_relationships
    ):
        """Test get_child_documents with relationship type filter."""
        prd = docs_with_relationships["prd"]
        arch = docs_with_relationships["arch"]
        story = docs_with_relationships["story"]

        registry.add_relationship(prd.id, arch.id, RelationshipType.DERIVED_FROM)
        registry.add_relationship(prd.id, story.id, RelationshipType.IMPLEMENTS)

        children = registry.get_child_documents(
            prd.id, rel_type=RelationshipType.IMPLEMENTS
        )

        assert len(children) == 1
        assert children[0].id == story.id


# Error Handling Tests


class TestErrorHandling:
    """Tests for error handling."""

    def test_validation_error_includes_field_info(self, registry):
        """Test ValidationError includes field information."""
        with pytest.raises(ValidationError) as exc_info:
            registry.register_document(
                path="test.md", doc_type="invalid_type", author="John"
            )

        error = exc_info.value
        assert error.field == "doc_type"
        assert error.value == "invalid_type"

    def test_document_not_found_error_includes_doc_id(self, registry):
        """Test DocumentNotFoundError includes doc_id."""
        with pytest.raises(DocumentNotFoundError) as exc_info:
            registry.get_document(99999)

        error = exc_info.value
        assert error.doc_id == 99999

    def test_document_already_exists_error_includes_path(self, registry):
        """Test DocumentAlreadyExistsError includes path."""
        path = "docs/test.md"
        registry.register_document(path=path, doc_type="prd", author="John")

        with pytest.raises(DocumentAlreadyExistsError) as exc_info:
            registry.register_document(path=path, doc_type="prd", author="Jane")

        error = exc_info.value
        assert error.path == path


# Integration Tests


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_register_query_verify_workflow(self, registry):
        """Test complete workflow: register, query, verify."""
        # Register multiple documents
        doc1 = registry.register_document(
            path="docs/prd.md",
            doc_type="prd",
            author="John",
            feature="auth",
            metadata={"tags": ["security"]},
        )
        doc2 = registry.register_document(
            path="docs/arch.md",
            doc_type="architecture",
            author="Jane",
            feature="auth",
        )

        # Query by feature
        docs = registry.query_documents(feature="auth")

        assert len(docs) == 2
        assert {doc.path for doc in docs} == {"docs/prd.md", "docs/arch.md"}

        # Verify data integrity
        retrieved_doc = registry.get_document(doc1.id)
        assert retrieved_doc.path == doc1.path
        assert retrieved_doc.metadata == doc1.metadata

    def test_document_lifecycle_workflow(self, registry):
        """Test document lifecycle: draft -> active -> obsolete -> archived."""
        # Create draft
        doc = registry.register_document(
            path="docs/test.md", doc_type="prd", author="John"
        )
        assert doc.state == DocumentState.DRAFT

        # Activate
        doc = registry.update_document(doc.id, state=DocumentState.ACTIVE)
        assert doc.state == DocumentState.ACTIVE

        # Mark obsolete
        doc = registry.update_document(doc.id, state=DocumentState.OBSOLETE)
        assert doc.state == DocumentState.OBSOLETE

        # Archive
        registry.delete_document(doc.id, soft=True)
        doc = registry.get_document(doc.id)
        assert doc.state == DocumentState.ARCHIVED

    def test_relationship_lineage_workflow(self, registry):
        """Test creating and querying document lineage."""
        # Create document hierarchy: PRD -> Architecture -> Story
        prd = registry.register_document(
            path="docs/prd.md", doc_type="prd", author="John"
        )
        arch = registry.register_document(
            path="docs/arch.md", doc_type="architecture", author="Jane"
        )
        story = registry.register_document(
            path="docs/story.md", doc_type="story", author="Alice"
        )

        # Create relationships
        registry.add_relationship(prd.id, arch.id, RelationshipType.DERIVED_FROM)
        registry.add_relationship(arch.id, story.id, RelationshipType.IMPLEMENTS)

        # Verify lineage
        story_parents = registry.get_parent_documents(story.id)
        assert len(story_parents) == 1
        assert story_parents[0].id == arch.id

        arch_parents = registry.get_parent_documents(arch.id)
        assert len(arch_parents) == 1
        assert arch_parents[0].id == prd.id

        prd_children = registry.get_child_documents(prd.id)
        assert len(prd_children) == 1
        assert prd_children[0].id == arch.id
