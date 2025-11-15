"""Tests for POC validator.

Tests the validation framework components:
- Sample conversation diversity
- Agreement calculation logic
- Report generation
- Model comparison

Epic: 37 - UX Quality Analysis
Story: 37.0 - deepseek-r1 Quality Validation POC
"""

import pytest
from typing import List

from tests.e2e.validation.sample_conversations import SAMPLE_CONVERSATIONS
from tests.e2e.validation.models import (
    QualityReport,
    QualityIssue,
    IssueType,
    IssueSeverity,
    ComparisonResult,
    ValidationResult
)
from tests.e2e.validation.poc_validator import POCValidator
from pathlib import Path


class TestSampleConversations:
    """Test sample conversations coverage and diversity."""

    def test_has_10_conversations(self):
        """Test that we have exactly 10 sample conversations."""
        assert len(SAMPLE_CONVERSATIONS) == 10

    def test_conversations_have_required_fields(self):
        """Test all conversations have required fields."""
        for conv in SAMPLE_CONVERSATIONS:
            assert "id" in conv
            assert "name" in conv
            assert "description" in conv
            assert "transcript" in conv
            assert isinstance(conv["transcript"], list)
            assert len(conv["transcript"]) > 0

    def test_conversation_diversity(self):
        """Test conversations cover diverse scenarios."""
        names = [conv["name"] for conv in SAMPLE_CONVERSATIONS]

        # Check for expected scenario types
        assert any("greenfield" in name and "vague" in name for name in names)
        assert any("greenfield" in name and "detailed" in name for name in names)
        assert any("brownfield" in name for name in names)
        assert any("error" in name for name in names)
        assert any("multi_turn" in name or "clarification" in name for name in names)
        assert any("context" in name and "switching" in name for name in names)
        assert any("complex" in name for name in names)
        assert any("ambiguous" in name for name in names)
        assert any("help" in name for name in names)
        assert any("exit" in name for name in names)

    def test_transcript_structure(self):
        """Test transcript turns have correct structure."""
        for conv in SAMPLE_CONVERSATIONS:
            for turn in conv["transcript"]:
                assert "user" in turn
                assert "brian" in turn
                assert isinstance(turn["user"], str)
                assert isinstance(turn["brian"], str)


