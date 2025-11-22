"""Configuration loader with defaults and user overrides."""

from pathlib import Path
from typing import Any, Dict
import yaml
import structlog

logger = structlog.get_logger(__name__)


class ConfigLoader:
    """Load and manage GAO-Dev configuration."""

    def __init__(self, project_root: Path):
        """
        Initialize config loader.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root

        # Load embedded defaults
        defaults_path = Path(__file__).parent.parent / "config" / "defaults.yaml"
        with open(defaults_path, "r", encoding="utf-8") as f:
            self.defaults = yaml.safe_load(f) or {}

        # Load user config if it exists
        self.user_config = {}
        user_config_path = project_root / "gao-dev.yaml"
        if user_config_path.exists():
            with open(user_config_path, "r", encoding="utf-8") as f:
                self.user_config = yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        # Check user config first (highest priority)
        if key in self.user_config:
            return self.user_config[key]

        # Fall back to embedded defaults
        if key in self.defaults:
            return self.defaults[key]

        # Finally, use provided default
        return default

    def get_workflows_path(self) -> Path:
        """Get path to embedded workflows."""
        return Path(__file__).parent.parent / "workflows"

    def get_bmad_workflows_path(self) -> Path:
        """
        Get path to BMAD workflows (Story 7.2.6).

        Returns path to bmad/bmm/workflows where the complete catalog
        of 34+ workflows is installed.
        """
        return self.project_root / "bmad" / "bmm" / "workflows"

    def get_agents_path(self) -> Path:
        """Get path to embedded agents."""
        return Path(__file__).parent.parent / "agents"

    def get_checklists_path(self) -> Path:
        """Get path to embedded checklists."""
        return Path(__file__).parent.parent / "checklists"

    def get_output_folder(self) -> Path:
        """Get output folder path."""
        folder = self.get("output_folder", "docs")
        return self.project_root / folder

    def get_story_location(self) -> Path:
        """Get story location path."""
        location = self.get("dev_story_location", "docs/stories")
        return self.project_root / location

    def get_prd_location(self) -> Path:
        """Get PRD file path."""
        location = self.get("prd_location", "docs/PRD.md")
        return self.project_root / location

    def get_architecture_location(self) -> Path:
        """Get architecture file path."""
        location = self.get("architecture_location", "docs/architecture.md")
        return self.project_root / location

    def get_epics_location(self) -> Path:
        """Get epics file path."""
        location = self.get("epics_location", "docs/epics.md")
        return self.project_root / location

    def is_git_auto_commit_enabled(self) -> bool:
        """Check if git auto-commit is enabled."""
        return self.get("git_auto_commit", True)

    def get_git_commit_footer(self) -> str:
        """Get git commit footer."""
        default_footer = "\n\n🤖 Generated with GAO-Dev\nCo-Authored-By: Claude <noreply@anthropic.com>"
        return self.get("git_commit_footer", default_footer)

    def get_claude_model(self) -> str:
        """Get Claude model to use."""
        return self.get("claude_model", "claude-sonnet-4")

    def to_dict(self) -> dict:
        """Export configuration as dictionary."""
        # Merge defaults and user config
        config = self.defaults.copy()
        config.update(self.user_config)
        return config

    def get_workflow_defaults(self) -> Dict[str, str]:
        """
        Get default values for workflow variables.

        Returns dict mapping variable names to default values (all strings).
        Loads from workflow_defaults section in defaults.yaml and user config.

        Priority order:
        1. User config workflow_defaults (highest)
        2. Embedded defaults.yaml workflow_defaults

        Returns:
            Dict mapping variable names to default values
        """
        try:
            if not hasattr(self, '_workflow_defaults'):
                # Load embedded defaults first
                embedded_defaults = self.defaults.get('workflow_defaults', {})

                # Load user config overrides
                user_defaults = self.user_config.get('workflow_defaults', {})

                # Merge with user config taking priority
                merged_defaults = embedded_defaults.copy()
                merged_defaults.update(user_defaults)

                # Validate all defaults are strings (path values)
                validated_defaults = {}
                for key, value in merged_defaults.items():
                    if not isinstance(value, str):
                        logger.warning(
                            "workflow_default_invalid_type",
                            variable=key,
                            value_type=type(value).__name__,
                            message="Workflow default must be string - skipping"
                        )
                        continue
                    validated_defaults[key] = value

                self._workflow_defaults = validated_defaults

                logger.debug(
                    "workflow_defaults_loaded",
                    defaults_count=len(self._workflow_defaults),
                    defaults=list(self._workflow_defaults.keys())
                )

            return self._workflow_defaults.copy()

        except Exception as e:
            logger.error(
                "workflow_defaults_load_error",
                error=str(e),
                error_type=type(e).__name__,
                message="Failed to load workflow defaults - using empty dict"
            )
            return {}
