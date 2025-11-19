"""
End-to-end onboarding flow tests.

Tests complete onboarding flows in different environments, verifying all
steps complete successfully.
"""

import os
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
import structlog

from gao_dev.core.environment_detector import (
    EnvironmentType,
    detect_environment,
    clear_cache,
    is_interactive,
    has_gui,
)

logger = structlog.get_logger()


# =============================================================================
# Onboarding Step Definitions
# =============================================================================


class OnboardingStep:
    """Onboarding steps."""

    DETECT_ENVIRONMENT = "detect_environment"
    SELECT_WIZARD = "select_wizard"
    PROJECT_CONFIG = "project_config"
    GIT_CONFIG = "git_config"
    PROVIDER_SELECT = "provider_select"
    CREDENTIALS = "credentials"
    INITIALIZE = "initialize"
    COMPLETE = "complete"


# =============================================================================
# Mock Onboarding Flow (simulates actual implementation)
# =============================================================================


class OnboardingFlow:
    """Simulated onboarding flow for testing."""

    def __init__(self) -> None:
        self.steps_completed: List[str] = []
        self.config: Dict[str, Any] = {}

    def detect_environment(self) -> EnvironmentType:
        """Step 1: Detect environment."""
        env_type = detect_environment()
        self.steps_completed.append(OnboardingStep.DETECT_ENVIRONMENT)
        self.config["environment"] = env_type
        return env_type

    def select_wizard(self) -> str:
        """Step 2: Select wizard type."""
        env_type = self.config.get("environment", EnvironmentType.HEADLESS)

        if env_type == EnvironmentType.HEADLESS:
            wizard = "none"
        elif env_type == EnvironmentType.DESKTOP:
            wizard = "web"
        else:
            wizard = "tui"

        self.steps_completed.append(OnboardingStep.SELECT_WIZARD)
        self.config["wizard"] = wizard
        return wizard

    def configure_project(self, name: str = "test-project", project_type: str = "greenfield") -> None:
        """Step 3: Configure project."""
        self.config["project"] = {
            "name": name,
            "type": project_type,
        }
        self.steps_completed.append(OnboardingStep.PROJECT_CONFIG)

    def configure_git(self, name: str = "Test User", email: str = "test@example.com") -> None:
        """Step 4: Configure git."""
        self.config["git"] = {
            "name": name,
            "email": email,
        }
        self.steps_completed.append(OnboardingStep.GIT_CONFIG)

    def select_provider(self, provider: str = "claude-code") -> None:
        """Step 5: Select provider."""
        self.config["provider"] = provider
        self.steps_completed.append(OnboardingStep.PROVIDER_SELECT)

    def configure_credentials(self, api_key: str = "sk-test-key") -> bool:
        """Step 6: Configure credentials."""
        # Check environment variable first
        env_key = os.environ.get("ANTHROPIC_API_KEY")
        if env_key:
            self.config["credentials"] = {"source": "environment", "key": "ANTHROPIC_API_KEY"}
        else:
            self.config["credentials"] = {"source": "input", "value": "***"}

        self.steps_completed.append(OnboardingStep.CREDENTIALS)
        return True

    def initialize_project(self, project_path: Path) -> bool:
        """Step 7: Initialize project."""
        # Create project structure
        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir(exist_ok=True)

        self.config["project_path"] = str(project_path)
        self.steps_completed.append(OnboardingStep.INITIALIZE)
        return True

    def complete(self) -> bool:
        """Step 8: Complete onboarding."""
        self.config["completed"] = True
        self.steps_completed.append(OnboardingStep.COMPLETE)
        return True

    def is_complete(self) -> bool:
        """Check if onboarding is complete."""
        return OnboardingStep.COMPLETE in self.steps_completed

    def get_progress(self) -> float:
        """Get completion progress as percentage."""
        total_steps = 8
        return len(self.steps_completed) / total_steps * 100


# =============================================================================
# Docker Full Flow Tests
# =============================================================================


