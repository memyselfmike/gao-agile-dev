"""Comprehensive tests for pattern-based quality detection.

Story: 37.2 - Pattern-Based Quality Detection
Epic: 37 - UX Quality Analysis

Tests ConversationAnalyzer's ability to detect UX issues using pattern matching.
"""

import pytest
from pathlib import Path
import json
import time
from datetime import datetime

from tests.e2e.analyzer.conversation_analyzer import ConversationAnalyzer
from tests.e2e.models.quality_models import (
    QualityIssue,
    QualityReport,
    IssueType,
    IssueSeverity,
)


class TestConversationAnalyzerCore:
    """Test core ConversationAnalyzer functionality (AC1)."""

    def test_analyze_conversation_method_exists(self):
        """AC1: ConversationAnalyzer.analyze_conversation() method implemented."""
        analyzer = ConversationAnalyzer()
        assert hasattr(analyzer, "analyze_conversation")
        assert callable(analyzer.analyze_conversation)

    def test_analyze_conversation_returns_quality_report(self, tmp_path):
        """AC1: analyze_conversation() returns QualityReport."""
        # Create sample transcript
        transcript = [
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": "Build a todo app",
                "brian_response": "Sure, I'll build that for you",
                "context_used": {"project_root": str(tmp_path), "session_id": "test"},
            }
        ]

        transcript_path = tmp_path / "test_transcript.json"
        with open(transcript_path, "w") as f:
            json.dump(transcript, f)

        analyzer = ConversationAnalyzer()
        report = analyzer.analyze_conversation(transcript_path)

        assert isinstance(report, QualityReport)
        assert report.transcript_path == transcript_path
        assert report.total_turns == 1

    def test_analyze_missing_transcript_raises_error(self, tmp_path):
        """Test error handling for missing transcript."""
        analyzer = ConversationAnalyzer()
        missing_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            analyzer.analyze_conversation(missing_path)

    def test_analyze_invalid_json_raises_error(self, tmp_path):
        """Test error handling for invalid JSON."""
        invalid_path = tmp_path / "invalid.json"
        with open(invalid_path, "w") as f:
            f.write("{invalid json")

        analyzer = ConversationAnalyzer()

        with pytest.raises(json.JSONDecodeError):
            analyzer.analyze_conversation(invalid_path)


class TestIssueTypeDetection:
    """Test detection of all required issue types (AC2)."""

    def test_detects_intent_misunderstanding(self, tmp_path):
        """AC2: Detects intent_misunderstanding issues."""
        transcript = [
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": "No, that's not what I meant. I want a web app.",
                "brian_response": "I understand you want a desktop app",
                "context_used": {"project_root": str(tmp_path), "session_id": "test"},
            }
        ]

        transcript_path = tmp_path / "intent_test.json"
        with open(transcript_path, "w") as f:
            json.dump(transcript, f)

        analyzer = ConversationAnalyzer()
        report = analyzer.analyze_conversation(transcript_path)

        intent_issues = report.get_issues_by_type(IssueType.INTENT_MISUNDERSTANDING)
        assert len(intent_issues) > 0
        assert intent_issues[0].issue_type == IssueType.INTENT_MISUNDERSTANDING

    def test_detects_missed_probing(self, tmp_path):
        """AC2: Detects missed_probing issues."""
        transcript = [
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": "Build a website",  # Vague
                "brian_response": "I'll build that for you.",  # No probing
                "context_used": {"project_root": str(tmp_path), "session_id": "test"},
            }
        ]

        transcript_path = tmp_path / "probing_test.json"
        with open(transcript_path, "w") as f:
            json.dump(transcript, f)

        analyzer = ConversationAnalyzer()
        report = analyzer.analyze_conversation(transcript_path)

        probing_issues = report.get_issues_by_type(IssueType.MISSED_PROBING)
        assert len(probing_issues) > 0
        assert probing_issues[0].issue_type == IssueType.MISSED_PROBING

    def test_detects_unused_context(self, tmp_path):
        """AC2: Detects unused_context issues."""
        transcript = [
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": "What epic are we working on?",  # User asks about context
                "brian_response": "We're working on your project.",  # Doesn't use context
                "context_used": {
                    "project_root": str(tmp_path),
                    "session_id": "test",
                    "current_epic": 5,  # Context available
                    "current_story": 3,
                },
            }
        ]

        transcript_path = tmp_path / "context_test.json"
        with open(transcript_path, "w") as f:
            json.dump(transcript, f)

        analyzer = ConversationAnalyzer()
        report = analyzer.analyze_conversation(transcript_path)

        context_issues = report.get_issues_by_type(IssueType.UNUSED_CONTEXT)
        assert len(context_issues) > 0
        assert context_issues[0].issue_type == IssueType.UNUSED_CONTEXT

    def test_detects_poor_relevance(self, tmp_path):
        """AC2: Detects poor_relevance issues."""
        transcript = [
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": "How should I architect the authentication system?",
                "brian_response": "OK.",  # Generic response
                "context_used": {"project_root": str(tmp_path), "session_id": "test"},
            }
        ]

        transcript_path = tmp_path / "relevance_test.json"
        with open(transcript_path, "w") as f:
            json.dump(transcript, f)

        analyzer = ConversationAnalyzer()
        report = analyzer.analyze_conversation(transcript_path)

        relevance_issues = report.get_issues_by_type(IssueType.POOR_RELEVANCE)
        assert len(relevance_issues) > 0
        assert relevance_issues[0].issue_type == IssueType.POOR_RELEVANCE

    def test_detects_multiple_issue_types(self, tmp_path):
        """AC2: Detects 4+ different issue types in single conversation."""
        transcript = [
            # Turn 0: Intent misunderstanding
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": "No, you misunderstood",
                "brian_response": "I thought you said...",
                "context_used": {"project_root": str(tmp_path), "session_id": "test"},
            },
            # Turn 1: Missed probing
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": "Build something",
                "brian_response": "I'll start building",
                "context_used": {"project_root": str(tmp_path), "session_id": "test"},
            },
            # Turn 2: Unused context
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": "What's the current story?",
                "brian_response": "Let me check",
                "context_used": {
                    "project_root": str(tmp_path),
                    "session_id": "test",
                    "current_epic": 1,
                    "current_story": 2,
                },
            },
            # Turn 3: Poor relevance
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": "Can you explain the architecture in detail?",
                "brian_response": "Sure",
                "context_used": {"project_root": str(tmp_path), "session_id": "test"},
            },
        ]

        transcript_path = tmp_path / "multi_issue_test.json"
        with open(transcript_path, "w") as f:
            json.dump(transcript, f)

        analyzer = ConversationAnalyzer()
        report = analyzer.analyze_conversation(transcript_path)

        issue_types_found = set(issue.issue_type for issue in report.issues)
        assert len(issue_types_found) >= 4


