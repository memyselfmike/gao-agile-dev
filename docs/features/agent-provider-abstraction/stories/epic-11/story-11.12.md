# Story 11.12: Provider Plugin System

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P2 (Medium)
**Estimated Effort**: 8 story points
**Owner**: Amelia (Developer) + Winston (Architect)
**Created**: 2025-11-04
**Dependencies**: Story 11.1 (Provider Interface), Story 11.3 (ProviderFactory)

---

## User Story

**As a** plugin developer
**I want** to create custom provider implementations
**So that** I can integrate GAO-Dev with proprietary or specialized AI systems

---

## Acceptance Criteria

### AC1: Provider Plugin Base Class
- ✅ `BaseProviderPlugin` class created
- ✅ Located in `gao_dev/plugins/provider_plugin.py`
- ✅ Extends `BasePlugin`
- ✅ Abstract methods for provider registration
- ✅ Type-safe implementation

### AC2: Provider Plugin Manager
- ✅ `ProviderPluginManager` class created
- ✅ Discovers provider plugins
- ✅ Loads and initializes plugins
- ✅ Registers providers with factory
- ✅ Handles plugin lifecycle
- ✅ Error handling for plugin failures

### AC3: Plugin Registration API
- ✅ `register_provider()` method in plugin base
- ✅ Returns provider class and metadata
- ✅ Validates provider implements `IAgentProvider`
- ✅ Supports provider configuration
- ✅ Clear registration errors

### AC4: Plugin Discovery
- ✅ Discovers plugins in `~/.gao-dev/plugins/`
- ✅ Discovers plugins in project `./plugins/`
- ✅ Entry point discovery (`gao_dev.providers`)
- ✅ Auto-registration on system startup
- ✅ Manual registration API

### AC5: Provider Plugin Template
- ✅ Template created: `templates/provider-plugin/`
- ✅ Example custom provider implementation
- ✅ README with setup instructions
- ✅ Tests included
- ✅ Configuration examples

### AC6: Plugin Permissions & Sandboxing
- ✅ Plugin permissions system
- ✅ Resource limits (CPU, memory)
- ✅ Network access controls
- ✅ File system access controls
- ✅ Security warnings for untrusted plugins

### AC7: Factory Integration
- ✅ `ProviderFactory` loads plugin providers
- ✅ Plugin providers listed alongside built-ins
- ✅ Plugin providers usable in configuration
- ✅ Plugin metadata accessible

### AC8: Example Plugin Created
- ✅ Example plugin: `examples/plugins/azure-openai-provider/`
- ✅ Implements Azure OpenAI provider
- ✅ Full documentation
- ✅ Tests included
- ✅ Demonstrates best practices

### AC9: CLI Commands
- ✅ `gao-dev plugins list-providers` - List provider plugins
- ✅ `gao-dev plugins validate-provider <name>` - Validate plugin
- ✅ `gao-dev plugins install-provider <path>` - Install plugin
- ✅ `gao-dev plugins uninstall-provider <name>` - Uninstall plugin

### AC10: Testing
- ✅ Unit tests for plugin system
- ✅ Integration tests with example plugin
- ✅ Security tests (sandboxing)
- ✅ All tests pass

### AC11: Documentation
- ✅ Plugin development guide updated
- ✅ Provider plugin section added
- ✅ API reference complete
- ✅ Security best practices
- ✅ Publishing guide

---

## Technical Details

### File Structure
```
gao_dev/plugins/
├── __init__.py                      # MODIFIED: Export provider plugin classes
├── base_plugin.py                   # Base plugin class
├── provider_plugin.py               # NEW: Provider plugin base
├── provider_plugin_manager.py       # NEW: Provider plugin manager
└── loader.py                        # MODIFIED: Load provider plugins

templates/
└── provider-plugin/                 # NEW: Provider plugin template
    ├── README.md
    ├── setup.py
    ├── my_provider/
    │   ├── __init__.py
    │   ├── provider.py
    │   └── plugin.py
    └── tests/
        └── test_provider.py

examples/plugins/
└── azure-openai-provider/           # NEW: Example plugin
    ├── README.md
    ├── setup.py
    ├── azure_openai_provider/
    │   ├── __init__.py
    │   ├── provider.py
    │   └── plugin.py
    └── tests/
        └── test_azure_provider.py

docs/
└── plugin-development-guide.md      # MODIFIED: Add provider plugin section
```

### Implementation Approach

#### Step 1: Create Provider Plugin Base Class

**File**: `gao_dev/plugins/provider_plugin.py`

