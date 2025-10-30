"""Tests for BenchmarkTrackingService."""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock

from gao_dev.sandbox.services.benchmark_tracking import BenchmarkTrackingService
from gao_dev.sandbox.models import ProjectMetadata, ProjectStatus, BenchmarkRun
from gao_dev.sandbox.exceptions import ProjectNotFoundError


@pytest.fixture
def mock_state_service():
    """Create mock ProjectStateService."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_lifecycle_service():
    """Create mock ProjectLifecycleService."""
    service = MagicMock()
    service.list_projects = MagicMock(return_value=[])
    return service


@pytest.fixture
def tracking_service(mock_state_service):
    """Create BenchmarkTrackingService instance."""
    return BenchmarkTrackingService(state_service=mock_state_service)


@pytest.fixture
def sample_project_metadata():
    """Create sample ProjectMetadata."""
    return ProjectMetadata(
        name="test-project",
        created_at=datetime.now(),
        status=ProjectStatus.ACTIVE,
        runs=[],
    )


class TestBenchmarkTrackingServiceInit:
    """Tests for BenchmarkTrackingService initialization."""

    def test_init_sets_state_service(self, mock_state_service):
        """Test that initialization sets state service."""
        service = BenchmarkTrackingService(state_service=mock_state_service)

        assert service.state_service is mock_state_service


class TestAddBenchmarkRun:
    """Tests for add_benchmark_run method."""

    def test_add_benchmark_run_success(
        self,
        tracking_service,
        mock_state_service,
        mock_lifecycle_service,
        sample_project_metadata,
    ):
        """Test adding a benchmark run."""
        mock_state_service.get_project.return_value = sample_project_metadata

        run = tracking_service.add_benchmark_run(
            project_name="test-project",
            run_id="run-001",
            config_file="/path/to/config.yaml",
            lifecycle_service=mock_lifecycle_service,
        )

        assert run.run_id == "run-001"
        assert run.config_file == "/path/to/config.yaml"
        assert isinstance(run.started_at, datetime)

    def test_add_benchmark_run_adds_to_metadata(
        self,
        tracking_service,
        mock_state_service,
        mock_lifecycle_service,
        sample_project_metadata,
    ):
        """Test that run is added to project metadata."""
        mock_state_service.get_project.return_value = sample_project_metadata

        tracking_service.add_benchmark_run(
            project_name="test-project",
            run_id="run-001",
            config_file="/path/to/config.yaml",
            lifecycle_service=mock_lifecycle_service,
        )

        # Verify update_project was called
        mock_state_service.update_project.assert_called_once()

    def test_add_benchmark_run_nonexistent_project(
        self,
        tracking_service,
        mock_state_service,
        mock_lifecycle_service,
    ):
        """Test adding run to nonexistent project raises error."""
        mock_state_service.get_project.side_effect = ProjectNotFoundError("test-project")

        with pytest.raises(ProjectNotFoundError):
            tracking_service.add_benchmark_run(
                project_name="test-project",
                run_id="run-001",
                config_file="/path/to/config.yaml",
                lifecycle_service=mock_lifecycle_service,
            )


class TestGetRunHistory:
    """Tests for get_run_history method."""

    def test_get_run_history_empty(
        self,
        tracking_service,
        mock_state_service,
        mock_lifecycle_service,
        sample_project_metadata,
    ):
        """Test getting run history for project with no runs."""
        mock_state_service.get_project.return_value = sample_project_metadata

        runs = tracking_service.get_run_history(
            project_name="test-project",
            lifecycle_service=mock_lifecycle_service,
        )

        assert len(runs) == 0

    def test_get_run_history_multiple_runs(
        self,
        tracking_service,
        mock_state_service,
        mock_lifecycle_service,
        sample_project_metadata,
    ):
        """Test getting run history with multiple runs."""
        # Create multiple runs
        run1 = BenchmarkRun(
            run_id="run-001",
            started_at=datetime(2024, 1, 1),
            config_file="config1.yaml",
        )
        run2 = BenchmarkRun(
            run_id="run-002",
            started_at=datetime(2024, 1, 2),
            config_file="config2.yaml",
        )

        sample_project_metadata.runs = [run1, run2]
        mock_state_service.get_project.return_value = sample_project_metadata

        runs = tracking_service.get_run_history(
            project_name="test-project",
            lifecycle_service=mock_lifecycle_service,
        )

        assert len(runs) == 2
        # Verify sorted by started_at descending (newest first)
        assert runs[0].run_id == "run-002"
        assert runs[1].run_id == "run-001"

    def test_get_run_history_nonexistent_project(
        self,
        tracking_service,
        mock_state_service,
        mock_lifecycle_service,
    ):
        """Test getting history for nonexistent project raises error."""
        mock_state_service.get_project.side_effect = ProjectNotFoundError("test-project")

        with pytest.raises(ProjectNotFoundError):
            tracking_service.get_run_history(
                project_name="test-project",
                lifecycle_service=mock_lifecycle_service,
            )


class TestGetLastRunNumber:
    """Tests for get_last_run_number method."""

    def test_get_last_run_number_no_runs(
        self,
        tracking_service,
        mock_lifecycle_service,
    ):
        """Test getting last run number when no runs exist."""
        mock_lifecycle_service.list_projects.return_value = []

        last_num = tracking_service.get_last_run_number(
            benchmark_name="test-benchmark",
            lifecycle_service=mock_lifecycle_service,
        )

        assert last_num == 0

    def test_get_last_run_number_single_run(
        self,
        tracking_service,
        mock_lifecycle_service,
    ):
        """Test getting last run number with one run."""
        project = ProjectMetadata(
            name="test-benchmark-run-001",
            created_at=datetime.now(),
        )
        mock_lifecycle_service.list_projects.return_value = [project]

        last_num = tracking_service.get_last_run_number(
            benchmark_name="test-benchmark",
            lifecycle_service=mock_lifecycle_service,
        )

        assert last_num == 1

    def test_get_last_run_number_multiple_runs(
        self,
        tracking_service,
        mock_lifecycle_service,
    ):
        """Test getting last run number with multiple runs."""
        projects = [
            ProjectMetadata(name="test-benchmark-run-001", created_at=datetime.now()),
            ProjectMetadata(name="test-benchmark-run-003", created_at=datetime.now()),
            ProjectMetadata(name="test-benchmark-run-002", created_at=datetime.now()),
        ]
        mock_lifecycle_service.list_projects.return_value = projects

        last_num = tracking_service.get_last_run_number(
            benchmark_name="test-benchmark",
            lifecycle_service=mock_lifecycle_service,
        )

        # Should return highest number
        assert last_num == 3

    def test_get_last_run_number_filters_by_benchmark(
        self,
        tracking_service,
        mock_lifecycle_service,
    ):
        """Test that only matching benchmark projects are considered."""
        projects = [
            ProjectMetadata(name="test-benchmark-run-001", created_at=datetime.now()),
            ProjectMetadata(name="other-benchmark-run-005", created_at=datetime.now()),
        ]
        mock_lifecycle_service.list_projects.return_value = projects

        last_num = tracking_service.get_last_run_number(
            benchmark_name="test-benchmark",
            lifecycle_service=mock_lifecycle_service,
        )

        # Should only count test-benchmark runs
        assert last_num == 1

    def test_get_last_run_number_skips_invalid_numbers(
        self,
        tracking_service,
        mock_lifecycle_service,
    ):
        """Test that runs with invalid numbers are skipped."""
        projects = [
            ProjectMetadata(name="test-benchmark-run-001", created_at=datetime.now()),
            ProjectMetadata(name="test-benchmark-run-abc", created_at=datetime.now()),
            ProjectMetadata(name="test-benchmark-run-003", created_at=datetime.now()),
        ]
        mock_lifecycle_service.list_projects.return_value = projects

        last_num = tracking_service.get_last_run_number(
            benchmark_name="test-benchmark",
            lifecycle_service=mock_lifecycle_service,
        )

        # Should skip invalid number and return 3
        assert last_num == 3


class TestCreateRunProject:
    """Tests for create_run_project method."""

    def test_create_run_project_auto_increments(
        self,
        tracking_service,
        mock_lifecycle_service,
        mock_state_service,
    ):
        """Test that run project auto-increments run number."""
        # Setup existing runs
        existing_projects = [
            ProjectMetadata(name="todo-app-run-001", created_at=datetime.now()),
        ]
        mock_lifecycle_service.list_projects.return_value = existing_projects

        # Setup create_project to return metadata
        created_metadata = ProjectMetadata(
            name="todo-app-run-002",
            created_at=datetime.now(),
        )
        mock_lifecycle_service.create_project.return_value = created_metadata

        result = tracking_service.create_run_project(
            benchmark_name="todo-app",
            benchmark_version="1.0.0",
            benchmark_file=Path("/path/to/config.yaml"),
            complexity_level=2,
            estimated_duration_minutes=30,
            prompt_hash="hash123",
            lifecycle_service=mock_lifecycle_service,
        )

        # Verify run number was incremented
        assert "run-002" in result.name

    def test_create_run_project_generates_tags(
        self,
        tracking_service,
        mock_lifecycle_service,
        mock_state_service,
    ):
        """Test that generated project has appropriate tags."""
        mock_lifecycle_service.list_projects.return_value = []

        created_metadata = ProjectMetadata(
            name="todo-app-run-001",
            created_at=datetime.now(),
            tags=["benchmark", "todo-app", "version:1.0.0"],
        )
        mock_lifecycle_service.create_project.return_value = created_metadata

        tracking_service.create_run_project(
            benchmark_name="todo-app",
            benchmark_version="1.0.0",
            benchmark_file=Path("/path/to/config.yaml"),
            complexity_level=2,
            estimated_duration_minutes=30,
            prompt_hash="hash123",
            lifecycle_service=mock_lifecycle_service,
        )

        # Verify create_project was called with correct tags
        call_kwargs = mock_lifecycle_service.create_project.call_args[1]
        assert "benchmark" in call_kwargs["tags"]
        assert "todo-app" in call_kwargs["tags"]
        assert "version:1.0.0" in call_kwargs["tags"]

    def test_create_run_project_stores_benchmark_info(
        self,
        tracking_service,
        mock_lifecycle_service,
        mock_state_service,
    ):
        """Test that benchmark info is stored in metadata."""
        mock_lifecycle_service.list_projects.return_value = []

        created_metadata = ProjectMetadata(
            name="todo-app-run-001",
            created_at=datetime.now(),
        )
        mock_lifecycle_service.create_project.return_value = created_metadata

        tracking_service.create_run_project(
            benchmark_name="todo-app",
            benchmark_version="1.0.0",
            benchmark_file=Path("/path/to/config.yaml"),
            complexity_level=2,
            estimated_duration_minutes=30,
            prompt_hash="hash123",
            lifecycle_service=mock_lifecycle_service,
        )

        # Verify update_project was called with benchmark info
        mock_state_service.update_project.assert_called_once()
        call_args = mock_state_service.update_project.call_args
        metadata = call_args[0][1]
        assert metadata.benchmark_info is not None
        assert metadata.benchmark_info["benchmark_name"] == "todo-app"
        assert metadata.benchmark_info["benchmark_version"] == "1.0.0"
        assert metadata.benchmark_info["complexity_level"] == 2
        assert metadata.benchmark_info["estimated_duration_minutes"] == 30


class TestGetProjectsForBenchmark:
    """Tests for get_projects_for_benchmark method."""

    def test_get_projects_for_benchmark_empty(
        self,
        tracking_service,
        mock_lifecycle_service,
    ):
        """Test getting projects when none exist."""
        mock_lifecycle_service.list_projects.return_value = []

        projects = tracking_service.get_projects_for_benchmark(
            benchmark_name="test-benchmark",
            lifecycle_service=mock_lifecycle_service,
        )

        assert len(projects) == 0

    def test_get_projects_for_benchmark_filters_correctly(
        self,
        tracking_service,
        mock_lifecycle_service,
    ):
        """Test that benchmark filter works correctly."""
        projects = [
            ProjectMetadata(name="test-benchmark-run-001", created_at=datetime.now()),
            ProjectMetadata(name="test-benchmark-run-002", created_at=datetime.now()),
            ProjectMetadata(name="other-benchmark-run-001", created_at=datetime.now()),
        ]
        mock_lifecycle_service.list_projects.return_value = projects

        results = tracking_service.get_projects_for_benchmark(
            benchmark_name="test-benchmark",
            lifecycle_service=mock_lifecycle_service,
        )

        # Should only return test-benchmark projects
        assert len(results) == 2
        assert all("test-benchmark-run" in p.name for p in results)
