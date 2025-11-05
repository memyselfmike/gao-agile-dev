"""Tests for MarkdownSyncer.

Tests bidirectional sync between markdown files and SQLite database.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from gao_dev.core.state import (
    StateTracker,
    MarkdownSyncer,
    SyncReport,
    ConflictResolution,
    SyncError,
    ConflictError,
)


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database with schema."""
    db_path = tmp_path / "test.db"

    # Create database with schema
    import sqlite3
    from gao_dev.core.state import get_schema_path

    schema_sql = get_schema_path().read_text()

    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)

    return db_path


@pytest.fixture
def tracker(temp_db):
    """Create StateTracker instance."""
    return StateTracker(temp_db)


@pytest.fixture
def syncer(tracker):
    """Create MarkdownSyncer instance."""
    return MarkdownSyncer(tracker)


@pytest.fixture
def sample_markdown(tmp_path):
    """Create sample markdown file."""
    md_file = tmp_path / "story-1.1.md"
    content = """---
epic: 1
story_num: 1
title: Test Story
status: pending
owner: Amelia
points: 3
priority: P1
---

## Story Description

This is a test story.

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
"""
    md_file.write_text(content, encoding="utf-8")
    return md_file


class TestMarkdownSyncer:
    """Test suite for MarkdownSyncer."""

    def test_init(self, tracker):
        """Test syncer initialization."""
        syncer = MarkdownSyncer(tracker)

        assert syncer.state_tracker is tracker
        assert syncer.conflict_strategy == ConflictResolution.DATABASE_WINS
        assert syncer.parser is not None

    def test_init_custom_strategy(self, tracker):
        """Test initialization with custom conflict strategy."""
        syncer = MarkdownSyncer(tracker, ConflictResolution.MARKDOWN_WINS)

        assert syncer.conflict_strategy == ConflictResolution.MARKDOWN_WINS

    def test_sync_from_markdown_creates_story(self, syncer, sample_markdown, tracker):
        """Test sync creates new story in database."""
        # Setup: Create epic first
        tracker.create_epic(1, "Test Epic", "test-feature")

        result = syncer.sync_from_markdown(sample_markdown)

        assert result["status"] == "created"
        assert result["epic"] == 1
        assert result["story"] == 1

        # Verify story created in database
        story = tracker.get_story(1, 1)
        assert story.title == "Test Story"
        assert story.status == "pending"
        assert story.owner == "Amelia"
        assert story.points == 3
        assert story.content_hash is not None

    def test_sync_from_markdown_updates_story(self, syncer, sample_markdown, tracker):
        """Test sync updates existing story."""
        # Setup: Create epic and story
        tracker.create_epic(1, "Test Epic", "test-feature")
        tracker.create_story(1, 1, "Old Title", content_hash="old_hash")

        result = syncer.sync_from_markdown(sample_markdown)

        assert result["status"] == "updated"

        # Verify story updated
        story = tracker.get_story(1, 1)
        assert story.content_hash != "old_hash"

    def test_sync_from_markdown_skips_unchanged(self, syncer, sample_markdown, tracker):
        """Test sync skips file when content hash matches."""
        # Setup: Create epic
        tracker.create_epic(1, "Test Epic", "test-feature")

        # First sync
        result1 = syncer.sync_from_markdown(sample_markdown)
        assert result1["status"] == "created"

        # Second sync (no changes)
        result2 = syncer.sync_from_markdown(sample_markdown)
        assert result2["status"] == "skipped"
        assert result2["reason"] == "no_changes"

    def test_sync_from_markdown_missing_epic(self, syncer, tmp_path):
        """Test sync fails when epic missing in frontmatter."""
        md_file = tmp_path / "invalid.md"
        content = """---
story_num: 1
title: Test
---

Body
"""
        md_file.write_text(content, encoding="utf-8")

        with pytest.raises(SyncError, match="Missing epic"):
            syncer.sync_from_markdown(md_file)

    def test_sync_from_markdown_missing_story_num(self, syncer, tmp_path):
        """Test sync fails when story_num missing."""
        md_file = tmp_path / "invalid.md"
        content = """---
epic: 1
title: Test
---

Body
"""
        md_file.write_text(content, encoding="utf-8")

        with pytest.raises(SyncError, match="story_num"):
            syncer.sync_from_markdown(md_file)

    def test_sync_from_markdown_calculates_hash(self, syncer, sample_markdown, tracker):
        """Test sync calculates SHA256 hash correctly."""
        tracker.create_epic(1, "Test Epic", "test-feature")

        result = syncer.sync_from_markdown(sample_markdown)

        story = tracker.get_story(1, 1)
        assert story.content_hash is not None
        assert len(story.content_hash) == 64  # SHA256 hex length

    def test_sync_to_markdown_creates_file(self, syncer, tracker, tmp_path):
        """Test sync to markdown creates new file."""
        # Setup: Create epic and story
        tracker.create_epic(1, "Test Epic", "test-feature")
        story = tracker.create_story(1, 1, "Test Story", status="in_progress")

        file_path = tmp_path / "story-1.1.md"
        result_path = syncer.sync_to_markdown(1, 1, file_path)

        assert result_path == file_path
        assert file_path.exists()

        content = file_path.read_text(encoding="utf-8")
        assert "epic: 1" in content
        assert "story_num: 1" in content
        assert "title: Test Story" in content
        assert "status: in_progress" in content

    def test_sync_to_markdown_updates_frontmatter(self, syncer, tracker, tmp_path):
        """Test sync updates frontmatter while preserving body."""
        # Setup: Create epic and story
        tracker.create_epic(1, "Test Epic", "test-feature")
        tracker.create_story(1, 1, "Test Story", status="pending")

        # Create existing file with body
        file_path = tmp_path / "story-1.1.md"
        original_content = """---
epic: 1
story_num: 1
title: Old Title
status: pending
---

## Original Body

This body should be preserved.
"""
        file_path.write_text(original_content, encoding="utf-8")

        # Update story in database
        tracker.update_story_status(1, 1, "done")

        # Sync to markdown
        syncer.sync_to_markdown(1, 1, file_path)

        content = file_path.read_text(encoding="utf-8")
        assert "status: done" in content
        assert "## Original Body" in content
        assert "This body should be preserved." in content

    def test_sync_to_markdown_creates_backup(self, syncer, tracker, tmp_path):
        """Test sync creates backup before overwriting."""
        # Setup
        tracker.create_epic(1, "Test Epic", "test-feature")
        tracker.create_story(1, 1, "Test Story")

        file_path = tmp_path / "story-1.1.md"
        file_path.write_text("original content", encoding="utf-8")

        syncer.sync_to_markdown(1, 1, file_path)

        backup_path = tmp_path / "story-1.1.md.bak"
        assert backup_path.exists()
        assert backup_path.read_text(encoding="utf-8") == "original content"

    def test_sync_directory_batch(self, syncer, tracker, tmp_path):
        """Test batch sync processes multiple files."""
        # Setup: Create epic
        tracker.create_epic(1, "Test Epic", "test-feature")

        # Create multiple markdown files
        for i in range(1, 4):
            md_file = tmp_path / f"story-1.{i}.md"
            content = f"""---
epic: 1
story_num: {i}
title: Story {i}
status: pending
---

Story {i} body
"""
            md_file.write_text(content, encoding="utf-8")

        report = syncer.sync_directory(tmp_path, recursive=False)

        assert report.files_processed == 3
        assert report.stories_created == 3
        assert report.stories_updated == 0
        assert report.files_skipped == 0
        assert len(report.errors) == 0

    def test_sync_directory_recursive(self, syncer, tracker, tmp_path):
        """Test recursive directory sync."""
        tracker.create_epic(1, "Test Epic", "test-feature")

        # Create nested directory structure
        subdir = tmp_path / "epic-1"
        subdir.mkdir()

        md_file = subdir / "story-1.1.md"
        content = """---
epic: 1
story_num: 1
title: Test
status: pending
---

Body
"""
        md_file.write_text(content, encoding="utf-8")

        report = syncer.sync_directory(tmp_path, recursive=True)

        assert report.files_processed == 1
        assert report.stories_created == 1

    def test_sync_directory_handles_errors(self, syncer, tracker, tmp_path):
        """Test directory sync continues on errors."""
        tracker.create_epic(1, "Test Epic", "test-feature")

        # Valid file
        md1 = tmp_path / "story-1.1.md"
        md1.write_text("""---
epic: 1
story_num: 1
title: Valid
status: pending
---
Body""", encoding="utf-8")

        # Invalid file (missing story_num)
        md2 = tmp_path / "invalid.md"
        md2.write_text("""---
epic: 1
title: Invalid
---
Body""", encoding="utf-8")

        report = syncer.sync_directory(tmp_path, recursive=False)

        assert report.files_processed == 2
        assert report.stories_created == 1
        assert len(report.errors) == 1

    def test_conflict_detection(self, syncer, tracker, sample_markdown):
        """Test conflict detection between database and markdown."""
        # Setup: Create epic and story with different status
        tracker.create_epic(1, "Test Epic", "test-feature")
        story = tracker.create_story(
            1, 1, "Test Story",
            status="done",  # Different from markdown (pending)
            content_hash="old_hash"
        )

        # Modify markdown to trigger update
        content = sample_markdown.read_text()
        sample_markdown.write_text(content + "\n# Modified", encoding="utf-8")

        result = syncer.sync_from_markdown(sample_markdown)

        # Should detect conflict and log it
        assert result["status"] == "updated"
        assert syncer.conflict_log_path.exists()

    def test_conflict_strategy_database_wins(self, tracker, sample_markdown):
        """Test database_wins conflict resolution."""
        syncer = MarkdownSyncer(tracker, ConflictResolution.DATABASE_WINS)

        # Setup: Create story with database values
        tracker.create_epic(1, "Test Epic", "test-feature")
        tracker.create_story(
            1, 1, "Test Story",
            status="done",  # Database has 'done'
            owner="Bob",
            content_hash="old_hash"
        )

        # Markdown has 'pending' and 'Amelia'
        result = syncer.sync_from_markdown(sample_markdown)

        # Database values should win
        story = tracker.get_story(1, 1)
        assert story.status == "done"  # Database value preserved
        assert story.owner == "Bob"  # Database value preserved

    def test_conflict_strategy_markdown_wins(self, tracker, sample_markdown):
        """Test markdown_wins conflict resolution."""
        syncer = MarkdownSyncer(tracker, ConflictResolution.MARKDOWN_WINS)

        # Setup: Create story with database values
        tracker.create_epic(1, "Test Epic", "test-feature")
        tracker.create_story(
            1, 1, "Test Story",
            status="done",  # Database has 'done'
            owner="Bob",
            content_hash="old_hash"
        )

        # Markdown has 'pending' and 'Amelia'
        result = syncer.sync_from_markdown(sample_markdown)

        # Markdown values should win
        story = tracker.get_story(1, 1)
        assert story.status == "pending"  # Markdown value applied
        assert story.owner == "Amelia"  # Markdown value applied

    def test_conflict_strategy_manual(self, tracker, sample_markdown):
        """Test manual conflict resolution raises error."""
        syncer = MarkdownSyncer(tracker, ConflictResolution.MANUAL)

        # Setup: Create story with conflicting values
        tracker.create_epic(1, "Test Epic", "test-feature")
        tracker.create_story(
            1, 1, "Test Story",
            status="done",
            content_hash="old_hash"
        )

        # ConflictError is wrapped in SyncError
        with pytest.raises(SyncError, match="Manual conflict resolution required"):
            syncer.sync_from_markdown(sample_markdown)

    def test_calculate_hash(self, syncer):
        """Test SHA256 hash calculation."""
        content = "Test content"
        hash1 = syncer._calculate_hash(content)
        hash2 = syncer._calculate_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 64

        # Different content produces different hash
        hash3 = syncer._calculate_hash("Different content")
        assert hash3 != hash1

    def test_story_to_frontmatter(self, syncer, tracker):
        """Test converting Story to frontmatter dict."""
        tracker.create_epic(1, "Test Epic", "test-feature")
        story = tracker.create_story(
            1, 1, "Test Story",
            status="in_progress",
            owner="Amelia",
            points=5,
            priority="P0"
        )

        frontmatter = syncer._story_to_frontmatter(story)

        assert frontmatter["epic"] == 1
        assert frontmatter["story_num"] == 1
        assert frontmatter["title"] == "Test Story"
        assert frontmatter["status"] == "in_progress"
        assert frontmatter["owner"] == "Amelia"
        assert frontmatter["points"] == 5
        assert frontmatter["priority"] == "P0"

    def test_resolve_story_path(self, syncer):
        """Test story path resolution."""
        path = syncer._resolve_story_path(15, 3)

        assert "epic-15" in str(path)
        assert "story-15.3.md" in str(path)

    def test_generate_default_body(self, syncer, tracker):
        """Test default body generation."""
        tracker.create_epic(1, "Test Epic", "test-feature")
        story = tracker.create_story(1, 1, "Test Story")

        body = syncer._generate_default_body(story)

        assert "## Story Description" in body
        assert "## Acceptance Criteria" in body
        assert "## Technical Notes" in body
        assert "## Definition of Done" in body

    def test_sync_report_str(self):
        """Test SyncReport string representation."""
        report = SyncReport(
            files_processed=10,
            stories_created=5,
            stories_updated=3,
            files_skipped=2,
            errors=["Error 1"]
        )

        report_str = str(report)
        assert "Files processed: 10" in report_str
        assert "Stories created: 5" in report_str
        assert "Stories updated: 3" in report_str
        assert "Errors: 1" in report_str

    def test_sync_preserves_sprint_assignment(self, syncer, tracker, tmp_path):
        """Test sync preserves sprint assignments."""
        # Setup
        tracker.create_epic(1, "Test Epic", "test-feature")
        tracker.create_sprint(1, "2025-01-01", "2025-01-14")

        md_file = tmp_path / "story-1.1.md"
        content = """---
epic: 1
story_num: 1
title: Test Story
status: pending
sprint: 1
---

Body
"""
        md_file.write_text(content, encoding="utf-8")

        result = syncer.sync_from_markdown(md_file)

        story = tracker.get_story(1, 1)
        assert story.sprint == 1

    def test_sync_handles_none_values(self, syncer, tracker, tmp_path):
        """Test sync handles null/None values correctly."""
        tracker.create_epic(1, "Test Epic", "test-feature")

        md_file = tmp_path / "story-1.1.md"
        content = """---
epic: 1
story_num: 1
title: Test Story
status: pending
owner: null
sprint: null
---

Body
"""
        md_file.write_text(content, encoding="utf-8")

        result = syncer.sync_from_markdown(md_file)

        story = tracker.get_story(1, 1)
        assert story.owner is None
        assert story.sprint is None
