"""Unit tests for error handler with recovery flows.

Epic 42: Streamlined Onboarding Experience
Story 42.3: Error Messages and Recovery Flows
"""

from unittest.mock import MagicMock, patch, call

import pytest
from rich.console import Console

from gao_dev.core.errors import ErrorCode, OnboardingError, RecoveryAction
from gao_dev.core.error_handler import (
    ErrorRecoveryManager,
    handle_onboarding_error,
    create_error_for_exception,
)


class TestErrorRecoveryManager:
    """Test ErrorRecoveryManager class."""

    @pytest.fixture
    def console(self):
        """Create mock console."""
        return MagicMock(spec=Console)

    @pytest.fixture
    def manager(self, console):
        """Create error recovery manager."""
        return ErrorRecoveryManager(console, max_retries=3)

    def test_initialization(self, manager):
        """Test manager initializes correctly."""
        assert manager.max_retries == 3
        assert manager.retry_counts == {}
        assert manager.skipped_steps == []

    def test_reset(self, manager):
        """Test reset clears state."""
        manager.retry_counts["E001"] = 2
        manager.skipped_steps.append("step1")

        manager.reset()

        assert manager.retry_counts == {}
        assert manager.skipped_steps == []

    def test_get_retry_count_default(self, manager):
        """Test get_retry_count returns 0 for new error."""
        count = manager.get_retry_count(ErrorCode.GIT_NOT_INSTALLED)
        assert count == 0

    def test_get_retry_count_existing(self, manager):
        """Test get_retry_count returns existing count."""
        manager.retry_counts["E001"] = 2
        count = manager.get_retry_count(ErrorCode.GIT_NOT_INSTALLED)
        assert count == 2

    def test_increment_retry(self, manager):
        """Test increment_retry increases count."""
        count1 = manager.increment_retry(ErrorCode.GIT_NOT_INSTALLED)
        count2 = manager.increment_retry(ErrorCode.GIT_NOT_INSTALLED)

        assert count1 == 1
        assert count2 == 2
        assert manager.get_retry_count(ErrorCode.GIT_NOT_INSTALLED) == 2

    def test_can_retry_under_limit(self, manager):
        """Test can_retry returns True under limit."""
        manager.retry_counts["E001"] = 2

        assert manager.can_retry(ErrorCode.GIT_NOT_INSTALLED) is True

    def test_can_retry_at_limit(self, manager):
        """Test can_retry returns False at limit."""
        manager.retry_counts["E001"] = 3

        assert manager.can_retry(ErrorCode.GIT_NOT_INSTALLED) is False

    def test_can_retry_over_limit(self, manager):
        """Test can_retry returns False over limit."""
        manager.retry_counts["E001"] = 5

        assert manager.can_retry(ErrorCode.GIT_NOT_INSTALLED) is False

    def test_add_skipped(self, manager):
        """Test add_skipped tracks step."""
        manager.add_skipped("git_check")
        manager.add_skipped("keychain_setup")

        assert manager.skipped_steps == ["git_check", "keychain_setup"]

    def test_get_skipped_steps_returns_copy(self, manager):
        """Test get_skipped_steps returns copy."""
        manager.add_skipped("step1")

        steps = manager.get_skipped_steps()
        steps.append("step2")

        assert manager.skipped_steps == ["step1"]

    def test_display_error(self, manager, console):
        """Test display_error shows error panel."""
        error = OnboardingError.git_not_installed()

        with patch.object(error, "log_error") as mock_log:
            manager.display_error(error)

            assert console.print.called
            mock_log.assert_called_once()

    def test_display_max_retries_exceeded(self, manager, console):
        """Test display_max_retries_exceeded shows warning."""
        error = OnboardingError.git_not_installed()
        manager.retry_counts["E001"] = 3

        manager.display_max_retries_exceeded(error)

        # Should print warning message
        console.print.assert_called()
        call_str = str(console.print.call_args)
        assert "retries" in call_str.lower() or "3" in call_str

    def test_prompt_recovery_with_retries_left(self, manager, console):
        """Test prompt_recovery shows retries left."""
        error = OnboardingError.git_not_installed()
        manager.retry_counts["E001"] = 1
        console.input.return_value = "r"

        manager.prompt_recovery(error)

        # Should show "2 left"
        call_str = str(console.print.call_args_list)
        assert "2 left" in call_str

    def test_prompt_recovery_increments_retry(self, manager, console):
        """Test prompt_recovery increments retry count."""
        error = OnboardingError.git_not_installed()
        console.input.return_value = "r"

        manager.prompt_recovery(error)

        assert manager.get_retry_count(ErrorCode.GIT_NOT_INSTALLED) == 1

    def test_prompt_recovery_respects_max_retries(self, manager, console):
        """Test prompt_recovery hides retry when maxed."""
        error = OnboardingError.git_not_installed()
        manager.retry_counts["E001"] = 3
        console.input.return_value = "e"

        manager.prompt_recovery(error)

        # Should not show retry option
        call_str = str(console.print.call_args_list)
        assert "Retry" not in call_str or "0 left" in call_str

    def test_handle_error_tracks_skip(self, manager, console):
        """Test handle_error tracks skipped step."""
        error = OnboardingError(
            code=ErrorCode.KEYCHAIN_UNAVAILABLE,
            title="Test",
            description="Test",
            can_skip=True,
        )
        console.input.return_value = "s"

        manager.handle_error(error, step_name="keychain_check")

        assert "keychain_check" in manager.skipped_steps

    def test_handle_error_shows_max_retries_message(self, manager, console):
        """Test handle_error shows max retries message."""
        error = OnboardingError.git_not_installed()
        manager.retry_counts["E001"] = 3
        console.input.return_value = "e"

        with patch.object(manager, "display_max_retries_exceeded") as mock_display:
            manager.handle_error(error)
            mock_display.assert_called_once_with(error)

    def test_display_summary_empty(self, manager, console):
        """Test display_summary with no errors."""
        manager.display_summary()

        # Should not print anything
        assert not console.print.called

    def test_display_summary_with_retries(self, manager, console):
        """Test display_summary shows retry counts."""
        manager.retry_counts["E001"] = 2
        manager.retry_counts["E201"] = 1

        manager.display_summary()

        call_str = str(console.print.call_args_list)
        assert "E001" in call_str
        assert "E201" in call_str

    def test_display_summary_with_skipped(self, manager, console):
        """Test display_summary shows skipped steps."""
        manager.add_skipped("git_check")
        manager.add_skipped("keychain_setup")

        manager.display_summary()

        call_str = str(console.print.call_args_list)
        assert "git_check" in call_str
        assert "keychain_setup" in call_str


