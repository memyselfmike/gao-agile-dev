"""Custom provider plugin template.

Use this template to create your own custom provider plugin for GAO-Dev.

Instructions:
1. Copy this file to your plugins directory
2. Rename the file and classes
3. Implement your custom provider class
4. Fill in the plugin methods
5. Test with: gao-dev providers list
"""

from typing import Dict, List, Optional, Type

from gao_dev.core.providers.base import (
    AgentContext,
    AgentResult,
    IAgentProvider,
    ProviderCapabilities,
)
from gao_dev.plugins.provider_plugin import BaseProviderPlugin


# ============================================================================
# STEP 1: Implement Your Custom Provider
# ============================================================================


class CustomProvider(IAgentProvider):
    """Your custom provider implementation.

    Replace this with your actual provider logic. You can:
    - Call external APIs
    - Execute CLI commands
    - Interface with custom systems
    - Implement any execution logic

    Required methods:
    - execute_task: Execute a task with the AI agent
    - get_capabilities: Return provider capabilities
    """

    def __init__(
        self,
        api_key: str,
        model: str = "default-model",
        timeout: int = 300,
        **kwargs,
    ):
        """Initialize your custom provider.

        Args:
            api_key: API key for authentication
            model: Model name to use
            timeout: Execution timeout in seconds
            **kwargs: Additional configuration
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.config = kwargs

    def execute_task(
        self,
        task: str,
        context: AgentContext,
        timeout: Optional[int] = None,
    ) -> AgentResult:
        """Execute a task with your custom provider.

        This is where you implement your provider's core logic.

        Args:
            task: Task description/prompt
            context: Execution context (model, tools, etc.)
            timeout: Optional timeout override

        Returns:
            AgentResult with execution results

        Example Implementation:
            ```python
            # Call your API
            response = your_api.execute(
                prompt=task,
                model=context.model or self.model,
                timeout=timeout or self.timeout
            )

            # Parse results
            success = response.status == 200
            output = response.content
            tokens = response.usage.get("total_tokens", 0)
            cost = self._calculate_cost(tokens)

            return AgentResult(
                success=success,
                output=output,
                error=None if success else response.error,
                metadata={
                    "tokens": tokens,
                    "cost": cost,
                    "model": context.model,
                    "duration": response.duration
                }
            )
            ```
        """
        # TODO: Implement your execution logic
        raise NotImplementedError("Implement execute_task for your provider")

    def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities.

        Returns:
            ProviderCapabilities describing what this provider supports
        """
        return ProviderCapabilities(
            supports_streaming=False,  # Set True if you support streaming
            supports_tools=True,  # Set True if you support tool calling
            supports_vision=False,  # Set True if you support vision
            supports_function_calling=False,  # Set True if you support functions
            max_tokens=4000,  # Maximum tokens per request
            supported_models=["model-1", "model-2"],  # List your models
        )


# ============================================================================
# STEP 2: Implement Your Provider Plugin
# ============================================================================


class CustomProviderPlugin(BaseProviderPlugin):
    """Plugin that registers your custom provider.

    This class tells GAO-Dev about your provider and handles configuration.
    """

    def get_provider_name(self) -> str:
        """Get unique name for your provider.

        Returns:
            Provider name (lowercase with hyphens)

        Example: "my-custom-api", "local-llama", "custom-backend"
        """
        # TODO: Set your provider name
        return "custom-provider"

    def get_provider_class(self) -> Type[IAgentProvider]:
        """Get your provider class.

        Returns:
            Your provider class (must implement IAgentProvider)
        """
        return CustomProvider

    def validate_configuration(self, config: Dict) -> bool:
        """Validate provider configuration.

        Check that all required fields are present and valid.

        Args:
            config: Configuration dictionary from user

        Returns:
            True if valid, False otherwise

        Example:
            ```python
            required = ["api_key", "endpoint"]
            if not all(k in config for k in required):
                return False

            # Validate types
            if not isinstance(config.get("timeout"), (int, float, type(None))):
                return False

            return True
            ```
        """
        # TODO: Implement validation for your provider
        required = ["api_key"]  # Adjust based on your needs
        return all(k in config for k in required)

    def get_default_configuration(self) -> Dict:
        """Get default configuration values.

        Returns:
            Dictionary of default values

        Example:
            ```python
            return {
                "model": "default-model",
                "timeout": 300,
                "max_tokens": 4000,
                "temperature": 0.7,
                "endpoint": "https://api.example.com"
            }
            ```
        """
        # TODO: Set your defaults
        return {
            "model": "default-model",
            "timeout": 300,
            "max_tokens": 4000,
        }

    def get_supported_models(self) -> List[str]:
        """Get list of supported models.

        Returns:
            List of model names

        Example: ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"]
        """
        # TODO: List your supported models
        return ["model-1", "model-2"]

    def get_required_tools(self) -> List[str]:
        """Get list of required external tools.

        Returns:
            List of tool names (CLI commands, etc.)

        Example: ["azure-cli", "jq", "curl"]
        """
        # TODO: List any required tools
        return []  # Empty if no external tools needed

    def get_setup_instructions(self) -> Optional[str]:
        """Get setup instructions for users.

        Returns:
            Markdown-formatted setup guide

        Example:
            ```python
            return '''
            # Custom Provider Setup

            ## Prerequisites
            1. Account at example.com
            2. API key from dashboard

            ## Configuration
            ```yaml
            providers:
              custom-provider:
                api_key: "your-api-key"
                endpoint: "https://api.example.com"
            ```

            ## Testing
            ```bash
            gao-dev providers test custom-provider "Hello world"
            ```
            '''
            ```
        """
        # TODO: Write setup instructions
        return """
# Custom Provider Setup

## Configuration

Set your API key:
```bash
export CUSTOM_PROVIDER_API_KEY="your-api-key"
```

Add to defaults.yaml:
```yaml
providers:
  custom-provider:
    api_key: "${CUSTOM_PROVIDER_API_KEY}"
```

## Testing

```bash
gao-dev providers test custom-provider "Hello world"
```
"""


# ============================================================================
# Optional: Lifecycle Hooks
# ============================================================================


# Uncomment and implement if you need initialization logic
"""
def initialize(self) -> bool:
    '''Initialize plugin.

    Called when plugin is loaded. Use for:
    - Checking dependencies
    - Validating environment
    - Setting up resources

    Returns:
        True to continue loading, False to abort
    '''
    # Check if required tools are available
    import shutil
    if not shutil.which("required-tool"):
        logger.warning("required-tool not found")
        return False

    return True


def cleanup(self) -> None:
    '''Cleanup plugin resources.

    Called when plugin is unloaded. Use for:
    - Closing connections
    - Releasing resources
    - Saving state
    '''
    # Clean up any resources
    if hasattr(self, 'connection'):
        self.connection.close()
"""


# ============================================================================
# Testing Your Plugin
# ============================================================================

if __name__ == "__main__":
    """Quick test of your plugin."""
    plugin = CustomProviderPlugin()

    print(f"Provider name: {plugin.get_provider_name()}")
    print(f"Provider class: {plugin.get_provider_class().__name__}")
    print(f"Supported models: {plugin.get_supported_models()}")
    print(f"Required tools: {plugin.get_required_tools()}")

    # Test configuration validation
    valid_config = {"api_key": "test123"}
    invalid_config = {}

    print(f"\nValid config: {plugin.validate_configuration(valid_config)}")
    print(f"Invalid config: {plugin.validate_configuration(invalid_config)}")

    print("\nSetup instructions:")
    print(plugin.get_setup_instructions())
