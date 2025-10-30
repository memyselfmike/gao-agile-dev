"""Tests for ProjectStateService."""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock
import yaml

from gao_dev.sandbox.services.project_state import ProjectStateService
from gao_dev.sandbox.models import ProjectStatus, ProjectMetadata
from gao_dev.sandbox.exceptions import (
    ProjectNotFoundError,
    ProjectStateError,
)


METADATA_FILENAME = ".sandbox.yaml"


@pytest.fixture
def state_service(tmp_path):
    """Create ProjectStateService instance."""
    sandbox_root = tmp_path / "sandbox"
    sandbox_root.mkdir(parents=True, exist_ok=True)
    return ProjectStateService(sandbox_root)


@pytest.fixture
def mock_lifecycle_service():
    """Create mock ProjectLifecycleService."""
    service = MagicMock()
    service.project_exists = MagicMock(return_value=True)
    service.get_project_path = MagicMock(return_value=Path("/tmp/project"))
    return service


@pytest.fixture
def sample_metadata():
    """Create sample ProjectMetadata."""
    return ProjectMetadata(
        name="test-project",
        created_at=datetime.now(),
        status=ProjectStatus.ACTIVE,
        description="Test project",
        tags=["test"],
    )


class TestProjectStateServiceInit:
    """Tests for ProjectStateService initialization."""

    def test_init_sets_paths(self, tmp_path):
        """Test that initialization sets correct paths."""
        sandbox_root = tmp_path / "sandbox"
        service = ProjectStateService(sandbox_root)

        assert service.sandbox_root == sandbox_root.resolve()
        assert service.projects_dir == sandbox_root.resolve() / "projects"

    def test_init_resolves_path(self, tmp_path):
        """Test that initialization resolves relative paths."""
        service = ProjectStateService(tmp_path / "sandbox")

        assert service.sandbox_root.is_absolute()


