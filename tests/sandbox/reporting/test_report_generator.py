"""Tests for report generation."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from gao_dev.sandbox.reporting.report_generator import (
    ReportGenerator,
    RunNotFoundError,
    TemplateNotFoundError,
    ChangeDirection,
)
from gao_dev.sandbox.models import BenchmarkRun
from gao_dev.sandbox.metrics.models import (
    PerformanceMetrics,
    QualityMetrics,
    WorkflowMetrics,
)
from gao_dev.sandbox.metrics.storage import MetricsStorage


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary metrics database."""
    db_path = tmp_path / "test_metrics.db"
    storage = MetricsStorage(db_path)

    # Create sample run
    run = BenchmarkRun(
        run_id="test-run-001",
        benchmark_name="test-benchmark",
        project_name="test-project",
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(minutes=5),
        status="completed",
    )
    storage.save_run(run)

    # Create sample metrics
    perf = PerformanceMetrics(
        run_id="test-run-001",
        avg_response_time_ms=150.0,
        min_response_time_ms=100.0,
        max_response_time_ms=200.0,
        total_api_calls=25,
        total_tokens_used=5000,
        peak_memory_mb=256.0,
    )
    storage.save_performance_metrics(perf)

    qual = QualityMetrics(
        run_id="test-run-001",
        test_coverage_percent=85.5,
        test_count=50,
        tests_passed=48,
        tests_failed=2,
        error_count=3,
        type_check_passed=True,
    )
    storage.save_quality_metrics(qual)

    workflow = WorkflowMetrics(
        run_id="test-run-001",
        phase_durations={"init": 60.0, "planning": 120.0, "implementation": 180.0},
        agent_handoffs=5,
        manual_interventions=1,
        autonomy_score=90.0,
    )
    storage.save_workflow_metrics(workflow)

    yield db_path, storage


