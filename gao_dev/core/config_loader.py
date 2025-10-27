"""Configuration loader with defaults and user overrides."""

from pathlib import Path
from typing import Any, Optional
import yaml


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