class TestAgreementCalculation:
    """Test agreement calculation logic."""

    def test_perfect_agreement(self):
        """Test calculation with perfect agreement."""
        claude_reports = [
            QualityReport(
                conversation_id=1,
                conversation_name="test1",
                quality_score=85,
                issues=[
                    QualityIssue(
                        turn_num=1,
                        issue_type=IssueType.INTENT_MISUNDERSTANDING,
                        severity=IssueSeverity.MEDIUM,
                        description="Test issue",
                        suggestion="Test suggestion"
                    )
                ]
            ),
            QualityReport(
                conversation_id=2,
                conversation_name="test2",
                quality_score=70,
                issues=[]
            )
        ]

        deepseek_reports = [
            QualityReport(
                conversation_id=1,
                conversation_name="test1",
                quality_score=85,  # Exact match
                issues=[
                    QualityIssue(
                        turn_num=1,
                        issue_type=IssueType.INTENT_MISUNDERSTANDING,
                        severity=IssueSeverity.HIGH,  # Severity can differ
                        description="Same issue",
                        suggestion="Same suggestion"
                    )
                ]
            ),
            QualityReport(
                conversation_id=2,
                conversation_name="test2",
                quality_score=70,  # Exact match
                issues=[]
            )
        ]

        validator = POCValidator(project_root=Path.cwd())
        result = validator.calculate_agreement(claude_reports, deepseek_reports)

        assert result.conversations_analyzed == 2
        assert result.score_agreement_pct == 100.0  # Both within 15 points
        assert result.issue_detection_recall == 100.0  # Perfect issue detection

    def test_partial_agreement(self):
        """Test calculation with partial agreement."""
        claude_reports = [
            QualityReport(
                conversation_id=1,
                conversation_name="test1",
                quality_score=85,
                issues=[
                    QualityIssue(
                        turn_num=1,
                        issue_type=IssueType.INTENT_MISUNDERSTANDING,
                        severity=IssueSeverity.MEDIUM,
                        description="Issue 1",
                        suggestion="Suggestion 1"
                    )
                ]
            ),
            QualityReport(
                conversation_id=2,
                conversation_name="test2",
                quality_score=70,
                issues=[
                    QualityIssue(
                        turn_num=1,
                        issue_type=IssueType.MISSED_PROBING,
                        severity=IssueSeverity.HIGH,
                        description="Issue 2",
                        suggestion="Suggestion 2"
                    )
                ]
            )
        ]

        deepseek_reports = [
            QualityReport(
                conversation_id=1,
                conversation_name="test1",
                quality_score=80,  # Within 15 points
                issues=[
                    QualityIssue(
                        turn_num=1,
                        issue_type=IssueType.INTENT_MISUNDERSTANDING,
                        severity=IssueSeverity.MEDIUM,
                        description="Same issue",
                        suggestion="Same"
                    )
                ]
            ),
            QualityReport(
                conversation_id=2,
                conversation_name="test2",
                quality_score=50,  # NOT within 15 points (diff = 20)
                issues=[
                    QualityIssue(
                        turn_num=1,
                        issue_type=IssueType.UNUSED_CONTEXT,  # Different issue
                        severity=IssueSeverity.LOW,
                        description="Different issue",
                        suggestion="Different"
                    )
                ]
            )
        ]

        validator = POCValidator(project_root=Path.cwd())
        result = validator.calculate_agreement(claude_reports, deepseek_reports)

        assert result.conversations_analyzed == 2
        assert result.score_agreement_pct == 50.0  # 1 of 2 within threshold
        assert result.issue_detection_recall == 50.0  # 50% average recall

    def test_no_agreement(self):
        """Test calculation with no agreement."""
        claude_reports = [
            QualityReport(
                conversation_id=1,
                conversation_name="test1",
                quality_score=85,
                issues=[
                    QualityIssue(
                        turn_num=1,
                        issue_type=IssueType.MISSED_PROBING,
                        severity=IssueSeverity.HIGH,
                        description="Issue",
                        suggestion="Suggestion"
                    )
                ]
            )
        ]

        deepseek_reports = [
            QualityReport(
                conversation_id=1,
                conversation_name="test1",
                quality_score=40,  # Far off (diff = 45)
                issues=[]  # No issues detected
            )
        ]

        validator = POCValidator(project_root=Path.cwd())
        result = validator.calculate_agreement(claude_reports, deepseek_reports)

        assert result.conversations_analyzed == 1
        assert result.score_agreement_pct == 0.0  # No agreement
        assert result.issue_detection_recall == 0.0  # Missed all issues


class TestValidationResult:
    """Test ValidationResult decision logic."""

    def test_pass_decision(self):
        """Test PASS decision with >80% score agreement and >70% issue recall."""
        result = ValidationResult(
            conversations_analyzed=10,
            score_agreement_pct=85.0,
            issue_detection_recall=75.0
        )

        assert result.decision == "PASS"
        assert "Proceed" in result.recommendation

    def test_partial_pass_decision(self):
        """Test PARTIAL PASS decision with 60-80% agreement."""
        result = ValidationResult(
            conversations_analyzed=10,
            score_agreement_pct=70.0,
            issue_detection_recall=65.0
        )

        assert result.decision == "PARTIAL PASS"
        assert "Hybrid" in result.recommendation

    def test_fail_decision(self):
        """Test FAIL decision with <60% agreement."""
        result = ValidationResult(
            conversations_analyzed=10,
            score_agreement_pct=50.0,
            issue_detection_recall=40.0
        )

        assert result.decision == "FAIL"
        assert "Reconsider" in result.recommendation


