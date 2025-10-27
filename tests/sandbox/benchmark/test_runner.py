"""Tests for benchmark runner."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from gao_dev.sandbox.benchmark.runner import (
    BenchmarkRunner,
    BenchmarkResult,
    BenchmarkStatus,
)
from gao_dev.sandbox.benchmark.config import BenchmarkConfig, SuccessCriteria
from gao_dev.sandbox.metrics.models import (
    BenchmarkMetrics,
    PerformanceMetrics,
    AutonomyMetrics,
    QualityMetrics,
    WorkflowMetrics,
)


@pytest.fixture
def valid_config():
    """Create a valid benchmark config."""
    return BenchmarkConfig(
        name="test-benchmark",
        description="Test benchmark",
        boilerplate_url="https://github.com/user/template",
        timeout_seconds=3600,
    )


@pytest.fixture
def mock_sandbox_manager():
    """Create a mock sandbox manager."""
    manager = Mock()
    project = Mock()
    project.project_path = Path("/tmp/test-project")
    project.project_name = "test-project"
    manager.init_project.return_value = project
    return manager


@pytest.fixture
def mock_metrics_collector():
    """Create a mock metrics collector."""
    collector = Mock()
    metrics = BenchmarkMetrics(
        run_id="test-run",
        project_name="test",
        benchmark_name="test",
        timestamp=datetime.now(),
        performance=PerformanceMetrics(),
        autonomy=AutonomyMetrics(),
        quality=QualityMetrics(),
        workflow=WorkflowMetrics(),
    )
    collector.stop_collection.return_value = metrics
    return collector


class TestBenchmarkStatus:
    """Tests for BenchmarkStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert BenchmarkStatus.PENDING.value == "pending"
        assert BenchmarkStatus.RUNNING.value == "running"
        assert BenchmarkStatus.COMPLETED.value == "completed"
        assert BenchmarkStatus.FAILED.value == "failed"
        assert BenchmarkStatus.TIMEOUT.value == "timeout"


class TestBenchmarkResult:
    """Tests for BenchmarkResult."""

    def test_result_creation(self, valid_config):
        """Test creating benchmark result."""
        result = BenchmarkResult(
            run_id="test-123",
            config=valid_config,
            status=BenchmarkStatus.PENDING,
            start_time=datetime.now(),
        )

        assert result.run_id == "test-123"
        assert result.config == valid_config
        assert result.status == BenchmarkStatus.PENDING
        assert result.duration_seconds == 0.0
        assert result.metrics is None
        assert result.errors == []
        assert result.warnings == []

    def test_summary_without_metrics(self, valid_config):
        """Test summary generation without metrics."""
        result = BenchmarkResult(
            run_id="test-123",
            config=valid_config,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.now(),
            duration_seconds=10.5,
        )

        summary = result.summary()
        assert "test-123" in summary
        assert "completed" in summary
        assert "10.50s" in summary

    def test_summary_with_metrics(self, valid_config):
        """Test summary generation with metrics."""
        metrics = BenchmarkMetrics(
            run_id="test-123",
            project_name="test",
            benchmark_name="test",
            timestamp=datetime.now(),
            performance=PerformanceMetrics(total_time_seconds=15.0),
            autonomy=AutonomyMetrics(manual_interventions_count=2),
            quality=QualityMetrics(code_coverage_percentage=85.5),
            workflow=WorkflowMetrics(),
        )

        result = BenchmarkResult(
            run_id="test-123",
            config=valid_config,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.now(),
            duration_seconds=15.0,
            metrics=metrics,
        )

        summary = result.summary()
        assert "15.00s" in summary
        assert "2" in summary  # interventions
        assert "85.5%" in summary  # coverage

    def test_to_dict(self, valid_config):
        """Test converting result to dictionary."""
        result = BenchmarkResult(
            run_id="test-123",
            config=valid_config,
            status=BenchmarkStatus.COMPLETED,
            start_time=datetime.now(),
        )

        data = result.to_dict()
        assert isinstance(data, dict)
        assert data["run_id"] == "test-123"
        assert data["status"] == "completed"
        assert "start_time" in data
        assert isinstance(data["config"], dict)


