# Story 11.3: Create Provider Factory

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P1 (High)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-04
**Dependencies**: Story 11.1 (Provider Interface), Story 11.2 (ClaudeCodeProvider)

---

## User Story

**As a** GAO-Dev developer
**I want** a centralized provider factory with plugin support
**So that** I can create provider instances consistently and register custom providers

---

## Acceptance Criteria

### AC1: ProviderFactory Class Implemented
- ✅ `ProviderFactory` class created in `factory.py`
- ✅ Registry pattern implemented (Dict[str, Type[IAgentProvider]])
- ✅ Built-in providers auto-registered on initialization
- ✅ Type hints complete
- ✅ Class docstring comprehensive

### AC2: Provider Creation
- ✅ `create_provider(provider_name, config)` method implemented
- ✅ Returns configured provider instance
- ✅ Accepts provider-specific configuration dict
- ✅ Configuration passed to provider constructor
- ✅ Raises `ProviderNotFoundError` if provider not registered
- ✅ Raises `ProviderCreationError` if instantiation fails
- ✅ Logs provider creation

### AC3: Provider Registration
- ✅ `register_provider(provider_name, provider_class)` method implemented
- ✅ Validates provider class implements `IAgentProvider`
- ✅ Raises `ProviderRegistrationError` if invalid class
- ✅ Raises `DuplicateProviderError` if already registered
- ✅ Optional `allow_override` parameter for re-registration
- ✅ Logs registration

### AC4: Provider Discovery
- ✅ `list_providers()` method returns all registered names
- ✅ `provider_exists(provider_name)` checks registration
- ✅ `get_provider_class(provider_name)` returns class without instantiation
- ✅ All methods handle case-insensitive provider names

### AC5: Built-in Provider Registration
- ✅ `_register_builtin_providers()` private method
- ✅ Auto-registers ClaudeCodeProvider on initialization
- ✅ Registration happens in __init__
- ✅ Logs built-in provider registration

### AC6: Error Handling
- ✅ Clear error messages for all failure cases
- ✅ Available providers listed in ProviderNotFoundError
- ✅ Class name included in ProviderRegistrationError
- ✅ Proper exception chaining (raise ... from e)

### AC7: Thread Safety Note
- ✅ Documented as NOT thread-safe
- ✅ Recommendation: one instance per orchestrator
- ✅ No global singleton (testability)

### AC8: Unit Tests
- ✅ Tests in `tests/core/providers/test_factory.py`
- ✅ Test coverage >90%
- ✅ All public methods tested
- ✅ Error cases tested
- ✅ Registration validation tested

---

## Technical Details

### File Structure
```
gao_dev/core/providers/
└── factory.py                  # ProviderFactory

tests/core/providers/
└── test_factory.py             # Unit tests
```

### Implementation Approach

**File**: `gao_dev/core/providers/factory.py`

```python
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
```

### Unit Tests

**File**: `tests/core/providers/test_factory.py`

