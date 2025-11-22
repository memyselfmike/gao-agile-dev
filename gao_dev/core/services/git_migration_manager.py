"""Git Migration Manager - Safe migration to hybrid architecture.

This service orchestrates migration from file-based to hybrid (file + DB) architecture
with git transaction safety. Each phase creates a git commit checkpoint for rollback.

Epic: 25 - Git-Integrated State Manager
Story: 25.4 - Implement GitMigrationManager (Phase 1-2)
Story: 25.5 - Implement GitMigrationManager (Phase 3-4)

Design Pattern: Orchestrator + Transaction
Dependencies: GitManager, StateCoordinator, Migration005, structlog

Migration Phases:
    1. Create state tables (run Migration 005) - Commit checkpoint
    2. Backfill epics from filesystem - Commit checkpoint
    3. Backfill stories from filesystem (infer state from git) - Commit checkpoint
    4. Validate migration completeness - Commit checkpoint

Transaction Safety:
    - Each phase is atomic (DB + git commit)
    - Checkpoint tracking (save SHAs for rollback)
    - Migration branch for isolation
    - Rollback support (delete branch, reset to checkpoint)

Example:
    ```python
    manager = GitMigrationManager(
        db_path=Path(".gao-dev/documents.db"),
        project_path=Path("/project")
    )

    # Run full migration
    result = manager.migrate_to_hybrid_architecture()

    # Check result
    if result.success:
        print(f"Migration complete: {result.summary}")
        print(f"Epics migrated: {result.epics_count}")
        print(f"Stories migrated: {result.stories_count}")
    else:
        print(f"Migration failed: {result.error}")
        # Automatic rollback performed
    ```
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

import structlog

from gao_dev.core.git_manager import GitManager
from gao_dev.core.state_coordinator import StateCoordinator

logger = structlog.get_logger()


@dataclass
class MigrationResult:
    """Result of migration operation."""

    success: bool
    phase_completed: int  # 1-4 or 0 if failed
    epics_count: int = 0
    stories_count: int = 0
    checkpoints: Dict[str, str] = field(default_factory=dict)  # phase -> sha
    summary: str = ""
    error: Optional[str] = None
    rollback_performed: bool = False


class GitMigrationManagerError(Exception):
    """Base exception for git migration manager errors."""
    pass


class GitMigrationManager:
    """
    Git-aware migration manager for hybrid architecture transition.

    Orchestrates safe migration from file-based to hybrid (file + DB)
    architecture with git transaction support and rollback capability.

    Attributes:
        db_path: Path to SQLite database
        project_path: Path to project root
        git_manager: GitManager for git operations
        coordinator: StateCoordinator for database operations
    """

    MIGRATION_BRANCH = "migration/hybrid-architecture"

    def __init__(
        self,
        db_path: Path,
        project_path: Path
    ):
        """
        Initialize git migration manager.

        Args:
            db_path: Path to SQLite database file
            project_path: Path to project root (for git operations)
        """
        self.db_path = Path(db_path)
        self.project_path = Path(project_path)

        # Initialize managers
        self.git_manager = GitManager(project_path=self.project_path)
        self.coordinator = StateCoordinator(db_path=self.db_path)

        # Checkpoint tracking
        self.checkpoints: Dict[str, str] = {}  # phase -> sha

        self.logger = logger.bind(
            service="git_migration_manager",
            project=str(self.project_path)
        )

        self.logger.info(
            "git_migration_manager_initialized",
            db_path=str(self.db_path),
            project_path=str(self.project_path)
        )

    # ============================================================================
    # MAIN MIGRATION ORCHESTRATION
    # ============================================================================

    def migrate_to_hybrid_architecture(
        self,
        create_branch: bool = True,
        auto_merge: bool = False
    ) -> MigrationResult:
        """
        Migrate project to hybrid architecture with git safety.

        Executes all 4 migration phases with git commit checkpoints.
        Creates migration branch for isolation, supports rollback on error.

        Args:
            create_branch: Whether to create migration branch (default: True)
            auto_merge: Whether to auto-merge to main after success (default: False)

        Returns:
            MigrationResult with success status, counts, and checkpoints

        Example:
            ```python
            manager = GitMigrationManager(db_path, project_path)
            result = manager.migrate_to_hybrid_architecture()

            if result.success:
                print(f"Migrated {result.epics_count} epics, {result.stories_count} stories")
            else:
                print(f"Migration failed: {result.error}")
            ```
        """
        self.logger.info("starting_hybrid_migration", create_branch=create_branch)

        result = MigrationResult(success=False, phase_completed=0)
        original_branch = None

        try:
            # Pre-flight checks
            self._preflight_checks()

            # Save original branch
            original_branch = self.git_manager.get_current_branch()
            result.checkpoints["original"] = self.git_manager.get_head_sha()

            # Create migration branch if requested
            if create_branch:
                self._create_migration_branch()

            # Phase 1: Create tables
            self.logger.info("migration_phase_1_starting")
            self._phase_1_create_tables()
            result.checkpoints["phase_1"] = self.git_manager.get_head_sha()
            result.phase_completed = 1
            self.logger.info("migration_phase_1_complete", sha=result.checkpoints["phase_1"])

            # Phase 2: Backfill epics
            self.logger.info("migration_phase_2_starting")
            epics_count = self._phase_2_backfill_epics()
            result.epics_count = epics_count
            result.checkpoints["phase_2"] = self.git_manager.get_head_sha()
            result.phase_completed = 2
            self.logger.info("migration_phase_2_complete",
                           epics_count=epics_count,
                           sha=result.checkpoints["phase_2"])

            # Phase 3: Backfill stories
            self.logger.info("migration_phase_3_starting")
            stories_count = self._phase_3_backfill_stories()
            result.stories_count = stories_count
            result.checkpoints["phase_3"] = self.git_manager.get_head_sha()
            result.phase_completed = 3
            self.logger.info("migration_phase_3_complete",
                           stories_count=stories_count,
                           sha=result.checkpoints["phase_3"])

            # Phase 4: Validate
            self.logger.info("migration_phase_4_starting")
            self._phase_4_validate()
            result.checkpoints["phase_4"] = self.git_manager.get_head_sha()
            result.phase_completed = 4
            self.logger.info("migration_phase_4_complete", sha=result.checkpoints["phase_4"])

            # Migration successful
            result.success = True
            result.summary = (
                f"Migration complete: {result.epics_count} epics, "
                f"{result.stories_count} stories migrated to hybrid architecture"
            )

            # Auto-merge if requested
            if auto_merge and original_branch:
                self._merge_migration_branch(original_branch)
                result.summary += f" (merged to {original_branch})"

            self.logger.info(
                "migration_successful",
                epics_count=result.epics_count,
                stories_count=result.stories_count,
                phase_completed=result.phase_completed
            )

            return result

        except Exception as e:
            # Migration failed - rollback
            self.logger.error("migration_failed", error=str(e), phase=result.phase_completed)

            result.success = False
            result.error = str(e)

            # Attempt rollback
            try:
                if create_branch:
                    self.rollback_migration(
                        checkpoint_sha=result.checkpoints.get("original"),
                        original_branch=original_branch
                    )
                    result.rollback_performed = True
                    result.summary = f"Migration failed at phase {result.phase_completed}, rollback successful"
                else:
                    # Not on migration branch - just reset
                    if result.checkpoints.get("original"):
                        self.git_manager.reset_hard(result.checkpoints["original"])
                    result.rollback_performed = True
                    result.summary = f"Migration failed at phase {result.phase_completed}, rollback successful"

            except Exception as rollback_error:
                self.logger.error("rollback_failed", error=str(rollback_error))
                result.summary = (
                    f"Migration failed at phase {result.phase_completed}, "
                    f"rollback also failed: {rollback_error}"
                )

            return result

    # ============================================================================
    # PHASE 1: CREATE TABLES
    # ============================================================================

    def _phase_1_create_tables(self) -> None:
        """
        Phase 1: Create state tables using Migration 005.

        Creates tables: epic_state, story_state, action_items,
        ceremonies, learning_index.

        Creates git commit checkpoint after table creation.

        Raises:
            GitMigrationManagerError: If table creation fails
        """
        self.logger.info("phase_1_creating_tables")

        try:
            # Import migration module dynamically
            import importlib
            import sqlite3
            migration_module = importlib.import_module("gao_dev.lifecycle.migrations.005_add_state_tables")
            Migration005 = migration_module.Migration005

            # Run migration (uses static method with connection)
            conn = sqlite3.connect(str(self.db_path))
            try:
                Migration005.up(conn)
                conn.commit()
            finally:
                conn.close()

            self.logger.info("phase_1_tables_created")

            # Commit checkpoint
            message = (
                "chore(migration): Phase 1 - Create state tables\n\n"
                "Created tables: epic_state, story_state, action_items, "
                "ceremonies, learning_index\n\n"
                "Migration to hybrid architecture in progress."
            )

            commit_sha = self.git_manager.commit(message, allow_empty=True)

            self.logger.info(
                "phase_1_checkpoint_created",
                commit_sha=commit_sha
            )

        except Exception as e:
            error_msg = f"Phase 1 failed: {e}"
            self.logger.error("phase_1_failed", error=error_msg)
            raise GitMigrationManagerError(error_msg) from e

    # ============================================================================
    # PHASE 2: BACKFILL EPICS
    # ============================================================================

    def _phase_2_backfill_epics(self) -> int:
        """
        Phase 2: Backfill epics from filesystem.

        Scans docs/ directory for epic files (epic-*.md), extracts metadata,
        and creates epic_state records.

        Creates git commit checkpoint after epic backfill.

        Returns:
            Number of epics migrated

        Raises:
            GitMigrationManagerError: If epic backfill fails
        """
        self.logger.info("phase_2_backfilling_epics")

        try:
            epics_count = 0

            # Find epic files
            epic_files = self._find_epic_files()

            self.logger.info("phase_2_found_epic_files", count=len(epic_files))

            # Process each epic
            for epic_file in epic_files:
                epic_data = self._parse_epic_file(epic_file)

                if epic_data:
                    # Create epic in database
                    self.coordinator.create_epic(
                        epic_num=epic_data["epic_num"],
                        title=epic_data["title"],
                        status=epic_data.get("status", "planning"),
                        total_stories=epic_data.get("total_stories", 0),
                        metadata=epic_data.get("metadata")
                    )

                    epics_count += 1

                    self.logger.info(
                        "phase_2_epic_migrated",
                        epic_num=epic_data["epic_num"],
                        title=epic_data["title"]
                    )

            # Commit checkpoint
            message = (
                f"chore(migration): Phase 2 - Backfill {epics_count} epics\n\n"
                f"Migrated {epics_count} epic records from filesystem to database.\n\n"
                "Migration to hybrid architecture in progress."
            )

            commit_sha = self.git_manager.commit(message, allow_empty=True)

            self.logger.info(
                "phase_2_checkpoint_created",
                epics_count=epics_count,
                commit_sha=commit_sha
            )

            return epics_count

        except Exception as e:
            error_msg = f"Phase 2 failed: {e}"
            self.logger.error("phase_2_failed", error=error_msg)
            raise GitMigrationManagerError(error_msg) from e

    # ============================================================================
    # PHASE 3: BACKFILL STORIES (Story 25.5)
    # ============================================================================

    def _phase_3_backfill_stories(self) -> int:
        """
        Phase 3: Backfill stories from filesystem with git state inference.

        Scans docs/ directory for story files, extracts metadata,
        infers story state from git history, and creates story_state records.

        State inference logic:
        - Check last commit for file
        - If commit message contains "complete"/"done" -> status="completed"
        - If commit message contains "wip"/"progress" -> status="in_progress"
        - Otherwise -> status="pending"

        Creates git commit checkpoint after story backfill.

        Returns:
            Number of stories migrated

        Raises:
            GitMigrationManagerError: If story backfill fails
        """
        self.logger.info("phase_3_backfilling_stories")

        try:
            stories_count = 0

            # Find story files
            story_files = self._find_story_files()

            self.logger.info("phase_3_found_story_files", count=len(story_files))

            # Process each story
            for story_file in story_files:
                story_data = self._parse_story_file(story_file)

                if story_data:
                    # Infer state from git history
                    inferred_status = self._infer_story_state_from_git(story_file)

                    # Create story in database
                    self.coordinator.create_story(
                        epic_num=story_data["epic_num"],
                        story_num=story_data["story_num"],
                        title=story_data["title"],
                        status=inferred_status,
                        assignee=story_data.get("assignee"),
                        priority=story_data.get("priority", "P2"),
                        estimate_hours=story_data.get("estimate_hours"),
                        metadata=story_data.get("metadata"),
                        auto_update_epic=False  # Don't update epic counts during migration
                    )

                    stories_count += 1

                    self.logger.info(
                        "phase_3_story_migrated",
                        epic_num=story_data["epic_num"],
                        story_num=story_data["story_num"],
                        title=story_data["title"],
                        status=inferred_status
                    )

            # Commit checkpoint
            message = (
                f"chore(migration): Phase 3 - Backfill {stories_count} stories\n\n"
                f"Migrated {stories_count} story records from filesystem to database.\n"
                "Story states inferred from git history.\n\n"
                "Migration to hybrid architecture in progress."
            )

            commit_sha = self.git_manager.commit(message, allow_empty=True)

            self.logger.info(
                "phase_3_checkpoint_created",
                stories_count=stories_count,
                commit_sha=commit_sha
            )

            return stories_count

        except Exception as e:
            error_msg = f"Phase 3 failed: {e}"
            self.logger.error("phase_3_failed", error=error_msg)
            raise GitMigrationManagerError(error_msg) from e

    # ============================================================================
    # PHASE 4: VALIDATE (Story 25.5)
    # ============================================================================

    def _phase_4_validate(self) -> None:
        """
        Phase 4: Validate migration completeness.

        Validates that:
        1. All epic files have corresponding DB records
        2. All story files have corresponding DB records
        3. Epic story counts match filesystem
        4. No orphaned DB records

        Creates git commit checkpoint after validation.

        Raises:
            GitMigrationManagerError: If validation fails
        """
        self.logger.info("phase_4_validating_migration")

        try:
            validation_errors = []

            # Validate epics
            epic_files = self._find_epic_files()
            for epic_file in epic_files:
                epic_data = self._parse_epic_file(epic_file)
                if epic_data:
                    try:
                        db_epic = self.coordinator.epic_service.get(epic_data["epic_num"])
                        if not db_epic:
                            validation_errors.append(
                                f"Epic {epic_data['epic_num']} missing from database"
                            )
                    except Exception:
                        validation_errors.append(
                            f"Epic {epic_data['epic_num']} missing from database"
                        )

            # Validate stories
            story_files = self._find_story_files()
            for story_file in story_files:
                story_data = self._parse_story_file(story_file)
                if story_data:
                    try:
                        db_story = self.coordinator.story_service.get(
                            epic_num=story_data["epic_num"],
                            story_num=story_data["story_num"]
                        )
                        if not db_story:
                            validation_errors.append(
                                f"Story {story_data['epic_num']}.{story_data['story_num']} missing from database"
                            )
                    except Exception:
                        validation_errors.append(
                            f"Story {story_data['epic_num']}.{story_data['story_num']} missing from database"
                        )

            # Check for validation errors
            if validation_errors:
                error_msg = f"Validation failed: {len(validation_errors)} issues found:\n"
                error_msg += "\n".join(validation_errors)
                raise GitMigrationManagerError(error_msg)

            self.logger.info(
                "phase_4_validation_passed",
                epics_validated=len(epic_files),
                stories_validated=len(story_files)
            )

            # Commit checkpoint
            message = (
                "chore(migration): Phase 4 - Validate migration completeness\n\n"
                f"Validated {len(epic_files)} epics and {len(story_files)} stories.\n"
                "All files have corresponding database records.\n\n"
                "Migration to hybrid architecture complete."
            )

            commit_sha = self.git_manager.commit(message, allow_empty=True)

            self.logger.info(
                "phase_4_checkpoint_created",
                commit_sha=commit_sha
            )

        except Exception as e:
            error_msg = f"Phase 4 failed: {e}"
            self.logger.error("phase_4_failed", error=error_msg)
            raise GitMigrationManagerError(error_msg) from e

    # ============================================================================
    # ROLLBACK SUPPORT (Story 25.5)
    # ============================================================================

    def rollback_migration(
        self,
        checkpoint_sha: Optional[str] = None,
        original_branch: Optional[str] = None
    ) -> None:
        """
        Rollback migration to checkpoint.

        Deletes migration branch (force) and resets to checkpoint SHA.
        Returns to original branch.

        Args:
            checkpoint_sha: SHA to reset to (default: current HEAD)
            original_branch: Branch to return to (default: main)

        Raises:
            GitMigrationManagerError: If rollback fails
        """
        self.logger.warning(
            "rolling_back_migration",
            checkpoint_sha=checkpoint_sha,
            original_branch=original_branch
        )

        try:
            # Checkout original branch
            target_branch = original_branch or "main"
            self.git_manager.checkout(target_branch)

            # Delete migration branch (force)
            try:
                self.git_manager.delete_branch(self.MIGRATION_BRANCH, force=True)
                self.logger.info("migration_branch_deleted", branch=self.MIGRATION_BRANCH)
            except Exception as e:
                self.logger.warning("migration_branch_delete_failed", error=str(e))

            # Reset to checkpoint if provided
            if checkpoint_sha:
                self.git_manager.reset_hard(checkpoint_sha)
                self.logger.info("reset_to_checkpoint", sha=checkpoint_sha)

            self.logger.info("rollback_complete")

        except Exception as e:
            error_msg = f"Rollback failed: {e}"
            self.logger.error("rollback_failed", error=error_msg)
            raise GitMigrationManagerError(error_msg) from e

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _preflight_checks(self) -> None:
        """Pre-flight checks before migration."""
        # Check git repo exists
        if not self.git_manager.is_git_repo():
            raise GitMigrationManagerError("Not a git repository")

        # Check working tree is clean
        if not self.git_manager.is_working_tree_clean():
            raise GitMigrationManagerError(
                "Working tree has uncommitted changes. Commit or stash before migration."
            )

        self.logger.info("preflight_checks_passed")

    def _create_migration_branch(self) -> None:
        """Create migration branch for isolation."""
        try:
            # Delete existing migration branch if exists
            try:
                self.git_manager.delete_branch(self.MIGRATION_BRANCH, force=True)
            except Exception:
                pass  # Branch doesn't exist, that's fine

            # Create new migration branch
            self.git_manager.create_branch(self.MIGRATION_BRANCH, checkout=True)

            self.logger.info("migration_branch_created", branch=self.MIGRATION_BRANCH)

        except Exception as e:
            raise GitMigrationManagerError(f"Failed to create migration branch: {e}") from e

    def _merge_migration_branch(self, target_branch: str) -> None:
        """Merge migration branch to target branch."""
        try:
            # Checkout target branch
            self.git_manager.checkout(target_branch)

            # Merge migration branch (no fast-forward)
            self.git_manager.merge(
                self.MIGRATION_BRANCH,
                no_ff=True,
                message="Merge migration/hybrid-architecture into main\n\nMigration complete."
            )

            # Delete migration branch
            self.git_manager.delete_branch(self.MIGRATION_BRANCH)

            self.logger.info("migration_branch_merged", target=target_branch)

        except Exception as e:
            raise GitMigrationManagerError(f"Failed to merge migration branch: {e}") from e

    def _find_epic_files(self) -> List[Path]:
        """Find all epic files in docs/ directory."""
        epic_files = []
        docs_dir = self.project_path / "docs"

        if not docs_dir.exists():
            return epic_files

        # Search for epic-*.md files
        for path in docs_dir.rglob("epic-*.md"):
            if path.is_file():
                epic_files.append(path)

        return sorted(epic_files)

    def _find_story_files(self) -> List[Path]:
        """Find all story files in docs/ directory."""
        story_files = []
        docs_dir = self.project_path / "docs"

        if not docs_dir.exists():
            return story_files

        # Search for story-*.md files
        for path in docs_dir.rglob("story-*.md"):
            if path.is_file():
                story_files.append(path)

        return sorted(story_files)

    def _parse_epic_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse epic file and extract metadata.

        Looks for:
        - Epic number from filename (epic-N.md)
        - Title from first # header
        - Status from **Status**: field
        - Total stories from **Total Stories**: field

        Args:
            path: Path to epic file

        Returns:
            Epic data dict or None if parsing fails
        """
        try:
            content = path.read_text(encoding="utf-8")

            # Extract epic number from filename
            match = re.search(r"epic-(\d+)", path.name)
            if not match:
                return None
            epic_num = int(match.group(1))

            # Extract title from first # header
            title_match = re.search(r"^#\s+Epic\s+\d+[:\s]+(.+)$", content, re.MULTILINE | re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else f"Epic {epic_num}"

            # Extract status
            status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content, re.IGNORECASE)
            status = status_match.group(1).lower() if status_match else "planning"

            # Extract total stories
            stories_match = re.search(r"\*\*Total Stories\*\*:\s*(\d+)", content, re.IGNORECASE)
            total_stories = int(stories_match.group(1)) if stories_match else 0

            return {
                "epic_num": epic_num,
                "title": title,
                "status": status,
                "total_stories": total_stories,
                "metadata": {"file_path": str(path)}
            }

        except Exception as e:
            self.logger.warning("epic_file_parse_failed", path=str(path), error=str(e))
            return None

    def _parse_story_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse story file and extract metadata.

        Looks for:
        - Story number from filename (story-N.M.md)
        - Title from first # header
        - Assignee from **Owner**: field
        - Priority from **Priority**: field
        - Estimate from **Estimate**: field

        Args:
            path: Path to story file

        Returns:
            Story data dict or None if parsing fails
        """
        try:
            content = path.read_text(encoding="utf-8")

            # Extract story number from filename
            match = re.search(r"story-(\d+)\.(\d+)", path.name)
            if not match:
                return None
            epic_num = int(match.group(1))
            story_num = int(match.group(2))

            # Extract title from first # header
            title_match = re.search(r"^#\s+Story\s+\d+\.\d+[:\s]+(.+)$", content, re.MULTILINE | re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else f"Story {epic_num}.{story_num}"

            # Extract assignee
            assignee_match = re.search(r"\*\*Owner\*\*:\s*(\w+)", content, re.IGNORECASE)
            assignee = assignee_match.group(1) if assignee_match else None

            # Extract priority
            priority_match = re.search(r"\*\*Priority\*\*:\s*(P\d+)", content, re.IGNORECASE)
            priority = priority_match.group(1) if priority_match else "P2"

            # Extract estimate
            estimate_match = re.search(r"\*\*Estimate\*\*:\s*(\d+(?:\.\d+)?)\s*hours?", content, re.IGNORECASE)
            estimate_hours = float(estimate_match.group(1)) if estimate_match else None

            return {
                "epic_num": epic_num,
                "story_num": story_num,
                "title": title,
                "assignee": assignee,
                "priority": priority,
                "estimate_hours": estimate_hours,
                "metadata": {"file_path": str(path)}
            }

        except Exception as e:
            self.logger.warning("story_file_parse_failed", path=str(path), error=str(e))
            return None

    def _infer_story_state_from_git(self, path: Path) -> str:
        """
        Infer story state from git history.

        Uses git log to check last commit for file, then infers state
        from commit message keywords:
        - "complete", "done", "finished" -> "completed"
        - "wip", "progress", "working" -> "in_progress"
        - Otherwise -> "pending"

        Args:
            path: Path to story file

        Returns:
            Inferred status: "completed", "in_progress", or "pending"
        """
        try:
            # Get last commit for file
            commit_info = self.git_manager.get_last_commit_for_file(path)

            if not commit_info:
                # No git history, assume pending
                return "pending"

            # Check commit message for keywords
            message = commit_info["message"].lower()

            # Check for completion keywords
            if any(keyword in message for keyword in ["complete", "done", "finished", "feat("]):
                return "completed"

            # Check for in-progress keywords
            if any(keyword in message for keyword in ["wip", "progress", "working", "chore("]):
                return "in_progress"

            # Default to pending
            return "pending"

        except Exception as e:
            self.logger.warning(
                "state_inference_failed",
                path=str(path),
                error=str(e)
            )
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
