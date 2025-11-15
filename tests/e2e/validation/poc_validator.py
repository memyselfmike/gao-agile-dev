"""POC validator for comparing Claude and deepseek-r1 quality analysis.

This module orchestrates the validation process:
1. Analyze conversations with Claude (ground truth)
2. Analyze same conversations with deepseek-r1
3. Calculate agreement metrics
4. Generate validation report

Epic: 37 - UX Quality Analysis
Story: 37.0 - deepseek-r1 Quality Validation POC
"""

import asyncio
import structlog
from pathlib import Path
from typing import List, Optional

from gao_dev.core.services.process_executor import ProcessExecutor
from gao_dev.core.services.ai_analysis_service import AIAnalysisService

from .conversation_analyzer import ConversationAnalyzer
from .models import (
    QualityReport,
    ComparisonResult,
    ValidationResult,
    IssueType
)
from .sample_conversations import SAMPLE_CONVERSATIONS

logger = structlog.get_logger()


class POCValidator:
    """
    Validates deepseek-r1 quality against Claude baseline.

    Orchestrates the validation process and generates comparison reports.
    """

    def __init__(self, project_root: Path):
        """
        Initialize validator.

        Args:
            project_root: Root directory of GAO-Dev project
        """
        self.project_root = project_root
        self.logger = logger.bind(component="poc_validator")

    async def analyze_with_claude(
        self, conversations: List[dict]
    ) -> List[QualityReport]:
        """
        Analyze conversations using Claude API (ground truth).

        Args:
            conversations: List of conversation dicts

        Returns:
            List of QualityReport from Claude
        """
        self.logger.info(
            "analyzing_with_claude",
            conversation_count=len(conversations)
        )

        # Create ProcessExecutor with Claude Code provider
        executor = ProcessExecutor(
            project_root=self.project_root,
            provider_name="claude-code",
            provider_config={}
        )

        # Create AI service and analyzer
        ai_service = AIAnalysisService(executor=executor)
        analyzer = ConversationAnalyzer(ai_service=ai_service)

        # Analyze all conversations
        reports = []
        for conv in conversations:
            try:
                report = await analyzer.analyze_conversation(conv)
                reports.append(report)
                self.logger.info(
                    "claude_analysis_completed",
                    conversation_id=conv["id"],
                    quality_score=report.quality_score
                )
            except Exception as e:
                self.logger.error(
                    "claude_analysis_failed",
                    conversation_id=conv["id"],
                    error=str(e),
                    exc_info=True
                )
                raise

        return reports

    async def analyze_with_deepseek(
        self, conversations: List[dict]
    ) -> List[QualityReport]:
        """
        Analyze conversations using deepseek-r1 (local model).

        Args:
            conversations: List of conversation dicts

        Returns:
            List of QualityReport from deepseek-r1
        """
        self.logger.info(
            "analyzing_with_deepseek",
            conversation_count=len(conversations)
        )

        # Create ProcessExecutor with OpenCode + ollama/deepseek-r1
        executor = ProcessExecutor(
            project_root=self.project_root,
            provider_name="opencode",
            provider_config={
                "ai_provider": "ollama",
                "use_local": True,
                "model": "deepseek-r1"
            }
        )

        # Create AI service and analyzer
        ai_service = AIAnalysisService(
            executor=executor,
            default_model="deepseek-r1"
        )
        analyzer = ConversationAnalyzer(ai_service=ai_service)

        # Analyze all conversations
        reports = []
        for conv in conversations:
            try:
                report = await analyzer.analyze_conversation(conv)
                reports.append(report)
                self.logger.info(
                    "deepseek_analysis_completed",
                    conversation_id=conv["id"],
                    quality_score=report.quality_score
                )
            except Exception as e:
                self.logger.error(
                    "deepseek_analysis_failed",
                    conversation_id=conv["id"],
                    error=str(e),
                    exc_info=True
                )
                raise

        return reports

    def calculate_agreement(
        self,
        claude_reports: List[QualityReport],
        deepseek_reports: List[QualityReport]
    ) -> ValidationResult:
        """
        Calculate agreement metrics between Claude and deepseek-r1.

        Args:
            claude_reports: Reports from Claude analysis
            deepseek_reports: Reports from deepseek-r1 analysis

        Returns:
            ValidationResult with agreement metrics
        """
        self.logger.info("calculating_agreement")

        if len(claude_reports) != len(deepseek_reports):
            raise ValueError(
                f"Report count mismatch: Claude={len(claude_reports)}, "
                f"deepseek={len(deepseek_reports)}"
            )

        # Compare each conversation
        comparisons = []
        score_agreements = 0
        issue_recalls = []

        for c_report, d_report in zip(claude_reports, deepseek_reports):
            if c_report.conversation_id != d_report.conversation_id:
                raise ValueError(
                    f"Conversation ID mismatch: {c_report.conversation_id} != "
                    f"{d_report.conversation_id}"
                )

            # Extract issue types
            c_issues = [issue.issue_type for issue in c_report.issues]
            d_issues = [issue.issue_type for issue in d_report.issues]

            # Create comparison
            comparison = ComparisonResult(
                conversation_id=c_report.conversation_id,
                conversation_name=c_report.conversation_name,
                claude_score=c_report.quality_score,
                deepseek_score=d_report.quality_score,
                score_difference=0,  # Will be calculated in __post_init__
                score_agreement=False,  # Will be calculated in __post_init__
                claude_issues=c_issues,
                deepseek_issues=d_issues
            )

            comparisons.append(comparison)

            # Count agreements
            if comparison.score_agreement:
                score_agreements += 1

            issue_recalls.append(comparison.issue_recall)

        # Calculate overall metrics
        score_agreement_pct = (score_agreements / len(comparisons)) * 100
        avg_issue_recall = sum(issue_recalls) / len(issue_recalls) if issue_recalls else 0

        result = ValidationResult(
            conversations_analyzed=len(comparisons),
            score_agreement_pct=score_agreement_pct,
            issue_detection_recall=avg_issue_recall,
            comparisons=comparisons,
            claude_reports=claude_reports,
            deepseek_reports=deepseek_reports
        )

        self.logger.info(
            "agreement_calculated",
            score_agreement_pct=score_agreement_pct,
            issue_detection_recall=avg_issue_recall,
            decision=result.decision
        )

        return result

    def generate_report(self, result: ValidationResult) -> str:
        """
        Generate validation report markdown.

        Args:
            result: ValidationResult with all metrics

        Returns:
            Markdown report string
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("deepseek-r1 QUALITY VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        stats = result.get_summary_stats()
        lines.append("## Summary")
        lines.append("")
        lines.append(f"**Conversations Analyzed**: {stats['total_conversations']}")
        lines.append(f"**Score Agreement**: {stats['score_agreement_pct']}%")
        lines.append(f"**Issue Detection Recall**: {stats['issue_detection_recall']}%")
        lines.append(f"**Average Claude Score**: {stats['avg_claude_score']}")
        lines.append(f"**Average deepseek-r1 Score**: {stats['avg_deepseek_score']}")
        lines.append("")

        # Decision
        lines.append("-" * 80)
        lines.append("## RECOMMENDATION")
        lines.append("-" * 80)
        lines.append("")
        lines.append(f"**STATUS**: {result.decision}")
        lines.append("")

        if result.decision == "PASS":
            lines.append("deepseek-r1 demonstrates sufficient quality for conversation analysis.")
            lines.append("")
            lines.append("**DECISION**: PROCEED with Stories 37.1-37.4 using deepseek-r1")
            lines.append("")
            lines.append("**Rationale**:")
            lines.append(f"- Score agreement ({stats['score_agreement_pct']}%) meets threshold (>80%)")
            lines.append(f"- Issue detection ({stats['issue_detection_recall']}%) meets threshold (>70%)")
            lines.append("- Cost savings: $40-200/month by using local model")
            lines.append("- No significant degradation in analysis quality detected")
        elif result.decision == "PARTIAL PASS":
            lines.append("deepseek-r1 shows acceptable but imperfect quality.")
            lines.append("")
            lines.append("**DECISION**: HYBRID APPROACH")
            lines.append("")
            lines.append("**Recommendation**:")
            lines.append("- Use Claude API for conversation analysis (Mode 2) - $5-10/month")
            lines.append("- Use deepseek-r1 for regression tests (Mode 3) - $0/month")
            lines.append("")
            lines.append("**Rationale**:")
            lines.append(f"- Score agreement ({stats['score_agreement_pct']}%) below ideal threshold")
            lines.append("- Quality matters more than cost for UX analysis")
            lines.append("- Regression tests can use local model (determinism > quality)")
        else:  # FAIL
            lines.append("deepseek-r1 quality insufficient for reliable analysis.")
            lines.append("")
            lines.append("**DECISION**: RECONSIDER FEATURE SCOPE")
            lines.append("")
            lines.append("**Options**:")
            lines.append("1. Use Claude API for all analysis (accept $10-50/month cost)")
            lines.append("2. Reduce Epic 37 scope (pattern-only detection, no AI analysis)")
            lines.append("3. Defer Epic 37 until better local models available")
            lines.append("")
            lines.append("**Rationale**:")
            lines.append(f"- Score agreement ({stats['score_agreement_pct']}%) too low for trust")
            lines.append("- Poor analysis worse than no analysis (misleading recommendations)")
            lines.append("- Cost savings not worth unreliable quality insights")

        lines.append("")

        # Detailed comparison
        lines.append("-" * 80)
        lines.append("## Detailed Comparison")
        lines.append("-" * 80)
        lines.append("")

        for comp in result.comparisons:
            lines.append(f"### Conversation {comp.conversation_id}: {comp.conversation_name}")
            lines.append("")
            lines.append(f"- **Claude Score**: {comp.claude_score}")
            lines.append(f"- **deepseek-r1 Score**: {comp.deepseek_score}")
            lines.append(f"- **Difference**: {comp.score_difference:.1f} points")
            lines.append(f"- **Agreement**: {'YES' if comp.score_agreement else 'NO'}")
            lines.append(f"- **Issue Recall**: {comp.issue_recall:.1f}%")
            lines.append("")

            if comp.claude_issues:
                lines.append(f"  **Claude Issues**: {', '.join(str(i.value) for i in comp.claude_issues)}")
            if comp.deepseek_issues:
                lines.append(f"  **deepseek Issues**: {', '.join(str(i.value) for i in comp.deepseek_issues)}")
            if comp.issue_overlap:
                lines.append(f"  **Overlap**: {', '.join(str(i.value) for i in comp.issue_overlap)}")

            lines.append("")

        lines.append("=" * 80)
        lines.append("")

        return "\n".join(lines)

    async def run_validation(
        self,
        conversations: Optional[List[dict]] = None
    ) -> ValidationResult:
        """
        Run complete validation process.

        Args:
            conversations: Optional list of conversations (defaults to SAMPLE_CONVERSATIONS)

        Returns:
            ValidationResult with all metrics and reports
        """
        if conversations is None:
            conversations = SAMPLE_CONVERSATIONS

        self.logger.info(
            "validation_started",
            conversation_count=len(conversations)
        )

        # Analyze with both models
        claude_reports = await self.analyze_with_claude(conversations)
        deepseek_reports = await self.analyze_with_deepseek(conversations)

        # Calculate agreement
        result = self.calculate_agreement(claude_reports, deepseek_reports)

        self.logger.info(
            "validation_completed",
            decision=result.decision,
            score_agreement=result.score_agreement_pct,
            issue_recall=result.issue_detection_recall
        )

        return result
