# Migration Guide - Git-Integrated Hybrid Architecture

This guide provides step-by-step instructions for migrating existing GAO-Dev projects from file-based state management to the new git-integrated hybrid architecture.

**Epic**: 27 - Integration & Migration
**Story**: 27.6 - Documentation & Migration Guide
**Last Updated**: 2025-11-09

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Pre-Migration Checklist](#pre-migration-checklist)
4. [Migration Process](#migration-process)
5. [Post-Migration Validation](#post-migration-validation)
6. [Rollback Procedure](#rollback-procedure)
7. [Common Issues](#common-issues)
8. [FAQ](#faq)

---

## Overview

### What is the Hybrid Architecture?

The git-integrated hybrid architecture combines:
- **Human-readable files** (markdown for epics/stories)
- **Structured database** (SQLite for fast queries)
- **Git transaction safety** (atomic commits, rollback support)

### Why Migrate?

**Benefits**:
- **Performance**: 100x faster state queries (database vs file scanning)
- **Consistency**: Automatic file-DB synchronization with validation
- **Safety**: Atomic transactions with automatic rollback on failure
- **Context Loading**: <5ms context loads with intelligent caching
- **Multi-Agent**: Enables ceremony orchestration and conversation management

### What Changes?

**Before Migration**:
```
project/
├── docs/
│   ├── epics/
│   │   └── epic-1.md          # File-based state
│   └── stories/
│       └── epic-1/
│           └── story-1.1.md   # File-based state
```

**After Migration**:
```
project/
├── .gao-dev/
│   ├── documents.db           # NEW: Database state
│   └── context.json           # Execution context
├── docs/
│   ├── epics/
│   │   └── epic-1.md          # Still human-readable
│   └── stories/
│       └── epic-1/
│           └── story-1.1.md   # Still human-readable
```

**Files remain human-readable**, but database provides fast access and enforces consistency.

---

## Prerequisites

### System Requirements

- **GAO-Dev Version**: >= 1.0.0 (with Epic 27 complete)
- **Python Version**: >= 3.11
- **Git**: Installed and accessible
- **Disk Space**: Estimate ~1KB per file (database overhead)

### Installation

Ensure you have the latest version:

```bash
cd gao-agile-dev
git pull origin main
pip install -e .
```

Verify installation:

```bash
gao-dev --version
# Should show version 1.0.0 or higher

gao-dev migrate --help
# Should show migration command options
```

---

## Pre-Migration Checklist

### 1. Backup Your Project

**Create full backup**:
```bash
# Tar backup
tar -czf project-backup-$(date +%Y%m%d).tar.gz /path/to/project

# Or git archive
cd /path/to/project
git archive --format=tar.gz --output=../project-backup.tar.gz HEAD
```

### 2. Commit All Changes

Migration requires a clean working tree:

```bash
cd /path/to/project

# Check status
git status

# Commit any pending changes
git add -A
git commit -m "chore: prepare for hybrid architecture migration"

# Or stash changes
git stash save "Before hybrid migration"
```

### 3. Verify Project Structure

Ensure standard structure:

```bash
# Required directories
ls -la docs/epics/      # Should contain epic-*.md files
ls -la docs/stories/    # Should contain epic-*/story-*.md files

# Optional but recommended
ls -la docs/architecture/
ls -la docs/prd/
```

### 4. Review Existing State

**Count your files**:
```bash
# Count epics
find docs/epics -name "epic-*.md" | wc -l

# Count stories
find docs/stories -name "story-*.md" | wc -l

# Total files to migrate
find docs -name "*.md" | wc -l
```

**Estimate migration time**:
- Small project (<10 files): ~5 seconds
- Medium project (10-100 files): ~1 minute
- Large project (100-1000 files): ~5 minutes
- Very large project (1000+ files): ~30 minutes

### 5. Test Migration (Dry Run)

**Preview migration without changes**:
```bash
gao-dev migrate --dry-run

# Output shows:
#   - Epics found: X
#   - Stories found: Y
#   - Database path: .gao-dev/documents.db
#   - Ready for migration
```

**Review output carefully**:
- Verify epic and story counts match expectations
- Check database path is correct
- Note any warnings

---

## Migration Process

### Step 1: Run Migration Command

**Basic migration** (recommended):
```bash
cd /path/to/project
gao-dev migrate

# Output:
# ======================================================================
# GAO-Dev Migration to Hybrid Architecture
# ======================================================================
#
# Project Path: /path/to/project
# Database Path: .gao-dev/documents.db
# Mode: LIVE MIGRATION
#
# Proceed with migration? [Y/n]: y
#
# Initializing migration manager...
# Starting migration...
# ----------------------------------------------------------------------
# Phase 1/4: Creating database tables...        [OK]
# Phase 2/4: Migrating epics from filesystem... [OK] (5 epics)
# Phase 3/4: Migrating stories from filesystem..[OK] (25 stories)
# Phase 4/4: Validating migration completeness..[OK]
#
# ======================================================================
# Migration Status: SUCCESS
# ======================================================================
#   Phase Completed: 4/4
#   Epics Migrated: 5
#   Stories Migrated: 25
#
# Summary: Migration completed successfully
#
# Git Checkpoints:
#   phase_1: abc12345
#   phase_2: def67890
#   phase_3: ghi12345
#   phase_4: jkl67890
#
# [OK] Migration completed successfully!
```

### Step 2: Migration Options

**Advanced options**:

```bash
# Skip branch isolation (migrate directly on current branch)
gao-dev migrate --no-branch

# Auto-merge migration branch after success
gao-dev migrate --auto-merge

# Specify custom database path
gao-dev migrate --db-path /custom/path/documents.db

# Migrate specific project (not current directory)
gao-dev migrate --project /path/to/project
```

### Step 3: Monitor Progress

Migration creates git commits after each phase:

```bash
# View migration commits
git log --oneline -10

# Example output:
# jkl67890 Migration Phase 4: Validation complete
# ghi12345 Migration Phase 3: Stories migrated (25 stories)
# def67890 Migration Phase 2: Epics migrated (5 epics)
# abc12345 Migration Phase 1: Database tables created
```

### Step 4: Migration Phases Explained

**Phase 1: Create Database Tables** (~1 second)
- Creates `.gao-dev/documents.db`
- Runs migration 005 (creates epics, stories, documents tables)
- Creates indexes for fast queries
- Git commit: "Migration Phase 1: Database schema created"

**Phase 2: Backfill Epics** (~100ms per epic)
- Scans `docs/epics/epic-*.md` files
- Parses metadata (title, description, dates)
- Inserts records into epics table
- Git commit: "Migration Phase 2: Epics migrated (X epics)"

**Phase 3: Backfill Stories** (~100ms per story)
- Scans `docs/stories/**/story-*.md` files
- Infers state from git history (completed if committed and closed)
- Inserts records into stories table
- Git commit: "Migration Phase 3: Stories migrated (Y stories)"

**Phase 4: Validate Migration** (~1 second)
- Verifies all files have DB records
- Checks referential integrity (story.epic_num → epics.epic_num)
- Validates state consistency
- Git commit: "Migration Phase 4: Validation complete"

---

## Post-Migration Validation

### Step 1: Run Consistency Check

Verify file-database consistency:

```bash
gao-dev consistency-check

# Output:
# ======================================================================
# GAO-Dev Consistency Check
# ======================================================================
#
# Project Path: /path/to/project
# Database Path: .gao-dev/documents.db
#
# Initializing consistency checker...
# Checking consistency...
# ----------------------------------------------------------------------
#
# ======================================================================
# Consistency Check Report - 2025-11-09 14:30:00
# ======================================================================
#
# [OK] No consistency issues found!
#   File and database state are in sync.
```

**If issues found**:
```bash
# Detailed report
gao-dev consistency-check --verbose

# Repair issues
gao-dev consistency-repair
```

### Step 2: Verify Database Contents

**Check database created**:
```bash
ls -lh .gao-dev/documents.db

# Example output:
# -rw-r--r-- 1 user group 245K Nov  9 14:30 .gao-dev/documents.db
```

**Query database** (optional):
```bash
sqlite3 .gao-dev/documents.db "SELECT COUNT(*) FROM epics;"
sqlite3 .gao-dev/documents.db "SELECT COUNT(*) FROM stories;"

# Or use CLI
gao-dev state list-epics
gao-dev state list-stories 1  # Stories for epic 1
```

### Step 3: Test State Queries

**Test fast queries**:
```bash
# List all epics (database query, <10ms)
gao-dev state list-epics

# Show story details (database query, <5ms)
gao-dev state show-story 1 1

# Show epic status (database aggregate, <10ms)
gao-dev state show-epic 1
```

**Compare with file scanning** (before migration):
- Database query: <10ms
- File scanning: 100-1000ms (10-100x slower!)

### Step 4: Test CLI Commands

**Test orchestrator initialization**:
```bash
# Should use GitIntegratedStateManager
python -c "
from gao_dev.orchestrator import GAODevOrchestrator
from pathlib import Path
orch = GAODevOrchestrator.create_default(Path.cwd())
print(f'Git State Manager: {orch.git_state_manager is not None}')
print(f'Fast Context Loader: {orch.fast_context_loader is not None}')
orch.close()
"

# Output:
# Git State Manager: True
# Fast Context Loader: True
```

**Test story creation** (uses hybrid mode):
```bash
gao-dev create-story --epic 1 --story 99 --title "Test Story"

# Verify created in both file and database
ls docs/stories/epic-1/story-1.99.md          # File exists
gao-dev state show-story 1 99                 # Database record exists
```

### Step 5: Verify Git History

**Check migration commits**:
```bash
git log --oneline --decorate --graph -10

# Should show 4 migration commits + merge commit
```

**Verify branch cleanup** (if used):
```bash
git branch -a

# Migration branch should be deleted after merge
# (unless --no-branch was used)
```

---

## Rollback Procedure

### Automatic Rollback

If migration fails, automatic rollback is performed:

```bash
gao-dev migrate

# If phase 3 fails:
# [ERROR] Migration failed: Database connection error
# [WARNING] Automatic rollback performed.
#   Project state restored to pre-migration.
```

**What happens during rollback**:
1. Delete migration branch (if created)
2. Reset to initial commit SHA (before migration started)
3. Remove `.gao-dev/documents.db` (if partially created)
4. Restore working tree to clean state

### Manual Rollback

If you need to rollback after successful migration:

**Option 1: Git Reset** (destructive):
```bash
# Find commit before migration
git log --oneline -20

# Reset to commit before migration phase 1
git reset --hard <commit-sha-before-migration>

# Remove database
rm -rf .gao-dev/documents.db
```

**Option 2: Git Revert** (safe, preserves history):
```bash
# Revert migration commits (phase 4 → phase 1)
git revert --no-edit jkl67890  # Phase 4
git revert --no-edit ghi12345  # Phase 3
git revert --no-edit def67890  # Phase 2
git revert --no-edit abc12345  # Phase 1

# Remove database
rm -rf .gao-dev/documents.db
```

**Option 3: Restore from Backup**:
```bash
# Extract backup
tar -xzf project-backup-YYYYMMDD.tar.gz

# Copy project files
cp -r project-backup/* /path/to/project/

# Reset git state
cd /path/to/project
git reset --hard HEAD~4  # Remove 4 migration commits
```

---

## Common Issues

### Issue 1: Working Tree Dirty

**Symptom**:
```
[ERROR] Migration failed: Working tree is dirty
  Cannot create migration branch with uncommitted changes.
  Please commit or stash changes before migration.
```

**Solution**:
```bash
# Option A: Commit changes
git add -A
git commit -m "chore: prepare for migration"

# Option B: Stash changes
git stash save "Before migration"

# Then retry migration
gao-dev migrate
```

### Issue 2: Database Already Exists

**Symptom**:
```
[WARNING] Database already exists. Migration may fail.
  Backup existing database before migrating.
```

**Solution**:
```bash
# Backup existing database
cp .gao-dev/documents.db .gao-dev/documents.db.backup

# Remove existing database
rm .gao-dev/documents.db

# Retry migration
gao-dev migrate
```

### Issue 3: File Parsing Errors

**Symptom**:
```
[ERROR] Migration Phase 2 failed: Failed to parse epic-5.md
  Invalid markdown format or missing metadata
```

**Solution**:
```bash
# Validate file format
cat docs/epics/epic-5.md

# Ensure file has proper structure:
# # Epic 5: Title
#
# ## Description
# ...

# Fix file format, then retry
gao-dev migrate
```

### Issue 4: Git Permission Denied

**Symptom**:
```
[ERROR] Migration failed: Permission denied (git)
  Cannot create git commit
```

**Solution**:
```bash
# Check git configuration
git config user.name
git config user.email

# Set if missing
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Retry migration
gao-dev migrate
```

### Issue 5: Disk Space Insufficient

**Symptom**:
```
[ERROR] Migration failed: No space left on device
```

**Solution**:
```bash
# Check disk space
df -h .gao-dev/

# Estimate required space
# Database size ≈ 1KB per file + overhead
# For 100 files: ~100KB + 100KB overhead = 200KB

# Free up space, then retry
gao-dev migrate
```

---

## FAQ

### Q: Will migration affect my existing files?

**A**: No. Migration only reads files and creates database records. Files remain unchanged.

### Q: Can I continue using file-based workflows?

**A**: Yes. Hybrid architecture maintains backward compatibility. You can still edit files manually, but database provides fast queries.

### Q: What if migration fails partway?

**A**: Automatic rollback restores project to pre-migration state. No data loss.

### Q: How long does migration take?

**A**: Approximately 100ms per file. For 100 files, expect ~10 seconds.

### Q: Can I migrate multiple projects?

**A**: Yes. Each project has isolated `.gao-dev/documents.db`. Migrate each project separately.

### Q: Does migration require internet connection?

**A**: No. Migration is entirely local.

### Q: What if I have uncommitted changes?

**A**: Commit or stash changes first. Migration requires clean working tree.

### Q: Can I undo migration?

**A**: Yes. Use git reset/revert to remove migration commits and delete database.

### Q: Will performance improve after migration?

**A**: Yes. Database queries are 10-100x faster than file scanning.

### Q: Is the database portable?

**A**: Yes. `.gao-dev/documents.db` can be moved with project.

### Q: Can I view database contents?

**A**: Yes. Use `sqlite3` CLI or `gao-dev state` commands.

### Q: What if I delete a file after migration?

**A**: Run `gao-dev consistency-repair` to sync database with filesystem.

### Q: Can I add files manually after migration?

**A**: Yes. New files are automatically detected and registered. Or use `gao-dev lifecycle register`.

### Q: Is migration reversible?

**A**: Yes. Git commits allow full rollback.

### Q: What about .gitignore?

**A**: Add `.gao-dev/` to `.gitignore` if you don't want to commit database.

### Q: Can I migrate partial project (only epics, no stories)?

**A**: Migration is all-or-nothing. All files migrated together for consistency.

---

## Next Steps

After successful migration:

1. **Read API Reference**: [API.md](./API.md) - Learn how to use services
2. **Troubleshooting Guide**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues
3. **Update CLAUDE.md**: Review git-integrated architecture section
4. **Test performance**: Run `pytest tests/performance/test_system_performance.py`
5. **Start using CLI**: `gao-dev state list-epics`, `gao-dev consistency-check`

---

## Support

For issues or questions:
- **GitHub Issues**: [gao-agile-dev/issues](https://github.com/your-org/gao-agile-dev/issues)
- **Documentation**: See `docs/features/git-integrated-hybrid-wisdom/`
- **Logs**: Check structured logs with `gao-dev` commands (JSON format)

---

**Migration Guide Version**: 1.0.0
**Last Updated**: 2025-11-09
**Epic**: 27 - Integration & Migration
**Story**: 27.6 - Documentation & Migration Guide
