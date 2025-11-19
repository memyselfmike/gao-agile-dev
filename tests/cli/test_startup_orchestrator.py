"""Tests for StartupOrchestrator.

Epic 40: Streamlined Onboarding
Story 40.3: StartupOrchestrator Implementation
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from gao_dev.cli.startup_orchestrator import (
    StartupOrchestrator,
    startup,
)
from gao_dev.cli.startup_result import (
    OnboardingMode,
    PhaseResult,
    StartupError,
    StartupPhase,
    StartupResult,
    WizardType,
)
from gao_dev.core.environment_detector import EnvironmentType
from gao_dev.core.state_detector import GlobalState, ProjectState


class TestStartupResult:
    """Tests for StartupResult dataclass."""

    def test_startup_result_creation(self, tmp_path: Path) -> None:
        """Test creating a StartupResult."""
        result = StartupResult(
            success=True,
            wizard_type=WizardType.WEB,
            onboarding_mode=OnboardingMode.FULL,
            interface_launched="web",
            project_path=tmp_path,
            total_duration_ms=100.0,
        )

        assert result.success is True
        assert result.wizard_type == WizardType.WEB
        assert result.onboarding_mode == OnboardingMode.FULL
        assert result.interface_launched == "web"
        assert result.project_path == tmp_path
        assert result.total_duration_ms == 100.0
        assert result.phases == []
        assert result.error is None

    def test_add_phase(self, tmp_path: Path) -> None:
        """Test adding phase results."""
        result = StartupResult(
            success=False,
            wizard_type=WizardType.NONE,
            onboarding_mode=OnboardingMode.SKIP,
            interface_launched="",
            project_path=tmp_path,
            total_duration_ms=0.0,
        )

        phase = PhaseResult(
            phase=StartupPhase.DETECTION,
            success=True,
            duration_ms=10.0,
            message="Detection complete",
        )

        result.add_phase(phase)
        assert len(result.phases) == 1
        assert result.phases[0].phase == StartupPhase.DETECTION

    def test_get_phase(self, tmp_path: Path) -> None:
        """Test getting a specific phase result."""
        result = StartupResult(
            success=True,
            wizard_type=WizardType.WEB,
            onboarding_mode=OnboardingMode.FULL,
            interface_launched="web",
            project_path=tmp_path,
            total_duration_ms=100.0,
        )

        phase = PhaseResult(
            phase=StartupPhase.DETECTION,
            success=True,
            duration_ms=10.0,
            message="Test",
        )
        result.add_phase(phase)

        found = result.get_phase(StartupPhase.DETECTION)
        assert found is not None
        assert found.phase == StartupPhase.DETECTION

        not_found = result.get_phase(StartupPhase.LAUNCH)
        assert not_found is None


class TestStartupError:
    """Tests for StartupError exception."""

    def test_startup_error_basic(self) -> None:
        """Test basic StartupError creation."""
        error = StartupError("Test error")
        assert str(error) == "Test error"
        assert error.phase is None
        assert error.suggestions == []
        assert error.details == {}

    def test_startup_error_with_phase(self) -> None:
        """Test StartupError with phase."""
        error = StartupError(
            "Detection failed",
            phase=StartupPhase.DETECTION,
            suggestions=["Check environment"],
            details={"key": "value"},
        )

        assert error.phase == StartupPhase.DETECTION
        assert "Check environment" in error.suggestions
        assert error.details["key"] == "value"


class TestWizardSelectionMatrix:
    """Tests for wizard selection matrix.

    Tests all combinations of Environment, GlobalState, and ProjectState.
    """

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> StartupOrchestrator:
        """Create orchestrator for testing."""
        return StartupOrchestrator(project_path=tmp_path)

    # Desktop Environment Tests
    def test_desktop_firsttime_empty_returns_web_full(
        self, orchestrator: StartupOrchestrator
    ) -> None:
        """Desktop + First-time + Empty = Web wizard with Full mode."""
        orchestrator.environment = EnvironmentType.DESKTOP
        orchestrator.global_state = GlobalState.FIRST_TIME
        orchestrator.project_state = ProjectState.EMPTY

        wizard, mode = orchestrator._select_wizard_and_mode()

        assert wizard == WizardType.WEB
        assert mode == OnboardingMode.FULL

    def test_desktop_firsttime_brownfield_returns_web_full(
        self, orchestrator: StartupOrchestrator
    ) -> None:
        """Desktop + First-time + Brownfield = Web wizard with Full mode."""
        orchestrator.environment = EnvironmentType.DESKTOP
        orchestrator.global_state = GlobalState.FIRST_TIME
        orchestrator.project_state = ProjectState.BROWNFIELD

        wizard, mode = orchestrator._select_wizard_and_mode()

        assert wizard == WizardType.WEB
        assert mode == OnboardingMode.FULL

    def test_desktop_returning_empty_returns_web_abbreviated(
        self, orchestrator: StartupOrchestrator
    ) -> None:
        """Desktop + Returning + Empty = Web wizard with Abbreviated mode."""
        orchestrator.environment = EnvironmentType.DESKTOP
        orchestrator.global_state = GlobalState.RETURNING
        orchestrator.project_state = ProjectState.EMPTY

        wizard, mode = orchestrator._select_wizard_and_mode()

        assert wizard == WizardType.WEB
        assert mode == OnboardingMode.ABBREVIATED

    def test_desktop_returning_brownfield_returns_web_abbreviated(
        self, orchestrator: StartupOrchestrator
    ) -> None:
        """Desktop + Returning + Brownfield = Web wizard with Abbreviated mode."""
        orchestrator.environment = EnvironmentType.DESKTOP
        orchestrator.global_state = GlobalState.RETURNING
        orchestrator.project_state = ProjectState.BROWNFIELD

        wizard, mode = orchestrator._select_wizard_and_mode()

        assert wizard == WizardType.WEB
        assert mode == OnboardingMode.ABBREVIATED

    def test_desktop_any_gaodev_returns_none_skip(
        self, orchestrator: StartupOrchestrator
    ) -> None:
        """Desktop + Any + GAO_DEV_PROJECT = No wizard, Skip mode."""
        orchestrator.environment = EnvironmentType.DESKTOP
        orchestrator.global_state = GlobalState.FIRST_TIME
        orchestrator.project_state = ProjectState.GAO_DEV_PROJECT

        wizard, mode = orchestrator._select_wizard_and_mode()

        assert wizard == WizardType.NONE
        assert mode == OnboardingMode.SKIP

        # Also test with returning user
        orchestrator.global_state = GlobalState.RETURNING
        wizard, mode = orchestrator._select_wizard_and_mode()

        assert wizard == WizardType.NONE
        assert mode == OnboardingMode.SKIP

    # Container/SSH/WSL/Remote Environment Tests
    @pytest.mark.parametrize(
        "env_type",
        [
            EnvironmentType.CONTAINER,
            EnvironmentType.SSH,
            EnvironmentType.WSL,
            EnvironmentType.REMOTE_DEV,
        ],
    )
    def test_terminal_firsttime_any_returns_tui_full(
        self, orchestrator: StartupOrchestrator, env_type: EnvironmentType
    ) -> None:
        """Container/SSH/WSL/Remote + First-time + Any = TUI wizard with Full mode."""
        orchestrator.environment = env_type
        orchestrator.global_state = GlobalState.FIRST_TIME
        orchestrator.project_state = ProjectState.EMPTY

        wizard, mode = orchestrator._select_wizard_and_mode()

        assert wizard == WizardType.TUI
        assert mode == OnboardingMode.FULL

    @pytest.mark.parametrize(
        "env_type",
        [
            EnvironmentType.CONTAINER,
            EnvironmentType.SSH,
            EnvironmentType.WSL,
            EnvironmentType.REMOTE_DEV,
        ],
    )
    def test_terminal_returning_empty_returns_tui_abbreviated(
        self, orchestrator: StartupOrchestrator, env_type: EnvironmentType
    ) -> None:
        """Container/SSH/WSL/Remote + Returning + Empty = TUI wizard with Abbreviated mode."""
        orchestrator.environment = env_type
        orchestrator.global_state = GlobalState.RETURNING
        orchestrator.project_state = ProjectState.EMPTY

        wizard, mode = orchestrator._select_wizard_and_mode()

        assert wizard == WizardType.TUI
        assert mode == OnboardingMode.ABBREVIATED

    @pytest.mark.parametrize(
        "env_type",
        [
            EnvironmentType.CONTAINER,
            EnvironmentType.SSH,
            EnvironmentType.WSL,
            EnvironmentType.REMOTE_DEV,
        ],
    )
    def test_terminal_returning_gaodev_returns_none_skip(
        self, orchestrator: StartupOrchestrator, env_type: EnvironmentType
    ) -> None:
        """Container/SSH/WSL/Remote + Returning + GAO_DEV_PROJECT = No wizard, Skip mode."""
        orchestrator.environment = env_type
        orchestrator.global_state = GlobalState.RETURNING
        orchestrator.project_state = ProjectState.GAO_DEV_PROJECT

        wizard, mode = orchestrator._select_wizard_and_mode()

        assert wizard == WizardType.NONE
        assert mode == OnboardingMode.SKIP

    # Headless Environment Tests
    def test_headless_any_any_returns_none_skip(
        self, orchestrator: StartupOrchestrator
    ) -> None:
        """Headless + Any + Any = No wizard, Skip mode."""
        orchestrator.environment = EnvironmentType.HEADLESS

        # Test all combinations of global and project state
        for global_state in GlobalState:
            for project_state in ProjectState:
                orchestrator.global_state = global_state
                orchestrator.project_state = project_state

                wizard, mode = orchestrator._select_wizard_and_mode()

                assert wizard == WizardType.NONE
                assert mode == OnboardingMode.SKIP


class TestStartupOrchestrator:
    """Tests for StartupOrchestrator class."""

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    @pytest.fixture
    def gao_dev_project(self, tmp_path: Path) -> Path:
        """Create a temporary GAO-Dev project directory."""
        gao_dev_dir = tmp_path / ".gao-dev"
        gao_dev_dir.mkdir()
        return tmp_path

    @pytest.mark.asyncio
    async def test_initialization(self, tmp_project: Path) -> None:
        """Test orchestrator initialization."""
        orchestrator = StartupOrchestrator(
            project_path=tmp_project,
            headless=True,
            no_browser=True,
            port=8080,
        )

        assert orchestrator.project_path == tmp_project
        assert orchestrator.headless is True
        assert orchestrator.no_browser is True
        assert orchestrator.port == 8080

    @pytest.mark.asyncio
    async def test_detection_phase_headless_override(self, tmp_project: Path) -> None:
        """Test that --headless flag overrides detected environment."""
        orchestrator = StartupOrchestrator(
            project_path=tmp_project,
            headless=True,
        )

        phase_result = await orchestrator._run_detection_phase()

        assert phase_result.success is True
        assert orchestrator.environment == EnvironmentType.HEADLESS

    @pytest.mark.asyncio
    async def test_detection_phase_success(self, tmp_project: Path) -> None:
        """Test successful detection phase."""
        orchestrator = StartupOrchestrator(project_path=tmp_project)

        # Mock environment detection to return a specific value
        with patch(
            "gao_dev.cli.startup_orchestrator.detect_environment"
        ) as mock_env, patch(
            "gao_dev.cli.startup_orchestrator.detect_states"
        ) as mock_states:
            mock_env.return_value = EnvironmentType.DESKTOP
            mock_states.return_value = (GlobalState.FIRST_TIME, ProjectState.EMPTY)

            phase_result = await orchestrator._run_detection_phase()

            assert phase_result.success is True
            assert phase_result.phase == StartupPhase.DETECTION
            assert orchestrator.environment == EnvironmentType.DESKTOP
            assert orchestrator.global_state == GlobalState.FIRST_TIME
            assert orchestrator.project_state == ProjectState.EMPTY

    @pytest.mark.asyncio
    async def test_decision_phase_success(self, tmp_project: Path) -> None:
        """Test successful decision phase."""
        orchestrator = StartupOrchestrator(project_path=tmp_project)
        orchestrator.environment = EnvironmentType.DESKTOP
        orchestrator.global_state = GlobalState.FIRST_TIME
        orchestrator.project_state = ProjectState.EMPTY

        phase_result = await orchestrator._run_decision_phase()

        assert phase_result.success is True
        assert phase_result.phase == StartupPhase.DECISION
        assert orchestrator.wizard_type == WizardType.WEB
        assert orchestrator.onboarding_mode == OnboardingMode.FULL

    @pytest.mark.asyncio
    async def test_onboarding_phase_skip(self, tmp_project: Path) -> None:
        """Test onboarding phase when mode is SKIP."""
        orchestrator = StartupOrchestrator(project_path=tmp_project)
        orchestrator.wizard_type = WizardType.NONE
        orchestrator.onboarding_mode = OnboardingMode.SKIP

        phase_result = await orchestrator._run_onboarding_phase()

        assert phase_result.success is True
        assert phase_result.phase == StartupPhase.ONBOARDING
        assert "skipped" in phase_result.message.lower()

    @pytest.mark.asyncio
    async def test_onboarding_phase_stub(self, tmp_project: Path) -> None:
        """Test onboarding phase stub for non-skip modes."""
        orchestrator = StartupOrchestrator(project_path=tmp_project)
        orchestrator.wizard_type = WizardType.WEB
        orchestrator.onboarding_mode = OnboardingMode.FULL

        phase_result = await orchestrator._run_onboarding_phase()

        assert phase_result.success is True
        assert phase_result.details.get("stub") == "true"

    @pytest.mark.asyncio
    async def test_validation_phase_with_api_key(self, tmp_project: Path) -> None:
        """Test validation phase when API key is set."""
        orchestrator = StartupOrchestrator(project_path=tmp_project)
        orchestrator.environment = EnvironmentType.DESKTOP

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            phase_result = await orchestrator._run_validation_phase()

            assert phase_result.success is True
            assert phase_result.details["anthropic_key"] == "set"

    @pytest.mark.asyncio
    async def test_validation_phase_headless_no_key_fails(
        self, tmp_project: Path
    ) -> None:
        """Test validation phase fails in headless mode without API key."""
        orchestrator = StartupOrchestrator(project_path=tmp_project)
        orchestrator.environment = EnvironmentType.HEADLESS

        # Ensure no API keys are set
        with patch.dict(os.environ, {}, clear=True):
            # Remove specific keys if they exist
            for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]:
                os.environ.pop(key, None)

            phase_result = await orchestrator._run_validation_phase()

            assert phase_result.success is False
            assert "No API keys" in phase_result.message

    @pytest.mark.asyncio
    async def test_initialization_phase_creates_directory(
        self, tmp_project: Path
    ) -> None:
        """Test initialization phase creates .gao-dev/ directory."""
        orchestrator = StartupOrchestrator(project_path=tmp_project)
        orchestrator.onboarding_mode = OnboardingMode.FULL

        phase_result = await orchestrator._run_initialization_phase()

        assert phase_result.success is True
        assert (tmp_project / ".gao-dev").exists()
        assert (tmp_project / ".gao-dev" / "sessions").exists()
        assert (tmp_project / ".gao-dev" / "metrics").exists()
        assert phase_result.details["created"] == "true"

    @pytest.mark.asyncio
    async def test_initialization_phase_skips_existing(
        self, gao_dev_project: Path
    ) -> None:
        """Test initialization phase skips existing .gao-dev/ directory."""
        orchestrator = StartupOrchestrator(project_path=gao_dev_project)
        orchestrator.onboarding_mode = OnboardingMode.FULL

        phase_result = await orchestrator._run_initialization_phase()

        assert phase_result.success is True
        assert phase_result.details["created"] == "false"
        assert "already initialized" in phase_result.message.lower()

    @pytest.mark.asyncio
    async def test_initialization_phase_skips_in_skip_mode(
        self, tmp_project: Path
    ) -> None:
        """Test initialization phase skips when onboarding mode is SKIP."""
        orchestrator = StartupOrchestrator(project_path=tmp_project)
        orchestrator.onboarding_mode = OnboardingMode.SKIP

        phase_result = await orchestrator._run_initialization_phase()

        assert phase_result.success is True
        assert phase_result.details["created"] == "false"
        assert not (tmp_project / ".gao-dev").exists()

    @pytest.mark.asyncio
    async def test_launch_phase_cli(self, tmp_project: Path) -> None:
        """Test launch phase selects CLI interface."""
        orchestrator = StartupOrchestrator(
            project_path=tmp_project,
            no_browser=True,
        )
        orchestrator.environment = EnvironmentType.DESKTOP
        orchestrator.wizard_type = WizardType.NONE

        phase_result = await orchestrator._run_launch_phase()

        assert phase_result.success is True
        assert phase_result.details["interface"] == "cli"

    @pytest.mark.asyncio
    async def test_launch_phase_web(self, tmp_project: Path) -> None:
        """Test launch phase selects web interface."""
        orchestrator = StartupOrchestrator(
            project_path=tmp_project,
            no_browser=False,
            port=8080,
        )
        orchestrator.environment = EnvironmentType.DESKTOP
        orchestrator.wizard_type = WizardType.WEB

        phase_result = await orchestrator._run_launch_phase()

        assert phase_result.success is True
        assert phase_result.details["interface"] == "web"
        assert phase_result.details["port"] == "8080"


class TestStartupOrchestratorIntegration:
    """Integration tests for complete startup flow."""

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    @pytest.mark.asyncio
    async def test_complete_headless_flow(self, tmp_project: Path) -> None:
        """Test complete startup flow in headless mode with API key."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = await startup(
                project_path=tmp_project,
                headless=True,
            )

            assert result.success is True
            assert result.wizard_type == WizardType.NONE
            assert result.onboarding_mode == OnboardingMode.SKIP
            assert len(result.phases) >= 6  # All phases including COMPLETE

    @pytest.mark.asyncio
    async def test_complete_headless_flow_no_key_fails(
        self, tmp_project: Path
    ) -> None:
        """Test complete startup flow fails in headless mode without API key."""
        # Ensure no API keys
        env = os.environ.copy()
        env.pop("ANTHROPIC_API_KEY", None)
        env.pop("OPENAI_API_KEY", None)

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(StartupError) as exc_info:
                await startup(
                    project_path=tmp_project,
                    headless=True,
                )

            assert exc_info.value.phase == StartupPhase.VALIDATION
            assert "API keys" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_complete_desktop_firsttime_flow(self, tmp_project: Path) -> None:
        """Test complete startup flow for desktop first-time user."""
        with patch(
            "gao_dev.cli.startup_orchestrator.detect_environment"
        ) as mock_env, patch(
            "gao_dev.cli.startup_orchestrator.detect_states"
        ) as mock_states:
            mock_env.return_value = EnvironmentType.DESKTOP
            mock_states.return_value = (GlobalState.FIRST_TIME, ProjectState.EMPTY)

            result = await startup(project_path=tmp_project)

            assert result.success is True
            assert result.wizard_type == WizardType.WEB
            assert result.onboarding_mode == OnboardingMode.FULL
            assert (tmp_project / ".gao-dev").exists()

    @pytest.mark.asyncio
    async def test_complete_existing_project_flow(self, tmp_project: Path) -> None:
        """Test complete startup flow for existing GAO-Dev project."""
        # Create .gao-dev directory
        (tmp_project / ".gao-dev").mkdir()

        with patch(
            "gao_dev.cli.startup_orchestrator.detect_environment"
        ) as mock_env, patch(
            "gao_dev.cli.startup_orchestrator.detect_states"
        ) as mock_states:
            mock_env.return_value = EnvironmentType.DESKTOP
            mock_states.return_value = (
                GlobalState.RETURNING,
                ProjectState.GAO_DEV_PROJECT,
            )

            result = await startup(project_path=tmp_project)

            assert result.success is True
            assert result.wizard_type == WizardType.NONE
            assert result.onboarding_mode == OnboardingMode.SKIP

    @pytest.mark.asyncio
    async def test_startup_performance(self, tmp_project: Path) -> None:
        """Test startup completes within 2 seconds (AC12)."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = await startup(
                project_path=tmp_project,
                headless=True,
            )

            # Should complete in < 2000ms (2 seconds)
            assert result.total_duration_ms < 2000

    @pytest.mark.asyncio
    async def test_port_option(self, tmp_project: Path) -> None:
        """Test --port option is passed through."""
        orchestrator = StartupOrchestrator(
            project_path=tmp_project,
            port=9000,
        )

        assert orchestrator.port == 9000

    @pytest.mark.asyncio
    async def test_no_browser_option(self, tmp_project: Path) -> None:
        """Test --no-browser option is passed through."""
        orchestrator = StartupOrchestrator(
            project_path=tmp_project,
            no_browser=True,
        )
        orchestrator.environment = EnvironmentType.DESKTOP
        orchestrator.wizard_type = WizardType.WEB

        phase_result = await orchestrator._run_launch_phase()

        assert phase_result.details["no_browser"] == "true"
        # Even with WEB wizard, CLI interface when no_browser is set
        assert phase_result.details["interface"] == "cli"


class TestStartupOrchestratorCLIOptions:
    """Tests for CLI options (--headless, --no-browser, --port)."""

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    @pytest.mark.asyncio
    async def test_headless_flag_overrides_detection(
        self, tmp_project: Path
    ) -> None:
        """Test --headless flag overrides environment detection."""
        with patch(
            "gao_dev.cli.startup_orchestrator.detect_environment"
        ) as mock_env:
            # Would normally detect desktop
            mock_env.return_value = EnvironmentType.DESKTOP

            orchestrator = StartupOrchestrator(
                project_path=tmp_project,
                headless=True,
            )

            await orchestrator._run_detection_phase()

            # Should be headless regardless of detection
            assert orchestrator.environment == EnvironmentType.HEADLESS

    @pytest.mark.asyncio
    async def test_default_port(self, tmp_project: Path) -> None:
        """Test default port is 3000."""
        orchestrator = StartupOrchestrator(project_path=tmp_project)
        assert orchestrator.port == 3000

    @pytest.mark.asyncio
    async def test_custom_port(self, tmp_project: Path) -> None:
        """Test custom port is respected."""
        orchestrator = StartupOrchestrator(
            project_path=tmp_project,
            port=8080,
        )
        assert orchestrator.port == 8080


class TestStartupOrchestratorErrorHandling:
    """Tests for error handling in startup phases."""

    @pytest.fixture
    def tmp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    @pytest.mark.asyncio
    async def test_detection_phase_error(self, tmp_project: Path) -> None:
        """Test error handling in detection phase."""
        orchestrator = StartupOrchestrator(project_path=tmp_project)

        with patch(
            "gao_dev.cli.startup_orchestrator.detect_environment"
        ) as mock_env:
            mock_env.side_effect = Exception("Detection error")

            phase_result = await orchestrator._run_detection_phase()

            assert phase_result.success is False
            assert "Detection error" in phase_result.message

    @pytest.mark.asyncio
    async def test_initialization_permission_error(self, tmp_project: Path) -> None:
        """Test error handling for permission errors."""
        orchestrator = StartupOrchestrator(project_path=tmp_project)
        orchestrator.onboarding_mode = OnboardingMode.FULL

        with patch.object(Path, "mkdir") as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("No write permission")

            phase_result = await orchestrator._run_initialization_phase()

            assert phase_result.success is False
            assert "Permission denied" in phase_result.message

    @pytest.mark.asyncio
    async def test_startup_error_has_suggestions(self, tmp_project: Path) -> None:
        """Test that StartupError includes actionable suggestions."""
        # Ensure no API keys
        env = os.environ.copy()
        env.pop("ANTHROPIC_API_KEY", None)
        env.pop("OPENAI_API_KEY", None)

        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(StartupError) as exc_info:
                await startup(
                    project_path=tmp_project,
                    headless=True,
                )

            error = exc_info.value
            assert len(error.suggestions) > 0


class TestPhaseResultDetails:
    """Tests for PhaseResult details."""

    def test_phase_result_creation(self) -> None:
        """Test creating a PhaseResult."""
        result = PhaseResult(
            phase=StartupPhase.DETECTION,
            success=True,
            duration_ms=10.5,
            message="Test message",
            details={"key": "value"},
        )

        assert result.phase == StartupPhase.DETECTION
        assert result.success is True
        assert result.duration_ms == 10.5
        assert result.message == "Test message"
        assert result.details["key"] == "value"

    def test_phase_result_defaults(self) -> None:
        """Test PhaseResult default values."""
        result = PhaseResult(
            phase=StartupPhase.LAUNCH,
            success=False,
            duration_ms=0.0,
        )

        assert result.message == ""
        assert result.details == {}


class TestEnums:
    """Tests for enum values."""

    def test_wizard_type_values(self) -> None:
        """Test WizardType enum values."""
        assert WizardType.WEB.value == "web"
        assert WizardType.TUI.value == "tui"
        assert WizardType.NONE.value == "none"

    def test_onboarding_mode_values(self) -> None:
        """Test OnboardingMode enum values."""
        assert OnboardingMode.FULL.value == "full"
        assert OnboardingMode.ABBREVIATED.value == "abbreviated"
        assert OnboardingMode.SKIP.value == "skip"

    def test_startup_phase_values(self) -> None:
        """Test StartupPhase enum values."""
        assert StartupPhase.DETECTION.value == "detection"
        assert StartupPhase.DECISION.value == "decision"
        assert StartupPhase.ONBOARDING.value == "onboarding"
        assert StartupPhase.VALIDATION.value == "validation"
        assert StartupPhase.INITIALIZATION.value == "initialization"
        assert StartupPhase.LAUNCH.value == "launch"
        assert StartupPhase.COMPLETE.value == "complete"
