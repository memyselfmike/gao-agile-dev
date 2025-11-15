"""Data models for conversation quality analysis.

Story: 37.2 - Pattern-Based Quality Detection
Epic: 37 - UX Quality Analysis

Defines data structures for quality issues and reports.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from pathlib import Path


class IssueType(Enum):
    """Types of conversation quality issues."""

    INTENT_MISUNDERSTANDING = "intent_misunderstanding"
    MISSED_PROBING = "missed_probing"
    UNUSED_CONTEXT = "unused_context"
    POOR_RELEVANCE = "poor_relevance"
    ABRUPT_RESPONSE = "abrupt_response"
    NO_CONFIRMATION = "no_confirmation"


class IssueSeverity(Enum):
    """Severity levels for quality issues."""

    LOW = "low"  # Minor UX degradation
    MEDIUM = "medium"  # Noticeable UX problem
    HIGH = "high"  # Significant UX failure
    CRITICAL = "critical"  # Conversation failure


@dataclass
class QualityIssue:
    """
    A detected quality issue in a conversation turn.

    AC3: Each detected issue includes turn_num, issue_type, severity,
    description, suggestion.
    """

    turn_num: int
    issue_type: IssueType
    severity: IssueSeverity
    description: str
    suggestion: str
    pattern_matched: Optional[str] = None  # Which pattern detected this
    confidence: float = 1.0  # 0.0-1.0, higher = more confident

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "turn_num": self.turn_num,
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "suggestion": self.suggestion,
            "pattern_matched": self.pattern_matched,
            "confidence": self.confidence,
        }


@dataclass
class QualityReport:
    """
    Complete quality analysis report for a conversation.

    Contains all detected issues, statistics, quality score, and metadata.

    Story 37.3: Added quality_score (0-100%) calculation.
    """

    transcript_path: Path
    total_turns: int
    issues: List[QualityIssue] = field(default_factory=list)
    quality_score: float = 100.0  # 0-100%, defaults to perfect
    analysis_duration_seconds: float = 0.0
    analyzed_at: Optional[str] = None

    def add_issue(self, issue: QualityIssue) -> None:
        """Add an issue to the report."""
        self.issues.append(issue)

    def get_issues_by_type(self, issue_type: IssueType) -> List[QualityIssue]:
        """Get all issues of a specific type."""
        return [issue for issue in self.issues if issue.issue_type == issue_type]

    def get_issues_by_severity(self, severity: IssueSeverity) -> List[QualityIssue]:
        """Get all issues of a specific severity."""
        return [issue for issue in self.issues if issue.severity == severity]

    def get_issue_count_by_type(self) -> Dict[IssueType, int]:
        """Get count of issues by type."""
        counts = {issue_type: 0 for issue_type in IssueType}
        for issue in self.issues:
            counts[issue.issue_type] += 1
        return counts

    def get_issue_count_by_severity(self) -> Dict[IssueSeverity, int]:
        """Get count of issues by severity."""
        counts = {severity: 0 for severity in IssueSeverity}
        for issue in self.issues:
            counts[issue.severity] += 1
        return counts

    def get_average_confidence(self) -> float:
        """Get average confidence across all issues."""
        if not self.issues:
            return 0.0
        return sum(issue.confidence for issue in self.issues) / len(self.issues)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "transcript_path": str(self.transcript_path),
            "total_turns": self.total_turns,
            "quality_score": round(self.quality_score, 2),
            "total_issues": len(self.issues),
            "issues": [issue.to_dict() for issue in self.issues],
            "issue_counts_by_type": {
                k.value: v for k, v in self.get_issue_count_by_type().items()
            },
            "issue_counts_by_severity": {
                k.value: v for k, v in self.get_issue_count_by_severity().items()
            },
            "average_confidence": self.get_average_confidence(),
            "analysis_duration_seconds": self.analysis_duration_seconds,
            "analyzed_at": self.analyzed_at,
        }
