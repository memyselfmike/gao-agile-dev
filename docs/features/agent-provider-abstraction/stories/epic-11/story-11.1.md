# Story 11.1: Create Provider Interface & Base Structure

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P0 (Critical)
**Estimated Effort**: 8 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-04
**Dependencies**: None

---

## User Story

**As a** GAO-Dev developer
**I want** a well-defined provider interface and base module structure
**So that** all providers (built-in and plugin) implement a consistent contract enabling provider abstraction

---

## Acceptance Criteria

### AC1: Provider Module Structure Created
- ✅ `gao_dev/core/providers/` directory created
- ✅ `__init__.py` exports key classes and exceptions
- ✅ Module structure follows GAO-Dev conventions
- ✅ Imports work correctly from other modules

### AC2: IAgentProvider Interface Defined
- ✅ Abstract base class `IAgentProvider` created in `base.py`
- ✅ All required methods defined with proper signatures:
  - `name` property (str)
  - `version` property (str)
  - `execute_task()` async method (returns AsyncGenerator[str, None])
  - `supports_tool()` method (returns bool)
  - `get_supported_models()` method (returns List[str])
  - `translate_model_name()` method (returns str)
  - `validate_configuration()` async method (returns bool)
  - `get_configuration_schema()` method (returns Dict)
  - `initialize()` async method
  - `cleanup()` async method
- ✅ All methods have comprehensive docstrings with examples
- ✅ Type hints complete and correct
- ✅ Abstract methods decorated with `@abstractmethod`

### AC3: Exception Hierarchy & Error Taxonomy (R2 - Winston's Recommendation)
- ✅ Standard error taxonomy `ProviderErrorType` enum defined in `exceptions.py`:
  - `AUTHENTICATION_ERROR` - API key invalid/missing
  - `AUTHORIZATION_ERROR` - Insufficient permissions
  - `RATE_LIMIT_ERROR` - API rate limit exceeded
  - `QUOTA_EXCEEDED_ERROR` - Monthly/daily quota exceeded
  - `MODEL_NOT_FOUND_ERROR` - Model not available
  - `INVALID_REQUEST_ERROR` - Malformed request
  - `CONTENT_POLICY_ERROR` - Content policy violation
  - `TIMEOUT_ERROR` - Request timed out
  - `NETWORK_ERROR` - Network connectivity issues
  - `PROVIDER_UNAVAILABLE_ERROR` - Service down/unreachable
  - `CLI_NOT_FOUND_ERROR` - CLI executable not found
  - `CONFIGURATION_ERROR` - Provider misconfigured
  - `UNKNOWN_ERROR` - Unclassified error
- ✅ Base exception `ProviderError` with standardized attributes:
  - `error_type`: ProviderErrorType enum value
  - `message`: Human-readable error message
  - `provider_name`: Name of provider that raised error
  - `original_error`: Original exception (if any)
  - `retry_after`: Seconds to wait before retry (for rate limits)
  - `context`: Additional debugging context
- ✅ `ProviderError` has intelligent methods:
  - `is_retryable()` - Check if error is retryable
  - `should_fallback()` - Check if should try different provider
- ✅ Specific exception classes for common errors:
  - `AuthenticationError` (AUTHENTICATION_ERROR)
  - `RateLimitError` (RATE_LIMIT_ERROR)
  - `ModelNotFoundError` (MODEL_NOT_FOUND_ERROR)
  - `ProviderUnavailableError` (PROVIDER_UNAVAILABLE_ERROR)
- ✅ Legacy exception aliases maintained for backward compatibility:
  - `ProviderNotFoundError` → maps to PROVIDER_UNAVAILABLE_ERROR
  - `ProviderExecutionError` → maps to UNKNOWN_ERROR
  - `ProviderTimeoutError` → maps to TIMEOUT_ERROR
  - `ProviderConfigurationError` → maps to CONFIGURATION_ERROR
- ✅ Each exception has comprehensive docstring with examples
- ✅ Error translation guidance documented

### AC4: Provider Models Created
- ✅ `AgentContext` dataclass defined in `models.py` (or extended if exists)
- ✅ Required fields: `project_root` (Path)
- ✅ Optional fields:
  - `metadata` (Dict[str, str])
  - `working_directory` (Optional[Path])
  - `environment_vars` (Dict[str, str])
  - `allow_destructive_operations` (bool)
  - `enable_network` (bool)
- ✅ Post-init validation logic included
- ✅ Type hints complete

