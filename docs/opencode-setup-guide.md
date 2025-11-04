# OpenCode Setup Guide

**Version**: OpenCode v0.1.x
**Target**: GAO-Dev developers and users
**Last Updated**: 2025-11-04

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

---

## Overview

OpenCode is an open-source AI coding agent that supports 75+ LLM providers through Models.dev integration. This guide walks you through installing and configuring OpenCode for use with GAO-Dev.

**Why OpenCode?**
- Multi-provider support (Anthropic, OpenAI, Google, and more)
- Open-source (MIT license)
- Active development and community
- Cost optimization through provider switching

**When to use OpenCode vs Claude Code:**
- Use **Claude Code** if you only need Anthropic models (default, recommended)
- Use **OpenCode** if you need OpenAI, Google, or other providers

---

## Prerequisites

### System Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux
- **Network**: Internet access for AI provider APIs
- **Disk Space**: ~50-100MB for OpenCode binary

### API Keys

You'll need API keys for the providers you want to use:

- **Anthropic**: Get from https://console.anthropic.com
- **OpenAI**: Get from https://platform.openai.com/api-keys
- **Google**: Get from https://aistudio.google.com

**Note**: At least one API key is required.

---

## Installation

### Method 1: Quick Install (Recommended)

**Best for**: Most users, all platforms

```bash
curl -fsSL https://opencode.ai/install | bash
```

This will:
1. Download the latest OpenCode binary
2. Install to appropriate directory
3. Add to PATH automatically

**Custom Installation Directory**:
```bash
OPENCODE_INSTALL_DIR=/usr/local/bin curl -fsSL https://opencode.ai/install | bash
```

---

### Method 2: Package Managers

#### npm/bun/pnpm (Cross-platform)
```bash
# npm
npm i -g opencode-ai@latest

# bun
bun install -g opencode-ai@latest

# pnpm
pnpm add -g opencode-ai@latest
```

#### Homebrew (macOS/Linux)
```bash
brew install opencode
```

#### Windows (Scoop)
```bash
scoop bucket add extras
scoop install extras/opencode
```

#### Windows (Chocolatey)
```bash
choco install opencode
```

#### Arch Linux
```bash
paru -S opencode-bin
```

---

### Installation Directory Priority

OpenCode installs to the first available directory:

1. `$OPENCODE_INSTALL_DIR` (if set)
2. `$XDG_BIN_DIR` (if set)
3. `$HOME/bin` (if exists)
4. `$HOME/.opencode/bin` (default fallback)

**Verify Installation Location**:
```bash
which opencode
# Should output: /path/to/opencode
```

---

## Configuration

### Step 1: Set API Keys (Environment Variables)

**Recommended method**: Set environment variables

#### Linux/macOS

Add to `~/.bashrc`, `~/.zshrc`, or `~/.profile`:

```bash
# Anthropic (Claude)
export ANTHROPIC_API_KEY=sk-ant-api03-...

# OpenAI (GPT)
export OPENAI_API_KEY=sk-...

# Google (Gemini)
export GOOGLE_API_KEY=...
```

Reload shell:
```bash
source ~/.bashrc
# OR
source ~/.zshrc
```

#### Windows (PowerShell)

Add to PowerShell profile (`$PROFILE`):

```powershell
# Anthropic (Claude)
$env:ANTHROPIC_API_KEY = "sk-ant-api03-..."

# OpenAI (GPT)
$env:OPENAI_API_KEY = "sk-..."

# Google (Gemini)
$env:GOOGLE_API_KEY = "..."
```

Reload profile:
```powershell
. $PROFILE
```

#### Windows (Command Prompt)

```cmd
setx ANTHROPIC_API_KEY "sk-ant-api03-..."
setx OPENAI_API_KEY "sk-..."
setx GOOGLE_API_KEY "..."
```

**Note**: Restart terminal after setting environment variables.

---

### Step 2: Authenticate (Alternative Method)

If you prefer not to use environment variables:

```bash
opencode auth login
```

This will:
1. Prompt for provider selection
2. Ask for API key
3. Store credentials in `~/.local/share/opencode/auth.json`

**List authenticated providers**:
```bash
opencode auth list
```

**Logout (remove credentials)**:
```bash
opencode auth logout
```

---

### Step 3: Create Configuration File (Optional)

**Location**: `~/.config/opencode/opencode.json`

**Example Configuration**:
```json
{
  "model": "anthropic/claude-sonnet-4.5",
  "providers": {
    "anthropic": {
      "apiKey": "{env:ANTHROPIC_API_KEY}"
    },
    "openai": {
      "apiKey": "{env:OPENAI_API_KEY}"
    }
  },
  "debug": false
}
```

**Configuration Options**:
- `model`: Default model (format: `provider/model`)
- `providers`: Provider-specific settings
- `debug`: Enable debug logging
- Environment variable substitution: `{env:VAR_NAME}`

---

## Verification

### Step 1: Check Installation

```bash
opencode --version
```

**Expected output**:
```
opencode v0.1.x
```

---

### Step 2: List Available Models

```bash
opencode models
```

**Expected output** (if authenticated):
```
anthropic/claude-sonnet-4.5
anthropic/claude-opus-4.1
openai/gpt-5
openai/gpt-4-turbo
google/gemini-2.5-pro
```

**If no models listed**: Check API keys are set correctly.

---

### Step 3: Test Simple Execution

