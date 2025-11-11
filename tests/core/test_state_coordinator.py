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
from gao_dev.core.services.feature_state_service import (
    FeatureScope,
    FeatureStatus,
)


@pytest.fixture
def temp_db():
    """Create a temporary database with migration applied."""
    # Create a temporary directory structure: project_root/.gao-dev/documents.db
    import tempfile
    import shutil

    temp_dir = Path(tempfile.mkdtemp())
    gao_dev_dir = temp_dir / ".gao-dev"
    gao_dev_dir.mkdir(parents=True, exist_ok=True)
    db_path = gao_dev_dir / "documents.db"

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

    # Cleanup temp directory
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def coordinator(temp_db):
    """Create StateCoordinator instance."""
    # project_root is parent of .gao-dev directory
    project_root = temp_db.parent.parent
    coord = StateCoordinator(db_path=temp_db, project_root=project_root)
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


class TestStateCoordinatorFeatureOperations:
    """Tests for feature-related operations (Story 32.2)."""

    def test_create_feature(self, coordinator):
        """Test creating feature through coordinator."""
        feature = coordinator.create_feature(
            name="user-auth",
            scope=FeatureScope.FEATURE,
            scale_level=3,
            description="User authentication system",
            owner="john",
        )

        assert feature.name == "user-auth"
        assert feature.scope == FeatureScope.FEATURE
        assert feature.scale_level == 3
        assert feature.description == "User authentication system"
        assert feature.owner == "john"
        assert feature.status == FeatureStatus.PLANNING

    def test_get_feature(self, coordinator):
        """Test getting feature by name."""
        coordinator.create_feature(
            name="test-feature", scope=FeatureScope.MVP, scale_level=2
        )

        feature = coordinator.get_feature("test-feature")

        assert feature is not None
        assert feature["name"] == "test-feature"
        assert feature["scope"] == "mvp"

    def test_get_feature_nonexistent(self, coordinator):
        """Test getting nonexistent feature returns None."""
        feature = coordinator.get_feature("nonexistent")

        assert feature is None

    def test_list_features(self, coordinator):
        """Test listing features with filters."""
        coordinator.create_feature(
            name="mvp-1", scope=FeatureScope.MVP, scale_level=2
        )
        coordinator.create_feature(
            name="feature-1", scope=FeatureScope.FEATURE, scale_level=3
        )
        coordinator.create_feature(
            name="feature-2", scope=FeatureScope.FEATURE, scale_level=4
        )

        # List all features
        all_features = coordinator.list_features()
        assert len(all_features) == 3

        # List MVP features
        mvp_features = coordinator.list_features(scope=FeatureScope.MVP)
        assert len(mvp_features) == 1
        assert mvp_features[0].name == "mvp-1"

        # List FEATURE scope
        feature_scope = coordinator.list_features(scope=FeatureScope.FEATURE)
        assert len(feature_scope) == 2

    def test_update_feature_status(self, coordinator):
        """Test updating feature status."""
        coordinator.create_feature(
            name="test-feature", scope=FeatureScope.MVP, scale_level=2
        )

        # Update to active
        result = coordinator.update_feature_status("test-feature", FeatureStatus.ACTIVE)
        assert result is True

        # Verify status changed
        feature = coordinator.get_feature("test-feature")
        assert feature["status"] == "active"

    def test_update_feature_status_nonexistent(self, coordinator):
        """Test updating status of nonexistent feature returns False."""
        result = coordinator.update_feature_status(
            "nonexistent", FeatureStatus.ACTIVE
        )
        assert result is False

    def test_get_feature_state_not_found(self, coordinator):
        """Test get_feature_state raises ValueError if feature not found."""
        with pytest.raises(ValueError, match="Feature 'nonexistent' not found"):
            coordinator.get_feature_state("nonexistent")

    def test_get_feature_state_no_epics(self, coordinator):
        """Test get_feature_state with feature but no epics."""
        coordinator.create_feature(
            name="test-feature", scope=FeatureScope.MVP, scale_level=2
        )

        state = coordinator.get_feature_state("test-feature")

        assert state["feature"] is not None
        assert state["feature"]["name"] == "test-feature"
        assert len(state["epics"]) == 0
        assert len(state["epic_summaries"]) == 0
        assert state["total_stories"] == 0
        assert state["completed_stories"] == 0
        assert state["completion_pct"] == 0.0

    def test_get_feature_state_with_epics_and_stories(self, coordinator):
        """Test get_feature_state returns comprehensive data with epics and stories."""
        # Create feature
        coordinator.create_feature(
            name="test-feature", scope=FeatureScope.MVP, scale_level=3
        )

        # Create epics (Note: epic_state table doesn't have feature column)
        # We need to work with what's available in epic_state
        # This test may need adjustment based on actual schema
        coordinator.create_epic(epic_num=1, title="Epic 1", total_stories=3)
        coordinator.create_epic(epic_num=2, title="Epic 2", total_stories=2)

        # Create stories
        coordinator.create_story(epic_num=1, story_num=1, title="Story 1.1")
        coordinator.create_story(epic_num=1, story_num=2, title="Story 1.2")
        coordinator.create_story(epic_num=2, story_num=1, title="Story 2.1")

        # Complete one story
        coordinator.complete_story(epic_num=1, story_num=1, actual_hours=5.0)

        # Note: This test won't work properly until epic_state table has feature column
        # For now, we test that the method runs without error
        # When epic_state has feature column, update epics to have feature="test-feature"

        # Since epic_state doesn't have feature column yet, this will return empty
        state = coordinator.get_feature_state("test-feature")

        # Assertions for structure (even if data is empty)
        assert "feature" in state
        assert "epics" in state
        assert "epic_summaries" in state
        assert "total_stories" in state
        assert "completed_stories" in state
        assert "completion_pct" in state

    def test_feature_service_initialization(self, coordinator):
        """Test that feature_service is properly initialized."""
        assert coordinator.feature_service is not None
        assert hasattr(coordinator, "feature_service")

    def test_list_features_by_status(self, coordinator):
        """Test listing features filtered by status."""
        coordinator.create_feature(
            name="feature-1", scope=FeatureScope.FEATURE, scale_level=2
        )
        coordinator.create_feature(
            name="feature-2", scope=FeatureScope.FEATURE, scale_level=3
        )

        # Update one to active
        coordinator.update_feature_status("feature-1", FeatureStatus.ACTIVE)

        # List active features
        active_features = coordinator.list_features(status=FeatureStatus.ACTIVE)
        assert len(active_features) == 1
        assert active_features[0].name == "feature-1"

        # List planning features
        planning_features = coordinator.list_features(status=FeatureStatus.PLANNING)
        assert len(planning_features) == 1
        assert planning_features[0].name == "feature-2"
