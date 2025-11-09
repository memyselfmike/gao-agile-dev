"""
Tests for ActionItemService, CeremonyService, and LearningIndexService.

Epic: 24 - State Tables & Tracker
Stories: 24.4, 24.5, 24.6
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

from gao_dev.core.services.action_item_service import ActionItemService


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
    """Create ActionItemService instance."""
    svc = ActionItemService(db_path=temp_db)
    yield svc
    svc.close()


class TestActionItemServiceCreate:
    """Tests for create method."""

    def test_create_basic_item(self, service):
        """Test creating a basic action item."""
        item = service.create(title="Update documentation")

        assert item["title"] == "Update documentation"
        assert item["status"] == "pending"
        assert item["priority"] == "medium"

    def test_create_with_all_fields(self, service):
        """Test creating item with all fields."""
        item = service.create(
            title="Fix bug",
            description="Fix null pointer",
            priority="high",
            assignee="amelia",
            due_date="2025-11-15",
            metadata={"urgency": "critical"},
        )

        assert item["priority"] == "high"
        assert item["assignee"] == "amelia"
        assert item["due_date"] == "2025-11-15"


class TestActionItemServiceComplete:
    """Tests for complete method."""

    def test_complete_item(self, service):
        """Test completing an action item."""
        item = service.create(title="Task 1")

        completed = service.complete(item_id=item["id"])

        assert completed["status"] == "completed"
        assert completed["completed_at"] is not None


class TestActionItemServiceGetActive:
    """Tests for get_active method."""

    def test_get_active_items(self, service):
        """Test getting active action items."""
        service.create(title="Item 1", priority="high")
        service.create(title="Item 2", priority="low")
        item3 = service.create(title="Item 3")
        service.complete(item_id=item3["id"])

        active = service.get_active()

        assert len(active) == 2
        # High priority should come first
        assert active[0]["priority"] == "high"

    def test_get_active_by_assignee(self, service):
        """Test filtering active items by assignee."""
        service.create(title="Task 1", assignee="bob")
        service.create(title="Task 2", assignee="amelia")
        service.create(title="Task 3", assignee="bob")

        bob_items = service.get_active(assignee="bob")

        assert len(bob_items) == 2
        assert all(item["assignee"] == "bob" for item in bob_items)