```python
"""Provider plugin system.

Allows third-party plugins to register custom AI provider implementations.
"""

from abc import abstractmethod
from typing import Type, Dict, Any, Optional, List
import structlog

from gao_dev.plugins.base_plugin import BasePlugin
from gao_dev.core.providers.base import IAgentProvider

logger = structlog.get_logger(__name__)


class ProviderMetadata:
    """Metadata for a provider plugin."""

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        author: str,
        supported_models: List[str],
        requires_api_key: bool = True,
        requires_cli: bool = False,
    ):
        """
        Initialize provider metadata.

        Args:
            name: Provider name (e.g., "azure-openai")
            version: Provider version
            description: Human-readable description
            author: Plugin author
            supported_models: List of supported models
            requires_api_key: Whether API key is required
            requires_cli: Whether CLI is required
        """
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.supported_models = supported_models
        self.requires_api_key = requires_api_key
        self.requires_cli = requires_cli


class BaseProviderPlugin(BasePlugin):
    """
    Base class for provider plugins.

    Extend this class to create custom AI provider implementations.

    Example:
        class MyProviderPlugin(BaseProviderPlugin):
            def get_provider_class(self):
                return MyCustomProvider

            def get_provider_metadata(self):
                return ProviderMetadata(
                    name="my-provider",
                    version="1.0.0",
                    description="My custom AI provider",
                    author="Your Name",
                    supported_models=["model-1", "model-2"],
                )
    """

    @abstractmethod
    def get_provider_class(self) -> Type[IAgentProvider]:
        """
        Return the provider class.

        Returns:
            Provider class that implements IAgentProvider

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        pass

    @abstractmethod
    def get_provider_metadata(self) -> ProviderMetadata:
        """
        Return provider metadata.

        Returns:
            Provider metadata

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        pass

    def get_default_config(self) -> Optional[Dict[str, Any]]:
        """
        Return default configuration for this provider.

        Returns:
            Default configuration dict, or None

        Override this to provide default configuration values.
        """
        return None

    def validate_provider_class(self) -> bool:
        """
        Validate that provider class implements IAgentProvider.

        Returns:
            True if valid, False otherwise
        """
        provider_class = self.get_provider_class()

        # Check if subclass of IAgentProvider
        if not issubclass(provider_class, IAgentProvider):
            logger.error(
                "provider_plugin_invalid",
                plugin=self.name,
                error="Provider class does not implement IAgentProvider",
            )
            return False

        # Check required methods exist
        required_methods = [
            "execute_task",
            "supports_tool",
            "get_supported_models",
            "validate",
        ]

        for method_name in required_methods:
            if not hasattr(provider_class, method_name):
                logger.error(
                    "provider_plugin_missing_method",
                    plugin=self.name,
                    method=method_name,
                )
                return False

        return True


class ProviderPluginError(Exception):
    """Raised when provider plugin operation fails."""
    pass
```

#### Step 2: Create Provider Plugin Manager

**File**: `gao_dev/plugins/provider_plugin_manager.py`

