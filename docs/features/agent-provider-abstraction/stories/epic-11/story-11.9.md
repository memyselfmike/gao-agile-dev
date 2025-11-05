# Story 11.9: Multi-Provider Documentation

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P1 (High)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer) + Bob (Scrum Master)
**Created**: 2025-11-04
**Dependencies**: Story 11.7 (OpenCodeProvider)

---

## User Story

**As a** GAO-Dev user
**I want** comprehensive documentation on using multiple providers
**So that** I can easily configure and switch between providers

---

## Acceptance Criteria

### AC1: CLAUDE.md Updated
- ✅ Provider section added to CLAUDE.md
- ✅ Overview of provider abstraction
- ✅ Quick start for each provider
- ✅ Provider comparison table
- ✅ Links to detailed guides

### AC2: Provider Selection Guide Created
- ✅ Document created: `docs/provider-selection-guide.md`
- ✅ Decision tree for choosing provider
- ✅ Use case recommendations
- ✅ Cost comparison
- ✅ Performance comparison
- ✅ Feature comparison

### AC3: Setup Guides Complete
- ✅ Claude Code setup guide exists/updated
- ✅ OpenCode setup guide created (Story 11.6 deliverable)
- ✅ Direct API setup guide (forward-looking)
- ✅ Step-by-step instructions with commands
- ✅ Troubleshooting sections

### AC4: Configuration Reference
- ✅ Document created: `docs/provider-configuration-reference.md`
- ✅ Configuration options for each provider
- ✅ Environment variables documented
- ✅ YAML configuration examples
- ✅ Default values documented

### AC5: Troubleshooting Guide
- ✅ Document created: `docs/provider-troubleshooting.md`
- ✅ Common issues and solutions
- ✅ Provider-specific issues
- ✅ Diagnostic commands
- ✅ Error message explanations

### AC6: FAQ Section
- ✅ Document created: `docs/provider-faq.md`
- ✅ 20+ common questions answered
- ✅ Provider comparison questions
- ✅ Migration questions
- ✅ Performance questions
- ✅ Cost questions

### AC7: CLI Command Reference
- ✅ `gao-dev providers` commands documented
- ✅ `list`, `validate`, `migrate` commands
- ✅ Examples for each command
- ✅ Help text comprehensive

### AC8: External Review
- ✅ Documentation reviewed by external user
- ✅ Feedback incorporated
- ✅ Clarity validated
- ✅ Examples tested

---

## Technical Details

### Deliverable Files
```
docs/
├── provider-selection-guide.md           # NEW: How to choose
├── provider-configuration-reference.md   # NEW: Config reference
├── provider-troubleshooting.md           # NEW: Common issues
├── provider-faq.md                       # NEW: FAQ
├── opencode-setup-guide.md               # EXISTS: From Story 11.6
├── MIGRATION_PROVIDER.md                 # EXISTS: From Story 11.5
└── CLAUDE.md                             # MODIFIED: Add provider section

CLAUDE.md: Add new provider section
README.md: Update with provider information
```

### Implementation Approach

#### Step 1: Update CLAUDE.md

**File**: `CLAUDE.md` (add new section)

```markdown
## Multi-Provider Support (Epic 11)

### Overview

GAO-Dev supports multiple AI agent execution providers, giving you flexibility in choosing your AI backend without vendor lock-in.

**Supported Providers**:
- **Claude Code** (default) - Anthropic's official CLI
- **OpenCode** - Open-source multi-provider agent (Anthropic, OpenAI, Google)
- **Direct API** - Direct API calls without CLI overhead (coming soon)
- **Custom** - Plugin system for custom providers

### Quick Start

#### Using Default Provider (Claude Code)

```bash
# No changes needed - just works
gao-dev create-prd --name "My Project"
```

#### Switching to OpenCode

```bash
# 1. Install OpenCode
npm install -g @sst/opencode

# 2. Update agent config
# Edit gao_dev/config/agents/amelia.yaml:
agent:
  configuration:
    provider: "opencode"
    provider_config:
      ai_provider: "anthropic"  # or "openai", "google"

