"""
Wizard type selection tests.

Tests that verify the correct wizard type (TUI vs Web) is selected
based on environment type.
"""

from pathlib import Path
from typing import Any
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
# Wizard Type Enum (for testing - would be defined in implementation)
# =============================================================================


class WizardType:
    """Wizard types for onboarding."""

    TUI = "tui"
    WEB = "web"
    NONE = "none"  # For headless/CI


# =============================================================================
# Wizard Selector Logic (would be in implementation)
# =============================================================================


def select_wizard(env_type: EnvironmentType) -> str:
    """
    Select appropriate wizard based on environment.

    Args:
        env_type: Detected environment type

    Returns:
        Wizard type to use
    """
    if env_type == EnvironmentType.HEADLESS:
        return WizardType.NONE
    elif env_type == EnvironmentType.DESKTOP:
        return WizardType.WEB
    else:
        # SSH, CONTAINER, WSL, REMOTE_DEV all use TUI
        return WizardType.TUI


# =============================================================================
# TUI Wizard Selection Tests
# =============================================================================


class TestTUIWizardSelection:
    """Test TUI wizard is selected for appropriate environments."""

    def test_tui_for_docker(self, docker_environment: Path) -> None:
        """Given Docker environment, when wizard selected, then TUI wizard runs."""
        env_type = detect_environment()
        wizard = select_wizard(env_type)

        assert wizard == WizardType.TUI
        logger.info("tui_selected_for_docker", wizard=wizard)

    def test_tui_for_ssh(self, ssh_environment: None) -> None:
        """Given SSH session, when wizard selected, then TUI wizard runs."""
        env_type = detect_environment()
        wizard = select_wizard(env_type)

        assert wizard == WizardType.TUI
        logger.info("tui_selected_for_ssh", wizard=wizard)

    def test_tui_for_vscode_remote(self, vscode_remote_environment: None) -> None:
        """Given VS Code Remote, when wizard selected, then TUI wizard runs."""
        env_type = detect_environment()
        wizard = select_wizard(env_type)

        assert wizard == WizardType.TUI
        logger.info("tui_selected_for_vscode_remote", wizard=wizard)

    def test_tui_for_wsl(self) -> None:
        """Given WSL environment, when wizard selected, then TUI wizard runs."""
        # Test the selection logic directly
        wizard = select_wizard(EnvironmentType.WSL)

        assert wizard == WizardType.TUI


# =============================================================================
# Web Wizard Selection Tests
# =============================================================================


class TestWebWizardSelection:
    """Test Web wizard is selected for desktop environments."""

    def test_web_for_desktop(self, desktop_environment: None) -> None:
        """Given desktop environment, when wizard selected, then Web wizard runs."""
        env_type = detect_environment()
        wizard = select_wizard(env_type)

        assert wizard == WizardType.WEB
        logger.info("web_selected_for_desktop", wizard=wizard)

    def test_web_wizard_when_gui_available(
        self, desktop_environment: None
    ) -> None:
        """Test Web wizard selected when GUI is available."""
        assert has_gui() is True
        assert is_interactive() is True

        env_type = detect_environment()
        wizard = select_wizard(env_type)

        assert wizard == WizardType.WEB


# =============================================================================
# No Wizard (Headless) Tests
# =============================================================================


class TestNoWizardSelection:
    """Test no wizard for headless/CI environments."""

    def test_none_for_headless(self, headless_environment: None) -> None:
        """Given CI/CD environment, when wizard selected, then no wizard (env vars only)."""
        env_type = detect_environment()
        wizard = select_wizard(env_type)

        assert wizard == WizardType.NONE
        logger.info("no_wizard_for_headless", wizard=wizard)

    def test_headless_uses_env_vars_only(
        self, headless_environment: None
    ) -> None:
        """Test headless environment uses environment variables only."""
        assert is_interactive() is False
        assert has_gui() is False

        env_type = detect_environment()
        wizard = select_wizard(env_type)

        assert wizard == WizardType.NONE


# =============================================================================
# Override Tests
# =============================================================================


