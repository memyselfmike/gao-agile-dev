"""State management for stories and workflows."""

from pathlib import Path
from typing import Optional, Dict, Any
import re

from .config_loader import ConfigLoader


class StateManager:
    """Manage story and workflow state."""

    def __init__(self, config_loader: ConfigLoader):
        """
        Initialize state manager.

        Args:
            config_loader: Configuration loader instance
        """
        self.config_loader = config_loader
        self.project_root = config_loader.project_root

    def get_story_status(self, epic: int, story: int) -> Optional[str]:
        """
        Get story status.

        Args:
            epic: Epic number
            story: Story number

        Returns:
            Story status string or None if not found
        """
        story_file = self._get_story_path(epic, story)
        if not story_file.exists():
            return None

        content = story_file.read_text(encoding="utf-8")

        # Parse status from frontmatter
        status_match = re.search(r"\*\*Status:\*\*\s+([A-Za-z\s]+)", content)
        if status_match:
            return status_match.group(1).strip()

        return None

    def set_story_status(self, epic: int, story: int, status: str) -> bool:
        """
        Set story status.

        Args:
            epic: Epic number
            story: Story number
            status: New status

        Returns:
            True if successful
        """
        story_file = self._get_story_path(epic, story)
        if not story_file.exists():
            return False

        content = story_file.read_text(encoding="utf-8")

        # Update status in frontmatter
        updated_content = re.sub(
            r"(\*\*Status:\*\*\s+)[A-Za-z\s]+",
            f"\\1{status}",
            content
        )

        story_file.write_text(updated_content, encoding="utf-8")
        return True

    def _get_story_path(self, epic: int, story: int) -> Path:
        """Get path to story file."""
        story_location = self.config_loader.get_story_location()
        return story_location / f"epic-{epic}" / f"story-{epic}.{story}.md"

    def ensure_story_directory(self, epic: int) -> Path:
        """
        Ensure story directory exists.

        Args:
            epic: Epic number

        Returns:
            Path to epic directory
        """
        story_location = self.config_loader.get_story_location()
        epic_dir = story_location / f"epic-{epic}"
        epic_dir.mkdir(parents=True, exist_ok=True)
        return epic_dir

    def get_sprint_status(self) -> Dict[str, Any]:
        """
        Get overall sprint status.

        Returns:
            Sprint status dictionary
        """
        # Simplified version for POC
        story_location = self.config_loader.get_story_location()

        if not story_location.exists():
            return {"stories": [], "total": 0}

        stories = []
        for epic_dir in story_location.iterdir():
            if epic_dir.is_dir() and epic_dir.name.startswith("epic-"):
                epic_num = int(epic_dir.name.split("-")[1])

                for story_file in epic_dir.glob("story-*.md"):
                    # Parse story number from filename
                    match = re.match(r"story-(\d+)\.(\d+)\.md", story_file.name)
                    if match:
                        story_num = int(match.group(2))
                        status = self.get_story_status(epic_num, story_num)
                        stories.append({
                            "epic": epic_num,
                            "story": story_num,
                            "status": status
                        })

        return {
            "stories": stories,
            "total": len(stories)
        }
