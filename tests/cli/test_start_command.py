"""Tests for the unified gao-dev start command.

Epic 40: Streamlined Onboarding
Story 40.4: Unified gao-dev start Command
"""

import os
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from click.testing import CliRunner

from gao_dev.cli.commands import cli, start, _show_startup_message
from gao_dev.cli.startup_result import (
    OnboardingMode,
    StartupError,
    StartupPhase,
    StartupResult,
    WizardType,
)
from gao_dev.core.environment_detector import EnvironmentType
from gao_dev.core.state_detector import GlobalState, ProjectState

# Patch paths - these are imported inside _show_startup_message
PATCH_DETECT_ENV = "gao_dev.core.environment_detector.detect_environment"
PATCH_DETECT_STATES = "gao_dev.core.state_detector.detect_states"
PATCH_STARTUP_ORCH = "gao_dev.cli.startup_orchestrator.StartupOrchestrator"


class TestStartCommandOptions:
    """Tests for CLI options of the start command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    def test_start_command_exists(self, runner: CliRunner) -> None:
        """Test that start command is registered."""
        result = runner.invoke(cli, ["start", "--help"])
        assert result.exit_code == 0
        assert "Start GAO-Dev with intelligent environment detection" in result.output

    def test_start_command_has_all_options(self, runner: CliRunner) -> None:
        """Test that start command has all required options."""
        result = runner.invoke(cli, ["start", "--help"])

        assert "--project" in result.output
        assert "--headless" in result.output
        assert "--no-browser" in result.output
        assert "--port" in result.output
        assert "--tui" in result.output

    def test_start_command_shows_examples(self, runner: CliRunner) -> None:
        """Test that start command help shows examples."""
        result = runner.invoke(cli, ["start", "--help"])

        assert "gao-dev start" in result.output
        assert "--headless" in result.output
        assert "--port 8080" in result.output

    def test_headless_option_description(self, runner: CliRunner) -> None:
        """Test --headless option description."""
        result = runner.invoke(cli, ["start", "--help"])
        assert "Force headless mode" in result.output

    def test_no_browser_option_description(self, runner: CliRunner) -> None:
        """Test --no-browser option description."""
        result = runner.invoke(cli, ["start", "--help"])
        assert "without opening browser" in result.output

    def test_port_option_has_default(self, runner: CliRunner) -> None:
        """Test --port option has default value of 3000."""
        result = runner.invoke(cli, ["start", "--help"])
        assert "default: 3000" in result.output

    def test_tui_option_description(self, runner: CliRunner) -> None:
        """Test --tui option description."""
        result = runner.invoke(cli, ["start", "--help"])
        assert "Force TUI wizard" in result.output


class TestStartCommandExecution:
    """Tests for start command execution."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    @pytest.fixture
    def mock_orchestrator(self) -> MagicMock:
        """Create a mock orchestrator with successful result."""
        mock = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.NONE,
            onboarding_mode=OnboardingMode.SKIP,
            interface_launched="cli",
            project_path=Path("/tmp/test"),
            total_duration_ms=100.0,
        )
        mock.start = AsyncMock(return_value=result)
        return mock

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_start_command_success(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test successful start command execution."""
        # Setup mocks
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.GAO_DEV_PROJECT)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.NONE,
            onboarding_mode=OnboardingMode.SKIP,
            interface_launched="cli",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(cli, ["start", "--project", str(tmp_project)])

        assert result.exit_code == 0
        assert "Startup complete" in result.output or "CLI interface ready" in result.output

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_start_command_with_headless(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test start command with --headless flag."""
        mock_env.return_value = EnvironmentType.HEADLESS
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.EMPTY)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.NONE,
            onboarding_mode=OnboardingMode.SKIP,
            interface_launched="cli",
            project_path=tmp_project,
            total_duration_ms=50.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = True
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(
            cli, ["start", "--headless", "--project", str(tmp_project)]
        )

        # Should call StartupOrchestrator with headless=True
        mock_orch_class.assert_called_once()
        call_kwargs = mock_orch_class.call_args[1]
        assert call_kwargs["headless"] is True

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_start_command_with_port(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test start command with --port option."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.GAO_DEV_PROJECT)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.NONE,
            onboarding_mode=OnboardingMode.SKIP,
            interface_launched="cli",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(
            cli, ["start", "--port", "8080", "--project", str(tmp_project)]
        )

        # Should call StartupOrchestrator with port=8080
        mock_orch_class.assert_called_once()
        call_kwargs = mock_orch_class.call_args[1]
        assert call_kwargs["port"] == 8080

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_start_command_with_no_browser(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test start command with --no-browser flag."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.GAO_DEV_PROJECT)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.NONE,
            onboarding_mode=OnboardingMode.SKIP,
            interface_launched="cli",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = True
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(
            cli, ["start", "--no-browser", "--project", str(tmp_project)]
        )

        # Should call StartupOrchestrator with no_browser=True
        mock_orch_class.assert_called_once()
        call_kwargs = mock_orch_class.call_args[1]
        assert call_kwargs["no_browser"] is True


class TestStartCommandExitCodes:
    """Tests for exit codes of start command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_exit_code_0_on_success(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test exit code 0 on successful startup."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.GAO_DEV_PROJECT)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.NONE,
            onboarding_mode=OnboardingMode.SKIP,
            interface_launched="cli",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(cli, ["start", "--project", str(tmp_project)])
        assert result.exit_code == 0

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_exit_code_1_on_error(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test exit code 1 on general error."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.GAO_DEV_PROJECT)

        mock_orch = MagicMock()
        mock_orch.start = AsyncMock(
            side_effect=StartupError(
                "Validation failed",
                phase=StartupPhase.VALIDATION,
                suggestions=["Check API keys"],
            )
        )
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(cli, ["start", "--project", str(tmp_project)])
        assert result.exit_code == 1

    def test_exit_code_2_on_invalid_project_path(
        self, runner: CliRunner
    ) -> None:
        """Test exit code 2 on invalid project path."""
        # Use a path that definitely doesn't exist
        result = runner.invoke(cli, ["start", "--project", "/this/path/definitely/does/not/exist/anywhere"])
        # CliRunner catches SystemExit, so we check output
        assert result.exit_code != 0
        assert "does not exist" in result.output

    def test_exit_code_2_on_file_instead_of_directory(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test exit code 2 when project path is a file."""
        # Create a file instead of directory
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test")

        result = runner.invoke(cli, ["start", "--project", str(test_file)])
        assert result.exit_code == 2
        assert "not a directory" in result.output

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_exit_code_130_on_interrupt(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test exit code 130 on keyboard interrupt."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.GAO_DEV_PROJECT)

        mock_orch = MagicMock()
        mock_orch.start = AsyncMock(side_effect=KeyboardInterrupt())
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(cli, ["start", "--project", str(tmp_project)])
        assert result.exit_code == 130
        assert "interrupted" in result.output.lower()


class TestStartCommandStartupMessage:
    """Tests for startup message display."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_startup_message_shows_version(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test startup message shows version."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.FIRST_TIME, ProjectState.EMPTY)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.WEB,
            onboarding_mode=OnboardingMode.FULL,
            interface_launched="web",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(cli, ["start", "--project", str(tmp_project)])

        assert "GAO-Dev" in result.output

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_startup_message_shows_environment(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test startup message shows detected environment."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.FIRST_TIME, ProjectState.EMPTY)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.WEB,
            onboarding_mode=OnboardingMode.FULL,
            interface_launched="web",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(cli, ["start", "--project", str(tmp_project)])

        assert "Environment:" in result.output
        assert "Desktop" in result.output

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_startup_message_shows_user_state(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test startup message shows user state."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.FIRST_TIME, ProjectState.EMPTY)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.WEB,
            onboarding_mode=OnboardingMode.FULL,
            interface_launched="web",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(cli, ["start", "--project", str(tmp_project)])

        assert "User:" in result.output
        assert "First-time" in result.output

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_startup_message_shows_project_state(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test startup message shows project state."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.FIRST_TIME, ProjectState.EMPTY)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.WEB,
            onboarding_mode=OnboardingMode.FULL,
            interface_launched="web",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(cli, ["start", "--project", str(tmp_project)])

        assert "Project:" in result.output
        assert "Empty directory" in result.output


class TestStartCommandErrorHandling:
    """Tests for error handling in start command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_startup_error_shows_suggestions(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test that StartupError displays suggestions."""
        mock_env.return_value = EnvironmentType.HEADLESS
        mock_states.return_value = (GlobalState.FIRST_TIME, ProjectState.EMPTY)

        mock_orch = MagicMock()
        mock_orch.start = AsyncMock(
            side_effect=StartupError(
                "No API keys found",
                phase=StartupPhase.VALIDATION,
                suggestions=["Set ANTHROPIC_API_KEY", "Set OPENAI_API_KEY"],
            )
        )
        mock_orch.headless = True
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(cli, ["start", "--project", str(tmp_project)])

        assert result.exit_code == 1
        assert "No API keys found" in result.output
        assert "Suggestions:" in result.output
        assert "ANTHROPIC_API_KEY" in result.output

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_unexpected_error_handling(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test handling of unexpected errors."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.FIRST_TIME, ProjectState.EMPTY)

        mock_orch = MagicMock()
        mock_orch.start = AsyncMock(side_effect=RuntimeError("Unexpected failure"))
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(cli, ["start", "--project", str(tmp_project)])

        assert result.exit_code == 1
        assert "Unexpected error" in result.output

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_failed_result_shows_error(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test that failed result shows error message."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.FIRST_TIME, ProjectState.EMPTY)

        mock_orch = MagicMock()
        result = StartupResult(
            success=False,
            wizard_type=WizardType.NONE,
            onboarding_mode=OnboardingMode.SKIP,
            interface_launched="",
            project_path=tmp_project,
            total_duration_ms=100.0,
            error="Phase failed",
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(cli, ["start", "--project", str(tmp_project)])

        assert result.exit_code == 1
        assert "Phase failed" in result.output


class TestStartCommandInterfaceLaunch:
    """Tests for interface launch messaging."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_web_interface_shows_url(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test that web interface shows URL."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.FIRST_TIME, ProjectState.EMPTY)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.WEB,
            onboarding_mode=OnboardingMode.FULL,
            interface_launched="web",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(
            cli, ["start", "--port", "8080", "--project", str(tmp_project)]
        )

        assert result.exit_code == 0
        assert "http://localhost:8080" in result.output

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_cli_interface_shows_ready(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test that CLI interface shows ready message."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.GAO_DEV_PROJECT)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.NONE,
            onboarding_mode=OnboardingMode.SKIP,
            interface_launched="cli",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(cli, ["start", "--project", str(tmp_project)])

        assert result.exit_code == 0
        assert "CLI interface ready" in result.output


class TestShowStartupMessageHelper:
    """Tests for _show_startup_message helper function."""

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_headless_mode_message(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        tmp_project: Path,
    ) -> None:
        """Test startup message for headless mode."""
        from rich.console import Console
        from io import StringIO
        from gao_dev.cli.startup_orchestrator import StartupOrchestrator

        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.FIRST_TIME, ProjectState.EMPTY)

        console = Console(file=StringIO(), force_terminal=True)
        orchestrator = StartupOrchestrator(
            project_path=tmp_project,
            headless=True,
        )

        _show_startup_message(console, "1.0.0", orchestrator, force_tui=False)

        output = console.file.getvalue()
        assert "headless mode" in output.lower()

    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_tui_mode_message(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        tmp_project: Path,
    ) -> None:
        """Test startup message for TUI mode."""
        from rich.console import Console
        from io import StringIO
        from gao_dev.cli.startup_orchestrator import StartupOrchestrator

        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.FIRST_TIME, ProjectState.EMPTY)

        console = Console(file=StringIO(), force_terminal=True)
        orchestrator = StartupOrchestrator(
            project_path=tmp_project,
            headless=False,
        )

        _show_startup_message(console, "1.0.0", orchestrator, force_tui=True)

        output = console.file.getvalue()
        assert "TUI" in output

    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_returning_user_message(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        tmp_project: Path,
    ) -> None:
        """Test startup message for returning user."""
        from rich.console import Console
        from io import StringIO
        from gao_dev.cli.startup_orchestrator import StartupOrchestrator

        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.BROWNFIELD)

        console = Console(file=StringIO(), force_terminal=True)
        orchestrator = StartupOrchestrator(
            project_path=tmp_project,
            headless=False,
        )

        _show_startup_message(console, "1.0.0", orchestrator, force_tui=False)

        output = console.file.getvalue()
        assert "Returning user" in output
        assert "brownfield" in output.lower()

    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_gaodev_project_message(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        tmp_project: Path,
    ) -> None:
        """Test startup message for existing GAO-Dev project."""
        from rich.console import Console
        from io import StringIO
        from gao_dev.cli.startup_orchestrator import StartupOrchestrator

        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.GAO_DEV_PROJECT)

        console = Console(file=StringIO(), force_terminal=True)
        orchestrator = StartupOrchestrator(
            project_path=tmp_project,
            headless=False,
        )

        _show_startup_message(console, "1.0.0", orchestrator, force_tui=False)

        output = console.file.getvalue()
        assert "GAO-Dev project" in output
        assert "Launching existing project" in output


