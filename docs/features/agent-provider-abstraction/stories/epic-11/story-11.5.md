# Story 11.5: Update Configuration Schema for Providers

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P1 (High)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-04
**Dependencies**: Story 11.3 (ProviderFactory)

---

## User Story

**As a** GAO-Dev user
**I want** to specify provider settings in agent YAML configurations
**So that** I can choose which provider each agent uses without code changes

---

## Acceptance Criteria

### AC1: Agent YAML Schema Extended
- ✅ Optional `provider` field added to agent configuration
- ✅ Optional `provider_config` field for provider-specific settings
- ✅ Fields added under `agent.configuration` section
- ✅ Defaults to system default if not specified
- ✅ JSON Schema updated (`gao_dev/config/schemas/agent_schema.json`)
- ✅ Schema validation passes for new fields

### AC2: System Defaults Configuration
- ✅ `gao_dev/config/defaults.yaml` updated with:
  - Provider registry
  - Default provider setting
  - Provider-specific defaults
  - Fallback chain configuration
- ✅ Model name mappings defined (canonical → provider-specific)
- ✅ Well-documented with comments

### AC3: Backward Compatibility
- ✅ Old agent YAML configs work without modification
- ✅ Missing `provider` field defaults to "claude-code"
- ✅ Missing `provider_config` uses provider defaults
- ✅ All existing configs validated successfully
- ✅ No breaking changes

### AC4: Configuration Loading
- ✅ `AgentConfigLoader` reads provider fields
- ✅ `AgentConfig` model includes provider fields
- ✅ Validation enforces schema
- ✅ Logs provider configuration

### AC5: Migration Guide Created
- ✅ Document created: `docs/MIGRATION_PROVIDER.md`
- ✅ Migration steps documented
- ✅ Before/after examples
- ✅ Rollback instructions
- ✅ Tested by external reviewer

### AC6: Configuration Examples
- ✅ Example for each provider type
- ✅ Example with provider-specific config
- ✅ Example using defaults
- ✅ Example for OpenCode (forward-looking)

### AC7: Schema Validation Tests
- ✅ Tests for valid configurations
- ✅ Tests for invalid configurations
- ✅ Tests for backward compatibility
- ✅ Tests for provider-specific validation

---

## Technical Details

### File Structure
```
gao_dev/config/
├── defaults.yaml                           # MODIFIED: Add provider registry
├── schemas/
│   └── agent_schema.json                   # MODIFIED: Add provider fields
└── agents/
    └── *.yaml                              # OPTIONAL: Can add provider fields

docs/
└── MIGRATION_PROVIDER.md                   # NEW: Migration guide

tests/core/
└── test_config_schema_validation.py        # MODIFIED: Add provider tests
```

### Implementation Approach

#### Step 1: Update defaults.yaml

**File**: `gao_dev/config/defaults.yaml`

