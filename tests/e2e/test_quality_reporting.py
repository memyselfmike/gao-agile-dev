"""Comprehensive tests for quality reporting.

Story: 37.4 - Quality Reporting
Epic: 37 - UX Quality Analysis

Tests the report generation with actionable recommendations.
"""

import pytest
from pathlib import Path
from datetime import datetime

from tests.e2e.reporting.quality_report_generator import ReportGenerator
from tests.e2e.models.quality_models import (
    QualityReport,
    QualityIssue,
    IssueType,
    IssueSeverity,
)
from tests.e2e.analyzer.conversation_analyzer import ConversationAnalyzer


class TestReportGeneratorCore:
    """Test ReportGenerator.generate() method (AC1)."""

    def test_generate_method_exists(self):
        """AC1: ReportGenerator.generate() method implemented."""
        generator = ReportGenerator()
        assert hasattr(generator, "generate")
        assert callable(generator.generate)

    def test_generate_returns_string(self, tmp_path):
        """AC1: generate() returns formatted string."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)
        report.quality_score = 95.0

        generator = ReportGenerator()
        output = generator.generate(report)

        assert isinstance(output, str)
        assert len(output) > 0


class TestReportSummary:
    """Test report includes summary information (AC2)."""

    def test_report_includes_quality_score(self, tmp_path):
        """AC2: Report includes overall quality score."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=10)
        report.quality_score = 87.5

        generator = ReportGenerator()
        output = generator.generate(report)

        assert "87.5" in output or "87.50" in output
        assert "QUALITY SCORE" in output or "Quality Score" in output

    def test_report_includes_total_turns(self, tmp_path):
        """AC2: Report includes total turns."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=15)

        generator = ReportGenerator()
        output = generator.generate(report)

        assert "15" in output
        assert "turns" in output.lower() or "Turns" in output

    def test_report_includes_issues_count(self, tmp_path):
        """AC2: Report includes issues count."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=10)

        # Add 3 issues
        for i in range(3):
            report.add_issue(
                QualityIssue(
                    i, IssueType.MISSED_PROBING, IssueSeverity.MEDIUM, "Test", "Test"
                )
            )

        generator = ReportGenerator()
        output = generator.generate(report)

        assert "3" in output
        assert "issues" in output.lower() or "Issues" in output


class TestTurnByTurnAnalysis:
    """Test turn-by-turn analysis (AC3)."""

    def test_report_shows_turn_numbers(self, tmp_path):
        """AC3: Turn-by-turn analysis shows turn numbers."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)

        report.add_issue(
            QualityIssue(
                0,
                IssueType.INTENT_MISUNDERSTANDING,
                IssueSeverity.HIGH,
                "User had to clarify",
                "Confirm intent before proceeding",
            )
        )

        report.add_issue(
            QualityIssue(
                2,
                IssueType.MISSED_PROBING,
                IssueSeverity.MEDIUM,
                "Vague input not probed",
                "Ask clarifying questions",
            )
        )

        generator = ReportGenerator()
        output = generator.generate(report, include_details=True)

        assert "Turn 0" in output
        assert "Turn 2" in output

    def test_report_includes_issue_examples(self, tmp_path):
        """AC3: Turn-by-turn shows issues with examples."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)

        report.add_issue(
            QualityIssue(
                0,
                IssueType.INTENT_MISUNDERSTANDING,
                IssueSeverity.HIGH,
                "User said: 'No, that's not what I meant'",
                "Use confirmation signals",
            )
        )

        generator = ReportGenerator()
        output = generator.generate(report, include_details=True)

        assert "not what I meant" in output
        assert "confirmation" in output.lower()


