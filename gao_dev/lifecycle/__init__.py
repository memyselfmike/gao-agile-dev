"""
Document Lifecycle Management System.

This module provides comprehensive document lifecycle management including:
- Document registry with SQLite database
- Standardized naming conventions
- YAML frontmatter schema validation
- Document state tracking (draft, active, obsolete, archived)
- Governance fields (owner, reviewer, review due dates)
- Document relationships and linking
- Document scanning with 5S classification
- Archival system with retention policies
"""

from gao_dev.lifecycle.naming_convention import DocumentNamingConvention
from gao_dev.lifecycle.models import (
    Document,
    DocumentRelationship,
    DocumentType,
    DocumentState,
    RelationshipType,
)
from gao_dev.lifecycle.scanner import DocumentScanner, ScanResult
from gao_dev.lifecycle.archival import ArchivalManager, RetentionPolicy, ArchivalAction

__all__ = [
    "DocumentNamingConvention",
    "Document",
    "DocumentRelationship",
    "DocumentType",
    "DocumentState",
    "RelationshipType",
    "DocumentScanner",
    "ScanResult",
    "ArchivalManager",
    "RetentionPolicy",
    "ArchivalAction",
]
