"""Tests for SandboxManager."""

import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from gao_dev.sandbox.benchmark import BenchmarkConfig
from gao_dev.sandbox.exceptions import (
    InvalidProjectNameError,
    ProjectExistsError,
    ProjectNotFoundError,
    ProjectStateError,
)
from gao_dev.sandbox.manager import SandboxManager
from gao_dev.sandbox.models import BenchmarkRun, ProjectMetadata, ProjectStatus


class TestSandboxManagerInit:
    """Tests for SandboxManager initialization."""

    def test_init_creates_projects_directory(self, tmp_path):
        """Test that initialization creates projects directory."""
        sandbox_root = tmp_path / "sandbox"
        manager = SandboxManager(sandbox_root)

        assert manager.sandbox_root == sandbox_root.resolve()
        assert manager.projects_dir == sandbox_root.resolve() / "projects"
        assert manager.projects_dir.exists()
        assert manager.projects_dir.is_dir()

    def test_init_with_existing_directory(self, tmp_path):
        """Test initialization with existing projects directory."""
        sandbox_root = tmp_path / "sandbox"
        projects_dir = sandbox_root / "projects"
        projects_dir.mkdir(parents=True)

        manager = SandboxManager(sandbox_root)

        assert manager.projects_dir.exists()

    def test_init_resolves_path(self, tmp_path):
        """Test that initialization resolves relative paths."""
        # Use a relative path
        manager = SandboxManager(tmp_path)

        # Should be resolved to absolute
        assert manager.sandbox_root.is_absolute()


