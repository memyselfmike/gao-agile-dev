# Example: First-Time Setup

This example shows the complete first-time setup flow for Interactive Provider Selection.

## Scenario

You're setting up GAO-Dev for the first time and want to use OpenCode with a local Ollama model to save costs.

## Prerequisites

- GAO-Dev installed
- Ollama installed: `brew install ollama` (macOS) or [https://ollama.ai/download](https://ollama.ai/download)
- Model pulled: `ollama pull deepseek-r1`

## Steps

### 1. Start GAO-Dev

```bash
cd your-project
gao-dev start
```

### 2. See Provider Selection Table

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

**Action**: Type `2` and press Enter.

### 3. OpenCode Configuration

```
OpenCode Configuration

Use local model via Ollama? [y/N]:
```

**Action**: Type `y` and press Enter.

### 4. Model Selection

```
Detecting Ollama models (may take a moment)...

Available Models
┌────────┬────────────────┬──────┐
│ Option │ Model          │ Size │
├────────┼────────────────┼──────┤
│ 1      │ deepseek-r1    │ 7B   │
│ 2      │ llama2         │ 7B   │
│ 3      │ codellama      │ 13B  │
└────────┴────────────────┴──────┘

Select model [1-3] (default: 1):
```

**Action**: Press Enter (use default: deepseek-r1).

### 5. Validation

```
Validating opencode...
Checking opencode CLI availability...
opencode CLI available
Checking Ollama models...
Found 3 Ollama model(s)

✓ Configuration validated successfully
```

### 6. Save Preferences

```
Save as default for future sessions? [Y/n]:
```

**Action**: Press Enter (save preferences).

### 7. REPL Starts

```
✓ Preferences saved to .gao-dev/provider_preferences.yaml

Starting GAO-Dev with OpenCode + deepseek-r1...

Welcome to GAO-Dev Interactive Development!

Type 'help' for available commands, or describe what you want to build.

gao-dev>
```

## Result

- **Provider**: OpenCode with local Ollama (deepseek-r1)
- **Preferences saved**: `.gao-dev/provider_preferences.yaml`
- **REPL ready**: Start building your application!
- **Cost**: $0.00 (free local model)

## Next Startup

```bash
gao-dev start

Saved Configuration Found:
  provider: opencode
  model: deepseek-r1

Use saved configuration? [Y/n/c (change)] (default: Y): <Enter>

✓ Using saved configuration
Starting GAO-Dev with OpenCode + deepseek-r1...
```

**Result**: Instant startup with saved configuration!

## Tips

- **Change provider**: When prompted "Use saved configuration?", type `n`
- **Bypass prompts**: Set `export AGENT_PROVIDER=opencode:deepseek-r1`
- **Reset**: Delete `.gao-dev/provider_preferences.yaml` to trigger first-time setup

---

**See Also**:
- [USER_GUIDE.md](../USER_GUIDE.md) - Complete user guide
- [change-provider.md](change-provider.md) - How to change providers
- [local-models.md](local-models.md) - Local model setup guide
