# Story 15.3 (ENHANCED): Markdown-SQLite Syncer

**Epic:** 15 - State Tracking Database
**Story Points:** 6
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Implement bidirectional sync between markdown story files and SQLite database with intelligent conflict detection and resolution. This maintains compatibility with existing markdown-based workflows while enabling powerful SQL queries and analytics. The syncer preserves the "markdown as source of truth" principle for content while using the database for structured queries and state tracking.

---

## Business Value

This story bridges the gap between human-readable markdown files and machine-queryable database, delivering critical capabilities:

- **Backward Compatibility**: Existing markdown workflows continue to work seamlessly
- **Query Power**: Enables SQL queries for filtering, aggregation, and reporting without parsing files
- **Performance**: Database queries 100x faster than grepping markdown files
- **Consistency**: Single source of truth maintained through bidirectional sync
- **Conflict Resolution**: Intelligent merge strategies prevent data loss
- **Audit Trail**: Content hash tracking detects and logs all changes
- **Batch Operations**: Sync entire feature directories efficiently
- **Developer Experience**: Developers can edit markdown files directly with IDE
- **Agent Integration**: Agents query database for fast state access, write to markdown for human review
- **Migration Path**: Smooth transition from pure markdown to hybrid markdown+database architecture

---

## Acceptance Criteria

### Sync From Markdown
- [ ] `sync_from_markdown(file_path)` parses markdown and updates database
- [ ] Frontmatter parsing extracts: status, owner, points, priority, epic, story_num, sprint
- [ ] Content hash (SHA256) calculated for change detection
- [ ] Story creation if not exists in database
- [ ] Story update if exists and hash changed
- [ ] Batch sync for directory: `sync_directory(dir_path, recursive=True)`
- [ ] Missing files handled gracefully (log warning, continue)
- [ ] Invalid frontmatter handled gracefully (skip file, log error)
- [ ] Returns sync report: files processed, created, updated, skipped, errors

### Sync To Markdown
- [ ] `sync_to_markdown(epic, story)` writes database state to markdown file
- [ ] Frontmatter regenerated with current metadata from database
- [ ] Content body preserved (not overwritten, only frontmatter updated)
- [ ] File formatting preserved (line endings, spacing, indentation)
- [ ] Backup created before overwrite: `.story.md.bak`
- [ ] File path resolved from story metadata
- [ ] New file created if doesn't exist
- [ ] Frontmatter validates against schema before writing

### Conflict Detection
- [ ] Content hash comparison detects changes
- [ ] Three-way merge detection: database, markdown, last-synced
- [ ] Conflict resolution strategy configurable: `database_wins`, `markdown_wins`, `manual`
- [ ] Default strategy: database wins for status/metadata, markdown wins for content body
- [ ] Conflict log written to: `gao_dev/logs/sync_conflicts.log`
- [ ] Conflict contains: file path, field, database value, markdown value, timestamp
- [ ] Manual conflicts require user intervention (raise ConflictError)
- [ ] Safe mode: never overwrite without backup

### Sync Triggers
- [ ] Manual: `gao-dev state sync` CLI command
- [ ] Manual: `gao-dev state sync --direction from-markdown` or `to-markdown`
- [ ] On file save (optional, file watcher with watchdog library)
- [ ] On database update (optional, trigger in StateTracker)
- [ ] Scheduled sync (configurable interval, default: disabled)
- [ ] Pre-commit hook integration (validate sync before commit)

### Performance
- [ ] Sync single file completes in <200ms
- [ ] Batch sync 100 files completes in <10 seconds
- [ ] Hash-based change detection (only sync changed files)
- [ ] Parallel processing for batch sync (multiprocessing)
- [ ] File caching reduces repeated reads
- [ ] Database transaction batching for bulk updates

---

## Technical Notes

### Markdown Syncer Implementation

