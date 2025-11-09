"""Ceremony failure handling with circuit breaker pattern.

This service handles ceremony failures with configurable policies to prevent
workflow hangs and provide appropriate escalation.

Epic: 28 - Ceremony-Driven Workflow Integration
Story: 28.4 - Orchestrator Integration with Atomic Ceremonies

Implements C9 Fix: Ceremony failure handling
- ABORT: Stop workflow execution (planning ceremonies)
- RETRY: Retry ceremony up to 3 times (retrospectives)
- CONTINUE: Log error, continue workflow (standups)
- SKIP: Skip ceremony after circuit breaker triggered

Design Pattern: Service Layer with Circuit Breaker
Dependencies: structlog
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict

from structlog import get_logger

logger = get_logger(__name__)


class CeremonyFailurePolicy(Enum):
    """Failure handling policies for ceremonies."""
    ABORT = "abort"        # Stop workflow execution, escalate to user
    RETRY = "retry"        # Retry ceremony up to max_retries times
    CONTINUE = "continue"  # Log error, continue workflow without ceremony
    SKIP = "skip"          # Skip ceremony (circuit breaker triggered)


@dataclass
class FailureConfig:
    """Configuration for ceremony failure handling."""
    policy: CeremonyFailurePolicy
    max_retries: int = 3
    retry_delay_seconds: int = 5
    circuit_breaker_threshold: int = 3


class CeremonyFailureHandler:
    """
    Handle ceremony failures with configurable policies.

    Implements C9 Fix: Ceremony failure handling with circuit breaker pattern.

    Failure Policies:
    - Planning: ABORT (critical ceremony - workflow cannot proceed)
    - Standup: CONTINUE (optional - log and continue)
    - Retrospective: RETRY (try to save learnings - 3 attempts)

    Circuit Breaker:
    - Tracks consecutive failures per (epic_num, ceremony_type)
    - Opens circuit after 3 consecutive failures
    - When open, returns SKIP policy to prevent resource waste
    - Resets on successful ceremony execution

    Example:
        ```python
        handler = CeremonyFailureHandler()

        # Handle failure
        policy = handler.handle_failure(
            ceremony_type="planning",
            epic_num=1,
            error=Exception("Planning failed")
        )
        # Returns: ABORT (planning is critical)

        # Reset on success
        handler.reset_failures("planning", 1)
        ```
    """

    FAILURE_POLICIES = {
        "planning": FailureConfig(
            policy=CeremonyFailurePolicy.ABORT,
            max_retries=3  # Try hard, planning is critical
        ),
        "standup": FailureConfig(
            policy=CeremonyFailurePolicy.CONTINUE,
            max_retries=0  # Don't retry, not critical
        ),
        "retrospective": FailureConfig(
            policy=CeremonyFailurePolicy.RETRY,
            max_retries=3  # Try to save learnings
        )
    }

    def __init__(self):
        """Initialize failure handler with empty state."""
        self.failure_counts: Dict[str, int] = {}  # Track consecutive failures
        self.circuit_open: Dict[str, bool] = {}   # Circuit breaker state

        logger.info("ceremony_failure_handler_initialized")

    def handle_failure(
        self,
        ceremony_type: str,
        epic_num: int,
        error: Exception
    ) -> CeremonyFailurePolicy:
        """
        Handle ceremony failure according to policy.

        Implements circuit breaker pattern:
        1. Check if circuit is already open -> return SKIP
        2. Track consecutive failures
        3. Open circuit if threshold reached -> return SKIP
        4. Otherwise return configured policy

        Args:
            ceremony_type: Type of ceremony (planning, standup, retrospective)
            epic_num: Epic number
            error: Exception that occurred

        Returns:
            Policy to apply (ABORT, RETRY, CONTINUE, SKIP)

        Example:
            ```python
            # First failure
            policy = handler.handle_failure("planning", 1, error)
            # Returns: ABORT

            # After 3 consecutive failures
            policy = handler.handle_failure("planning", 1, error)
            # Returns: SKIP (circuit open)
            ```
        """
        config = self.FAILURE_POLICIES.get(
            ceremony_type,
            FailureConfig(policy=CeremonyFailurePolicy.CONTINUE)
        )

        # Check circuit breaker
        key = f"{ceremony_type}_{epic_num}"
        if self.circuit_open.get(key, False):
            logger.warning(
                "ceremony_circuit_breaker_open",
                ceremony_type=ceremony_type,
                epic_num=epic_num,
                message="Circuit breaker is open - skipping ceremony"
            )
            return CeremonyFailurePolicy.SKIP

        # Track consecutive failures
        self.failure_counts[key] = self.failure_counts.get(key, 0) + 1

        logger.error(
            "ceremony_failure_tracked",
            ceremony_type=ceremony_type,
            epic_num=epic_num,
            consecutive_failures=self.failure_counts[key],
            error=str(error),
            policy=config.policy.value
        )

        # Check circuit breaker threshold
        if self.failure_counts[key] >= config.circuit_breaker_threshold:
            self.circuit_open[key] = True
            logger.error(
                "ceremony_circuit_breaker_triggered",
                ceremony_type=ceremony_type,
                epic_num=epic_num,
                consecutive_failures=self.failure_counts[key],
                threshold=config.circuit_breaker_threshold,
                message="Circuit breaker triggered - future ceremonies will be skipped"
            )
            return CeremonyFailurePolicy.SKIP

        # Return configured policy
        return config.policy

    def reset_failures(self, ceremony_type: str, epic_num: int):
        """
        Reset failure count on success.

        Clears failure tracking and closes circuit breaker for this ceremony type and epic.

        Args:
            ceremony_type: Type of ceremony
            epic_num: Epic number

        Example:
            ```python
            # After successful ceremony
            handler.reset_failures("planning", 1)
            ```
        """
        key = f"{ceremony_type}_{epic_num}"

        # Clear failure count
        if key in self.failure_counts:
            old_count = self.failure_counts[key]
            del self.failure_counts[key]

            logger.info(
                "ceremony_failures_reset",
                ceremony_type=ceremony_type,
                epic_num=epic_num,
                previous_failures=old_count
            )

        # Reset circuit breaker
        if key in self.circuit_open:
            del self.circuit_open[key]

            logger.info(
                "ceremony_circuit_breaker_reset",
                ceremony_type=ceremony_type,
                epic_num=epic_num,
                message="Circuit breaker reset - ceremonies can execute again"
            )

    def get_config(self, ceremony_type: str) -> FailureConfig:
        """
        Get failure configuration for ceremony type.

        Args:
            ceremony_type: Type of ceremony

        Returns:
            FailureConfig with policy and settings

        Example:
            ```python
            config = handler.get_config("planning")
            print(f"Max retries: {config.max_retries}")
            # Output: Max retries: 3
            ```
        """
        return self.FAILURE_POLICIES.get(
            ceremony_type,
            FailureConfig(policy=CeremonyFailurePolicy.CONTINUE)
        )

    def get_failure_count(self, ceremony_type: str, epic_num: int) -> int:
        """
        Get current failure count for ceremony.

        Args:
            ceremony_type: Type of ceremony
            epic_num: Epic number

        Returns:
            Number of consecutive failures

        Example:
            ```python
            count = handler.get_failure_count("planning", 1)
            print(f"Failures: {count}")
            ```
        """
        key = f"{ceremony_type}_{epic_num}"
        return self.failure_counts.get(key, 0)

    def is_circuit_open(self, ceremony_type: str, epic_num: int) -> bool:
        """
        Check if circuit breaker is open for ceremony.

        Args:
            ceremony_type: Type of ceremony
            epic_num: Epic number

        Returns:
            True if circuit is open, False otherwise

        Example:
            ```python
            if handler.is_circuit_open("planning", 1):
                print("Cannot execute planning ceremony - circuit open")
            ```
        """
        key = f"{ceremony_type}_{epic_num}"
        return self.circuit_open.get(key, False)
