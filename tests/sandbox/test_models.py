"""Tests for sandbox data models."""

from datetime import datetime, timedelta

import pytest

from gao_dev.sandbox.models import BenchmarkRun, ProjectMetadata, ProjectStatus


class TestProjectStatus:
    """Tests for ProjectStatus enum."""

    def test_enum_values(self):
        """Test that enum has correct values."""
        assert ProjectStatus.ACTIVE.value == "active"
        assert ProjectStatus.COMPLETED.value == "completed"
        assert ProjectStatus.FAILED.value == "failed"
        assert ProjectStatus.ARCHIVED.value == "archived"

    def test_enum_from_string(self):
        """Test creating enum from string value."""
        assert ProjectStatus("active") == ProjectStatus.ACTIVE
        assert ProjectStatus("completed") == ProjectStatus.COMPLETED
        assert ProjectStatus("failed") == ProjectStatus.FAILED
        assert ProjectStatus("archived") == ProjectStatus.ARCHIVED

    def test_enum_invalid_value(self):
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            ProjectStatus("invalid")


class TestBenchmarkRun:
    """Tests for BenchmarkRun model."""

    @pytest.fixture
    def sample_run(self):
        """Create sample benchmark run."""
        return BenchmarkRun(
            run_id="run-001",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
            config_file="benchmark.yaml",
        )

    def test_create_benchmark_run(self):
        """Test creating benchmark run with required fields."""
        run = BenchmarkRun(
            run_id="test-run",
            started_at=datetime.now(),
            config_file="test.yaml",
        )

        assert run.run_id == "test-run"
        assert run.config_file == "test.yaml"
        assert run.status == ProjectStatus.ACTIVE
        assert run.completed_at is None
        assert run.metrics == {}

    def test_create_benchmark_run_with_all_fields(self):
        """Test creating benchmark run with all fields."""
        started = datetime(2025, 1, 1, 12, 0, 0)
        completed = datetime(2025, 1, 1, 13, 0, 0)

        run = BenchmarkRun(
            run_id="test-run",
            started_at=started,
            completed_at=completed,
            status=ProjectStatus.COMPLETED,
            config_file="test.yaml",
            metrics={"duration": 3600, "lines_of_code": 1000},
        )

        assert run.run_id == "test-run"
        assert run.started_at == started
        assert run.completed_at == completed
        assert run.status == ProjectStatus.COMPLETED
        assert run.metrics == {"duration": 3600, "lines_of_code": 1000}

    def test_to_dict(self, sample_run):
        """Test serialization to dictionary."""
        data = sample_run.to_dict()

        assert data["run_id"] == "run-001"
        assert data["started_at"] == "2025-01-01T12:00:00"
        assert data["completed_at"] is None
        assert data["status"] == "active"
        assert data["config_file"] == "benchmark.yaml"
        assert data["metrics"] == {}

    def test_to_dict_with_completed(self):
        """Test serialization with completed_at set."""
        run = BenchmarkRun(
            run_id="test-run",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
            completed_at=datetime(2025, 1, 1, 13, 0, 0),
            status=ProjectStatus.COMPLETED,
            config_file="test.yaml",
        )

        data = run.to_dict()

        assert data["completed_at"] == "2025-01-01T13:00:00"
        assert data["status"] == "completed"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "run_id": "run-001",
            "started_at": "2025-01-01T12:00:00",
            "completed_at": "2025-01-01T13:00:00",
            "status": "completed",
            "config_file": "test.yaml",
            "metrics": {"duration": 3600},
        }

        run = BenchmarkRun.from_dict(data)

        assert run.run_id == "run-001"
        assert run.started_at == datetime(2025, 1, 1, 12, 0, 0)
        assert run.completed_at == datetime(2025, 1, 1, 13, 0, 0)
        assert run.status == ProjectStatus.COMPLETED
        assert run.config_file == "test.yaml"
        assert run.metrics == {"duration": 3600}

    def test_from_dict_without_completed(self):
        """Test deserialization without completed_at."""
        data = {
            "run_id": "run-001",
            "started_at": "2025-01-01T12:00:00",
            "status": "active",
            "config_file": "test.yaml",
        }

        run = BenchmarkRun.from_dict(data)

        assert run.completed_at is None
        assert run.metrics == {}

    def test_round_trip_serialization(self, sample_run):
        """Test that serialization and deserialization are reversible."""
        data = sample_run.to_dict()
        restored = BenchmarkRun.from_dict(data)

        assert restored.run_id == sample_run.run_id
        assert restored.started_at == sample_run.started_at
        assert restored.completed_at == sample_run.completed_at
        assert restored.status == sample_run.status
        assert restored.config_file == sample_run.config_file
        assert restored.metrics == sample_run.metrics


