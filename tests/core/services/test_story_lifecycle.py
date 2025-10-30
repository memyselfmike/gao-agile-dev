"""
Tests for StoryLifecycleManager service.

Tests story creation, state transitions, validation, and epic tracking.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from gao_dev.core.services.story_lifecycle import (
    StoryLifecycleManager,
    StoryTransitionError
)
from gao_dev.core.models.story import Story, StoryIdentifier, StoryStatus
from gao_dev.core.interfaces.repository import IStoryRepository
from gao_dev.core.interfaces.event_bus import IEventBus


@pytest.fixture
def mock_story_repository():
    """Create mock story repository."""
    repo = AsyncMock(spec=IStoryRepository)
    # Configure return values to avoid unraisable exceptions
    repo.save.return_value = None
    repo.find_by_id.return_value = None
    repo.find_by_epic.return_value = []
    repo.find_by_status.return_value = []
    return repo


@pytest.fixture
def mock_event_bus():
    """Create mock event bus."""
    bus = Mock(spec=IEventBus)
    return bus


@pytest.fixture
def lifecycle_manager(mock_story_repository, mock_event_bus):
    """Create StoryLifecycleManager with mocked dependencies."""
    return StoryLifecycleManager(
        story_repository=mock_story_repository,
        event_bus=mock_event_bus
    )


@pytest.mark.asyncio
class TestStoryCreation:
    """Test story creation functionality."""

    async def test_create_story_basic(self, lifecycle_manager, mock_story_repository, mock_event_bus):
        """Test creating a basic story."""
        # Act
        story = await lifecycle_manager.create_story(
            epic=1,
            story=1,
            title="Test Story"
        )

        # Assert
        assert story.id.epic == 1
        assert story.id.story == 1
        assert story.title == "Test Story"
        assert story.status == StoryStatus.BACKLOG

        # Verify repository save called
        mock_story_repository.save.assert_called_once()

        # Verify event published
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert event.type == "StoryCreated"
        assert event.data["epic"] == 1
        assert event.data["story"] == 1

    async def test_create_story_with_details(self, lifecycle_manager, mock_story_repository):
        """Test creating a story with full details."""
        # Act
        story = await lifecycle_manager.create_story(
            epic=2,
            story=3,
            title="Implement feature X",
            description="Full description here",
            story_points=5,
            assigned_to="Amelia"
        )

        # Assert
        assert story.title == "Implement feature X"
        assert story.description == "Full description here"
        assert story.story_points == 5
        assert story.assigned_to == "Amelia"

    async def test_create_story_invalid_epic(self, lifecycle_manager):
        """Test creating story with invalid epic number."""
        # Act & Assert
        with pytest.raises(ValueError, match="Epic must be >= 1"):
            await lifecycle_manager.create_story(
                epic=0,
                story=1,
                title="Invalid"
            )

    async def test_create_story_invalid_story_number(self, lifecycle_manager):
        """Test creating story with invalid story number."""
        # Act & Assert
        with pytest.raises(ValueError, match="Story must be >= 1"):
            await lifecycle_manager.create_story(
                epic=1,
                story=-1,
                title="Invalid"
            )


@pytest.mark.asyncio
class TestStateTransitions:
    """Test story state transitions and validation."""

    async def test_valid_transition_backlog_to_todo(
        self, lifecycle_manager, mock_story_repository, mock_event_bus
    ):
        """Test valid transition from BACKLOG to TODO."""
        # Arrange
        story_id = StoryIdentifier(1, 1)
        existing_story = Story(
            id=story_id,
            title="Test",
            status=StoryStatus.BACKLOG,
            file_path=story_id.to_path()
        )
        mock_story_repository.find_by_id.return_value = existing_story

        # Act
        updated_story = await lifecycle_manager.transition_state(
            story_id,
            StoryStatus.TODO
        )

        # Assert
        assert updated_story.status == StoryStatus.TODO
        mock_story_repository.save.assert_called_once()

        # Verify event
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert event.type == "StoryStateTransitioned"
        assert event.data["old_state"] == "backlog"
        assert event.data["new_state"] == "todo"

    async def test_valid_transition_todo_to_in_progress(
        self, lifecycle_manager, mock_story_repository
    ):
        """Test valid transition from TODO to IN_PROGRESS."""
        # Arrange
        story_id = StoryIdentifier(1, 1)
        existing_story = Story(
            id=story_id,
            title="Test",
            status=StoryStatus.TODO,
            file_path=story_id.to_path()
        )
        mock_story_repository.find_by_id.return_value = existing_story

        # Act
        updated_story = await lifecycle_manager.transition_state(
            story_id,
            StoryStatus.IN_PROGRESS
        )

        # Assert
        assert updated_story.status == StoryStatus.IN_PROGRESS

    async def test_valid_transition_in_progress_to_review(
        self, lifecycle_manager, mock_story_repository
    ):
        """Test valid transition from IN_PROGRESS to REVIEW."""
        # Arrange
        story_id = StoryIdentifier(1, 1)
        existing_story = Story(
            id=story_id,
            title="Test",
            status=StoryStatus.IN_PROGRESS,
            file_path=story_id.to_path()
        )
        mock_story_repository.find_by_id.return_value = existing_story

        # Act
        updated_story = await lifecycle_manager.transition_state(
            story_id,
            StoryStatus.REVIEW
        )

        # Assert
        assert updated_story.status == StoryStatus.REVIEW

    async def test_valid_transition_review_to_done(
        self, lifecycle_manager, mock_story_repository
    ):
        """Test valid transition from REVIEW to DONE."""
        # Arrange
        story_id = StoryIdentifier(1, 1)
        existing_story = Story(
            id=story_id,
            title="Test",
            status=StoryStatus.REVIEW,
            file_path=story_id.to_path()
        )
        mock_story_repository.find_by_id.return_value = existing_story

        # Act
        updated_story = await lifecycle_manager.transition_state(
            story_id,
            StoryStatus.DONE
        )

        # Assert
        assert updated_story.status == StoryStatus.DONE

    async def test_valid_transition_review_back_to_todo(
        self, lifecycle_manager, mock_story_repository
    ):
        """Test valid transition from REVIEW back to TODO (review failed)."""
        # Arrange
        story_id = StoryIdentifier(1, 1)
        existing_story = Story(
            id=story_id,
            title="Test",
            status=StoryStatus.REVIEW,
            file_path=story_id.to_path()
        )
        mock_story_repository.find_by_id.return_value = existing_story

        # Act
        updated_story = await lifecycle_manager.transition_state(
            story_id,
            StoryStatus.TODO
        )

        # Assert
        assert updated_story.status == StoryStatus.TODO

    async def test_invalid_transition_backlog_to_done(
        self, lifecycle_manager, mock_story_repository
    ):
        """Test invalid transition from BACKLOG directly to DONE."""
        # Arrange
        story_id = StoryIdentifier(1, 1)
        existing_story = Story(
            id=story_id,
            title="Test",
            status=StoryStatus.BACKLOG,
            file_path=story_id.to_path()
        )
        mock_story_repository.find_by_id.return_value = existing_story

        # Act & Assert
        with pytest.raises(StoryTransitionError) as exc_info:
            await lifecycle_manager.transition_state(
                story_id,
                StoryStatus.DONE
            )

        assert "Invalid transition" in str(exc_info.value)
        assert "backlog → done" in str(exc_info.value)

    async def test_invalid_transition_done_to_anything(
        self, lifecycle_manager, mock_story_repository
    ):
        """Test that DONE is a terminal state (no transitions allowed)."""
        # Arrange
        story_id = StoryIdentifier(1, 1)
        existing_story = Story(
            id=story_id,
            title="Test",
            status=StoryStatus.DONE,
            file_path=story_id.to_path()
        )
        mock_story_repository.find_by_id.return_value = existing_story

        # Act & Assert
        with pytest.raises(StoryTransitionError):
            await lifecycle_manager.transition_state(
                story_id,
                StoryStatus.IN_PROGRESS
            )

    async def test_transition_story_not_found(
        self, lifecycle_manager, mock_story_repository
    ):
        """Test transition fails when story doesn't exist."""
        # Arrange
        story_id = StoryIdentifier(1, 1)
        mock_story_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Story not found"):
            await lifecycle_manager.transition_state(
                story_id,
                StoryStatus.TODO
            )


