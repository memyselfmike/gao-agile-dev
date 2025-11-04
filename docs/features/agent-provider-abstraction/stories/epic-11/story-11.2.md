# Story 11.2: Implement ClaudeCodeProvider

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P0 (Critical)
**Estimated Effort**: 13 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-04
**Dependencies**: Story 11.1 (Provider Interface)

---

## User Story

**As a** GAO-Dev developer
**I want** ClaudeCodeProvider to extract and encapsulate current ProcessExecutor behavior
**So that** Claude Code execution works identically while conforming to the provider abstraction

---

## Acceptance Criteria

### AC1: ClaudeCodeProvider Class Implemented
- ✅ `ClaudeCodeProvider` class created in `claude_code.py`
- ✅ Implements `IAgentProvider` interface completely
- ✅ All abstract methods implemented with proper signatures
- ✅ Type hints complete and correct
- ✅ Class docstring comprehensive

### AC2: Subprocess Logic Extracted
- ✅ All subprocess execution logic moved from `ProcessExecutor`
- ✅ CLI command building identical to current implementation
- ✅ Exact same CLI flags preserved:
  - `--print`
  - `--dangerously-skip-permissions`
  - `--model`
  - `--add-dir`
- ✅ Environment variable handling identical
- ✅ Timeout handling preserved
- ✅ Error handling matches current behavior

### AC3: Model Name Translation
- ✅ `MODEL_MAPPING` dictionary defined with canonical → Claude translations:
  - `"sonnet-4.5"` → `"claude-sonnet-4-5-20250929"`
  - `"sonnet-3.5"` → `"claude-sonnet-3-5-20241022"`
  - `"opus-3"` → `"claude-opus-3-20250219"`
- ✅ Passthrough for full model IDs
- ✅ `translate_model_name()` method implemented
- ✅ `get_supported_models()` returns canonical names

### AC4: Tool Support Checking
- ✅ `TOOL_MAPPING` dictionary defined (GAO-Dev → Claude Code tools)
- ✅ `supports_tool()` method implemented
- ✅ All standard tools mapped correctly

### AC5: Configuration Validation
- ✅ `validate_configuration()` checks:
  - CLI path exists
  - API key is set (ANTHROPIC_API_KEY)
- ✅ Returns bool (not raising exceptions)
- ✅ Logs warnings for configuration issues
- ✅ `get_configuration_schema()` returns valid JSON Schema

### AC6: CLI Auto-Detection
- ✅ Uses `detect_claude_cli()` from `cli_detector.py`
- ✅ Constructor accepts optional `cli_path`
- ✅ Auto-detects if not provided
- ✅ Stores API key from env or constructor

### AC7: Initialization & Cleanup
- ✅ `initialize()` method implemented (can be no-op for CLI)
- ✅ `cleanup()` method implemented
- ✅ Lifecycle management clear

### AC8: Error Handling Identical
- ✅ Subprocess timeout raises `ProviderTimeoutError`
- ✅ Non-zero exit code raises `ProviderExecutionError`
- ✅ CLI not found raises clear error
- ✅ API key missing logged as warning
- ✅ All error messages match current format

### AC9: Logging Complete
- ✅ Uses structlog consistently
- ✅ Logs execution start, completion, errors
- ✅ Log format matches current ProcessExecutor
- ✅ No sensitive data logged (API keys masked)

### AC10: Windows Compatibility
- ✅ Subprocess encoding set to 'utf-8'
- ✅ Error handling with `errors='replace'`
- ✅ Path handling works on Windows

### AC11: Testing Comprehensive
- ✅ Unit tests in `tests/core/providers/test_claude_code.py`
- ✅ Integration tests in `tests/integration/test_claude_code_integration.py`
- ✅ Test coverage >90%
- ✅ All edge cases tested:
  - Timeout scenarios
  - Error scenarios
  - Model translation
  - Tool support checking
  - Configuration validation

### AC12: Performance Validation
- ✅ Performance within 5% of current ProcessExecutor
- ✅ No memory leaks
- ✅ Subprocess cleanup correct

---

