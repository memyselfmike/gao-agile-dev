"""Quality report generator for conversation analysis.

Story: 37.4 - Quality Reporting
Epic: 37 - UX Quality Analysis

Generates human-readable reports from QualityReport objects with
actionable recommendations and turn-by-turn analysis.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from tests.e2e.models.quality_models import (
    QualityReport,
    QualityIssue,
    IssueType,
    IssueSeverity,
)


class ReportGenerator:
    """
    Generate formatted quality reports from analysis results.

    AC1: ReportGenerator.generate() method implemented
    AC2-AC5: Report formatting with summary, turn-by-turn, recommendations
    AC8: Can be saved to file or displayed in console
    """

    def generate(
        self, report: QualityReport, format: str = "text", include_details: bool = True
    ) -> str:
        """
        Generate formatted quality report.

        AC1: Core generation method

        Args:
            report: QualityReport to format
            format: Output format ("text" or "markdown")
            include_details: Include turn-by-turn details

        Returns:
            Formatted report string (AC5: human-readable)
        """
        if format == "markdown":
            return self._generate_markdown(report, include_details)
        else:
            return self._generate_text(report, include_details)

    def save_to_file(self, report: QualityReport, output_path: Path) -> None:
        """
        Save report to file.

        AC8: Reports can be saved to file

        Args:
            report: QualityReport to save
            output_path: Output file path
        """
        content = self.generate(report)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_text(self, report: QualityReport, include_details: bool) -> str:
        """Generate text format report."""
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("CONVERSATION QUALITY REPORT")
        lines.append("=" * 80)
        lines.append("")

        # AC2: Overall Summary
        lines.append(f"Transcript: {report.transcript_path.name}")
        lines.append(f"Analyzed: {report.analyzed_at or 'N/A'}")
        lines.append(f"Analysis Duration: {report.analysis_duration_seconds:.3f}s")
        lines.append("")

        # AC2: Quality Score
        lines.append(f"QUALITY SCORE: {report.quality_score:.2f}%")
        lines.append(self._get_score_rating(report.quality_score))
        lines.append("")

        # AC2: Summary Statistics
        lines.append("SUMMARY STATISTICS:")
        lines.append(f"  Total Turns: {report.total_turns}")
        lines.append(f"  Total Issues: {len(report.issues)}")
        lines.append("")

        # Issue counts by severity
        severity_counts = report.get_issue_count_by_severity()
        lines.append("  Issues by Severity:")
        for severity in [
            IssueSeverity.CRITICAL,
            IssueSeverity.HIGH,
            IssueSeverity.MEDIUM,
            IssueSeverity.LOW,
        ]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                lines.append(f"    {severity.value.upper()}: {count}")

        # Issue counts by type
        type_counts = report.get_issue_count_by_type()
        lines.append("")
        lines.append("  Issues by Type:")
        for issue_type in IssueType:
            count = type_counts.get(issue_type, 0)
            if count > 0:
                lines.append(f"    {issue_type.value}: {count}")

        lines.append("")
        lines.append("-" * 80)

        # AC3: Turn-by-turn Analysis (if requested)
        if include_details and report.issues:
            lines.append("")
            lines.append("DETAILED ANALYSIS:")
            lines.append("")

            # Group issues by turn
            issues_by_turn = {}
            for issue in report.issues:
                if issue.turn_num not in issues_by_turn:
                    issues_by_turn[issue.turn_num] = []
                issues_by_turn[issue.turn_num].append(issue)

            # Display turn-by-turn
            for turn_num in sorted(issues_by_turn.keys()):
                issues = issues_by_turn[turn_num]
                lines.append(f"Turn {turn_num}:")

                for issue in issues:
                    lines.append(f"  - [{issue.severity.value.upper()}] {issue.issue_type.value}")
                    lines.append(f"    Problem: {issue.description}")
                    lines.append(f"    Fix: {issue.suggestion}")
                    if issue.pattern_matched:
                        lines.append(f"    Pattern: {issue.pattern_matched}")
                    lines.append("")

            lines.append("-" * 80)

        # AC4: Actionable Recommendations
        lines.append("")
        lines.append("RECOMMENDATIONS:")
        lines.append("")

        recommendations = self._generate_recommendations(report)
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _generate_markdown(self, report: QualityReport, include_details: bool) -> str:
        """Generate markdown format report."""
        lines = []

        # Header
        lines.append("# Conversation Quality Report")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Transcript**: {report.transcript_path.name}")
        lines.append(f"- **Analyzed**: {report.analyzed_at or 'N/A'}")
        lines.append(f"- **Analysis Duration**: {report.analysis_duration_seconds:.3f}s")
        lines.append(f"- **Total Turns**: {report.total_turns}")
        lines.append(f"- **Total Issues**: {len(report.issues)}")
        lines.append("")

        # Quality Score
        lines.append("## Quality Score")
        lines.append("")
        lines.append(f"**{report.quality_score:.2f}%** - {self._get_score_rating(report.quality_score)}")
        lines.append("")

        # Issue breakdown
        lines.append("## Issue Breakdown")
        lines.append("")

        severity_counts = report.get_issue_count_by_severity()
        type_counts = report.get_issue_count_by_type()

        lines.append("### By Severity")
        lines.append("")
        for severity in [
            IssueSeverity.CRITICAL,
            IssueSeverity.HIGH,
            IssueSeverity.MEDIUM,
            IssueSeverity.LOW,
        ]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                lines.append(f"- **{severity.value.upper()}**: {count}")

        lines.append("")
        lines.append("### By Type")
        lines.append("")
        for issue_type in IssueType:
            count = type_counts.get(issue_type, 0)
            if count > 0:
                lines.append(f"- **{issue_type.value}**: {count}")

        # Detailed Analysis
        if include_details and report.issues:
            lines.append("")
            lines.append("## Detailed Analysis")
            lines.append("")

            issues_by_turn = {}
            for issue in report.issues:
                if issue.turn_num not in issues_by_turn:
                    issues_by_turn[issue.turn_num] = []
                issues_by_turn[issue.turn_num].append(issue)

            for turn_num in sorted(issues_by_turn.keys()):
                issues = issues_by_turn[turn_num]
                lines.append(f"### Turn {turn_num}")
                lines.append("")

                for issue in issues:
                    lines.append(f"**[{issue.severity.value.upper()}] {issue.issue_type.value}**")
                    lines.append(f"- Problem: {issue.description}")
                    lines.append(f"- Fix: {issue.suggestion}")
                    lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        lines.append("")

        recommendations = self._generate_recommendations(report)
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")

        return "\n".join(lines)

    def _get_score_rating(self, score: float) -> str:
        """Get qualitative rating for score."""
        if score >= 95:
            return "Excellent - Minimal UX issues"
        elif score >= 85:
            return "Good - Minor UX improvements possible"
        elif score >= 75:
            return "Fair - Noticeable UX issues to address"
        elif score >= 60:
            return "Poor - Significant UX problems"
        else:
            return "Critical - Major conversation failures"

    def _generate_recommendations(self, report: QualityReport) -> list:
        """
        Generate actionable recommendations.

        AC4: Recommendations are specific and actionable
        AC6: 80%+ of recommendations are actionable

        Returns:
            List of actionable recommendation strings
        """
        recommendations = []

        # Analyze by issue type
        type_counts = report.get_issue_count_by_type()

        # Intent misunderstanding recommendations
        if type_counts.get(IssueType.INTENT_MISUNDERSTANDING, 0) > 0:
            recommendations.append(
                "CRITICAL: Improve intent understanding by using confirmation signals "
                "before proceeding ('To confirm, you want...')"
            )

        # Probing recommendations
        if type_counts.get(IssueType.MISSED_PROBING, 0) > 1:
            recommendations.append(
                "Ask clarifying questions when user input is vague. "
                "Example: 'What specific features are you looking for?'"
            )

        # Context recommendations
        if type_counts.get(IssueType.UNUSED_CONTEXT, 0) > 0:
            recommendations.append(
                "Reference available context in responses. "
                "Example: 'For Epic X, Story Y...' or 'Given the current project context...'"
            )

        # Relevance recommendations
        if type_counts.get(IssueType.POOR_RELEVANCE, 0) > 1:
            recommendations.append(
                "Provide detailed, specific responses instead of generic acknowledgments. "
                "Add concrete examples or actionable next steps."
            )

        # Confirmation recommendations
        if type_counts.get(IssueType.NO_CONFIRMATION, 0) > 0:
            recommendations.append(
                "Confirm understanding before taking action to prevent misalignment. "
                "Example: 'To confirm, I'll create...'"
            )

        # General score-based recommendations
        if report.quality_score < 85:
            recommendations.append(
                "Focus on proactive communication: confirm intent, ask follow-up questions, "
                "and provide detailed explanations."
            )

        # If no specific recommendations, add general one
        if not recommendations:
            recommendations.append(
                "Continue maintaining high conversation quality. "
                "Focus on confirmation signals and detailed responses."
            )

        return recommendations