# 3. Verify
gao-dev providers validate
```

### Provider Comparison

| Feature | Claude Code | OpenCode | Direct API |
|---------|-------------|----------|------------|
| **AI Providers** | Anthropic only | Multi (Anthropic, OpenAI, Google) | Multi |
| **Installation** | Binary | npm/Bun | Python package |
| **Performance** | Baseline | ~15% slower | ~25% faster |
| **Cost** | Anthropic API | Varies by provider | Varies by provider |
| **Maturity** | High | Medium | High |
| **License** | Proprietary | MIT (Open Source) | Varies |

### Choosing a Provider

- **Default/Recommended**: Claude Code - Most stable, best tested
- **Multi-Provider Needs**: OpenCode - Use OpenAI or Google models
- **Best Performance**: Direct API - Fastest execution (when available)
- **Custom Requirements**: Write a custom provider plugin

### See Also

- [Provider Selection Guide](docs/provider-selection-guide.md)
- [Provider Configuration Reference](docs/provider-configuration-reference.md)
- [Provider Troubleshooting](docs/provider-troubleshooting.md)
- [Provider FAQ](docs/provider-faq.md)
- [OpenCode Setup Guide](docs/opencode-setup-guide.md)
- [Migration Guide](docs/MIGRATION_PROVIDER.md)
```

#### Step 2: Create Provider Selection Guide

**File**: `docs/provider-selection-guide.md`

```markdown
# Provider Selection Guide

This guide helps you choose the right AI agent provider for your GAO-Dev setup.

---

## Decision Tree

```
START: Do you need GAO-Dev now?
│
├─ YES → Do you have ANTHROPIC_API_KEY?
│  │
│  ├─ YES → Do you need OpenAI or Google models?
│  │  │
│  │  ├─ NO → ✅ Use Claude Code (default)
│  │  │       Fast, stable, no setup needed
│  │  │
│  │  └─ YES → ✅ Use OpenCode with your preferred provider
│  │            Supports Anthropic, OpenAI, Google
│  │
│  └─ NO → Do you have OPENAI_API_KEY or GOOGLE_API_KEY?
│     │
│     ├─ YES → ✅ Use OpenCode with OpenAI/Google
│     │
│     └─ NO → ❌ Get an API key first
│               https://console.anthropic.com
│
└─ NO (planning) → Continue reading this guide
```

---

## Provider Comparison

### Claude Code

**Best For**:
- First-time users
- Stable, production use
- Anthropic-only workloads
- Windows users (best Windows support)

**Pros**:
- ✅ Default - zero configuration
- ✅ Most stable and tested
- ✅ Best Windows compatibility
- ✅ Official Anthropic support

**Cons**:
- ❌ Anthropic models only
- ❌ Proprietary (no source code)
- ❌ CLI subprocess overhead

**Setup Time**: 0 minutes (already configured)

**When to Use**:
- You're new to GAO-Dev
- You want the most stable experience
- You're happy with Claude models
- You're on Windows

---

### OpenCode

**Best For**:
- Multi-provider needs
- Cost optimization
- Open-source preference
- Experimentation

**Pros**:
- ✅ Multiple AI providers (Anthropic, OpenAI, Google, local)
- ✅ Open source (MIT license)
- ✅ Active community
- ✅ Cost optimization via provider switching
- ✅ Built-in LSP support

**Cons**:
- ❌ Requires Bun runtime
- ❌ Less mature than Claude Code
- ❌ ~15% slower than Claude Code
- ❌ Potential breaking changes

**Setup Time**: 5-10 minutes

**When to Use**:
- You want to use OpenAI or Google models
- You want to optimize costs
- You value open source
- You're comfortable with newer tools

---

### Direct API (Coming Soon)

**Best For**:
- Performance-critical paths
- High-volume usage
- Advanced users

**Pros**:
- ✅ Best performance (~25% faster)
- ✅ No CLI subprocess overhead
- ✅ Fine-grained control
- ✅ Better error handling

**Cons**:
- ❌ More complex setup
- ❌ Requires Python API client
- ❌ Less tool support initially

**Setup Time**: 10-15 minutes

**When to Use**:
- Performance is critical
- You need advanced features
- You have high API volume

---

## Use Case Recommendations

### Personal Project
→ **Claude Code** (default)
- Zero setup, just works
- Stable and reliable

### Startup/Small Team
→ **OpenCode** with cost optimization
- Use cheap models for simple tasks
- Use powerful models for critical tasks
- Optimize costs as you scale

### Enterprise
→ **Claude Code** or **Direct API**
- Claude Code: Stability priority
- Direct API: Performance priority
- Custom provider: Special requirements

### Open Source Project
→ **OpenCode**
- Open source matches project values
- Contributors can use any AI provider
- Lower barrier to entry

### Research/Experimentation
→ **OpenCode**
- Try different models easily
- Compare AI provider outputs
- Flexibility for research needs

---

## Cost Comparison

### Token Costs (Approximate)

| Provider | Model | Input (per 1M tokens) | Output (per 1M tokens) |
|----------|-------|----------------------|------------------------|
| **Anthropic** | Sonnet 4.5 | $3.00 | $15.00 |
| **Anthropic** | Opus 3 | $15.00 | $75.00 |
| **OpenAI** | GPT-4 | $30.00 | $60.00 |
| **OpenAI** | GPT-4 Turbo | $10.00 | $30.00 |
| **Google** | Gemini Pro | $0.50 | $1.50 |

**Cost Optimization Strategy**:
- Simple tasks (docs, tests): Use Gemini Pro (cheapest)
- Standard tasks: Use Sonnet 4.5 (balanced)
- Complex tasks: Use Opus 3 or GPT-4 (most capable)

**Estimated Monthly Costs** (100 tasks/day):
- Claude Code only: $100-300/month
- OpenCode optimized: $50-150/month (40-50% savings)
- Mix of providers: $70-200/month

---

## Performance Comparison

### Benchmark Results

Based on provider comparison tests (Story 11.8):

| Task Type | Claude Code | OpenCode (Anthropic) | OpenCode (OpenAI) |
|-----------|-------------|---------------------|------------------|
| Simple file | 5.2s | 6.0s (+15%) | 5.8s (+12%) |
| Code gen | 12.3s | 14.1s (+15%) | 13.5s (+10%) |
| Complex | 45.2s | 52.3s (+16%) | 48.7s (+8%) |

**Performance Tips**:
- Direct API will be fastest when available
- OpenAI slightly faster than Anthropic via OpenCode
- Subprocess overhead affects all CLI providers

---

## Migration Path

### From Claude Code → OpenCode

**Difficulty**: Easy (15 minutes)

```bash
# 1. Install OpenCode
npm install -g @sst/opencode

