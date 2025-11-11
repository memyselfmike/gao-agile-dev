"""State Coordinator - Facade for all state services.

This coordinator provides a unified interface to all state management
services with coordinated operations.

Epic: 24 - State Tables & Tracker
Story: 24.7 - Implement StateCoordinator Facade

Design Pattern: Facade
Dependencies: All 5 state services, structlog
"""

from pathlib import Path
from typing import Optional, List, Dict, Any

import structlog

from gao_dev.core.services.epic_state_service import EpicStateService
from gao_dev.core.services.story_state_service import StoryStateService
from gao_dev.core.services.action_item_service import ActionItemService
from gao_dev.core.services.ceremony_service import CeremonyService
from gao_dev.core.services.learning_index_service import LearningIndexService
from gao_dev.core.services.feature_state_service import (
    FeatureStateService,
    Feature,
    FeatureScope,
    FeatureStatus,
)

logger = structlog.get_logger()


class StateCoordinator:
    """
    Facade coordinating all state management services.

    Provides unified interface to epic, story, action item, ceremony,
    learning, and feature state services with coordinated operations.

    Example:
        ```python
        coordinator = StateCoordinator(
            db_path=Path(".gao-dev/documents.db"),
            project_root=Path("/project")
        )

        # Create epic and stories in one operation
        epic = coordinator.create_epic(
            epic_num=1,
            title="User Authentication",
            total_stories=5
        )

        story = coordinator.create_story(
            epic_num=1,
            story_num=1,
            title="Login endpoint",
            auto_update_epic=True  # Automatically updates epic progress
        )

        # Complete story and update epic in one transaction
        coordinator.complete_story(
            epic_num=1,
            story_num=1,
            actual_hours=8.0,
            auto_update_epic=True
        )

        # Get comprehensive epic state
        state = coordinator.get_epic_state(epic_num=1)
        # Returns: epic info + all stories + related action items + learnings
        ```
    """

    def __init__(self, db_path: Path, project_root: Optional[Path] = None):
        """
        Initialize state coordinator with all services.

        Args:
            db_path: Path to SQLite database file (shared across all services)
            project_root: Project root directory (for feature service)
        """
        self.db_path = Path(db_path)
        self.project_root = Path(project_root) if project_root else self.db_path.parent.parent

        # Initialize all services with same database
        self.epic_service = EpicStateService(db_path=self.db_path)
        self.story_service = StoryStateService(db_path=self.db_path)
        self.action_service = ActionItemService(db_path=self.db_path)
        self.ceremony_service = CeremonyService(db_path=self.db_path)
        self.learning_service = LearningIndexService(db_path=self.db_path)
        self.feature_service = FeatureStateService(project_root=self.project_root)

        self.logger = logger.bind(service="state_coordinator")

    # Epic Operations

    def create_epic(
        self,
        epic_num: int,
        title: str,
        status: str = "planning",
        total_stories: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create new epic.

        Delegates to EpicStateService.

        Args:
            epic_num: Epic number
            title: Epic title
            status: Epic status
            total_stories: Total number of stories
            metadata: Additional metadata

        Returns:
            Created epic record
        """
        return self.epic_service.create(
            epic_num=epic_num,
            title=title,
            status=status,
            total_stories=total_stories,
            metadata=metadata,
        )

    def get_epic_state(self, epic_num: int) -> Dict[str, Any]:
        """
        Get comprehensive epic state.

        Returns epic info plus all related stories.

        Args:
            epic_num: Epic number

        Returns:
            Dictionary with 'epic' and 'stories' keys
        """
        epic = self.epic_service.get(epic_num)
        stories = self.story_service.list_by_epic(epic_num)

        return {"epic": epic, "stories": stories}

    # Story Operations

    def create_story(
        self,
        epic_num: int,
        story_num: int,
        title: str,
        status: str = "pending",
        assignee: Optional[str] = None,
        priority: str = "P2",
        estimate_hours: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_update_epic: bool = False,
    ) -> Dict[str, Any]:
        """
        Create new story.

        Optionally updates epic's total_stories count.

        Args:
            epic_num: Epic number
            story_num: Story number
            title: Story title
            status: Story status
            assignee: Assignee name
            priority: Priority level
            estimate_hours: Estimated hours
            metadata: Additional metadata
            auto_update_epic: If True, increment epic's total_stories

        Returns:
            Created story record
        """
        # Create story
        story = self.story_service.create(
            epic_num=epic_num,
            story_num=story_num,
            title=title,
            status=status,
            assignee=assignee,
            priority=priority,
            estimate_hours=estimate_hours,
            metadata=metadata,
        )

        # Update epic if requested
        if auto_update_epic:
            epic = self.epic_service.get(epic_num)
            self.epic_service.update_progress(
                epic_num=epic_num, total_stories=epic["total_stories"] + 1
            )

            self.logger.info(
                "epic_total_stories_incremented",
                epic_num=epic_num,
                new_total=epic["total_stories"] + 1,
            )

        return story

    def complete_story(
        self,
        epic_num: int,
        story_num: int,
        actual_hours: Optional[float] = None,
        auto_update_epic: bool = False,
    ) -> Dict[str, Any]:
        """
        Mark story as completed.

        Optionally updates epic's completed_stories count and progress.

        Args:
            epic_num: Epic number
            story_num: Story number
            actual_hours: Actual hours spent
            auto_update_epic: If True, increment epic's completed_stories

        Returns:
            Updated story record
        """
        # Complete story
        story = self.story_service.complete(
            epic_num=epic_num, story_num=story_num, actual_hours=actual_hours
        )

        # Update epic if requested
        if auto_update_epic:
            epic = self.epic_service.get(epic_num)
            new_completed = epic["completed_stories"] + 1

            # Auto-transition epic to in_progress or completed
            new_status = epic["status"]
            if new_status == "planning" and new_completed > 0:
                new_status = "in_progress"
            elif new_completed >= epic["total_stories"] and epic["total_stories"] > 0:
                new_status = "completed"

            self.epic_service.update_progress(
                epic_num=epic_num,
                completed_stories=new_completed,
                status=new_status,
            )

            self.logger.info(
                "epic_progress_auto_updated",
                epic_num=epic_num,
                completed_stories=new_completed,
                total_stories=epic["total_stories"],
                new_status=new_status,
            )

        return story

    # Action Item Operations

    def create_action_item(
        self,
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        assignee: Optional[str] = None,
        epic_num: Optional[int] = None,
        story_num: Optional[int] = None,
        due_date: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create action item. Delegates to ActionItemService."""
        return self.action_service.create(
            title=title,
            description=description,
            priority=priority,
            assignee=assignee,
            epic_num=epic_num,
            story_num=story_num,
            due_date=due_date,
            metadata=metadata,
        )

    def get_active_action_items(
        self, assignee: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active action items. Delegates to ActionItemService."""
        return self.action_service.get_active(assignee=assignee)

    # Ceremony Operations

    def record_ceremony(
        self,
        ceremony_type: str,
        summary: str,
        participants: Optional[str] = None,
        decisions: Optional[str] = None,
        action_items: Optional[str] = None,
        epic_num: Optional[int] = None,
        story_num: Optional[int] = None,
        held_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record ceremony summary. Delegates to CeremonyService."""
        return self.ceremony_service.create_summary(
            ceremony_type=ceremony_type,
            summary=summary,
            participants=participants,
            decisions=decisions,
            action_items=action_items,
            epic_num=epic_num,
            story_num=story_num,
            held_at=held_at,
            metadata=metadata,
        )

    def get_recent_ceremonies(
        self, ceremony_type: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent ceremonies. Delegates to CeremonyService."""
        return self.ceremony_service.get_recent(
            ceremony_type=ceremony_type, limit=limit
        )

    # Learning Operations

    def index_learning(
        self,
        topic: str,
        category: str,
        learning: str,
        context: Optional[str] = None,
        source_type: Optional[str] = None,
        epic_num: Optional[int] = None,
        story_num: Optional[int] = None,
        relevance_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Index a learning. Delegates to LearningIndexService."""
        return self.learning_service.index(
            topic=topic,
            category=category,
            learning=learning,
            context=context,
            source_type=source_type,
            epic_num=epic_num,
            story_num=story_num,
            relevance_score=relevance_score,
            metadata=metadata,
        )

    def search_learnings(
        self,
        topic: Optional[str] = None,
        category: Optional[str] = None,
        active_only: bool = True,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search learnings. Delegates to LearningIndexService."""
        return self.learning_service.search(
            topic=topic, category=category, active_only=active_only, limit=limit
        )

    # Feature Operations

    def create_feature(
        self,
        name: str,
        scope: FeatureScope,
        scale_level: int,
        description: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> Feature:
        """
        Create feature (facade to FeatureStateService).

        Args:
            name: Feature name (e.g., "user-auth", "mvp")
            scope: MVP or FEATURE
            scale_level: 0-4
            description: Optional description
            owner: Optional owner

        Returns:
            Feature object

        Raises:
            ValueError: If feature already exists
        """
        self.logger.info(
            "creating_feature",
            name=name,
            scope=scope.value if isinstance(scope, FeatureScope) else scope,
            scale_level=scale_level,
        )
        return self.feature_service.create_feature(
            name=name,
            scope=scope,
            scale_level=scale_level,
            description=description,
            owner=owner,
        )

    def get_feature(self, name: str) -> Optional[Dict[str, Any]]:
        """Get feature by name (facade)."""
        return self.feature_service.get_feature(name)

    def list_features(
        self,
        scope: Optional[FeatureScope] = None,
        status: Optional[FeatureStatus] = None,
    ) -> List[Feature]:
        """List features with optional filters (facade)."""
        return self.feature_service.list_features(scope=scope, status=status)

    def update_feature_status(self, name: str, status: FeatureStatus) -> bool:
        """Update feature status (facade)."""
        self.logger.info(
            "updating_feature_status",
            name=name,
            status=status.value if isinstance(status, FeatureStatus) else status,
        )
        return self.feature_service.update_status(name=name, status=status)

    def get_feature_state(self, name: str) -> Dict[str, Any]:
        """
        Get comprehensive feature state.

        Returns complete feature data including:
        - Feature metadata
        - All epics for this feature
        - Story counts
        - Completion metrics

        Args:
            name: Feature name

        Returns:
            Dictionary with:
                - feature: Feature dict
                - epics: List of Epic dicts for this feature
                - epic_summaries: List of {epic_num, title, status, story_count, completed_count}
                - total_stories: Total story count across all epics
                - completed_stories: Number of completed stories
                - completion_pct: Percentage of stories complete

        Raises:
            ValueError: If feature not found
        """
        # Get feature metadata
        feature = self.feature_service.get_feature(name)
        if not feature:
            raise ValueError(f"Feature '{name}' not found")

        # Get all epics for this feature (from epics table, filter by feature column)
        # Note: EpicStateService uses epic_state table, but we need epics table
        # Since EpicStateService doesn't support feature filtering yet,
        # we'll query directly or filter in-memory
        all_epics = self.epic_service.list()
        feature_epics = [e for e in all_epics if e.get("feature") == name]

        # Build epic summaries
        epic_summaries = []
        total_stories = 0
        completed_stories = 0

        for epic in feature_epics:
            epic_num = epic["epic_num"]
            stories = self.story_service.list_by_epic(epic_num)
            story_count = len(stories)
            completed_count = len([s for s in stories if s["status"] == "completed"])

            epic_summaries.append(
                {
                    "epic_num": epic_num,
                    "title": epic["title"],
                    "status": epic["status"],
                    "story_count": story_count,
                    "completed_count": completed_count,
                }
            )

            total_stories += story_count
            completed_stories += completed_count

        completion_pct = (
            (completed_stories / total_stories * 100) if total_stories > 0 else 0.0
        )

        self.logger.info(
            "feature_state_retrieved",
            name=name,
            num_epics=len(feature_epics),
            total_stories=total_stories,
            completed_stories=completed_stories,
            completion_pct=completion_pct,
        )

        return {
            "feature": feature,
            "epics": feature_epics,
            "epic_summaries": epic_summaries,
            "total_stories": total_stories,
            "completed_stories": completed_stories,
            "completion_pct": completion_pct,
        }

    # Cleanup

    def close(self) -> None:
        """Close all service connections."""
        self.epic_service.close()
        self.story_service.close()
        self.action_service.close()
        self.ceremony_service.close()
        self.learning_service.close()
        self.feature_service.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close all connections."""
        self.close()
