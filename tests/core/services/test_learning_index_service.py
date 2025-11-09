"""
Tests for LearningIndexService.

Epic: 24 - State Tables & Tracker
Story: 24.6
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

from gao_dev.core.services.learning_index_service import LearningIndexService
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
    """Create LearningIndexService instance."""
    svc = LearningIndexService(db_path=temp_db)
    yield svc
    svc.close()


class TestLearningIndexServiceIndex:
    """Tests for index method."""

    def test_index_basic_learning(self, service):
        """Test indexing a basic learning."""
        learning = service.index(
            topic="Migrations",
            category="technical",
            learning="Use numbered migration files",
        )

        assert learning["topic"] == "Migrations"
        assert learning["category"] == "technical"
        assert learning["is_active"] == 1

    def test_index_with_all_fields(self, service, temp_db):
        """Test indexing with all fields."""
        # Create epic first for foreign key
        epic_svc = EpicStateService(db_path=temp_db)
        epic_svc.create(epic_num=24, title="Test Epic")
        epic_svc.close()

        learning = service.index(
            topic="Testing patterns",
            category="technical",
            learning="Use fixtures for database setup",
            context="Epic 24 implementation",
            source_type="code_review",
            epic_num=24,
            relevance_score=0.9,
            metadata={"impact": "high"},
        )

        assert learning["source_type"] == "code_review"
        assert learning["epic_num"] == 24
        assert learning["relevance_score"] == 0.9


class TestLearningIndexServiceSupersede:
    """Tests for supersede method."""

    def test_supersede_learning(self, service):
        """Test superseding a learning with newer one."""
        old = service.index(
            topic="Testing",
            category="technical",
            learning="Old approach",
        )
        new = service.index(
            topic="Testing",
            category="technical",
            learning="New approach",
        )

        superseded = service.supersede(old_id=old["id"], new_id=new["id"])

        assert superseded["is_active"] == 0
        assert superseded["superseded_by"] == new["id"]

    def test_supersede_nonexistent_fails(self, service):
        """Test that superseding with nonexistent new_id fails."""
        old = service.index(topic="Test", category="technical", learning="Old")

        with pytest.raises(ValueError, match="not found"):
            service.supersede(old_id=old["id"], new_id=999)


class TestLearningIndexServiceSearch:
    """Tests for search method."""

    def test_search_by_topic(self, service):
        """Test searching by topic."""
        service.index(topic="Database migrations", category="technical", learning="L1")
        service.index(topic="Testing patterns", category="technical", learning="L2")
        service.index(topic="Migration tools", category="technical", learning="L3")

        results = service.search(topic="migration")

        assert len(results) >= 2  # Should match "migrations" and "Migration"

    def test_search_by_category(self, service):
        """Test searching by category."""
        service.index(topic="T1", category="technical", learning="L1")
        service.index(topic="T2", category="process", learning="L2")
        service.index(topic="T3", category="technical", learning="L3")

        results = service.search(category="technical")

        assert len(results) == 2
        assert all(r["category"] == "technical" for r in results)

    def test_search_excludes_inactive(self, service):
        """Test that search excludes inactive learnings by default."""
        l1 = service.index(topic="T1", category="technical", learning="L1")
        l2 = service.index(topic="T2", category="technical", learning="L2")
        service.supersede(old_id=l1["id"], new_id=l2["id"])

        results = service.search(active_only=True)

        assert len(results) == 1
        assert results[0]["id"] == l2["id"]

    def test_search_ordered_by_relevance(self, service):
        """Test that search results are ordered by relevance."""
        service.index(topic="T1", category="technical", learning="L1", relevance_score=0.5)
        service.index(topic="T2", category="technical", learning="L2", relevance_score=0.9)
        service.index(topic="T3", category="technical", learning="L3", relevance_score=0.7)

        results = service.search()

        assert results[0]["relevance_score"] == 0.9
        assert results[1]["relevance_score"] == 0.7
        assert results[2]["relevance_score"] == 0.5