# 2. Set API key (if using different provider)
export OPENAI_API_KEY=sk-...

# 3. Update agent config (optional)
# Edit gao_dev/config/agents/amelia.yaml

# 4. Test
gao-dev providers validate
```

**Rollback**: Remove provider field from agent configs

### From OpenCode → Claude Code

**Difficulty**: Trivial (1 minute)

```bash
# Remove provider fields from agent configs
# System will default to Claude Code
```

---

## Decision Matrix

| Your Situation | Recommended Provider |
|----------------|---------------------|
| "I just want it to work" | Claude Code |
| "I want to save money" | OpenCode (cost-optimized) |
| "I need OpenAI models" | OpenCode with OpenAI |
| "I want the fastest execution" | Direct API (when available) |
| "I'm on Windows" | Claude Code (best support) |
| "I value open source" | OpenCode |
| "I have high volume" | Direct API (when available) |
| "I want to experiment" | OpenCode |
| "Enterprise requirements" | Claude Code or custom |

---

## Still Unsure?

**Start with Claude Code** (default). You can always switch later with minimal effort.

**Questions?** See [Provider FAQ](provider-faq.md)

**Need Help?** Join our community or open an issue.
```

#### Step 3: Create Configuration Reference

**File**: `docs/provider-configuration-reference.md`

```markdown
# Provider Configuration Reference

Complete reference for configuring GAO-Dev providers.

---

## Configuration Hierarchy

GAO-Dev loads provider configuration from multiple sources:

1. **System Defaults**: `gao_dev/config/defaults.yaml`
2. **Agent Config**: `gao_dev/config/agents/<agent>.yaml`
3. **Runtime Override**: Command-line flags or API parameters

**Precedence**: Runtime > Agent Config > System Defaults

---

## System Configuration

**File**: `gao_dev/config/defaults.yaml`

```yaml
providers:
  # Default provider for all agents
  default: "claude-code"

  # Auto-detection and fallback
  auto_detect: true
  auto_fallback: true
  fallback_chain:
    - "claude-code"
    - "opencode"
    - "direct-api"

  # Provider-specific defaults
  claude-code:
    cli_path: null  # Auto-detect
    api_key_env: "ANTHROPIC_API_KEY"
    default_model: "sonnet-4.5"
    timeout: 3600

  opencode:
    cli_path: null
    ai_provider: "anthropic"
    api_key_env: "ANTHROPIC_API_KEY"
    default_model: "sonnet-4.5"
    timeout: 3600

  direct-api:
    provider: "anthropic"
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: null
    default_model: "sonnet-4.5"
    timeout: 3600
    max_retries: 3

models:
  registry:
    - canonical: "sonnet-4.5"
      providers:
        claude-code: "claude-sonnet-4-5-20250929"
        opencode: "anthropic/claude-sonnet-4.5"
        direct-api: "claude-sonnet-4-5-20250929"
```

---

## Agent Configuration

**File**: `gao_dev/config/agents/<agent>.yaml`

### Claude Code Example

```yaml
agent:
  configuration:
    provider: "claude-code"  # Optional (defaults to system default)
    provider_config:
      cli_path: "/usr/local/bin/claude"  # Optional
      api_key: null  # Use ANTHROPIC_API_KEY env
    model: "sonnet-4.5"
