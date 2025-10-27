"""Autonomy metrics tracking.

This module provides the AutonomyTracker class for tracking manual interventions,
success rates, agent handoffs, and calculating overall autonomy scores during
benchmark execution.
"""

from typing import Optional, List, Dict, Any
from enum import Enum

from .collector import MetricsCollector


class InterventionType(Enum):
    """Types of manual interventions that can occur during benchmark execution.

    Attributes:
        CLARIFICATION: User needed to clarify requirements or instructions
        ERROR_FIX: User needed to fix an error or bug
        DIRECTION_CHANGE: User changed the direction or approach
        BLOCKED: Agent was blocked and needed user help to proceed
        USER_CORRECTION: User corrected agent's work or output
    """

    CLARIFICATION = "clarification"
    ERROR_FIX = "error_fix"
    DIRECTION_CHANGE = "direction_change"
    BLOCKED = "blocked"
    USER_CORRECTION = "user_correction"


class AutonomyTracker:
    """
    Tracks autonomy metrics during benchmark execution.

    Wraps a MetricsCollector to provide specialized methods for tracking
    manual interventions, success rates, agent handoffs, and prompts.
    Calculates an overall autonomy score based on collected metrics.

    Example:
        tracker = AutonomyTracker()

        # Record intervention
        tracker.record_intervention(
            InterventionType.CLARIFICATION,
            agent_name="amelia",
            phase="implementation",
            reason="Unclear acceptance criteria"
        )

        # Record prompt
        tracker.record_prompt(is_initial=True)

        # Record success
        tracker.record_one_shot_success("story_3_1", success=True)

        # Calculate autonomy
        score = tracker.calculate_autonomy_score()
    """

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """Initialize autonomy tracker.

        Args:
            collector: Optional MetricsCollector instance. If not provided,
                      creates a new collector instance (singleton).
        """
        self.collector = collector or MetricsCollector()
        self.interventions: List[Dict[str, Any]] = []

    def record_intervention(
        self,
        intervention_type: InterventionType,
        agent_name: str,
        phase: str,
        reason: str,
    ) -> None:
        """Record a manual intervention.

        Tracks when a user needs to manually intervene during autonomous
        execution. Increments overall intervention counter and type-specific
        counter, stores intervention details, and records an event.

        Args:
            intervention_type: Type of intervention from InterventionType enum
            agent_name: Name of the agent that needed intervention
            phase: Development phase where intervention occurred
            reason: Human-readable reason for the intervention
        """
        self.collector.increment_counter("interventions_total")
        self.collector.increment_counter(f"interventions_{intervention_type.value}")

        intervention = {
            "type": intervention_type.value,
            "agent": agent_name,
            "phase": phase,
            "reason": reason,
        }
        self.interventions.append(intervention)
        self.collector.record_event("intervention", intervention)

    def record_prompt(self, is_initial: bool = True) -> None:
        """Record user prompt.

        Tracks initial prompts (starting a new task) versus follow-up prompts
        (providing additional guidance or corrections).

        Args:
            is_initial: True for initial prompt, False for follow-up prompt
        """
        if is_initial:
            self.collector.increment_counter("prompts_initial")
        else:
            self.collector.increment_counter("prompts_followup")

    def record_one_shot_success(self, task_name: str, success: bool) -> None:
        """Record whether task succeeded on first attempt.

        Tracks "one-shot success rate" - the percentage of tasks completed
        correctly on the first attempt without requiring rework or corrections.

        Args:
            task_name: Name/identifier of the task attempted
            success: True if succeeded on first try, False if needed rework
        """
        key = "one_shot_successes" if success else "one_shot_failures"
        self.collector.increment_counter(key)
        self.collector.record_event(
            "one_shot_attempt", {"task": task_name, "success": success}
        )

    def record_error_recovery(self, recovered: bool) -> None:
        """Record error recovery attempt.

        Tracks whether the system was able to automatically recover from
        an error or if manual intervention was required.

        Args:
            recovered: True if error was automatically recovered,
                      False if manual intervention needed
        """
        key = "errors_recovered" if recovered else "errors_unrecovered"
        self.collector.increment_counter(key)

    def record_handoff(self, from_agent: str, to_agent: str, success: bool) -> None:
        """Record agent handoff.

        Tracks transitions between agents in multi-agent workflows. Successful
        handoffs indicate proper context transfer; failed handoffs indicate
        communication breakdowns.

        Args:
            from_agent: Name of the agent handing off work
            to_agent: Name of the agent receiving work
            success: True if handoff successful, False if handoff failed
        """
        key = "handoffs_successful" if success else "handoffs_failed"
        self.collector.increment_counter(key)

        self.collector.record_event(
            "handoff", {"from": from_agent, "to": to_agent, "success": success}
        )

    def calculate_autonomy_score(self) -> float:
        """Calculate overall autonomy score (0-100).

        Computes a simple autonomy score based on interventions and failures.
        Higher scores indicate better autonomous performance with less manual
        intervention required.

        Formula:
            score = 100 - (interventions * 10) - (failures * 5)
            score = max(0, score)

        Returns:
            Autonomy score from 0 to 100, where:
            - 100 = Perfect autonomy, no interventions or failures
            - 0 = Poor autonomy, many interventions or failures
        """
        interventions = self.collector.get_counter("interventions_total", 0)
        failures = self.collector.get_counter("one_shot_failures", 0)
        score = max(0.0, 100.0 - (interventions * 10) - (failures * 5))
        return score

    def get_intervention_summary(self) -> Dict[str, Any]:
        """Get summary of all recorded interventions.

        Returns:
            Dictionary containing:
            - total: Total number of interventions
            - by_type: Count of each intervention type
            - by_agent: Count of interventions per agent
            - by_phase: Count of interventions per phase
            - details: List of all intervention records
        """
        by_type: Dict[str, int] = {}
        by_agent: Dict[str, int] = {}
        by_phase: Dict[str, int] = {}

        for intervention in self.interventions:
            # Count by type
            itype = intervention["type"]
            by_type[itype] = by_type.get(itype, 0) + 1

            # Count by agent
            agent = intervention["agent"]
            by_agent[agent] = by_agent.get(agent, 0) + 1

            # Count by phase
            phase = intervention["phase"]
            by_phase[phase] = by_phase.get(phase, 0) + 1

        return {
            "total": len(self.interventions),
            "by_type": by_type,
            "by_agent": by_agent,
            "by_phase": by_phase,
            "details": self.interventions,
        }

    def get_success_rate(self) -> float:
        """Calculate one-shot success rate.

        Computes the percentage of tasks that succeeded on the first attempt
        without requiring rework.

        Returns:
            Success rate as a percentage (0.0 to 100.0), or 0.0 if no attempts
        """
        successes = self.collector.get_counter("one_shot_successes", 0)
        failures = self.collector.get_counter("one_shot_failures", 0)
        total = successes + failures

        if total == 0:
            return 0.0

        return (successes / total) * 100.0

    def get_error_recovery_rate(self) -> float:
        """Calculate error recovery rate.

        Computes the percentage of errors that were automatically recovered
        without manual intervention.

        Returns:
            Recovery rate as a percentage (0.0 to 100.0), or 0.0 if no errors
        """
        recovered = self.collector.get_counter("errors_recovered", 0)
        unrecovered = self.collector.get_counter("errors_unrecovered", 0)
        total = recovered + unrecovered

        if total == 0:
            return 0.0

        return (recovered / total) * 100.0

    def get_handoff_success_rate(self) -> float:
        """Calculate agent handoff success rate.

        Computes the percentage of agent handoffs that were successful.

        Returns:
            Handoff success rate as a percentage (0.0 to 100.0), or 0.0 if no handoffs
        """
        successful = self.collector.get_counter("handoffs_successful", 0)
        failed = self.collector.get_counter("handoffs_failed", 0)
        total = successful + failed

        if total == 0:
            return 0.0

        return (successful / total) * 100.0

    def get_prompt_ratio(self) -> float:
        """Calculate follow-up to initial prompt ratio.

        Computes the ratio of follow-up prompts to initial prompts. Lower
        ratios indicate better autonomy (fewer follow-ups needed).

        Returns:
            Ratio of follow-up prompts to initial prompts, or 0.0 if no initial prompts
        """
        initial = self.collector.get_counter("prompts_initial", 0)
        followup = self.collector.get_counter("prompts_followup", 0)

        if initial == 0:
            return 0.0

        return followup / initial
