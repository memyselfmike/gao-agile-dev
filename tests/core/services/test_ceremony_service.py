"""
Tests for CeremonyService.

Epic: 24 - State Tables & Tracker
Story: 24.5
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

from gao_dev.core.services.ceremony_service import CeremonyService
from gao_dev.core.services.epic_state_service import EpicStateService


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
    """Create CeremonyService instance."""
    svc = CeremonyService(db_path=temp_db)
    yield svc
    svc.close()


class TestCeremonyServiceCreateSummary:
    """Tests for create_summary method."""

    def test_create_basic_summary(self, service):
        """Test creating a basic ceremony summary."""
        ceremony = service.create_summary(
            ceremony_type="retrospective",
            summary="Good sprint, completed all stories",
        )

        assert ceremony["ceremony_type"] == "retrospective"
        assert ceremony["summary"] == "Good sprint, completed all stories"

    def test_create_with_all_fields(self, service, temp_db):
        """Test creating summary with all fields."""
        # Create epic first for foreign key
        epic_svc = EpicStateService(db_path=temp_db)
        epic_svc.create(epic_num=25, title="Test Epic")
        epic_svc.close()

        ceremony = service.create_summary(
            ceremony_type="planning",
            summary="Planned Epic 25",
            participants="team",
            decisions="Use new architecture pattern",
            action_items="Create migration first",
            epic_num=25,
        )

        assert ceremony["participants"] == "team"
        assert ceremony["decisions"] == "Use new architecture pattern"
        assert ceremony["epic_num"] == 25


class TestCeremonyServiceGetRecent:
    """Tests for get_recent method."""

    def test_get_recent_all_types(self, service):
        """Test getting recent ceremonies of all types."""
        service.create_summary(ceremony_type="standup", summary="S1")
        service.create_summary(ceremony_type="review", summary="R1")
        service.create_summary(ceremony_type="retrospective", summary="Ret1")

        recent = service.get_recent(limit=10)

        assert len(recent) == 3

    def test_get_recent_by_type(self, service):
        """Test filtering recent ceremonies by type."""
        service.create_summary(ceremony_type="standup", summary="S1")
        service.create_summary(ceremony_type="standup", summary="S2")
        service.create_summary(ceremony_type="review", summary="R1")

        standups = service.get_recent(ceremony_type="standup", limit=10)

        assert len(standups) == 2
        assert all(c["ceremony_type"] == "standup" for c in standups)

    def test_get_recent_respects_limit(self, service):
        """Test that limit is respected."""
        for i in range(10):
            service.create_summary(ceremony_type="standup", summary=f"S{i}")

        recent = service.get_recent(limit=5)

        assert len(recent) == 5
