"""Provider factory for creating agent execution providers."""

from typing import Dict, Type, Optional, List
from pathlib import Path
import structlog

from .base import IAgentProvider
from .claude_code import ClaudeCodeProvider
from .opencode import OpenCodeProvider
from .cache import ProviderCache, hash_config
from .exceptions import (
    ProviderNotFoundError,
    ProviderCreationError,
    ProviderRegistrationError,
    DuplicateProviderError
)

logger = structlog.get_logger()


class ProviderFactory:
    """
    Factory for creating agent execution providers.

    Implements Factory Pattern with registry for plugin support.

    Features:
    - Automatic registration of built-in providers
    - Plugin provider registration
    - Configuration-driven provider creation
    - Provider discovery and listing

    Thread Safety: Not thread-safe. Use one instance per orchestrator.

    Example:
        ```python
        factory = ProviderFactory()

        # List available providers
        providers = factory.list_providers()
        print(providers)  # ['claude-code']

        # Create provider
        provider = factory.create_provider(
            "claude-code",
            config={"api_key": "sk-..."}
        )

        # Register custom provider
        factory.register_provider("custom", CustomProvider)
        ```
    """

    def __init__(self):
        """Initialize factory with built-in providers."""
        self._registry: Dict[str, Type[IAgentProvider]] = {}
        self._register_builtin_providers()

        # Provider instance cache for performance
        self._cache = ProviderCache(max_size=10, ttl_seconds=3600)

        # Model name translation cache (immutable)
        self._model_cache: Dict[str, str] = {}

        logger.info(
            "provider_factory_initialized",
            providers=list(self._registry.keys())
        )

    def create_provider(
        self,
        provider_name: str,
        config: Optional[Dict] = None,
        use_cache: bool = True
    ) -> IAgentProvider:
        """
        Create a provider instance with caching.

        Args:
            provider_name: Provider identifier (e.g., 'claude-code', 'direct-api-anthropic')
            config: Optional provider-specific configuration
            use_cache: Whether to use cached provider if available (default: True)

        Returns:
            Configured provider instance (may be cached)

        Raises:
            ProviderNotFoundError: If provider not registered
            ProviderCreationError: If provider creation fails

        Example:
            ```python
            provider = factory.create_provider(
                "claude-code",
                config={"cli_path": "/usr/bin/claude", "api_key": "sk-..."}
            )

            # Direct API provider
            provider = factory.create_provider(
                "direct-api-anthropic",
                config={"api_key": "sk-..."}
            )
            ```
        """
        provider_name_lower = provider_name.lower()

        # Check cache first (if enabled)
        if use_cache:
            config_hash = hash_config(config)
            cached = self._cache.get(provider_name_lower, config_hash)

            if cached is not None:
                logger.debug(
                    "provider_factory_cache_hit",
                    provider=provider_name_lower,
                )
                return cached

        # Special handling for direct-api providers
        if provider_name_lower.startswith("direct-api-"):
            from .direct_api import DirectAPIProvider

            provider_type = provider_name_lower.replace("direct-api-", "")

            try:
                config = config or {}
                provider = DirectAPIProvider(provider=provider_type, **config)

                # Cache the provider
                if use_cache:
                    config_hash = hash_config(config)
                    self._cache.put(provider_name_lower, config_hash, provider)

                logger.info(
                    "provider_created",
                    provider_name=provider_name,
                    provider_version=provider.version
                )

                return provider

            except Exception as e:
                logger.error(
                    "provider_creation_failed",
                    provider_name=provider_name,
                    error=str(e),
                    exc_info=True
                )
                raise ProviderCreationError(
                    f"Failed to create provider '{provider_name}': {e}"
                ) from e

        # Standard provider creation
        if provider_name_lower not in self._registry:
            available = ", ".join(self.list_providers())
            raise ProviderNotFoundError(
                f"Provider '{provider_name}' not found. "
                f"Available providers: {available}"
            )

        provider_class = self._registry[provider_name_lower]

        try:
            # Create instance with config
            if config:
                provider = provider_class(**config)
            else:
                provider = provider_class()

            # Cache the provider
            if use_cache:
                config_hash = hash_config(config)
                self._cache.put(provider_name_lower, config_hash, provider)

            logger.info(
                "provider_created",
                provider_name=provider_name,
                provider_version=provider.version
            )

            return provider

        except Exception as e:
            logger.error(
                "provider_creation_failed",
                provider_name=provider_name,
                error=str(e),
                exc_info=True
            )
            raise ProviderCreationError(
                f"Failed to create provider '{provider_name}': {e}"
            ) from e

    def register_provider(
        self,
        provider_name: str,
        provider_class: Type[IAgentProvider],
        allow_override: bool = False
    ) -> None:
        """
        Register a provider class (for plugins).

        Args:
            provider_name: Unique provider identifier
            provider_class: Class implementing IAgentProvider
            allow_override: Allow overriding existing registration

        Raises:
            ProviderRegistrationError: If class doesn't implement interface
            DuplicateProviderError: If provider already registered

        Example:
            ```python
            class CustomProvider(IAgentProvider):
                # Implementation
                pass

            factory.register_provider("custom", CustomProvider)
            ```
        """
        # Validate interface implementation
        if not issubclass(provider_class, IAgentProvider):
            raise ProviderRegistrationError(
                f"Provider class '{provider_class.__name__}' must "
                f"implement IAgentProvider interface"
            )

        provider_name_lower = provider_name.lower()

        # Check for duplicates
        if provider_name_lower in self._registry and not allow_override:
            raise DuplicateProviderError(
                f"Provider '{provider_name}' already registered. "
                f"Use allow_override=True to replace."
            )

        # Register
        self._registry[provider_name_lower] = provider_class

        logger.info(
            "provider_registered",
            provider_name=provider_name,
            provider_class=provider_class.__name__,
            override=allow_override and provider_name_lower in self._registry
        )

    def list_providers(self) -> List[str]:
        """
        List all registered provider names.

        Returns:
            Sorted list of provider identifiers

        Example:
            ```python
            providers = factory.list_providers()
            # ['claude-code', 'direct-api-anthropic', 'direct-api-google',
            #  'direct-api-openai', 'opencode']
            ```
        """
        providers = list(self._registry.keys())

        # Add direct-api providers
        providers.extend([
            "direct-api-anthropic",
            "direct-api-openai",
            "direct-api-google",
        ])

        return sorted(providers)

    def provider_exists(self, provider_name: str) -> bool:
        """
        Check if a provider is registered.

        Args:
            provider_name: Provider identifier

        Returns:
            True if registered, False otherwise

        Example:
            ```python
            if factory.provider_exists("claude-code"):
                provider = factory.create_provider("claude-code")
            ```
        """
        provider_name_lower = provider_name.lower()

        # Check direct-api providers
        if provider_name_lower.startswith("direct-api-"):
            provider_type = provider_name_lower.replace("direct-api-", "")
            return provider_type in ["anthropic", "openai", "google"]

        return provider_name_lower in self._registry

    def get_provider_class(self, provider_name: str) -> Type[IAgentProvider]:
        """
        Get provider class without instantiating.

        Useful for inspection and validation.

        Args:
            provider_name: Provider identifier

        Returns:
            Provider class

        Raises:
            ProviderNotFoundError: If provider not registered

        Example:
            ```python
            provider_class = factory.get_provider_class("claude-code")
            # Inspect class attributes
            print(provider_class.MODEL_MAPPING)
            ```
        """
        provider_name_lower = provider_name.lower()

        if provider_name_lower not in self._registry:
            raise ProviderNotFoundError(
                f"Provider '{provider_name}' not registered"
            )

        return self._registry[provider_name_lower]

    def _register_builtin_providers(self) -> None:
        """Register all built-in providers."""
        from .direct_api import DirectAPIProvider

        builtin_providers = {
            "claude-code": ClaudeCodeProvider,
            "opencode": OpenCodeProvider,
            "direct-api-anthropic": lambda: DirectAPIProvider(provider="anthropic"),
            "direct-api-openai": lambda: DirectAPIProvider(provider="openai"),
            "direct-api-google": lambda: DirectAPIProvider(provider="google"),
        }

        # Note: Direct API providers need special handling since they require a provider parameter
        # Register claude-code and opencode normally
        self._registry["claude-code"] = ClaudeCodeProvider
        self._registry["opencode"] = OpenCodeProvider

        # For direct-api, we'll need a wrapper or special handling in create_provider
        # For now, register them with a special marker
        logger.debug(
            "builtin_providers_registered",
            count=2,  # Only actual registered providers
            providers=["claude-code", "opencode"]
        )

    def translate_model_name(
        self,
        provider_name: str,
        canonical_name: str
    ) -> str:
        """
        Translate model name with caching.

        Translates canonical model names (e.g., 'sonnet-4.5') to
        provider-specific identifiers. Results are cached for performance.

        Args:
            provider_name: Provider identifier
            canonical_name: Canonical model name

        Returns:
            Provider-specific model ID

        Raises:
            ProviderNotFoundError: If provider not found

        Example:
            ```python
            model_id = factory.translate_model_name("claude-code", "sonnet-4.5")
            # "claude-sonnet-4-5-20250929"
            ```
        """
        # Check cache
        cache_key = f"{provider_name}:{canonical_name}"
        if cache_key in self._model_cache:
            logger.debug(
                "model_translation_cache_hit",
                provider=provider_name,
                canonical=canonical_name,
            )
            return self._model_cache[cache_key]

        # Cache miss - translate
        provider = self.create_provider(provider_name)
        translated = provider.translate_model_name(canonical_name)

        # Cache result (model mappings don't change)
        self._model_cache[cache_key] = translated

        logger.debug(
            "model_translation_cached",
            provider=provider_name,
            canonical=canonical_name,
            translated=translated,
        )

        return translated

    def clear_cache(self) -> None:
        """
        Clear all caches.

        Useful for testing or when configuration changes.

        Example:
            ```python
            factory.clear_cache()
            ```
        """
        self._cache.clear()
        self._model_cache.clear()
        logger.info("factory_cache_cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dict with cache sizes

        Example:
            ```python
            stats = factory.get_cache_stats()
            # {"provider_cache_size": 3, "model_cache_size": 12}
            ```
        """
        return {
            "provider_cache_size": self._cache.size(),
            "model_cache_size": len(self._model_cache),
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"ProviderFactory(providers={list(self._registry.keys())})"
