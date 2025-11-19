"""Result types for startup orchestration.

This module defines result types for the StartupOrchestrator, including
startup phases, results, and exceptions.

Epic 40: Streamlined Onboarding
Story 40.3: StartupOrchestrator Implementation
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class StartupPhase(str, Enum):
    """Phases of the startup process."""

    DETECTION = "detection"
    DECISION = "decision"
    ONBOARDING = "onboarding"
    VALIDATION = "validation"
    INITIALIZATION = "initialization"
    LAUNCH = "launch"
    COMPLETE = "complete"


class WizardType(str, Enum):
    """Types of onboarding wizards."""

    WEB = "web"
    TUI = "tui"
    NONE = "none"


class OnboardingMode(str, Enum):
    """Onboarding mode based on user state."""

    FULL = "full"
    ABBREVIATED = "abbreviated"
    SKIP = "skip"


@dataclass
class PhaseResult:
    """Result of a single startup phase.

    Attributes:
        phase: The phase that was executed
        success: Whether the phase completed successfully
        duration_ms: Time taken to complete the phase in milliseconds
        message: Human-readable status message
        details: Additional details about the phase result
    """

    phase: StartupPhase
    success: bool
    duration_ms: float
    message: str = ""
    details: Dict[str, str] = field(default_factory=dict)


@dataclass
class StartupResult:
    """Result of the complete startup process.

    Attributes:
        success: Whether startup completed successfully
        wizard_type: The wizard type that was selected
        onboarding_mode: The onboarding mode that was used
        interface_launched: Type of interface launched ('web' or 'cli')
        project_path: Path to the project directory
        total_duration_ms: Total time taken for startup in milliseconds
        phases: Results of each phase
        error: Error message if startup failed
        timestamp: When startup was initiated
    """

    success: bool
    wizard_type: WizardType
    onboarding_mode: OnboardingMode
    interface_launched: str
    project_path: Path
    total_duration_ms: float
    phases: List[PhaseResult] = field(default_factory=list)
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def add_phase(self, phase_result: PhaseResult) -> None:
        """Add a phase result.

        Args:
            phase_result: The phase result to add
        """
        self.phases.append(phase_result)

    def get_phase(self, phase: StartupPhase) -> Optional[PhaseResult]:
        """Get result for a specific phase.

        Args:
            phase: The phase to get result for

        Returns:
            PhaseResult if found, None otherwise
        """
        for p in self.phases:
            if p.phase == phase:
                return p
        return None


class StartupError(Exception):
    """Exception raised when startup fails.

    Attributes:
        phase: The phase where failure occurred
        message: Error message
        suggestions: List of actionable suggestions to fix the issue
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        phase: Optional[StartupPhase] = None,
        suggestions: Optional[List[str]] = None,
        details: Optional[Dict[str, str]] = None,
    ):
        """Initialize StartupError.

        Args:
            message: Error message
            phase: The phase where failure occurred
            suggestions: List of actionable suggestions
            details: Additional error details
        """
        super().__init__(message)
        self.phase = phase
        self.suggestions = suggestions or []
        self.details = details or {}
