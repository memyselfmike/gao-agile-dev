"""Workflow metrics tracking.

This module provides the WorkflowTracker class for tracking workflow metrics
during benchmark execution, including story lifecycle, phase timing, and
rework tracking.
"""

import time
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, field

from .collector import MetricsCollector


@dataclass
class StoryMetrics:
    """Metrics for a single story.

    Attributes:
        story_id: Unique identifier for the story
        start_time: Unix timestamp when story started
        end_time: Unix timestamp when story completed (None if in progress)
        phase_times: Dictionary mapping phase names to elapsed times
        rework_count: Number of times story required rework
        completed: Whether story has been completed
    """

    story_id: str
    start_time: float
    end_time: Optional[float] = None
    phase_times: Dict[str, float] = field(default_factory=dict)
    rework_count: int = 0
    completed: bool = False


class WorkflowTracker:
    """
    Tracks workflow metrics during benchmark execution.

    This class wraps MetricsCollector to provide high-level workflow tracking
    including story lifecycle management, phase timing, cycle time calculation,
    and rework tracking.

    Example:
        tracker = WorkflowTracker()

        # Track story lifecycle
        tracker.start_story("story_3_1")
        # ... work on story ...
        tracker.complete_story("story_3_1")

        # Track phase timing
        tracker.start_phase("planning")
        # ... planning work ...
        tracker.end_phase("planning")

        # Record rework
        tracker.record_rework("story_3_2", "Failed acceptance criteria")

        # Get summary
        summary = tracker.get_workflow_summary()
    """

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """
        Initialize workflow tracker.

        Args:
            collector: Optional MetricsCollector instance (creates new if None)
        """
        self.collector = collector or MetricsCollector()
        self.stories: Dict[str, StoryMetrics] = {}
        self.phase_start_times: Dict[str, float] = {}

    def start_story(self, story_id: str) -> None:
        """
        Start tracking a new story.

        Creates a new StoryMetrics object and increments the stories_created
        counter. If a story with this ID already exists, it will be overwritten.

        Args:
            story_id: Unique identifier for the story
        """
        self.stories[story_id] = StoryMetrics(
            story_id=story_id,
            start_time=time.time()
        )
        self.collector.increment_counter("stories_created")

    def complete_story(self, story_id: str) -> None:
        """
        Mark story as completed.

        Records the completion time, calculates cycle time, and updates
        average cycle time. If story doesn't exist, this is a no-op.

        Args:
            story_id: Unique identifier for the story
        """
        if story_id in self.stories:
            story = self.stories[story_id]
            story.end_time = time.time()
            story.completed = True

            # Calculate cycle time
            cycle_time = story.end_time - story.start_time
            self.collector.set_value(f"story_{story_id}_cycle_time", cycle_time)
            self.collector.increment_counter("stories_completed")

            # Update average cycle time
            self._update_average_cycle_time()

    def record_rework(self, story_id: str, reason: str) -> None:
        """
        Record story rework.

        Increments rework counters and records a rework event with the reason.
        If story doesn't exist, this is a no-op.

        Args:
            story_id: Unique identifier for the story
            reason: Description of why rework was needed
        """
        if story_id in self.stories:
            self.stories[story_id].rework_count += 1
            self.collector.increment_counter("rework_total")
            self.collector.record_event("rework", {
                "story_id": story_id,
                "reason": reason
            })

    def start_phase(self, phase_name: str) -> None:
        """
        Start tracking a workflow phase.

        Records the start time for a named phase. Multiple phases can be
        tracked simultaneously.

        Args:
            phase_name: Name of the workflow phase
        """
        self.phase_start_times[phase_name] = time.time()

    def end_phase(self, phase_name: str) -> None:
        """
        End tracking a workflow phase.

        Calculates elapsed time and updates phase distribution. If phase
        was never started, this is a no-op.

        Args:
            phase_name: Name of the workflow phase
        """
        if phase_name in self.phase_start_times:
            elapsed = time.time() - self.phase_start_times[phase_name]
            self.collector.set_value(f"phase_{phase_name}_time", elapsed)
            del self.phase_start_times[phase_name]

            # Update phase distribution
            self._update_phase_distribution()

    def _update_average_cycle_time(self) -> None:
        """
        Calculate and update average cycle time.

        Computes the average cycle time across all completed stories and
        stores it in the collector.
        """
        completed_stories = [s for s in self.stories.values() if s.completed]
        if completed_stories:
            cycle_times = [s.end_time - s.start_time for s in completed_stories]
            avg_cycle_time = sum(cycle_times) / len(cycle_times)
            self.collector.set_value("avg_cycle_time", avg_cycle_time)

    def _update_phase_distribution(self) -> None:
        """
        Calculate phase time distribution.

        Computes the percentage of total time spent in each phase and stores
        the distribution in the collector.
        """
        phase_times = {}
        total_time = 0.0

        for key, value in self.collector.values.items():
            if key.startswith("phase_") and key.endswith("_time"):
                phase_name = key.replace("phase_", "").replace("_time", "")
                phase_times[phase_name] = value
                total_time += value

        if total_time > 0:
            phase_distribution = {
                phase: (time_spent / total_time * 100)
                for phase, time_spent in phase_times.items()
            }
            self.collector.set_value("phase_distribution", phase_distribution)

    def get_workflow_summary(self) -> Dict:
        """
        Get workflow metrics summary.

        Returns a dictionary containing key workflow metrics including story
        counts, cycle times, rework, and phase distribution.

        Returns:
            Dictionary with the following keys:
                - stories_created: Total stories created
                - stories_completed: Total stories completed
                - avg_cycle_time: Average cycle time in seconds
                - rework_count: Total rework count
                - phase_distribution: Dict mapping phase names to percentages
        """
        return {
            "stories_created": self.collector.counters.get("stories_created", 0),
            "stories_completed": self.collector.counters.get("stories_completed", 0),
            "avg_cycle_time": self.collector.values.get("avg_cycle_time", 0.0),
            "rework_count": self.collector.counters.get("rework_total", 0),
            "phase_distribution": self.collector.values.get("phase_distribution", {}),
        }
