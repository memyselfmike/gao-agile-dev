"""Unit tests for onboarding error messages.

Epic 42: Streamlined Onboarding Experience
Story 42.3: Error Messages and Recovery Flows
"""

import platform
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console
from rich.panel import Panel

from gao_dev.core.errors import (
    ErrorCode,
    RecoveryAction,
    OnboardingError,
    OnboardingErrorHandler,
    handle_error_with_recovery,
)


class TestErrorCode:
    """Test ErrorCode enum."""

    def test_all_error_codes_defined(self):
        """Test all required error codes are defined."""
        required_codes = [
            "GIT_NOT_INSTALLED",
            "GIT_NOT_CONFIGURED",
            "API_KEY_INVALID",
            "API_KEY_RATE_LIMITED",
            "API_KEY_NETWORK_ERROR",
            "NETWORK_ERROR",
            "NETWORK_TIMEOUT",
            "PORT_IN_USE",
            "KEYCHAIN_UNAVAILABLE",
            "PERMISSION_DENIED",
            "CONFIG_CORRUPTED",
            "ONBOARDING_INTERRUPTED",
        ]

        for code_name in required_codes:
            assert hasattr(ErrorCode, code_name), f"{code_name} not defined"

    def test_error_codes_are_unique(self):
        """Test all error codes have unique values."""
        values = [code.value for code in ErrorCode]
        assert len(values) == len(set(values)), "Duplicate error code values found"

    def test_error_code_format(self):
        """Test error codes follow E<category><number> format."""
        for code in ErrorCode:
            assert code.value.startswith("E"), f"{code.name} should start with 'E'"
            assert len(code.value) == 4, f"{code.name} should be 4 characters"
            assert code.value[1:].isdigit(), f"{code.name} should have numeric suffix"


class TestRecoveryAction:
    """Test RecoveryAction enum."""

    def test_all_actions_defined(self):
        """Test all recovery actions are defined."""
        required_actions = ["RETRY", "SKIP", "EXIT", "USE_ALTERNATIVE"]

        for action_name in required_actions:
            assert hasattr(RecoveryAction, action_name), f"{action_name} not defined"

    def test_action_values(self):
        """Test action values are lowercase strings."""
        for action in RecoveryAction:
            assert action.value.islower(), f"{action.name} value should be lowercase"
            assert isinstance(action.value, str), f"{action.name} value should be string"


class TestOnboardingError:
    """Test OnboardingError dataclass."""

    def test_basic_initialization(self):
        """Test OnboardingError can be initialized."""
        error = OnboardingError(
            code=ErrorCode.GIT_NOT_INSTALLED,
            title="Git Not Installed",
            description="Git is required",
            suggestions=["Install git"],
        )

        assert error.code == ErrorCode.GIT_NOT_INSTALLED
        assert error.title == "Git Not Installed"
        assert error.description == "Git is required"
        assert "Install git" in error.suggestions

    def test_default_values(self):
        """Test default values are set correctly."""
        error = OnboardingError(
            code=ErrorCode.NETWORK_ERROR,
            title="Network Error",
            description="Connection failed",
        )

        assert error.critical is True
        assert error.can_skip is False
        assert error.can_retry is True
        assert error.suggestions == []
        assert error.context == {}

    def test_to_panel_returns_panel(self):
        """Test to_panel returns Rich Panel."""
        error = OnboardingError(
            code=ErrorCode.GIT_NOT_INSTALLED,
            title="Test Error",
            description="Test description",
            suggestions=["Suggestion 1", "Suggestion 2"],
        )

        panel = error.to_panel()
        assert isinstance(panel, Panel)
        assert panel.border_style == "red"

    def test_log_error_logs_with_context(self):
        """Test log_error logs with structlog."""
        with patch("gao_dev.core.errors.logger") as mock_logger:
            error = OnboardingError(
                code=ErrorCode.PORT_IN_USE,
                title="Port Error",
                description="Port 8000 in use",
                context={"port": 8000},
            )

            error.log_error()

            mock_logger.error.assert_called_once()
            call_kwargs = mock_logger.error.call_args[1]
            assert call_kwargs["error_code"] == "E301"
            assert call_kwargs["port"] == 8000


