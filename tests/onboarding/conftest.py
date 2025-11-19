"""
Shared fixtures for onboarding tests.

Provides environment simulation fixtures for Docker, SSH, WSL, and desktop
environments to enable comprehensive cross-platform testing.
"""

import os
import platform
import tempfile
from pathlib import Path
from typing import Generator

import pytest
import structlog

logger = structlog.get_logger()


# =============================================================================
# Environment Simulation Fixtures
# =============================================================================


@pytest.fixture
def docker_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[Path, None, None]:
    """
    Simulate Docker container environment.

    Creates a .dockerenv marker file and sets appropriate environment variables
    to simulate running inside a Docker container.

    Args:
        monkeypatch: Pytest monkeypatch fixture
        tmp_path: Temporary path fixture

    Yields:
        Path: Path to the temporary .dockerenv file
    """
    # Clear environment detection cache
    from gao_dev.core.environment_detector import clear_cache
    clear_cache()

    # Create .dockerenv marker
    dockerenv = tmp_path / ".dockerenv"
    dockerenv.touch()

    # Set Docker environment variable
    monkeypatch.setenv("GAO_DEV_DOCKER", "1")

    # Remove display variables to simulate headless container
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    # Remove SSH variables
    monkeypatch.delenv("SSH_CLIENT", raising=False)
    monkeypatch.delenv("SSH_TTY", raising=False)

    # Remove CI variables
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    logger.debug("docker_environment_fixture_setup", dockerenv_path=str(dockerenv))

    yield dockerenv

    # Cleanup
    if dockerenv.exists():
        dockerenv.unlink()

    clear_cache()


@pytest.fixture
def ssh_environment(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """
    Simulate SSH session environment.

    Sets SSH_CLIENT and SSH_TTY environment variables to simulate an SSH session.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Yields:
        None
    """
    # Clear environment detection cache
    from gao_dev.core.environment_detector import clear_cache
    clear_cache()

    # Set SSH environment variables
    monkeypatch.setenv("SSH_CLIENT", "192.168.1.1 54321 22")
    monkeypatch.setenv("SSH_TTY", "/dev/pts/0")

    # Remove display variables
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    # Remove Docker variables
    monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)

    # Remove CI variables
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    logger.debug("ssh_environment_fixture_setup")

    yield

    clear_cache()


@pytest.fixture
def wsl_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[Path, None, None]:
    """
    Simulate WSL environment.

    Creates a mock /proc/version file containing Microsoft marker and sets
    appropriate environment variables.

    Args:
        monkeypatch: Pytest monkeypatch fixture
        tmp_path: Temporary path fixture

    Yields:
        Path: Path to mock proc directory
    """
    # Clear environment detection cache
    from gao_dev.core.environment_detector import clear_cache
    clear_cache()

    # Set WSL-specific environment variable (for testing purposes)
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")

    # Create mock /proc/version with Microsoft marker
    mock_proc = tmp_path / "proc"
    mock_proc.mkdir()
    version_file = mock_proc / "version"
    version_file.write_text(
        "Linux version 5.15.0-1-microsoft-standard-WSL2 "
        "(oe-user@oe-host) (gcc (Ubuntu 10.3.0-1ubuntu1) 10.3.0, "
        "GNU ld (GNU Binutils for Ubuntu) 2.36.1)"
    )

    # Remove Docker and SSH variables
    monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)
    monkeypatch.delenv("SSH_CLIENT", raising=False)
    monkeypatch.delenv("SSH_TTY", raising=False)

    # Remove CI variables
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    logger.debug("wsl_environment_fixture_setup", mock_proc=str(mock_proc))

    yield mock_proc

    clear_cache()


@pytest.fixture
def desktop_environment(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """
    Simulate desktop environment with display.

    Sets DISPLAY environment variable and removes SSH/Docker markers.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Yields:
        None
    """
    # Clear environment detection cache
    from gao_dev.core.environment_detector import clear_cache
    clear_cache()

    # Set display variable (Linux/macOS style)
    monkeypatch.setenv("DISPLAY", ":0")

    # Remove SSH variables
    monkeypatch.delenv("SSH_CLIENT", raising=False)
    monkeypatch.delenv("SSH_TTY", raising=False)

    # Remove Docker variables
    monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)

    # Remove CI variables
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    logger.debug("desktop_environment_fixture_setup")

    yield

    clear_cache()


@pytest.fixture
def headless_environment(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """
    Simulate headless/CI environment.

    Sets CI environment variable and removes all display markers.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Yields:
        None
    """
    # Clear environment detection cache
    from gao_dev.core.environment_detector import clear_cache
    clear_cache()

    # Set CI variable
    monkeypatch.setenv("CI", "true")

    # Remove all display/GUI variables
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    # Remove SSH variables
    monkeypatch.delenv("SSH_CLIENT", raising=False)
    monkeypatch.delenv("SSH_TTY", raising=False)

    # Remove Docker variables
    monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)

    logger.debug("headless_environment_fixture_setup")

    yield

    clear_cache()