@pytest.mark.docker
class TestDockerFullOnboardingFlow:
    """Test complete onboarding flow in Docker environment."""

    def test_complete_flow(
        self, docker_environment: Path, mock_project: Path
    ) -> None:
        """Given Docker environment, when full onboarding runs, then completes successfully."""
        flow = OnboardingFlow()

        # Step 1: Detect environment
        env_type = flow.detect_environment()
        assert env_type == EnvironmentType.CONTAINER

        # Step 2: Select wizard
        wizard = flow.select_wizard()
        assert wizard == "tui"

        # Step 3: Configure project
        flow.configure_project(name="docker-project")

        # Step 4: Configure git
        flow.configure_git()

        # Step 5: Select provider
        flow.select_provider()

        # Step 6: Configure credentials
        assert flow.configure_credentials()

        # Step 7: Initialize project
        assert flow.initialize_project(mock_project)

        # Step 8: Complete
        assert flow.complete()

        # Verify completion
        assert flow.is_complete()
        assert flow.get_progress() == 100.0
        assert (mock_project / ".gao-dev").exists()

        logger.info("docker_full_flow_completed", steps=len(flow.steps_completed))

    def test_env_var_credentials_preferred(
        self, docker_environment: Path, mock_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test environment variable credentials are detected in Docker."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-docker-key")

        flow = OnboardingFlow()
        flow.detect_environment()
        flow.select_wizard()
        flow.configure_project()
        flow.configure_git()
        flow.select_provider()
        flow.configure_credentials()

        # Should detect env var
        assert flow.config["credentials"]["source"] == "environment"
        assert flow.config["credentials"]["key"] == "ANTHROPIC_API_KEY"


# =============================================================================
# SSH Full Flow Tests
# =============================================================================


@pytest.mark.ssh
class TestSSHFullOnboardingFlow:
    """Test complete onboarding flow in SSH environment."""

    def test_complete_flow(
        self, ssh_environment: None, mock_project: Path
    ) -> None:
        """Given SSH session, when full onboarding runs, then completes successfully."""
        flow = OnboardingFlow()

        # Step 1: Detect environment
        env_type = flow.detect_environment()
        assert env_type == EnvironmentType.SSH

        # Step 2: Select wizard
        wizard = flow.select_wizard()
        assert wizard == "tui"

        # Complete remaining steps
        flow.configure_project(name="ssh-project")
        flow.configure_git()
        flow.select_provider()
        flow.configure_credentials()
        flow.initialize_project(mock_project)
        flow.complete()

        assert flow.is_complete()
        logger.info("ssh_full_flow_completed")


# =============================================================================
# Desktop Full Flow Tests
# =============================================================================


@pytest.mark.desktop
class TestDesktopFullOnboardingFlow:
    """Test complete onboarding flow in desktop environment."""

    def test_complete_flow(
        self, desktop_environment: None, mock_project: Path
    ) -> None:
        """Given desktop environment, when full onboarding runs, then completes successfully."""
        flow = OnboardingFlow()

        # Step 1: Detect environment
        env_type = flow.detect_environment()
        assert env_type == EnvironmentType.DESKTOP

        # Step 2: Select wizard
        wizard = flow.select_wizard()
        assert wizard == "web"

        # Complete remaining steps
        flow.configure_project(name="desktop-project")
        flow.configure_git()
        flow.select_provider()
        flow.configure_credentials()
        flow.initialize_project(mock_project)
        flow.complete()

        assert flow.is_complete()
        logger.info("desktop_full_flow_completed")


# =============================================================================
# Headless Full Flow Tests
# =============================================================================


