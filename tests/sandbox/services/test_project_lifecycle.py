"""Tests for ProjectLifecycleService."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime
import yaml

from gao_dev.sandbox.services.project_lifecycle import ProjectLifecycleService
from gao_dev.sandbox.services.project_state import ProjectStateService
from gao_dev.sandbox.models import ProjectStatus, ProjectMetadata
from gao_dev.sandbox.exceptions import (
    ProjectExistsError,
    ProjectNotFoundError,
    InvalidProjectNameError,
)


@pytest.fixture
def state_service(tmp_path):
    """Create real ProjectStateService instance."""
    return ProjectStateService(sandbox_root=tmp_path / "sandbox")


@pytest.fixture
def mock_boilerplate_service():
    """Create mock BoilerplateService."""
    return MagicMock()


@pytest.fixture
def lifecycle_service(tmp_path, state_service, mock_boilerplate_service):
    """Create ProjectLifecycleService instance with real state service."""
    return ProjectLifecycleService(
        sandbox_root=tmp_path / "sandbox",
        state_service=state_service,
        boilerplate_service=mock_boilerplate_service,
    )


class TestProjectLifecycleServiceInit:
    """Tests for ProjectLifecycleService initialization."""

    def test_init_creates_projects_directory(self, tmp_path, state_service):
        """Test that initialization creates projects directory."""
        service = ProjectLifecycleService(
            sandbox_root=tmp_path / "sandbox",
            state_service=state_service,
        )

        assert service.projects_dir.exists()
        assert service.projects_dir.is_dir()

    def test_init_resolves_path(self, tmp_path, state_service):
        """Test that initialization resolves relative paths."""
        service = ProjectLifecycleService(
            sandbox_root=tmp_path / "sandbox",
            state_service=state_service,
        )

        assert service.sandbox_root.is_absolute()


class TestCreateProject:
    """Tests for create_project method."""

    def test_create_project_minimal(self, lifecycle_service):
        """Test creating project with minimal parameters."""
        metadata = lifecycle_service.create_project(name="test-project")

        assert metadata.name == "test-project"
        assert metadata.status == ProjectStatus.ACTIVE

    def test_create_project_with_all_parameters(self, lifecycle_service):
        """Test creating project with all parameters."""
        metadata = lifecycle_service.create_project(
            name="test-project",
            description="Test project",
            tags=["test", "benchmark"],
        )

        assert metadata.name == "test-project"
        assert metadata.tags == ["test", "benchmark"]
        assert metadata.description == "Test project"

    def test_create_project_creates_directory(self, lifecycle_service):
        """Test that project directory is created."""
        lifecycle_service.create_project(name="test-project")

        project_dir = lifecycle_service.get_project_path("test-project")
        assert project_dir.exists()
        assert project_dir.is_dir()

    def test_create_project_already_exists(self, lifecycle_service):
        """Test that creating project twice raises error."""
        # Create first project
        lifecycle_service.create_project(name="test-project")

        # Verify it exists and attempting to create again raises error
        assert lifecycle_service.project_exists("test-project")

        with pytest.raises(ProjectExistsError):
            lifecycle_service.create_project(name="test-project")

    def test_create_project_invalid_name_too_short(self, lifecycle_service):
        """Test that invalid short names are rejected."""
        with pytest.raises(InvalidProjectNameError):
            lifecycle_service.create_project(name="ab")

    def test_create_project_invalid_name_too_long(self, lifecycle_service):
        """Test that names longer than 50 chars are rejected."""
        with pytest.raises(InvalidProjectNameError):
            lifecycle_service.create_project(name="a" * 51)

    def test_create_project_invalid_name_uppercase(self, lifecycle_service):
        """Test that uppercase names are rejected."""
        with pytest.raises(InvalidProjectNameError):
            lifecycle_service.create_project(name="Test-Project")

    def test_create_project_invalid_name_special_chars(self, lifecycle_service):
        """Test that special characters are rejected."""
        with pytest.raises(InvalidProjectNameError):
            lifecycle_service.create_project(name="test_project")

    def test_create_project_with_boilerplate(self, lifecycle_service, mock_boilerplate_service):
        """Test creating project with boilerplate URL."""
        lifecycle_service.create_project(
            name="test-project",
            boilerplate_url="https://github.com/test/repo.git",
        )

        mock_boilerplate_service.clone_boilerplate.assert_called_once()

    def test_create_project_cleanup_on_failure(self, lifecycle_service, mock_boilerplate_service):
        """Test that project directory is cleaned up on failure."""
        mock_boilerplate_service.clone_boilerplate.side_effect = Exception("Clone failed")

        with pytest.raises(Exception):
            lifecycle_service.create_project(
                name="test-project",
                boilerplate_url="https://github.com/test/repo.git",
            )

        # Project directory should be cleaned up
        project_dir = lifecycle_service.get_project_path("test-project")
        assert not project_dir.exists()


class TestProjectOperations:
    """Tests for project operations."""

    def test_project_exists_true(self, lifecycle_service):
        """Test checking if project exists (positive case)."""
        metadata = lifecycle_service.create_project(name="test-project")

        # Verify the project was actually created and metadata exists
        project_dir = lifecycle_service.get_project_path("test-project")
        assert (project_dir / ".sandbox.yaml").exists()

        assert lifecycle_service.project_exists("test-project") is True

    def test_project_exists_false(self, lifecycle_service):
        """Test checking if project exists (negative case)."""
        assert lifecycle_service.project_exists("nonexistent") is False

    def test_get_project_path(self, lifecycle_service):
        """Test getting project path."""
        lifecycle_service.create_project(name="test-project")

        path = lifecycle_service.get_project_path("test-project")

        assert "test-project" in str(path)
        assert path.is_absolute()

    def test_delete_project(self, lifecycle_service):
        """Test deleting a project."""
        # Create project
        lifecycle_service.create_project(name="test-project")
        project_dir = lifecycle_service.get_project_path("test-project")
        assert (project_dir / ".sandbox.yaml").exists()

        assert lifecycle_service.project_exists("test-project") is True

        lifecycle_service.delete_project("test-project")

        # Project directory should be deleted
        assert not project_dir.exists()
        assert lifecycle_service.project_exists("test-project") is False

    def test_delete_nonexistent_project(self, lifecycle_service):
        """Test deleting nonexistent project raises error."""
        with pytest.raises(ProjectNotFoundError):
            lifecycle_service.delete_project("nonexistent")

    def test_list_projects_empty(self, lifecycle_service):
        """Test listing projects when none exist."""
        projects = lifecycle_service.list_projects()

        assert isinstance(projects, list)
        assert len(projects) == 0

    def test_list_projects_multiple(self, lifecycle_service):
        """Test listing multiple projects."""
        # Create multiple projects
        for i in range(3):
            lifecycle_service.create_project(name=f"test-project-{i}")

        # Now list them - the real service should find them
        projects = lifecycle_service.list_projects()

        assert len(projects) == 3
        assert any("test-project-0" in p.name for p in projects)
        assert any("test-project-1" in p.name for p in projects)
        assert any("test-project-2" in p.name for p in projects)

    def test_list_projects_with_status_filter(self, lifecycle_service):
        """Test listing projects with status filter."""
        # Create two projects with mocked metadata
        p1 = lifecycle_service.create_project(name="test-project-1")
        p2 = lifecycle_service.create_project(name="test-project-2")

        # Update one to COMPLETED status
        project_dir_2 = lifecycle_service.get_project_path("test-project-2")
        p2.status = ProjectStatus.COMPLETED
        lifecycle_service.state_service.save_metadata(project_dir_2, p2)

        # List only ACTIVE projects
        projects = lifecycle_service.list_projects(status=ProjectStatus.ACTIVE)

        # Should have 1 ACTIVE project
        assert len(projects) == 1
        assert projects[0].name == "test-project-1"


class TestProjectStructure:
    """Tests for project directory structure."""

    def test_create_project_structure(self, lifecycle_service):
        """Test that standard directory structure is created."""
        lifecycle_service.create_project(name="test-project")

        project_dir = lifecycle_service.get_project_path("test-project")

        expected_dirs = ["docs", "src", "tests", "benchmarks", ".gao-dev"]
        for dir_name in expected_dirs:
            assert (project_dir / dir_name).exists()
            assert (project_dir / dir_name).is_dir()
