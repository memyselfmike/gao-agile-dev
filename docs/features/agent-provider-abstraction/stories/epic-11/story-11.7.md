# Story 11.7: Implement OpenCodeProvider

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P1 (High)
**Estimated Effort**: 13 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-04
**Dependencies**: Story 11.1 (Provider Interface), Story 11.6 (OpenCode Research)

---

## User Story

**As a** GAO-Dev user
**I want** OpenCodeProvider that supports multiple AI backends
**So that** I can use OpenAI, Google, or Anthropic through OpenCode

---

## Acceptance Criteria

### AC1: OpenCodeProvider Class Implemented
- ✅ `OpenCodeProvider` class created in `opencode.py`
- ✅ Implements `IAgentProvider` interface completely
- ✅ All abstract methods implemented
- ✅ Type hints complete
- ✅ Comprehensive docstring

### AC2: Multi-Provider Support
- ✅ Supports Anthropic provider
- ✅ Supports OpenAI provider
- ✅ Supports Google provider
- ✅ Provider selection via constructor or config
- ✅ Provider-specific API key handling

### AC3: CLI Invocation
- ✅ Builds correct OpenCode CLI command
- ✅ Correct flags for provider selection
- ✅ Correct flags for model specification
- ✅ Working directory set correctly
- ✅ Environment variables set correctly

### AC4: Model Name Translation
- ✅ `MODEL_MAPPING` for each AI provider
- ✅ Canonical names map to OpenCode format
- ✅ `translate_model_name()` handles all providers
- ✅ `get_supported_models()` returns provider-specific models
- ✅ Unsupported model raises clear error

### AC5: Tool Support
- ✅ `TOOL_MAPPING` from GAO-Dev to OpenCode
- ✅ `supports_tool()` checks OpenCode capabilities
- ✅ Tool mapping based on research (Story 11.6)
- ✅ Graceful handling of unsupported tools

### AC6: Output Parsing
- ✅ Parses OpenCode streaming output correctly
- ✅ Handles progress indicators
- ✅ Yields results as strings
- ✅ Compatible with existing GAO-Dev expectations

### AC7: Error Handling
- ✅ CLI not found raises clear error
- ✅ Provider not supported raises clear error
- ✅ API key missing raises clear error
- ✅ Timeout handling works
- ✅ Non-zero exit code handled
- ✅ Error messages include provider context

### AC8: Configuration Validation
- ✅ `validate_configuration()` checks:
  - OpenCode CLI exists
  - API key set for selected provider
  - Provider is valid
- ✅ Returns bool, logs warnings
- ✅ `get_configuration_schema()` returns provider-specific schema

### AC9: CLI Auto-Detection
- ✅ Auto-detects OpenCode CLI if not provided
- ✅ Searches common installation paths
- ✅ Platform-specific detection (Windows, Mac, Linux)

### AC10: Windows Compatibility
- ✅ Subprocess encoding set to 'utf-8'
- ✅ Path handling works on Windows
- ✅ Bun/OpenCode works on Windows

### AC11: Testing Comprehensive
- ✅ Unit tests in `tests/core/providers/test_opencode.py`
- ✅ Integration tests (if API keys available)
- ✅ Test coverage >90%
- ✅ All providers tested (mock if no API keys)
- ✅ Error scenarios tested
- ✅ Timeout scenarios tested

### AC12: Performance Acceptable
- ✅ Performance within 2x of ClaudeCodeProvider
- ✅ No memory leaks
- ✅ Subprocess cleanup correct

---

## Technical Details

### File Structure
```
gao_dev/core/providers/
├── opencode.py                     # OpenCodeProvider implementation
└── opencode_detector.py            # CLI detection (optional)

tests/core/providers/
└── test_opencode.py                # Unit tests

tests/integration/
└── test_opencode_integration.py    # Integration tests
```

### Implementation Approach

#### Step 1: Create OpenCodeProvider Class

**File**: `gao_dev/core/providers/opencode.py`