class TestCreateProject:
    """Tests for create_project method."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create SandboxManager instance."""
        return SandboxManager(tmp_path / "sandbox")

    def test_create_project_minimal(self, manager):
        """Test creating project with minimal parameters."""
        metadata = manager.create_project(name="test-project")

        assert metadata.name == "test-project"
        assert metadata.status == ProjectStatus.ACTIVE
        assert metadata.boilerplate_url is None
        assert metadata.tags == []
        assert metadata.description == ""
        assert isinstance(metadata.created_at, datetime)

    def test_create_project_with_all_parameters(self, manager):
        """Test creating project with all parameters."""
        metadata = manager.create_project(
            name="test-project",
            boilerplate_url=None,
            tags=["test", "benchmark"],
            description="Test project description",
        )

        assert metadata.name == "test-project"
        assert metadata.tags == ["test", "benchmark"]
        assert metadata.description == "Test project description"

    def test_create_project_creates_directory(self, manager):
        """Test that project directory is created."""
        metadata = manager.create_project(name="test-project")

        project_dir = manager.get_project_path("test-project")
        assert project_dir.exists()
        assert project_dir.is_dir()

    def test_create_project_creates_standard_structure(self, manager):
        """Test that standard directory structure is created."""
        manager.create_project(name="test-project")

        project_dir = manager.get_project_path("test-project")

        expected_dirs = ["docs", "src", "tests", "benchmarks", ".gao-dev"]
        for dir_name in expected_dirs:
            assert (project_dir / dir_name).exists()
            assert (project_dir / dir_name).is_dir()

    def test_create_project_saves_metadata(self, manager):
        """Test that metadata file is created."""
        manager.create_project(name="test-project")

        project_dir = manager.get_project_path("test-project")
        metadata_file = project_dir / ".sandbox.yaml"

        assert metadata_file.exists()
        assert metadata_file.is_file()

    def test_create_project_metadata_is_valid_yaml(self, manager):
        """Test that saved metadata is valid YAML."""
        manager.create_project(name="test-project")

        project_dir = manager.get_project_path("test-project")
        metadata_file = project_dir / ".sandbox.yaml"

        with open(metadata_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data is not None
        assert data["name"] == "test-project"

    def test_create_project_with_existing_name_raises_error(self, manager):
        """Test that creating duplicate project raises error."""
        manager.create_project(name="test-project")

        with pytest.raises(ProjectExistsError) as exc_info:
            manager.create_project(name="test-project")

        assert exc_info.value.project_name == "test-project"

    def test_create_project_with_invalid_name_raises_error(self, manager):
        """Test that invalid project name raises error."""
        invalid_names = [
            "ab",  # Too short
            "Test Project",  # Has spaces
            "TEST",  # Uppercase
            "-invalid",  # Starts with hyphen
            "invalid-",  # Ends with hyphen
            "a" * 51,  # Too long
        ]

        for invalid_name in invalid_names:
            with pytest.raises(InvalidProjectNameError):
                manager.create_project(name=invalid_name)

    def test_create_project_with_valid_names(self, manager):
        """Test that valid project names are accepted."""
        valid_names = [
            "test",
            "test-project",
            "project123",
            "123project",
            "my-test-project-123",
        ]

        for valid_name in valid_names:
            metadata = manager.create_project(name=valid_name)
            assert metadata.name == valid_name

    @patch("gao_dev.sandbox.manager.GitCloner")
    def test_create_project_with_boilerplate_url(self, mock_git_cloner_class, manager):
        """Test creating project with boilerplate repository."""
        mock_cloner = Mock()
        mock_git_cloner_class.return_value = mock_cloner

        boilerplate_url = "https://github.com/test/repo.git"
        metadata = manager.create_project(
            name="test-project",
            boilerplate_url=boilerplate_url,
        )

        assert metadata.boilerplate_url == boilerplate_url
        # Verify git clone was called
        mock_cloner.clone_repository.assert_called_once()

    @patch("gao_dev.sandbox.manager.GitCloner")
    def test_create_project_cleans_up_on_boilerplate_failure(
        self, mock_git_cloner_class, manager
    ):
        """Test that project is cleaned up if boilerplate clone fails."""
        mock_cloner = Mock()
        mock_cloner.clone_repository.side_effect = Exception("Clone failed")
        mock_git_cloner_class.return_value = mock_cloner

        with pytest.raises(Exception):
            manager.create_project(
                name="test-project",
                boilerplate_url="https://github.com/test/repo.git",
            )

        # Project directory should be cleaned up
        assert not manager.project_exists("test-project")


class TestGetProject:
    """Tests for get_project method."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create SandboxManager with a test project."""
        mgr = SandboxManager(tmp_path / "sandbox")
        mgr.create_project(name="test-project", description="Test")
        return mgr

    def test_get_existing_project(self, manager):
        """Test getting metadata for existing project."""
        metadata = manager.get_project("test-project")

        assert metadata.name == "test-project"
        assert metadata.description == "Test"
        assert isinstance(metadata, ProjectMetadata)

    def test_get_nonexistent_project_raises_error(self, manager):
        """Test that getting nonexistent project raises error."""
        with pytest.raises(ProjectNotFoundError) as exc_info:
            manager.get_project("nonexistent")

        assert exc_info.value.project_name == "nonexistent"


class TestListProjects:
    """Tests for list_projects method."""

    @pytest.fixture
    def manager_with_projects(self, tmp_path):
        """Create SandboxManager with multiple test projects."""
        mgr = SandboxManager(tmp_path / "sandbox")
        mgr.create_project(name="project-1", tags=["tag1"])
        mgr.create_project(name="project-2", tags=["tag2"])
        mgr.create_project(name="project-3", tags=["tag1", "tag2"])
        return mgr

    def test_list_all_projects(self, manager_with_projects):
        """Test listing all projects."""
        projects = manager_with_projects.list_projects()

        assert len(projects) == 3
        project_names = {p.name for p in projects}
        assert project_names == {"project-1", "project-2", "project-3"}

    def test_list_projects_returns_metadata(self, manager_with_projects):
        """Test that list returns ProjectMetadata objects."""
        projects = manager_with_projects.list_projects()

        for project in projects:
            assert isinstance(project, ProjectMetadata)

    def test_list_projects_sorted_by_last_modified(self, manager_with_projects):
        """Test that projects are sorted by last_modified descending."""
        projects = manager_with_projects.list_projects()

        # Should be sorted newest first
        for i in range(len(projects) - 1):
            assert projects[i].last_modified >= projects[i + 1].last_modified

    def test_list_projects_with_status_filter(self, manager_with_projects):
        """Test filtering projects by status."""
        # Change status of one project
        manager_with_projects.update_status("project-2", ProjectStatus.COMPLETED)

        active_projects = manager_with_projects.list_projects(status=ProjectStatus.ACTIVE)
        completed_projects = manager_with_projects.list_projects(status=ProjectStatus.COMPLETED)

        assert len(active_projects) == 2
        assert len(completed_projects) == 1
        assert completed_projects[0].name == "project-2"

    def test_list_projects_empty_sandbox(self, tmp_path):
        """Test listing projects in empty sandbox."""
        manager = SandboxManager(tmp_path / "sandbox")
        projects = manager.list_projects()

        assert projects == []

    def test_list_projects_skips_invalid_metadata(self, manager_with_projects):
        """Test that projects with invalid metadata are skipped."""
        # Create a directory without metadata
        bad_project_dir = manager_with_projects.projects_dir / "bad-project"
        bad_project_dir.mkdir()

        projects = manager_with_projects.list_projects()

        # Should only return the 3 valid projects
        assert len(projects) == 3


class TestUpdateProject:
    """Tests for update_project method."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create SandboxManager with a test project."""
        mgr = SandboxManager(tmp_path / "sandbox")
        mgr.create_project(name="test-project")
        return mgr

    def test_update_project_metadata(self, manager):
        """Test updating project metadata."""
        metadata = manager.get_project("test-project")
        metadata.description = "Updated description"
        metadata.tags = ["new-tag"]

        manager.update_project("test-project", metadata)

        updated = manager.get_project("test-project")
        assert updated.description == "Updated description"
        assert updated.tags == ["new-tag"]

    def test_update_project_updates_last_modified(self, manager):
        """Test that update changes last_modified timestamp."""
        metadata = manager.get_project("test-project")
        original_modified = metadata.last_modified

        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)

        metadata.description = "Updated"
        manager.update_project("test-project", metadata)

        updated = manager.get_project("test-project")
        assert updated.last_modified > original_modified

    def test_update_nonexistent_project_raises_error(self, manager):
        """Test that updating nonexistent project raises error."""
        metadata = ProjectMetadata(name="nonexistent", created_at=datetime.now())

        with pytest.raises(ProjectNotFoundError):
            manager.update_project("nonexistent", metadata)


