"""
Data models for checklists.

Defines the core data structures used throughout the checklist system,
including ChecklistItem and Checklist dataclasses, as well as execution
tracking models (ItemResult, ExecutionResult).
"""

from dataclasses import dataclass, field
from datetime import datetime
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


@dataclass
class ItemResult:
    """
    Result of a single checklist item execution.

    Attributes:
        item_id: Item ID from checklist definition
        item_category: Category for grouping
        status: Result status (pass, fail, skip, na)
        notes: Optional notes explaining the result
        checked_at: When the item was checked
        checked_by: Who checked this item
        evidence_path: Optional path to evidence file/screenshot
        evidence_metadata: Optional additional evidence metadata
    """

    item_id: str
    item_category: Optional[str]
    status: str
    notes: Optional[str] = None
    checked_at: Optional[datetime] = None
    checked_by: Optional[str] = None
    evidence_path: Optional[str] = None
    evidence_metadata: Optional[Dict] = None

    def __post_init__(self):
        """Ensure evidence_metadata is never None."""
        if self.evidence_metadata is None:
            self.evidence_metadata = {}


@dataclass
class ExecutionResult:
    """
    Complete checklist execution result with all item results.

    Attributes:
        execution_id: Unique execution ID
        checklist_name: Name of checklist executed
        checklist_version: Version of checklist
        artifact_type: Type of artifact (story, epic, prd, etc.)
        artifact_id: ID of artifact
        epic_num: Epic number if applicable
        story_num: Story number if applicable
        executed_by: Who executed the checklist
        executed_at: When execution started
        completed_at: When execution completed
        overall_status: Overall execution status (in_progress, pass, fail, partial)
        item_results: List of individual item results
        notes: Optional overall execution notes
        duration_ms: Total execution time in milliseconds
        workflow_execution_id: Optional link to workflow execution
        metadata: Additional metadata
    """

    execution_id: int
    checklist_name: str
    checklist_version: str
    artifact_type: str
    artifact_id: str
    executed_by: str
    executed_at: datetime
    overall_status: str
    item_results: List[ItemResult]
    epic_num: Optional[int] = None
    story_num: Optional[int] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    duration_ms: Optional[int] = None
    workflow_execution_id: Optional[int] = None
    metadata: Optional[Dict] = None

    def __post_init__(self):
        """Ensure metadata and item_results are never None."""
        if self.metadata is None:
            self.metadata = {}
        if self.item_results is None:
            self.item_results = []