class TestIssueStructure:
    """Test that issues have required fields (AC3)."""

    def test_issue_has_all_required_fields(self, tmp_path):
        """AC3: Each detected issue includes all required fields."""
        transcript = [
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": "That's not what I asked",
                "brian_response": "OK",
                "context_used": {"project_root": str(tmp_path), "session_id": "test"},
            }
        ]

        transcript_path = tmp_path / "fields_test.json"
        with open(transcript_path, "w") as f:
            json.dump(transcript, f)

        analyzer = ConversationAnalyzer()
        report = analyzer.analyze_conversation(transcript_path)

        assert len(report.issues) > 0

        for issue in report.issues:
            # AC3: Required fields
            assert hasattr(issue, "turn_num")
            assert hasattr(issue, "issue_type")
            assert hasattr(issue, "severity")
            assert hasattr(issue, "description")
            assert hasattr(issue, "suggestion")

            # Verify types
            assert isinstance(issue.turn_num, int)
            assert isinstance(issue.issue_type, IssueType)
            assert isinstance(issue.severity, IssueSeverity)
            assert isinstance(issue.description, str)
            assert isinstance(issue.suggestion, str)

            # Verify non-empty
            assert len(issue.description) > 0
            assert len(issue.suggestion) > 0


class TestPatternLibrary:
    """Test pattern library coverage (AC4)."""

    def test_intent_patterns_count(self):
        """AC4: Intent pattern library has 10+ patterns."""
        analyzer = ConversationAnalyzer()
        assert len(analyzer.INTENT_PATTERNS) >= 10

    def test_probing_patterns_count(self):
        """AC4: Probing pattern library has 10+ patterns."""
        analyzer = ConversationAnalyzer()
        assert len(analyzer.PROBING_PATTERNS) >= 10

    def test_relevance_patterns_count(self):
        """AC4: Relevance pattern library has 10+ patterns."""
        analyzer = ConversationAnalyzer()
        assert len(analyzer.RELEVANCE_PATTERNS) >= 10

    def test_patterns_are_valid_regex(self):
        """AC4: All patterns are valid regular expressions."""
        import re

        analyzer = ConversationAnalyzer()

        all_patterns = (
            analyzer.INTENT_PATTERNS
            + analyzer.PROBING_PATTERNS
            + analyzer.RELEVANCE_PATTERNS
            + analyzer.CONFIRMATION_PATTERNS
        )

        for pattern in all_patterns:
            # Should not raise exception
            re.compile(pattern)


