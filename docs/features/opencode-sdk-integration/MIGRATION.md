# Migration Guide: OpenCode CLI to SDK Provider

## Overview

This guide helps you migrate from the OpenCode CLI provider to the new SDK provider.

The OpenCode SDK provider (`opencode-sdk`) offers better reliability and performance compared to the CLI-based provider (`opencode-cli`).

## Why Migrate?

**Benefits of SDK Provider:**
- **No subprocess hanging issues** - Direct API calls instead of CLI subprocess
- **Better performance** - Direct API communication vs CLI overhead
- **More reliable error handling** - SDK provides structured error responses
- **Advanced features support** - Server lifecycle management, health checks
- **Better observability** - Structured logging and metrics

**When to Migrate:**
- If experiencing CLI hanging issues with `opencode` provider
- For production deployments requiring reliability
- When you need better observability and error handling
- For performance-sensitive applications

## Prerequisites

Before migrating, ensure you have:

1. **OpenCode CLI installed**:
   ```bash
   opencode --version
   ```
   If not installed, follow: https://github.com/opencode-ai/opencode

2. **OpenCode SDK installed** (usually installed with GAO-Dev):
   ```bash
   python -c "from opencode_ai import Opencode; print('SDK available')"
   ```
   If not available:
   ```bash
   pip install opencode-ai
   ```

3. **API key configured**:
   ```bash
   # For Anthropic (default)
   export ANTHROPIC_API_KEY=your_api_key_here

   # For OpenAI
   export OPENAI_API_KEY=your_api_key_here

   # For Google
   export GOOGLE_API_KEY=your_api_key_here
   ```

## Migration Steps

### Step 1: Update Environment Variable

The simplest way to switch to the SDK provider is via the `AGENT_PROVIDER` environment variable.

**Before (CLI provider):**
```bash
# .env file
AGENT_PROVIDER=opencode
# or
AGENT_PROVIDER=opencode-cli
```

**After (SDK provider):**
```bash
# .env file
AGENT_PROVIDER=opencode-sdk
```

### Step 2: Verify Configuration

Test that the SDK provider is working:

```bash
# Set environment variable
export AGENT_PROVIDER=opencode-sdk

# Run a simple GAO-Dev command
gao-dev list-agents

# Expected output:
# Available agents:
# - Brian (Workflow Coordinator)
# - John (Product Manager)
# - Winston (Technical Architect)
# ...
```

### Step 3: Test with a Simple Task

Run a simple test to verify the provider works:

```bash
# Set provider
export AGENT_PROVIDER=opencode-sdk

# Run a simple benchmark or task
gao-dev sandbox init test-sdk-provider
cd sandbox/projects/test-sdk-provider

# Create a simple task file
echo "Create a hello.py file with a hello world function" > task.txt

# Run with OpenCode SDK provider
# (Actual command depends on your GAO-Dev setup)
```

### Step 4: Update Configuration Files (Optional)

For more advanced configuration, you can specify provider settings in your configuration files:

**config.yaml:**
```yaml
provider:
  name: opencode-sdk
  config:
    server_url: http://localhost:4096  # Default OpenCode server
    port: 4096
    startup_timeout: 30
    auto_start_server: true  # Automatically start OpenCode server if not running
    api_key: ${ANTHROPIC_API_KEY}  # Reference from environment
```

### Step 5: Run Full Test Suite

Verify all tests pass with the new provider:

```bash
# Set provider
export AGENT_PROVIDER=opencode-sdk

# Run tests
pytest tests/

# Expected: All tests should pass
```

## Configuration Options

The SDK provider supports the following configuration options:

| Option | Default | Description |
|--------|---------|-------------|
| `server_url` | `http://localhost:4096` | URL of OpenCode server |
| `port` | `4096` | Server port (used if auto-starting) |
| `startup_timeout` | `30` | Max seconds to wait for server startup |
| `auto_start_server` | `true` | Auto-start server if not running |
| `api_key` | From env var | API key for AI provider |

**Example configuration:**

```python
from gao_dev.core.providers import OpenCodeSDKProvider

provider = OpenCodeSDKProvider(
    server_url="http://localhost:4096",
    port=4096,
    startup_timeout=30,
    auto_start_server=True
)
```

## Rollback Plan

If you encounter issues with the SDK provider, you can easily rollback to the CLI provider:

### Quick Rollback

```bash
# In .env file
AGENT_PROVIDER=opencode-cli

# Or unset to use default
unset AGENT_PROVIDER
```

### Full Rollback

1. **Update environment variable:**
   ```bash
   export AGENT_PROVIDER=opencode-cli
   ```

