"""
Credential storage backend selection tests.

Tests that verify correct credential backend is selected for each
environment type (environment variables, keychain, encrypted file).
"""

import os
from pathlib import Path
from typing import Any, List

import pytest
import structlog

from gao_dev.core.environment_detector import (
    EnvironmentType,
    detect_environment,
    clear_cache,
    has_gui,
)

logger = structlog.get_logger()


# =============================================================================
# Backend Type Enum (for testing - would be defined in implementation)
# =============================================================================


class CredentialBackend:
    """Credential storage backend types."""

    ENVIRONMENT = "environment"
    KEYCHAIN = "keychain"
    ENCRYPTED_FILE = "encrypted_file"
    MOUNTED_CONFIG = "mounted_config"


# =============================================================================
# Backend Selector Logic (would be in implementation)
# =============================================================================


def get_backend_priority(env_type: EnvironmentType) -> List[str]:
    """
    Get credential backend priority order for environment.

    Args:
        env_type: Detected environment type

    Returns:
        List of backend types in priority order
    """
    # Environment variables are always first
    backends = [CredentialBackend.ENVIRONMENT]

    if env_type == EnvironmentType.DESKTOP:
        # Desktop can use keychain
        backends.append(CredentialBackend.KEYCHAIN)
    elif env_type in (EnvironmentType.CONTAINER, EnvironmentType.SSH):
        # Container/SSH can use mounted config
        backends.append(CredentialBackend.MOUNTED_CONFIG)

    # Encrypted file is always last resort
    backends.append(CredentialBackend.ENCRYPTED_FILE)

    return backends


def get_primary_backend(env_type: EnvironmentType) -> str:
    """
    Get primary credential backend for environment.

    Args:
        env_type: Detected environment type

    Returns:
        Primary backend type
    """
    backends = get_backend_priority(env_type)
    return backends[0] if backends else CredentialBackend.ENVIRONMENT


# =============================================================================
# Environment Variable Backend Tests
# =============================================================================


class TestEnvironmentVariableBackend:
    """Test environment variable backend selection."""

    def test_env_vars_always_primary(self) -> None:
        """Test environment variables are always checked first."""
        for env_type in EnvironmentType:
            backends = get_backend_priority(env_type)
            assert backends[0] == CredentialBackend.ENVIRONMENT

    def test_env_vars_in_docker(self, docker_environment: Path) -> None:
        """Given container environment, when credential backend selected, then env vars primary."""
        env_type = detect_environment()
        primary = get_primary_backend(env_type)

        assert primary == CredentialBackend.ENVIRONMENT
        logger.info("env_vars_primary_in_docker", backend=primary)

    def test_env_vars_in_ssh(self, ssh_environment: None) -> None:
        """Test environment variables are primary in SSH."""
        env_type = detect_environment()
        primary = get_primary_backend(env_type)

        assert primary == CredentialBackend.ENVIRONMENT

    def test_env_vars_in_headless(self, headless_environment: None) -> None:
        """Test environment variables are primary in headless/CI."""
        env_type = detect_environment()
        primary = get_primary_backend(env_type)

        assert primary == CredentialBackend.ENVIRONMENT

    def test_env_vars_in_desktop(self, desktop_environment: None) -> None:
        """Test environment variables are still primary on desktop."""
        env_type = detect_environment()
        primary = get_primary_backend(env_type)

        # Even on desktop, env vars are checked first
        assert primary == CredentialBackend.ENVIRONMENT


# =============================================================================
# Keychain Backend Tests
# =============================================================================


