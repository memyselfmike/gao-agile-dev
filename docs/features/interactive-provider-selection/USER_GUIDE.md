# Interactive Provider Selection - User Guide

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Version**: 1.0
**Last Updated**: 2025-01-12

---

## Table of Contents

1. [Overview](#overview)
2. [First-Time Setup](#first-time-setup)
3. [Returning User Flow](#returning-user-flow)
4. [Changing Providers](#changing-providers)
5. [Using Environment Variables](#using-environment-variables)
6. [Feature Flag Usage](#feature-flag-usage)
7. [Working with Local Models](#working-with-local-models)
8. [Command Reference](#command-reference)

---

## Overview

Interactive Provider Selection allows you to choose which AI provider GAO-Dev uses when you start the REPL with `gao-dev start`. Instead of being locked into a single provider, you can interactively select from:

- **claude-code**: Claude Code CLI (Anthropic)
- **opencode**: OpenCode CLI (Multi-provider support)
- **direct-api-anthropic**: Direct Anthropic API

### Key Features

- **Interactive Prompts**: Beautiful Rich-formatted tables for provider selection
- **Preference Persistence**: Save your choices for future sessions
- **Validation**: Automatic validation before starting REPL
- **Environment Variable Bypass**: Skip prompts with `AGENT_PROVIDER` env var
- **Local Model Support**: Use Ollama for free local models
- **Cross-Platform**: Works on Windows, macOS, and Linux

---

## First-Time Setup

When you run `gao-dev start` for the first time, you'll be guided through an interactive setup process.

### Step-by-Step Walkthrough

**1. Start GAO-Dev**

```bash
cd your-project
gao-dev start
```

**2. See Provider Selection Table**

```
Available AI Providers
┌────────┬─────────────────────┬──────────────────────────────────┐
│ Option │ Provider            │ Description                      │
├────────┼─────────────────────┼──────────────────────────────────┤
│ 1      │ claude-code         │ Claude Code CLI (Anthropic)      │
│ 2      │ opencode            │ OpenCode CLI (Multi-provider)    │
│ 3      │ direct-api-anthropic│ Direct Anthropic API             │
└────────┴─────────────────────┴──────────────────────────────────┘

Select provider [1-3] (default: 1):
```

**3. Choose Your Provider**

- Press **Enter** to use the default (claude-code)
- Or type **2** for OpenCode
- Or type **3** for Direct API

**4. Configure Provider-Specific Settings** *(OpenCode only)*

If you selected OpenCode, you'll see additional prompts:

```
OpenCode Configuration

Use local model via Ollama? [y/N]:
```

- Type **y** to use local models (Ollama)
- Press **Enter** for cloud models (Anthropic/OpenAI/Google)

**5. Validation**

The system validates your selection:

```
Validating opencode...
Checking opencode CLI availability...
opencode CLI available
Checking Ollama models...
Found 3 Ollama model(s)
```

**6. Save Preferences** *(Optional)*

```
Save these preferences? [y/N]:
```

- Type **y** to save for future sessions
- Press **Enter** to skip saving (prompts again next time)

**7. REPL Starts**

```
Starting GAO-Dev with OpenCode + deepseek-r1...

[GAO-Dev REPL greeting...]
```

---

## Returning User Flow

When you've saved preferences, subsequent startups are much faster.

### Typical Flow

**1. Start GAO-Dev**

```bash
gao-dev start
```

**2. See Saved Configuration**

```
Saved Configuration Found:
  provider: opencode
  model: deepseek-r1

Use saved configuration? [Y/n/c (change)] (default: Y):
```

**3. Choose Action**

- Press **Enter** to use saved config (default)
- Type **n** to reconfigure from scratch
- Type **c** to change specific settings

**4. REPL Starts Immediately**

```
Using saved configuration
Starting GAO-Dev with OpenCode + deepseek-r1...

[GAO-Dev REPL ready]
```

---

## Changing Providers

You can change your provider selection at any time.

### Method 1: Delete Preferences File

```bash
# Delete preferences to trigger first-time setup
rm .gao-dev/provider_preferences.yaml
gao-dev start
```

### Method 2: Decline Saved Preferences

When prompted "Use saved configuration?", type **n**:

```
Use saved configuration? [Y/n/c (change)]: n
```

This will trigger the full interactive setup again.

### Method 3: Use Environment Variable (Temporary)

Override preferences for a single session:

```bash
export AGENT_PROVIDER=claude-code
gao-dev start  # Uses claude-code this time only
```

### Method 4: Edit Preferences File Directly

Edit `.gao-dev/provider_preferences.yaml`:

```yaml
version: "1.0.0"
provider:
  name: "claude-code"  # Change this
  model: "sonnet-4.5"  # Change this
  config:
    api_key_env: "ANTHROPIC_API_KEY"
metadata:
  last_updated: "2025-01-12T10:30:00Z"
  cli_version: "1.0.0"
```

---

## Using Environment Variables

Environment variables allow you to bypass interactive prompts entirely.

### Setting AGENT_PROVIDER

**Format**: `provider` or `provider:model`

```bash
# Use claude-code with default model (sonnet-4.5)
export AGENT_PROVIDER=claude-code

# Use opencode with specific model (deepseek-r1)
export AGENT_PROVIDER=opencode:deepseek-r1

# Use direct API with specific model
export AGENT_PROVIDER=direct-api-anthropic:claude-3-5-sonnet-20241022
```

### Permanent Configuration

**Bash/Zsh** (`~/.bashrc` or `~/.zshrc`):

```bash
echo 'export AGENT_PROVIDER=opencode:deepseek-r1' >> ~/.bashrc
source ~/.bashrc
```

**PowerShell** (`$PROFILE`):

```powershell
[Environment]::SetEnvironmentVariable("AGENT_PROVIDER", "opencode:deepseek-r1", "User")
```

**Windows CMD** (System-wide):

```cmd
setx AGENT_PROVIDER "opencode:deepseek-r1"
```

### CI/CD Usage

In CI/CD pipelines, set the environment variable in your workflow:

**GitHub Actions**:

```yaml
jobs:
  test:
    env:
      AGENT_PROVIDER: claude-code
    steps:
      - run: gao-dev start
```

**GitLab CI**:

```yaml
test:
  variables:
    AGENT_PROVIDER: "claude-code"
  script:
    - gao-dev start
```

**Docker**:

```dockerfile
ENV AGENT_PROVIDER=claude-code
```

---

## Feature Flag Usage

The interactive provider selection feature can be disabled using a feature flag.

### Disabling the Feature

Edit `gao_dev/config/defaults.yaml`:

```yaml
features:
  # Set to false to disable interactive provider selection
  interactive_provider_selection: false
```

### When to Disable

- **Rollback**: If issues arise in production
- **Legacy Systems**: Maintain old behavior for compatibility
- **Automated Scripts**: Skip prompts entirely

When disabled, GAO-Dev falls back to:
1. Environment variable (`AGENT_PROVIDER`)
2. Hardcoded defaults (claude-code + sonnet-4.5)

---

## Working with Local Models

Save costs by using free local models via Ollama.

### Prerequisites

**1. Install Ollama**

Visit [https://ollama.ai/download](https://ollama.ai/download) and follow instructions for your platform.

**Windows**:
```bash
# Download installer from https://ollama.ai/download
```

**macOS**:
```bash
brew install ollama
```

**Linux**:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**2. Pull a Model**

```bash
# Recommended for coding (7B)
ollama pull deepseek-r1

# Alternative models
ollama pull llama2      # General purpose (7B)
ollama pull codellama   # Coding-focused (13B)
ollama pull mistral     # Fast & capable (7B)
```

**3. Verify Installation**

```bash
ollama list
```

### Selecting Local Model in GAO-Dev

**1. Run Setup**

```bash
gao-dev start
```

**2. Choose OpenCode**

```
Select provider [1-3]: 2
```

**3. Choose Local Model**

```
Use local model via Ollama? [y/N]: y
```

**4. Detect Models**

```
Detecting Ollama models (may take a moment)...

Available Models
┌────────┬────────────┬──────┐
│ Option │ Model      │ Size │
├────────┼────────────┼──────┤
│ 1      │ deepseek-r1│ 7B   │
│ 2      │ llama2     │ 7B   │
│ 3      │ codellama  │ 13B  │
└────────┴────────────┴──────┘

Select model [1-3] (default: 1):
```

**5. Save Preferences**

```
Save these preferences? [y/N]: y
```

### Benefits of Local Models

- **Zero API Costs**: No per-token charges
- **Offline Development**: Work without internet
- **Privacy**: Data never leaves your machine
- **Speed**: Low latency for local processing

### Performance Tips

- Use **deepseek-r1** (7B) for best coding performance
- Use **codellama** (13B) for more complex tasks (slower)
- Ensure Ollama service is running: `ollama serve`
- Check available RAM (7B models need ~8GB, 13B need ~16GB)

---

## Command Reference

### gao-dev start

Start GAO-Dev REPL with interactive provider selection.

```bash
gao-dev start
```

**Behavior**:
1. Checks `AGENT_PROVIDER` env var (bypasses prompts if set)
2. Checks saved preferences (prompts to use if exist)
3. Shows interactive prompts (first-time setup)
4. Validates provider configuration
5. Starts REPL with selected provider

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AGENT_PROVIDER` | Override provider selection | `export AGENT_PROVIDER=opencode` |
| `ANTHROPIC_API_KEY` | API key for Anthropic providers | `export ANTHROPIC_API_KEY=sk-ant-...` |
| `OPENAI_API_KEY` | API key for OpenAI (via OpenCode) | `export OPENAI_API_KEY=sk-...` |
| `GOOGLE_API_KEY` | API key for Google (via OpenCode) | `export GOOGLE_API_KEY=...` |

### Preferences File

**Location**: `.gao-dev/provider_preferences.yaml`

**Format**:

```yaml
version: "1.0.0"
provider:
  name: "opencode"
  model: "deepseek-r1"
  config:
    ai_provider: "ollama"
    use_local: true
metadata:
  last_updated: "2025-01-12T10:30:00Z"
  cli_version: "1.0.0"
```

**Operations**:

```bash
# View preferences
cat .gao-dev/provider_preferences.yaml

# Delete preferences (trigger first-time setup)
rm .gao-dev/provider_preferences.yaml

# Backup preferences
cp .gao-dev/provider_preferences.yaml{,.backup}

# Restore from backup
cp .gao-dev/provider_preferences.yaml{.backup,}
```

---

## Troubleshooting

### Issue: "CLI not found"

**Symptom**: `opencode CLI not found in PATH`

**Solutions**:
```bash
# Install OpenCode
npm install -g opencode

# Verify installation
opencode --version

# Check PATH
echo $PATH
```

### Issue: "No Ollama models found"

**Symptom**: `No Ollama models found` warning

**Solutions**:
```bash
# Pull a model
ollama pull deepseek-r1

# Verify Ollama running
ollama list

# Start Ollama service (if not running)
ollama serve
```

### Issue: "API key not set"

**Symptom**: `ANTHROPIC_API_KEY not set`

**Solutions**:
```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-api03-...

# Make permanent (add to ~/.bashrc)
echo 'export ANTHROPIC_API_KEY=sk-ant-api03-...' >> ~/.bashrc
```

### Issue: Validation takes too long

**Symptom**: "Detecting Ollama models (may take a moment)..." hangs

**Cause**: Slow disk (HDD/NAS) or large model count

**Solution**: Wait up to 10 seconds (timeout built-in)

For more troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## Best Practices

### 1. Save Preferences for Regular Use

Always save preferences if you'll use the same provider regularly:

```
Save these preferences? [y/N]: y
```

### 2. Use Environment Variables for Testing

Test different providers without changing saved preferences:

```bash
AGENT_PROVIDER=claude-code gao-dev start
```

### 3. Keep API Keys Secure

Never commit API keys to version control:

```bash
# .gitignore
.env
*.env
```

Use environment variables or `.env` files:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Use Local Models for Development

Save costs by using Ollama during development:

```bash
# Use free local model for dev
export AGENT_PROVIDER=opencode:deepseek-r1

# Use Claude for production
export AGENT_PROVIDER=claude-code
```

### 5. Monitor Validation Time

If validation consistently takes >5 seconds, check:
- Network connectivity (for cloud providers)
- Ollama service status (for local models)
- Disk performance (slow disks affect Ollama detection)

---

## Next Steps

- **Examples**: See [examples/](examples/) for complete workflows
- **FAQ**: Read [FAQ.md](FAQ.md) for common questions
- **API Reference**: See [API_REFERENCE.md](API_REFERENCE.md) for developers
- **Troubleshooting**: Consult [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for issues

---

**Version**: 1.0
**Last Updated**: 2025-01-12
**Epic**: 35 - Interactive Provider Selection at Startup