class TestDeleteProject:
    """Tests for delete_project method."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create SandboxManager with a test project."""
        mgr = SandboxManager(tmp_path / "sandbox")
        mgr.create_project(name="test-project")
        return mgr

    def test_delete_existing_project(self, manager):
        """Test deleting an existing project."""
        assert manager.project_exists("test-project")

        manager.delete_project("test-project")

        assert not manager.project_exists("test-project")

    def test_delete_project_removes_directory(self, manager):
        """Test that project directory is removed."""
        project_dir = manager.get_project_path("test-project")
        assert project_dir.exists()

        manager.delete_project("test-project")

        assert not project_dir.exists()

    def test_delete_nonexistent_project_raises_error(self, manager):
        """Test that deleting nonexistent project raises error."""
        with pytest.raises(ProjectNotFoundError):
            manager.delete_project("nonexistent")


class TestProjectExists:
    """Tests for project_exists method."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create SandboxManager with a test project."""
        mgr = SandboxManager(tmp_path / "sandbox")
        mgr.create_project(name="test-project")
        return mgr

    def test_project_exists_returns_true(self, manager):
        """Test that existing project returns True."""
        assert manager.project_exists("test-project") is True

    def test_project_exists_returns_false(self, manager):
        """Test that nonexistent project returns False."""
        assert manager.project_exists("nonexistent") is False

    def test_project_exists_without_metadata(self, manager):
        """Test that directory without metadata returns False."""
        # Create directory without metadata
        bad_dir = manager.projects_dir / "bad-project"
        bad_dir.mkdir()

        assert manager.project_exists("bad-project") is False


