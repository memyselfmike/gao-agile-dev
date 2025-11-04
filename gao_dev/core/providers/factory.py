"""Provider factory for creating agent execution providers."""

from typing import Dict, Type, Optional, List
from pathlib import Path
import structlog

from .base import IAgentProvider
from .claude_code import ClaudeCodeProvider
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

        logger.info(
            "provider_factory_initialized",
            providers=list(self._registry.keys())
        )

    def create_provider(
        self,
        provider_name: str,
        config: Optional[Dict] = None
    ) -> IAgentProvider:
        """
        Create a provider instance.

        Args:
            provider_name: Provider identifier (e.g., 'claude-code')
            config: Optional provider-specific configuration

        Returns:
            Configured provider instance

        Raises:
            ProviderNotFoundError: If provider not registered
            ProviderCreationError: If provider creation fails

        Example:
            ```python
            provider = factory.create_provider(
                "claude-code",
                config={"cli_path": "/usr/bin/claude", "api_key": "sk-..."}
            )
            ```
        """
        provider_name_lower = provider_name.lower()

        if provider_name_lower not in self._registry:
            available = ", ".join(self._registry.keys())
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
            # ['claude-code', 'opencode', 'custom']
            ```
        """
        return sorted(self._registry.keys())

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
        return provider_name.lower() in self._registry

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
        builtin_providers = {
            "claude-code": ClaudeCodeProvider,
            # Future: add opencode, direct-api when implemented
        }

        for name, provider_class in builtin_providers.items():
            self._registry[name] = provider_class

        logger.debug(
            "builtin_providers_registered",
            count=len(builtin_providers),
            providers=list(builtin_providers.keys())
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"ProviderFactory(providers={list(self._registry.keys())})"