class TestReportGenerator:
    """Test report generation functionality."""

    def test_initialization(self, temp_db):
        """Test report generator initialization."""
        db_path, _ = temp_db
        generator = ReportGenerator(db_path)

        assert generator.storage is not None
        assert generator.env is not None

    def test_generate_run_report(self, temp_db, tmp_path):
        """Test run report generation."""
        db_path, _ = temp_db
        generator = ReportGenerator(db_path)

        output_path = tmp_path / "test_report.html"

        result = generator.generate_run_report(
            run_id="test-run-001",
            output_path=output_path,
            include_charts=False,  # Skip charts for speed
        )

        assert result == output_path
        assert output_path.exists()

        # Check HTML content
        html = output_path.read_text()
        assert "test-benchmark" in html
        assert "test-run-001" in html
        assert "completed" in html

    def test_generate_run_report_with_charts(self, temp_db, tmp_path):
        """Test run report generation with charts."""
        db_path, _ = temp_db
        generator = ReportGenerator(db_path)

        output_path = tmp_path / "test_report_charts.html"

        result = generator.generate_run_report(
            run_id="test-run-001",
            output_path=output_path,
            include_charts=True,
        )

        assert result == output_path
        assert output_path.exists()

        html = output_path.read_text()
        assert "data:image/png;base64," in html or "test-benchmark" in html

    def test_generate_run_report_run_not_found(self, temp_db, tmp_path):
        """Test run report with non-existent run."""
        db_path, _ = temp_db
        generator = ReportGenerator(db_path)

        output_path = tmp_path / "nonexistent.html"

        with pytest.raises(RunNotFoundError):
            generator.generate_run_report(
                run_id="nonexistent-run",
                output_path=output_path,
            )

    def test_generate_comparison_report(self, temp_db, tmp_path):
        """Test comparison report generation."""
        db_path, storage = temp_db

        # Create second run
        run2 = BenchmarkRun(
            run_id="test-run-002",
            benchmark_name="test-benchmark",
            project_name="test-project",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(minutes=4),
            status="completed",
        )
        storage.save_run(run2)

        perf2 = PerformanceMetrics(
            run_id="test-run-002",
            avg_response_time_ms=140.0,  # Improved
            min_response_time_ms=95.0,
            max_response_time_ms=190.0,
            total_api_calls=23,  # Improved
            total_tokens_used=4800,  # Improved
            peak_memory_mb=250.0,
        )
        storage.save_performance_metrics(perf2)

        qual2 = QualityMetrics(
            run_id="test-run-002",
            test_coverage_percent=87.0,  # Improved
            test_count=52,
            tests_passed=50,
            tests_failed=2,
            error_count=2,  # Improved
            type_check_passed=True,
        )
        storage.save_quality_metrics(qual2)

        workflow2 = WorkflowMetrics(
            run_id="test-run-002",
            phase_durations={"init": 55.0, "planning": 115.0, "implementation": 170.0},
            agent_handoffs=4,
            manual_interventions=0,
            autonomy_score=95.0,
        )
        storage.save_workflow_metrics(workflow2)

        # Generate comparison report
        generator = ReportGenerator(db_path)
        output_path = tmp_path / "comparison.html"

        result = generator.generate_comparison_report(
            run_id1="test-run-001",
            run_id2="test-run-002",
            output_path=output_path,
            include_charts=False,
        )

        assert result == output_path
        assert output_path.exists()

        html = output_path.read_text()
        assert "test-run-001" in html
        assert "test-run-002" in html
        assert "Comparison" in html

    def test_generate_trend_report(self, temp_db, tmp_path):
        """Test trend report generation."""
        db_path, storage = temp_db

        # Create multiple runs
        for i in range(2, 5):
            run = BenchmarkRun(
                run_id=f"test-run-00{i}",
                benchmark_name="test-benchmark",
                project_name="test-project",
                start_time=datetime.now() + timedelta(hours=i),
                end_time=datetime.now() + timedelta(hours=i, minutes=5),
                status="completed",
            )
            storage.save_run(run)

            perf = PerformanceMetrics(
                run_id=f"test-run-00{i}",
                avg_response_time_ms=150.0 - (i * 5),  # Improving trend
                total_api_calls=25 - i,
                total_tokens_used=5000 - (i * 100),
            )
            storage.save_performance_metrics(perf)

            qual = QualityMetrics(
                run_id=f"test-run-00{i}",
                test_coverage_percent=85.0 + i,  # Improving trend
                test_count=50,
                tests_passed=48,
                tests_failed=2,
                error_count=3,
            )
            storage.save_quality_metrics(qual)

        # Generate trend report
        generator = ReportGenerator(db_path)
        output_path = tmp_path / "trend.html"

        result = generator.generate_trend_report(
            output_path=output_path,
            include_charts=False,
        )

        assert result == output_path
        assert output_path.exists()

        html = output_path.read_text()
        assert "Trend" in html

    def test_format_duration_filter(self):
        """Test duration formatting filter."""
        assert ReportGenerator._format_duration(45.0) == "45.0s"
        assert ReportGenerator._format_duration(90.0) == "1.5m"
        assert ReportGenerator._format_duration(7200.0) == "2.0h"
        assert ReportGenerator._format_duration(None) == "N/A"

    def test_format_timestamp_filter(self):
        """Test timestamp formatting filter."""
        dt = datetime(2025, 1, 15, 14, 30, 0)
        result = ReportGenerator._format_timestamp(dt)
        assert "2025-01-15" in result
        assert "14:30:00" in result

        assert ReportGenerator._format_timestamp(None) == "N/A"

    def test_format_percent_filter(self):
        """Test percent formatting filter."""
        assert ReportGenerator._format_percent(85.5) == "85.5%"
        assert ReportGenerator._format_percent(None) == "N/A"

    def test_format_number_filter(self):
        """Test number formatting filter."""
        assert ReportGenerator._format_number(5.2) == "5.20"
        assert ReportGenerator._format_number(150.8) == "151"
        assert ReportGenerator._format_number(None) == "N/A"

    def test_status_class_filter(self):
        """Test status class filter."""
        assert ReportGenerator._status_class("completed") == "status-success"
        assert ReportGenerator._status_class("failed") == "status-error"
        assert ReportGenerator._status_class("timeout") == "status-warning"
        assert ReportGenerator._status_class("running") == "status-info"
        assert ReportGenerator._status_class("unknown") == "status-default"

    def test_metric_comparison(self):
        """Test metric comparison calculation."""
        from gao_dev.sandbox.reporting.report_generator import ReportGenerator

        # Create instance (need db_path but won't use storage for this test)
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            generator = ReportGenerator(db_path)

            comparison = generator._create_metric_comparison(
                name="Response Time",
                value1=100.0,
                value2=90.0,
                threshold=5.0,
                lower_is_better=True
            )

            assert comparison.name == "Response Time"
            assert comparison.run1_value == 100.0
            assert comparison.run2_value == 90.0
            assert comparison.absolute_delta == -10.0
            assert comparison.percent_delta == -10.0
            assert comparison.direction == ChangeDirection.IMPROVED
            assert comparison.is_significant is True

    def test_overwrite_protection(self, temp_db, tmp_path):
        """Test overwrite protection."""
        db_path, _ = temp_db
        generator = ReportGenerator(db_path)

        output_path = tmp_path / "existing.html"
        output_path.write_text("existing content")

        # Should raise error without overwrite=True
        with pytest.raises(IOError):
            generator.generate_run_report(
                run_id="test-run-001",
                output_path=output_path,
                overwrite=False,
            )

        # Should succeed with overwrite=True
        result = generator.generate_run_report(
            run_id="test-run-001",
            output_path=output_path,
            overwrite=True,
        )

        assert result == output_path
        content = output_path.read_text()
        assert content != "existing content"