### AC5: Type Checking & Documentation
- ✅ MyPy strict mode passes with no errors
- ✅ All public interfaces documented
- ✅ Usage examples in docstrings
- ✅ README created in providers/ directory

### AC6: Unit Tests
- ✅ `tests/core/providers/test_base.py` created
- ✅ `tests/core/providers/test_exceptions.py` created
- ✅ Exception hierarchy tested (inheritance, attributes)
- ✅ Interface structure validated
- ✅ Test coverage >90%

---

## Technical Details

### File Structure
```
gao_dev/core/providers/
├── __init__.py              # Export public interface
├── base.py                  # IAgentProvider interface
├── exceptions.py            # Provider exception hierarchy
├── models.py                # Provider models (AgentContext, etc.)
└── README.md                # Provider module documentation

tests/core/providers/
├── __init__.py
├── test_base.py             # Interface tests
└── test_exceptions.py       # Exception tests
```

### Implementation Approach

#### Step 1: Create Module Structure
```bash
mkdir -p gao_dev/core/providers
mkdir -p tests/core/providers
```

#### Step 2: Implement IAgentProvider Interface

**File**: `gao_dev/core/providers/base.py`

```python
"""Provider interface for agent execution backends."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Optional
from pathlib import Path
from ..models.agent import AgentContext


class IAgentProvider(ABC):
    """
    Abstract interface for agent execution providers.

    All providers (built-in and plugin) must implement this interface
    to be compatible with GAO-Dev's execution system.

    Design Pattern: Strategy Pattern
    - Context: ProcessExecutor
    - Strategy: IAgentProvider
    - Concrete Strategies: ClaudeCodeProvider, OpenCodeProvider, etc.

    Example:
        ```python
        class CustomProvider(IAgentProvider):
            @property
            def name(self) -> str:
                return "custom-provider"

            @property
            def version(self) -> str:
                return "1.0.0"

            async def execute_task(self, task, context, model, tools, timeout):
                # Implementation
                yield "Result"

            # ... implement other methods
        ```
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique provider identifier.

        Returns:
            Provider name (e.g., 'claude-code', 'opencode', 'direct-api')

        Example:
            'claude-code', 'opencode', 'direct-api', 'custom-ollama'
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """
        Provider version for compatibility tracking.

        Returns:
            Semantic version string (e.g., '1.0.0')
        """
        pass

    @abstractmethod
    async def execute_task(
        self,
        task: str,
        context: AgentContext,
        model: str,
        tools: List[str],
        timeout: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Execute an agent task using this provider.

        This is the core method that delegates task execution to the
        underlying provider (CLI subprocess, API call, etc.).

        Args:
            task: Task description/prompt for the AI agent
            context: Execution context (project root, metadata, etc.)
            model: Canonical model name (provider translates to specific ID)
            tools: List of tool names to enable (e.g., ['Read', 'Write', 'Bash'])
            timeout: Optional timeout in seconds (None = use provider default)
            **kwargs: Provider-specific additional arguments

        Yields:
            Progress messages and results from provider execution

        Raises:
            ProviderExecutionError: If execution fails
            ProviderTimeoutError: If execution exceeds timeout
            ProviderConfigurationError: If provider not properly configured

        Example:
            ```python
            async for message in provider.execute_task(
                task="Implement feature X",
                context=AgentContext(project_root=Path("/project")),
                model="sonnet-4.5",
                tools=["Read", "Write", "Edit"],
                timeout=3600
            ):
                print(message)
            ```
        """
        pass

    @abstractmethod
    def supports_tool(self, tool_name: str) -> bool:
        """
        Check if provider supports a specific tool.

        Different providers may support different tool sets. This method
        enables runtime validation and graceful degradation.

        Args:
            tool_name: Tool name (e.g., 'Read', 'Write', 'Bash')

        Returns:
            True if tool is supported, False otherwise

        Example:
            ```python
            if provider.supports_tool("Bash"):
                # Use Bash tool
            else:
                # Fallback to alternative
            ```
        """
        pass

    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """
        Get list of canonical model names supported by this provider.

        Returns canonical names, not provider-specific IDs. This enables
        model discovery and validation.

        Returns:
            List of canonical model names

        Example:
            ['sonnet-4.5', 'sonnet-3.5', 'opus-3', 'gpt-4', 'gpt-4-turbo']
        """
        pass

    @abstractmethod
    def translate_model_name(self, canonical_name: str) -> str:
        """
        Translate canonical model name to provider-specific identifier.

        GAO-Dev uses canonical names (e.g., 'sonnet-4.5') that are
        provider-agnostic. Each provider translates to its specific format.

        Args:
            canonical_name: Canonical model name (e.g., 'sonnet-4.5')

        Returns:
            Provider-specific model identifier

        Examples:
            ClaudeCodeProvider:
                'sonnet-4.5' → 'claude-sonnet-4-5-20250929'

            OpenCodeProvider:
                'sonnet-4.5' → 'anthropic/claude-sonnet-4.5'

            DirectAPIProvider:
                'sonnet-4.5' → 'claude-sonnet-4-5-20250929'

        Raises:
            ModelNotSupportedError: If model not supported by provider
        """
        pass

    @abstractmethod
    async def validate_configuration(self) -> bool:
        """
        Validate that provider is properly configured and ready to use.

        Checks:
        - CLI executable exists (for CLI providers)
        - API keys are set (for API providers)
        - Required dependencies installed
        - Network connectivity (for API providers)

        Returns:
            True if configuration valid, False otherwise

        Side Effects:
            May log warnings for configuration issues

        Example:
            ```python
            if not await provider.validate_configuration():
                logger.error("Provider not configured")
                # Fallback to alternative provider
            ```
        """
        pass

    @abstractmethod
    def get_configuration_schema(self) -> Dict:
        """
        Get JSON Schema for provider-specific configuration.

        Used for:
        - Configuration validation
        - Documentation generation
        - IDE autocomplete

        Returns:
            JSON Schema dict describing configuration options

        Example:
            ```python
            {
                "type": "object",
                "properties": {
                    "cli_path": {"type": "string"},
                    "api_key": {"type": "string"},
                    "timeout": {"type": "integer", "default": 3600}
                },
                "required": ["api_key"]
            }
            ```
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize provider resources (connections, subprocess, etc.).

        Called before first execution. Idempotent - can be called multiple times.

        Raises:
            ProviderInitializationError: If initialization fails
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up provider resources (close connections, kill processes, etc.).

        Called after last execution or on error. Should be safe to call
        even if initialization failed.
        """
        pass
```

