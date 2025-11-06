# OpenCode SDK Integration - Technical Architecture

## Overview

This document describes the technical architecture of the OpenCode SDK integration in GAO-Dev, including the SDK provider implementation, server lifecycle management, and integration with the provider abstraction system.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        GAO-Dev Application                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       ProcessExecutor                            │
│  - Reads AGENT_PROVIDER env var                                 │
│  - Creates provider via ProviderFactory                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ProviderFactory                             │
│  - Registers: claude-code, opencode, opencode-cli, opencode-sdk │
│  - Creates provider instances                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
┌────────────────────────────┐  ┌────────────────────────────┐
│  OpenCodeCLIProvider       │  │  OpenCodeSDKProvider       │
│  (Legacy, Deprecated)      │  │  (Recommended)             │
│                            │  │                            │
│  - Uses subprocess         │  │  - Uses SDK API            │
│  - Hangs possible          │  │  - Server lifecycle mgmt   │
└────────────────────────────┘  └──────────┬─────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────┐
                    │       OpenCode Server (HTTP API)         │
                    │  - Auto-started by SDK provider          │
                    │  - Health checks                         │
                    │  - Session management                    │
                    │  - Graceful shutdown                     │
                    └──────────────────────────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────┐
                    │         AI Provider APIs                 │
                    │  - Anthropic (Claude)                    │
                    │  - OpenAI (GPT)                          │
                    │  - Google (Gemini)                       │
                    └──────────────────────────────────────────┘
