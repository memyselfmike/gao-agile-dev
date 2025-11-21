"""Startup orchestrator for GAO-Dev onboarding flow.

This module coordinates the entire startup process including environment detection,
state detection, wizard selection, credential validation, and interface launch.

Epic 40: Streamlined Onboarding
Story 40.3: StartupOrchestrator Implementation
"""

import os
import time
from pathlib import Path
from typing import Optional

import structlog

from gao_dev.cli.startup_result import (
    OnboardingMode,
    PhaseResult,
    StartupError,
    StartupPhase,
    StartupResult,
    WizardType,
)
from gao_dev.core.environment_detector import (
    EnvironmentType,
    detect_environment,
)
from gao_dev.core.state_detector import (
    GlobalState,
    ProjectState,
    detect_states,
)

logger = structlog.get_logger()


class StartupOrchestrator:
    """Coordinates the entire startup flow based on environment detection.

    The orchestrator manages:
    1. Environment detection (Desktop, SSH, Container, etc.)
    2. State detection (Global and Project)
    3. Wizard selection (Web, TUI, None)
    4. Onboarding mode (Full, Abbreviated, Skip)
    5. Credential validation
    6. Project initialization
    7. Interface launch

    Attributes:
        project_path: Path to the project directory
        headless: Force headless mode
        no_browser: Don't open browser in web mode
        port: Port for web server
        environment: Detected environment type
        global_state: Detected global user state
        project_state: Detected project state
        wizard_type: Selected wizard type
        onboarding_mode: Selected onboarding mode
    """

    def __init__(
        self,
        project_path: Optional[Path] = None,
        headless: bool = False,
        no_browser: bool = False,
        port: int = 3000,
    ):
        """Initialize StartupOrchestrator.

        Args:
            project_path: Path to project directory. Defaults to cwd.
            headless: Force headless mode (no wizards, env vars only)
            no_browser: Don't open browser in web mode
            port: Port for web server (default 3000)
        """
        self.project_path = project_path or Path.cwd()
        self.headless = headless
        self.no_browser = no_browser
        self.port = port

        # Will be set during detection phase
        self.environment: Optional[EnvironmentType] = None
        self.global_state: Optional[GlobalState] = None
        self.project_state: Optional[ProjectState] = None

        # Will be set during decision phase
        self.wizard_type: Optional[WizardType] = None
        self.onboarding_mode: Optional[OnboardingMode] = None

        self.logger = logger.bind(component="startup_orchestrator")

    async def start(self) -> StartupResult:
        """Execute the complete startup flow.

        This is the main entry point that coordinates all phases:
        1. Detection Phase: Detect environment and states
        2. Decision Phase: Determine wizard type and onboarding mode
        3. Onboarding Phase: Run appropriate wizard (stub for Epic 41)
        4. Validation Phase: Validate credentials (stub)
        5. Initialization Phase: Create .gao-dev/ if needed
        6. Launch Phase: Start web server or CLI (stub)

        Returns:
            StartupResult with complete startup information

        Raises:
            StartupError: If startup fails at any phase
        """
        start_time = time.perf_counter()
        self.logger.info("startup_initiated", project_path=str(self.project_path))

        # Create result object
        result = StartupResult(
            success=False,
            wizard_type=WizardType.NONE,
            onboarding_mode=OnboardingMode.SKIP,
            interface_launched="",
            project_path=self.project_path,
            total_duration_ms=0.0,
        )

        try:
            # Phase 1: Detection
            phase_result = await self._run_detection_phase()
            result.add_phase(phase_result)
            if not phase_result.success:
                raise StartupError(
                    phase_result.message,
                    phase=StartupPhase.DETECTION,
                    suggestions=["Check environment variables and project path"],
                )

            # Phase 2: Decision
            phase_result = await self._run_decision_phase()
            result.add_phase(phase_result)
            if not phase_result.success:
                raise StartupError(
                    phase_result.message,
                    phase=StartupPhase.DECISION,
                    suggestions=["Review detected environment and state"],
                )

            # Update result with decisions
            result.wizard_type = self.wizard_type
            result.onboarding_mode = self.onboarding_mode

            # Phase 3: Onboarding
            phase_result = await self._run_onboarding_phase()
            result.add_phase(phase_result)
            if not phase_result.success:
                raise StartupError(
                    phase_result.message,
                    phase=StartupPhase.ONBOARDING,
                    suggestions=["Check wizard availability", "Try --headless mode"],
                )

            # Phase 4: Validation
            phase_result = await self._run_validation_phase()
            result.add_phase(phase_result)
            if not phase_result.success:
                raise StartupError(
                    phase_result.message,
                    phase=StartupPhase.VALIDATION,
                    suggestions=["Check API keys", "Verify credentials"],
                    details=phase_result.details,
                )

            # Phase 5: Initialization
            phase_result = await self._run_initialization_phase()
            result.add_phase(phase_result)
            if not phase_result.success:
                raise StartupError(
                    phase_result.message,
                    phase=StartupPhase.INITIALIZATION,
                    suggestions=["Check write permissions", "Verify disk space"],
                )

            # Phase 6: Launch
            phase_result = await self._run_launch_phase()
            result.add_phase(phase_result)
            if not phase_result.success:
                raise StartupError(
                    phase_result.message,
                    phase=StartupPhase.LAUNCH,
                    suggestions=["Check port availability", "Verify dependencies"],
                )

            # Update result with launch info
            result.interface_launched = phase_result.details.get("interface", "cli")

            # Mark complete
            result.add_phase(
                PhaseResult(
                    phase=StartupPhase.COMPLETE,
                    success=True,
                    duration_ms=0.0,
                    message="Startup complete",
                )
            )

            result.success = True
            result.total_duration_ms = (time.perf_counter() - start_time) * 1000

            self.logger.info(
                "startup_complete",
                wizard_type=result.wizard_type.value,
                onboarding_mode=result.onboarding_mode.value,
                interface=result.interface_launched,
                total_ms=round(result.total_duration_ms, 2),
            )

            return result

        except StartupError as e:
            result.error = str(e)
            result.total_duration_ms = (time.perf_counter() - start_time) * 1000

            self.logger.error(
                "startup_failed",
                phase=e.phase.value if e.phase else "unknown",
                error=str(e),
                suggestions=e.suggestions,
            )

            raise

        except Exception as e:
            result.error = str(e)
            result.total_duration_ms = (time.perf_counter() - start_time) * 1000

            self.logger.exception("startup_unexpected_error", error=str(e))

            raise StartupError(
                f"Unexpected error during startup: {e}",
                suggestions=["Check logs for details", "Report issue if persists"],
            )

    async def _run_detection_phase(self) -> PhaseResult:
        """Run the detection phase.

        Detects:
        - Environment type (Desktop, SSH, Container, etc.)
        - Global state (First-time or Returning)
        - Project state (Empty, Brownfield, GAO-Dev project)

        Returns:
            PhaseResult for the detection phase
        """
        start_time = time.perf_counter()
        self.logger.info("detection_phase_started")

        try:
            # Detect environment (respects --headless flag)
            if self.headless:
                self.environment = EnvironmentType.HEADLESS
            else:
                self.environment = detect_environment()

            # Detect global and project states
            self.global_state, self.project_state = detect_states(self.project_path)

            duration_ms = (time.perf_counter() - start_time) * 1000

            self.logger.info(
                "detection_phase_complete",
                environment=self.environment.value,
                global_state=self.global_state.value,
                project_state=self.project_state.value,
                duration_ms=round(duration_ms, 2),
            )

            return PhaseResult(
                phase=StartupPhase.DETECTION,
                success=True,
                duration_ms=duration_ms,
                message="Environment and state detected successfully",
                details={
                    "environment": self.environment.value,
                    "global_state": self.global_state.value,
                    "project_state": self.project_state.value,
                },
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error("detection_phase_failed", error=str(e))

            return PhaseResult(
                phase=StartupPhase.DETECTION,
                success=False,
                duration_ms=duration_ms,
                message=f"Detection failed: {e}",
            )

    async def _run_decision_phase(self) -> PhaseResult:
        """Run the decision phase.

        Determines:
        - Wizard type (Web, TUI, None)
        - Onboarding mode (Full, Abbreviated, Skip)

        Based on the wizard selection matrix:
        | Environment | Global State | Project State | Wizard | Mode |
        |-------------|--------------|---------------|--------|------|
        | Desktop | First-time | Empty | Web | Full |
        | Desktop | First-time | Brownfield | Web | Full |
        | Desktop | Returning | Empty | Web | Abbreviated |
        | Desktop | Returning | Brownfield | Web | Abbreviated |
        | Desktop | * | GAO_DEV_PROJECT | None | Skip |
        | Container/SSH/WSL/Remote | First-time | * | TUI | Full |
        | Container/SSH/WSL/Remote | Returning | Empty | TUI | Abbreviated |
        | Container/SSH/WSL/Remote | Returning | GAO_DEV_PROJECT | None | Skip |
        | Headless | * | * | None | Skip |

        Returns:
            PhaseResult for the decision phase
        """
        start_time = time.perf_counter()
        self.logger.info("decision_phase_started")

        try:
            # Determine wizard type and onboarding mode
            self.wizard_type, self.onboarding_mode = self._select_wizard_and_mode()

            duration_ms = (time.perf_counter() - start_time) * 1000

            self.logger.info(
                "decision_phase_complete",
                wizard_type=self.wizard_type.value,
                onboarding_mode=self.onboarding_mode.value,
                duration_ms=round(duration_ms, 2),
            )

            return PhaseResult(
                phase=StartupPhase.DECISION,
                success=True,
                duration_ms=duration_ms,
                message=f"Selected {self.wizard_type.value} wizard with {self.onboarding_mode.value} mode",
                details={
                    "wizard_type": self.wizard_type.value,
                    "onboarding_mode": self.onboarding_mode.value,
                },
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error("decision_phase_failed", error=str(e))

            return PhaseResult(
                phase=StartupPhase.DECISION,
                success=False,
                duration_ms=duration_ms,
                message=f"Decision failed: {e}",
            )

    def _select_wizard_and_mode(self) -> tuple[WizardType, OnboardingMode]:
        """Select wizard type and onboarding mode based on environment and state.

        Returns:
            Tuple of (WizardType, OnboardingMode)
        """
        # Headless environments always skip
        if self.environment == EnvironmentType.HEADLESS:
            return WizardType.NONE, OnboardingMode.SKIP

        # Existing GAO-Dev project - skip onboarding, launch directly
        if self.project_state == ProjectState.GAO_DEV_PROJECT:
            return WizardType.NONE, OnboardingMode.SKIP

        # Desktop environment - use Web wizard
        if self.environment == EnvironmentType.DESKTOP:
            if self.global_state == GlobalState.FIRST_TIME:
                return WizardType.WEB, OnboardingMode.FULL
            else:
                # Returning user with new project (empty or brownfield)
                return WizardType.WEB, OnboardingMode.ABBREVIATED

        # Container, SSH, WSL, Remote Dev - use TUI wizard
        if self.environment in (
            EnvironmentType.CONTAINER,
            EnvironmentType.SSH,
            EnvironmentType.WSL,
            EnvironmentType.REMOTE_DEV,
        ):
            if self.global_state == GlobalState.FIRST_TIME:
                return WizardType.TUI, OnboardingMode.FULL
            else:
                # Returning user with new project
                return WizardType.TUI, OnboardingMode.ABBREVIATED

        # Default fallback
        return WizardType.NONE, OnboardingMode.SKIP

    async def _run_onboarding_phase(self) -> PhaseResult:
        """Run the onboarding phase.

        Runs the appropriate wizard based on wizard_type and onboarding_mode.
        NOTE: This is a stub for Epic 41 which will implement the actual wizards.

        Returns:
            PhaseResult for the onboarding phase
        """
        start_time = time.perf_counter()
        self.logger.info(
            "onboarding_phase_started",
            wizard_type=self.wizard_type.value,
            onboarding_mode=self.onboarding_mode.value,
        )

        try:
            # Stub implementation - Epic 41 will add real wizards
            if self.onboarding_mode == OnboardingMode.SKIP:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return PhaseResult(
                    phase=StartupPhase.ONBOARDING,
                    success=True,
                    duration_ms=duration_ms,
                    message="Onboarding skipped",
                    details={"reason": "skip_mode"},
                )

            # Placeholder for wizard execution
            # Epic 41 will implement:
            # - WebWizard for WEB wizard type
            # - TUIWizard for TUI wizard type
            self.logger.info(
                "onboarding_wizard_stub",
                message="Wizard execution will be implemented in Epic 41",
            )

            duration_ms = (time.perf_counter() - start_time) * 1000

            return PhaseResult(
                phase=StartupPhase.ONBOARDING,
                success=True,
                duration_ms=duration_ms,
                message=f"Onboarding {self.onboarding_mode.value} mode complete (stub)",
                details={
                    "wizard_type": self.wizard_type.value,
                    "onboarding_mode": self.onboarding_mode.value,
                    "stub": "true",
                },
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error("onboarding_phase_failed", error=str(e))

            return PhaseResult(
                phase=StartupPhase.ONBOARDING,
                success=False,
                duration_ms=duration_ms,
                message=f"Onboarding failed: {e}",
            )

    async def _run_validation_phase(self) -> PhaseResult:
        """Run the validation phase.

        Validates credentials and API keys before launching interface.
        NOTE: This is a stub - actual validation will be added.

        Returns:
            PhaseResult for the validation phase
        """
        start_time = time.perf_counter()
        self.logger.info("validation_phase_started")

        try:
            # Stub implementation - validate credentials
            # Check for common API keys
            has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
            has_openai = bool(os.environ.get("OPENAI_API_KEY"))
            has_any_key = has_anthropic or has_openai

            # For headless mode, we require env vars
            if self.environment == EnvironmentType.HEADLESS and not has_any_key:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return PhaseResult(
                    phase=StartupPhase.VALIDATION,
                    success=False,
                    duration_ms=duration_ms,
                    message="No API keys found in headless mode",
                    details={
                        "anthropic_key": "not_set",
                        "openai_key": "not_set",
                    },
                )

            duration_ms = (time.perf_counter() - start_time) * 1000

            self.logger.info(
                "validation_phase_complete",
                has_anthropic=has_anthropic,
                has_openai=has_openai,
                duration_ms=round(duration_ms, 2),
            )

            return PhaseResult(
                phase=StartupPhase.VALIDATION,
                success=True,
                duration_ms=duration_ms,
                message="Credentials validated successfully",
                details={
                    "anthropic_key": "set" if has_anthropic else "not_set",
                    "openai_key": "set" if has_openai else "not_set",
                },
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error("validation_phase_failed", error=str(e))

            return PhaseResult(
                phase=StartupPhase.VALIDATION,
                success=False,
                duration_ms=duration_ms,
                message=f"Validation failed: {e}",
            )

    async def _run_initialization_phase(self) -> PhaseResult:
        """Run the initialization phase.

        Creates .gao-dev/ directory structure if needed.

        Returns:
            PhaseResult for the initialization phase
        """
        start_time = time.perf_counter()
        self.logger.info("initialization_phase_started")

        try:
            # Check if initialization is needed
            gao_dev_dir = self.project_path / ".gao-dev"

            if gao_dev_dir.exists():
                duration_ms = (time.perf_counter() - start_time) * 1000
                return PhaseResult(
                    phase=StartupPhase.INITIALIZATION,
                    success=True,
                    duration_ms=duration_ms,
                    message="Project already initialized",
                    details={"created": "false", "path": str(gao_dev_dir)},
                )

            # Skip initialization in headless mode without explicit request
            if self.onboarding_mode == OnboardingMode.SKIP:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return PhaseResult(
                    phase=StartupPhase.INITIALIZATION,
                    success=True,
                    duration_ms=duration_ms,
                    message="Initialization skipped (no onboarding)",
                    details={"created": "false", "reason": "skip_mode"},
                )

            # Create .gao-dev/ directory
            gao_dev_dir.mkdir(parents=True, exist_ok=True)

            # Create basic structure
            (gao_dev_dir / "sessions").mkdir(exist_ok=True)
            (gao_dev_dir / "metrics").mkdir(exist_ok=True)

            duration_ms = (time.perf_counter() - start_time) * 1000

            self.logger.info(
                "initialization_phase_complete",
                path=str(gao_dev_dir),
                duration_ms=round(duration_ms, 2),
            )

            return PhaseResult(
                phase=StartupPhase.INITIALIZATION,
                success=True,
                duration_ms=duration_ms,
                message="Project directory structure created",
                details={"created": "true", "path": str(gao_dev_dir)},
            )

        except PermissionError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error("initialization_permission_error", error=str(e))

            return PhaseResult(
                phase=StartupPhase.INITIALIZATION,
                success=False,
                duration_ms=duration_ms,
                message=f"Permission denied: {e}",
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error("initialization_phase_failed", error=str(e))

            return PhaseResult(
                phase=StartupPhase.INITIALIZATION,
                success=False,
                duration_ms=duration_ms,
                message=f"Initialization failed: {e}",
            )

    async def _run_launch_phase(self) -> PhaseResult:
        """Run the launch phase.

        Launches appropriate interface (web server or CLI REPL).

        Returns:
            PhaseResult for the launch phase
        """
        start_time = time.perf_counter()
        self.logger.info("launch_phase_started")

        try:
            # Determine interface type
            # Web interface for Desktop (unless --no-browser)
            # CLI for headless/SSH/Docker environments
            interface = "cli"

            if self.environment == EnvironmentType.DESKTOP and not self.no_browser:
                # Always launch web interface for Desktop
                # Frontend will handle onboarding vs main interface
                interface = "web"

            # Launch appropriate interface
            if interface == "web":
                # Start web server with auto-open browser
                from ..web.server import ServerManager
                from ..web.config import WebConfig

                self.logger.info(
                    "launching_web_interface",
                    port=self.port,
                    auto_open=not self.no_browser,
                )

                # Create config
                config = WebConfig(
                    host="127.0.0.1",
                    port=self.port,
                    auto_open=not self.no_browser,
                )

                # Print URL for user
                url = config.get_url()
                print(f"Web interface available at {url}")

                # Create manager and await the async start method
                # This will block until server stops
                # It opens browser automatically if auto_open=True
                manager = ServerManager(config)
                try:
                    await manager.start_async()
                except KeyboardInterrupt:
                    self.logger.info("shutting_down_web_server", reason="keyboard_interrupt")
                finally:
                    manager.stop()
                    self.logger.info("web_server_stopped")

            else:
                # CLI interface - delegate to ChatREPL
                # For now, just log that we're ready for CLI
                self.logger.info("cli_interface_ready", message="Use ChatREPL for interaction")

            duration_ms = (time.perf_counter() - start_time) * 1000

            return PhaseResult(
                phase=StartupPhase.LAUNCH,
                success=True,
                duration_ms=duration_ms,
                message=f"Interface launched: {interface}",
                details={
                    "interface": interface,
                    "port": str(self.port) if interface == "web" else "",
                    "no_browser": str(self.no_browser).lower(),
                },
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error("launch_phase_failed", error=str(e))

            return PhaseResult(
                phase=StartupPhase.LAUNCH,
                success=False,
                duration_ms=duration_ms,
                message=f"Launch failed: {e}",
            )


async def startup(
    project_path: Optional[Path] = None,
    headless: bool = False,
    no_browser: bool = False,
    port: int = 3000,
) -> StartupResult:
    """Convenience function to run the startup orchestrator.

    Args:
        project_path: Path to project directory. Defaults to cwd.
        headless: Force headless mode (no wizards, env vars only)
        no_browser: Don't open browser in web mode
        port: Port for web server (default 3000)

    Returns:
        StartupResult with complete startup information

    Raises:
        StartupError: If startup fails at any phase
    """
    orchestrator = StartupOrchestrator(
        project_path=project_path,
        headless=headless,
        no_browser=no_browser,
        port=port,
    )
    return await orchestrator.start()
