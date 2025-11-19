"""Onboarding error messages and recovery flows.

This module provides comprehensive error handling for onboarding operations with:
- Unique error codes for support reference
- Actionable fix suggestions for each error type
- Platform-specific installation commands
- Provider dashboard URLs for API key retrieval
- Recovery options (retry, skip, exit)

Epic 42: Streamlined Onboarding Experience
Story 42.3: Error Messages and Recovery Flows

Error Code Reference:
    E001 - Git not installed
    E002 - Git not configured
    E101 - API key invalid
    E102 - API key rate limited
    E103 - API key network error
    E201 - Network error
    E202 - Network timeout
    E301 - Port in use
    E401 - Keychain unavailable
    E501 - Permission denied
    E601 - Config corrupted
    E701 - Onboarding interrupted
"""

import platform
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import structlog
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

logger = structlog.get_logger()


class ErrorCode(Enum):
    """Unique error codes for support reference.

    Each code maps to a specific error condition and can be used
    for documentation, support tickets, and troubleshooting guides.

    Format: E<category><number>
    - E0xx: Git errors
    - E1xx: API key errors
    - E2xx: Network errors
    - E3xx: Port/resource errors
    - E4xx: Security errors
    - E5xx: Permission errors
    - E6xx: Configuration errors
    - E7xx: Process errors
    """
    GIT_NOT_INSTALLED = "E001"
    GIT_NOT_CONFIGURED = "E002"
    API_KEY_INVALID = "E101"
    API_KEY_RATE_LIMITED = "E102"
    API_KEY_NETWORK_ERROR = "E103"
    NETWORK_ERROR = "E201"
    NETWORK_TIMEOUT = "E202"
    PORT_IN_USE = "E301"
    KEYCHAIN_UNAVAILABLE = "E401"
    PERMISSION_DENIED = "E501"
    CONFIG_CORRUPTED = "E601"
    ONBOARDING_INTERRUPTED = "E701"


class RecoveryAction(Enum):
    """User's chosen recovery action after an error.

    Each action determines how the error handler should proceed
    after displaying the error message and suggestions.

    Attributes:
        RETRY: Attempt the failed operation again
        SKIP: Skip the current step if possible
        EXIT: Exit the onboarding process
        USE_ALTERNATIVE: Use an alternative method (e.g., env var instead of keychain)
    """
    RETRY = "retry"
    SKIP = "skip"
    EXIT = "exit"
    USE_ALTERNATIVE = "use_alternative"


