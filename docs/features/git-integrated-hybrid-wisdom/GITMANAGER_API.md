# GitManager API Reference

**Version**: 2.0 (Epic 23 Enhanced)
**Module**: `gao_dev.core.git_manager`
**Status**: Production Ready

## Overview

GitManager provides comprehensive git operations for the GAO-Dev hybrid architecture. Enhanced in Epic 23 with 14 new methods supporting:

- **Transaction Support**: Atomic git operations with rollback capability
- **Branch Management**: Safe migration branches and feature workflows
- **File History Queries**: State inference from git history
- **Query Enhancements**: Detailed commit metadata and ranges

All methods include comprehensive error handling, structured logging, and full type hints.

## Table of Contents

1. [Transaction Support Methods](#transaction-support-methods) (5 methods)
2. [Branch Management Methods](#branch-management-methods) (4 methods)
3. [File History Query Methods](#file-history-query-methods) (4 methods)
4. [Query Enhancement Methods](#query-enhancement-methods) (2 methods)
5. [Usage Patterns](#usage-patterns)
6. [Error Handling](#error-handling)

---

## Transaction Support Methods

### `is_working_tree_clean() -> bool`

Check if working directory has uncommitted changes.

**Returns**: `True` if clean, `False` if dirty

**Use Case**: Pre-check before atomic operations

```python
git = GitManager(Path("/project"))
if not git.is_working_tree_clean():
    raise StateError("Uncommitted changes exist")
# Safe to proceed
```

---

### `add_all() -> bool`

Stage all changes (tracked and untracked files).

**Returns**: `True` if successful

**Equivalent**: `git add -A`

```python
git.add_all()  # Stage everything
git.commit("feat: new feature")
```

---

### `commit(message: str, allow_empty: bool = False) -> str`

Create a git commit with the given message.

**Parameters**:
- `message`: Commit message (conventional commits format recommended)
- `allow_empty`: Allow empty commits (default: False)

**Returns**: Short SHA (7 characters) of created commit

**Raises**: `subprocess.CalledProcessError` if commit fails

```python
sha = git.commit("feat: add authentication")
print(sha)  # "abc1234"
```

---

### `reset_hard(target: str = "HEAD") -> bool`

Perform hard reset to discard uncommitted changes (DESTRUCTIVE).

**Parameters**:
- `target`: Git ref to reset to (default: "HEAD")

**Returns**: `True` if successful

**WARNING**: Discards all uncommitted changes permanently

```python
try:
    # Atomic operation
    git.add_all()
    git.commit("feat: change")
except Exception:
    # Rollback on error
    git.reset_hard()
    raise
```

---

### `get_head_sha(short: bool = True) -> str`

Get current commit hash.

**Parameters**:
- `short`: Return short SHA (7 chars) if True, long SHA (40 chars) if False

**Returns**: Commit SHA (short or long form)

```python
sha = git.get_head_sha()  # "abc1234"
full_sha = git.get_head_sha(short=False)  # "abc123456..."
```

---

## Branch Management Methods

### `create_branch(name: str, checkout: bool = True) -> bool`

Create a new branch and optionally check it out.

**Parameters**:
- `name`: Branch name (e.g., "feature/epic-23", "migration/hybrid")
- `checkout`: Whether to checkout after creation (default: True)

**Returns**: `True` if successful

```python
git.create_branch("migration/hybrid-architecture")
# Now on migration/hybrid-architecture branch
```

---

### `checkout(branch: str) -> bool`

Switch to an existing branch.

**Parameters**:
- `branch`: Branch name to checkout

**Returns**: `True` if successful

**Note**: Creates tracking branch if exists on remote

```python
git.checkout("main")
git.checkout("feature-branch")  # Creates tracking branch if remote exists
```

---

### `delete_branch(name: str, force: bool = False) -> bool`

Delete a local branch.

**Parameters**:
- `name`: Branch name to delete
- `force`: Force deletion even if unmerged (default: False)

**Returns**: `True` if successful

```python
git.checkout("main")
git.delete_branch("migration/test")  # Safe: prevents unmerged
git.delete_branch("old-branch", force=True)  # Force delete
```

---

### `merge(branch: str, no_ff: bool = False, message: Optional[str] = None) -> bool`

Merge a branch into the current branch.

**Parameters**:
- `branch`: Branch name to merge
- `no_ff`: Use --no-ff flag to preserve history (default: False)
- `message`: Custom merge commit message (optional)

**Returns**: `True` if successful

```python
git.checkout("main")
git.merge("migration/hybrid", no_ff=True, message="Merge migration")
```

---

## File History Query Methods

### `get_last_commit_for_file(path: Path) -> Optional[Dict[str, Any]]`

Get detailed information about the last commit that modified a file.

**Parameters**:
- `path`: Path to file (relative to repo root or absolute)

**Returns**: Dict with keys: `sha`, `full_sha`, `message`, `author`, `date`
           Returns `None` if file not tracked or no commits

```python
info = git.get_last_commit_for_file(Path("docs/story.md"))
if info and "complete" in info["message"].lower():
    state = "done"
```

---

### `file_deleted_in_history(path: Path) -> bool`

Check if a file was deleted in git history.

**Parameters**:
- `path`: Path to file

**Returns**: `True` if file was deleted, `False` otherwise

```python
if git.file_deleted_in_history(Path("docs/old.md")):
    print("File was deleted")
```

---

### `is_file_tracked(path: Path) -> bool`

Check if a file is tracked by git (in the index).

**Parameters**:
- `path`: Path to file

**Returns**: `True` if tracked, `False` otherwise

```python
if git.is_file_tracked(Path("docs/new.md")):
    print("File is tracked")
```

---

### `get_file_status(path: Path) -> str`

Get the git status of a specific file.

**Parameters**:
- `path`: Path to file

**Returns**: One of: `"clean"`, `"modified"`, `"staged"`, `"untracked"`, `"deleted"`, `"unknown"`

```python
status = git.get_file_status(Path("docs/file.md"))
if status == "modified":
    print("File has uncommitted changes")
```

---

## Query Enhancement Methods

### `get_commit_info(sha: str = "HEAD") -> Dict[str, Any]`

Get comprehensive information about a specific commit.

**Parameters**:
- `sha`: Commit SHA or ref (default: "HEAD")

**Returns**: Dict with keys: `sha`, `full_sha`, `message`, `author`, `email`, `date`, `files_changed`

```python
commit = git.get_commit_info("HEAD")
print(f"{commit['sha']}: {commit['message']}")
print(f"Files changed: {len(commit['files_changed'])}")
```

---

### `get_commits_since(since: str, until: str = "HEAD", file_path: Optional[Path] = None) -> List[Dict[str, Any]]`

Get list of commits in a range, optionally filtered by file.

**Parameters**:
- `since`: Starting ref (exclusive)
- `until`: Ending ref (inclusive) (default: "HEAD")
- `file_path`: Optional file path to filter commits

**Returns**: List of commit dicts with keys: `sha`, `full_sha`, `message`, `author`, `email`, `date`

```python
# Get all commits since abc1234
commits = git.get_commits_since("abc1234", "HEAD")
for commit in commits:
    print(f"{commit['sha']}: {commit['message']}")

# Get commits affecting specific file
file_commits = git.get_commits_since(
    "start-sha",
    "HEAD",
    file_path=Path("docs/important.md")
)
```

---

## Usage Patterns

### Atomic Transaction Pattern

```python
from gao_dev.core.git_manager import GitManager
from pathlib import Path

git = GitManager(Path("/project"))

# Check clean state
if not git.is_working_tree_clean():
    raise StateError("Uncommitted changes exist")

# Begin operation
try:
    # Make file changes
    Path("/project/config.json").write_text(new_config)

    # Stage and commit atomically
    git.add_all()
    sha = git.commit("feat: update configuration")

    print(f"Successfully committed: {sha}")

except Exception:
    # Rollback on error
    git.reset_hard()
    raise
```

### Safe Migration Pattern

```python
# Create migration branch
git.create_branch("migration/hybrid-architecture")

try:
    # Phase 1: Database migration
    migrate_database()
    git.add_all()
    git.commit("migration: phase 1 - database schema")

    # Phase 2: Code migration
    migrate_code()
    git.add_all()
    git.commit("migration: phase 2 - code updates")

    # Phase 3: Documentation
    update_docs()
    git.add_all()
    git.commit("migration: phase 3 - documentation")

    # Merge back to main
    git.checkout("main")
    git.merge("migration/hybrid-architecture", no_ff=True,
              message="Complete hybrid architecture migration")

    # Cleanup migration branch
    git.delete_branch("migration/hybrid-architecture")

    print("Migration successful!")

except Exception as e:
    # Rollback: delete migration branch
    git.checkout("main")
    git.delete_branch("migration/hybrid-architecture", force=True)
    raise RuntimeError(f"Migration failed: {e}")
```

### State Inference from History

```python
from pathlib import Path

def infer_story_state(git: GitManager, story_path: Path) -> str:
    """Infer story state from git history."""

    # Check if file exists
    if not story_path.exists():
        if git.file_deleted_in_history(story_path):
            return "archived"
        return "not_created"

    # Check if tracked
    if not git.is_file_tracked(story_path):
        return "draft"

    # Get last commit
    commit_info = git.get_last_commit_for_file(story_path)
    if not commit_info:
        return "todo"

    # Infer from commit message
    message = commit_info["message"].lower()
    if "complete" in message or "done" in message:
        return "done"
    elif "progress" in message or "wip" in message:
        return "in_progress"

    return "todo"

# Usage
state = infer_story_state(git, Path("docs/stories/epic-5/story-5.3.md"))
print(f"Story state: {state}")
```

### Consistency Checking

```python
def check_file_database_consistency(
    git: GitManager,
    registry: DocumentRegistry,
    docs_dir: Path
) -> List[str]:
    """Check for inconsistencies between git and database."""
    issues = []

    # Check for unregistered tracked files
    for file in docs_dir.rglob("*.md"):
        if git.is_file_tracked(file):
            if not registry.get_by_path(file):
                issues.append(f"Unregistered tracked file: {file}")

    # Check for orphaned DB records
    for doc in registry.get_all_documents():
        status = git.get_file_status(doc.path)
        if status == "deleted":
            issues.append(f"Orphaned DB record: {doc.path}")

    return issues

# Usage
issues = check_file_database_consistency(git, registry, Path("docs"))
if issues:
    for issue in issues:
        print(f"WARNING: {issue}")
```

---

## Error Handling

All methods raise `subprocess.CalledProcessError` on git command failures. Always wrap in try/except:

```python
try:
    git.commit("feat: new feature")
except subprocess.CalledProcessError as e:
    logger.error(f"Commit failed: {e.stderr}")
    # Handle error (rollback, notify user, etc.)
```

**Common Errors**:

| Error | Cause | Solution |
|-------|-------|----------|
| `nothing to commit` | No staged changes | Call `add_all()` first or use `allow_empty=True` |
| `branch already exists` | Branch name conflict | Use different name or delete existing branch |
| `branch not found` | Invalid branch name | Check branch exists with `get_current_branch()` |
| `uncommitted changes` | Dirty working tree | Call `is_working_tree_clean()` first |
| `not a git repository` | No .git directory | Call `init_repo()` first |

---

## Performance Considerations

All operations complete in <100ms for typical repositories:

| Method | Typical Duration |
|--------|------------------|
| `is_working_tree_clean()` | <10ms |
| `add_all()` | <20ms |
| `commit()` | <50ms |
| `reset_hard()` | <30ms |
| `get_head_sha()` | <10ms |
| `create_branch()` | <15ms |
| `checkout()` | <20ms |
| `get_last_commit_for_file()` | 10-50ms |
| `get_commit_info()` | 20-50ms |
| `get_commits_since()` | 50-200ms |

**Optimization Tips**:
- Batch file operations before calling `add_all()`
- Cache `get_head_sha()` results if calling frequently
- Limit `get_commits_since()` ranges to <100 commits
- Use file path filtering in `get_commits_since()` for better performance

---

## Migration from GitCommitManager

If you were using the old `GitCommitManager`, migrate to `GitManager` as follows:

### Method Mapping

| Old (GitCommitManager) | New (GitManager) |
|------------------------|------------------|
| `commit_changes(message)` | `add_all()` + `commit(message)` |
| `create_atomic_commit(message)` | `add_all()` + `commit(message)` |
| `_has_staged_changes()` | `not is_working_tree_clean()` |

### Example Migration

**Before** (GitCommitManager):
```python
from gao_dev.sandbox.git_commit_manager import GitCommitManager

git_commit_mgr = GitCommitManager(sandbox_path, run_id)
git_commit_mgr.commit_changes("feat: complete story")
```

**After** (GitManager):
```python
from gao_dev.core.git_manager import GitManager

git = GitManager(project_path=sandbox_path)
git.add_all()
sha = git.commit("feat: complete story")
```

---

## Testing

Comprehensive test coverage:
- **Unit Tests**: 45 tests (Stories 23.1-23.4) - `tests/core/test_git_manager_enhanced.py`
- **Integration Tests**: 10 tests (Story 23.6) - `tests/integration/test_git_manager_integration.py`

Run tests:
```bash
# Unit tests only
pytest tests/core/test_git_manager_enhanced.py -v

# Integration tests only
pytest tests/integration/test_git_manager_integration.py -v

# All GitManager tests
pytest tests/core/test_git_manager_enhanced.py tests/integration/test_git_manager_integration.py -v
```

---

## See Also

- [Epic 23 Stories](./stories/epic-23/) - Implementation details for all enhancements
- [CLAUDE.md](../../../CLAUDE.md) - GAO-Dev project guide
- [Git Transaction Architecture](./ARCHITECTURE.md) - System design for hybrid architecture

---

**Last Updated**: 2025-11-09
**Epic**: 23 - GitManager Enhancement
**Stories**: 23.1-23.4, 23.6-23.7