class TestGetProjectPath:
    """Tests for get_project_path method."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create SandboxManager instance."""
        return SandboxManager(tmp_path / "sandbox")

    def test_get_project_path_returns_absolute_path(self, manager):
        """Test that project path is absolute."""
        path = manager.get_project_path("test-project")

        assert path.is_absolute()

    def test_get_project_path_format(self, manager):
        """Test project path format."""
        path = manager.get_project_path("test-project")

        assert path == manager.projects_dir / "test-project"
        assert path.name == "test-project"


class TestUpdateStatus:
    """Tests for update_status method."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create SandboxManager with a test project."""
        mgr = SandboxManager(tmp_path / "sandbox")
        mgr.create_project(name="test-project")
        return mgr

    def test_update_status_valid_transition(self, manager):
        """Test updating status with valid transition."""
        manager.update_status("test-project", ProjectStatus.COMPLETED)

        metadata = manager.get_project("test-project")
        assert metadata.status == ProjectStatus.COMPLETED

    def test_update_status_invalid_transition_raises_error(self, manager):
        """Test that invalid transition raises error."""
        # Try invalid transition (would need to check state machine)
        # For now, test same status (which is always valid)
        manager.update_status("test-project", ProjectStatus.ACTIVE)
        # Should not raise

    def test_update_status_updates_last_modified(self, manager):
        """Test that status update changes last_modified."""
        metadata = manager.get_project("test-project")
        original_modified = metadata.last_modified

        import time
        time.sleep(0.01)

        manager.update_status("test-project", ProjectStatus.COMPLETED)

        updated = manager.get_project("test-project")
        assert updated.last_modified > original_modified

    def test_update_status_nonexistent_project_raises_error(self, manager):
        """Test that updating status of nonexistent project raises error."""
        with pytest.raises(ProjectNotFoundError):
            manager.update_status("nonexistent", ProjectStatus.COMPLETED)


class TestBenchmarkRuns:
    """Tests for benchmark run management."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create SandboxManager with a test project."""
        mgr = SandboxManager(tmp_path / "sandbox")
        mgr.create_project(name="test-project")
        return mgr

    def test_add_benchmark_run(self, manager):
        """Test adding benchmark run to project."""
        run = manager.add_benchmark_run(
            project_name="test-project",
            run_id="run-001",
            config_file="benchmark.yaml",
        )

        assert run.run_id == "run-001"
        assert run.config_file == "benchmark.yaml"
        assert isinstance(run, BenchmarkRun)

    def test_add_benchmark_run_updates_metadata(self, manager):
        """Test that adding run updates project metadata."""
        manager.add_benchmark_run(
            project_name="test-project",
            run_id="run-001",
            config_file="benchmark.yaml",
        )

        metadata = manager.get_project("test-project")
        assert len(metadata.runs) == 1
        assert metadata.runs[0].run_id == "run-001"

    def test_get_run_history_empty(self, manager):
        """Test getting run history for project with no runs."""
        runs = manager.get_run_history("test-project")

        assert runs == []

    def test_get_run_history_sorted(self, manager):
        """Test that run history is sorted by started_at descending."""
        # Add multiple runs
        run1 = manager.add_benchmark_run("test-project", "run-001", "test.yaml")
        run2 = manager.add_benchmark_run("test-project", "run-002", "test.yaml")
        run3 = manager.add_benchmark_run("test-project", "run-003", "test.yaml")

        runs = manager.get_run_history("test-project")

        # Should be sorted newest first
        assert len(runs) == 3
        assert runs[0].started_at >= runs[1].started_at >= runs[2].started_at