```python
"""OpenCode CLI provider implementation."""

from pathlib import Path
from typing import AsyncGenerator, List, Dict, Optional
import subprocess
import os
import structlog

from .base import IAgentProvider
from .models import AgentContext
from .exceptions import (
    ProviderExecutionError,
    ProviderTimeoutError,
    ProviderConfigurationError,
    ModelNotSupportedError
)

logger = structlog.get_logger()


class OpenCodeProvider(IAgentProvider):
    """
    Provider for OpenCode CLI execution with multi-AI-provider support.

    OpenCode is an open-source AI coding agent that supports multiple
    AI providers (Anthropic, OpenAI, Google) through a unified interface.

    Execution Model: Subprocess (OpenCode CLI)
    Backend: Multiple (Anthropic, OpenAI, Google, local)

    Example:
        ```python
        # Use with Anthropic
        provider = OpenCodeProvider(ai_provider="anthropic")

        # Use with OpenAI
        provider = OpenCodeProvider(ai_provider="openai")

        async for result in provider.execute_task(
            task="Write a hello world script",
            context=AgentContext(project_root=Path("/project")),
            model="sonnet-4.5",  # or "gpt-4" for OpenAI
            tools=["Read", "Write", "Bash"],
            timeout=3600
        ):
            print(result)
        ```
    """

    # Tool mapping: GAO-Dev tool name → OpenCode tool name
    # NOTE: Based on research from Story 11.6
    TOOL_MAPPING = {
        "Read": "read",
        "Write": "write",
        "Edit": "edit",
        "Bash": "bash",
        "Grep": "grep",
        "Glob": "glob",
        # Add more based on OpenCode research
    }

    # Model translation per AI provider
    # Canonical → OpenCode format
    MODEL_MAPPING = {
        "anthropic": {
            "sonnet-4.5": "anthropic/claude-sonnet-4.5",
            "sonnet-3.5": "anthropic/claude-sonnet-3.5",
            "opus-3": "anthropic/claude-opus-3",
            "haiku-3": "anthropic/claude-haiku-3",
        },
        "openai": {
            "gpt-4": "openai/gpt-4",
            "gpt-4-turbo": "openai/gpt-4-turbo-preview",
            "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
        },
        "google": {
            "gemini-pro": "google/gemini-pro",
            "gemini-ultra": "google/gemini-ultra",
        }
    }

    # API key environment variables per provider
    API_KEY_ENV_VARS = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
    }

    DEFAULT_TIMEOUT = 3600  # 1 hour

    def __init__(
        self,
        cli_path: Optional[Path] = None,
        ai_provider: str = "anthropic",
        api_key: Optional[str] = None
    ):
        """
        Initialize OpenCode provider.

        Args:
            cli_path: Path to OpenCode CLI (auto-detected if None)
            ai_provider: AI provider to use (anthropic, openai, google)
            api_key: API key (uses env var if None)
        """
        self.cli_path = cli_path or self._detect_opencode_cli()
        self.ai_provider = ai_provider.lower()

        # Get API key from parameter or environment
        if api_key:
            self.api_key = api_key
        else:
            env_var = self.API_KEY_ENV_VARS.get(self.ai_provider)
            self.api_key = os.getenv(env_var) if env_var else None

        self._initialized = False

        logger.info(
            "opencode_provider_initialized",
            has_cli_path=self.cli_path is not None,
            ai_provider=self.ai_provider,
            has_api_key=bool(self.api_key),
            cli_path=str(self.cli_path) if self.cli_path else None
        )

    @property
    def name(self) -> str:
        """Provider name."""
        return "opencode"

    @property
    def version(self) -> str:
        """Provider version."""
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
        """
        Execute task via OpenCode CLI.

        Args:
            task: Task description/prompt
            context: Execution context
            model: Canonical model name
            tools: List of tool names
            timeout: Timeout in seconds
            **kwargs: Additional arguments (ignored)

        Yields:
            Output from OpenCode CLI

        Raises:
            ProviderExecutionError: If execution fails
            ProviderTimeoutError: If execution times out
            ProviderConfigurationError: If not configured
        """
        if not self.cli_path:
            raise ProviderConfigurationError(
                "OpenCode CLI not found. Install OpenCode or set cli_path. "
                "See: docs/opencode-setup-guide.md"
            )

        # Translate model name
        model_id = self.translate_model_name(model)

        # Build command
        # NOTE: Adjust based on OpenCode research (Story 11.6)
        cmd = [str(self.cli_path)]
        cmd.extend(['--provider', self.ai_provider])
        cmd.extend(['--model', model_id])
        cmd.extend(['--cwd', str(context.project_root)])
        # Add other flags as needed

        # Set environment
        env = os.environ.copy()
        if self.api_key:
            env_var = self.API_KEY_ENV_VARS.get(self.ai_provider)
            if env_var:
                env[env_var] = self.api_key

        # Log execution
        logger.info(
            "executing_opencode_cli",
            ai_provider=self.ai_provider,
            model=model_id,
            tools=tools,
            timeout=timeout or self.DEFAULT_TIMEOUT,
            project_root=str(context.project_root)
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
                "opencode_cli_completed",
                return_code=process.returncode,
                ai_provider=self.ai_provider,
                stdout_length=len(stdout) if stdout else 0,
                stderr_length=len(stderr) if stderr else 0
            )

            if stderr:
                logger.warning("opencode_cli_stderr", stderr=stderr[:1000])

            # Yield output
            if stdout:
                yield stdout

            # Check exit code
            if process.returncode != 0:
                error_msg = f"OpenCode CLI failed with exit code {process.returncode}"
                if stderr:
                    error_msg += f": {stderr[:500]}"

                logger.error(
                    "opencode_cli_execution_failed",
                    exit_code=process.returncode,
                    error=error_msg
                )
                raise ProviderExecutionError(error_msg, provider_name=self.name)

        except subprocess.TimeoutExpired:
            process.kill()
            logger.error(
                "opencode_cli_timeout",
                timeout=timeout or self.DEFAULT_TIMEOUT,
                task_preview=task[:100]
            )
            raise ProviderTimeoutError(
                f"Execution timed out after {timeout or self.DEFAULT_TIMEOUT} seconds",
                provider_name=self.name
            )

        except ProviderExecutionError:
            raise

        except Exception as e:
            logger.error(
                "opencode_cli_execution_error",
                error=str(e),
                exc_info=True
            )
            raise ProviderExecutionError(
                f"Process execution failed: {str(e)}",
                provider_name=self.name
            ) from e

    def supports_tool(self, tool_name: str) -> bool:
        """Check if OpenCode supports this tool."""
        return tool_name in self.TOOL_MAPPING

    def get_supported_models(self) -> List[str]:
        """Get supported models for current AI provider."""
        provider_models = self.MODEL_MAPPING.get(self.ai_provider, {})
        return list(provider_models.keys())

    def translate_model_name(self, canonical_name: str) -> str:
        """
        Translate canonical name to OpenCode model ID.

        Args:
            canonical_name: Canonical model name

        Returns:
            OpenCode-specific model ID

        Raises:
            ModelNotSupportedError: If model not supported
        """
        provider_models = self.MODEL_MAPPING.get(self.ai_provider, {})

        if canonical_name not in provider_models:
            supported = list(provider_models.keys())
            raise ModelNotSupportedError(canonical_name, self.name)

        translated = provider_models[canonical_name]

        logger.debug(
            "model_name_translated",
            canonical=canonical_name,
            translated=translated,
            ai_provider=self.ai_provider
        )

        return translated

    async def validate_configuration(self) -> bool:
        """
        Validate OpenCode configuration.

        Checks:
        - CLI executable exists
        - AI provider is valid
        - API key is set

        Returns:
            True if valid, False otherwise
        """
        is_valid = True

        # Check CLI
        if not self.cli_path or not self.cli_path.exists():
            logger.warning(
                "opencode_cli_not_found",
                cli_path=str(self.cli_path) if self.cli_path else None
            )
            is_valid = False

        # Check provider
        if self.ai_provider not in self.MODEL_MAPPING:
            logger.warning(
                "invalid_ai_provider",
                ai_provider=self.ai_provider,
                valid_providers=list(self.MODEL_MAPPING.keys())
            )
            is_valid = False

        # Check API key
        if not self.api_key:
            env_var = self.API_KEY_ENV_VARS.get(self.ai_provider)
            logger.warning(
                "api_key_not_set",
                ai_provider=self.ai_provider,
                env_var=env_var
            )
            is_valid = False

        logger.info(
            "opencode_configuration_validated",
            is_valid=is_valid,
            ai_provider=self.ai_provider
        )

        return is_valid

    def get_configuration_schema(self) -> Dict:
        """Get configuration schema for OpenCode."""
        return {
            "type": "object",
            "properties": {
                "cli_path": {
                    "type": "string",
                    "description": "Path to OpenCode CLI executable"
                },
                "ai_provider": {
                    "type": "string",
                    "enum": ["anthropic", "openai", "google"],
                    "description": "AI provider to use"
                },
                "api_key": {
                    "type": "string",
                    "description": "API key for the AI provider"
                }
            },
            "required": ["ai_provider"]
        }

    async def initialize(self) -> None:
        """Initialize provider."""
        self._initialized = True
        logger.debug("opencode_provider_initialized")

    async def cleanup(self) -> None:
        """Cleanup provider."""
        self._initialized = False
        logger.debug("opencode_provider_cleaned_up")

    def _detect_opencode_cli(self) -> Optional[Path]:
        """
        Auto-detect OpenCode CLI installation.

        Searches common installation paths for opencode executable.

        Returns:
            Path to OpenCode CLI if found, None otherwise
        """
        # Common installation paths
        search_paths = [
            Path.home() / ".bun" / "bin" / "opencode",
            Path("/usr/local/bin/opencode"),
            Path("/usr/bin/opencode"),
        ]

        # Windows paths
        if os.name == 'nt':
            search_paths.extend([
                Path(os.environ.get("LOCALAPPDATA", "")) / "bun" / "bin" / "opencode.exe",
                Path("C:/Program Files/opencode/opencode.exe"),
            ])

        for path in search_paths:
            if path.exists():
                logger.info("opencode_cli_detected", path=str(path))
                return path

        logger.warning("opencode_cli_not_detected")
        return None

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"OpenCodeProvider("
            f"ai_provider={self.ai_provider}, "
            f"has_api_key={bool(self.api_key)})"
        )
```

