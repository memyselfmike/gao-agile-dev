"""Detect runtime environment for GAO-Dev onboarding.

This module detects the runtime environment to optimize the onboarding experience.
It identifies Docker containers, SSH sessions, WSL, VS Code Remote, desktop GUI,
and CI/CD environments.
"""

import os
import platform
import functools
from enum import Enum
from pathlib import Path
from typing import Optional
import structlog

logger = structlog.get_logger()


class EnvironmentType(str, Enum):
    """Runtime environment types."""

    DESKTOP = "desktop"
    SSH = "ssh"
    CONTAINER = "container"
    WSL = "wsl"
    REMOTE_DEV = "remote_dev"
    HEADLESS = "headless"


def _check_explicit_override() -> Optional[EnvironmentType]:
    """Check for explicit environment overrides via environment variables.

    Returns:
        EnvironmentType if override is set, None otherwise.
    """
    # GAO_DEV_HEADLESS takes precedence
    if os.environ.get("GAO_DEV_HEADLESS", "").lower() in ("1", "true", "yes"):
        logger.debug("environment_override_headless")
        return EnvironmentType.HEADLESS

    # GAO_DEV_GUI forces desktop mode
    if os.environ.get("GAO_DEV_GUI", "").lower() in ("1", "true", "yes"):
        logger.debug("environment_override_gui")
        return EnvironmentType.DESKTOP

    return None


def _check_ci_cd() -> bool:
    """Check if running in CI/CD environment.

    Returns:
        True if CI/CD environment detected.
    """
    ci_vars = ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL", "TRAVIS", "CIRCLECI"]
    for var in ci_vars:
        if os.environ.get(var):
            logger.debug("ci_cd_detected", variable=var)
            return True
    return False


def _check_container() -> bool:
    """Check if running inside a Docker container.

    Returns:
        True if container environment detected.
    """
    # Explicit Docker env var
    if os.environ.get("GAO_DEV_DOCKER", "").lower() in ("1", "true", "yes"):
        logger.debug("docker_env_var_detected")
        return True

    # Check for /.dockerenv file (Linux only)
    if platform.system() == "Linux":
        dockerenv_path = Path("/.dockerenv")
        if dockerenv_path.exists():
            logger.debug("dockerenv_file_detected")
            return True

        # Check cgroup for docker/container references
        try:
            cgroup_path = Path("/proc/1/cgroup")
            if cgroup_path.exists():
                cgroup_content = cgroup_path.read_text()
                if "docker" in cgroup_content or "containerd" in cgroup_content:
                    logger.debug("cgroup_docker_detected")
                    return True
        except (OSError, PermissionError):
            pass

    return False


def _check_ssh() -> bool:
    """Check if running in an SSH session.

    Returns:
        True if SSH session detected.
    """
    if os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY"):
        logger.debug("ssh_session_detected")
        return True
    return False


def _check_vscode_remote() -> bool:
    """Check if running in VS Code Remote development.

    Returns:
        True if VS Code Remote detected.
    """
    if os.environ.get("VSCODE_IPC_HOOK_CLI"):
        logger.debug("vscode_remote_detected")
        return True
    return False


def _check_wsl() -> bool:
    """Check if running in Windows Subsystem for Linux.

    Returns:
        True if WSL detected.
    """
    if platform.system() != "Linux":
        return False

    try:
        proc_version_path = Path("/proc/version")
        if proc_version_path.exists():
            version_content = proc_version_path.read_text().lower()
            if "microsoft" in version_content or "wsl" in version_content:
                logger.debug("wsl_detected")
                return True
    except (OSError, PermissionError):
        pass

    return False


def _check_desktop() -> bool:
    """Check if running in a desktop GUI environment.

    Returns:
        True if desktop GUI detected.
    """
    # Windows always has GUI
    if platform.system() == "Windows":
        logger.debug("windows_desktop_detected")
        return True

    # macOS always has GUI when not in SSH/container
    if platform.system() == "Darwin":
        # Check if we have a display
        if os.environ.get("DISPLAY") or os.environ.get("TERM_PROGRAM"):
            logger.debug("macos_desktop_detected")
            return True

    # Linux - check DISPLAY or Wayland
    if platform.system() == "Linux":
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            logger.debug("linux_desktop_detected")
            return True

    return False


@functools.lru_cache(maxsize=1)
def detect_environment() -> EnvironmentType:
    """Detect the current runtime environment.

    Detection priority (highest to lowest):
    1. Explicit overrides (GAO_DEV_HEADLESS, GAO_DEV_GUI)
    2. CI/CD environment variables
    3. Container markers (.dockerenv)
    4. Remote development (VS Code Remote - checked before SSH as it's more specific)
    5. SSH session
    6. WSL detection
    7. Desktop detection
    8. Default to HEADLESS

    The result is cached since the environment doesn't change during process lifetime.

    Returns:
        EnvironmentType indicating the detected environment.
    """
    logger.debug("detecting_environment")

    # Priority 1: Explicit overrides
    override = _check_explicit_override()
    if override:
        logger.info("environment_detected", type=override.value, method="explicit_override")
        return override

    # Priority 2: CI/CD
    if _check_ci_cd():
        logger.info("environment_detected", type=EnvironmentType.HEADLESS.value, method="ci_cd")
        return EnvironmentType.HEADLESS

    # Priority 3: Container
    if _check_container():
        logger.info("environment_detected", type=EnvironmentType.CONTAINER.value, method="container")
        return EnvironmentType.CONTAINER

    # Priority 4: VS Code Remote (before SSH since it's more specific)
    if _check_vscode_remote():
        logger.info(
            "environment_detected", type=EnvironmentType.REMOTE_DEV.value, method="vscode_remote"
        )
        return EnvironmentType.REMOTE_DEV

    # Priority 5: SSH
    if _check_ssh():
        logger.info("environment_detected", type=EnvironmentType.SSH.value, method="ssh")
        return EnvironmentType.SSH

    # Priority 6: WSL
    if _check_wsl():
        logger.info("environment_detected", type=EnvironmentType.WSL.value, method="wsl")
        return EnvironmentType.WSL

    # Priority 7: Desktop
    if _check_desktop():
        logger.info("environment_detected", type=EnvironmentType.DESKTOP.value, method="desktop")
        return EnvironmentType.DESKTOP

    # Default: Headless
    logger.info("environment_detected", type=EnvironmentType.HEADLESS.value, method="default")
    return EnvironmentType.HEADLESS


def clear_cache() -> None:
    """Clear the detection cache for testing purposes."""
    detect_environment.cache_clear()


def is_interactive() -> bool:
    """Check if the environment supports interactive prompts.

    Returns:
        True if the environment supports interactive user input.
    """
    env_type = detect_environment()
    return env_type in (EnvironmentType.DESKTOP, EnvironmentType.SSH, EnvironmentType.WSL)


def has_gui() -> bool:
    """Check if the environment has GUI support.

    Returns:
        True if the environment has GUI support.
    """
    env_type = detect_environment()
    return env_type == EnvironmentType.DESKTOP