class TestGitErrors:
    """Test Git-related error factories."""

    def test_git_not_installed_windows(self):
        """Test git_not_installed error on Windows."""
        with patch("platform.system", return_value="Windows"):
            error = OnboardingError.git_not_installed()

            assert error.code == ErrorCode.GIT_NOT_INSTALLED
            assert "winget" in str(error.suggestions) or "git-scm.com" in str(error.suggestions)
            assert error.context["platform"] == "Windows"

    def test_git_not_installed_macos(self):
        """Test git_not_installed error on macOS."""
        with patch("platform.system", return_value="Darwin"):
            error = OnboardingError.git_not_installed()

            assert error.code == ErrorCode.GIT_NOT_INSTALLED
            assert any("xcode-select" in s or "brew" in s for s in error.suggestions)
            assert error.context["platform"] == "Darwin"

    def test_git_not_installed_linux(self):
        """Test git_not_installed error on Linux."""
        with patch("platform.system", return_value="Linux"):
            error = OnboardingError.git_not_installed()

            assert error.code == ErrorCode.GIT_NOT_INSTALLED
            assert any("apt" in s or "dnf" in s or "pacman" in s for s in error.suggestions)
            assert error.context["platform"] == "Linux"

    def test_git_not_configured(self):
        """Test git_not_configured error."""
        error = OnboardingError.git_not_configured()

        assert error.code == ErrorCode.GIT_NOT_CONFIGURED
        assert any("user.name" in s for s in error.suggestions)
        assert any("user.email" in s for s in error.suggestions)


class TestApiKeyErrors:
    """Test API key error factories."""

    def test_api_key_invalid_anthropic(self):
        """Test api_key_invalid for Anthropic."""
        error = OnboardingError.api_key_invalid("anthropic")

        assert error.code == ErrorCode.API_KEY_INVALID
        assert "Anthropic" in error.title
        assert any("console.anthropic.com" in s for s in error.suggestions)
        assert any("ANTHROPIC_API_KEY" in s for s in error.suggestions)
        assert any("sk-ant-" in s for s in error.suggestions)

    def test_api_key_invalid_openai(self):
        """Test api_key_invalid for OpenAI."""
        error = OnboardingError.api_key_invalid("openai")

        assert error.code == ErrorCode.API_KEY_INVALID
        assert "Openai" in error.title
        assert any("platform.openai.com" in s for s in error.suggestions)
        assert any("OPENAI_API_KEY" in s for s in error.suggestions)

    def test_api_key_invalid_google(self):
        """Test api_key_invalid for Google."""
        error = OnboardingError.api_key_invalid("google")

        assert error.code == ErrorCode.API_KEY_INVALID
        assert "Google" in error.title
        assert any("aistudio.google.com" in s for s in error.suggestions)
        assert any("GOOGLE_API_KEY" in s for s in error.suggestions)

    def test_api_key_rate_limited_with_retry(self):
        """Test api_key_rate_limited with retry_after."""
        error = OnboardingError.api_key_rate_limited("anthropic", retry_after=60)

        assert error.code == ErrorCode.API_KEY_RATE_LIMITED
        assert error.critical is False
        assert any("60 seconds" in s for s in error.suggestions)
        assert error.context["retry_after"] == 60

    def test_api_key_rate_limited_without_retry(self):
        """Test api_key_rate_limited without retry_after."""
        error = OnboardingError.api_key_rate_limited("openai")

        assert error.code == ErrorCode.API_KEY_RATE_LIMITED
        assert any("few minutes" in s for s in error.suggestions)


class TestNetworkErrors:
    """Test network error factories."""

    def test_network_error(self):
        """Test network_error."""
        error = OnboardingError.network_error()

        assert error.code == ErrorCode.NETWORK_ERROR
        assert error.critical is False
        assert error.can_retry is True
        assert any("internet" in s.lower() for s in error.suggestions)

    def test_network_timeout(self):
        """Test network_timeout with custom timeout."""
        error = OnboardingError.network_timeout(timeout_seconds=45)

        assert error.code == ErrorCode.NETWORK_TIMEOUT
        assert "45" in error.description
        assert error.context["timeout_seconds"] == 45


class TestPortError:
    """Test port in use error."""

    def test_port_in_use_windows(self):
        """Test port_in_use on Windows."""
        with patch("platform.system", return_value="Windows"):
            error = OnboardingError.port_in_use(8080)

            assert error.code == ErrorCode.PORT_IN_USE
            assert "8080" in error.title
            assert any("netstat" in s for s in error.suggestions)
            assert any("--port 8081" in s for s in error.suggestions)

    def test_port_in_use_unix(self):
        """Test port_in_use on Unix."""
        with patch("platform.system", return_value="Linux"):
            error = OnboardingError.port_in_use(3000)

            assert error.code == ErrorCode.PORT_IN_USE
            assert "3000" in error.title
            assert any("lsof" in s for s in error.suggestions)


