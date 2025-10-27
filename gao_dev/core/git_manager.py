"""Git operations manager."""

from pathlib import Path
from typing import List, Optional
import subprocess

from .config_loader import ConfigLoader


class GitManager:
    """Manage git operations."""

    def __init__(self, config_loader: ConfigLoader):
        """
        Initialize git manager.

        Args:
            config_loader: Configuration loader instance
        """
        self.config_loader = config_loader
        self.project_root = config_loader.project_root

    def git_init(self) -> bool:
        """
        Initialize git repository.

        Returns:
            True if successful
        """
        try:
            subprocess.run(
                ["git", "init"],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )
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
        """
        try:
            subprocess.run(
                ["git", "add"] + files,
                cwd=self.project_root,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def git_commit(self, message: str) -> bool:
        """
        Create git commit.

        Args:
            message: Commit message

        Returns:
            True if successful
        """
        try:
            # Add footer if auto-commit is enabled
            if self.config_loader.is_git_auto_commit_enabled():
                footer = self.config_loader.get_git_commit_footer()
                message = message + footer

            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )
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
        """
        try:
            if create:
                subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    cwd=self.project_root,
                    check=True,
                    capture_output=True
                )
            else:
                subprocess.run(
                    ["git", "checkout", branch_name],
                    cwd=self.project_root,
                    check=True,
                    capture_output=True
                )
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
        """
        try:
            subprocess.run(
                ["git", "merge", branch_name],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def is_git_repo(self) -> bool:
        """
        Check if directory is a git repository.

        Returns:
            True if git repo
        """
        git_dir = self.project_root / ".git"
        return git_dir.exists()

    def get_current_branch(self) -> Optional[str]:
        """
        Get current branch name.

        Returns:
            Branch name or None
        """
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def create_conventional_commit(
        self,
        commit_type: str,
        scope: str,
        description: str,
        body: Optional[str] = None
    ) -> str:
        """
        Create conventional commit message.

        Args:
            commit_type: Commit type (feat, fix, docs, etc.)
            scope: Commit scope
            description: Short description
            body: Optional detailed body

        Returns:
            Formatted commit message
        """
        message = f"{commit_type}({scope}): {description}"

        if body:
            message += f"\n\n{body}"

        return message
