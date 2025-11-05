"""Provider instance caching for performance."""

import hashlib
import json
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import structlog

from gao_dev.core.providers.base import IAgentProvider

logger = structlog.get_logger(__name__)


class ProviderCacheEntry:
    """Cache entry for a provider instance."""

    def __init__(self, provider: IAgentProvider):
        """
        Initialize cache entry.

        Args:
            provider: Provider instance to cache
        """
        self.provider = provider
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 0

    def touch(self) -> None:
        """Update last accessed time and increment access count."""
        self.last_accessed = datetime.now()
        self.access_count += 1


class ProviderCache:
    """
    Thread-safe cache for provider instances.

    Caches providers by (provider_name, config_hash) to avoid
    repeated initialization. Implements LRU eviction and TTL expiration.

    Example:
        cache = ProviderCache(max_size=10, ttl_seconds=3600)
        provider = cache.get("claude-code", config_hash)
        if provider is None:
            provider = ClaudeCodeProvider()
            cache.put("claude-code", config_hash, provider)
    """

    def __init__(
        self,
        max_size: int = 10,
        ttl_seconds: int = 3600,
    ):
        """
        Initialize provider cache.

        Args:
            max_size: Maximum number of cached providers
            ttl_seconds: Time-to-live for cached providers in seconds
        """
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: Dict[str, ProviderCacheEntry] = {}
        self._lock = threading.RLock()

        logger.debug(
            "provider_cache_initialized",
            max_size=max_size,
            ttl_seconds=ttl_seconds,
        )

    def get(
        self,
        provider_name: str,
        config_hash: str,
    ) -> Optional[IAgentProvider]:
        """
        Get cached provider.

        Args:
            provider_name: Name of provider
            config_hash: Hash of configuration

        Returns:
            Cached provider, or None if not found or expired
        """
        cache_key = f"{provider_name}:{config_hash}"

        with self._lock:
            entry = self._cache.get(cache_key)

            if entry is None:
                logger.debug("provider_cache_miss", key=cache_key)
                return None

            # Check if expired
            age = datetime.now() - entry.created_at
            if age > self.ttl:
                logger.debug(
                    "provider_cache_expired",
                    key=cache_key,
                    age_seconds=age.total_seconds(),
                )
                del self._cache[cache_key]
                return None

            # Update access tracking
            entry.touch()

            logger.debug(
                "provider_cache_hit",
                key=cache_key,
                access_count=entry.access_count,
            )

            return entry.provider

    def put(
        self,
        provider_name: str,
        config_hash: str,
        provider: IAgentProvider,
    ) -> None:
        """
        Put provider in cache.

        Args:
            provider_name: Name of provider
            config_hash: Hash of configuration
            provider: Provider instance to cache
        """
        cache_key = f"{provider_name}:{config_hash}"

        with self._lock:
            # Evict if at max size
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                self._evict_lru()

            # Add to cache
            self._cache[cache_key] = ProviderCacheEntry(provider)

            logger.debug(
                "provider_cache_put",
                key=cache_key,
                cache_size=len(self._cache),
            )

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed,
        )

        del self._cache[lru_key]

        logger.debug("provider_cache_evicted", key=lru_key)

    def clear(self) -> None:
        """Clear all cached providers."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.debug("provider_cache_cleared", count=count)

    def size(self) -> int:
        """
        Get current cache size.

        Returns:
            Number of cached providers
        """
        with self._lock:
            return len(self._cache)


def hash_config(config: Optional[Dict[str, Any]]) -> str:
    """
    Hash configuration for cache key.

    Creates a stable hash from configuration dict that can be used
    as a cache key. Handles nested dicts and sorts keys for consistency.

    Args:
        config: Configuration dict

    Returns:
        Hash string (hexdigest)

    Example:
        config = {"api_key": "sk-123", "model": "claude-3"}
        hash_str = hash_config(config)  # "a1b2c3d4..."
    """
    if config is None:
        return "default"

    # Sort keys for consistent hashing
    sorted_config = _sort_dict(config)

    # Convert to JSON string
    json_str = json.dumps(sorted_config, sort_keys=True)

    # Hash the JSON string
    hash_obj = hashlib.sha256(json_str.encode("utf-8"))

    return hash_obj.hexdigest()[:16]  # First 16 chars for brevity


def _sort_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sort dictionary by keys.

    Args:
        d: Dictionary to sort

    Returns:
        Sorted dictionary
    """
    result = {}
    for key in sorted(d.keys()):
        value = d[key]
        if isinstance(value, dict):
            result[key] = _sort_dict(value)
        else:
            result[key] = value
    return result
