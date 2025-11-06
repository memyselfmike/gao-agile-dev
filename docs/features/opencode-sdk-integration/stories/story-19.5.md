# Story 19.5: Provider Registration and Documentation

**Epic**: Epic 19 - OpenCode SDK Integration
**Status**: Draft
**Priority**: P1 (High)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer) + John (Product Manager)
**Created**: 2025-11-06

---

## User Story

**As a** GAO-Dev user
**I want** the OpenCode SDK provider registered and documented
**So that** I can easily switch to the new provider and understand how to use it

---

## Acceptance Criteria

### AC1: Provider Factory Registration
- `opencode-sdk` registered in `ProviderFactory`
- Factory creates `OpenCodeSDKProvider` for name `opencode-sdk`
- Factory tests pass for SDK provider
- Legacy CLI provider accessible as `opencode-cli`

### AC2: Environment Variable Support
- `AGENT_PROVIDER=opencode-sdk` environment variable works
- Provider selection via `.env` file works
- Configuration documented in `.env.example`
- Invalid provider names show helpful error

### AC3: CLI Provider Deprecation
- `OpenCodeProvider` renamed to `OpenCodeCLIProvider`
- CLI provider still accessible for backward compatibility
- Deprecation warning added to CLI provider
- Migration path documented

### AC4: Process Executor Integration
- `ProcessExecutor` supports `opencode-sdk` provider
- Provider switching works without code changes
- Configuration passed correctly to provider
- Error handling for provider failures

### AC5: Documentation Complete
- README updated with SDK provider instructions
- ARCHITECTURE document updated
- API documentation generated
- Migration guide created for users

### AC6: Benchmark Validation
- Full benchmark run completes with SDK provider
- Benchmark results comparable to CLI provider
- No errors or warnings during benchmark
- Metrics collected correctly

---

## Technical Details

### File Structure
```
gao_dev/core/providers/
├── __init__.py                  # MODIFIED: Export renamed CLI provider
├── factory.py                   # MODIFIED: Register SDK provider
├── opencode_sdk.py              # EXISTING: SDK provider (Stories 19.2-19.3)
├── opencode.py                  # RENAMED TO: opencode_cli.py
└── opencode_cli.py              # NEW: Renamed CLI provider

gao_dev/core/services/
└── process_executor.py          # MODIFIED: Support opencode-sdk

docs/features/opencode-sdk-integration/
├── README.md                    # MODIFIED: Add usage instructions
├── ARCHITECTURE.md              # MODIFIED: Update architecture
└── MIGRATION.md                 # NEW: Migration guide

.env                             # MODIFIED: Add AGENT_PROVIDER example
```

### Implementation Approach

**Step 1: Register SDK Provider in Factory**
```python
# gao_dev/core/providers/factory.py

from typing import Dict, Any, Optional
import structlog

from gao_dev.core.providers.interfaces import IAgentProvider
from gao_dev.core.providers.anthropic import AnthropicProvider
from gao_dev.core.providers.opencode_cli import OpenCodeCLIProvider
from gao_dev.core.providers.opencode_sdk import OpenCodeSDKProvider

logger = structlog.get_logger(__name__)


class ProviderFactory:
    """Factory for creating agent providers."""

    _PROVIDERS = {
        "anthropic": AnthropicProvider,
        "opencode": OpenCodeCLIProvider,  # Default to CLI for backward compatibility
        "opencode-cli": OpenCodeCLIProvider,  # Explicit CLI provider
        "opencode-sdk": OpenCodeSDKProvider,  # NEW: SDK provider
    }

    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> IAgentProvider:
        """
        Create an agent provider instance.

        Args:
            provider_name: Name of provider (anthropic, opencode-cli, opencode-sdk)
            config: Provider configuration

        Returns:
            Initialized provider instance

        Raises:
            ValueError: If provider name not found
        """
        config = config or {}

        provider_class = cls._PROVIDERS.get(provider_name)
        if not provider_class:
            available = ", ".join(cls._PROVIDERS.keys())
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available providers: {available}"
            )

        logger.info(
            "provider_factory_create",
            provider_name=provider_name,
            provider_class=provider_class.__name__,
        )

        return provider_class(**config)

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names."""
        return list(cls._PROVIDERS.keys())
```

