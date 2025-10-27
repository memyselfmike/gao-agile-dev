"""Tests for metrics storage and retrieval.

This module tests the MetricsStorage class for saving, retrieving,
querying, and deleting benchmark metrics.
"""

import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, UTC

from gao_dev.sandbox.metrics.storage import MetricsStorage
from gao_dev.sandbox.metrics.models import (
    BenchmarkMetrics,
    PerformanceMetrics,
    AutonomyMetrics,
    QualityMetrics,
    WorkflowMetrics,
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def storage(temp_db):
    """Create MetricsStorage instance with temp database."""
    return MetricsStorage(temp_db)


@pytest.fixture
def sample_metrics():
    """Create sample BenchmarkMetrics for testing."""
    return BenchmarkMetrics(
        run_id="test-run-001",
        timestamp=datetime.now(UTC).isoformat(),
        project_name="test-project",
        benchmark_name="basic-benchmark",
        version="1.0.0",
        performance=PerformanceMetrics(
            total_time_seconds=120.5,
            phase_times={"planning": 30.0, "development": 90.5},
            token_usage_total=5000,
            token_usage_by_agent={"amelia": 3000, "bob": 2000},
            api_calls_count=10,
            api_calls_cost=0.15,
        ),
        autonomy=AutonomyMetrics(
            manual_interventions_count=2,
            manual_interventions_types=["clarification", "decision"],
            prompts_needed_initial=1,
            prompts_needed_followup=1,
            one_shot_success_rate=0.85,
            error_recovery_rate=0.9,
            agent_handoffs_successful=5,
            agent_handoffs_failed=1,
        ),
        quality=QualityMetrics(
            tests_written=15,
            tests_passing=14,
            code_coverage_percentage=92.5,
            linting_errors_count=3,
            linting_errors_by_severity={"warning": 2, "error": 1},
            type_errors_count=0,
            security_vulnerabilities_count=0,
            security_vulnerabilities_by_severity={},
            functional_completeness_percentage=95.0,
        ),
        workflow=WorkflowMetrics(
            stories_created=5,
            stories_completed=4,
            avg_cycle_time_seconds=600.0,
            phase_distribution={"planning": 0.2, "development": 0.6, "testing": 0.2},
            rework_count=1,
        ),
        metadata={"environment": "test", "agent_version": "1.0.0"},
    )


class TestMetricsStorageInit:
    """Tests for MetricsStorage initialization."""

    def test_init_with_custom_path(self, temp_db):
        """Test initialization with custom database path."""
        storage = MetricsStorage(temp_db)
        assert storage.db is not None
        assert storage.db.db_path == temp_db

    def test_init_with_default_path(self):
        """Test initialization with default database path."""
        storage = MetricsStorage()
        assert storage.db is not None
        assert storage.db.db_path == Path.home() / ".gao-dev" / "metrics.db"


class TestSaveMetrics:
    """Tests for saving metrics."""

    def test_save_valid_metrics(self, storage, sample_metrics):
        """Test saving valid metrics succeeds."""
        result = storage.save_metrics(sample_metrics)
        assert result is True

    def test_save_invalid_metrics_raises_value_error(self, storage):
        """Test saving invalid metrics raises ValueError."""
        invalid_metrics = BenchmarkMetrics(
            run_id="",  # Invalid - empty run_id
            timestamp=datetime.now(UTC).isoformat(),
            project_name="test",
            benchmark_name="test",
        )
        with pytest.raises(ValueError, match="Invalid metrics data"):
            storage.save_metrics(invalid_metrics)

    def test_save_metrics_all_categories(self, storage, sample_metrics):
        """Test that all metric categories are saved."""
        storage.save_metrics(sample_metrics)

        # Verify all tables have data
        with storage.db.connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM benchmark_runs WHERE run_id = ?",
                         (sample_metrics.run_id,))
            assert cursor.fetchone()[0] == 1

            cursor.execute("SELECT COUNT(*) FROM performance_metrics WHERE run_id = ?",
                         (sample_metrics.run_id,))
            assert cursor.fetchone()[0] == 1

            cursor.execute("SELECT COUNT(*) FROM autonomy_metrics WHERE run_id = ?",
                         (sample_metrics.run_id,))
            assert cursor.fetchone()[0] == 1

            cursor.execute("SELECT COUNT(*) FROM quality_metrics WHERE run_id = ?",
                         (sample_metrics.run_id,))
            assert cursor.fetchone()[0] == 1

            cursor.execute("SELECT COUNT(*) FROM workflow_metrics WHERE run_id = ?",
                         (sample_metrics.run_id,))
            assert cursor.fetchone()[0] == 1

    def test_save_metrics_json_serialization(self, storage, sample_metrics):
        """Test that complex fields are JSON serialized correctly."""
        storage.save_metrics(sample_metrics)

        with storage.db.connection() as conn:
            cursor = conn.cursor()

            # Check performance metrics JSON fields
            cursor.execute("SELECT phase_times, token_usage_by_agent FROM performance_metrics WHERE run_id = ?",
                         (sample_metrics.run_id,))
            row = cursor.fetchone()
            phase_times = json.loads(row[0])
            token_usage = json.loads(row[1])
            assert phase_times == sample_metrics.performance.phase_times
            assert token_usage == sample_metrics.performance.token_usage_by_agent

    def test_save_duplicate_run_id_raises_error(self, storage, sample_metrics):
        """Test that saving metrics with duplicate run_id raises error."""
        storage.save_metrics(sample_metrics)

        with pytest.raises(RuntimeError, match="Failed to save metrics"):
            storage.save_metrics(sample_metrics)

    def test_transaction_rollback_on_error(self, storage, sample_metrics, monkeypatch):
        """Test that transaction is rolled back on error."""
        # Save initial metrics
        storage.save_metrics(sample_metrics)

        # Count initial records
        with storage.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM benchmark_runs")
            initial_count = cursor.fetchone()[0]

        # Try to save metrics that will fail (duplicate run_id)
        try:
            storage.save_metrics(sample_metrics)
        except RuntimeError:
            pass

        # Verify count hasn't changed (rollback worked)
        with storage.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM benchmark_runs")
            final_count = cursor.fetchone()[0]
            assert final_count == initial_count


