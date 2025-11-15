"""Comprehensive tests for quality scoring algorithm.

Story: 37.3 - Quality Scoring Algorithm
Epic: 37 - UX Quality Analysis

Tests the scoring algorithm that converts detected issues into
a 0-100% quality score.
"""

import pytest
from pathlib import Path
import json
from datetime import datetime

from tests.e2e.analyzer.conversation_analyzer import ConversationAnalyzer
from tests.e2e.models.quality_models import (
    QualityIssue,
    QualityReport,
    IssueType,
    IssueSeverity,
)


class TestScoringMethod:
    """Test _calculate_score() method implementation (AC1)."""

    def test_calculate_score_method_exists(self):
        """AC1: _calculate_score() method implemented."""
        analyzer = ConversationAnalyzer()
        assert hasattr(analyzer, "_calculate_score")
        assert callable(analyzer._calculate_score)

    def test_calculate_score_called_during_analysis(self, tmp_path):
        """AC1: Score is calculated during analysis."""
        transcript = [
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": "Build app",
                "brian_response": "OK",
                "context_used": {"project_root": str(tmp_path), "session_id": "test"},
            }
        ]

        transcript_path = tmp_path / "test.json"
        with open(transcript_path, "w") as f:
            json.dump(transcript, f)

        analyzer = ConversationAnalyzer()
        report = analyzer.analyze_conversation(transcript_path)

        # Score should be set
        assert hasattr(report, "quality_score")
        assert isinstance(report.quality_score, float)