#### Step 3: Implement Exception Hierarchy

**File**: `gao_dev/core/providers/exceptions.py`

```python
"""Provider exception hierarchy."""

from typing import Optional


class ProviderError(Exception):
    """Base exception for all provider errors."""
    pass


class ProviderNotFoundError(ProviderError):
    """Raised when requested provider not registered."""
    pass


class ProviderExecutionError(ProviderError):
    """Raised when provider execution fails."""

    def __init__(self, message: str, provider_name: Optional[str] = None):
        super().__init__(message)
        self.provider_name = provider_name


class ProviderTimeoutError(ProviderExecutionError):
    """Raised when provider execution times out."""
    pass


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is invalid."""
    pass


class ProviderInitializationError(ProviderError):
    """Raised when provider initialization fails."""
    pass


class ProviderRegistrationError(ProviderError):
    """Raised when provider registration fails."""
    pass


class DuplicateProviderError(ProviderRegistrationError):
    """Raised when attempting to register duplicate provider."""
    pass


class ModelNotSupportedError(ProviderError):
    """Raised when model not supported by provider."""

    def __init__(self, model: str, provider: str):
        super().__init__(
            f"Model '{model}' not supported by provider '{provider}'"
        )
        self.model = model
        self.provider = provider
```

#### Step 4: Implement Provider Models

**File**: `gao_dev/core/providers/models.py`

```python
"""Provider models and data structures."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class AgentContext:
    """
    Context information for agent task execution.

    Provides environment and metadata needed by providers
    to execute tasks correctly.
    """

    # Required fields
    project_root: Path

    # Optional fields
    metadata: Dict[str, str] = field(default_factory=dict)
    """Additional metadata (user ID, session ID, etc.)"""

    working_directory: Optional[Path] = None
    """Current working directory (defaults to project_root)"""

    environment_vars: Dict[str, str] = field(default_factory=dict)
    """Additional environment variables for subprocess"""

    # Execution hints
    allow_destructive_operations: bool = True
    """Whether to allow file deletion, git reset, etc."""

    enable_network: bool = True
    """Whether to allow network access"""

    def __post_init__(self):
        """Validate and set defaults."""
        if self.working_directory is None:
            self.working_directory = self.project_root

        # Ensure paths are absolute
        self.project_root = self.project_root.resolve()
        self.working_directory = self.working_directory.resolve()
```

#### Step 5: Create Module Exports

**File**: `gao_dev/core/providers/__init__.py`