class TestKeychainBackend:
    """Test keychain backend availability."""

    def test_keychain_available_on_desktop(
        self, desktop_environment: None
    ) -> None:
        """Given desktop environment, when credential backend selected, then keychain available."""
        env_type = detect_environment()
        backends = get_backend_priority(env_type)

        assert CredentialBackend.KEYCHAIN in backends
        logger.info("keychain_available_on_desktop")

    def test_keychain_not_available_in_docker(
        self, docker_environment: Path
    ) -> None:
        """Test keychain is not available in Docker."""
        env_type = detect_environment()
        backends = get_backend_priority(env_type)

        assert CredentialBackend.KEYCHAIN not in backends

    def test_keychain_not_available_in_ssh(
        self, ssh_environment: None
    ) -> None:
        """Test keychain is not available in SSH."""
        env_type = detect_environment()
        backends = get_backend_priority(env_type)

        assert CredentialBackend.KEYCHAIN not in backends

    def test_keychain_not_available_in_headless(
        self, headless_environment: None
    ) -> None:
        """Test keychain is not available in headless/CI."""
        env_type = detect_environment()
        backends = get_backend_priority(env_type)

        assert CredentialBackend.KEYCHAIN not in backends

    def test_keychain_requires_gui(self) -> None:
        """Test keychain is only available when GUI is present."""
        # Keychain requires GUI for password prompts
        for env_type in EnvironmentType:
            backends = get_backend_priority(env_type)
            if CredentialBackend.KEYCHAIN in backends:
                assert env_type == EnvironmentType.DESKTOP


# =============================================================================
# Mounted Config Backend Tests
# =============================================================================


class TestMountedConfigBackend:
    """Test mounted config backend selection."""

    def test_mounted_config_in_docker(
        self, docker_environment: Path
    ) -> None:
        """Test mounted config is available in Docker."""
        env_type = detect_environment()
        backends = get_backend_priority(env_type)

        assert CredentialBackend.MOUNTED_CONFIG in backends

    def test_mounted_config_in_ssh(
        self, ssh_environment: None
    ) -> None:
        """Test mounted config is available in SSH."""
        env_type = detect_environment()
        backends = get_backend_priority(env_type)

        assert CredentialBackend.MOUNTED_CONFIG in backends

    def test_mounted_config_not_on_desktop(
        self, desktop_environment: None
    ) -> None:
        """Test mounted config not used on desktop (keychain preferred)."""
        env_type = detect_environment()
        backends = get_backend_priority(env_type)

        assert CredentialBackend.MOUNTED_CONFIG not in backends


# =============================================================================
# Encrypted File Backend Tests
# =============================================================================


class TestEncryptedFileBackend:
    """Test encrypted file backend as fallback."""

    def test_encrypted_file_always_available(self) -> None:
        """Test encrypted file is always available as fallback."""
        for env_type in EnvironmentType:
            backends = get_backend_priority(env_type)
            assert CredentialBackend.ENCRYPTED_FILE in backends

    def test_encrypted_file_is_last(self) -> None:
        """Test encrypted file is always last priority."""
        for env_type in EnvironmentType:
            backends = get_backend_priority(env_type)
            assert backends[-1] == CredentialBackend.ENCRYPTED_FILE

    def test_encrypted_file_in_docker(
        self, docker_environment: Path
    ) -> None:
        """Test encrypted file available in Docker."""
        env_type = detect_environment()
        backends = get_backend_priority(env_type)

        assert CredentialBackend.ENCRYPTED_FILE in backends
        assert backends.index(CredentialBackend.ENCRYPTED_FILE) > 0


# =============================================================================
# Complete Priority Order Tests
# =============================================================================


class TestBackendPriorityOrder:
    """Test complete backend priority order for each environment."""

    def test_desktop_priority_order(
        self, desktop_environment: None
    ) -> None:
        """Test desktop backend priority: env -> keychain -> encrypted."""
        env_type = detect_environment()
        backends = get_backend_priority(env_type)

        expected = [
            CredentialBackend.ENVIRONMENT,
            CredentialBackend.KEYCHAIN,
            CredentialBackend.ENCRYPTED_FILE,
        ]
        assert backends == expected

    def test_docker_priority_order(
        self, docker_environment: Path
    ) -> None:
        """Test Docker backend priority: env -> mounted -> encrypted."""
        env_type = detect_environment()
        backends = get_backend_priority(env_type)

        expected = [
            CredentialBackend.ENVIRONMENT,
            CredentialBackend.MOUNTED_CONFIG,
            CredentialBackend.ENCRYPTED_FILE,
        ]
        assert backends == expected

    def test_ssh_priority_order(
        self, ssh_environment: None
    ) -> None:
        """Test SSH backend priority: env -> mounted -> encrypted."""
        env_type = detect_environment()
        backends = get_backend_priority(env_type)

        expected = [
            CredentialBackend.ENVIRONMENT,
            CredentialBackend.MOUNTED_CONFIG,
            CredentialBackend.ENCRYPTED_FILE,
        ]
        assert backends == expected

    def test_headless_priority_order(
        self, headless_environment: None
    ) -> None:
        """Test headless backend priority: env -> encrypted."""
        env_type = detect_environment()
        backends = get_backend_priority(env_type)

        expected = [
            CredentialBackend.ENVIRONMENT,
            CredentialBackend.ENCRYPTED_FILE,
        ]
        assert backends == expected