```

### OpenCode with Anthropic Example

```yaml
agent:
  configuration:
    provider: "opencode"
    provider_config:
      ai_provider: "anthropic"
      cli_path: null  # Auto-detect
    model: "sonnet-4.5"
```

### OpenCode with OpenAI Example

```yaml
agent:
  configuration:
    provider: "opencode"
    provider_config:
      ai_provider: "openai"
      cli_path: null
    model: "gpt-4"
```

---

## Environment Variables

### Claude Code

```bash
# Required
export ANTHROPIC_API_KEY=sk-ant-...

# Optional
export CLAUDE_CLI_PATH=/usr/local/bin/claude
```

### OpenCode

```bash
# For Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# For OpenAI
export OPENAI_API_KEY=sk-...

# For Google
export GOOGLE_API_KEY=...

# Optional
export OPENCODE_CLI_PATH=/usr/local/bin/opencode
```

### Direct API

```bash
# Provider-specific
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export GOOGLE_API_KEY=...

# Optional overrides
export ANTHROPIC_BASE_URL=https://custom-api.example.com
```

---

## Model Names

### Canonical Names (Provider-Agnostic)

Use these in your configurations:
- `sonnet-4.5` - Claude Sonnet 4.5 (recommended)
- `sonnet-3.5` - Claude Sonnet 3.5
- `opus-3` - Claude Opus 3 (most capable)
- `haiku-3` - Claude Haiku 3 (fast/cheap)
- `gpt-4` - OpenAI GPT-4
- `gpt-4-turbo` - OpenAI GPT-4 Turbo
- `gemini-pro` - Google Gemini Pro

### Provider-Specific Translations

GAO-Dev automatically translates canonical names:

| Canonical | Claude Code | OpenCode | Direct API |
|-----------|-------------|----------|------------|
| `sonnet-4.5` | `claude-sonnet-4-5-20250929` | `anthropic/claude-sonnet-4.5` | `claude-sonnet-4-5-20250929` |
| `gpt-4` | ❌ Not supported | `openai/gpt-4` | `gpt-4-0125-preview` |

---

## CLI Commands

### List Providers

```bash
gao-dev providers list

# Output:
# Available providers:
#   ✓ claude-code (default) - Claude Code CLI
#       Status: Configured
#       CLI: /usr/local/bin/claude
#       API Key: Set (ANTHROPIC_API_KEY)
#   ✓ opencode - OpenCode multi-provider agent
#       Status: Configured
#       CLI: /usr/local/bin/opencode
#       API Key: Set (ANTHROPIC_API_KEY)
```

### Validate Configuration

```bash
gao-dev providers validate

# Output:
# Validating providers...
#   ✓ claude-code: Configured correctly
#   ✓ opencode: Configured correctly
#   ⚠ direct-api: Not configured (API key not set)
```

### Provider-Specific Validation

```bash
gao-dev providers validate claude-code
gao-dev providers validate opencode
```

---

## Configuration Examples

See [Provider Selection Guide](provider-selection-guide.md) for use-case-specific examples.
```

#### Step 4: Create Troubleshooting Guide

Create comprehensive troubleshooting documentation in `docs/provider-troubleshooting.md`

#### Step 5: Create FAQ

Create FAQ document in `docs/provider-faq.md` with 20+ questions covering:
- Provider selection
- Setup and configuration
- Troubleshooting
- Performance
- Costs
- Migration

#### Step 6: Update README.md

Add provider section to main README with links to detailed guides.

---

## Testing Strategy

### Documentation Testing
- All commands tested and working
- All examples validated
- External review completed
- Links verified

### User Testing
- New user follows setup guide
- Existing user follows migration guide
- Troubleshooting guide resolves issues

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] CLAUDE.md updated
- [ ] Provider selection guide created
- [ ] Configuration reference complete
- [ ] Troubleshooting guide complete
- [ ] FAQ complete
- [ ] All examples tested
- [ ] External review completed
- [ ] Feedback incorporated
- [ ] Links verified
- [ ] Changes committed

---

## Dependencies

**Upstream**:
- Story 11.7 (OpenCodeProvider) - MUST be complete
- Story 11.6 (OpenCode Research) - provides setup guide

**Downstream**:
- Essential for user adoption
- Reduces support burden

---

## Notes

- Documentation is as important as code
- Examples must be tested and working
- External review critical for clarity
- Keep documentation up to date as providers evolve
- Clear, concise language essential

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
- Story 11.5: `story-11.5.md` (MIGRATION_PROVIDER.md)
- Story 11.6: `story-11.6.md` (OpenCode setup guide)
