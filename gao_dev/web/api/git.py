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


class CommitFilters(BaseModel):
    """Applied filters for commit list."""

    author: Optional[str] = None
    since: Optional[str] = None
    until: Optional[str] = None
    search: Optional[str] = None


class CommitListResponse(BaseModel):
    """Response model for commit list endpoint."""

    commits: List[CommitInfo]
    total: int
    total_unfiltered: int
    has_more: bool
    filters_applied: CommitFilters


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


def _get_agent_emails() -> List[str]:
    """
    Get list of all GAO-Dev agent email addresses.

    Returns:
        List of agent email addresses
    """
    return [
        "brian@gao-dev.local",
        "john@gao-dev.local",
        "winston@gao-dev.local",
        "sally@gao-dev.local",
        "bob@gao-dev.local",
        "amelia@gao-dev.local",
        "murat@gao-dev.local",
        "mary@gao-dev.local",
        "noreply@anthropic.com",  # Claude's email
        "dev@gao-dev.local",  # Generic agent email
    ]


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
    author: Optional[str] = Query(
        None, description="Filter by author: 'all', 'agents', 'user', or specific agent/username"
    ),
    since: Optional[str] = Query(None, description="Filter commits since date (ISO 8601)"),
    until: Optional[str] = Query(None, description="Filter commits until date (ISO 8601)"),
    search: Optional[str] = Query(None, description="Search commit messages"),
) -> CommitListResponse:
    """
    Get commit history with pagination and filtering.

    Returns commits in reverse chronological order (newest first) with:
    - Commit hash (full and short 7-char)
    - Commit message
    - Author information with agent/user detection
    - Timestamp (ISO 8601)
    - File statistics (files changed, insertions, deletions)

    Filtering:
    - author: 'all' (default), 'agents' (all agents), 'user' (non-agents), or specific agent name
    - since/until: ISO 8601 date strings
    - search: Case-insensitive search in commit messages

    Args:
        request: FastAPI request object (for accessing app.state)
        limit: Number of commits per page (1-100, default: 50)
        offset: Number of commits to skip for pagination (default: 0)
        author: Filter by author (all/agents/user/specific)
        since: Filter commits after this date (ISO 8601 format)
        until: Filter commits before this date (ISO 8601 format)
        search: Search term for commit messages

    Returns:
        CommitListResponse with commits, total (filtered), total_unfiltered, has_more, filters_applied

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

        # Parse author filter
        author_filter = None
        if author and author != "all":
            if author == "agents":
                # Filter for all agent commits (OR logic for multiple authors)
                agent_emails = _get_agent_emails()
                # Git --author supports regex, so we'll use OR pattern
                author_filter = "|".join([f"({email})" for email in agent_emails])
            elif author == "user":
                # Filter for non-agent commits (inverse of agents filter)
                # Git doesn't support --not-author, so we need to handle this differently
                # We'll get all commits and filter in Python
                author_filter = "user"  # Special marker
            else:
                # Specific agent or username
                author_filter = author

        # Parse date filters
        since_dt = None
        until_dt = None
        if since:
            try:
                # Handle both Z and +00:00 timezone formats
                normalized_since = since.replace("Z", "+00:00")
                since_dt = datetime.fromisoformat(normalized_since)
            except (ValueError, TypeError) as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid since date: {since}. Error: {str(e)}"
                )
        if until:
            try:
                # Handle both Z and +00:00 timezone formats
                normalized_until = until.replace("Z", "+00:00")
                until_dt = datetime.fromisoformat(normalized_until)
            except (ValueError, TypeError) as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid until date: {until}. Error: {str(e)}"
                )

        # Validate date range
        if since_dt and until_dt and since_dt > until_dt:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before end date",
            )

        # Get filtered commits using GitManager
        # Special handling for "user" filter (need to get all and filter)
        if author_filter == "user":
            # Get all commits and filter in Python
            all_commits = git_manager.get_commit_history(
                limit=limit + offset + 100,  # Get extra to account for filtering
                offset=0,
                since=since_dt,
                until=until_dt,
                message_search=search,
            )

            # Filter out agent commits (use same logic as _is_agent_commit)
            user_commits = [c for c in all_commits if not _is_agent_commit(c["email"])]

            # Apply pagination to filtered results
            commits_data = user_commits[offset : offset + limit]
            total_filtered = len(user_commits)
            has_more = offset + limit < total_filtered
        else:
            # Use GitManager's native filtering
            commits_data = git_manager.get_commit_history(
                limit=limit,
                offset=offset,
                author=author_filter if author_filter and author_filter != "user" else None,
                since=since_dt,
                until=until_dt,
                message_search=search,
            )

            # Get total count with same filters
            total_filtered = git_manager.get_commit_count(
                author=author_filter if author_filter and author_filter != "user" else None,
                since=since_dt,
                until=until_dt,
                message_search=search,
            )
            has_more = offset + len(commits_data) < total_filtered

        # Get unfiltered total
        total_unfiltered = git_manager.get_commit_count()

        # Convert to CommitInfo models
        commits = []
        for commit_data in commits_data:
            # Get commit statistics
            stats = _parse_commit_stats(git_manager, commit_data["full_sha"])

            commit_info = CommitInfo(
                hash=commit_data["full_sha"],
                short_hash=commit_data["sha"],
                message=commit_data["message"],
                author=CommitAuthor(
                    name=commit_data["author"],
                    email=commit_data["email"],
                    is_agent=_is_agent_commit(commit_data["email"]),
                ),
                timestamp=commit_data["date"],
                files_changed=stats["files_changed"],
                insertions=stats["insertions"],
                deletions=stats["deletions"],
            )

            commits.append(commit_info)

        logger.info(
            "retrieved_commit_history",
            count=len(commits),
            offset=offset,
            limit=limit,
            total_filtered=total_filtered,
            total_unfiltered=total_unfiltered,
            has_more=has_more,
            filters_applied=bool(author or since or until or search),
        )

        return CommitListResponse(
            commits=commits,
            total=total_filtered,
            total_unfiltered=total_unfiltered,
            has_more=has_more,
            filters_applied=CommitFilters(
                author=author,
                since=since,
                until=until,
                search=search,
            ),
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
