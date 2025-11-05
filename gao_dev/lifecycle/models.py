"""
Document Lifecycle Database Models.

This module defines the data models for the document lifecycle management system,
including documents, relationships, and enumerations for document types and states.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class DocumentType(str, Enum):
    """Valid document types in the system."""

    PRD = "prd"
    ARCHITECTURE = "architecture"
    EPIC = "epic"
    STORY = "story"
    ADR = "adr"
    POSTMORTEM = "postmortem"
    RUNBOOK = "runbook"
    QA_REPORT = "qa_report"
    TEST_REPORT = "test_report"


class DocumentState(str, Enum):
    """Document lifecycle states."""

    DRAFT = "draft"
    ACTIVE = "active"
    OBSOLETE = "obsolete"
    ARCHIVED = "archived"


class RelationshipType(str, Enum):
    """Types of relationships between documents."""

    DERIVED_FROM = "derived_from"  # e.g., Architecture derived from PRD
    IMPLEMENTS = "implements"  # e.g., Story implements Epic
    TESTS = "tests"  # e.g., Test Report tests Story
    REPLACES = "replaces"  # e.g., New version replaces old
    REFERENCES = "references"  # e.g., Document references another


@dataclass
class Document:
    """
    Represents a document in the lifecycle management system.

    This model includes all fields from the database schema, including
    governance fields for ownership and review tracking.
    """

    # Core fields
    path: str
    type: DocumentType
    state: DocumentState
    created_at: str
    modified_at: str

    # Optional fields
    id: Optional[int] = None
    author: Optional[str] = None
    feature: Optional[str] = None
    epic: Optional[int] = None
    story: Optional[str] = None
    content_hash: Optional[str] = None

    # Governance fields (ENHANCED in Epic 12)
    owner: Optional[str] = None
    reviewer: Optional[str] = None
    review_due_date: Optional[str] = None

    # Extensible metadata (stored as JSON in database)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize fields after initialization."""
        # Ensure type and state are enums
        if isinstance(self.type, str):
            self.type = DocumentType(self.type)
        if isinstance(self.state, str):
            self.state = DocumentState(self.state)

        # Ensure metadata is a dict
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert document to dictionary for database storage.

        Returns:
            Dictionary representation suitable for database insertion
        """
        data = asdict(self)
        # Convert enums to their string values
        data["type"] = self.type.value
        data["state"] = self.state.value
        # Convert metadata to JSON string
        data["metadata"] = json.dumps(self.metadata)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """
        Create Document instance from dictionary (e.g., database row).

        Args:
            data: Dictionary with document data

        Returns:
            Document instance
        """
        # Parse metadata JSON if it's a string
        if "metadata" in data and isinstance(data["metadata"], str):
            data["metadata"] = json.loads(data["metadata"])

        # Convert type and state strings to enums
        if "type" in data and isinstance(data["type"], str):
            data["type"] = DocumentType(data["type"])
        if "state" in data and isinstance(data["state"], str):
            data["state"] = DocumentState(data["state"])

        return cls(**data)

    def add_tag(self, tag: str) -> None:
        """Add a tag to the document's metadata."""
        if "tags" not in self.metadata:
            self.metadata["tags"] = []
        if tag not in self.metadata["tags"]:
            self.metadata["tags"].append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the document's metadata."""
        if "tags" in self.metadata and tag in self.metadata["tags"]:
            self.metadata["tags"].remove(tag)

    def get_tags(self) -> List[str]:
        """Get all tags for this document."""
        return self.metadata.get("tags", [])

    def set_retention_policy(self, policy: str) -> None:
        """Set the retention policy for this document."""
        self.metadata["retention_policy"] = policy

    def get_retention_policy(self) -> Optional[str]:
        """Get the retention policy for this document."""
        return self.metadata.get("retention_policy")

    def is_due_for_review(self) -> bool:
        """
        Check if document is due for review.

        Returns:
            True if review_due_date is set and has passed, False otherwise
        """
        if not self.review_due_date:
            return False

        try:
            due_date = datetime.fromisoformat(self.review_due_date)
            return datetime.now() >= due_date
        except (ValueError, TypeError):
            return False

    def update_modified_at(self) -> None:
        """Update the modified_at timestamp to current time."""
        self.modified_at = datetime.now().isoformat()


@dataclass
class DocumentRelationship:
    """
    Represents a relationship between two documents.

    Examples:
    - Architecture DERIVED_FROM PRD
    - Story IMPLEMENTS Epic
    - Test Report TESTS Story
    """

    parent_id: int
    child_id: int
    relationship_type: RelationshipType

    def __post_init__(self):
        """Validate fields after initialization."""
        if isinstance(self.relationship_type, str):
            self.relationship_type = RelationshipType(self.relationship_type)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert relationship to dictionary for database storage.

        Returns:
            Dictionary representation
        """
        return {
            "parent_id": self.parent_id,
            "child_id": self.child_id,
            "relationship_type": self.relationship_type.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentRelationship":
        """
        Create DocumentRelationship instance from dictionary.

        Args:
            data: Dictionary with relationship data

        Returns:
            DocumentRelationship instance
        """
        if isinstance(data.get("relationship_type"), str):
            data["relationship_type"] = RelationshipType(data["relationship_type"])
        return cls(**data)


@dataclass
class DocumentQuery:
    """
    Helper class for building document queries.

    This provides a fluent interface for constructing WHERE clauses
    and query parameters.
    """

    type: Optional[DocumentType] = None
    state: Optional[DocumentState] = None
    feature: Optional[str] = None
    epic: Optional[int] = None
    owner: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def build_where_clause(self) -> tuple[str, Dict[str, Any]]:
        """
        Build SQL WHERE clause and parameters.

        Returns:
            Tuple of (where_clause, parameters)
        """
        conditions = []
        params = {}

        if self.type:
            conditions.append("type = :type")
            params["type"] = self.type.value

        if self.state:
            conditions.append("state = :state")
            params["state"] = self.state.value

        if self.feature:
            conditions.append("feature = :feature")
            params["feature"] = self.feature

        if self.epic:
            conditions.append("epic = :epic")
            params["epic"] = self.epic

        if self.owner:
            conditions.append("owner = :owner")
            params["owner"] = self.owner

        # Tags require JSON extraction
        for i, tag in enumerate(self.tags):
            conditions.append(f"json_extract(metadata, '$.tags') LIKE :tag{i}")
            params[f"tag{i}"] = f'%"{tag}"%'

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params