## Technical Details

### File Structure
```
gao_dev/core/providers/
└── claude_code.py              # ClaudeCodeProvider implementation

tests/core/providers/
└── test_claude_code.py         # Unit tests

tests/integration/
└── test_claude_code_integration.py  # Integration tests
```

### Implementation Approach

#### Step 1: Create ClaudeCodeProvider Class

**File**: `gao_dev/core/providers/claude_code.py`

```python
"""Claude Code CLI provider implementation."""

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
    ProviderConfigurationError
)
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

    Example:
        ```python
        provider = ClaudeCodeProvider()

        if await provider.validate_configuration():
            async for result in provider.execute_task(
                task="Write a hello world script",
                context=AgentContext(project_root=Path("/project")),
                model="sonnet-4.5",
                tools=["Read", "Write", "Bash"],
                timeout=3600
            ):
                print(result)
        ```
    """

    # Tool mapping: GAO-Dev tool name → Claude Code tool name
    TOOL_MAPPING = {
        "Read": "read",
        "Write": "write",
        "Edit": "edit",
        "MultiEdit": "multiedit",
        "Bash": "bash",
        "Grep": "grep",
        "Glob": "glob",
        "Task": "task",
        "WebFetch": "webfetch",
        "WebSearch": "websearch",
        "TodoWrite": "todowrite",
        "AskUserQuestion": "askuserquestion",
    }

    # Model translation: Canonical → Claude-specific
    MODEL_MAPPING = {
        # Canonical names
        "sonnet-4.5": "claude-sonnet-4-5-20250929",
        "sonnet-3.5": "claude-sonnet-3-5-20241022",
        "opus-3": "claude-opus-3-20250219",
        "haiku-3": "claude-haiku-3-20250219",

        # Passthrough for full model IDs
        "claude-sonnet-4-5-20250929": "claude-sonnet-4-5-20250929",
        "claude-sonnet-3-5-20241022": "claude-sonnet-3-5-20241022",
        "claude-opus-3-20250219": "claude-opus-3-20250219",
        "claude-haiku-3-20250219": "claude-haiku-3-20250219",
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
            has_api_key=bool(self.api_key),
            cli_path=str(self.cli_path) if self.cli_path else None
        )

    @property
    def name(self) -> str:
        """Provider name."""
        return "claude-code"

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
        Execute task via Claude Code CLI.

        Args:
            task: Task description/prompt
            context: Execution context
            model: Canonical model name
            tools: List of tool names
            timeout: Timeout in seconds
            **kwargs: Additional arguments (ignored)

        Yields:
            Output from Claude CLI

        Raises:
            ProviderExecutionError: If execution fails
            ProviderTimeoutError: If execution times out
            ProviderConfigurationError: If not configured
        """
        if not self.cli_path:
            raise ProviderConfigurationError(
                "Claude CLI not found. Install Claude Code or set cli_path."
            )

        # Translate model name
        model_id = self.translate_model_name(model)

        # Build command (exact same flags as original ProcessExecutor)
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
            timeout=timeout or self.DEFAULT_TIMEOUT,
            project_root=str(context.project_root)
        )

        try:
            # Execute subprocess (exact same as ProcessExecutor)
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
                stderr_length=len(stderr) if stderr else 0,
                stdout_preview=stdout[:200] if stdout else "(empty)",
                stderr_preview=stderr[:200] if stderr else "(empty)"
            )

            # Log stderr if present
            if stderr:
                logger.warning("claude_cli_stderr", stderr=stderr[:1000])

            # Yield output
            if stdout:
                yield stdout

            # Check exit code
            if process.returncode != 0:
                error_msg = f"Claude CLI failed with exit code {process.returncode}"
                if stderr:
                    error_msg += f": {stderr[:500]}"
                if not stdout and not stderr:
                    error_msg += " (no output - check if claude.bat is configured correctly)"

                logger.error(
                    "claude_cli_execution_failed",
                    exit_code=process.returncode,
                    error=error_msg
                )
                raise ProviderExecutionError(error_msg, provider_name=self.name)

        except subprocess.TimeoutExpired:
            process.kill()
            logger.error(
                "claude_cli_timeout",
                timeout=timeout or self.DEFAULT_TIMEOUT,
                task_preview=task[:100]
            )
            raise ProviderTimeoutError(
                f"Execution timed out after {timeout or self.DEFAULT_TIMEOUT} seconds",
                provider_name=self.name
            )

        except ProviderExecutionError:
            # Re-raise our own exceptions
            raise

        except Exception as e:
            logger.error(
                "claude_cli_execution_error",
                error=str(e),
                exc_info=True
            )
            raise ProviderExecutionError(
                f"Process execution failed: {str(e)}",
                provider_name=self.name
            ) from e

    def supports_tool(self, tool_name: str) -> bool:
        """Check if Claude Code supports this tool."""
        return tool_name in self.TOOL_MAPPING

    def get_supported_models(self) -> List[str]:
        """Get supported Claude models (canonical names only)."""
        # Return only canonical names, not full IDs
        return ["sonnet-4.5", "sonnet-3.5", "opus-3", "haiku-3"]

    def translate_model_name(self, canonical_name: str) -> str:
        """
        Translate canonical name to Claude model ID.

        Args:
            canonical_name: Canonical model name

        Returns:
            Claude-specific model ID

        Raises:
            ModelNotSupportedError: If model not in mapping
        """
        # Try mapping, fallback to passthrough
        translated = self.MODEL_MAPPING.get(canonical_name, canonical_name)

        logger.debug(
            "model_name_translated",
            canonical=canonical_name,
            translated=translated
        )

        return translated

    async def validate_configuration(self) -> bool:
        """
        Validate Claude Code configuration.

        Checks:
        - CLI executable exists
        - API key is set

        Returns:
            True if valid, False otherwise
        """
        is_valid = True

        if not self.cli_path or not self.cli_path.exists():
            logger.warning(
                "claude_cli_not_found",
                cli_path=str(self.cli_path) if self.cli_path else None
            )
            is_valid = False

        if not self.api_key:
            logger.warning("anthropic_api_key_not_set")
            is_valid = False

        logger.info(
            "claude_code_configuration_validated",
            is_valid=is_valid
        )

        return is_valid

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
        """Initialize provider (no-op for CLI provider)."""
        self._initialized = True
        logger.debug("claude_code_provider_initialized")

    async def cleanup(self) -> None:
        """Cleanup provider (no-op for CLI provider)."""
        self._initialized = False
        logger.debug("claude_code_provider_cleaned_up")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ClaudeCodeProvider("
            f"cli_path={self.cli_path}, "
            f"has_api_key={bool(self.api_key)})"
        )
```

