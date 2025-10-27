"""Tests for autonomy metrics tracker.

Tests the AutonomyTracker class including intervention tracking, success rates,
agent handoffs, prompt tracking, and autonomy score calculation.
"""

import pytest

from gao_dev.sandbox.metrics.autonomy_tracker import (
    AutonomyTracker,
    InterventionType,
)
from gao_dev.sandbox.metrics.collector import MetricsCollector


@pytest.fixture
def collector():
    """Create a fresh collector for testing."""
    collector = MetricsCollector()
    collector.reset()
    yield collector
    collector.reset()


@pytest.fixture
def tracker(collector):
    """Create a fresh tracker with collector for testing."""
    return AutonomyTracker(collector)


class TestInterventionType:
    """Tests for InterventionType enum."""

    def test_intervention_types_exist(self):
        """Test all intervention types are defined."""
        assert InterventionType.CLARIFICATION.value == "clarification"
        assert InterventionType.ERROR_FIX.value == "error_fix"
        assert InterventionType.DIRECTION_CHANGE.value == "direction_change"
        assert InterventionType.BLOCKED.value == "blocked"
        assert InterventionType.USER_CORRECTION.value == "user_correction"

    def test_intervention_types_are_strings(self):
        """Test intervention type values are strings."""
        for intervention_type in InterventionType:
            assert isinstance(intervention_type.value, str)