@pytest.mark.asyncio
class TestEpicProgress:
    """Test epic progress tracking."""

    async def test_get_epic_progress_empty_epic(
        self, lifecycle_manager, mock_story_repository
    ):
        """Test progress for epic with no stories."""
        # Arrange
        mock_story_repository.find_by_epic.return_value = []

        # Act
        progress = await lifecycle_manager.get_epic_progress(epic=1)

        # Assert
        assert progress["epic"] == 1
        assert progress["total_stories"] == 0
        assert progress["completed_stories"] == 0
        assert progress["completion_percentage"] == 0

    async def test_get_epic_progress_partial_completion(
        self, lifecycle_manager, mock_story_repository
    ):
        """Test progress for epic with partial completion."""
        # Arrange
        stories = [
            Story(
                id=StoryIdentifier(1, 1),
                title="Story 1",
                status=StoryStatus.DONE,
                file_path=StoryIdentifier(1, 1).to_path()
            ),
            Story(
                id=StoryIdentifier(1, 2),
                title="Story 2",
                status=StoryStatus.IN_PROGRESS,
                file_path=StoryIdentifier(1, 2).to_path()
            ),
            Story(
                id=StoryIdentifier(1, 3),
                title="Story 3",
                status=StoryStatus.TODO,
                file_path=StoryIdentifier(1, 3).to_path()
            ),
        ]
        mock_story_repository.find_by_epic.return_value = stories

        # Act
        progress = await lifecycle_manager.get_epic_progress(epic=1)

        # Assert
        assert progress["total_stories"] == 3
        assert progress["completed_stories"] == 1
        assert progress["in_progress_stories"] == 1
        assert progress["completion_percentage"] == 33  # 1/3 * 100

    async def test_get_epic_progress_all_complete(
        self, lifecycle_manager, mock_story_repository, mock_event_bus
    ):
        """Test progress for fully completed epic (publishes EpicCompleted event)."""
        # Arrange
        stories = [
            Story(
                id=StoryIdentifier(1, 1),
                title="Story 1",
                status=StoryStatus.DONE,
                file_path=StoryIdentifier(1, 1).to_path()
            ),
            Story(
                id=StoryIdentifier(1, 2),
                title="Story 2",
                status=StoryStatus.DONE,
                file_path=StoryIdentifier(1, 2).to_path()
            ),
        ]
        mock_story_repository.find_by_epic.return_value = stories

        # Act
        progress = await lifecycle_manager.get_epic_progress(epic=1)

        # Assert
        assert progress["total_stories"] == 2
        assert progress["completed_stories"] == 2
        assert progress["completion_percentage"] == 100

        # Verify EpicCompleted event published
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert event.type == "EpicCompleted"
        assert event.data["epic"] == 1
        assert event.data["story_count"] == 2


