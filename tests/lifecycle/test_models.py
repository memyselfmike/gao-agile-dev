"""
Unit tests for lifecycle models.

Tests cover:
- Document model CRUD operations
- DocumentRelationship model
- Enum types
- Helper methods
- JSON serialization
"""

import pytest
import json
from datetime import datetime

from gao_dev.lifecycle.models import (
    Document,
    DocumentRelationship,
    DocumentType,
    DocumentState,
    RelationshipType,
    DocumentQuery,
)


class TestDocumentType:
    """Tests for DocumentType enum."""

    def test_all_document_types(self):
        """Test all document types are available."""
        assert DocumentType.PRD.value == "prd"
        assert DocumentType.ARCHITECTURE.value == "architecture"
        assert DocumentType.EPIC.value == "epic"
        assert DocumentType.STORY.value == "story"
        assert DocumentType.ADR.value == "adr"
        assert DocumentType.POSTMORTEM.value == "postmortem"
        assert DocumentType.RUNBOOK.value == "runbook"
        assert DocumentType.QA_REPORT.value == "qa_report"
        assert DocumentType.TEST_REPORT.value == "test_report"


class TestDocumentState:
    """Tests for DocumentState enum."""

    def test_all_document_states(self):
        """Test all document states are available."""
        assert DocumentState.DRAFT.value == "draft"
        assert DocumentState.ACTIVE.value == "active"
        assert DocumentState.OBSOLETE.value == "obsolete"
        assert DocumentState.ARCHIVED.value == "archived"


class TestRelationshipType:
    """Tests for RelationshipType enum."""

    def test_all_relationship_types(self):
        """Test all relationship types are available."""
        assert RelationshipType.DERIVED_FROM.value == "derived_from"
        assert RelationshipType.IMPLEMENTS.value == "implements"
        assert RelationshipType.TESTS.value == "tests"
        assert RelationshipType.REPLACES.value == "replaces"
        assert RelationshipType.REFERENCES.value == "references"