@pytest.fixture
def vscode_remote_environment(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """
    Simulate VS Code Remote development environment.

    Sets VSCODE_IPC_HOOK_CLI environment variable.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Yields:
        None
    """
    # Clear environment detection cache
    from gao_dev.core.environment_detector import clear_cache
    clear_cache()

    # Set VS Code Remote variable
    monkeypatch.setenv("VSCODE_IPC_HOOK_CLI", "/tmp/vscode-ipc-abc123.sock")

    # Remove Docker variables (VS Code Remote can be in containers too)
    monkeypatch.delenv("GAO_DEV_DOCKER", raising=False)

    # Remove CI variables
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    logger.debug("vscode_remote_environment_fixture_setup")

    yield

    clear_cache()


# =============================================================================
# Override Fixtures
# =============================================================================


@pytest.fixture
def explicit_headless_override(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """
    Simulate explicit headless override via environment variable.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Yields:
        None
    """
    from gao_dev.core.environment_detector import clear_cache
    clear_cache()

    monkeypatch.setenv("GAO_DEV_HEADLESS", "1")

    yield

    clear_cache()


@pytest.fixture
def explicit_gui_override(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """
    Simulate explicit GUI override via environment variable.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Yields:
        None
    """
    from gao_dev.core.environment_detector import clear_cache
    clear_cache()

    monkeypatch.setenv("GAO_DEV_GUI", "1")

    yield

    clear_cache()


# =============================================================================
# Configuration and Project Fixtures
# =============================================================================


@pytest.fixture
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """
    Provide a clean environment with minimal variables set.

    Removes all environment-related variables to test default behavior.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Yields:
        None
    """
    from gao_dev.core.environment_detector import clear_cache
    clear_cache()

    # Remove all environment detection variables
    env_vars = [
        "GAO_DEV_DOCKER",
        "GAO_DEV_HEADLESS",
        "GAO_DEV_GUI",
        "SSH_CLIENT",
        "SSH_TTY",
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_URL",
        "TRAVIS",
        "CIRCLECI",
        "VSCODE_IPC_HOOK_CLI",
        "DISPLAY",
        "WAYLAND_DISPLAY",
        "WSL_DISTRO_NAME",
        "TERM_PROGRAM",
    ]

    for var in env_vars:
        monkeypatch.delenv(var, raising=False)

    yield

    clear_cache()


@pytest.fixture
def mock_global_config(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a mock global configuration directory.

    Args:
        tmp_path: Temporary path fixture

    Yields:
        Path: Path to mock .gao-dev config directory
    """
    config_dir = tmp_path / ".gao-dev"
    config_dir.mkdir()

    yield config_dir


@pytest.fixture
def mock_project(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a mock project directory with basic structure.

    Args:
        tmp_path: Temporary path fixture

    Yields:
        Path: Path to mock project root
    """
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Create basic structure
    (project_dir / "src").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "docs").mkdir()

    yield project_dir


@pytest.fixture
def mock_gao_dev_project(mock_project: Path) -> Generator[Path, None, None]:
    """
    Create a mock GAO-Dev initialized project.

    Args:
        mock_project: Mock project fixture

    Yields:
        Path: Path to GAO-Dev project root
    """
    gao_dev_dir = mock_project / ".gao-dev"
    gao_dev_dir.mkdir()

    # Create minimal config
    config_file = gao_dev_dir / "config.yaml"
    config_file.write_text(
        """version: "1.0"
project:
  name: test-project
  type: greenfield
"""
    )

    yield mock_project


# =============================================================================
# Performance Testing Fixtures
# =============================================================================


@pytest.fixture
def performance_timer():
    """
    Provide a simple performance timer context manager.

    Yields:
        callable: Timer context manager factory
    """
    import time
    from contextlib import contextmanager
    from typing import Dict

    timings: Dict[str, float] = {}

    @contextmanager
    def timer(name: str):
        start = time.perf_counter()
        yield
        elapsed = time.perf_counter() - start
        timings[name] = elapsed
        logger.debug("performance_timing", name=name, elapsed_ms=elapsed * 1000)

    timer.timings = timings
    yield timer


# =============================================================================
# Pytest Markers Registration
# =============================================================================


def pytest_configure(config):
    """Register custom pytest markers for onboarding tests."""
    config.addinivalue_line(
        "markers", "docker: Tests that require Docker environment simulation"
    )
    config.addinivalue_line(
        "markers", "ssh: Tests that require SSH environment simulation"
    )
    config.addinivalue_line(
        "markers", "wsl: Tests that require WSL environment simulation"
    )
    config.addinivalue_line(
        "markers", "requires_wsl: Tests that require actual WSL installation"
    )
    config.addinivalue_line(
        "markers", "desktop: Tests that require desktop environment simulation"
    )
    config.addinivalue_line(
        "markers", "headless: Tests that require headless environment simulation"
    )
    config.addinivalue_line(
        "markers", "performance: Performance benchmark tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer than usual"
    )