class TestActionableRecommendations:
    """Test recommendations are specific and actionable (AC4, AC6)."""

    def test_recommendations_are_specific(self, tmp_path):
        """AC4: Recommendations are specific, not generic."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=10)

        report.add_issue(
            QualityIssue(
                0,
                IssueType.INTENT_MISUNDERSTANDING,
                IssueSeverity.HIGH,
                "Test",
                "Test",
            )
        )

        generator = ReportGenerator()
        output = generator.generate(report)

        # Should have specific recommendation about intent
        assert "RECOMMENDATIONS" in output or "Recommendations" in output

        # Should mention confirmation signals (specific)
        assert "confirm" in output.lower() or "clarify" in output.lower()

    def test_recommendations_include_examples(self, tmp_path):
        """AC4: Recommendations include specific examples."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=10)

        # Add 2 probing issues to trigger specific recommendation
        report.add_issue(
            QualityIssue(
                0,
                IssueType.MISSED_PROBING,
                IssueSeverity.MEDIUM,
                "Test",
                "Test",
            )
        )
        report.add_issue(
            QualityIssue(
                1,
                IssueType.MISSED_PROBING,
                IssueSeverity.MEDIUM,
                "Test2",
                "Test2",
            )
        )

        generator = ReportGenerator()
        output = generator.generate(report)

        # Should include example questions
        assert "?" in output or "example" in output.lower() or "Example" in output

    def test_critical_issues_get_priority_recommendations(self, tmp_path):
        """AC4: Critical issues appear in recommendations."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)

        report.add_issue(
            QualityIssue(
                0,
                IssueType.INTENT_MISUNDERSTANDING,
                IssueSeverity.CRITICAL,
                "Total conversation failure",
                "Test",
            )
        )

        generator = ReportGenerator()
        output = generator.generate(report)

        # Intent misunderstanding should be in recommendations
        recommendations_section = output.split("RECOMMENDATIONS")[-1]
        assert "intent" in recommendations_section.lower() or "confirm" in recommendations_section.lower()


class TestReportFormat:
    """Test report format is human-readable (AC5)."""

    def test_report_has_header(self, tmp_path):
        """AC5: Report has clear header."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)

        generator = ReportGenerator()
        output = generator.generate(report)

        # Should have a header
        assert "QUALITY REPORT" in output or "Quality Report" in output

    def test_report_has_sections(self, tmp_path):
        """AC5: Report is well-structured with sections."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)

        generator = ReportGenerator()
        output = generator.generate(report)

        # Should have multiple sections
        assert "SUMMARY" in output or "Summary" in output
        assert "RECOMMENDATIONS" in output or "Recommendations" in output

    def test_report_uses_visual_separators(self, tmp_path):
        """AC5: Report uses visual separators for readability."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)

        generator = ReportGenerator()
        output = generator.generate(report)

        # Should have visual separators (lines)
        assert "=" in output or "-" in output

    def test_markdown_format_supported(self, tmp_path):
        """AC5: Markdown format is supported."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)

        generator = ReportGenerator()
        output = generator.generate(report, format="markdown")

        # Should have markdown headers
        assert "#" in output or "**" in output


class TestFileSaving:
    """Test reports can be saved to file (AC8)."""

    def test_save_to_file_creates_file(self, tmp_path):
        """AC8: save_to_file() creates output file."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)
        report.quality_score = 90.0

        output_path = tmp_path / "reports" / "quality_report.txt"

        generator = ReportGenerator()
        generator.save_to_file(report, output_path)

        assert output_path.exists()

    def test_saved_file_contains_report(self, tmp_path):
        """AC8: Saved file contains full report."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)
        report.quality_score = 85.5

        output_path = tmp_path / "quality_report.txt"

        generator = ReportGenerator()
        generator.save_to_file(report, output_path)

        with open(output_path, "r") as f:
            content = f.read()

        assert "85.5" in content or "85.50" in content
        assert "QUALITY" in content or "Quality" in content


class TestRealSampleReports:
    """Test report generation on real sample conversations (AC7)."""

    def test_generate_reports_for_samples(self, tmp_path):
        """AC7: Generate reports for sample conversations."""
        sample_dir = Path("tests/e2e/sample_transcripts")

        if not sample_dir.exists():
            pytest.skip("Sample transcripts not found")

        transcripts = list(sample_dir.glob("*.json"))
        if len(transcripts) == 0:
            pytest.skip("No sample transcripts")

        analyzer = ConversationAnalyzer()
        generator = ReportGenerator()

        reports_generated = 0

        for transcript_path in transcripts[:3]:  # Test first 3
            # Analyze
            report = analyzer.analyze_conversation(transcript_path)

            # Generate report
            output = generator.generate(report)

            # Should be valid
            assert len(output) > 100  # Substantial content
            assert "QUALITY SCORE" in output or "Quality Score" in output
            assert "RECOMMENDATIONS" in output or "Recommendations" in output

            reports_generated += 1

        assert reports_generated >= 3


class TestScoreRatings:
    """Test qualitative score ratings."""

    def test_excellent_rating(self, tmp_path):
        """Test 95%+ gets 'Excellent' rating."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)
        report.quality_score = 97.0

        generator = ReportGenerator()
        output = generator.generate(report)

        assert "Excellent" in output or "excellent" in output

    def test_good_rating(self, tmp_path):
        """Test 85-95% gets 'Good' rating."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)
        report.quality_score = 88.0

        generator = ReportGenerator()
        output = generator.generate(report)

        assert "Good" in output or "good" in output

    def test_low_score_rating(self, tmp_path):
        """Test low scores get appropriate rating."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=5)
        report.quality_score = 55.0

        generator = ReportGenerator()
        output = generator.generate(report)

        # Should indicate poor/critical quality
        assert "poor" in output.lower() or "critical" in output.lower()