```python
# gao_dev/core/state/markdown_syncer.py
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass, asdict

from .state_tracker import StateTracker
from .frontmatter_parser import FrontmatterParser
from .models import Story
from .exceptions import SyncError, ConflictError

@dataclass
class SyncReport:
    """Report of sync operation results."""
    files_processed: int = 0
    stories_created: int = 0
    stories_updated: int = 0
    files_skipped: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class ConflictResolution:
    """Conflict resolution strategies."""
    DATABASE_WINS = "database_wins"
    MARKDOWN_WINS = "markdown_wins"
    MANUAL = "manual"

class MarkdownSyncer:
    """
    Bidirectional sync between markdown files and SQLite database.

    Maintains consistency between human-readable markdown and machine-queryable
    database with intelligent conflict detection and resolution.
    """

    def __init__(
        self,
        state_tracker: StateTracker,
        conflict_strategy: str = ConflictResolution.DATABASE_WINS
    ):
        """
        Initialize MarkdownSyncer.

        Args:
            state_tracker: StateTracker instance for database access
            conflict_strategy: Conflict resolution strategy
        """
        self.state_tracker = state_tracker
        self.conflict_strategy = conflict_strategy
        self.parser = FrontmatterParser()
        self.conflict_log_path = Path("gao_dev/logs/sync_conflicts.log")
        self.conflict_log_path.parent.mkdir(parents=True, exist_ok=True)

    def sync_from_markdown(self, file_path: Path) -> Dict[str, Any]:
        """
        Sync markdown file to database.

        Args:
            file_path: Path to markdown file

        Returns:
            Sync result dict with status and details

        Raises:
            SyncError: If sync fails
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
                raise SyncError(f"Missing epic or story_num in {file_path}")

            # Check if story exists in database
            try:
                existing_story = self.state_tracker.get_story(epic_num, story_num)

                # Check if content changed
                if existing_story.content_hash == content_hash:
                    return {"status": "skipped", "reason": "no_changes"}

                # Detect conflicts
                conflicts = self._detect_conflicts(existing_story, frontmatter)
                if conflicts:
                    self._handle_conflicts(conflicts, file_path)

                # Update story
                self._update_story_from_frontmatter(epic_num, story_num, frontmatter, content_hash)
                return {"status": "updated", "epic": epic_num, "story": story_num}

            except RecordNotFoundError:
                # Create new story
                self._create_story_from_frontmatter(epic_num, story_num, frontmatter, content_hash, file_path)
                return {"status": "created", "epic": epic_num, "story": story_num}

        except Exception as e:
            raise SyncError(f"Failed to sync {file_path}: {e}") from e

    def sync_to_markdown(self, epic_num: int, story_num: int, file_path: Optional[Path] = None) -> Path:
        """
        Sync database story to markdown file.

        Args:
            epic_num: Epic number
            story_num: Story number
            file_path: Target file path (optional, auto-resolve if None)

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

                # Parse existing content
                existing_content = file_path.read_text(encoding="utf-8")
                _, body = self.parser.parse(existing_content)
            else:
                body = self._generate_default_body(story)

            # Generate updated frontmatter
            frontmatter = self._story_to_frontmatter(story)

            # Regenerate markdown
            updated_content = self.parser.serialize(frontmatter, body)

            # Write to file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(updated_content, encoding="utf-8")

            return file_path

        except Exception as e:
            raise SyncError(f"Failed to sync story {epic_num}.{story_num} to markdown: {e}") from e

    def sync_directory(
        self,
        dir_path: Path,
        recursive: bool = True,
        pattern: str = "*.md"
    ) -> SyncReport:
        """
        Batch sync directory of markdown files.

        Args:
            dir_path: Directory to sync
            recursive: Recursively sync subdirectories
            pattern: File pattern to match

        Returns:
            SyncReport with operation results
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
                print(f"Error syncing {file_path}: {e}")

        return report

    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _detect_conflicts(self, db_story: Story, md_frontmatter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect conflicts between database and markdown.

        Returns:
            List of conflict dicts with field, db_value, md_value
        """
        conflicts = []

        # Check status
        if db_story.status != md_frontmatter.get("status"):
            conflicts.append({
                "field": "status",
                "db_value": db_story.status,
                "md_value": md_frontmatter.get("status")
            })

        # Check owner
        if db_story.owner != md_frontmatter.get("owner"):
            conflicts.append({
                "field": "owner",
                "db_value": db_story.owner,
                "md_value": md_frontmatter.get("owner")
            })

        # Check points
        if db_story.points != md_frontmatter.get("points"):
            conflicts.append({
                "field": "points",
                "db_value": db_story.points,
                "md_value": md_frontmatter.get("points")
            })

        return conflicts

    def _handle_conflicts(self, conflicts: List[Dict[str, Any]], file_path: Path):
        """Handle conflicts based on resolution strategy."""
        if self.conflict_strategy == ConflictResolution.MANUAL:
            raise ConflictError(f"Manual conflict resolution required for {file_path}: {conflicts}")

        # Log conflicts
        self._log_conflicts(conflicts, file_path)

        # Database wins or markdown wins handled in update logic

    def _log_conflicts(self, conflicts: List[Dict[str, Any]], file_path: Path):
        """Log conflicts to conflict log."""
        with open(self.conflict_log_path, "a", encoding="utf-8") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"\n[{timestamp}] Conflicts in {file_path}:\n")
            for conflict in conflicts:
                f.write(f"  - {conflict['field']}: DB={conflict['db_value']}, MD={conflict['md_value']}\n")

    def _update_story_from_frontmatter(
        self,
        epic_num: int,
        story_num: int,
        frontmatter: Dict[str, Any],
        content_hash: str
    ):
        """Update story in database from frontmatter."""
        # Apply conflict resolution strategy
        if self.conflict_strategy == ConflictResolution.MARKDOWN_WINS:
            # Update all fields from markdown
            self.state_tracker.update_story_status(epic_num, story_num, frontmatter.get("status", "pending"))
            if "owner" in frontmatter:
                self.state_tracker.update_story_owner(epic_num, story_num, frontmatter["owner"])
            if "points" in frontmatter:
                self.state_tracker.update_story_points(epic_num, story_num, frontmatter["points"])

        # Always update content hash
        # Note: Requires adding update_story_hash method to StateTracker
        # self.state_tracker.update_story_hash(epic_num, story_num, content_hash)

    def _create_story_from_frontmatter(
        self,
        epic_num: int,
        story_num: int,
        frontmatter: Dict[str, Any],
        content_hash: str,
        file_path: Path
    ):
        """Create new story in database from frontmatter."""
        self.state_tracker.create_story(
            epic_num=epic_num,
            story_num=story_num,
            title=frontmatter.get("title", file_path.stem),
            status=frontmatter.get("status", "pending"),
            owner=frontmatter.get("owner"),
            points=frontmatter.get("points", 0),
            priority=frontmatter.get("priority", "P1"),
            sprint=frontmatter.get("sprint")
        )

    def _story_to_frontmatter(self, story: Story) -> Dict[str, Any]:
        """Convert Story model to frontmatter dict."""
        return {
            "epic": story.epic,
            "story_num": story.story_num,
            "title": story.title,
            "status": story.status,
            "owner": story.owner,
            "points": story.points,
            "priority": story.priority,
            "sprint": story.sprint,
            "updated_at": story.updated_at
        }

    def _resolve_story_path(self, epic_num: int, story_num: int) -> Path:
        """Resolve file path for story."""
        # Standard path: docs/features/<feature>/stories/epic-<N>/story-<N>.<M>.md
        # Simplified: just use epic structure
        return Path(f"docs/features/stories/epic-{epic_num}/story-{epic_num}.{story_num}.md")

    def _generate_default_body(self, story: Story) -> str:
        """Generate default markdown body for new story."""
        return f"""## Story Description

[Story description here]

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Technical Notes

[Technical notes here]

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
"""
```