```yaml
# GAO-Dev System Defaults Configuration

# Provider Configuration
providers:
  # Default provider for all agents (can be overridden per-agent)
  default: "claude-code"

  # Auto-detection settings
  auto_detect: true
  auto_fallback: true

  # Fallback chain if primary provider fails
  fallback_chain:
    - "claude-code"
    - "opencode"
    - "direct-api"

  # Provider-specific configuration
  claude-code:
    cli_path: null  # Auto-detect if null
    api_key_env: "ANTHROPIC_API_KEY"
    default_model: "sonnet-4.5"
    timeout: 3600

  opencode:
    cli_path: null  # Auto-detect if null
    ai_provider: "anthropic"  # anthropic, openai, google
    api_key_env: "ANTHROPIC_API_KEY"
    default_model: "sonnet-4.5"
    timeout: 3600

  direct-api:
    provider: "anthropic"  # anthropic, openai, google
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: null  # Optional override
    default_model: "sonnet-4.5"
    timeout: 3600
    max_retries: 3
    retry_delay: 1.0

# Model Name Registry
# Defines canonical model names and their provider-specific translations
models:
  registry:
    # Claude models
    - canonical: "sonnet-4.5"
      description: "Claude Sonnet 4.5 (Latest, most capable)"
      providers:
        claude-code: "claude-sonnet-4-5-20250929"
        opencode: "anthropic/claude-sonnet-4.5"
        direct-api: "claude-sonnet-4-5-20250929"

    - canonical: "sonnet-3.5"
      description: "Claude Sonnet 3.5"
      providers:
        claude-code: "claude-sonnet-3-5-20241022"
        opencode: "anthropic/claude-sonnet-3.5"
        direct-api: "claude-sonnet-3-5-20241022"

    - canonical: "opus-3"
      description: "Claude Opus 3 (Most capable, expensive)"
      providers:
        claude-code: "claude-opus-3-20250219"
        opencode: "anthropic/claude-opus-3"
        direct-api: "claude-opus-3-20250219"

    - canonical: "haiku-3"
      description: "Claude Haiku 3 (Fast, cost-effective)"
      providers:
        claude-code: "claude-haiku-3-20250219"
        opencode: "anthropic/claude-haiku-3"
        direct-api: "claude-haiku-3-20250219"

    # OpenAI models (OpenCode and Direct API only)
    - canonical: "gpt-4"
      description: "OpenAI GPT-4"
      providers:
        opencode: "openai/gpt-4"
        direct-api: "gpt-4-0125-preview"

    - canonical: "gpt-4-turbo"
      description: "OpenAI GPT-4 Turbo"
      providers:
        opencode: "openai/gpt-4-turbo-preview"
        direct-api: "gpt-4-turbo-preview"

    # Google models (OpenCode and Direct API only)
    - canonical: "gemini-pro"
      description: "Google Gemini Pro"
      providers:
        opencode: "google/gemini-pro"
        direct-api: "models/gemini-pro"

# Existing defaults below...
# (keep all existing configuration)
```

#### Step 2: Update Agent YAML Schema

**File**: `gao_dev/config/schemas/agent_schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["agent"],
  "properties": {
    "agent": {
      "type": "object",
      "required": ["metadata", "persona", "tools", "configuration"],
      "properties": {
        "metadata": {
          "type": "object",
          "required": ["name", "role", "version"],
          "properties": {
            "name": {"type": "string"},
            "role": {"type": "string"},
            "version": {"type": "string"}
          }
        },
        "persona": {
          "type": "object",
          "required": ["background"],
          "properties": {
            "background": {"type": "string"},
            "responsibilities": {
              "type": "array",
              "items": {"type": "string"}
            }
          }
        },
        "tools": {
          "type": "array",
          "items": {"type": "string"}
        },
        "configuration": {
          "type": "object",
          "required": ["model", "max_tokens", "temperature"],
          "properties": {
            "provider": {
              "type": "string",
              "description": "Provider to use for this agent (optional, defaults to system default)"
            },
            "provider_config": {
              "type": "object",
              "description": "Provider-specific configuration (optional)",
              "additionalProperties": true
            },
            "model": {
              "type": "string",
              "description": "Canonical model name (provider translates to specific ID)"
            },
            "max_tokens": {"type": "integer"},
            "temperature": {"type": "number"}
          }
        }
      }
    }
  }
}
```

#### Step 3: Example Agent Configuration

**File**: `gao_dev/config/agents/amelia.yaml` (example with provider)

```yaml
agent:
  metadata:
    name: Amelia
    role: Software Developer
    version: 1.0.0

  persona:
    background: |
      You are Amelia, a skilled software developer specializing in
      implementing features, writing clean code, and ensuring quality.

    responsibilities:
      - Implement user stories following acceptance criteria
      - Write clean, maintainable, well-tested code
      - Perform code reviews and provide constructive feedback

  tools:
    - Read
    - Write
    - Edit
    - MultiEdit
    - Bash
    - Grep
    - Glob

  configuration:
    # NEW: Provider selection (optional, defaults to system default)
    provider: "claude-code"

    # NEW: Provider-specific config (optional)
    provider_config:
      # For ClaudeCode, these are optional
      cli_path: null  # Auto-detect
      api_key: null   # From ANTHROPIC_API_KEY env

    # Canonical model name (provider translates to specific ID)
    model: "sonnet-4.5"

    # Standard configuration (unchanged)
    max_tokens: 8000
    temperature: 0.7
```