class TestBenchmarkRunner:
    """Tests for BenchmarkRunner."""

    def test_runner_creation(
        self, valid_config, mock_sandbox_manager, mock_metrics_collector
    ):
        """Test creating benchmark runner."""
        runner = BenchmarkRunner(
            config=valid_config,
            sandbox_manager=mock_sandbox_manager,
            metrics_collector=mock_metrics_collector,
            sandbox_root=Path("/tmp/sandbox"),
        )

        assert runner.config == valid_config
        assert runner.sandbox_manager == mock_sandbox_manager
        assert runner.metrics_collector == mock_metrics_collector
        assert runner.sandbox_root == Path("/tmp/sandbox")

    def test_generate_run_id(
        self, valid_config, mock_sandbox_manager, mock_metrics_collector
    ):
        """Test run ID generation."""
        runner = BenchmarkRunner(
            config=valid_config,
            sandbox_manager=mock_sandbox_manager,
            metrics_collector=mock_metrics_collector,
            sandbox_root=Path("/tmp/sandbox"),
        )

        run_id1 = runner._generate_run_id()
        run_id2 = runner._generate_run_id()

        assert run_id1.startswith("test-benchmark-")
        assert run_id2.startswith("test-benchmark-")
        assert run_id1 != run_id2  # Should be unique

    @patch("gao_dev.sandbox.git_cloner.GitCloner")
    def test_run_validates_config(
        self,
        mock_git_cloner_class,
        valid_config,
        mock_sandbox_manager,
        mock_metrics_collector,
    ):
        """Test that run() validates configuration first."""
        invalid_config = BenchmarkConfig(
            name="", description="", boilerplate_url="https://github.com/user/repo"
        )

        runner = BenchmarkRunner(
            config=invalid_config,
            sandbox_manager=mock_sandbox_manager,
            metrics_collector=mock_metrics_collector,
            sandbox_root=Path("/tmp/sandbox"),
        )

        result = runner.run()

        assert result.status == BenchmarkStatus.FAILED
        assert len(result.errors) > 0
        # Should contain validation errors
        assert "name" in result.errors[0].lower() or "description" in result.errors[0].lower()

    @patch("gao_dev.sandbox.git_cloner.GitCloner")
    def test_run_initializes_sandbox(
        self,
        mock_git_cloner_class,
        valid_config,
        mock_sandbox_manager,
        mock_metrics_collector,
    ):
        """Test that run() initializes sandbox project."""
        runner = BenchmarkRunner(
            config=valid_config,
            sandbox_manager=mock_sandbox_manager,
            metrics_collector=mock_metrics_collector,
            sandbox_root=Path("/tmp/sandbox"),
        )

        result = runner.run()

        mock_sandbox_manager.init_project.assert_called_once()
        call_args = mock_sandbox_manager.init_project.call_args
        assert call_args[1]["name"] == "test-benchmark"
        assert "benchmark_run_id" in call_args[1]["config"]

    @patch("gao_dev.sandbox.git_cloner.GitCloner")
    def test_run_sets_up_boilerplate_from_url(
        self,
        mock_git_cloner_class,
        valid_config,
        mock_sandbox_manager,
        mock_metrics_collector,
    ):
        """Test that run() sets up boilerplate from URL."""
        mock_cloner = Mock()
        mock_git_cloner_class.return_value = mock_cloner

        runner = BenchmarkRunner(
            config=valid_config,
            sandbox_manager=mock_sandbox_manager,
            metrics_collector=mock_metrics_collector,
            sandbox_root=Path("/tmp/sandbox"),
        )

        result = runner.run()

        mock_cloner.clone.assert_called_once()
        call_args = mock_cloner.clone.call_args
        assert call_args[1]["url"] == "https://github.com/user/template"

    @patch("shutil.copytree")
    def test_run_sets_up_boilerplate_from_path(
        self,
        mock_shutil,
        mock_sandbox_manager,
        mock_metrics_collector,
    ):
        """Test that run() sets up boilerplate from local path."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_path=Path("/local/template"),
        )

        runner = BenchmarkRunner(
            config=config,
            sandbox_manager=mock_sandbox_manager,
            metrics_collector=mock_metrics_collector,
            sandbox_root=Path("/tmp/sandbox"),
        )

        result = runner.run()

        mock_shutil.assert_called_once()

    @patch("gao_dev.sandbox.git_cloner.GitCloner")
    def test_run_collects_metrics(
        self,
        mock_git_cloner_class,
        valid_config,
        mock_sandbox_manager,
        mock_metrics_collector,
    ):
        """Test that run() collects metrics."""
        runner = BenchmarkRunner(
            config=valid_config,
            sandbox_manager=mock_sandbox_manager,
            metrics_collector=mock_metrics_collector,
            sandbox_root=Path("/tmp/sandbox"),
        )

        result = runner.run()

        mock_metrics_collector.start_collection.assert_called_once()
        mock_metrics_collector.stop_collection.assert_called_once()
        assert result.metrics is not None

    @patch("gao_dev.sandbox.git_cloner.GitCloner")
    def test_run_returns_result(
        self,
        mock_git_cloner_class,
        valid_config,
        mock_sandbox_manager,
        mock_metrics_collector,
    ):
        """Test that run() returns BenchmarkResult."""
        runner = BenchmarkRunner(
            config=valid_config,
            sandbox_manager=mock_sandbox_manager,
            metrics_collector=mock_metrics_collector,
            sandbox_root=Path("/tmp/sandbox"),
        )

        result = runner.run()

        assert isinstance(result, BenchmarkResult)
        assert result.run_id.startswith("test-benchmark-")
        assert result.config == valid_config
        assert result.status == BenchmarkStatus.COMPLETED
        assert result.duration_seconds > 0

    @patch("gao_dev.sandbox.git_cloner.GitCloner")
    def test_run_handles_sandbox_errors(
        self,
        mock_git_cloner_class,
        valid_config,
        mock_sandbox_manager,
        mock_metrics_collector,
    ):
        """Test error handling for sandbox failures."""
        mock_sandbox_manager.init_project.side_effect = Exception("Sandbox error")

        runner = BenchmarkRunner(
            config=valid_config,
            sandbox_manager=mock_sandbox_manager,
            metrics_collector=mock_metrics_collector,
            sandbox_root=Path("/tmp/sandbox"),
        )

        result = runner.run()

        assert result.status == BenchmarkStatus.FAILED
        assert len(result.errors) > 0
        assert "Sandbox error" in result.errors[0]

    @patch("gao_dev.sandbox.git_cloner.GitCloner")
    def test_cleanup_always_runs(
        self,
        mock_git_cloner_class,
        valid_config,
        mock_sandbox_manager,
        mock_metrics_collector,
    ):
        """Test that cleanup runs even on error."""
        mock_sandbox_manager.init_project.side_effect = Exception("Test error")

        runner = BenchmarkRunner(
            config=valid_config,
            sandbox_manager=mock_sandbox_manager,
            metrics_collector=mock_metrics_collector,
            sandbox_root=Path("/tmp/sandbox"),
        )

        result = runner.run()

        # Even though error occurred, result should have end_time and duration
        assert result.end_time is not None
        assert result.duration_seconds > 0

    @patch("gao_dev.sandbox.metrics.storage.MetricsStorage")
    @patch("gao_dev.sandbox.git_cloner.GitCloner")
    def test_cleanup_saves_metrics(
        self,
        mock_git_cloner_class,
        mock_storage_class,
        valid_config,
        mock_sandbox_manager,
        mock_metrics_collector,
    ):
        """Test that cleanup saves metrics to database."""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage

        runner = BenchmarkRunner(
            config=valid_config,
            sandbox_manager=mock_sandbox_manager,
            metrics_collector=mock_metrics_collector,
            sandbox_root=Path("/tmp/sandbox"),
        )

        result = runner.run()

        # Metrics should be saved
        mock_storage.save_benchmark_metrics.assert_called_once()
        call_args = mock_storage.save_benchmark_metrics.call_args
        assert call_args[0][0] == result.run_id
        assert call_args[0][1] == result.metrics