### Frontmatter Parser Implementation

```python
# gao_dev/core/state/frontmatter_parser.py
import re
from typing import Dict, Any, Tuple
import yaml

class FrontmatterParser:
    """Parse and serialize YAML frontmatter in markdown files."""

    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

    def parse(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse markdown content into frontmatter and body.

        Args:
            content: Markdown file content

        Returns:
            Tuple of (frontmatter dict, body string)
        """
        match = self.FRONTMATTER_PATTERN.match(content)

        if match:
            frontmatter_str = match.group(1)
            body = match.group(2).strip()

            try:
                frontmatter = yaml.safe_load(frontmatter_str)
                if frontmatter is None:
                    frontmatter = {}
            except yaml.YAMLError:
                frontmatter = {}

            return frontmatter, body
        else:
            # No frontmatter found
            return {}, content.strip()

    def serialize(self, frontmatter: Dict[str, Any], body: str) -> str:
        """
        Serialize frontmatter and body into markdown content.

        Args:
            frontmatter: Frontmatter dict
            body: Body string

        Returns:
            Complete markdown content
        """
        frontmatter_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        return f"---\n{frontmatter_str}---\n\n{body}\n"

    def validate_frontmatter(self, frontmatter: Dict[str, Any]) -> bool:
        """
        Validate frontmatter has required fields.

        Args:
            frontmatter: Frontmatter dict

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["epic", "story_num", "title", "status"]
        return all(field in frontmatter for field in required_fields)
```

