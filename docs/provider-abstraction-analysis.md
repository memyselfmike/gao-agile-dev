# GAO-Dev Agent Provider Abstraction Analysis

**Date**: 2025-11-04
**Status**: Design Phase
**Epic**: Future Enhancement

---

## Executive Summary

This document analyzes GAO-Dev's current coupling to Claude Code/Anthropic SDK and proposes an abstraction layer to support multiple agent execution providers (Claude Code, OpenCode, direct API calls, etc.).

**Key Finding**: GAO-Dev has **low coupling** to Claude Code - only one critical dependency point (`ProcessExecutor`). Migration to provider-agnostic architecture is **highly feasible** with minimal disruption.

**Recommendation**: Implement provider abstraction layer to enable multi-provider support while maintaining backward compatibility.

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [OpenCode Architecture Review](#opencode-architecture-review)
3. [Coupling Points Assessment](#coupling-points-assessment)
4. [Proposed Architecture](#proposed-architecture)
5. [Implementation Plan](#implementation-plan)
6. [Migration Strategy](#migration-strategy)
7. [Trade-offs and Considerations](#trade-offs-and-considerations)
8. [Appendix](#appendix)

---

## Current State Analysis

### Claude Code Dependency Points

GAO-Dev's architecture has **1 critical dependency** on Claude Code:

#### Critical Dependency: ProcessExecutor

**Location**: `gao_dev/core/services/process_executor.py`

**Current Implementation**:
```python
class ProcessExecutor:
    """Executes external processes (Claude CLI)."""

    async def execute_agent_task(self, task: str, timeout: Optional[int] = None):
        # Hardcoded Claude CLI invocation
        cmd = [str(self.cli_path)]
        cmd.extend(['--print'])  # Non-interactive output
        cmd.extend(['--dangerously-skip-permissions'])  # Auto-approve tools
        cmd.extend(['--model', 'claude-sonnet-4-5-20250929'])
        cmd.extend(['--add-dir', str(self.project_root)])

        # Execute subprocess
        process = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, ...)
        stdout, stderr = process.communicate(input=task, timeout=timeout)
```

**Coupling Level**: **TIGHT** - Direct subprocess invocation with Claude-specific flags.

#### Non-Critical Dependencies

These are **easily abstracted** and pose minimal migration risk:

1. **Model Names** - Referenced in configs but abstracted through variables
   - `claude-sonnet-4-5-20250929` hardcoded in agent configs
   - Already externalized to YAML files (Epic 10)
   - Simple string mapping can translate model names

2. **API Key** - Environment variable
   - `ANTHROPIC_API_KEY` used in ProcessExecutor
   - Can be generalized to provider-specific keys

3. **Comments/Logs** - References to "Claude" in logs
   - No functional impact
   - Can be updated to generic "AI Agent" terminology

### Architecture Strengths (Enables Easy Migration)

GAO-Dev's architecture has **excellent abstraction** that makes provider migration straightforward:

1. **IAgent Interface** - Provider-agnostic contract
   - `execute_task(task, context) -> AsyncGenerator[str, None]`
   - No Claude-specific methods or dependencies
   - Clean abstraction boundary

2. **Agent Factory Pattern** - Centralized creation
   - Single point of control for agent instantiation
   - Already supports plugin agents
   - Can inject provider-specific implementations

3. **YAML Configuration** - Externalized agent definitions
   - All agent configs in `gao_dev/config/agents/*.yaml`
   - Model names, tools, personas all configurable
   - Provider can be added as configuration field

4. **Service Layer Architecture** - Clean separation
   - ProcessExecutor is isolated service
   - Single Responsibility Principle enforced
   - Can be replaced without touching orchestration logic

**Assessment**: GAO-Dev is **well-positioned** for provider abstraction with minimal refactoring.

---

## OpenCode Architecture Review

### Overview

**OpenCode** is an open-source AI coding agent built for terminal environments.

**GitHub**: https://github.com/sst/opencode
**License**: MIT
**Stars**: 31.3k
**Language**: TypeScript (59.5%), Python (14.8%), Go (12.0%)

### Key Features

1. **Provider-Agnostic Architecture**
   - Supports Anthropic (Claude), OpenAI (GPT), Google (Gemini), local models
   - Abstracted provider interface
   - Runtime provider selection

2. **Built-in LSP Support**
   - Language Server Protocol integration
   - Enhanced code intelligence
   - Better than basic file operations

3. **Terminal-First Design**
   - Optimized for neovim and CLI workflows
   - Non-GUI interaction patterns
   - Aligns with GAO-Dev's CLI focus

4. **Client/Server Architecture**
   - Separates execution from control
   - Enables remote agent execution
   - Mobile client support

5. **Modular Design**
   - Monorepo with package-based architecture
   - Plugin system for extensibility
   - VS Code SDK available

### Technology Stack

- **Runtime**: Bun (JavaScript/TypeScript)
- **Languages**: TypeScript, Python, Go
- **Package Manager**: Bun with workspace support
- **Infrastructure**: GitHub Actions, Husky hooks
- **Config**: `opencode.json` files

### Comparison with Claude Code

| Feature | Claude Code | OpenCode |
|---------|-------------|----------|
| **Provider Support** | Anthropic only | Multi-provider |
| **Language** | Node.js/TypeScript | Bun/TypeScript |
| **LSP Support** | Unknown | Built-in |
| **Architecture** | CLI tool | Client/Server |
| **License** | Proprietary | MIT (Open Source) |
| **Customization** | Limited | High (plugin system) |
| **Mobile Support** | No | Yes (via server) |
| **Cost** | Anthropic API | Varies by provider |

### Integration Feasibility

**High Feasibility** - OpenCode can be integrated as an alternative provider:

1. **Command-line Interface** - Similar to Claude Code
2. **Task-based Execution** - Accepts prompts, returns results
3. **Tool Support** - Likely supports file operations, bash, etc.
4. **Async Execution** - Can be wrapped in async Python interface

**Challenges**:
1. **TypeScript/Bun Dependency** - Requires Bun runtime installation
2. **Different CLI Flags** - Will need to map GAO-Dev concepts to OpenCode commands
3. **Output Format** - May differ from Claude Code
4. **Documentation** - Need to study OpenCode's CLI interface

**Next Steps for OpenCode Integration**:
1. Install OpenCode locally
2. Test basic CLI invocation
3. Map CLI flags and options
4. Implement provider adapter

---

## Coupling Points Assessment

### Severity Matrix

| Component | Coupling Level | Migration Effort | Risk |
|-----------|---------------|------------------|------|
| **ProcessExecutor** | **TIGHT** | **Medium** | **Low** |
| Agent Configs (YAML) | Loose | Low | Minimal |
| Model Names | Loose | Low | Minimal |
| API Keys | Loose | Low | Minimal |
| IAgent Interface | None | None | None |
| Agent Factory | None | None | None |
| Orchestrators | None | None | None |

### Detailed Assessment

#### 1. ProcessExecutor (CRITICAL PATH)

**Current State**:
```python
# Hardcoded Claude CLI execution
cmd = [str(self.cli_path), '--print', '--dangerously-skip-permissions', ...]
process = subprocess.Popen(cmd, ...)
```

**Migration Strategy**: Replace with provider abstraction

**Effort**: Medium (2-3 days)
- Create IAgentProvider interface
- Implement ClaudeCodeProvider
- Implement OpenCodeProvider (or DirectAPIProvider)
- Update ProcessExecutor to use provider
- Test both providers

**Risk**: Low
- ProcessExecutor is isolated service
- Well-tested with integration tests
- Easy to validate with existing test suite

#### 2. Agent YAML Configurations

**Current State**:
```yaml
agent:
  configuration:
    model: "claude-sonnet-4-5-20250929"
```

**Migration Strategy**: Add provider field

**Effort**: Low (< 1 day)
- Add optional `provider` field to agent YAML schema
- Default to "claude-code" for backward compatibility
- Support provider-specific model names

**Risk**: Minimal
- Backward compatible (optional field)
- Schema validation already in place
- Isolated to config loading

#### 3. Model Name Mapping

**Current State**:
- Hardcoded Claude model IDs in configs
- Used by ProcessExecutor when building CLI command

**Migration Strategy**: Model registry/mapping

**Effort**: Low (< 1 day)
- Create model name mapping (Claude → OpenAI → Google, etc.)
- Provider-specific model translation
- Centralized in provider implementation

**Risk**: Minimal
- No breaking changes
- Can maintain Claude names as canonical
- Translation happens at provider boundary

#### 4. API Key Management

**Current State**:
```python
self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
```

**Migration Strategy**: Multi-key support

**Effort**: Low (< 1 day)
- Provider-specific environment variables
- Configuration-based key selection
- Fallback to provider defaults

**Risk**: Minimal
- Environment variables isolated
- No code changes in orchestrators
- Provider manages own auth

### Total Migration Estimate

**Effort**: 4-6 days
**Risk**: Low
**Impact**: High (enables multi-provider support)

---

## Proposed Architecture

### Provider Abstraction Layer

```
┌─────────────────────────────────────────────────────────────┐
│                     GAO-Dev Orchestrator                     │
│                    (Provider-Agnostic)                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    IAgentProvider                            │
│                   (Abstract Interface)                       │
│  + execute_task(task, context) -> AsyncGenerator[str]       │
│  + supports_tool(tool_name) -> bool                          │
│  + get_supported_models() -> List[str]                       │
│  + validate_config(config) -> bool                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┬─────────────────┐
        │               │               │                 │
        ▼               ▼               ▼                 ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ ClaudeCode   │ │  OpenCode    │ │  DirectAPI   │ │   Custom     │
│  Provider    │ │  Provider    │ │  Provider    │ │  Provider    │
│              │ │              │ │              │ │ (Plugin)     │
│ - Subprocess │ │ - Subprocess │ │ - HTTP API   │ │ - User       │
│ - Claude CLI │ │ - OpenCode   │ │ - Anthropic  │ │   Defined    │
│              │ │   CLI        │ │   SDK        │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

### IAgentProvider Interface

```python
"""Provider interface for agent execution backends."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Optional
from pathlib import Path
from ..models.agent import AgentContext


class IAgentProvider(ABC):
    """
    Abstract interface for agent execution providers.

    Implementations can use different backends:
    - Claude Code CLI (subprocess)
    - OpenCode CLI (subprocess)
    - Direct API calls (Anthropic, OpenAI, etc.)
    - Custom providers (via plugins)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'claude-code', 'opencode', 'direct-api')."""
        pass

    @abstractmethod
    async def execute_task(
        self,
        task: str,
        context: AgentContext,
        model: str,
        tools: List[str],
        timeout: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute an agent task using this provider.

        Args:
            task: Task description/prompt
            context: Execution context (project root, etc.)
            model: Model identifier (provider-specific)
            tools: List of tool names to enable
            timeout: Optional timeout in seconds

        Yields:
            Progress messages and results

        Raises:
            ProviderExecutionError: If execution fails
        """
        pass

    @abstractmethod
    def supports_tool(self, tool_name: str) -> bool:
        """Check if provider supports a given tool."""
        pass

    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Get list of models supported by this provider."""
        pass

    @abstractmethod
    def translate_model_name(self, canonical_name: str) -> str:
        """
        Translate canonical model name to provider-specific name.

        Example:
            canonical: "sonnet-4.5"
            claude-code: "claude-sonnet-4-5-20250929"
            opencode: "anthropic/claude-sonnet-4.5"
        """
        pass

    @abstractmethod
    async def validate_configuration(self) -> bool:
        """Validate that provider is properly configured (API keys, CLI installed, etc.)."""
        pass

    @abstractmethod
    def get_configuration_schema(self) -> Dict:
        """Get JSON schema for provider-specific configuration."""
        pass
```

### ClaudeCodeProvider Implementation

```python
"""Claude Code provider implementation."""

from pathlib import Path
from typing import AsyncGenerator, List, Dict, Optional
import subprocess
import os
import structlog

from .base import IAgentProvider
from ..models.agent import AgentContext
from ..exceptions import ProviderExecutionError

logger = structlog.get_logger()


class ClaudeCodeProvider(IAgentProvider):
    """
    Provider that executes tasks using Claude Code CLI.

    This is the original GAO-Dev implementation, extracted
    into a provider for multi-provider support.
    """

    TOOL_MAPPING = {
        "Read": "read",
        "Write": "write",
        "Edit": "edit",
        "Bash": "bash",
        "Grep": "grep",
        "Glob": "glob",
        # ... etc
    }

    MODEL_MAPPING = {
        "sonnet-4.5": "claude-sonnet-4-5-20250929",
        "sonnet-3.5": "claude-sonnet-3-5-20241022",
        "opus-3": "claude-opus-3-20250219",
        # Passthrough for full names
        "claude-sonnet-4-5-20250929": "claude-sonnet-4-5-20250929",
    }

    def __init__(self, cli_path: Optional[Path] = None):
        """
        Initialize Claude Code provider.

        Args:
            cli_path: Path to Claude CLI executable (auto-detected if None)
        """
        self.cli_path = cli_path or self._find_cli()
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

    @property
    def name(self) -> str:
        return "claude-code"

    async def execute_task(
        self,
        task: str,
        context: AgentContext,
        model: str,
        tools: List[str],
        timeout: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Execute task via Claude Code CLI."""

        # Translate model name
        model_id = self.translate_model_name(model)

        # Build command
        cmd = [str(self.cli_path)]
        cmd.extend(['--print'])
        cmd.extend(['--dangerously-skip-permissions'])
        cmd.extend(['--model', model_id])
        cmd.extend(['--add-dir', str(context.project_root)])

        # Set environment
        env = os.environ.copy()
        if self.api_key:
            env['ANTHROPIC_API_KEY'] = self.api_key

        # Execute
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                cwd=str(context.project_root)
            )

            stdout, stderr = process.communicate(input=task, timeout=timeout or 3600)

            if stdout:
                yield stdout

            if process.returncode != 0:
                raise ProviderExecutionError(
                    f"Claude Code failed with exit code {process.returncode}: {stderr}"
                )

        except subprocess.TimeoutExpired:
            process.kill()
            raise ProviderExecutionError(f"Execution timed out after {timeout} seconds")

    def supports_tool(self, tool_name: str) -> bool:
        """Check if Claude Code supports this tool."""
        return tool_name in self.TOOL_MAPPING

    def get_supported_models(self) -> List[str]:
        """Get supported Claude models."""
        return list(self.MODEL_MAPPING.keys())

    def translate_model_name(self, canonical_name: str) -> str:
        """Translate to Claude-specific model ID."""
        return self.MODEL_MAPPING.get(canonical_name, canonical_name)

    async def validate_configuration(self) -> bool:
        """Validate Claude Code is installed and configured."""
        if not self.cli_path or not self.cli_path.exists():
            return False
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set")
            return False
        return True

    def get_configuration_schema(self) -> Dict:
        """Get configuration schema for Claude Code."""
        return {
            "type": "object",
            "properties": {
                "cli_path": {"type": "string", "description": "Path to Claude CLI"},
                "api_key": {"type": "string", "description": "Anthropic API key"}
            }
        }

    def _find_cli(self) -> Optional[Path]:
        """Auto-detect Claude CLI installation."""
        # Implementation from existing cli_detector.py
        pass
```

### OpenCodeProvider Implementation

```python
"""OpenCode provider implementation."""

from pathlib import Path
from typing import AsyncGenerator, List, Dict, Optional
import subprocess
import os
import structlog

from .base import IAgentProvider
from ..models.agent import AgentContext
from ..exceptions import ProviderExecutionError

logger = structlog.get_logger()


class OpenCodeProvider(IAgentProvider):
    """
    Provider that executes tasks using OpenCode CLI.

    OpenCode is an open-source AI coding agent that supports
    multiple providers (Anthropic, OpenAI, Google, local models).
    """

    MODEL_MAPPING = {
        # Map canonical names to OpenCode provider/model format
        "sonnet-4.5": "anthropic/claude-sonnet-4.5",
        "gpt-4": "openai/gpt-4",
        "gemini-pro": "google/gemini-pro",
    }

    def __init__(
        self,
        cli_path: Optional[Path] = None,
        provider: str = "anthropic"
    ):
        """
        Initialize OpenCode provider.

        Args:
            cli_path: Path to OpenCode CLI (auto-detected if None)
            provider: Underlying AI provider (anthropic, openai, google)
        """
        self.cli_path = cli_path or self._find_cli()
        self.ai_provider = provider
        self.api_key = self._get_api_key(provider)

    @property
    def name(self) -> str:
        return "opencode"

    async def execute_task(
        self,
        task: str,
        context: AgentContext,
        model: str,
        tools: List[str],
        timeout: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Execute task via OpenCode CLI."""

        # Translate model name
        model_id = self.translate_model_name(model)

        # Build command (will need to be refined based on OpenCode docs)
        cmd = [str(self.cli_path)]
        cmd.extend(['--provider', self.ai_provider])
        cmd.extend(['--model', model_id])
        cmd.extend(['--cwd', str(context.project_root)])
        # Add OpenCode-specific flags

        # Set environment
        env = os.environ.copy()
        if self.api_key:
            env[f'{self.ai_provider.upper()}_API_KEY'] = self.api_key

        # Execute (similar to ClaudeCodeProvider)
        # ... implementation ...

        yield "OpenCode execution placeholder"

    def supports_tool(self, tool_name: str) -> bool:
        """Check if OpenCode supports this tool."""
        # OpenCode has LSP support, so it may have different tools
        return True  # Placeholder

    def get_supported_models(self) -> List[str]:
        """Get supported models for current provider."""
        return list(self.MODEL_MAPPING.keys())

    def translate_model_name(self, canonical_name: str) -> str:
        """Translate to OpenCode model format."""
        return self.MODEL_MAPPING.get(canonical_name, f"{self.ai_provider}/{canonical_name}")

    async def validate_configuration(self) -> bool:
        """Validate OpenCode is installed and configured."""
        if not self.cli_path or not self.cli_path.exists():
            return False
        if not self.api_key:
            logger.warning(f"{self.ai_provider.upper()}_API_KEY not set")
            return False
        return True

    def get_configuration_schema(self) -> Dict:
        """Get configuration schema."""
        return {
            "type": "object",
            "properties": {
                "cli_path": {"type": "string"},
                "provider": {
                    "type": "string",
                    "enum": ["anthropic", "openai", "google", "local"]
                },
                "api_key": {"type": "string"}
            }
        }

    def _find_cli(self) -> Optional[Path]:
        """Auto-detect OpenCode CLI installation."""
        # Check common installation paths
        pass

    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for provider."""
        key_mapping = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
        }
        return os.getenv(key_mapping.get(provider, ""))
```

### Provider Factory

```python
"""Provider factory for creating agent execution providers."""

from typing import Dict, Type, Optional
from pathlib import Path
import structlog

from .base import IAgentProvider
from .claude_code import ClaudeCodeProvider
from .opencode import OpenCodeProvider
from ..exceptions import ProviderNotFoundError

logger = structlog.get_logger()


class ProviderFactory:
    """
    Factory for creating agent execution providers.

    Supports built-in providers (claude-code, opencode) and
    custom providers via plugin registration.
    """

    def __init__(self):
        """Initialize provider factory with built-in providers."""
        self._registry: Dict[str, Type[IAgentProvider]] = {
            "claude-code": ClaudeCodeProvider,
            "opencode": OpenCodeProvider,
        }

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
        """
        if provider_name not in self._registry:
            available = ", ".join(self._registry.keys())
            raise ProviderNotFoundError(
                f"Provider '{provider_name}' not found. Available: {available}"
            )

        provider_class = self._registry[provider_name]

        # Create provider with config
        if config:
            return provider_class(**config)
        else:
            return provider_class()

    def register_provider(
        self,
        provider_name: str,
        provider_class: Type[IAgentProvider]
    ) -> None:
        """
        Register a custom provider (for plugins).

        Args:
            provider_name: Unique provider identifier
            provider_class: Provider class implementing IAgentProvider
        """
        if not issubclass(provider_class, IAgentProvider):
            raise ValueError(
                f"Provider class must implement IAgentProvider interface"
            )

        self._registry[provider_name] = provider_class

        logger.info(
            "provider_registered",
            provider_name=provider_name,
            provider_class=provider_class.__name__
        )

    def list_providers(self) -> list[str]:
        """List all registered providers."""
        return list(self._registry.keys())
```

### Configuration Schema Updates

#### Agent YAML Configuration

```yaml
# gao_dev/config/agents/amelia.yaml

agent:
  metadata:
    name: Amelia
    role: Software Developer
    version: 1.0.0

  persona:
    background: |
      You are Amelia, a skilled software developer...

  tools:
    - Read
    - Write
    - Edit
    - Bash

  configuration:
    # NEW: Provider selection (optional, defaults to claude-code)
    provider: "claude-code"  # or "opencode", "direct-api", custom

    # NEW: Provider-specific config (optional)
    provider_config:
      # For OpenCode
      ai_provider: "anthropic"  # or "openai", "google"

    # Canonical model name (translated by provider)
    model: "sonnet-4.5"  # Provider translates to specific ID

    max_tokens: 8000
    temperature: 0.7
```

#### System Configuration

```yaml
# gao_dev/config/defaults.yaml

providers:
  # Default provider for all agents
  default: "claude-code"

  # Provider-specific configuration
  claude-code:
    cli_path: null  # Auto-detect
    api_key_env: "ANTHROPIC_API_KEY"

  opencode:
    cli_path: null  # Auto-detect
    ai_provider: "anthropic"
    api_key_env: "ANTHROPIC_API_KEY"

  direct-api:
    provider: "anthropic"
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: null  # Optional override

# Model name registry (canonical -> provider-specific)
models:
  canonical:
    - name: "sonnet-4.5"
      providers:
        claude-code: "claude-sonnet-4-5-20250929"
        opencode: "anthropic/claude-sonnet-4.5"
        direct-api: "claude-sonnet-4-5-20250929"

    - name: "gpt-4"
      providers:
        opencode: "openai/gpt-4"
        direct-api: "gpt-4"
```

### Updated ProcessExecutor

```python
"""ProcessExecutor refactored to use provider abstraction."""

from pathlib import Path
from typing import AsyncGenerator, Optional
import structlog

from ..providers.factory import ProviderFactory
from ..providers.base import IAgentProvider
from ..models.agent import AgentContext

logger = structlog.get_logger()


class ProcessExecutor:
    """
    Executes agent tasks via configurable provider.

    Refactored from Claude-specific implementation to support
    multiple providers (Claude Code, OpenCode, Direct API, etc.).
    """

    DEFAULT_TIMEOUT = 3600

    def __init__(
        self,
        project_root: Path,
        provider: Optional[IAgentProvider] = None,
        provider_name: str = "claude-code",
        provider_config: Optional[dict] = None
    ):
        """
        Initialize executor with provider.

        Args:
            project_root: Project root directory
            provider: Pre-configured provider instance (optional)
            provider_name: Provider name if creating new instance
            provider_config: Provider-specific configuration
        """
        self.project_root = project_root

        # Use provided instance or create from factory
        if provider:
            self.provider = provider
        else:
            factory = ProviderFactory()
            self.provider = factory.create_provider(
                provider_name,
                provider_config
            )

        logger.info(
            "process_executor_initialized",
            project_root=str(project_root),
            provider=self.provider.name
        )

    async def execute_agent_task(
        self,
        task: str,
        model: str = "sonnet-4.5",
        tools: Optional[list[str]] = None,
        timeout: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute agent task via configured provider.

        Args:
            task: Task description/prompt
            model: Canonical model name
            tools: List of tool names to enable
            timeout: Optional timeout in seconds

        Yields:
            Progress messages and results
        """
        # Validate provider configuration
        is_valid = await self.provider.validate_configuration()
        if not is_valid:
            raise ValueError(
                f"Provider '{self.provider.name}' not properly configured"
            )

        # Create execution context
        context = AgentContext(project_root=self.project_root)

        # Delegate to provider
        logger.info(
            "executing_task_via_provider",
            provider=self.provider.name,
            model=model,
            tools=tools
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

---

## Implementation Plan

### Phase 1: Foundation (Week 1)

**Goal**: Create provider abstraction layer without breaking existing functionality.

#### Tasks

1. **Create Provider Module Structure** (1 day)
   - [ ] Create `gao_dev/core/providers/` directory
   - [ ] Create `base.py` with `IAgentProvider` interface
   - [ ] Create `exceptions.py` for provider errors
   - [ ] Create `factory.py` for provider creation
   - [ ] Update `__init__.py` exports

2. **Implement ClaudeCodeProvider** (2 days)
   - [ ] Extract ProcessExecutor logic into ClaudeCodeProvider
   - [ ] Implement all IAgentProvider methods
   - [ ] Add model name translation
   - [ ] Add tool support checking
   - [ ] Add configuration validation
   - [ ] Add CLI auto-detection
   - [ ] Write unit tests

3. **Refactor ProcessExecutor** (1 day)
   - [ ] Update to use IAgentProvider
   - [ ] Add provider injection via constructor
   - [ ] Maintain backward compatibility (default to claude-code)
   - [ ] Update tests to cover both old and new usage
   - [ ] Update documentation

4. **Update Configuration Schema** (1 day)
   - [ ] Add optional `provider` field to agent YAML schema
   - [ ] Add `provider_config` field for provider-specific config
   - [ ] Update `defaults.yaml` with provider registry
   - [ ] Add model name mapping configuration
   - [ ] Update schema validation
   - [ ] Add migration notes to CHANGELOG

**Deliverables**:
- [ ] Working provider abstraction layer
- [ ] ClaudeCodeProvider fully tested
- [ ] ProcessExecutor refactored (backward compatible)
- [ ] Configuration schema updated
- [ ] All existing tests passing

**Success Criteria**:
- All 400+ existing tests pass
- No breaking changes to public API
- ClaudeCodeProvider produces identical results to old ProcessExecutor
- CI/CD pipeline green

### Phase 2: OpenCode Integration (Week 2)

**Goal**: Add OpenCode as alternative provider.

#### Tasks

1. **Research OpenCode CLI** (1 day)
   - [ ] Install OpenCode locally
   - [ ] Test basic CLI commands
   - [ ] Document CLI flags and options
   - [ ] Test with different providers (Anthropic, OpenAI)
   - [ ] Document output formats
   - [ ] Identify gaps/limitations

2. **Implement OpenCodeProvider** (2 days)
   - [ ] Create `opencode.py` provider implementation
   - [ ] Implement CLI invocation logic
   - [ ] Add provider selection (anthropic, openai, google)
   - [ ] Implement model name translation
   - [ ] Add tool support mapping
   - [ ] Add configuration validation
   - [ ] Write unit tests
   - [ ] Write integration tests

3. **Create Provider Comparison Test Suite** (1 day)
   - [ ] Create test cases that run against both providers
   - [ ] Compare outputs for identical tasks
   - [ ] Document behavioral differences
   - [ ] Create compatibility matrix
   - [ ] Add to CI pipeline

4. **Documentation** (1 day)
   - [ ] Update CLAUDE.md with provider information
   - [ ] Create provider selection guide
   - [ ] Document provider configuration
   - [ ] Add troubleshooting section
   - [ ] Create OpenCode setup guide
   - [ ] Update CLI command docs

**Deliverables**:
- [ ] Working OpenCodeProvider
- [ ] Provider comparison test suite
- [ ] Comprehensive documentation
- [ ] Setup guides for both providers

**Success Criteria**:
- OpenCodeProvider can execute basic tasks
- Tests pass with both providers
- Clear documentation for users
- No regression in ClaudeCodeProvider

### Phase 3: Advanced Features (Week 3)

**Goal**: Add advanced provider features and optimizations.

#### Tasks

1. **Direct API Provider** (2 days)
   - [ ] Create `DirectAPIProvider` using Anthropic SDK
   - [ ] Bypass CLI subprocess overhead
   - [ ] Implement streaming responses
   - [ ] Add retry logic
   - [ ] Add rate limiting
   - [ ] Optimize for performance
   - [ ] Write tests

2. **Provider Selection Strategy** (1 day)
   - [ ] Auto-select provider based on availability
   - [ ] Fallback chain (DirectAPI → ClaudeCode → OpenCode)
   - [ ] Cost optimization (prefer cheaper providers)
   - [ ] Performance optimization (prefer faster providers)
   - [ ] User preference overrides

3. **Provider Plugin System** (1 day)
   - [ ] Extend existing plugin system for providers
   - [ ] Create provider plugin interface
   - [ ] Example custom provider plugin
   - [ ] Documentation for custom providers
   - [ ] Test plugin registration

4. **Performance Optimization** (1 day)
   - [ ] Benchmark all providers
   - [ ] Optimize subprocess handling
   - [ ] Add caching where appropriate
   - [ ] Reduce overhead in provider factory
   - [ ] Document performance characteristics

**Deliverables**:
- [ ] DirectAPIProvider implementation
- [ ] Provider selection strategy
- [ ] Provider plugin support
- [ ] Performance benchmarks

**Success Criteria**:
- 3 working providers (ClaudeCode, OpenCode, DirectAPI)
- Automatic provider selection works
- Performance meets or exceeds original implementation
- Plugin system supports custom providers

### Phase 4: Production Readiness (Week 4)

**Goal**: Polish, test, and prepare for production deployment.

#### Tasks

1. **Comprehensive Testing** (2 days)
   - [ ] End-to-end tests with all providers
   - [ ] Stress testing (concurrent tasks)
   - [ ] Error handling tests
   - [ ] Timeout handling tests
   - [ ] API key validation tests
   - [ ] Configuration validation tests
   - [ ] Provider fallback tests

2. **Migration Tooling** (1 day)
   - [ ] Create migration script for existing configs
   - [ ] Add provider detection utility
   - [ ] Add provider validation command
   - [ ] Create migration guide
   - [ ] Test migration on real projects

3. **Documentation & Examples** (1 day)
   - [ ] Complete API reference for providers
   - [ ] Provider selection decision tree
   - [ ] Configuration examples for each provider
   - [ ] Troubleshooting guide
   - [ ] FAQ section
   - [ ] Video walkthrough (optional)

4. **Release Preparation** (1 day)
   - [ ] Update CHANGELOG
   - [ ] Version bump (minor version)
   - [ ] Update README with provider info
   - [ ] Create release notes
   - [ ] Tag release
   - [ ] Deploy to production

**Deliverables**:
- [ ] Full test coverage for provider system
- [ ] Migration tooling and guides
- [ ] Complete documentation
- [ ] Production release

**Success Criteria**:
- 100% test coverage for provider module
- Zero regressions in existing functionality
- Comprehensive documentation
- Successful production deployment

---

## Migration Strategy

### Backward Compatibility Approach

**Philosophy**: Zero breaking changes for existing users.

#### Default Behavior

```python
# OLD CODE - Still works exactly as before
executor = ProcessExecutor(
    project_root=Path("/project"),
    cli_path=Path("/usr/bin/claude"),
    api_key="sk-..."
)

# Internally, this now uses ClaudeCodeProvider
# Users see no difference
```

#### New Provider Selection

```python
# NEW CODE - Explicit provider selection
from gao_dev.core.providers import ProviderFactory

factory = ProviderFactory()
provider = factory.create_provider("opencode", {
    "ai_provider": "anthropic"
})

executor = ProcessExecutor(
    project_root=Path("/project"),
    provider=provider
)

# Or via configuration
executor = ProcessExecutor(
    project_root=Path("/project"),
    provider_name="opencode",
    provider_config={"ai_provider": "openai"}
)
```

### Configuration Migration

#### Step 1: Auto-Detection

```bash
# New CLI command to detect available providers
gao-dev providers list

# Output:
# Available providers:
#   ✓ claude-code (Claude CLI detected at /usr/local/bin/claude)
#   ✓ opencode (OpenCode CLI detected at /usr/local/bin/opencode)
#   ✗ direct-api (ANTHROPIC_API_KEY not set)
```

#### Step 2: Configuration Update

```bash
# Migrate existing config to new format
gao-dev providers migrate

# This updates agent YAML files to include provider field
# while maintaining full backward compatibility
```

#### Step 3: Validation

```bash
# Validate provider configuration
gao-dev providers validate

# Output:
# Validating providers...
#   ✓ claude-code: Configured correctly
#   ✓ opencode: Configured correctly
#   ⚠ direct-api: API key not set (optional)
```

### Rollout Plan

#### Phase 1: Soft Launch (Internal Testing)

- Deploy provider abstraction to development environment
- Test with existing benchmarks
- Verify no performance regression
- Gather internal feedback

#### Phase 2: Beta Release (Early Adopters)

- Release as beta feature (flag: `--enable-multi-provider`)
- Invite community testing
- Document known issues
- Iterate based on feedback

#### Phase 3: General Availability

- Enable multi-provider by default
- Claude Code remains default provider
- Comprehensive documentation
- Migration support for existing users

#### Phase 4: Optimization

- Based on usage data, optimize default provider selection
- Add provider-specific optimizations
- Expand provider ecosystem

---

## Trade-offs and Considerations

### Benefits

1. **Provider Independence**
   - ✅ Not locked into Claude Code
   - ✅ Can switch providers if one becomes unavailable
   - ✅ Can use best provider for each task
   - ✅ Cost optimization opportunities

2. **Flexibility**
   - ✅ Support for multiple AI providers (OpenAI, Google, local)
   - ✅ Custom providers via plugin system
   - ✅ Easy to add new providers
   - ✅ A/B testing different providers

3. **Performance**
   - ✅ Direct API option avoids subprocess overhead
   - ✅ Can optimize per-provider
   - ✅ Parallel provider execution (future)

4. **Reliability**
   - ✅ Automatic fallback if primary provider fails
   - ✅ Better error handling
   - ✅ Provider-specific retry logic

5. **Open Source Alignment**
   - ✅ OpenCode is MIT licensed
   - ✅ Community-driven development
   - ✅ More transparency

### Costs/Risks

1. **Complexity**
   - ❌ Additional abstraction layer
   - ❌ More configuration options
   - ❌ More code to maintain
   - **Mitigation**: Good documentation, sensible defaults

2. **Testing Burden**
   - ❌ Must test against multiple providers
   - ❌ More integration tests needed
   - ❌ Behavioral differences between providers
   - **Mitigation**: Automated test matrix, clear compatibility docs

3. **Migration Effort**
   - ❌ 4 weeks of development time
   - ❌ Risk of introducing bugs
   - ❌ Learning curve for users
   - **Mitigation**: Backward compatibility, comprehensive testing

4. **Provider Parity**
   - ❌ Not all providers support same features
   - ❌ Different tool sets
   - ❌ Different output formats
   - **Mitigation**: Feature detection, graceful degradation

5. **Maintenance**
   - ❌ Must track changes across multiple CLIs/APIs
   - ❌ Provider-specific bugs
   - ❌ Version compatibility issues
   - **Mitigation**: Provider versioning, deprecation policy

### Alternatives Considered

#### Alternative 1: Do Nothing (Status Quo)

**Pros**:
- Zero effort
- No risk
- Works today

**Cons**:
- Vendor lock-in to Anthropic/Claude Code
- No flexibility
- Vulnerability to provider changes

**Verdict**: ❌ **Not Recommended** - Too risky long-term

#### Alternative 2: Direct API Only (No CLI)

**Pros**:
- Simpler implementation
- Better performance (no subprocess)
- More control

**Cons**:
- Loses Claude Code's tooling
- Must reimplement tool execution
- More development effort

**Verdict**: ⚠️ **Partial Solution** - Good as one provider option, not exclusive

#### Alternative 3: OpenCode Only (Replace Claude Code)

**Pros**:
- Open source
- Multi-provider built-in
- Active community

**Cons**:
- Risky migration (all eggs in one basket)
- OpenCode maturity unknown
- May not support all GAO-Dev features

**Verdict**: ❌ **Too Risky** - OpenCode unproven for our use case

#### Alternative 4: Provider Abstraction (Recommended)

**Pros**:
- Best of all worlds
- Backward compatible
- Future-proof
- Flexible

**Cons**:
- Development effort
- Additional complexity

**Verdict**: ✅ **RECOMMENDED** - Balances risk and reward

---

## Appendix

### A. Current File Dependencies

Files that reference Claude/Anthropic:

```
gao_dev/core/services/process_executor.py (CRITICAL)
gao_dev/agents/claude_agent.py (model name only)
gao_dev/core/cli_detector.py (CLI detection)
gao_dev/config/agents/*.yaml (model names)
```

### B. Provider Feature Matrix

| Feature | Claude Code | OpenCode | Direct API |
|---------|-------------|----------|------------|
| **Subprocess Execution** | ✅ Yes | ✅ Yes | ❌ No (HTTP) |
| **Multi-Provider** | ❌ No | ✅ Yes | Varies |
| **LSP Support** | ❓ Unknown | ✅ Yes | ❌ No |
| **Tool Execution** | ✅ Yes | ✅ Yes | ⚠️ Limited |
| **Streaming** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Cost** | Anthropic API | Varies | Varies |
| **Maturity** | High | Medium | High |
| **License** | Proprietary | MIT | Varies |

### C. Model Name Mapping Reference

```yaml
# Canonical model names (provider-agnostic)
canonical_models:
  - sonnet-4.5
  - sonnet-3.5
  - opus-3
  - gpt-4
  - gpt-4-turbo
  - gemini-pro
  - gemini-ultra

# Provider-specific translations
providers:
  claude-code:
    sonnet-4.5: "claude-sonnet-4-5-20250929"
    sonnet-3.5: "claude-sonnet-3-5-20241022"
    opus-3: "claude-opus-3-20250219"

  opencode:
    sonnet-4.5: "anthropic/claude-sonnet-4.5"
    gpt-4: "openai/gpt-4"
    gemini-pro: "google/gemini-pro"

  direct-api:
    sonnet-4.5: "claude-sonnet-4-5-20250929"
    gpt-4: "gpt-4-0125-preview"
    gemini-pro: "models/gemini-pro"
```

### D. Environment Variable Mapping

```bash
# Claude Code
ANTHROPIC_API_KEY=sk-ant-...

# OpenCode (varies by provider)
ANTHROPIC_API_KEY=sk-ant-...  # For Anthropic models
OPENAI_API_KEY=sk-...         # For OpenAI models
GOOGLE_API_KEY=...            # For Google models

# Direct API (varies by provider)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
```

### E. Estimated Costs

#### Development Cost

- **Phase 1**: 5 days × 8 hours = 40 hours
- **Phase 2**: 5 days × 8 hours = 40 hours
- **Phase 3**: 5 days × 8 hours = 40 hours
- **Phase 4**: 5 days × 8 hours = 40 hours
- **Total**: 160 hours (~4 weeks)

#### Ongoing Maintenance Cost

- **Provider updates**: ~2 hours/month
- **Bug fixes**: ~4 hours/month
- **Documentation updates**: ~1 hour/month
- **Total**: ~7 hours/month

#### ROI Calculation

**Benefits** (Quantitative):
- Reduced vendor lock-in risk: **High value**
- Cost optimization potential: **$100-500/month** (vary by usage)
- Performance improvements: **10-30% faster** (Direct API)

**Conclusion**: ROI positive within 6 months

---

## Next Steps

### Immediate Actions

1. **Stakeholder Review** (This Document)
   - Review architecture proposal
   - Approve implementation plan
   - Prioritize phases

2. **OpenCode Feasibility Test** (1-2 days)
   - Install OpenCode locally
   - Test basic execution
   - Validate compatibility with GAO-Dev use cases
   - Document findings

3. **Create Epic/Stories** (1 day)
   - Epic 11: Multi-Provider Agent Abstraction
   - Stories for each phase
   - Add to backlog

### Decision Points

**Go/No-Go Criteria**:

1. ✅ OpenCode CLI can execute basic coding tasks
2. ✅ OpenCode output is parseable and usable
3. ✅ OpenCode supports required tools (Read, Write, Edit, Bash)
4. ✅ Performance is acceptable (within 2x of Claude Code)

**If Go**:
- Proceed with Phase 1 implementation
- Target completion: 4 weeks from start

**If No-Go**:
- Re-evaluate alternatives
- Consider Direct API only approach
- Maintain status quo with risk mitigation plan

---

## Conclusion

GAO-Dev is **well-positioned** for provider abstraction due to excellent existing architecture:

- ✅ Clean IAgent interface (already provider-agnostic)
- ✅ Service layer separation (ProcessExecutor is isolated)
- ✅ YAML configuration (externalized model names)
- ✅ Factory pattern (centralized agent creation)

**Recommendation**: **PROCEED** with provider abstraction implementation.

**Rationale**:
1. **Low risk** - Only 1 critical coupling point (ProcessExecutor)
2. **High value** - Eliminates vendor lock-in, enables flexibility
3. **Feasible** - 4 weeks development time, manageable complexity
4. **Future-proof** - Positions GAO-Dev as truly provider-agnostic system

**Next Step**: Conduct OpenCode feasibility test to validate assumptions.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-04
**Author**: Claude (GAO-Dev Analysis)
**Status**: Awaiting Stakeholder Review
