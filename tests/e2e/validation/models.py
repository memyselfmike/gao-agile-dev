"""Data models for POC validation.

Contains models for quality analysis, validation results, and reports.

Epic: 37 - UX Quality Analysis
Story: 37.0 - deepseek-r1 Quality Validation POC
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class IssueType(str, Enum):
    """Types of quality issues that can be detected."""

    INTENT_MISUNDERSTANDING = "intent_misunderstanding"
    MISSED_PROBING = "missed_probing"
    UNUSED_CONTEXT = "unused_context"
    POOR_RELEVANCE = "poor_relevance"
    NO_CONFIRMATION = "no_confirmation"
    ABRUPT_RESPONSE = "abrupt_response"


class IssueSeverity(str, Enum):
    """Severity levels for quality issues."""

    CRITICAL = "critical"  # Completely wrong understanding
    HIGH = "high"  # Missed important clarification
    MEDIUM = "medium"  # Could be better
    LOW = "low"  # Minor improvement opportunity


@dataclass
class QualityIssue:
    """Represents a quality issue detected in conversation analysis."""

    turn_num: int
    issue_type: IssueType
    severity: IssueSeverity
    description: str
    suggestion: str

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if isinstance(self.issue_type, str):
            self.issue_type = IssueType(self.issue_type)
        if isinstance(self.severity, str):
            self.severity = IssueSeverity(self.severity)


@dataclass
class QualityReport:
    """Quality analysis report for a single conversation."""

    conversation_id: int
    conversation_name: str
    quality_score: float  # 0-100
    issues: List[QualityIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    model_used: str = ""

    def __post_init__(self) -> None:
        """Validate quality score."""
        if not 0 <= self.quality_score <= 100:
            raise ValueError(f"Quality score must be 0-100, got {self.quality_score}")


@dataclass
class ComparisonResult:
    """Result of comparing two quality reports (Claude vs deepseek-r1)."""

    conversation_id: int
    conversation_name: str
    claude_score: float
    deepseek_score: float
    score_difference: float
    score_agreement: bool  # Within 15 points

    claude_issues: List[IssueType] = field(default_factory=list)
    deepseek_issues: List[IssueType] = field(default_factory=list)
    issue_overlap: List[IssueType] = field(default_factory=list)
    issue_recall: float = 0.0  # % of Claude issues detected by deepseek

    def __post_init__(self) -> None:
        """Calculate derived metrics."""
        self.score_difference = abs(self.claude_score - self.deepseek_score)
        self.score_agreement = self.score_difference <= 15.0

        # Calculate issue recall
        if self.claude_issues:
            overlap = set(self.claude_issues) & set(self.deepseek_issues)
            self.issue_overlap = list(overlap)
            self.issue_recall = len(overlap) / len(set(self.claude_issues)) * 100
        else:
            self.issue_recall = 100.0  # No issues to detect


@dataclass
class ValidationResult:
    """Overall validation result across all conversations."""

    conversations_analyzed: int
    score_agreement_pct: float  # % of conversations with score agreement
    issue_detection_recall: float  # Average recall across conversations

    comparisons: List[ComparisonResult] = field(default_factory=list)
    claude_reports: List[QualityReport] = field(default_factory=list)
    deepseek_reports: List[QualityReport] = field(default_factory=list)

    decision: str = ""  # PASS, PARTIAL PASS, or FAIL
    recommendation: str = ""

    def __post_init__(self) -> None:
        """Determine decision based on metrics."""
        if not self.decision:
            if self.score_agreement_pct >= 80 and self.issue_detection_recall >= 70:
                self.decision = "PASS"
                self.recommendation = "Proceed with Stories 37.1-37.4 using deepseek-r1"
            elif self.score_agreement_pct >= 60:
                self.decision = "PARTIAL PASS"
                self.recommendation = "Hybrid approach: Claude for analysis, deepseek-r1 for regression"
            else:
                self.decision = "FAIL"
                self.recommendation = "Reconsider feature scope or use Claude API"

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for reporting."""
        return {
            "total_conversations": self.conversations_analyzed,
            "score_agreement_pct": round(self.score_agreement_pct, 1),
            "issue_detection_recall": round(self.issue_detection_recall, 1),
            "avg_claude_score": round(
                sum(r.quality_score for r in self.claude_reports) / len(self.claude_reports), 1
            ) if self.claude_reports else 0,
            "avg_deepseek_score": round(
                sum(r.quality_score for r in self.deepseek_reports) / len(self.deepseek_reports), 1
            ) if self.deepseek_reports else 0,
            "decision": self.decision,
            "recommendation": self.recommendation,
        }
