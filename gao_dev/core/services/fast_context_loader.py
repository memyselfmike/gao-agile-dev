"""Fast Context Loader - <5ms context queries for agents.

This service provides ultra-fast context loading using indexed database queries.
Optimized for agent operations requiring rapid access to epic/story state.

Epic: 25 - Git-Integrated State Manager
Story: 25.3 - Implement FastContextLoader

Design Pattern: Service Layer + Caching
Dependencies: StateCoordinator (Epic 24), structlog

Performance Targets:
    - Epic context: <5ms (p95)
    - Agent context: <5ms (p95)
    - Project analysis: <10ms (p95)

Example:
    ```python
    loader = FastContextLoader(db_path=Path(".gao-dev/documents.db"))

    # Get epic context (all stories + metadata)
    context = loader.get_epic_context(epic_num=1)
    # Returns in <5ms: {epic: {...}, stories: [{...}], summary: {...}}

    # Get agent-specific context (role-based filtering)
    context = loader.get_agent_context(
        agent_role="developer",
        epic_num=1
    )
    # Returns stories assigned to developers, active actions, etc.

    # Analyze existing project
    analysis = loader.analyze_existing_project(project_path=Path("/project"))
    # Scans filesystem + database to determine project state
    ```
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import structlog

from gao_dev.core.state_coordinator import StateCoordinator

logger = structlog.get_logger()


class FastContextLoader:
    """
    Fast context loader for agent operations.

    Provides <5ms context queries using indexed database lookups and
    intelligent caching. Designed for high-frequency agent queries.

    Attributes:
        db_path: Path to SQLite database
        coordinator: StateCoordinator for database access
    """

    def __init__(self, db_path: Path):
        """
        Initialize fast context loader.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.coordinator = StateCoordinator(db_path=self.db_path)

        self.logger = logger.bind(service="fast_context_loader")

        self.logger.info(
            "fast_context_loader_initialized",
            db_path=str(self.db_path)
        )

    # ============================================================================
    # EPIC CONTEXT QUERIES (<5ms target)
    # ============================================================================

    def get_epic_context(
        self,
        epic_num: int,
        include_stories: bool = True,
        include_summary: bool = True,
    ) -> Dict[str, Any]:
        """
        Get comprehensive epic context.

        Returns epic info with optional stories and summary statistics.
        Optimized for <5ms performance using indexed queries.

        Args:
            epic_num: Epic number
            include_stories: Include all stories (default: True)
            include_summary: Include summary stats (default: True)

        Returns:
            Dictionary with keys:
                - epic: Epic record
                - stories: List of story records (if include_stories=True)
                - summary: Summary statistics (if include_summary=True)
                    - total_stories: int
                    - completed_stories: int
                    - in_progress_stories: int
                    - blocked_stories: int
                    - progress_percentage: float

        Raises:
            ValueError: If epic not found

        Example:
            ```python
            context = loader.get_epic_context(epic_num=1)
            print(f"Epic: {context['epic']['title']}")
            print(f"Progress: {context['summary']['progress_percentage']}%")
            for story in context['stories']:
                print(f"  - Story {story['story_num']}: {story['title']}")
            ```
        """
        start_time = datetime.now()

        # Get epic (fast indexed lookup)
        epic = self.coordinator.epic_service.get(epic_num)

        context = {"epic": epic}

        # Get stories (if requested)
        if include_stories:
            stories = self.coordinator.story_service.list_by_epic(epic_num)
            context["stories"] = stories
        else:
            context["stories"] = []

        # Calculate summary (if requested)
        if include_summary:
            stories = context["stories"] if include_stories else self.coordinator.story_service.list_by_epic(epic_num)

            # Calculate summary statistics
            total = len(stories)
            completed = sum(1 for s in stories if s["status"] == "completed")
            in_progress = sum(1 for s in stories if s["status"] == "in_progress")
            blocked = sum(1 for s in stories if s["status"] == "blocked")
            progress = (completed / total * 100.0) if total > 0 else 0.0

            context["summary"] = {
                "total_stories": total,
                "completed_stories": completed,
                "in_progress_stories": in_progress,
                "blocked_stories": blocked,
                "progress_percentage": progress,
            }

        # Log performance
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.logger.debug(
            "epic_context_loaded",
            epic_num=epic_num,
            duration_ms=duration_ms,
            stories_count=len(context["stories"]),
        )

        return context

    def get_story_context(
        self,
        epic_num: int,
        story_num: int,
        include_epic: bool = True,
    ) -> Dict[str, Any]:
        """
        Get comprehensive story context.

        Returns story info with optional epic context.

        Args:
            epic_num: Epic number
            story_num: Story number
            include_epic: Include epic context (default: True)

        Returns:
            Dictionary with keys:
                - story: Story record
                - epic: Epic record (if include_epic=True)

        Example:
            ```python
            context = loader.get_story_context(epic_num=1, story_num=1)
            print(f"Story: {context['story']['title']}")
            print(f"Epic: {context['epic']['title']}")
            ```
        """
        start_time = datetime.now()

        # Get story
        story = self.coordinator.story_service.get(epic_num, story_num)

        context = {"story": story}

        # Get epic (if requested)
        if include_epic:
            epic = self.coordinator.epic_service.get(epic_num)
            context["epic"] = epic

        # Log performance
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.logger.debug(
            "story_context_loaded",
            epic_num=epic_num,
            story_num=story_num,
            duration_ms=duration_ms,
        )

        return context

    # ============================================================================
    # AGENT-SPECIFIC CONTEXT (<5ms target)
    # ============================================================================

    def get_agent_context(
        self,
        agent_role: str,
        epic_num: Optional[int] = None,
        assignee: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get context tailored for specific agent role.

        Returns role-specific filtered context optimized for agent needs.

        Args:
            agent_role: Agent role (developer, product_manager, architect, etc.)
            epic_num: Optional epic filter
            assignee: Optional assignee filter

        Returns:
            Dictionary with role-specific context:
                - For 'developer': assigned stories, blocked items, action items
                - For 'product_manager': all epics, planning stories, decisions needed
                - For 'architect': design stories, technical debt
                - For 'test_engineer': testing stories, quality metrics

        Example:
            ```python
            # Get developer context
            context = loader.get_agent_context(
                agent_role="developer",
                assignee="Amelia"
            )
            # Returns: stories assigned to Amelia, blocked items, action items

            # Get product manager context
            context = loader.get_agent_context(
                agent_role="product_manager",
                epic_num=1
            )
            # Returns: epic overview, planning stories, decisions needed
            ```
        """
        start_time = datetime.now()

        context = {
            "agent_role": agent_role,
            "epic_num": epic_num,
            "assignee": assignee,
        }

        if agent_role == "developer":
            # Developer needs: assigned stories, blocked items, action items
            if epic_num:
                stories = self.coordinator.story_service.list_by_epic(epic_num)
            else:
                # Get all active stories across all epics
                stories = self._get_all_active_stories()

            # Filter by assignee if provided
            if assignee:
                stories = [s for s in stories if s.get("assignee") == assignee]

            # Filter by status (developers care about in_progress and pending)
            relevant_stories = [
                s for s in stories
                if s["status"] in ["in_progress", "pending", "blocked"]
            ]

            context["stories"] = relevant_stories
            context["blocked_count"] = sum(1 for s in stories if s["status"] == "blocked")

            # Get active action items
            action_items = self.coordinator.action_service.get_active(assignee=assignee)
            context["action_items"] = action_items

        elif agent_role == "product_manager":
            # PM needs: epic overview, planning stories, progress
            if epic_num:
                epic_context = self.get_epic_context(epic_num)
                context.update(epic_context)
            else:
                # Get all active epics
                epics = self.coordinator.epic_service.list_active()
                context["epics"] = epics

        elif agent_role in ["architect", "technical_architect"]:
            # Architect needs: design stories, technical stories
            if epic_num:
                stories = self.coordinator.story_service.list_by_epic(epic_num)
            else:
                stories = self._get_all_active_stories()

            # Filter for high-priority and design-related stories
            relevant_stories = [
                s for s in stories
                if s["priority"] in ["P0", "P1"]
            ]

            context["stories"] = relevant_stories

        elif agent_role == "test_engineer":
            # Test engineer needs: testing stories, quality metrics
            if epic_num:
                stories = self.coordinator.story_service.list_by_epic(epic_num)
            else:
                stories = self._get_all_active_stories()

            # Filter for testing and review statuses
            relevant_stories = [
                s for s in stories
                if s["status"] in ["testing", "review", "completed"]
            ]

            context["stories"] = relevant_stories

        else:
            # Generic context: just return all stories
            if epic_num:
                stories = self.coordinator.story_service.list_by_epic(epic_num)
            else:
                stories = self._get_all_active_stories()

            context["stories"] = stories

        # Log performance
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.logger.debug(
            "agent_context_loaded",
            agent_role=agent_role,
            epic_num=epic_num,
            duration_ms=duration_ms,
        )

        return context

    # ============================================================================
    # PROJECT ANALYSIS (<10ms target)
    # ============================================================================

    def analyze_existing_project(
        self,
        project_path: Path,
    ) -> Dict[str, Any]:
        """
        Analyze existing project to determine state.

        Scans filesystem and database to build project overview.
        Useful for agent initialization and project discovery.

        Args:
            project_path: Path to project root

        Returns:
            Dictionary with analysis:
                - has_database: bool (whether .gao-dev/documents.db exists)
                - epic_count: int
                - story_count: int
                - active_epics: List[int]
                - project_path: str

        Example:
            ```python
            analysis = loader.analyze_existing_project(Path("/project"))
            if analysis["has_database"]:
                print(f"Found {analysis['epic_count']} epics")
            else:
                print("No database found - new project")
            ```
        """
        start_time = datetime.now()

        project_path = Path(project_path)

        # Check for database
        db_path = project_path / ".gao-dev" / "documents.db"
        has_database = db_path.exists()

        analysis = {
            "project_path": str(project_path),
            "has_database": has_database,
            "epic_count": 0,
            "story_count": 0,
            "active_epics": [],
        }

        if has_database:
            # Load epics and stories
            epics = self.coordinator.epic_service.list_active()
            analysis["epic_count"] = len(epics)
            analysis["active_epics"] = [e["epic_num"] for e in epics]

            # Count total stories across all epics
            total_stories = 0
            for epic in epics:
                stories = self.coordinator.story_service.list_by_epic(epic["epic_num"])
                total_stories += len(stories)

            analysis["story_count"] = total_stories

        # Log performance
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.logger.debug(
            "project_analyzed",
            project_path=str(project_path),
            duration_ms=duration_ms,
            has_database=has_database,
        )

        return analysis

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _get_all_active_stories(self) -> List[Dict[str, Any]]:
        """
        Get all active stories across all epics.

        Returns:
            List of all story records from active epics
        """
        # Get all active epics
        epics = self.coordinator.epic_service.list_active()

        # Get stories for each epic
        all_stories = []
        for epic in epics:
            stories = self.coordinator.story_service.list_by_epic(epic["epic_num"])
            all_stories.extend(stories)

        return all_stories

    # ============================================================================
    # CLEANUP
    # ============================================================================

    def close(self) -> None:
        """Close all connections."""
        self.coordinator.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connections."""
        self.close()