class TestDocument:
    """Tests for Document model."""

    def test_create_document_minimal(self):
        """Test creating document with minimal fields."""
        doc = Document(
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
        )

        assert doc.path == "/docs/test.md"
        assert doc.type == DocumentType.PRD
        assert doc.state == DocumentState.DRAFT
        assert doc.created_at == "2024-11-05"
        assert doc.modified_at == "2024-11-05"
        assert doc.id is None
        assert doc.metadata == {}

    def test_create_document_with_all_fields(self):
        """Test creating document with all fields."""
        doc = Document(
            id=1,
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.ACTIVE,
            created_at="2024-11-05",
            modified_at="2024-11-05",
            author="John",
            feature="user-auth",
            epic=12,
            story="12.1",
            content_hash="abc123",
            owner="John",
            reviewer="Winston",
            review_due_date="2024-12-05",
            metadata={"tags": ["auth", "security"]},
        )

        assert doc.id == 1
        assert doc.author == "John"
        assert doc.feature == "user-auth"
        assert doc.epic == 12
        assert doc.story == "12.1"
        assert doc.content_hash == "abc123"
        assert doc.owner == "John"
        assert doc.reviewer == "Winston"
        assert doc.review_due_date == "2024-12-05"
        assert doc.metadata == {"tags": ["auth", "security"]}

    def test_document_post_init_converts_string_enums(self):
        """Test that string type/state are converted to enums."""
        doc = Document(
            path="/docs/test.md",
            type="prd",  # String instead of enum
            state="draft",  # String instead of enum
            created_at="2024-11-05",
            modified_at="2024-11-05",
        )

        assert doc.type == DocumentType.PRD
        assert doc.state == DocumentState.DRAFT

    def test_document_post_init_handles_none_metadata(self):
        """Test that None metadata is converted to empty dict."""
        doc = Document(
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
            metadata=None,
        )

        assert doc.metadata == {}

    def test_document_to_dict(self):
        """Test converting document to dictionary."""
        doc = Document(
            id=1,
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
            owner="John",
            metadata={"tags": ["test"]},
        )

        doc_dict = doc.to_dict()

        assert doc_dict["id"] == 1
        assert doc_dict["path"] == "/docs/test.md"
        assert doc_dict["type"] == "prd"  # Converted to string
        assert doc_dict["state"] == "draft"  # Converted to string
        assert doc_dict["owner"] == "John"
        assert isinstance(doc_dict["metadata"], str)  # Converted to JSON string
        assert json.loads(doc_dict["metadata"]) == {"tags": ["test"]}

    def test_document_from_dict(self):
        """Test creating document from dictionary."""
        doc_dict = {
            "id": 1,
            "path": "/docs/test.md",
            "type": "prd",
            "state": "draft",
            "created_at": "2024-11-05",
            "modified_at": "2024-11-05",
            "owner": "John",
            "metadata": '{"tags": ["test"]}',
        }

        doc = Document.from_dict(doc_dict)

        assert doc.id == 1
        assert doc.path == "/docs/test.md"
        assert doc.type == DocumentType.PRD
        assert doc.state == DocumentState.DRAFT
        assert doc.owner == "John"
        assert doc.metadata == {"tags": ["test"]}

    def test_document_add_tag(self):
        """Test adding tags to document."""
        doc = Document(
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
        )

        doc.add_tag("authentication")
        doc.add_tag("security")

        assert "authentication" in doc.get_tags()
        assert "security" in doc.get_tags()

    def test_document_add_duplicate_tag(self):
        """Test that duplicate tags are not added."""
        doc = Document(
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
        )

        doc.add_tag("test")
        doc.add_tag("test")

        assert doc.get_tags().count("test") == 1

    def test_document_remove_tag(self):
        """Test removing tags from document."""
        doc = Document(
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
        )

        doc.add_tag("test")
        doc.add_tag("temp")
        doc.remove_tag("temp")

        assert "test" in doc.get_tags()
        assert "temp" not in doc.get_tags()

    def test_document_get_tags_empty(self):
        """Test getting tags when none exist."""
        doc = Document(
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
        )

        assert doc.get_tags() == []

    def test_document_set_retention_policy(self):
        """Test setting retention policy."""
        doc = Document(
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
        )

        doc.set_retention_policy("archive_after_1_year")

        assert doc.get_retention_policy() == "archive_after_1_year"

    def test_document_get_retention_policy_none(self):
        """Test getting retention policy when not set."""
        doc = Document(
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
        )

        assert doc.get_retention_policy() is None

    def test_document_is_due_for_review_no_date(self):
        """Test is_due_for_review when review_due_date not set."""
        doc = Document(
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
        )

        assert doc.is_due_for_review() is False

    def test_document_is_due_for_review_future_date(self):
        """Test is_due_for_review with future date."""
        doc = Document(
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
            review_due_date="2099-12-31",
        )

        assert doc.is_due_for_review() is False

    def test_document_is_due_for_review_past_date(self):
        """Test is_due_for_review with past date."""
        doc = Document(
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
            review_due_date="2020-01-01",
        )

        assert doc.is_due_for_review() is True

    def test_document_is_due_for_review_invalid_date(self):
        """Test is_due_for_review with invalid date format."""
        doc = Document(
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
            review_due_date="invalid-date",
        )

        assert doc.is_due_for_review() is False

    def test_document_update_modified_at(self):
        """Test updating modified_at timestamp."""
        doc = Document(
            path="/docs/test.md",
            type=DocumentType.PRD,
            state=DocumentState.DRAFT,
            created_at="2024-11-05",
            modified_at="2024-11-05",
        )

        old_modified = doc.modified_at
        doc.update_modified_at()

        assert doc.modified_at != old_modified
        # Verify it's a valid ISO format
        datetime.fromisoformat(doc.modified_at)


