"""
Tests for EpicStateService.

Epic: 24 - State Tables & Tracker
Story: 24.2 - Implement EpicStateService
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


@pytest.fixture
def temp_db():
    """Create a temporary database with migration applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    # Apply migration
    conn = sqlite3.connect(str(db_path))

    # Create schema_version table
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

    # Apply migration 005
    Migration005.up(conn)
    conn.close()

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def service(temp_db):
    """Create EpicStateService instance."""
    svc = EpicStateService(db_path=temp_db)
    yield svc
    # Cleanup: close connection
    svc.close()


class TestEpicStateServiceCreate:
    """Tests for create method."""

    def test_create_basic_epic(self, service):
        """Test creating a basic epic."""
        epic = service.create(
            epic_num=1,
            title="User Authentication",
            status="planning",
            total_stories=5,
        )

        assert epic["epic_num"] == 1
        assert epic["title"] == "User Authentication"
        assert epic["status"] == "planning"
        assert epic["total_stories"] == 5
        assert epic["completed_stories"] == 0
        assert epic["progress_percentage"] == 0.0
        assert epic["created_at"] is not None
        assert epic["updated_at"] is not None

    def test_create_with_metadata(self, service):
        """Test creating epic with metadata."""
        epic = service.create(
            epic_num=2,
            title="API Gateway",
            metadata={"priority": "high", "team": "backend"},
        )

        assert epic["metadata"] is not None
        # Metadata is stored as JSON string
        import json
        metadata = json.loads(epic["metadata"])
        assert metadata["priority"] == "high"
        assert metadata["team"] == "backend"

    def test_create_duplicate_fails(self, service):
        """Test that creating duplicate epic fails."""
        service.create(epic_num=1, title="Epic 1")

        with pytest.raises(ValueError, match="already exists"):
            service.create(epic_num=1, title="Epic 1 Duplicate")

    def test_create_invalid_status_fails(self, service):
        """Test that invalid status fails."""
        with pytest.raises(ValueError, match="Invalid status"):
            service.create(epic_num=1, title="Epic 1", status="invalid_status")


class TestEpicStateServiceGet:
    """Tests for get method."""

    def test_get_existing_epic(self, service):
        """Test getting an existing epic."""
        created = service.create(epic_num=1, title="Epic 1")
        fetched = service.get(epic_num=1)

        assert fetched["epic_num"] == created["epic_num"]
        assert fetched["title"] == created["title"]

    def test_get_nonexistent_epic_fails(self, service):
        """Test that getting nonexistent epic fails."""
        with pytest.raises(ValueError, match="not found"):
            service.get(epic_num=999)


class TestEpicStateServiceUpdateProgress:
    """Tests for update_progress method."""

    def test_update_completed_stories(self, service):
        """Test updating completed stories count."""
        service.create(epic_num=1, title="Epic 1", total_stories=5)

        updated = service.update_progress(epic_num=1, completed_stories=2)

        assert updated["completed_stories"] == 2
        assert updated["progress_percentage"] == 40.0

    def test_update_progress_calculates_percentage(self, service):
        """Test that progress percentage is calculated correctly."""
        service.create(epic_num=1, title="Epic 1", total_stories=10)

        updated = service.update_progress(epic_num=1, completed_stories=7)

        assert updated["progress_percentage"] == 70.0

    def test_update_status(self, service):
        """Test updating epic status."""
        service.create(epic_num=1, title="Epic 1")

        updated = service.update_progress(epic_num=1, status="in_progress")

        assert updated["status"] == "in_progress"
        assert updated["started_at"] is not None

    def test_update_sets_started_at_automatically(self, service):
        """Test that started_at is set when moving to in_progress."""
        service.create(epic_num=1, title="Epic 1")

        updated = service.update_progress(epic_num=1, status="in_progress")

        assert updated["started_at"] is not None

    def test_update_sets_completed_at_automatically(self, service):
        """Test that completed_at is set when moving to completed."""
        service.create(epic_num=1, title="Epic 1", total_stories=5)

        updated = service.update_progress(
            epic_num=1, completed_stories=5, status="completed"
        )

        assert updated["completed_at"] is not None
        assert updated["progress_percentage"] == 100.0

    def test_update_with_blocked_reason(self, service):
        """Test updating epic with blocked reason."""
        service.create(epic_num=1, title="Epic 1")

        updated = service.update_progress(
            epic_num=1, status="blocked", blocked_reason="Waiting for API approval"
        )

        assert updated["status"] == "blocked"
        assert updated["blocked_reason"] == "Waiting for API approval"


class TestEpicStateServiceArchive:
    """Tests for archive method."""

    def test_archive_epic(self, service):
        """Test archiving an epic."""
        service.create(epic_num=1, title="Epic 1")

        archived = service.archive(epic_num=1, reason="All stories completed")

        assert archived["status"] == "archived"
        assert archived["blocked_reason"] == "All stories completed"

    def test_archive_nonexistent_epic_fails(self, service):
        """Test that archiving nonexistent epic fails."""
        with pytest.raises(ValueError, match="not found"):
            service.archive(epic_num=999)


class TestEpicStateServiceListActive:
    """Tests for list_active method."""

    def test_list_active_excludes_archived(self, service):
        """Test that list_active excludes archived epics."""
        service.create(epic_num=1, title="Epic 1", status="planning")
        service.create(epic_num=2, title="Epic 2", status="in_progress")
        service.create(epic_num=3, title="Epic 3", status="archived")

        active = service.list_active()

        assert len(active) == 2
        assert all(e["status"] != "archived" for e in active)

    def test_list_active_empty(self, service):
        """Test list_active when no epics exist."""
        active = service.list_active()

        assert active == []

    def test_list_active_ordered_by_epic_num(self, service):
        """Test that list_active returns epics ordered by epic_num."""
        service.create(epic_num=3, title="Epic 3")
        service.create(epic_num=1, title="Epic 1")
        service.create(epic_num=2, title="Epic 2")

        active = service.list_active()

        assert active[0]["epic_num"] == 1
        assert active[1]["epic_num"] == 2
        assert active[2]["epic_num"] == 3
