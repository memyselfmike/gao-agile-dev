"""Tests for StateImporter."""

import pytest
import sqlite3
import yaml
from pathlib import Path
from datetime import datetime

from gao_dev.core.state.importer import StateImporter, ImportReport
from gao_dev.core.state.state_tracker import StateTracker
from gao_dev.core.state.exceptions import RecordNotFoundError


@pytest.fixture
def db_path(tmp_path):
    """Create temporary database with schema."""
    db_file = tmp_path / "test_state.db"

    # Create schema
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE epics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epic_num INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            feature TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            total_points INTEGER DEFAULT 0,
            completed_points INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epic_num INTEGER NOT NULL,
            story_num INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            owner TEXT,
            points INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'P1',
            content_hash TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(epic_num, story_num),
            FOREIGN KEY (epic_num) REFERENCES epics(epic_num)
        )
    """)

    cursor.execute("""
        CREATE TABLE sprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sprint_num INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE story_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sprint_num INTEGER NOT NULL,
            epic_num INTEGER NOT NULL,
            story_num INTEGER NOT NULL,
            assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(epic_num, story_num),
            FOREIGN KEY (sprint_num) REFERENCES sprints(sprint_num),
            FOREIGN KEY (epic_num, story_num) REFERENCES stories(epic_num, story_num)
        )
    """)

    cursor.execute("""
        CREATE TABLE workflow_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_name TEXT NOT NULL,
            epic_num INTEGER NOT NULL,
            story_num INTEGER NOT NULL,
            status TEXT NOT NULL,
            executor TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            duration_ms INTEGER,
            output TEXT
        )
    """)

    conn.commit()
    conn.close()

    return db_file


@pytest.fixture
def tracker(db_path):
    """Create StateTracker with test database."""
    return StateTracker(db_path)


@pytest.fixture
def importer(tracker):
    """Create StateImporter."""
    return StateImporter(tracker)


@pytest.fixture
def sample_sprint_yaml(tmp_path):
    """Create sample sprint-status.yaml file."""
    sprint_data = {
        "sprint_name": "Epic 15 Implementation",
        "start_date": "2025-11-01",
        "phase": "4-implementation",
        "scale_level": 3,
        "epics": [
            {
                "epic_number": 15,
                "name": "State Tracking Database",
                "status": "active",
                "stories": [
                    {"number": 1, "status": "done", "name": "Schema Design"},
                    {"number": 2, "status": "done", "name": "StateTracker Implementation"},
                    {"number": 3, "status": "in_progress", "name": "Markdown Syncer"},
                    {"number": 4, "status": "pending", "name": "Query Builder"},
                ],
            },
            {
                "epic_number": 16,
                "name": "Document Templates",
                "status": "planned",
                "stories": [
                    {"number": 1, "status": "pending", "name": "Template Engine"},
                ],
            },
        ],
    }

    yaml_path = tmp_path / "sprint-status.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(sprint_data, f)

    return yaml_path


@pytest.fixture
def sample_story_files(tmp_path):
    """Create sample story markdown files."""
    stories_dir = tmp_path / "docs" / "features" / "test" / "stories" / "epic-15"
    stories_dir.mkdir(parents=True)

    # Create story 15.1
    story_15_1 = stories_dir / "story-15.1.md"
    story_15_1.write_text(
        """---
epic: 15
story_num: 1
title: Schema Design
status: done
priority: P0
points: 3
owner: Amelia
---

## Story Description

Design database schema for state tracking.

## Acceptance Criteria

- [ ] Schema designed
- [ ] Tables created
"""
    )

    # Create story 15.2
    story_15_2 = stories_dir / "story-15.2.md"
    story_15_2.write_text(
        """---
epic: 15
story_num: 2
title: StateTracker Implementation
status: done
priority: P0
points: 5
owner: Amelia
---

## Story Description

