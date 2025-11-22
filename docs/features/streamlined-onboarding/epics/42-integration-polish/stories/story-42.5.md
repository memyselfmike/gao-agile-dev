# Story 42.5: Deprecation Warnings and Migration Guide

## User Story

As an existing GAO-Dev user with scripts using old commands,
I want clear deprecation warnings with a migration timeline,
So that I can update my workflows before the old commands are removed.

## Acceptance Criteria

- [ ] AC1: `gao-dev init` shows deprecation warning when invoked
- [ ] AC2: `gao-dev web start` shows deprecation warning when invoked
- [ ] AC3: Warnings include the replacement command (`gao-dev start`)
- [ ] AC4: Warnings include removal timeline (e.g., "Will be removed in v3.0, estimated Q2 2026")
- [ ] AC5: Migration guide document covers all deprecated commands
- [ ] AC6: Migration guide includes before/after examples
- [ ] AC7: Migration guide addresses common scripts (CI/CD, Makefiles)
- [ ] AC8: Warnings are logged for telemetry (if enabled)
- [ ] AC9: `--quiet` flag suppresses warnings for gradual migration
- [ ] AC10: Release notes clearly document deprecations
- [ ] AC11: CHANGELOG updated with deprecation notices
- [ ] AC12: Deprecation tracked in GitHub issues for visibility

## Technical Notes

### Migration Guide Content

```markdown
# Migration Guide: Deprecated Commands

## Overview

As of GAO-Dev 2.0, the following commands are deprecated:
- `gao-dev init`
- `gao-dev web start`

They will be removed in GAO-Dev 3.0 (estimated Q2 2026).

## Why the Change?

The new `gao-dev start` command provides:
- Single entry point for all workflows
- Automatic environment detection
- Guided onboarding wizard
- Unified web/CLI experience

## Migration Examples

### Before: Creating a New Project

# Old way
mkdir my-project && cd my-project
gao-dev init
gao-dev web start

### After: Creating a New Project

# New way
mkdir my-project && cd my-project
gao-dev start

### Before: CI/CD Pipeline

# Old way
- name: Initialize GAO-Dev
  run: |
    gao-dev init --non-interactive
    gao-dev web start --headless &

### After: CI/CD Pipeline

# New way
- name: Start GAO-Dev
  run: gao-dev start --headless
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    AGENT_PROVIDER: claude-code

### Before: Makefile

# Old way
setup:
    gao-dev init
    gao-dev web start

### After: Makefile

# New way
setup:
    gao-dev start

## Suppressing Warnings

During migration, use --quiet to suppress deprecation warnings:

# Suppress warning while migrating
gao-dev init --quiet

## Feature Comparison

| Feature | gao-dev init + web start | gao-dev start |
|---------|--------------------------|---------------|
| Single command | No | Yes |
| Auto-detection | No | Yes |
| Onboarding wizard | No | Yes |
| Environment aware | No | Yes |
| CI/CD mode | Manual flags | Automatic |

## Timeline

- **2.0.0**: Commands deprecated with warnings
- **2.1.0**: Warnings become more prominent
- **3.0.0**: Commands removed (estimated Q2 2026)

## Getting Help

If you encounter issues during migration:
1. Check the [FAQ](./faq.md)
2. Search [GitHub Issues](https://github.com/gao-dev/gao-dev/issues)
3. Ask in [Discussions](https://github.com/gao-dev/gao-dev/discussions)
```

### Deprecation Warning Display

Already implemented in Story 40.5, but ensure:
- Consistent styling across all deprecated commands
- Same removal timeline mentioned everywhere
- Telemetry events logged (if enabled)

### CHANGELOG Entry

```markdown
### Deprecated

- `gao-dev init` command - use `gao-dev start` instead. Will be removed in v3.0.
- `gao-dev web start` command - use `gao-dev start` instead. Will be removed in v3.0.

See [Migration Guide](docs/migration/deprecated-commands.md) for details.
```

### GitHub Issue Template

```markdown
## Deprecation Tracking: gao-dev init

### Timeline
- **Deprecated**: v2.0.0 (2025-XX-XX)
- **Removal**: v3.0.0 (estimated Q2 2026)

### Replacement
Use `gao-dev start` instead.

### Migration Guide
See: docs/migration/deprecated-commands.md

### Telemetry
Track usage of deprecated command to inform removal timing.
```

## Test Scenarios

1. **Init warning displayed**: Given `gao-dev init` run, When executed, Then deprecation warning shows

2. **Web start warning displayed**: Given `gao-dev web start` run, When executed, Then deprecation warning shows

3. **Quiet flag works**: Given `gao-dev init --quiet`, When executed, Then no warning displayed

4. **Removal version shown**: Given any deprecated command, When warning displayed, Then shows "v3.0"

5. **Replacement command shown**: Given any deprecated command, When warning displayed, Then shows `gao-dev start`

6. **Migration guide exists**: Given migration guide path, When accessed, Then document found with examples

7. **CI/CD example works**: Given CI example from migration guide, When executed, Then works correctly

8. **Telemetry logged**: Given telemetry enabled, When deprecated command used, Then event logged

9. **CHANGELOG updated**: Given CHANGELOG checked, When searching deprecation, Then entries found

10. **GitHub issue exists**: Given GitHub issues checked, When searching deprecation, Then tracking issue found

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Migration guide complete and accurate
- [ ] CHANGELOG updated
- [ ] GitHub issues created for tracking
- [ ] Telemetry events configured
- [ ] Documentation links verified
- [ ] Release notes drafted
- [ ] Code reviewed

## Story Points: 3

## Dependencies

- Story 40.5: Deprecated Command Handling (implementation)
- Story 42.4: Documentation (for migration guide location)

## Notes

- Give users at least 12 months warning before removal
- Consider deprecation analytics to time removal
- Update any tutorials or external documentation
- Notify in Discord/community channels
- Consider blog post explaining the change
- Ensure removal is a major version bump (3.0)
