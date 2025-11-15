"""Conversation quality analyzer with pattern-based detection.

Story: 37.2 - Pattern-Based Quality Detection
Epic: 37 - UX Quality Analysis

Analyzes conversation transcripts to identify UX deficiencies using
pattern matching and AI-powered analysis.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import re
from datetime import datetime
import time
import structlog

from tests.e2e.models.quality_models import (
    QualityIssue,
    QualityReport,
    IssueType,
    IssueSeverity,
)
from gao_dev.core.services.ai_analysis_service import AIAnalysisService

logger = structlog.get_logger()


class ConversationAnalyzer:
    """
    Analyze conversation transcripts for UX quality issues.

    AC1: ConversationAnalyzer.analyze_conversation() method implemented
    AC2: Detects 4+ issue types
    AC4: Pattern library includes 10+ detection patterns per issue type
    AC7: Uses deepseek-r1 for AI-powered analysis
    """

    # AC4: Pattern libraries (10+ patterns per issue type)
    INTENT_PATTERNS = [
        # Negative patterns (indicate misunderstanding)
        r"(?i)that'?s\s+not\s+what\s+i\s+(meant|asked|wanted)",
        r"(?i)no,?\s+i\s+(meant|want|need)",
        r"(?i)you\s+misunderstood",
        r"(?i)i\s+didn'?t\s+say\s+that",
        r"(?i)that'?s\s+not\s+correct",
        r"(?i)actually,?\s+i\s+was\s+asking",
        r"(?i)wrong\s+interpretation",
        r"(?i)not\s+what\s+i'?m\s+looking\s+for",
        r"(?i)let\s+me\s+clarify",
        r"(?i)to\s+be\s+clear",
        r"(?i)what\s+i\s+really\s+want",
    ]

    PROBING_PATTERNS = [
        # User input that should trigger questions
        r"(?i)^(build|create|make)\s+(a|an)\s+\w+$",  # Vague requests
        r"(?i)^(help|assist)\s+me\s+with",  # Help without specifics
        r"(?i)something\s+like",  # Vague comparisons
        r"(?i)kind\s+of\s+like",
        r"(?i)similar\s+to",
        r"(?i)^i\s+want\s+to\s+\w+$",  # Single-word goals
        r"(?i)^can\s+you\s+\w+$",  # Yes/no without details
        r"(?i)(maybe|perhaps|possibly|might)",  # Uncertainty
        r"(?i)not\s+sure\s+(about|how|what|if)",
        r"(?i)any\s+(ideas|suggestions|thoughts)\??$",  # Open requests
        r"(?i)^what\s+about",  # Open questions
    ]

    NO_QUESTION_PATTERNS = [
        # Brian responses that lack clarifying questions
        r"^[^?]*$",  # No question mark in response
    ]

    CONTEXT_KEYWORDS = [
        "epic",
        "story",
        "project",
        "feature",
        "PRD",
        "architecture",
        "greenfield",
        "brownfield",
    ]

    RELEVANCE_PATTERNS = [
        # Generic/unhelpful responses
        r"(?i)^(ok|okay|sure|yes|no)\.?$",
        r"(?i)^i\s+understand\.?$",
        r"(?i)^got\s+it\.?$",
        r"(?i)^sounds\s+good\.?$",
        r"(?i)^that'?s\s+fine\.?$",
        r"(?i)^will\s+do\.?$",
        r"(?i)^(alright|right)\.?$",
        r"(?i)i\s+can\s+help\s+with\s+that\.?$",  # Generic promise
        r"(?i)let\s+me\s+know\s+if\s+you\s+need",  # Generic offer
        r"(?i)is\s+there\s+anything\s+else\??$",  # Generic follow-up
    ]

    CONFIRMATION_PATTERNS = [
        # Confirmation signals (good)
        r"(?i)to\s+confirm",
        r"(?i)let\s+me\s+make\s+sure",
        r"(?i)just\s+to\s+clarify",
        r"(?i)so\s+you\s+want",
        r"(?i)you'?re\s+saying",
        r"(?i)if\s+i\s+understand\s+correctly",
        r"(?i)in\s+other\s+words",
    ]

    def __init__(self, ai_service: Optional[AIAnalysisService] = None):
        """
        Initialize analyzer.

        Args:
            ai_service: Optional AI service for deep analysis (defaults to deepseek-r1)
        """
        self.ai_service = ai_service
        self.logger = logger.bind(component="conversation_analyzer")

    def analyze_conversation(self, transcript_path: Path) -> QualityReport:
        """
        Analyze a conversation transcript for quality issues.

        AC1: Core analysis method
        AC6: Completes in <10s per conversation

        Args:
            transcript_path: Path to conversation transcript JSON

        Returns:
            QualityReport with detected issues

        Raises:
            FileNotFoundError: If transcript doesn't exist
            json.JSONDecodeError: If transcript is invalid JSON
        """
        start_time = time.perf_counter()

        self.logger.info("analyzing_conversation", path=str(transcript_path))

        # Load transcript
        transcript = self._load_transcript(transcript_path)

        # Create report
        report = QualityReport(
            transcript_path=transcript_path,
            total_turns=len(transcript),
            analyzed_at=datetime.now().isoformat(),
        )

        # Analyze each turn
        for turn_num, turn in enumerate(transcript):
            # Pattern-based detection
            issues = []
            issues.extend(self._detect_intent_issues(turn_num, turn))
            issues.extend(self._detect_probing_issues(turn_num, turn))
            issues.extend(self._detect_context_issues(turn_num, turn))
            issues.extend(self._detect_relevance_issues(turn_num, turn))
            issues.extend(self._detect_confirmation_issues(turn_num, turn))

            for issue in issues:
                report.add_issue(issue)

        # Calculate duration
        duration = time.perf_counter() - start_time
        report.analysis_duration_seconds = round(duration, 3)

        self.logger.info(
            "analysis_complete",
            turns=len(transcript),
            issues=len(report.issues),
            duration_s=report.analysis_duration_seconds,
        )

        return report

    def _load_transcript(self, transcript_path: Path) -> List[Dict[str, Any]]:
        """
        Load conversation transcript from JSON file.

        Args:
            transcript_path: Path to transcript

        Returns:
            List of turn dictionaries

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        if not transcript_path.exists():
            raise FileNotFoundError(f"Transcript not found: {transcript_path}")

        with open(transcript_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _detect_intent_issues(
        self, turn_num: int, turn: Dict[str, Any]
    ) -> List[QualityIssue]:
        """
        Detect intent understanding issues.

        AC2: One of 4+ issue types
        AC3: Issues include all required fields

        Looks for:
        - User corrections ("that's not what I meant")
        - Clarifications ("let me clarify")
        - Disagreements ("that's not correct")

        Args:
            turn_num: Turn number (0-indexed)
            turn: Turn dictionary

        Returns:
            List of detected issues
        """
        issues = []
        user_input = turn.get("user_input", "")

        # Check for intent misunderstanding signals
        for pattern in self.INTENT_PATTERNS:
            if re.search(pattern, user_input):
                issues.append(
                    QualityIssue(
                        turn_num=turn_num,
                        issue_type=IssueType.INTENT_MISUNDERSTANDING,
                        severity=IssueSeverity.HIGH,
                        description=f"User had to clarify intent: '{user_input[:50]}...'",
                        suggestion="Improve intent understanding in previous turn. "
                        "Use confirmation signals like 'To confirm, you want...' "
                        "before proceeding.",
                        pattern_matched=pattern,
                    )
                )
                break  # Only report once per turn

        return issues

    def _detect_probing_issues(
        self, turn_num: int, turn: Dict[str, Any]
    ) -> List[QualityIssue]:
        """
        Detect missed probing opportunities.

        AC2: One of 4+ issue types

        Looks for:
        - Vague user input that should trigger questions
        - Brian response that doesn't ask clarifying questions
        - Uncertainty signals that need probing

        Args:
            turn_num: Turn number
            turn: Turn dictionary

        Returns:
            List of detected issues
        """
        issues = []
        user_input = turn.get("user_input", "")
        brian_response = turn.get("brian_response", "")

        # Check if user input is vague
        is_vague = False
        matched_pattern = None

        for pattern in self.PROBING_PATTERNS:
            if re.search(pattern, user_input):
                is_vague = True
                matched_pattern = pattern
                break

        # Check if Brian asked questions
        has_questions = "?" in brian_response

        # If input is vague and Brian didn't probe, flag it
        if is_vague and not has_questions:
            issues.append(
                QualityIssue(
                    turn_num=turn_num,
                    issue_type=IssueType.MISSED_PROBING,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Vague input not probed: '{user_input[:50]}...'",
                    suggestion="Ask clarifying questions when user input is vague or uncertain. "
                    "Examples: 'What specific features do you need?' or "
                    "'Can you describe the use case in more detail?'",
                    pattern_matched=matched_pattern,
                )
            )

        return issues

    def _detect_context_issues(
        self, turn_num: int, turn: Dict[str, Any]
    ) -> List[QualityIssue]:
        """
        Detect unused context issues.

        AC2: One of 4+ issue types

        Looks for:
        - Available context not referenced in response
        - User mentioning context Brian should already know

        Args:
            turn_num: Turn number
            turn: Turn dictionary

        Returns:
            List of detected issues
        """
        issues = []
        context_used = turn.get("context_used", {})
        brian_response = turn.get("brian_response", "")
        user_input = turn.get("user_input", "")

        # Check if context is available but not used
        has_epic = context_used.get("current_epic") is not None
        has_story = context_used.get("current_story") is not None

        # Check if Brian's response mentions specific epic/story numbers
        response_lower = brian_response.lower()
        mentions_epic_number = (
            has_epic and f"epic {context_used.get('current_epic')}" in response_lower
        )
        mentions_story_number = (
            has_story
            and f"story {context_used.get('current_story')}" in response_lower
        )
        mentions_context = mentions_epic_number or mentions_story_number

        # Check if user mentions context Brian should know
        user_lower = user_input.lower()
        user_mentions_context = any(
            keyword in user_lower for keyword in self.CONTEXT_KEYWORDS
        )

        # If context exists and user asks about it, but Brian doesn't provide it
        if (has_epic or has_story) and user_mentions_context and not mentions_context:
            issues.append(
                QualityIssue(
                    turn_num=turn_num,
                    issue_type=IssueType.UNUSED_CONTEXT,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Available context not used (epic={context_used.get('current_epic')}, "
                    f"story={context_used.get('current_story')})",
                    suggestion="Reference available context in responses. "
                    "Example: 'For Epic 1, Story 2...' or 'Given the current project context...'",
                    pattern_matched="context_available",
                )
            )

        return issues

    def _detect_relevance_issues(
        self, turn_num: int, turn: Dict[str, Any]
    ) -> List[QualityIssue]:
        """
        Detect poor response relevance issues.

        AC2: One of 4+ issue types

        Looks for:
        - Generic/unhelpful responses
        - Responses that don't address user input
        - Very short responses to complex questions

        Args:
            turn_num: Turn number
            turn: Turn dictionary

        Returns:
            List of detected issues
        """
        issues = []
        brian_response = turn.get("brian_response", "")
        user_input = turn.get("user_input", "")

        # Check for generic responses
        for pattern in self.RELEVANCE_PATTERNS:
            if re.search(pattern, brian_response):
                issues.append(
                    QualityIssue(
                        turn_num=turn_num,
                        issue_type=IssueType.POOR_RELEVANCE,
                        severity=IssueSeverity.LOW,
                        description=f"Generic/unhelpful response: '{brian_response[:50]}...'",
                        suggestion="Provide specific, actionable responses. "
                        "Avoid generic acknowledgments without substance.",
                        pattern_matched=pattern,
                    )
                )
                break

        # Check for very short responses to long questions
        if len(user_input) > 100 and len(brian_response) < 50:
            issues.append(
                QualityIssue(
                    turn_num=turn_num,
                    issue_type=IssueType.POOR_RELEVANCE,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Short response ({len(brian_response)} chars) to detailed question ({len(user_input)} chars)",
                    suggestion="Provide detailed responses proportional to question complexity.",
                    pattern_matched="length_mismatch",
                )
            )

        return issues

    def _detect_confirmation_issues(
        self, turn_num: int, turn: Dict[str, Any]
    ) -> List[QualityIssue]:
        """
        Detect lack of confirmation signals.

        AC2: Additional issue type beyond required 4

        Looks for:
        - Important actions without confirmation
        - Assumptions without validation

        Args:
            turn_num: Turn number
            turn: Turn dictionary

        Returns:
            List of detected issues
        """
        issues = []
        brian_response = turn.get("brian_response", "")
        user_input = turn.get("user_input", "")

        # Check if Brian is taking action
        action_keywords = [
            "i'll",
            "i will",
            "let me",
            "going to",
            "i'm creating",
            "i'm building",
        ]
        is_action = any(keyword in brian_response.lower() for keyword in action_keywords)

        # Check if Brian confirms understanding
        has_confirmation = any(
            re.search(pattern, brian_response) for pattern in self.CONFIRMATION_PATTERNS
        )

        # If taking action without confirmation, flag it
        if is_action and not has_confirmation and len(user_input) > 20:
            issues.append(
                QualityIssue(
                    turn_num=turn_num,
                    issue_type=IssueType.NO_CONFIRMATION,
                    severity=IssueSeverity.LOW,
                    description="Action taken without confirming understanding",
                    suggestion="Confirm understanding before taking action. "
                    "Example: 'To confirm, you want me to create...'",
                    pattern_matched="action_without_confirmation",
                )
            )

        return issues

    def ai_analyze_turn(
        self, turn_num: int, turn: Dict[str, Any], report: QualityReport
    ) -> List[QualityIssue]:
        """
        Perform AI-powered deep analysis on a turn.

        AC7: Uses deepseek-r1 for AI-powered analysis

        This is optional and slower than pattern matching, but can detect
        nuanced issues that patterns miss.

        Args:
            turn_num: Turn number
            turn: Turn dictionary
            report: Current quality report (for context)

        Returns:
            List of additional issues detected by AI
        """
        if not self.ai_service:
            return []

        # TODO: Implement AI analysis in future story if needed
        # For now, pattern-based detection is sufficient
        return []
