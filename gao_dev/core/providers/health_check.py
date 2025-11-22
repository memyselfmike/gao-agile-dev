"""Provider health checking."""

from typing import Dict
from datetime import datetime
import structlog

from gao_dev.core.providers.base import IAgentProvider

logger = structlog.get_logger(__name__)


class ProviderHealthChecker:
    """Checks and caches provider health status."""

    def __init__(self, cache_duration: int = 300):
        """
        Initialize health checker.

        Args:
            cache_duration: Cache duration in seconds (default 5 minutes)
        """
        self.cache_duration = cache_duration
        self._health_cache: Dict[str, tuple[bool, datetime]] = {}

    def is_healthy(self, provider_name: str) -> bool:
        """
        Check if provider is healthy.

        Args:
            provider_name: Name of provider

        Returns:
            True if healthy, False otherwise
        """
        # Check cache
        if provider_name in self._health_cache:
            is_healthy, checked_at = self._health_cache[provider_name]
            age = (datetime.now() - checked_at).total_seconds()

            if age < self.cache_duration:
                logger.debug(
                    "health_check_cache_hit",
                    provider=provider_name,
                    is_healthy=is_healthy,
                )
                return is_healthy

        # Cache miss or expired - always return True for now
        # TODO: Implement actual health check
        logger.debug(
            "health_check_cache_miss",
            provider=provider_name,
        )

        # Update cache
        self._health_cache[provider_name] = (True, datetime.now())
        return True

    async def check_provider_health(
        self, provider: IAgentProvider
    ) -> bool:
        """
        Perform actual health check on provider.

        Args:
            provider: Provider instance

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Use provider's validate method
            is_healthy = await provider.validate_configuration()

            # Update cache
            self._health_cache[provider.name] = (is_healthy, datetime.now())

            logger.info(
                "health_check_completed",
                provider=provider.name,
                is_healthy=is_healthy,
            )

            return is_healthy

        except Exception as e:
            logger.error(
                "health_check_failed",
                provider=provider.name,
                error=str(e),
            )

            # Update cache as unhealthy
            self._health_cache[provider.name] = (False, datetime.now())
            return False

    def mark_unhealthy(self, provider_name: str):
        """
        Manually mark a provider as unhealthy.

        Args:
            provider_name: Name of provider
        """
        self._health_cache[provider_name] = (False, datetime.now())
        logger.info("provider_marked_unhealthy", provider=provider_name)

    def clear_cache(self):
        """Clear health cache."""
        self._health_cache.clear()
        logger.debug("health_cache_cleared")
