"""
Tests for StateCoordinator.

Epic: 24 - State Tables & Tracker
Story: 24.7 - Implement StateCoordinator Facade
"""

import sqlite3
import tempfile
from pathlib import Path
import importlib.util
import sys

import pytest


def load_migration_005():
    """Load migration 005 module dynamically."""
    migration_path = Path(__file__).parent.parent.parent / "gao_dev" / "lifecycle" / "migrations" / "005_add_state_tables.py"
    spec = importlib.util.spec_from_file_location("migration_005", migration_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["migration_005"] = module
    spec.loader.exec_module(module)
    return module.Migration005


Migration005 = load_migration_005()

from gao_dev.core.state_coordinator import StateCoordinator


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
def coordinator(temp_db):
    """Create StateCoordinator instance."""
    coord = StateCoordinator(db_path=temp_db)
    yield coord
    coord.close()


class TestStateCoordinatorEpicOperations:
    """Tests for epic-related operations."""

    def test_create_epic(self, coordinator):
        """Test creating an epic through coordinator."""
        epic = coordinator.create_epic(
            epic_num=1, title="Test Epic", total_stories=5
        )

        assert epic["epic_num"] == 1
        assert epic["title"] == "Test Epic"
        assert epic["total_stories"] == 5

    def test_get_epic_state(self, coordinator):
        """Test getting comprehensive epic state."""
        coordinator.create_epic(epic_num=1, title="Epic 1")
        coordinator.create_story(epic_num=1, story_num=1, title="Story 1")
        coordinator.create_story(epic_num=1, story_num=2, title="Story 2")

        state = coordinator.get_epic_state(epic_num=1)

        assert "epic" in state
        assert "stories" in state
        assert state["epic"]["epic_num"] == 1
        assert len(state["stories"]) == 2


class TestStateCoordinatorStoryOperations:
    """Tests for story-related operations."""

    def test_create_story_without_epic_update(self, coordinator):
        """Test creating story without auto-updating epic."""
        coordinator.create_epic(epic_num=1, title="Epic 1", total_stories=0)

        story = coordinator.create_story(
            epic_num=1,
            story_num=1,
            title="Story 1",
            auto_update_epic=False,
        )

        assert story["epic_num"] == 1
        assert story["story_num"] == 1

        # Epic total_stories should still be 0
        epic = coordinator.epic_service.get(epic_num=1)
        assert epic["total_stories"] == 0

    def test_create_story_with_epic_update(self, coordinator):
        """Test creating story with auto-updating epic."""
        coordinator.create_epic(epic_num=1, title="Epic 1", total_stories=0)

        coordinator.create_story(
            epic_num=1,
            story_num=1,
            title="Story 1",
            auto_update_epic=True,
        )

        # Epic total_stories should be incremented
        epic = coordinator.epic_service.get(epic_num=1)
        assert epic["total_stories"] == 1

    def test_complete_story_without_epic_update(self, coordinator):
        """Test completing story without auto-updating epic."""
        coordinator.create_epic(epic_num=1, title="Epic 1", total_stories=2)
        coordinator.create_story(epic_num=1, story_num=1, title="Story 1")

        story = coordinator.complete_story(
            epic_num=1, story_num=1, actual_hours=8.0, auto_update_epic=False
        )

        assert story["status"] == "completed"

        # Epic completed_stories should still be 0
        epic = coordinator.epic_service.get(epic_num=1)
        assert epic["completed_stories"] == 0

    def test_complete_story_with_epic_update(self, coordinator):
        """Test completing story with auto-updating epic."""
        coordinator.create_epic(epic_num=1, title="Epic 1", total_stories=2)
        coordinator.create_story(epic_num=1, story_num=1, title="Story 1")

        coordinator.complete_story(
            epic_num=1, story_num=1, actual_hours=8.0, auto_update_epic=True
        )

        # Epic completed_stories should be incremented
        epic = coordinator.epic_service.get(epic_num=1)
        assert epic["completed_stories"] == 1
        assert epic["progress_percentage"] == 50.0

    def test_complete_story_auto_transitions_epic_to_in_progress(self, coordinator):
        """Test that completing story transitions epic from planning to in_progress."""
        coordinator.create_epic(
            epic_num=1, title="Epic 1", status="planning", total_stories=2
        )
        coordinator.create_story(epic_num=1, story_num=1, title="Story 1")

        coordinator.complete_story(
            epic_num=1, story_num=1, auto_update_epic=True
        )

        epic = coordinator.epic_service.get(epic_num=1)
        assert epic["status"] == "in_progress"

    def test_complete_story_auto_transitions_epic_to_completed(self, coordinator):
        """Test that completing all stories transitions epic to completed."""
        coordinator.create_epic(
            epic_num=1, title="Epic 1", status="in_progress", total_stories=2
        )
        coordinator.create_story(epic_num=1, story_num=1, title="Story 1")
        coordinator.create_story(epic_num=1, story_num=2, title="Story 2")

        # Complete first story
        coordinator.complete_story(
            epic_num=1, story_num=1, auto_update_epic=True
        )

        epic = coordinator.epic_service.get(epic_num=1)
        assert epic["status"] == "in_progress"

        # Complete second story - should transition epic to completed
        coordinator.complete_story(
            epic_num=1, story_num=2, auto_update_epic=True
        )

        epic = coordinator.epic_service.get(epic_num=1)
        assert epic["status"] == "completed"
        assert epic["completed_stories"] == 2
        assert epic["progress_percentage"] == 100.0


class TestStateCoordinatorActionItemOperations:
    """Tests for action item operations."""

    def test_create_action_item(self, coordinator):
        """Test creating action item."""
        item = coordinator.create_action_item(
            title="Update docs", priority="high", assignee="john"
        )

        assert item["title"] == "Update docs"
        assert item["priority"] == "high"
        assert item["assignee"] == "john"

    def test_get_active_action_items(self, coordinator):
        """Test getting active action items."""
        coordinator.create_action_item(title="Task 1", assignee="bob")
        coordinator.create_action_item(title="Task 2", assignee="amelia")

        active = coordinator.get_active_action_items()

        assert len(active) == 2


class TestStateCoordinatorCeremonyOperations:
    """Tests for ceremony operations."""

    def test_record_ceremony(self, coordinator):
        """Test recording ceremony."""
        # Create epic first for foreign key
        coordinator.create_epic(epic_num=1, title="Test Epic")

        ceremony = coordinator.record_ceremony(
            ceremony_type="retrospective",
            summary="Good sprint",
            epic_num=1,
        )

        assert ceremony["ceremony_type"] == "retrospective"
        assert ceremony["summary"] == "Good sprint"

    def test_get_recent_ceremonies(self, coordinator):
        """Test getting recent ceremonies."""
        coordinator.record_ceremony(ceremony_type="standup", summary="S1")
        coordinator.record_ceremony(ceremony_type="review", summary="R1")

        recent = coordinator.get_recent_ceremonies(limit=10)

        assert len(recent) == 2


class TestStateCoordinatorLearningOperations:
    """Tests for learning operations."""

    def test_index_learning(self, coordinator):
        """Test indexing learning."""
        learning = coordinator.index_learning(
            topic="Testing",
            category="technical",
            learning="Use fixtures for setup",
        )

        assert learning["topic"] == "Testing"
        assert learning["category"] == "technical"

    def test_search_learnings(self, coordinator):
        """Test searching learnings."""
        coordinator.index_learning(
            topic="Testing patterns", category="technical", learning="L1"
        )
        coordinator.index_learning(
            topic="Database migrations", category="technical", learning="L2"
        )

        results = coordinator.search_learnings(category="technical")

        assert len(results) == 2