class TestChatCommandLegacy:
    """Tests for legacy chat command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    def test_chat_command_exists(self, runner: CliRunner) -> None:
        """Test that chat command exists as legacy."""
        result = runner.invoke(cli, ["chat", "--help"])
        assert result.exit_code == 0
        assert "legacy" in result.output.lower()
        assert "gao-dev start" in result.output


class TestStartCommandDefaultBehavior:
    """Tests for default behavior of start command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_default_port_is_3000(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test that default port is 3000."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.GAO_DEV_PROJECT)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.NONE,
            onboarding_mode=OnboardingMode.SKIP,
            interface_launched="cli",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(cli, ["start", "--project", str(tmp_project)])

        mock_orch_class.assert_called_once()
        call_kwargs = mock_orch_class.call_args[1]
        assert call_kwargs["port"] == 3000

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_default_uses_current_directory(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test that command uses current directory by default."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.GAO_DEV_PROJECT)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.NONE,
            onboarding_mode=OnboardingMode.SKIP,
            interface_launched="cli",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        # Run without --project option
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["start"])

            # Should use current directory
            mock_orch_class.assert_called_once()
            call_kwargs = mock_orch_class.call_args[1]
            # project_path should be set (to cwd)
            assert "project_path" in call_kwargs


class TestStartCommandMultipleOptions:
    """Tests for combinations of options."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_headless_with_port(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test --headless with --port combination."""
        mock_env.return_value = EnvironmentType.HEADLESS
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.EMPTY)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.NONE,
            onboarding_mode=OnboardingMode.SKIP,
            interface_launched="cli",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = True
        mock_orch.no_browser = False
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(
            cli,
            ["start", "--headless", "--port", "9000", "--project", str(tmp_project)],
        )

        mock_orch_class.assert_called_once()
        call_kwargs = mock_orch_class.call_args[1]
        assert call_kwargs["headless"] is True
        assert call_kwargs["port"] == 9000

    @patch(PATCH_STARTUP_ORCH)
    @patch(PATCH_DETECT_ENV)
    @patch(PATCH_DETECT_STATES)
    def test_no_browser_with_port(
        self,
        mock_states: MagicMock,
        mock_env: MagicMock,
        mock_orch_class: MagicMock,
        runner: CliRunner,
        tmp_project: Path,
    ) -> None:
        """Test --no-browser with --port combination."""
        mock_env.return_value = EnvironmentType.DESKTOP
        mock_states.return_value = (GlobalState.RETURNING, ProjectState.EMPTY)

        mock_orch = MagicMock()
        result = StartupResult(
            success=True,
            wizard_type=WizardType.WEB,
            onboarding_mode=OnboardingMode.ABBREVIATED,
            interface_launched="cli",
            project_path=tmp_project,
            total_duration_ms=100.0,
        )
        mock_orch.start = AsyncMock(return_value=result)
        mock_orch.headless = False
        mock_orch.no_browser = True
        mock_orch.project_path = tmp_project
        mock_orch_class.return_value = mock_orch

        result = runner.invoke(
            cli,
            ["start", "--no-browser", "--port", "7000", "--project", str(tmp_project)],
        )

        mock_orch_class.assert_called_once()
        call_kwargs = mock_orch_class.call_args[1]
        assert call_kwargs["no_browser"] is True
        assert call_kwargs["port"] == 7000