class TestProjectMetadata:
    """Tests for ProjectMetadata model."""

    @pytest.fixture
    def sample_metadata(self):
        """Create sample project metadata."""
        return ProjectMetadata(
            name="test-project",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
        )

    def test_create_project_metadata_minimal(self):
        """Test creating metadata with minimal required fields."""
        created = datetime.now()
        metadata = ProjectMetadata(
            name="test-project",
            created_at=created,
        )

        assert metadata.name == "test-project"
        assert metadata.created_at == created
        assert metadata.status == ProjectStatus.ACTIVE
        assert metadata.boilerplate_url is None
        assert metadata.runs == []
        assert metadata.tags == []
        assert metadata.description == ""
        assert metadata.benchmark_info is None
        # last_modified should be set automatically
        assert isinstance(metadata.last_modified, datetime)

    def test_create_project_metadata_with_all_fields(self):
        """Test creating metadata with all fields."""
        created = datetime(2025, 1, 1, 12, 0, 0)
        modified = datetime(2025, 1, 2, 12, 0, 0)

        metadata = ProjectMetadata(
            name="test-project",
            created_at=created,
            status=ProjectStatus.COMPLETED,
            boilerplate_url="https://github.com/test/repo.git",
            last_modified=modified,
            runs=[],
            tags=["test", "benchmark"],
            description="Test project",
            benchmark_info={"version": "1.0.0"},
        )

        assert metadata.name == "test-project"
        assert metadata.status == ProjectStatus.COMPLETED
        assert metadata.boilerplate_url == "https://github.com/test/repo.git"
        assert metadata.last_modified == modified
        assert metadata.tags == ["test", "benchmark"]
        assert metadata.description == "Test project"
        assert metadata.benchmark_info == {"version": "1.0.0"}

    def test_to_dict_minimal(self, sample_metadata):
        """Test serialization with minimal fields."""
        data = sample_metadata.to_dict()

        assert data["name"] == "test-project"
        assert data["created_at"] == "2025-01-01T12:00:00"
        assert data["status"] == "active"
        assert data["boilerplate_url"] is None
        assert isinstance(data["last_modified"], str)
        assert data["runs"] == []
        assert data["tags"] == []
        assert data["description"] == ""
        assert "benchmark_info" not in data

    def test_to_dict_with_benchmark_info(self):
        """Test serialization includes benchmark_info when present."""
        metadata = ProjectMetadata(
            name="test-project",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            benchmark_info={"version": "1.0.0", "complexity": 2},
        )

        data = metadata.to_dict()

        assert "benchmark_info" in data
        assert data["benchmark_info"] == {"version": "1.0.0", "complexity": 2}

    def test_to_dict_with_runs(self):
        """Test serialization with benchmark runs."""
        run = BenchmarkRun(
            run_id="run-001",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
            config_file="test.yaml",
        )

        metadata = ProjectMetadata(
            name="test-project",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            runs=[run],
        )

        data = metadata.to_dict()

        assert len(data["runs"]) == 1
        assert data["runs"][0]["run_id"] == "run-001"

    def test_from_dict_minimal(self):
        """Test deserialization with minimal fields."""
        data = {
            "name": "test-project",
            "created_at": "2025-01-01T12:00:00",
            "status": "active",
            "boilerplate_url": None,
            "last_modified": "2025-01-01T12:00:00",
            "runs": [],
            "tags": [],
            "description": "",
        }

        metadata = ProjectMetadata.from_dict(data)

        assert metadata.name == "test-project"
        assert metadata.created_at == datetime(2025, 1, 1, 12, 0, 0)
        assert metadata.status == ProjectStatus.ACTIVE
        assert metadata.boilerplate_url is None
        assert metadata.runs == []
        assert metadata.tags == []
        assert metadata.description == ""
        assert metadata.benchmark_info is None

    def test_from_dict_with_all_fields(self):
        """Test deserialization with all fields."""
        data = {
            "name": "test-project",
            "created_at": "2025-01-01T12:00:00",
            "status": "completed",
            "boilerplate_url": "https://github.com/test/repo.git",
            "last_modified": "2025-01-02T12:00:00",
            "runs": [
                {
                    "run_id": "run-001",
                    "started_at": "2025-01-01T12:00:00",
                    "completed_at": None,
                    "status": "active",
                    "config_file": "test.yaml",
                    "metrics": {},
                }
            ],
            "tags": ["test", "benchmark"],
            "description": "Test project",
            "benchmark_info": {"version": "1.0.0"},
        }

        metadata = ProjectMetadata.from_dict(data)

        assert metadata.name == "test-project"
        assert metadata.status == ProjectStatus.COMPLETED
        assert metadata.boilerplate_url == "https://github.com/test/repo.git"
        assert metadata.last_modified == datetime(2025, 1, 2, 12, 0, 0)
        assert len(metadata.runs) == 1
        assert metadata.runs[0].run_id == "run-001"
        assert metadata.tags == ["test", "benchmark"]
        assert metadata.description == "Test project"
        assert metadata.benchmark_info == {"version": "1.0.0"}

    def test_from_dict_without_last_modified(self):
        """Test deserialization falls back to created_at for last_modified."""
        data = {
            "name": "test-project",
            "created_at": "2025-01-01T12:00:00",
            "status": "active",
        }

        metadata = ProjectMetadata.from_dict(data)

        assert metadata.last_modified == metadata.created_at

    def test_round_trip_serialization(self, sample_metadata):
        """Test that serialization and deserialization are reversible."""
        data = sample_metadata.to_dict()
        restored = ProjectMetadata.from_dict(data)

        assert restored.name == sample_metadata.name
        assert restored.created_at == sample_metadata.created_at
        assert restored.status == sample_metadata.status
        assert restored.boilerplate_url == sample_metadata.boilerplate_url
        assert len(restored.runs) == len(sample_metadata.runs)
        assert restored.tags == sample_metadata.tags
        assert restored.description == sample_metadata.description

    def test_add_run(self, sample_metadata):
        """Test adding a benchmark run."""
        assert len(sample_metadata.runs) == 0

        run = BenchmarkRun(
            run_id="run-001",
            started_at=datetime.now(),
            config_file="test.yaml",
        )

        original_modified = sample_metadata.last_modified
        sample_metadata.add_run(run)

        assert len(sample_metadata.runs) == 1
        assert sample_metadata.runs[0] == run
        assert sample_metadata.last_modified > original_modified

    def test_get_run_count(self, sample_metadata):
        """Test getting run count."""
        assert sample_metadata.get_run_count() == 0

        sample_metadata.add_run(
            BenchmarkRun(
                run_id="run-001",
                started_at=datetime.now(),
                config_file="test.yaml",
            )
        )

        assert sample_metadata.get_run_count() == 1

        sample_metadata.add_run(
            BenchmarkRun(
                run_id="run-002",
                started_at=datetime.now(),
                config_file="test.yaml",
            )
        )

        assert sample_metadata.get_run_count() == 2

    def test_get_latest_run_with_no_runs(self, sample_metadata):
        """Test getting latest run when no runs exist."""
        assert sample_metadata.get_latest_run() is None

    def test_get_latest_run_with_one_run(self, sample_metadata):
        """Test getting latest run with one run."""
        run = BenchmarkRun(
            run_id="run-001",
            started_at=datetime.now(),
            config_file="test.yaml",
        )

        sample_metadata.add_run(run)

        latest = sample_metadata.get_latest_run()
        assert latest == run

    def test_get_latest_run_with_multiple_runs(self, sample_metadata):
        """Test getting latest run returns most recent."""
        run1 = BenchmarkRun(
            run_id="run-001",
            started_at=datetime(2025, 1, 1, 12, 0, 0),
            config_file="test.yaml",
        )

        run2 = BenchmarkRun(
            run_id="run-002",
            started_at=datetime(2025, 1, 2, 12, 0, 0),
            config_file="test.yaml",
        )

        run3 = BenchmarkRun(
            run_id="run-003",
            started_at=datetime(2025, 1, 1, 18, 0, 0),
            config_file="test.yaml",
        )

        # Add in non-chronological order
        sample_metadata.add_run(run1)
        sample_metadata.add_run(run3)
        sample_metadata.add_run(run2)

        latest = sample_metadata.get_latest_run()
        assert latest == run2  # Most recent by started_at