```python
"""Provider abstraction module for multi-provider agent execution."""

from .base import IAgentProvider
from .exceptions import (
    ProviderError,
    ProviderNotFoundError,
    ProviderExecutionError,
    ProviderTimeoutError,
    ProviderConfigurationError,
    ProviderInitializationError,
    ProviderRegistrationError,
    DuplicateProviderError,
    ModelNotSupportedError,
)
from .models import AgentContext

__all__ = [
    # Interface
    "IAgentProvider",

    # Exceptions
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderExecutionError",
    "ProviderTimeoutError",
    "ProviderConfigurationError",
    "ProviderInitializationError",
    "ProviderRegistrationError",
    "DuplicateProviderError",
    "ModelNotSupportedError",

    # Models
    "AgentContext",
]
```

#### Step 6: Write Unit Tests

**File**: `tests/core/providers/test_exceptions.py`

```python
"""Unit tests for provider exception hierarchy."""

import pytest
from gao_dev.core.providers.exceptions import (
    ProviderError,
    ProviderNotFoundError,
    ProviderExecutionError,
    ModelNotSupportedError,
)


class TestProviderExceptions:
    """Test provider exception hierarchy."""

    def test_provider_error_is_base(self):
        """Test ProviderError is base for all exceptions."""
        assert issubclass(ProviderNotFoundError, ProviderError)
        assert issubclass(ProviderExecutionError, ProviderError)

    def test_provider_execution_error_stores_provider_name(self):
        """Test ProviderExecutionError stores provider name."""
        error = ProviderExecutionError("Failed", provider_name="test-provider")
        assert error.provider_name == "test-provider"

    def test_model_not_supported_error_attributes(self):
        """Test ModelNotSupportedError stores model and provider."""
        error = ModelNotSupportedError("gpt-4", "claude-code")
        assert error.model == "gpt-4"
        assert error.provider == "claude-code"
        assert "gpt-4" in str(error)
        assert "claude-code" in str(error)
```

**File**: `tests/core/providers/test_base.py`

```python
"""Unit tests for IAgentProvider interface."""

import pytest
from abc import ABC
from gao_dev.core.providers.base import IAgentProvider


class TestIAgentProvider:
    """Test IAgentProvider interface structure."""

    def test_is_abstract_base_class(self):
        """Test IAgentProvider is an ABC."""
        assert issubclass(IAgentProvider, ABC)

    def test_cannot_instantiate_directly(self):
        """Test IAgentProvider cannot be instantiated."""
        with pytest.raises(TypeError):
            IAgentProvider()

    def test_has_required_methods(self):
        """Test IAgentProvider defines all required methods."""
        required_methods = [
            'execute_task',
            'supports_tool',
            'get_supported_models',
            'translate_model_name',
            'validate_configuration',
            'get_configuration_schema',
            'initialize',
            'cleanup',
        ]

        for method_name in required_methods:
            assert hasattr(IAgentProvider, method_name)

    def test_has_required_properties(self):
        """Test IAgentProvider defines required properties."""
        assert hasattr(IAgentProvider, 'name')
        assert hasattr(IAgentProvider, 'version')
```

---

## Testing Strategy

### Unit Tests
- Exception hierarchy tests (inheritance, attributes, messages)
- Interface structure validation (methods, properties)
- AgentContext validation tests (path resolution, defaults)

### Type Checking
```bash
mypy gao_dev/core/providers/ --strict
```

### Coverage Target
- >90% coverage for all files
- 100% for exception hierarchy
- Interface structure tests comprehensive

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Code reviewed and approved
- [ ] Unit tests passing (>90% coverage)
- [ ] Type checking passing (mypy strict)
- [ ] Documentation complete with examples
- [ ] No linting errors (ruff)
- [ ] Changes committed with clear message
- [ ] Story marked as complete in sprint-status.yaml

---

## Dependencies

**Upstream**: None (foundational story)

**Downstream**:
- Story 11.2 (ClaudeCodeProvider) - needs IAgentProvider
- Story 11.3 (ProviderFactory) - needs IAgentProvider
- Story 11.7 (OpenCodeProvider) - needs IAgentProvider
- Story 11.10 (DirectAPIProvider) - needs IAgentProvider

---

## Notes

- This is a foundational story - must be rock-solid
- Interface design is critical - hard to change later
- Focus on clarity and usability
- Examples in docstrings are essential
- Type hints must be complete and correct
- Consider future extensibility (but don't over-engineer)

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
- Epic Breakdown: `docs/features/agent-provider-abstraction/epics.md`
