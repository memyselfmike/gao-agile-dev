# Migration Guide: Deprecated Commands

This guide covers the deprecated commands in GAO-Dev and how to migrate to their replacements.

## Table of Contents

- [Overview](#overview)
- [Deprecated Commands](#deprecated-commands)
- [Migration Examples](#migration-examples)
- [CI/CD Pipeline Updates](#cicd-pipeline-updates)
- [Makefile Updates](#makefile-updates)
- [Feature Comparison](#feature-comparison)
- [Timeline](#timeline)
- [Suppressing Warnings](#suppressing-warnings)
- [FAQ](#faq)

## Overview

GAO-Dev v2.0 introduces a unified startup experience with `gao-dev start`. The following commands are deprecated and will be removed in v3.0 (scheduled for Q2 2026):

- `gao-dev init`
- `gao-dev web start`

### Why the Change?

The new `gao-dev start` command provides:

1. **Intelligent Environment Detection** - Automatically detects your environment and project state
2. **Unified Experience** - Single command for all startup scenarios
3. **Interactive Provider Selection** - Choose AI providers at startup
4. **Guided Setup Wizard** - Step-by-step onboarding for new users
5. **Brownfield Support** - Seamless integration with existing projects

## Deprecated Commands

### gao-dev init

**Status**: Deprecated in v2.0.0, removal in v3.0.0

**Old Usage**:
```bash
gao-dev init --name "My Project"
```

**New Usage**:
```bash
gao-dev start
```

The `gao-dev start` command automatically detects whether you need initialization and guides you through the process.

**Current Behavior**:
- Shows deprecation warning
- Waits 5 seconds (unless `--no-wait`)
- Redirects to `gao-dev start`

### gao-dev web start

**Status**: Deprecated in v2.0.0, removal in v3.0.0

**Old Usage**:
```bash
gao-dev web start --port 3000
```

**New Usage**:
```bash
gao-dev start --port 3000
```

The `gao-dev start` command detects your environment and launches the appropriate interface (web or CLI).

**Current Behavior**:
- Shows deprecation warning
- Waits 5 seconds (unless `--no-wait`)
- Redirects to `gao-dev start`

## Migration Examples

### Basic Migration

**Before (v1.x)**:
```bash
# Initialize new project
gao-dev init --name "Todo App"

# Start web interface
gao-dev web start
```

**After (v2.0)**:
```bash
# Single command handles everything
gao-dev start
```

### With Custom Port

**Before**:
```bash
gao-dev web start --port 8080 --no-browser
```

**After**:
```bash
gao-dev start --port 8080 --no-browser
```

### Headless Mode (CI/CD)

**Before**:
```bash
gao-dev init --name "My Project"
# Then manually configure providers...
```

**After**:
```bash
# Set environment variables for automated setup
export AGENT_PROVIDER=claude-code
export ANTHROPIC_API_KEY=sk-ant-...

# Headless mode skips interactive prompts
gao-dev start --headless
```

### Script Migration

**Before**:
```bash
#!/bin/bash
# setup.sh

# Initialize project
gao-dev init --name "$PROJECT_NAME"

# Start web server
gao-dev web start --port 3000 &
```

**After**:
```bash
#!/bin/bash
# setup.sh

# Set provider (skip interactive prompts)
export AGENT_PROVIDER="${AGENT_PROVIDER:-claude-code}"

# Single command handles init + start
gao-dev start --port 3000
```

## CI/CD Pipeline Updates

### GitHub Actions

**Before**:
```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install GAO-Dev
        run: pip install -e .

      - name: Initialize Project
        run: gao-dev init --name "CI Test"
```

**After**:
```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    env:
      AGENT_PROVIDER: direct-api-anthropic
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install GAO-Dev
        run: pip install -e .

      - name: Start GAO-Dev (Headless)
        run: gao-dev start --headless
```

### GitLab CI

**Before**:
```yaml
setup:
  script:
    - pip install -e .
    - gao-dev init --name "CI Test"
    - gao-dev web start --port 3000 &
```

**After**:
```yaml
setup:
  variables:
    AGENT_PROVIDER: direct-api-anthropic
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
  script:
    - pip install -e .
    - gao-dev start --headless --port 3000
```

### Jenkins Pipeline

**Before**:
```groovy
pipeline {
    stages {
        stage('Setup') {
            steps {
                sh 'gao-dev init --name "Jenkins Build"'
                sh 'gao-dev web start &'
            }
        }
    }
}
```

**After**:
```groovy
pipeline {
    environment {
        AGENT_PROVIDER = 'direct-api-anthropic'
        ANTHROPIC_API_KEY = credentials('anthropic-key')
    }
    stages {
        stage('Setup') {
            steps {
                sh 'gao-dev start --headless'
            }
        }
    }
}
```

### Azure DevOps

**Before**:
```yaml
steps:
  - script: |
      pip install -e .
      gao-dev init --name "Azure Build"
      gao-dev web start --port 3000 &
    displayName: 'Setup GAO-Dev'
```

**After**:
```yaml
variables:
  AGENT_PROVIDER: 'direct-api-anthropic'

steps:
  - script: |
      pip install -e .
      gao-dev start --headless --port 3000
    displayName: 'Start GAO-Dev'
    env:
      ANTHROPIC_API_KEY: $(ANTHROPIC_API_KEY)
```

## Makefile Updates

**Before**:
```makefile
# Makefile

.PHONY: init start dev

init:
	gao-dev init --name "$(PROJECT_NAME)"

start:
	gao-dev web start --port 3000

dev: init start
```

**After**:
```makefile
# Makefile

.PHONY: start dev

# Suppress deprecation warnings with --quiet for scripts
start:
	gao-dev start --port 3000

# Headless mode for CI
start-ci:
	AGENT_PROVIDER=claude-code gao-dev start --headless

dev: start

# If you need to see the warning once
init:
	@echo "NOTE: 'make init' is deprecated. Use 'make start' instead."
	gao-dev init --name "$(PROJECT_NAME)" --quiet --no-wait
```

## Feature Comparison

| Feature | gao-dev init | gao-dev web start | gao-dev start |
|---------|-------------|-------------------|---------------|
| Project initialization | Yes | No | Yes |
| Web interface | No | Yes | Yes |
| CLI interface | No | No | Yes |
| Provider selection | No | No | Yes |
| Environment detection | No | No | Yes |
| Brownfield support | No | No | Yes |
| Greenfield support | Yes | No | Yes |
| Interactive wizard | No | No | Yes |
| Headless mode | No | No | Yes |
| Custom port | N/A | Yes | Yes |
| Auto-open browser | N/A | Yes | Yes |
| Context persistence | No | No | Yes |
| Session management | No | Limited | Full |
| Scale level detection | No | No | Yes |
| TUI wizard | No | No | Yes |

## Timeline

| Version | Date | Action |
|---------|------|--------|
| v2.0.0 | 2025-01 | Commands deprecated, warnings added |
| v2.1.0 | 2025-03 | Warnings become more prominent |
| v2.5.0 | 2025-06 | Usage statistics collected for removal planning |
| v3.0.0 | Q2 2026 | Commands removed |

### Deprecation Notice Phases

1. **v2.0.0 - Initial Deprecation**
   - Commands work but show warnings
   - 5-second delay before redirect
   - Full documentation available

2. **v2.1.0 - Enhanced Warnings**
   - Warnings highlighted more prominently
   - Shorter redirect delay (3 seconds)
   - Migration reminders in error messages

3. **v2.5.0 - Final Warning**
   - Commands flagged as "pending removal"
   - Warning cannot be suppressed for interactive use
   - CI/CD can still use `--quiet`

4. **v3.0.0 - Removal**
   - Commands removed
   - Clear error message points to migration guide
   - No functionality remains

## Suppressing Warnings

### For Scripts and CI/CD

Use `--quiet` flag to suppress warnings (still logged):

```bash
# Suppress visual warning
gao-dev init --name "Project" --quiet

# Also skip the delay
gao-dev init --name "Project" --quiet --no-wait

# Web start equivalent
gao-dev web start --quiet --no-wait
```

### Environment Variable

Set `GAO_DEV_QUIET=1` to suppress all deprecation warnings:

```bash
export GAO_DEV_QUIET=1
gao-dev init --name "Project"  # No warning displayed
```

### Important Notes

1. Warnings are always logged at WARNING level regardless of suppression
2. `--quiet` affects display only, not logging
3. Telemetry still tracks deprecated command usage
4. Suppression is for automation, not to ignore the migration

## FAQ

### Q: Do I have to migrate immediately?

No. The deprecated commands will continue to work until v3.0 (Q2 2026). However, we recommend migrating soon to benefit from the improved features.

### Q: Will my existing projects break?

No. The deprecated commands redirect to `gao-dev start`, which handles all existing scenarios. Your projects will continue to work.

### Q: How do I migrate existing scripts?

1. Replace `gao-dev init` with `gao-dev start --headless`
2. Replace `gao-dev web start` with `gao-dev start`
3. Set `AGENT_PROVIDER` environment variable for CI/CD

### Q: What if I need initialization only?

`gao-dev start` handles initialization automatically when needed. If you explicitly need init-only behavior:

```bash
# Initialize without launching interface
gao-dev start --headless
# Then exit after initialization completes
```

### Q: How do I track deprecation warnings in my CI/CD?

Check logs for `deprecated_command_used` events:

```bash
# In GitHub Actions
- name: Check for deprecation warnings
  run: |
    gao-dev init --quiet 2>&1 | grep -c "deprecated_command_used" && \
    echo "::warning::Using deprecated commands"
```

### Q: Can I still use --name with gao-dev start?

The `--name` parameter is not needed. `gao-dev start` will prompt for the project name during interactive setup or detect it automatically for existing projects.

For CI/CD, the project name is taken from the current directory name.

### Q: What about custom configurations I passed to init?

Any custom configuration should be set via:
- Environment variables (`AGENT_PROVIDER`, `GAO_DEV_*`)
- Configuration files (`.gao-dev/provider_preferences.yaml`)
- Interactive prompts (for first-time setup)

---

## Getting Help

### Resources

- **Quick Start**: `docs/getting-started/quick-start.md`
- **Environment Variables**: `docs/guides/environment-variables.md`
- **Troubleshooting**: `docs/troubleshooting/common-errors.md`
- **Upgrade Guide**: `docs/migration/upgrading-to-v2.md`

### Support

If you encounter issues migrating:

1. Check the FAQ above
2. Search existing GitHub issues
3. Create a new issue with the `deprecation` label
4. Include your current command and expected behavior

### Feedback

We welcome feedback on the deprecation process:

- Timeline concerns
- Migration difficulties
- Feature requests for `gao-dev start`

Create an issue with the `feedback` label.

---

**See Also:**
- [Upgrading to v2.0](upgrading-to-v2.md)
- [Quick Start Guide](../getting-started/quick-start.md)
- [Environment Variables Reference](../guides/environment-variables.md)

---

**Last Updated**: 2025-11-19
