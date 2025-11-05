"""
Data models for checklists.

Defines the core data structures used throughout the checklist system,
including ChecklistItem and Checklist dataclasses.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ChecklistItem:
    """
    A single checklist item with validation requirements.

    Attributes:
        id: Unique identifier for the item within the checklist
        text: The actual checklist item text
        severity: Importance level (critical, high, medium, low)
        category: Optional subcategory for grouping items
        help_text: Optional additional guidance for completing the item
        references: Optional list of documentation links or standards
    """

    id: str
    text: str
    severity: str
    category: Optional[str] = None
    help_text: Optional[str] = None
    references: Optional[List[str]] = None

    def __post_init__(self):
        """Ensure references is never None."""
        if self.references is None:
            self.references = []


@dataclass
class Checklist:
    """
    A complete checklist with metadata and items.

    Attributes:
        name: Unique checklist name
        category: Primary category (testing, code-quality, security, etc.)
        version: Semantic version (e.g., "1.0.0")
        description: Human-readable description
        items: List of checklist items
        metadata: Additional metadata (domain, tags, author, etc.)
    """

    name: str
    category: str
    version: str
    description: Optional[str]
    items: List[ChecklistItem]
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Ensure metadata is never None."""
        if self.metadata is None:
            self.metadata = {}
