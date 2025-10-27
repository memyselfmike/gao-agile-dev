"""Tests for metrics export functionality.

This module tests the MetricsExporter class for exporting benchmark metrics
to JSON and CSV formats.
"""

import csv
import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, UTC

from gao_dev.sandbox.metrics.export import MetricsExporter
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
def temp_export_dir():
    """Create temporary directory for export files."""
    import shutil

    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup - use shutil.rmtree for better Windows compatibility
    try:
        shutil.rmtree(temp_dir)
    except (PermissionError, OSError):
        # On Windows, sometimes files are locked - best effort cleanup
        pass


@pytest.fixture
def storage(temp_db):
    """Create MetricsStorage instance with temp database."""
    return MetricsStorage(temp_db)


@pytest.fixture
def exporter(storage):
    """Create MetricsExporter instance with temp storage."""
    return MetricsExporter(storage)


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


@pytest.fixture
def sample_metrics_2():
    """Create second sample BenchmarkMetrics for testing."""
    return BenchmarkMetrics(
        run_id="test-run-002",
        timestamp=datetime.now(UTC).isoformat(),
        project_name="test-project",
        benchmark_name="basic-benchmark",
        version="1.0.0",
        performance=PerformanceMetrics(
            total_time_seconds=150.0,
            token_usage_total=6000,
            api_calls_count=12,
            api_calls_cost=0.18,
        ),
        autonomy=AutonomyMetrics(
            manual_interventions_count=3,
            prompts_needed_initial=2,
            prompts_needed_followup=1,
            one_shot_success_rate=0.75,
            error_recovery_rate=0.85,
            agent_handoffs_successful=4,
            agent_handoffs_failed=2,
        ),
        quality=QualityMetrics(
            tests_written=20,
            tests_passing=18,
            code_coverage_percentage=88.0,
            linting_errors_count=5,
            type_errors_count=1,
            security_vulnerabilities_count=0,
            functional_completeness_percentage=90.0,
        ),
        workflow=WorkflowMetrics(
            stories_created=6,
            stories_completed=5,
            avg_cycle_time_seconds=720.0,
            rework_count=2,
        ),
    )


class TestMetricsExporterInit:
    """Tests for MetricsExporter initialization."""

    def test_init_with_storage(self, storage):
        """Test initialization with provided storage."""
        exporter = MetricsExporter(storage)
        assert exporter.storage == storage

    def test_init_without_storage(self):
        """Test initialization creates default storage."""
        exporter = MetricsExporter()
        assert exporter.storage is not None
        assert isinstance(exporter.storage, MetricsStorage)


