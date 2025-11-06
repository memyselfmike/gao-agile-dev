# Provider Plugin Development Guide

This guide shows you how to create custom provider plugins for GAO-Dev, enabling integration with any AI backend or execution environment.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Provider Plugin Architecture](#provider-plugin-architecture)
4. [Creating a Provider](#creating-a-provider)
5. [Creating a Plugin](#creating-a-plugin)
6. [Testing](#testing)
7. [Distribution](#distribution)
8. [Examples](#examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

Provider plugins extend GAO-Dev with custom agent providers. Use cases include:

- **Alternative AI Backends**: Azure OpenAI, Google Gemini, local LLMs
- **Custom Execution Environments**: Containers, sandboxes, remote systems
- **Specialized Providers**: Domain-specific optimizations, caching layers
- **Enterprise Integrations**: Internal AI platforms, compliance wrappers

### What You'll Build

A provider plugin consists of two main components:

1. **Provider Class**: Implements `IAgentProvider` interface for task execution
2. **Plugin Class**: Inherits from `BaseProviderPlugin` for registration and configuration

---

## Quick Start

### 1. Use the Template

Copy the provider plugin template:

```bash
cp examples/provider-plugin-template/custom_provider_plugin.py \
   plugins/my_provider_plugin.py
```

### 2. Implement Your Provider

```python
from gao_dev.core.providers.base import IAgentProvider, AgentContext, AgentResult

class MyProvider(IAgentProvider):
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs

    def execute_task(
        self,
        task: str,
        context: AgentContext,
        timeout: Optional[int] = None,
    ) -> AgentResult:
        # Your execution logic here
        response = your_api.execute(task)

        return AgentResult(
            success=True,
            output=response.content,
            error=None,
            metadata={"tokens": response.tokens}
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=False,
            supports_tools=True,
            max_tokens=4000,
            supported_models=["your-model"]
        )
```

### 3. Create Your Plugin

```python
from gao_dev.plugins.provider_plugin import BaseProviderPlugin

class MyProviderPlugin(BaseProviderPlugin):
    def get_provider_name(self) -> str:
        return "my-provider"

    def get_provider_class(self) -> Type[IAgentProvider]:
        return MyProvider

    def validate_configuration(self, config: Dict) -> bool:
        return "api_key" in config
```

### 4. Test Your Plugin

```bash
# Copy to plugins directory
cp plugins/my_provider_plugin.py ~/.gao-dev/plugins/

# Verify discovery
gao-dev providers list

# Test execution
gao-dev providers test my-provider "Write a hello world function"
```

---

## Provider Plugin Architecture

### Component Interaction

```
┌─────────────────┐
│  GAO-Dev Core   │
└────────┬────────┘
         │
         v
┌─────────────────┐         ┌──────────────────┐
│ ProviderFactory │<────────│ PluginManager    │
└────────┬────────┘         └──────────────────┘
         │                           │
         v                           v
┌─────────────────┐         ┌──────────────────┐
│  IAgentProvider │<────────│ BaseProviderPlugin│
└─────────────────┘         └──────────────────┘
         ^                           ^
         │                           │
    ┌────┴────┐                 ┌───┴────┐
    │  Your   │                 │  Your  │
    │ Provider│                 │ Plugin │
    └─────────┘                 └────────┘
```

### Lifecycle

1. **Discovery**: PluginManager discovers plugins in plugin directories
2. **Validation**: Plugin validated (implements BaseProviderPlugin, provider implements IAgentProvider)
3. **Registration**: Provider class registered with ProviderFactory
4. **Configuration**: User configures provider in YAML or environment
5. **Instantiation**: Factory creates provider instance when needed
6. **Execution**: Provider executes tasks via execute_task method
7. **Cleanup**: Plugin cleanup called on shutdown

---

## Creating a Provider

### Step 1: Implement IAgentProvider

Your provider must implement the `IAgentProvider` interface:

```python
from gao_dev.core.providers.base import (
    IAgentProvider,
    AgentContext,
    AgentResult,
    ProviderCapabilities
)

class MyCustomProvider(IAgentProvider):
    """Your custom provider implementation."""

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        model: str = "default",
        timeout: int = 300,
        **kwargs
    ):
        """Initialize provider with configuration."""
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout
        self.config = kwargs
```

### Step 2: Implement execute_task

This is the core method that executes AI tasks:

```python
def execute_task(
    self,
    task: str,
    context: AgentContext,
    timeout: Optional[int] = None,
) -> AgentResult:
    """Execute a task with your AI backend.

    Args:
        task: Task description/prompt
        context: Execution context (model, tools, working directory)
        timeout: Optional timeout override

    Returns:
        AgentResult with success, output, error, metadata
    """
    try:
        # Use context for task-specific overrides
        model = context.model or self.model
        tools = context.tools or []
        timeout_val = timeout or self.timeout

        # Call your API
        response = your_api.chat_completion(
            prompt=task,
            model=model,
            tools=tools,
            timeout=timeout_val
        )

        # Parse response
        return AgentResult(
            success=True,
            output=response.content,
            error=None,
            metadata={
                "tokens": response.usage.total_tokens,
                "cost": self._calculate_cost(response.usage),
                "model": model,
                "duration": response.duration,
                "provider": "my-provider"
            }
        )

    except YourAPIException as e:
        return AgentResult(
            success=False,
            output="",
            error=str(e),
            metadata={"error_type": type(e).__name__}
        )
```

### Step 3: Implement get_capabilities

Describe what your provider supports:

```python
def get_capabilities(self) -> ProviderCapabilities:
    """Return provider capabilities."""
    return ProviderCapabilities(
        supports_streaming=True,  # Can stream responses?
        supports_tools=True,  # Supports tool calling?
        supports_vision=False,  # Supports image inputs?
        supports_function_calling=True,  # Supports function calling?
        max_tokens=8000,  # Maximum tokens per request
        supported_models=[  # List of model names
            "model-v1",
            "model-v2",
            "model-v3"
        ]
    )
```

### Step 4: Add Helper Methods (Optional)

```python
def _calculate_cost(self, usage: Dict) -> float:
    """Calculate cost based on token usage."""
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    # Your pricing logic
    input_cost = input_tokens * 0.000003  # $3 per 1M tokens
    output_cost = output_tokens * 0.000015  # $15 per 1M tokens

    return input_cost + output_cost

def _format_tools(self, tools: List[str]) -> List[Dict]:
    """Convert GAO-Dev tool names to your API format."""
    tool_mapping = {
        "Read": {"name": "read_file", "type": "file_system"},
        "Write": {"name": "write_file", "type": "file_system"},
        "Edit": {"name": "edit_file", "type": "file_system"},
        # ... more mappings
    }
    return [tool_mapping.get(t, {}) for t in tools if t in tool_mapping]
```

---

## Creating a Plugin

### Step 1: Inherit from BaseProviderPlugin

```python
from gao_dev.plugins.provider_plugin import BaseProviderPlugin

class MyProviderPlugin(BaseProviderPlugin):
    """Plugin for registering MyCustomProvider."""
```

### Step 2: Implement Required Methods

#### get_provider_name

```python
def get_provider_name(self) -> str:
    """Return unique provider name.

    Use lowercase with hyphens: "my-provider", "azure-openai"
    """
    return "my-custom-provider"
```

#### get_provider_class

```python
def get_provider_class(self) -> Type[IAgentProvider]:
    """Return your provider class."""
    return MyCustomProvider
```

### Step 3: Implement Optional Methods

#### validate_configuration

```python
def validate_configuration(self, config: Dict) -> bool:
    """Validate provider configuration.

    Check all required fields are present and valid.
    """
    # Check required fields
    required = ["api_key", "endpoint"]
    if not all(k in config for k in required):
        return False

    # Validate field types
    if not isinstance(config.get("timeout"), (int, float, type(None))):
        return False

    # Validate field values
    endpoint = config.get("endpoint", "")
    if not endpoint.startswith("https://"):
        return False

    return True
```

#### get_default_configuration

```python
def get_default_configuration(self) -> Dict:
    """Return sensible defaults for your provider."""
    return {
        "model": "default-model-v1",
        "timeout": 300,
        "max_tokens": 4000,
        "temperature": 0.7,
        "top_p": 1.0
    }
```

#### get_supported_models

```python
def get_supported_models(self) -> List[str]:
    """List models supported by your provider."""
    return [
        "model-v1-small",
        "model-v1-large",
        "model-v2-ultra"
    ]
```

#### get_required_tools

```python
def get_required_tools(self) -> List[str]:
    """List external CLI tools required."""
    return ["curl", "jq"]  # Empty list if none
```

#### get_setup_instructions

```python
def get_setup_instructions(self) -> Optional[str]:
    """Return markdown setup instructions."""
    return """
# My Custom Provider Setup

## Prerequisites

1. Account at my-service.com
2. API key from dashboard

## Configuration

### Environment Variables

```bash
export MY_PROVIDER_API_KEY="your-api-key"
export MY_PROVIDER_ENDPOINT="https://api.my-service.com"
```

### Configuration File

Add to `gao_dev/config/defaults.yaml`:

```yaml
providers:
  my-custom-provider:
    api_key: "${MY_PROVIDER_API_KEY}"
    endpoint: "${MY_PROVIDER_ENDPOINT}"
    model: "model-v1"
```

## Testing

```bash
gao-dev providers test my-custom-provider "Hello world"
```

## Troubleshooting

**Error: "API key invalid"**
- Verify API key in dashboard
- Check for extra whitespace

**Error: "Endpoint not reachable"**
- Check firewall settings
- Verify endpoint URL format
"""
```

### Step 4: Add Lifecycle Hooks (Optional)

#### initialize

```python
def initialize(self) -> bool:
    """Called when plugin loads.

    Returns:
        True to continue loading, False to abort
    """
    import shutil

    # Check required tools
    for tool in self.get_required_tools():
        if not shutil.which(tool):
            logger.warning(f"Required tool '{tool}' not found")
            return False

    # Validate environment
    if not self._check_connectivity():
        logger.error("Cannot connect to API endpoint")
        return False

    return True
```

#### cleanup

```python
def cleanup(self) -> None:
    """Called when plugin unloads."""
    # Close any open connections
    if hasattr(self, 'session'):
        self.session.close()

    # Save state if needed
    self._save_cache()
```

#### on_provider_registered

```python
def on_provider_registered(self) -> None:
    """Called after successful registration."""
    logger.info(
        "custom_provider_registered",
        provider=self.get_provider_name(),
        models=len(self.get_supported_models())
    )
```

---

## Testing

### Unit Tests

Create `tests/test_my_provider_plugin.py`:

```python
import pytest
from my_provider_plugin import MyProviderPlugin, MyCustomProvider

def test_provider_name():
    plugin = MyProviderPlugin()
    assert plugin.get_provider_name() == "my-custom-provider"

def test_provider_class():
    plugin = MyProviderPlugin()
    assert plugin.get_provider_class() == MyCustomProvider

def test_configuration_validation():
    plugin = MyProviderPlugin()

    # Valid
    assert plugin.validate_configuration({
        "api_key": "test",
        "endpoint": "https://api.example.com"
    })

    # Invalid - missing api_key
    assert not plugin.validate_configuration({
        "endpoint": "https://api.example.com"
    })

    # Invalid - bad endpoint
    assert not plugin.validate_configuration({
        "api_key": "test",
        "endpoint": "http://api.example.com"  # Not HTTPS
    })

def test_default_configuration():
    plugin = MyProviderPlugin()
    defaults = plugin.get_default_configuration()
    assert "model" in defaults
    assert "timeout" in defaults
```

### Integration Tests

```python
def test_provider_execution():
    """Test actual provider execution."""
    provider = MyCustomProvider(
        api_key="test-key",
        endpoint="https://api.example.com"
    )

    context = AgentContext(
        model="model-v1",
        tools=["Read", "Write"],
        working_dir=Path.cwd()
    )

    result = provider.execute_task(
        "Write a hello world function",
        context
    )

    assert result.success
    assert len(result.output) > 0
    assert result.metadata["provider"] == "my-custom-provider"
```

### Manual Testing

```bash
# 1. Copy to plugins directory
cp my_provider_plugin.py ~/.gao-dev/plugins/

# 2. List providers (should appear)
gao-dev providers list

# 3. Validate configuration
gao-dev providers validate my-custom-provider

# 4. Test execution
gao-dev providers test my-custom-provider "Write a function"

# 5. Use in workflow
gao-dev create-prd --name "Test" --provider my-custom-provider
```

---

## Distribution

### Option 1: Plugin Directory

Place plugin in one of these directories:

- `~/.gao-dev/plugins/` (user-specific)
- `./plugins/` (project-specific)
- Custom directory via `GAOGAO_DEV_PLUGIN_PATH` environment variable

### Option 2: Python Package

Create installable package:

```
my-provider-plugin/
├── setup.py
├── README.md
├── my_provider/
│   ├── __init__.py
│   ├── provider.py
│   └── plugin.py
└── tests/
    └── test_plugin.py
```

`setup.py`:
```python
from setuptools import setup, find_packages

setup(
    name="gao-dev-my-provider",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "gao-dev>=0.1.0",
        "your-api-client>=1.0.0"
    ],
    entry_points={
        "gao_dev.plugins": [
            "my-provider = my_provider.plugin:MyProviderPlugin"
        ]
    }
)
```

### Option 3: GitHub Repository

Host plugin on GitHub for easy sharing:

```bash
# Install from GitHub
pip install git+https://github.com/username/gao-dev-my-provider.git
```

---

## Examples

### Example 1: REST API Provider

```python
import requests
from gao_dev.core.providers.base import IAgentProvider

class RestAPIProvider(IAgentProvider):
    """Provider using REST API."""

    def __init__(self, api_key: str, endpoint: str, **kwargs):
        self.api_key = api_key
        self.endpoint = endpoint
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def execute_task(self, task: str, context: AgentContext, timeout: Optional[int] = None) -> AgentResult:
        try:
            response = self.session.post(
                f"{self.endpoint}/execute",
                json={
                    "task": task,
                    "model": context.model,
                    "tools": context.tools
                },
                timeout=timeout or 300
            )
            response.raise_for_status()

            data = response.json()
            return AgentResult(
                success=True,
                output=data["output"],
                error=None,
                metadata=data.get("metadata", {})
            )
        except requests.RequestException as e:
            return AgentResult(
                success=False,
                output="",
                error=str(e),
                metadata={}
            )
```

### Example 2: CLI Wrapper Provider

```python
import subprocess
from gao_dev.core.providers.base import IAgentProvider

class CLIWrapperProvider(IAgentProvider):
    """Provider wrapping external CLI tool."""

    def __init__(self, cli_path: str, **kwargs):
        self.cli_path = cli_path
        self.config = kwargs

    def execute_task(self, task: str, context: AgentContext, timeout: Optional[int] = None) -> AgentResult:
        try:
            cmd = [
                self.cli_path,
                "execute",
                "--task", task,
                "--model", context.model or "default"
            ]

            if context.tools:
                cmd.extend(["--tools", ",".join(context.tools)])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or 300,
                cwd=context.working_dir
            )

            return AgentResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                metadata={"exit_code": result.returncode}
            )
        except subprocess.TimeoutExpired:
            return AgentResult(
                success=False,
                output="",
                error="Execution timeout",
                metadata={}
            )
```

### Example 3: Local Model Provider

```python
from gao_dev.core.providers.base import IAgentProvider

class LocalModelProvider(IAgentProvider):
    """Provider using local AI model."""

    def __init__(self, model_path: str, **kwargs):
        self.model_path = model_path
        self.model = self._load_model()

    def _load_model(self):
        # Load model (e.g., with transformers, llama.cpp, etc.)
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model = AutoModelForCausalLM.from_pretrained(self.model_path)
        tokenizer = AutoTokenizer.from_pretrained(self.model_path)

        return {"model": model, "tokenizer": tokenizer}

    def execute_task(self, task: str, context: AgentContext, timeout: Optional[int] = None) -> AgentResult:
        tokenizer = self.model["tokenizer"]
        model = self.model["model"]

        # Generate response
        inputs = tokenizer(task, return_tensors="pt")
        outputs = model.generate(**inputs, max_length=context.max_tokens or 2000)
        response = tokenizer.decode(outputs[0])

        return AgentResult(
            success=True,
            output=response,
            error=None,
            metadata={"tokens": len(outputs[0])}
        )
```

---

## Best Practices

### 1. Error Handling

Always return AgentResult with proper error information:

```python
try:
    result = your_api.execute(task)
    return AgentResult(success=True, output=result, error=None)
except APIException as e:
    return AgentResult(
        success=False,
        output="",
        error=f"API Error: {e}",
        metadata={"error_type": type(e).__name__}
    )
```

### 2. Logging

Use structlog for structured logging:

```python
import structlog
logger = structlog.get_logger(__name__)

def execute_task(self, task: str, context: AgentContext, timeout: Optional[int] = None):
    logger.info(
        "executing_task",
        provider=self.get_provider_name(),
        model=context.model,
        tools=context.tools
    )

    # ... execution logic

    logger.info(
        "task_completed",
        success=result.success,
        tokens=result.metadata.get("tokens"),
        duration=result.metadata.get("duration")
    )
```

### 3. Configuration

Support environment variables:

```python
import os

def get_default_configuration(self) -> Dict:
    return {
        "api_key": os.getenv("MY_PROVIDER_API_KEY", ""),
        "endpoint": os.getenv("MY_PROVIDER_ENDPOINT", "https://api.default.com"),
        "model": os.getenv("MY_PROVIDER_MODEL", "default")
    }
```

### 4. Validation

Validate early and fail fast:

```python
def validate_configuration(self, config: Dict) -> bool:
    # Check required fields
    required = ["api_key", "endpoint"]
    if not all(k in config for k in required):
        logger.error("missing_required_config", required=required)
        return False

    # Validate types
    if not isinstance(config.get("timeout"), (int, float, type(None))):
        logger.error("invalid_timeout_type", timeout=config.get("timeout"))
        return False

    return True
```

### 5. Documentation

Provide comprehensive setup instructions:

- Prerequisites
- Step-by-step configuration
- Example configurations
- Testing instructions
- Troubleshooting common issues

### 6. Testing

Test all scenarios:

- Valid configuration
- Invalid configuration
- Successful execution
- Failed execution
- Timeout handling
- Error recovery

### 7. Backwards Compatibility

Don't break existing behavior:

- Support old configuration formats
- Provide sensible defaults
- Add deprecation warnings for old patterns

---

## Troubleshooting

### Plugin Not Discovered

**Problem**: `gao-dev providers list` doesn't show your plugin

**Solutions**:
1. Check plugin is in correct directory
2. Verify file name uses underscores not hyphens
3. Ensure class inherits from `BaseProviderPlugin`
4. Check for import errors: `python -c "import my_plugin"`

### Validation Fails

**Problem**: Plugin found but validation fails

**Solutions**:
1. Ensure `get_provider_name()` returns non-empty string
2. Verify `get_provider_class()` returns class implementing `IAgentProvider`
3. Check provider class has all required methods
4. Enable debug logging: `gao-dev --log-level debug providers list`

### Execution Fails

**Problem**: Provider registered but execution fails

**Solutions**:
1. Check configuration is valid
2. Test API connectivity separately
3. Verify credentials are correct
4. Check timeout settings
5. Review error messages in logs
6. Test with simple task first

### Import Errors

**Problem**: `ModuleNotFoundError` when loading plugin

**Solutions**:
1. Ensure all dependencies installed
2. Check Python path includes plugin directory
3. Verify imports use correct module names
4. Install plugin as package: `pip install -e .`

---

## Resources

- [Provider Interface Reference](api/provider-api-reference.md)
- [Azure OpenAI Example](../examples/azure-openai-provider-plugin/)
- [Plugin Template](../examples/provider-plugin-template/)
- [GAO-Dev Plugin System](plugin-development-guide.md)

---

**Need Help?**

- GitHub Issues: https://github.com/vanman/gao-agile-dev/issues
- Discussions: https://github.com/vanman/gao-agile-dev/discussions
- Documentation: https://gao-dev.readthedocs.io