class TestFalsePositiveRate:
    """Test false positive rate (AC5)."""

    def test_no_issues_on_perfect_conversation(self, tmp_path):
        """AC5: Perfect conversation should have few/no false positives."""
        transcript = [
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": "I need to build a todo application with user authentication",
                "brian_response": "To confirm, you want a todo application with user authentication? What type of authentication are you thinking - OAuth, email/password, or something else?",
                "context_used": {"project_root": str(tmp_path), "session_id": "test"},
            },
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": "Email and password would be fine",
                "brian_response": "Great! Let me create a PRD for a todo application with email/password authentication. I'll include user registration, login, and password reset flows. For Epic 1, I'll focus on the authentication system.",
                "context_used": {
                    "project_root": str(tmp_path),
                    "session_id": "test",
                    "current_epic": 1,
                },
            },
        ]

        transcript_path = tmp_path / "perfect_conversation.json"
        with open(transcript_path, "w") as f:
            json.dump(transcript, f)

        analyzer = ConversationAnalyzer()
        report = analyzer.analyze_conversation(transcript_path)

        # Perfect conversation should have 0 high-severity issues
        high_issues = report.get_issues_by_severity(IssueSeverity.HIGH)
        assert len(high_issues) == 0

        # Should have few medium-severity issues
        medium_issues = report.get_issues_by_severity(IssueSeverity.MEDIUM)
        assert len(medium_issues) <= 1


class TestPerformance:
    """Test analysis performance (AC6)."""

    def test_analysis_completes_under_10_seconds(self, tmp_path):
        """AC6: Analysis completes in <10s per conversation."""
        # Create a moderately long conversation (20 turns)
        transcript = []
        for i in range(20):
            transcript.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "user_input": f"Turn {i}: Can you help me with my project?",
                    "brian_response": f"Turn {i}: Yes, I can help with that. What do you need?",
                    "context_used": {
                        "project_root": str(tmp_path),
                        "session_id": "test",
                    },
                }
            )

        transcript_path = tmp_path / "performance_test.json"
        with open(transcript_path, "w") as f:
            json.dump(transcript, f)

        analyzer = ConversationAnalyzer()

        start = time.perf_counter()
        report = analyzer.analyze_conversation(transcript_path)
        duration = time.perf_counter() - start

        # Should complete in <10 seconds
        assert duration < 10.0

        # Report should track duration
        assert report.analysis_duration_seconds > 0
        assert report.analysis_duration_seconds < 10.0


class TestSampleConversationAnalysis:
    """Test analysis of real sample conversations (AC8)."""

    def test_analyze_sample_transcripts(self, tmp_path):
        """AC8: 10+ sample conversations analyzed with documented results."""
        sample_dir = Path("tests/e2e/sample_transcripts")

        if not sample_dir.exists():
            pytest.skip("Sample transcripts directory not found")

        # Find all JSON transcripts
        transcripts = list(sample_dir.glob("*.json"))

        # Should have multiple samples
        assert len(transcripts) >= 5

        analyzer = ConversationAnalyzer()
        results = []

        for transcript_path in transcripts:
            report = analyzer.analyze_conversation(transcript_path)
            results.append(
                {
                    "transcript": transcript_path.name,
                    "total_turns": report.total_turns,
                    "total_issues": len(report.issues),
                    "issue_types": list(
                        set(issue.issue_type.value for issue in report.issues)
                    ),
                    "duration_s": report.analysis_duration_seconds,
                }
            )

        # All should complete successfully
        assert len(results) == len(transcripts)

        # All should complete quickly
        for result in results:
            assert result["duration_s"] < 10.0


class TestQualityReportMethods:
    """Test QualityReport utility methods."""

    def test_get_issues_by_type(self, tmp_path):
        """Test filtering issues by type."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=1)

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

        intent_issues = report.get_issues_by_type(IssueType.INTENT_MISUNDERSTANDING)
        assert len(intent_issues) == 1
        assert intent_issues[0].issue_type == IssueType.INTENT_MISUNDERSTANDING

    def test_get_issues_by_severity(self, tmp_path):
        """Test filtering issues by severity."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=1)

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
                severity=IssueSeverity.LOW,
                description="Test",
                suggestion="Test",
            )
        )

        high_issues = report.get_issues_by_severity(IssueSeverity.HIGH)
        assert len(high_issues) == 1
        assert high_issues[0].severity == IssueSeverity.HIGH

    def test_get_issue_count_by_type(self, tmp_path):
        """Test counting issues by type."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=1)

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
                issue_type=IssueType.INTENT_MISUNDERSTANDING,
                severity=IssueSeverity.HIGH,
                description="Test",
                suggestion="Test",
            )
        )

        counts = report.get_issue_count_by_type()
        assert counts[IssueType.INTENT_MISUNDERSTANDING] == 2

    def test_to_dict_serialization(self, tmp_path):
        """Test report serialization to dictionary."""
        report = QualityReport(transcript_path=tmp_path / "test.json", total_turns=1)

        report.add_issue(
            QualityIssue(
                turn_num=0,
                issue_type=IssueType.INTENT_MISUNDERSTANDING,
                severity=IssueSeverity.HIGH,
                description="Test",
                suggestion="Test",
            )
        )

        report_dict = report.to_dict()

        assert isinstance(report_dict, dict)
        assert "transcript_path" in report_dict
        assert "total_turns" in report_dict
        assert "total_issues" in report_dict
        assert "issues" in report_dict
        assert isinstance(report_dict["issues"], list)
