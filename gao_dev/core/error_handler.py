"""Error handler with recovery flows for onboarding.

This module provides the main error handling interface for onboarding operations,
including error display, recovery prompts, and logging.

Epic 42: Streamlined Onboarding Experience
Story 42.3: Error Messages and Recovery Flows
"""

from typing import Optional

import structlog
from rich.console import Console

from gao_dev.core.errors import OnboardingError, RecoveryAction, ErrorCode

logger = structlog.get_logger()


class ErrorRecoveryManager:
    """Manages error recovery flows during onboarding.

    Provides high-level error handling with automatic retry logic,
    skip tracking, and exit handling.

    Attributes:
        console: Rich Console for output
        max_retries: Maximum retry attempts per error
        retry_counts: Dict tracking retries per error code
        skipped_steps: List of skipped step names

    Example:
        ```python
        manager = ErrorRecoveryManager(console)

        result = await manager.handle_with_retry(
            operation=check_git_installed,
            error_factory=OnboardingError.git_not_installed,
            step_name="git_check"
        )

        if result is None:
            # User chose to exit
            sys.exit(1)
        ```
    """

    def __init__(self, console: Console, max_retries: int = 3):
        """Initialize error recovery manager.

        Args:
            console: Rich Console for output
            max_retries: Maximum retry attempts per error
        """
        self.console = console
        self.max_retries = max_retries
        self.retry_counts: dict[str, int] = {}
        self.skipped_steps: list[str] = []
        self.logger = logger.bind(component="error_recovery_manager")

    def reset(self) -> None:
        """Reset retry counts and skipped steps."""
        self.retry_counts.clear()
        self.skipped_steps.clear()
        self.logger.debug("recovery_manager_reset")

    def get_retry_count(self, error_code: ErrorCode) -> int:
        """Get current retry count for error code.

        Args:
            error_code: ErrorCode to check

        Returns:
            Number of retries for this error
        """
        return self.retry_counts.get(error_code.value, 0)

    def increment_retry(self, error_code: ErrorCode) -> int:
        """Increment retry count for error code.

        Args:
            error_code: ErrorCode to increment

        Returns:
            New retry count
        """
        current = self.retry_counts.get(error_code.value, 0)
        self.retry_counts[error_code.value] = current + 1
        return current + 1

    def can_retry(self, error_code: ErrorCode) -> bool:
        """Check if error can be retried.

        Args:
            error_code: ErrorCode to check

        Returns:
            True if under max retries, False otherwise
        """
        return self.get_retry_count(error_code) < self.max_retries

    def add_skipped(self, step_name: str) -> None:
        """Record a skipped step.

        Args:
            step_name: Name of skipped step
        """
        self.skipped_steps.append(step_name)
        self.logger.info("step_skipped", step=step_name)

    def get_skipped_steps(self) -> list[str]:
        """Get list of skipped steps.

        Returns:
            List of skipped step names
        """
        return self.skipped_steps.copy()

    def display_error(self, error: OnboardingError) -> None:
        """Display error to user.

        Args:
            error: OnboardingError to display
        """
        self.console.print()
        self.console.print(error.to_panel())
        self.console.print()
        error.log_error()

    def display_max_retries_exceeded(self, error: OnboardingError) -> None:
        """Display message when max retries exceeded.

        Args:
            error: Error that exceeded retries
        """
        retry_count = self.get_retry_count(error.code)
        self.console.print(
            f"[yellow]Maximum retries ({retry_count}) exceeded for {error.title}[/yellow]"
        )
        self.logger.warning(
            "max_retries_exceeded",
            error_code=error.code.value,
            retries=retry_count
        )

    def prompt_recovery(
        self,
        error: OnboardingError,
        include_retry: Optional[bool] = None
    ) -> RecoveryAction:
        """Prompt user for recovery action.

        Args:
            error: Error to recover from
            include_retry: Override retry availability (uses can_retry if None)

        Returns:
            RecoveryAction chosen by user
        """
        # Determine if retry is available
        if include_retry is None:
            include_retry = error.can_retry and self.can_retry(error.code)

        # Build options
        options = []
        if include_retry:
            retries_left = self.max_retries - self.get_retry_count(error.code)
            options.append(f"[R]etry ({retries_left} left)")

        if error.can_skip:
            options.append("[S]kip")

        options.append("[E]xit")

        options_str = " / ".join(options)
        self.console.print(f"[bold]Options:[/bold] {options_str}")

        while True:
            choice = self.console.input("[bold]Choose action:[/bold] ").strip().lower()

            if choice in ("r", "retry") and include_retry:
                self.increment_retry(error.code)
                self.logger.info(
                    "recovery_action",
                    action="retry",
                    error_code=error.code.value,
                    retry_count=self.get_retry_count(error.code)
                )
                return RecoveryAction.RETRY

            elif choice in ("s", "skip") and error.can_skip:
                self.logger.info("recovery_action", action="skip", error_code=error.code.value)
                return RecoveryAction.SKIP

            elif choice in ("e", "exit"):
                self.logger.info("recovery_action", action="exit", error_code=error.code.value)
                return RecoveryAction.EXIT

            else:
                valid = []
                if include_retry:
                    valid.append("r")
                if error.can_skip:
                    valid.append("s")
                valid.append("e")
                self.console.print(f"[red]Invalid choice. Enter: {', '.join(valid)}[/red]")

    def handle_error(
        self,
        error: OnboardingError,
        step_name: Optional[str] = None
    ) -> RecoveryAction:
        """Handle error with recovery flow.

        Complete flow:
        1. Display error
        2. Check retry limits
        3. Prompt for action
        4. Track skipped steps

        Args:
            error: Error to handle
            step_name: Name of step for skip tracking

        Returns:
            RecoveryAction chosen by user
        """
        self.display_error(error)

        # Check retry limits
        if error.can_retry and not self.can_retry(error.code):
            self.display_max_retries_exceeded(error)

        action = self.prompt_recovery(error)

        # Track skipped steps
        if action == RecoveryAction.SKIP and step_name:
            self.add_skipped(step_name)

        return action

    def display_summary(self) -> None:
        """Display summary of error handling session.

        Shows retry counts and skipped steps.
        """
        if not self.retry_counts and not self.skipped_steps:
            return

        self.console.print("\n[bold]Error Recovery Summary:[/bold]")

        if self.retry_counts:
            self.console.print("\nRetries:")
            for code, count in self.retry_counts.items():
                self.console.print(f"  - {code}: {count} retries")

        if self.skipped_steps:
            self.console.print("\nSkipped Steps:")
            for step in self.skipped_steps:
                self.console.print(f"  - {step}")

        self.console.print()