class TestGetMetrics:
    """Tests for retrieving metrics."""

    def test_get_existing_metrics(self, storage, sample_metrics):
        """Test retrieving existing metrics."""
        storage.save_metrics(sample_metrics)
        retrieved = storage.get_metrics(sample_metrics.run_id)

        assert retrieved is not None
        assert retrieved.run_id == sample_metrics.run_id
        assert retrieved.project_name == sample_metrics.project_name
        assert retrieved.benchmark_name == sample_metrics.benchmark_name

    def test_get_nonexistent_metrics_returns_none(self, storage):
        """Test retrieving non-existent metrics returns None."""
        result = storage.get_metrics("nonexistent-run-id")
        assert result is None

    def test_get_metrics_all_fields(self, storage, sample_metrics):
        """Test that all fields are correctly reconstructed."""
        storage.save_metrics(sample_metrics)
        retrieved = storage.get_metrics(sample_metrics.run_id)

        # Performance metrics
        assert retrieved.performance.total_time_seconds == sample_metrics.performance.total_time_seconds
        assert retrieved.performance.phase_times == sample_metrics.performance.phase_times
        assert retrieved.performance.token_usage_total == sample_metrics.performance.token_usage_total
        assert retrieved.performance.token_usage_by_agent == sample_metrics.performance.token_usage_by_agent

        # Autonomy metrics
        assert retrieved.autonomy.manual_interventions_count == sample_metrics.autonomy.manual_interventions_count
        assert retrieved.autonomy.manual_interventions_types == sample_metrics.autonomy.manual_interventions_types
        assert retrieved.autonomy.one_shot_success_rate == sample_metrics.autonomy.one_shot_success_rate

        # Quality metrics
        assert retrieved.quality.tests_written == sample_metrics.quality.tests_written
        assert retrieved.quality.tests_passing == sample_metrics.quality.tests_passing
        assert retrieved.quality.code_coverage_percentage == sample_metrics.quality.code_coverage_percentage

        # Workflow metrics
        assert retrieved.workflow.stories_created == sample_metrics.workflow.stories_created
        assert retrieved.workflow.stories_completed == sample_metrics.workflow.stories_completed
        assert retrieved.workflow.phase_distribution == sample_metrics.workflow.phase_distribution

        # Metadata
        assert retrieved.metadata == sample_metrics.metadata

    def test_get_metrics_validates(self, storage, sample_metrics):
        """Test that retrieved metrics pass validation."""
        storage.save_metrics(sample_metrics)
        retrieved = storage.get_metrics(sample_metrics.run_id)

        assert retrieved.validate() is True


