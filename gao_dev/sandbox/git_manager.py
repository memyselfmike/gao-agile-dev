"""Git repository management for sandbox projects."""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog

from .exceptions import ProjectStateError

logger = structlog.get_logger(__name__)


class GitManager:
    """
    Manages git operations for sandbox projects.

    Handles repository initialization, commits, status checking,
    and other git operations needed for incremental story-based workflow.
    """

    DEFAULT_USER_NAME = "GAO-Dev Benchmark"
    DEFAULT_USER_EMAIL = "benchmark@gao-dev.local"

    def __init__(self, project_path: Path):
        """
        Initialize git manager for a project.

        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path).resolve()
        self.logger = logger.bind(component="GitManager", project=str(project_path))

    def init_repo(
        self,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        initial_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        Initialize git repository in project directory.

        Creates a new git repository, configures user info,
        creates .gitignore, and optionally makes initial commit.

        Args:
            user_name: Git user name (defaults to DEFAULT_USER_NAME)
            user_email: Git user email (defaults to DEFAULT_USER_EMAIL)
            initial_commit: Whether to create initial commit

        Returns:
            Dictionary with initialization results:
                - initialized: bool
                - commit_hash: Optional[str] (if initial_commit=True)
                - timestamp: datetime

        Raises:
            ProjectStateError: If git init fails
        """
        self.logger.info("initializing_git_repository")

        try:
            # Initialize git repository
            self._run_git_command(["init"])

            # Configure user name and email
            name = user_name or self.DEFAULT_USER_NAME
            email = user_email or self.DEFAULT_USER_EMAIL
            self._run_git_command(["config", "user.name", name])
            self._run_git_command(["config", "user.email", email])

            # Create .gitignore
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
                    message="chore: initialize project repository\n\nInitial project structure created by GAO-Dev Benchmark system.",
                    allow_empty=True,
                )
                result["commit_hash"] = commit_result["hash"]
                result["commit_message"] = commit_result["message"]

            self.logger.info(
                "git_repository_initialized",
                user_name=name,
                initial_commit=initial_commit,
            )

            return result

        except subprocess.CalledProcessError as e:
            error_msg = f"Git initialization failed: {e.stderr}"
            self.logger.error("git_init_failed", error=error_msg)
            raise ProjectStateError(
                str(self.project_path), "uninitialized", "git_initialized"
            )

    def create_commit(
        self,
        message: str,
        add_all: bool = True,
        allow_empty: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a git commit.

        Args:
            message: Commit message
            add_all: Whether to stage all changes (git add -A)
            allow_empty: Whether to allow empty commits

        Returns:
            Dictionary with commit information:
                - hash: str (short hash)
                - message: str
                - timestamp: datetime
                - files_changed: List[str]

        Raises:
            ProjectStateError: If commit fails
        """
        self.logger.info("creating_commit", message=message[:50])

        try:
            # Stage changes if requested
            if add_all:
                self._run_git_command(["add", "-A"])

            # Build commit command
            cmd = ["commit", "-m", message]
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
                "message": message,
                "timestamp": datetime.now(),
                "files_changed": files_changed,
            }

            self.logger.info(
                "commit_created",
                hash=commit_hash,
                files_changed=len(files_changed),
            )

            return result

        except subprocess.CalledProcessError as e:
            error_msg = f"Git commit failed: {e.stderr}"
            self.logger.error("git_commit_failed", error=error_msg)
            raise ProjectStateError(
                str(self.project_path), "uncommitted", "committed"
            )

    def get_status(self) -> Dict[str, Any]:
        """
        Get git repository status.

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
            ProjectStateError: If git status check fails
        """
        try:
            # Check if it's a git repository
            is_repo = self._is_git_repo()

            if not is_repo:
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
            branch_output = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
            branch = branch_output.strip()

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
            self.logger.error("git_status_failed", error=error_msg)
            raise ProjectStateError(
                str(self.project_path), "unknown", "status_checked"
            )

    def _create_gitignore(self) -> None:
        """Create .gitignore file with common patterns."""
        gitignore_path = self.project_path / ".gitignore"

        # Don't overwrite existing .gitignore
        if gitignore_path.exists():
            return

        gitignore_content = """# GAO-Dev Sandbox Project .gitignore

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

# GAO-Dev metadata (keep tracked for benchmarking)
# .sandbox.yaml is tracked to preserve project metadata
"""

        gitignore_path.write_text(gitignore_content, encoding="utf-8")
        self.logger.debug("gitignore_created")

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

    def _is_git_repo(self) -> bool:
        """Check if directory is a git repository."""
        try:
            self._run_git_command(["rev-parse", "--git-dir"])
            return True
        except subprocess.CalledProcessError:
            return False

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