2. **Verify CLI provider works:**
   ```bash
   gao-dev list-agents
   ```

3. **Update configuration files:**
   ```yaml
   provider:
     name: opencode-cli
   ```

## Troubleshooting

### Issue: SDK Import Error

**Error:**
```
ImportError: No module named 'opencode_ai'
```

**Solution:**
Install the OpenCode SDK:
```bash
pip install opencode-ai
```

### Issue: Server Won't Start

**Error:**
```
ProviderInitializationError: OpenCode server failed to start
```

**Solution:**
1. Check OpenCode CLI is installed:
   ```bash
   opencode --version
   ```

2. Try starting server manually:
   ```bash
   opencode server start
   ```

3. Check server health:
   ```bash
   curl http://localhost:4096/health
   ```

### Issue: Port Already in Use

**Error:**
```
ProviderInitializationError: Port 4096 already in use
```

**Solution:**
Use a different port:
```bash
# In .env
OPENCODE_PORT=4097
```

Or in configuration:
```python
provider = OpenCodeSDKProvider(port=4097)
```

### Issue: API Key Not Found

**Error:**
```
ProviderConfigurationError: ANTHROPIC_API_KEY not set
```

**Solution:**
Set the appropriate API key:
```bash
# For Anthropic
export ANTHROPIC_API_KEY=your_key_here

# For OpenAI
export OPENAI_API_KEY=your_key_here

# For Google
export GOOGLE_API_KEY=your_key_here
```

### Issue: Deprecation Warnings

**Warning:**
```
DeprecationWarning: OpenCodeProvider is deprecated. Use OpenCodeSDKProvider...
```

**Solution:**
This warning appears when using the old CLI provider. Follow this migration guide to switch to `opencode-sdk`.

## Performance Comparison

Expected performance improvements with SDK provider:

| Metric | CLI Provider | SDK Provider | Improvement |
|--------|--------------|--------------|-------------|
| Startup time | 2-5s | 0.5-1s | 2-5x faster |
| Task execution | Variable (hangs) | Consistent | More reliable |
| Error handling | Basic | Structured | Better debugging |
| Resource usage | High (subprocess) | Low (API) | Lower overhead |

## Compatibility Notes

### Backward Compatibility

- The old `opencode` provider name still works (defaults to CLI provider)
- `opencode-cli` explicitly uses CLI provider
- `opencode-sdk` uses new SDK provider
- `OpenCodeProvider` class still available (with deprecation warning)
- `OpenCodeCLIProvider` alias available for clarity

### Breaking Changes

**None** - This migration is fully backward compatible. The CLI provider remains available.

### Deprecation Timeline

- **v1.0.0** - SDK provider introduced, CLI provider deprecated
- **v1.x.x** - Both providers supported
- **v2.0.0** (future) - CLI provider may be removed

## Best Practices

1. **Use environment variables** for provider selection:
   ```bash
   export AGENT_PROVIDER=opencode-sdk
   ```

2. **Set API keys in environment** (not in code):
   ```bash
   export ANTHROPIC_API_KEY=your_key_here
   ```

3. **Use configuration files** for advanced settings:
   ```yaml
   provider:
     name: opencode-sdk
     config:
       startup_timeout: 60
   ```

4. **Monitor logs** during migration:
   ```bash
   # Enable debug logging
   export GAO_DEV_LOG_LEVEL=DEBUG
   ```

5. **Test thoroughly** before production deployment

## Additional Resources

- **OpenCode SDK Integration PRD**: [PRD.md](PRD.md)
- **Architecture Documentation**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **OpenCode Documentation**: https://github.com/opencode-ai/opencode
- **GAO-Dev Setup Guide**: [../../SETUP.md](../../SETUP.md)

## Support

For issues or questions:

1. **Check logs** for detailed error messages
2. **Review troubleshooting** section above
3. **Open GitHub issue** with:
   - Error message
   - Configuration used
   - Steps to reproduce
   - Expected vs actual behavior

## Summary

Migrating from CLI to SDK provider:

1. Set `AGENT_PROVIDER=opencode-sdk` in .env
2. Verify SDK installed: `python -c "from opencode_ai import Opencode"`
3. Test with `gao-dev list-agents`
4. Run full test suite
5. Monitor for issues
6. Rollback to `opencode-cli` if needed

**Recommended for all users** - The SDK provider offers significant reliability and performance improvements over the CLI provider.

---

**Migration Date**: 2025-11-06
**GAO-Dev Version**: 1.0.0+
**Status**: Stable