class TestListRuns:
    """Tests for listing runs."""

    def test_list_all_runs(self, storage, sample_metrics):
        """Test listing all runs without filters."""
        storage.save_metrics(sample_metrics)

        # Create second metrics with different run_id
        metrics2 = BenchmarkMetrics(
            run_id="test-run-002",
            timestamp=datetime.now(UTC).isoformat(),
            project_name="test-project",
            benchmark_name="basic-benchmark",
        )
        storage.save_metrics(metrics2)

        runs = storage.list_runs()
        assert len(runs) == 2

    def test_list_runs_filtered_by_project(self, storage, sample_metrics):
        """Test filtering runs by project name."""
        storage.save_metrics(sample_metrics)

        metrics2 = BenchmarkMetrics(
            run_id="test-run-002",
            timestamp=datetime.now(UTC).isoformat(),
            project_name="other-project",
            benchmark_name="basic-benchmark",
        )
        storage.save_metrics(metrics2)

        runs = storage.list_runs(project_name="test-project")
        assert len(runs) == 1
        assert runs[0]["project_name"] == "test-project"

    def test_list_runs_filtered_by_benchmark(self, storage, sample_metrics):
        """Test filtering runs by benchmark name."""
        storage.save_metrics(sample_metrics)

        metrics2 = BenchmarkMetrics(
            run_id="test-run-002",
            timestamp=datetime.now(UTC).isoformat(),
            project_name="test-project",
            benchmark_name="advanced-benchmark",
        )
        storage.save_metrics(metrics2)

        runs = storage.list_runs(benchmark_name="basic-benchmark")
        assert len(runs) == 1
        assert runs[0]["benchmark_name"] == "basic-benchmark"

    def test_list_runs_filtered_by_date_range(self, storage):
        """Test filtering runs by date range."""
        # Create metrics with specific timestamps
        metrics1 = BenchmarkMetrics(
            run_id="test-run-001",
            timestamp="2025-01-01T10:00:00Z",
            project_name="test-project",
            benchmark_name="basic-benchmark",
        )
        storage.save_metrics(metrics1)

        metrics2 = BenchmarkMetrics(
            run_id="test-run-002",
            timestamp="2025-01-15T10:00:00Z",
            project_name="test-project",
            benchmark_name="basic-benchmark",
        )
        storage.save_metrics(metrics2)

        metrics3 = BenchmarkMetrics(
            run_id="test-run-003",
            timestamp="2025-02-01T10:00:00Z",
            project_name="test-project",
            benchmark_name="basic-benchmark",
        )
        storage.save_metrics(metrics3)

        # Filter for January only
        runs = storage.list_runs(start_date="2025-01-01T00:00:00Z", end_date="2025-01-31T23:59:59Z")
        assert len(runs) == 2

    def test_list_runs_sorted_by_timestamp_desc(self, storage):
        """Test that runs are sorted by timestamp descending."""
        metrics1 = BenchmarkMetrics(
            run_id="test-run-001",
            timestamp="2025-01-01T10:00:00Z",
            project_name="test-project",
            benchmark_name="basic-benchmark",
        )
        storage.save_metrics(metrics1)

        metrics2 = BenchmarkMetrics(
            run_id="test-run-002",
            timestamp="2025-01-15T10:00:00Z",
            project_name="test-project",
            benchmark_name="basic-benchmark",
        )
        storage.save_metrics(metrics2)

        runs = storage.list_runs()
        assert runs[0]["run_id"] == "test-run-002"  # Most recent first
        assert runs[1]["run_id"] == "test-run-001"

    def test_list_runs_respects_limit(self, storage):
        """Test that limit parameter is respected."""
        for i in range(10):
            metrics = BenchmarkMetrics(
                run_id=f"test-run-{i:03d}",
                timestamp=datetime.now(UTC).isoformat(),
                project_name="test-project",
                benchmark_name="basic-benchmark",
            )
            storage.save_metrics(metrics)

        runs = storage.list_runs(limit=5)
        assert len(runs) == 5

    def test_list_runs_empty_database(self, storage):
        """Test listing runs from empty database."""
        runs = storage.list_runs()
        assert runs == []


