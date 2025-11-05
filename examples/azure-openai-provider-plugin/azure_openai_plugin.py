"""Example Azure OpenAI provider plugin.

This example demonstrates how to create a custom provider plugin that integrates
Azure OpenAI with GAO-Dev's provider abstraction system.
"""

from pathlib import Path
from typing import Dict, List, Optional, Type

from gao_dev.core.providers.base import IAgentProvider
from gao_dev.core.providers.direct_api import DirectAPIProvider
from gao_dev.plugins.provider_plugin import BaseProviderPlugin


class AzureOpenAIProvider(DirectAPIProvider):
    """Azure OpenAI provider using direct API calls.

    This provider extends DirectAPIProvider to support Azure OpenAI's
    specific endpoint and authentication requirements.
    """

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment: str,
        api_version: str = "2024-02-01",
        **kwargs,
    ):
        """Initialize Azure OpenAI provider.

        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint URL
            deployment: Deployment name (e.g., "my-gpt4-deployment")
            api_version: API version string
            **kwargs: Additional configuration (timeout, max_tokens, etc.)
        """
        super().__init__(
            api_key=api_key,
            provider_type="azure",
            **kwargs,
        )
        self.endpoint = endpoint
        self.deployment = deployment
        self.api_version = api_version

    def _get_base_url(self) -> str:
        """Get Azure OpenAI base URL."""
        return (
            f"{self.endpoint}/openai/deployments/{self.deployment}"
            f"/chat/completions?api-version={self.api_version}"
        )


class AzureOpenAIProviderPlugin(BaseProviderPlugin):
    """Provider plugin for Azure OpenAI.

    This plugin demonstrates how to:
    - Create a custom provider class
    - Validate Azure-specific configuration
    - Provide default configuration
    - List supported models
    - Specify required tools
    - Provide setup instructions
    """

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "azure-openai"

    def get_provider_class(self) -> Type[IAgentProvider]:
        """Get provider class."""
        return AzureOpenAIProvider

    def validate_configuration(self, config: Dict) -> bool:
        """Validate Azure OpenAI configuration.

        Required fields:
        - api_key: Azure OpenAI API key
        - endpoint: Azure OpenAI endpoint URL
        - deployment: Deployment name

        Optional fields:
        - api_version: API version (default: "2024-02-01")
        - timeout: Request timeout in seconds (default: 300)
        - max_tokens: Maximum tokens per request (default: 4000)
        """
        required = ["api_key", "endpoint", "deployment"]

        # Check required fields
        if not all(k in config for k in required):
            return False

        # Validate endpoint format
        endpoint = config.get("endpoint", "")
        if not endpoint.startswith("https://"):
            return False

        # Validate timeout if provided
        timeout = config.get("timeout")
        if timeout is not None and not isinstance(timeout, (int, float)):
            return False

        # Validate max_tokens if provided
        max_tokens = config.get("max_tokens")
        if max_tokens is not None and not isinstance(max_tokens, int):
            return False

        return True

    def get_default_configuration(self) -> Dict:
        """Get default configuration."""
        return {
            "api_version": "2024-02-01",
            "timeout": 300,
            "max_tokens": 4000,
            "temperature": 0.7,
        }

    def get_supported_models(self) -> List[str]:
        """Get supported models.

        Note: Azure OpenAI uses deployments, not model names directly.
        This list shows which base models can be deployed.
        """
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-32k",
            "gpt-35-turbo",
            "gpt-35-turbo-16k",
        ]

    def get_required_tools(self) -> List[str]:
        """Get required tools.

        Azure CLI is recommended but not strictly required.
        """
        return []  # No CLI tools required for API access

    def get_setup_instructions(self) -> Optional[str]:
        """Get setup instructions."""
        return """
# Azure OpenAI Provider Setup

## Prerequisites

1. **Azure Subscription**: You need an active Azure subscription
2. **Azure OpenAI Resource**: Create an Azure OpenAI resource in Azure portal
3. **Model Deployment**: Deploy a model (e.g., GPT-4) in your resource

## Configuration Steps

### 1. Get Azure OpenAI Credentials

Visit Azure Portal > Your OpenAI Resource > Keys and Endpoint

Copy:
- **Endpoint**: e.g., `https://your-resource.openai.azure.com/`
- **API Key**: e.g., `abc123...`
- **Deployment Name**: e.g., `my-gpt4-deployment`

### 2. Configure Environment Variables (Option 1)

```bash
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="my-gpt4-deployment"
```

### 3. Configure in defaults.yaml (Option 2)

```yaml
providers:
  azure-openai:
    api_key: "${AZURE_OPENAI_API_KEY}"
    endpoint: "${AZURE_OPENAI_ENDPOINT}"
    deployment: "${AZURE_OPENAI_DEPLOYMENT}"
    api_version: "2024-02-01"
    timeout: 300
    max_tokens: 4000
```

### 4. Use in Agent Configuration

```yaml
# gao_dev/config/agents/amelia.yaml
agent:
  configuration:
    provider: azure-openai
    # provider_config will use defaults from defaults.yaml
```

## Testing

Test your configuration:

```bash
gao-dev providers list
gao-dev providers validate azure-openai
gao-dev providers test azure-openai "Write a hello world function"
```

## Troubleshooting

**Error: "Invalid endpoint URL"**
- Ensure endpoint starts with `https://`
- Don't include `/openai/deployments/...` in endpoint
- Example: `https://your-resource.openai.azure.com/`

**Error: "Deployment not found"**
- Verify deployment name matches Azure portal
- Deployment names are case-sensitive
- Check the deployment is in "Succeeded" state

**Error: "API key invalid"**
- Regenerate key in Azure portal
- Ensure no extra spaces in key
- Try KEY 1 or KEY 2 from portal

## Resources

- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure OpenAI Quickstart](https://learn.microsoft.com/azure/ai-services/openai/quickstart)
"""
