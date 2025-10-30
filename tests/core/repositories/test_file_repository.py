"""Tests for file-based repositories."""

import pytest
from pathlib import Path

from gao_dev.core.repositories.file_repository import FileRepository, StateRepository


class TestFileRepository:
    """Tests for FileRepository base class."""

    @pytest.fixture
    def repo(self, tmp_path):
        """Create test repository."""
        return FileRepository(tmp_path / "test_repo", ".yaml")

    def test_save_and_get(self, repo):
        """Test saving and retrieving data."""
        data = {"key": "value", "number": 42}
        repo.save("test_entity", data)

        retrieved = repo.get("test_entity")
        assert retrieved == data

    def test_exists(self, repo):
        """Test entity existence check."""
        assert not repo.exists("nonexistent")

        repo.save("test", {"data": "value"})
        assert repo.exists("test")

    def test_delete(self, repo):
        """Test entity deletion."""
        repo.save("test", {"data": "value"})
        assert repo.exists("test")

        assert repo.delete("test") is True
        assert not repo.exists("test")

    def test_delete_nonexistent_returns_false(self, repo):
        """Test deleting non-existent entity returns False."""
        assert repo.delete("nonexistent") is False

    def test_update(self, repo):
        """Test updating existing entity."""
        repo.save("test", {"version": 1})
        assert repo.update("test", {"version": 2}) is True

        updated = repo.get("test")
        assert updated["version"] == 2

    def test_update_nonexistent_returns_false(self, repo):
        """Test updating non-existent entity returns False."""
        assert repo.update("nonexistent", {}) is False

    def test_list_all(self, repo):
        """Test listing all entities."""
        assert repo.list_all() == []

        repo.save("entity1", {"data": 1})
        repo.save("entity2", {"data": 2})

        entities = repo.list_all()
        assert len(entities) == 2
        assert "entity1" in entities
        assert "entity2" in entities


class TestStateRepository:
    """Tests for StateRepository."""

    @pytest.fixture
    def repo(self, tmp_path):
        """Create test state repository."""
        return StateRepository(tmp_path / "states")

    def test_save_and_get_project_state(self, repo):
        """Test saving and getting project state."""
        state = {
            "project_name": "test_project",
            "status": "active",
            "created_at": "2025-10-29"
        }

        repo.save_project_state("test_project", state)

        retrieved = repo.get_project_state("test_project")
        assert retrieved == state

    def test_update_project_status(self, repo):
        """Test updating project status."""
        initial_state = {"status": "active"}
        repo.save_project_state("test_project", initial_state)

        assert repo.update_project_status("test_project", "completed") is True

        updated = repo.get_project_state("test_project")
        assert updated["status"] == "completed"

    def test_update_status_nonexistent_project_returns_false(self, repo):
        """Test updating status for non-existent project returns False."""
        assert repo.update_project_status("nonexistent", "active") is False