#### Step 2: Update ProviderFactory

**File**: `gao_dev/core/providers/factory.py`

```python
# Add OpenCodeProvider to built-in providers

from .opencode import OpenCodeProvider

def _register_builtin_providers(self) -> None:
    """Register all built-in providers."""
    builtin_providers = {
        "claude-code": ClaudeCodeProvider,
        "opencode": OpenCodeProvider,  # NEW
        # "direct-api": DirectAPIProvider,  # Future
    }
    # ... rest of method
```

#### Step 3: Write Comprehensive Tests

**File**: `tests/core/providers/test_opencode.py`

```python
"""Unit tests for OpenCodeProvider."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

from gao_dev.core.providers.opencode import OpenCodeProvider
from gao_dev.core.providers.models import AgentContext
from gao_dev.core.providers.exceptions import (
    ProviderExecutionError,
    ProviderTimeoutError,
    ModelNotSupportedError
)


class TestOpenCodeProvider:
    """Test OpenCodeProvider implementation."""

    def test_provider_name(self):
        """Test provider name."""
        provider = OpenCodeProvider()
        assert provider.name == "opencode"

    def test_provider_version(self):
        """Test provider version."""
        provider = OpenCodeProvider()
        assert provider.version == "1.0.0"

    def test_model_translation_anthropic(self):
        """Test model translation for Anthropic."""
        provider = OpenCodeProvider(ai_provider="anthropic")

        assert provider.translate_model_name("sonnet-4.5") == "anthropic/claude-sonnet-4.5"
        assert provider.translate_model_name("opus-3") == "anthropic/claude-opus-3"

    def test_model_translation_openai(self):
        """Test model translation for OpenAI."""
        provider = OpenCodeProvider(ai_provider="openai")

        assert provider.translate_model_name("gpt-4") == "openai/gpt-4"
        assert provider.translate_model_name("gpt-4-turbo") == "openai/gpt-4-turbo-preview"

    def test_model_not_supported_raises_error(self):
        """Test unsupported model raises error."""
        provider = OpenCodeProvider(ai_provider="anthropic")

        with pytest.raises(ModelNotSupportedError):
            provider.translate_model_name("gpt-4")  # OpenAI model on Anthropic provider

    def test_get_supported_models_anthropic(self):
        """Test getting supported models for Anthropic."""
        provider = OpenCodeProvider(ai_provider="anthropic")
        models = provider.get_supported_models()

        assert "sonnet-4.5" in models
        assert "opus-3" in models
        assert "gpt-4" not in models

    def test_get_supported_models_openai(self):
        """Test getting supported models for OpenAI."""
        provider = OpenCodeProvider(ai_provider="openai")
        models = provider.get_supported_models()

        assert "gpt-4" in models
        assert "gpt-4-turbo" in models
        assert "sonnet-4.5" not in models

    @pytest.mark.asyncio
    async def test_validate_configuration_valid(self):
        """Test configuration validation when valid."""
        with patch.object(Path, 'exists', return_value=True):
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                ai_provider="anthropic",
                api_key="test-key"
            )
            is_valid = await provider.validate_configuration()
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_configuration_no_cli(self):
        """Test configuration validation when CLI missing."""
        provider = OpenCodeProvider(cli_path=None, api_key="test")
        is_valid = await provider.validate_configuration()
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_configuration_invalid_provider(self):
        """Test configuration validation with invalid provider."""
        with patch.object(Path, 'exists', return_value=True):
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                ai_provider="invalid",
                api_key="test"
            )
            is_valid = await provider.validate_configuration()
            assert is_valid is False


@pytest.mark.integration
@pytest.mark.asyncio
class TestOpenCodeProviderIntegration:
    """Integration tests for OpenCodeProvider."""

    async def test_execute_task_anthropic(self, tmp_path):
        """Test task execution with Anthropic."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Task completed", "")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                ai_provider="anthropic",
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            results = []
            async for result in provider.execute_task(
                task="Test task",
                context=context,
                model="sonnet-4.5",
                tools=["Read", "Write"],
                timeout=60
            ):
                results.append(result)

            assert len(results) > 0
            assert "Task completed" in results[0]

    async def test_execute_task_timeout(self, tmp_path):
        """Test task execution timeout."""
        mock_process = Mock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired("cmd", 60)

        with patch('subprocess.Popen', return_value=mock_process):
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                ai_provider="anthropic",
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            with pytest.raises(ProviderTimeoutError):
                async for _ in provider.execute_task(
                    task="Test task",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=1
                ):
                    pass
```

