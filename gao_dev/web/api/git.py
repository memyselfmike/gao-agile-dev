"""Git operations API endpoints for GAO-Dev web interface."""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from gao_dev.core.git_manager import GitManager

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/git", tags=["git"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class CommitAuthor(BaseModel):
    """Commit author information."""

    name: str
    email: str
    is_agent: bool


class CommitInfo(BaseModel):
    """Commit information for timeline display."""

    hash: str
    short_hash: str
    message: str
    author: CommitAuthor
    timestamp: str  # ISO 8601 format
    files_changed: int
    insertions: int
    deletions: int


class CommitListResponse(BaseModel):
    """Response model for commit list endpoint."""

    commits: List[CommitInfo]
    total: int
    has_more: bool


class FileChange(BaseModel):
    """File change information in a commit diff."""

    path: str
    change_type: str  # "added", "modified", "deleted"
    insertions: int
    deletions: int
    is_binary: bool
    diff: Optional[str]
    original_content: Optional[str]
    modified_content: Optional[str]


class CommitDiffResponse(BaseModel):
    """Response model for commit diff endpoint."""

    files: List[FileChange]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _is_agent_commit(email: str) -> bool:
    """
    Detect if commit is from GAO-Dev agent based on email pattern.

    Agent commits have emails like:
    - *@gao-dev.local (agent commits)
    - noreply@anthropic.com (Claude/agent commits)

    Args:
        email: Commit author email

    Returns:
        True if agent commit, False if user commit
    """
    agent_patterns = [
        "@gao-dev.local",
        "noreply@anthropic.com",
        "dev@gao-dev.local",
    ]
    return any(pattern in email.lower() for pattern in agent_patterns)


def _parse_commit_stats(git_manager: GitManager, commit_hash: str) -> Dict[str, int]:
    """
    Parse commit statistics (files changed, insertions, deletions).

    Uses 'git show --numstat' to get detailed statistics.

    Args:
        git_manager: GitManager instance
        commit_hash: Commit SHA

    Returns:
        Dict with keys: files_changed, insertions, deletions
    """
    try:
        # Get numstat for commit
        result = git_manager._run_git_command(["show", "--numstat", "--format=", commit_hash])

        files_changed = 0
        total_insertions = 0
        total_deletions = 0

        for line in result.strip().split("\n"):
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) >= 2:
                insertions = parts[0]
                deletions = parts[1]

                # Handle binary files (marked with -)
                if insertions != "-" and deletions != "-":
                    total_insertions += int(insertions)
                    total_deletions += int(deletions)
                    files_changed += 1

        return {
            "files_changed": files_changed,
            "insertions": total_insertions,
            "deletions": total_deletions,
        }

    except Exception as e:
        logger.warning(
            "failed_to_parse_commit_stats",
            commit_hash=commit_hash,
            error=str(e),
        )
        return {"files_changed": 0, "insertions": 0, "deletions": 0}


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.get("/commits", response_model=CommitListResponse)
async def get_commits(
    request: Request,
    limit: int = Query(50, ge=1, le=100, description="Number of commits to return"),
    offset: int = Query(0, ge=0, description="Number of commits to skip"),
    author: Optional[str] = Query(None, description="Filter by author name or email"),
    since: Optional[str] = Query(None, description="Filter commits since date (ISO 8601)"),
    until: Optional[str] = Query(None, description="Filter commits until date (ISO 8601)"),
) -> CommitListResponse:
    """
    Get commit history with pagination and filtering.

    Returns commits in reverse chronological order (newest first) with:
    - Commit hash (full and short 7-char)
    - Commit message
    - Author information with agent/user detection
    - Timestamp (ISO 8601)
    - File statistics (files changed, insertions, deletions)

    Args:
        request: FastAPI request object (for accessing app.state)
        limit: Number of commits per page (1-100, default: 50)
        offset: Number of commits to skip for pagination (default: 0)
        author: Filter by author name or email (partial match)
        since: Filter commits after this date (ISO 8601 format)
        until: Filter commits before this date (ISO 8601 format)

    Returns:
        CommitListResponse with commits array, total count, and has_more flag

    Raises:
        HTTPException: If git operations fail or repository not found
    """
    try:
        # Get project root from app state
        project_root: Path = request.app.state.project_root

        # Initialize GitManager
        git_manager = GitManager(project_path=project_root)

        # Check if it's a git repository
        if not git_manager.is_git_repo():
            raise HTTPException(
                status_code=404,
                detail="Not a git repository. Initialize git first.",
            )

        # Build git log command with filters
        # Format: %H (full hash) | %h (short hash) | %s (subject) | %an (author name) |
        #         %ae (author email) | %ai (author date ISO 8601)
        cmd = [
            "log",
            "--format=%H|%h|%s|%an|%ae|%ai",
            f"--skip={offset}",
            f"--max-count={limit + 1}",  # +1 to check if there are more
        ]

        # Add author filter
        if author:
            cmd.append(f"--author={author}")

        # Add date filters
        if since:
            cmd.append(f"--since={since}")
        if until:
            cmd.append(f"--until={until}")

        # Execute git log
        try:
            result = git_manager._run_git_command(cmd)
        except subprocess.CalledProcessError as e:
            # No commits yet (empty repo)
            # Git returns exit status 128 for "fatal: your current branch does not have any commits yet"
            error_msg = (e.stderr or "").lower() + (e.stdout or "").lower()
            if "does not have any commits yet" in error_msg or "bad default revision" in error_msg:
                return CommitListResponse(commits=[], total=0, has_more=False)
            raise

        # Parse commit output
        lines = [line for line in result.strip().split("\n") if line]

        # Check if there are more commits
        has_more = len(lines) > limit
        if has_more:
            lines = lines[:limit]

        commits = []
        for line in lines:
            parts = line.split("|", 5)
            if len(parts) != 6:
                logger.warning("invalid_commit_line", line=line)
                continue

            full_hash, short_hash, message, author_name, author_email, timestamp = parts

            # Get commit statistics
            stats = _parse_commit_stats(git_manager, full_hash)

            # Build commit info
            commit_info = CommitInfo(
                hash=full_hash,
                short_hash=short_hash,
                message=message,
                author=CommitAuthor(
                    name=author_name,
                    email=author_email,
                    is_agent=_is_agent_commit(author_email),
                ),
                timestamp=timestamp,
                files_changed=stats["files_changed"],
                insertions=stats["insertions"],
                deletions=stats["deletions"],
            )

            commits.append(commit_info)

        # Get total count (approximate - full count would be expensive)
        # For now, use has_more to indicate if there are more commits
        # Frontend can use infinite scroll
        total = offset + len(commits)
        if has_more:
            total += 1  # Indicate there's at least one more

        logger.info(
            "retrieved_commit_history",
            count=len(commits),
            offset=offset,
            limit=limit,
            has_more=has_more,
        )

        return CommitListResponse(
            commits=commits,
            total=total,
            has_more=has_more,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_commits_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get commit history: {str(e)}",
        )