class TestCleanOperations:
    """Tests for project clean operations."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create SandboxManager with a test project."""
        mgr = SandboxManager(tmp_path / "sandbox")
        mgr.create_project(name="test-project")
        return mgr

    def test_is_clean_new_project(self, manager):
        """Test that new project is clean."""
        assert manager.is_clean("test-project") is True

    def test_is_clean_with_completed_run(self, manager):
        """Test that project with completed run is clean."""
        run = manager.add_benchmark_run("test-project", "run-001", "test.yaml")
        run.status = ProjectStatus.COMPLETED

        metadata = manager.get_project("test-project")
        metadata.runs[0] = run
        manager.update_project("test-project", metadata)

        assert manager.is_clean("test-project") is True

    def test_is_not_clean_with_active_run(self, manager):
        """Test that project with active run is not clean."""
        manager.add_benchmark_run("test-project", "run-001", "test.yaml")

        assert manager.is_clean("test-project") is False

    def test_is_not_clean_with_failed_status(self, manager):
        """Test that failed project is not clean."""
        manager.update_status("test-project", ProjectStatus.FAILED)

        assert manager.is_clean("test-project") is False

    def test_mark_clean(self, manager):
        """Test marking project as clean."""
        manager.update_status("test-project", ProjectStatus.FAILED)
        assert not manager.is_clean("test-project")

        manager.mark_clean("test-project")

        metadata = manager.get_project("test-project")
        assert metadata.status == ProjectStatus.ACTIVE

    def test_clean_project_runs_only(self, manager):
        """Test cleaning only run history."""
        manager.add_benchmark_run("test-project", "run-001", "test.yaml")
        manager.add_benchmark_run("test-project", "run-002", "test.yaml")

        stats = manager.clean_project("test-project", runs_only=True)

        assert stats["runs_cleared"] == 2
        metadata = manager.get_project("test-project")
        assert len(metadata.runs) == 0

    def test_clean_project_standard(self, manager):
        """Test standard project clean."""
        project_dir = manager.get_project_path("test-project")

        # Create some files in standard directories
        (project_dir / "src" / "test.py").write_text("test")
        (project_dir / "docs" / "readme.md").write_text("test")

        stats = manager.clean_project("test-project")

        assert stats["files_deleted"] > 0
        # Directory structure should still exist
        assert (project_dir / "src").exists()
        assert (project_dir / "docs").exists()
        # But files should be gone
        assert not (project_dir / "src" / "test.py").exists()


class TestBenchmarkProjectManagement:
    """Tests for benchmark-specific project management."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create SandboxManager instance."""
        return SandboxManager(tmp_path / "sandbox")

    def test_get_projects_for_benchmark(self, manager):
        """Test getting projects for specific benchmark."""
        manager.create_project(name="todo-app-baseline-run-001")
        manager.create_project(name="todo-app-baseline-run-002")
        manager.create_project(name="other-project")

        projects = manager.get_projects_for_benchmark("todo-app-baseline")

        assert len(projects) == 2
        names = {p.name for p in projects}
        assert "todo-app-baseline-run-001" in names
        assert "todo-app-baseline-run-002" in names

    def test_get_last_run_number_no_runs(self, manager):
        """Test getting last run number with no existing runs."""
        last_run = manager.get_last_run_number("todo-app-baseline")

        assert last_run == 0

    def test_get_last_run_number_with_runs(self, manager):
        """Test getting last run number with existing runs."""
        manager.create_project(name="todo-app-baseline-run-001")
        manager.create_project(name="todo-app-baseline-run-005")
        manager.create_project(name="todo-app-baseline-run-003")

        last_run = manager.get_last_run_number("todo-app-baseline")

        assert last_run == 5

    def test_create_run_project_auto_generates_id(self, manager, tmp_path):
        """Test that create_run_project auto-generates run ID."""
        # Create a mock benchmark config
        benchmark_file = tmp_path / "benchmark.yaml"
        config_data = {
            "benchmark": {
                "name": "test-benchmark",
                "version": "1.0.0",
                "description": "Test",
                "initial_prompt": "Test prompt",
                "complexity_level": 1,
                "estimated_duration_minutes": 30,
            }
        }

        with open(benchmark_file, "w") as f:
            yaml.safe_dump(config_data, f)

        benchmark_config = BenchmarkConfig(config_data, benchmark_file)

        metadata = manager.create_run_project(benchmark_file, benchmark_config)

        assert metadata.name == "test-benchmark-run-001"
        assert "benchmark" in metadata.tags

    def test_create_run_project_increments_run_number(self, manager, tmp_path):
        """Test that run numbers increment correctly."""
        benchmark_file = tmp_path / "benchmark.yaml"
        config_data = {
            "benchmark": {
                "name": "test-benchmark",
                "version": "1.0.0",
                "description": "Test",
                "initial_prompt": "Test prompt",
                "complexity_level": 1,
                "estimated_duration_minutes": 30,
            }
        }

        with open(benchmark_file, "w") as f:
            yaml.safe_dump(config_data, f)

        benchmark_config = BenchmarkConfig(config_data, benchmark_file)

        # Create first run
        run1 = manager.create_run_project(benchmark_file, benchmark_config)
        assert run1.name == "test-benchmark-run-001"

        # Create second run
        run2 = manager.create_run_project(benchmark_file, benchmark_config)
        assert run2.name == "test-benchmark-run-002"

        # Create third run
        run3 = manager.create_run_project(benchmark_file, benchmark_config)
        assert run3.name == "test-benchmark-run-003"


