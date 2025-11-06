"""
Data models for workflow context.

This module provides data models used by WorkflowContext for tracking
workflow execution state, transitions, and history.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PhaseTransition:
    """
    Record of phase transition in workflow execution.

    Tracks when a workflow moves from one phase to another, including
    duration spent in the previous phase.

    Attributes:
        phase: Name of the phase being exited
        timestamp: ISO 8601 timestamp of transition
        duration: Duration spent in phase (seconds), None for first transition
    """

    phase: str
    timestamp: str
    duration: Optional[float] = None  # seconds

    def __repr__(self) -> str:
        """String representation of phase transition."""
        if self.duration is not None:
            return f"PhaseTransition(phase={self.phase}, duration={self.duration:.2f}s)"
        return f"PhaseTransition(phase={self.phase})"
