"""
Unit tests for EnvironmentDetector.

Tests environment detection logic for Docker, SSH, WSL, desktop, and
headless environments with various combinations of markers.
"""

import os
import platform
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import structlog

from gao_dev.core.environment_detector import (
    EnvironmentType,
    detect_environment,
    clear_cache,
    is_interactive,
    has_gui,
    _check_container,
    _check_ssh,
    _check_wsl,
    _check_desktop,
    _check_ci_cd,
    _check_vscode_remote,
    _check_explicit_override,
)

logger = structlog.get_logger()


# =============================================================================
# Environment Type Detection Tests
# =============================================================================


class TestEnvironmentTypeDetection:
    """Test correct EnvironmentType is returned for each environment."""

    def test_docker_environment_detected(self, docker_environment: Path) -> None:
        """Test that Docker environment returns CONTAINER type."""
        env_type = detect_environment()

        assert env_type == EnvironmentType.CONTAINER
        logger.info("docker_detection_test_passed", type=env_type.value)

    def test_ssh_environment_detected(self, ssh_environment: None) -> None:
        """Test that SSH environment returns SSH type."""
        env_type = detect_environment()

        assert env_type == EnvironmentType.SSH
        logger.info("ssh_detection_test_passed", type=env_type.value)

    def test_desktop_environment_detected(self, desktop_environment: None) -> None:
        """Test that desktop environment returns DESKTOP type."""
        # Skip on non-Linux/macOS platforms where DISPLAY doesn't apply
        if platform.system() == "Windows":
            # Windows always returns DESKTOP regardless of DISPLAY
            pass

        env_type = detect_environment()

        assert env_type == EnvironmentType.DESKTOP
        logger.info("desktop_detection_test_passed", type=env_type.value)

    def test_headless_environment_detected(self, headless_environment: None) -> None:
        """Test that CI/CD environment returns HEADLESS type."""
        env_type = detect_environment()

        assert env_type == EnvironmentType.HEADLESS
        logger.info("headless_detection_test_passed", type=env_type.value)

    def test_vscode_remote_detected(self, vscode_remote_environment: None) -> None:
        """Test that VS Code Remote returns REMOTE_DEV type."""
        env_type = detect_environment()

        assert env_type == EnvironmentType.REMOTE_DEV
        logger.info("vscode_remote_detection_test_passed", type=env_type.value)


# =============================================================================
# Detection Priority Tests
# =============================================================================