**Example with OpenCode** (forward-looking):

```yaml
agent:
  metadata:
    name: Amelia
    role: Software Developer
    version: 1.0.0

  # ... (persona and tools same as above)

  configuration:
    # Use OpenCode with OpenAI
    provider: "opencode"

    provider_config:
      ai_provider: "openai"  # Use OpenAI instead of Anthropic
      cli_path: null         # Auto-detect

    model: "gpt-4"           # Canonical name (OpenCode translates)

    max_tokens: 8000
    temperature: 0.7
```

#### Step 4: Create Migration Guide

**File**: `docs/MIGRATION_PROVIDER.md`

```markdown
# Provider Configuration Migration Guide

This guide helps you migrate to GAO-Dev's new provider abstraction system introduced in Epic 11.

## Overview

GAO-Dev now supports multiple AI providers (Claude Code, OpenCode, Direct API, custom) while maintaining 100% backward compatibility.

## Do I Need to Migrate?

**No!** Your existing configurations will continue to work without any changes.

Migration is **optional** and only needed if you want to:
- Use a different provider (OpenCode, Direct API)
- Customize provider-specific settings
- Switch providers per-agent

## What Changed

### Before (Still Works)

```yaml
# gao_dev/config/agents/amelia.yaml
agent:
  configuration:
    model: "sonnet-4.5"
    max_tokens: 8000
    temperature: 0.7
```

### After (Optional)

```yaml
# gao_dev/config/agents/amelia.yaml
agent:
  configuration:
    provider: "claude-code"        # NEW: optional
    provider_config:                # NEW: optional
      cli_path: "/usr/bin/claude"
    model: "sonnet-4.5"
    max_tokens: 8000
    temperature: 0.7
```

## Migration Steps

### Step 1: Check Current Provider

```bash
# See what provider is currently configured
gao-dev providers list

# Output:
# Available providers:
#   ✓ claude-code (default) - Claude Code CLI
#   ✗ opencode - Not installed
#   ✗ direct-api - API key not set
```

### Step 2: Validate Configuration

```bash
# Validate all providers
gao-dev providers validate

# Output:
# Validating providers...
#   ✓ claude-code: Configured correctly
#   ⚠ opencode: CLI not found
#   ⚠ direct-api: API key not set
```

### Step 3: Update Agent Configs (Optional)

If you want to use a different provider for specific agents, update their YAML files:

```yaml
agent:
  configuration:
    provider: "opencode"
    provider_config:
      ai_provider: "openai"
    model: "gpt-4"
```

### Step 4: Test

```bash
# Test with specific provider
gao-dev sandbox run benchmark.yaml --provider opencode
```

## Example Configurations

### Use OpenCode with Anthropic

```yaml
configuration:
  provider: "opencode"
  provider_config:
    ai_provider: "anthropic"
  model: "sonnet-4.5"
```

### Use OpenCode with OpenAI

```yaml
configuration:
  provider: "opencode"
  provider_config:
    ai_provider: "openai"
  model: "gpt-4"
```

### Use Direct API (No CLI)

```yaml
configuration:
  provider: "direct-api"
  provider_config:
    provider: "anthropic"
    max_retries: 3
  model: "sonnet-4.5"
