"""Git operations manager for GAO-Dev.

Unified git management supporting both:
- GAO-Dev's own repository operations
- Agent/sandbox project git operations
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    import structlog
    logger = structlog.get_logger(__name__)
    HAS_STRUCTLOG = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    HAS_STRUCTLOG = False


class GitManager:
    """
    Unified git operations manager.

    Supports two initialization modes:
    1. With ConfigLoader (for GAO-Dev's own repo)
    2. With direct path (for agent/sandbox projects)
    """

    DEFAULT_USER_NAME = "GAO-Dev"
    DEFAULT_USER_EMAIL = "dev@gao-dev.local"

    def __init__(
        self,
        project_path: Optional[Path] = None,
        config_loader: Optional[Any] = None
    ):
        """
        Initialize git manager.

        Args:
            project_path: Direct path to project (for sandbox/agent use)
            config_loader: ConfigLoader instance (for GAO-Dev's own repo)

        Note: Provide either project_path OR config_loader, not both
        """
        if project_path and config_loader:
            raise ValueError("Provide either project_path OR config_loader, not both")

        if config_loader:
            # GAO-Dev's own repo mode
            self.config_loader = config_loader
            self.project_path = config_loader.project_root
        elif project_path:
            # Agent/sandbox mode
            self.config_loader = None
            self.project_path = Path(project_path).resolve()
        else:
            raise ValueError("Must provide either project_path or config_loader")

        # Set up logging
        if HAS_STRUCTLOG:
            self.logger = logger.bind(component="GitManager", project=str(self.project_path))
        else:
            self.logger = logger

    # ============================================================================
    # HIGH-LEVEL OPERATIONS (Enhanced from sandbox version)
    # ============================================================================

    def init_repo(
        self,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        initial_commit: bool = True,
        create_gitignore: bool = True,
    ) -> Dict[str, Any]:
        """
        Initialize git repository with full setup.

        Creates repository, configures user, optionally creates .gitignore
        and initial commit.

        Args:
            user_name: Git user name (defaults to DEFAULT_USER_NAME)
            user_email: Git user email (defaults to DEFAULT_USER_EMAIL)
            initial_commit: Whether to create initial commit
            create_gitignore: Whether to create .gitignore file

        Returns:
            Dictionary with initialization results:
                - initialized: bool
                - commit_hash: Optional[str] (if initial_commit=True)
                - timestamp: datetime
                - user_name: str
                - user_email: str

        Raises:
            subprocess.CalledProcessError: If git operations fail
        """
        self._log("info", "initializing_git_repository")

        try:
            # Initialize repository
            self.git_init()

            # Configure user
            name = user_name or self.DEFAULT_USER_NAME
            email = user_email or self.DEFAULT_USER_EMAIL
            self._run_git_command(["config", "user.name", name])
            self._run_git_command(["config", "user.email", email])

            # Create .gitignore if requested
            if create_gitignore:
                self._create_gitignore()

            result = {
                "initialized": True,
                "timestamp": datetime.now(),
                "user_name": name,
                "user_email": email,
            }

            # Create initial commit if requested
            if initial_commit:
                commit_result = self.create_commit(
                    message="chore: initialize project repository\n\nInitial project structure created by GAO-Dev.",
                    allow_empty=True,
                )
                result["commit_hash"] = commit_result["hash"]
                result["commit_message"] = commit_result["message"]

            self._log("info", "git_repository_initialized",
                     user_name=name, initial_commit=initial_commit)

            return result

        except subprocess.CalledProcessError as e:
            error_msg = f"Git initialization failed: {e.stderr}"
            self._log("error", "git_init_failed", error=error_msg)
            raise

    def create_commit(
        self,
        message: str,
        add_all: bool = True,
        allow_empty: bool = False,
        add_footer: bool = None,
    ) -> Dict[str, Any]:
        """
        Create a git commit with enhanced metadata tracking.

        Args:
            message: Commit message
            add_all: Whether to stage all changes (git add -A)
            allow_empty: Whether to allow empty commits
            add_footer: Whether to add GAO-Dev footer (None = auto from config)

        Returns:
            Dictionary with commit information:
                - hash: str (short hash)
                - message: str
                - timestamp: datetime
                - files_changed: List[str]

        Raises:
            subprocess.CalledProcessError: If commit fails
        """
        self._log("info", "creating_commit", commit_msg=message[:50])

        try:
            # Stage changes if requested
            if add_all:
                self._run_git_command(["add", "-A"])

            # Add footer if configured (for GAO-Dev's own repo)
            final_message = message
            if add_footer is None and self.config_loader:
                if self.config_loader.is_git_auto_commit_enabled():
                    footer = self.config_loader.get_git_commit_footer()
                    final_message = message + footer
            elif add_footer:
                final_message = message + "\n\n🤖 Generated with GAO-Dev\nCo-Authored-By: Claude <noreply@anthropic.com>"

            # Build commit command
            cmd = ["commit", "-m", final_message]
            if allow_empty:
                cmd.append("--allow-empty")

            # Create commit
            self._run_git_command(cmd)

            # Get commit hash
            hash_output = self._run_git_command(["rev-parse", "--short", "HEAD"])
            commit_hash = hash_output.strip()

            # Get changed files
            files_changed = self._get_changed_files(commit_hash)

            result = {
                "hash": commit_hash,
                "message": final_message,
                "timestamp": datetime.now(),
                "files_changed": files_changed,
            }

            self._log("info", "commit_created",
                     hash=commit_hash, files_changed=len(files_changed))

            return result

        except subprocess.CalledProcessError as e:
            error_msg = f"Git commit failed: {e.stderr}"
            self._log("error", "git_commit_failed", error=error_msg)
            raise

    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive git repository status.

        Returns:
            Dictionary with status information:
                - is_repo: bool
                - has_commits: bool
                - clean: bool (no uncommitted changes)
                - branch: str (current branch name)
                - staged_files: List[str]
                - unstaged_files: List[str]
                - untracked_files: List[str]

        Raises:
            Exception: If status check fails
        """
        try:
            # Check if it's a git repository
            if not self.is_git_repo():
                return {
                    "is_repo": False,
                    "has_commits": False,
                    "clean": True,
                    "branch": None,
                    "staged_files": [],
                    "unstaged_files": [],
                    "untracked_files": [],
                }

            # Get current branch
            branch = self.get_current_branch()

            # Check if there are any commits
            has_commits = self._has_commits()

            # Get status for different file states
            staged_files = self._get_staged_files()
            unstaged_files = self._get_unstaged_files()
            untracked_files = self._get_untracked_files()

            # Repo is clean if no staged, unstaged, or untracked files
            clean = not (staged_files or unstaged_files or untracked_files)

            return {
                "is_repo": True,
                "has_commits": has_commits,
                "clean": clean,
                "branch": branch,
                "staged_files": staged_files,
                "unstaged_files": unstaged_files,
                "untracked_files": untracked_files,
            }

        except Exception as e:
            error_msg = f"Failed to get git status: {str(e)}"
            self._log("error", "git_status_failed", error=error_msg)
            raise

    # ============================================================================
    # BASIC GIT OPERATIONS (Original core methods)
    # ============================================================================

    def git_init(self) -> bool:
        """
        Initialize git repository.

        Returns:
            True if successful

        Raises:
            subprocess.CalledProcessError: If git init fails
        """
        try:
            self._run_git_command(["init"])
            return True
        except subprocess.CalledProcessError:
            return False

    def git_add(self, files: List[str]) -> bool:
        """
        Stage files for commit.

        Args:
            files: List of file paths to stage

        Returns:
            True if successful

        Raises:
            subprocess.CalledProcessError: If git add fails
        """
        try:
            self._run_git_command(["add"] + files)
            return True
        except subprocess.CalledProcessError:
            return False

    def git_commit(self, message: str) -> bool:
        """
        Create git commit (simple version for backward compatibility).

        Args:
            message: Commit message

        Returns:
            True if successful

        Raises:
            subprocess.CalledProcessError: If git commit fails
        """
        try:
            # Add footer if configured (for GAO-Dev's own repo)
            final_message = message
            if self.config_loader and self.config_loader.is_git_auto_commit_enabled():
                footer = self.config_loader.get_git_commit_footer()
                final_message = message + footer

            self._run_git_command(["commit", "-m", final_message])
            return True
        except subprocess.CalledProcessError:
            return False

    def git_branch(self, branch_name: str, create: bool = True) -> bool:
        """
        Create or switch to branch.

        Args:
            branch_name: Branch name
            create: If True, create branch; if False, switch to existing

        Returns:
            True if successful

        Raises:
            subprocess.CalledProcessError: If branch operation fails
        """
        try:
            if create:
                self._run_git_command(["checkout", "-b", branch_name])
            else:
                self._run_git_command(["checkout", branch_name])
            return True
        except subprocess.CalledProcessError:
            return False

    def git_merge(self, branch_name: str) -> bool:
        """
        Merge branch into current branch.

        Args:
            branch_name: Branch to merge

        Returns:
            True if successful

        Raises:
            subprocess.CalledProcessError: If merge fails
        """
        try:
            self._run_git_command(["merge", branch_name])
            return True
        except subprocess.CalledProcessError:
            return False

    # ============================================================================
    # QUERY OPERATIONS
    # ============================================================================

    def is_git_repo(self) -> bool:
        """
        Check if directory is a git repository.

        Returns:
            True if git repo
        """
        # Method 1: Check for .git directory
        git_dir = self.project_path / ".git"
        if git_dir.exists():
            return True

        # Method 2: Try git command
        try:
            self._run_git_command(["rev-parse", "--git-dir"])
            return True
        except subprocess.CalledProcessError:
            return False

    def get_current_branch(self) -> Optional[str]:
        """
        Get current branch name.

        Returns:
            Branch name or None
        """
        try:
            result = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
            return result.strip()
        except subprocess.CalledProcessError:
            # Fallback to old method
            try:
                result = self._run_git_command(["branch", "--show-current"])
                return result.strip()
            except subprocess.CalledProcessError:
                return None

    # ============================================================================
    # CONVENTIONAL COMMITS
    # ============================================================================

    def create_conventional_commit(
        self,
        commit_type: str,
        scope: str,
        description: str,
        body: Optional[str] = None,
        add_all: bool = True,
    ) -> Dict[str, Any]:
        """
        Create conventional commit message and commit.

        Args:
            commit_type: Commit type (feat, fix, docs, etc.)
            scope: Commit scope
            description: Short description
            body: Optional detailed body
            add_all: Whether to stage all changes

        Returns:
            Commit info dict from create_commit()
        """
        message = f"{commit_type}({scope}): {description}"

        if body:
            message += f"\n\n{body}"

        return self.create_commit(message=message, add_all=add_all)

    # ============================================================================
    # TRANSACTION SUPPORT METHODS (Epic 23.1)
    # ============================================================================

    def is_working_tree_clean(self) -> bool:
        """
        Check if working directory has uncommitted changes.

        Returns True if the working tree is clean (no uncommitted changes),
        False if there are staged, unstaged, or untracked files.

        This method should be called before starting atomic operations to
        ensure no conflicts from uncommitted changes.

        Returns:
            bool: True if clean, False if dirty

        Raises:
            subprocess.CalledProcessError: If git command fails

        Example:
            >>> git = GitManager(Path("/project"))
            >>> if not git.is_working_tree_clean():
            ...     raise StateError("Uncommitted changes exist")
            >>> # Safe to proceed with atomic operation

        See Also:
            - get_status(): Get detailed status information
            - add_all(): Stage all changes
        """
        try:
            result = self._run_git_command(["status", "--porcelain"])
            is_clean = result.strip() == ""
            self._log("debug", "working_tree_clean_check", is_clean=is_clean)
            return is_clean
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to check working tree status: {e.stderr}"
            self._log("error", "working_tree_check_failed", error=error_msg)
            raise

    def add_all(self) -> bool:
        """
        Stage all changes (tracked and untracked files).

        Equivalent to 'git add -A', this stages all modifications,
        deletions, and new files for the next commit.

        Returns:
            bool: True if successful

        Raises:
            subprocess.CalledProcessError: If git add fails

        Example:
            >>> git = GitManager(Path("/project"))
            >>> # Make some changes
            >>> git.add_all()
            >>> git.commit("feat: add new feature")

        See Also:
            - commit(): Create commit after staging
            - is_working_tree_clean(): Check for changes
        """
        try:
            self._run_git_command(["add", "-A"])
            self._log("debug", "staged_all_changes")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to stage changes: {e.stderr}"
            self._log("error", "add_all_failed", error=error_msg)
            raise

    def commit(self, message: str, allow_empty: bool = False) -> str:
        """
        Create a git commit with the given message.

        This method commits all staged changes to the repository. Ensure you have
        called add_all() first to stage changes, or pass allow_empty=True to create
        an empty commit.

        The commit is created with the configured git user name and email. Returns
        the short SHA (7 characters) of the created commit for checkpoint tracking.

        Args:
            message: Commit message (conventional commits format recommended)
            allow_empty: Allow creating commits with no changes (default: False)

        Returns:
            str: Short SHA (7 characters) of created commit

        Raises:
            subprocess.CalledProcessError: If commit fails (e.g., no changes and allow_empty=False)

        Example:
            >>> git = GitManager(Path("/project"))
            >>> git.add_all()
            >>> sha = git.commit("feat: add new feature")
            >>> print(sha)  # "abc1234"

        See Also:
            - add_all(): Stage changes before committing
            - is_working_tree_clean(): Check for uncommitted changes
            - get_commit_info(): Retrieve commit details

        Note:
            Commits are permanent - they cannot be removed, only reverted.
            Use descriptive commit messages following conventional commits format.
        """
        try:
            # Build commit command
            cmd = ["commit", "-m", message]
            if allow_empty:
                cmd.append("--allow-empty")

            # Create commit
            self._run_git_command(cmd)

            # Get commit hash (short form)
            hash_output = self._run_git_command(["rev-parse", "--short", "HEAD"])
            commit_sha = hash_output.strip()

            self._log("info", "commit_created", sha=commit_sha, commit_message=message[:50])
            return commit_sha

        except subprocess.CalledProcessError as e:
            error_msg = f"Commit failed: {e.stderr}"
            self._log("error", "commit_failed", error=error_msg, commit_message=message[:50])
            raise

    def reset_hard(self, target: str = "HEAD") -> bool:
        """
        Perform hard reset to discard uncommitted changes (DESTRUCTIVE).

        WARNING: This operation is DESTRUCTIVE and cannot be undone.
        It discards all uncommitted changes permanently.

        Use only in error recovery scenarios. Consider alternatives like
        'git stash' for user-facing operations.

        Args:
            target: Git ref to reset to (default: "HEAD")

        Returns:
            bool: True if successful

        Raises:
            subprocess.CalledProcessError: If reset fails

        Example:
            >>> git = GitManager(Path("/project"))
            >>> try:
            ...     # Atomic operation
            ...     git.add_all()
            ...     git.commit("feat: change")
            ... except Exception:
            ...     # Rollback on error
            ...     git.reset_hard()
            ...     raise

        Warning:
            DESTRUCTIVE: Discards all uncommitted changes permanently.
            Use with extreme caution.

        See Also:
            - is_working_tree_clean(): Check for uncommitted changes
            - get_head_sha(): Get current commit before reset
        """
        try:
            self._log("warning", "DESTRUCTIVE_reset_hard", target=target)
            self._run_git_command(["reset", "--hard", target])
            self._log("info", "reset_hard_complete", target=target)
            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"Reset hard failed: {e.stderr}"
            self._log("error", "reset_hard_failed", error=error_msg, target=target)
            raise

    def get_head_sha(self, short: bool = True) -> str:
        """
        Get current commit hash.

        Returns the SHA of the current HEAD commit. Use short=True for
        7-character short form, short=False for full 40-character hash.

        Args:
            short: Return short SHA (7 chars) if True, long SHA (40 chars) if False

        Returns:
            str: Commit SHA (short or long form)

        Raises:
            subprocess.CalledProcessError: If no commits exist or git command fails

        Example:
            >>> git = GitManager(Path("/project"))
            >>> sha = git.get_head_sha()
            >>> print(sha)  # "abc1234"
            >>> full_sha = git.get_head_sha(short=False)
            >>> print(full_sha)  # "abc1234567890abcdef1234567890abcdef12345"

        See Also:
            - commit(): Create new commit
            - get_commit_info(): Get detailed commit information
        """
        try:
            if short:
                result = self._run_git_command(["rev-parse", "--short", "HEAD"])
            else:
                result = self._run_git_command(["rev-parse", "HEAD"])

            sha = result.strip()
            self._log("debug", "retrieved_head_sha", sha=sha, short=short)
            return sha
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to get HEAD SHA: {e.stderr}"
            self._log("error", "get_head_sha_failed", error=error_msg)
            raise

    # ============================================================================
    # BRANCH MANAGEMENT METHODS (Epic 23.2)
    # ============================================================================

    def create_branch(self, name: str, checkout: bool = True) -> bool:
        """
        Create a new branch and optionally check it out.

        Creates a new branch from the current HEAD. If checkout=True,
        immediately switches to the new branch.

        Args:
            name: Branch name (e.g., "feature/epic-23", "migration/hybrid")
            checkout: Whether to checkout the branch after creation (default: True)

        Returns:
            bool: True if successful

        Raises:
            subprocess.CalledProcessError: If branch already exists or creation fails

        Example:
            >>> git = GitManager(Path("/project"))
            >>> git.create_branch("migration/hybrid-architecture")
            >>> # Now on migration/hybrid-architecture branch

        See Also:
            - checkout(): Switch to existing branch
            - delete_branch(): Delete branch after merge
        """
        try:
            self._run_git_command(["branch", name])
            self._log("info", "branch_created", branch=name)

            if checkout:
                self._run_git_command(["checkout", name])
                self._log("info", "branch_checked_out", branch=name)

            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to create branch '{name}': {e.stderr}"
            self._log("error", "create_branch_failed", error=error_msg, branch=name)
            raise

    def checkout(self, branch: str) -> bool:
        """
        Switch to an existing branch.

        Checks out a local or remote branch. If the branch doesn't exist locally
        but exists on a remote (e.g., origin/branch), creates a tracking branch.

        Args:
            branch: Branch name to checkout

        Returns:
            bool: True if successful

        Raises:
            subprocess.CalledProcessError: If branch doesn't exist or working tree is dirty

        Example:
            >>> git = GitManager(Path("/project"))
            >>> git.checkout("main")
            >>> # Now on main branch

        Warning:
            Fails if working tree has uncommitted changes.
            Call is_working_tree_clean() first to verify.

        See Also:
            - create_branch(): Create new branch
            - is_working_tree_clean(): Check for uncommitted changes
        """
        try:
            # Try local checkout first
            try:
                self._run_git_command(["checkout", branch])
                self._log("info", "branch_checked_out", branch=branch)
                return True
            except subprocess.CalledProcessError:
                # Try as remote tracking branch
                self._run_git_command(["checkout", "-b", branch, f"origin/{branch}"])
                self._log("info", "remote_branch_checked_out", branch=branch)
                return True
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to checkout branch '{branch}': {e.stderr}"
            self._log("error", "checkout_failed", error=error_msg, branch=branch)
            raise

    def delete_branch(self, name: str, force: bool = False) -> bool:
        """
        Delete a local branch.

        Deletes a branch from the local repository. By default, prevents deletion
        of unmerged branches (safety check). Use force=True to override.

        Args:
            name: Branch name to delete
            force: Force deletion even if unmerged (default: False)

        Returns:
            bool: True if successful

        Raises:
            subprocess.CalledProcessError: If branch doesn't exist or has unmerged changes (without force)

        Example:
            >>> git = GitManager(Path("/project"))
            >>> git.create_branch("migration/test")
            >>> # ... work on branch, merge to main ...
            >>> git.checkout("main")
            >>> git.delete_branch("migration/test")

        Warning:
            Use force=True only when intentional (e.g., migration rollback).
            Default behavior prevents accidental loss of unmerged work.

        See Also:
            - create_branch(): Create new branch
            - merge(): Merge branch before deletion
        """
        try:
            force_flag = "-D" if force else "-d"

            if force:
                self._log("warning", "force_deleting_branch", branch=name)

            self._run_git_command(["branch", force_flag, name])
            self._log("info", "branch_deleted", branch=name, force=force)
            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to delete branch '{name}': {e.stderr}"
            self._log("error", "delete_branch_failed", error=error_msg, branch=name)
            raise

    def merge(self, branch: str, no_ff: bool = False, message: Optional[str] = None) -> bool:
        """
        Merge a branch into the current branch.

        Merges the specified branch into the current branch. Supports no-fast-forward
        merges to preserve branch history, and custom commit messages.

        Args:
            branch: Branch name to merge
            no_ff: Use --no-ff flag to preserve merge history (default: False)
            message: Custom merge commit message (optional)

        Returns:
            bool: True if successful

        Raises:
            subprocess.CalledProcessError: If merge fails or has conflicts

        Example:
            >>> git = GitManager(Path("/project"))
            >>> git.checkout("main")
            >>> git.merge("migration/hybrid", no_ff=True, message="Merge migration")

        See Also:
            - create_branch(): Create branch to merge
            - delete_branch(): Delete branch after merge
        """
        try:
            cmd = ["merge"]
            if no_ff:
                cmd.append("--no-ff")
            if message:
                cmd.extend(["-m", message])
            cmd.append(branch)

            self._run_git_command(cmd)
            self._log("info", "branch_merged", branch=branch, no_ff=no_ff)
            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to merge branch '{branch}': {e.stderr}"
            self._log("error", "merge_failed", error=error_msg, branch=branch)
            raise

    # ============================================================================
    # FILE HISTORY QUERY METHODS (Epic 23.3)
    # ============================================================================

    def get_last_commit_for_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about the last commit that modified a file.

        Returns commit metadata including SHA, message, author, and date.
        Returns None if file is not tracked or has no commits.

        Args:
            path: Path to file (relative to repo root or absolute)

        Returns:
            Optional[Dict]: Commit info dict with keys: sha, message, author, date
                           Returns None if file not tracked or no commits

        Example:
            >>> git = GitManager(Path("/project"))
            >>> info = git.get_last_commit_for_file(Path("docs/story.md"))
            >>> if info and "complete" in info["message"].lower():
            ...     state = "done"

        See Also:
            - get_commit_info(): Get commit info by SHA
            - is_file_tracked(): Check if file is tracked
        """
        try:
            # Convert to relative path if absolute
            if path.is_absolute():
                try:
                    path = path.relative_to(self.project_path)
                except ValueError:
                    # Path outside repo
                    self._log("warning", "file_outside_repo", path=str(path))
                    return None

            result = self._run_git_command([
                "log", "-1", "--format=%H|%s|%an|%ai", "--", str(path)
            ])

            if not result.strip():
                return None  # File not tracked or no commits

            parts = result.strip().split("|", 3)
            if len(parts) != 4:
                return None

            full_sha, message, author, date = parts

            commit_info = {
                "sha": full_sha[:7],  # Short SHA
                "full_sha": full_sha,
                "message": message,
                "author": author,
                "date": date
            }

            self._log("debug", "retrieved_file_commit_info", path=str(path), sha=commit_info["sha"])
            return commit_info

        except subprocess.CalledProcessError as e:
            self._log("warning", "get_last_commit_failed", path=str(path), error=str(e))
            return None

    def file_deleted_in_history(self, path: Path) -> bool:
        """
        Check if a file was deleted in git history.

        Searches git history for deletion commits affecting the file.

        Args:
            path: Path to file (relative to repo root or absolute)

        Returns:
            bool: True if file was deleted in history, False otherwise

        Example:
            >>> git = GitManager(Path("/project"))
            >>> if git.file_deleted_in_history(Path("docs/old.md")):
            ...     print("File was deleted")

        See Also:
            - get_last_commit_for_file(): Get last commit info
            - is_file_tracked(): Check if currently tracked
        """
        try:
            # Convert to relative path if absolute
            if path.is_absolute():
                try:
                    path = path.relative_to(self.project_path)
                except ValueError:
                    return False

            result = self._run_git_command([
                "log", "--diff-filter=D", "--", str(path)
            ])

            was_deleted = bool(result.strip())
            self._log("debug", "file_deletion_check", path=str(path), was_deleted=was_deleted)
            return was_deleted

        except subprocess.CalledProcessError:
            return False

    def is_file_tracked(self, path: Path) -> bool:
        """
        Check if a file is tracked by git (in the index).

        Args:
            path: Path to file (relative to repo root or absolute)

        Returns:
            bool: True if file is tracked, False otherwise

        Example:
            >>> git = GitManager(Path("/project"))
            >>> if git.is_file_tracked(Path("docs/new.md")):
            ...     print("File is tracked")

        See Also:
            - get_file_status(): Get detailed file status
            - add_all(): Stage untracked files
        """
        try:
            # Convert to relative path if absolute
            if path.is_absolute():
                try:
                    path = path.relative_to(self.project_path)
                except ValueError:
                    return False

            result = self._run_git_command(["ls-files", str(path)])
            is_tracked = bool(result.strip())
            self._log("debug", "file_tracked_check", path=str(path), is_tracked=is_tracked)
            return is_tracked

        except subprocess.CalledProcessError:
            return False

    def get_file_status(self, path: Path) -> str:
        """
        Get the git status of a specific file.

        Returns one of: "clean", "modified", "staged", "untracked", "deleted", "unknown"

        Args:
            path: Path to file (relative to repo root or absolute)

        Returns:
            str: File status (clean, modified, staged, untracked, deleted, unknown)

        Example:
            >>> git = GitManager(Path("/project"))
            >>> status = git.get_file_status(Path("docs/file.md"))
            >>> if status == "deleted":
            ...     print("File was deleted")

        See Also:
            - is_file_tracked(): Check if file is tracked
            - get_status(): Get overall repository status
        """
        try:
            # Convert to relative path if absolute
            if path.is_absolute():
                try:
                    path = path.relative_to(self.project_path)
                except ValueError:
                    return "unknown"

            result = self._run_git_command(["status", "--porcelain", str(path)])

            if not result.strip():
                # Empty means clean (if tracked) or not in repo
                if self.is_file_tracked(path):
                    return "clean"
                else:
                    return "untracked"

            status_code = result[:2] if len(result) >= 2 else "  "

            # Map git status codes to readable names
            status_map = {
                "  ": "clean",
                " M": "modified",
                "M ": "staged",
                "MM": "staged",  # Modified and staged
                "A ": "staged",
                "AM": "staged",
                "??": "untracked",
                " D": "deleted",
                "D ": "staged",  # Staged for deletion
            }

            file_status = status_map.get(status_code, "unknown")
            self._log("debug", "file_status_check", path=str(path), status=file_status)
            return file_status

        except subprocess.CalledProcessError:
            return "unknown"

    # ============================================================================
    # QUERY ENHANCEMENT METHODS (Epic 23.4)
    # ============================================================================

    def get_commit_info(self, sha: str = "HEAD") -> Dict[str, Any]:
        """
        Get comprehensive information about a specific commit.

        Returns detailed commit metadata including SHA, message, author, email,
        date, and list of files changed.

        Args:
            sha: Commit SHA or ref (e.g., "HEAD", "abc1234") (default: "HEAD")

        Returns:
            Dict: Commit info with keys: sha, full_sha, message, author, email, date, files_changed

        Raises:
            subprocess.CalledProcessError: If commit doesn't exist

        Example:
            >>> git = GitManager(Path("/project"))
            >>> commit = git.get_commit_info("HEAD")
            >>> print(f"{commit['sha']}: {commit['message']}")

        See Also:
            - get_commits_since(): Get commit range
            - get_head_sha(): Get current commit SHA
        """
        try:
            # Get commit metadata
            result = self._run_git_command([
                "show", "--format=%H|%h|%s|%an|%ae|%ai", "--name-only", sha
            ])

            lines = result.strip().split("\n")
            if not lines:
                raise ValueError(f"Invalid commit: {sha}")

            # Parse first line (metadata)
            parts = lines[0].split("|", 5)
            if len(parts) != 6:
                raise ValueError(f"Failed to parse commit info: {sha}")

            full_sha, short_sha, message, author, email, date = parts

            # Get files changed (skip blank line after metadata)
            files = [line.strip() for line in lines[2:] if line.strip()]

            commit_info = {
                "sha": short_sha,
                "full_sha": full_sha,
                "message": message,
                "author": author,
                "email": email,
                "date": date,
                "files_changed": files
            }

            self._log("debug", "retrieved_commit_info", sha=short_sha, files_count=len(files))
            return commit_info

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to get commit info for '{sha}': {e.stderr}"
            self._log("error", "get_commit_info_failed", error=error_msg, sha=sha)
            raise

    def get_commits_since(
        self,
        since: str,
        until: str = "HEAD",
        file_path: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of commits in a range, optionally filtered by file.

        Returns commits between 'since' and 'until' refs. Optionally filters
        to only commits affecting a specific file.

        Args:
            since: Starting ref (exclusive)
            until: Ending ref (inclusive) (default: "HEAD")
            file_path: Optional file path to filter commits (default: None)

        Returns:
            List[Dict]: List of commit dicts with keys: sha, full_sha, message, author, email, date

        Example:
            >>> git = GitManager(Path("/project"))
            >>> commits = git.get_commits_since("abc1234", "HEAD")
            >>> for commit in commits:
            ...     print(f"{commit['sha']}: {commit['message']}")

        See Also:
            - get_commit_info(): Get detailed info for single commit
            - get_last_commit_for_file(): Get last commit for file
        """
        try:
            cmd = ["log", f"{since}..{until}", "--format=%H|%h|%s|%an|%ae|%ai"]

            if file_path:
                # Convert to relative path if absolute
                if file_path.is_absolute():
                    try:
                        file_path = file_path.relative_to(self.project_path)
                    except ValueError:
                        self._log("warning", "file_outside_repo", path=str(file_path))
                        return []
                cmd.extend(["--", str(file_path)])

            result = self._run_git_command(cmd)

            commits = []
            for line in result.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("|", 5)
                if len(parts) != 6:
                    continue

                full_sha, short_sha, message, author, email, date = parts

                commits.append({
                    "sha": short_sha,
                    "full_sha": full_sha,
                    "message": message,
                    "author": author,
                    "email": email,
                    "date": date
                })

            self._log("debug", "retrieved_commit_range",
                     since=since, until=until, count=len(commits),
                     file=str(file_path) if file_path else None)

            return commits

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to get commits since '{since}': {e.stderr}"
            self._log("error", "get_commits_since_failed", error=error_msg, since=since, until=until)
            raise

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _create_gitignore(self) -> None:
        """Create comprehensive .gitignore file."""
        gitignore_path = self.project_path / ".gitignore"

        # Don't overwrite existing .gitignore
        if gitignore_path.exists():
            return

        gitignore_content = """# GAO-Dev Project .gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
venv/
ENV/
env/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# Next.js
.next/
out/

# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/
.nox/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Environment
.env
.env.local
.env.*.local

# GAO-Dev metadata
.gao-dev/
"""

        gitignore_path.write_text(gitignore_content, encoding="utf-8")
        self._log("debug", "gitignore_created")

    def _run_git_command(self, args: List[str]) -> str:
        """
        Run a git command in the project directory.

        Args:
            args: Git command arguments (e.g., ['status', '--short'])

        Returns:
            Command output (stdout)

        Raises:
            subprocess.CalledProcessError: If command fails
        """
        cmd = ["git"] + args
        result = subprocess.run(
            cmd,
            cwd=self.project_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def _has_commits(self) -> bool:
        """Check if repository has any commits."""
        try:
            self._run_git_command(["rev-parse", "HEAD"])
            return True
        except subprocess.CalledProcessError:
            return False

    def _get_staged_files(self) -> List[str]:
        """Get list of staged files."""
        try:
            output = self._run_git_command(["diff", "--cached", "--name-only"])
            return [f.strip() for f in output.splitlines() if f.strip()]
        except subprocess.CalledProcessError:
            return []

    def _get_unstaged_files(self) -> List[str]:
        """Get list of modified but unstaged files."""
        try:
            output = self._run_git_command(["diff", "--name-only"])
            return [f.strip() for f in output.splitlines() if f.strip()]
        except subprocess.CalledProcessError:
            return []

    def _get_untracked_files(self) -> List[str]:
        """Get list of untracked files."""
        try:
            output = self._run_git_command(
                ["ls-files", "--others", "--exclude-standard"]
            )
            return [f.strip() for f in output.splitlines() if f.strip()]
        except subprocess.CalledProcessError:
            return []

    def _get_changed_files(self, commit_hash: str) -> List[str]:
        """Get list of files changed in a commit."""
        try:
            output = self._run_git_command(
                ["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash]
            )
            return [f.strip() for f in output.splitlines() if f.strip()]
        except subprocess.CalledProcessError:
            return []

    def _log(self, level: str, message: str, **kwargs):
        """Log message with appropriate logger."""
        if HAS_STRUCTLOG:
            getattr(self.logger, level)(message, **kwargs)
        else:
            log_msg = f"{message} {kwargs}" if kwargs else message
            getattr(self.logger, level)(log_msg)
