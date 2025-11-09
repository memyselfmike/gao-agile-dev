"""Git-Aware Consistency Checker - Detect and repair file-database inconsistencies.

This service uses git status and git history to detect inconsistencies between
filesystem and database state, then repairs them by syncing DB to filesystem
(file is source of truth).

Epic: 25 - Git-Integrated State Manager
Story: 25.6 - Implement GitAwareConsistencyChecker

Design Pattern: Service
Dependencies: GitManager, StateCoordinator, structlog

Consistency Checks:
    1. Uncommitted changes (working tree dirty)
    2. Orphaned DB records (file deleted from filesystem)
    3. Unregistered files (file exists but not in DB)
    4. State mismatches (DB state != git-inferred state)

Repair Strategy:
    - File is source of truth
    - Register untracked files
    - Remove orphaned DB records
    - Update stale DB records
    - Atomic commit after repair

Example:
    ```python
    checker = GitAwareConsistencyChecker(
        db_path=Path(".gao-dev/documents.db"),
        project_path=Path("/project")
    )

    # Check consistency
    report = checker.check_consistency()

    if report.has_issues:
        print(f"Found {report.total_issues} issues:")
        print(f"  Orphaned records: {len(report.orphaned_records)}")
        print(f"  Unregistered files: {len(report.unregistered_files)}")

        # Repair issues
        checker.repair(report)
        print("Issues repaired")
    else:
        print("No consistency issues found")
    ```
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import structlog

from gao_dev.core.git_manager import GitManager
from gao_dev.core.state_coordinator import StateCoordinator

logger = structlog.get_logger()


@dataclass
class ConsistencyIssue:
    """Single consistency issue."""

    issue_type: str  # "uncommitted", "orphaned_record", "unregistered_file", "state_mismatch"
    severity: str  # "warning", "error"
    description: str
    file_path: Optional[Path] = None
    epic_num: Optional[int] = None
    story_num: Optional[int] = None
    db_state: Optional[str] = None
    git_state: Optional[str] = None


@dataclass
class ConsistencyReport:
    """Result of consistency check."""

    timestamp: datetime
    has_issues: bool
    total_issues: int
    uncommitted_changes: List[str] = field(default_factory=list)
    orphaned_records: List[ConsistencyIssue] = field(default_factory=list)
    unregistered_files: List[ConsistencyIssue] = field(default_factory=list)
    state_mismatches: List[ConsistencyIssue] = field(default_factory=list)
    all_issues: List[ConsistencyIssue] = field(default_factory=list)

    def __post_init__(self):
        """Calculate total issues after initialization."""
        self.total_issues = (
            len(self.uncommitted_changes)
            + len(self.orphaned_records)
            + len(self.unregistered_files)
            + len(self.state_mismatches)
        )
        self.has_issues = self.total_issues > 0


class GitAwareConsistencyCheckerError(Exception):
    """Base exception for consistency checker errors."""
    pass


class GitAwareConsistencyChecker:
    """
    Git-aware consistency checker for file-database sync validation.

    Detects inconsistencies between filesystem and database state using
    git operations. Repairs issues by treating files as source of truth.

    Attributes:
        db_path: Path to SQLite database
        project_path: Path to project root
        git_manager: GitManager for git operations
        coordinator: StateCoordinator for database operations
    """

    def __init__(
        self,
        db_path: Path,
        project_path: Path
    ):
        """
        Initialize git-aware consistency checker.

        Args:
            db_path: Path to SQLite database file
            project_path: Path to project root (for git operations)
        """
        self.db_path = Path(db_path)
        self.project_path = Path(project_path)

        # Initialize managers
        self.git_manager = GitManager(project_path=self.project_path)
        self.coordinator = StateCoordinator(db_path=self.db_path)

        self.logger = logger.bind(
            service="git_consistency_checker",
            project=str(self.project_path)
        )

        self.logger.info(
            "git_consistency_checker_initialized",
            db_path=str(self.db_path),
            project_path=str(self.project_path)
        )

    # ============================================================================
    # CONSISTENCY CHECKING
    # ============================================================================

    def check_consistency(self) -> ConsistencyReport:
        """
        Check file-database consistency using git awareness.

        Performs 4 types of checks:
        1. Uncommitted changes (warns about dirty working tree)
        2. Orphaned DB records (file deleted from filesystem)
        3. Unregistered files (file exists but not in DB)
        4. State mismatches (DB state != git-inferred state)

        Returns:
            ConsistencyReport with all detected issues

        Example:
            ```python
            checker = GitAwareConsistencyChecker(db_path, project_path)
            report = checker.check_consistency()

            if report.has_issues:
                for issue in report.all_issues:
                    print(f"[{issue.severity}] {issue.description}")
            ```
        """
        self.logger.info("checking_consistency")

        report = ConsistencyReport(
            timestamp=datetime.now(),
            has_issues=False,
        )

        # Check 1: Uncommitted changes
        uncommitted = self._check_uncommitted_changes()
        report.uncommitted_changes = uncommitted

        if uncommitted:
            for file in uncommitted:
                issue = ConsistencyIssue(
                    issue_type="uncommitted",
                    severity="warning",
                    description=f"Uncommitted changes in {file}",
                    file_path=Path(file)
                )
                report.all_issues.append(issue)

        # Check 2: Orphaned DB records
        orphaned = self._check_orphaned_records()
        report.orphaned_records = orphaned
        report.all_issues.extend(orphaned)

        # Check 3: Unregistered files
        unregistered = self._check_unregistered_files()
        report.unregistered_files = unregistered
        report.all_issues.extend(unregistered)

        # Check 4: State mismatches
        mismatches = self._check_state_mismatches()
        report.state_mismatches = mismatches
        report.all_issues.extend(mismatches)

        # Update totals
        report.total_issues = len(report.all_issues)
        report.has_issues = report.total_issues > 0

        self.logger.info(
            "consistency_check_complete",
            total_issues=report.total_issues,
            uncommitted=len(uncommitted),
            orphaned=len(orphaned),
            unregistered=len(unregistered),
            mismatches=len(mismatches)
        )

        return report

    def repair(
        self,
        report: ConsistencyReport,
        create_commit: bool = True
    ) -> None:
        """
        Repair consistency issues (file is source of truth).

        Repairs all issues in the report:
        - Orphaned records: Remove from DB
        - Unregistered files: Register in DB
        - State mismatches: Update DB to match git-inferred state

        Note: Uncommitted changes are NOT repaired (user must commit first).

        Args:
            report: ConsistencyReport from check_consistency()
            create_commit: Whether to create git commit after repair (default: True)

        Raises:
            GitAwareConsistencyCheckerError: If repair fails

        Example:
            ```python
            report = checker.check_consistency()
            if report.has_issues:
                checker.repair(report)
            ```
        """
        self.logger.info("repairing_consistency_issues", total_issues=report.total_issues)

        if not report.has_issues:
            self.logger.info("no_issues_to_repair")
            return

        # Warn about uncommitted changes (cannot repair)
        if report.uncommitted_changes:
            self.logger.warning(
                "uncommitted_changes_present",
                count=len(report.uncommitted_changes),
                message="Commit changes before repairing other issues"
            )

        try:
            # Repair orphaned records
            for issue in report.orphaned_records:
                self._repair_orphaned_record(issue)

            # Repair unregistered files
            for issue in report.unregistered_files:
                self._repair_unregistered_file(issue)

            # Repair state mismatches
            for issue in report.state_mismatches:
                self._repair_state_mismatch(issue)

            # Create commit if requested
            if create_commit:
                message = (
                    f"chore(consistency): repair {report.total_issues} consistency issues\n\n"
                    f"Repaired:\n"
                    f"- Orphaned records: {len(report.orphaned_records)}\n"
                    f"- Unregistered files: {len(report.unregistered_files)}\n"
                    f"- State mismatches: {len(report.state_mismatches)}\n"
                )

                self.git_manager.commit(message, allow_empty=True)

            self.logger.info(
                "consistency_repair_complete",
                orphaned_repaired=len(report.orphaned_records),
                unregistered_repaired=len(report.unregistered_files),
                mismatches_repaired=len(report.state_mismatches)
            )

        except Exception as e:
            error_msg = f"Consistency repair failed: {e}"
            self.logger.error("repair_failed", error=error_msg)
            raise GitAwareConsistencyCheckerError(error_msg) from e

    # ============================================================================
    # CHECK IMPLEMENTATIONS
    # ============================================================================

    def _check_uncommitted_changes(self) -> List[str]:
        """
        Check for uncommitted changes in working tree.

        Returns:
            List of file paths with uncommitted changes
        """
        try:
            status = self.git_manager.get_status()

            uncommitted_files = []
            uncommitted_files.extend(status["staged_files"])
            uncommitted_files.extend(status["unstaged_files"])
            uncommitted_files.extend(status["untracked_files"])

            if uncommitted_files:
                self.logger.warning(
                    "uncommitted_changes_detected",
                    count=len(uncommitted_files)
                )

            return uncommitted_files

        except Exception as e:
            self.logger.error("check_uncommitted_failed", error=str(e))
            return []

    def _check_orphaned_records(self) -> List[ConsistencyIssue]:
        """
        Check for orphaned DB records (file deleted from filesystem).

        Returns:
            List of ConsistencyIssue for orphaned records
        """
        issues = []

        try:
            # Check epics
            epics = self.coordinator.epic_service.list()

            for epic in epics:
                file_path = epic.get("metadata", {}).get("file_path")

                if file_path:
                    full_path = self.project_path / file_path if not Path(file_path).is_absolute() else Path(file_path)

                    # Check if file exists
                    if not full_path.exists():
                        # Check if file was deleted in git history
                        was_deleted = self.git_manager.file_deleted_in_history(full_path)

                        if was_deleted or not self.git_manager.is_file_tracked(full_path):
                            issues.append(ConsistencyIssue(
                                issue_type="orphaned_record",
                                severity="error",
                                description=f"Epic {epic['epic_num']} file deleted from filesystem",
                                file_path=full_path,
                                epic_num=epic["epic_num"]
                            ))

            # Check stories
            stories = self.coordinator.story_service.list()

            for story in stories:
                file_path = story.get("metadata", {}).get("file_path")

                if file_path:
                    full_path = self.project_path / file_path if not Path(file_path).is_absolute() else Path(file_path)

                    if not full_path.exists():
                        was_deleted = self.git_manager.file_deleted_in_history(full_path)

                        if was_deleted or not self.git_manager.is_file_tracked(full_path):
                            issues.append(ConsistencyIssue(
                                issue_type="orphaned_record",
                                severity="error",
                                description=f"Story {story['epic_num']}.{story['story_num']} file deleted from filesystem",
                                file_path=full_path,
                                epic_num=story["epic_num"],
                                story_num=story["story_num"]
                            ))

            if issues:
                self.logger.warning("orphaned_records_detected", count=len(issues))

            return issues

        except Exception as e:
            self.logger.error("check_orphaned_failed", error=str(e))
            return []

    def _check_unregistered_files(self) -> List[ConsistencyIssue]:
        """
        Check for unregistered files (file exists but not in DB).

        Returns:
            List of ConsistencyIssue for unregistered files
        """
        issues = []

        try:
            # Find all epic files
            docs_dir = self.project_path / "docs"
            if not docs_dir.exists():
                return issues

            # Check epic files
            for epic_file in docs_dir.rglob("epic-*.md"):
                if epic_file.is_file():
                    # Parse epic number from filename
                    import re
                    match = re.search(r"epic-(\d+)", epic_file.name)
                    if match:
                        epic_num = int(match.group(1))

                        # Check if in database
                        try:
                            self.coordinator.epic_service.get(epic_num)
                        except Exception:
                            # Not in database
                            issues.append(ConsistencyIssue(
                                issue_type="unregistered_file",
                                severity="warning",
                                description=f"Epic file {epic_file.name} not registered in database",
                                file_path=epic_file,
                                epic_num=epic_num
                            ))

            # Check story files
            for story_file in docs_dir.rglob("story-*.md"):
                if story_file.is_file():
                    # Parse story number from filename
                    import re
                    match = re.search(r"story-(\d+)\.(\d+)", story_file.name)
                    if match:
                        epic_num = int(match.group(1))
                        story_num = int(match.group(2))

                        # Check if in database
                        try:
                            self.coordinator.story_service.get(epic_num, story_num)
                        except Exception:
                            # Not in database
                            issues.append(ConsistencyIssue(
                                issue_type="unregistered_file",
                                severity="warning",
                                description=f"Story file {story_file.name} not registered in database",
                                file_path=story_file,
                                epic_num=epic_num,
                                story_num=story_num
                            ))

            if issues:
                self.logger.warning("unregistered_files_detected", count=len(issues))

            return issues

        except Exception as e:
            self.logger.error("check_unregistered_failed", error=str(e))
            return []

    def _check_state_mismatches(self) -> List[ConsistencyIssue]:
        """
        Check for state mismatches (DB state != git-inferred state).

        Returns:
            List of ConsistencyIssue for state mismatches
        """
        issues = []

        try:
            # Check story states
            stories = self.coordinator.story_service.list()

            for story in stories:
                file_path = story.get("metadata", {}).get("file_path")

                if file_path:
                    full_path = self.project_path / file_path if not Path(file_path).is_absolute() else Path(file_path)

                    if full_path.exists():
                        # Infer state from git
                        git_state = self._infer_state_from_git(full_path)
                        db_state = story["status"]

                        # Check for mismatch
                        if git_state != db_state:
                            issues.append(ConsistencyIssue(
                                issue_type="state_mismatch",
                                severity="warning",
                                description=f"Story {story['epic_num']}.{story['story_num']} state mismatch",
                                file_path=full_path,
                                epic_num=story["epic_num"],
                                story_num=story["story_num"],
                                db_state=db_state,
                                git_state=git_state
                            ))

            if issues:
                self.logger.warning("state_mismatches_detected", count=len(issues))

            return issues

        except Exception as e:
            self.logger.error("check_state_mismatches_failed", error=str(e))
            return []

    # ============================================================================
    # REPAIR IMPLEMENTATIONS
    # ============================================================================

    def _repair_orphaned_record(self, issue: ConsistencyIssue) -> None:
        """
        Repair orphaned record by removing from database.

        Args:
            issue: ConsistencyIssue with orphaned record info
        """
        try:
            if issue.story_num is not None:
                # Delete story
                self.coordinator.story_service.delete(
                    epic_num=issue.epic_num,
                    story_num=issue.story_num
                )
                self.logger.info(
                    "orphaned_story_removed",
                    epic_num=issue.epic_num,
                    story_num=issue.story_num
                )
            elif issue.epic_num is not None:
                # Delete epic
                self.coordinator.epic_service.delete(epic_num=issue.epic_num)
                self.logger.info("orphaned_epic_removed", epic_num=issue.epic_num)

        except Exception as e:
            self.logger.error(
                "repair_orphaned_failed",
                issue=issue.description,
                error=str(e)
            )

    def _repair_unregistered_file(self, issue: ConsistencyIssue) -> None:
        """
        Repair unregistered file by registering in database.

        Args:
            issue: ConsistencyIssue with unregistered file info
        """
        try:
            if issue.story_num is not None and issue.file_path:
                # Register story
                content = issue.file_path.read_text(encoding="utf-8")

                # Parse story metadata
                import re

                title_match = re.search(r"^#\s+Story\s+\d+\.\d+[:\s]+(.+)$", content, re.MULTILINE | re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else f"Story {issue.epic_num}.{issue.story_num}"

                # Infer state from git
                git_state = self._infer_state_from_git(issue.file_path)

                self.coordinator.create_story(
                    epic_num=issue.epic_num,
                    story_num=issue.story_num,
                    title=title,
                    status=git_state,
                    metadata={"file_path": str(issue.file_path)}
                )

                self.logger.info(
                    "unregistered_story_added",
                    epic_num=issue.epic_num,
                    story_num=issue.story_num,
                    status=git_state
                )

            elif issue.epic_num is not None and issue.file_path:
                # Register epic
                content = issue.file_path.read_text(encoding="utf-8")

                # Parse epic metadata
                import re

                title_match = re.search(r"^#\s+Epic\s+\d+[:\s]+(.+)$", content, re.MULTILINE | re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else f"Epic {issue.epic_num}"

                self.coordinator.create_epic(
                    epic_num=issue.epic_num,
                    title=title,
                    status="planning",
                    metadata={"file_path": str(issue.file_path)}
                )

                self.logger.info(
                    "unregistered_epic_added",
                    epic_num=issue.epic_num
                )

        except Exception as e:
            self.logger.error(
                "repair_unregistered_failed",
                issue=issue.description,
                error=str(e)
            )

    def _repair_state_mismatch(self, issue: ConsistencyIssue) -> None:
        """
        Repair state mismatch by updating DB to match git state.

        Args:
            issue: ConsistencyIssue with state mismatch info
        """
        try:
            if issue.story_num is not None and issue.git_state:
                # Update story state
                self.coordinator.story_service.transition(
                    epic_num=issue.epic_num,
                    story_num=issue.story_num,
                    new_status=issue.git_state
                )

                self.logger.info(
                    "story_state_updated",
                    epic_num=issue.epic_num,
                    story_num=issue.story_num,
                    old_state=issue.db_state,
                    new_state=issue.git_state
                )

        except Exception as e:
            self.logger.error(
                "repair_state_mismatch_failed",
                issue=issue.description,
                error=str(e)
            )

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _infer_state_from_git(self, path: Path) -> str:
        """
        Infer state from git history (same logic as GitMigrationManager).

        Args:
            path: Path to file

        Returns:
            Inferred status: "completed", "in_progress", or "pending"
        """
        try:
            commit_info = self.git_manager.get_last_commit_for_file(path)

            if not commit_info:
                return "pending"

            message = commit_info["message"].lower()

            # Check for completion keywords
            if any(keyword in message for keyword in ["complete", "done", "finished", "feat("]):
                return "completed"

            # Check for in-progress keywords
            if any(keyword in message for keyword in ["wip", "progress", "working", "chore("]):
                return "in_progress"

            return "pending"

        except Exception:
            return "pending"

    # ============================================================================
    # CONTEXT MANAGEMENT
    # ============================================================================

    def close(self) -> None:
        """Close all connections."""
        self.coordinator.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close all connections."""
        self.close()