@router.get("/commits/{commit_hash}/diff", response_model=CommitDiffResponse)
async def get_commit_diff(
    request: Request,
    commit_hash: str,
) -> CommitDiffResponse:
    """
    Get diff for a specific commit.

    Returns all files changed in the commit with:
    - Change type (added, modified, deleted)
    - Insertions and deletions count
    - Binary file detection
    - Full diff patch
    - Original and modified file contents (for Monaco diff editor)

    Args:
        request: FastAPI request object (for accessing app.state)
        commit_hash: Full or short commit SHA

    Returns:
        CommitDiffResponse with list of file changes

    Raises:
        HTTPException: If commit not found or git operations fail
    """
    try:
        # Get project root from app state
        project_root: Path = request.app.state.project_root

        # Initialize GitManager
        git_manager = GitManager(project_path=project_root)

        # Check if it's a git repository
        if not git_manager.is_git_repo():
            raise HTTPException(
                status_code=404,
                detail="Not a git repository. Initialize git first.",
            )

        # Get commit diff from GitManager
        try:
            files_data = git_manager.get_commit_diff(commit_hash)
        except subprocess.CalledProcessError as e:
            # Commit not found or invalid
            error_msg = (e.stderr or "").lower() + (e.stdout or "").lower()
            if "unknown revision" in error_msg or "bad object" in error_msg:
                raise HTTPException(
                    status_code=404,
                    detail=f"Commit not found: {commit_hash}",
                )
            raise

        # Convert to FileChange models
        files = []
        for file_data in files_data:
            files.append(
                FileChange(
                    path=file_data["path"],
                    change_type=file_data["change_type"],
                    insertions=file_data["insertions"],
                    deletions=file_data["deletions"],
                    is_binary=file_data["is_binary"],
                    diff=file_data["diff"] if not file_data["is_binary"] else None,
                    original_content=(
                        file_data["original_content"] if not file_data["is_binary"] else None
                    ),
                    modified_content=(
                        file_data["modified_content"] if not file_data["is_binary"] else None
                    ),
                )
            )

        logger.info(
            "retrieved_commit_diff",
            commit_hash=commit_hash,
            files_count=len(files),
        )

        return CommitDiffResponse(files=files)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_commit_diff_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get commit diff: {str(e)}",
        )
