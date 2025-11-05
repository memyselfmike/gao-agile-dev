# Provider Configuration Migration Guide

This guide helps you migrate to GAO-Dev's new provider abstraction system introduced in Epic 11.

## Overview

GAO-Dev now supports multiple AI providers (Claude Code, OpenCode, Direct API, custom) while maintaining 100% backward compatibility.

## Do I Need to Migrate?

**No!** Your existing code will continue to work without any changes.

Migration is **optional** and only needed if you want to:
- Use a different provider (OpenCode, Direct API)
- Customize provider-specific settings
- Switch providers per-agent
- Build custom providers via plugins

## What Changed

### ProcessExecutor API

**Before (Still Works)**:
```python
from gao_dev.core.services.process_executor import ProcessExecutor

executor = ProcessExecutor(
    project_root=Path("/project"),
    cli_path=Path("/usr/bin/claude"),
    api_key="sk-ant-..."
)

async for output in executor.execute_agent_task("Implement feature X"):
    print(output)
```

**After (New API - Recommended)**:
```python
from gao_dev.core.services.process_executor import ProcessExecutor

# Option 1: Provider name only (uses defaults)
executor = ProcessExecutor(
    project_root=Path("/project"),
    provider_name="claude-code"
)

# Option 2: Provider with config
executor = ProcessExecutor(
    project_root=Path("/project"),
    provider_name="claude-code",
    provider_config={"api_key": "sk-ant-..."}
)

# Option 3: Provider instance injection
from gao_dev.core.providers import ClaudeCodeProvider

provider = ClaudeCodeProvider(api_key="sk-ant-...")
executor = ProcessExecutor(
    project_root=Path("/project"),
    provider=provider
)

async for output in executor.execute_agent_task(
    task="Implement feature X",
    model="sonnet-4.5",
    tools=["Read", "Write", "Bash"]
):
    print(output)
```

### Agent Configuration

**Before (Still Works)**:
```yaml
# gao_dev/config/agents/amelia.yaml (Epic 10)
agent:
  metadata:
    name: Amelia
    role: Software Developer
    version: 1.0.0

  configuration:
    model: "sonnet-4.5"
    max_tokens: 8000
    temperature: 0.7
```

**After (Optional)**:
```yaml
# gao_dev/config/agents/amelia.yaml
agent:
  metadata:
    name: Amelia
    role: Software Developer
    version: 1.0.0

  configuration:
    provider: "claude-code"        # NEW: optional provider selection
    provider_config:                # NEW: optional provider-specific settings
      cli_path: "/usr/bin/claude"
      api_key: null                 # null = use environment variable

    model: "sonnet-4.5"
    max_tokens: 8000
    temperature: 0.7
```

## Migration Steps

### Step 1: Check Current Provider

```bash
# List available providers
python -c "from gao_dev.core.providers import ProviderFactory; print(ProviderFactory().list_providers())"

# Output: ['claude-code']
```

### Step 2: Validate Configuration

```python
from gao_dev.core.providers import ClaudeCodeProvider

provider = ClaudeCodeProvider()

# Check if properly configured
is_valid = await provider.validate_configuration()
if not is_valid:
    print("Provider not configured. Check API key and CLI installation.")
```

### Step 3: Update Code (Optional)

If you want to use the new provider-based API, update your code to use one of the new patterns shown above. The old API will continue to work indefinitely.

### Step 4: Test

Run your existing tests to verify backward compatibility:

```bash
pytest tests/
```

## Configuration Reference

### System Defaults

Edit `gao_dev/config/defaults.yaml`:

```yaml
# Provider Configuration
providers:
  # Default provider for all agents
  default: "claude-code"

  # Provider-specific configuration
  claude-code:
    cli_path: null  # Auto-detect if null
    api_key_env: "ANTHROPIC_API_KEY"
    default_model: "sonnet-4.5"
    timeout: 3600
```

### Agent-Specific Provider

Edit agent YAML files (when using Epic 10):

```yaml
agent:
  configuration:
    # Override system default provider for this agent
    provider: "claude-code"

    # Provide agent-specific config
    provider_config:
      timeout: 7200  # 2 hours for this agent
```

## Example Configurations

### Use ClaudeCode (Default)

```python
executor = ProcessExecutor(
    project_root=Path("/project"),
    provider_name="claude-code"
)
```

### Use ClaudeCode with Custom Config

```python
executor = ProcessExecutor(
    project_root=Path("/project"),
    provider_name="claude-code",
    provider_config={
        "cli_path": "/custom/path/claude",
        "api_key": "sk-ant-..."
    }
)
```

### Use OpenCode (Future)

```python
executor = ProcessExecutor(
    project_root=Path("/project"),
    provider_name="opencode",
    provider_config={
        "ai_provider": "anthropic"
    }
)
```

### Use Direct API (Future)

```python
executor = ProcessExecutor(
    project_root=Path("/project"),
    provider_name="direct-api",
    provider_config={
        "provider": "anthropic",
        "max_retries": 3
    }
)
```

## Creating Custom Providers

You can create custom providers for proprietary execution backends:

```python
from gao_dev.core.providers import IAgentProvider

class CustomProvider(IAgentProvider):
    @property
    def name(self) -> str:
        return "custom"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def execute_task(self, task, context, model, tools, timeout=None, **kwargs):
        # Your implementation
        yield "Processing..."
        yield "Complete!"

    # Implement other required methods...

# Register and use
from gao_dev.core.providers import ProviderFactory

factory = ProviderFactory()
factory.register_provider("custom", CustomProvider)

executor = ProcessExecutor(
    project_root=Path("/project"),
    provider_name="custom"
)
```

## Troubleshooting

### Provider Not Found

**Error**: `Provider 'opencode' not found`

**Solution**: The provider is not implemented yet or not registered. Use `list_providers()` to see available providers.

### Provider Not Configured

**Error**: `Provider 'claude-code' not properly configured`

**Solution**:
1. Check that Claude CLI is installed: `which claude` (Unix) or `where claude` (Windows)
2. Check that API key is set: `echo $ANTHROPIC_API_KEY`
3. Run provider validation: `await provider.validate_configuration()`

### Legacy API Not Working

**Error**: Code that used to work now fails

**Solution**: The legacy API should work identically. Please report this as a bug with:
- Code snippet showing usage
- Error message
- Expected behavior vs. actual behavior

## Rollback

If you encounter issues with the new provider system, you can:

1. **Continue using legacy API**: No changes needed, it works the same as before
2. **Disable provider abstraction**: Set `features.provider_abstraction_enabled: false` in `defaults.yaml` (if feature flag is implemented)
3. **Report issues**: Open a GitHub issue with details

## Support

- **Documentation**: `docs/features/agent-provider-abstraction/`
- **Issues**: https://github.com/anthropics/gao-dev/issues
- **Examples**: `tests/core/services/test_process_executor_providers.py`

## FAQ

### Q: Do I have to migrate immediately?

No, the legacy API will continue to work indefinitely. Migrate when you need new provider features.

### Q: Can I mix old and new APIs?

Yes, you can use the legacy API in some places and the new API in others.

### Q: Will my existing tests break?

No, all existing tests should pass without modification. If they don't, please report it as a bug.

### Q: When should I use the new API?

Use the new API when:
- Starting new projects
- Adding support for multiple providers
- Customizing provider behavior
- Building plugins

### Q: How do I know which provider is being used?

Check the logs - ProcessExecutor logs the provider name and version on initialization.

---

**Last Updated**: 2025-11-04
**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Phase 1 Complete