#### Step 2: Write Comprehensive Unit Tests

**File**: `tests/core/providers/test_claude_code.py`

```python
"""Unit tests for ClaudeCodeProvider."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import subprocess

from gao_dev.core.providers.claude_code import ClaudeCodeProvider
from gao_dev.core.providers.models import AgentContext
from gao_dev.core.providers.exceptions import (
    ProviderExecutionError,
    ProviderTimeoutError,
    ProviderConfigurationError
)


class TestClaudeCodeProvider:
    """Test ClaudeCodeProvider implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = ClaudeCodeProvider(
            cli_path=Path("/usr/bin/claude"),
            api_key="test-key"
        )

    def test_provider_name(self):
        """Test provider name."""
        assert self.provider.name == "claude-code"

    def test_provider_version(self):
        """Test provider version."""
        assert self.provider.version == "1.0.0"

    def test_model_translation_canonical(self):
        """Test model name translation for canonical names."""
        assert self.provider.translate_model_name("sonnet-4.5") == "claude-sonnet-4-5-20250929"
        assert self.provider.translate_model_name("sonnet-3.5") == "claude-sonnet-3-5-20241022"
        assert self.provider.translate_model_name("opus-3") == "claude-opus-3-20250219"

    def test_model_translation_passthrough(self):
        """Test model name passthrough for full IDs."""
        full_id = "claude-sonnet-4-5-20250929"
        assert self.provider.translate_model_name(full_id) == full_id

    def test_supports_tool(self):
        """Test tool support checking."""
        assert self.provider.supports_tool("Read") is True
        assert self.provider.supports_tool("Write") is True
        assert self.provider.supports_tool("Bash") is True
        assert self.provider.supports_tool("NonExistentTool") is False

    def test_get_supported_models(self):
        """Test getting supported models."""
        models = self.provider.get_supported_models()
        assert "sonnet-4.5" in models
        assert "sonnet-3.5" in models
        assert "opus-3" in models

    @pytest.mark.asyncio
    async def test_validate_configuration_valid(self):
        """Test configuration validation when valid."""
        with patch.object(Path, 'exists', return_value=True):
            is_valid = await self.provider.validate_configuration()
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_configuration_no_cli(self):
        """Test configuration validation when CLI missing."""
        provider = ClaudeCodeProvider(cli_path=None, api_key="test")
        is_valid = await provider.validate_configuration()
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_configuration_no_api_key(self):
        """Test configuration validation when API key missing."""
        provider = ClaudeCodeProvider(cli_path=Path("/usr/bin/claude"), api_key=None)
        with patch.object(Path, 'exists', return_value=True):
            is_valid = await provider.validate_configuration()
            assert is_valid is False

    def test_configuration_schema(self):
        """Test configuration schema."""
        schema = self.provider.get_configuration_schema()
        assert schema["type"] == "object"
        assert "cli_path" in schema["properties"]
        assert "api_key" in schema["properties"]

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test provider initialization."""
        await self.provider.initialize()
        assert self.provider._initialized is True

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test provider cleanup."""
        await self.provider.initialize()
        await self.provider.cleanup()
        assert self.provider._initialized is False


@pytest.mark.integration
@pytest.mark.asyncio
class TestClaudeCodeProviderIntegration:
    """Integration tests for ClaudeCodeProvider."""

    async def test_execute_task_success(self, tmp_path):
        """Test successful task execution."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Task completed", "")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
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
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
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

    async def test_execute_task_failure(self, tmp_path):
        """Test task execution failure."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("", "Error occurred")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            with pytest.raises(ProviderExecutionError):
                async for _ in provider.execute_task(
                    task="Test task",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=60
                ):
                    pass
```