```python
"""Unit tests for ProviderFactory."""

import pytest
from gao_dev.core.providers.factory import ProviderFactory
from gao_dev.core.providers.base import IAgentProvider
from gao_dev.core.providers.exceptions import (
    ProviderNotFoundError,
    ProviderCreationError,
    ProviderRegistrationError,
    DuplicateProviderError
)


class MockProvider(IAgentProvider):
    """Mock provider for testing."""

    def __init__(self, config_value: str = "default"):
        self.config_value = config_value

    @property
    def name(self) -> str:
        return "mock"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def execute_task(self, task, context, model, tools, timeout=None, **kwargs):
        yield "mock result"

    def supports_tool(self, tool_name: str) -> bool:
        return True

    def get_supported_models(self):
        return ["mock-model"]

    def translate_model_name(self, canonical_name: str) -> str:
        return canonical_name

    async def validate_configuration(self) -> bool:
        return True

    def get_configuration_schema(self):
        return {}

    async def initialize(self) -> None:
        pass

    async def cleanup(self) -> None:
        pass


class InvalidProvider:
    """Invalid provider (doesn't implement IAgentProvider)."""
    pass


class TestProviderFactory:
    """Test ProviderFactory."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = ProviderFactory()

    def test_factory_initialization(self):
        """Test factory initializes with built-in providers."""
        providers = self.factory.list_providers()
        assert "claude-code" in providers

    def test_create_claude_code_provider(self):
        """Test creating ClaudeCodeProvider."""
        provider = self.factory.create_provider("claude-code")
        assert provider.name == "claude-code"
        assert provider.version is not None

    def test_create_provider_with_config(self):
        """Test creating provider with configuration."""
        # Register mock provider
        self.factory.register_provider("mock", MockProvider)

        # Create with config
        provider = self.factory.create_provider(
            "mock",
            config={"config_value": "test"}
        )

        assert provider.config_value == "test"

    def test_create_provider_not_found(self):
        """Test creating non-existent provider raises error."""
        with pytest.raises(ProviderNotFoundError) as exc_info:
            self.factory.create_provider("non-existent")

        assert "non-existent" in str(exc_info.value)
        assert "Available providers" in str(exc_info.value)

    def test_register_provider(self):
        """Test registering custom provider."""
        self.factory.register_provider("mock", MockProvider)
        assert "mock" in self.factory.list_providers()

    def test_register_invalid_provider_raises_error(self):
        """Test registering invalid provider raises error."""
        with pytest.raises(ProviderRegistrationError) as exc_info:
            self.factory.register_provider("invalid", InvalidProvider)

        assert "must implement IAgentProvider" in str(exc_info.value)

    def test_register_duplicate_provider_raises_error(self):
        """Test registering duplicate provider raises error."""
        self.factory.register_provider("mock", MockProvider)

        with pytest.raises(DuplicateProviderError):
            self.factory.register_provider("mock", MockProvider)

    def test_register_duplicate_with_override(self):
        """Test registering duplicate with allow_override."""
        self.factory.register_provider("mock", MockProvider)
        # Should not raise
        self.factory.register_provider("mock", MockProvider, allow_override=True)

    def test_list_providers(self):
        """Test listing providers."""
        providers = self.factory.list_providers()
        assert isinstance(providers, list)
        assert "claude-code" in providers
        assert providers == sorted(providers)  # Should be sorted

    def test_provider_exists(self):
        """Test checking provider existence."""
        assert self.factory.provider_exists("claude-code") is True
        assert self.factory.provider_exists("non-existent") is False

    def test_provider_exists_case_insensitive(self):
        """Test provider_exists is case-insensitive."""
        assert self.factory.provider_exists("CLAUDE-CODE") is True
        assert self.factory.provider_exists("Claude-Code") is True

    def test_get_provider_class(self):
        """Test getting provider class."""
        from gao_dev.core.providers.claude_code import ClaudeCodeProvider

        provider_class = self.factory.get_provider_class("claude-code")
        assert provider_class is ClaudeCodeProvider

    def test_get_provider_class_not_found(self):
        """Test getting non-existent provider class raises error."""
        with pytest.raises(ProviderNotFoundError):
            self.factory.get_provider_class("non-existent")

    def test_factory_repr(self):
        """Test factory string representation."""
        repr_str = repr(self.factory)
        assert "ProviderFactory" in repr_str
        assert "claude-code" in repr_str
```

---

## Testing Strategy

### Unit Tests
- Factory initialization (built-in providers registered)
- Provider creation (with and without config)
- Provider registration (valid and invalid)
- Duplicate registration (with and without override)
- Provider discovery (list, exists, get_class)
- Case-insensitive provider names
- Error handling (not found, invalid class, duplicate)

### Integration Tests
- Create provider and execute task
- Register plugin provider and use it

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Code reviewed and approved
- [ ] Unit tests passing (>90% coverage)
- [ ] Type checking passing (mypy strict)
- [ ] No linting errors (ruff)
- [ ] Documentation complete
- [ ] Changes committed with atomic commit
- [ ] Story marked complete in sprint-status.yaml

---

## Dependencies

**Upstream**:
- Story 11.1 (Provider Interface) - MUST be complete
- Story 11.2 (ClaudeCodeProvider) - MUST be complete

**Downstream**:
- Story 11.4 (Refactor ProcessExecutor) - needs ProviderFactory
- Story 11.5 (Configuration Schema) - needs ProviderFactory

---

## Notes

- Keep factory simple - no caching or singleton pattern (testability)
- One factory instance per orchestrator (no global state)
- Case-insensitive provider names for user convenience
- Clear error messages essential for troubleshooting
- Built-in providers registered automatically
- Plugin providers registered manually

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
- Story 11.1: `story-11.1.md` (Interface)
- Story 11.2: `story-11.2.md` (ClaudeCodeProvider)