**Step 2: Rename CLI Provider**
```python
# gao_dev/core/providers/opencode_cli.py (renamed from opencode.py)

import warnings
from gao_dev.core.providers.interfaces import IAgentProvider

# ... existing OpenCodeProvider implementation ...


class OpenCodeCLIProvider(IAgentProvider):
    """
    OpenCode CLI-based agent provider (DEPRECATED).

    This provider uses CLI subprocess calls which can cause hanging issues.
    Consider using OpenCodeSDKProvider instead.

    See: docs/features/opencode-sdk-integration/MIGRATION.md
    """

    def __init__(self, *args, **kwargs):
        """Initialize CLI provider with deprecation warning."""
        warnings.warn(
            "OpenCodeCLIProvider is deprecated. "
            "Use OpenCodeSDKProvider for better reliability. "
            "Set AGENT_PROVIDER=opencode-sdk in .env",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    # ... rest of implementation (unchanged) ...


# Backward compatibility alias
OpenCodeProvider = OpenCodeCLIProvider
```

**Step 3: Update ProcessExecutor**
```python
# gao_dev/core/services/process_executor.py

import os
from gao_dev.core.providers.factory import ProviderFactory

class ProcessExecutor:
    """Execute agent tasks using configured provider."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize process executor.

        Args:
            config: Executor configuration
        """
        self.config = config or {}

        # Get provider from environment or config
        provider_name = os.environ.get(
            "AGENT_PROVIDER",
            self.config.get("provider", "anthropic")
        )

        logger.info(
            "process_executor_init",
            provider_name=provider_name,
        )

        # Create provider
        self.provider = ProviderFactory.create_provider(
            provider_name=provider_name,
            config=self.config.get("provider_config", {}),
        )

        # Initialize provider
        self.provider.initialize()

    # ... rest of implementation ...
```

**Step 4: Update __init__.py**
```python
# gao_dev/core/providers/__init__.py

from .interfaces import IAgentProvider, AgentResponse
from .anthropic import AnthropicProvider
from .opencode_cli import OpenCodeCLIProvider, OpenCodeProvider  # Backward compat
from .opencode_sdk import OpenCodeSDKProvider
from .factory import ProviderFactory
from .exceptions import ProviderError, TaskExecutionError

__all__ = [
    "IAgentProvider",
    "AgentResponse",
    "AnthropicProvider",
    "OpenCodeCLIProvider",
    "OpenCodeProvider",  # Deprecated alias
    "OpenCodeSDKProvider",
    "ProviderFactory",
    "ProviderError",
    "TaskExecutionError",
]
```

**Step 5: Create Migration Guide**
```markdown
# Migration Guide: CLI to SDK Provider

## Overview

This guide helps you migrate from the OpenCode CLI provider to the new SDK provider.

## Why Migrate?

**Benefits of SDK Provider:**
- No subprocess hanging issues
- Better performance (direct API vs CLI)
- More reliable error handling
- Advanced features support

**When to Migrate:**
- If experiencing CLI hanging issues
- For production deployments
- For better observability

## Migration Steps

### 1. Update Environment Variable

Update your `.env` file:

```bash
# Before
AGENT_PROVIDER=opencode

# After
AGENT_PROVIDER=opencode-sdk
```

### 2. Verify Dependencies

Ensure OpenCode SDK is installed:

```bash
pip install -e .
python -c "from opencode_ai import Opencode; print('OK')"
```

### 3. Test the Change

Run a simple test:

```bash
# Set environment variable
export AGENT_PROVIDER=opencode-sdk

