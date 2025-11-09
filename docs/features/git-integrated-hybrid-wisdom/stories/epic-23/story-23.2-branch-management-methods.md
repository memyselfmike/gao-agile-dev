# Story 23.2: Add Branch Management Methods

**Epic**: Epic 23 - GitManager Enhancement
**Story ID**: 23.2
**Priority**: P0
**Estimate**: 4 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Add enhanced branch management methods to GitManager to support safe migration branches and feature branch workflows. These methods are essential for Epic 25 (GitMigrationManager) which creates a migration branch for safe rollback.

The migration strategy requires creating a temporary `migration/hybrid-architecture` branch, performing migration commits, and then either merging to main (success) or deleting the branch (rollback). Without proper branch management, safe migration is impossible.

This story implements 3 core methods: `create_branch()` for creating migration/feature branches, `checkout()` for switching branches, and `delete_branch()` for cleanup. It also enhances the existing `merge()` method to support no-fast-forward merges with custom messages.

---

## Acceptance Criteria

- [ ] `create_branch(name, checkout=True)` creates new branch and optionally checks it out
- [ ] `checkout(branch)` switches to existing branch (local or remote)
- [ ] `delete_branch(name, force=False)` deletes branch with optional force flag
- [ ] Enhanced `merge()` supports `--no-ff` flag and custom commit messages
- [ ] All methods handle both local and remote branches appropriately
- [ ] Error handling for branch already exists, branch not found, etc.
- [ ] Comprehensive docstrings with usage examples
- [ ] Structured logging for all branch operations
- [ ] 10 unit tests covering all scenarios
- [ ] Type hints for all parameters and return values

---

## Technical Approach

### Implementation Details

Add three new branch management methods and enhance the existing merge method. These methods provide safe branch operations with proper error handling.

**Key Methods**:
1. **create_branch()**: Creates branch from current HEAD, optionally checks out
2. **checkout()**: Switches to branch (creates tracking branch for remotes)
3. **delete_branch()**: Deletes local branch (with force option for unmerged)
4. **merge() [enhanced]**: Adds no_ff and message parameters

**Design Pattern**: Extension of existing GitManager service

### Files to Modify

- `gao_dev/core/git_manager.py` (+~50 LOC / -0 LOC)
  - Add: `create_branch(name: str, checkout: bool = True) -> bool` method (~15 LOC)
  - Add: `checkout(branch: str) -> bool` method (~12 LOC)
  - Add: `delete_branch(name: str, force: bool = False) -> bool` method (~12 LOC)
  - Modify: `merge()` method to add no_ff and message parameters (+~10 LOC)

### New Files to Create

- `tests/core/test_git_manager_enhanced.py` (+~100 LOC appended)
  - Purpose: Unit tests for branch management methods
  - Key components:
    - 10 unit tests for branch operations
    - Mock git subprocess calls
    - Test branch creation, switching, deletion scenarios

---

## Testing Strategy

### Unit Tests (10 tests)

- test_create_branch_success() - Tests new branch creation
- test_create_branch_and_checkout() - Tests branch creation with immediate checkout
- test_create_branch_already_exists() - Tests error when branch exists
- test_checkout_existing_branch() - Tests switching to existing branch
- test_checkout_creates_tracking_branch() - Tests checkout of remote branch
- test_checkout_branch_not_found() - Tests error when branch doesn't exist
- test_delete_branch_success() - Tests branch deletion
- test_delete_branch_with_force() - Tests forced deletion of unmerged branch
- test_delete_branch_not_found() - Tests error when branch doesn't exist
- test_merge_no_fast_forward() - Tests merge with --no-ff flag

**Total Tests**: 10 tests
**Test File**: `tests/core/test_git_manager_enhanced.py` (appended)

---

## Dependencies

**Upstream**: Story 23.1 (transaction support provides foundation)

**Downstream**:
- Story 25.4 (GitMigrationManager uses create_branch, checkout, delete_branch)
- Story 25.5 (migration rollback uses delete_branch)

---

## Implementation Notes

### Branch Naming Conventions

**Migration branches**: `migration/<feature-name>`
- Example: `migration/hybrid-architecture`
- Created by GitMigrationManager
- Deleted after successful merge or on rollback

**Feature branches**: `feature/<epic-name>`
- Example: `feature/epic-23-gitmanager-enhancement`
- Created by CLI commands
- Merged with --no-ff to preserve history

### Git Command Details

```python
# create_branch() implementation
subprocess.run(
    ["git", "branch", name],
    cwd=self.repo_path,
    check=True
)
if checkout:
    subprocess.run(
        ["git", "checkout", name],
        cwd=self.repo_path,
        check=True
    )

# checkout() implementation
# Try local first, then remote tracking
try:
    subprocess.run(
        ["git", "checkout", branch],
        cwd=self.repo_path,
        check=True
    )
except subprocess.CalledProcessError:
    # Try as remote tracking branch
    subprocess.run(
        ["git", "checkout", "-b", branch, f"origin/{branch}"],
        cwd=self.repo_path,
        check=True
    )

# delete_branch() implementation
force_flag = "-D" if force else "-d"
subprocess.run(
    ["git", "branch", force_flag, name],
    cwd=self.repo_path,
    check=True
)

# Enhanced merge() implementation
def merge(self, branch: str, no_ff: bool = False, message: Optional[str] = None) -> bool:
    cmd = ["git", "merge"]
    if no_ff:
        cmd.append("--no-ff")
    if message:
        cmd.extend(["-m", message])
    cmd.append(branch)
    subprocess.run(cmd, cwd=self.repo_path, check=True)
    return True
```

### Safety Considerations

**delete_branch() safety**:
- Default `-d` flag prevents deletion of unmerged branches
- Use `force=True` only when intentional (migration rollback)
- Log warning when force=True

**checkout() behavior**:
- Fails if working tree is dirty (safety check)
- Can create tracking branches for remotes
- Updates working directory (inform user)

**Branch existence checks**:
- create_branch() fails if branch exists
- checkout() fails if branch doesn't exist
- delete_branch() fails if branch doesn't exist (unless force)

### Error Handling

All methods must handle:
- Branch already exists: Raise GitError("Branch 'X' already exists")
- Branch not found: Raise GitError("Branch 'X' not found")
- Dirty working tree: Raise GitError("Working tree has uncommitted changes")
- Git command failures: Log error, raise GitError

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (10/10)
- [ ] Code coverage >80% for new methods
- [ ] Code review completed
- [ ] Documentation updated (comprehensive docstrings)
- [ ] No breaking changes (existing merge() calls still work)
- [ ] Git commit created with message: "feat(epic-23): add branch management methods to GitManager"
- [ ] MyPy strict mode passes
- [ ] No linting errors (Ruff)

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09