**Non-interactive mode** (used by GAO-Dev):

```bash
opencode run "Create a file named test.txt with content 'Hello, OpenCode!'"
```

**Expected behavior**:
- Command executes
- File `test.txt` created in current directory
- Output printed to stdout

**Verify file**:
```bash
cat test.txt
# Should output: Hello, OpenCode!
```

---

### Step 4: Test with Specific Provider

**Anthropic (Claude)**:
```bash
opencode run --model anthropic/claude-sonnet-4.5 "Write a Python hello world script"
```

**OpenAI (GPT)**:
```bash
opencode run --model openai/gpt-4 "Write a Python hello world script"
```

**Google (Gemini)**:
```bash
opencode run --model google/gemini-2.5-pro "Write a Python hello world script"
```

---

## Troubleshooting

### Problem: `opencode: command not found`

**Cause**: OpenCode not in PATH

**Solution 1**: Add installation directory to PATH

```bash
# Find installation location
find ~ -name opencode 2>/dev/null

# Add to PATH (Linux/macOS)
export PATH="$HOME/.opencode/bin:$PATH"

# Add to PATH (Windows)
$env:PATH += ";$HOME\.opencode\bin"
```

**Solution 2**: Reinstall with custom directory

```bash
OPENCODE_INSTALL_DIR=/usr/local/bin curl -fsSL https://opencode.ai/install | bash
```

---

### Problem: No models listed

**Cause**: API keys not set

**Check environment variables**:
```bash
# Linux/macOS
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
echo $GOOGLE_API_KEY

# Windows PowerShell
$env:ANTHROPIC_API_KEY
$env:OPENAI_API_KEY
$env:GOOGLE_API_KEY
```

**Solution**: Set API keys (see [Configuration](#configuration))

---

### Problem: API key authentication fails

**Cause**: Invalid or expired API key

**Verify API key**:
- Anthropic: https://console.anthropic.com/settings/keys
- OpenAI: https://platform.openai.com/api-keys
- Google: https://aistudio.google.com

**Solution**: Generate new API key and update configuration

---

### Problem: Permission denied errors

**Cause**: Insufficient file permissions

**Solution (Linux/macOS)**:
```bash
# Make executable
chmod +x ~/.opencode/bin/opencode

# If installed via package manager
sudo chown -R $USER:$USER ~/.opencode
```

**Solution (Windows)**:
- Run terminal as Administrator
- Check antivirus isn't blocking execution

---

### Problem: Execution fails with no output

**Cause**: Various (check logs)

**Enable debug logging**:
```bash
opencode --log-level debug run "Test task"
```

**Check logs**:
```bash
opencode --print-logs
```

**Common issues**:
1. API rate limit exceeded
2. Network connectivity issues
3. Invalid model name
4. Insufficient API credits

---

### Problem: Windows-specific issues

**Issue**: Path separator errors

**Solution**: Use forward slashes or double backslashes
```bash
# Good
opencode run --cwd /c/Projects/myapp "Task"

# Also good
opencode run --cwd C:\\Projects\\myapp "Task"
```

**Issue**: Encoding errors

**Solution**: Set PowerShell encoding
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

---

## Next Steps

### For GAO-Dev Users

1. **Verify setup**:
   ```bash
   gao-dev providers validate
   ```

2. **Update agent configuration** (optional):
   Edit `gao_dev/config/agents/amelia.yaml`:
   ```yaml
   agent:
     configuration:
       provider: "opencode"
       provider_config:
         ai_provider: "anthropic"  # or "openai", "google"
   ```

3. **Test with GAO-Dev**:
   ```bash
   gao-dev create-prd --name "Test Project"
   ```

---

### For Direct OpenCode Usage

**Interactive TUI mode**:
```bash
opencode
```

**Non-interactive mode** (scripting):
```bash
opencode run "Your task here"
```

**With specific model**:
```bash
opencode run --model anthropic/claude-sonnet-4.5 "Your task"
```

**Read prompt from file**:
```bash
opencode run --file prompt.txt
```

---

### Advanced Configuration

**Project-specific config**:
Create `.opencode/config.json` in project root:
```json
{
  "model": "openai/gpt-4",
  "agents": {
    "code-reviewer": {
      "systemPrompt": "You are a code reviewer...",
      "model": "anthropic/claude-opus-4.1"
    }
  }
}
```

**Custom agents**:
```bash
opencode agent create
```

---

## Resources

- **Official Documentation**: https://opencode.ai/docs
- **GitHub Repository**: https://github.com/sst/opencode
- **Models Registry**: https://models.dev
- **GAO-Dev Provider Guide**: `docs/provider-selection-guide.md`
- **GAO-Dev Provider Configuration**: `docs/provider-configuration-reference.md`

---

## Support

**GAO-Dev Issues**:
- Open issue: https://github.com/your-org/gao-agile-dev/issues

**OpenCode Issues**:
- Open issue: https://github.com/sst/opencode/issues
- Community: https://discord.gg/opencode (if available)

---

## Upgrading

**Check for updates**:
```bash
opencode upgrade
```

**Upgrade to specific version**:
```bash
opencode upgrade v0.1.50
```

**Upgrade method**:
```bash
# Use specific method
opencode upgrade --method brew
opencode upgrade --method npm
```

---

**Setup Complete!** OpenCode is now ready to use with GAO-Dev or standalone.

For provider selection guidance, see [Provider Selection Guide](provider-selection-guide.md).
