# Story 11.4: Refactor ProcessExecutor to Use Providers

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P0 (Critical)
**Estimated Effort**: 8 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-04
**Dependencies**: Story 11.2 (ClaudeCodeProvider), Story 11.3 (ProviderFactory)

---

## User Story

**As a** GAO-Dev user
**I want** ProcessExecutor to use provider abstraction internally
**So that** I can switch providers without changing my code while maintaining 100% backward compatibility

---

## Acceptance Criteria

### AC1: Constructor Updated with Provider Support
- ✅ Accepts `provider` instance parameter (takes precedence over other params)
- ✅ Accepts `provider_name` string parameter (default: "claude-code")
- ✅ Accepts `provider_config` dict parameter for provider-specific settings
- ✅ Legacy parameters (`cli_path`, `api_key`) still work
- ✅ Creates provider via ProviderFactory if not provided
- ✅ Type hints complete and correct

### AC2: Backward Compatibility Maintained
- ✅ Legacy constructor signature works identically:
  ```python
  ProcessExecutor(project_root, cli_path, api_key)
  ```
- ✅ Auto-creates ClaudeCodeProvider when legacy params used
- ✅ Logs deprecation warning for legacy usage
- ✅ All 400+ existing tests pass without modification
- ✅ No breaking changes to public API

### AC3: Execute Method Delegates to Provider
- ✅ `execute_agent_task()` delegates to `provider.execute_task()`
- ✅ Validates provider configuration before execution
- ✅ Creates `AgentContext` from project_root
- ✅ Passes model, tools, timeout to provider
- ✅ Returns AsyncGenerator[str, None] (same as before)
- ✅ Error handling preserved

### AC4: Provider Validation
- ✅ Calls `provider.validate_configuration()` before execution
- ✅ Raises clear `ValueError` if not configured
- ✅ Error message includes provider name
- ✅ Suggests configuration steps

### AC5: Logging Provider-Agnostic
- ✅ Logs include provider name
- ✅ Logs remain structlog format
- ✅ No Claude-specific terminology (e.g., "claude_cli_executing")
- ✅ Generic provider terminology (e.g., "executing_via_provider")
- ✅ Backward compatible log format

### AC6: Error Handling Preserved
- ✅ Provider exceptions bubble up correctly
- ✅ Timeout errors handled same as before
- ✅ Execution errors handled same as before
- ✅ Configuration errors clear

### AC7: New Constructor API Works
- ✅ Provider instance injection:
  ```python
  provider = ClaudeCodeProvider()
  executor = ProcessExecutor(project_root, provider=provider)
  ```
- ✅ Provider name with config:
  ```python
  executor = ProcessExecutor(
      project_root,
      provider_name="claude-code",
      provider_config={"api_key": "sk-..."}
  )
  ```
- ✅ Provider name only (uses defaults):
  ```python
  executor = ProcessExecutor(project_root, provider_name="claude-code")
  ```

### AC8: Testing Comprehensive
- ✅ All existing ProcessExecutor tests pass unchanged
- ✅ New tests for provider-based constructor
- ✅ New tests for provider injection
- ✅ Tests for backward compatibility
- ✅ Tests for provider validation
- ✅ Performance tests (within 5% of original)

### AC9: Documentation Updated
- ✅ ProcessExecutor docstring updated
- ✅ Constructor parameters documented
- ✅ Migration examples provided
- ✅ Deprecation warnings added to legacy usage

### AC10: Feature Flag Support (R1 - Winston's Recommendation)
- ✅ Reads `features.provider_abstraction_enabled` from config
- ✅ If `false`, uses legacy ProcessExecutor behavior (direct CLI calls)
- ✅ If `true`, uses provider abstraction system
- ✅ Defaults to `false` for safety (gradual rollout)
- ✅ Logs feature flag state on initialization
- ✅ Can override via environment variable: `GAO_PROVIDER_ABSTRACTION_ENABLED`

---

## Technical Details

### File Structure
```
gao_dev/core/services/
└── process_executor.py         # MODIFIED: Use provider abstraction

tests/core/services/
├── test_process_executor.py               # EXISTING: All pass unchanged
└── test_process_executor_providers.py     # NEW: Provider-specific tests

tests/integration/
└── test_process_executor_legacy.py        # NEW: Backward compat tests
```

### Implementation Approach

#### Step 1: Update ProcessExecutor Class

**File**: `gao_dev/core/services/process_executor.py`