class TestDeleteMetrics:
    """Tests for deleting metrics."""

    def test_delete_existing_metrics(self, storage, sample_metrics):
        """Test deleting existing metrics."""
        storage.save_metrics(sample_metrics)
        result = storage.delete_metrics(sample_metrics.run_id)
        assert result is True

        # Verify it's deleted
        retrieved = storage.get_metrics(sample_metrics.run_id)
        assert retrieved is None

    def test_delete_nonexistent_metrics(self, storage):
        """Test deleting non-existent metrics returns False."""
        result = storage.delete_metrics("nonexistent-run-id")
        assert result is False

    def test_delete_cascades_to_all_tables(self, storage, sample_metrics):
        """Test that delete cascades to all related tables."""
        storage.save_metrics(sample_metrics)
        storage.delete_metrics(sample_metrics.run_id)

        # Verify all tables are empty for this run_id
        with storage.db.connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM benchmark_runs WHERE run_id = ?",
                         (sample_metrics.run_id,))
            assert cursor.fetchone()[0] == 0

            cursor.execute("SELECT COUNT(*) FROM performance_metrics WHERE run_id = ?",
                         (sample_metrics.run_id,))
            assert cursor.fetchone()[0] == 0

            cursor.execute("SELECT COUNT(*) FROM autonomy_metrics WHERE run_id = ?",
                         (sample_metrics.run_id,))
            assert cursor.fetchone()[0] == 0

            cursor.execute("SELECT COUNT(*) FROM quality_metrics WHERE run_id = ?",
                         (sample_metrics.run_id,))
            assert cursor.fetchone()[0] == 0

            cursor.execute("SELECT COUNT(*) FROM workflow_metrics WHERE run_id = ?",
                         (sample_metrics.run_id,))
            assert cursor.fetchone()[0] == 0