async def handle_onboarding_error(
    error: OnboardingError,
    console: Console,
    step_name: Optional[str] = None,
    manager: Optional[ErrorRecoveryManager] = None
) -> RecoveryAction:
    """Handle onboarding error with recovery flow.

    Convenience function for handling errors in async contexts.

    Args:
        error: Error to handle
        console: Rich Console for output
        step_name: Name of step for tracking
        manager: Optional existing ErrorRecoveryManager

    Returns:
        RecoveryAction chosen by user

    Example:
        ```python
        try:
            result = await check_git()
        except GitNotFoundError:
            error = OnboardingError.git_not_installed()
            action = await handle_onboarding_error(error, console, "git_check")

            if action == RecoveryAction.RETRY:
                # Retry
                pass
            elif action == RecoveryAction.EXIT:
                raise SystemExit(1)
        ```
    """
    if manager is None:
        manager = ErrorRecoveryManager(console)

    return manager.handle_error(error, step_name)


def create_error_for_exception(
    exception: Exception,
    context: Optional[dict] = None
) -> OnboardingError:
    """Create OnboardingError from Python exception.

    Maps common exceptions to appropriate OnboardingError types.

    Args:
        exception: Python exception to convert
        context: Optional additional context

    Returns:
        Appropriate OnboardingError

    Example:
        ```python
        try:
            result = await operation()
        except Exception as e:
            error = create_error_for_exception(e, {"operation": "git_check"})
            action = await handle_onboarding_error(error, console)
        ```
    """
    context = context or {}

    exception_str = str(exception).lower()

    # Network errors
    if any(word in exception_str for word in ["timeout", "timed out"]):
        return OnboardingError.network_timeout()

    if any(word in exception_str for word in ["connection", "network", "unreachable", "dns"]):
        return OnboardingError.network_error()

    # Permission errors
    if any(word in exception_str for word in ["permission", "access denied", "not permitted"]):
        path = context.get("path", "unknown")
        return OnboardingError.permission_denied(path)

    # Git errors
    if "git" in exception_str:
        if "not found" in exception_str or "not installed" in exception_str:
            return OnboardingError.git_not_installed()
        if "config" in exception_str or "user.name" in exception_str or "user.email" in exception_str:
            return OnboardingError.git_not_configured()

    # Rate limit errors (check before API key errors)
    if any(word in exception_str for word in ["rate limit", "rate_limit", "ratelimit"]):
        provider = context.get("provider", "unknown")
        return OnboardingError.api_key_rate_limited(provider)

    # API key errors
    if any(word in exception_str for word in ["api key", "apikey", "authentication", "unauthorized"]):
        provider = context.get("provider", "unknown")
        return OnboardingError.api_key_invalid(provider)

    # Port errors
    if any(word in exception_str for word in ["port", "address already in use", "bind"]):
        port = context.get("port", 8000)
        return OnboardingError.port_in_use(port)

    # Config errors
    if any(word in exception_str for word in ["yaml", "json", "config", "parse"]):
        path = context.get("path", "config file")
        return OnboardingError.config_corrupted(path)

    # Default: create generic error
    return OnboardingError(
        code=ErrorCode.ONBOARDING_INTERRUPTED,
        title="Unexpected Error",
        description=str(exception),
        suggestions=[
            "Check the error message above",
            "Run with --verbose for more details",
            "Report this issue at https://github.com/gao-dev/gao-agile-dev/issues"
        ],
        critical=True,
        can_skip=False,
        can_retry=True,
        context=context
    )