---

## Testing Strategy

### Unit Tests
- Provider properties (name, version)
- Model name translation (canonical and passthrough)
- Tool support checking
- Configuration validation (valid, no CLI, no key)
- Configuration schema
- Initialization and cleanup

### Integration Tests
- Successful task execution (mocked subprocess)
- Timeout handling
- Failure handling
- Command building
- Environment variable handling

### Performance Tests
- Compare with current ProcessExecutor
- Measure overhead (<5% target)
- Memory usage validation

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] ClaudeCodeProvider produces identical output to ProcessExecutor
- [ ] Code reviewed and approved
- [ ] Unit tests passing (>90% coverage)
- [ ] Integration tests passing
- [ ] Type checking passing (mypy strict)
- [ ] Performance within 5% of current implementation
- [ ] No linting errors (ruff)
- [ ] Documentation complete
- [ ] Changes committed with atomic commit
- [ ] Story marked complete in sprint-status.yaml

---

## Dependencies

**Upstream**:
- Story 11.1 (Provider Interface) - MUST be complete

**Downstream**:
- Story 11.3 (Provider Factory) - needs ClaudeCodeProvider class
- Story 11.4 (Refactor ProcessExecutor) - needs working ClaudeCodeProvider

---

## Notes

- **CRITICAL**: Must maintain 100% behavioral compatibility with ProcessExecutor
- This is extraction, not rewrite - preserve all edge case handling
- Windows compatibility essential (encoding, path handling)
- Performance must match current implementation
- All logging must match current format for backward compatibility
- API keys must never be logged (mask in all log statements)

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
- Epic Breakdown: `docs/features/agent-provider-abstraction/epics.md`
- Story 11.1: `story-11.1.md`
- Current Implementation: `gao_dev/core/services/process_executor.py` (reference)