```python
"""ProcessExecutor Service - Executes external processes via providers.

Refactored to use provider abstraction while maintaining 100% backward
compatibility with existing code.
"""

import structlog
from typing import AsyncGenerator, Optional, List, Dict
from pathlib import Path

from ..providers.factory import ProviderFactory
from ..providers.base import IAgentProvider
from ..providers.models import AgentContext

logger = structlog.get_logger()


class ProcessExecutor:
    """
    Executes agent tasks via configurable provider.

    Refactored to use provider abstraction while maintaining
    100% backward compatibility with existing code.

    New API (Recommended):
        ```python
        # Option 1: Provider instance injection
        provider = ClaudeCodeProvider()
        executor = ProcessExecutor(project_root, provider=provider)

        # Option 2: Provider name with config
        executor = ProcessExecutor(
            project_root,
            provider_name="opencode",
            provider_config={"ai_provider": "anthropic"}
        )

        # Option 3: Provider name only (uses defaults)
        executor = ProcessExecutor(project_root, provider_name="claude-code")
        ```

    Legacy API (Still Supported):
        ```python
        # Old constructor still works
        executor = ProcessExecutor(
            project_root=Path("/project"),
            cli_path=Path("/usr/bin/claude"),
            api_key="sk-ant-..."
        )
        ```
    """

    DEFAULT_TIMEOUT = 3600  # 1 hour

    def __init__(
        self,
        project_root: Path,
        provider: Optional[IAgentProvider] = None,
        provider_name: str = "claude-code",
        provider_config: Optional[Dict] = None,
        # Legacy parameters (deprecated but supported)
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
            ```python
            executor = ProcessExecutor(
                project_root=Path("/project"),
                provider_name="opencode",
                provider_config={"ai_provider": "anthropic"}
            )
            ```

        Example (Legacy API - still works):
            ```python
            executor = ProcessExecutor(
                project_root=Path("/project"),
                cli_path=Path("/usr/bin/claude"),
                api_key="sk-ant-..."
            )
            ```
        """
        self.project_root = project_root

        # R1: Check feature flag for provider abstraction
        self.provider_abstraction_enabled = self._check_feature_flag()

        if not self.provider_abstraction_enabled:
            logger.info(
                "provider_abstraction_disabled",
                message="Provider abstraction is disabled. Using legacy behavior."
            )
            # Use legacy ProcessExecutor implementation (pre-Epic 11)
            # This ensures safe gradual rollout
            self._use_legacy_implementation(cli_path, api_key)
            return

        logger.info("provider_abstraction_enabled")

        # Handle legacy constructor (backward compatibility)
        if provider is None and (cli_path is not None or api_key is not None):
            # Legacy mode: create ClaudeCodeProvider with old params
            logger.info(
                "process_executor_legacy_mode",
                message="Using legacy constructor. Consider migrating to provider-based API.",
                migration_guide="See docs/MIGRATION_PROVIDER.md"
            )

            factory = ProviderFactory()
            legacy_config = {}
            if cli_path is not None:
                legacy_config["cli_path"] = cli_path
            if api_key is not None:
                legacy_config["api_key"] = api_key

            self.provider = factory.create_provider("claude-code", config=legacy_config)

        # Use provided provider instance
        elif provider is not None:
            self.provider = provider
            logger.info(
                "process_executor_provider_injected",
                provider=provider.name,
                provider_version=provider.version
            )

        # Create provider from factory
        else:
            factory = ProviderFactory()
            self.provider = factory.create_provider(provider_name, config=provider_config)
            logger.info(
                "process_executor_provider_created",
                provider_name=provider_name,
                has_config=provider_config is not None
            )

        logger.info(
            "process_executor_initialized",
            project_root=str(project_root),
            provider=self.provider.name,
            provider_version=self.provider.version
        )

    def _check_feature_flag(self) -> bool:
        """
        Check if provider abstraction is enabled via feature flag.

        Feature flag priority (highest to lowest):
        1. Environment variable: GAO_PROVIDER_ABSTRACTION_ENABLED
        2. Configuration file: features.provider_abstraction_enabled
        3. Default: False (safe gradual rollout)

        Returns:
            True if provider abstraction enabled, False for legacy behavior
        """
        import os
        from gao_dev.core.config_loader import ConfigLoader

        # Check environment variable first
        env_flag = os.environ.get("GAO_PROVIDER_ABSTRACTION_ENABLED")
        if env_flag is not None:
            enabled = env_flag.lower() in ("true", "1", "yes")
            logger.info(
                "feature_flag_from_env",
                enabled=enabled,
                source="environment"
            )
            return enabled

        # Check configuration file
        try:
            config = ConfigLoader().load_config()
            enabled = config.get("features", {}).get("provider_abstraction_enabled", False)
            logger.info(
                "feature_flag_from_config",
                enabled=enabled,
                source="config_file"
            )
            return enabled
        except Exception as e:
            logger.warning(
                "feature_flag_load_failed",
                error=str(e),
                defaulting_to=False
            )
            return False

    def _use_legacy_implementation(self, cli_path: Optional[Path], api_key: Optional[str]):
        """
        Use legacy ProcessExecutor implementation (pre-Epic 11).

        This preserves the exact behavior before provider abstraction
        for safe gradual rollout.

        Args:
            cli_path: Path to Claude CLI
            api_key: Anthropic API key
        """
        # Set up legacy instance variables
        self.cli_path = cli_path
        self.api_key = api_key
        self.provider = None  # No provider in legacy mode

        logger.info(
            "process_executor_legacy_mode",
            message="Using pre-Epic 11 implementation"
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
            ValueError: If provider not properly configured
            ProviderExecutionError: If execution fails
            ProviderTimeoutError: If execution times out
        """
        # Validate provider configuration
        is_valid = await self.provider.validate_configuration()
        if not is_valid:
            logger.error(
                "provider_not_configured",
                provider=self.provider.name
            )
            raise ValueError(
                f"Provider '{self.provider.name}' not properly configured. "
                f"Check API keys and CLI installation. "
                f"See: gao-dev providers validate"
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

        try:
            async for message in self.provider.execute_task(
                task=task,
                context=context,
                model=model,
                tools=tools or [],
                timeout=timeout or self.DEFAULT_TIMEOUT
            ):
                yield message

            logger.info(
                "task_execution_completed",
                provider=self.provider.name
            )

        except Exception as e:
            logger.error(
                "task_execution_failed",
                provider=self.provider.name,
                error=str(e),
                exc_info=True
            )
            raise

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ProcessExecutor("
            f"project_root={self.project_root}, "
            f"provider={self.provider.name})"
        )
```