@dataclass
class OnboardingError:
    """Actionable error message with fix instructions.

    Represents a complete error with:
    - Error code for support reference
    - Brief description of what went wrong
    - Specific, actionable fix suggestions
    - Whether the error is critical (stops onboarding)
    - Whether the error can be skipped
    - Whether the error can be retried

    Attributes:
        code: Unique error code (e.g., E001)
        title: Short error title
        description: What went wrong
        suggestions: List of actionable fix suggestions
        critical: Whether this error stops onboarding
        can_skip: Whether this error can be skipped
        can_retry: Whether this error can be retried
        context: Additional context for logging

    Example:
        ```python
        error = OnboardingError.git_not_installed()
        console.print(error.to_panel())

        if error.can_retry:
            action = await handle_error_with_recovery(error, console)
            if action == RecoveryAction.RETRY:
                # Retry the operation
                pass
        ```
    """
    code: ErrorCode
    title: str
    description: str
    suggestions: list[str] = field(default_factory=list)
    critical: bool = True
    can_skip: bool = False
    can_retry: bool = True
    context: dict = field(default_factory=dict)

    def to_panel(self) -> Panel:
        """Create Rich Panel for error display.

        Returns:
            Panel with formatted error message and suggestions
        """
        text = Text()

        # Error code and title
        text.append(f"[{self.code.value}] ", style="bold red")
        text.append(f"{self.title}\n\n", style="bold")

        # Description
        text.append(f"{self.description}\n", style="dim")

        # Suggestions
        if self.suggestions:
            text.append("\nHow to fix:\n", style="bold yellow")
            for i, suggestion in enumerate(self.suggestions, 1):
                text.append(f"  {i}. {suggestion}\n", style="white")

        return Panel(
            text,
            title="Error",
            border_style="red",
            expand=False
        )

    def log_error(self) -> None:
        """Log error with full context using structlog."""
        logger.error(
            "onboarding_error",
            error_code=self.code.value,
            title=self.title,
            description=self.description,
            critical=self.critical,
            can_skip=self.can_skip,
            can_retry=self.can_retry,
            **self.context
        )

    @staticmethod
    def git_not_installed() -> "OnboardingError":
        """Create error for git not installed.

        Includes platform-specific installation commands for Windows, macOS, and Linux.

        Returns:
            OnboardingError with installation suggestions
        """
        system = platform.system()
        suggestions = []

        if system == "Windows":
            suggestions = [
                "Download Git from https://git-scm.com/download/win",
                "Or install with winget: winget install Git.Git",
                "Or install with Chocolatey: choco install git",
                "After installation, restart your terminal",
                "Verify: git --version"
            ]
        elif system == "Darwin":
            suggestions = [
                "Install Xcode Command Line Tools: xcode-select --install",
                "Or install with Homebrew: brew install git",
                "Verify: git --version"
            ]
        else:  # Linux
            suggestions = [
                "Ubuntu/Debian: sudo apt-get install git",
                "Fedora: sudo dnf install git",
                "Arch: sudo pacman -S git",
                "Verify: git --version"
            ]

        return OnboardingError(
            code=ErrorCode.GIT_NOT_INSTALLED,
            title="Git Not Installed",
            description="Git is required for version control but was not found on your system.",
            suggestions=suggestions,
            critical=True,
            can_skip=False,
            can_retry=True,
            context={"platform": system}
        )

    @staticmethod
    def git_not_configured() -> "OnboardingError":
        """Create error for git not configured with user name/email.

        Returns:
            OnboardingError with git config commands
        """
        return OnboardingError(
            code=ErrorCode.GIT_NOT_CONFIGURED,
            title="Git Not Configured",
            description="Git requires user name and email for commits.",
            suggestions=[
                'Set your name: git config --global user.name "Your Name"',
                'Set your email: git config --global user.email "your@email.com"',
                "Verify: git config --global --list"
            ],
            critical=True,
            can_skip=False,
            can_retry=True
        )

    @staticmethod
    def api_key_invalid(provider: str) -> "OnboardingError":
        """Create error for invalid API key.

        Includes provider-specific dashboard URLs for getting new keys.

        Args:
            provider: Provider name (e.g., 'anthropic', 'openai', 'google')

        Returns:
            OnboardingError with API key suggestions
        """
        dashboard_urls = {
            "anthropic": "https://console.anthropic.com/settings/keys",
            "openai": "https://platform.openai.com/api-keys",
            "google": "https://aistudio.google.com/app/apikey"
        }

        env_vars = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY"
        }

        provider_lower = provider.lower()
        dashboard_url = dashboard_urls.get(provider_lower, "your provider's dashboard")
        env_var = env_vars.get(provider_lower, f"{provider.upper()}_API_KEY")

        suggestions = [
            f"Get a new API key from {dashboard_url}",
            f"Set the environment variable: export {env_var}=your-api-key",
            "Verify the key has correct permissions",
            "Check for trailing spaces or newlines in the key"
        ]

        if provider_lower == "anthropic":
            suggestions.append("Ensure key starts with 'sk-ant-'")

        return OnboardingError(
            code=ErrorCode.API_KEY_INVALID,
            title=f"Invalid {provider.title()} API Key",
            description=f"The {provider.title()} API key is invalid or expired.",
            suggestions=suggestions,
            critical=True,
            can_skip=False,
            can_retry=True,
            context={"provider": provider}
        )

    @staticmethod
    def api_key_rate_limited(provider: str, retry_after: Optional[int] = None) -> "OnboardingError":
        """Create error for rate-limited API key.

        Args:
            provider: Provider name
            retry_after: Seconds to wait before retry (if known)

        Returns:
            OnboardingError with rate limit suggestions
        """
        wait_msg = f"Wait {retry_after} seconds" if retry_after else "Wait a few minutes"

        return OnboardingError(
            code=ErrorCode.API_KEY_RATE_LIMITED,
            title=f"{provider.title()} Rate Limited",
            description=f"You've exceeded the rate limit for {provider.title()} API.",
            suggestions=[
                wait_msg + " and try again",
                "Check your usage at the provider's dashboard",
                "Consider upgrading your plan for higher limits",
                "Use a local model (Ollama) to avoid API limits"
            ],
            critical=False,
            can_skip=False,
            can_retry=True,
            context={"provider": provider, "retry_after": retry_after}
        )

    @staticmethod
    def network_error() -> "OnboardingError":
        """Create error for general network issues.

        Returns:
            OnboardingError with network troubleshooting suggestions
        """
        return OnboardingError(
            code=ErrorCode.NETWORK_ERROR,
            title="Network Connection Error",
            description="Unable to connect to the internet.",
            suggestions=[
                "Check your internet connection",
                "Try pinging: ping 8.8.8.8",
                "Check if you're behind a proxy or firewall",
                "Try disabling VPN temporarily",
                "Retry in a few moments"
            ],
            critical=False,
            can_skip=False,
            can_retry=True
        )

    @staticmethod
    def network_timeout(timeout_seconds: int = 30) -> "OnboardingError":
        """Create error for network timeout.

        Args:
            timeout_seconds: Timeout value that was exceeded

        Returns:
            OnboardingError with timeout suggestions
        """
        return OnboardingError(
            code=ErrorCode.NETWORK_TIMEOUT,
            title="Network Timeout",
            description=f"Request timed out after {timeout_seconds} seconds.",
            suggestions=[
                "Check your internet connection stability",
                "The server may be experiencing high load",
                "Try again in a few moments",
                "Consider using a local model (Ollama) for offline work"
            ],
            critical=False,
            can_skip=False,
            can_retry=True,
            context={"timeout_seconds": timeout_seconds}
        )

    @staticmethod
    def port_in_use(port: int) -> "OnboardingError":
        """Create error for port already in use.

        Args:
            port: Port number that is in use

        Returns:
            OnboardingError with port conflict suggestions
        """
        system = platform.system()

        if system == "Windows":
            find_cmd = f"netstat -ano | findstr :{port}"
        else:
            find_cmd = f"lsof -i :{port}"

        return OnboardingError(
            code=ErrorCode.PORT_IN_USE,
            title=f"Port {port} Already in Use",
            description=f"Cannot start server because port {port} is already in use by another process.",
            suggestions=[
                f"Find the process using port {port}: {find_cmd}",
                f"Use a different port: gao-dev start --port {port + 1}",
                "Kill the process using the port and retry",
                "Check if another GAO-Dev instance is running"
            ],
            critical=True,
            can_skip=False,
            can_retry=True,
            context={"port": port, "platform": system}
        )

    @staticmethod
    def keychain_unavailable() -> "OnboardingError":
        """Create error for keychain/credential store unavailable.

        Returns:
            OnboardingError with keychain alternative suggestions
        """
        system = platform.system()

        if system == "Darwin":
            keychain_name = "Keychain Access"
        elif system == "Windows":
            keychain_name = "Credential Manager"
        else:
            keychain_name = "Secret Service (libsecret)"

        return OnboardingError(
            code=ErrorCode.KEYCHAIN_UNAVAILABLE,
            title="Credential Store Unavailable",
            description=f"{keychain_name} is not available for secure credential storage.",
            suggestions=[
                "Use environment variables instead: export ANTHROPIC_API_KEY=...",
                "Store credentials in a .env file (add to .gitignore)",
                f"Enable {keychain_name} on your system",
                "Run with --no-keychain to skip secure storage"
            ],
            critical=False,
            can_skip=True,
            can_retry=False,
            context={"keychain": keychain_name, "platform": system}
        )

    @staticmethod
    def permission_denied(path: str) -> "OnboardingError":
        """Create error for permission denied on file/directory.

        Args:
            path: Path that cannot be accessed

        Returns:
            OnboardingError with permission fix suggestions
        """
        system = platform.system()

        if system == "Windows":
            suggestions = [
                f'Run as Administrator, or',
                f'Right-click folder -> Properties -> Security -> Edit permissions',
                f'Check if folder is marked as read-only'
            ]
        else:
            suggestions = [
                f"Check ownership: ls -la {path}",
                f"Change permissions: chmod 755 {path}",
                f"Change ownership: sudo chown $USER {path}",
                "Check if path is on a read-only filesystem"
            ]

        return OnboardingError(
            code=ErrorCode.PERMISSION_DENIED,
            title="Permission Denied",
            description=f"Cannot access or modify: {path}",
            suggestions=suggestions,
            critical=True,
            can_skip=False,
            can_retry=True,
            context={"path": path, "platform": system}
        )

    @staticmethod
    def config_corrupted(path: str) -> "OnboardingError":
        """Create error for corrupted configuration file.

        Args:
            path: Path to corrupted config file

        Returns:
            OnboardingError with recovery suggestions
        """
        return OnboardingError(
            code=ErrorCode.CONFIG_CORRUPTED,
            title="Configuration File Corrupted",
            description=f"The configuration file is corrupted or invalid: {path}",
            suggestions=[
                f"Backup the corrupted file: cp {path} {path}.backup",
                f"Delete and recreate: rm {path}",
                "Check file for YAML syntax errors",
                "Restore from version control: git checkout {path}",
                "Run gao-dev init to create fresh configuration"
            ],
            critical=True,
            can_skip=False,
            can_retry=True,
            context={"path": path}
        )

    @staticmethod
    def onboarding_interrupted() -> "OnboardingError":
        """Create error for interrupted onboarding process.

        Returns:
            OnboardingError with resume instructions
        """
        return OnboardingError(
            code=ErrorCode.ONBOARDING_INTERRUPTED,
            title="Onboarding Interrupted",
            description="The onboarding process was interrupted before completion.",
            suggestions=[
                "Run 'gao-dev start' to resume onboarding",
                "Your progress has been saved",
                "Use 'gao-dev status' to check current state",
                "Run 'gao-dev init --force' to start fresh"
            ],
            critical=False,
            can_skip=True,
            can_retry=True
        )


