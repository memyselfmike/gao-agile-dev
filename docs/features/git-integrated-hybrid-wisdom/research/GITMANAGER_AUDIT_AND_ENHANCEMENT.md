# GitManager Audit & Enhancement Plan
## Existing Implementation Review and Hybrid Architecture Requirements

**Date**: 2025-11-09
**Purpose**: Audit existing GitManager, identify gaps for hybrid architecture, create enhancement plan
**Status**: Analysis Complete

---

## Executive Summary

**Current State**: GitManager exists and is functional, but **incomplete** for git-integrated hybrid architecture needs.

**Assessment**:
- ✅ **Keep**: Core GitManager (~70% of what we need)
- ⚠️ **Enhance**: Add ~10 missing methods for transaction support
- ❌ **Deprecate**: GitCommitManager (redundant, replaced by enhanced GitManager)
- ✅ **Keep**: GitCloner (separate concern, still needed)

**Effort**: 2-3 days to enhance GitManager with required methods

---

## Current Implementation Analysis

### 1. Core GitManager (`gao_dev/core/git_manager.py`)

**Location**: `gao_dev/core/git_manager.py`
**LOC**: 616 lines
**Status**: ✅ **Active and Used**

**Current Features**:

| Feature | Method | Status | Notes |
|---------|--------|--------|-------|
| **Initialization** | `__init__(project_path, config_loader)` | ✅ Good | Supports both GAO-Dev repo and sandbox mode |
| **Init Repo** | `init_repo()` | ✅ Good | Creates repo, configures user, initial commit |
| **Create Commit** | `create_commit()` | ✅ Good | Enhanced metadata tracking, footer support |
| **Get Status** | `get_status()` | ✅ Good | Comprehensive status with staged/unstaged/untracked |
| **Basic Git Ops** | `git_init()`, `git_add()`, `git_commit()` | ✅ Good | Low-level operations |
| **Branching** | `git_branch()`, `git_merge()` | ✅ Good | Create/switch branches, merge |
| **Is Repo** | `is_git_repo()` | ✅ Good | Check if directory is git repo |
| **Current Branch** | `get_current_branch()` | ✅ Good | Get active branch name |
| **Conventional Commits** | `create_conventional_commit()` | ✅ Good | Structured commit messages |

**Current Usage**:
```python
# CLI commands (gao_dev/cli/commands.py)
git_manager = GitManager(ConfigLoader(project_root))
if git_manager.git_init():
    ...

# Sandbox runner (gao_dev/sandbox/benchmark/runner.py)
git_manager = GitManager(project_path)
init_result = git_manager.init_repo(...)
status = git_manager.get_status()
```

**Strengths**:
- ✅ Well-structured, clean code
- ✅ Good logging (structlog integration)
- ✅ Supports both GAO-Dev repo and sandbox projects
- ✅ Comprehensive status checking
- ✅ Conventional commits support

**Weaknesses for Hybrid Architecture**:
- ❌ No `is_working_tree_clean()` method (must parse get_status)
- ❌ No `reset_hard()` for rollback
- ❌ No `get_head_sha()` for commit tracking
- ❌ No `delete_branch()` for cleanup
- ❌ No file history methods (get_last_commit_for_file, etc.)
- ❌ No transaction boundary methods

---

### 2. GitCommitManager (`gao_dev/sandbox/git_commit_manager.py`)

**Location**: `gao_dev/sandbox/git_commit_manager.py`
**LOC**: 259 lines
**Status**: ⚠️ **DEPRECATED - Should be removed**

**Purpose**: Creates atomic commits for benchmark artifacts

**Current Features**:
- `commit_artifacts()` - Stage and commit files for a phase
- `_format_commit_message()` - Format conventional commits
- `_phase_to_scope()` - Map phases to commit scopes

**Problems**:
1. **Duplicates GitManager functionality** - Reimplements commit creation
2. **Bypasses GitManager** - Uses direct subprocess calls instead of GitManager
3. **Limited scope** - Only used by benchmark system
4. **Missing methods** - Has `stage_file()` call but GitManager doesn't have it!

