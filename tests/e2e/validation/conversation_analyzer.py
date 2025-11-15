"""Conversation quality analyzer for POC validation.

This is a prototype implementation that uses AI (Claude or deepseek-r1)
to analyze conversation quality and detect issues.

Epic: 37 - UX Quality Analysis
Story: 37.0 - deepseek-r1 Quality Validation POC
"""

import json
import structlog
from typing import Dict, Any, List
from pathlib import Path

from .models import QualityReport, QualityIssue, IssueType, IssueSeverity

logger = structlog.get_logger()


class ConversationAnalyzer:
    """
    Analyzes conversation quality using AI.

    This is a prototype for POC validation. Uses AIAnalysisService
    to analyze conversations and generate quality reports.
    """

    def __init__(self, ai_service: Any):
        """
        Initialize analyzer.

        Args:
            ai_service: AIAnalysisService instance (Claude or deepseek-r1)
        """
        self.ai_service = ai_service
        self.logger = logger.bind(component="conversation_analyzer")

    async def analyze_conversation(
        self, conversation: Dict[str, Any]
    ) -> QualityReport:
        """
        Analyze a conversation for quality.

        Args:
            conversation: Conversation dict with transcript

        Returns:
            QualityReport with score and detected issues
        """
        conv_id = conversation["id"]
        conv_name = conversation["name"]
        transcript = conversation["transcript"]

        self.logger.info(
            "analyzing_conversation",
            conversation_id=conv_id,
            conversation_name=conv_name,
            turns=len(transcript)
        )

        # Build analysis prompt
        prompt = self._build_analysis_prompt(conversation)

        # Call AI for analysis
        try:
            result = await self.ai_service.analyze(
                prompt=prompt,
                response_format="json",
                max_tokens=2048,
                temperature=0.3  # Low temperature for consistent analysis
            )

            # Parse response
            analysis = json.loads(result.response)

            # Extract quality data
            quality_score = float(analysis.get("quality_score", 50))
            issues_data = analysis.get("issues", [])
            recommendations = analysis.get("recommendations", [])
            strengths = analysis.get("strengths", [])

            # Convert issues to QualityIssue objects
            issues = []
            for issue_data in issues_data:
                try:
                    issue = QualityIssue(
                        turn_num=int(issue_data.get("turn_num", 0)),
                        issue_type=IssueType(issue_data.get("issue_type", "poor_relevance")),
                        severity=IssueSeverity(issue_data.get("severity", "medium")),
                        description=issue_data.get("description", ""),
                        suggestion=issue_data.get("suggestion", "")
                    )
                    issues.append(issue)
                except (ValueError, KeyError) as e:
                    self.logger.warning(
                        "failed_to_parse_issue",
                        error=str(e),
                        issue_data=issue_data
                    )

            report = QualityReport(
                conversation_id=conv_id,
                conversation_name=conv_name,
                quality_score=quality_score,
                issues=issues,
                recommendations=recommendations,
                strengths=strengths,
                model_used=result.model_used
            )

            self.logger.info(
                "analysis_completed",
                conversation_id=conv_id,
                quality_score=quality_score,
                issues_count=len(issues),
                model=result.model_used
            )

            return report

        except json.JSONDecodeError as e:
            self.logger.error(
                "failed_to_parse_analysis_json",
                conversation_id=conv_id,
                error=str(e)
            )
            # Return default low-quality report on parse failure
            return QualityReport(
                conversation_id=conv_id,
                conversation_name=conv_name,
                quality_score=0,
                issues=[],
                recommendations=["Failed to analyze conversation - JSON parse error"],
                model_used="unknown"
            )

        except Exception as e:
            self.logger.error(
                "analysis_failed",
                conversation_id=conv_id,
                error=str(e),
                exc_info=True
            )
            raise

    def _build_analysis_prompt(self, conversation: Dict[str, Any]) -> str:
        """
        Build prompt for conversation analysis.

        Args:
            conversation: Conversation dict with transcript

        Returns:
            Analysis prompt for AI
        """
        conv_name = conversation["name"]
        description = conversation.get("description", "")
        transcript = conversation["transcript"]

        # Format transcript
        transcript_text = []
        for i, turn in enumerate(transcript, 1):
            transcript_text.append(f"Turn {i}:")
            transcript_text.append(f"User: {turn['user']}")
            transcript_text.append(f"Brian: {turn['brian']}")
            transcript_text.append("")

        transcript_str = "\n".join(transcript_text)

        prompt = f"""Analyze this conversation between a user and Brian (AI development coordinator) for quality.

**Conversation**: {conv_name}
**Description**: {description}

**Transcript**:
{transcript_str}

**Analysis Task**:
Evaluate the conversation quality on these dimensions:

1. **Intent Understanding**: Does Brian correctly understand user goals?
2. **Probing Quality**: Does Brian ask appropriate clarifying questions for vague input?
3. **Context Usage**: Does Brian reference and use available context effectively?
4. **Response Relevance**: Are Brian's responses helpful and actionable?
5. **Confirmation**: Does Brian confirm understanding before proceeding?

**Scoring Criteria** (0-100):
- 90-100: Excellent conversation quality, all dimensions strong
- 75-89: Good quality, minor improvements possible
- 60-74: Acceptable quality, some issues present
- 40-59: Poor quality, significant issues
- 0-39: Very poor quality, major issues

**Issue Types**:
- intent_misunderstanding: Brian misunderstands user intent
- missed_probing: Brian fails to probe for clarification on vague input
- unused_context: Brian has context but doesn't use it
- poor_relevance: Response not relevant or helpful
- no_confirmation: Brian doesn't confirm understanding
- abrupt_response: Brian is too terse or doesn't explain

**Response Format** (JSON):
{{
    "quality_score": <0-100>,
    "issues": [
        {{
            "turn_num": <1-N>,
            "issue_type": "<issue_type>",
            "severity": "<critical|high|medium|low>",
            "description": "<what's wrong>",
            "suggestion": "<how to fix>"
        }}
    ],
    "recommendations": [
        "<actionable recommendation 1>",
        "<actionable recommendation 2>"
    ],
    "strengths": [
        "<what Brian did well>",
        "<another strength>"
    ]
}}

Provide your analysis as JSON only, no additional text."""

        return prompt