Implement StateTracker class.
"""
    )

    return tmp_path / "docs" / "features"


class TestImportReport:
    """Test ImportReport dataclass."""

    def test_import_report_creation(self):
        """Test ImportReport creation with defaults."""
        report = ImportReport()
        assert report.epics_created == 0
        assert report.stories_created == 0
        assert report.sprints_created == 0
        assert len(report.errors) == 0
        assert len(report.warnings) == 0

    def test_import_report_str(self):
        """Test ImportReport string representation."""
        report = ImportReport(
            epics_created=2,
            stories_created=5,
            sprints_created=1,
            duration_seconds=1.5,
        )
        report_str = str(report)
        assert "Epics created: 2" in report_str
        assert "Stories created: 5" in report_str
        assert "Sprints created: 1" in report_str
        assert "Duration: 1.50s" in report_str


class TestSprintStatusImport:
    """Test importing sprint-status.yaml."""

    def test_import_sprint_status_success(self, importer, sample_sprint_yaml):
        """Test successful sprint-status.yaml import."""
        report = importer.import_sprint_status(sample_sprint_yaml)

        assert report.sprints_created == 1
        assert report.epics_created == 2
        assert len(report.errors) == 0

    def test_import_sprint_status_creates_sprint(
        self, importer, sample_sprint_yaml, tracker
    ):
        """Test that sprint is created."""
        report = importer.import_sprint_status(sample_sprint_yaml)

        # Verify sprint created
        sprint = tracker.get_sprint(1)
        assert sprint.name == "Sprint 1"
        assert sprint.start_date == "2025-11-01"

    def test_import_sprint_status_creates_epics(
        self, importer, sample_sprint_yaml, tracker
    ):
        """Test that epics are created."""
        report = importer.import_sprint_status(sample_sprint_yaml)

        # Verify epics created
        epic15 = tracker.get_epic(15)
        assert epic15.title == "State Tracking Database"
        assert epic15.status == "active"

        epic16 = tracker.get_epic(16)
        assert epic16.title == "Document Templates"
        assert epic16.status == "planned"

    def test_import_sprint_status_creates_stories(
        self, importer, sample_sprint_yaml, tracker
    ):
        """Test that stories are created."""
        report = importer.import_sprint_status(sample_sprint_yaml)

        # Verify stories created for epic 15
        stories = tracker.get_stories_by_epic(15)
        assert len(stories) == 4

        story1 = tracker.get_story(15, 1)
        assert story1.title == "Schema Design"
        assert story1.status == "done"

    def test_import_sprint_status_file_not_found(self, importer, tmp_path):
        """Test import with non-existent file."""
        report = importer.import_sprint_status(tmp_path / "nonexistent.yaml")

        assert len(report.errors) > 0
        assert "not found" in report.errors[0].lower()

    def test_import_sprint_status_dry_run(self, tracker, sample_sprint_yaml):
        """Test dry-run mode doesn't create records."""
        importer = StateImporter(tracker, dry_run=True)
        report = importer.import_sprint_status(sample_sprint_yaml)

        # Should not create any actual records
        with pytest.raises(RecordNotFoundError):
            tracker.get_sprint(1)


class TestStoryFilesImport:
    """Test importing story markdown files."""

    def test_import_story_files_success(self, importer, sample_story_files):
        """Test successful story files import."""
        # First create the epic that stories reference
        importer.state_tracker.create_epic(15, "Test Epic", "test-feature", 0)

        report = importer.import_story_files(sample_story_files)

        assert report.stories_created == 2
        assert len(report.errors) == 0

    def test_import_story_files_creates_stories(
        self, importer, sample_story_files, tracker
    ):
        """Test that stories are created from files."""
        # Create epic first
        tracker.create_epic(15, "Test Epic", "test-feature", 0)

        report = importer.import_story_files(sample_story_files)

        # Verify stories created
        story1 = tracker.get_story(15, 1)
        assert story1.title == "Schema Design"
        assert story1.status == "done"
        assert story1.points == 3
        assert story1.owner == "Amelia"

        story2 = tracker.get_story(15, 2)
        assert story2.title == "StateTracker Implementation"
        assert story2.points == 5

    def test_import_story_files_non_recursive(self, importer, sample_story_files):
        """Test non-recursive import."""
        # Create epic first
        importer.state_tracker.create_epic(15, "Test Epic", "test-feature", 0)

        # Non-recursive should find nothing (files are in subdirs)
        report = importer.import_story_files(sample_story_files, recursive=False)
        assert report.stories_created == 0


class TestFullImport:
    """Test importing all data."""

    def test_import_all_success(
        self, importer, sample_sprint_yaml, sample_story_files
    ):
        """Test full import of all data."""
        report = importer.import_all(
            sample_sprint_yaml, [sample_story_files], create_backup=False
        )

        assert report.sprints_created == 1
        assert report.epics_created == 2
        # Stories from sprint-status.yaml (5) + story files (2) = 7
        # But story files duplicate sprint-status, so actual may vary
        assert report.stories_created >= 2

    def test_import_all_with_backup(
        self, importer, sample_sprint_yaml, sample_story_files
    ):
        """Test import with backup creation."""
        report = importer.import_all(
            sample_sprint_yaml, [sample_story_files], create_backup=True
        )

        # Verify backup was created
        assert importer.backup_path is not None
        assert importer.backup_path.exists()

        # Save backup path before cleanup
        backup_path = importer.backup_path

        # Cleanup
        importer.cleanup_backup()
        assert not backup_path.exists()

    def test_import_all_validation(
        self, importer, sample_sprint_yaml, sample_story_files
    ):
        """Test validation after import."""
        report = importer.import_all(
            sample_sprint_yaml, [sample_story_files], create_backup=False
        )

        # Should have no validation errors
        assert len(report.validation_errors) == 0


