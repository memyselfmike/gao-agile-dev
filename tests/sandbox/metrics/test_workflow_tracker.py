"""Tests for workflow tracker.

Tests the WorkflowTracker class including story lifecycle, phase tracking,
cycle time calculation, rework tracking, and summary generation.
"""

import pytest
import time

from gao_dev.sandbox.metrics.collector import MetricsCollector
from gao_dev.sandbox.metrics.workflow_tracker import WorkflowTracker, StoryMetrics


@pytest.fixture
def collector():
    """Create a fresh collector for testing."""
    collector = MetricsCollector()
    collector.reset()
    yield collector
    collector.reset()


@pytest.fixture
def tracker(collector):
    """Create a workflow tracker with fresh collector."""
    return WorkflowTracker(collector=collector)


class TestStoryMetrics:
    """Tests for StoryMetrics dataclass."""

    def test_story_metrics_creation(self):
        """Test creating StoryMetrics instance."""
        story = StoryMetrics(story_id="test_story", start_time=time.time())

        assert story.story_id == "test_story"
        assert story.start_time > 0
        assert story.end_time is None
        assert story.phase_times == {}
        assert story.rework_count == 0
        assert story.completed is False

    def test_story_metrics_with_completion(self):
        """Test StoryMetrics with completion data."""
        start = time.time()
        end = start + 10.5

        story = StoryMetrics(
            story_id="completed_story",
            start_time=start,
            end_time=end,
            completed=True
        )

        assert story.end_time == end
        assert story.completed is True
        assert end - start == 10.5

    def test_story_metrics_with_rework(self):
        """Test StoryMetrics with rework count."""
        story = StoryMetrics(
            story_id="rework_story",
            start_time=time.time(),
            rework_count=3
        )

        assert story.rework_count == 3