class TestExportToJSON:
    """Tests for JSON export functionality."""

    def test_export_single_run_to_json(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test exporting single run to JSON."""
        storage.save_metrics(sample_metrics)
        output_path = temp_export_dir / "metrics.json"

        exporter.export_to_json([sample_metrics.run_id], output_path)

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["run_id"] == sample_metrics.run_id

    def test_export_multiple_runs_to_json(
        self, exporter, storage, sample_metrics, sample_metrics_2, temp_export_dir
    ):
        """Test exporting multiple runs to JSON."""
        storage.save_metrics(sample_metrics)
        storage.save_metrics(sample_metrics_2)
        output_path = temp_export_dir / "metrics.json"

        exporter.export_to_json(
            [sample_metrics.run_id, sample_metrics_2.run_id], output_path
        )

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["run_id"] == sample_metrics.run_id
        assert data[1]["run_id"] == sample_metrics_2.run_id

    def test_export_json_pretty_print(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test JSON is pretty-printed by default."""
        storage.save_metrics(sample_metrics)
        output_path = temp_export_dir / "metrics.json"

        exporter.export_to_json([sample_metrics.run_id], output_path, pretty=True)

        content = output_path.read_text()
        assert "\n" in content  # Pretty-printed has newlines
        assert "  " in content  # Has indentation

    def test_export_json_compact(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test JSON can be exported compact (no pretty-print)."""
        storage.save_metrics(sample_metrics)
        output_path = temp_export_dir / "metrics.json"

        exporter.export_to_json([sample_metrics.run_id], output_path, pretty=False)

        content = output_path.read_text()
        # Compact JSON has fewer newlines and no indentation
        assert content.count("\n") < 5

    def test_export_json_all_fields_included(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test all metric fields are included in JSON export."""
        storage.save_metrics(sample_metrics)
        output_path = temp_export_dir / "metrics.json"

        exporter.export_to_json([sample_metrics.run_id], output_path)

        with open(output_path) as f:
            data = json.load(f)
        metrics = data[0]

        # Check all top-level fields
        assert "run_id" in metrics
        assert "timestamp" in metrics
        assert "project_name" in metrics
        assert "benchmark_name" in metrics
        assert "version" in metrics
        assert "performance" in metrics
        assert "autonomy" in metrics
        assert "quality" in metrics
        assert "workflow" in metrics
        assert "metadata" in metrics

        # Check nested fields
        assert "total_time_seconds" in metrics["performance"]
        assert "manual_interventions_count" in metrics["autonomy"]
        assert "tests_written" in metrics["quality"]
        assert "stories_created" in metrics["workflow"]

    def test_export_json_nonexistent_run_skipped(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test that non-existent runs are skipped in export."""
        storage.save_metrics(sample_metrics)
        output_path = temp_export_dir / "metrics.json"

        exporter.export_to_json(
            [sample_metrics.run_id, "nonexistent-run"], output_path
        )

        with open(output_path) as f:
            data = json.load(f)
        assert len(data) == 1  # Only the existing run
        assert data[0]["run_id"] == sample_metrics.run_id

    def test_export_json_creates_parent_directory(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test that parent directories are created if needed."""
        storage.save_metrics(sample_metrics)
        output_path = temp_export_dir / "subdir" / "nested" / "metrics.json"

        exporter.export_to_json([sample_metrics.run_id], output_path)

        assert output_path.exists()
        assert output_path.parent.exists()


class TestExportToCSV:
    """Tests for CSV export functionality."""

    def test_export_single_run_to_csv(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test exporting single run to CSV creates all files."""
        storage.save_metrics(sample_metrics)

        exporter.export_to_csv([sample_metrics.run_id], temp_export_dir)

        # Check all CSV files exist
        assert (temp_export_dir / "runs.csv").exists()
        assert (temp_export_dir / "performance.csv").exists()
        assert (temp_export_dir / "autonomy.csv").exists()
        assert (temp_export_dir / "quality.csv").exists()
        assert (temp_export_dir / "workflow.csv").exists()

    def test_export_multiple_runs_to_csv(
        self, exporter, storage, sample_metrics, sample_metrics_2, temp_export_dir
    ):
        """Test exporting multiple runs to CSV."""
        storage.save_metrics(sample_metrics)
        storage.save_metrics(sample_metrics_2)

        exporter.export_to_csv(
            [sample_metrics.run_id, sample_metrics_2.run_id], temp_export_dir
        )

        # Check runs.csv has both runs
        with open(temp_export_dir / "runs.csv") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 3  # Header + 2 data rows

    def test_csv_runs_structure(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test runs.csv has correct structure and data."""
        storage.save_metrics(sample_metrics)

        exporter.export_to_csv([sample_metrics.run_id], temp_export_dir)

        with open(temp_export_dir / "runs.csv") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check header
        assert rows[0] == [
            "run_id",
            "timestamp",
            "project_name",
            "benchmark_name",
            "version",
        ]

        # Check data
        assert rows[1][0] == sample_metrics.run_id
        assert rows[1][2] == sample_metrics.project_name
        assert rows[1][3] == sample_metrics.benchmark_name
        assert rows[1][4] == sample_metrics.version

    def test_csv_performance_structure(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test performance.csv has correct structure and data."""
        storage.save_metrics(sample_metrics)

        exporter.export_to_csv([sample_metrics.run_id], temp_export_dir)

        with open(temp_export_dir / "performance.csv") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check header
        assert rows[0] == [
            "run_id",
            "total_time_seconds",
            "token_usage_total",
            "api_calls_count",
            "api_calls_cost",
        ]

        # Check data
        assert rows[1][0] == sample_metrics.run_id
        assert float(rows[1][1]) == sample_metrics.performance.total_time_seconds
        assert int(rows[1][2]) == sample_metrics.performance.token_usage_total
        assert int(rows[1][3]) == sample_metrics.performance.api_calls_count
        assert float(rows[1][4]) == sample_metrics.performance.api_calls_cost

    def test_csv_autonomy_structure(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test autonomy.csv has correct structure and data."""
        storage.save_metrics(sample_metrics)

        exporter.export_to_csv([sample_metrics.run_id], temp_export_dir)

        with open(temp_export_dir / "autonomy.csv") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check header
        assert rows[0] == [
            "run_id",
            "manual_interventions_count",
            "prompts_needed_initial",
            "prompts_needed_followup",
            "one_shot_success_rate",
            "error_recovery_rate",
            "agent_handoffs_successful",
            "agent_handoffs_failed",
        ]

        # Check data
        assert rows[1][0] == sample_metrics.run_id
        assert int(rows[1][1]) == sample_metrics.autonomy.manual_interventions_count
        assert int(rows[1][2]) == sample_metrics.autonomy.prompts_needed_initial
        assert (
            float(rows[1][4]) == sample_metrics.autonomy.one_shot_success_rate
        )

    def test_csv_quality_structure(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test quality.csv has correct structure and data."""
        storage.save_metrics(sample_metrics)

        exporter.export_to_csv([sample_metrics.run_id], temp_export_dir)

        with open(temp_export_dir / "quality.csv") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check header
        assert rows[0] == [
            "run_id",
            "tests_written",
            "tests_passing",
            "code_coverage_percentage",
            "linting_errors_count",
            "type_errors_count",
            "security_vulnerabilities_count",
            "functional_completeness_percentage",
        ]

        # Check data
        assert rows[1][0] == sample_metrics.run_id
        assert int(rows[1][1]) == sample_metrics.quality.tests_written
        assert int(rows[1][2]) == sample_metrics.quality.tests_passing
        assert float(rows[1][3]) == sample_metrics.quality.code_coverage_percentage

    def test_csv_workflow_structure(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test workflow.csv has correct structure and data."""
        storage.save_metrics(sample_metrics)

        exporter.export_to_csv([sample_metrics.run_id], temp_export_dir)

        with open(temp_export_dir / "workflow.csv") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check header
        assert rows[0] == [
            "run_id",
            "stories_created",
            "stories_completed",
            "avg_cycle_time_seconds",
            "rework_count",
        ]

        # Check data
        assert rows[1][0] == sample_metrics.run_id
        assert int(rows[1][1]) == sample_metrics.workflow.stories_created
        assert int(rows[1][2]) == sample_metrics.workflow.stories_completed
        assert float(rows[1][3]) == sample_metrics.workflow.avg_cycle_time_seconds
        assert int(rows[1][4]) == sample_metrics.workflow.rework_count

    def test_export_csv_empty_run_list_does_nothing(self, exporter, temp_export_dir):
        """Test exporting empty run list doesn't create files."""
        exporter.export_to_csv([], temp_export_dir)

        # No CSV files should be created
        assert not (temp_export_dir / "runs.csv").exists()
        assert not (temp_export_dir / "performance.csv").exists()

    def test_export_csv_nonexistent_runs_skipped(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test that non-existent runs are skipped in CSV export."""
        storage.save_metrics(sample_metrics)

        exporter.export_to_csv(
            [sample_metrics.run_id, "nonexistent-run"], temp_export_dir
        )

        # Check only one row of data (plus header)
        with open(temp_export_dir / "runs.csv") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 2  # Header + 1 data row


class TestExportRun:
    """Tests for export_run convenience method."""

    def test_export_run_json(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test export_run with JSON format."""
        storage.save_metrics(sample_metrics)
        output_path = temp_export_dir / "metrics.json"

        exporter.export_run(sample_metrics.run_id, output_path, format="json")

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["run_id"] == sample_metrics.run_id

    def test_export_run_csv(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test export_run with CSV format."""
        storage.save_metrics(sample_metrics)
        output_path = temp_export_dir / "metrics.csv"

        exporter.export_run(sample_metrics.run_id, output_path, format="csv")

        # CSV creates files in parent directory
        assert (temp_export_dir / "runs.csv").exists()
        assert (temp_export_dir / "performance.csv").exists()

    def test_export_run_invalid_format_raises_error(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test export_run with invalid format raises ValueError."""
        storage.save_metrics(sample_metrics)
        output_path = temp_export_dir / "metrics.xml"

        with pytest.raises(ValueError, match="Unknown format: xml"):
            exporter.export_run(sample_metrics.run_id, output_path, format="xml")

    def test_export_run_default_format_json(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test export_run defaults to JSON format."""
        storage.save_metrics(sample_metrics)
        output_path = temp_export_dir / "metrics.json"

        exporter.export_run(sample_metrics.run_id, output_path)

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert len(data) == 1


class TestExportFiltered:
    """Tests for export_filtered method."""

    def test_export_filtered_by_project(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test exporting filtered by project name."""
        storage.save_metrics(sample_metrics)

        # Create metrics for different project
        other_metrics = BenchmarkMetrics(
            run_id="other-run-001",
            timestamp=datetime.now(UTC).isoformat(),
            project_name="other-project",
            benchmark_name="basic-benchmark",
        )
        storage.save_metrics(other_metrics)

        output_path = temp_export_dir / "metrics.json"
        count = exporter.export_filtered(
            output_path, format="json", project_name="test-project"
        )

        assert count == 1
        with open(output_path) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["project_name"] == "test-project"

    def test_export_filtered_by_benchmark(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test exporting filtered by benchmark name."""
        storage.save_metrics(sample_metrics)

        # Create metrics for different benchmark
        other_metrics = BenchmarkMetrics(
            run_id="other-run-001",
            timestamp=datetime.now(UTC).isoformat(),
            project_name="test-project",
            benchmark_name="advanced-benchmark",
        )
        storage.save_metrics(other_metrics)

        output_path = temp_export_dir / "metrics.json"
        count = exporter.export_filtered(
            output_path, format="json", benchmark_name="basic-benchmark"
        )

        assert count == 1
        with open(output_path) as f:
            data = json.load(f)
        assert data[0]["benchmark_name"] == "basic-benchmark"

    def test_export_filtered_by_date_range(
        self, exporter, storage, temp_export_dir
    ):
        """Test exporting filtered by date range."""
        # Create metrics with specific dates
        metrics1 = BenchmarkMetrics(
            run_id="run-001",
            timestamp="2025-01-15T10:00:00Z",
            project_name="test-project",
            benchmark_name="basic-benchmark",
        )
        storage.save_metrics(metrics1)

        metrics2 = BenchmarkMetrics(
            run_id="run-002",
            timestamp="2025-02-15T10:00:00Z",
            project_name="test-project",
            benchmark_name="basic-benchmark",
        )
        storage.save_metrics(metrics2)

        output_path = temp_export_dir / "metrics.json"
        count = exporter.export_filtered(
            output_path,
            format="json",
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-01-31T23:59:59Z",
        )

        assert count == 1
        with open(output_path) as f:
            data = json.load(f)
        assert data[0]["run_id"] == "run-001"

    def test_export_filtered_csv_format(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test export_filtered with CSV format."""
        storage.save_metrics(sample_metrics)

        count = exporter.export_filtered(
            temp_export_dir, format="csv", project_name="test-project"
        )

        assert count == 1
        assert (temp_export_dir / "runs.csv").exists()

    def test_export_filtered_no_matches_returns_zero(
        self, exporter, storage, temp_export_dir
    ):
        """Test export_filtered returns 0 when no matches found."""
        output_path = temp_export_dir / "metrics.json"
        count = exporter.export_filtered(
            output_path, format="json", project_name="nonexistent-project"
        )

        assert count == 0

    def test_export_filtered_respects_limit(
        self, exporter, storage, temp_export_dir
    ):
        """Test export_filtered respects limit parameter."""
        # Create 10 metrics
        for i in range(10):
            metrics = BenchmarkMetrics(
                run_id=f"run-{i:03d}",
                timestamp=datetime.now(UTC).isoformat(),
                project_name="test-project",
                benchmark_name="basic-benchmark",
            )
            storage.save_metrics(metrics)

        output_path = temp_export_dir / "metrics.json"
        count = exporter.export_filtered(
            output_path, format="json", project_name="test-project", limit=5
        )

        assert count == 5
        with open(output_path) as f:
            data = json.load(f)
        assert len(data) == 5

    def test_export_filtered_invalid_format_raises_error(
        self, exporter, storage, temp_export_dir
    ):
        """Test export_filtered with invalid format raises ValueError."""
        output_path = temp_export_dir / "metrics.xml"

        with pytest.raises(ValueError, match="Unknown format: xml"):
            exporter.export_filtered(output_path, format="xml")


class TestIntegration:
    """Integration tests for export functionality."""

    def test_json_export_can_be_reimported(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test that exported JSON can be read back and parsed."""
        storage.save_metrics(sample_metrics)
        output_path = temp_export_dir / "metrics.json"

        exporter.export_to_json([sample_metrics.run_id], output_path)

        # Read back and verify
        with open(output_path) as f:
            data = json.load(f)

        # Verify can reconstruct BenchmarkMetrics
        reconstructed = BenchmarkMetrics.from_dict(data[0])
        assert reconstructed.run_id == sample_metrics.run_id
        assert reconstructed.validate()

    def test_csv_export_readable_in_excel(
        self, exporter, storage, sample_metrics, temp_export_dir
    ):
        """Test that CSV files use standard format readable by Excel."""
        storage.save_metrics(sample_metrics)

        exporter.export_to_csv([sample_metrics.run_id], temp_export_dir)

        # Verify CSV format (should be comma-separated, no extra quoting)
        with open(temp_export_dir / "runs.csv") as f:
            content = f.read()
            assert "," in content
            # Check no unnecessary quoting
            first_line = content.split("\n")[0]
            assert first_line.startswith("run_id,")

    def test_export_all_formats_workflow(
        self, exporter, storage, sample_metrics, sample_metrics_2, temp_export_dir
    ):
        """Test complete workflow: save, export JSON, export CSV."""
        # Save metrics
        storage.save_metrics(sample_metrics)
        storage.save_metrics(sample_metrics_2)

        # Export to JSON
        json_path = temp_export_dir / "all_metrics.json"
        exporter.export_to_json(
            [sample_metrics.run_id, sample_metrics_2.run_id], json_path
        )

        # Export to CSV
        csv_dir = temp_export_dir / "csv"
        exporter.export_to_csv(
            [sample_metrics.run_id, sample_metrics_2.run_id], csv_dir
        )

        # Verify both exports succeeded
        assert json_path.exists()
        assert (csv_dir / "runs.csv").exists()

        # Verify data consistency
        with open(json_path) as f:
            json_data = json.load(f)
        with open(csv_dir / "runs.csv") as f:
            csv_reader = csv.DictReader(f)
            csv_data = list(csv_reader)

        assert len(json_data) == len(csv_data) == 2
        assert json_data[0]["run_id"] == csv_data[0]["run_id"]
