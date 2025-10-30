"""
StoryLifecycleManager Service - Manages story and epic lifecycle.

Extracted from GAODevOrchestrator (Epic 6, Story 6.2) to achieve SOLID principles.

Responsibilities:
- Create new stories and epics
- Transition story states with validation
- Track epic progress
- Publish lifecycle events

NOT responsible for:
- Workflow execution (WorkflowCoordinator)
- Quality validation (QualityGateManager)
- File operations (Repository layer)
- Subprocess execution (ProcessExecutor)
"""

import structlog
from typing import Dict, List, Optional
from datetime import datetime

from ..interfaces.repository import IStoryRepository
from ..interfaces.event_bus import IEventBus
from ..events.event_bus import Event
from ..models.story import Story, StoryIdentifier, StoryStatus

logger = structlog.get_logger()


class StoryTransitionError(Exception):
    """Raised when an invalid story state transition is attempted."""
    pass


class StoryLifecycleManager:
    """
    Manages story and epic lifecycle.

    Single Responsibility: Create stories, transition states, track epic progress,
    and publish lifecycle events.

    This service was extracted from GAODevOrchestrator (Epic 6, Story 6.2) to
    follow the Single Responsibility Principle.

    Responsibilities:
    - Create stories and epics
    - Manage state transitions with validation
    - Validate state machine rules
    - Track epic completion
    - Publish lifecycle events

    NOT responsible for:
    - Workflow execution (WorkflowCoordinator)
    - Quality gates (QualityGateManager)
    - File operations (Repository layer)
    - Subprocess execution (ProcessExecutor)

    State Machine:
    ```
    backlog → todo → in-progress → review → done
                ↑           ↓
                └───────────┘
             (back to todo if review fails)
    ```

    Example:
        ```python
        lifecycle = StoryLifecycleManager(
            story_repository=repo,
            event_bus=bus
        )

        # Create new story
        story = await lifecycle.create_story(
            epic=1,
            story=1,
            title="Implement feature X"
        )

        # Transition state
        await lifecycle.transition_state(
            story.id,
            StoryStatus.IN_PROGRESS
        )

        # Track epic progress
        progress = await lifecycle.get_epic_progress(epic=1)
        ```
    """

    # Valid state transitions (state machine definition)
    VALID_TRANSITIONS: Dict[StoryStatus, List[StoryStatus]] = {
        StoryStatus.BACKLOG: [StoryStatus.TODO],
        StoryStatus.TODO: [StoryStatus.IN_PROGRESS],
        StoryStatus.IN_PROGRESS: [StoryStatus.REVIEW, StoryStatus.TODO],
        StoryStatus.REVIEW: [StoryStatus.DONE, StoryStatus.TODO],
        StoryStatus.DONE: [],  # Terminal state
    }

    def __init__(
        self,
        story_repository: IStoryRepository,
        event_bus: IEventBus
    ):
        """
        Initialize lifecycle manager with injected dependencies.

        Args:
            story_repository: Repository for story persistence
            event_bus: Event bus for publishing lifecycle events
        """
        self.story_repository = story_repository
        self.event_bus = event_bus

        logger.info("story_lifecycle_manager_initialized")

    async def create_story(
        self,
        epic: int,
        story: int,
        title: str,
        description: Optional[str] = None,
        story_points: Optional[int] = None,
        assigned_to: Optional[str] = None
    ) -> Story:
        """
        Create a new story.

        Creates a story with BACKLOG status and publishes StoryCreated event.

        Args:
            epic: Epic number
            story: Story number
            title: Story title
            description: Optional story description
            story_points: Optional story points
            assigned_to: Optional assigned agent

        Returns:
            Created Story instance

        Raises:
            ValueError: If epic or story numbers are invalid
            RepositoryError: If save operation fails
        """
        # Create story identifier
        story_id = StoryIdentifier(epic=epic, story=story)

        logger.info(
            "creating_story",
            epic=epic,
            story=story,
            title=title
        )

        # Create story object (initial status: BACKLOG)
        new_story = Story(
            id=story_id,
            title=title,
            status=StoryStatus.BACKLOG,
            file_path=story_id.to_path(),
            description=description,
            story_points=story_points,
            assigned_to=assigned_to
        )

        # Persist story
        await self.story_repository.save(new_story)

        # Publish event
        self.event_bus.publish(Event(
            type="StoryCreated",
            data={
                "story_id": story_id.to_string(),
                "epic": epic,
                "story": story,
                "title": title,
                "status": StoryStatus.BACKLOG.value
            }
        ))

        logger.info(
            "story_created",
            story_id=story_id.to_string(),
            status=StoryStatus.BACKLOG.value
        )

        return new_story

    async def transition_state(
        self,
        story_id: StoryIdentifier,
        new_state: StoryStatus
    ) -> Story:
        """
        Transition story to a new state with validation.

        Validates transition according to state machine rules and publishes
        StoryStateTransitioned event.

        Args:
            story_id: Story identifier
            new_state: Target state

        Returns:
            Updated Story instance

        Raises:
            StoryTransitionError: If transition is invalid
            RepositoryError: If story not found or save fails
        """
        # Load current story
        story = await self.story_repository.find_by_id(story_id.to_string())
        if not story:
            raise ValueError(f"Story not found: {story_id}")

        old_state = story.status

        # Validate transition
        if not self._is_valid_transition(old_state, new_state):
            raise StoryTransitionError(
                f"Invalid transition: {old_state.value} → {new_state.value}. "
                f"Valid transitions from {old_state.value}: "
                f"{[s.value for s in self.VALID_TRANSITIONS.get(old_state, [])]}"
            )

        logger.info(
            "transitioning_story_state",
            story_id=story_id.to_string(),
            old_state=old_state.value,
            new_state=new_state.value
        )

        # Update story status
        story.status = new_state
        await self.story_repository.save(story)

        # Publish event
        self.event_bus.publish(Event(
            type="StoryStateTransitioned",
            data={
                "story_id": story_id.to_string(),
                "old_state": old_state.value,
                "new_state": new_state.value,
                "timestamp": datetime.now().isoformat()
            }
        ))

        logger.info(
            "story_state_transitioned",
            story_id=story_id.to_string(),
            old_state=old_state.value,
            new_state=new_state.value
        )

        return story

    def _is_valid_transition(
        self,
        current_state: StoryStatus,
        target_state: StoryStatus
    ) -> bool:
        """
        Check if a state transition is valid.

        Uses state machine definition to validate transitions.

        Args:
            current_state: Current story state
            target_state: Target story state

        Returns:
            True if transition is valid, False otherwise
        """
        valid_targets = self.VALID_TRANSITIONS.get(current_state, [])
        return target_state in valid_targets

    async def get_epic_progress(self, epic: int) -> Dict[str, int]:
        """
        Get epic completion status and progress.

        Args:
            epic: Epic number

        Returns:
            Dictionary with:
                - total_stories: Total stories in epic
                - completed_stories: Stories with DONE status
                - in_progress_stories: Stories in progress
                - completion_percentage: Percentage complete (0-100)

        Raises:
            RepositoryError: If data access fails
        """
        logger.debug("calculating_epic_progress", epic=epic)

        # Load all stories in epic
        stories = await self.story_repository.find_by_epic(epic)

        # Calculate metrics
        total_stories = len(stories)
        completed_stories = sum(1 for s in stories if s.status == StoryStatus.DONE)
        in_progress_stories = sum(1 for s in stories if s.status == StoryStatus.IN_PROGRESS)

        completion_percentage = (
            (completed_stories / total_stories * 100) if total_stories > 0 else 0
        )

        progress = {
            "epic": epic,
            "total_stories": total_stories,
            "completed_stories": completed_stories,
            "in_progress_stories": in_progress_stories,
            "completion_percentage": int(completion_percentage)
        }

        logger.info("epic_progress_calculated", **progress)

        # Publish EpicCompleted event if all done
        if total_stories > 0 and completed_stories == total_stories:
            self.event_bus.publish(Event(
                type="EpicCompleted",
                data={
                    "epic": epic,
                    "story_count": total_stories
                }
            ))
            logger.info("epic_completed", epic=epic, story_count=total_stories)

        return progress

    async def get_story(self, story_id: StoryIdentifier) -> Optional[Story]:
        """
        Get a story by its identifier.

        Args:
            story_id: Story identifier

        Returns:
            Story if found, None otherwise

        Raises:
            RepositoryError: If data access fails
        """
        return await self.story_repository.find_by_id(story_id.to_string())

    async def list_stories_by_status(self, status: StoryStatus) -> List[Story]:
        """
        List all stories with a given status.

        Args:
            status: Story status to filter by

        Returns:
            List of stories (may be empty)

        Raises:
            RepositoryError: If data access fails
        """
        return await self.story_repository.find_by_status(status)