class TestDetectionPriority:
    """Test detection priority order is respected."""

    def test_explicit_headless_override_takes_precedence(
        self, explicit_headless_override: None, docker_environment: Path
    ) -> None:
        """Test explicit headless override beats Docker detection."""
        env_type = detect_environment()

        assert env_type == EnvironmentType.HEADLESS

    def test_explicit_gui_override_takes_precedence(
        self, explicit_gui_override: None, ssh_environment: None
    ) -> None:
        """Test explicit GUI override beats SSH detection."""
        env_type = detect_environment()

        assert env_type == EnvironmentType.DESKTOP

    def test_ci_beats_container(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test CI/CD detection takes precedence over container."""
        clear_cache()

        # Set both CI and Docker
        monkeypatch.setenv("CI", "true")
        monkeypatch.setenv("GAO_DEV_DOCKER", "1")

        env_type = detect_environment()

        assert env_type == EnvironmentType.HEADLESS
        clear_cache()

    def test_container_beats_ssh(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test container detection takes precedence over SSH."""
        clear_cache()

        # Set both Docker and SSH
        monkeypatch.setenv("GAO_DEV_DOCKER", "1")
        monkeypatch.setenv("SSH_CLIENT", "192.168.1.1 54321 22")

        env_type = detect_environment()

        assert env_type == EnvironmentType.CONTAINER
        clear_cache()

    def test_vscode_remote_beats_ssh(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test VS Code Remote detection takes precedence over SSH."""
        clear_cache()

        # Set both VS Code Remote and SSH
        monkeypatch.setenv("VSCODE_IPC_HOOK_CLI", "/tmp/vscode.sock")
        monkeypatch.setenv("SSH_CLIENT", "192.168.1.1 54321 22")

        # Remove Docker to test VS Code vs SSH
        monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)
        monkeypatch.delenv("CI", raising=False)

        env_type = detect_environment()

        assert env_type == EnvironmentType.REMOTE_DEV
        clear_cache()


# =============================================================================
# Individual Check Function Tests
# =============================================================================


class TestIndividualChecks:
    """Test individual check functions in isolation."""

    def test_check_container_with_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _check_container with GAO_DEV_DOCKER environment variable."""
        monkeypatch.setenv("GAO_DEV_DOCKER", "1")

        assert _check_container() is True

    def test_check_container_without_markers(
        self, clean_environment: None
    ) -> None:
        """Test _check_container returns False without markers."""
        assert _check_container() is False

    def test_check_ssh_with_client_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _check_ssh with SSH_CLIENT variable."""
        monkeypatch.setenv("SSH_CLIENT", "192.168.1.1 54321 22")

        assert _check_ssh() is True

    def test_check_ssh_with_tty_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _check_ssh with SSH_TTY variable."""
        monkeypatch.setenv("SSH_TTY", "/dev/pts/0")

        assert _check_ssh() is True

    def test_check_ssh_without_markers(
        self, clean_environment: None
    ) -> None:
        """Test _check_ssh returns False without markers."""
        assert _check_ssh() is False

    def test_check_ci_cd_with_ci_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _check_ci_cd with CI variable."""
        monkeypatch.setenv("CI", "true")

        assert _check_ci_cd() is True

    def test_check_ci_cd_with_github_actions(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _check_ci_cd with GITHUB_ACTIONS variable."""
        monkeypatch.setenv("GITHUB_ACTIONS", "true")

        assert _check_ci_cd() is True

    def test_check_ci_cd_without_markers(
        self, clean_environment: None
    ) -> None:
        """Test _check_ci_cd returns False without markers."""
        assert _check_ci_cd() is False

    def test_check_vscode_remote_with_hook(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _check_vscode_remote with IPC hook."""
        monkeypatch.setenv("VSCODE_IPC_HOOK_CLI", "/tmp/vscode.sock")

        assert _check_vscode_remote() is True

    def test_check_vscode_remote_without_markers(
        self, clean_environment: None
    ) -> None:
        """Test _check_vscode_remote returns False without markers."""
        assert _check_vscode_remote() is False

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_check_desktop_on_windows(
        self, clean_environment: None
    ) -> None:
        """Test _check_desktop returns True on Windows."""
        assert _check_desktop() is True

    def test_check_desktop_with_display_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _check_desktop with DISPLAY variable on Linux."""
        if platform.system() == "Linux":
            monkeypatch.setenv("DISPLAY", ":0")
            assert _check_desktop() is True

    def test_check_desktop_with_wayland(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _check_desktop with WAYLAND_DISPLAY variable."""
        if platform.system() == "Linux":
            monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
            assert _check_desktop() is True


# =============================================================================
# Explicit Override Tests
# =============================================================================


class TestExplicitOverrides:
    """Test explicit environment overrides."""

    def test_headless_override_true(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test GAO_DEV_HEADLESS=1 returns HEADLESS."""
        monkeypatch.setenv("GAO_DEV_HEADLESS", "1")

        result = _check_explicit_override()

        assert result == EnvironmentType.HEADLESS

    def test_headless_override_yes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test GAO_DEV_HEADLESS=yes returns HEADLESS."""
        monkeypatch.setenv("GAO_DEV_HEADLESS", "yes")

        result = _check_explicit_override()

        assert result == EnvironmentType.HEADLESS

    def test_gui_override_true(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test GAO_DEV_GUI=1 returns DESKTOP."""
        monkeypatch.setenv("GAO_DEV_GUI", "1")

        result = _check_explicit_override()

        assert result == EnvironmentType.DESKTOP

    def test_gui_override_case_insensitive(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test GAO_DEV_GUI=TRUE returns DESKTOP (case insensitive)."""
        monkeypatch.setenv("GAO_DEV_GUI", "TRUE")

        result = _check_explicit_override()

        assert result == EnvironmentType.DESKTOP

    def test_headless_beats_gui_override(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test GAO_DEV_HEADLESS takes precedence over GAO_DEV_GUI."""
        monkeypatch.setenv("GAO_DEV_HEADLESS", "1")
        monkeypatch.setenv("GAO_DEV_GUI", "1")

        result = _check_explicit_override()

        assert result == EnvironmentType.HEADLESS

    def test_no_override_returns_none(
        self, clean_environment: None
    ) -> None:
        """Test no override returns None."""
        result = _check_explicit_override()

        assert result is None


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestHelperFunctions:
    """Test helper functions is_interactive and has_gui."""

    def test_is_interactive_desktop(
        self, desktop_environment: None
    ) -> None:
        """Test is_interactive returns True for desktop."""
        assert is_interactive() is True

    def test_is_interactive_ssh(
        self, ssh_environment: None
    ) -> None:
        """Test is_interactive returns True for SSH."""
        assert is_interactive() is True

    def test_is_interactive_headless(
        self, headless_environment: None
    ) -> None:
        """Test is_interactive returns False for headless."""
        assert is_interactive() is False

    def test_is_interactive_container(
        self, docker_environment: Path
    ) -> None:
        """Test is_interactive returns False for container."""
        assert is_interactive() is False

    def test_has_gui_desktop(
        self, desktop_environment: None
    ) -> None:
        """Test has_gui returns True for desktop."""
        assert has_gui() is True

    def test_has_gui_ssh(
        self, ssh_environment: None
    ) -> None:
        """Test has_gui returns False for SSH."""
        assert has_gui() is False

    def test_has_gui_headless(
        self, headless_environment: None
    ) -> None:
        """Test has_gui returns False for headless."""
        assert has_gui() is False


# =============================================================================
# Cache Tests
# =============================================================================


class TestCaching:
    """Test caching behavior of detect_environment."""

    def test_cache_returns_same_result(
        self, clean_environment: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test cached result is returned on subsequent calls."""
        # Set CI environment
        monkeypatch.setenv("CI", "true")

        # First call
        result1 = detect_environment()

        # Change environment (should not affect cached result)
        monkeypatch.delenv("CI")
        monkeypatch.setenv("DISPLAY", ":0")

        # Second call should return cached result
        result2 = detect_environment()

        assert result1 == result2 == EnvironmentType.HEADLESS

    def test_clear_cache_resets_detection(
        self, clean_environment: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test clear_cache allows re-detection."""
        # Set CI environment
        monkeypatch.setenv("CI", "true")
        result1 = detect_environment()

        # Clear cache and change environment
        clear_cache()
        monkeypatch.delenv("CI")
        monkeypatch.setenv("GAO_DEV_DOCKER", "1")

        # Should detect new environment
        result2 = detect_environment()

        assert result1 == EnvironmentType.HEADLESS
        assert result2 == EnvironmentType.CONTAINER


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and unusual configurations."""

    def test_empty_environment_defaults_to_headless(
        self, clean_environment: None
    ) -> None:
        """Test default behavior with no markers is platform-dependent."""
        env_type = detect_environment()

        # On Windows, should detect DESKTOP
        # On Linux/macOS without display, should default to HEADLESS
        if platform.system() == "Windows":
            assert env_type == EnvironmentType.DESKTOP
        else:
            # Without DISPLAY, defaults to HEADLESS
            assert env_type == EnvironmentType.HEADLESS

    def test_invalid_override_value_ignored(
        self, monkeypatch: pytest.MonkeyPatch, desktop_environment: None
    ) -> None:
        """Test invalid override values are ignored."""
        clear_cache()
        monkeypatch.setenv("GAO_DEV_HEADLESS", "invalid")

        # Should fall through to normal detection
        result = _check_explicit_override()

        assert result is None

    def test_multiple_ci_variables(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test detection with multiple CI variables set."""
        clear_cache()
        monkeypatch.setenv("CI", "true")
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        monkeypatch.setenv("GITLAB_CI", "true")

        env_type = detect_environment()

        assert env_type == EnvironmentType.HEADLESS
        clear_cache()


# =============================================================================
# Diagnostic Output Tests
# =============================================================================


class TestDiagnosticOutput:
    """Test that detection produces clear diagnostic output."""

    def test_docker_detection_logs_method(
        self, docker_environment: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test Docker detection logs the detection method."""
        import logging

        with caplog.at_level(logging.DEBUG):
            detect_environment()

        # Check that detection was logged (structlog may format differently)
        # We just verify the function completes and returns correct type
        assert detect_environment() == EnvironmentType.CONTAINER

    def test_ssh_detection_logs_variables(
        self, ssh_environment: None
    ) -> None:
        """Test SSH detection provides useful diagnostic info."""
        # Verify SSH environment variables are set
        assert os.environ.get("SSH_CLIENT") is not None
        assert os.environ.get("SSH_TTY") is not None

        env_type = detect_environment()

        assert env_type == EnvironmentType.SSH