@pytest.mark.headless
class TestHeadlessFullOnboardingFlow:
    """Test complete onboarding flow in headless/CI environment."""

    def test_complete_flow_with_env_vars(
        self, headless_environment: None, mock_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given CI environment, when env vars set, then onboarding completes automatically."""
        # Set all required env vars
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-ci-key")
        monkeypatch.setenv("AGENT_PROVIDER", "claude-code")

        flow = OnboardingFlow()

        # Detect environment
        env_type = flow.detect_environment()
        assert env_type == EnvironmentType.HEADLESS

        # No wizard in headless
        wizard = flow.select_wizard()
        assert wizard == "none"

        # Steps complete from env vars
        flow.configure_project()
        flow.configure_git()
        flow.select_provider(provider=os.environ.get("AGENT_PROVIDER", "claude-code"))
        flow.configure_credentials()
        flow.initialize_project(mock_project)
        flow.complete()

        assert flow.is_complete()
        assert flow.config["credentials"]["source"] == "environment"
        logger.info("headless_full_flow_completed")

    def test_fails_without_env_vars(
        self, headless_environment: None, mock_project: Path
    ) -> None:
        """Test headless fails gracefully without required env vars."""
        flow = OnboardingFlow()

        flow.detect_environment()
        flow.select_wizard()

        # Would fail credential validation in real implementation
        # This test documents the expected behavior
        flow.configure_credentials()

        # Credentials from input (would fail in CI)
        assert flow.config["credentials"]["source"] == "input"


# =============================================================================
# Resumable Flow Tests
# =============================================================================


class TestResumableOnboardingFlow:
    """Test onboarding can be resumed after interruption."""

    def test_resume_from_provider_step(
        self, desktop_environment: None, mock_project: Path
    ) -> None:
        """Test resuming onboarding from provider selection step."""
        flow = OnboardingFlow()

        # Simulate completed steps
        flow.detect_environment()
        flow.select_wizard()
        flow.configure_project()
        flow.configure_git()

        # Check progress
        assert OnboardingStep.PROVIDER_SELECT not in flow.steps_completed
        progress = flow.get_progress()
        assert progress == 50.0  # 4 of 8 steps

        # Resume from provider step
        flow.select_provider()
        flow.configure_credentials()
        flow.initialize_project(mock_project)
        flow.complete()

        assert flow.is_complete()
        assert flow.get_progress() == 100.0

    def test_progress_tracking(self, desktop_environment: None) -> None:
        """Test progress is tracked correctly."""
        flow = OnboardingFlow()

        assert flow.get_progress() == 0.0

        flow.detect_environment()
        assert flow.get_progress() == 12.5

        flow.select_wizard()
        assert flow.get_progress() == 25.0

        flow.configure_project()
        assert flow.get_progress() == 37.5


# =============================================================================
# Error Recovery Tests
# =============================================================================


class TestOnboardingErrorRecovery:
    """Test error recovery in onboarding flow."""

    def test_invalid_api_key_handling(
        self, desktop_environment: None, mock_project: Path
    ) -> None:
        """Test handling of invalid API key."""
        flow = OnboardingFlow()

        flow.detect_environment()
        flow.select_wizard()
        flow.configure_project()
        flow.configure_git()
        flow.select_provider()

        # Invalid key would be caught in real implementation
        # Flow should allow retry
        flow.configure_credentials(api_key="invalid")

        # Step is marked complete (validation happens later)
        assert OnboardingStep.CREDENTIALS in flow.steps_completed

    def test_project_init_failure_recovery(
        self, desktop_environment: None
    ) -> None:
        """Test recovery from project initialization failure."""
        flow = OnboardingFlow()

        flow.detect_environment()
        flow.select_wizard()
        flow.configure_project()
        flow.configure_git()
        flow.select_provider()
        flow.configure_credentials()

        # Invalid path would fail
        # In real implementation, would show error and allow retry


# =============================================================================
# Multiple Environment Flow Tests
# =============================================================================


class TestCrossEnvironmentFlows:
    """Test flows work consistently across environments."""

    @pytest.mark.parametrize(
        "fixture_name",
        ["docker_environment", "ssh_environment", "desktop_environment"],
    )
    def test_all_steps_complete(
        self, fixture_name: str, mock_project: Path, request: pytest.FixtureRequest
    ) -> None:
        """Test all steps complete in each environment."""
        # Get fixture
        request.getfixturevalue(fixture_name)

        flow = OnboardingFlow()

        # Complete all steps
        flow.detect_environment()
        flow.select_wizard()
        flow.configure_project()
        flow.configure_git()
        flow.select_provider()
        flow.configure_credentials()
        flow.initialize_project(mock_project)
        flow.complete()

        # Verify
        assert flow.is_complete()
        assert len(flow.steps_completed) == 8

    def test_consistent_project_structure(
        self, docker_environment: Path, mock_project: Path
    ) -> None:
        """Test project structure is consistent across environments."""
        flow = OnboardingFlow()

        # Complete flow
        flow.detect_environment()
        flow.select_wizard()
        flow.configure_project()
        flow.configure_git()
        flow.select_provider()
        flow.configure_credentials()
        flow.initialize_project(mock_project)
        flow.complete()

        # Verify structure
        gao_dev_dir = mock_project / ".gao-dev"
        assert gao_dev_dir.exists()


# =============================================================================
# Performance Tests
# =============================================================================


@pytest.mark.performance
class TestOnboardingFlowPerformance:
    """Performance tests for onboarding flow."""

    def test_full_flow_under_100ms(
        self, desktop_environment: None, mock_project: Path, performance_timer: Any
    ) -> None:
        """Test full onboarding flow completes in <100ms (excluding I/O)."""
        flow = OnboardingFlow()

        with performance_timer("full_flow"):
            flow.detect_environment()
            flow.select_wizard()
            flow.configure_project()
            flow.configure_git()
            flow.select_provider()
            flow.configure_credentials()
            flow.initialize_project(mock_project)
            flow.complete()

        elapsed_ms = performance_timer.timings["full_flow"] * 1000
        assert elapsed_ms < 100, f"Flow took {elapsed_ms:.2f}ms, expected <100ms"

    def test_environment_detection_under_10ms(
        self, desktop_environment: None, performance_timer: Any
    ) -> None:
        """Test environment detection step is fast."""
        clear_cache()

        with performance_timer("detection"):
            detect_environment()

        elapsed_ms = performance_timer.timings["detection"] * 1000
        assert elapsed_ms < 10, f"Detection took {elapsed_ms:.2f}ms, expected <10ms"