```python
"""Provider plugin manager.

Discovers, loads, and manages provider plugins.
"""

from pathlib import Path
from typing import Dict, List, Type
import importlib.metadata
import structlog

from gao_dev.plugins.provider_plugin import (
    BaseProviderPlugin,
    ProviderMetadata,
    ProviderPluginError,
)
from gao_dev.plugins.discovery import PluginDiscovery
from gao_dev.core.providers.base import IAgentProvider
from gao_dev.core.providers.factory import ProviderFactory

logger = structlog.get_logger(__name__)


class ProviderPluginManager:
    """
    Manages provider plugins.

    Discovers, loads, validates, and registers provider plugins.
    """

    def __init__(
        self,
        factory: ProviderFactory,
        plugin_discovery: PluginDiscovery,
    ):
        """
        Initialize provider plugin manager.

        Args:
            factory: Provider factory to register plugins with
            plugin_discovery: Plugin discovery service
        """
        self.factory = factory
        self.plugin_discovery = plugin_discovery
        self.loaded_plugins: Dict[str, BaseProviderPlugin] = {}

    def discover_and_load_plugins(self) -> int:
        """
        Discover and load all provider plugins.

        Returns:
            Number of plugins loaded

        Raises:
            ProviderPluginError: If plugin loading fails critically
        """
        logger.info("provider_plugin_manager_discovering")

        # Discover all plugins
        plugins = self.plugin_discovery.discover_plugins()

        # Filter to provider plugins only
        provider_plugins = [
            p for p in plugins
            if isinstance(p, BaseProviderPlugin)
        ]

        logger.info(
            "provider_plugins_discovered",
            num_total=len(plugins),
            num_providers=len(provider_plugins),
        )

        # Load each plugin
        loaded_count = 0
        for plugin in provider_plugins:
            try:
                self.load_plugin(plugin)
                loaded_count += 1
            except Exception as e:
                logger.error(
                    "provider_plugin_load_failed",
                    plugin=plugin.name,
                    error=str(e),
                )
                # Continue loading other plugins

        logger.info(
            "provider_plugins_loaded",
            num_loaded=loaded_count,
            num_failed=len(provider_plugins) - loaded_count,
        )

        return loaded_count

    def load_plugin(self, plugin: BaseProviderPlugin) -> None:
        """
        Load and register a provider plugin.

        Args:
            plugin: Provider plugin instance

        Raises:
            ProviderPluginError: If plugin invalid or registration fails
        """
        logger.info("provider_plugin_loading", plugin=plugin.name)

        # Validate plugin
        if not plugin.validate_provider_class():
            raise ProviderPluginError(
                f"Plugin '{plugin.name}' has invalid provider class"
            )

        # Get provider class and metadata
        provider_class = plugin.get_provider_class()
        metadata = plugin.get_provider_metadata()

        # Register with factory
        try:
            self.factory.register_provider(
                metadata.name,
                provider_class,
            )

            logger.info(
                "provider_plugin_registered",
                plugin=plugin.name,
                provider_name=metadata.name,
                supported_models=metadata.supported_models,
            )

        except Exception as e:
            raise ProviderPluginError(
                f"Failed to register provider '{metadata.name}': {e}"
            ) from e

        # Store loaded plugin
        self.loaded_plugins[metadata.name] = plugin

    def list_provider_plugins(self) -> List[ProviderMetadata]:
        """
        List all loaded provider plugins.

        Returns:
            List of provider metadata
        """
        return [
            plugin.get_provider_metadata()
            for plugin in self.loaded_plugins.values()
        ]

    def get_plugin(self, provider_name: str) -> BaseProviderPlugin:
        """
        Get loaded plugin by provider name.

        Args:
            provider_name: Name of provider

        Returns:
            Provider plugin instance

        Raises:
            KeyError: If plugin not found
        """
        if provider_name not in self.loaded_plugins:
            raise KeyError(f"Provider plugin '{provider_name}' not loaded")

        return self.loaded_plugins[provider_name]

    def unload_plugin(self, provider_name: str) -> None:
        """
        Unload a provider plugin.

        Args:
            provider_name: Name of provider

        Raises:
            KeyError: If plugin not found
        """
        if provider_name not in self.loaded_plugins:
            raise KeyError(f"Provider plugin '{provider_name}' not loaded")

        # Remove from loaded plugins
        plugin = self.loaded_plugins.pop(provider_name)

        # TODO: Unregister from factory
        # (ProviderFactory doesn't currently support unregistration)

        logger.info(
            "provider_plugin_unloaded",
            provider_name=provider_name,
        )
```

#### Step 3: Create Provider Plugin Template

**File**: `templates/provider-plugin/README.md`

```markdown
# GAO-Dev Provider Plugin Template

This template helps you create a custom AI provider plugin for GAO-Dev.

## Structure

```
my_provider/
├── __init__.py           # Package initialization
├── provider.py           # Your provider implementation
└── plugin.py             # Plugin registration
```

## Quick Start

1. **Copy this template**:
   ```bash
   cp -r templates/provider-plugin/ my-provider-plugin/
   cd my-provider-plugin/
   ```

2. **Rename `my_provider` directory** to your provider name

3. **Implement your provider** in `provider.py`:
   ```python
   from gao_dev.core.providers.base import IAgentProvider

   class MyProvider(IAgentProvider):
       async def execute_task(self, task, context, model, tools, timeout):
           # Your implementation
           pass
   ```

4. **Update `plugin.py`** with your metadata:
   ```python
   from gao_dev.plugins.provider_plugin import BaseProviderPlugin, ProviderMetadata
   from .provider import MyProvider

   class MyProviderPlugin(BaseProviderPlugin):
       def get_provider_class(self):
           return MyProvider

       def get_provider_metadata(self):
           return ProviderMetadata(
               name="my-provider",
               version="1.0.0",
               description="My custom AI provider",
               author="Your Name",
               supported_models=["model-1", "model-2"],
           )
   ```

5. **Install plugin**:
   ```bash
   gao-dev plugins install-provider ./
   ```

6. **Use your provider**:
   ```yaml
   # In agent configuration
   configuration:
     provider: "my-provider"
     model: "model-1"
   ```

## Testing

Create tests in `tests/test_provider.py`:

```python
import pytest
from my_provider.provider import MyProvider
from gao_dev.core.providers.models import AgentContext

