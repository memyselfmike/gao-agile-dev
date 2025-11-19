# Environment Variables Reference

Complete reference for all environment variables supported by GAO-Dev.

## Table of Contents

- [Provider Configuration](#provider-configuration)
- [API Keys](#api-keys)
- [System Configuration](#system-configuration)
- [Paths and Directories](#paths-and-directories)
- [Debug and Logging](#debug-and-logging)
- [CI/CD Configuration](#cicd-configuration)
- [Examples](#examples)

## Provider Configuration

### AGENT_PROVIDER

Skip interactive provider selection and use the specified provider.

| Property | Value |
|----------|-------|
| Required | No |
| Default | None (interactive selection) |
| Values | `claude-code`, `opencode`, `direct-api-anthropic`, `direct-api-openai` |

**Example:**
```bash
# Linux/macOS
export AGENT_PROVIDER=claude-code

# Windows CMD
set AGENT_PROVIDER=claude-code

# Windows PowerShell
$env:AGENT_PROVIDER="claude-code"
```

### GAO_DEV_MODEL

Override the default model for the selected provider.

| Property | Value |
|----------|-------|
| Required | No |
| Default | Provider-specific default |
| Values | Valid model name for the provider |

**Example:**
```bash
export GAO_DEV_MODEL=claude-sonnet-4-20250514
```

## API Keys

### ANTHROPIC_API_KEY

API key for Anthropic's Claude API.

| Property | Value |
|----------|-------|
| Required | Yes (for Claude-based providers) |
| Default | None |
| Format | `sk-ant-api03-...` |

**Example:**
```bash
export ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

**Getting a Key:**
1. Visit [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
2. Create a new API key
3. Copy and set the environment variable

### OPENAI_API_KEY

API key for OpenAI's API.

| Property | Value |
|----------|-------|
| Required | Yes (for OpenAI-based providers) |
| Default | None |
| Format | `sk-...` |

**Example:**
```bash
export OPENAI_API_KEY=sk-your-key-here
```

### AZURE_OPENAI_API_KEY

API key for Azure OpenAI Service.

| Property | Value |
|----------|-------|
| Required | Yes (for Azure OpenAI provider) |
| Default | None |
| Format | Provider-specific |

**Example:**
```bash
export AZURE_OPENAI_API_KEY=your-azure-key
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

## System Configuration

### GAO_DEV_DEBUG

Enable debug logging for troubleshooting.

| Property | Value |
|----------|-------|
| Required | No |
| Default | `false` |
| Values | `true`, `false` |

**Example:**
```bash
export GAO_DEV_DEBUG=true
```

**When to Enable:**
- Troubleshooting provider issues
- Debugging workflow execution
- Investigating API errors

### BENCHMARK_TIMEOUT_SECONDS

Default timeout for benchmark execution.

| Property | Value |
|----------|-------|
| Required | No |
| Default | `14400` (4 hours) |
| Values | Positive integer (seconds) |

**Example:**
```bash
export BENCHMARK_TIMEOUT_SECONDS=7200  # 2 hours
```

## Paths and Directories

### SANDBOX_ROOT

Root directory for sandbox projects and benchmarks.

| Property | Value |
|----------|-------|
| Required | No |
| Default | `./sandbox` |
| Values | Absolute or relative path |

**Example:**
```bash
export SANDBOX_ROOT=/data/gao-dev/sandbox
```

### METRICS_OUTPUT_DIR

Directory for metrics and benchmark reports.

| Property | Value |
|----------|-------|
| Required | No |
| Default | `$SANDBOX_ROOT/metrics` |
| Values | Absolute or relative path |

**Example:**
```bash
export METRICS_OUTPUT_DIR=/data/gao-dev/metrics
```

### GAO_DEV_CONFIG_DIR

Custom directory for GAO-Dev configuration files.

| Property | Value |
|----------|-------|
| Required | No |
| Default | `.gao-dev` (in project root) |
| Values | Absolute path |

**Example:**
```bash
export GAO_DEV_CONFIG_DIR=/etc/gao-dev
```

## Debug and Logging

### GAO_DEV_LOG_LEVEL

Set logging verbosity.

| Property | Value |
|----------|-------|
| Required | No |
| Default | `INFO` |
| Values | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

**Example:**
```bash
export GAO_DEV_LOG_LEVEL=DEBUG
```

### GAO_DEV_LOG_FORMAT

Customize log output format.

| Property | Value |
|----------|-------|
| Required | No |
| Default | `json` |
| Values | `json`, `text` |

**Example:**
```bash
export GAO_DEV_LOG_FORMAT=text
```

## CI/CD Configuration

### CI

Standard CI environment indicator.

| Property | Value |
|----------|-------|
| Required | No |
| Default | Not set |
| Values | `true`, `1` |

When set, GAO-Dev:
- Skips interactive prompts
- Uses headless mode
- Requires `AGENT_PROVIDER` to be set

**Example:**
```bash
export CI=true
export AGENT_PROVIDER=claude-code
export ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }}
```

### TERM

Terminal type for Rich formatting.

| Property | Value |
|----------|-------|
| Required | No |
| Default | System default |
| Values | `xterm`, `xterm-256color`, `dumb` |

**Example:**
```bash
# Disable colors in CI
export TERM=dumb
```

## Complete Environment File

Create a `.env` file in your project root:

```bash
# .env - GAO-Dev Environment Configuration

# Provider Configuration
AGENT_PROVIDER=claude-code
GAO_DEV_MODEL=

# API Keys (required based on provider)
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=

# Paths and Directories
SANDBOX_ROOT=./sandbox
METRICS_OUTPUT_DIR=./sandbox/metrics

# System Configuration
BENCHMARK_TIMEOUT_SECONDS=14400
GAO_DEV_DEBUG=false
GAO_DEV_LOG_LEVEL=INFO
GAO_DEV_LOG_FORMAT=json

# CI/CD (uncomment for automated environments)
# CI=true
# TERM=dumb
```

## Examples

### Development Environment

```bash
# ~/.bashrc or ~/.zshrc
export ANTHROPIC_API_KEY=sk-ant-api03-...
export GAO_DEV_DEBUG=true
export GAO_DEV_LOG_LEVEL=DEBUG
```

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/gao-dev.yml
env:
  AGENT_PROVIDER: claude-code
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  CI: true
  TERM: dumb
```

### Docker Environment

```bash
docker run -it \
  -e AGENT_PROVIDER=claude-code \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e GAO_DEV_DEBUG=false \
  -e SANDBOX_ROOT=/app/sandbox \
  gao-dev/gao-dev:latest
```

### Local Ollama Setup

```bash
export AGENT_PROVIDER=opencode
export OLLAMA_HOST=http://localhost:11434
# No API key needed for local models
```

### Production Environment

```bash
# /etc/environment or systemd service file
AGENT_PROVIDER=claude-code
ANTHROPIC_API_KEY=sk-ant-api03-...
GAO_DEV_DEBUG=false
GAO_DEV_LOG_LEVEL=WARNING
SANDBOX_ROOT=/var/lib/gao-dev/sandbox
METRICS_OUTPUT_DIR=/var/log/gao-dev/metrics
```

## Priority Order

When the same setting is configured in multiple places, GAO-Dev uses this priority:

1. **Command line arguments** (highest)
2. **Environment variables**
3. **`.env` file**
4. **Configuration files**
5. **Default values** (lowest)

## Validation

Check your environment configuration:

```bash
# View current environment
env | grep -E "GAO_DEV|AGENT_|ANTHROPIC|OPENAI"

# Run health check
gao-dev health

# Test provider selection
gao-dev start --dry-run
```

## Security Notes

1. **Never commit API keys** - Use `.env` files (gitignored) or secret managers
2. **Use secret managers in CI/CD** - GitHub Secrets, AWS Secrets Manager, etc.
3. **Rotate keys regularly** - Create new keys and revoke old ones
4. **Set file permissions** - `.env` should be `chmod 600`
5. **Audit access** - Monitor API key usage in provider dashboards

---

**See Also:**
- [Credential Management Guide](./credential-management.md)
- [Docker Deployment Guide](../getting-started/docker-deployment.md)
- [Troubleshooting Guide](../troubleshooting/common-errors.md)

---

**Last Updated**: 2025-11-19