# Run GAO-Dev command
gao-dev list-agents
```

### 4. Run Full Tests

```bash
pytest tests/
```

### 5. Update Configuration (Optional)

For advanced configuration:

```yaml
# config.yaml
provider:
  name: opencode-sdk
  config:
    port: 4096
    startup_timeout: 30
    auto_start_server: true
```

## Rollback

If you encounter issues, rollback to CLI provider:

```bash
# In .env
AGENT_PROVIDER=opencode-cli
```

## Troubleshooting

### Issue: SDK Import Error

**Solution**: Install SDK dependency
```bash
pip install opencode-ai
```

### Issue: Server Won't Start

**Solution**: Check OpenCode CLI is installed
```bash
opencode --version
```

### Issue: Port Conflict

**Solution**: Use different port
```python
AGENT_PROVIDER=opencode-sdk
OPENCODE_PORT=4097
```

## Support

For issues, see:
- [OpenCode SDK Documentation](docs/features/opencode-sdk-integration/)
- [GitHub Issues](https://github.com/your-org/gao-agile-dev/issues)
```

**Step 6: Update .env.example**
```bash
# .env.example

# Agent Provider Selection
# Options: anthropic, opencode-cli, opencode-sdk (recommended)
AGENT_PROVIDER=opencode-sdk

# Anthropic Configuration
ANTHROPIC_API_KEY=your_api_key_here

# OpenCode SDK Configuration (optional)
OPENCODE_PORT=4096
OPENCODE_SERVER_URL=http://localhost:4096
```

---

## Testing Approach

### Manual Testing
```bash
# Test factory registration
python -c "
from gao_dev.core.providers.factory import ProviderFactory
provider = ProviderFactory.create_provider('opencode-sdk')
print(f'Provider: {type(provider).__name__}')
"

# Test environment variable
export AGENT_PROVIDER=opencode-sdk
gao-dev list-agents

# Test CLI provider still works
export AGENT_PROVIDER=opencode-cli
gao-dev list-agents

# Run benchmark with SDK provider
export AGENT_PROVIDER=opencode-sdk
gao-dev sandbox run sandbox/benchmarks/simple-test.yaml
```

### Automated Testing
```python
# tests/core/providers/test_factory.py

def test_factory_creates_sdk_provider():
    """Test factory creates SDK provider."""
    provider = ProviderFactory.create_provider("opencode-sdk")
    assert isinstance(provider, OpenCodeSDKProvider)


def test_factory_creates_cli_provider():
    """Test factory creates CLI provider (backward compat)."""
    provider = ProviderFactory.create_provider("opencode-cli")
    assert isinstance(provider, OpenCodeCLIProvider)


def test_factory_unknown_provider():
    """Test factory raises error for unknown provider."""
    with pytest.raises(ValueError) as exc_info:
        ProviderFactory.create_provider("unknown-provider")

    assert "unknown provider" in str(exc_info.value).lower()


def test_environment_variable_selection():
    """Test provider selection via environment variable."""
    import os
    os.environ["AGENT_PROVIDER"] = "opencode-sdk"

    executor = ProcessExecutor()
    assert isinstance(executor.provider, OpenCodeSDKProvider)
```

---

## Dependencies

### Required Packages
- All from Stories 19.1-19.4

### Code Dependencies
- Story 19.1 (SDK dependency)
- Story 19.2 (Core provider)
- Story 19.3 (Server lifecycle)
- Story 19.4 (Testing)

### External Dependencies
- None (documentation only)

---

## Definition of Done

- [x] `opencode-sdk` registered in `ProviderFactory`
- [x] Environment variable `AGENT_PROVIDER=opencode-sdk` works
- [x] CLI provider renamed to `OpenCodeCLIProvider`
- [x] Deprecation warning added to CLI provider
- [x] Backward compatibility maintained (alias `OpenCodeProvider`)
- [x] `ProcessExecutor` supports SDK provider
- [x] README updated with usage instructions
- [x] ARCHITECTURE document updated
- [x] Migration guide created
- [x] `.env.example` updated
- [x] Factory tests pass
- [x] Environment variable tests pass
- [x] Full benchmark completes with SDK provider
- [x] All existing tests pass
- [x] Code follows existing style (ASCII-only, type hints)
- [x] Committed to git with conventional commit message