@pytest.mark.asyncio
async def test_execute_task():
    provider = MyProvider()
    context = AgentContext(project_root=Path("/tmp"))

    results = []
    async for result in provider.execute_task(
        task="test", context=context, model="model-1"
    ):
        results.append(result)

    assert len(results) > 0
```

Run tests:
```bash
pytest tests/
```

## Publishing

See `docs/plugin-development-guide.md` for publishing instructions.
```

**File**: `templates/provider-plugin/my_provider/provider.py`

```python
"""Custom provider implementation."""

from typing import AsyncGenerator, List, Optional
from pathlib import Path
import structlog

from gao_dev.core.providers.base import IAgentProvider, ProviderError
from gao_dev.core.providers.models import AgentContext

logger = structlog.get_logger(__name__)


class MyProvider(IAgentProvider):
    """
    Custom AI provider implementation.

    Replace this with your actual provider logic.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize provider.

        Args:
            api_key: API key for your service
            **kwargs: Additional configuration
        """
        self.api_key = api_key
        # Add your initialization here

    @property
    def name(self) -> str:
        """Get provider name."""
        return "my-provider"

    async def execute_task(
        self,
        task: str,
        context: AgentContext,
        model: str,
        tools: Optional[List[str]] = None,
        timeout: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Execute AI task.

        Args:
            task: Task prompt
            context: Execution context
            model: Model name
            tools: Tool names (optional)
            timeout: Timeout in seconds

        Yields:
            Response chunks

        Raises:
            ProviderError: If execution fails
        """
        # TODO: Implement your provider logic
        # This is a placeholder that yields the task back

        logger.info("my_provider_executing", task=task[:100])

        try:
            # Your implementation here
            # Example: Call your AI service API

            yield f"Executing task: {task}"

        except Exception as e:
            raise ProviderError(f"My provider failed: {e}") from e

    def supports_tool(self, tool_name: str) -> bool:
        """Check if tool is supported."""
        # Update with your supported tools
        return False

    def get_supported_models(self) -> List[str]:
        """Get supported model names."""
        # Update with your supported models
        return ["model-1", "model-2"]

    async def validate(self) -> bool:
        """Validate provider configuration."""
        # Add validation logic
        return self.api_key is not None
```

**File**: `templates/provider-plugin/my_provider/plugin.py`

```python
"""Provider plugin registration."""

from gao_dev.plugins.provider_plugin import (
    BaseProviderPlugin,
    ProviderMetadata,
)
from .provider import MyProvider


class MyProviderPlugin(BaseProviderPlugin):
    """Plugin for MyProvider."""

    def get_provider_class(self):
        """Return provider class."""
        return MyProvider

    def get_provider_metadata(self):
        """Return provider metadata."""
        return ProviderMetadata(
            name="my-provider",
            version="1.0.0",
            description="My custom AI provider",
            author="Your Name",
            supported_models=["model-1", "model-2"],
            requires_api_key=True,
            requires_cli=False,
        )

    def get_default_config(self):
        """Return default configuration."""
        return {
            "api_key": None,  # Set via env or config
            "timeout": 3600,
        }
```

#### Step 4: Create Example Plugin (Azure OpenAI)

**File**: `examples/plugins/azure-openai-provider/README.md`

```markdown
# Azure OpenAI Provider Plugin

This plugin enables GAO-Dev to use Azure OpenAI Service.

## Installation

```bash
pip install openai  # Install OpenAI SDK
gao-dev plugins install-provider ./examples/plugins/azure-openai-provider/
```

## Configuration

Set environment variables:
```bash
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="your-deployment-name"
```

Or configure in YAML:
```yaml
configuration:
  provider: "azure-openai"
  provider_config:
    api_key: "your-api-key"
    endpoint: "https://your-resource.openai.azure.com/"
    deployment: "your-deployment-name"
  model: "gpt-4"
```

## Usage

```bash
# Use in command
gao-dev create-prd --name "MyProject" --provider azure-openai

# Or set as default in defaults.yaml
providers:
  default: "azure-openai"
```

## Supported Models

- gpt-4
- gpt-4-turbo
- gpt-35-turbo

(Based on your Azure OpenAI deployment)
```

**File**: `examples/plugins/azure-openai-provider/azure_openai_provider/provider.py`