**Example Code**:
```python
class GitCommitManager:
    def __init__(self, project_root: Path, run_id: str):
        self.git_manager = GitManager(project_path=self.project_root)

    def commit_artifacts(self, phase, artifact_paths, agent_name):
        # Problem: Calls self.git_manager.stage_file() which doesn't exist!
        for path in artifact_paths:
            self.git_manager.stage_file(file_path)  # ← METHOD DOESN'T EXIST

        # Problem: Bypasses GitManager for commit
        subprocess.run(["git", "commit", "-m", message, "--author", author])
```

**Verdict**: 🔴 **REMOVE** - Functionality should be in GitManager

---

### 3. GitCloner (`gao_dev/sandbox/git_cloner.py`)

**Location**: `gao_dev/sandbox/git_cloner.py`
**LOC**: 363 lines
**Status**: ✅ **Keep - Different Concern**

**Purpose**: Clone external repositories for boilerplate integration

**Current Features**:
- `clone_repository()` - Clone with retries, validation
- `validate_git_url()` - URL format validation (HTTPS, SSH)
- `get_default_branch()` - Detect default branch
- Retry logic with exponential backoff
- Cleanup on failure

**Verdict**: ✅ **KEEP** - Separate concern from state management, well-implemented

---

## Gap Analysis: What's Missing for Hybrid Architecture

### Required Methods for Git-Integrated Hybrid Architecture

From `GIT_INTEGRATED_HYBRID_ARCHITECTURE.md`, we need:

| Method | Purpose | Exists? | Notes |
|--------|---------|---------|-------|
| **Transaction Support** |
| `is_working_tree_clean()` | Check no uncommitted changes | ⚠️ Partial | Must parse `get_status()` |
| `add_all()` | Stage all changes | ✅ Yes | Part of `create_commit()` |
| `commit()` | Create commit | ✅ Yes | `create_commit()` |
| `reset_hard()` | Rollback file changes | ❌ **MISSING** | Critical for rollback |
| `get_head_sha()` | Get current commit hash | ⚠️ Partial | Embedded in `create_commit()` |
| **Branch Management** |
| `create_branch()` | Create new branch | ✅ Yes | `git_branch(create=True)` |
| `checkout()` | Switch branch | ✅ Yes | `git_branch(create=False)` |
| `delete_branch()` | Delete branch | ❌ **MISSING** | Needed for migration cleanup |
| `merge()` | Merge branch | ✅ Yes | `git_merge()` |
| **File History** |
| `get_uncommitted_files()` | List uncommitted files | ✅ Yes | `get_status()` returns them |
| `get_last_commit_for_file()` | Last commit touching file | ❌ **MISSING** | For state inference |
| `file_deleted_in_history()` | Check if file deleted | ❌ **MISSING** | For consistency checking |
| `is_file_tracked()` | Check if git tracks file | ❌ **MISSING** | For consistency checking |
| **Query Operations** |
| `get_commit_info()` | Get commit metadata | ⚠️ Partial | Need enhancement |
| `get_file_status()` | Get specific file status | ❌ **MISSING** | For selective operations |

**Summary**:
- ✅ **Have**: 60% of required functionality
- ⚠️ **Partial**: 20% (exists but needs enhancement)
- ❌ **Missing**: 20% (must implement)

---

## Enhancement Plan

### Phase 1: Add Transaction Support Methods (Priority: CRITICAL)

