"""Git repository cloning functionality for sandbox projects."""

import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import structlog

from .exceptions import (
    GitCloneError,
    GitNotInstalledError,
    InvalidGitUrlError,
)

logger = structlog.get_logger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
SUPPORTED_SCHEMES = {"https", "http", "ssh", "git"}

# URL patterns
HTTPS_URL_PATTERN = re.compile(
    r"^https?://[\w\-.]+(:\d+)?/[\w\-./]+\.git$|"
    r"^https?://[\w\-.]+(:\d+)?/[\w\-./]+$"
)
SSH_URL_PATTERN = re.compile(
    r"^git@[\w\-.]+(:\d+)?:[\w\-./]+\.git$|"
    r"^git@[\w\-.]+(:\d+)?:[\w\-./]+$|"
    r"^ssh://git@[\w\-.]+(:\d+)?/[\w\-./]+\.git$"
)


class GitCloner:
    """
    Handles cloning Git repositories for boilerplate integration.

    Supports HTTPS and SSH URLs with automatic retry logic,
    validation, and cleanup on failure.
    """

    def __init__(self):
        """Initialize Git cloner."""
        self._check_git_installed()

    def clone_repository(
        self,
        repo_url: str,
        destination: Path,
        branch: Optional[str] = None,
    ) -> bool:
        """
        Clone Git repository to destination.

        Automatically retries on network failures with exponential backoff.
        Cleans up partial clones on failure.

        Args:
            repo_url: Git repository URL (HTTPS or SSH)
            destination: Target directory for clone
            branch: Specific branch to clone (default: auto-detect)

        Returns:
            True if successful

        Raises:
            InvalidGitUrlError: If URL format is invalid
            GitCloneError: If cloning fails after retries
        """
        # Validate URL
        if not self.validate_git_url(repo_url):
            raise InvalidGitUrlError(repo_url, "URL format not supported")

        # Ensure destination parent exists
        destination = Path(destination).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)

        # If no branch specified, try to get default branch
        if branch is None:
            try:
                branch = self.get_default_branch(repo_url)
                logger.info("detected_default_branch", branch=branch, repo_url=repo_url)
            except GitCloneError:
                # If we can't detect, let git clone figure it out
                branch = None

        # Attempt clone with retries
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(
                    "cloning_repository",
                    repo_url=repo_url,
                    destination=str(destination),
                    branch=branch,
                    attempt=attempt,
                    max_retries=MAX_RETRIES,
                )

                # Build git clone command
                cmd = ["git", "clone", "--progress"]

                # Add branch if specified
                if branch:
                    cmd.extend(["--branch", branch])

                # Add shallow clone for faster cloning
                cmd.extend(["--depth", "1"])

                # Add repo URL and destination
                cmd.extend([repo_url, str(destination)])

                # Execute git clone
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                    check=False,
                )

                if result.returncode == 0:
                    logger.info(
                        "clone_successful",
                        repo_url=repo_url,
                        destination=str(destination),
                    )
                    return True

                # Clone failed, check if it's a retryable error
                error_msg = result.stderr or result.stdout
                if self._is_retryable_error(error_msg):
                    last_error = error_msg
                    if attempt < MAX_RETRIES:
                        delay = RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
                        logger.warning(
                            "clone_failed_retrying",
                            attempt=attempt,
                            delay_seconds=delay,
                            error=error_msg,
                        )
                        time.sleep(delay)
                        continue

                # Non-retryable error, raise immediately
                self._cleanup_failed_clone(destination)
                raise GitCloneError(repo_url, error_msg)

            except subprocess.TimeoutExpired:
                last_error = "Clone operation timed out after 5 minutes"
                logger.warning(
                    "clone_timeout",
                    attempt=attempt,
                    repo_url=repo_url,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS * (2 ** (attempt - 1)))
                    self._cleanup_failed_clone(destination)
                    continue
                break

            except Exception as e:
                last_error = str(e)
                logger.error(
                    "clone_unexpected_error",
                    error=str(e),
                    attempt=attempt,
                )
                break

        # All retries failed
        self._cleanup_failed_clone(destination)
        raise GitCloneError(
            repo_url,
            f"Failed after {MAX_RETRIES} attempts. Last error: {last_error}",
        )

    def validate_git_url(self, url: str) -> bool:
        """
        Validate Git repository URL format.

        Supports:
        - HTTPS: https://github.com/user/repo.git
        - HTTP: http://github.com/user/repo.git
        - SSH: git@github.com:user/repo.git
        - SSH: ssh://git@github.com/user/repo.git

        Args:
            url: URL to validate

        Returns:
            True if URL is valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False

        url = url.strip()

        # Check HTTPS/HTTP pattern
        if HTTPS_URL_PATTERN.match(url):
            return True

        # Check SSH pattern
        if SSH_URL_PATTERN.match(url):
            return True

        # Try parsing as URL for additional validation
        try:
            parsed = urlparse(url)
            if parsed.scheme in SUPPORTED_SCHEMES:
                return True
        except Exception:
            pass

        return False

    def get_default_branch(self, repo_url: str) -> str:
        """
        Determine default branch for repository.

        Attempts to detect the default branch by querying the remote
        repository without cloning it.

        Args:
            repo_url: Git repository URL

        Returns:
            Name of default branch (e.g., "main", "master")

        Raises:
            GitCloneError: If unable to determine default branch
        """
        try:
            logger.debug("detecting_default_branch", repo_url=repo_url)

            # Use git ls-remote to query default branch
            result = subprocess.run(
                ["git", "ls-remote", "--symref", repo_url, "HEAD"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            if result.returncode != 0:
                raise GitCloneError(
                    repo_url,
                    f"Unable to query remote repository: {result.stderr}",
                )

            # Parse output to find default branch
            # Format: ref: refs/heads/main	HEAD
            output = result.stdout.strip()
            for line in output.split("\n"):
                if line.startswith("ref:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        ref = parts[1]
                        # Extract branch name from refs/heads/<branch>
                        if ref.startswith("refs/heads/"):
                            branch = ref.replace("refs/heads/", "")
                            logger.debug(
                                "default_branch_detected",
                                repo_url=repo_url,
                                branch=branch,
                            )
                            return branch

            # Couldn't parse output, fall back to common defaults
            logger.warning(
                "could_not_detect_branch_using_fallback",
                repo_url=repo_url,
            )
            return "main"

        except subprocess.TimeoutExpired:
            raise GitCloneError(
                repo_url,
                "Timeout while querying default branch",
            )
        except Exception as e:
            raise GitCloneError(
                repo_url,
                f"Error detecting default branch: {str(e)}",
            )

    def _check_git_installed(self) -> None:
        """
        Check if git is installed and available.

        Raises:
            GitNotInstalledError: If git is not available
        """
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if result.returncode != 0:
                raise GitNotInstalledError()

            logger.debug("git_version_check", version=result.stdout.strip())

        except FileNotFoundError:
            raise GitNotInstalledError()
        except Exception:
            raise GitNotInstalledError()

    def _is_retryable_error(self, error_msg: str) -> bool:
        """
        Check if error is retryable (network issues, etc).

        Args:
            error_msg: Error message from git

        Returns:
            True if error should be retried
        """
        if not error_msg:
            return False

        error_msg = error_msg.lower()

        # Network-related errors that should be retried
        retryable_patterns = [
            "connection",
            "network",
            "timeout",
            "timed out",
            "could not resolve host",
            "failed to connect",
            "temporary failure",
            "unable to access",
        ]

        return any(pattern in error_msg for pattern in retryable_patterns)

    def _cleanup_failed_clone(self, destination: Path) -> None:
        """
        Clean up partial clone on failure.

        Args:
            destination: Directory to clean up
        """
        if destination.exists():
            try:
                logger.debug("cleaning_up_failed_clone", destination=str(destination))
                shutil.rmtree(destination)
            except Exception as e:
                logger.warning(
                    "cleanup_failed",
                    destination=str(destination),
                    error=str(e),
                )