```python
"""Azure OpenAI provider implementation."""

import os
from typing import AsyncGenerator, List, Optional
import structlog

try:
    from openai import AsyncAzureOpenAI
except ImportError:
    AsyncAzureOpenAI = None  # type: ignore

from gao_dev.core.providers.base import IAgentProvider, ProviderError
from gao_dev.core.providers.models import AgentContext

logger = structlog.get_logger(__name__)


class AzureOpenAIProvider(IAgentProvider):
    """Provider for Azure OpenAI Service."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
    ):
        """Initialize Azure OpenAI provider."""
        if AsyncAzureOpenAI is None:
            raise ProviderError(
                "openai package not installed. "
                "Install with: pip install openai"
            )

        self.api_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.deployment = deployment or os.environ.get("AZURE_OPENAI_DEPLOYMENT")

        if not self.api_key:
            raise ProviderError("AZURE_OPENAI_API_KEY not set")
        if not self.endpoint:
            raise ProviderError("AZURE_OPENAI_ENDPOINT not set")
        if not self.deployment:
            raise ProviderError("AZURE_OPENAI_DEPLOYMENT not set")

        self.client = AsyncAzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.endpoint,
            api_version=api_version,
        )

    @property
    def name(self) -> str:
        return "azure-openai"

    async def execute_task(
        self,
        task: str,
        context: AgentContext,
        model: str,
        tools: Optional[List[str]] = None,
        timeout: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Execute task via Azure OpenAI."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.deployment,  # Use deployment name
                messages=[{"role": "user", "content": task}],
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise ProviderError(f"Azure OpenAI error: {e}") from e

    def supports_tool(self, tool_name: str) -> bool:
        return False

    def get_supported_models(self) -> List[str]:
        return ["gpt-4", "gpt-4-turbo", "gpt-35-turbo"]

    async def validate(self) -> bool:
        """Validate configuration."""
        try:
            # Test with minimal request
            await self.client.chat.completions.create(
                model=self.deployment,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except Exception:
            return False
```

#### Step 5: Add CLI Commands

**File**: `gao_dev/cli/commands.py` (MODIFIED - Add commands section)

```python
@cli.command("list-providers")
def list_provider_plugins():
    """List all provider plugins."""
    from gao_dev.plugins.provider_plugin_manager import ProviderPluginManager
    from gao_dev.core.providers.factory import ProviderFactory
    from gao_dev.plugins.discovery import PluginDiscovery

    factory = ProviderFactory()
    discovery = PluginDiscovery()
    manager = ProviderPluginManager(factory, discovery)

    plugins = manager.list_provider_plugins()

    if not plugins:
        print("No provider plugins loaded.")
        return

    print(f"\nFound {len(plugins)} provider plugin(s):\n")

    for metadata in plugins:
        print(f"  {metadata.name} v{metadata.version}")
        print(f"    {metadata.description}")
        print(f"    Author: {metadata.author}")
        print(f"    Models: {', '.join(metadata.supported_models)}")
        print()


@cli.command("validate-provider")
@click.argument("name")
def validate_provider_plugin(name: str):
    """Validate a provider plugin."""
    # Implementation here
    pass


@cli.command("install-provider")
@click.argument("path")
def install_provider_plugin(path: str):
    """Install a provider plugin."""
    # Implementation here
    pass
```

---

## Testing Strategy

### Unit Tests
- Plugin discovery and loading
- Provider validation
- Registration with factory
- Error handling

### Integration Tests
- End-to-end plugin loading
- Provider usage via plugin
- Configuration loading

### Security Tests
- Malicious plugin detection
- Resource limit enforcement
- Permission violations

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Provider plugin base class created
- [ ] Provider plugin manager working
- [ ] Plugin discovery integrated
- [ ] Provider template created
- [ ] Example plugin working
- [ ] Permissions system implemented
- [ ] Factory integration complete
- [ ] CLI commands working
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Security tests passing
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Changes committed

---

## Dependencies

**Upstream**:
- Story 11.1 (Provider Interface) - MUST be complete
- Story 11.3 (ProviderFactory) - MUST be complete

**Downstream**:
- Enables community provider implementations
- Supports proprietary AI system integrations

---

## Notes

- **Security**: Plugin sandboxing critical for untrusted plugins
- **Permissions**: Clear permission model for resource access
- **Template**: Make it easy to create new providers
- **Example**: Azure OpenAI shows real-world usage
- **Entry Points**: Support Python entry points for discovery
- **Documentation**: Clear guide for third-party developers
- **Testing**: Template includes tests to guide developers
- **Publishing**: Consider PyPI publishing workflow

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
- Plugin Guide: `docs/plugin-development-guide.md`
- Story 11.1: `story-11.1.md` (Provider Interface)
- Story 11.3: `story-11.3.md` (ProviderFactory)
