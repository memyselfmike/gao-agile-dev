# Interactive Provider Selection Feature

**Status**: Planning
**Epic**: Epic 35
**Version**: 1.0
**Owner**: Amelia (Software Developer)

---

## Overview

Interactive provider selection adds a user-friendly startup flow to the Brian REPL that allows users to choose their AI provider (Claude Code, OpenCode, local Ollama models) through clear prompts with preference persistence.

### Problem

Currently, users must manually configure providers through environment variables or config files. This creates friction when:
- Testing different providers
- Switching between local and cloud models
- Setting up GAO-Dev for the first time
- Working offline with local models

### Solution

Add interactive prompts during `gao-dev start` that guide users through provider selection with:
- Clear options table
- Provider-specific configuration (e.g., OpenCode local vs cloud)
- Model selection from available models
- Preference persistence for future sessions
- Zero configuration for subsequent startups

---

## Quick Start

### First-Time Startup

```bash
$ gao-dev start

┌─────────────────────────────────────────────────┐
│ Welcome to GAO-Dev Interactive Setup            │
└─────────────────────────────────────────────────┘

Available AI Providers
┌────────┬─────────────────────┬──────────────────────────┐
│ Option │ Provider            │ Description              │
├────────┼─────────────────────┼──────────────────────────┤
│ 1      │ claude-code         │ Claude Code CLI          │
│ 2      │ opencode            │ OpenCode CLI             │
│ 3      │ direct-api-anthropic│ Direct Anthropic API     │
└────────┴─────────────────────┴──────────────────────────┘

Select provider [1/2/3] (1): 2

Use local model via Ollama? [y/N]: y

Available Models
┌────────┬────────────────┐
│ Option │ Model          │
├────────┼────────────────┤
│ 1      │ deepseek-r1    │
│ 2      │ llama2         │
└────────┴────────────────┘

Select model [1/2] (1): 1

✓ Configuration validated
Save as default? [Y/n]: y

Starting GAO-Dev with OpenCode + deepseek-r1...
```

### Returning User

```bash
$ gao-dev start

Saved provider: opencode (local: deepseek-r1)
Use saved configuration? [Y/n]: <Enter>

Starting GAO-Dev with OpenCode + deepseek-r1...
```

### Bypass Prompts (CI/CD)

```bash
export AGENT_PROVIDER=claude-code
gao-dev start  # No prompts, uses environment variable
```

---

## Features

### ✅ Interactive Provider Selection
- Clear table of available providers
- Descriptions for each option
- Default recommendations
- Input validation

### ✅ OpenCode Configuration
- Local model (Ollama) vs cloud prompts
- Cloud provider selection (Anthropic/OpenAI/Google)
- Automatic Ollama model detection

### ✅ Model Selection
- List of available models per provider
- Model descriptions and sizes
- Recommended model highlighting

### ✅ Preference Persistence
- Save configuration to `.gao-dev/provider_preferences.yaml`
- Reuse saved config on subsequent startups
- Option to change or reconfigure

### ✅ Validation
- Check CLI availability before starting
- Validate API keys (for direct API providers)
- Clear error messages with fix suggestions
- Retry on validation failure

### ✅ Zero Regressions
- All existing functionality works unchanged
- Environment variables still override
- Backward compatible with all configs

---

## Architecture

### Components

```
ChatREPL
  │
  ├─ ProviderSelector (orchestrator)
  │   ├─ InteractivePrompter (UI)
  │   ├─ PreferenceManager (persistence)
  │   └─ ProviderValidator (validation)
  │
  └─ ProcessExecutor (uses selected config)
```

### Data Flow

```
1. User runs `gao-dev start`
2. ProviderSelector checks:
   - Environment variable (AGENT_PROVIDER)
   - Saved preferences (.gao-dev/provider_preferences.yaml)
   - If neither: interactive prompts
3. ProviderValidator validates configuration
4. ProcessExecutor created with selected config
5. ChatREPL starts with validated provider
```

---

## Documentation

### For Users
- **[User Guide](USER_GUIDE.md)** - Complete walkthrough with examples
- **[FAQ](FAQ.md)** - Common questions and answers
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

### For Developers
- **[PRD](PRD.md)** - Product requirements document
- **[Architecture](ARCHITECTURE.md)** - Technical architecture
- **[API Reference](API_REFERENCE.md)** - Class and method documentation
- **[Testing Guide](TESTING.md)** - How to run and write tests
- **[Integration Guide](INTEGRATION_GUIDE.md)** - Adding new provider types

### Epic Planning
- **[Epic 35 Breakdown](EPIC-35.md)** - Stories, tasks, and timeline

---

## Implementation Status

| Story | Title | Status | Points |
|-------|-------|--------|--------|
| 35.1 | Project Setup & Architecture | 📋 Ready | 2 |
| 35.2 | PreferenceManager Implementation | 📋 Ready | 5 |
| 35.3 | ProviderValidator Implementation | 📋 Ready | 5 |
| 35.4 | InteractivePrompter Implementation | 📋 Ready | 8 |
| 35.5 | ProviderSelector Implementation | 📋 Ready | 5 |
| 35.6 | ChatREPL Integration | 📋 Ready | 3 |
| 35.7 | Testing & Regression Validation | 📋 Ready | 8 |
| 35.8 | Documentation & Examples | 📋 Ready | 3 |

**Total**: 39 story points (~40-50 hours)

---