class TestDocumentRelationship:
    """Tests for DocumentRelationship model."""

    def test_create_relationship(self):
        """Test creating document relationship."""
        rel = DocumentRelationship(
            parent_id=1,
            child_id=2,
            relationship_type=RelationshipType.DERIVED_FROM,
        )

        assert rel.parent_id == 1
        assert rel.child_id == 2
        assert rel.relationship_type == RelationshipType.DERIVED_FROM

    def test_relationship_post_init_converts_string_enum(self):
        """Test that string relationship_type is converted to enum."""
        rel = DocumentRelationship(
            parent_id=1, child_id=2, relationship_type="implements"
        )

        assert rel.relationship_type == RelationshipType.IMPLEMENTS

    def test_relationship_to_dict(self):
        """Test converting relationship to dictionary."""
        rel = DocumentRelationship(
            parent_id=1,
            child_id=2,
            relationship_type=RelationshipType.DERIVED_FROM,
        )

        rel_dict = rel.to_dict()

        assert rel_dict["parent_id"] == 1
        assert rel_dict["child_id"] == 2
        assert rel_dict["relationship_type"] == "derived_from"

    def test_relationship_from_dict(self):
        """Test creating relationship from dictionary."""
        rel_dict = {
            "parent_id": 1,
            "child_id": 2,
            "relationship_type": "implements",
        }

        rel = DocumentRelationship.from_dict(rel_dict)

        assert rel.parent_id == 1
        assert rel.child_id == 2
        assert rel.relationship_type == RelationshipType.IMPLEMENTS


class TestDocumentQuery:
    """Tests for DocumentQuery helper class."""

    def test_build_where_clause_empty(self):
        """Test building WHERE clause with no filters."""
        query = DocumentQuery()
        where, params = query.build_where_clause()

        assert where == "1=1"
        assert params == {}

    def test_build_where_clause_type(self):
        """Test building WHERE clause with type filter."""
        query = DocumentQuery(type=DocumentType.PRD)
        where, params = query.build_where_clause()

        assert "type = :type" in where
        assert params["type"] == "prd"

    def test_build_where_clause_state(self):
        """Test building WHERE clause with state filter."""
        query = DocumentQuery(state=DocumentState.ACTIVE)
        where, params = query.build_where_clause()

        assert "state = :state" in where
        assert params["state"] == "active"

    def test_build_where_clause_feature(self):
        """Test building WHERE clause with feature filter."""
        query = DocumentQuery(feature="user-auth")
        where, params = query.build_where_clause()

        assert "feature = :feature" in where
        assert params["feature"] == "user-auth"

    def test_build_where_clause_epic(self):
        """Test building WHERE clause with epic filter."""
        query = DocumentQuery(epic=12)
        where, params = query.build_where_clause()

        assert "epic = :epic" in where
        assert params["epic"] == 12

    def test_build_where_clause_owner(self):
        """Test building WHERE clause with owner filter."""
        query = DocumentQuery(owner="John")
        where, params = query.build_where_clause()

        assert "owner = :owner" in where
        assert params["owner"] == "John"

    def test_build_where_clause_tags(self):
        """Test building WHERE clause with tag filters."""
        query = DocumentQuery(tags=["auth", "security"])
        where, params = query.build_where_clause()

        assert "json_extract(metadata, '$.tags') LIKE :tag0" in where
        assert "json_extract(metadata, '$.tags') LIKE :tag1" in where
        assert params["tag0"] == '%"auth"%'
        assert params["tag1"] == '%"security"%'

    def test_build_where_clause_multiple_filters(self):
        """Test building WHERE clause with multiple filters."""
        query = DocumentQuery(
            type=DocumentType.PRD,
            state=DocumentState.ACTIVE,
            feature="user-auth",
            owner="John",
        )
        where, params = query.build_where_clause()

        assert "type = :type" in where
        assert "state = :state" in where
        assert "feature = :feature" in where
        assert "owner = :owner" in where
        assert " AND " in where
        assert len(params) == 4