```

## Component Design

### 1. OpenCodeSDKProvider

**Location**: `gao_dev/core/providers/opencode_sdk.py`

**Responsibilities:**
- Implement `IAgentProvider` interface
- Manage OpenCode server lifecycle
- Execute tasks via SDK API
- Handle errors and retries
- Translate model names

**Key Methods:**

```python
class OpenCodeSDKProvider(IAgentProvider):
    """SDK-based OpenCode provider."""

    async def initialize(self) -> None:
        """Initialize provider and start server if needed."""

    async def execute_task(
        self,
        task: str,
        context: AgentContext,
        model: str,
        tools: List[str],
        timeout: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Execute task via SDK."""

    async def cleanup(self) -> None:
        """Cleanup and shutdown server."""

    def _ensure_server_running(self) -> None:
        """Start server if not running."""

    def _wait_for_server_ready(self, timeout: int) -> bool:
        """Wait for server to become healthy."""
```

**Configuration:**

```python
provider = OpenCodeSDKProvider(
    server_url="http://localhost:4096",  # Server URL
    port=4096,                           # Port for auto-start
    startup_timeout=30,                  # Max wait for startup
    auto_start_server=True               # Auto-start if not running
)
```

### 2. Server Lifecycle Management

**Startup Flow:**

```
┌─────────────────┐
│ initialize()    │
└────────┬────────┘
         │
         ▼
┌────────────────────────┐
│ Check server health    │
│ GET /health            │
└────────┬───────────────┘
         │
    ┌────┴────┐
    │ Running?│
    └────┬────┘
         │
    No   │   Yes
    ┌────┴────┐
    ▼         ▼
┌─────────────────┐  ┌──────────────┐
│ Start server    │  │ Server ready │
│ subprocess      │  └──────────────┘
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ Wait for /health OK  │
│ (up to 30s)          │
└──────────┬───────────┘
           │
           ▼
    ┌──────────────┐
    │ Server ready │
    └──────────────┘
```

**Health Check:**

```python
def _is_server_healthy(self) -> bool:
    """Check if server is healthy."""
    try:
        response = requests.get(
            f"{self.server_url}/health",
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False
```

**Shutdown Flow:**

```
┌─────────────────┐
│ cleanup()       │
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ Close SDK session    │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Shutdown server      │
│ POST /shutdown       │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Cleanup process      │
└──────────────────────┘
```

### 3. ProviderFactory Integration

**Registration:**

```python
# gao_dev/core/providers/factory.py

class ProviderFactory:
    def _register_builtin_providers(self) -> None:
        """Register all built-in providers."""
        self._registry["claude-code"] = ClaudeCodeProvider
        self._registry["opencode"] = OpenCodeProvider  # CLI (backward compat)
        self._registry["opencode-cli"] = OpenCodeProvider  # CLI (explicit)
        self._registry["opencode-sdk"] = OpenCodeSDKProvider  # SDK (recommended)
```

**Provider Selection:**

```python
# Via environment variable
export AGENT_PROVIDER=opencode-sdk

# Or via code
factory = ProviderFactory()
provider = factory.create_provider("opencode-sdk")
```

### 4. ProcessExecutor Integration

**Environment Variable Support:**

```python
# gao_dev/core/services/process_executor.py

class ProcessExecutor:
    def __init__(
        self,
        project_root: Path,
        provider_name: str = "claude-code",
        ...
    ):
        # Check environment variable (priority: env > parameter)
        env_provider = os.getenv("AGENT_PROVIDER")
        if env_provider:
            provider_name = env_provider

        # Create provider
        factory = ProviderFactory()
        self.provider = factory.create_provider(provider_name)
```

### 5. Backward Compatibility

**Legacy CLI Provider:**

```python
# gao_dev/core/providers/opencode.py

class OpenCodeProvider(IAgentProvider):
    """CLI-based provider (DEPRECATED)."""

    def __init__(self, ...):
        # Emit deprecation warning
        warnings.warn(
            "OpenCodeProvider is deprecated. "
            "Use OpenCodeSDKProvider (opencode-sdk) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        ...

# Alias for clarity
OpenCodeCLIProvider = OpenCodeProvider
```

**Provider Mapping:**

| Provider Name | Class | Status | Description |
|---------------|-------|--------|-------------|
| `claude-code` | `ClaudeCodeProvider` | Active | Claude Code CLI |
| `opencode` | `OpenCodeProvider` | Deprecated | CLI (backward compat) |
| `opencode-cli` | `OpenCodeProvider` | Legacy | CLI (explicit) |
| `opencode-sdk` | `OpenCodeSDKProvider` | **Recommended** | SDK (reliable) |

## Data Flow

### Task Execution Flow

```
1. User Request
   └─> ProcessExecutor.execute_agent_task(task, model, tools)

2. Provider Selection
   └─> Read AGENT_PROVIDER env var
   └─> Create provider via ProviderFactory
   └─> Validate provider configuration

3. SDK Provider Execution
   └─> Ensure server is running (_ensure_server_running)
   └─> Create SDK session (session.create)
   └─> Send task via SDK (session.chat)
   └─> Stream response back to caller
   └─> Cleanup session

4. Response Processing
   └─> Parse SDK response
   └─> Yield output to caller
   └─> Handle errors (retry if needed)
   └─> Log metrics
```

### Model Name Translation

```python
# Canonical name -> Provider-specific ID
MODEL_MAP = {
    "sonnet-4.5": ("anthropic", "claude-sonnet-4.5"),
    "opus-4": ("anthropic", "claude-opus-4"),
    "gpt-4": ("openai", "gpt-4"),
}

def translate_model_name(self, canonical_name: str) -> tuple[str, str]:
    """Translate canonical name to (provider_id, model_id)."""
    if canonical_name in self.MODEL_MAP:
        return self.MODEL_MAP[canonical_name]
    raise ModelNotSupportedError(canonical_name)
```

## Error Handling

### Error Hierarchy

```
ProviderError (base)
├── ProviderInitializationError
│   └── Server startup failed
├── ProviderConfigurationError
│   └── Invalid configuration
├── ProviderExecutionError
│   └── Task execution failed
├── ModelNotSupportedError
│   └── Unknown model name
└── ProviderTimeoutError
    └── Operation timed out
```

### Error Handling Strategy

```python
try:
    async for result in provider.execute_task(...):
        yield result

except ProviderInitializationError as e:
    # Server failed to start - terminal error
    logger.error("server_startup_failed", error=str(e))
    raise

except ProviderExecutionError as e:
    # Task execution failed - may be retryable
    if e.is_retryable():
        logger.warning("task_execution_failed_retrying", error=str(e))
        # Retry logic
    else:
        logger.error("task_execution_failed_terminal", error=str(e))
        raise

except Exception as e:
    # Unexpected error
    logger.error("unexpected_error", error=str(e), exc_info=True)
    raise ProviderExecutionError(f"Unexpected error: {e}") from e
```

## Configuration

### Environment Variables

```bash
# Provider selection
AGENT_PROVIDER=opencode-sdk

# API keys (choose one)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Server configuration (optional)
OPENCODE_PORT=4096
OPENCODE_SERVER_URL=http://localhost:4096
```

### Configuration File

```yaml
# config.yaml
provider:
  name: opencode-sdk
  config:
    server_url: http://localhost:4096
    port: 4096
    startup_timeout: 30
    auto_start_server: true
    api_key: ${ANTHROPIC_API_KEY}
```

### Provider Config Schema

```json
{
  "type": "object",
  "properties": {
    "server_url": {
      "type": "string",
      "description": "URL of OpenCode server",
      "default": "http://localhost:4096"
    },
    "port": {
      "type": "integer",
      "description": "Port for server (if auto-starting)",
      "default": 4096
    },
    "startup_timeout": {
      "type": "integer",
      "description": "Max seconds to wait for server startup",
      "default": 30
    },
    "auto_start_server": {
      "type": "boolean",
      "description": "Auto-start server if not running",
      "default": true
    }
  }
}
```

## Performance Considerations

### Startup Performance

| Phase | CLI Provider | SDK Provider | Improvement |
|-------|-------------|--------------|-------------|
| Provider init | ~0.1s | ~0.1s | Same |
| Server check | N/A | ~0.1s | New overhead |
| Server start (cold) | N/A | ~2-3s | One-time cost |
| Task execution | 2-5s | 0.5-1s | 2-5x faster |
| **Total (warm)** | **2-5s** | **0.5-1s** | **2-5x faster** |
| **Total (cold)** | **2-5s** | **2.5-4s** | Comparable |

### Resource Usage

```
CLI Provider:
- Memory: ~50MB per subprocess
- CPU: High during subprocess startup
- Processes: 1 per task

SDK Provider:
- Memory: ~100MB (server + client)
- CPU: Low (persistent server)
- Processes: 1 server (shared across tasks)
```

### Scalability

```
CLI Provider:
- Tasks: Linear growth in processes
- Overhead: High (subprocess per task)
- Max concurrent: ~10-20

SDK Provider:
- Tasks: Constant 1 server
- Overhead: Low (shared server)
- Max concurrent: ~100+
```

## Testing Strategy

### Unit Tests

```python
# tests/core/providers/test_opencode_sdk.py

def test_sdk_provider_initialization():
    """Test provider initializes correctly."""

def test_sdk_provider_server_lifecycle():
    """Test server start/stop lifecycle."""

def test_sdk_provider_task_execution():
    """Test task execution via SDK."""

def test_sdk_provider_error_handling():
    """Test error handling and retries."""
```

### Integration Tests

```python
# tests/integration/test_opencode_sdk_integration.py

async def test_provider_factory_creates_sdk_provider():
    """Test factory creates SDK provider."""

async def test_process_executor_uses_sdk_provider():
    """Test ProcessExecutor uses SDK provider."""

async def test_environment_variable_provider_selection():
    """Test AGENT_PROVIDER env var works."""
```

### End-to-End Tests

```bash
# Manual E2E test
export AGENT_PROVIDER=opencode-sdk
gao-dev sandbox run sandbox/benchmarks/simple-test.yaml

# Expected: Benchmark completes successfully
```

## Security Considerations

### API Key Management

```python
# Good: Load from environment
api_key = os.getenv("ANTHROPIC_API_KEY")

# Bad: Hardcode in code
api_key = "sk-ant-..."  # NEVER DO THIS
```

### Server Security

```python
# Server runs locally on localhost
server_url = "http://localhost:4096"  # Not exposed externally

# Health check only (no sensitive data)
requests.get(f"{server_url}/health")
```

### Process Isolation

```python
# Server runs in separate process
# Isolated from GAO-Dev application
# Clean shutdown on exit (atexit handler)
```

## Monitoring and Observability

### Structured Logging

```python
logger.info(
    "opencode_sdk_task_execution",
    model=model,
    tools=tools,
    timeout=timeout,
    server_url=self.server_url
)
```

### Metrics Tracking

```python
# Collected automatically by GAO-Dev
- task_duration_seconds
- api_calls_total
- errors_total
- server_startup_duration_seconds
```

### Health Checks

```python
# Periodic health checks
async def check_provider_health():
    is_healthy = await provider.validate_configuration()
    return is_healthy
```

## Future Enhancements

### Planned Features

1. **Connection Pooling** - Reuse SDK sessions across tasks
2. **Retry Logic** - Automatic retry with exponential backoff
3. **Circuit Breaker** - Prevent cascading failures
4. **Metrics Dashboard** - Real-time provider metrics
5. **Multi-Server Support** - Load balancing across multiple servers

### Potential Optimizations

1. **Session Caching** - Cache sessions for faster execution
2. **Lazy Server Start** - Defer server start until first task
3. **Connection Keep-Alive** - Maintain persistent connections
4. **Batch Processing** - Execute multiple tasks in single session

## Migration Path

### From CLI to SDK Provider

```bash
# Step 1: Update environment variable
export AGENT_PROVIDER=opencode-sdk

# Step 2: Verify configuration
gao-dev list-agents

# Step 3: Run tests
pytest tests/

# Step 4: Deploy to production
```

See [MIGRATION.md](MIGRATION.md) for detailed migration guide.

## References

- **OpenCode GitHub**: https://github.com/opencode-ai/opencode
- **OpenCode SDK**: https://pypi.org/project/opencode-ai/
- **GAO-Dev Provider Abstraction**: Epic 11
- **Provider Interface**: `gao_dev/core/providers/base.py`

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-06
**Author**: GAO-Dev Team
**Status**: Complete