#### Step 2: Update Existing Tests (Ensure They Pass)

**File**: `tests/core/services/test_process_executor.py`

All existing tests should pass WITHOUT modification. The only change needed is ensuring test setup creates providers correctly if mocking is involved.

#### Step 3: Add New Provider-Specific Tests

**File**: `tests/core/services/test_process_executor_providers.py`

```python
"""Tests for ProcessExecutor provider functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from gao_dev.core.services.process_executor import ProcessExecutor
from gao_dev.core.providers.claude_code import ClaudeCodeProvider
from gao_dev.core.providers.base import IAgentProvider


class MockProvider(IAgentProvider):
    """Mock provider for testing."""

    def __init__(self):
        self._configured = True

    @property
    def name(self) -> str:
        return "mock"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def execute_task(self, task, context, model, tools, timeout=None, **kwargs):
        yield f"Mock result for: {task}"

    def supports_tool(self, tool_name: str) -> bool:
        return True

    def get_supported_models(self):
        return ["mock-model"]

    def translate_model_name(self, canonical_name: str) -> str:
        return canonical_name

    async def validate_configuration(self) -> bool:
        return self._configured

    def get_configuration_schema(self):
        return {}

    async def initialize(self) -> None:
        pass

    async def cleanup(self) -> None:
        pass


class TestProcessExecutorProviders:
    """Test ProcessExecutor provider functionality."""

    @pytest.mark.asyncio
    async def test_provider_injection(self, tmp_path):
        """Test injecting provider instance."""
        provider = MockProvider()
        executor = ProcessExecutor(tmp_path, provider=provider)

        assert executor.provider is provider
        assert executor.provider.name == "mock"

    @pytest.mark.asyncio
    async def test_provider_name_only(self, tmp_path):
        """Test creating provider by name."""
        with patch('gao_dev.core.providers.factory.ProviderFactory.create_provider') as mock_create:
            mock_create.return_value = MockProvider()

            executor = ProcessExecutor(tmp_path, provider_name="claude-code")

            mock_create.assert_called_once_with("claude-code", config=None)

    @pytest.mark.asyncio
    async def test_provider_with_config(self, tmp_path):
        """Test creating provider with config."""
        with patch('gao_dev.core.providers.factory.ProviderFactory.create_provider') as mock_create:
            mock_create.return_value = MockProvider()

            config = {"api_key": "test"}
            executor = ProcessExecutor(
                tmp_path,
                provider_name="claude-code",
                provider_config=config
            )

            mock_create.assert_called_once_with("claude-code", config=config)

    @pytest.mark.asyncio
    async def test_execute_with_provider(self, tmp_path):
        """Test executing task with provider."""
        provider = MockProvider()
        executor = ProcessExecutor(tmp_path, provider=provider)

        results = []
        async for result in executor.execute_agent_task("Test task"):
            results.append(result)

        assert len(results) > 0
        assert "Mock result" in results[0]

    @pytest.mark.asyncio
    async def test_provider_not_configured_raises_error(self, tmp_path):
        """Test error when provider not configured."""
        provider = MockProvider()
        provider._configured = False

        executor = ProcessExecutor(tmp_path, provider=provider)

        with pytest.raises(ValueError) as exc_info:
            async for _ in executor.execute_agent_task("Test task"):
                pass

        assert "not properly configured" in str(exc_info.value)
        assert provider.name in str(exc_info.value)


class TestProcessExecutorLegacyAPI:
    """Test ProcessExecutor backward compatibility."""

    @pytest.mark.asyncio
    async def test_legacy_constructor(self, tmp_path):
        """Test legacy constructor still works."""
        with patch('gao_dev.core.providers.factory.ProviderFactory.create_provider') as mock_create:
            mock_create.return_value = MockProvider()

            executor = ProcessExecutor(
                project_root=tmp_path,
                cli_path=Path("/usr/bin/claude"),
                api_key="sk-test"
            )

            # Should create claude-code provider with legacy config
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            assert args[0] == "claude-code"
            assert "cli_path" in kwargs["config"]
            assert "api_key" in kwargs["config"]

    @pytest.mark.asyncio
    async def test_legacy_logs_deprecation_warning(self, tmp_path, caplog):
        """Test legacy constructor logs deprecation warning."""
        with patch('gao_dev.core.providers.factory.ProviderFactory.create_provider') as mock_create:
            mock_create.return_value = MockProvider()

            executor = ProcessExecutor(
                project_root=tmp_path,
                cli_path=Path("/usr/bin/claude"),
                api_key="sk-test"
            )

            # Check for deprecation log (implementation may vary)
            # This ensures users are informed about migration
```