class OnboardingErrorHandler:
    """Handles error display and recovery flow.

    Provides methods to display formatted error messages and prompt
    users for recovery actions.

    Attributes:
        console: Rich Console for output
        logger: Structured logger for error logging

    Example:
        ```python
        handler = OnboardingErrorHandler(console)
        error = OnboardingError.git_not_installed()

        action = await handler.handle_error(error)
        if action == RecoveryAction.RETRY:
            # Retry the operation
            pass
        elif action == RecoveryAction.EXIT:
            sys.exit(1)
        ```
    """

    def __init__(self, console: Console):
        """Initialize error handler.

        Args:
            console: Rich Console for output
        """
        self.console = console
        self.logger = logger.bind(component="error_handler")

    def display_error(self, error: OnboardingError) -> None:
        """Display error to user and log it.

        Args:
            error: OnboardingError to display
        """
        # Display formatted error panel
        self.console.print()
        self.console.print(error.to_panel())
        self.console.print()

        # Log with full context
        error.log_error()

    def get_recovery_options(self, error: OnboardingError) -> list[str]:
        """Get available recovery options for error.

        Args:
            error: OnboardingError to get options for

        Returns:
            List of option strings (e.g., ['[R]etry', '[E]xit'])
        """
        options = []

        if error.can_retry:
            options.append("[R]etry")

        if error.can_skip:
            options.append("[S]kip")

        # Always allow exit
        options.append("[E]xit")

        return options

    def prompt_recovery(self, error: OnboardingError) -> RecoveryAction:
        """Prompt user for recovery action.

        Displays available options and gets user input.

        Args:
            error: OnboardingError to recover from

        Returns:
            RecoveryAction chosen by user
        """
        options = self.get_recovery_options(error)
        options_str = " / ".join(options)

        self.console.print(f"[bold]Options:[/bold] {options_str}")

        while True:
            choice = self.console.input("[bold]Choose action:[/bold] ").strip().lower()

            if choice in ("r", "retry") and error.can_retry:
                self.logger.info("recovery_action", action="retry", error_code=error.code.value)
                return RecoveryAction.RETRY
            elif choice in ("s", "skip") and error.can_skip:
                self.logger.info("recovery_action", action="skip", error_code=error.code.value)
                return RecoveryAction.SKIP
            elif choice in ("e", "exit"):
                self.logger.info("recovery_action", action="exit", error_code=error.code.value)
                return RecoveryAction.EXIT
            elif choice in ("a", "alt", "alternative") and not error.critical:
                self.logger.info("recovery_action", action="use_alternative", error_code=error.code.value)
                return RecoveryAction.USE_ALTERNATIVE
            else:
                valid_choices = []
                if error.can_retry:
                    valid_choices.append("r")
                if error.can_skip:
                    valid_choices.append("s")
                valid_choices.append("e")

                self.console.print(f"[red]Invalid choice. Please enter: {', '.join(valid_choices)}[/red]")

    def handle_error(self, error: OnboardingError) -> RecoveryAction:
        """Display error and get recovery action.

        Complete error handling flow:
        1. Display formatted error
        2. Prompt for recovery action
        3. Return chosen action

        Args:
            error: OnboardingError to handle

        Returns:
            RecoveryAction chosen by user
        """
        self.display_error(error)
        return self.prompt_recovery(error)


# Async wrapper for compatibility with async code
async def handle_error_with_recovery(
    error: OnboardingError,
    console: Console
) -> RecoveryAction:
    """Display error and get user's recovery choice.

    Async wrapper around OnboardingErrorHandler for use in async contexts.

    Args:
        error: OnboardingError to handle
        console: Rich Console for output

    Returns:
        RecoveryAction chosen by user

    Example:
        ```python
        error = OnboardingError.git_not_installed()
        action = await handle_error_with_recovery(error, console)

        if action == RecoveryAction.RETRY:
            # Retry the operation
            pass
        ```
    """
    handler = OnboardingErrorHandler(console)
    return handler.handle_error(error)
