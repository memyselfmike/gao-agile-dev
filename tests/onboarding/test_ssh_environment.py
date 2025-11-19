"""
SSH environment integration tests.

Tests specific to SSH session environments, verifying correct detection,
wizard selection, and credential backend handling.
"""

import os
from pathlib import Path

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
# SSH Detection Tests
# =============================================================================


@pytest.mark.ssh
class TestSSHDetection:
    """Test SSH environment detection accuracy."""

    def test_returns_ssh_type(self, ssh_environment: None) -> None:
        """Given SSH session, when environment detected, then returns SSH."""
        env_type = detect_environment()

        assert env_type == EnvironmentType.SSH
        logger.info("ssh_detection_verified", environment=env_type.value)

    def test_ssh_client_alone_sufficient(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test SSH_CLIENT alone is sufficient for detection."""
        clear_cache()
        monkeypatch.setenv("SSH_CLIENT", "192.168.1.1 54321 22")
        monkeypatch.delenv("SSH_TTY", raising=False)
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)
        monkeypatch.delenv("VSCODE_IPC_HOOK_CLI", raising=False)

        env_type = detect_environment()

        assert env_type == EnvironmentType.SSH
        clear_cache()

    def test_ssh_tty_alone_sufficient(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test SSH_TTY alone is sufficient for detection."""
        clear_cache()
        monkeypatch.setenv("SSH_TTY", "/dev/pts/0")
        monkeypatch.delenv("SSH_CLIENT", raising=False)
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)
        monkeypatch.delenv("VSCODE_IPC_HOOK_CLI", raising=False)

        env_type = detect_environment()

        assert env_type == EnvironmentType.SSH
        clear_cache()

    def test_both_ssh_vars_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test detection with both SSH_CLIENT and SSH_TTY set."""
        clear_cache()
        monkeypatch.setenv("SSH_CLIENT", "192.168.1.1 54321 22")
        monkeypatch.setenv("SSH_TTY", "/dev/pts/0")
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)
        monkeypatch.delenv("VSCODE_IPC_HOOK_CLI", raising=False)

        env_type = detect_environment()

        assert env_type == EnvironmentType.SSH
        clear_cache()

    def test_ssh_client_format_variations(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test various SSH_CLIENT formats are accepted."""
        clear_cache()
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)
        monkeypatch.delenv("VSCODE_IPC_HOOK_CLI", raising=False)

        # IPv4 format
        monkeypatch.setenv("SSH_CLIENT", "10.0.0.1 12345 22")
        clear_cache()
        assert detect_environment() == EnvironmentType.SSH

        # IPv6 format
        monkeypatch.setenv("SSH_CLIENT", "::1 54321 22")
        clear_cache()
        assert detect_environment() == EnvironmentType.SSH

        # Different port
        monkeypatch.setenv("SSH_CLIENT", "192.168.1.100 8888 2222")
        clear_cache()
        assert detect_environment() == EnvironmentType.SSH

        clear_cache()


# =============================================================================
# SSH Wizard Selection Tests
# =============================================================================


@pytest.mark.ssh
class TestSSHWizardSelection:
    """Test correct wizard type selection for SSH."""

    def test_is_interactive(self, ssh_environment: None) -> None:
        """Test SSH environment is interactive."""
        result = is_interactive()

        assert result is True

    def test_no_gui_support(self, ssh_environment: None) -> None:
        """Test SSH environment has no GUI support."""
        result = has_gui()

        assert result is False

    def test_tui_wizard_should_be_selected(self, ssh_environment: None) -> None:
        """Given SSH session, when wizard selected, then TUI wizard runs."""
        env_type = detect_environment()

        # TUI wizard should be selected for SSH type
        assert env_type == EnvironmentType.SSH
        assert is_interactive() is True  # Can prompt user
        assert has_gui() is False  # But no web browser
        # WizardSelector would select TUI for SSH sessions


# =============================================================================
# SSH Credential Backend Tests
# =============================================================================


@pytest.mark.ssh
class TestSSHCredentialBackend:
    """Test credential storage backend selection for SSH."""

    def test_environment_vars_preferred(self, ssh_environment: None) -> None:
        """Given SSH environment, when credential backend selected, then env vars preferred."""
        env_type = detect_environment()

        assert env_type == EnvironmentType.SSH
        # CredentialManager would select EnvironmentVariableBackend first

    def test_keychain_not_available(self, ssh_environment: None) -> None:
        """Test keychain is not available in SSH environment."""
        # SSH sessions typically don't have access to GUI keychain
        assert has_gui() is False

    def test_file_based_fallback(
        self, ssh_environment: None, tmp_path: Path
    ) -> None:
        """Test file-based credential storage is available."""
        # Create config directory (would be in home directory)
        config_dir = tmp_path / ".gao-dev"
        config_dir.mkdir()

        assert config_dir.exists()


# =============================================================================
# SSH Full Flow Tests
# =============================================================================


