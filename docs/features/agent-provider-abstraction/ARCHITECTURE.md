# Technical Architecture
## Agent Provider Abstraction System

**Version:** 1.0.0
**Date:** 2025-11-04
**Status:** Design
**Author:** Winston (Technical Architect) via GAO-Dev Workflow
**Epic:** Epic 11 - Multi-Provider Agent Abstraction

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Architecture Analysis](#current-architecture-analysis)
3. [Proposed Architecture](#proposed-architecture)
4. [Component Design](#component-design)
5. [Data Flow](#data-flow)
6. [Interface Specifications](#interface-specifications)
7. [Provider Implementations](#provider-implementations)
8. [Configuration Management](#configuration-management)
9. [Error Handling](#error-handling)
10. [Performance Considerations](#performance-considerations)
11. [Security Architecture](#security-architecture)
12. [Testing Strategy](#testing-strategy)
13. [Migration Path](#migration-path)
14. [Appendix](#appendix)

---

## Executive Summary

### Architectural Vision

Transform GAO-Dev's agent execution layer from a tightly-coupled Claude Code implementation to a pluggable, provider-agnostic architecture that supports multiple AI agent backends while maintaining 100% backward compatibility.

### Key Architectural Decisions

**Decision 1: Provider Abstraction via Interface**
- **Pattern**: Strategy Pattern with Factory
- **Rationale**: Enables runtime provider selection without code changes
- **Trade-off**: Slight indirection overhead (<5%) for significant flexibility gain

**Decision 2**: Maintain Existing IAgent Interface
- **Rationale**: Provider abstraction hidden from agents - no cascading changes
- **Trade-off**: Provider capabilities must map to IAgent contract

**Decision 3**: Configuration-Driven Provider Selection
- **Rationale**: Zero code changes for provider switching
- **Trade-off**: More complex configuration schema

**Decision 4**: Backward Compatible Defaults
- **Rationale**: No breaking changes for existing users
- **Trade-off**: Slightly more complex default handling logic

### Architectural Principles

1. **Single Responsibility**: Each provider handles one execution backend
2. **Open/Closed**: Open for extension (new providers), closed for modification
3. **Liskov Substitution**: All providers interchangeable via IAgentProvider
4. **Interface Segregation**: Minimal interface, no provider-specific methods
5. **Dependency Inversion**: High-level code depends on abstractions, not concrete providers

---

## Current Architecture Analysis

### Component Diagram (Current State)

```
┌─────────────────────────────────────────────────────────────┐
│                    GAODevOrchestrator                        │
│                  (High-level coordination)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     ProcessExecutor                          │
│              (Agent task execution service)                  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  execute_agent_task(task, timeout)                 │    │
│  │                                                     │    │
│  │  cmd = ['claude', '--print', '--model', ...]       │ ← TIGHT COUPLING
│  │  process = subprocess.Popen(cmd, ...)              │    │
│  │  stdout, stderr = process.communicate(task)        │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code CLI                          │
│                  (External subprocess)                       │
└─────────────────────────────────────────────────────────────┘
```

### Coupling Analysis

**Single Tight Coupling Point:**
```python
# gao_dev/core/services/process_executor.py (lines 131-164)

cmd = [str(self.cli_path)]
cmd.extend(['--print'])                              # Claude Code specific
cmd.extend(['--dangerously-skip-permissions'])       # Claude Code specific
cmd.extend(['--model', 'claude-sonnet-4-5-20250929']) # Claude Code specific
cmd.extend(['--add-dir', str(self.project_root)])    # Claude Code specific

process = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    errors='replace',
    env=env,
    cwd=str(self.project_root)
)
```

**Assessment**:
- ✅ Only ONE file with tight coupling
- ✅ Clean service boundary (ProcessExecutor is isolated)
- ✅ Well-tested (integration tests exist)
- ✅ Clear interface (async generator pattern)
- ✅ Migration risk: **LOW**

### Architecture Strengths

1. **Clean Service Layer**: ProcessExecutor already isolated
2. **Agent Abstraction**: IAgent interface provider-agnostic
3. **Factory Pattern**: AgentFactory centralizes creation
4. **YAML Configuration**: External config enables provider switching
5. **Async/Await**: Modern async patterns support provider abstraction

**Conclusion**: Current architecture is **excellent foundation** for provider abstraction.

---

## Proposed Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       GAODevOrchestrator                             │
│                    (Provider-agnostic)                               │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       ProcessExecutor                                │
│                    (Provider-agnostic)                               │
│                                                                       │
│  Uses: IAgentProvider (via ProviderFactory)                          │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      IAgentProvider                                  │
│                   (Abstract Interface)                               │
│                                                                       │
│  + execute_task(task, context, model, tools, timeout)               │
│  + supports_tool(tool_name) -> bool                                 │
│  + get_supported_models() -> List[str]                              │
│  + translate_model_name(canonical) -> str                           │
│  + validate_configuration() -> bool                                 │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┬─────────────────┐
        │                   │                   │                 │
        ▼                   ▼                   ▼                 ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ ClaudeCode   │   │  OpenCode    │   │  DirectAPI   │   │   Custom     │
│  Provider    │   │  Provider    │   │  Provider    │   │  Provider    │
│              │   │              │   │              │   │ (Plugin)     │
│ - Subprocess │   │ - Subprocess │   │ - HTTP API   │   │ - User       │
│ - Claude CLI │   │ - OpenCode   │   │ - Anthropic  │   │   Defined    │
│              │   │   CLI        │   │   SDK        │   │              │
│              │   │ - Multi AI   │   │ - OpenAI     │   │              │
│              │   │   Provider   │   │   SDK        │   │              │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

### Component Hierarchy

```
gao_dev/
├── core/
│   ├── providers/                    # NEW: Provider abstraction
│   │   ├── __init__.py
│   │   ├── base.py                   # IAgentProvider interface
│   │   ├── exceptions.py             # Provider exceptions
│   │   ├── factory.py                # ProviderFactory
│   │   ├── claude_code.py            # ClaudeCodeProvider
│   │   ├── opencode.py               # OpenCodeProvider
│   │   ├── direct_api.py             # DirectAPIProvider
│   │   └── models.py                 # Provider models/enums
│   │
│   ├── services/
│   │   └── process_executor.py       # MODIFIED: Use IAgentProvider
│   │
│   ├── models/
│   │   └── agent.py                  # AgentContext, etc.
│   │
│   └── config/
│       └── providers/                 # NEW: Provider configs
│           ├── claude_code.yaml
│           ├── opencode.yaml
│           └── direct_api.yaml
│
├── config/
│   ├── agents/                        # MODIFIED: Add provider field
│   │   └── *.yaml
│   └── defaults.yaml                  # MODIFIED: Provider registry
│
└── plugins/
    ├── agent_plugin.py                # MODIFIED: Support provider plugins
    └── provider_plugin.py             # NEW: Provider plugin interface
```

---

## Component Design

### 1. IAgentProvider Interface

**Module**: `gao_dev/core/providers/base.py`

**Purpose**: Define contract that all provider implementations must fulfill.

**Interface Design**:

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
            async for message in provider.execute_task(
                task="Implement feature X",
                context=AgentContext(project_root=Path("/project")),
                model="sonnet-4.5",
                tools=["Read", "Write", "Edit"],
                timeout=3600
            ):
                print(message)
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
            if provider.supports_tool("Bash"):
                # Use Bash tool
            else:
                # Fallback to alternative
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
            if not await provider.validate_configuration():
                logger.error("Provider not configured")
                # Fallback to alternative provider
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
            {
                "type": "object",
                "properties": {
                    "cli_path": {"type": "string"},
                    "api_key": {"type": "string"},
                    "timeout": {"type": "integer", "default": 3600}
                },
                "required": ["api_key"]
            }
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

**Design Notes:**
- **Async by Default**: All I/O operations are async for performance
- **Generator Pattern**: `execute_task` yields results for streaming
- **Validation Built-in**: `validate_configuration()` prevents runtime failures
- **Tool Compatibility**: `supports_tool()` enables graceful degradation
- **Model Translation**: Canonical names abstract provider differences

---

### 2. ProviderFactory

**Module**: `gao_dev/core/providers/factory.py`

**Purpose**: Centralized provider creation with registration support.

**Class Design**:

```python
"""Provider factory for creating agent execution providers."""

from typing import Dict, Type, Optional, List
from pathlib import Path
import structlog

from .base import IAgentProvider
from .claude_code import ClaudeCodeProvider
from .opencode import OpenCodeProvider
from .direct_api import DirectAPIProvider
from .exceptions import (
    ProviderNotFoundError,
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
            provider = factory.create_provider(
                "opencode",
                config={"ai_provider": "anthropic", "cli_path": "/usr/bin/opencode"}
            )
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
        """
        return sorted(self._registry.keys())

    def provider_exists(self, provider_name: str) -> bool:
        """
        Check if a provider is registered.

        Args:
            provider_name: Provider identifier

        Returns:
            True if registered, False otherwise
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
            "opencode": OpenCodeProvider,
            "direct-api": DirectAPIProvider,
        }

        for name, provider_class in builtin_providers.items():
            self._registry[name] = provider_class

        logger.debug(
            "builtin_providers_registered",
            count=len(builtin_providers),
            providers=list(builtin_providers.keys())
        )
```

**Design Patterns:**
- **Factory Pattern**: Encapsulates provider creation logic
- **Registry Pattern**: Manages provider types
- **Plugin Support**: External registration for extensibility

---

### 3. ClaudeCodeProvider

**Module**: `gao_dev/core/providers/claude_code.py`

**Purpose**: Provider implementation for Claude Code CLI (current behavior).

**Implementation Highlights**:

```python
"""Claude Code CLI provider implementation."""

from pathlib import Path
from typing import AsyncGenerator, List, Dict, Optional
import subprocess
import os
import structlog

from .base import IAgentProvider
from ..models.agent import AgentContext
from ..exceptions import ProviderExecutionError, ProviderTimeoutError
from ..cli_detector import detect_claude_cli

logger = structlog.get_logger()


class ClaudeCodeProvider(IAgentProvider):
    """
    Provider for Claude Code CLI execution.

    This provider maintains the exact behavior of the original
    ProcessExecutor implementation, extracted into a provider
    for multi-provider support.

    Execution Model: Subprocess (Claude CLI)
    Backend: Anthropic Claude
    """

    # Tool mapping: GAO-Dev tool name → Claude Code tool name
    TOOL_MAPPING = {
        "Read": "read",
        "Write": "write",
        "Edit": "edit",
        "Bash": "bash",
        "Grep": "grep",
        "Glob": "glob",
        "Task": "task",
        "WebFetch": "webfetch",
        "WebSearch": "websearch",
        # ... etc
    }

    # Model translation: Canonical → Claude-specific
    MODEL_MAPPING = {
        "sonnet-4.5": "claude-sonnet-4-5-20250929",
        "sonnet-3.5": "claude-sonnet-3-5-20241022",
        "opus-3": "claude-opus-3-20250219",
        # Passthrough for full model IDs
        "claude-sonnet-4-5-20250929": "claude-sonnet-4-5-20250929",
        "claude-sonnet-3-5-20241022": "claude-sonnet-3-5-20241022",
    }

    DEFAULT_TIMEOUT = 3600  # 1 hour

    def __init__(
        self,
        cli_path: Optional[Path] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize Claude Code provider.

        Args:
            cli_path: Path to Claude CLI executable (auto-detected if None)
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env if None)
        """
        self.cli_path = cli_path or detect_claude_cli()
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._initialized = False

        logger.info(
            "claude_code_provider_initialized",
            has_cli_path=self.cli_path is not None,
            has_api_key=bool(self.api_key)
        )

    @property
    def name(self) -> str:
        return "claude-code"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def execute_task(
        self,
        task: str,
        context: AgentContext,
        model: str,
        tools: List[str],
        timeout: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Execute task via Claude Code CLI."""

        if not self.cli_path:
            raise ProviderExecutionError(
                "Claude CLI not found. Install Claude Code or set cli_path."
            )

        # Translate model name
        model_id = self.translate_model_name(model)

        # Build command (exact same flags as original)
        cmd = [str(self.cli_path)]
        cmd.extend(['--print'])
        cmd.extend(['--dangerously-skip-permissions'])
        cmd.extend(['--model', model_id])
        cmd.extend(['--add-dir', str(context.project_root)])

        # Set environment
        env = os.environ.copy()
        if self.api_key:
            env['ANTHROPIC_API_KEY'] = self.api_key

        # Log execution
        logger.info(
            "executing_claude_cli",
            model=model_id,
            tools=tools,
            timeout=timeout or self.DEFAULT_TIMEOUT
        )

        try:
            # Execute subprocess
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',  # Windows compatibility
                env=env,
                cwd=str(context.project_root)
            )

            # Communicate with timeout
            stdout, stderr = process.communicate(
                input=task,
                timeout=timeout or self.DEFAULT_TIMEOUT
            )

            # Log completion
            logger.info(
                "claude_cli_completed",
                return_code=process.returncode,
                stdout_length=len(stdout) if stdout else 0,
                stderr_length=len(stderr) if stderr else 0
            )

            # Yield output
            if stdout:
                yield stdout

            # Check exit code
            if process.returncode != 0:
                error_msg = f"Claude CLI failed with exit code {process.returncode}"
                if stderr:
                    error_msg += f": {stderr[:500]}"

                logger.error("claude_cli_failed", error=error_msg)
                raise ProviderExecutionError(error_msg)

        except subprocess.TimeoutExpired:
            process.kill()
            logger.error(
                "claude_cli_timeout",
                timeout=timeout or self.DEFAULT_TIMEOUT
            )
            raise ProviderTimeoutError(
                f"Execution timed out after {timeout or self.DEFAULT_TIMEOUT} seconds"
            )

    def supports_tool(self, tool_name: str) -> bool:
        """Check if Claude Code supports this tool."""
        return tool_name in self.TOOL_MAPPING

    def get_supported_models(self) -> List[str]:
        """Get supported Claude models."""
        return list(self.MODEL_MAPPING.keys())

    def translate_model_name(self, canonical_name: str) -> str:
        """Translate canonical name to Claude model ID."""
        # Try mapping, fallback to passthrough
        return self.MODEL_MAPPING.get(canonical_name, canonical_name)

    async def validate_configuration(self) -> bool:
        """Validate Claude Code configuration."""
        if not self.cli_path or not self.cli_path.exists():
            logger.warning("claude_cli_not_found", cli_path=str(self.cli_path))
            return False

        if not self.api_key:
            logger.warning("anthropic_api_key_not_set")
            return False

        return True

    def get_configuration_schema(self) -> Dict:
        """Get configuration schema for Claude Code."""
        return {
            "type": "object",
            "properties": {
                "cli_path": {
                    "type": "string",
                    "description": "Path to Claude CLI executable"
                },
                "api_key": {
                    "type": "string",
                    "description": "Anthropic API key"
                }
            },
            "required": []  # Both optional (auto-detected)
        }

    async def initialize(self) -> None:
        """Initialize provider (no-op for CLI)."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider (no-op for CLI)."""
        self._initialized = False
```

**Key Features:**
- **Exact Behavior**: Maintains 100% compatibility with original ProcessExecutor
- **Backward Compatible**: Supports legacy constructor signatures
- **Robust Error Handling**: Same timeout, error, and logging behavior
- **Windows Compatible**: Encoding and error handling for Windows

---

### 4. ProcessExecutor Refactoring

**Module**: `gao_dev/core/services/process_executor.py`

**Changes**: Update to use IAgentProvider while maintaining API compatibility.

**Before** (Current):
```python
class ProcessExecutor:
    def __init__(self, project_root: Path, cli_path: Optional[Path], api_key: Optional[str]):
        self.project_root = project_root
        self.cli_path = cli_path
        self.api_key = api_key

    async def execute_agent_task(self, task: str, timeout: Optional[int]):
        # Hardcoded Claude CLI execution
        cmd = [str(self.cli_path), '--print', ...]
        process = subprocess.Popen(cmd, ...)
```

**After** (Provider-based):
```python
class ProcessExecutor:
    """
    Executes agent tasks via configurable provider.

    Refactored to use provider abstraction while maintaining
    100% backward compatibility with existing code.
    """

    DEFAULT_TIMEOUT = 3600

    def __init__(
        self,
        project_root: Path,
        provider: Optional[IAgentProvider] = None,
        provider_name: str = "claude-code",
        provider_config: Optional[Dict] = None,
        # Legacy parameters (backward compatibility)
        cli_path: Optional[Path] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize executor with provider.

        Args:
            project_root: Project root directory
            provider: Pre-configured provider instance (takes precedence)
            provider_name: Provider name if creating new instance
            provider_config: Provider-specific configuration
            cli_path: DEPRECATED - Use provider_config instead
            api_key: DEPRECATED - Use provider_config instead

        Example (New API):
            executor = ProcessExecutor(
                project_root=Path("/project"),
                provider_name="opencode",
                provider_config={"ai_provider": "anthropic"}
            )

        Example (Legacy API - still works):
            executor = ProcessExecutor(
                project_root=Path("/project"),
                cli_path=Path("/usr/bin/claude"),
                api_key="sk-ant-..."
            )
        """
        self.project_root = project_root

        # Handle legacy constructor (backward compatibility)
        if provider is None and (cli_path is not None or api_key is not None):
            # Legacy mode: create ClaudeCodeProvider with old params
            logger.info(
                "process_executor_legacy_mode",
                message="Using legacy constructor. Consider migrating to provider-based API."
            )

            factory = ProviderFactory()
            self.provider = factory.create_provider(
                "claude-code",
                config={"cli_path": cli_path, "api_key": api_key}
            )

        # Use provided provider instance
        elif provider is not None:
            self.provider = provider

        # Create provider from factory
        else:
            factory = ProviderFactory()
            self.provider = factory.create_provider(
                provider_name,
                config=provider_config
            )

        logger.info(
            "process_executor_initialized",
            project_root=str(project_root),
            provider=self.provider.name,
            provider_version=self.provider.version
        )

    async def execute_agent_task(
        self,
        task: str,
        model: str = "sonnet-4.5",
        tools: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute agent task via configured provider.

        Args:
            task: Task description/prompt
            model: Canonical model name (provider translates)
            tools: List of tool names to enable
            timeout: Optional timeout in seconds

        Yields:
            Progress messages and results

        Raises:
            ProviderExecutionError: If execution fails
            ProviderTimeoutError: If execution times out
        """
        # Validate provider configuration
        is_valid = await self.provider.validate_configuration()
        if not is_valid:
            logger.warning(
                "provider_not_configured",
                provider=self.provider.name
            )
            raise ValueError(
                f"Provider '{self.provider.name}' not properly configured. "
                f"Check API keys and CLI installation."
            )

        # Create execution context
        context = AgentContext(project_root=self.project_root)

        # Delegate to provider
        logger.info(
            "executing_task_via_provider",
            provider=self.provider.name,
            model=model,
            tools=tools,
            timeout=timeout or self.DEFAULT_TIMEOUT
        )

        async for message in self.provider.execute_task(
            task=task,
            context=context,
            model=model,
            tools=tools or [],
            timeout=timeout or self.DEFAULT_TIMEOUT
        ):
            yield message
```

**Backward Compatibility Strategy:**
1. Legacy constructor parameters still work (`cli_path`, `api_key`)
2. Automatically creates ClaudeCodeProvider when legacy params used
3. New API coexists with old API
4. Deprecation warnings guide users to migrate
5. All existing tests pass without modification

---

## Data Flow

### Request Flow Diagram

```
┌──────────────┐
│ User Request │
│ (CLI/API)    │
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│ GAODevOrchestrator  │
│ - Receives request  │
│ - Selects agent     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────────┐
│ ProcessExecutor         │
│ - Has provider instance │
│ - Builds context        │
└──────┬──────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ IAgentProvider.execute_task()    │
│ - Provider-specific logic        │
│ - CLI invocation OR API call     │
└──────┬───────────────────────────┘
       │
       ├─[ClaudeCodeProvider]────────┐
       │                              ▼
       │                    ┌──────────────────┐
       │                    │ Claude CLI       │
       │                    │ (subprocess)     │
       │                    └──────────────────┘
       │
       ├─[OpenCodeProvider]──────────┐
       │                              ▼
       │                    ┌──────────────────┐
       │                    │ OpenCode CLI     │
       │                    │ (subprocess)     │
       │                    └──────────────────┘
       │
       └─[DirectAPIProvider]─────────┐
                                      ▼
                            ┌───────────────────┐
                            │ Anthropic/OpenAI  │
                            │ API (HTTP)        │
                            └───────────────────┘
```

### Configuration Flow

```
┌──────────────────────┐
│ System Startup       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Load defaults.yaml           │
│ - Provider registry          │
│ - Default provider           │
│ - Model mappings             │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Load agent YAML configs      │
│ - gao_dev/config/agents/*.yaml│
│ - Read "provider" field      │
│ - Read "provider_config"     │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ AgentFactory.create_agent()  │
│ - Loads agent config         │
│ - Determines provider        │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ ProviderFactory              │
│ - Creates provider instance  │
│ - Applies configuration      │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ ProcessExecutor              │
│ - Receives provider instance │
│ - Ready for task execution   │
└──────────────────────────────┘
```

---

## Interface Specifications

### AgentContext Model

```python
"""Agent execution context."""

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

### Provider Exceptions

```python
"""Provider exception hierarchy."""


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

---

## Configuration Management

### Provider Registry Configuration

**File**: `gao_dev/config/defaults.yaml`

```yaml
# Provider configuration and registry

providers:
  # Default provider for all agents (can be overridden per-agent)
  default: "claude-code"

  # Auto-detection settings
  auto_detect: true
  auto_fallback: true

  # Fallback chain if primary provider fails
  fallback_chain:
    - "claude-code"
    - "opencode"
    - "direct-api"

  # Provider-specific configuration
  claude-code:
    cli_path: null  # Auto-detect if null
    api_key_env: "ANTHROPIC_API_KEY"
    default_model: "sonnet-4.5"
    timeout: 3600

  opencode:
    cli_path: null  # Auto-detect if null
    ai_provider: "anthropic"  # anthropic, openai, google
    api_key_env: "ANTHROPIC_API_KEY"
    default_model: "sonnet-4.5"
    timeout: 3600

  direct-api:
    provider: "anthropic"  # anthropic, openai, google
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: null  # Optional override
    default_model: "sonnet-4.5"
    timeout: 3600
    max_retries: 3
    retry_delay: 1.0

# Model name registry (canonical → provider-specific)
models:
  # Define canonical model names and their provider translations
  registry:
    - canonical: "sonnet-4.5"
      description: "Claude Sonnet 4.5 (Latest)"
      providers:
        claude-code: "claude-sonnet-4-5-20250929"
        opencode: "anthropic/claude-sonnet-4.5"
        direct-api: "claude-sonnet-4-5-20250929"

    - canonical: "sonnet-3.5"
      description: "Claude Sonnet 3.5"
      providers:
        claude-code: "claude-sonnet-3-5-20241022"
        opencode: "anthropic/claude-sonnet-3.5"
        direct-api: "claude-sonnet-3-5-20241022"

    - canonical: "opus-3"
      description: "Claude Opus 3 (Most Capable)"
      providers:
        claude-code: "claude-opus-3-20250219"
        opencode: "anthropic/claude-opus-3"
        direct-api: "claude-opus-3-20250219"

    - canonical: "gpt-4"
      description: "OpenAI GPT-4"
      providers:
        opencode: "openai/gpt-4"
        direct-api: "gpt-4-0125-preview"

    - canonical: "gpt-4-turbo"
      description: "OpenAI GPT-4 Turbo"
      providers:
        opencode: "openai/gpt-4-turbo-preview"
        direct-api: "gpt-4-turbo-preview"

    - canonical: "gemini-pro"
      description: "Google Gemini Pro"
      providers:
        opencode: "google/gemini-pro"
        direct-api: "models/gemini-pro"
```

### Agent Configuration with Provider

**File**: `gao_dev/config/agents/amelia.yaml`

```yaml
agent:
  metadata:
    name: Amelia
    role: Software Developer
    version: 1.0.0

  persona:
    background: |
      You are Amelia, a skilled software developer specializing in
      implementing features, writing clean code, and ensuring quality.

  tools:
    - Read
    - Write
    - Edit
    - MultiEdit
    - Bash
    - Grep
    - Glob

  configuration:
    # NEW: Provider selection (optional, defaults to system default)
    provider: "claude-code"  # or "opencode", "direct-api", custom

    # NEW: Provider-specific config (optional)
    provider_config:
      # For OpenCode
      ai_provider: "anthropic"  # or "openai", "google"

      # For DirectAPI
      max_retries: 3
      retry_delay: 2.0

    # Canonical model name (provider translates to specific ID)
    model: "sonnet-4.5"

    # Standard config (unchanged)
    max_tokens: 8000
    temperature: 0.7
```

**Backward Compatibility**:
- If `provider` field omitted, uses system default ("claude-code")
- If `provider_config` omitted, uses provider defaults
- Old configs work without modification

---

## Error Handling

### Error Handling Strategy

**Principle**: Fail fast, fail clearly, with actionable error messages.

### Standard Error Taxonomy (R2 - Winston's Recommendation)

**Purpose**: Standardize error handling across all providers to enable intelligent fallback and consistent user experience.

**Error Type Hierarchy**:

```python
"""Standard error taxonomy for provider abstraction."""

from enum import Enum
from typing import Optional, Dict, Any


class ProviderErrorType(Enum):
    """
    Standardized error types for provider operations.

    This taxonomy enables:
    - Intelligent error handling and fallback strategies
    - Consistent error messages across providers
    - Error analytics and monitoring
    - Provider-specific error translation
    """

    # Authentication & Authorization
    AUTHENTICATION_ERROR = "authentication_error"
    """API key invalid, expired, or missing."""

    AUTHORIZATION_ERROR = "authorization_error"
    """Insufficient permissions for requested operation."""

    # Rate Limiting & Quotas
    RATE_LIMIT_ERROR = "rate_limit_error"
    """API rate limit exceeded, retry after delay."""

    QUOTA_EXCEEDED_ERROR = "quota_exceeded_error"
    """Monthly/daily quota exceeded, cannot retry."""

    # Model & Request Errors
    MODEL_NOT_FOUND_ERROR = "model_not_found_error"
    """Requested model not available on this provider."""

    INVALID_REQUEST_ERROR = "invalid_request_error"
    """Malformed request (e.g., invalid parameters)."""

    CONTENT_POLICY_ERROR = "content_policy_error"
    """Request violates provider's content policy."""

    # Network & Infrastructure
    TIMEOUT_ERROR = "timeout_error"
    """Request timed out (client-side or server-side)."""

    NETWORK_ERROR = "network_error"
    """Network connectivity issues."""

    # Provider Availability
    PROVIDER_UNAVAILABLE_ERROR = "provider_unavailable_error"
    """Provider service is down or unreachable."""

    CLI_NOT_FOUND_ERROR = "cli_not_found_error"
    """CLI executable not found (for CLI-based providers)."""

    # Configuration
    CONFIGURATION_ERROR = "configuration_error"
    """Provider misconfigured (e.g., invalid base URL)."""

    # Unknown
    UNKNOWN_ERROR = "unknown_error"
    """Unclassified error (should be rare)."""


class ProviderError(Exception):
    """
    Base exception for all provider errors.

    Attributes:
        error_type: Standardized error type from taxonomy
        message: Human-readable error message
        provider_name: Name of provider that raised error
        original_error: Original exception from provider (if any)
        retry_after: Seconds to wait before retry (for rate limits)
        context: Additional context for debugging
    """

    def __init__(
        self,
        error_type: ProviderErrorType,
        message: str,
        provider_name: str,
        original_error: Optional[Exception] = None,
        retry_after: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.provider_name = provider_name
        self.original_error = original_error
        self.retry_after = retry_after
        self.context = context or {}

    def is_retryable(self) -> bool:
        """
        Check if error is retryable.

        Returns:
            True if operation should be retried
        """
        retryable_types = {
            ProviderErrorType.RATE_LIMIT_ERROR,
            ProviderErrorType.TIMEOUT_ERROR,
            ProviderErrorType.NETWORK_ERROR,
            ProviderErrorType.PROVIDER_UNAVAILABLE_ERROR,
        }
        return self.error_type in retryable_types

    def should_fallback(self) -> bool:
        """
        Check if error should trigger provider fallback.

        Returns:
            True if should try different provider
        """
        fallback_types = {
            ProviderErrorType.PROVIDER_UNAVAILABLE_ERROR,
            ProviderErrorType.CLI_NOT_FOUND_ERROR,
            ProviderErrorType.AUTHENTICATION_ERROR,
            ProviderErrorType.MODEL_NOT_FOUND_ERROR,
            ProviderErrorType.QUOTA_EXCEEDED_ERROR,
        }
        return self.error_type in fallback_types


# Specific exception classes for common errors

class AuthenticationError(ProviderError):
    """Authentication failed (invalid API key)."""
    def __init__(self, provider_name: str, message: str, **kwargs):
        super().__init__(
            ProviderErrorType.AUTHENTICATION_ERROR,
            message,
            provider_name,
            **kwargs
        )


class RateLimitError(ProviderError):
    """Rate limit exceeded."""
    def __init__(self, provider_name: str, retry_after: int, message: str, **kwargs):
        super().__init__(
            ProviderErrorType.RATE_LIMIT_ERROR,
            message,
            provider_name,
            retry_after=retry_after,
            **kwargs
        )


class ModelNotFoundError(ProviderError):
    """Requested model not available."""
    def __init__(self, provider_name: str, model_name: str, **kwargs):
        super().__init__(
            ProviderErrorType.MODEL_NOT_FOUND_ERROR,
            f"Model '{model_name}' not found on provider '{provider_name}'",
            provider_name,
            **kwargs
        )


class ProviderUnavailableError(ProviderError):
    """Provider service unavailable."""
    def __init__(self, provider_name: str, message: str, **kwargs):
        super().__init__(
            ProviderErrorType.PROVIDER_UNAVAILABLE_ERROR,
            message,
            provider_name,
            **kwargs
        )
```

**Provider-Specific Error Translation**:

Each provider must translate its native errors to standard taxonomy:

```python
class ClaudeCodeProvider(IAgentProvider):
    """Claude Code CLI provider with error translation."""

    def _translate_error(self, error: Exception) -> ProviderError:
        """
        Translate provider-specific errors to standard taxonomy.

        Args:
            error: Original error from Claude Code CLI

        Returns:
            Standardized ProviderError
        """
        error_str = str(error).lower()

        # Authentication errors
        if "invalid api key" in error_str or "authentication failed" in error_str:
            return AuthenticationError(
                provider_name=self.name,
                message="Invalid Anthropic API key",
                original_error=error,
                context={"env_var": "ANTHROPIC_API_KEY"}
            )

        # Rate limit errors
        if "rate limit" in error_str or "429" in error_str:
            # Extract retry_after from error if available
            return RateLimitError(
                provider_name=self.name,
                retry_after=60,  # Default 60 seconds
                message="Anthropic API rate limit exceeded",
                original_error=error
            )

        # CLI not found
        if "command not found" in error_str or "no such file" in error_str:
            return ProviderError(
                error_type=ProviderErrorType.CLI_NOT_FOUND_ERROR,
                message="Claude Code CLI not found. Install from: https://docs.anthropic.com/claude/docs/claude-code",
                provider_name=self.name,
                original_error=error
            )

        # Default: unknown error
        return ProviderError(
            error_type=ProviderErrorType.UNKNOWN_ERROR,
            message=str(error),
            provider_name=self.name,
            original_error=error
        )
```

**Intelligent Fallback Based on Error Type**:

```python
async def execute_with_fallback(
    task: str,
    providers: List[IAgentProvider],
    **kwargs
) -> AsyncGenerator[str, None]:
    """
    Execute task with intelligent fallback based on error types.

    Args:
        task: Task to execute
        providers: List of providers (in fallback order)
        **kwargs: Additional arguments

    Yields:
        Task results

    Raises:
        ProviderError: If all providers fail
    """
    last_error = None

    for provider in providers:
        try:
            async for result in provider.execute_task(task, **kwargs):
                yield result
            return  # Success

        except ProviderError as e:
            logger.warning(
                "provider_failed_checking_fallback",
                provider=provider.name,
                error_type=e.error_type.value,
                should_fallback=e.should_fallback()
            )

            last_error = e

            # Check if should fallback
            if not e.should_fallback():
                # Error not suitable for fallback (e.g., invalid request)
                raise

            # Try next provider in fallback chain
            logger.info("attempting_fallback_provider", next_provider=provider.name)
            continue

    # All providers failed
    raise ProviderError(
        error_type=ProviderErrorType.PROVIDER_UNAVAILABLE_ERROR,
        message=f"All providers failed. Last error: {last_error.message}",
        provider_name="fallback-chain",
        original_error=last_error
    )
```

### Error Scenarios & Handling

#### 1. Provider Not Found

```python
try:
    provider = factory.create_provider("non-existent-provider")
except ProviderNotFoundError as e:
    logger.error("provider_not_found", error=str(e))
    # Fallback to default provider
    provider = factory.create_provider("claude-code")
```

**User Message**:
```
Error: Provider 'non-existent-provider' not found.
Available providers: claude-code, opencode, direct-api

Falling back to default provider: claude-code
```

#### 2. Provider Configuration Invalid

```python
async def validate_or_fail():
    if not await provider.validate_configuration():
        raise ProviderConfigurationError(
            f"Provider '{provider.name}' not properly configured.\n"
            f"Please check:\n"
            f"  - API key is set ({provider.get_api_key_env_var()})\n"
            f"  - CLI is installed (if using CLI provider)\n"
            f"  - Configuration schema is valid"
        )
```

**User Message**:
```
Error: Provider 'claude-code' not properly configured.
Please check:
  - API key is set (ANTHROPIC_API_KEY)
  - CLI is installed (if using CLI provider)
  - Configuration schema is valid

Run 'gao-dev providers validate' for detailed diagnostics.
```

#### 3. Provider Execution Failure

```python
try:
    async for result in provider.execute_task(...):
        yield result
except ProviderExecutionError as e:
    logger.error(
        "provider_execution_failed",
        provider=provider.name,
        error=str(e)
    )

    # Attempt fallback provider if configured
    if fallback_provider:
        logger.info("attempting_fallback_provider", provider=fallback_provider.name)
        async for result in fallback_provider.execute_task(...):
            yield result
    else:
        raise
```

**User Message**:
```
Error: Provider 'opencode' execution failed: OpenCode CLI returned exit code 1

Attempting fallback provider: claude-code
Success: Task completed using fallback provider.
```

#### 4. Provider Timeout

```python
try:
    async for result in provider.execute_task(..., timeout=3600):
        yield result
except ProviderTimeoutError as e:
    logger.error("provider_timeout", provider=provider.name, timeout=3600)
    raise TimeoutError(
        f"Task execution timed out after 3600 seconds.\n"
        f"Provider: {provider.name}\n"
        f"Consider:\n"
        f"  - Increasing timeout value\n"
        f"  - Breaking task into smaller steps\n"
        f"  - Using faster provider (direct-api)"
    )
```

#### 5. Model Not Supported

```python
try:
    model_id = provider.translate_model_name("gpt-4")
except ModelNotSupportedError as e:
    logger.error("model_not_supported", model="gpt-4", provider=provider.name)

    # Show supported models
    supported = provider.get_supported_models()
    raise ValueError(
        f"Model 'gpt-4' not supported by provider '{provider.name}'.\n"
        f"Supported models: {', '.join(supported)}\n"
        f"Consider using a different provider (e.g., opencode with OpenAI)"
    )
```

### Retry Logic

**Built into DirectAPIProvider**:

```python
async def execute_task_with_retry(
    self,
    task: str,
    context: AgentContext,
    **kwargs
) -> AsyncGenerator[str, None]:
    """Execute with exponential backoff retry."""

    max_retries = self.config.get("max_retries", 3)
    retry_delay = self.config.get("retry_delay", 1.0)

    for attempt in range(max_retries):
        try:
            async for result in self._execute_task_once(task, context, **kwargs):
                yield result
            return  # Success

        except ProviderExecutionError as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(
                    "provider_execution_failed_retrying",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    wait_time=wait_time,
                    error=str(e)
                )
                await asyncio.sleep(wait_time)
            else:
                # Final attempt failed
                logger.error("provider_execution_failed_all_retries_exhausted")
                raise
```

---

## Performance Considerations

### Performance Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Provider Switching Overhead** | <100ms | Negligible impact on task execution |
| **Factory Creation Overhead** | <10ms | Fast provider instantiation |
| **Subprocess Performance** | Within 5% of current | No noticeable regression |
| **Direct API Performance** | >20% faster | Eliminates subprocess overhead |
| **Memory Overhead** | <50MB | Minimal memory footprint |
| **Concurrent Tasks** | 100+ | Support parallel agent execution |

### Optimization Strategies

#### 1. Lazy Initialization

```python
class ProviderFactory:
    def __init__(self):
        self._registry = {}
        self._instances: Dict[str, IAgentProvider] = {}  # Cache instances
        self._register_builtin_providers()

    def get_or_create_provider(
        self,
        provider_name: str,
        config: Optional[Dict] = None
    ) -> IAgentProvider:
        """Get cached instance or create new one."""
        cache_key = f"{provider_name}_{hash(frozenset(config.items() if config else []))}"

        if cache_key not in self._instances:
            self._instances[cache_key] = self.create_provider(provider_name, config)

        return self._instances[cache_key]
```

#### 2. Subprocess Pooling (Future Enhancement)

```python
class SubprocessPoolProvider:
    """Provider with subprocess pooling for reduced overhead."""

    def __init__(self, pool_size: int = 4):
        self.pool: List[subprocess.Popen] = []
        self.pool_size = pool_size

    async def _get_or_create_subprocess(self) -> subprocess.Popen:
        """Get available subprocess from pool or create new one."""
        # Implementation: reuse subprocesses for multiple tasks
        pass
```

#### 3. Direct API Optimization

```python
class DirectAPIProvider:
    """Optimized provider using direct API calls."""

    def __init__(self):
        # Persistent HTTP session for connection pooling
        self.session = httpx.AsyncClient(
            limits=httpx.Limits(max_keepalive_connections=10),
            timeout=httpx.Timeout(timeout=60.0)
        )

    async def execute_task(...):
        # Streaming API calls - lower latency than subprocess
        async with self.session.stream('POST', url, json=payload) as response:
            async for chunk in response.aiter_text():
                yield chunk
```

#### 4. Configuration Caching

```python
class ConfigurationCache:
    """Cache provider configurations to avoid repeated file I/O."""

    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._cache_ttl = 300  # 5 minutes

    def get_provider_config(self, provider_name: str) -> Dict:
        """Get cached config or load from file."""
        if provider_name in self._cache:
            if not self._is_expired(provider_name):
                return self._cache[provider_name]

        # Load from file and cache
        config = self._load_config(provider_name)
        self._cache[provider_name] = config
        return config
```

### Performance Benchmarks

**To Be Measured in Phase 4**:

```python
# Benchmark script
async def benchmark_providers():
    """Benchmark all providers for performance comparison."""

    providers = ["claude-code", "opencode", "direct-api"]
    task = "Write a simple Python function"

    results = {}

    for provider_name in providers:
        provider = factory.create_provider(provider_name)

        start = time.time()
        async for _ in provider.execute_task(task, context, ...):
            pass
        duration = time.time() - start

        results[provider_name] = duration

    # Generate comparison report
    print(f"Performance Comparison:")
    for name, duration in sorted(results.items(), key=lambda x: x[1]):
        print(f"  {name}: {duration:.2f}s")
```

---

## Security Architecture

### Security Considerations

#### 1. API Key Management

**Principle**: Never log or expose API keys.

```python
class SecureProvider(IAgentProvider):
    def __init__(self, api_key: Optional[str] = None):
        # Store securely
        self._api_key = api_key or os.getenv(self.get_api_key_env_var())

        # NEVER log the actual key
        logger.info(
            "provider_initialized",
            has_api_key=bool(self._api_key),
            api_key="[REDACTED]"  # Never log actual value
        )

    def __repr__(self):
        # Mask API key in repr
        return f"{self.__class__.__name__}(api_key={'***' if self._api_key else None})"
```

#### 2. Subprocess Isolation

**Principle**: Subprocess should NOT have elevated privileges.

```python
# DO NOT run subprocess as root
# DO NOT allow shell injection
# DO validate all subprocess arguments

cmd = [str(self.cli_path)]  # ✅ List, not string
cmd.extend(['--print'])      # ✅ Safe: no shell interpretation

# ❌ NEVER DO THIS:
# cmd = f"{cli_path} --input '{user_input}'"  # Shell injection risk!
# subprocess.run(cmd, shell=True)  # Dangerous!
```

#### 3. Input Validation

**Principle**: Validate all user inputs before passing to provider.

```python
def validate_task_input(task: str) -> None:
    """Validate task input for security."""

    # Check length
    if len(task) > 100_000:
        raise ValueError("Task input too long (max 100KB)")

    # Check for injection attempts (context-dependent)
    # For subprocess providers, ensure no shell metacharacters in critical fields

    # Sanitize if needed
    task = task.strip()
```

#### 4. Plugin Validation

**Principle**: Validate plugin providers before registration.

```python
def register_provider(
    self,
    provider_name: str,
    provider_class: Type[IAgentProvider]
) -> None:
    """Register provider with security validation."""

    # Validate interface
    if not issubclass(provider_class, IAgentProvider):
        raise ProviderRegistrationError("Must implement IAgentProvider")

    # Validate provider name (no special characters)
    if not re.match(r'^[a-z0-9-]+$', provider_name):
        raise ProviderRegistrationError(
            "Provider name must contain only lowercase letters, numbers, and hyphens"
        )

    # Check for malicious code (basic heuristics)
    source = inspect.getsource(provider_class)
    if 'exec(' in source or 'eval(' in source:
        logger.warning(
            "provider_contains_exec_eval",
            provider_name=provider_name
        )
        # Optionally block registration

    # Register
    self._registry[provider_name] = provider_class
```

#### 5. Audit Logging

**Principle**: Log all provider operations for audit trail.

```python
async def execute_task(...):
    """Execute with comprehensive audit logging."""

    # Log start
    logger.info(
        "provider_execution_start",
        provider=self.name,
        model=model,
        task_hash=hashlib.sha256(task.encode()).hexdigest(),  # Hash, not full task
        timestamp=datetime.utcnow().isoformat(),
        user_id=context.metadata.get("user_id"),
        session_id=context.metadata.get("session_id")
    )

    try:
        async for result in self._execute_internal(...):
            yield result

        # Log success
        logger.info(
            "provider_execution_success",
            provider=self.name,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        # Log failure
        logger.error(
            "provider_execution_failure",
            provider=self.name,
            error_type=type(e).__name__,
            error_message=str(e),
            timestamp=datetime.utcnow().isoformat()
        )
        raise
```

---

## Testing Strategy

### Test Pyramid

```
         ┌─────────────┐
         │   E2E Tests │  10% (End-to-end workflows)
         │     (10)    │
         └─────────────┘
       ┌──────────────────┐
       │ Integration Tests│  30% (Provider integration)
       │      (30)        │
       └──────────────────┘
     ┌───────────────────────┐
     │     Unit Tests        │  60% (Component testing)
     │        (60)           │
     └───────────────────────┘
```

### Unit Tests (60%)

**Test Coverage Target**: >90% for provider module

**Test Files**:
- `tests/core/providers/test_base.py` - Interface validation
- `tests/core/providers/test_factory.py` - Factory logic
- `tests/core/providers/test_claude_code.py` - ClaudeCodeProvider
- `tests/core/providers/test_opencode.py` - OpenCodeProvider
- `tests/core/providers/test_direct_api.py` - DirectAPIProvider

**Example Unit Test**:

```python
import pytest
from gao_dev.core.providers.factory import ProviderFactory
from gao_dev.core.providers.exceptions import ProviderNotFoundError


class TestProviderFactory:
    """Unit tests for ProviderFactory."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = ProviderFactory()

    def test_create_claude_code_provider(self):
        """Test creating ClaudeCodeProvider."""
        provider = self.factory.create_provider("claude-code")

        assert provider.name == "claude-code"
        assert provider.version is not None

    def test_create_provider_not_found(self):
        """Test creating non-existent provider raises error."""
        with pytest.raises(ProviderNotFoundError) as exc_info:
            self.factory.create_provider("non-existent")

        assert "non-existent" in str(exc_info.value)
        assert "Available providers" in str(exc_info.value)

    def test_register_provider(self):
        """Test registering custom provider."""
        class CustomProvider(IAgentProvider):
            # Minimal implementation
            pass

        self.factory.register_provider("custom", CustomProvider)

        assert "custom" in self.factory.list_providers()

    def test_register_duplicate_provider_raises_error(self):
        """Test registering duplicate provider raises error."""
        with pytest.raises(DuplicateProviderError):
            self.factory.register_provider("claude-code", SomeClass)
```

### Integration Tests (30%)

**Purpose**: Test provider integration with ProcessExecutor and orchestrator.

**Test Files**:
- `tests/integration/test_provider_integration.py` - Provider + ProcessExecutor
- `tests/integration/test_multi_provider.py` - Multiple providers
- `tests/integration/test_provider_fallback.py` - Fallback behavior

**Example Integration Test**:

```python
import pytest
from pathlib import Path
from gao_dev.core.services.process_executor import ProcessExecutor
from gao_dev.core.models.agent import AgentContext


@pytest.mark.integration
@pytest.mark.asyncio
class TestProviderIntegration:
    """Integration tests for provider + ProcessExecutor."""

    async def test_execute_task_with_claude_code_provider(self, tmp_path):
        """Test executing task via ClaudeCodeProvider."""
        executor = ProcessExecutor(
            project_root=tmp_path,
            provider_name="claude-code"
        )

        task = "Write a simple hello world script"

        results = []
        async for message in executor.execute_agent_task(task):
            results.append(message)

        assert len(results) > 0
        assert any("hello" in msg.lower() for msg in results)

    async def test_provider_switching(self, tmp_path):
        """Test switching between providers."""
        # Execute with ClaudeCode
        executor1 = ProcessExecutor(
            project_root=tmp_path,
            provider_name="claude-code"
        )

        results1 = []
        async for msg in executor1.execute_agent_task("Test task"):
            results1.append(msg)

        # Execute with OpenCode
        executor2 = ProcessExecutor(
            project_root=tmp_path,
            provider_name="opencode",
            provider_config={"ai_provider": "anthropic"}
        )

        results2 = []
        async for msg in executor2.execute_agent_task("Test task"):
            results2.append(msg)

        # Both should succeed (results may differ slightly)
        assert len(results1) > 0
        assert len(results2) > 0
```

### End-to-End Tests (10%)

**Purpose**: Test complete workflows with real benchmarks.

**Test Files**:
- `tests/e2e/test_provider_workflows.py` - Full workflow execution

**Example E2E Test**:

```python
@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
class TestProviderWorkflows:
    """End-to-end tests for provider workflows."""

    async def test_simple_benchmark_with_opencode(self, benchmark_config):
        """Test running simple benchmark with OpenCode provider."""
        # Update benchmark config to use OpenCode
        benchmark_config["provider"] = "opencode"

        # Run benchmark
        orchestrator = BenchmarkOrchestrator(config=benchmark_config)
        result = await orchestrator.run()

        # Verify success
        assert result.success is True
        assert result.metrics is not None
        assert result.provider_used == "opencode"
```

### Provider Comparison Tests

**Purpose**: Validate provider equivalence for identical tasks.

```python
@pytest.mark.comparison
@pytest.mark.asyncio
class TestProviderComparison:
    """Compare providers for identical tasks."""

    @pytest.mark.parametrize("provider_name", ["claude-code", "opencode", "direct-api"])
    async def test_simple_task_all_providers(self, provider_name, tmp_path):
        """Test simple task executes successfully on all providers."""
        executor = ProcessExecutor(
            project_root=tmp_path,
            provider_name=provider_name
        )

        task = "Create a file named test.txt with content 'Hello World'"

        results = []
        async for msg in executor.execute_agent_task(task):
            results.append(msg)

        # Verify file created
        test_file = tmp_path / "test.txt"
        assert test_file.exists()
        assert test_file.read_text() == "Hello World"
```

### Continuous Integration

**CI Pipeline Steps**:

1. **Unit Tests**: Run on every commit
2. **Integration Tests**: Run on PR
3. **E2E Tests**: Run nightly
4. **Performance Benchmarks**: Run weekly
5. **Security Scans**: Run on PR

**GitHub Actions Workflow**:

```yaml
name: Provider Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run unit tests
        run: |
          pytest tests/core/providers/ -v --cov=gao_dev.core.providers

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Run integration tests
        run: |
          pytest tests/integration/ -v --mark=integration
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## Migration Path

### Phase 1: Internal Refactoring (No User Impact)

**Goal**: Extract ClaudeCodeProvider without breaking existing functionality.

**Steps**:
1. Create provider module structure
2. Implement IAgentProvider interface
3. Extract ClaudeCodeProvider from ProcessExecutor
4. Update ProcessExecutor to use provider internally
5. Run full test suite - all tests pass unchanged

**User Impact**: ZERO - completely internal refactoring

---

### Phase 2: Configuration Schema Update (Optional Adoption)

**Goal**: Add provider configuration fields while maintaining backward compatibility.

**Steps**:
1. Update agent YAML schema (add optional `provider` field)
2. Update defaults.yaml (add provider registry)
3. Update documentation
4. Test with both old and new configs

**User Impact**: MINIMAL - old configs work unchanged, new field optional

**Migration Tool**:

```bash
# CLI command to show provider status
$ gao-dev providers list

Available providers:
  ✓ claude-code (default) - Claude Code CLI
      Status: Configured
      CLI: /usr/local/bin/claude
      API Key: Set (ANTHROPIC_API_KEY)

  ✓ opencode - OpenCode multi-provider agent
      Status: Configured
      CLI: /usr/local/bin/opencode
      API Key: Set (ANTHROPIC_API_KEY)

  ✗ direct-api - Direct API provider
      Status: Not configured
      API Key: Not set (ANTHROPIC_API_KEY)

Current default: claude-code
```

---

### Phase 3: OpenCode Integration (Opt-In)

**Goal**: Add OpenCode as alternative provider for users who want it.

**Steps**:
1. Implement OpenCodeProvider
2. Add to provider registry
3. Document setup instructions
4. Create example configurations

**User Impact**: NONE (unless user opts in)

**Setup Guide**:

```bash
# Install OpenCode
$ npm install -g @sst/opencode

# Verify installation
$ gao-dev providers validate

# Update agent config to use OpenCode (optional)
$ gao-dev config set amelia.provider opencode

# Test OpenCode
$ gao-dev sandbox run benchmark.yaml --provider opencode
```

---

### Phase 4: Production Deployment (Default Remains Claude Code)

**Goal**: Deploy provider abstraction to production with Claude Code as default.

**Steps**:
1. Full test suite passes
2. Documentation complete
3. Migration guide published
4. Release notes prepared
5. Deploy to production

**User Impact**: POSITIVE - more flexibility, no required changes

**Communication**:

```
GAO-Dev v0.11.0 - Multi-Provider Support

New Features:
✨ Multi-provider architecture - use Claude Code, OpenCode, or direct APIs
✨ Intelligent provider fallback - automatic failover if primary unavailable
✨ Plugin support - create custom providers for specialized AI systems

Breaking Changes:
None! Your existing setup continues to work exactly as before.

Migration:
Optional - you can continue using Claude Code (default) or try alternative providers.

See migration guide: docs/MIGRATION_PROVIDER.md
```

---

## Appendix

### A. Glossary

- **Provider**: Backend system for executing AI agent tasks (CLI tool, API, or custom)
- **IAgentProvider**: Abstract interface all providers implement
- **ProviderFactory**: Factory for creating provider instances
- **ClaudeCodeProvider**: Provider using Claude Code CLI (current implementation)
- **OpenCodeProvider**: Provider using OpenCode CLI (multi-AI support)
- **DirectAPIProvider**: Provider using direct HTTP API calls
- **Canonical Model Name**: Provider-agnostic model identifier (e.g., "sonnet-4.5")
- **Model Translation**: Converting canonical names to provider-specific IDs
- **Provider Plugin**: Custom provider registered via plugin system

### B. Comparison with Similar Systems

| System | Architecture | Provider Support | Open Source |
|--------|--------------|------------------|-------------|
| **GAO-Dev (Proposed)** | Provider abstraction | Multi-provider | Yes (MIT) |
| **Claude Code** | Monolithic | Anthropic only | No |
| **OpenCode** | Multi-provider built-in | Multiple | Yes (MIT) |
| **Aider** | LLM library abstraction | Multiple (via library) | Yes (Apache) |
| **Cursor** | Proprietary | Multiple | No |

**GAO-Dev's Unique Value**:
- Only autonomous dev system with provider abstraction
- Plugin ecosystem for custom providers
- Workflow-driven development (not just code editing)
- Scale-adaptive routing (Levels 0-4)

### C. Future Enhancements (Out of Scope for Epic 11)

**Potential Future Work**:

1. **Provider Load Balancing**
   - Distribute tasks across multiple provider instances
   - Parallel execution for performance
   - Cost optimization via intelligent routing

2. **Provider A/B Testing**
   - Run same task on multiple providers
   - Compare quality, speed, cost
   - Automated quality scoring

3. **Provider Monitoring Dashboard**
   - Real-time provider health
   - Performance metrics per provider
   - Cost tracking and alerts

4. **Hybrid Execution**
   - Use different providers for different task types
   - Planning tasks → Claude
   - Implementation tasks → OpenCode with OpenAI
   - Code review → Direct API for speed

5. **Local Model Support**
   - Ollama integration
   - LM Studio integration
   - Self-hosted models for privacy

### D. References

- **OpenCode GitHub**: https://github.com/sst/opencode
- **Claude Code Documentation**: https://claude.ai/claude-code
- **Anthropic API Docs**: https://docs.anthropic.com/
- **OpenAI API Docs**: https://platform.openai.com/docs
- **Original Analysis**: `docs/provider-abstraction-analysis.md`
- **PRD**: `docs/features/agent-provider-abstraction/PRD.md`

### E. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-04 | Winston (Architect) | Initial architecture design |

---

**Architecture Review Sign-off:**

- [ ] Technical Architect (Winston) - Approved
- [ ] Lead Developer (Amelia) - Reviewed
- [ ] Product Manager (John) - Aligned with PRD
- [ ] Security Review - Approved

**Next Steps:**
1. Approve architecture design
2. Break down into detailed stories
3. Begin Phase 1 implementation
4. Set up test infrastructure
