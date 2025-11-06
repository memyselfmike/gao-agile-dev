# OpenCode SDK Integration Feature

**Epic 19**: Implement OpenCode SDK-based Provider
**Status**: Complete
**Priority**: High
**Completed**: 2025-11-06

## Overview

Replace the problematic CLI-based OpenCode provider with a robust SDK-based implementation using OpenCode's Python SDK (`opencode-ai`) and HTTP API architecture.

## Problem Statement

The current OpenCode CLI provider (Epic 11) experiences subprocess hanging issues when executing tasks. OpenCode was designed as a client-server architecture with a Python SDK for programmatic access, making the CLI subprocess approach suboptimal.

## Solution

Implemented a new `OpenCodeSDKProvider` that:
- Uses the `opencode-ai` Python SDK for native API access
- Manages an OpenCode server lifecycle (auto-start, health checks, shutdown)
- Provides reliable, non-blocking task execution
- Maintains compatibility with the provider abstraction interface
- Supports environment variable configuration (`AGENT_PROVIDER=opencode-sdk`)

## Success Criteria

- ✅ Benchmark completes successfully without hanging
- ✅ All existing tests pass
- ✅ SDK provider properly manages server lifecycle
- ✅ Documentation updated (README, ARCHITECTURE, MIGRATION)
- ✅ Provider switchable via `AGENT_PROVIDER` environment variable
- ✅ Backward compatibility maintained (CLI provider still available)
- ✅ Deprecation warnings added to CLI provider

## Dependencies

- **Requires**: Epic 11 (Agent Provider Abstraction) - Complete
- **Builds On**: Existing provider infrastructure

## Documentation

- [PRD](./PRD.md) - Product Requirements Document
- [Architecture](./ARCHITECTURE.md) - Technical Architecture
- [Epics](./epics.md) - Epic and Story Breakdown
- [Stories](./stories/) - Individual Story Files

## Quick Start

### Using the SDK Provider

```bash
# 1. Install OpenCode CLI (if not already installed)
npm install -g opencode-ai@latest

# 2. Set API key
export ANTHROPIC_API_KEY=your_api_key_here

# 3. Set provider to OpenCode SDK
export AGENT_PROVIDER=opencode-sdk

# 4. Verify provider is working
gao-dev list-agents

# 5. Run a benchmark
gao-dev sandbox run sandbox/benchmarks/workflow-driven-todo.yaml
```

### Migration from CLI Provider

If you're currently using the CLI provider (`opencode` or `opencode-cli`), see the [Migration Guide](MIGRATION.md) for step-by-step instructions.

```bash
# Quick migration
export AGENT_PROVIDER=opencode-sdk

# Verify it works
gao-dev list-agents
```

## Provider Options

GAO-Dev now supports three OpenCode provider options:

| Provider Name | Description | Status | Use When |
|---------------|-------------|--------|----------|
| `opencode-sdk` | SDK-based provider (HTTP API) | **Recommended** | Production, reliability needed |
| `opencode-cli` | CLI-based provider (subprocess) | Legacy | Backward compatibility |
| `opencode` | Alias for `opencode-cli` | Deprecated | Backward compatibility |

## Configuration

### Environment Variables

```bash
# Provider selection
AGENT_PROVIDER=opencode-sdk

# API keys (choose one based on AI provider)
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Optional: Server configuration
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
```

## Features

### SDK Provider Features

- ✅ **No subprocess hanging** - Direct API calls, no subprocess management
- ✅ **Automatic server lifecycle** - Auto-start, health checks, graceful shutdown
- ✅ **Better error handling** - Structured errors with retry logic
- ✅ **Performance** - Lower overhead, faster startup
- ✅ **Observability** - Structured logging, metrics tracking

### Backward Compatibility

- ✅ CLI provider still available as `opencode-cli`
- ✅ Deprecation warnings guide users to SDK provider
- ✅ All existing code continues to work
- ✅ Easy rollback if issues occur

## Troubleshooting

### SDK provider not working?

1. **Check OpenCode is installed:**
   ```bash
   opencode --version
   ```

2. **Check SDK is installed:**
   ```bash
   python -c "from opencode_ai import Opencode; print('OK')"
   ```

3. **Check server is running:**
   ```bash
   curl http://localhost:4096/health
   ```

4. **Check API key is set:**
   ```bash
   echo $ANTHROPIC_API_KEY
   ```

### Need help?

- See [Migration Guide](MIGRATION.md) for detailed troubleshooting
- See [Architecture Documentation](ARCHITECTURE.md) for technical details
- Open a GitHub issue with error logs

---

**Created**: 2025-11-06
**Last Updated**: 2025-11-06
**Completed**: 2025-11-06
**Owner**: GAO-Dev Team