class TestHandleOnboardingError:
    """Test handle_onboarding_error async function."""

    @pytest.fixture
    def console(self):
        """Create mock console."""
        return MagicMock(spec=Console)

    @pytest.mark.asyncio
    async def test_handle_with_new_manager(self, console):
        """Test handle_onboarding_error creates manager."""
        error = OnboardingError.git_not_installed()
        console.input.return_value = "e"

        action = await handle_onboarding_error(error, console)

        assert action == RecoveryAction.EXIT

    @pytest.mark.asyncio
    async def test_handle_with_existing_manager(self, console):
        """Test handle_onboarding_error uses existing manager."""
        manager = ErrorRecoveryManager(console)
        error = OnboardingError.git_not_installed()
        console.input.return_value = "r"

        action = await handle_onboarding_error(error, console, manager=manager)

        assert action == RecoveryAction.RETRY
        assert manager.get_retry_count(ErrorCode.GIT_NOT_INSTALLED) == 1

    @pytest.mark.asyncio
    async def test_handle_with_step_name(self, console):
        """Test handle_onboarding_error tracks step name."""
        manager = ErrorRecoveryManager(console)
        error = OnboardingError(
            code=ErrorCode.KEYCHAIN_UNAVAILABLE,
            title="Test",
            description="Test",
            can_skip=True,
        )
        console.input.return_value = "s"

        await handle_onboarding_error(
            error, console, step_name="keychain_check", manager=manager
        )

        assert "keychain_check" in manager.get_skipped_steps()


class TestCreateErrorForException:
    """Test create_error_for_exception function."""

    def test_timeout_exception(self):
        """Test timeout exception creates network timeout error."""
        exc = Exception("Connection timed out after 30 seconds")

        error = create_error_for_exception(exc)

        assert error.code == ErrorCode.NETWORK_TIMEOUT

    def test_network_exception(self):
        """Test network exception creates network error."""
        exc = Exception("Connection refused - network unreachable")

        error = create_error_for_exception(exc)

        assert error.code == ErrorCode.NETWORK_ERROR

    def test_permission_exception(self):
        """Test permission exception creates permission error."""
        exc = Exception("Permission denied: /home/user/file")
        context = {"path": "/home/user/file"}

        error = create_error_for_exception(exc, context)

        assert error.code == ErrorCode.PERMISSION_DENIED
        assert "/home/user/file" in error.description

    def test_git_not_found_exception(self):
        """Test git not found exception."""
        exc = Exception("git not found in PATH")

        error = create_error_for_exception(exc)

        assert error.code == ErrorCode.GIT_NOT_INSTALLED

    def test_git_config_exception(self):
        """Test git config exception."""
        exc = Exception("git config user.name not set")

        error = create_error_for_exception(exc)

        assert error.code == ErrorCode.GIT_NOT_CONFIGURED

    def test_api_key_invalid_exception(self):
        """Test API key invalid exception."""
        exc = Exception("API key authentication failed")
        context = {"provider": "anthropic"}

        error = create_error_for_exception(exc, context)

        assert error.code == ErrorCode.API_KEY_INVALID
        assert error.context["provider"] == "anthropic"

    def test_rate_limit_exception(self):
        """Test rate limit exception."""
        exc = Exception("API rate limit exceeded")
        context = {"provider": "openai"}

        error = create_error_for_exception(exc, context)

        assert error.code == ErrorCode.API_KEY_RATE_LIMITED

    def test_port_exception(self):
        """Test port in use exception."""
        exc = Exception("Address already in use: port 8000")
        context = {"port": 8000}

        error = create_error_for_exception(exc, context)

        assert error.code == ErrorCode.PORT_IN_USE
        assert "8000" in error.title

    def test_config_exception(self):
        """Test config parse exception."""
        exc = Exception("YAML parse error in config file")
        context = {"path": "/path/to/config.yaml"}

        error = create_error_for_exception(exc, context)

        assert error.code == ErrorCode.CONFIG_CORRUPTED

    def test_unknown_exception(self):
        """Test unknown exception creates interrupted error."""
        exc = Exception("Some random error")

        error = create_error_for_exception(exc)

        assert error.code == ErrorCode.ONBOARDING_INTERRUPTED
        assert "Some random error" in error.description

    def test_exception_with_empty_context(self):
        """Test exception with no context."""
        exc = Exception("Error")

        error = create_error_for_exception(exc)

        assert error is not None
        assert error.code is not None


