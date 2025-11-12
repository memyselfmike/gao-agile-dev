# Interactive Provider Selection - Integration Guide

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Version**: 1.0
**Last Updated**: 2025-01-12

---

## Adding New Provider Types

This guide shows how to add custom AI providers to GAO-Dev.

### Step 1: Implement Provider Interface

Create a new provider class implementing `BaseProvider`:

```python
# gao_dev/core/providers/my_provider.py

from gao_dev.core.providers.base import BaseProvider

class MyCustomProvider(BaseProvider):
    """Custom AI provider implementation."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = os.getenv(config.get('api_key_env', 'MY_API_KEY'))
        self.model = config.get('model', 'default-model')

    def execute(self, prompt: str, **kwargs) -> str:
        """Execute prompt with custom provider."""
        # Implement your provider logic here
        response = self._call_api(prompt)
        return response

    def _call_api(self, prompt: str) -> str:
        """Call custom API."""
        # Your API integration here
        pass
```

### Step 2: Register in ProviderFactory

Add your provider to the factory:

```python
# gao_dev/core/providers/factory.py

from gao_dev.core.providers.my_provider import MyCustomProvider

class ProviderFactory:
    def __init__(self):
        self._providers = {
            'claude-code': ClaudeCodeProvider,
            'opencode': OpenCodeProvider,
            'my-provider': MyCustomProvider,  # Add here
        }
```

### Step 3: Add to ProviderSelector

Update provider lists:

```python
# gao_dev/cli/provider_selector.py

AVAILABLE_PROVIDERS = [
    "claude-code",
    "opencode",
    "direct-api-anthropic",
    "my-provider",  # Add here
]

PROVIDER_DESCRIPTIONS = {
    "claude-code": "Claude Code CLI (Anthropic)",
    "opencode": "OpenCode CLI (Multi-provider)",
    "direct-api-anthropic": "Direct Anthropic API",
    "my-provider": "My Custom Provider",  # Add description
}

DEFAULT_MODELS = {
    "claude-code": "sonnet-4.5",
    "opencode": "deepseek-r1",
    "direct-api-anthropic": "claude-3-5-sonnet-20241022",
    "my-provider": "default-model",  # Add default
}

AVAILABLE_MODELS = {
    "claude-code": ["sonnet-4.5", "opus-4", "haiku-3.5"],
    "opencode": ["deepseek-r1", "llama2", "codellama"],
    "direct-api-anthropic": [...],
    "my-provider": ["model-1", "model-2"],  # Add models
}
```

### Step 4: Implement Validation

Add validation logic to `ProviderValidator`:

```python
# gao_dev/cli/provider_validator.py

class ProviderValidator:
    def suggest_fixes(self, provider_name: str) -> List[str]:
        # ... existing code ...

        elif provider_name == "my-provider":
            suggestions.append("Install My Provider: pip install my-provider")
            suggestions.append("Set API key: export MY_API_KEY=...")
            suggestions.append("Verify: my-provider --version")

        return suggestions
```

### Step 5: Test Your Provider

Create tests:

```python
# tests/providers/test_my_provider.py

import pytest
from gao_dev.core.providers.my_provider import MyCustomProvider

class TestMyCustomProvider:
    def test_initialization(self):
        """Test provider initialization."""
        config = {'api_key_env': 'MY_API_KEY', 'model': 'test-model'}
        provider = MyCustomProvider(config)
        assert provider.model == 'test-model'

    def test_execute(self):
        """Test prompt execution."""
        provider = MyCustomProvider({'model': 'test-model'})
        result = provider.execute("Test prompt")
        assert isinstance(result, str)
```

### Step 6: Document Your Provider

Update documentation:

```markdown
## My Custom Provider

### Installation

```bash
pip install my-provider
```

### Configuration

```yaml
provider:
  name: "my-provider"
  model: "model-1"
  config:
    api_key_env: "MY_API_KEY"
```

### Usage

```bash
export MY_API_KEY=your-key-here
export AGENT_PROVIDER=my-provider
gao-dev start
```
```

---

## Best Practices

1. **Error Handling**: Implement robust error handling and retries
2. **Logging**: Use structlog for consistent logging
3. **Security**: Never log API keys or sensitive data
4. **Testing**: Achieve >90% test coverage
5. **Documentation**: Document all configuration options

---

## Related Documentation

- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Testing**: [TESTING.md](TESTING.md)

---

**Version**: 1.0
**Last Updated**: 2025-01-12