**Files to Create:**
- `gao_dev/core/state/markdown_syncer.py`
- `gao_dev/core/state/frontmatter_parser.py`
- `gao_dev/core/state/exceptions.py` (add SyncError, ConflictError)
- `tests/core/state/test_markdown_syncer.py`
- `tests/core/state/test_frontmatter_parser.py`

**Dependencies:** Story 15.2 (StateTracker)

---

## Testing Requirements

### Unit Tests

**Frontmatter Parser:**
- [ ] Test `parse()` extracts frontmatter and body correctly
- [ ] Test `parse()` handles missing frontmatter
- [ ] Test `parse()` handles malformed YAML
- [ ] Test `serialize()` generates valid markdown
- [ ] Test `validate_frontmatter()` checks required fields

**Sync From Markdown:**
- [ ] Test sync creates new story if not exists
- [ ] Test sync updates existing story if changed
- [ ] Test sync skips unchanged files (hash match)
- [ ] Test sync handles missing epic/story_num
- [ ] Test sync handles invalid frontmatter
- [ ] Test batch sync processes multiple files
- [ ] Test batch sync continues on errors
- [ ] Test sync report contains correct counts

**Sync To Markdown:**
- [ ] Test sync writes database state to file
- [ ] Test sync preserves content body
- [ ] Test sync updates only frontmatter
- [ ] Test sync creates backup before overwrite
- [ ] Test sync creates new file if doesn't exist
- [ ] Test sync preserves file formatting

**Conflict Detection:**
- [ ] Test detects status conflicts
- [ ] Test detects owner conflicts
- [ ] Test detects points conflicts
- [ ] Test logs conflicts correctly
- [ ] Test database_wins strategy applies DB values
- [ ] Test markdown_wins strategy applies MD values
- [ ] Test manual strategy raises ConflictError

### Integration Tests
- [ ] Create markdown file, sync to DB, verify data
- [ ] Update DB, sync to markdown, verify file
- [ ] Modify both, sync with conflict resolution
- [ ] Batch sync directory with mixed files
- [ ] End-to-end: create -> update -> sync -> verify

### Performance Tests
- [ ] Single file sync completes in <200ms
- [ ] Batch sync 100 files in <10 seconds
- [ ] Hash calculation overhead <10ms per file
- [ ] Parallel processing achieves 4x speedup

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation (docstrings) for all methods
- [ ] Sync workflow documentation with diagrams
- [ ] Conflict resolution strategy guide
- [ ] CLI command usage examples
- [ ] Frontmatter schema documentation
- [ ] Migration guide from pure markdown
- [ ] Troubleshooting guide for sync issues
- [ ] Performance tuning recommendations

---

## Implementation Details

### Development Approach

**Phase 1: Parser Foundation**
1. Implement FrontmatterParser with parse/serialize
2. Add frontmatter validation
3. Write comprehensive parser tests

**Phase 2: Sync From Markdown**
1. Implement single file sync
2. Add hash-based change detection
3. Implement batch sync
4. Add conflict detection

**Phase 3: Sync To Markdown**
1. Implement database to markdown sync
2. Add backup creation
3. Add content preservation
4. Add file path resolution

**Phase 4: Integration & CLI**
1. Add CLI commands
2. Integrate with StateTracker
3. Add conflict resolution strategies
4. Add performance optimizations

### Quality Gates
- [ ] All unit tests pass with >80% coverage
- [ ] Integration tests verify end-to-end sync
- [ ] Performance benchmarks met
- [ ] Conflict resolution tested with all strategies
- [ ] Documentation complete with examples

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Bidirectional sync working correctly
- [ ] Conflict detection and resolution implemented
- [ ] Frontmatter parser handles all edge cases
- [ ] Batch sync supports parallel processing
- [ ] Performance benchmarks met (<200ms single, <10s batch)
- [ ] Tests passing (>80% coverage)
- [ ] CLI commands implemented and tested
- [ ] Code reviewed and approved
- [ ] Documentation complete with examples
- [ ] No regression in existing functionality
- [ ] Migration guide created
- [ ] Committed with atomic commit message:
  ```
  feat(epic-15): implement Story 15.3 - Markdown-SQLite Syncer

  - Implement bidirectional sync between markdown and database
  - Add FrontmatterParser for YAML frontmatter parsing
  - Implement conflict detection with configurable resolution strategies
  - Add batch sync with parallel processing
  - Support hash-based change detection (SHA256)
  - Create CLI commands for manual sync
  - Add comprehensive unit tests (>80% coverage)
  - Performance optimizations (<200ms single file, <10s batch 100)

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
