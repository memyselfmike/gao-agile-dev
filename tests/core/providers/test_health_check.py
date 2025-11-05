"""Tests for provider health checker."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from gao_dev.core.providers.health_check import ProviderHealthChecker


class TestProviderHealthChecker:
    """Test health checker."""

    def test_initialization(self):
        """Test checker initializes correctly."""
        checker = ProviderHealthChecker(cache_duration=300)

        assert checker.cache_duration == 300
        assert checker._health_cache == {}

    def test_is_healthy_default(self):
        """Test providers are healthy by default."""
        checker = ProviderHealthChecker()

        is_healthy = checker.is_healthy("claude-code")

        assert is_healthy is True

    def test_caches_health_status(self):
        """Test caches health check results."""
        checker = ProviderHealthChecker()

        # First check
        checker.is_healthy("claude-code")

        # Should be cached
        assert "claude-code" in checker._health_cache

    def test_uses_cached_value_within_duration(self):
        """Test uses cached value if within cache duration."""
        checker = ProviderHealthChecker(cache_duration=300)

        # First check
        is_healthy_1 = checker.is_healthy("claude-code")

        # Second check (should use cache)
        is_healthy_2 = checker.is_healthy("claude-code")

        assert is_healthy_1 == is_healthy_2

    def test_expires_cache_after_duration(self):
        """Test expires cache after duration."""
        checker = ProviderHealthChecker(cache_duration=0)  # Immediate expiry

        # First check
        checker.is_healthy("claude-code")

        # Manually set old timestamp
        checker._health_cache["claude-code"] = (
            False,
            datetime.now() - timedelta(seconds=10)
        )

        # Should re-check (cache expired)
        is_healthy = checker.is_healthy("claude-code")

        # Should default to healthy (no actual check implemented yet)
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_check_provider_health_success(self):
        """Test checking provider health successfully."""
        checker = ProviderHealthChecker()

        # Mock provider with validate method
        mock_provider = Mock()
        mock_provider.name = "claude-code"
        mock_provider.validate_configuration = AsyncMock(return_value=True)

        is_healthy = await checker.check_provider_health(mock_provider)

        assert is_healthy is True
        assert checker._health_cache["claude-code"][0] is True

    @pytest.mark.asyncio
    async def test_check_provider_health_failure(self):
        """Test checking provider health failure."""
        checker = ProviderHealthChecker()

        # Mock provider that fails validation
        mock_provider = Mock()
        mock_provider.name = "claude-code"
        mock_provider.validate_configuration = AsyncMock(return_value=False)

        is_healthy = await checker.check_provider_health(mock_provider)

        assert is_healthy is False
        assert checker._health_cache["claude-code"][0] is False

    @pytest.mark.asyncio
    async def test_check_provider_health_exception(self):
        """Test checking provider health handles exceptions."""
        checker = ProviderHealthChecker()

        # Mock provider that raises exception
        mock_provider = Mock()
        mock_provider.name = "claude-code"
        mock_provider.validate_configuration = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        is_healthy = await checker.check_provider_health(mock_provider)

        assert is_healthy is False

    def test_mark_unhealthy(self):
        """Test manually marking provider as unhealthy."""
        checker = ProviderHealthChecker()

        checker.mark_unhealthy("claude-code")

        is_healthy = checker.is_healthy("claude-code")

        assert is_healthy is False

    def test_clear_cache(self):
        """Test clearing health cache."""
        checker = ProviderHealthChecker()

        checker.mark_unhealthy("claude-code")
        checker.clear_cache()

        assert checker._health_cache == {}