class TestKeychainError:
    """Test keychain unavailable error."""

    def test_keychain_unavailable_macos(self):
        """Test keychain_unavailable on macOS."""
        with patch("platform.system", return_value="Darwin"):
            error = OnboardingError.keychain_unavailable()

            assert error.code == ErrorCode.KEYCHAIN_UNAVAILABLE
            assert "Keychain" in error.context["keychain"]
            assert error.can_skip is True

    def test_keychain_unavailable_windows(self):
        """Test keychain_unavailable on Windows."""
        with patch("platform.system", return_value="Windows"):
            error = OnboardingError.keychain_unavailable()

            assert error.code == ErrorCode.KEYCHAIN_UNAVAILABLE
            assert "Credential Manager" in error.context["keychain"]


class TestPermissionError:
    """Test permission denied error."""

    def test_permission_denied_windows(self):
        """Test permission_denied on Windows."""
        with patch("platform.system", return_value="Windows"):
            error = OnboardingError.permission_denied("C:\\Users\\test")

            assert error.code == ErrorCode.PERMISSION_DENIED
            assert "C:\\Users\\test" in error.description
            assert any("Administrator" in s for s in error.suggestions)

    def test_permission_denied_unix(self):
        """Test permission_denied on Unix."""
        with patch("platform.system", return_value="Linux"):
            error = OnboardingError.permission_denied("/home/user/project")

            assert error.code == ErrorCode.PERMISSION_DENIED
            assert "/home/user/project" in error.description
            assert any("chmod" in s for s in error.suggestions)
            assert any("chown" in s for s in error.suggestions)


class TestConfigError:
    """Test config corrupted error."""

    def test_config_corrupted(self):
        """Test config_corrupted error."""
        error = OnboardingError.config_corrupted("/path/to/config.yaml")

        assert error.code == ErrorCode.CONFIG_CORRUPTED
        assert "/path/to/config.yaml" in error.description
        assert any("backup" in s.lower() for s in error.suggestions)
        assert any("git checkout" in s for s in error.suggestions)


class TestOnboardingInterrupted:
    """Test onboarding interrupted error."""

    def test_onboarding_interrupted(self):
        """Test onboarding_interrupted error."""
        error = OnboardingError.onboarding_interrupted()

        assert error.code == ErrorCode.ONBOARDING_INTERRUPTED
        assert error.critical is False
        assert error.can_skip is True
        assert any("gao-dev start" in s for s in error.suggestions)
        assert any("gao-dev status" in s for s in error.suggestions)


class TestOnboardingErrorHandler:
    """Test OnboardingErrorHandler class."""

    @pytest.fixture
    def console(self):
        """Create mock console."""
        return MagicMock(spec=Console)

    @pytest.fixture
    def handler(self, console):
        """Create error handler."""
        return OnboardingErrorHandler(console)

    def test_display_error(self, handler, console):
        """Test display_error shows panel."""
        error = OnboardingError.git_not_installed()

        with patch.object(error, "log_error") as mock_log:
            handler.display_error(error)

            assert console.print.called
            mock_log.assert_called_once()

    def test_get_recovery_options_all_options(self, handler):
        """Test get_recovery_options with all options available."""
        error = OnboardingError(
            code=ErrorCode.NETWORK_ERROR,
            title="Test",
            description="Test",
            can_retry=True,
            can_skip=True,
        )

        options = handler.get_recovery_options(error)

        assert "[R]etry" in options
        assert "[S]kip" in options
        assert "[E]xit" in options

    def test_get_recovery_options_retry_only(self, handler):
        """Test get_recovery_options with retry only."""
        error = OnboardingError(
            code=ErrorCode.GIT_NOT_INSTALLED,
            title="Test",
            description="Test",
            can_retry=True,
            can_skip=False,
        )

        options = handler.get_recovery_options(error)

        assert "[R]etry" in options
        assert "[S]kip" not in options
        assert "[E]xit" in options

    def test_get_recovery_options_exit_only(self, handler):
        """Test get_recovery_options with exit only."""
        error = OnboardingError(
            code=ErrorCode.GIT_NOT_INSTALLED,
            title="Test",
            description="Test",
            can_retry=False,
            can_skip=False,
        )

        options = handler.get_recovery_options(error)

        assert "[R]etry" not in options
        assert "[S]kip" not in options
        assert "[E]xit" in options

    def test_prompt_recovery_retry(self, handler, console):
        """Test prompt_recovery returns RETRY."""
        error = OnboardingError.git_not_installed()
        console.input.return_value = "r"

        action = handler.prompt_recovery(error)

        assert action == RecoveryAction.RETRY

    def test_prompt_recovery_skip(self, handler, console):
        """Test prompt_recovery returns SKIP."""
        error = OnboardingError(
            code=ErrorCode.KEYCHAIN_UNAVAILABLE,
            title="Test",
            description="Test",
            can_skip=True,
        )
        console.input.return_value = "s"

        action = handler.prompt_recovery(error)

        assert action == RecoveryAction.SKIP

    def test_prompt_recovery_exit(self, handler, console):
        """Test prompt_recovery returns EXIT."""
        error = OnboardingError.git_not_installed()
        console.input.return_value = "e"

        action = handler.prompt_recovery(error)

        assert action == RecoveryAction.EXIT

    def test_prompt_recovery_full_word(self, handler, console):
        """Test prompt_recovery accepts full words."""
        error = OnboardingError.git_not_installed()
        console.input.return_value = "retry"

        action = handler.prompt_recovery(error)

        assert action == RecoveryAction.RETRY

    def test_prompt_recovery_invalid_then_valid(self, handler, console):
        """Test prompt_recovery reprompts on invalid input."""
        error = OnboardingError.git_not_installed()
        console.input.side_effect = ["invalid", "x", "r"]

        action = handler.prompt_recovery(error)

        assert action == RecoveryAction.RETRY
        assert console.input.call_count == 3
        # Should have printed error messages
        assert console.print.call_count >= 2

    def test_handle_error_complete_flow(self, handler, console):
        """Test handle_error completes full flow."""
        error = OnboardingError.git_not_installed()
        console.input.return_value = "e"

        with patch.object(error, "log_error"):
            action = handler.handle_error(error)

        assert action == RecoveryAction.EXIT
        assert console.print.called


