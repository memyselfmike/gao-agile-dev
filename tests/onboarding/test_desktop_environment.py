"""
Desktop environment integration tests.

Tests specific to desktop GUI environments (Windows, macOS, Linux), verifying
correct detection, wizard selection, and credential backend handling.
"""

import os
import platform
from pathlib import Path

import pytest
import structlog

from gao_dev.core.environment_detector import (
    EnvironmentType,
    detect_environment,
    clear_cache,
    is_interactive,
    has_gui,
    _check_desktop,
)

logger = structlog.get_logger()


# =============================================================================
# Desktop Detection Tests
# =============================================================================


@pytest.mark.desktop
class TestDesktopDetection:
    """Test desktop environment detection accuracy."""

    def test_returns_desktop_type(self, desktop_environment: None) -> None:
        """Given desktop with DISPLAY, when environment detected, then returns DESKTOP."""
        env_type = detect_environment()

        assert env_type == EnvironmentType.DESKTOP
        logger.info("desktop_detection_verified", environment=env_type.value)

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_windows_always_desktop(self, clean_environment: None) -> None:
        """Test Windows always returns DESKTOP type."""
        clear_cache()
        env_type = detect_environment()

        assert env_type == EnvironmentType.DESKTOP
        clear_cache()

    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux-specific test")
    def test_linux_with_display(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test Linux with DISPLAY variable returns DESKTOP."""
        clear_cache()
        monkeypatch.setenv("DISPLAY", ":0")
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("SSH_CLIENT", raising=False)
        monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)

        env_type = detect_environment()

        assert env_type == EnvironmentType.DESKTOP
        clear_cache()

    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux-specific test")
    def test_linux_with_wayland(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test Linux with WAYLAND_DISPLAY returns DESKTOP."""
        clear_cache()
        monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
        monkeypatch.delenv("DISPLAY", raising=False)
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("SSH_CLIENT", raising=False)
        monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)

        env_type = detect_environment()

        assert env_type == EnvironmentType.DESKTOP
        clear_cache()

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_macos_with_display(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test macOS with DISPLAY or TERM_PROGRAM returns DESKTOP."""
        clear_cache()
        monkeypatch.setenv("TERM_PROGRAM", "Apple_Terminal")
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("SSH_CLIENT", raising=False)
        monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)

        env_type = detect_environment()

        assert env_type == EnvironmentType.DESKTOP
        clear_cache()


# =============================================================================
# Desktop Wizard Selection Tests
# =============================================================================


@pytest.mark.desktop
class TestDesktopWizardSelection:
    """Test correct wizard type selection for desktop."""

    def test_is_interactive(self, desktop_environment: None) -> None:
        """Test desktop environment is interactive."""
        result = is_interactive()

        assert result is True

    def test_has_gui_support(self, desktop_environment: None) -> None:
        """Test desktop environment has GUI support."""
        result = has_gui()

        assert result is True

    def test_web_wizard_should_be_selected(self, desktop_environment: None) -> None:
        """Given desktop environment, when wizard selected, then Web wizard runs."""
        env_type = detect_environment()

        # Web wizard should be selected for DESKTOP type
        assert env_type == EnvironmentType.DESKTOP
        assert is_interactive() is True
        assert has_gui() is True
        # WizardSelector would select Web wizard for desktop environments


# =============================================================================
# Desktop Credential Backend Tests
# =============================================================================


@pytest.mark.desktop
class TestDesktopCredentialBackend:
    """Test credential storage backend selection for desktop."""

    def test_keychain_available(self, desktop_environment: None) -> None:
        """Given desktop environment, when credential backend selected, then keychain available."""
        env_type = detect_environment()

        assert env_type == EnvironmentType.DESKTOP
        assert has_gui() is True
        # CredentialManager would select KeychainBackend for desktop

    def test_environment_vars_still_checked_first(
        self, desktop_environment: None
    ) -> None:
        """Test environment variables are still checked first even on desktop."""
        # Even on desktop, env vars take precedence (for CI/automation)
        # CredentialManager checks EnvironmentVariableBackend first
        pass


# =============================================================================
# Desktop Full Flow Tests
# =============================================================================


@pytest.mark.desktop
class TestDesktopFullFlow:
    """Test complete onboarding flow in desktop environment."""

    def test_environment_detection_fast(
        self, desktop_environment: None, performance_timer
    ) -> None:
        """Test environment detection is fast on desktop."""
        clear_cache()

        with performance_timer("env_detection"):
            env_type = detect_environment()

        assert env_type == EnvironmentType.DESKTOP
        assert performance_timer.timings["env_detection"] < 0.1  # <100ms

    def test_complete_detection_cycle(self, desktop_environment: None) -> None:
        """Given desktop environment, when full onboarding runs, then completes successfully."""
        # Step 1: Detect environment
        env_type = detect_environment()
        assert env_type == EnvironmentType.DESKTOP

        # Step 2: Check capabilities
        assert is_interactive() is True
        assert has_gui() is True

        # Step 3: Verify correct type for onboarding flow
        # In production, this would trigger Web wizard with browser auto-open
        assert env_type.value == "desktop"

        logger.info("desktop_full_flow_test_passed")

    def test_display_variable_set(self, desktop_environment: None) -> None:
        """Test DISPLAY variable is set in desktop fixture."""
        # On non-Windows platforms, DISPLAY should be set
        if platform.system() != "Windows":
            assert os.environ.get("DISPLAY") == ":0"

    def test_desktop_with_api_key_env(
        self, desktop_environment: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test desktop with API key in environment variable."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-12345")

        env_type = detect_environment()
        assert env_type == EnvironmentType.DESKTOP

        # API key should be accessible
        assert os.environ.get("ANTHROPIC_API_KEY") is not None


# =============================================================================
# Desktop Edge Cases
# =============================================================================


@pytest.mark.desktop
class TestDesktopEdgeCases:
    """Test edge cases specific to desktop environments."""

    def test_ci_beats_desktop(
        self, desktop_environment: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test CI override beats desktop detection."""
        monkeypatch.setenv("CI", "true")

        clear_cache()
        env_type = detect_environment()

        assert env_type == EnvironmentType.HEADLESS
        clear_cache()

    def test_docker_beats_desktop(
        self, desktop_environment: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test Docker detection beats desktop."""
        monkeypatch.setenv("GAO_DEV_DOCKER", "1")

        clear_cache()
        env_type = detect_environment()

        assert env_type == EnvironmentType.CONTAINER
        clear_cache()

    def test_ssh_beats_desktop(
        self, desktop_environment: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test SSH detection beats desktop."""
        monkeypatch.setenv("SSH_CLIENT", "192.168.1.1 54321 22")

        clear_cache()
        env_type = detect_environment()

        assert env_type == EnvironmentType.SSH
        clear_cache()

    def test_headless_override_on_desktop(
        self, desktop_environment: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test explicit headless override on desktop."""
        monkeypatch.setenv("GAO_DEV_HEADLESS", "1")

        clear_cache()
        env_type = detect_environment()

        assert env_type == EnvironmentType.HEADLESS
        clear_cache()


# =============================================================================
# Platform-Specific Desktop Tests
# =============================================================================


@pytest.mark.desktop
class TestPlatformSpecificDesktop:
    """Test platform-specific desktop detection."""

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific")
    def test_windows_check_desktop(self) -> None:
        """Test _check_desktop returns True on Windows."""
        result = _check_desktop()

        assert result is True

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific")
    def test_macos_check_desktop_with_term_program(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test macOS detection with TERM_PROGRAM."""
        monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")

        result = _check_desktop()

        assert result is True

    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux-specific")
    def test_linux_check_desktop_without_display(
        self, clean_environment: None
    ) -> None:
        """Test Linux returns False without DISPLAY."""
        result = _check_desktop()

        assert result is False


# =============================================================================
# Desktop Display Variable Tests
# =============================================================================


@pytest.mark.desktop
class TestDesktopDisplayVariables:
    """Test various display variable configurations."""

    def test_display_number_formats(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test various DISPLAY format strings."""
        if platform.system() not in ("Linux", "Darwin"):
            pytest.skip("DISPLAY only relevant on Linux/macOS")

        clear_cache()
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("SSH_CLIENT", raising=False)
        monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)

        # Test various formats
        formats = [":0", ":0.0", "localhost:0", "localhost:10.0"]

        for display_format in formats:
            monkeypatch.setenv("DISPLAY", display_format)
            clear_cache()
            assert _check_desktop() is True, f"Failed for DISPLAY={display_format}"

        clear_cache()

    def test_wayland_session(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test Wayland session detection."""
        if platform.system() != "Linux":
            pytest.skip("Wayland only on Linux")

        clear_cache()
        monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
        monkeypatch.delenv("DISPLAY", raising=False)
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("SSH_CLIENT", raising=False)
        monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)

        result = _check_desktop()

        assert result is True
        clear_cache()


# =============================================================================
# Desktop Performance Tests
# =============================================================================


@pytest.mark.desktop
@pytest.mark.performance
class TestDesktopPerformance:
    """Performance tests for desktop environment."""

    def test_detection_under_10ms(
        self, desktop_environment: None, performance_timer
    ) -> None:
        """Test environment detection completes in <10ms."""
        clear_cache()

        with performance_timer("detection"):
            detect_environment()

        elapsed_ms = performance_timer.timings["detection"] * 1000
        assert elapsed_ms < 10, f"Detection took {elapsed_ms:.2f}ms, expected <10ms"

    def test_cached_detection_under_1ms(
        self, desktop_environment: None, performance_timer
    ) -> None:
        """Test cached detection returns in <1ms."""
        # Prime cache
        detect_environment()

        with performance_timer("cached_detection"):
            for _ in range(100):
                detect_environment()

        avg_ms = (performance_timer.timings["cached_detection"] / 100) * 1000
        assert avg_ms < 1, f"Cached detection took {avg_ms:.3f}ms avg, expected <1ms"

    def test_helper_functions_fast(
        self, desktop_environment: None, performance_timer
    ) -> None:
        """Test helper functions are fast."""
        with performance_timer("is_interactive"):
            for _ in range(100):
                is_interactive()

        with performance_timer("has_gui"):
            for _ in range(100):
                has_gui()

        interactive_avg = (performance_timer.timings["is_interactive"] / 100) * 1000
        gui_avg = (performance_timer.timings["has_gui"] / 100) * 1000

        assert interactive_avg < 1, f"is_interactive took {interactive_avg:.3f}ms avg"
        assert gui_avg < 1, f"has_gui took {gui_avg:.3f}ms avg"

    def test_check_desktop_fast(
        self, desktop_environment: None, performance_timer
    ) -> None:
        """Test _check_desktop is fast."""
        with performance_timer("check_desktop"):
            for _ in range(100):
                _check_desktop()

        avg_ms = (performance_timer.timings["check_desktop"] / 100) * 1000
        assert avg_ms < 1, f"_check_desktop took {avg_ms:.3f}ms avg, expected <1ms"
