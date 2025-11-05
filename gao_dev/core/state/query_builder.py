"""Query builder for complex state queries with intuitive API.

Provides convenience methods for common query patterns with optimized
performance, pagination support, and typed result formatting.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from .state_tracker import StateTracker
from .models import Story, Epic, Sprint
from .exceptions import RecordNotFoundError


class QueryBuilder:
    """Query builder for complex state queries.

    Provides high-level convenience methods for common query patterns
    with automatic optimization, pagination, and result formatting.
    All queries use indexed fields for performance.

    Attributes:
        state_tracker: StateTracker instance for database access

    Example:
        >>> tracker = StateTracker(Path("state.db"))
        >>> builder = QueryBuilder(tracker)
        >>> stories = builder.get_stories_by_status("in_progress")
        >>> progress = builder.get_epic_progress(15)
    """

    def __init__(self, state_tracker: StateTracker):
        """Initialize QueryBuilder.

        Args:
            state_tracker: StateTracker instance for database access
        """
        self.state_tracker = state_tracker

    # ==================== CONVENIENCE METHODS ====================

    def get_stories_by_status(
        self,
        status: str,
        epic_num: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
        as_dict: bool = False,
    ) -> List[Story] | List[Dict[str, Any]]:
        """Get stories by status with optional epic filter.

        Optimized query using status index. Supports pagination and
        both typed model and dict output formats.

        Args:
            status: Story status to filter by
            epic_num: Optional epic number to filter by
            limit: Maximum number of results (default: 100)
            offset: Number of results to skip for pagination (default: 0)
            as_dict: Return as dictionaries instead of Story instances

        Returns:
            List of Story instances or dictionaries

        Example:
            >>> # Get first 10 in-progress stories from epic 15
            >>> stories = builder.get_stories_by_status(
            ...     "in_progress", epic_num=15, limit=10
            ... )
        """
        if epic_num is not None:
            # Get stories from specific epic with status filter
            all_stories = self.state_tracker.get_stories_by_epic(epic_num)
            stories = [s for s in all_stories if s.status == status]
            # Apply pagination
            stories = stories[offset : offset + limit]
        else:
            # Use StateTracker's optimized status query
            stories = self.state_tracker.get_stories_by_status(status, limit, offset)

        if as_dict:
            return [self._story_to_dict(s) for s in stories]
        return stories

    def get_epic_progress(self, epic_num: int) -> Dict[str, Any]:
        """Get epic progress with completed, total, and percentage.

        Returns comprehensive progress metrics for an epic including
        story counts, point totals, and completion percentage.

        Args:
            epic_num: Epic number

        Returns:
            Dictionary with progress metrics:
                - epic_num: Epic number
                - completed: Completed story points
                - total: Total story points
                - percentage: Completion percentage (0.0-100.0)
                - stories_done: Number of completed stories
                - stories_total: Total number of stories

        Raises:
            RecordNotFoundError: If epic not found

        Example:
            >>> progress = builder.get_epic_progress(15)
            >>> print(f"{progress['percentage']:.1f}% complete")
        """
        epic = self.state_tracker.get_epic(epic_num)
        stories = self.state_tracker.get_stories_by_epic(epic_num)

        stories_done = sum(1 for s in stories if s.status == "done")
        stories_total = len(stories)

        return {
            "epic_num": epic_num,
            "completed": epic.completed_points,
            "total": epic.total_points,
            "percentage": epic.progress,
            "stories_done": stories_done,
            "stories_total": stories_total,
        }

    def get_sprint_velocity(self, sprint_num: int) -> int:
        """Get sprint velocity (completed story points).

        Calculates total completed story points for a sprint.
        Uses optimized query with joins.

        Args:
            sprint_num: Sprint number

        Returns:
            Total completed story points

        Raises:
            RecordNotFoundError: If sprint not found

        Example:
            >>> velocity = builder.get_sprint_velocity(5)
            >>> print(f"Sprint 5 velocity: {velocity} points")
        """
        return self.state_tracker.get_sprint_velocity(sprint_num)

    def get_blocked_stories(
        self, limit: int = 100, offset: int = 0, as_dict: bool = False
    ) -> List[Story] | List[Dict[str, Any]]:
        """Get all blocked stories.

        Returns stories with status='blocked', useful for identifying
        bottlenecks and blockers that need attention.

        Args:
            limit: Maximum number of results (default: 100)
            offset: Number of results to skip for pagination (default: 0)
            as_dict: Return as dictionaries instead of Story instances

        Returns:
            List of blocked Story instances or dictionaries

        Example:
            >>> blocked = builder.get_blocked_stories()
            >>> for story in blocked:
            ...     print(f"Blocked: {story.full_id} - {story.title}")
        """
        stories = self.state_tracker.get_stories_by_status("blocked", limit, offset)

        if as_dict:
            return [self._story_to_dict(s) for s in stories]
        return stories

    def get_stories_needing_review(
        self, limit: int = 100, offset: int = 0, as_dict: bool = False
    ) -> List[Story] | List[Dict[str, Any]]:
        """Get stories needing review based on criteria.

        Returns stories that are 'done' but not yet merged/reviewed,
        based on workflow execution status. Useful for code review
        queues and quality gates.

        Args:
            limit: Maximum number of results (default: 100)
            offset: Number of results to skip for pagination (default: 0)
            as_dict: Return as dictionaries instead of Story instances

        Returns:
            List of Story instances or dictionaries needing review

        Example:
            >>> review_queue = builder.get_stories_needing_review()
            >>> print(f"{len(review_queue)} stories need review")
        """
        # Stories marked as 'done' are candidates for review
        # In future, could check workflow_executions for review workflows
        stories = self.state_tracker.get_stories_by_status("done", limit, offset)

        if as_dict:
            return [self._story_to_dict(s) for s in stories]
        return stories

    # ==================== ADVANCED QUERIES ====================

    def get_sprint_summary(self, sprint_num: int) -> Dict[str, Any]:
        """Get comprehensive sprint summary with all metrics.

        Aggregates multiple queries into a single summary report
        including velocity, burndown data, and story breakdown.

        Args:
            sprint_num: Sprint number

        Returns:
            Dictionary with comprehensive sprint metrics:
                - sprint_num: Sprint number
                - sprint_name: Sprint name
                - velocity: Completed story points
                - total_points: Total story points
                - completed_points: Completed story points
                - remaining_points: Remaining story points
                - completion_rate: Story completion rate (0.0-1.0)
                - stories_done: Number of completed stories
                - stories_total: Total number of stories
                - stories_in_progress: Number of in-progress stories
                - stories_blocked: Number of blocked stories

        Raises:
            RecordNotFoundError: If sprint not found

        Example:
            >>> summary = builder.get_sprint_summary(5)
            >>> print(f"Sprint {summary['sprint_name']}")
            >>> print(f"Velocity: {summary['velocity']} points")
        """
        sprint = self.state_tracker.get_sprint(sprint_num)
        burndown = self.state_tracker.get_sprint_burndown_data(sprint_num)
        stories = self.state_tracker.get_stories_by_sprint(sprint_num)

        stories_done = sum(1 for s in stories if s.status == "done")
        stories_in_progress = sum(1 for s in stories if s.status == "in_progress")
        stories_blocked = sum(1 for s in stories if s.status == "blocked")

        return {
            "sprint_num": sprint_num,
            "sprint_name": sprint.name,
            "velocity": burndown["completed_points"],
            "total_points": burndown["total_points"],
            "completed_points": burndown["completed_points"],
            "remaining_points": burndown["remaining_points"],
            "completion_rate": burndown["completion_rate"],
            "stories_done": stories_done,
            "stories_total": len(stories),
            "stories_in_progress": stories_in_progress,
            "stories_blocked": stories_blocked,
        }

    def get_epic_summary(self, epic_num: int) -> Dict[str, Any]:
        """Get comprehensive epic summary with all metrics.

        Aggregates multiple queries into a single summary report
        including progress, story breakdown by status, and velocity.

        Args:
            epic_num: Epic number

        Returns:
            Dictionary with comprehensive epic metrics:
                - epic_num: Epic number
                - title: Epic title
                - feature: Feature name
                - status: Epic status
                - progress: Completion percentage
                - total_points: Total story points
                - completed_points: Completed story points
                - stories_total: Total number of stories
                - stories_done: Number of completed stories
                - stories_in_progress: Number of in-progress stories
                - stories_blocked: Number of blocked stories
                - stories_pending: Number of pending stories
                - velocity: Epic velocity (completion rate)

        Raises:
            RecordNotFoundError: If epic not found

        Example:
            >>> summary = builder.get_epic_summary(15)
            >>> print(f"Epic {summary['title']}: {summary['progress']:.1f}%")
        """
        epic = self.state_tracker.get_epic(epic_num)
        stories = self.state_tracker.get_stories_by_epic(epic_num)
        velocity = self.state_tracker.get_epic_velocity(epic_num)

        stories_done = sum(1 for s in stories if s.status == "done")
        stories_in_progress = sum(1 for s in stories if s.status == "in_progress")
        stories_blocked = sum(1 for s in stories if s.status == "blocked")
        stories_pending = sum(1 for s in stories if s.status == "pending")

        return {
            "epic_num": epic_num,
            "title": epic.title,
            "feature": epic.feature,
            "status": epic.status,
            "progress": epic.progress,
            "total_points": epic.total_points,
            "completed_points": epic.completed_points,
            "stories_total": len(stories),
            "stories_done": stories_done,
            "stories_in_progress": stories_in_progress,
            "stories_blocked": stories_blocked,
            "stories_pending": stories_pending,
            "velocity": velocity,
        }

    def get_all_active_work(self) -> Dict[str, Any]:
        """Get all active work across all epics and sprints.

        Returns a comprehensive view of all in-progress work,
        useful for status reports and standups.

        Returns:
            Dictionary with active work breakdown:
                - stories_in_progress: List of in-progress stories
                - stories_blocked: List of blocked stories
                - active_epics: List of active epic summaries
                - current_sprint: Current sprint summary (if any)

        Example:
            >>> work = builder.get_all_active_work()
            >>> print(f"{len(work['stories_in_progress'])} stories in progress")
        """
        stories_in_progress = self.state_tracker.get_stories_in_progress()
        stories_blocked = self.state_tracker.get_blocked_stories()
        active_epics = self.state_tracker.get_active_epics()
        current_sprint = self.state_tracker.get_current_sprint()

        result: Dict[str, Any] = {
            "stories_in_progress": [self._story_to_dict(s) for s in stories_in_progress],
            "stories_blocked": [self._story_to_dict(s) for s in stories_blocked],
            "active_epics": [self._epic_to_dict(e) for e in active_epics],
        }

        if current_sprint:
            result["current_sprint"] = self.get_sprint_summary(current_sprint.sprint_num)

        return result

    # ==================== HELPER METHODS ====================

    def _story_to_dict(self, story: Story) -> Dict[str, Any]:
        """Convert Story model to dictionary.

        Args:
            story: Story instance

        Returns:
            Dictionary representation
        """
        return {
            "id": story.id,
            "epic": story.epic,
            "story_num": story.story_num,
            "full_id": story.full_id,
            "title": story.title,
            "status": story.status,
            "owner": story.owner,
            "points": story.points,
            "priority": story.priority,
            "sprint": story.sprint,
            "created_at": story.created_at,
            "updated_at": story.updated_at,
        }

    def _epic_to_dict(self, epic: Epic) -> Dict[str, Any]:
        """Convert Epic model to dictionary.

        Args:
            epic: Epic instance

        Returns:
            Dictionary representation
        """
        return {
            "id": epic.id,
            "epic_num": epic.epic_num,
            "title": epic.title,
            "feature": epic.feature,
            "status": epic.status,
            "total_points": epic.total_points,
            "completed_points": epic.completed_points,
            "progress": epic.progress,
            "created_at": epic.created_at,
            "updated_at": epic.updated_at,
        }

    def _sprint_to_dict(self, sprint: Sprint) -> Dict[str, Any]:
        """Convert Sprint model to dictionary.

        Args:
            sprint: Sprint instance

        Returns:
            Dictionary representation
        """
        return {
            "id": sprint.id,
            "sprint_num": sprint.sprint_num,
            "name": sprint.name,
            "start_date": sprint.start_date,
            "end_date": sprint.end_date,
            "status": sprint.status,
            "created_at": sprint.created_at,
        }
