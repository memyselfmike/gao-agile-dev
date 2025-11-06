"""
Integration tests for unified database (Story 17.2).

Tests that all components (StateTracker, ContextPersistence, ContextUsageTracker,
ContextLineageTracker) use the same unified database and foreign key constraints work.
"""

import pytest
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime

from gao_dev.core.state.state_tracker import StateTracker
from gao_dev.core.state.migrations.migration_001_create_state_schema import Migration001
from gao_dev.core.context.context_persistence import ContextPersistence
from gao_dev.core.context.context_usage_tracker import ContextUsageTracker
from gao_dev.core.context.context_lineage import ContextLineageTracker
from gao_dev.core.context.workflow_context import WorkflowContext
from gao_dev.core.context.migrations.migration_003_unify_database import Migration003
from gao_dev.core.config import DatabaseConfig


@pytest.fixture
def unified_db(tmp_path: Path) -> Path:
    """Create unified database with full schema."""
    db_path = tmp_path / "gao_dev.db"

    # Initialize with state schema
    Migration001.upgrade(db_path)

    # Add context tables
    Migration003.upgrade(db_path, backup=False)

    return db_path


@pytest.fixture
def state_tracker(unified_db: Path) -> StateTracker:
    """Get StateTracker for unified database."""
    return StateTracker(unified_db)


@pytest.fixture
def context_persistence(unified_db: Path) -> ContextPersistence:
    """Get ContextPersistence for unified database."""
    return ContextPersistence(unified_db)


@pytest.fixture
def usage_tracker(unified_db: Path) -> ContextUsageTracker:
    """Get ContextUsageTracker for unified database."""
    return ContextUsageTracker(unified_db)


@pytest.fixture
def lineage_tracker(unified_db: Path) -> ContextLineageTracker:
    """Get ContextLineageTracker for unified database."""
    return ContextLineageTracker(unified_db)


class TestUnifiedDatabase:
    """Test that all tables are in single database."""

    def test_all_tables_exist(self, unified_db: Path):
        """Test that all expected tables exist in unified database."""
        conn = sqlite3.connect(str(unified_db))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        # State tables
        assert "epics" in tables
        assert "stories" in tables
        assert "sprints" in tables
        assert "story_assignments" in tables
        assert "workflow_executions" in tables
        assert "state_changes" in tables

        # Context tables
        assert "workflow_context" in tables
        assert "context_usage" in tables

    def test_foreign_keys_enabled(self, unified_db: Path):
        """Test that foreign keys can be enabled."""
        conn = sqlite3.connect(str(unified_db))
        # Enable foreign keys (must be done per connection in SQLite)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        conn.close()

        assert fk_enabled == 1, "Foreign keys should be enabled"

    def test_all_components_use_same_database(
        self,
        unified_db: Path,
        state_tracker: StateTracker,
        context_persistence: ContextPersistence,
        usage_tracker: ContextUsageTracker,
        lineage_tracker: ContextLineageTracker,
    ):
        """Test that all components point to same database file."""
        assert state_tracker.db_path == unified_db
        assert context_persistence.db_path == unified_db
        assert usage_tracker.db_path == unified_db
        assert lineage_tracker.db_path == unified_db


class TestForeignKeyConstraints:
    """Test foreign key constraints between tables."""

    def test_context_usage_references_workflow_context(
        self,
        unified_db: Path,
        context_persistence: ContextPersistence,
        lineage_tracker: ContextLineageTracker,
    ):
        """Test that context_usage.workflow_id FK to workflow_context works."""
        # Generate valid UUID for workflow_id
        workflow_id = str(uuid.uuid4())

        # Create workflow context
        context = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=1,
            story_num=1,
            feature="test-feature",
            workflow_name="test-workflow",
            current_phase="implementation",
        )
        context_persistence.save_context(context)

        # Record usage with valid workflow_id
        usage_id = lineage_tracker.record_usage(
            artifact_type="story",
            artifact_id="1.1",
            document_version="abc123",
            workflow_id=workflow_id,
        )
        assert usage_id > 0

        # Verify usage was recorded
        usage = lineage_tracker.get_workflow_context(workflow_id)
        assert len(usage) == 1
        assert usage[0]["workflow_id"] == workflow_id

    def test_cascade_delete_workflow_context(
        self,
        unified_db: Path,
        context_persistence: ContextPersistence,
        lineage_tracker: ContextLineageTracker,
    ):
        """Test that deleting workflow_context cascades to context_usage (SET NULL)."""
        # Generate valid UUID for workflow_id
        workflow_id = str(uuid.uuid4())

        # Create workflow context
        context = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=2,
            story_num=1,
            feature="test-feature",
            workflow_name="test-workflow",
            current_phase="implementation",
        )
        context_persistence.save_context(context)

        # Record usage
        lineage_tracker.record_usage(
            artifact_type="story",
            artifact_id="2.1",
            document_version="def456",
            workflow_id=workflow_id,
        )

        # Delete workflow context
        deleted = context_persistence.delete_context(workflow_id)
        assert deleted

        # Check that context_usage.workflow_id is set to NULL (not deleted)
        usage = lineage_tracker.get_artifact_context("story", "2.1")
        assert len(usage) == 1
        assert usage[0]["workflow_id"] is None  # FK ON DELETE SET NULL

    def test_invalid_workflow_id_allowed(
        self,
        unified_db: Path,
        lineage_tracker: ContextLineageTracker,
    ):
        """Test that context_usage allows NULL workflow_id (FK is nullable)."""
        # Record usage without workflow_id (NULL is allowed)
        usage_id = lineage_tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="ghi789",
            workflow_id=None,
        )
        assert usage_id > 0

        # Verify the usage was recorded
        usage = lineage_tracker.get_artifact_context("story", "3.1")
        assert len(usage) == 1
        assert usage[0]["workflow_id"] is None