---

## Testing Strategy

### Unit Tests
- Provider properties
- Model translation (all AI providers)
- Tool support checking
- Configuration validation
- CLI detection

### Integration Tests
- Task execution (mocked subprocess)
- Multiple AI providers
- Timeout handling
- Error handling

### Manual Testing (if API keys available)
- Real Anthropic execution
- Real OpenAI execution
- Real Google execution

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] OpenCodeProvider works with Anthropic
- [ ] OpenCodeProvider works with OpenAI (if tested)
- [ ] Code reviewed and approved
- [ ] Unit tests passing (>90% coverage)
- [ ] Integration tests passing
- [ ] Type checking passing (mypy strict)
- [ ] Performance acceptable (<2x ClaudeCode)
- [ ] Documentation complete
- [ ] Changes committed
- [ ] Story marked complete

---

## Dependencies

**Upstream**:
- Story 11.1 (Provider Interface) - MUST be complete
- Story 11.6 (OpenCode Research) - MUST be complete

**Downstream**:
- Story 11.8 (Provider Comparison) - needs OpenCodeProvider
- Story 11.11 (Provider Selection) - benefits from OpenCodeProvider

---

## Notes

- Implementation depends on Story 11.6 findings
- If Story 11.6 is NO-GO, skip this story
- Multi-provider support is key differentiator
- CLI detection important for user experience
- Error messages must be clear about which AI provider failed

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
- Story 11.6: `story-11.6.md` (OpenCode Research)
- OpenCode Setup Guide: `docs/opencode-setup-guide.md` (from Story 11.6)