```

## Rollback

If you encounter issues, simply remove the `provider` and `provider_config` fields from your agent configurations. The system will default to Claude Code.

## Troubleshooting

### Provider Not Found

**Error**: `Provider 'opencode' not found`

**Solution**: Install the provider or check the name
```bash
gao-dev providers list
```

### Provider Not Configured

**Error**: `Provider 'claude-code' not properly configured`

**Solution**: Check API keys and CLI installation
```bash
gao-dev providers validate
```

## Support

- Documentation: `docs/features/agent-provider-abstraction/`
- Issues: https://github.com/anthropics/gao-dev/issues
- Provider list: `gao-dev providers list --help`
```

#### Step 5: Update Tests

**File**: `tests/core/test_config_schema_validation.py`

```python
"""Tests for configuration schema validation with provider support."""

import pytest
from pathlib import Path
import yaml
import jsonschema

from gao_dev.core.agent_config_loader import AgentConfigLoader


class TestAgentSchemaWithProviders:
    """Test agent schema validation with provider fields."""

    def test_agent_config_without_provider_valid(self, tmp_path):
        """Test agent config without provider field is valid (backward compat)."""
        config = {
            "agent": {
                "metadata": {
                    "name": "Test",
                    "role": "Tester",
                    "version": "1.0.0"
                },
                "persona": {
                    "background": "Test persona"
                },
                "tools": ["Read", "Write"],
                "configuration": {
                    "model": "sonnet-4.5",
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            }
        }

        # Write config
        config_file = tmp_path / "test.agent.yaml"
        config_file.write_text(yaml.dump(config))

        # Load and validate
        loader = AgentConfigLoader(tmp_path)
        agent_config = loader.load_agent("test")

        assert agent_config is not None

    def test_agent_config_with_provider_valid(self, tmp_path):
        """Test agent config with provider field is valid."""
        config = {
            "agent": {
                "metadata": {
                    "name": "Test",
                    "role": "Tester",
                    "version": "1.0.0"
                },
                "persona": {
                    "background": "Test persona"
                },
                "tools": ["Read", "Write"],
                "configuration": {
                    "provider": "claude-code",
                    "provider_config": {
                        "cli_path": "/usr/bin/claude"
                    },
                    "model": "sonnet-4.5",
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            }
        }

        # Write config
        config_file = tmp_path / "test.agent.yaml"
        config_file.write_text(yaml.dump(config))

        # Load and validate
        loader = AgentConfigLoader(tmp_path)
        agent_config = loader.load_agent("test")

        assert agent_config is not None
        # Check provider fields loaded (if AgentConfig model updated)

    def test_all_existing_agent_configs_valid(self):
        """Test all existing agent configs are valid."""
        agents_dir = Path("gao_dev/config/agents")
        loader = AgentConfigLoader(agents_dir)

        for agent_file in agents_dir.glob("*.agent.yaml"):
            agent_name = agent_file.stem.replace(".agent", "")
            agent_config = loader.load_agent(agent_name)
            assert agent_config is not None
```

---

## Testing Strategy

### Schema Validation Tests
- Old configs without provider fields validate
- New configs with provider fields validate
- Invalid provider configs rejected
- All existing agent configs validate

### Configuration Loading Tests
- Defaults applied when fields missing
- Provider fields loaded correctly
- Provider-specific validation works

### Integration Tests
- Agent configs loaded and used
- Provider selection works
- Default provider used when not specified

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] defaults.yaml updated with provider registry
- [ ] agent_schema.json updated with provider fields
- [ ] Migration guide created and reviewed
- [ ] All existing configs validate
- [ ] Schema validation tests passing
- [ ] Code reviewed and approved
- [ ] Type checking passing
- [ ] Documentation complete
- [ ] Changes committed
- [ ] Story marked complete

---

## Dependencies

**Upstream**:
- Story 11.3 (ProviderFactory) - MUST be complete

**Downstream**:
- All stories benefit from configuration support
- Story 11.7 (OpenCodeProvider) - needs OpenCode config

---

## Notes

- Backward compatibility is critical
- Clear migration guide essential
- Well-documented configuration examples
- Schema validation prevents configuration errors
- Provider defaults sensible for most users

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
- Story 11.3: `story-11.3.md` (ProviderFactory)
