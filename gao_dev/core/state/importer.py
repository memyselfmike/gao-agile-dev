"""Data importer for existing sprint-status.yaml and story markdown files.

Provides one-time migration from file-based state tracking to database-backed
state tracking with validation, rollback, and idempotent operations.
"""

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

import yaml

from .state_tracker import StateTracker
from .markdown_syncer import MarkdownSyncer


@dataclass
class ImportReport:
    """Report of import operation results.

    Tracks counts of imported records, errors, and validation results.

    Attributes:
        epics_created: Number of epics created
        stories_created: Number of stories created
        sprints_created: Number of sprints created
        errors: List of error messages
        warnings: List of warning messages
        validation_errors: List of validation errors
        skipped: Number of items skipped
        duration_seconds: Import duration in seconds
    """

    epics_created: int = 0
    stories_created: int = 0
    sprints_created: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    skipped: int = 0
    duration_seconds: float = 0.0

    def __str__(self) -> str:
        """Return formatted string representation."""
        return (
            f"Import Report:\n"
            f"  Epics created: {self.epics_created}\n"
            f"  Stories created: {self.stories_created}\n"
            f"  Sprints created: {self.sprints_created}\n"
            f"  Skipped: {self.skipped}\n"
            f"  Errors: {len(self.errors)}\n"
            f"  Warnings: {len(self.warnings)}\n"
            f"  Validation errors: {len(self.validation_errors)}\n"
            f"  Duration: {self.duration_seconds:.2f}s"
        )