class TestWorkflowTracker:
    """Tests for WorkflowTracker class."""

    def test_tracker_initialization(self, tracker, collector):
        """Test tracker initializes correctly."""
        assert tracker.collector is collector
        assert tracker.stories == {}
        assert tracker.phase_start_times == {}

    def test_tracker_default_collector(self):
        """Test tracker creates default collector."""
        tracker = WorkflowTracker()

        assert tracker.collector is not None
        assert isinstance(tracker.collector, MetricsCollector)

    def test_start_story(self, tracker):
        """Test starting a new story."""
        tracker.start_story("story_1")

        assert "story_1" in tracker.stories
        story = tracker.stories["story_1"]
        assert story.story_id == "story_1"
        assert story.start_time > 0
        assert story.completed is False
        assert tracker.collector.get_counter("stories_created") == 1

    def test_start_multiple_stories(self, tracker):
        """Test starting multiple stories."""
        tracker.start_story("story_1")
        tracker.start_story("story_2")
        tracker.start_story("story_3")

        assert len(tracker.stories) == 3
        assert tracker.collector.get_counter("stories_created") == 3

    def test_complete_story(self, tracker):
        """Test completing a story."""
        tracker.start_story("story_1")
        time.sleep(0.05)  # Small delay
        tracker.complete_story("story_1")

        story = tracker.stories["story_1"]
        assert story.completed is True
        assert story.end_time is not None
        assert story.end_time > story.start_time

        # Check counters and values
        assert tracker.collector.get_counter("stories_completed") == 1
        cycle_time = tracker.collector.get_value("story_story_1_cycle_time")
        assert cycle_time >= 0.05

    def test_complete_nonexistent_story(self, tracker):
        """Test completing story that doesn't exist."""
        # Should not raise an error
        tracker.complete_story("nonexistent_story")

        assert tracker.collector.get_counter("stories_completed") == 0

    def test_cycle_time_calculation(self, tracker):
        """Test cycle time is calculated correctly."""
        tracker.start_story("timed_story")
        start_time = tracker.stories["timed_story"].start_time

        time.sleep(0.1)  # Sleep for 100ms
        tracker.complete_story("timed_story")

        end_time = tracker.stories["timed_story"].end_time
        cycle_time = end_time - start_time

        assert cycle_time >= 0.1
        assert cycle_time < 0.2  # Should not be too long

        stored_cycle_time = tracker.collector.get_value("story_timed_story_cycle_time")
        assert abs(stored_cycle_time - cycle_time) < 0.001

    def test_average_cycle_time(self, tracker):
        """Test average cycle time calculation."""
        # Create and complete multiple stories with different cycle times
        tracker.start_story("story_1")
        time.sleep(0.05)
        tracker.complete_story("story_1")

        tracker.start_story("story_2")
        time.sleep(0.1)
        tracker.complete_story("story_2")

        tracker.start_story("story_3")
        time.sleep(0.05)
        tracker.complete_story("story_3")

        avg_cycle_time = tracker.collector.get_value("avg_cycle_time")
        assert avg_cycle_time is not None
        assert avg_cycle_time > 0

        # Calculate expected average manually
        cycle_times = []
        for story in tracker.stories.values():
            if story.completed:
                cycle_times.append(story.end_time - story.start_time)

        expected_avg = sum(cycle_times) / len(cycle_times)
        assert abs(avg_cycle_time - expected_avg) < 0.001

    def test_average_cycle_time_single_story(self, tracker):
        """Test average cycle time with single story."""
        tracker.start_story("single_story")
        time.sleep(0.05)
        tracker.complete_story("single_story")

        avg_cycle_time = tracker.collector.get_value("avg_cycle_time")
        cycle_time = tracker.collector.get_value("story_single_story_cycle_time")

        assert avg_cycle_time == cycle_time

    def test_record_rework(self, tracker):
        """Test recording rework."""
        tracker.start_story("story_with_rework")

        tracker.record_rework("story_with_rework", "Failed tests")

        story = tracker.stories["story_with_rework"]
        assert story.rework_count == 1
        assert tracker.collector.get_counter("rework_total") == 1

        # Check event was recorded
        events = tracker.collector.events
        assert len(events) == 1
        assert events[0]["type"] == "rework"
        assert events[0]["data"]["story_id"] == "story_with_rework"
        assert events[0]["data"]["reason"] == "Failed tests"

    def test_record_multiple_rework(self, tracker):
        """Test recording multiple rework instances."""
        tracker.start_story("story_1")
        tracker.record_rework("story_1", "Failed acceptance criteria")
        tracker.record_rework("story_1", "Failed review")

        tracker.start_story("story_2")
        tracker.record_rework("story_2", "Failed tests")

        assert tracker.stories["story_1"].rework_count == 2
        assert tracker.stories["story_2"].rework_count == 1
        assert tracker.collector.get_counter("rework_total") == 3
        assert len(tracker.collector.events) == 3

    def test_record_rework_nonexistent_story(self, tracker):
        """Test recording rework for nonexistent story."""
        # Should not raise an error
        tracker.record_rework("nonexistent_story", "Some reason")

        assert tracker.collector.get_counter("rework_total") == 0

    def test_start_phase(self, tracker):
        """Test starting a phase."""
        tracker.start_phase("planning")

        assert "planning" in tracker.phase_start_times
        assert tracker.phase_start_times["planning"] > 0

    def test_end_phase(self, tracker):
        """Test ending a phase."""
        tracker.start_phase("planning")
        time.sleep(0.05)
        tracker.end_phase("planning")

        # Phase should be removed from start times
        assert "planning" not in tracker.phase_start_times

        # Phase time should be recorded
        phase_time = tracker.collector.get_value("phase_planning_time")
        assert phase_time >= 0.05

    def test_end_phase_nonexistent(self, tracker):
        """Test ending phase that was never started."""
        # Should not raise an error
        tracker.end_phase("never_started")

        assert tracker.collector.get_value("phase_never_started_time") is None

    def test_multiple_phases(self, tracker):
        """Test tracking multiple phases."""
        tracker.start_phase("planning")
        time.sleep(0.05)
        tracker.start_phase("implementation")
        time.sleep(0.05)
        tracker.end_phase("planning")
        time.sleep(0.05)
        tracker.end_phase("implementation")

        planning_time = tracker.collector.get_value("phase_planning_time")
        implementation_time = tracker.collector.get_value("phase_implementation_time")

        assert planning_time >= 0.10  # ~100ms
        assert implementation_time >= 0.10  # ~100ms

    def test_phase_distribution(self, tracker):
        """Test phase distribution calculation."""
        tracker.start_phase("planning")
        time.sleep(0.1)
        tracker.end_phase("planning")

        tracker.start_phase("implementation")
        time.sleep(0.1)
        tracker.end_phase("implementation")

        tracker.start_phase("testing")
        time.sleep(0.2)
        tracker.end_phase("testing")

        distribution = tracker.collector.get_value("phase_distribution")
        assert distribution is not None
        assert "planning" in distribution
        assert "implementation" in distribution
        assert "testing" in distribution

        # Total should be 100%
        total_percent = sum(distribution.values())
        assert abs(total_percent - 100.0) < 0.1

        # Testing should have highest percentage (took longest)
        assert distribution["testing"] > distribution["planning"]
        assert distribution["testing"] > distribution["implementation"]

    def test_phase_distribution_equal_times(self, tracker):
        """Test phase distribution with equal times."""
        sleep_time = 0.05

        tracker.start_phase("phase1")
        time.sleep(sleep_time)
        tracker.end_phase("phase1")

        tracker.start_phase("phase2")
        time.sleep(sleep_time)
        tracker.end_phase("phase2")

        distribution = tracker.collector.get_value("phase_distribution")
        assert distribution is not None

        # Each phase should be approximately 50%
        assert abs(distribution["phase1"] - 50.0) < 5.0
        assert abs(distribution["phase2"] - 50.0) < 5.0

    def test_phase_distribution_empty(self, tracker):
        """Test phase distribution with no phases."""
        distribution = tracker.collector.get_value("phase_distribution")
        assert distribution is None or distribution == {}

    def test_get_workflow_summary_empty(self, tracker):
        """Test workflow summary with no data."""
        summary = tracker.get_workflow_summary()

        assert summary["stories_created"] == 0
        assert summary["stories_completed"] == 0
        assert summary["avg_cycle_time"] == 0.0
        assert summary["rework_count"] == 0
        assert summary["phase_distribution"] == {}

    def test_get_workflow_summary_with_data(self, tracker):
        """Test workflow summary with complete data."""
        # Create and complete stories
        tracker.start_story("story_1")
        time.sleep(0.05)
        tracker.complete_story("story_1")

        tracker.start_story("story_2")
        tracker.record_rework("story_2", "Failed tests")
        time.sleep(0.05)
        tracker.complete_story("story_2")

        # Track phases
        tracker.start_phase("planning")
        time.sleep(0.05)
        tracker.end_phase("planning")

        tracker.start_phase("implementation")
        time.sleep(0.05)
        tracker.end_phase("implementation")

        summary = tracker.get_workflow_summary()

        assert summary["stories_created"] == 2
        assert summary["stories_completed"] == 2
        assert summary["avg_cycle_time"] > 0
        assert summary["rework_count"] == 1
        assert len(summary["phase_distribution"]) == 2

    def test_workflow_summary_structure(self, tracker):
        """Test workflow summary has correct structure."""
        summary = tracker.get_workflow_summary()

        # Check all required keys exist
        assert "stories_created" in summary
        assert "stories_completed" in summary
        assert "avg_cycle_time" in summary
        assert "rework_count" in summary
        assert "phase_distribution" in summary

        # Check types
        assert isinstance(summary["stories_created"], int)
        assert isinstance(summary["stories_completed"], int)
        assert isinstance(summary["avg_cycle_time"], (int, float))
        assert isinstance(summary["rework_count"], int)
        assert isinstance(summary["phase_distribution"], dict)

    def test_stories_in_progress(self, tracker):
        """Test stories that are started but not completed."""
        tracker.start_story("story_1")
        tracker.start_story("story_2")
        tracker.complete_story("story_1")

        summary = tracker.get_workflow_summary()

        assert summary["stories_created"] == 2
        assert summary["stories_completed"] == 1

        # Story 2 should still be in progress
        assert not tracker.stories["story_2"].completed

    def test_story_overwrite(self, tracker):
        """Test that starting same story ID overwrites."""
        tracker.start_story("story_1")
        first_start_time = tracker.stories["story_1"].start_time

        time.sleep(0.05)

        tracker.start_story("story_1")
        second_start_time = tracker.stories["story_1"].start_time

        assert second_start_time > first_start_time
        assert tracker.collector.get_counter("stories_created") == 2

    def test_rework_impact_on_cycle_time(self, tracker):
        """Test that rework doesn't affect cycle time calculation."""
        tracker.start_story("story_with_rework")
        start_time = tracker.stories["story_with_rework"].start_time

        time.sleep(0.05)
        tracker.record_rework("story_with_rework", "Failed review")
        time.sleep(0.05)

        tracker.complete_story("story_with_rework")
        end_time = tracker.stories["story_with_rework"].end_time

        cycle_time = end_time - start_time
        stored_cycle_time = tracker.collector.get_value("story_story_with_rework_cycle_time")

        # Cycle time should include all time from start to complete
        assert abs(stored_cycle_time - cycle_time) < 0.001
        assert stored_cycle_time >= 0.1

    def test_concurrent_phases(self, tracker):
        """Test multiple phases running simultaneously."""
        tracker.start_phase("phase1")
        time.sleep(0.05)
        tracker.start_phase("phase2")
        time.sleep(0.05)
        tracker.end_phase("phase1")
        time.sleep(0.05)
        tracker.end_phase("phase2")

        phase1_time = tracker.collector.get_value("phase_phase1_time")
        phase2_time = tracker.collector.get_value("phase_phase2_time")

        # Both phases should have run for at least 100ms
        assert phase1_time >= 0.1  # phase1 ran for ~100ms
        assert phase2_time >= 0.1  # phase2 ran for ~100ms
        # Note: We don't assert which is longer due to timing variability

    def test_integration_full_workflow(self, tracker):
        """Test complete workflow scenario."""
        # Start benchmark
        tracker.collector.start_collection("test-project", "test-benchmark")

        # Planning phase
        tracker.start_phase("planning")
        tracker.start_story("story_1")
        time.sleep(0.05)
        tracker.end_phase("planning")

        # Implementation phase
        tracker.start_phase("implementation")
        time.sleep(0.05)
        tracker.complete_story("story_1")
        tracker.end_phase("implementation")

        # Story with rework
        tracker.start_phase("planning")
        tracker.start_story("story_2")
        time.sleep(0.05)
        tracker.end_phase("planning")

        tracker.start_phase("implementation")
        time.sleep(0.05)
        tracker.record_rework("story_2", "Failed tests")
        time.sleep(0.05)
        tracker.complete_story("story_2")
        tracker.end_phase("implementation")

        # Get summary
        summary = tracker.get_workflow_summary()

        assert summary["stories_created"] == 2
        assert summary["stories_completed"] == 2
        assert summary["rework_count"] == 1
        assert summary["avg_cycle_time"] > 0
        assert "planning" in summary["phase_distribution"]
        assert "implementation" in summary["phase_distribution"]

        # Stop collection
        metrics = tracker.collector.stop_collection()
        assert metrics.project_name == "test-project"