class TestWizardOverrides:
    """Test wizard selection with environment overrides."""

    def test_headless_override_forces_none(
        self, explicit_headless_override: None, desktop_environment: None
    ) -> None:
        """Test GAO_DEV_HEADLESS forces no wizard even on desktop."""
        env_type = detect_environment()
        wizard = select_wizard(env_type)

        assert wizard == WizardType.NONE

    def test_gui_override_forces_web(
        self, explicit_gui_override: None, ssh_environment: None
    ) -> None:
        """Test GAO_DEV_GUI forces Web wizard even in SSH."""
        env_type = detect_environment()
        wizard = select_wizard(env_type)

        assert wizard == WizardType.WEB


# =============================================================================
# Comprehensive Selection Matrix Tests
# =============================================================================


class TestWizardSelectionMatrix:
    """Test complete wizard selection matrix."""

    @pytest.mark.parametrize(
        "env_type,expected_wizard",
        [
            (EnvironmentType.DESKTOP, WizardType.WEB),
            (EnvironmentType.SSH, WizardType.TUI),
            (EnvironmentType.CONTAINER, WizardType.TUI),
            (EnvironmentType.WSL, WizardType.TUI),
            (EnvironmentType.REMOTE_DEV, WizardType.TUI),
            (EnvironmentType.HEADLESS, WizardType.NONE),
        ],
    )
    def test_wizard_selection_for_environment(
        self, env_type: EnvironmentType, expected_wizard: str
    ) -> None:
        """Test wizard selection for each environment type."""
        wizard = select_wizard(env_type)

        assert wizard == expected_wizard

    def test_all_environments_have_wizard_mapping(self) -> None:
        """Test all environment types are handled."""
        for env_type in EnvironmentType:
            wizard = select_wizard(env_type)
            assert wizard in (WizardType.TUI, WizardType.WEB, WizardType.NONE)


# =============================================================================
# Interactive Capability Tests
# =============================================================================


class TestInteractiveCapabilities:
    """Test interactive capabilities affect wizard selection."""

    def test_interactive_environments_can_prompt(self) -> None:
        """Test environments marked interactive can prompt user."""
        interactive_types = [
            EnvironmentType.DESKTOP,
            EnvironmentType.SSH,
            EnvironmentType.WSL,
        ]

        for env_type in interactive_types:
            wizard = select_wizard(env_type)
            # Interactive environments get either TUI or WEB
            assert wizard in (WizardType.TUI, WizardType.WEB)

    def test_non_interactive_skips_wizard(self) -> None:
        """Test non-interactive environments skip wizard."""
        wizard = select_wizard(EnvironmentType.HEADLESS)

        assert wizard == WizardType.NONE


# =============================================================================
# Edge Cases
# =============================================================================


class TestWizardSelectionEdgeCases:
    """Test edge cases in wizard selection."""

    def test_priority_respected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test detection priority affects wizard selection."""
        clear_cache()

        # Set multiple environment markers
        monkeypatch.setenv("CI", "true")
        monkeypatch.setenv("DISPLAY", ":0")

        env_type = detect_environment()
        wizard = select_wizard(env_type)

        # CI should win, resulting in no wizard
        assert wizard == WizardType.NONE
        clear_cache()

    def test_fallback_behavior(self) -> None:
        """Test fallback for unhandled environment types."""
        # All types should be handled
        for env_type in EnvironmentType:
            try:
                wizard = select_wizard(env_type)
                assert wizard is not None
            except KeyError:
                pytest.fail(f"Unhandled environment type: {env_type}")


# =============================================================================
# Performance Tests
# =============================================================================


@pytest.mark.performance
class TestWizardSelectionPerformance:
    """Performance tests for wizard selection."""

    def test_selection_fast(self, performance_timer: Any) -> None:
        """Test wizard selection is fast."""
        with performance_timer("selection"):
            for env_type in EnvironmentType:
                for _ in range(100):
                    select_wizard(env_type)

        total_selections = len(EnvironmentType) * 100
        avg_us = (performance_timer.timings["selection"] / total_selections) * 1_000_000

        assert avg_us < 10, f"Selection took {avg_us:.2f}us avg, expected <10us"