class StateImporter:
    """Import existing state data into database.

    Handles migration from file-based state tracking (sprint-status.yaml
    and markdown files) to database-backed state tracking with validation,
    duplicate detection, and rollback capability.

    Attributes:
        state_tracker: StateTracker instance for database access
        syncer: MarkdownSyncer for story file synchronization
        dry_run: If True, preview changes without committing

    Example:
        >>> tracker = StateTracker(Path("state.db"))
        >>> importer = StateImporter(tracker)
        >>> report = importer.import_sprint_status(Path("docs/sprint-status.yaml"))
        >>> print(report)
    """

    def __init__(
        self, state_tracker: StateTracker, dry_run: bool = False
    ):
        """Initialize StateImporter.

        Args:
            state_tracker: StateTracker instance for database access
            dry_run: If True, preview without committing to database
        """
        self.state_tracker = state_tracker
        self.syncer = MarkdownSyncer(state_tracker)
        self.dry_run = dry_run
        self.backup_path: Optional[Path] = None

    def import_sprint_status(
        self, sprint_status_path: Path
    ) -> ImportReport:
        """Import sprint-status.yaml into database.

        Parses sprint-status.yaml and imports epics, stories, and sprint
        assignments. Validates data consistency and detects duplicates.

        Args:
            sprint_status_path: Path to sprint-status.yaml file

        Returns:
            ImportReport with operation results

        Example:
            >>> report = importer.import_sprint_status(
            ...     Path("docs/sprint-status.yaml")
            ... )
            >>> print(f"Created {report.epics_created} epics")
        """
        report = ImportReport()
        start_time = datetime.now()

        try:
            # Load YAML file
            if not sprint_status_path.exists():
                report.errors.append(f"File not found: {sprint_status_path}")
                return report

            with open(sprint_status_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                report.errors.append("Empty or invalid YAML file")
                return report

            # Extract sprint information
            data.get("sprint_name", "Unknown Sprint")
            start_date = data.get("start_date", datetime.now().date().isoformat())

            # Create sprint if not in dry-run mode
            if not self.dry_run:
                # Calculate end date (2 weeks from start)
                from datetime import timedelta
                start_dt = datetime.fromisoformat(start_date)
                end_dt = start_dt + timedelta(days=14)
                end_date = end_dt.date().isoformat()

                # Find next sprint number
                sprint_num = self._get_next_sprint_number()

                try:
                    self.state_tracker.create_sprint(
                        sprint_num=sprint_num,
                        start_date=start_date,
                        end_date=end_date,
                    )
                    report.sprints_created += 1
                except Exception as e:
                    report.warnings.append(f"Sprint already exists or error: {e}")

            # Process epics
            epics = data.get("epics", [])
            for epic_data in epics:
                epic_result = self._import_epic(epic_data, report)
                if epic_result:
                    report.epics_created += 1

        except Exception as e:
            report.errors.append(f"Failed to import sprint-status.yaml: {e}")

        report.duration_seconds = (datetime.now() - start_time).total_seconds()
        return report

    def import_story_files(
        self, stories_dir: Path, recursive: bool = True
    ) -> ImportReport:
        """Import story markdown files from directory.

        Scans directory for story-*.md files and imports them using
        MarkdownSyncer. Validates frontmatter and detects duplicates.

        Args:
            stories_dir: Directory containing story markdown files
            recursive: If True, recursively scan subdirectories

        Returns:
            ImportReport with operation results

        Example:
            >>> report = importer.import_story_files(
            ...     Path("docs/features/*/stories")
            ... )
        """
        report = ImportReport()
        start_time = datetime.now()

        try:
            # Find all story markdown files
            if recursive:
                files = list(stories_dir.rglob("story-*.md"))
            else:
                files = list(stories_dir.glob("story-*.md"))

            for file_path in files:
                try:
                    # Use MarkdownSyncer to import
                    result = self.syncer.sync_from_markdown(file_path)

                    if result["status"] == "created":
                        report.stories_created += 1
                    elif result["status"] == "skipped":
                        report.skipped += 1

                except Exception as e:
                    report.errors.append(f"{file_path.name}: {str(e)}")

        except Exception as e:
            report.errors.append(f"Failed to import story files: {e}")

        report.duration_seconds = (datetime.now() - start_time).total_seconds()
        return report

    def import_all(
        self,
        sprint_status_path: Path,
        stories_dirs: List[Path],
        create_backup: bool = True,
    ) -> ImportReport:
        """Import all data from sprint-status.yaml and story files.

        Performs complete migration with optional backup and rollback.
        Creates database backup before importing and validates all data.

        Args:
            sprint_status_path: Path to sprint-status.yaml
            stories_dirs: List of directories containing story files
            create_backup: If True, create database backup before import

        Returns:
            ImportReport with comprehensive results

        Example:
            >>> report = importer.import_all(
            ...     Path("docs/sprint-status.yaml"),
            ...     [Path("docs/features")],
            ...     create_backup=True
            ... )
        """
        report = ImportReport()
        start_time = datetime.now()

        try:
            # Create backup if requested
            if create_backup and not self.dry_run:
                self.backup_path = self._create_backup()

            # Import sprint status (epics and sprint)
            sprint_report = self.import_sprint_status(sprint_status_path)
            report.epics_created += sprint_report.epics_created
            report.stories_created += sprint_report.stories_created
            report.sprints_created += sprint_report.sprints_created
            report.errors.extend(sprint_report.errors)
            report.warnings.extend(sprint_report.warnings)

            # Import story files from all directories
            for stories_dir in stories_dirs:
                if stories_dir.exists():
                    stories_report = self.import_story_files(stories_dir)
                    report.stories_created += stories_report.stories_created
                    report.skipped += stories_report.skipped
                    report.errors.extend(stories_report.errors)
                else:
                    report.warnings.append(f"Directory not found: {stories_dir}")

            # Validate imported data
            validation_errors = self._validate_import()
            report.validation_errors.extend(validation_errors)

        except Exception as e:
            report.errors.append(f"Import failed: {e}")

            # Rollback if backup exists
            if self.backup_path and self.backup_path.exists():
                self._rollback()
                report.warnings.append("Rolled back to backup due to errors")

        report.duration_seconds = (datetime.now() - start_time).total_seconds()
        return report

    def _import_epic(
        self, epic_data: Dict[str, Any], report: ImportReport
    ) -> bool:
        """Import single epic from YAML data.

        Args:
            epic_data: Epic data dictionary from YAML
            report: ImportReport to update with results

        Returns:
            True if epic created, False otherwise
        """
        try:
            epic_num = epic_data.get("epic_number")
            name = epic_data.get("name", f"Epic {epic_num}")
            status = epic_data.get("status", "active")

            # Extract feature from name (heuristic)
            feature = self._extract_feature_from_name(name)

            # Calculate total points from stories
            stories = epic_data.get("stories", [])
            total_points = sum(
                self._parse_story_points(s.get("name", "")) for s in stories
            )

            # Count completed stories
            completed_stories = [s for s in stories if s.get("status") == "done"]
            completed_points = sum(
                self._parse_story_points(s.get("name", "")) for s in completed_stories
            )

            if not self.dry_run:
                try:
                    self.state_tracker.create_epic(
                        epic_num=epic_num,
                        title=name,
                        feature=feature,
                        total_points=total_points,
                    )

                    # Update points
                    self.state_tracker.update_epic_points(
                        epic_num, total_points, completed_points
                    )

                    # Update status
                    self.state_tracker.update_epic_status(epic_num, status)

                except Exception as e:
                    report.warnings.append(
                        f"Epic {epic_num} already exists or error: {e}"
                    )
                    return False

            # Import stories for this epic
            for story_data in stories:
                self._import_story_from_yaml(epic_num, story_data, report)

            return True

        except Exception as e:
            report.errors.append(f"Failed to import epic: {e}")
            return False

    def _import_story_from_yaml(
        self, epic_num: int, story_data: Dict[str, Any], report: ImportReport
    ) -> bool:
        """Import single story from YAML data.

        Args:
            epic_num: Epic number
            story_data: Story data dictionary from YAML
            report: ImportReport to update with results

        Returns:
            True if story created, False otherwise
        """
        try:
            story_num = story_data.get("number")
            name = story_data.get("name", f"Story {epic_num}.{story_num}")
            status = story_data.get("status", "pending")
            owner = story_data.get("owner")

            # Parse story points from name (e.g., "Story Name (3 points)")
            points = self._parse_story_points(name)

            if not self.dry_run:
                try:
                    self.state_tracker.create_story(
                        epic_num=epic_num,
                        story_num=story_num,
                        title=name,
                        status=status,
                        owner=owner,
                        points=points,
                    )
                    report.stories_created += 1
                    return True

                except Exception as e:
                    report.warnings.append(
                        f"Story {epic_num}.{story_num} already exists or error: {e}"
                    )
                    return False

        except Exception as e:
            report.errors.append(f"Failed to import story: {e}")
            return False

    def _extract_feature_from_name(self, name: str) -> str:
        """Extract feature name from epic name.

        Args:
            name: Epic name

        Returns:
            Feature name (kebab-case)
        """
        # Convert to lowercase and replace spaces with hyphens
        feature = name.lower()
        feature = re.sub(r"[^a-z0-9\s-]", "", feature)
        feature = re.sub(r"\s+", "-", feature)
        return feature

    def _parse_story_points(self, name: str) -> int:
        """Parse story points from story name.

        Looks for patterns like "(3 points)" or "3pt" in name.

        Args:
            name: Story name

        Returns:
            Story points (0 if not found)
        """
        # Look for "(N points)" or "Npt" pattern
        match = re.search(r"\((\d+)\s*points?\)", name, re.IGNORECASE)
        if match:
            return int(match.group(1))

        match = re.search(r"(\d+)pt", name, re.IGNORECASE)
        if match:
            return int(match.group(1))

        return 0

    def _get_next_sprint_number(self) -> int:
        """Get next available sprint number.

        Returns:
            Next sprint number
        """
        with self.state_tracker._get_connection() as conn:
            cursor = conn.execute("SELECT MAX(sprint_num) as max_num FROM sprints")
            row = cursor.fetchone()
            max_num = row["max_num"] if row["max_num"] else 0
            return max_num + 1

    def _create_backup(self) -> Path:
        """Create backup of database before import.

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.state_tracker.db_path.with_suffix(
            f".backup_{timestamp}.db"
        )

        shutil.copy2(self.state_tracker.db_path, backup_path)
        return backup_path

    def _rollback(self) -> None:
        """Rollback to backup by restoring backup file."""
        if self.backup_path and self.backup_path.exists():
            shutil.copy2(self.backup_path, self.state_tracker.db_path)

    def _validate_import(self) -> List[str]:
        """Validate imported data for consistency.

        Checks:
        - All stories reference valid epics
        - No orphaned records
        - Status values are valid

        Returns:
            List of validation error messages
        """
        errors = []

        try:
            with self.state_tracker._get_connection() as conn:
                # Check for stories without valid epics
                cursor = conn.execute("""
                    SELECT s.epic_num, s.story_num
                    FROM stories s
                    LEFT JOIN epics e ON s.epic_num = e.epic_num
                    WHERE e.epic_num IS NULL
                """)
                orphaned_stories = cursor.fetchall()
                for row in orphaned_stories:
                    errors.append(
                        f"Story {row['epic_num']}.{row['story_num']} "
                        f"references non-existent epic"
                    )

                # Check for invalid story statuses
                cursor = conn.execute("""
                    SELECT epic_num, story_num, status
                    FROM stories
                    WHERE status NOT IN ('pending', 'in_progress', 'done', 'blocked', 'cancelled')
                """)
                invalid_statuses = cursor.fetchall()
                for row in invalid_statuses:
                    errors.append(
                        f"Story {row['epic_num']}.{row['story_num']} "
                        f"has invalid status: {row['status']}"
                    )

                # Check for invalid epic statuses
                cursor = conn.execute("""
                    SELECT epic_num, status
                    FROM epics
                    WHERE status NOT IN ('planned', 'active', 'completed', 'cancelled')
                """)
                invalid_epic_statuses = cursor.fetchall()
                for row in invalid_epic_statuses:
                    errors.append(
                        f"Epic {row['epic_num']} has invalid status: {row['status']}"
                    )

        except Exception as e:
            errors.append(f"Validation failed: {e}")

        return errors

    def cleanup_backup(self) -> None:
        """Remove backup file after successful import."""
        if self.backup_path and self.backup_path.exists():
            self.backup_path.unlink()
            self.backup_path = None
