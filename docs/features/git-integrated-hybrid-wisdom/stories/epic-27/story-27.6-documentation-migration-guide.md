# Story 27.6: Documentation and Migration Guide

**Epic**: Epic 27 - Integration & Migration
**Story ID**: 27.6
**Priority**: P0
**Estimate**: 6 hours
**Owner**: Amelia + Bob
**Status**: Todo

---

## Story Description

Complete all documentation for production release: update CLAUDE.md with new architecture, create comprehensive migration guide, document API, create troubleshooting guide.

---

## Acceptance Criteria

- [ ] CLAUDE.md updated with hybrid architecture overview
- [ ] Migration guide complete with step-by-step instructions
- [ ] API documentation complete for all new services
- [ ] Troubleshooting guide with common issues and solutions
- [ ] Examples and tutorials for all major features
- [ ] Performance characteristics documented
- [ ] Architecture diagrams updated

---

## Files to Create

- `docs/features/git-integrated-hybrid-wisdom/MIGRATION_GUIDE.md` (~500 LOC)
  - Pre-migration checklist
  - Step-by-step migration instructions
  - Rollback procedures
  - Common migration issues and solutions

- `docs/features/git-integrated-hybrid-wisdom/API.md` (~400 LOC)
  - Complete API reference for all services
  - Code examples
  - Usage patterns

- `docs/features/git-integrated-hybrid-wisdom/TROUBLESHOOTING.md` (~300 LOC)
  - Common issues and solutions
  - Debugging tips
  - Performance tuning
  - FAQ

## Files to Modify

- `CLAUDE.md` (+~200 LOC)
  - Add: Hybrid Architecture section
  - Add: Git Transaction Model section
  - Add: State Services section
  - Add: Fast Context Loading section
  - Add: Multi-Agent Ceremonies section
  - Update: Core Services reference
  - Update: Quick Reference table

---

## CLAUDE.md Updates

Add new sections:

```markdown
## Hybrid Architecture (NEW)

GAO-Dev uses a hybrid architecture combining SQLite for fast queries and Markdown for human-readable documentation.

**Key Benefits**:
- 10-20x faster context loading (5ms vs 50-100ms)
- 15x less data transferred (2KB vs 31KB)
- 100% data consistency via git transactions
- Full rollback capability

**Git Transaction Model**:
Every state change = one atomic git commit bundling file + database changes.

**See**: [Architecture Guide](docs/features/git-integrated-hybrid-wisdom/ARCHITECTURE.md)

## Core Services (UPDATED)

### GitIntegratedStateManager
**Purpose**: Atomic operations via git commits
**Methods**: create_epic(), create_story(), transition_story()
**Pattern**: File + DB + Git Commit (atomic)

### FastContextLoader
**Purpose**: <5ms context queries
**Methods**: get_epic_context(), get_agent_context()
**Performance**: <5ms for epic with 50 stories

### CeremonyOrchestrator
**Purpose**: Multi-agent ceremonies
**Methods**: hold_standup(), hold_retrospective(), hold_planning()
**Integration**: Uses FastContextLoader for real-time context

## Migration Guide

Existing projects can migrate to hybrid architecture:

\`\`\`bash
# Preview migration
gao-dev migrate --dry-run

# Execute migration
gao-dev migrate

# Rollback if needed
gao-dev migrate --rollback
\`\`\`

**See**: [Migration Guide](docs/features/git-integrated-hybrid-wisdom/MIGRATION_GUIDE.md)
```

---

## Migration Guide Structure

```markdown
# Migration Guide: Hybrid Architecture

## Overview
This guide walks through migrating an existing GAO-Dev project to the hybrid architecture...

## Pre-Migration Checklist
- [ ] Git repository clean (no uncommitted changes)
- [ ] Backup created
- [ ] GAO-Dev version >=2.0.0
- [ ] Python >=3.11
- [ ] Git >=2.30

## Migration Steps

### Step 1: Dry Run
\`\`\`bash
gao-dev migrate --dry-run
\`\`\`

### Step 2: Execute Migration
\`\`\`bash
gao-dev migrate
\`\`\`

### Step 3: Validate
\`\`\`bash
gao-dev consistency-check
\`\`\`

### Step 4: Test
...

## Rollback Procedure
If migration fails or causes issues:
\`\`\`bash
gao-dev migrate --rollback
\`\`\`

## Common Issues
...

## Performance Tuning
...
```

---

## Troubleshooting Guide Structure

```markdown
# Troubleshooting Guide

## Common Issues

### Issue 1: Migration Fails with "Uncommitted Changes"
**Symptom**: Migration fails immediately
**Cause**: Working tree has uncommitted changes
**Solution**: Commit or stash changes before migration

### Issue 2: Context Loading Slow (>5ms)
**Symptom**: Performance slower than expected
**Cause**: Database not indexed, too many stories
**Solution**: Run \`ANALYZE\` on database, archive old epics

### Issue 3: File-Database Inconsistency
**Symptom**: Consistency check reports mismatches
**Cause**: Manual file edits outside git transactions
**Solution**: Run \`gao-dev consistency-check --repair\`

...

## Debugging Tips
...

## Performance Tuning
...

## FAQ
...
```

---

## Definition of Done

- [ ] CLAUDE.md updated
- [ ] Migration guide complete
- [ ] API documentation complete
- [ ] Troubleshooting guide complete
- [ ] All documentation reviewed
- [ ] Examples validated
- [ ] Git commit: "docs(epic-27): complete documentation and migration guide"

---

**Created**: 2025-11-09