---

## Related Stories

**Depends On**:
- Story 19.1 (Add OpenCode SDK Dependency)
- Story 19.2 (Implement OpenCodeSDKProvider Core)
- Story 19.3 (Server Lifecycle Management)
- Story 19.4 (Integration Testing and Validation)

**Blocks**: None (final story in epic)

---

## Notes

### Backward Compatibility

The implementation maintains backward compatibility:
- `AGENT_PROVIDER=opencode` still works (uses CLI provider)
- `OpenCodeProvider` class alias preserved
- Deprecation warnings guide users to SDK provider
- CLI provider still fully functional

### Recommended Configuration

For new projects:
```bash
# .env
AGENT_PROVIDER=opencode-sdk
```

For existing projects:
```bash
# .env
AGENT_PROVIDER=opencode-cli  # Keep using CLI provider
```

### Documentation Structure

Documentation is organized for different audiences:
- **README.md**: Quick start for users
- **ARCHITECTURE.md**: Technical details for developers
- **MIGRATION.md**: Step-by-step migration guide
- **API docs**: Generated from docstrings

---

## Acceptance Testing

### Test Case 1: Factory Registration
```python
provider = ProviderFactory.create_provider("opencode-sdk")
assert isinstance(provider, OpenCodeSDKProvider)
```
**Expected**: SDK provider created successfully

### Test Case 2: Environment Variable
```bash
$ export AGENT_PROVIDER=opencode-sdk
$ gao-dev list-agents
[List of agents shown...]
```
**Expected**: SDK provider used, command succeeds

### Test Case 3: CLI Provider Backward Compatibility
```python
provider = ProviderFactory.create_provider("opencode")
assert isinstance(provider, OpenCodeCLIProvider)
```
**Expected**: CLI provider created (with deprecation warning)

### Test Case 4: Benchmark Run
```bash
$ export AGENT_PROVIDER=opencode-sdk
$ gao-dev sandbox run sandbox/benchmarks/simple-test.yaml
...
Benchmark completed successfully
```
**Expected**: Benchmark completes without errors

### Test Case 5: Migration Guide Works
```bash
# Follow migration guide steps
$ export AGENT_PROVIDER=opencode-sdk
$ pytest tests/
===== 420+ passed =====
```
**Expected**: All tests pass after migration

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Backward compat breaks | High | Low | Maintain aliases, thorough testing |
| Users don't migrate | Low | Medium | Deprecation warnings, clear docs |
| Documentation unclear | Medium | Low | Review with users, examples |
| Benchmark fails | High | Low | Test thoroughly before release |

---

## Implementation Checklist

- [ ] Register SDK provider in `ProviderFactory`
- [ ] Add `opencode-sdk` to provider map
- [ ] Rename `opencode.py` to `opencode_cli.py`
- [ ] Add deprecation warning to CLI provider
- [ ] Create `OpenCodeProvider` alias for backward compat
- [ ] Update `ProcessExecutor` to support SDK provider
- [ ] Update `__init__.py` exports
- [ ] Create migration guide (MIGRATION.md)
- [ ] Update README.md with SDK provider instructions
- [ ] Update ARCHITECTURE.md
- [ ] Update .env.example
- [ ] Write factory tests
- [ ] Write environment variable tests
- [ ] Run full benchmark with SDK provider
- [ ] Run all tests
- [ ] Review documentation with team
- [ ] Create git commit with conventional message

---

**Created by**: Bob (Scrum Master) via BMAD workflow
**Ready for Implementation**: Yes (after Stories 19.1-19.4)
**Estimated Completion**: 0.5 days

---

*This story is part of the GAO-Dev OpenCode SDK Integration project.*