```python
class GitManager:
    """Enhanced with transaction support."""

    def is_working_tree_clean(self) -> bool:
        """
        Check if working tree has uncommitted changes.

        Returns:
            True if clean (no staged, unstaged, or untracked files)
        """
        status = self.get_status()
        return status["clean"]

    def add_all(self) -> bool:
        """
        Stage all changes (git add -A).

        Returns:
            True if successful
        """
        try:
            self._run_git_command(["add", "-A"])
            return True
        except subprocess.CalledProcessError:
            return False

    def commit(
        self,
        message: str,
        allow_empty: bool = False,
        author: Optional[str] = None
    ) -> str:
        """
        Create commit and return SHA.

        Args:
            message: Commit message
            allow_empty: Allow empty commits
            author: Optional author override

        Returns:
            Commit SHA (short hash)

        Raises:
            subprocess.CalledProcessError: If commit fails
        """
        cmd = ["commit", "-m", message]
        if allow_empty:
            cmd.append("--allow-empty")
        if author:
            cmd.extend(["--author", author])

        self._run_git_command(cmd)
        return self.get_head_sha()

    def reset_hard(self, target: str = "HEAD") -> bool:
        """
        Hard reset to target commit (DESTRUCTIVE - loses uncommitted changes).

        Args:
            target: Commit to reset to (default: HEAD)

        Returns:
            True if successful

        Warning:
            This discards all uncommitted changes!
        """
        try:
            self._run_git_command(["reset", "--hard", target])
            self._log("warning", "reset_hard_executed", target=target)
            return True
        except subprocess.CalledProcessError:
            return False

    def get_head_sha(self, short: bool = True) -> str:
        """
        Get current HEAD commit SHA.

        Args:
            short: Return short hash (7 chars) or full hash

        Returns:
            Commit SHA

        Raises:
            subprocess.CalledProcessError: If no commits exist
        """
        cmd = ["rev-parse"]
        if short:
            cmd.append("--short")
        cmd.append("HEAD")

        result = self._run_git_command(cmd)
        return result.strip()
```

---

### Phase 2: Add Branch Management Methods (Priority: HIGH)

```python
class GitManager:
    """Enhanced with complete branch management."""

    def create_branch(self, branch_name: str, checkout: bool = True) -> bool:
        """
        Create new branch.

        Args:
            branch_name: Branch name
            checkout: If True, checkout new branch immediately

        Returns:
            True if successful
        """
        try:
            if checkout:
                self._run_git_command(["checkout", "-b", branch_name])
            else:
                self._run_git_command(["branch", branch_name])
            return True
        except subprocess.CalledProcessError:
            return False

    def checkout(self, branch_name: str) -> bool:
        """
        Checkout existing branch.

        Args:
            branch_name: Branch to checkout

        Returns:
            True if successful
        """
        try:
            self._run_git_command(["checkout", branch_name])
            return True
        except subprocess.CalledProcessError:
            return False

    def delete_branch(self, branch_name: str, force: bool = False) -> bool:
        """
        Delete branch.

        Args:
            branch_name: Branch to delete
            force: Force delete even if not merged

        Returns:
            True if successful
        """
        try:
            flag = "-D" if force else "-d"
            self._run_git_command(["branch", flag, branch_name])
            return True
        except subprocess.CalledProcessError:
            return False

    def merge(
        self,
        branch_name: str,
        no_ff: bool = False,
        message: Optional[str] = None
    ) -> bool:
        """
        Merge branch into current branch.

        Args:
            branch_name: Branch to merge
            no_ff: Force merge commit (no fast-forward)
            message: Optional merge commit message

        Returns:
            True if successful
        """
        try:
            cmd = ["merge"]
            if no_ff:
                cmd.append("--no-ff")
            if message:
                cmd.extend(["-m", message])
            cmd.append(branch_name)

            self._run_git_command(cmd)
            return True
        except subprocess.CalledProcessError:
            return False
```

---

### Phase 3: Add File History Methods (Priority: HIGH)