## Usage Examples

### Example 1: First-Time Setup with Claude Code

```bash
$ gao-dev start
Select provider [1/2/3] (1): 1
Select model [1/2/3] (1): 1  # sonnet-4.5
Save as default? [Y/n]: y

✓ Starting with claude-code + sonnet-4.5
```

### Example 2: Switch to Local Ollama Model

```bash
$ gao-dev start
Use saved configuration? [Y/n/c]: c  # Change

Select provider [1/2/3] (1): 2  # opencode
Use local model via Ollama? [y/N]: y
Select model [1/2/3] (1): 1  # deepseek-r1
Save as default? [Y/n]: y

✓ Starting with opencode + deepseek-r1
```

### Example 3: CI/CD (No Prompts)

```bash
# In CI/CD pipeline
export AGENT_PROVIDER=claude-code
export ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY_SECRET

gao-dev start  # No prompts, uses env vars
```

---

## Benefits

### For Users
- ✅ **No manual configuration** - Just answer prompts
- ✅ **Clear options** - See all available providers
- ✅ **Cost savings** - Easy to use free local models
- ✅ **Offline support** - Work with Ollama without internet
- ✅ **Fast setup** - <30 seconds to configure

### For Developers
- ✅ **Zero regressions** - All existing code unchanged
- ✅ **Clean architecture** - Modular, testable components
- ✅ **Extensible** - Easy to add new provider types
- ✅ **Well-tested** - >90% coverage, comprehensive regression suite
- ✅ **Documented** - Complete API and user documentation

---

## Configuration File

**`.gao-dev/provider_preferences.yaml`**:
```yaml
version: "1.0"
last_updated: "2025-01-12T10:30:00Z"

provider:
  name: "opencode"
  model: "deepseek-r1"

  config:
    ai_provider: "ollama"
    use_local: true
    timeout: 3600

metadata:
  cli_version: "1.2.3"
  last_validated: "2025-01-12T10:30:00Z"
  validation_status: "healthy"
```

---

## Error Handling

### Clear Error Messages

```
✗ Error: OpenCode CLI not found

OpenCode is not installed or not in PATH.

Installation Options:
  1. npm install -g opencode
  2. Download from: https://github.com/opencode/cli

Would you like to:
  [1] Try different provider
  [2] Exit and install OpenCode
  [3] Continue anyway (may fail)
```

### Validation Failures

```
✗ Validation Failed: ANTHROPIC_API_KEY not set

To use Claude Code, you need an Anthropic API key.

Fix:
  export ANTHROPIC_API_KEY=sk-ant-api03-...

Get API key: https://console.anthropic.com/

Try different provider? [Y/n]:
```

---

## Performance

| Operation | Target | Actual |
|-----------|--------|--------|
| Load preferences | <100ms | TBD |
| Provider validation | <2s | TBD |
| Ollama model detection | <3s | TBD |
| Interactive flow (total) | <30s | TBD |
| ChatREPL startup | <5s | TBD |

---

## Testing

### Coverage Targets
- **Overall project**: No decrease from current
- **New code**: >90%
- **PreferenceManager**: >95%
- **ProviderValidator**: >90%
- **InteractivePrompter**: >85%
- **ProviderSelector**: >90%

### Test Suites
- **Unit tests**: 60+ tests
- **Integration tests**: 30+ tests
- **End-to-end tests**: 10+ tests
- **Regression tests**: 20+ tests
- **Total**: 120+ tests

---

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `AGENT_PROVIDER` | Override provider selection | `export AGENT_PROVIDER=opencode` |
| `SKIP_PROVIDER_SELECTION` | Skip prompts, use defaults | `export SKIP_PROVIDER_SELECTION=1` |
| `ANTHROPIC_API_KEY` | API key for Anthropic | `export ANTHROPIC_API_KEY=sk-ant-...` |

---

## Troubleshooting

### Common Issues

**Problem**: Prompts don't appear
- **Solution**: Check if `AGENT_PROVIDER` env var is set

**Problem**: Preferences not saved
- **Solution**: Check `.gao-dev/` directory permissions

**Problem**: Ollama models not detected
- **Solution**: Ensure `ollama` command is in PATH

**Problem**: Validation fails
- **Solution**: Check error message for specific fix suggestions

See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for more.

---

## Future Enhancements

After Epic 35:
- Global preferences in `~/.gao-dev/global_preferences.yaml`
- Provider performance benchmarking
- Automatic provider recommendation based on task
- Cloud cost estimation
- Provider A/B testing mode
- `gao-dev configure` standalone command

---

## Contributing

To add a new provider type:
1. Read **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)**
2. Implement provider class
3. Add to ProviderFactory registry
4. Add validation logic
5. Update prompts and documentation
6. Add tests

---

## Related Epics

- **Epic 30**: Interactive Brian Chat Interface - Complete ✅
- **Epic 21**: AI Analysis Service & Provider Abstraction - Complete ✅
- **Epic 11**: Agent Provider Abstraction System - Complete ✅

---

## Questions?

- See **[FAQ.md](FAQ.md)** for common questions
- Check **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for issues
- Read **[USER_GUIDE.md](USER_GUIDE.md)** for detailed walkthrough

---

## License

Part of GAO-Dev project. See main LICENSE file.

---

**Last Updated**: 2025-01-12
**Status**: Planning - Ready to implement
**Next Action**: Begin Story 35.1 (Project Setup & Architecture)
