# Example: Changing Providers

This example shows how to change your provider after initial setup.

## Scenario

You've been using local Ollama models (deepseek-r1) but now want to switch to Claude Code for higher quality outputs on an important project.

## Method 1: Decline Saved Preferences

### Steps

**1. Start GAO-Dev**:
```bash
gao-dev start
```

**2. Decline saved config**:
```
Saved Configuration Found:
  provider: opencode
  model: deepseek-r1

Use saved configuration? [Y/n/c (change)]: n
```

**3. Complete new setup**:
Follow the interactive prompts to select claude-code.

## Method 2: Delete Preferences File

### Steps

```bash
# Delete preferences
rm .gao-dev/provider_preferences.yaml

# Start GAO-Dev (triggers first-time setup)
gao-dev start
```

## Method 3: Environment Variable Override

### Temporary Override

```bash
# Override for this session only
AGENT_PROVIDER=claude-code gao-dev start
```

Your saved preferences remain unchanged for future sessions.

### Permanent Override

```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export AGENT_PROVIDER=claude-code' >> ~/.bashrc
source ~/.bashrc

# All future sessions use claude-code
gao-dev start
```

## Method 4: Edit Preferences File

### Steps

**1. Open preferences file**:
```bash
nano .gao-dev/provider_preferences.yaml
```

**2. Edit provider and model**:
```yaml
version: "1.0.0"
provider:
  name: "claude-code"  # Changed from "opencode"
  model: "sonnet-4.5"  # Changed from "deepseek-r1"
  config:
    api_key_env: "ANTHROPIC_API_KEY"
metadata:
  last_updated: "2025-01-12T10:30:00Z"
```

**3. Save and start**:
```bash
gao-dev start  # Uses edited preferences
```

---

**See Also**:
- [USER_GUIDE.md](../USER_GUIDE.md) - Complete user guide
- [FAQ.md](../FAQ.md) - Frequently asked questions