@pytest.mark.asyncio
class TestQueryMethods:
    """Test query methods for story retrieval."""

    async def test_get_story_found(self, lifecycle_manager, mock_story_repository):
        """Test getting a story that exists."""
        # Arrange
        story_id = StoryIdentifier(1, 1)
        expected_story = Story(
            id=story_id,
            title="Test",
            status=StoryStatus.TODO,
            file_path=story_id.to_path()
        )
        mock_story_repository.find_by_id.return_value = expected_story

        # Act
        story = await lifecycle_manager.get_story(story_id)

        # Assert
        assert story == expected_story
        mock_story_repository.find_by_id.assert_called_once_with("1.1")

    async def test_get_story_not_found(self, lifecycle_manager, mock_story_repository):
        """Test getting a story that doesn't exist."""
        # Arrange
        story_id = StoryIdentifier(1, 1)
        mock_story_repository.find_by_id.return_value = None

        # Act
        story = await lifecycle_manager.get_story(story_id)

        # Assert
        assert story is None

    async def test_list_stories_by_status(self, lifecycle_manager, mock_story_repository):
        """Test listing stories filtered by status."""
        # Arrange
        in_progress_stories = [
            Story(
                id=StoryIdentifier(1, 1),
                title="Story 1",
                status=StoryStatus.IN_PROGRESS,
                file_path=StoryIdentifier(1, 1).to_path()
            ),
            Story(
                id=StoryIdentifier(2, 1),
                title="Story 2",
                status=StoryStatus.IN_PROGRESS,
                file_path=StoryIdentifier(2, 1).to_path()
            ),
        ]
        mock_story_repository.find_by_status.return_value = in_progress_stories

        # Act
        stories = await lifecycle_manager.list_stories_by_status(StoryStatus.IN_PROGRESS)

        # Assert
        assert len(stories) == 2
        assert all(s.status == StoryStatus.IN_PROGRESS for s in stories)