#### Step 4: Add Integration Tests for Backward Compatibility

**File**: `tests/integration/test_process_executor_legacy.py`

```python
"""Integration tests for ProcessExecutor backward compatibility."""

import pytest
from pathlib import Path

from gao_dev.core.services.process_executor import ProcessExecutor


@pytest.mark.integration
@pytest.mark.asyncio
class TestProcessExecutorBackwardCompatibility:
    """Test that existing code continues to work."""

    async def test_existing_code_pattern_works(self, tmp_path):
        """Test that existing usage pattern still works."""
        # This is how ProcessExecutor is currently used in the codebase
        # It MUST continue to work exactly the same way

        executor = ProcessExecutor(
            project_root=tmp_path,
            cli_path=None,  # Auto-detect
            api_key=None    # From env
        )

        # Should have created claude-code provider internally
        assert executor.provider is not None
        assert executor.provider.name == "claude-code"
```

---

## Testing Strategy

### Unit Tests
- Provider injection
- Provider creation by name
- Provider creation with config
- Legacy constructor
- Provider validation
- Error handling

### Integration Tests
- Backward compatibility with existing usage
- All existing ProcessExecutor tests pass unchanged
- Real provider execution (if API keys available)

### Performance Tests
- Measure overhead vs original implementation
- Target: <5% performance difference
- Memory usage validation

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All 400+ existing tests pass without modification
- [ ] New provider tests passing
- [ ] Legacy API works identically
- [ ] New provider API works
- [ ] Performance within 5% of original
- [ ] Code reviewed and approved
- [ ] Type checking passing (mypy strict)
- [ ] No linting errors (ruff)
- [ ] Documentation updated
- [ ] Changes committed with atomic commit
- [ ] Story marked complete in sprint-status.yaml

---

## Dependencies

**Upstream**:
- Story 11.2 (ClaudeCodeProvider) - MUST be complete
- Story 11.3 (ProviderFactory) - MUST be complete

**Downstream**:
- All code using ProcessExecutor benefits from provider abstraction
- Story 11.5 (Configuration Schema) - can proceed in parallel

---

## Notes

- **CRITICAL**: Backward compatibility is non-negotiable
- All existing tests MUST pass without modification
- Legacy constructor must work identically
- Performance must match current implementation
- Clear deprecation warnings for legacy usage
- Migration guide essential for users

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
- Story 11.2: `story-11.2.md` (ClaudeCodeProvider)
- Story 11.3: `story-11.3.md` (ProviderFactory)
- Current Implementation: `gao_dev/core/services/process_executor.py` (reference)