class TestScoreRange:
    """Test score is in 0-100% range (AC2)."""

    def test_perfect_conversation_scores_100(self, tmp_path):
        """AC2: Perfect conversation (no issues) scores 100%."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=10)

        analyzer = ConversationAnalyzer()
        score = analyzer._calculate_score(report)

        assert score == 100.0

    def test_score_is_between_0_and_100(self, tmp_path):
        """AC2: Score is always in [0, 100] range."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)

        # Add various issues
        report.add_issue(
            QualityIssue(
                turn_num=0,
                issue_type=IssueType.INTENT_MISUNDERSTANDING,
                severity=IssueSeverity.HIGH,
                description="Test",
                suggestion="Test",
            )
        )

        report.add_issue(
            QualityIssue(
                turn_num=1,
                issue_type=IssueType.MISSED_PROBING,
                severity=IssueSeverity.MEDIUM,
                description="Test",
                suggestion="Test",
            )
        )

        analyzer = ConversationAnalyzer()
        score = analyzer._calculate_score(report)

        assert 0.0 <= score <= 100.0

    def test_many_issues_approaches_zero(self, tmp_path):
        """AC2: Many severe issues result in low score."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)

        # Add many critical issues
        for i in range(10):
            report.add_issue(
                QualityIssue(
                    turn_num=i % 5,
                    issue_type=IssueType.INTENT_MISUNDERSTANDING,
                    severity=IssueSeverity.CRITICAL,
                    description="Test",
                    suggestion="Test",
                )
            )

        analyzer = ConversationAnalyzer()
        score = analyzer._calculate_score(report)

        # Should be very low but not negative
        assert 0.0 <= score < 10.0


class TestSeverityWeights:
    """Test severity weights are defined and justified (AC3)."""

    def test_severity_weights_defined(self):
        """AC3: Severity weights are defined in _calculate_score()."""
        analyzer = ConversationAnalyzer()
        report = QualityReport(Path("test.json"), total_turns=10)

        # Add one of each severity
        report.add_issue(
            QualityIssue(
                0, IssueType.MISSED_PROBING, IssueSeverity.LOW, "Test", "Test"
            )
        )
        report.add_issue(
            QualityIssue(
                1, IssueType.MISSED_PROBING, IssueSeverity.MEDIUM, "Test", "Test"
            )
        )
        report.add_issue(
            QualityIssue(
                2, IssueType.MISSED_PROBING, IssueSeverity.HIGH, "Test", "Test"
            )
        )
        report.add_issue(
            QualityIssue(
                3, IssueType.MISSED_PROBING, IssueSeverity.CRITICAL, "Test", "Test"
            )
        )

        # Should not raise error
        score = analyzer._calculate_score(report)
        assert isinstance(score, float)

    def test_high_severity_impacts_score_more_than_low(self, tmp_path):
        """AC3: HIGH severity (3.0) impacts score more than LOW (1.0)."""
        analyzer = ConversationAnalyzer()

        # Report with 1 LOW issue
        report_low = QualityReport(transcript_path=tmp_path / "test.json", total_turns=10)
        report_low.add_issue(
            QualityIssue(
                0, IssueType.MISSED_PROBING, IssueSeverity.LOW, "Test", "Test"
            )
        )
        score_low = analyzer._calculate_score(report_low)

        # Report with 1 HIGH issue
        report_high = QualityReport(
            transcript_path=tmp_path / "test.json", total_turns=10
        )
        report_high.add_issue(
            QualityIssue(
                0, IssueType.MISSED_PROBING, IssueSeverity.HIGH, "Test", "Test"
            )
        )
        score_high = analyzer._calculate_score(report_high)

        # HIGH should reduce score more than LOW
        assert score_high < score_low

        # Expected: LOW = 100 - (1/100)*100 = 99, HIGH = 100 - (3/100)*100 = 97
        assert score_low == pytest.approx(99.0, abs=0.1)
        assert score_high == pytest.approx(97.0, abs=0.1)

    def test_medium_severity_between_low_and_high(self, tmp_path):
        """AC3: MEDIUM severity (2.0) is between LOW and HIGH."""
        analyzer = ConversationAnalyzer()

        # Report with 1 MEDIUM issue
        report_medium = QualityReport(
            transcript_path=tmp_path / "test.json", total_turns=10
        )
        report_medium.add_issue(
            QualityIssue(
                0, IssueType.MISSED_PROBING, IssueSeverity.MEDIUM, "Test", "Test"
            )
        )
        score_medium = analyzer._calculate_score(report_medium)

        # Expected: MEDIUM = 100 - (2/100)*100 = 98
        assert score_medium == pytest.approx(98.0, abs=0.1)


class TestScoringFormula:
    """Test scoring formula correctness (AC3, AC5)."""

    def test_scoring_formula_documented(self):
        """AC5: Algorithm is documented with examples."""
        analyzer = ConversationAnalyzer()

        # Check docstring exists and is comprehensive
        assert analyzer._calculate_score.__doc__ is not None
        docstring = analyzer._calculate_score.__doc__

        # Should document formula
        assert "Formula" in docstring or "formula" in docstring

        # Should document severity weights
        assert "CRITICAL" in docstring
        assert "HIGH" in docstring
        assert "MEDIUM" in docstring
        assert "LOW" in docstring

        # Should have examples
        assert "Example" in docstring or "example" in docstring

    def test_formula_calculation_accuracy(self, tmp_path):
        """AC5: Formula calculates correctly."""
        analyzer = ConversationAnalyzer()

        # Test case: 1 HIGH issue (weight=3.0) in 10 turns
        # Expected: 100 * (1 - (3 / (10 * 10))) = 100 * (1 - 0.03) = 97.0
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=10)
        report.add_issue(
            QualityIssue(
                0, IssueType.INTENT_MISUNDERSTANDING, IssueSeverity.HIGH, "Test", "Test"
            )
        )

        score = analyzer._calculate_score(report)
        assert score == 97.0

    def test_formula_with_multiple_issues(self, tmp_path):
        """AC5: Formula handles multiple issues correctly."""
        analyzer = ConversationAnalyzer()

        # Test case: 2 MEDIUM issues (weight=2.0 each) in 10 turns
        # Expected: 100 * (1 - (4 / (10 * 10))) = 100 * (1 - 0.04) = 96.0
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=10)
        report.add_issue(
            QualityIssue(
                0, IssueType.MISSED_PROBING, IssueSeverity.MEDIUM, "Test", "Test"
            )
        )
        report.add_issue(
            QualityIssue(
                1, IssueType.UNUSED_CONTEXT, IssueSeverity.MEDIUM, "Test", "Test"
            )
        )

        score = analyzer._calculate_score(report)
        assert score == 96.0


class TestEdgeCases:
    """Test edge cases are handled (AC6)."""

    def test_zero_turns(self, tmp_path):
        """AC6: Edge case - 0 turns handled gracefully."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=0)

        analyzer = ConversationAnalyzer()
        score = analyzer._calculate_score(report)

        # Should return 100 (perfect score for empty conversation)
        assert score == 100.0

    def test_no_issues(self, tmp_path):
        """AC6: Edge case - no issues returns 100."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=10)

        analyzer = ConversationAnalyzer()
        score = analyzer._calculate_score(report)

        assert score == 100.0

    def test_all_issues(self, tmp_path):
        """AC6: Edge case - excessive issues handled (floor at 0)."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=1)

        # Add way too many critical issues
        for i in range(50):
            report.add_issue(
                QualityIssue(
                    0, IssueType.INTENT_MISUNDERSTANDING, IssueSeverity.CRITICAL, "Test", "Test"
                )
            )

        analyzer = ConversationAnalyzer()
        score = analyzer._calculate_score(report)

        # Should be clamped to 0
        assert score == 0.0


