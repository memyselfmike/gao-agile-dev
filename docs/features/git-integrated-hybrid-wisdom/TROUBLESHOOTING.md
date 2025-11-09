# Troubleshooting Guide - Git-Integrated Hybrid Architecture

Common issues, solutions, and debugging techniques for the git-integrated hybrid architecture.

**Epic**: 27 - Integration & Migration
**Story**: 27.6 - Documentation & Migration Guide
**Last Updated**: 2025-11-09

---

## Table of Contents

1. [Migration Issues](#migration-issues)
2. [Consistency Issues](#consistency-issues)
3. [Performance Issues](#performance-issues)
4. [Git-Related Issues](#git-related-issues)
5. [Database Issues](#database-issues)
6. [Context Loading Issues](#context-loading-issues)
7. [Debug Logging](#debug-logging)
8. [Getting Help](#getting-help)

---

## Migration Issues

### Issue: Working Tree Dirty

**Symptom**:
```
[ERROR] Migration failed: Working tree is dirty
  Cannot create migration branch with uncommitted changes
```

**Cause**: Git working tree has uncommitted changes.

**Solution**:
```bash
# Option 1: Commit changes
git add -A
git commit -m "chore: prepare for migration"

# Option 2: Stash changes
git stash save "Before hybrid migration"

# Option 3: Check what's uncommitted
git status

# Then retry migration
gao-dev migrate
```

**Prevention**: Always commit or stash before migration.

---

### Issue: Database Already Exists

**Symptom**:
```
[WARNING] Database already exists. Migration may fail.
  File: .gao-dev/documents.db
```

**Cause**: Previous migration or manual database creation.

**Solution**:
```bash
# 1. Backup existing database
cp .gao-dev/documents.db .gao-dev/documents.db.backup-$(date +%Y%m%d)

# 2. Remove database
rm .gao-dev/documents.db

# 3. Retry migration
gao-dev migrate

# If needed, restore backup
# cp .gao-dev/documents.db.backup-YYYYMMDD .gao-dev/documents.db
```

**Alternative**: Use `--db-path` to specify different database location.

---

### Issue: File Parsing Errors

**Symptom**:
```
[ERROR] Migration Phase 2 failed: Failed to parse epic-5.md
  Invalid markdown format or missing metadata
```

**Cause**: Malformed epic/story file.

**Solution**:
```bash
# 1. Identify problematic file
cat docs/epics/epic-5.md

# 2. Validate format
# Expected structure:
# # Epic 5: Title
#
# ## Description
# Epic description here
#
# ## Stories
# - Story 5.1: ...

# 3. Fix format issues

# 4. Retry migration
gao-dev migrate
```

**Common format issues**:
- Missing title (`# Epic X: Title`)
- Missing description section
- Invalid epic/story number in filename
- Non-ASCII characters (use UTF-8)

---

### Issue: Migration Rollback Failed

**Symptom**:
```
[ERROR] Rollback failed: Cannot reset to commit abc123
  Working tree conflicts detected
```

**Cause**: File conflicts during rollback.

**Solution**:
```bash
# 1. Check git status
git status

# 2. Resolve conflicts manually
# Edit conflicted files
# Remove conflict markers (<<<<<<<, =======, >>>>>>>)

# 3. Complete rollback manually
git reset --hard <commit-before-migration>

# 4. Cleanup database
rm -rf .gao-dev/documents.db

# 5. Verify clean state
git status
```

---

### Issue: Permission Denied (Git)

**Symptom**:
```
[ERROR] Migration failed: Permission denied (git)
  Cannot create git commit
```

**Cause**: Git configuration missing or insufficient permissions.

**Solution**:
```bash
# 1. Check git configuration
git config user.name
git config user.email

# 2. Set if missing
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 3. Check file permissions
ls -la .git/

# 4. Retry migration
gao-dev migrate
```

---

## Consistency Issues

### Issue: Orphaned Database Records

**Symptom**:
```
[WARNING] Consistency check found 5 orphaned records
  DB records exist but files deleted from filesystem
```

**Cause**: Files deleted without updating database.

**Solution**:
```bash
# 1. Run consistency check
gao-dev consistency-check --verbose

# 2. Review orphaned records
# Output shows which epics/stories are orphaned

# 3. Repair automatically (files are source of truth)
gao-dev consistency-repair

# Database records for deleted files will be removed
```

**Prevention**: Use `gao-dev lifecycle archive <path>` instead of manual deletion.

---

### Issue: Unregistered Files

**Symptom**:
```
[WARNING] Consistency check found 3 unregistered files
  Files exist but not in database
```

**Cause**: Files created manually without database registration.

**Solution**:
```bash
# 1. Run consistency check
gao-dev consistency-check --verbose

# 2. Review unregistered files
# Output shows which files are unregistered

# 3. Repair automatically (files are source of truth)
gao-dev consistency-repair

# Files will be registered in database
```

**Alternative**: Register files manually:
```bash
gao-dev lifecycle register docs/epics/epic-99.md epic
```

---

### Issue: State Mismatches

**Symptom**:
```
[WARNING] Consistency check found state mismatches
  DB state: in_progress | Git state: completed
```

**Cause**: Database state not synced with git history.

**Solution**:
```bash
# 1. Run consistency check
gao-dev consistency-check --verbose

# 2. Review mismatches
# Shows DB state vs. git-inferred state

# 3. Repair (git history is source of truth for state)
gao-dev consistency-repair

# Database states updated from git history
```

**Understanding git-inferred state**:
- Committed + merged → `completed`
- Committed but not merged → `in_progress`
- Uncommitted → `planning`

---

### Issue: Consistency Repair Fails

**Symptom**:
```
[ERROR] Consistency repair failed: Database locked
```

**Cause**: Database file locked by another process.

**Solution**:
```bash
# 1. Check for open database connections
lsof .gao-dev/documents.db  # Linux/Mac
# Or check Task Manager on Windows

# 2. Close any open connections
# Kill processes using database

# 3. Retry repair
gao-dev consistency-repair
```

---

## Performance Issues

### Issue: Slow Context Loading

**Symptom**: Context loading takes >100ms (expected: <5ms with cache).

**Diagnosis**:
```python
from gao_dev.core.context.fast_context_loader import FastContextLoader

loader = FastContextLoader(project_root=Path.cwd()))

# Check cache stats
stats = loader.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")  # Should be >80%
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")
```

**Solutions**:

1. **Low cache hit rate (<50%)**:
   ```python
   # Increase cache size
   loader = FastContextLoader(
       project_root=Path.cwd()),
       cache_size=200,  # Default: 100
       cache_ttl_seconds=600  # Default: 300
   )
   ```

2. **Cache warming**:
   ```python
   # Preload contexts for batch operations
   await loader.preload_contexts(epic_num=1, story_nums=range(1, 11))
   ```

3. **Large file sizes**:
   ```bash
   # Check file sizes
   du -sh docs/epics/*.md docs/stories/**/*.md

   # If files >1MB, consider splitting or summarizing
   ```

---

### Issue: Slow Epic/Story Creation

**Symptom**: Epic/story creation takes >1 second (expected: <200ms).

**Diagnosis**:
```bash
# Enable performance logging
export GAO_DEV_LOG_LEVEL=DEBUG

# Run operation
gao-dev create-story --epic 1 --story 99 --title "Test"

# Check logs for slow operations
# Look for "duration_ms" in JSON logs
```

**Common causes**:

1. **Large git repository**:
   ```bash
   # Check repo size
   du -sh .git/

   # If >1GB, consider:
   # - Git garbage collection: git gc --aggressive
   # - Remove large files from history: git filter-branch
   ```

2. **Slow disk I/O**:
   ```bash
   # Test disk speed
   dd if=/dev/zero of=test.tmp bs=1M count=100
   rm test.tmp

   # If <50MB/s, disk may be bottleneck
   ```

3. **Database fragmentation**:
   ```bash
   # Vacuum database
   sqlite3 .gao-dev/documents.db "VACUUM;"
   ```

---

### Issue: High Memory Usage

**Symptom**: Process memory >1GB for normal operations.

**Diagnosis**:
```python
import psutil
import os

process = psutil.Process(os.getpid())
memory_mb = process.memory_info().rss / 1024 / 1024
print(f"Memory usage: {memory_mb:.2f} MB")
```

**Solutions**:

1. **Reduce cache size**:
   ```python
   loader = FastContextLoader(
       project_root=Path.cwd()),
       cache_size=50  # Reduce from 100
   )
   ```

2. **Clear cache periodically**:
   ```python
   loader.clear_cache()
   ```

3. **Close orchestrator when done**:
   ```python
   orchestrator.close()  # Releases resources
   ```

---

## Git-Related Issues

### Issue: Git Command Not Found

**Symptom**:
```
[ERROR] Git command failed: git: command not found
```

**Cause**: Git not installed or not in PATH.

**Solution**:
```bash
# 1. Check git installation
which git  # Linux/Mac
where git  # Windows

# 2. Install git if missing
# Linux: sudo apt-get install git
# Mac: brew install git
# Windows: Download from https://git-scm.com/

# 3. Verify installation
git --version
```

---

### Issue: Detached HEAD State

**Symptom**:
```
[WARNING] Repository in detached HEAD state
  Cannot create commits
```

**Cause**: HEAD not pointing to branch.

**Solution**:
```bash
# 1. Check current state
git status

# 2. Create branch from detached HEAD
git checkout -b temp-branch

# 3. Or return to main branch
git checkout main

# 4. Retry operation
```

---

### Issue: Merge Conflicts

**Symptom**:
```
[ERROR] Merge conflict detected during migration
  Cannot auto-merge migration branch
```

**Cause**: Concurrent changes to same files.

**Solution**:
```bash
# 1. Check merge status
git status

# 2. Resolve conflicts manually
# Edit conflicted files
# Remove conflict markers

# 3. Complete merge
git add -A
git merge --continue

# 4. Or abort merge
git merge --abort
```

---

## Database Issues

### Issue: Database Locked

**Symptom**:
```
[ERROR] Database is locked
  database is locked (5)
```

**Cause**: Another process has exclusive lock on database.

**Solution**:
```bash
# 1. Check for open connections
lsof .gao-dev/documents.db  # Linux/Mac

# 2. Close other processes using database

# 3. If persistent, restart SQLite:
# Close all GAO-Dev processes
# Wait 5 seconds
# Retry operation

# 4. As last resort, remove lock file
rm -f .gao-dev/.documents.db-lock
```

---

### Issue: Database Corruption

**Symptom**:
```
[ERROR] Database disk image is malformed
  file is not a database
```

**Cause**: Incomplete write or filesystem error.

**Solution**:
```bash
# 1. Backup corrupted database
cp .gao-dev/documents.db .gao-dev/documents.db.corrupted

# 2. Try repair
sqlite3 .gao-dev/documents.db "PRAGMA integrity_check;"

# 3. If repair fails, restore from backup
cp .gao-dev/documents.db.backup .gao-dev/documents.db

# 4. Or re-migrate
rm .gao-dev/documents.db
gao-dev migrate
```

**Prevention**: Regular backups and use journaling mode:
```bash
sqlite3 .gao-dev/documents.db "PRAGMA journal_mode=WAL;"
```

---

### Issue: Database Schema Mismatch

**Symptom**:
```
[ERROR] no such table: stories
  Database schema incomplete
```

**Cause**: Migration incomplete or schema version mismatch.

**Solution**:
```bash
# 1. Check schema version
sqlite3 .gao-dev/documents.db "SELECT version FROM schema_version;"

# Expected: 5 (Migration 005)

# 2. If version < 5, re-run migration
rm .gao-dev/documents.db
gao-dev migrate

# 3. If version > 5, update GAO-Dev
pip install --upgrade gao-dev
```

---

## Context Loading Issues

### Issue: ContextLoaderError - Story Not Found

**Symptom**:
```python
ContextLoaderError: Story 1.99 not found
```

**Cause**: Story doesn't exist in database or file missing.

**Solution**:
```bash
# 1. Check database
gao-dev state show-story 1 99

# 2. Check file
ls docs/stories/epic-1/story-1.99.md

# 3. If database missing but file exists
gao-dev consistency-repair

# 4. If file missing, create story
gao-dev create-story --epic 1 --story 99 --title "Story Title"
```

---

### Issue: Cache Thrashing

**Symptom**: Cache hit rate <20%, frequent evictions.

**Diagnosis**:
```python
stats = loader.get_cache_stats()
print(f"Size: {stats['size']} / {stats['max_size']}")
print(f"Evictions: {stats['evictions']}")
```

**Cause**: Cache too small for access pattern.

**Solution**:
```python
# Increase cache size
loader = FastContextLoader(
    project_root=Path.cwd()),
    cache_size=200,  # Increase from 100
    cache_ttl_seconds=600  # Increase TTL
)
```

---

### Issue: Stale Context Data

**Symptom**: Context contains outdated information.

**Cause**: Cache entry not expired yet.

**Solution**:
```python
# Option 1: Clear cache
loader.clear_cache()

# Option 2: Reload specific context
context = await loader.load_story_context(1, 1, force_reload=True)

# Option 3: Reduce TTL
loader = FastContextLoader(
    project_root=Path.cwd()),
    cache_ttl_seconds=60  # Shorter TTL
)
```

---

## Debug Logging

### Enable Structured Logging

**Set environment variable**:
```bash
# Debug level (verbose)
export GAO_DEV_LOG_LEVEL=DEBUG

# Info level (default)
export GAO_DEV_LOG_LEVEL=INFO

# Error level (quiet)
export GAO_DEV_LOG_LEVEL=ERROR
```

**View logs**:
```bash
# JSON format (structured)
gao-dev create-story --epic 1 --story 99 --title "Test" 2>&1 | jq .

# Human-readable
gao-dev create-story --epic 1 --story 99 --title "Test"
```

### Filter Logs by Event

```bash
# Show only migration events
gao-dev migrate 2>&1 | jq 'select(.event | startswith("migration"))'

# Show only errors
gao-dev migrate 2>&1 | jq 'select(.level == "error")'

# Show timing information
gao-dev migrate 2>&1 | jq 'select(.duration_ms != null)'
```

### Enable Git Debug Logging

```bash
# Show all git commands
export GIT_TRACE=1
export GIT_TRACE_PERFORMANCE=1

gao-dev migrate
```

### Enable SQLite Debug Logging

```python
import sqlite3

# Enable trace callback
def trace_callback(statement):
    print(f"SQL: {statement}")

conn = sqlite3.connect(".gao-dev/documents.db")
conn.set_trace_callback(trace_callback)
```

---

## Getting Help

### Collect Diagnostic Information

```bash
# System information
gao-dev --version
python --version
git --version
sqlite3 --version

# Project structure
tree -L 3 docs/  # Linux/Mac
# Or: dir /s docs\  # Windows

# Database info
sqlite3 .gao-dev/documents.db ".schema"
sqlite3 .gao-dev/documents.db "SELECT COUNT(*) FROM epics;"
sqlite3 .gao-dev/documents.db "SELECT COUNT(*) FROM stories;"

# Git status
git status
git log --oneline -10

# Check consistency
gao-dev consistency-check --verbose
```

### Create Minimal Reproducible Example

```python
# minimal_repro.py
import asyncio
from pathlib import Path
from gao_dev.orchestrator import GAODevOrchestrator

async def main():
    # Describe issue here
    orchestrator = GAODevOrchestrator.create_default(Path.cwd())
    try:
        # Steps to reproduce issue
        pass
    finally:
        orchestrator.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Report Issue

Include:
1. GAO-Dev version (`gao-dev --version`)
2. Python version (`python --version`)
3. Operating system
4. Error message (full traceback)
5. Steps to reproduce
6. Diagnostic information (above)
7. Minimal reproducible example

**Where to report**:
- GitHub Issues: [gao-agile-dev/issues](https://github.com/your-org/gao-agile-dev/issues)
- Documentation: `docs/features/git-integrated-hybrid-wisdom/`

---

## Common Patterns

### Pattern: Check Before Operation

```python
# Check working tree clean
if not manager.is_working_tree_clean():
    print("Please commit or stash changes first")
    return

# Check story exists before transition
story = coordinator.get_story(epic_num, story_num)
if not story:
    print("Story does not exist")
    return

# Proceed with operation
manager.transition_story_state(epic_num, story_num, "in_progress")
```

### Pattern: Graceful Error Handling

```python
try:
    epic = manager.create_epic(...)
except WorkingTreeDirtyError:
    # Specific handling
    print("Commit changes first: git add -A && git commit")
except GitIntegratedStateManagerError as e:
    # State management error
    print(f"State error: {e}")
    # Maybe rollback or retry
except Exception as e:
    # Unexpected error
    logger.exception("Unexpected error")
    print(f"Unexpected: {e}")
```

### Pattern: Resource Cleanup

```python
# Always cleanup
orchestrator = GAODevOrchestrator.create_default(project_root)
try:
    # Use orchestrator
    pass
except Exception as e:
    logger.exception("Operation failed")
    raise
finally:
    # Always called
    orchestrator.close()
```

### Pattern: Performance Monitoring

```python
import time

def monitor_operation(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            print(f"{func.__name__}: {elapsed*1000:.2f}ms")
            return result
        except Exception as e:
            elapsed = time.time() - start
            print(f"{func.__name__} failed after {elapsed*1000:.2f}ms")
            raise
    return wrapper

@monitor_operation
def create_epic(...):
    return manager.create_epic(...)
```

---

## FAQ

**Q: Why is my operation slow?**
A: Check cache hit rate, database size, git repo size. See [Performance Issues](#performance-issues).

**Q: How do I reset everything?**
A: `rm -rf .gao-dev/documents.db && git reset --hard HEAD~N` (where N = number of migration commits).

**Q: Can I use SQLite Browser?**
A: Yes! Open `.gao-dev/documents.db` with [DB Browser for SQLite](https://sqlitebrowser.org/).

**Q: What if migration hangs?**
A: Check git operations (may be prompting for credentials). Use `export GIT_TERMINAL_PROMPT=0` to fail instead of prompt.

**Q: How do I backup database?**
A: `cp .gao-dev/documents.db .gao-dev/documents.db.backup`

**Q: Can I edit database directly?**
A: Not recommended. Use CLI commands or API. Direct edits may cause inconsistency.

---

**Troubleshooting Guide Version**: 1.0.0
**Last Updated**: 2025-11-09
**Epic**: 27 - Integration & Migration
**Story**: 27.6 - Documentation & Migration Guide