```python
class GitManager:
    """Enhanced with file history queries."""

    def get_last_commit_for_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Get last commit that modified a file.

        Args:
            file_path: Path to file (relative to project root)

        Returns:
            Dict with commit info:
                - sha: str (short hash)
                - message: str
                - author: str
                - timestamp: datetime
            Or None if file never committed

        Raises:
            subprocess.CalledProcessError: If git operation fails
        """
        try:
            # Get commit SHA
            sha_output = self._run_git_command([
                "log", "-1", "--format=%h", "--", str(file_path)
            ])
            sha = sha_output.strip()

            if not sha:
                return None

            # Get commit details
            details_output = self._run_git_command([
                "log", "-1", "--format=%h|%s|%an|%ai", sha
            ])
            parts = details_output.strip().split("|")

            return {
                "sha": parts[0],
                "message": parts[1],
                "author": parts[2],
                "timestamp": datetime.fromisoformat(parts[3]),
            }

        except subprocess.CalledProcessError:
            return None

    def file_deleted_in_history(self, file_path: Path) -> bool:
        """
        Check if file was deleted in git history.

        Args:
            file_path: Path to check

        Returns:
            True if file was deleted
        """
        try:
            # Check if file is in git history
            self._run_git_command(["log", "--", str(file_path)])

            # File is in history, check if it's deleted now
            try:
                self._run_git_command(["ls-files", "--error-unmatch", str(file_path)])
                return False  # File exists in index
            except subprocess.CalledProcessError:
                return True  # File not in index (deleted)

        except subprocess.CalledProcessError:
            # File never existed in history
            return False

    def is_file_tracked(self, file_path: Path) -> bool:
        """
        Check if file is tracked by git.

        Args:
            file_path: Path to check

        Returns:
            True if file is tracked
        """
        try:
            self._run_git_command(["ls-files", "--error-unmatch", str(file_path)])
            return True
        except subprocess.CalledProcessError:
            return False

    def get_file_status(self, file_path: Path) -> str:
        """
        Get status of specific file.

        Args:
            file_path: Path to check

        Returns:
            Status string:
                - "untracked" - Not tracked by git
                - "modified" - Modified but not staged
                - "staged" - Staged for commit
                - "clean" - No changes
                - "deleted" - Deleted

        Raises:
            subprocess.CalledProcessError: If git operation fails
        """
        try:
            # Check if tracked
            if not self.is_file_tracked(file_path):
                if file_path.exists():
                    return "untracked"
                else:
                    return "deleted"

            # Get status
            output = self._run_git_command(["status", "--porcelain", str(file_path)])

            if not output.strip():
                return "clean"

            # Parse status code (first two characters)
            status_code = output[:2]

            if status_code[0] in "MAD":  # Modified/Added/Deleted in index
                return "staged"
            elif status_code[1] in "MD":  # Modified/Deleted in working tree
                return "modified"
            else:
                return "clean"

        except subprocess.CalledProcessError:
            return "unknown"
```

---

### Phase 4: Add Query Enhancement Methods (Priority: MEDIUM)

```python
class GitManager:
    """Enhanced with additional query methods."""

    def get_commit_info(self, commit_sha: str = "HEAD") -> Dict[str, Any]:
        """
        Get detailed commit information.

        Args:
            commit_sha: Commit to query (default: HEAD)

        Returns:
            Dict with commit info:
                - sha: str (full hash)
                - short_sha: str (short hash)
                - message: str (full message)
                - subject: str (first line)
                - body: str (message body)
                - author: str
                - author_email: str
                - timestamp: datetime
                - files_changed: List[str]

        Raises:
            subprocess.CalledProcessError: If commit doesn't exist
        """
        # Get commit details in one call
        output = self._run_git_command([
            "log", "-1",
            "--format=%H|%h|%s|%b|%an|%ae|%ai",
            commit_sha
        ])

        parts = output.strip().split("|")

        # Get files changed
        files_output = self._run_git_command([
            "diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha
        ])
        files_changed = [f.strip() for f in files_output.splitlines() if f.strip()]

        return {
            "sha": parts[0],
            "short_sha": parts[1],
            "subject": parts[2],
            "body": parts[3],
            "message": f"{parts[2]}\n\n{parts[3]}" if parts[3] else parts[2],
            "author": parts[4],
            "author_email": parts[5],
            "timestamp": datetime.fromisoformat(parts[6]),
            "files_changed": files_changed,
        }

    def get_commits_since(
        self,
        since: str,
        until: str = "HEAD",
        file_path: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of commits in range.

        Args:
            since: Starting commit/tag/branch
            until: Ending commit/tag/branch (default: HEAD)
            file_path: Optional - only commits touching this file

        Returns:
            List of commit info dicts

        Raises:
            subprocess.CalledProcessError: If range invalid
        """
        cmd = ["log", f"{since}..{until}", "--format=%H|%s|%an|%ai"]

        if file_path:
            cmd.extend(["--", str(file_path)])

        output = self._run_git_command(cmd)

        commits = []
        for line in output.splitlines():
            if not line.strip():
                continue

            parts = line.split("|")
            commits.append({
                "sha": parts[0],
                "subject": parts[1],
                "author": parts[2],
                "timestamp": datetime.fromisoformat(parts[3]),
            })

        return commits
```

