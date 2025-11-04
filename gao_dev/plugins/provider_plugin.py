"""Provider plugin system for extending GAO-Dev with custom agent providers.

This module enables developers to create custom provider plugins that integrate
seamlessly with GAO-Dev's provider abstraction system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type

from gao_dev.core.providers.base import IAgentProvider
from gao_dev.plugins.base_plugin import BasePlugin


class BaseProviderPlugin(BasePlugin, ABC):
    """Abstract base class for provider plugins.

    Provider plugins extend GAO-Dev with custom agent providers that conform
    to the IAgentProvider interface. This enables support for new AI backends,
    custom execution environments, or specialized provider implementations.

    Example:
        ```python
        from gao_dev.plugins.provider_plugin import BaseProviderPlugin
        from gao_dev.core.providers.base import IAgentProvider

        class MyCustomProvider(IAgentProvider):
            # ... implement IAgentProvider interface
            pass

        class MyProviderPlugin(BaseProviderPlugin):
            def get_provider_name(self) -> str:
                return "my-custom"

            def get_provider_class(self) -> Type[IAgentProvider]:
                return MyCustomProvider

            def validate_configuration(self, config: Dict) -> bool:
                required = ["api_key", "model"]
                return all(k in config for k in required)

            def get_default_configuration(self) -> Dict:
                return {
                    "model": "default-model",
                    "timeout": 300
                }
        ```

    Lifecycle:
        1. Plugin loaded by PluginLoader
        2. initialize() called
        3. register_provider() called by ProviderPluginManager
        4. Provider registered in ProviderFactory
        5. Plugin active - provider can be used
        6. cleanup() called on shutdown
    """

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get unique name for this provider.

        This name is used to identify the provider in configuration files
        and when creating provider instances.

        Returns:
            Unique provider name (e.g., "azure-openai", "local-llama")

        Note:
            Provider names should be lowercase with hyphens, following
            the same convention as built-in providers.
        """
        pass

    @abstractmethod
    def get_provider_class(self) -> Type[IAgentProvider]:
        """Get the provider class to register.

        Returns:
            Class that implements IAgentProvider interface

        Raises:
            ValueError: If class doesn't implement IAgentProvider
        """
        pass

    def validate_configuration(self, config: Dict) -> bool:
        """Validate provider-specific configuration.

        Override this method to implement custom validation logic for
        provider configuration. This is called before provider creation.

        Args:
            config: Provider configuration dictionary

        Returns:
            True if configuration is valid, False otherwise

        Example:
            ```python
            def validate_configuration(self, config: Dict) -> bool:
                # Check required fields
                required = ["api_key", "model", "endpoint"]
                if not all(k in config for k in required):
                    return False

                # Validate field types
                if not isinstance(config.get("timeout"), (int, float)):
                    return False

                return True
            ```
        """
        return True  # Default: accept all configurations

    def get_default_configuration(self) -> Dict:
        """Get default configuration for this provider.

        Override this method to provide sensible defaults that users
        can override in their configuration files.

        Returns:
            Dictionary of default configuration values

        Example:
            ```python
            def get_default_configuration(self) -> Dict:
                return {
                    "model": "gpt-4",
                    "timeout": 300,
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            ```
        """
        return {}

    def get_supported_models(self) -> List[str]:
        """Get list of models supported by this provider.

        Override this method to specify which models can be used with
        this provider. This helps with validation and user guidance.

        Returns:
            List of supported model names

        Example:
            ```python
            def get_supported_models(self) -> List[str]:
                return [
                    "gpt-4",
                    "gpt-4-turbo",
                    "gpt-3.5-turbo"
                ]
            ```
        """
        return []  # Default: no restrictions

    def get_required_tools(self) -> List[str]:
        """Get list of external tools required by this provider.

        Override this method to specify command-line tools or dependencies
        that must be available for the provider to function.

        Returns:
            List of required tool names (e.g., ["bun", "opencode"])

        Example:
            ```python
            def get_required_tools(self) -> List[str]:
                return ["azure-cli", "jq"]
            ```
        """
        return []  # Default: no external tools required

    def get_setup_instructions(self) -> Optional[str]:
        """Get setup instructions for this provider.

        Override this method to provide user-friendly setup documentation
        that will be displayed when the provider is not properly configured.

        Returns:
            Setup instructions as markdown string, or None

        Example:
            ```python
            def get_setup_instructions(self) -> Optional[str]:
                return '''
                # Azure OpenAI Setup

                1. Install Azure CLI: `az login`
                2. Set environment variables:
                   - AZURE_OPENAI_ENDPOINT
                   - AZURE_OPENAI_API_KEY
                3. Configure in defaults.yaml:
                   ```yaml
                   providers:
                     azure-openai:
                       deployment: my-gpt4-deployment
                   ```
                '''
            ```
        """
        return None

    def on_provider_registered(self) -> None:
        """Called after provider is successfully registered.

        Override this method to perform actions after registration,
        such as logging, validation checks, or initialization.

        Example:
            ```python
            def on_provider_registered(self) -> None:
                import structlog
                logger = structlog.get_logger()
                logger.info(
                    "custom_provider_registered",
                    provider=self.get_provider_name()
                )
            ```
        """
        pass
