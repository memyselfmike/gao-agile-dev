# GAO-Dev Provider System Guide

**Complete guide to GAO-Dev's multi-provider agent execution system**

Version: 1.0.0
Last Updated: 2025-11-04
Epic: 11 - Agent Provider Abstraction

---

## Table of Contents

1. [Overview](#overview)
2. [Available Providers](#available-providers)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [CLI Commands](#cli-commands)
6. [Provider Selection](#provider-selection)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting](#troubleshooting)
9. [Migration Guide](#migration-guide)
10. [FAQ](#faq)
11. [Best Practices](#best-practices)

---

## Overview

GAO-Dev's provider system enables flexible AI agent execution across multiple backends:

- **Claude Code CLI**: Official Anthropic CLI (recommended)
- **OpenCode**: Community CLI alternative
- **Direct API**: Direct API integration (Anthropic, OpenAI, Google)
- **Custom Providers**: Plugin system for custom backends

### Key Features

- **Provider-agnostic**: Switch providers without code changes
- **Intelligent selection**: Automatic provider selection based on context
- **Performance optimized**: Caching, lazy initialization, <5% overhead
- **Plugin support**: Extensible via plugin system
- **Backward compatible**: Zero breaking changes

### Architecture

```
GAO-Dev Orchestrator
        |
        v
Provider Abstraction Layer
        |
   +-----------+-----------+
   |           |           |
   v           v           v
Claude Code  OpenCode   Direct API
   CLI        CLI        (Anthropic/
                          OpenAI/
                          Google)
```

---

## Available Providers

### 1. Claude Code (Recommended)

**Description**: Official Anthropic Claude Code CLI

**Pros**:
- Full tool support (Read, Write, Edit, Bash, etc.)
- Streaming output
- Production-ready
- Best integration with GAO-Dev

**Cons**:
- Requires CLI installation
- Windows-specific path handling

**Setup**:
```bash
npm install -g @anthropic/claude-code
export ANTHROPIC_API_KEY=sk-...
```

**Configuration**:
```python
from gao_dev.core.providers import ProviderFactory

factory = ProviderFactory()
provider = factory.create_provider("claude-code")
```

---

### 2. OpenCode

**Description**: Community alternative CLI

**Pros**:
- Similar to Claude Code
- Open source
- Active community

**Cons**:
- May lag behind official features
- Limited documentation

**Setup**:
```bash
npm install -g opencode
export OPENAI_API_KEY=sk-...
```

**Configuration**:
```python
provider = factory.create_provider("opencode")
```

---

### 3. Direct API - Anthropic

**Description**: Direct Anthropic API integration

**Pros**:
- No CLI required
- Direct control
- Lower latency

**Cons**:
- No tool support (Read, Write, Bash)
- Limited to text generation
- Manual API key management

**Setup**:
```bash
export ANTHROPIC_API_KEY=sk-...
```

**Configuration**:
```python
provider = factory.create_provider(
    "direct-api-anthropic",
    config={"api_key": "sk-..."}
)
```

---

### 4. Direct API - OpenAI

**Description**: Direct OpenAI API integration

**Pros**:
- No CLI required
- GPT-4 access
- Fast response times

**Cons**:
- No tool support
- Different token limits
- API compatibility layer

**Setup**:
```bash
export OPENAI_API_KEY=sk-...
```

**Configuration**:
```python
provider = factory.create_provider(
    "direct-api-openai",
    config={"api_key": "sk-..."}
)
```

---

### 5. Direct API - Google

**Description**: Direct Google Gemini API integration

**Pros**:
- No CLI required
- Gemini models
- Cost-effective

**Cons**:
- No tool support
- Different model capabilities
- Newer, less tested

**Setup**:
```bash
export GOOGLE_API_KEY=...
```

**Configuration**:
```python
provider = factory.create_provider(
    "direct-api-google",
    config={"api_key": "..."}
)
```

---

## Quick Start

### Basic Usage

```python
from gao_dev.core.providers import ProviderFactory, AgentContext
from pathlib import Path

# 1. Create factory
factory = ProviderFactory()

# 2. Create provider
provider = factory.create_provider("claude-code")

# 3. Create context
context = AgentContext(project_root=Path("/my/project"))

# 4. Execute task
async for message in provider.execute_task(
    task="Implement user authentication",
    context=context,
    model="sonnet-4.5",
    tools=["Read", "Write", "Bash"],
):
    print(message.content)
```

### With Provider Selection

```python
from gao_dev.core.providers import ProviderSelector

# Automatic selection
selector = ProviderSelector(factory)
provider = selector.select_provider(model="sonnet-4.5")
```

### Using CLI

```bash
# List providers
gao-dev providers list

# Validate configuration
gao-dev providers validate claude-code

# Test provider
gao-dev providers test claude-code --prompt "Hello"
```

---

## Configuration

### Environment Variables

```bash
# Claude Code / Direct API Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# OpenAI
export OPENAI_API_KEY=sk-...

# Google
export GOOGLE_API_KEY=...

# Optional: Explicit CLI path
export CLAUDE_CODE_CLI=/usr/local/bin/claude
```

### YAML Configuration

**File**: `config/providers.yaml`

```yaml
providers:
  default: claude-code

  claude-code:
    cli_path: /usr/local/bin/claude
    api_key_env: ANTHROPIC_API_KEY

  direct-api-anthropic:
    api_key_env: ANTHROPIC_API_KEY
    base_url: https://api.anthropic.com
    max_retries: 3
    timeout: 3600
```

### Programmatic Configuration

```python
config = {
    "api_key": "sk-...",
    "base_url": "https://api.anthropic.com",
    "max_retries": 3,
    "timeout": 3600,
}

provider = factory.create_provider("direct-api-anthropic", config=config)
```

---

## CLI Commands

### List Providers

```bash
gao-dev providers list
```

**Output**:
```
Available Providers
├─ claude-code (CLI - Claude Code)
├─ opencode (CLI - OpenCode)
├─ direct-api-anthropic (Direct API)
├─ direct-api-openai (Direct API)
└─ direct-api-google (Direct API)

Total: 5 providers available
```

### Validate Configuration

```bash
# Validate specific provider
gao-dev providers validate claude-code

# Validate all providers
gao-dev providers validate

# With API key override
gao-dev providers validate direct-api-anthropic --api-key sk-...
```

### Test Provider

```bash
gao-dev providers test claude-code --prompt "Say hello"
gao-dev providers test direct-api-anthropic --model "claude-3-opus" --api-key sk-...
```

### Health Check

```bash
gao-dev providers health
```

**Output**:
```
Provider Health Status
├─ claude-code: HEALTHY
├─ direct-api-anthropic: HEALTHY (API key valid)
└─ opencode: UNHEALTHY (CLI not found)

Summary: 2/3 healthy
```

### Provider Info

```bash
gao-dev providers info claude-code
```

**Output**:
```
Provider: claude-code
├─ Version: 1.0.0
├─ Supported Models:
│  ├─ claude-sonnet-4-5-20250929
│  ├─ claude-3-5-sonnet-20241022
│  └─ claude-3-opus-20240229
└─ Configuration:
   ├─ cli_path (optional)
   └─ api_key (optional)
```

### Cache Statistics

```bash
gao-dev providers cache-stats
```

---

## Provider Selection

GAO-Dev includes intelligent provider selection strategies.

### Auto-Detect Strategy (Default)

Automatically selects best available provider:

```python
from gao_dev.core.providers import ProviderSelector

selector = ProviderSelector(factory)
provider = selector.select_provider(model="sonnet-4.5")
```

**Selection Logic**:
1. Check for Claude Code CLI
2. Fall back to OpenCode
3. Fall back to Direct API (Anthropic)
4. Fall back to Direct API (OpenAI/Google)

### Performance-Based Strategy

Select provider based on performance metrics:

```python
from gao_dev.core.providers.selection import PerformanceBasedStrategy

strategy = PerformanceBasedStrategy(performance_tracker)
selector = ProviderSelector(factory, strategy=strategy)
provider = selector.select_provider(model="sonnet-4.5")
```

### Cost-Based Strategy

Select cheapest provider for model:

```python
from gao_dev.core.providers.selection import CostBasedStrategy

strategy = CostBasedStrategy(cost_config)
selector = ProviderSelector(factory, strategy=strategy)
provider = selector.select_provider(model="sonnet-4.5")
```

### Composite Strategy

Combine multiple strategies:

```python
from gao_dev.core.providers.selection import CompositeStrategy

strategy = CompositeStrategy([
    PerformanceBasedStrategy(tracker),
    CostBasedStrategy(cost_config),
    AutoDetectStrategy(),
])
selector = ProviderSelector(factory, strategy=strategy)
```

---

## Performance Optimization

GAO-Dev includes comprehensive performance optimizations:

### Provider Caching

**Feature**: Automatic provider instance caching

**Benefits**:
- >90% faster initialization (cached)
- <5ms cache lookup time
- Thread-safe LRU cache
- Configurable TTL

**Usage** (automatic):
```python
# First call: creates provider
provider1 = factory.create_provider("claude-code")  # ~50ms

# Second call: returns cached
provider2 = factory.create_provider("claude-code")  # <5ms

# Same instance
assert provider1 is provider2  # True
```

**Cache Control**:
```python
# Disable caching
provider = factory.create_provider("claude-code", use_cache=False)

# Clear cache
factory.clear_cache()

# Get stats
stats = factory.get_cache_stats()
# {"provider_cache_size": 3, "model_cache_size": 12}
```

### Model Name Translation Caching

**Feature**: Immutable cache for model name translations

**Benefits**:
- >99% faster translation (cached)
- <1ms lookup time
- Zero memory overhead

**Usage**:
```python
# First translation
model_id = factory.translate_model_name("claude-code", "sonnet-4.5")
# "claude-sonnet-4-5-20250929"

# Cached translation
model_id = factory.translate_model_name("claude-code", "sonnet-4.5")  # <1ms
```

### CLI Path Detection Caching

**Feature**: Class-level cache for CLI paths

**Benefits**:
- 98% faster detection
- Shared across all instances
- Automatic invalidation

**Performance Baseline**:

| Operation | Cold | Warm (Cached) | Improvement |
|-----------|------|---------------|-------------|
| Provider Init | 45ms | <5ms | 90% |
| Model Translation | 10ms | <1ms | 99% |
| CLI Detection | 50ms | <1ms | 98% |
| Cache Lookup | N/A | 0.05ms | N/A |

---

## Troubleshooting

### Common Issues

#### 1. Provider Not Found

**Error**: `ProviderNotFoundError: Provider 'xyz' not found`

**Solution**:
```bash
# List available providers
gao-dev providers list

# Use correct provider name
provider = factory.create_provider("claude-code")  # Not "claude"
```

#### 2. CLI Not Found

**Error**: `ProviderError: Claude Code CLI not found`

**Solutions**:
1. Install CLI:
   ```bash
   npm install -g @anthropic/claude-code
   ```

2. Explicit path:
   ```python
   provider = factory.create_provider(
       "claude-code",
       config={"cli_path": Path("/usr/local/bin/claude")}
   )
   ```

3. Use Direct API instead:
   ```python
   provider = factory.create_provider("direct-api-anthropic")
   ```

#### 3. Missing API Key

**Error**: `AuthenticationError: API key required`

**Solutions**:
```bash
# Set environment variable
export ANTHROPIC_API_KEY=sk-...

# Or pass explicitly
provider = factory.create_provider(
    "direct-api-anthropic",
    config={"api_key": "sk-..."}
)
```

#### 4. Rate Limiting

**Error**: `RateLimitError: Rate limit exceeded. Retry after 30s`

**Solution**:
```python
from gao_dev.core.providers import RateLimitError
import time

try:
    async for msg in provider.execute_task(...):
        print(msg)
except RateLimitError as e:
    if e.retry_after:
        time.sleep(e.retry_after)
        # Retry
```

#### 5. Timeout

**Error**: `ProviderTimeoutError: Task execution timed out`

**Solution**:
```python
# Increase timeout
async for msg in provider.execute_task(
    task="...",
    timeout=7200,  # 2 hours
):
    pass
```

### Debug Logging

Enable detailed logging:

```python
import structlog
import logging

logging.basicConfig(level=logging.DEBUG)
structlog.configure(wrapper_class=structlog.stdlib.BoundLogger)
```

### Health Checks

Run comprehensive health check:

```bash
gao-dev providers health
```

---

## Migration Guide

### From Direct ProcessExecutor

**Before** (direct usage):
```python
from gao_dev.core.process_executor import ProcessExecutor

executor = ProcessExecutor()
result = executor.execute(
    command="claude",
    args=["--prompt", "Hello"],
)
```

**After** (provider abstraction):
```python
from gao_dev.core.providers import ProviderFactory

factory = ProviderFactory()
provider = factory.create_provider("claude-code")

async for msg in provider.execute_task(
    task="Hello",
    context=context,
    model="sonnet-4.5",
):
    print(msg)
```

### From Hardcoded Provider

**Before**:
```python
from gao_dev.agents.claude_agent import ClaudeAgent

agent = ClaudeAgent()
result = agent.execute(task="...")
```

**After**:
```python
from gao_dev.core.providers import ProviderSelector

selector = ProviderSelector(factory)
provider = selector.select_provider(model="sonnet-4.5")

result = await provider.execute_task(...)
```

### Adding New Provider

1. **Implement Interface**:
```python
from gao_dev.core.providers import IAgentProvider

class MyProvider(IAgentProvider):
    @property
    def name(self) -> str:
        return "my-provider"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def execute_task(self, task, context, **kwargs):
        # Implementation
        yield Message(...)

    # ... implement other methods
```

2. **Register Provider**:
```python
factory.register_provider("my-provider", MyProvider)
```

3. **Use Provider**:
```python
provider = factory.create_provider("my-provider")
```

---

## FAQ

### Q: Which provider should I use?

**A**: For production, use **Claude Code** (CLI). It has full tool support and best integration. For development/testing, Direct API is easier (no CLI required).

### Q: Can I switch providers without code changes?

**A**: Yes! Use ProviderSelector with auto-detect strategy. It will automatically use the best available provider.

### Q: What's the performance overhead?

**A**: <5% overhead vs direct implementation. Caching makes repeated operations >90% faster.

### Q: Do all providers support all models?

**A**: No. Each provider supports specific models:
- Claude Code: All Claude models
- Direct API Anthropic: All Claude models
- Direct API OpenAI: GPT models only
- Direct API Google: Gemini models only

### Q: Can I use multiple providers simultaneously?

**A**: Yes! Create multiple provider instances and use them as needed:

```python
claude_provider = factory.create_provider("claude-code")
openai_provider = factory.create_provider("direct-api-openai")

# Use both
result1 = await claude_provider.execute_task(...)
result2 = await openai_provider.execute_task(...)
```

### Q: How do I add a custom provider?

**A**: Implement `IAgentProvider` interface and register:

```python
class CustomProvider(IAgentProvider):
    # Implement interface
    pass

factory.register_provider("custom", CustomProvider)
provider = factory.create_provider("custom")
```

### Q: Are API keys logged?

**A**: No. API keys are never logged. We follow security best practices to protect sensitive information.

### Q: Can I use providers in tests?

**A**: Yes! Use mock providers for testing:

```python
from unittest.mock import Mock

mock_provider = Mock(spec=IAgentProvider)
mock_provider.execute_task.return_value = AsyncMockIterator([...])
```

### Q: How do I debug provider issues?

**A**: Enable debug logging and use CLI validation:

```bash
# Validate provider
gao-dev providers validate claude-code

# Check health
gao-dev providers health

# Test with simple prompt
gao-dev providers test claude-code --prompt "test"
```

---

## Best Practices

### 1. Use Provider Selection

**Don't** hardcode providers:
```python
# Bad
provider = factory.create_provider("claude-code")
```

**Do** use selection:
```python
# Good
selector = ProviderSelector(factory)
provider = selector.select_provider(model="sonnet-4.5")
```

### 2. Handle Errors Gracefully

```python
from gao_dev.core.providers import (
    ProviderError,
    AuthenticationError,
    RateLimitError,
)

try:
    async for msg in provider.execute_task(...):
        print(msg)
except AuthenticationError:
    # Handle auth failure
    logger.error("Authentication failed")
except RateLimitError as e:
    # Handle rate limit
    time.sleep(e.retry_after)
except ProviderError as e:
    if e.should_fallback():
        # Try different provider
        fallback_provider = selector.select_provider(...)
    elif e.is_retryable():
        # Retry with exponential backoff
        retry_with_backoff()
```

### 3. Use Caching

Let the system cache automatically:

```python
# Good - uses cache
provider = factory.create_provider("claude-code")

# Only disable when needed
provider = factory.create_provider("claude-code", use_cache=False)
```

### 4. Validate Configuration

Always validate before production use:

```bash
gao-dev providers validate
```

### 5. Monitor Performance

Track cache hit rates:

```python
stats = factory.get_cache_stats()
logger.info("Cache stats", **stats)
```

### 6. Environment-Based Selection

```python
import os

if os.getenv("ENVIRONMENT") == "production":
    provider = factory.create_provider("claude-code")
else:
    provider = factory.create_provider("direct-api-anthropic")
```

### 7. Implement Fallbacks

```python
providers_to_try = ["claude-code", "opencode", "direct-api-anthropic"]

for provider_name in providers_to_try:
    try:
        provider = factory.create_provider(provider_name)
        result = await provider.execute_task(...)
        break  # Success
    except ProviderError:
        continue  # Try next provider
```

---

## Performance Characteristics

### Initialization Times

| Provider | Cold Init | Warm (Cached) |
|----------|-----------|---------------|
| Claude Code | 45ms | <5ms |
| OpenCode | 52ms | <5ms |
| Direct API | 12ms | <5ms |

### First Chunk Latency

| Provider | p50 | p99 |
|----------|-----|-----|
| Claude Code | 850ms | 1200ms |
| Direct API | 680ms | 950ms |

### Memory Usage

| Provider | Initial | Peak |
|----------|---------|------|
| Claude Code | 25MB | 45MB |
| Direct API | 18MB | 32MB |

### Streaming Throughput

| Provider | Chunks/sec |
|----------|------------|
| Claude Code | 45 |
| Direct API | 58 |

---

## Security Considerations

### API Key Management

1. **Never hardcode API keys**:
```python
# Bad
provider = factory.create_provider(
    "direct-api-anthropic",
    config={"api_key": "sk-hardcoded"}  # DON'T DO THIS
)

# Good
provider = factory.create_provider("direct-api-anthropic")  # Uses env var
```

2. **Use environment variables**:
```bash
export ANTHROPIC_API_KEY=sk-...
```

3. **Use secrets management** (production):
```python
from your_secrets_manager import get_secret

api_key = get_secret("anthropic_api_key")
provider = factory.create_provider(
    "direct-api-anthropic",
    config={"api_key": api_key}
)
```

### Plugin Security

When using custom providers via plugins:

1. Review plugin code before use
2. Use sandboxed execution
3. Limit plugin permissions
4. Monitor resource usage

---

## Support

### Getting Help

1. **Documentation**: This guide
2. **CLI Help**: `gao-dev providers --help`
3. **GitHub Issues**: Report bugs and request features
4. **Community**: Discord/Slack channels

### Reporting Issues

When reporting provider issues, include:

1. Provider name and version
2. Error message and stack trace
3. Configuration (redact API keys!)
4. Output of `gao-dev providers health`
5. Steps to reproduce

---

## Changelog

### Version 1.0.0 (2025-11-04)

- Initial release
- 5 built-in providers
- Provider abstraction layer
- Intelligent selection strategies
- Performance optimization (caching, lazy init)
- CLI commands
- Comprehensive testing (304 tests)
- Migration tooling

---

## License

Copyright (c) 2025 GAO-Dev Project
See LICENSE file for details

---

**End of Guide**

For more information, see:
- [Architecture Documentation](./features/agent-provider-abstraction/ARCHITECTURE.md)
- [PRD](./features/agent-provider-abstraction/PRD.md)
- [Plugin Development Guide](./plugin-development-guide.md)
