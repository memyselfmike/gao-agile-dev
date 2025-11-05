"""
Document Lifecycle Management System.

This module provides comprehensive document lifecycle management including:
- Document registry with SQLite database
- Standardized naming conventions
- YAML frontmatter schema validation
- Document state tracking (draft, active, obsolete, archived)
- Governance fields (owner, reviewer, review due dates)
- Document relationships and linking
"""

from gao_dev.lifecycle.naming_convention import DocumentNamingConvention
from gao_dev.lifecycle.models import (
    Document,
    DocumentRelationship,
    DocumentType,
    DocumentState,
    RelationshipType,
)

__all__ = [
    "DocumentNamingConvention",
    "Document",
    "DocumentRelationship",
    "DocumentType",
    "DocumentState",
    "RelationshipType",
]