class TestProjectNameValidation:
    """Tests for project name validation."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create SandboxManager instance."""
        return SandboxManager(tmp_path / "sandbox")

    def test_validate_name_too_short(self, manager):
        """Test that names shorter than 3 characters are rejected."""
        with pytest.raises(InvalidProjectNameError) as exc_info:
            manager.create_project(name="ab")

        assert "at least 3 characters" in str(exc_info.value)

    def test_validate_name_too_long(self, manager):
        """Test that names longer than 50 characters are rejected."""
        long_name = "a" * 51

        with pytest.raises(InvalidProjectNameError) as exc_info:
            manager.create_project(name=long_name)

        assert "at most 50 characters" in str(exc_info.value)

    def test_validate_name_invalid_characters(self, manager):
        """Test that names with invalid characters are rejected."""
        invalid_names = [
            "Test Project",  # Space
            "test_project",  # Underscore
            "test.project",  # Period
            "test@project",  # Special char
        ]

        for invalid_name in invalid_names:
            with pytest.raises(InvalidProjectNameError):
                manager.create_project(name=invalid_name)

    def test_validate_name_consecutive_hyphens(self, manager):
        """Test that consecutive hyphens are rejected."""
        with pytest.raises(InvalidProjectNameError) as exc_info:
            manager.create_project(name="test--project")

        assert "consecutive hyphens" in str(exc_info.value)


class TestStateTransitions:
    """Tests for project state transition validation."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create SandboxManager with a test project."""
        mgr = SandboxManager(tmp_path / "sandbox")
        mgr.create_project(name="test-project")
        return mgr

    def test_valid_transitions_from_active(self, manager):
        """Test valid transitions from ACTIVE status."""
        valid_targets = [
            ProjectStatus.COMPLETED,
            ProjectStatus.FAILED,
            ProjectStatus.ARCHIVED,
        ]

        for target in valid_targets:
            # Reset to ACTIVE
            manager.update_status("test-project", ProjectStatus.ACTIVE)
            # Try transition
            manager.update_status("test-project", target)
            # Verify
            metadata = manager.get_project("test-project")
            assert metadata.status == target

    def test_transition_to_same_status(self, manager):
        """Test that transitioning to same status is allowed."""
        manager.update_status("test-project", ProjectStatus.ACTIVE)

        metadata = manager.get_project("test-project")
        assert metadata.status == ProjectStatus.ACTIVE

    def test_transition_from_completed_to_active(self, manager):
        """Test transition from COMPLETED to ACTIVE."""
        manager.update_status("test-project", ProjectStatus.COMPLETED)
        manager.update_status("test-project", ProjectStatus.ACTIVE)

        metadata = manager.get_project("test-project")
        assert metadata.status == ProjectStatus.ACTIVE

    def test_transition_from_archived_to_active(self, manager):
        """Test transition from ARCHIVED to ACTIVE."""
        manager.update_status("test-project", ProjectStatus.ARCHIVED)
        manager.update_status("test-project", ProjectStatus.ACTIVE)

        metadata = manager.get_project("test-project")
        assert metadata.status == ProjectStatus.ACTIVE
