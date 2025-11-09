"""
Tests for StoryStateService.

Epic: 24 - State Tables & Tracker
Story: 24.3 - Implement StoryStateService
"""

import sqlite3
import tempfile
from pathlib import Path
import importlib.util
import sys

import pytest


def load_migration_005():
    """Load migration 005 module dynamically."""
    migration_path = Path(__file__).parent.parent.parent.parent / "gao_dev" / "lifecycle" / "migrations" / "005_add_state_tables.py"
    spec = importlib.util.spec_from_file_location("migration_005", migration_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["migration_005"] = module
    spec.loader.exec_module(module)
    return module.Migration005


Migration005 = load_migration_005()

from gao_dev.core.services.epic_state_service import EpicStateService
from gao_dev.core.services.story_state_service import StoryStateService


@pytest.fixture
def temp_db():
    """Create a temporary database with migration applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL,
            description TEXT
        )
        """
    )
    conn.commit()
    Migration005.up(conn)
    conn.close()

    yield db_path

    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def service(temp_db):
    """Create StoryStateService instance."""
    # Create epic first (for foreign key)
    epic_svc = EpicStateService(db_path=temp_db)
    epic_svc.create(epic_num=1, title="Test Epic")
    epic_svc.close()

    svc = StoryStateService(db_path=temp_db)
    yield svc
    svc.close()


class TestStoryStateServiceCreate:
    """Tests for create method."""

    def test_create_basic_story(self, service):
        """Test creating a basic story."""
        story = service.create(
            epic_num=1,
            story_num=1,
            title="User login endpoint",
            status="pending",
        )

        assert story["epic_num"] == 1
        assert story["story_num"] == 1
        assert story["title"] == "User login endpoint"
        assert story["status"] == "pending"
        assert story["priority"] == "P2"
        assert story["created_at"] is not None

    def test_create_with_all_fields(self, service):
        """Test creating story with all fields."""
        story = service.create(
            epic_num=1,
            story_num=2,
            title="Test story",
            status="in_progress",
            assignee="amelia",
            priority="P0",
            estimate_hours=8.0,
            metadata={"complexity": "high"},
        )

        assert story["assignee"] == "amelia"
        assert story["priority"] == "P0"
        assert story["estimate_hours"] == 8.0

    def test_create_duplicate_fails(self, service):
        """Test that creating duplicate story fails."""
        service.create(epic_num=1, story_num=1, title="Story 1")

        with pytest.raises(ValueError, match="already exists"):
            service.create(epic_num=1, story_num=1, title="Duplicate")

    def test_create_without_epic_fails(self, temp_db):
        """Test that creating story without epic fails."""
        svc = StoryStateService(db_path=temp_db)

        with pytest.raises(ValueError, match="Epic 999 does not exist"):
            svc.create(epic_num=999, story_num=1, title="Story")

        svc.close()


class TestStoryStateServiceGet:
    """Tests for get method."""

    def test_get_existing_story(self, service):
        """Test getting an existing story."""
        created = service.create(epic_num=1, story_num=1, title="Story 1")
        fetched = service.get(epic_num=1, story_num=1)

        assert fetched["title"] == created["title"]

    def test_get_nonexistent_story_fails(self, service):
        """Test that getting nonexistent story fails."""
        with pytest.raises(ValueError, match="not found"):
            service.get(epic_num=1, story_num=999)


class TestStoryStateServiceTransition:
    """Tests for transition method."""

    def test_transition_status(self, service):
        """Test transitioning story status."""
        service.create(epic_num=1, story_num=1, title="Story 1")

        updated = service.transition(
            epic_num=1, story_num=1, new_status="in_progress"
        )

        assert updated["status"] == "in_progress"

    def test_transition_sets_started_at(self, service):
        """Test that started_at is set when moving to in_progress."""
        service.create(epic_num=1, story_num=1, title="Story 1")

        updated = service.transition(
            epic_num=1, story_num=1, new_status="in_progress"
        )

        assert updated["started_at"] is not None

    def test_transition_with_assignee(self, service):
        """Test transitioning with assignee update."""
        service.create(epic_num=1, story_num=1, title="Story 1")

        updated = service.transition(
            epic_num=1, story_num=1, new_status="in_progress", assignee="bob"
        )

        assert updated["status"] == "in_progress"
        assert updated["assignee"] == "bob"

    def test_transition_to_blocked(self, service):
        """Test transitioning to blocked with reason."""
        service.create(epic_num=1, story_num=1, title="Story 1")

        updated = service.transition(
            epic_num=1,
            story_num=1,
            new_status="blocked",
            blocked_reason="Waiting for API",
        )

        assert updated["status"] == "blocked"
        assert updated["blocked_reason"] == "Waiting for API"


class TestStoryStateServiceComplete:
    """Tests for complete method."""

    def test_complete_story(self, service):
        """Test completing a story."""
        service.create(epic_num=1, story_num=1, title="Story 1")

        completed = service.complete(epic_num=1, story_num=1, actual_hours=6.5)

        assert completed["status"] == "completed"
        assert completed["actual_hours"] == 6.5
        assert completed["completed_at"] is not None

    def test_complete_nonexistent_story_fails(self, service):
        """Test that completing nonexistent story fails."""
        with pytest.raises(ValueError, match="not found"):
            service.complete(epic_num=1, story_num=999)


class TestStoryStateServiceListByEpic:
    """Tests for list_by_epic method."""

    def test_list_stories_for_epic(self, service):
        """Test listing all stories for an epic."""
        service.create(epic_num=1, story_num=1, title="Story 1")
        service.create(epic_num=1, story_num=2, title="Story 2")
        service.create(epic_num=1, story_num=3, title="Story 3")

        stories = service.list_by_epic(epic_num=1)

        assert len(stories) == 3
        assert stories[0]["story_num"] == 1
        assert stories[1]["story_num"] == 2
        assert stories[2]["story_num"] == 3

    def test_list_empty_epic(self, service):
        """Test listing stories for epic with no stories."""
        stories = service.list_by_epic(epic_num=1)

        assert stories == []


class TestStoryStateServiceListByStatus:
    """Tests for list_by_status method."""

    def test_list_by_status(self, service):
        """Test listing stories by status."""
        service.create(epic_num=1, story_num=1, title="S1", status="pending")
        service.create(epic_num=1, story_num=2, title="S2", status="in_progress")
        service.create(epic_num=1, story_num=3, title="S3", status="pending")

        pending = service.list_by_status("pending")

        assert len(pending) == 2
        assert all(s["status"] == "pending" for s in pending)

    def test_list_by_status_empty(self, service):
        """Test listing with status that has no stories."""
        stories = service.list_by_status("completed")

        assert stories == []