class TestAggregationQueries:
    """Tests for aggregation query methods."""

    def test_get_latest_runs(self, storage):
        """Test getting latest N runs."""
        for i in range(15):
            metrics = BenchmarkMetrics(
                run_id=f"test-run-{i:03d}",
                timestamp=f"2025-01-{i+1:02d}T10:00:00Z",
                project_name="test-project",
                benchmark_name="basic-benchmark",
            )
            storage.save_metrics(metrics)

        runs = storage.get_latest_runs(limit=5)
        assert len(runs) == 5
        # Should be most recent (sorted desc)
        assert runs[0]["run_id"] == "test-run-014"

    def test_get_runs_between_dates(self, storage):
        """Test getting runs between dates."""
        metrics1 = BenchmarkMetrics(
            run_id="test-run-001",
            timestamp="2025-01-01T10:00:00Z",
            project_name="test-project",
            benchmark_name="basic-benchmark",
        )
        storage.save_metrics(metrics1)

        metrics2 = BenchmarkMetrics(
            run_id="test-run-002",
            timestamp="2025-01-15T10:00:00Z",
            project_name="test-project",
            benchmark_name="basic-benchmark",
        )
        storage.save_metrics(metrics2)

        metrics3 = BenchmarkMetrics(
            run_id="test-run-003",
            timestamp="2025-02-01T10:00:00Z",
            project_name="test-project",
            benchmark_name="basic-benchmark",
        )
        storage.save_metrics(metrics3)

        runs = storage.get_runs_between_dates("2025-01-01T00:00:00Z", "2025-01-31T23:59:59Z")
        assert len(runs) == 2
        assert all("2025-01" in run["timestamp"] for run in runs)

    def test_get_average_metrics(self, storage):
        """Test calculating average metrics."""
        # Create multiple runs with known values
        for i in range(3):
            metrics = BenchmarkMetrics(
                run_id=f"test-run-{i:03d}",
                timestamp=datetime.now(UTC).isoformat(),
                project_name="test-project",
                benchmark_name="basic-benchmark",
                performance=PerformanceMetrics(
                    total_time_seconds=float(100 + i * 10),  # 100, 110, 120
                    token_usage_total=1000 + i * 100,  # 1000, 1100, 1200
                    api_calls_count=10 + i,  # 10, 11, 12
                    api_calls_cost=0.10 + i * 0.01,  # 0.10, 0.11, 0.12
                ),
            )
            storage.save_metrics(metrics)

        averages = storage.get_average_metrics(project_name="test-project")

        assert averages["total_time_seconds"] == pytest.approx(110.0, rel=0.01)
        assert averages["token_usage_total"] == pytest.approx(1100.0, rel=0.01)
        assert averages["api_calls_count"] == pytest.approx(11.0, rel=0.01)
        assert averages["api_calls_cost"] == pytest.approx(0.11, rel=0.01)

    def test_get_average_metrics_empty_returns_empty_dict(self, storage):
        """Test that get_average_metrics returns empty dict for no runs."""
        averages = storage.get_average_metrics(project_name="nonexistent")
        assert averages == {}

    def test_get_metric_trends(self, storage):
        """Test getting metric trends over time."""
        # Create runs with increasing total_time
        for i in range(5):
            metrics = BenchmarkMetrics(
                run_id=f"test-run-{i:03d}",
                timestamp=f"2025-01-{i+1:02d}T10:00:00Z",
                project_name="test-project",
                benchmark_name="basic-benchmark",
                performance=PerformanceMetrics(
                    total_time_seconds=float(100 + i * 10),  # 100, 110, 120, 130, 140
                ),
            )
            storage.save_metrics(metrics)

        trends = storage.get_metric_trends("total_time_seconds", project_name="test-project")

        assert len(trends) == 5
        # Should be sorted by timestamp ascending
        assert trends[0]["value"] == 100.0
        assert trends[4]["value"] == 140.0

        # Verify structure
        assert "timestamp" in trends[0]
        assert "run_id" in trends[0]
        assert "value" in trends[0]

    def test_get_metric_trends_multiple_categories(self, storage):
        """Test trends for metrics from different categories."""
        metrics = BenchmarkMetrics(
            run_id="test-run-001",
            timestamp=datetime.now(UTC).isoformat(),
            project_name="test-project",
            benchmark_name="basic-benchmark",
            performance=PerformanceMetrics(total_time_seconds=100.0),
            quality=QualityMetrics(code_coverage_percentage=85.0),
        )
        storage.save_metrics(metrics)

        # Test performance metric
        perf_trends = storage.get_metric_trends("total_time_seconds")
        assert len(perf_trends) == 1
        assert perf_trends[0]["value"] == 100.0

        # Test quality metric
        qual_trends = storage.get_metric_trends("code_coverage_percentage")
        assert len(qual_trends) == 1
        assert qual_trends[0]["value"] == 85.0

    def test_get_metric_trends_invalid_metric_returns_empty(self, storage, sample_metrics):
        """Test trends for invalid metric name returns empty list."""
        storage.save_metrics(sample_metrics)
        trends = storage.get_metric_trends("nonexistent_metric")
        assert trends == []


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_save_retrieve_delete_workflow(self, storage, sample_metrics):
        """Test complete workflow: save, retrieve, delete."""
        # Save
        storage.save_metrics(sample_metrics)

        # Retrieve
        retrieved = storage.get_metrics(sample_metrics.run_id)
        assert retrieved is not None
        assert retrieved.run_id == sample_metrics.run_id

        # List
        runs = storage.list_runs()
        assert len(runs) == 1

        # Delete
        result = storage.delete_metrics(sample_metrics.run_id)
        assert result is True

        # Verify deleted
        retrieved = storage.get_metrics(sample_metrics.run_id)
        assert retrieved is None

        runs = storage.list_runs()
        assert len(runs) == 0

    def test_multiple_projects_isolation(self, storage):
        """Test that projects are properly isolated."""
        metrics1 = BenchmarkMetrics(
            run_id="project-a-001",
            timestamp=datetime.now(UTC).isoformat(),
            project_name="project-a",
            benchmark_name="benchmark-1",
        )
        storage.save_metrics(metrics1)

        metrics2 = BenchmarkMetrics(
            run_id="project-b-001",
            timestamp=datetime.now(UTC).isoformat(),
            project_name="project-b",
            benchmark_name="benchmark-1",
        )
        storage.save_metrics(metrics2)

        # List project-a runs
        runs_a = storage.list_runs(project_name="project-a")
        assert len(runs_a) == 1
        assert runs_a[0]["project_name"] == "project-a"

        # List project-b runs
        runs_b = storage.list_runs(project_name="project-b")
        assert len(runs_b) == 1
        assert runs_b[0]["project_name"] == "project-b"

    def test_benchmarking_real_scenario(self, storage):
        """Test a realistic benchmarking scenario with multiple runs."""
        project_name = "todo-app"
        benchmark_name = "full-stack-benchmark"

        # Run benchmark 5 times with varying results
        for i in range(5):
            metrics = BenchmarkMetrics(
                run_id=f"run-{i:03d}",
                timestamp=f"2025-10-{i+1:02d}T10:00:00Z",
                project_name=project_name,
                benchmark_name=benchmark_name,
                performance=PerformanceMetrics(
                    total_time_seconds=float(300 - i * 10),  # Improving over time
                    token_usage_total=10000 + i * 500,
                    api_calls_count=50 + i * 5,
                    api_calls_cost=1.50 + i * 0.10,
                ),
                quality=QualityMetrics(
                    tests_written=20 + i * 2,
                    tests_passing=18 + i * 2,
                    code_coverage_percentage=80.0 + i * 2,
                ),
            )
            storage.save_metrics(metrics)

        # Get all runs
        all_runs = storage.list_runs(project_name=project_name)
        assert len(all_runs) == 5

        # Get averages
        averages = storage.get_average_metrics(project_name=project_name)
        assert "total_time_seconds" in averages
        assert averages["code_coverage_percentage"] > 80.0

        # Get trends showing improvement
        time_trends = storage.get_metric_trends("total_time_seconds", project_name=project_name)
        assert len(time_trends) == 5
        # First run should have higher time (worse) than last run
        assert time_trends[0]["value"] > time_trends[-1]["value"]

        # Coverage should improve
        coverage_trends = storage.get_metric_trends("code_coverage_percentage", project_name=project_name)
        assert coverage_trends[0]["value"] < coverage_trends[-1]["value"]
