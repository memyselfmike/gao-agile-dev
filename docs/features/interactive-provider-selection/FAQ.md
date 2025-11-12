# Interactive Provider Selection - Frequently Asked Questions

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Version**: 1.0
**Last Updated**: 2025-01-12

---

## Table of Contents

- [General](#general)
- [Troubleshooting](#troubleshooting)
- [Configuration](#configuration)
- [CI/CD & Automation](#cicd--automation)
- [Advanced Usage](#advanced-usage)

---

## General

### How do I skip the interactive prompts?

Set the `AGENT_PROVIDER` environment variable:

```bash
export AGENT_PROVIDER=claude-code
gao-dev start  # No prompts, uses env var
```

This bypasses all prompts and uses your specified provider directly.

### How do I change my provider after initial setup?

Three methods:

**Method 1**: Delete preferences file:
```bash
rm .gao-dev/provider_preferences.yaml
gao-dev start  # Triggers first-time setup
```

**Method 2**: Decline saved preferences when prompted:
```
Use saved configuration? [Y/n/c]: n
```

**Method 3**: Use environment variable (temporary override):
```bash
AGENT_PROVIDER=opencode gao-dev start
```

### Where are preferences stored?

`.gao-dev/provider_preferences.yaml` in your project directory.

Each project has its own preferences file, so you can use different providers for different projects.

### Can I use the same provider across all projects?

Not yet. Currently, preferences are per-project. Global preferences are planned for a future release.

### What happens if my preferences file gets corrupted?

The system automatically:
1. Detects corruption on load
2. Attempts to load from backup file (`.gao-dev/provider_preferences.yaml.bak`)
3. If both fail, prompts for fresh setup (no data loss)

### What providers are supported?

Three providers are currently supported:

1. **claude-code**: Claude Code CLI (requires npm installation)
2. **opencode**: OpenCode CLI (supports multiple AI backends)
3. **direct-api-anthropic**: Direct Anthropic API (no CLI needed)

### Can I add custom providers?

Yes! GAO-Dev supports custom providers through the plugin system. See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for details on adding new providers.

### What models are available for each provider?

**claude-code**:
- sonnet-4.5 (default)
- opus-4
- haiku-3.5

**opencode**:
- deepseek-r1 (default, local via Ollama)
- llama2 (local via Ollama)
- codellama (local via Ollama)
- Any cloud model (Anthropic, OpenAI, Google)

**direct-api-anthropic**:
- claude-3-5-sonnet-20241022
- claude-3-opus-20240229
- claude-3-haiku-20240307

---

## Troubleshooting

### Why isn't Ollama detected?

Common causes:

**1. Ollama not installed**:
```bash
# Check if installed
which ollama

# Install if missing
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh
# Windows: Download from https://ollama.ai/download
```

**2. No models pulled**:
```bash
# Check models
ollama list

# Pull a model if empty
ollama pull deepseek-r1
```

**3. Ollama service not running**:
```bash
# Start service
ollama serve
```

**4. Slow disk** (HDD/NAS):
- Validation has 10-second timeout
- Wait for detection to complete
- Consider using SSD for better performance

### What does "CLI not found" mean?

The CLI tool for your selected provider is not in your system PATH.

**For claude-code**:
```bash
npm install -g @anthropic/claude-code
claude --version  # Verify installation
```

**For opencode**:
```bash
npm install -g opencode
opencode --version  # Verify installation
```

**Check PATH**:
```bash
echo $PATH  # Unix/macOS
echo %PATH%  # Windows CMD
$env:PATH  # Windows PowerShell
```

### How do I fix "Validation failed"?

Validation failures have specific causes:

**CLI not found**: Install the CLI tool (see above)

**API key not set**:
```bash
# Anthropic
export ANTHROPIC_API_KEY=sk-ant-api03-...

# OpenAI
export OPENAI_API_KEY=sk-...

# Google
export GOOGLE_API_KEY=...
```

**Ollama models not available**: Pull models:
```bash
ollama pull deepseek-r1
```

**Network issues**: Check internet connectivity for cloud providers

### Validation is stuck/slow

**Cause**: Ollama detection on slow disks can take up to 10 seconds.

**Solutions**:
- Wait for 10-second timeout
- Use SSD instead of HDD/NAS
- Skip Ollama: Use cloud providers instead
- Set env var to bypass validation: `AGENT_PROVIDER=claude-code`

### Preferences file is corrupted

**Symptom**: `Invalid YAML in preferences file` warning

**Solutions**:

**1. Delete corrupted file** (triggers fresh setup):
```bash
rm .gao-dev/provider_preferences.yaml
gao-dev start
```

**2. Restore from backup**:
```bash
cp .gao-dev/provider_preferences.yaml.bak .gao-dev/provider_preferences.yaml
gao-dev start
```

**3. Manually fix** (validate YAML syntax):
```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('.gao-dev/provider_preferences.yaml'))"
```

---

## Configuration

### How do I set default providers for new projects?

Edit `gao_dev/config/defaults.yaml`:

```yaml
providers:
  default: "opencode"  # Change default provider
```

This affects new projects only. Existing projects use saved preferences.

### Can I customize the models list?

Yes! Edit `gao_dev/cli/provider_selector.py`:

```python
AVAILABLE_MODELS = {
    "opencode": ["deepseek-r1", "llama2", "codellama", "my-custom-model"],
}
```

For permanent changes, consider submitting a PR to add official support.

### How do I disable the feature entirely?

Edit `gao_dev/config/defaults.yaml`:

```yaml
features:
  interactive_provider_selection: false
```

System reverts to:
1. `AGENT_PROVIDER` environment variable
2. Hardcoded defaults (claude-code + sonnet-4.5)

### Can I change validation timeout?

Yes, but requires code modification. Edit `gao_dev/cli/provider_validator.py`:

```python
# Line 282: Change Ollama timeout from 10s
stdout, stderr = await asyncio.wait_for(
    proc.communicate(), timeout=20.0  # Increase to 20 seconds
)
```

---

## CI/CD & Automation

### How do I use this in CI/CD pipelines?

Set `AGENT_PROVIDER` environment variable in your CI config:

**GitHub Actions**:
```yaml
jobs:
  test:
    env:
      AGENT_PROVIDER: claude-code
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
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

**Jenkins**:
```groovy
environment {
    AGENT_PROVIDER = 'claude-code'
    ANTHROPIC_API_KEY = credentials('anthropic-api-key')
}
```

**Docker**:
```dockerfile
ENV AGENT_PROVIDER=claude-code
ENV ANTHROPIC_API_KEY=sk-ant-...
```

### What if CI/CD fails with "No TTY available"?

The system automatically falls back to basic `input()` when TTY unavailable.

Ensure `AGENT_PROVIDER` is set to bypass prompts entirely:

```yaml
env:
  AGENT_PROVIDER: claude-code
```

### Can I use this in automated scripts?

Yes! Set environment variable before running:

```bash
#!/bin/bash
export AGENT_PROVIDER=claude-code
export ANTHROPIC_API_KEY=sk-ant-...
gao-dev start --non-interactive
```

### How do I test multiple providers in CI?

Use matrix strategy:

**GitHub Actions**:
```yaml
jobs:
  test:
    strategy:
      matrix:
        provider: [claude-code, opencode, direct-api-anthropic]
    env:
      AGENT_PROVIDER: ${{ matrix.provider }}
    steps:
      - run: gao-dev start
```

---

## Advanced Usage

### Can I customize the validation logic?

Yes! Extend `ProviderValidator`:

```python
from gao_dev.cli.provider_validator import ProviderValidator

class MyValidator(ProviderValidator):
    async def validate_configuration(self, provider_name, config):
        result = await super().validate_configuration(provider_name, config)
        # Add custom validation here
        return result
```

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for details.

### Can I add custom providers?

Yes! Implement the provider interface:

```python
from gao_dev.core.providers.base import BaseProvider

class MyCustomProvider(BaseProvider):
    def __init__(self, config):
        super().__init__(config)
        # Initialize your provider

    def execute(self, prompt):
        # Execute prompt with your provider
        pass
```

Register in `ProviderFactory`:

```python
factory.register_provider("my-provider", MyCustomProvider)
```

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for full guide.

### How do I A/B test different providers?

Use environment variable to switch:

```bash
# Test A: Claude Code
AGENT_PROVIDER=claude-code gao-dev start

# Test B: OpenCode
AGENT_PROVIDER=opencode gao-dev start

# Compare metrics, cost, performance
```

### Can I use different providers for different agents?

Not yet. Currently, all agents use the same provider. Per-agent provider selection is planned for a future release.

### How do I monitor provider performance?

GAO-Dev collects metrics automatically:

```bash
# View metrics
gao-dev metrics report run <run_id>

# Compare providers
gao-dev metrics report compare <run_id_1> <run_id_2>
```

Metrics include:
- Token usage
- Cost per operation
- Response time
- Success/failure rate

### Can I switch providers mid-session?

Not yet. Provider is selected at REPL startup and persists for the session. Mid-session switching is planned for a future release.

### How secure is the preferences file?

Very secure:

1. **YAML Safety**: Uses `yaml.safe_dump()` to prevent code execution
2. **Input Sanitization**: All user input sanitized before saving
3. **File Permissions**: Set to 0600 (user-only) on Unix
4. **No API Keys**: API keys never saved (only environment variable names)
5. **Backup Strategy**: Automatic backups before overwriting

See [ARCHITECTURE.md](ARCHITECTURE.md) Section 8 for security details.

### What data is stored in preferences?

Only configuration metadata:

```yaml
version: "1.0.0"
provider:
  name: "opencode"
  model: "deepseek-r1"
  config:
    ai_provider: "ollama"  # NOT the API key!
    use_local: true
metadata:
  last_updated: "2025-01-12T10:30:00Z"
  cli_version: "1.0.0"
```

**Never stored**:
- API keys
- Personal information
- Model outputs
- Conversation history

### How do I migrate preferences to a new machine?

Copy the preferences file:

```bash
# On old machine
cp .gao-dev/provider_preferences.yaml ~/backup.yaml

# On new machine
mkdir -p .gao-dev
cp ~/backup.yaml .gao-dev/provider_preferences.yaml
```

Ensure API keys are set on new machine:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### Can I use multiple models with the same provider?

Yes! Change model in preferences or use environment variable:

```bash
# Use different model temporarily
AGENT_PROVIDER=opencode:llama2 gao-dev start
```

For permanent change, edit `.gao-dev/provider_preferences.yaml`:

```yaml
provider:
  name: "opencode"
  model: "llama2"  # Change model
```

---

## Still Have Questions?

- **User Guide**: [USER_GUIDE.md](USER_GUIDE.md) for detailed instructions
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md) for developers
- **Integration Guide**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for custom providers
- **GitHub Issues**: [Report a bug or request a feature](https://github.com/your-org/gao-agile-dev/issues)

---

**Version**: 1.0
**Last Updated**: 2025-01-12
**Epic**: 35 - Interactive Provider Selection at Startup
