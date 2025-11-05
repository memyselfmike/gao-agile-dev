# Azure OpenAI Provider Plugin Example

This example demonstrates how to create a custom provider plugin for GAO-Dev that integrates Azure OpenAI.

## Overview

The Azure OpenAI provider plugin shows how to:

- **Extend DirectAPIProvider**: Customize API provider for Azure-specific requirements
- **Implement BaseProviderPlugin**: Create plugin interface for registration
- **Validate Configuration**: Ensure required Azure credentials are present
- **Provide Documentation**: Setup instructions and troubleshooting
- **Support Multiple Models**: List available Azure OpenAI models

## Files

- `azure_openai_plugin.py` - Plugin implementation
- `README.md` - This file

## Installation

### 1. Copy Plugin to Plugins Directory

```bash
cp -r examples/azure-openai-provider-plugin ~/.gao-dev/plugins/
```

Or add to project-local plugins:

```bash
mkdir -p plugins
cp -r examples/azure-openai-provider-plugin plugins/
```

### 2. Configure Azure OpenAI Credentials

Set environment variables:

```bash
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="my-gpt4-deployment"
```

Or add to `gao_dev/config/defaults.yaml`:

```yaml
providers:
  azure-openai:
    api_key: "${AZURE_OPENAI_API_KEY}"
    endpoint: "${AZURE_OPENAI_ENDPOINT}"
    deployment: "${AZURE_OPENAI_DEPLOYMENT}"
    api_version: "2024-02-01"
```

### 3. Verify Installation

```bash
# List providers (should include azure-openai)
gao-dev providers list

# Validate configuration
gao-dev providers validate azure-openai

# Test provider
gao-dev providers test azure-openai "Write a hello world function in Python"
```

## Usage

### In Agent Configuration

Configure agents to use Azure OpenAI:

```yaml
# gao_dev/config/agents/amelia.yaml
agent:
  metadata:
    name: Amelia
    role: Software Developer

  configuration:
    provider: azure-openai
    model: gpt-4  # Uses your Azure deployment
    max_tokens: 4000
    temperature: 0.7
```

### In Code

```python
from gao_dev.core.providers.factory import ProviderFactory
from gao_dev.plugins.provider_plugin_manager import ProviderPluginManager
from examples.azure_openai_provider_plugin.azure_openai_plugin import (
    AzureOpenAIProviderPlugin
)

# Initialize factory and manager
factory = ProviderFactory()
manager = ProviderPluginManager(factory)

# Register plugin
plugin = AzureOpenAIProviderPlugin()
plugin.initialize()
manager.register_plugin(plugin)

# Create provider instance
provider = factory.create_provider(
    "azure-openai",
    {
        "api_key": "your-api-key",
        "endpoint": "https://your-resource.openai.azure.com/",
        "deployment": "my-gpt4-deployment"
    }
)

# Use provider
result = provider.execute_task(
    "Write a hello world function",
    model="gpt-4",
    tools=["Read", "Write", "Edit"]
)
```

## Customization

### Add Custom Validation

```python
def validate_configuration(self, config: Dict) -> bool:
    """Add custom validation logic."""
    # Call parent validation
    if not super().validate_configuration(config):
        return False

    # Add custom checks
    deployment = config.get("deployment", "")
    if "prod" in deployment and not self._is_authorized_for_prod():
        return False

    return True
```

### Override Default Configuration

```python
def get_default_configuration(self) -> Dict:
    """Customize defaults."""
    defaults = super().get_default_configuration()
    defaults.update({
        "timeout": 600,  # Longer timeout
        "max_tokens": 8000,  # More tokens
        "api_version": "2024-03-01"  # Newer API
    })
    return defaults
```

### Add Setup Validation

```python
def initialize(self) -> bool:
    """Validate setup on initialization."""
    # Check Azure CLI is installed
    import subprocess
    try:
        subprocess.run(["az", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Azure CLI not found - some features may not work")

    return True
```

## Testing

### Unit Tests

```python
import pytest
from azure_openai_plugin import AzureOpenAIProviderPlugin

def test_provider_name():
    plugin = AzureOpenAIProviderPlugin()
    assert plugin.get_provider_name() == "azure-openai"

def test_configuration_validation():
    plugin = AzureOpenAIProviderPlugin()

    # Valid config
    valid_config = {
        "api_key": "abc123",
        "endpoint": "https://my-resource.openai.azure.com/",
        "deployment": "my-gpt4"
    }
    assert plugin.validate_configuration(valid_config)

    # Invalid config - missing endpoint
    invalid_config = {
        "api_key": "abc123",
        "deployment": "my-gpt4"
    }
    assert not plugin.validate_configuration(invalid_config)

def test_supported_models():
    plugin = AzureOpenAIProviderPlugin()
    models = plugin.get_supported_models()
    assert "gpt-4" in models
    assert "gpt-35-turbo" in models
```

### Integration Tests

```python
def test_azure_openai_provider_execution():
    """Test actual Azure OpenAI execution."""
    plugin = AzureOpenAIProviderPlugin()
    provider_class = plugin.get_provider_class()

    provider = provider_class(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT")
    )

    result = provider.execute_task(
        "Write a function that adds two numbers",
        model="gpt-4",
        tools=["Write"]
    )

    assert result.success
    assert "def" in result.output
```

## Troubleshooting

### Plugin Not Discovered

**Problem**: `gao-dev providers list` doesn't show azure-openai

**Solution**:
1. Ensure plugin is in correct directory (`~/.gao-dev/plugins/` or `./plugins/`)
2. Check plugin file name matches import (avoid hyphens, use underscores)
3. Verify plugin class inherits from `BaseProviderPlugin`
4. Run with debug logging: `gao-dev --log-level debug providers list`

### Configuration Validation Fails

**Problem**: `gao-dev providers validate azure-openai` fails

**Solution**:
1. Check environment variables are set correctly
2. Verify endpoint format (must start with `https://`)
3. Ensure deployment name matches Azure portal exactly
4. Test API key with curl:
   ```bash
   curl -H "api-key: $AZURE_OPENAI_API_KEY" \
        "$AZURE_OPENAI_ENDPOINT/openai/deployments/$AZURE_OPENAI_DEPLOYMENT/chat/completions?api-version=2024-02-01"
   ```

### Provider Execution Fails

**Problem**: Tasks fail when using azure-openai provider

**Solution**:
1. Check Azure OpenAI service status
2. Verify deployment is in "Succeeded" state
3. Check rate limits (Azure has quota limits)
4. Enable debug logging to see API responses
5. Test with simple task first: `gao-dev providers test azure-openai "Say hello"`

## Resources

- [GAO-Dev Provider Plugin Guide](../../docs/provider-plugin-development.md)
- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Provider Interface Reference](../../docs/api/provider-api-reference.md)

## License

This example is part of GAO-Dev and follows the same license.