class TestRetryLogic:
    """Test retry logic and limits."""

    @pytest.fixture
    def console(self):
        """Create mock console."""
        return MagicMock(spec=Console)

    def test_retry_until_max(self, console):
        """Test retry increments until max."""
        manager = ErrorRecoveryManager(console, max_retries=2)

        # First retry
        assert manager.can_retry(ErrorCode.GIT_NOT_INSTALLED) is True
        manager.increment_retry(ErrorCode.GIT_NOT_INSTALLED)

        # Second retry
        assert manager.can_retry(ErrorCode.GIT_NOT_INSTALLED) is True
        manager.increment_retry(ErrorCode.GIT_NOT_INSTALLED)

        # No more retries
        assert manager.can_retry(ErrorCode.GIT_NOT_INSTALLED) is False

    def test_different_errors_tracked_separately(self, console):
        """Test different errors have separate retry counts."""
        manager = ErrorRecoveryManager(console, max_retries=2)

        manager.increment_retry(ErrorCode.GIT_NOT_INSTALLED)
        manager.increment_retry(ErrorCode.GIT_NOT_INSTALLED)

        # GIT_NOT_INSTALLED is maxed
        assert manager.can_retry(ErrorCode.GIT_NOT_INSTALLED) is False

        # NETWORK_ERROR is still available
        assert manager.can_retry(ErrorCode.NETWORK_ERROR) is True


class TestErrorLogging:
    """Test error logging functionality."""

    @pytest.fixture
    def console(self):
        """Create mock console."""
        return MagicMock(spec=Console)

    def test_error_logged_on_display(self, console):
        """Test error is logged when displayed."""
        manager = ErrorRecoveryManager(console)
        error = OnboardingError.git_not_installed()

        with patch("gao_dev.core.errors.logger") as mock_logger:
            manager.display_error(error)

            mock_logger.error.assert_called_once()
            call_kwargs = mock_logger.error.call_args[1]
            assert call_kwargs["error_code"] == "E001"

    def test_recovery_action_logged(self, console):
        """Test recovery action is logged."""
        manager = ErrorRecoveryManager(console)
        error = OnboardingError.git_not_installed()
        console.input.return_value = "r"

        # The logger is bound in __init__, so we need to mock the bound logger
        with patch.object(manager, "logger") as mock_logger:
            manager.prompt_recovery(error)

            # Should log the action
            assert mock_logger.info.called


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def console(self):
        """Create mock console."""
        return MagicMock(spec=Console)

    def test_zero_max_retries(self, console):
        """Test manager with zero max retries."""
        manager = ErrorRecoveryManager(console, max_retries=0)

        assert manager.can_retry(ErrorCode.GIT_NOT_INSTALLED) is False

    def test_case_insensitive_input(self, console):
        """Test input is case insensitive."""
        manager = ErrorRecoveryManager(console)
        error = OnboardingError.git_not_installed()

        # Test uppercase
        console.input.return_value = "R"
        action = manager.prompt_recovery(error)
        assert action == RecoveryAction.RETRY

    def test_whitespace_trimmed(self, console):
        """Test whitespace is trimmed from input."""
        manager = ErrorRecoveryManager(console)
        error = OnboardingError.git_not_installed()

        console.input.return_value = "  r  "
        action = manager.prompt_recovery(error)
        assert action == RecoveryAction.RETRY

    def test_empty_suggestions(self):
        """Test error with empty suggestions."""
        error = OnboardingError(
            code=ErrorCode.ONBOARDING_INTERRUPTED,
            title="Test",
            description="Test",
            suggestions=[],
        )

        # Should not crash
        panel = error.to_panel()
        assert panel is not None

    def test_very_long_path(self, console):
        """Test error with very long path."""
        long_path = "/very/long/path/" * 50
        error = OnboardingError.permission_denied(long_path)

        # Should not crash
        panel = error.to_panel()
        assert panel is not None

    def test_special_characters_in_path(self, console):
        """Test error with special characters in path."""
        special_path = "/path/with spaces/and'quotes/and\"quotes"
        error = OnboardingError.permission_denied(special_path)

        assert special_path in error.description
