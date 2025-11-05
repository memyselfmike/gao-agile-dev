"""Markdown-SQLite bidirectional syncer.

Provides bidirectional synchronization between markdown story files and
SQLite database with intelligent conflict detection and resolution.
"""

import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field

from .state_tracker import StateTracker
from .frontmatter_parser import FrontmatterParser
from .models import Story
from .exceptions import SyncError, ConflictError, RecordNotFoundError


@dataclass
class SyncReport:
    """Report of sync operation results.

    Tracks the outcome of batch sync operations including counts of
    files processed, stories created/updated, and any errors encountered.

    Attributes:
        files_processed: Total number of files processed
        stories_created: Number of new stories created in database
        stories_updated: Number of existing stories updated
        files_skipped: Number of files skipped (no changes detected)
        errors: List of error messages encountered
    """

    files_processed: int = 0
    stories_created: int = 0
    stories_updated: int = 0
    files_skipped: int = 0
    errors: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Return formatted string representation of sync report."""
        return (
            f"Sync Report:\n"
            f"  Files processed: {self.files_processed}\n"
            f"  Stories created: {self.stories_created}\n"
            f"  Stories updated: {self.stories_updated}\n"
            f"  Files skipped: {self.files_skipped}\n"
            f"  Errors: {len(self.errors)}"
        )


class ConflictResolution:
    """Conflict resolution strategy constants.

    Defines the available strategies for resolving conflicts between
    markdown files and database when both have been modified.
    """

    DATABASE_WINS = "database_wins"
    MARKDOWN_WINS = "markdown_wins"
    MANUAL = "manual"


class MarkdownSyncer:
    """Bidirectional sync between markdown files and SQLite database.

    Maintains consistency between human-readable markdown story files and
    machine-queryable database with intelligent conflict detection and
    resolution. Preserves "markdown as source of truth" for content while
    using database for structured queries and state tracking.

    Attributes:
        state_tracker: StateTracker instance for database access
        conflict_strategy: Conflict resolution strategy to use
        parser: FrontmatterParser for YAML frontmatter handling
        conflict_log_path: Path to conflict log file

    Example:
        >>> tracker = StateTracker(Path("state.db"))
        >>> syncer = MarkdownSyncer(tracker)
        >>> result = syncer.sync_from_markdown(Path("story-1.1.md"))
        >>> result['status']
        'created'
    """

    def __init__(
        self,
        state_tracker: StateTracker,
        conflict_strategy: str = ConflictResolution.DATABASE_WINS,
    ):
        """Initialize MarkdownSyncer.

        Args:
            state_tracker: StateTracker instance for database access
            conflict_strategy: Conflict resolution strategy
                (database_wins, markdown_wins, manual)
        """
        self.state_tracker = state_tracker
        self.conflict_strategy = conflict_strategy
        self.parser = FrontmatterParser()
        self.conflict_log_path = Path("gao_dev/logs/sync_conflicts.log")
        self.conflict_log_path.parent.mkdir(parents=True, exist_ok=True)

    def sync_from_markdown(self, file_path: Path) -> Dict[str, Any]:
        """Sync markdown file to database.

        Parses markdown file, extracts frontmatter and calculates content hash,
        then creates or updates the corresponding story in the database.
        Handles conflict detection when both markdown and database have changed.

        Args:
            file_path: Path to markdown file

        Returns:
            Sync result dict with status and details:
                - status: 'created', 'updated', or 'skipped'
                - epic: Epic number
                - story: Story number
                - reason: Reason for skip (if applicable)

        Raises:
            SyncError: If sync fails due to missing epic/story_num or parsing error
        """
        try:
            # Parse markdown file
            content = file_path.read_text(encoding="utf-8")
            frontmatter, body = self.parser.parse(content)

            # Calculate content hash
            content_hash = self._calculate_hash(content)

            # Extract story metadata
            epic_num = frontmatter.get("epic")
            story_num = frontmatter.get("story_num")

            if not epic_num or not story_num:
                raise SyncError(
                    f"Missing epic or story_num in frontmatter: {file_path}"
                )

            # Check if story exists in database
            try:
                existing_story = self.state_tracker.get_story(epic_num, story_num)

                # Check if content changed
                if existing_story.content_hash == content_hash:
                    return {
                        "status": "skipped",
                        "reason": "no_changes",
                        "epic": epic_num,
                        "story": story_num,
                    }

                # Detect conflicts
                conflicts = self._detect_conflicts(existing_story, frontmatter)
                if conflicts:
                    self._handle_conflicts(conflicts, file_path)

                # Update story
                self._update_story_from_frontmatter(
                    epic_num, story_num, frontmatter, content_hash
                )
                return {"status": "updated", "epic": epic_num, "story": story_num}

            except RecordNotFoundError:
                # Create new story
                self._create_story_from_frontmatter(
                    epic_num, story_num, frontmatter, content_hash, file_path
                )
                return {"status": "created", "epic": epic_num, "story": story_num}

        except Exception as e:
            raise SyncError(f"Failed to sync {file_path}: {e}") from e

    def sync_to_markdown(
        self, epic_num: int, story_num: int, file_path: Optional[Path] = None
    ) -> Path:
        """Sync database story to markdown file.

        Reads story from database and writes/updates the corresponding markdown
        file. Preserves the content body while updating frontmatter with current
        database state. Creates backup before overwriting existing files.

        Args:
            epic_num: Epic number
            story_num: Story number
            file_path: Target file path (optional, auto-resolved if None)

        Returns:
            Path to synced markdown file

        Raises:
            SyncError: If sync fails
        """
        try:
            # Get story from database
            story = self.state_tracker.get_story(epic_num, story_num)

            # Resolve file path
            if file_path is None:
                file_path = self._resolve_story_path(epic_num, story_num)

            # Read existing content if file exists
            if file_path.exists():
                # Create backup
                backup_path = file_path.with_suffix(".md.bak")
                shutil.copy2(file_path, backup_path)

                # Parse existing content to preserve body
                existing_content = file_path.read_text(encoding="utf-8")
                _, body = self.parser.parse(existing_content)
            else:
                # Generate default body for new file
                body = self._generate_default_body(story)

            # Generate updated frontmatter from database
            frontmatter = self._story_to_frontmatter(story)

            # Regenerate markdown
            updated_content = self.parser.serialize(frontmatter, body)

            # Write to file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(updated_content, encoding="utf-8")

            return file_path

        except Exception as e:
            raise SyncError(
                f"Failed to sync story {epic_num}.{story_num} to markdown: {e}"
            ) from e

    def sync_directory(
        self, dir_path: Path, recursive: bool = True, pattern: str = "*.md"
    ) -> SyncReport:
        """Batch sync directory of markdown files.

        Processes all markdown files in a directory, syncing each to the
        database. Continues processing even if individual files fail,
        collecting all errors in the report.

        Args:
            dir_path: Directory to sync
            recursive: Recursively sync subdirectories (default: True)
            pattern: File pattern to match (default: '*.md')

        Returns:
            SyncReport with operation results and error details

        Example:
            >>> syncer = MarkdownSyncer(tracker)
            >>> report = syncer.sync_directory(Path("docs/stories"))
            >>> print(f"Created {report.stories_created} stories")
        """
        report = SyncReport()

        # Find all markdown files
        if recursive:
            files = dir_path.rglob(pattern)
        else:
            files = dir_path.glob(pattern)

        for file_path in files:
            report.files_processed += 1

            try:
                result = self.sync_from_markdown(file_path)

                if result["status"] == "created":
                    report.stories_created += 1
                elif result["status"] == "updated":
                    report.stories_updated += 1
                elif result["status"] == "skipped":
                    report.files_skipped += 1

            except Exception as e:
                error_msg = f"{file_path}: {str(e)}"
                report.errors.append(error_msg)
                # Continue processing other files

        return report

    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content.

        Args:
            content: Content to hash

        Returns:
            Hex-encoded SHA256 hash
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _detect_conflicts(
        self, db_story: Story, md_frontmatter: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect conflicts between database and markdown.

        Compares key fields between database story and markdown frontmatter
        to identify conflicts that need resolution.

        Args:
            db_story: Story from database
            md_frontmatter: Frontmatter from markdown file

        Returns:
            List of conflict dicts with field, db_value, md_value
        """
        conflicts = []

        # Check status
        md_status = md_frontmatter.get("status")
        if md_status and db_story.status != md_status:
            conflicts.append(
                {
                    "field": "status",
                    "db_value": db_story.status,
                    "md_value": md_status,
                }
            )

        # Check owner
        md_owner = md_frontmatter.get("owner")
        if md_owner and db_story.owner != md_owner:
            conflicts.append(
                {"field": "owner", "db_value": db_story.owner, "md_value": md_owner}
            )

        # Check points
        md_points = md_frontmatter.get("points")
        if md_points is not None and db_story.points != md_points:
            conflicts.append(
                {
                    "field": "points",
                    "db_value": db_story.points,
                    "md_value": md_points,
                }
            )

        # Check priority
        md_priority = md_frontmatter.get("priority")
        if md_priority and db_story.priority != md_priority:
            conflicts.append(
                {
                    "field": "priority",
                    "db_value": db_story.priority,
                    "md_value": md_priority,
                }
            )

        return conflicts

    def _handle_conflicts(
        self, conflicts: List[Dict[str, Any]], file_path: Path
    ) -> None:
        """Handle conflicts based on resolution strategy.

        Args:
            conflicts: List of detected conflicts
            file_path: Path to markdown file with conflicts

        Raises:
            ConflictError: If manual resolution required
        """
        if self.conflict_strategy == ConflictResolution.MANUAL:
            raise ConflictError(
                f"Manual conflict resolution required for {file_path}:\n"
                + "\n".join(
                    f"  - {c['field']}: DB={c['db_value']}, MD={c['md_value']}"
                    for c in conflicts
                )
            )

        # Log conflicts regardless of strategy
        self._log_conflicts(conflicts, file_path)

        # For database_wins or markdown_wins, conflicts are handled
        # in _update_story_from_frontmatter

    def _log_conflicts(
        self, conflicts: List[Dict[str, Any]], file_path: Path
    ) -> None:
        """Log conflicts to conflict log file.

        Args:
            conflicts: List of detected conflicts
            file_path: Path to markdown file with conflicts
        """
        with open(self.conflict_log_path, "a", encoding="utf-8") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"\n[{timestamp}] Conflicts in {file_path}:\n")
            for conflict in conflicts:
                f.write(
                    f"  - {conflict['field']}: "
                    f"DB={conflict['db_value']}, MD={conflict['md_value']}\n"
                )

    def _update_story_from_frontmatter(
        self,
        epic_num: int,
        story_num: int,
        frontmatter: Dict[str, Any],
        content_hash: str,
    ) -> None:
        """Update story in database from frontmatter.

        Applies conflict resolution strategy when updating:
        - database_wins: Keep database values, only update hash
        - markdown_wins: Update all fields from markdown

        Args:
            epic_num: Epic number
            story_num: Story number
            frontmatter: Frontmatter dictionary from markdown
            content_hash: SHA256 hash of content
        """
        # Apply conflict resolution strategy
        if self.conflict_strategy == ConflictResolution.MARKDOWN_WINS:
            # Update all fields from markdown
            if "status" in frontmatter:
                self.state_tracker.update_story_status(
                    epic_num, story_num, frontmatter["status"]
                )
            if "owner" in frontmatter:
                self.state_tracker.update_story_owner(
                    epic_num, story_num, frontmatter["owner"]
                )
            if "points" in frontmatter:
                self.state_tracker.update_story_points(
                    epic_num, story_num, frontmatter["points"]
                )

        # Always update content hash
        self.state_tracker.update_story_hash(epic_num, story_num, content_hash)

    def _create_story_from_frontmatter(
        self,
        epic_num: int,
        story_num: int,
        frontmatter: Dict[str, Any],
        content_hash: str,
        file_path: Path,
    ) -> None:
        """Create new story in database from frontmatter.

        Args:
            epic_num: Epic number
            story_num: Story number
            frontmatter: Frontmatter dictionary from markdown
            content_hash: SHA256 hash of content
            file_path: Path to markdown file
        """
        self.state_tracker.create_story(
            epic_num=epic_num,
            story_num=story_num,
            title=frontmatter.get("title", file_path.stem),
            status=frontmatter.get("status", "pending"),
            owner=frontmatter.get("owner"),
            points=frontmatter.get("points", 0),
            priority=frontmatter.get("priority", "P1"),
            sprint=frontmatter.get("sprint"),
            content_hash=content_hash,
        )

    def _story_to_frontmatter(self, story: Story) -> Dict[str, Any]:
        """Convert Story model to frontmatter dict.

        Args:
            story: Story instance from database

        Returns:
            Dictionary suitable for YAML frontmatter
        """
        frontmatter = {
            "epic": story.epic,
            "story_num": story.story_num,
            "title": story.title,
            "status": story.status,
            "priority": story.priority,
            "points": story.points,
        }

        # Add optional fields if present
        if story.owner:
            frontmatter["owner"] = story.owner
        if story.sprint:
            frontmatter["sprint"] = story.sprint

        # Add timestamps for reference
        frontmatter["updated_at"] = story.updated_at

        return frontmatter

    def _resolve_story_path(self, epic_num: int, story_num: int) -> Path:
        """Resolve file path for story.

        Uses standard GAO-Dev path convention:
        docs/features/stories/epic-<N>/story-<N>.<M>.md

        Args:
            epic_num: Epic number
            story_num: Story number

        Returns:
            Resolved Path object
        """
        return Path(
            f"docs/features/stories/epic-{epic_num}/story-{epic_num}.{story_num}.md"
        )

    def _generate_default_body(self, story: Story) -> str:
        """Generate default markdown body for new story.

        Creates a standard story template with sections for description,
        acceptance criteria, technical notes, and definition of done.

        Args:
            story: Story instance

        Returns:
            Markdown content body string
        """
        return f"""## Story Description

[Story description for {story.title}]

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Notes

[Technical implementation notes]

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
"""