class TestSampleConversationScores:
    """Test scoring on real sample conversations (AC7)."""

    def test_sample_conversations_scored(self, tmp_path):
        """AC7: Sample conversations analyzed and scored."""
        sample_dir = Path("tests/e2e/sample_transcripts")

        if not sample_dir.exists():
            pytest.skip("Sample transcripts not found")

        transcripts = list(sample_dir.glob("*.json"))
        assert len(transcripts) >= 5

        analyzer = ConversationAnalyzer()
        scores = []

        for transcript_path in transcripts:
            report = analyzer.analyze_conversation(transcript_path)
            scores.append(
                {
                    "transcript": transcript_path.name,
                    "score": report.quality_score,
                    "issues": len(report.issues),
                }
            )

        # All should have scores
        assert len(scores) == len(transcripts)

        # All scores should be in valid range
        for result in scores:
            assert 0.0 <= result["score"] <= 100.0


class TestBaselineQualityScore:
    """Test baseline quality score establishment (AC8)."""

    def test_baseline_score_calculated(self, tmp_path):
        """AC8: Baseline quality score can be established."""
        sample_dir = Path("tests/e2e/sample_transcripts")

        if not sample_dir.exists():
            pytest.skip("Sample transcripts not found")

        transcripts = list(sample_dir.glob("*.json"))
        if len(transcripts) == 0:
            pytest.skip("No sample transcripts")

        analyzer = ConversationAnalyzer()
        scores = []

        for transcript_path in transcripts:
            report = analyzer.analyze_conversation(transcript_path)
            scores.append(report.quality_score)

        # Calculate baseline (average)
        baseline = sum(scores) / len(scores)

        # Baseline should be reasonable (not too low, can be near-perfect for good conversations)
        assert 50.0 <= baseline <= 100.0

        # Track for documentation
        print(f"\n" + "=" * 60)
        print(f"BASELINE QUALITY SCORE: {baseline:.2f}%")
        print(f"Sample size: {len(scores)} conversations")
        print(f"Min: {min(scores):.2f}%, Max: {max(scores):.2f}%")
        print("=" * 60)


class TestScoreInReport:
    """Test score is included in quality report."""

    def test_score_in_report_dict(self, tmp_path):
        """Test score appears in report.to_dict()."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=10)
        report.quality_score = 95.5

        report_dict = report.to_dict()

        assert "quality_score" in report_dict
        assert report_dict["quality_score"] == 95.5

    def test_score_rounded_to_2_decimals(self, tmp_path):
        """Test score is rounded to 2 decimal places."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=10)
        report.quality_score = 95.5555

        report_dict = report.to_dict()

        # Should be rounded to 2 decimals
        assert report_dict["quality_score"] == 95.56
