"""
Legal Team Checklist Plugin for GAO-Dev.

Provides legal and compliance checklists for contract review,
regulatory compliance, data privacy, and legal document review.
"""

from pathlib import Path
from typing import Dict, List

import structlog

from gao_dev.plugins.checklist_plugin import ChecklistPlugin

logger = structlog.get_logger(__name__)


class LegalChecklistPlugin(ChecklistPlugin):
    """
    Legal team checklist plugin.

    Provides checklists for:
    - Contract review and approval
    - Regulatory compliance verification
    - Legal document review
    - Data privacy and GDPR compliance
    """

    def get_checklist_directories(self) -> List[Path]:
        """
        Return legal checklist directories.

        Returns:
            List containing the legal checklists directory
        """
        base = Path(__file__).parent
        return [base / "checklists" / "legal"]

    def get_checklist_metadata(self) -> Dict:
        """
        Return plugin metadata.

        Returns:
            Dictionary with plugin information
        """
        return {
            "name": "legal-team",
            "version": "1.0.0",
            "author": "GAO Legal Team",
            "description": "Legal and compliance checklists for contract review, GDPR, etc.",
            "priority": 100,  # Override core if needed
            "checklist_prefix": "legal-",
            "dependencies": [],
        }

    def validate_checklist(self, checklist: Dict) -> bool:
        """
        Optional: Custom validation for legal checklists.

        Ensures legal checklists have required compliance metadata.

        Args:
            checklist: Parsed checklist dictionary

        Returns:
            True if valid, False otherwise
        """
        # Check for compliance tags in metadata
        checklist_data = checklist.get("checklist", {})
        metadata = checklist_data.get("metadata", {})
        compliance_tags = metadata.get("compliance_tags", [])

        if not compliance_tags:
            logger.warning(
                "legal_checklist_missing_compliance_tags",
                checklist_name=checklist_data.get("name"),
            )
            # Warning but not a failure
            return True

        return True

    def on_checklist_loaded(self, checklist_name: str, checklist: Dict):
        """Hook called after checklist loaded from this plugin."""
        logger.info(
            "legal_checklist_loaded",
            checklist_name=checklist_name,
            plugin="legal-team",
        )

    def on_checklist_executed(
        self, checklist_name: str, execution_id: int, status: str
    ):
        """
        Log legal checklist executions for audit.

        Legal checklist executions may require audit trail for compliance.
        """
        logger.info(
            "legal_checklist_executed",
            checklist=checklist_name,
            execution_id=execution_id,
            status=status,
        )

        if status == "fail":
            # Could send notification to legal team
            logger.warning(
                "legal_checklist_failed",
                checklist=checklist_name,
                execution_id=execution_id,
                action="notify_legal_team",
            )

    def on_checklist_failed(
        self, checklist_name: str, execution_id: int, errors: List[str]
    ):
        """Hook called when checklist execution fails."""
        logger.error(
            "legal_checklist_execution_failed",
            checklist=checklist_name,
            execution_id=execution_id,
            errors=errors,
            action="escalate_to_legal",
        )