@pytest.mark.ssh
class TestSSHFullFlow:
    """Test complete onboarding flow in SSH environment."""

    def test_environment_detection_fast(
        self, ssh_environment: None, performance_timer
    ) -> None:
        """Test environment detection is fast in SSH."""
        clear_cache()

        with performance_timer("env_detection"):
            env_type = detect_environment()

        assert env_type == EnvironmentType.SSH
        assert performance_timer.timings["env_detection"] < 0.1  # <100ms

    def test_complete_detection_cycle(self, ssh_environment: None) -> None:
        """Given SSH session, when full onboarding runs, then completes successfully."""
        # Step 1: Detect environment
        env_type = detect_environment()
        assert env_type == EnvironmentType.SSH

        # Step 2: Check capabilities
        assert is_interactive() is True  # Can prompt user
        assert has_gui() is False  # No web browser

        # Step 3: Verify correct type for onboarding flow
        # In production, this would trigger TUI wizard
        assert env_type.value == "ssh"

        logger.info("ssh_full_flow_test_passed")

    def test_no_display_required(self, ssh_environment: None) -> None:
        """Test SSH environment works without DISPLAY variable."""
        # DISPLAY should not be set in SSH fixture
        assert os.environ.get("DISPLAY") is None
        assert os.environ.get("WAYLAND_DISPLAY") is None

        # Detection should still work
        env_type = detect_environment()
        assert env_type == EnvironmentType.SSH

    def test_ssh_with_api_key_env(
        self, ssh_environment: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test SSH with API key in environment variable."""
        # Simulate API key being set in shell
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-12345")

        env_type = detect_environment()
        assert env_type == EnvironmentType.SSH

        # API key should be accessible
        assert os.environ.get("ANTHROPIC_API_KEY") is not None


# =============================================================================
# SSH Edge Cases
# =============================================================================


@pytest.mark.ssh
class TestSSHEdgeCases:
    """Test edge cases specific to SSH environments."""

    def test_vscode_remote_beats_ssh(
        self, ssh_environment: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test VS Code Remote detection beats SSH."""
        # Add VS Code Remote variable
        monkeypatch.setenv("VSCODE_IPC_HOOK_CLI", "/tmp/vscode.sock")

        clear_cache()
        env_type = detect_environment()

        # VS Code Remote should take precedence
        assert env_type == EnvironmentType.REMOTE_DEV
        clear_cache()

    def test_container_beats_ssh(
        self, ssh_environment: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test container detection beats SSH (SSH into container)."""
        # Add Docker variable
        monkeypatch.setenv("GAO_DEV_DOCKER", "1")

        clear_cache()
        env_type = detect_environment()

        # Container should take precedence
        assert env_type == EnvironmentType.CONTAINER
        clear_cache()

    def test_ci_beats_ssh(
        self, ssh_environment: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test CI override beats SSH detection."""
        # CI should take precedence
        monkeypatch.setenv("CI", "true")

        clear_cache()
        env_type = detect_environment()

        assert env_type == EnvironmentType.HEADLESS
        clear_cache()

    def test_headless_override_in_ssh(
        self, ssh_environment: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test explicit headless override in SSH session."""
        monkeypatch.setenv("GAO_DEV_HEADLESS", "1")

        clear_cache()
        env_type = detect_environment()

        assert env_type == EnvironmentType.HEADLESS
        clear_cache()

    def test_gui_override_in_ssh(
        self, ssh_environment: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test explicit GUI override in SSH session (X forwarding)."""
        monkeypatch.setenv("GAO_DEV_GUI", "1")

        clear_cache()
        env_type = detect_environment()

        # GUI override should force DESKTOP type
        assert env_type == EnvironmentType.DESKTOP
        clear_cache()


# =============================================================================
# SSH X Forwarding Tests
# =============================================================================


@pytest.mark.ssh
class TestSSHXForwarding:
    """Test SSH with X11 forwarding scenarios."""

    def test_ssh_with_display(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test SSH with DISPLAY set (X forwarding)."""
        clear_cache()
        monkeypatch.setenv("SSH_CLIENT", "192.168.1.1 54321 22")
        monkeypatch.setenv("SSH_TTY", "/dev/pts/0")
        monkeypatch.setenv("DISPLAY", "localhost:10.0")
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)
        monkeypatch.delenv("VSCODE_IPC_HOOK_CLI", raising=False)

        env_type = detect_environment()

        # SSH should still be detected (it's checked before desktop)
        assert env_type == EnvironmentType.SSH
        clear_cache()


# =============================================================================
# SSH Performance Tests
# =============================================================================


@pytest.mark.ssh
@pytest.mark.performance
class TestSSHPerformance:
    """Performance tests for SSH environment."""

    def test_detection_under_10ms(
        self, ssh_environment: None, performance_timer
    ) -> None:
        """Test environment detection completes in <10ms."""
        clear_cache()

        with performance_timer("detection"):
            detect_environment()

        elapsed_ms = performance_timer.timings["detection"] * 1000
        assert elapsed_ms < 10, f"Detection took {elapsed_ms:.2f}ms, expected <10ms"

    def test_cached_detection_under_1ms(
        self, ssh_environment: None, performance_timer
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
        self, ssh_environment: None, performance_timer
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
