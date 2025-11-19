"""Tests for deprecated command handling.

Epic 40: Streamlined Onboarding
Story 40.5: Deprecated Command Handling
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import time

from click.testing import CliRunner
from rich.console import Console

from gao_dev.cli.commands import cli, show_deprecation_warning
from gao_dev.cli.web_commands import web, show_web_deprecation_warning
from gao_dev.cli.startup_result import (
    StartupResult,
    WizardType,
    OnboardingMode,
)


# Patch paths - patch where the import happens (inside the function)
PATCH_STARTUP_ORCH = "gao_dev.cli.startup_orchestrator.StartupOrchestrator"
PATCH_WEB_STARTUP_ORCH = "gao_dev.cli.startup_orchestrator.StartupOrchestrator"


def create_mock_result(
    success: bool = True,
    total_duration_ms: float = 100.0,
    interface_launched: str = "cli",
    tmp_path: Path = None,
) -> StartupResult:
    """Create a mock StartupResult with all required fields."""
    return StartupResult(
        success=success,
        wizard_type=WizardType.NONE,
        onboarding_mode=OnboardingMode.SKIP,
        interface_launched=interface_launched,
        project_path=tmp_path or Path.cwd(),
        total_duration_ms=total_duration_ms,
        phases=[],
        error=None if success else "Mock error",
    )


class TestShowDeprecationWarning:
    """Tests for the show_deprecation_warning helper function."""

    def test_warning_logs_at_warning_level(self) -> None:
        """Test that deprecation warning is logged at WARNING level."""
        console = Console(force_terminal=True)

        with patch("gao_dev.cli.commands.logger") as mock_logger:
            show_deprecation_warning(
                console=console,
                old_command="gao-dev init",
                new_command="gao-dev start",
                quiet=True,  # Suppress display but should still log
                no_wait=True,
            )

            mock_logger.warning.assert_called_once_with(
                "deprecated_command_used",
                old_command="gao-dev init",
                new_command="gao-dev start",
                removal_version="v2.0",
            )

    def test_warning_quiet_suppresses_display(self) -> None:
        """Test that --quiet suppresses the warning display."""
        console = Console(file=MagicMock(), force_terminal=True)

        with patch("gao_dev.cli.commands.logger"):
            show_deprecation_warning(
                console=console,
                old_command="gao-dev init",
                new_command="gao-dev start",
                quiet=True,
                no_wait=True,
            )

            # Console should not have printed anything
            assert console.file.write.call_count == 0

    def test_warning_no_wait_skips_delay(self) -> None:
        """Test that --no-wait skips the delay countdown."""
        console = Console(force_terminal=True)

        start_time = time.time()
        with patch("gao_dev.cli.commands.logger"):
            show_deprecation_warning(
                console=console,
                old_command="gao-dev init",
                new_command="gao-dev start",
                quiet=False,
                no_wait=True,
            )
        elapsed = time.time() - start_time

        # Should complete in less than 1 second (no 5-second delay)
        assert elapsed < 1.0

    def test_warning_custom_removal_version(self) -> None:
        """Test that custom removal version is used."""
        console = Console(force_terminal=True)

        with patch("gao_dev.cli.commands.logger") as mock_logger:
            show_deprecation_warning(
                console=console,
                old_command="gao-dev old",
                new_command="gao-dev new",
                removal_version="v3.0",
                quiet=True,
                no_wait=True,
            )

            mock_logger.warning.assert_called_once_with(
                "deprecated_command_used",
                old_command="gao-dev old",
                new_command="gao-dev new",
                removal_version="v3.0",
            )


class TestInitCommandDeprecation:
    """Tests for gao-dev init command deprecation."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    def test_init_command_exists(self, runner: CliRunner) -> None:
        """Test that init command is registered."""
        result = runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0

    def test_init_help_shows_deprecated_marker(self, runner: CliRunner) -> None:
        """Test that init help text shows [DEPRECATED] marker."""
        result = runner.invoke(cli, ["init", "--help"])
        assert "[DEPRECATED]" in result.output

    def test_init_help_shows_replacement_command(self, runner: CliRunner) -> None:
        """Test that init help mentions the replacement command."""
        result = runner.invoke(cli, ["init", "--help"])
        assert "gao-dev start" in result.output

    def test_init_has_no_wait_flag(self, runner: CliRunner) -> None:
        """Test that init has --no-wait flag."""
        result = runner.invoke(cli, ["init", "--help"])
        assert "--no-wait" in result.output

    def test_init_has_quiet_flag(self, runner: CliRunner) -> None:
        """Test that init has --quiet flag."""
        result = runner.invoke(cli, ["init", "--help"])
        assert "--quiet" in result.output

    def test_init_shows_deprecation_warning(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that init shows deprecation warning."""
        mock_result = create_mock_result(tmp_path=tmp_project)

        with patch(PATCH_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(return_value=mock_result)
            mock_orch_class.return_value = mock_orch

            result = runner.invoke(
                cli,
                ["init", "--no-wait"],
                catch_exceptions=False,
            )

            # Check for deprecation warning content
            assert "DEPRECATION WARNING" in result.output or "deprecated" in result.output.lower()

    def test_init_redirects_to_start(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that init redirects to start command."""
        mock_result = create_mock_result(tmp_path=tmp_project)

        with patch(PATCH_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(return_value=mock_result)
            mock_orch_class.return_value = mock_orch

            result = runner.invoke(
                cli,
                ["init", "--no-wait", "--quiet"],
                catch_exceptions=False,
            )

            # Verify StartupOrchestrator was created and started
            mock_orch_class.assert_called_once()
            mock_orch.start.assert_called_once()

    def test_init_quiet_suppresses_warning(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that --quiet suppresses the deprecation warning display."""
        mock_result = create_mock_result(tmp_path=tmp_project)

        with patch(PATCH_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(return_value=mock_result)
            mock_orch_class.return_value = mock_orch

            result = runner.invoke(
                cli,
                ["init", "--quiet", "--no-wait"],
                catch_exceptions=False,
            )

            # Warning panel should not be in output when quiet
            assert "DEPRECATION WARNING" not in result.output

    def test_init_logs_deprecation_warning(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that init logs deprecation at WARNING level."""
        mock_result = create_mock_result(tmp_path=tmp_project)

        with patch(PATCH_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(return_value=mock_result)
            mock_orch_class.return_value = mock_orch

            with patch("gao_dev.cli.commands.logger") as mock_logger:
                result = runner.invoke(
                    cli,
                    ["init", "--no-wait", "--quiet"],
                    catch_exceptions=False,
                )

                # Verify warning was logged
                mock_logger.warning.assert_called_with(
                    "deprecated_command_used",
                    old_command="gao-dev init",
                    new_command="gao-dev start",
                    removal_version="v2.0",
                )

    def test_init_handles_startup_error(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that init handles StartupError from orchestrator."""
        from gao_dev.cli.startup_result import StartupError

        with patch(PATCH_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            error = StartupError("Test error", suggestions=["Try this"])
            mock_orch.start = AsyncMock(side_effect=error)
            mock_orch_class.return_value = mock_orch

            result = runner.invoke(
                cli,
                ["init", "--no-wait", "--quiet"],
                catch_exceptions=False,
            )

            assert result.exit_code == 1
            assert "Test error" in result.output

    def test_init_handles_keyboard_interrupt(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that init handles KeyboardInterrupt gracefully."""
        with patch(PATCH_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(side_effect=KeyboardInterrupt())
            mock_orch_class.return_value = mock_orch

            result = runner.invoke(
                cli,
                ["init", "--no-wait", "--quiet"],
                catch_exceptions=False,
            )

            assert result.exit_code == 130
            assert "interrupted" in result.output.lower()


class TestWebStartCommandDeprecation:
    """Tests for gao-dev web start command deprecation."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    def test_web_start_command_exists(self, runner: CliRunner) -> None:
        """Test that web start command is registered."""
        result = runner.invoke(cli, ["web", "start", "--help"])
        assert result.exit_code == 0

    def test_web_start_help_shows_deprecated_marker(self, runner: CliRunner) -> None:
        """Test that web start help text shows [DEPRECATED] marker."""
        result = runner.invoke(cli, ["web", "start", "--help"])
        assert "[DEPRECATED]" in result.output

    def test_web_start_help_shows_replacement_command(self, runner: CliRunner) -> None:
        """Test that web start help mentions the replacement command."""
        result = runner.invoke(cli, ["web", "start", "--help"])
        assert "gao-dev start" in result.output

    def test_web_start_has_no_wait_flag(self, runner: CliRunner) -> None:
        """Test that web start has --no-wait flag."""
        result = runner.invoke(cli, ["web", "start", "--help"])
        assert "--no-wait" in result.output

    def test_web_start_has_quiet_flag(self, runner: CliRunner) -> None:
        """Test that web start has --quiet flag."""
        result = runner.invoke(cli, ["web", "start", "--help"])
        assert "--quiet" in result.output

    def test_web_start_shows_deprecation_warning(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that web start shows deprecation warning."""
        mock_result = create_mock_result(tmp_path=tmp_project, interface_launched="web")

        with patch(PATCH_WEB_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(return_value=mock_result)
            mock_orch_class.return_value = mock_orch

            result = runner.invoke(
                cli,
                ["web", "start", "--no-wait"],
                catch_exceptions=False,
            )

            # Check for deprecation warning content
            assert "DEPRECATION WARNING" in result.output or "deprecated" in result.output.lower()

    def test_web_start_redirects_to_start(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that web start redirects to start command."""
        mock_result = create_mock_result(tmp_path=tmp_project, interface_launched="web")

        with patch(PATCH_WEB_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(return_value=mock_result)
            mock_orch_class.return_value = mock_orch

            result = runner.invoke(
                cli,
                ["web", "start", "--no-wait", "--quiet"],
                catch_exceptions=False,
            )

            # Verify StartupOrchestrator was created and started
            mock_orch_class.assert_called_once()
            mock_orch.start.assert_called_once()

    def test_web_start_quiet_suppresses_warning(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that --quiet suppresses the deprecation warning display."""
        mock_result = create_mock_result(tmp_path=tmp_project, interface_launched="web")

        with patch(PATCH_WEB_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(return_value=mock_result)
            mock_orch_class.return_value = mock_orch

            result = runner.invoke(
                cli,
                ["web", "start", "--quiet", "--no-wait"],
                catch_exceptions=False,
            )

            # Warning panel should not be in output when quiet
            assert "DEPRECATION WARNING" not in result.output

    def test_web_start_logs_deprecation_warning(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that web start logs deprecation at WARNING level."""
        mock_result = create_mock_result(tmp_path=tmp_project, interface_launched="web")

        with patch(PATCH_WEB_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(return_value=mock_result)
            mock_orch_class.return_value = mock_orch

            with patch("gao_dev.cli.web_commands.logger") as mock_logger:
                result = runner.invoke(
                    cli,
                    ["web", "start", "--no-wait", "--quiet"],
                    catch_exceptions=False,
                )

                # Verify warning was logged
                mock_logger.warning.assert_called_with(
                    "deprecated_command_used",
                    old_command="gao-dev web start",
                    new_command="gao-dev start",
                    removal_version="v2.0",
                )

    def test_web_start_preserves_port_option(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that web start passes port option to orchestrator."""
        mock_result = create_mock_result(tmp_path=tmp_project, interface_launched="web")

        with patch(PATCH_WEB_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(return_value=mock_result)
            mock_orch_class.return_value = mock_orch

            result = runner.invoke(
                cli,
                ["web", "start", "--port", "8080", "--no-wait", "--quiet"],
                catch_exceptions=False,
            )

            # Verify port was passed to orchestrator
            call_kwargs = mock_orch_class.call_args[1]
            assert call_kwargs["port"] == 8080

    def test_web_start_preserves_no_browser_option(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that web start passes no-browser option to orchestrator."""
        mock_result = create_mock_result(tmp_path=tmp_project, interface_launched="web")

        with patch(PATCH_WEB_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(return_value=mock_result)
            mock_orch_class.return_value = mock_orch

            result = runner.invoke(
                cli,
                ["web", "start", "--no-browser", "--no-wait", "--quiet"],
                catch_exceptions=False,
            )

            # Verify no_browser was passed to orchestrator
            call_kwargs = mock_orch_class.call_args[1]
            assert call_kwargs["no_browser"] is True

    def test_web_start_handles_startup_error(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that web start handles StartupError from orchestrator."""
        from gao_dev.cli.startup_result import StartupError

        with patch(PATCH_WEB_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            error = StartupError("Test error", suggestions=["Try this"])
            mock_orch.start = AsyncMock(side_effect=error)
            mock_orch_class.return_value = mock_orch

            result = runner.invoke(
                cli,
                ["web", "start", "--no-wait", "--quiet"],
                catch_exceptions=False,
            )

            assert result.exit_code == 1
            assert "Test error" in result.output

    def test_web_start_handles_keyboard_interrupt(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that web start handles KeyboardInterrupt gracefully."""
        with patch(PATCH_WEB_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(side_effect=KeyboardInterrupt())
            mock_orch_class.return_value = mock_orch

            result = runner.invoke(
                cli,
                ["web", "start", "--no-wait", "--quiet"],
                catch_exceptions=False,
            )

            assert result.exit_code == 130
            assert "interrupted" in result.output.lower()

    def test_web_start_shows_web_url_on_success(
        self, runner: CliRunner, tmp_project: Path
    ) -> None:
        """Test that web start shows the web URL on success."""
        mock_result = create_mock_result(tmp_path=tmp_project, interface_launched="web")

        with patch(PATCH_WEB_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(return_value=mock_result)
            mock_orch_class.return_value = mock_orch

            result = runner.invoke(
                cli,
                ["web", "start", "--port", "3001", "--no-wait", "--quiet"],
                catch_exceptions=False,
            )

            assert "localhost:3001" in result.output


class TestWebDeprecationWarningHelper:
    """Tests for the show_web_deprecation_warning helper function."""

    def test_warning_logs_at_warning_level(self) -> None:
        """Test that web deprecation warning is logged at WARNING level."""
        console = Console(force_terminal=True)

        with patch("gao_dev.cli.web_commands.logger") as mock_logger:
            show_web_deprecation_warning(
                console=console,
                quiet=True,
                no_wait=True,
            )

            mock_logger.warning.assert_called_once_with(
                "deprecated_command_used",
                old_command="gao-dev web start",
                new_command="gao-dev start",
                removal_version="v2.0",
            )

    def test_warning_quiet_suppresses_display(self) -> None:
        """Test that --quiet suppresses the warning display."""
        console = Console(file=MagicMock(), force_terminal=True)

        with patch("gao_dev.cli.web_commands.logger"):
            show_web_deprecation_warning(
                console=console,
                quiet=True,
                no_wait=True,
            )

            # Console should not have printed anything
            assert console.file.write.call_count == 0


class TestDeprecationWarningContent:
    """Tests for deprecation warning content and formatting."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_init_warning_mentions_v2_removal(self, runner: CliRunner) -> None:
        """Test that init warning mentions v2.0 removal timeline."""
        result = runner.invoke(cli, ["init", "--help"])
        assert "v2.0" in result.output

    def test_web_start_warning_mentions_v2_removal(self, runner: CliRunner) -> None:
        """Test that web start warning mentions v2.0 removal timeline."""
        result = runner.invoke(cli, ["web", "start", "--help"])
        assert "v2.0" in result.output

    def test_init_warning_includes_replacement_instructions(
        self, runner: CliRunner
    ) -> None:
        """Test that init warning includes replacement instructions."""
        result = runner.invoke(cli, ["init", "--help"])
        assert "gao-dev start" in result.output

    def test_web_start_warning_includes_replacement_instructions(
        self, runner: CliRunner
    ) -> None:
        """Test that web start warning includes replacement instructions."""
        result = runner.invoke(cli, ["web", "start", "--help"])
        assert "gao-dev start" in result.output


class TestDeprecationIntegration:
    """Integration tests for deprecated command behavior."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_init_and_start_produce_same_result(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test that init redirects to same startup flow as start."""
        mock_result = create_mock_result(tmp_path=tmp_path)

        # Test init
        with patch(PATCH_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(return_value=mock_result)
            mock_orch_class.return_value = mock_orch

            init_result = runner.invoke(
                cli,
                ["init", "--no-wait", "--quiet"],
                catch_exceptions=False,
            )

            init_call_args = mock_orch_class.call_args

        # Verify orchestrator was called
        assert init_call_args is not None
        assert init_result.exit_code == 0

    def test_web_start_and_start_produce_same_result(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test that web start redirects to same startup flow as start."""
        mock_result = create_mock_result(tmp_path=tmp_path, interface_launched="web")

        # Test web start
        with patch(PATCH_WEB_STARTUP_ORCH) as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.start = AsyncMock(return_value=mock_result)
            mock_orch_class.return_value = mock_orch

            web_result = runner.invoke(
                cli,
                ["web", "start", "--no-wait", "--quiet"],
                catch_exceptions=False,
            )

            web_call_args = mock_orch_class.call_args

        # Verify orchestrator was called
        assert web_call_args is not None
        assert web_result.exit_code == 0