class TestHandleErrorWithRecovery:
    """Test handle_error_with_recovery async function."""

    @pytest.mark.asyncio
    async def test_handle_error_with_recovery(self):
        """Test async wrapper returns correct action."""
        console = MagicMock(spec=Console)
        console.input.return_value = "e"

        error = OnboardingError.git_not_installed()
        action = await handle_error_with_recovery(error, console)

        assert action == RecoveryAction.EXIT


class TestErrorFormatting:
    """Test error formatting consistency."""

    def test_all_errors_have_title(self):
        """Test all error factories produce titled errors."""
        errors = [
            OnboardingError.git_not_installed(),
            OnboardingError.git_not_configured(),
            OnboardingError.api_key_invalid("anthropic"),
            OnboardingError.api_key_rate_limited("openai"),
            OnboardingError.network_error(),
            OnboardingError.network_timeout(),
            OnboardingError.port_in_use(8000),
            OnboardingError.keychain_unavailable(),
            OnboardingError.permission_denied("/path"),
            OnboardingError.config_corrupted("/path"),
            OnboardingError.onboarding_interrupted(),
        ]

        for error in errors:
            assert error.title, f"Error {error.code.value} has no title"
            assert len(error.title) > 0

    def test_all_errors_have_suggestions(self):
        """Test all error factories produce actionable suggestions."""
        errors = [
            OnboardingError.git_not_installed(),
            OnboardingError.git_not_configured(),
            OnboardingError.api_key_invalid("anthropic"),
            OnboardingError.api_key_rate_limited("openai"),
            OnboardingError.network_error(),
            OnboardingError.network_timeout(),
            OnboardingError.port_in_use(8000),
            OnboardingError.keychain_unavailable(),
            OnboardingError.permission_denied("/path"),
            OnboardingError.config_corrupted("/path"),
            OnboardingError.onboarding_interrupted(),
        ]

        for error in errors:
            assert len(error.suggestions) > 0, f"Error {error.code.value} has no suggestions"

    def test_all_errors_have_description(self):
        """Test all error factories produce descriptions."""
        errors = [
            OnboardingError.git_not_installed(),
            OnboardingError.git_not_configured(),
            OnboardingError.api_key_invalid("anthropic"),
            OnboardingError.api_key_rate_limited("openai"),
            OnboardingError.network_error(),
            OnboardingError.network_timeout(),
            OnboardingError.port_in_use(8000),
            OnboardingError.keychain_unavailable(),
            OnboardingError.permission_denied("/path"),
            OnboardingError.config_corrupted("/path"),
            OnboardingError.onboarding_interrupted(),
        ]

        for error in errors:
            assert error.description, f"Error {error.code.value} has no description"
