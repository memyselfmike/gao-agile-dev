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