class TestCrossComponentIntegration:
    """Test integration between StateTracker and Context components."""

    def test_workflow_execution_with_context(
        self,
        unified_db: Path,
        state_tracker: StateTracker,
        context_persistence: ContextPersistence,
    ):
        """Test creating workflow execution and associated context."""
        # Generate valid UUID for workflow_id
        workflow_id = str(uuid.uuid4())

        # Create epic and story
        epic = state_tracker.create_epic(
            epic_num=10,
            title="Test Epic",
            feature="test-feature",
        )
        story = state_tracker.create_story(
            epic_num=10,
            story_num=1,
            title="Test Story",
        )

        # Create workflow execution
        workflow_exec = state_tracker.track_workflow_execution(
            workflow_id=workflow_id,
            epic_num=10,
            story_num=1,
            workflow_name="story-implementation",
        )
        assert workflow_exec.workflow_id == workflow_id

        # Create workflow context with same ID
        context = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=10,
            story_num=1,
            feature="test-feature",
            workflow_name="story-implementation",
            current_phase="implementation",
        )
        version = context_persistence.save_context(context)
        assert version == 1

        # Verify both exist
        loaded_context = context_persistence.load_context(workflow_id)
        assert loaded_context.workflow_id == workflow_id
        assert loaded_context.epic_num == 10
        assert loaded_context.story_num == 1

    def test_full_lineage_tracking(
        self,
        unified_db: Path,
        state_tracker: StateTracker,
        context_persistence: ContextPersistence,
        lineage_tracker: ContextLineageTracker,
    ):
        """Test full lineage: Epic -> Story -> Workflow -> Context Usage."""
        # Generate valid UUID for workflow_id
        workflow_id = str(uuid.uuid4())

        # Create epic
        epic = state_tracker.create_epic(
            epic_num=20,
            title="Authentication",
            feature="user-management",
        )

        # Create story
        story = state_tracker.create_story(
            epic_num=20,
            story_num=1,
            title="Implement login",
            status="in_progress",
        )

        # Create workflow context
        context = WorkflowContext(
            workflow_id=workflow_id,
            epic_num=20,
            story_num=1,
            feature="user-management",
            workflow_name="implement-story",
            current_phase="implementation",
        )
        context_persistence.save_context(context)

        # Record document usage
        lineage_tracker.record_usage(
            artifact_type="story",
            artifact_id="20.1",
            document_version="arch-v1-abc123",
            document_type="architecture",
            document_path="docs/features/auth/ARCHITECTURE.md",
            workflow_id=workflow_id,
            epic=20,
            story="20.1",
        )

        lineage_tracker.record_usage(
            artifact_type="story",
            artifact_id="20.1",
            document_version="prd-v2-def456",
            document_type="prd",
            document_path="docs/features/auth/PRD.md",
            workflow_id=workflow_id,
            epic=20,
            story="20.1",
        )

        # Query lineage
        artifact_context = lineage_tracker.get_artifact_context("story", "20.1")
        assert len(artifact_context) == 2

        # Verify document types
        doc_types = {usage["document_type"] for usage in artifact_context}
        assert "architecture" in doc_types
        assert "prd" in doc_types

        # Get workflow context
        workflow_context = lineage_tracker.get_workflow_context(workflow_id)
        assert len(workflow_context) == 2


class TestDatabaseMigration:
    """Test migration from separate databases to unified database."""

    def test_migration_with_no_legacy_databases(self, tmp_path: Path):
        """Test migration when no legacy databases exist."""
        target_db = tmp_path / "gao_dev.db"

        # Run migration (should just create schema)
        Migration003.upgrade(target_db, backup=False)

        # Verify tables exist
        conn = sqlite3.connect(str(target_db))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('workflow_context', 'context_usage')"
        )
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "workflow_context" in tables
        assert "context_usage" in tables

    def test_migration_idempotent(self, tmp_path: Path):
        """Test that migration can be run multiple times safely."""
        target_db = tmp_path / "gao_dev.db"

        # Run migration twice
        Migration003.upgrade(target_db, backup=False)
        Migration003.upgrade(target_db, backup=False)

        # Verify tables still exist and are not duplicated
        conn = sqlite3.connect(str(target_db))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('workflow_context', 'context_usage')"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Should have exactly 2 tables (not duplicates)
        assert tables.count("workflow_context") == 1
        assert tables.count("context_usage") == 1


class TestDefaultDatabaseConfiguration:
    """Test DatabaseConfig default behavior."""

    def test_default_config_uses_cwd(self, tmp_path: Path, monkeypatch):
        """Test that default config uses current directory."""
        monkeypatch.chdir(tmp_path)

        config = DatabaseConfig.get_default()
        assert config.db_path == tmp_path / "gao_dev.db"

    def test_context_persistence_uses_default(self, tmp_path: Path, monkeypatch):
        """Test that ContextPersistence uses default database when no path provided."""
        monkeypatch.chdir(tmp_path)
        DatabaseConfig.reset_default()

        # Create with no explicit path
        persistence = ContextPersistence()

        # Should use default path
        expected_path = tmp_path / "gao_dev.db"
        assert persistence.db_path == expected_path

    def test_usage_tracker_uses_default(self, tmp_path: Path, monkeypatch):
        """Test that ContextUsageTracker uses default database when no path provided."""
        monkeypatch.chdir(tmp_path)
        DatabaseConfig.reset_default()

        # Create with no explicit path
        tracker = ContextUsageTracker()

        # Should use default path
        expected_path = tmp_path / "gao_dev.db"
        assert tracker.db_path == expected_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
