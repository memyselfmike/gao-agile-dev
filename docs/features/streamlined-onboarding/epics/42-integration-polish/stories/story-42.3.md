# Story 42.3: Error Messages and Recovery Flows

## User Story

As a developer encountering an error during onboarding,
I want clear error messages with specific fix suggestions,
So that I can resolve the issue quickly without searching for help.

## Acceptance Criteria

- [ ] AC1: All error messages include a brief description of what went wrong
- [ ] AC2: All error messages include specific, actionable fix suggestions
- [ ] AC3: Network errors suggest checking internet connection with retry option
- [ ] AC4: Git not installed errors include installation commands for each OS
- [ ] AC5: API key errors suggest getting new key with provider dashboard links
- [ ] AC6: Permission errors suggest specific chmod/permission fixes
- [ ] AC7: Port conflict errors suggest either waiting or using `--port` option
- [ ] AC8: Keychain unavailable errors suggest using environment variables instead
- [ ] AC9: Error codes are unique and documented for support reference
- [ ] AC10: Critical errors logged with full context for debugging
- [ ] AC11: Recovery options presented: retry, skip (if possible), exit
- [ ] AC12: Error messages formatted consistently with Rich styling

## Technical Notes

### Implementation Details

Create `gao_dev/core/errors.py`:

```python
from enum import Enum
from typing import Optional

class ErrorCode(Enum):
    """Unique error codes for support reference."""
    GIT_NOT_INSTALLED = "E001"
    GIT_NOT_CONFIGURED = "E002"
    API_KEY_INVALID = "E101"
    API_KEY_RATE_LIMITED = "E102"
    NETWORK_ERROR = "E201"
    PORT_IN_USE = "E301"
    KEYCHAIN_UNAVAILABLE = "E401"
    PERMISSION_DENIED = "E501"
    CONFIG_CORRUPTED = "E601"

class OnboardingError:
    """Actionable error messages with fix instructions."""

    @staticmethod
    def format_error(
        code: ErrorCode,
        description: str,
        fixes: list[str],
        recovery_options: list[str]
    ) -> str:
        """Format error message with Rich styling."""
        return Panel(
            f"[red bold]Error {code.value}[/red bold]\n\n"
            f"{description}\n\n"
            f"[yellow]How to fix:[/yellow]\n" +
            "\n".join(f"  {i+1}. {fix}" for i, fix in enumerate(fixes)) +
            f"\n\n[dim]Options: {', '.join(recovery_options)}[/dim]",
            border_style="red",
            title="Onboarding Error"
        )

    @staticmethod
    def git_not_installed() -> str:
        return OnboardingError.format_error(
            code=ErrorCode.GIT_NOT_INSTALLED,
            description="Git is not installed or not in your PATH.",
            fixes=[
                "Windows: Download from https://git-scm.com/download/win",
                "macOS: Run 'xcode-select --install' in Terminal",
                "Linux (Ubuntu/Debian): Run 'sudo apt install git'",
                "Linux (Fedora): Run 'sudo dnf install git'",
                "After installing, restart your terminal and try again"
            ],
            recovery_options=["Retry", "Exit"]
        )

    @staticmethod
    def api_key_invalid(provider: str) -> str:
        provider_urls = {
            "anthropic": "https://console.anthropic.com/settings/keys",
            "openai": "https://platform.openai.com/api-keys",
        }
        url = provider_urls.get(provider, "your provider's dashboard")

        return OnboardingError.format_error(
            code=ErrorCode.API_KEY_INVALID,
            description=f"The API key for {provider} is invalid or expired.",
            fixes=[
                f"Get a valid key from {url}",
                "Check for extra spaces or missing characters",
                "Ensure the key has the required permissions",
                f"Or set {provider.upper()}_API_KEY environment variable"
            ],
            recovery_options=["Retry", "Skip", "Exit"]
        )

    @staticmethod
    def keychain_unavailable() -> str:
        return OnboardingError.format_error(
            code=ErrorCode.KEYCHAIN_UNAVAILABLE,
            description="System keychain is not available in this environment.",
            fixes=[
                "This is normal for Docker containers and SSH sessions",
                "Set credentials as environment variables:",
                "  export ANTHROPIC_API_KEY='your-key-here'",
                "Or mount a config volume in Docker:",
                "  -v gao-dev-config:/root/.gao-dev"
            ],
            recovery_options=["Use environment variable", "Skip"]
        )

    @staticmethod
    def port_in_use(port: int) -> str:
        return OnboardingError.format_error(
            code=ErrorCode.PORT_IN_USE,
            description=f"Port {port} is already in use by another application.",
            fixes=[
                f"Wait for the other application to release port {port}",
                f"Use a different port: gao-dev start --port {port + 1}",
                f"Find what's using the port: lsof -i :{port} (macOS/Linux)",
                f"Or: netstat -ano | findstr {port} (Windows)"
            ],
            recovery_options=["Retry", "Use different port", "Exit"]
        )
```

### Error Message Format

```
+--------------------------------------------------+
|                 Onboarding Error                 |
+--------------------------------------------------+
| Error E001                                       |
|                                                  |
| Git is not installed or not in your PATH.        |
|                                                  |
| How to fix:                                      |
|   1. Windows: Download from https://git-scm.com  |
|   2. macOS: Run 'xcode-select --install'         |
|   3. Linux: Run 'sudo apt install git'           |
|   4. After installing, restart terminal          |
|                                                  |
| Options: Retry, Exit                             |
+--------------------------------------------------+
```

### Recovery Flow

```python
async def handle_error_with_recovery(
    error: OnboardingError,
    context: str
) -> RecoveryAction:
    """Display error and get user's recovery choice."""
    console.print(error)

    if "Retry" in error.recovery_options:
        if Confirm.ask("Would you like to retry?"):
            return RecoveryAction.RETRY

    if "Skip" in error.recovery_options:
        if Confirm.ask("Skip this step? (may cause issues later)"):
            return RecoveryAction.SKIP

    return RecoveryAction.EXIT
```

## Test Scenarios

1. **Git not installed message**: Given git not found, When error displayed, Then shows installation commands for all OS

2. **API key invalid message**: Given 401 from provider, When error displayed, Then shows provider dashboard URL

3. **Network error message**: Given connection timeout, When error displayed, Then suggests checking internet

4. **Port in use message**: Given port 3000 busy, When error displayed, Then suggests --port option

5. **Keychain unavailable message**: Given Docker environment, When keychain fails, Then suggests env vars

6. **Error code displayed**: Given any error, When displayed, Then shows unique error code

7. **Retry option works**: Given retriable error, When user selects retry, Then operation retried

8. **Skip option works**: Given skippable error, When user selects skip, Then continues without step

9. **Logging includes context**: Given any error, When logged, Then includes full debug context

10. **Consistent formatting**: Given any error, When displayed, Then uses Rich Panel with red border

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests for all error messages
- [ ] Error codes documented in troubleshooting guide
- [ ] All messages reviewed for clarity and actionability
- [ ] Code reviewed
- [ ] Type hints complete (no `Any`)

## Story Points: 5

## Dependencies

- Stories 40.1-40.5: Environment detection errors
- Stories 41.1-41.6: Wizard-related errors

## Notes

- Test error messages with real users for clarity
- Include links where possible (clickable in most terminals)
- Consider internationalization for future versions
- Ensure error codes don't conflict with existing GAO-Dev errors
- Log errors at ERROR level with structured data for Splunk/Datadog
- Consider adding `--debug` flag for verbose error output