class TestReportGeneration:
    """Test report generation."""

    def test_report_contains_summary(self):
        """Test report contains summary section."""
        result = ValidationResult(
            conversations_analyzed=10,
            score_agreement_pct=85.0,
            issue_detection_recall=75.0,
            claude_reports=[
                QualityReport(1, "test", 80.0)
            ],
            deepseek_reports=[
                QualityReport(1, "test", 82.0)
            ]
        )

        validator = POCValidator(project_root=Path.cwd())
        report = validator.generate_report(result)

        assert "Summary" in report
        assert "85.0%" in report
        assert "75.0%" in report
        assert "PASS" in report

    def test_report_contains_recommendation(self):
        """Test report contains recommendation section."""
        result = ValidationResult(
            conversations_analyzed=10,
            score_agreement_pct=85.0,
            issue_detection_recall=75.0,
            claude_reports=[
                QualityReport(1, "test", 80.0)
            ],
            deepseek_reports=[
                QualityReport(1, "test", 82.0)
            ]
        )

        validator = POCValidator(project_root=Path.cwd())
        report = validator.generate_report(result)

        assert "RECOMMENDATION" in report
        assert "DECISION" in report
        assert "Rationale" in report

    def test_report_contains_detailed_comparison(self):
        """Test report contains detailed conversation comparisons."""
        comparison = ComparisonResult(
            conversation_id=1,
            conversation_name="greenfield_vague",
            claude_score=75.0,
            deepseek_score=78.0,
            score_difference=0,  # Calculated in __post_init__
            score_agreement=False,
            claude_issues=[IssueType.MISSED_PROBING],
            deepseek_issues=[IssueType.MISSED_PROBING]
        )

        result = ValidationResult(
            conversations_analyzed=1,
            score_agreement_pct=100.0,
            issue_detection_recall=100.0,
            comparisons=[comparison],
            claude_reports=[
                QualityReport(1, "greenfield_vague", 75.0)
            ],
            deepseek_reports=[
                QualityReport(1, "greenfield_vague", 78.0)
            ]
        )

        validator = POCValidator(project_root=Path.cwd())
        report = validator.generate_report(result)

        assert "Detailed Comparison" in report
        assert "greenfield_vague" in report
        assert "75.0" in report
        assert "78.0" in report


class TestComparisonResult:
    """Test ComparisonResult calculations."""

    def test_score_agreement_calculation(self):
        """Test score agreement is calculated correctly."""
        # Within threshold
        comp1 = ComparisonResult(
            conversation_id=1,
            conversation_name="test",
            claude_score=85.0,
            deepseek_score=90.0,  # Diff = 5
            score_difference=0,
            score_agreement=False
        )
        assert comp1.score_agreement is True
        assert comp1.score_difference == 5.0

        # At threshold boundary
        comp2 = ComparisonResult(
            conversation_id=2,
            conversation_name="test",
            claude_score=85.0,
            deepseek_score=70.0,  # Diff = 15
            score_difference=0,
            score_agreement=False
        )
        assert comp2.score_agreement is True
        assert comp2.score_difference == 15.0

        # Outside threshold
        comp3 = ComparisonResult(
            conversation_id=3,
            conversation_name="test",
            claude_score=85.0,
            deepseek_score=69.0,  # Diff = 16
            score_difference=0,
            score_agreement=False
        )
        assert comp3.score_agreement is False
        assert comp3.score_difference == 16.0

    def test_issue_recall_calculation(self):
        """Test issue recall is calculated correctly."""
        # Perfect recall
        comp1 = ComparisonResult(
            conversation_id=1,
            conversation_name="test",
            claude_score=85.0,
            deepseek_score=85.0,
            score_difference=0,
            score_agreement=False,
            claude_issues=[IssueType.MISSED_PROBING, IssueType.UNUSED_CONTEXT],
            deepseek_issues=[IssueType.MISSED_PROBING, IssueType.UNUSED_CONTEXT]
        )
        assert comp1.issue_recall == 100.0
        assert len(comp1.issue_overlap) == 2

        # Partial recall
        comp2 = ComparisonResult(
            conversation_id=2,
            conversation_name="test",
            claude_score=85.0,
            deepseek_score=85.0,
            score_difference=0,
            score_agreement=False,
            claude_issues=[IssueType.MISSED_PROBING, IssueType.UNUSED_CONTEXT],
            deepseek_issues=[IssueType.MISSED_PROBING]
        )
        assert comp2.issue_recall == 50.0
        assert len(comp2.issue_overlap) == 1

        # No recall
        comp3 = ComparisonResult(
            conversation_id=3,
            conversation_name="test",
            claude_score=85.0,
            deepseek_score=85.0,
            score_difference=0,
            score_agreement=False,
            claude_issues=[IssueType.MISSED_PROBING],
            deepseek_issues=[IssueType.POOR_RELEVANCE]
        )
        assert comp3.issue_recall == 0.0
        assert len(comp3.issue_overlap) == 0

        # No issues to detect
        comp4 = ComparisonResult(
            conversation_id=4,
            conversation_name="test",
            claude_score=95.0,
            deepseek_score=92.0,
            score_difference=0,
            score_agreement=False,
            claude_issues=[],
            deepseek_issues=[]
        )
        assert comp4.issue_recall == 100.0  # No issues = perfect recall
