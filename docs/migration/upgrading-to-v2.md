# Migration Guide: Upgrading to GAO-Dev v2.0

This guide covers upgrading from previous versions of GAO-Dev to v2.0.

## Table of Contents

- [What's New in v2.0](#whats-new-in-v20)
- [Pre-Upgrade Checklist](#pre-upgrade-checklist)
- [Upgrade Process](#upgrade-process)
- [Configuration Migration](#configuration-migration)
- [Database Migration](#database-migration)
- [Deprecated Features](#deprecated-features)
- [Breaking Changes](#breaking-changes)
- [Rollback Procedure](#rollback-procedure)

## What's New in v2.0

GAO-Dev v2.0 introduces significant improvements:

### New Features

1. **Interactive Provider Selection** - Choose AI providers at startup
2. **Web Interface** - Browser-based chat and file management
3. **Streamlined Onboarding** - Automated setup and configuration
4. **Enhanced CLI** - New commands and improved UX
5. **Better Performance** - Faster context loading and caching

### Architecture Changes

- Provider abstraction layer (no more hardcoded providers)
- Project-scoped document lifecycle (`.gao-dev/` per project)
- Git-integrated state management
- Self-learning feedback loop

## Pre-Upgrade Checklist

Before upgrading, complete these steps:

### 1. Backup Your Data

```bash
# Backup entire .gao-dev directory
cp -r .gao-dev .gao-dev.backup

# Backup any custom configurations
cp gao_dev/config/agents/*.yaml ./backup/agents/
cp gao_dev/config/prompts/**/*.yaml ./backup/prompts/
```

### 2. Document Current Configuration

```bash
# Record current version
gao-dev --version > upgrade-notes.txt

# Record environment variables
env | grep -E "GAO_DEV|ANTHROPIC|OPENAI" >> upgrade-notes.txt

# Record custom workflows
ls gao_dev/workflows/custom/ >> upgrade-notes.txt
```

### 3. Check Dependencies

```bash
# Verify Python version (3.10+ required for v2.0)
python --version

# Check for conflicting packages
pip list | grep anthropic
pip list | grep openai
```

### 4. Review Breaking Changes

Read the [Breaking Changes](#breaking-changes) section below before proceeding.

## Upgrade Process

### Step 1: Update the Repository

```bash
# Pull latest changes
git fetch origin
git checkout main
git pull origin main

# Or for specific version
git checkout tags/v2.0.0
```

### Step 2: Install Updated Dependencies

```bash
# Install in development mode
pip install -e .

# Or with all extras
pip install -e ".[dev,test,web]"
```

### Step 3: Run Migrations

```bash
# Database migration
gao-dev migrate

# Configuration migration
gao-dev config-migrate
```

### Step 4: Verify Installation

```bash
# Check version
gao-dev --version
# Expected: gao-dev 2.0.0

# Health check
gao-dev health

# Test startup
gao-dev start --dry-run
```

## Configuration Migration

### Provider Configuration

**Old Format (v1.x):**
```python
# In code or environment
ANTHROPIC_API_KEY=sk-ant-...
# Provider was hardcoded
```

**New Format (v2.0):**
```yaml
# .gao-dev/provider_preferences.yaml
provider: claude-code
backend: anthropic
model: claude-sonnet-4-20250514
timestamp: '2025-01-15T10:30:00Z'
```

**Migration:**
```bash
# v2.0 will prompt on first run
gao-dev start

# Or set via environment
export AGENT_PROVIDER=claude-code
export ANTHROPIC_API_KEY=sk-ant-...
```

### Environment Variables

| Old Variable | New Variable | Notes |
|-------------|--------------|-------|
| `ANTHROPIC_KEY` | `ANTHROPIC_API_KEY` | Standardized naming |
| `CLAUDE_MODEL` | `GAO_DEV_MODEL` | Provider-agnostic |
| `DEBUG` | `GAO_DEV_DEBUG` | Namespaced |

**Migration Script:**
```bash
# Update .env file
sed -i 's/ANTHROPIC_KEY=/ANTHROPIC_API_KEY=/g' .env
sed -i 's/CLAUDE_MODEL=/GAO_DEV_MODEL=/g' .env
sed -i 's/^DEBUG=/GAO_DEV_DEBUG=/g' .env
```

### Custom Agents

Agent YAML format updated for v2.0.

**Old Format:**
```yaml
name: custom-agent
prompt: |
  You are a custom agent...
```

**New Format:**
```yaml
agent:
  name: custom-agent
  role: Custom Role
  version: "1.0"

prompts:
  system: |
    You are a custom agent...

  templates:
    task: "@file:prompts/custom/task.yaml"
```

**Migration:**
```bash
# Run automatic conversion
gao-dev config-migrate --agents

# Or manually update format
# See docs/features/prompt-abstraction/MIGRATION_GUIDE.md
```

### Custom Workflows

Workflow YAML format updated.

**Old Format:**
```yaml
workflow:
  name: my-workflow
  steps:
    - agent: john
      task: create_prd
```

**New Format:**
```yaml
workflow:
  metadata:
    name: my-workflow
    version: "1.0"
    scale_level: 2

  steps:
    - agent: john
      task: create_prd
      artifacts:
        - type: prd
          location: "{{prd_location}}"
```

## Database Migration

### Automatic Migration

```bash
# Run all pending migrations
gao-dev migrate

# Check migration status
gao-dev db-status

# View migration history
gao-dev migration-history
```

### Manual Migration (if needed)

```bash
# Export data before migration
gao-dev export --format json --output backup.json

# Apply specific migration
gao-dev migrate --target 007_workflow_adjustments

# Import data after migration
gao-dev import --format json --input backup.json
```

### Migration from Global to Project-Scoped

GAO-Dev v2.0 uses project-scoped databases.

**Old Location:**
```
gao-agile-dev/
  .gao-dev/
    documents.db  # Global database
```

**New Location:**
```
your-project/
  .gao-dev/
    documents.db  # Project-specific
```

**Migration:**
```bash
# Navigate to your project
cd /path/to/your-project

# Initialize project-scoped tracking
gao-dev init

# Import from old global database (if needed)
gao-dev import-legacy --source /path/to/old/.gao-dev/documents.db
```

## Deprecated Features

### Deprecated Commands

These commands are deprecated and will be removed in v3.0:

| Deprecated | Replacement | Notes |
|------------|-------------|-------|
| `gao-dev run` | `gao-dev start` | Interactive REPL |
| `gao-dev execute-workflow` | `gao-dev run-workflow` | Renamed |
| `gao-dev agent-spawn` | Removed | Use orchestrator |
| `gao-dev init-sandbox` | `gao-dev sandbox init` | Moved to subcommand |

### Deprecated Configuration

| Deprecated | Replacement |
|------------|-------------|
| `prompts/hardcoded.py` | `config/prompts/*.yaml` |
| `AgentSpawner` class | `GAODevOrchestrator` |
| Direct provider imports | Provider factory |

### Migration for Deprecated Features

```bash
# Update scripts using old commands
sed -i 's/gao-dev run/gao-dev start/g' your-script.sh
sed -i 's/gao-dev execute-workflow/gao-dev run-workflow/g' your-script.sh
```

## Breaking Changes

### 1. Provider Configuration Required

v2.0 requires explicit provider configuration.

**Impact:** Scripts that assumed Claude Code will fail.

**Fix:**
```bash
export AGENT_PROVIDER=claude-code
# or
export AGENT_PROVIDER=direct-api-anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Project Isolation

Each project now has its own `.gao-dev/` directory.

**Impact:** Global state is no longer shared.

**Fix:**
- Initialize `.gao-dev/` in each project
- Migrate relevant data from global database

### 3. Import Path Changes

```python
# Old
from gao_dev.agents import spawn_agent

# New
from gao_dev.orchestrator import GAODevOrchestrator
orchestrator = GAODevOrchestrator()
```

### 4. CLI Output Format

Output format changed for better parsing.

**Impact:** Scripts parsing CLI output may break.

**Fix:**
- Use `--format json` for machine-readable output
- Update parsing logic for new format

### 5. Configuration File Locations

```
# Old
gao_dev/config.yaml

# New
gao_dev/config/defaults.yaml
.gao-dev/provider_preferences.yaml
```

## Rollback Procedure

If you need to rollback to v1.x:

### Step 1: Restore Code

```bash
# Checkout previous version
git checkout tags/v1.9.0

# Reinstall
pip install -e .
```

### Step 2: Restore Data

```bash
# Restore backed up data
rm -rf .gao-dev
cp -r .gao-dev.backup .gao-dev

# Restore configuration
cp ./backup/agents/*.yaml gao_dev/config/agents/
```

### Step 3: Verify

```bash
gao-dev --version
# Should show v1.x

gao-dev health
```

## Post-Upgrade Tasks

### 1. Update CI/CD Pipelines

```yaml
# Update environment variables
env:
  AGENT_PROVIDER: claude-code  # NEW
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### 2. Update Documentation

Update any internal documentation referencing:
- Old command names
- Old configuration format
- Old environment variables

### 3. Train Team

Key changes to communicate:
- Interactive provider selection on first run
- New `gao-dev start` command
- Project-scoped configuration
- Web interface availability

### 4. Monitor

Watch for issues in first week:
- Check error logs
- Monitor performance
- Collect team feedback

## Getting Help

### Upgrade Support

- **Documentation**: `docs/INDEX.md`
- **Troubleshooting**: `docs/troubleshooting/common-errors.md`
- **Migration Guides**: `docs/migration/`

### Known Issues

Check the GitHub issues page for known v2.0 issues:
- Filter by label: `v2.0`, `migration`

### Community

- Share your upgrade experience
- Report issues encountered
- Suggest improvements

---

**See Also:**
- [Quick Start Guide](../getting-started/quick-start.md)
- [Environment Variables Reference](../guides/environment-variables.md)
- [Troubleshooting Guide](../troubleshooting/common-errors.md)

---

**Last Updated**: 2025-11-19
