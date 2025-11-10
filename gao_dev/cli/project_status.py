"""Project detection and status reporting for interactive chat."""

from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import structlog

from gao_dev.core.state.state_tracker import StateTracker
from gao_dev.core.git_manager import GitManager

logger = structlog.get_logger()


@dataclass
class ProjectStatus:
    """
    Project status information.

    Attributes:
        exists: Whether .gao-dev/ project exists
        project_name: Name of project
        project_root: Path to project root
        epic_count: Number of epics
        story_count: Number of stories
        recent_commits: List of recent commit messages
        current_epic: Current epic in progress (if any)
        is_greenfield: True if no .gao-dev/ found
    """

    exists: bool
    project_name: Optional[str] = None
    project_root: Optional[Path] = None
    epic_count: int = 0
    story_count: int = 0
    recent_commits: List[str] = field(default_factory=list)
    current_epic: Optional[str] = None
    is_greenfield: bool = False


class ProjectStatusReporter:
    """
    Detect and report GAO-Dev project status.

    Auto-detects .gao-dev/ directory, queries project state,
    and formats status summary for display in chat.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize reporter.

        Args:
            project_root: Optional explicit project root.
                         If None, auto-detects from current directory.
        """
        self.logger = logger.bind(component="project_status")
        self.project_root = project_root or self._auto_detect()

    def _auto_detect(self) -> Optional[Path]:
        """
        Auto-detect project root by searching for .gao-dev/

        Searches current directory and up to 5 parent directories.

        Returns:
            Path to project root if found, None otherwise
        """
        self.logger.info("auto_detecting_project")

        current = Path.cwd()
        max_levels = 5

        for _ in range(max_levels):
            gao_dev_dir = current / ".gao-dev"
            if gao_dev_dir.exists() and gao_dev_dir.is_dir():
                self.logger.info("project_detected", path=str(current))
                return current

            # Move to parent
            parent = current.parent
            if parent == current:
                # Reached filesystem root
                break
            current = parent

        self.logger.info("no_project_detected")
        return None

    def get_status(self) -> ProjectStatus:
        """
        Get comprehensive project status.

        Returns:
            ProjectStatus with all available information
        """
        if not self.project_root:
            return ProjectStatus(exists=False, is_greenfield=True)

        self.logger.info("getting_project_status", project_root=str(self.project_root))

        try:
            # Load state from StateTracker
            db_path = self.project_root / ".gao-dev" / "documents.db"

            # Check if database exists
            if not db_path.exists():
                self.logger.warning("database_not_found", path=str(db_path))
                return ProjectStatus(
                    exists=True,
                    project_name=self._get_project_name(),
                    project_root=self.project_root,
                    is_greenfield=True
                )

            state_tracker = StateTracker(db_path)

            # Get epics and stories
            epics = self._get_all_epics(state_tracker)
            stories = self._get_all_stories(state_tracker)

            # Get recent commits
            git_manager = GitManager(self.project_root)
            recent_commits = self._get_recent_commits(git_manager, count=5)

            # Determine current epic
            current_epic = self._determine_current_epic(epics)

            return ProjectStatus(
                exists=True,
                project_name=self._get_project_name(),
                project_root=self.project_root,
                epic_count=len(epics),
                story_count=len(stories),
                recent_commits=recent_commits,
                current_epic=current_epic,
                is_greenfield=False,
            )

        except Exception as e:
            self.logger.exception("failed_to_get_status", error=str(e))
            # Return minimal status on error
            return ProjectStatus(
                exists=True,
                project_name=self._get_project_name(),
                project_root=self.project_root,
            )

    def _get_project_name(self) -> str:
        """Get project name from directory."""
        if not self.project_root:
            return "Unknown"
        return self.project_root.name

    def _get_all_epics(self, state_tracker: StateTracker) -> List[Dict[str, Any]]:
        """
        Get all epics from state tracker.

        Args:
            state_tracker: StateTracker instance

        Returns:
            List of epic dictionaries
        """
        try:
            # Get active epics
            active_epics = state_tracker.get_active_epics()

            # Convert Epic objects to dicts
            epics = []
            for epic in active_epics:
                epics.append({
                    "epic_num": epic.epic_num,
                    "title": epic.title,
                    "status": epic.status,
                    "created_at": epic.created_at,
                })

            return epics
        except Exception as e:
            self.logger.warning("failed_to_get_epics", error=str(e))
            return []

    def _get_all_stories(self, state_tracker: StateTracker) -> List[Dict[str, Any]]:
        """
        Get all stories from state tracker.

        Args:
            state_tracker: StateTracker instance

        Returns:
            List of story dictionaries
        """
        try:
            # Get stories by different statuses and combine
            all_stories = []
            statuses = ["pending", "in_progress", "done", "blocked", "cancelled"]

            seen_keys = set()
            for status in statuses:
                stories = state_tracker.get_stories_by_status(status)
                for story in stories:
                    key = (story.epic, story.story_num)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_stories.append({
                            "epic_num": story.epic,
                            "story_num": story.story_num,
                            "title": story.title,
                            "status": story.status,
                        })

            return all_stories
        except Exception as e:
            self.logger.warning("failed_to_get_stories", error=str(e))
            return []

    def _get_recent_commits(self, git_manager: GitManager, count: int = 5) -> List[str]:
        """
        Get recent commit messages.

        Args:
            git_manager: GitManager instance
            count: Number of commits to retrieve

        Returns:
            List of commit messages (most recent first)
        """
        try:
            # Get commits using git log
            # We'll use a simple approach: get commits from HEAD~count to HEAD
            commits = []

            for i in range(count):
                try:
                    commit_info = git_manager.get_commit_info(f"HEAD~{i}")
                    # Get first line of commit message
                    message = commit_info["message"].split("\n")[0]
                    commits.append(message)
                except Exception:
                    # No more commits available
                    break

            return commits
        except Exception as e:
            self.logger.warning("failed_to_get_commits", error=str(e))
            return []

    def _determine_current_epic(self, epics: List[Dict[str, Any]]) -> Optional[str]:
        """
        Determine current epic in progress.

        Looks for epics with status "active" or most recent epic.

        Args:
            epics: List of epic records

        Returns:
            Epic identifier (e.g., "Epic 30: Interactive Brian Chat") or None
        """
        if not epics:
            return None

        # Look for active epic
        for epic in epics:
            if epic.get("status") == "active":
                return f"Epic {epic['epic_num']}: {epic['title']}"

        # Return most recent epic (by creation date)
        try:
            latest = max(epics, key=lambda e: e.get("created_at", ""))
            return f"Epic {latest['epic_num']}: {latest['title']}"
        except Exception:
            # Fallback to first epic
            if epics:
                return f"Epic {epics[0]['epic_num']}: {epics[0]['title']}"
            return None

    def format_status(self, status: ProjectStatus) -> str:
        """
        Format status for display in chat greeting.

        Args:
            status: ProjectStatus to format

        Returns:
            Formatted status message (markdown)
        """
        if status.is_greenfield:
            return """
No GAO-Dev project detected in this directory.

Would you like me to initialize a new project?
Type 'init' to get started, or type your request and I'll help!
            """.strip()

        if not status.exists:
            return "Unable to load project status."

        # Format commit list
        commit_section = ""
        if status.recent_commits:
            commits_formatted = "\n".join(f"  - {commit}" for commit in status.recent_commits)
            commit_section = f"\n\n**Recent Activity**:\n{commits_formatted}"

        # Format current epic
        epic_section = ""
        if status.current_epic:
            epic_section = f"\n**Current Epic**: {status.current_epic}"

        return f"""
**Project**: {status.project_name}
**Epics**: {status.epic_count} | **Stories**: {status.story_count}{epic_section}{commit_section}
        """.strip()