# =============================================================================
# Parametrized Matrix Tests
# =============================================================================


class TestBackendSelectionMatrix:
    """Test backend selection matrix comprehensively."""

    @pytest.mark.parametrize(
        "env_type,expected_backends",
        [
            (
                EnvironmentType.DESKTOP,
                [
                    CredentialBackend.ENVIRONMENT,
                    CredentialBackend.KEYCHAIN,
                    CredentialBackend.ENCRYPTED_FILE,
                ],
            ),
            (
                EnvironmentType.SSH,
                [
                    CredentialBackend.ENVIRONMENT,
                    CredentialBackend.MOUNTED_CONFIG,
                    CredentialBackend.ENCRYPTED_FILE,
                ],
            ),
            (
                EnvironmentType.CONTAINER,
                [
                    CredentialBackend.ENVIRONMENT,
                    CredentialBackend.MOUNTED_CONFIG,
                    CredentialBackend.ENCRYPTED_FILE,
                ],
            ),
            (
                EnvironmentType.WSL,
                [
                    CredentialBackend.ENVIRONMENT,
                    CredentialBackend.ENCRYPTED_FILE,
                ],
            ),
            (
                EnvironmentType.REMOTE_DEV,
                [
                    CredentialBackend.ENVIRONMENT,
                    CredentialBackend.ENCRYPTED_FILE,
                ],
            ),
            (
                EnvironmentType.HEADLESS,
                [
                    CredentialBackend.ENVIRONMENT,
                    CredentialBackend.ENCRYPTED_FILE,
                ],
            ),
        ],
    )
    def test_backend_selection_for_environment(
        self,
        env_type: EnvironmentType,
        expected_backends: List[str],
    ) -> None:
        """Test backend selection for each environment type."""
        backends = get_backend_priority(env_type)

        assert backends == expected_backends


# =============================================================================
# Edge Cases
# =============================================================================


class TestBackendEdgeCases:
    """Test edge cases in backend selection."""

    def test_no_empty_backend_lists(self) -> None:
        """Test no environment returns empty backend list."""
        for env_type in EnvironmentType:
            backends = get_backend_priority(env_type)
            assert len(backends) > 0

    def test_no_duplicate_backends(self) -> None:
        """Test no duplicate backends in priority list."""
        for env_type in EnvironmentType:
            backends = get_backend_priority(env_type)
            assert len(backends) == len(set(backends))


# =============================================================================
# Performance Tests
# =============================================================================


@pytest.mark.performance
class TestBackendSelectionPerformance:
    """Performance tests for backend selection."""

    def test_priority_lookup_fast(self, performance_timer: Any) -> None:
        """Test backend priority lookup is fast."""
        with performance_timer("priority_lookup"):
            for env_type in EnvironmentType:
                for _ in range(100):
                    get_backend_priority(env_type)

        total_lookups = len(EnvironmentType) * 100
        avg_us = (performance_timer.timings["priority_lookup"] / total_lookups) * 1_000_000

        assert avg_us < 10, f"Lookup took {avg_us:.2f}us avg, expected <10us"

    def test_primary_backend_fast(self, performance_timer: Any) -> None:
        """Test primary backend lookup is fast."""
        with performance_timer("primary_lookup"):
            for env_type in EnvironmentType:
                for _ in range(100):
                    get_primary_backend(env_type)

        total_lookups = len(EnvironmentType) * 100
        avg_us = (performance_timer.timings["primary_lookup"] / total_lookups) * 1_000_000

        assert avg_us < 10, f"Lookup took {avg_us:.2f}us avg, expected <10us"