class TestAutonomyTracker:
    """Tests for AutonomyTracker class."""

    def test_init_with_collector(self, collector):
        """Test initialization with provided collector."""
        tracker = AutonomyTracker(collector)

        assert tracker.collector is collector
        assert isinstance(tracker.interventions, list)
        assert len(tracker.interventions) == 0

    def test_init_without_collector(self):
        """Test initialization without collector creates one."""
        tracker = AutonomyTracker()

        assert tracker.collector is not None
        assert isinstance(tracker.collector, MetricsCollector)
        assert isinstance(tracker.interventions, list)

    def test_record_intervention(self, tracker):
        """Test recording a manual intervention."""
        tracker.record_intervention(
            InterventionType.CLARIFICATION,
            agent_name="amelia",
            phase="implementation",
            reason="Unclear acceptance criteria",
        )

        # Check counters incremented
        assert tracker.collector.get_counter("interventions_total") == 1
        assert tracker.collector.get_counter("interventions_clarification") == 1

        # Check intervention recorded in list
        assert len(tracker.interventions) == 1
        intervention = tracker.interventions[0]
        assert intervention["type"] == "clarification"
        assert intervention["agent"] == "amelia"
        assert intervention["phase"] == "implementation"
        assert intervention["reason"] == "Unclear acceptance criteria"

        # Check event recorded
        assert len(tracker.collector.events) == 1
        event = tracker.collector.events[0]
        assert event["type"] == "intervention"

    def test_record_multiple_interventions(self, tracker):
        """Test recording multiple interventions."""
        tracker.record_intervention(
            InterventionType.CLARIFICATION,
            agent_name="amelia",
            phase="implementation",
            reason="Unclear criteria",
        )
        tracker.record_intervention(
            InterventionType.ERROR_FIX,
            agent_name="bob",
            phase="planning",
            reason="Bug in story",
        )
        tracker.record_intervention(
            InterventionType.CLARIFICATION,
            agent_name="amelia",
            phase="testing",
            reason="Test requirements unclear",
        )

        # Check total counter
        assert tracker.collector.get_counter("interventions_total") == 3

        # Check type-specific counters
        assert tracker.collector.get_counter("interventions_clarification") == 2
        assert tracker.collector.get_counter("interventions_error_fix") == 1

        # Check interventions list
        assert len(tracker.interventions) == 3

    def test_record_all_intervention_types(self, tracker):
        """Test recording all intervention types."""
        for intervention_type in InterventionType:
            tracker.record_intervention(
                intervention_type,
                agent_name="test_agent",
                phase="test_phase",
                reason=f"Testing {intervention_type.value}",
            )

        # Should have one of each type
        assert tracker.collector.get_counter("interventions_total") == 5
        assert tracker.collector.get_counter("interventions_clarification") == 1
        assert tracker.collector.get_counter("interventions_error_fix") == 1
        assert tracker.collector.get_counter("interventions_direction_change") == 1
        assert tracker.collector.get_counter("interventions_blocked") == 1
        assert tracker.collector.get_counter("interventions_user_correction") == 1

    def test_record_prompt_initial(self, tracker):
        """Test recording initial prompt."""
        tracker.record_prompt(is_initial=True)

        assert tracker.collector.get_counter("prompts_initial") == 1
        assert tracker.collector.get_counter("prompts_followup") == 0

    def test_record_prompt_followup(self, tracker):
        """Test recording follow-up prompt."""
        tracker.record_prompt(is_initial=False)

        assert tracker.collector.get_counter("prompts_initial") == 0
        assert tracker.collector.get_counter("prompts_followup") == 1

    def test_record_multiple_prompts(self, tracker):
        """Test recording multiple prompts."""
        tracker.record_prompt(is_initial=True)
        tracker.record_prompt(is_initial=False)
        tracker.record_prompt(is_initial=False)
        tracker.record_prompt(is_initial=True)

        assert tracker.collector.get_counter("prompts_initial") == 2
        assert tracker.collector.get_counter("prompts_followup") == 2

    def test_record_one_shot_success_true(self, tracker):
        """Test recording successful one-shot attempt."""
        tracker.record_one_shot_success("story_3_1", success=True)

        assert tracker.collector.get_counter("one_shot_successes") == 1
        assert tracker.collector.get_counter("one_shot_failures") == 0

        # Check event recorded
        assert len(tracker.collector.events) == 1
        event = tracker.collector.events[0]
        assert event["type"] == "one_shot_attempt"
        assert event["data"]["task"] == "story_3_1"
        assert event["data"]["success"] is True

    def test_record_one_shot_success_false(self, tracker):
        """Test recording failed one-shot attempt."""
        tracker.record_one_shot_success("story_3_2", success=False)

        assert tracker.collector.get_counter("one_shot_successes") == 0
        assert tracker.collector.get_counter("one_shot_failures") == 1

        # Check event recorded
        event = tracker.collector.events[0]
        assert event["data"]["task"] == "story_3_2"
        assert event["data"]["success"] is False

    def test_record_multiple_one_shot_attempts(self, tracker):
        """Test recording multiple one-shot attempts."""
        tracker.record_one_shot_success("task1", success=True)
        tracker.record_one_shot_success("task2", success=True)
        tracker.record_one_shot_success("task3", success=False)
        tracker.record_one_shot_success("task4", success=True)

        assert tracker.collector.get_counter("one_shot_successes") == 3
        assert tracker.collector.get_counter("one_shot_failures") == 1

    def test_record_error_recovery_recovered(self, tracker):
        """Test recording successful error recovery."""
        tracker.record_error_recovery(recovered=True)

        assert tracker.collector.get_counter("errors_recovered") == 1
        assert tracker.collector.get_counter("errors_unrecovered") == 0

    def test_record_error_recovery_unrecovered(self, tracker):
        """Test recording failed error recovery."""
        tracker.record_error_recovery(recovered=False)

        assert tracker.collector.get_counter("errors_recovered") == 0
        assert tracker.collector.get_counter("errors_unrecovered") == 1

    def test_record_multiple_error_recoveries(self, tracker):
        """Test recording multiple error recoveries."""
        tracker.record_error_recovery(recovered=True)
        tracker.record_error_recovery(recovered=True)
        tracker.record_error_recovery(recovered=False)
        tracker.record_error_recovery(recovered=True)

        assert tracker.collector.get_counter("errors_recovered") == 3
        assert tracker.collector.get_counter("errors_unrecovered") == 1

    def test_record_handoff_successful(self, tracker):
        """Test recording successful agent handoff."""
        tracker.record_handoff("bob", "amelia", success=True)

        assert tracker.collector.get_counter("handoffs_successful") == 1
        assert tracker.collector.get_counter("handoffs_failed") == 0

        # Check event recorded
        assert len(tracker.collector.events) == 1
        event = tracker.collector.events[0]
        assert event["type"] == "handoff"
        assert event["data"]["from"] == "bob"
        assert event["data"]["to"] == "amelia"
        assert event["data"]["success"] is True

    def test_record_handoff_failed(self, tracker):
        """Test recording failed agent handoff."""
        tracker.record_handoff("bob", "amelia", success=False)

        assert tracker.collector.get_counter("handoffs_successful") == 0
        assert tracker.collector.get_counter("handoffs_failed") == 1

        # Check event recorded
        event = tracker.collector.events[0]
        assert event["data"]["success"] is False

    def test_record_multiple_handoffs(self, tracker):
        """Test recording multiple agent handoffs."""
        tracker.record_handoff("bob", "amelia", success=True)
        tracker.record_handoff("amelia", "murat", success=True)
        tracker.record_handoff("murat", "bob", success=False)
        tracker.record_handoff("bob", "winston", success=True)

        assert tracker.collector.get_counter("handoffs_successful") == 3
        assert tracker.collector.get_counter("handoffs_failed") == 1

    def test_calculate_autonomy_score_perfect(self, tracker):
        """Test autonomy score with no interventions or failures."""
        score = tracker.calculate_autonomy_score()

        assert score == 100.0

    def test_calculate_autonomy_score_with_interventions(self, tracker):
        """Test autonomy score with interventions."""
        # Add 2 interventions (each -10 points)
        tracker.record_intervention(
            InterventionType.CLARIFICATION,
            agent_name="amelia",
            phase="implementation",
            reason="Test",
        )
        tracker.record_intervention(
            InterventionType.ERROR_FIX,
            agent_name="bob",
            phase="planning",
            reason="Test",
        )

        score = tracker.calculate_autonomy_score()

        assert score == 80.0  # 100 - (2 * 10)

    def test_calculate_autonomy_score_with_failures(self, tracker):
        """Test autonomy score with failures."""
        # Add 3 failures (each -5 points)
        tracker.record_one_shot_success("task1", success=False)
        tracker.record_one_shot_success("task2", success=False)
        tracker.record_one_shot_success("task3", success=False)

        score = tracker.calculate_autonomy_score()

        assert score == 85.0  # 100 - (3 * 5)

    def test_calculate_autonomy_score_mixed(self, tracker):
        """Test autonomy score with both interventions and failures."""
        # Add 3 interventions (-30 points)
        for _ in range(3):
            tracker.record_intervention(
                InterventionType.CLARIFICATION,
                agent_name="test",
                phase="test",
                reason="test",
            )

        # Add 4 failures (-20 points)
        for _ in range(4):
            tracker.record_one_shot_success("task", success=False)

        score = tracker.calculate_autonomy_score()

        assert score == 50.0  # 100 - 30 - 20

    def test_calculate_autonomy_score_minimum(self, tracker):
        """Test autonomy score never goes below zero."""
        # Add 20 interventions (would be -200 points)
        for i in range(20):
            tracker.record_intervention(
                InterventionType.ERROR_FIX,
                agent_name="test",
                phase="test",
                reason=f"error_{i}",
            )

        score = tracker.calculate_autonomy_score()

        assert score == 0.0  # Should be clamped to 0

    def test_get_intervention_summary_empty(self, tracker):
        """Test intervention summary with no interventions."""
        summary = tracker.get_intervention_summary()

        assert summary["total"] == 0
        assert summary["by_type"] == {}
        assert summary["by_agent"] == {}
        assert summary["by_phase"] == {}
        assert summary["details"] == []

    def test_get_intervention_summary_with_data(self, tracker):
        """Test intervention summary with interventions."""
        tracker.record_intervention(
            InterventionType.CLARIFICATION, "amelia", "implementation", "reason1"
        )
        tracker.record_intervention(
            InterventionType.ERROR_FIX, "bob", "planning", "reason2"
        )
        tracker.record_intervention(
            InterventionType.CLARIFICATION, "amelia", "testing", "reason3"
        )

        summary = tracker.get_intervention_summary()

        assert summary["total"] == 3
        assert summary["by_type"]["clarification"] == 2
        assert summary["by_type"]["error_fix"] == 1
        assert summary["by_agent"]["amelia"] == 2
        assert summary["by_agent"]["bob"] == 1
        assert summary["by_phase"]["implementation"] == 1
        assert summary["by_phase"]["planning"] == 1
        assert summary["by_phase"]["testing"] == 1
        assert len(summary["details"]) == 3

    def test_get_success_rate_no_attempts(self, tracker):
        """Test success rate with no attempts."""
        rate = tracker.get_success_rate()

        assert rate == 0.0

    def test_get_success_rate_all_successes(self, tracker):
        """Test success rate with all successes."""
        tracker.record_one_shot_success("task1", success=True)
        tracker.record_one_shot_success("task2", success=True)
        tracker.record_one_shot_success("task3", success=True)

        rate = tracker.get_success_rate()

        assert rate == 100.0

    def test_get_success_rate_all_failures(self, tracker):
        """Test success rate with all failures."""
        tracker.record_one_shot_success("task1", success=False)
        tracker.record_one_shot_success("task2", success=False)

        rate = tracker.get_success_rate()

        assert rate == 0.0

    def test_get_success_rate_mixed(self, tracker):
        """Test success rate with mixed results."""
        tracker.record_one_shot_success("task1", success=True)
        tracker.record_one_shot_success("task2", success=True)
        tracker.record_one_shot_success("task3", success=True)
        tracker.record_one_shot_success("task4", success=False)

        rate = tracker.get_success_rate()

        assert rate == 75.0  # 3 out of 4 = 75%

    def test_get_error_recovery_rate_no_errors(self, tracker):
        """Test error recovery rate with no errors."""
        rate = tracker.get_error_recovery_rate()

        assert rate == 0.0

    def test_get_error_recovery_rate_all_recovered(self, tracker):
        """Test error recovery rate with all recovered."""
        tracker.record_error_recovery(recovered=True)
        tracker.record_error_recovery(recovered=True)
        tracker.record_error_recovery(recovered=True)

        rate = tracker.get_error_recovery_rate()

        assert rate == 100.0

    def test_get_error_recovery_rate_all_unrecovered(self, tracker):
        """Test error recovery rate with all unrecovered."""
        tracker.record_error_recovery(recovered=False)
        tracker.record_error_recovery(recovered=False)

        rate = tracker.get_error_recovery_rate()

        assert rate == 0.0

    def test_get_error_recovery_rate_mixed(self, tracker):
        """Test error recovery rate with mixed results."""
        tracker.record_error_recovery(recovered=True)
        tracker.record_error_recovery(recovered=True)
        tracker.record_error_recovery(recovered=False)
        tracker.record_error_recovery(recovered=True)

        rate = tracker.get_error_recovery_rate()

        assert rate == 75.0  # 3 out of 4 = 75%

    def test_get_handoff_success_rate_no_handoffs(self, tracker):
        """Test handoff success rate with no handoffs."""
        rate = tracker.get_handoff_success_rate()

        assert rate == 0.0

    def test_get_handoff_success_rate_all_successful(self, tracker):
        """Test handoff success rate with all successful."""
        tracker.record_handoff("bob", "amelia", success=True)
        tracker.record_handoff("amelia", "murat", success=True)
        tracker.record_handoff("murat", "bob", success=True)

        rate = tracker.get_handoff_success_rate()

        assert rate == 100.0

    def test_get_handoff_success_rate_all_failed(self, tracker):
        """Test handoff success rate with all failed."""
        tracker.record_handoff("bob", "amelia", success=False)
        tracker.record_handoff("amelia", "murat", success=False)

        rate = tracker.get_handoff_success_rate()

        assert rate == 0.0

    def test_get_handoff_success_rate_mixed(self, tracker):
        """Test handoff success rate with mixed results."""
        tracker.record_handoff("bob", "amelia", success=True)
        tracker.record_handoff("amelia", "murat", success=True)
        tracker.record_handoff("murat", "bob", success=False)
        tracker.record_handoff("bob", "winston", success=True)
        tracker.record_handoff("winston", "sally", success=False)

        rate = tracker.get_handoff_success_rate()

        assert rate == 60.0  # 3 out of 5 = 60%

    def test_get_prompt_ratio_no_prompts(self, tracker):
        """Test prompt ratio with no prompts."""
        ratio = tracker.get_prompt_ratio()

        assert ratio == 0.0

    def test_get_prompt_ratio_only_initial(self, tracker):
        """Test prompt ratio with only initial prompts."""
        tracker.record_prompt(is_initial=True)
        tracker.record_prompt(is_initial=True)
        tracker.record_prompt(is_initial=True)

        ratio = tracker.get_prompt_ratio()

        assert ratio == 0.0  # No follow-ups

    def test_get_prompt_ratio_equal(self, tracker):
        """Test prompt ratio with equal prompts."""
        tracker.record_prompt(is_initial=True)
        tracker.record_prompt(is_initial=True)
        tracker.record_prompt(is_initial=False)
        tracker.record_prompt(is_initial=False)

        ratio = tracker.get_prompt_ratio()

        assert ratio == 1.0  # 2 follow-ups / 2 initial = 1.0

    def test_get_prompt_ratio_more_followups(self, tracker):
        """Test prompt ratio with more follow-ups."""
        tracker.record_prompt(is_initial=True)
        tracker.record_prompt(is_initial=False)
        tracker.record_prompt(is_initial=False)
        tracker.record_prompt(is_initial=False)

        ratio = tracker.get_prompt_ratio()

        assert ratio == 3.0  # 3 follow-ups / 1 initial = 3.0

    def test_integration_full_workflow(self, tracker):
        """Test full workflow with all tracking methods."""
        # Record prompts
        tracker.record_prompt(is_initial=True)
        tracker.record_prompt(is_initial=False)

        # Record interventions
        tracker.record_intervention(
            InterventionType.CLARIFICATION,
            agent_name="amelia",
            phase="implementation",
            reason="Unclear requirements",
        )

        # Record successes and failures
        tracker.record_one_shot_success("story_1", success=True)
        tracker.record_one_shot_success("story_2", success=False)
        tracker.record_one_shot_success("story_3", success=True)

        # Record error recovery
        tracker.record_error_recovery(recovered=True)
        tracker.record_error_recovery(recovered=False)

        # Record handoffs
        tracker.record_handoff("bob", "amelia", success=True)
        tracker.record_handoff("amelia", "murat", success=True)

        # Check all metrics
        assert tracker.calculate_autonomy_score() == 85.0  # 100 - 10 - 5
        assert tracker.get_success_rate() == pytest.approx(66.67, rel=0.01)
        assert tracker.get_error_recovery_rate() == 50.0
        assert tracker.get_handoff_success_rate() == 100.0
        assert tracker.get_prompt_ratio() == 1.0

        summary = tracker.get_intervention_summary()
        assert summary["total"] == 1
        assert summary["by_agent"]["amelia"] == 1