---

## Deprecation Plan

### GitCommitManager - REMOVE

**Reason**: Duplicates GitManager functionality, incorrectly implemented

**Migration Strategy**:

```python
# OLD (GitCommitManager):
from gao_dev.sandbox.git_commit_manager import GitCommitManager

commit_manager = GitCommitManager(project_root, run_id)
commit_manager.commit_artifacts(
    phase="Product Requirements",
    artifact_paths=["docs/PRD.md"],
    agent_name="John"
)

# NEW (Enhanced GitManager):
from gao_dev.core.git_manager import GitManager

git_manager = GitManager(project_path=project_root)

# Stage files
for path in artifact_paths:
    git_manager.git_add([path])

# Create conventional commit
git_manager.create_conventional_commit(
    commit_type="feat",
    scope="prd",
    description="Create Product Requirements Document",
    body=f"Benchmark Run: {run_id}\n"
         f"Phase: {phase}\n"
         f"Agent: {agent_name}\n"
         f"Artifacts: {len(artifact_paths)} file(s)"
)
```

**Files to Update**:
1. `gao_dev/sandbox/benchmark/runner.py` - Replace GitCommitManager with GitManager
2. `gao_dev/sandbox/git_commit_manager.py` - DELETE FILE
3. `tests/sandbox/test_git_manager.py` - Remove GitCommitManager tests

**Timeline**: 1 day

---

## Implementation Timeline

### Week 1 (4 days)

**Day 1: Phase 1 - Transaction Support**
- Add `is_working_tree_clean()`
- Add `add_all()`
- Add `commit()` (simplified interface)
- Add `reset_hard()`
- Add `get_head_sha()`
- Unit tests for transaction methods

**Day 2: Phase 2 - Branch Management**
- Add `create_branch()`
- Add `checkout()`
- Add `delete_branch()`
- Enhance `merge()` with no-ff support
- Unit tests for branch methods

**Day 3: Phase 3 - File History**
- Add `get_last_commit_for_file()`
- Add `file_deleted_in_history()`
- Add `is_file_tracked()`
- Add `get_file_status()`
- Unit tests for file history methods

**Day 4: Phase 4 - Query Enhancements & Deprecation**
- Add `get_commit_info()`
- Add `get_commits_since()`
- Deprecate GitCommitManager
- Update sandbox runner to use GitManager
- Integration tests

---

## Final GitManager API

### Core Operations
```python
# Initialization
git = GitManager(project_path=Path("project"))

# Repository setup
git.init_repo(user_name="GAO-Dev", initial_commit=True)

# Transaction support
clean = git.is_working_tree_clean()  # ← NEW
git.add_all()  # ← NEW
sha = git.commit("message")  # ← NEW
git.reset_hard()  # ← NEW (rollback)

# Branch management
git.create_branch("feature/new")  # ← NEW
git.checkout("main")  # ← ENHANCED
git.delete_branch("feature/old", force=True)  # ← NEW
git.merge("feature/new", no_ff=True)  # ← ENHANCED

# File history
commit = git.get_last_commit_for_file(Path("story.md"))  # ← NEW
deleted = git.file_deleted_in_history(Path("old.md"))  # ← NEW
tracked = git.is_file_tracked(Path("new.md"))  # ← NEW
status = git.get_file_status(Path("file.md"))  # ← NEW

# Query operations
sha = git.get_head_sha()  # ← NEW
info = git.get_commit_info("abc123")  # ← NEW
commits = git.get_commits_since("v1.0", "HEAD")  # ← NEW
status = git.get_status()  # ← EXISTING (enhanced)

# Conventional commits
git.create_conventional_commit(
    commit_type="feat",
    scope="story-5.3",
    description="create story",
    body="Full story implementation"
)
```

---