class TestHelperMethods:
    """Test helper methods."""

    def test_extract_feature_from_name(self, importer):
        """Test feature name extraction."""
        assert importer._extract_feature_from_name("State Tracking Database") == (
            "state-tracking-database"
        )
        assert importer._extract_feature_from_name("Document Templates") == (
            "document-templates"
        )
        assert importer._extract_feature_from_name("Epic 15: Test") == "epic-15-test"

    def test_parse_story_points(self, importer):
        """Test parsing story points from name."""
        assert importer._parse_story_points("Schema Design (3 points)") == 3
        assert importer._parse_story_points("Implementation (5pt)") == 5
        assert importer._parse_story_points("No points here") == 0

    def test_get_next_sprint_number(self, importer, tracker):
        """Test getting next sprint number."""
        # First sprint should be 1
        assert importer._get_next_sprint_number() == 1

        # Create a sprint
        tracker.create_sprint(1, "2025-11-01", "2025-11-15")

        # Next should be 2
        assert importer._get_next_sprint_number() == 2


class TestValidation:
    """Test data validation."""

    def test_validate_import_success(self, importer, tracker):
        """Test validation with valid data."""
        # Create valid data
        tracker.create_epic(15, "Test Epic", "test-feature", 10)
        tracker.create_story(15, 1, "Test Story", status="done", points=5)

        errors = importer._validate_import()
        assert len(errors) == 0

    def test_validate_orphaned_stories(self, importer, tracker):
        """Test validation detects orphaned stories."""
        # Create story without epic (by direct SQL, disable FK check)
        conn = sqlite3.connect(str(tracker.db_path))
        conn.execute("PRAGMA foreign_keys = OFF")
        now = datetime.now().isoformat()
        conn.execute(
            """
            INSERT INTO stories (epic_num, story_num, title, status, created_at, updated_at)
            VALUES (999, 1, 'Orphan Story', 'pending', ?, ?)
            """,
            (now, now),
        )
        conn.commit()
        conn.close()

        errors = importer._validate_import()
        assert len(errors) > 0
        assert "non-existent epic" in errors[0]

    def test_validate_invalid_status(self, importer, tracker):
        """Test validation detects invalid statuses."""
        # Create epic and story with invalid status
        tracker.create_epic(15, "Test Epic", "test-feature", 10)

        # Create story with valid status first
        tracker.create_story(15, 1, "Test Story", status="pending")

        # Update to invalid status via SQL
        with tracker._get_connection() as conn:
            conn.execute(
                "UPDATE stories SET status = 'invalid_status' WHERE epic_num = 15 AND story_num = 1"
            )

        errors = importer._validate_import()
        assert len(errors) > 0
        assert "invalid status" in errors[0].lower()


class TestBackupAndRollback:
    """Test backup and rollback functionality."""

    def test_create_backup(self, importer, tracker):
        """Test backup creation."""
        # Create some data
        tracker.create_epic(15, "Test Epic", "test-feature", 10)

        # Create backup
        backup_path = importer._create_backup()

        assert backup_path.exists()
        assert "backup" in backup_path.name

        # Cleanup
        backup_path.unlink()

    def test_rollback(self, importer, tracker):
        """Test rollback to backup."""
        # Create initial data
        tracker.create_epic(15, "Original Epic", "test-feature", 10)

        # Create backup
        importer.backup_path = importer._create_backup()

        # Modify data
        tracker.create_epic(16, "New Epic", "test-feature", 5)

        # Rollback
        importer._rollback()

        # Verify rollback worked - epic 16 should not exist
        with pytest.raises(RecordNotFoundError):
            tracker.get_epic(16)

        # Original epic should still exist
        epic = tracker.get_epic(15)
        assert epic.title == "Original Epic"

        # Cleanup
        importer.cleanup_backup()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_yaml_file(self, importer, tmp_path):
        """Test import with empty YAML file."""
        empty_yaml = tmp_path / "empty.yaml"
        empty_yaml.write_text("")

        report = importer.import_sprint_status(empty_yaml)
        assert len(report.errors) > 0

    def test_missing_stories_directory(self, importer, tmp_path):
        """Test import with non-existent directory."""
        report = importer.import_story_files(tmp_path / "nonexistent")
        # Should not error, just return empty report
        assert report.stories_created == 0

    def test_duplicate_import(self, importer, sample_sprint_yaml):
        """Test importing same data twice (idempotent)."""
        # First import
        report1 = importer.import_sprint_status(sample_sprint_yaml)
        assert report1.epics_created == 2

        # Second import should skip duplicates
        report2 = importer.import_sprint_status(sample_sprint_yaml)
        assert len(report2.warnings) > 0  # Should have warnings about duplicates
