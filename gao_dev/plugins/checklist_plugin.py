"""Base plugin class for checklist plugins."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from gao_dev.plugins.base_plugin import BasePlugin


class ChecklistPlugin(BasePlugin, ABC):
    """
    Base class for checklist plugins.

    Checklist plugins provide domain-specific checklists that extend
    or override core checklists.

    Example:
        class LegalTeamPlugin(ChecklistPlugin):
            def get_checklist_directories(self) -> List[Path]:
                return [Path(__file__).parent / "checklists"]

            def get_checklist_metadata(self) -> Dict:
                return {
                    "name": "legal-team",
                    "version": "1.0.0",
                    "author": "Legal Team",
                    "description": "Legal compliance checklists",
                    "priority": 100  # Higher priority overrides lower
                }
    """

    @abstractmethod
    def get_checklist_directories(self) -> List[Path]:
        """
        Return list of directories containing checklist YAML files.

        Returns:
            List of Path objects to directories with checklists

        Example:
            return [
                Path(__file__).parent / "checklists" / "legal",
                Path(__file__).parent / "checklists" / "compliance"
            ]
        """
        pass

    @abstractmethod
    def get_checklist_metadata(self) -> Dict:
        """
        Return metadata about this plugin.

        Required fields:
            - name: Plugin name (unique identifier)
            - version: Semantic version (e.g., "1.0.0")
            - author: Plugin author

        Optional fields:
            - description: Plugin description
            - dependencies: List of plugin names this depends on
            - priority: Override priority (default: 0, higher wins)
            - checklist_prefix: Prefix for all checklists (e.g., "legal-")

        Returns:
            Dictionary with metadata
        """
        pass

    def validate_checklist(self, checklist: Dict) -> bool:
        """
        Optional: Custom validation for plugin checklists.

        Override to add domain-specific validation beyond schema.

        Args:
            checklist: Parsed checklist dictionary

        Returns:
            True if valid, False otherwise
        """
        return True

    def on_checklist_loaded(self, checklist_name: str, checklist: Dict):
        """Hook called after checklist loaded from this plugin."""
        pass

    def on_checklist_executed(
        self, checklist_name: str, execution_id: int, status: str
    ):
        """Hook called after checklist execution completes."""
        pass

    def on_checklist_failed(
        self, checklist_name: str, execution_id: int, errors: List[str]
    ):
        """Hook called when checklist execution fails."""
        pass