class TestMetadataPersistence:
    """Tests for metadata loading and saving."""

    def test_save_metadata(self, state_service, tmp_path, sample_metadata):
        """Test saving metadata to file."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        state_service.save_metadata(project_dir, sample_metadata)

        metadata_file = project_dir / METADATA_FILENAME
        assert metadata_file.exists()

    def test_load_metadata(self, state_service, tmp_path, sample_metadata):
        """Test loading metadata from file."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        state_service.save_metadata(project_dir, sample_metadata)
        loaded = state_service.load_metadata(project_dir)

        assert loaded.name == sample_metadata.name
        assert loaded.status == sample_metadata.status
        assert loaded.description == sample_metadata.description

    def test_load_metadata_file_not_found(self, state_service, tmp_path):
        """Test loading metadata when file doesn't exist."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            state_service.load_metadata(project_dir)

    def test_load_metadata_invalid_file(self, state_service, tmp_path):
        """Test loading invalid metadata file."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        metadata_file = project_dir / METADATA_FILENAME
        with open(metadata_file, "w") as f:
            f.write("")  # Empty file

        with pytest.raises(ValueError):
            state_service.load_metadata(project_dir)

    def test_metadata_round_trip(self, state_service, tmp_path, sample_metadata):
        """Test that metadata survives save/load cycle."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Save
        state_service.save_metadata(project_dir, sample_metadata)

        # Load
        loaded = state_service.load_metadata(project_dir)

        # Verify all fields
        assert loaded.name == sample_metadata.name
        assert loaded.status == sample_metadata.status
        assert loaded.description == sample_metadata.description
        assert loaded.tags == sample_metadata.tags
        assert loaded.boilerplate_url == sample_metadata.boilerplate_url


class TestCreateMetadata:
    """Tests for creating metadata."""

    def test_create_metadata_minimal(self, state_service):
        """Test creating metadata with minimal parameters."""
        metadata = state_service.create_metadata(name="test-project")

        assert metadata.name == "test-project"
        assert metadata.status == ProjectStatus.ACTIVE
        assert metadata.description == ""
        assert metadata.tags == []
        assert metadata.boilerplate_url is None

    def test_create_metadata_with_all_parameters(self, state_service):
        """Test creating metadata with all parameters."""
        metadata = state_service.create_metadata(
            name="test-project",
            description="Test description",
            boilerplate_url="https://github.com/test/repo.git",
            tags=["test", "benchmark"],
        )

        assert metadata.name == "test-project"
        assert metadata.description == "Test description"
        assert metadata.boilerplate_url == "https://github.com/test/repo.git"
        assert metadata.tags == ["test", "benchmark"]

    def test_create_metadata_has_timestamps(self, state_service):
        """Test that created metadata has timestamps."""
        metadata = state_service.create_metadata(name="test-project")

        assert metadata.created_at is not None
        assert metadata.last_modified is not None
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.last_modified, datetime)


class TestStatusTransitions:
    """Tests for status transition validation."""

    def test_valid_transition_active_to_completed(self, state_service):
        """Test valid transition from ACTIVE to COMPLETED."""
        assert state_service._is_valid_transition(
            ProjectStatus.ACTIVE,
            ProjectStatus.COMPLETED,
        ) is True

    def test_valid_transition_active_to_failed(self, state_service):
        """Test valid transition from ACTIVE to FAILED."""
        assert state_service._is_valid_transition(
            ProjectStatus.ACTIVE,
            ProjectStatus.FAILED,
        ) is True

    def test_valid_transition_same_status(self, state_service):
        """Test that same status is always valid."""
        assert state_service._is_valid_transition(
            ProjectStatus.ACTIVE,
            ProjectStatus.ACTIVE,
        ) is True

    def test_invalid_transition_completed_to_failed(self, state_service):
        """Test invalid transition from COMPLETED to FAILED."""
        assert state_service._is_valid_transition(
            ProjectStatus.COMPLETED,
            ProjectStatus.FAILED,
        ) is False

    def test_invalid_transition_failed_to_completed(self, state_service):
        """Test invalid transition from FAILED to COMPLETED."""
        assert state_service._is_valid_transition(
            ProjectStatus.FAILED,
            ProjectStatus.COMPLETED,
        ) is False


class TestUpdateStatus:
    """Tests for updating project status."""

    def test_update_status_valid_transition(
        self, state_service, tmp_path, mock_lifecycle_service, sample_metadata
    ):
        """Test updating status with valid transition."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        sample_metadata.status = ProjectStatus.ACTIVE
        state_service.save_metadata(project_dir, sample_metadata)

        mock_lifecycle_service.get_project_path.return_value = project_dir
        mock_lifecycle_service.project_exists.return_value = True

        updated = state_service.update_status(
            "test-project",
            ProjectStatus.COMPLETED,
            "Completed successfully",
            mock_lifecycle_service,
        )

        assert updated.status == ProjectStatus.COMPLETED

    def test_update_status_invalid_transition(
        self, state_service, tmp_path, mock_lifecycle_service, sample_metadata
    ):
        """Test updating status with invalid transition."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        sample_metadata.status = ProjectStatus.COMPLETED
        state_service.save_metadata(project_dir, sample_metadata)

        mock_lifecycle_service.get_project_path.return_value = project_dir
        mock_lifecycle_service.project_exists.return_value = True

        with pytest.raises(ProjectStateError):
            state_service.update_status(
                "test-project",
                ProjectStatus.FAILED,
                None,
                mock_lifecycle_service,
            )

    def test_update_status_nonexistent_project(
        self, state_service, mock_lifecycle_service
    ):
        """Test updating status of nonexistent project."""
        mock_lifecycle_service.project_exists.return_value = False

        with pytest.raises(ProjectNotFoundError):
            state_service.update_status(
                "nonexistent",
                ProjectStatus.COMPLETED,
                None,
                mock_lifecycle_service,
            )


class TestUpdateProject:
    """Tests for updating project metadata."""

    def test_update_project(
        self, state_service, tmp_path, mock_lifecycle_service, sample_metadata
    ):
        """Test updating project metadata."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        state_service.save_metadata(project_dir, sample_metadata)

        mock_lifecycle_service.get_project_path.return_value = project_dir
        mock_lifecycle_service.project_exists.return_value = True

        sample_metadata.description = "Updated description"
        state_service.update_project(
            "test-project",
            sample_metadata,
            mock_lifecycle_service,
        )

        loaded = state_service.load_metadata(project_dir)
        assert loaded.description == "Updated description"

    def test_update_project_nonexistent(
        self, state_service, mock_lifecycle_service, sample_metadata
    ):
        """Test updating nonexistent project raises error."""
        mock_lifecycle_service.project_exists.return_value = False

        with pytest.raises(ProjectNotFoundError):
            state_service.update_project(
                "nonexistent",
                sample_metadata,
                mock_lifecycle_service,
            )


class TestGetProject:
    """Tests for getting project metadata."""

    def test_get_project(
        self, state_service, tmp_path, mock_lifecycle_service, sample_metadata
    ):
        """Test getting project metadata."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        state_service.save_metadata(project_dir, sample_metadata)

        mock_lifecycle_service.get_project_path.return_value = project_dir
        mock_lifecycle_service.project_exists.return_value = True

        metadata = state_service.get_project("test-project", mock_lifecycle_service)

        assert metadata.name == "test-project"
        assert metadata.status == ProjectStatus.ACTIVE

    def test_get_project_nonexistent(self, state_service, mock_lifecycle_service):
        """Test getting nonexistent project raises error."""
        mock_lifecycle_service.project_exists.return_value = False

        with pytest.raises(ProjectNotFoundError):
            state_service.get_project("nonexistent", mock_lifecycle_service)