## Testing Strategy

### Unit Tests (New)
```python
# tests/core/test_git_manager_enhanced.py

def test_is_working_tree_clean_true():
    """Test clean working tree detection."""
    git = GitManager(tmp_path)
    git.init_repo()
    assert git.is_working_tree_clean() is True

def test_is_working_tree_clean_false():
    """Test dirty working tree detection."""
    git = GitManager(tmp_path)
    git.init_repo()

    # Create uncommitted file
    (tmp_path / "file.txt").write_text("content")

    assert git.is_working_tree_clean() is False

def test_reset_hard_rollback():
    """Test reset hard rolls back changes."""
    git = GitManager(tmp_path)
    git.init_repo()

    # Make change
    (tmp_path / "file.txt").write_text("content")

    # Rollback
    git.reset_hard()

    # File should be gone
    assert not (tmp_path / "file.txt").exists()

def test_delete_branch():
    """Test branch deletion."""
    git = GitManager(tmp_path)
    git.init_repo()

    git.create_branch("feature/test")
    git.checkout("main")
    assert git.delete_branch("feature/test") is True

def test_get_last_commit_for_file():
    """Test file history retrieval."""
    git = GitManager(tmp_path)
    git.init_repo()

    file_path = tmp_path / "test.txt"
    file_path.write_text("v1")
    git.add_all()
    git.commit("Initial")

    file_path.write_text("v2")
    git.add_all()
    git.commit("Update")

    commit = git.get_last_commit_for_file(Path("test.txt"))
    assert commit is not None
    assert commit["message"] == "Update"
```

### Integration Tests
```python
# tests/integration/test_git_integrated_state_manager.py

def test_atomic_story_creation_with_git(tmp_path):
    """Test story creation uses git as transaction boundary."""
    git = GitManager(tmp_path)
    state_mgr = GitIntegratedStateManager(git, registry)

    # Create story (should commit)
    story = state_mgr.create_story(
        epic_num=5,
        story_num=3,
        content="Story content",
        metadata={"title": "Test Story"}
    )

    # Verify git committed
    assert git.is_working_tree_clean() is True
    commit = git.get_commit_info()
    assert "story-5.3" in commit["message"]

def test_atomic_rollback_on_error(tmp_path):
    """Test rollback on error."""
    git = GitManager(tmp_path)
    state_mgr = GitIntegratedStateManager(git, registry)

    # Force error
    with pytest.raises(StateError):
        state_mgr.create_story(
            epic_num=5,
            story_num=3,
            content="Bad content",
            metadata={"invalid": True}  # Triggers error
        )

    # Verify rollback
    assert git.is_working_tree_clean() is True
    assert not (tmp_path / "docs/stories/epic-5/story-5.3.md").exists()
```

---

## Backward Compatibility

### No Breaking Changes

All new methods are **additions** - no existing methods are removed or changed signatures.

### Existing Code Continues to Work

```python
# All existing code continues to work unchanged
git = GitManager(project_path)
git.init_repo()
git.create_commit("message", add_all=True)
status = git.get_status()
```

### Gradual Migration

Projects using GitCommitManager have a clear migration path:
1. Continue using GitCommitManager (deprecated but functional)
2. Migrate to enhanced GitManager at convenience
3. Remove GitCommitManager in future release (3-6 months)

---

## Conclusion

**Recommendation**: ✅ **PROCEED WITH GITMANAGER ENHANCEMENT**

**Summary**:
- ✅ Core GitManager is solid foundation (~70% complete)
- ✅ Add ~10 new methods for transaction support (2-3 days)
- ❌ Deprecate GitCommitManager (duplicate functionality)
- ✅ Keep GitCloner (separate concern)
- ✅ No breaking changes
- ✅ Clean, well-tested enhancement

**Timeline**: 4 days total
- Day 1: Transaction support
- Day 2: Branch management
- Day 3: File history
- Day 4: Query enhancements & deprecation

**Risk**: 🟢 **LOW** - Non-breaking additions to existing solid codebase

---

**Document Version**: 1.0
**Date**: 2025-11-09
**Status**: Complete - Ready for Implementation
