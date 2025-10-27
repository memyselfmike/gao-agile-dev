"""Tests for metrics data models.

Tests all dataclasses for proper validation, serialization, and deserialization.
"""

import pytest
import json
from datetime import datetime

from gao_dev.sandbox.metrics.models import (
    PerformanceMetrics,
    AutonomyMetrics,
    QualityMetrics,
    WorkflowMetrics,
    BenchmarkMetrics,
)


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test PerformanceMetrics dataclass creation with defaults."""
        metrics = PerformanceMetrics()
        assert metrics.total_time_seconds == 0.0
        assert metrics.phase_times == {}
        assert metrics.token_usage_total == 0
        assert metrics.token_usage_by_agent == {}
        assert metrics.api_calls_count == 0
        assert metrics.api_calls_cost == 0.0

    def test_performance_metrics_with_values(self):
        """Test PerformanceMetrics with custom values."""
        metrics = PerformanceMetrics(
            total_time_seconds=120.5,
            phase_times={"planning": 30.0, "implementation": 90.5},
            token_usage_total=15000,
            token_usage_by_agent={"amelia": 10000, "bob": 5000},
            api_calls_count=25,
            api_calls_cost=2.50,
        )
        assert metrics.total_time_seconds == 120.5
        assert metrics.phase_times["planning"] == 30.0
        assert metrics.token_usage_total == 15000
        assert metrics.token_usage_by_agent["amelia"] == 10000
        assert metrics.api_calls_count == 25
        assert metrics.api_calls_cost == 2.50

    def test_performance_metrics_validation_valid(self):
        """Test PerformanceMetrics validation with valid data."""
        metrics = PerformanceMetrics(
            total_time_seconds=100.0,
            token_usage_total=1000,
            api_calls_count=10,
            api_calls_cost=1.0,
        )
        assert metrics.validate() is True

    def test_performance_metrics_validation_invalid(self):
        """Test PerformanceMetrics validation with invalid data."""
        metrics = PerformanceMetrics(
            total_time_seconds=-1.0,  # Invalid: negative time
        )
        assert metrics.validate() is False

        metrics = PerformanceMetrics(
            token_usage_total=-100,  # Invalid: negative tokens
        )
        assert metrics.validate() is False


class TestAutonomyMetrics:
    """Tests for AutonomyMetrics dataclass."""

    def test_autonomy_metrics_creation(self):
        """Test AutonomyMetrics dataclass creation with defaults."""
        metrics = AutonomyMetrics()
        assert metrics.manual_interventions_count == 0
        assert metrics.manual_interventions_types == []
        assert metrics.prompts_needed_initial == 0
        assert metrics.prompts_needed_followup == 0
        assert metrics.one_shot_success_rate == 0.0
        assert metrics.error_recovery_rate == 0.0
        assert metrics.agent_handoffs_successful == 0
        assert metrics.agent_handoffs_failed == 0

    def test_autonomy_metrics_with_values(self):
        """Test AutonomyMetrics with custom values."""
        metrics = AutonomyMetrics(
            manual_interventions_count=3,
            manual_interventions_types=["clarification", "error_fix"],
            prompts_needed_initial=1,
            prompts_needed_followup=2,
            one_shot_success_rate=0.85,
            error_recovery_rate=0.90,
            agent_handoffs_successful=10,
            agent_handoffs_failed=1,
        )
        assert metrics.manual_interventions_count == 3
        assert len(metrics.manual_interventions_types) == 2
        assert metrics.one_shot_success_rate == 0.85
        assert metrics.error_recovery_rate == 0.90

    def test_autonomy_metrics_validation_valid(self):
        """Test AutonomyMetrics validation with valid data."""
        metrics = AutonomyMetrics(
            manual_interventions_count=2,
            one_shot_success_rate=0.75,
            error_recovery_rate=0.80,
        )
        assert metrics.validate() is True

    def test_autonomy_metrics_validation_invalid(self):
        """Test AutonomyMetrics validation with invalid data."""
        # Invalid: success rate > 1.0
        metrics = AutonomyMetrics(one_shot_success_rate=1.5)
        assert metrics.validate() is False

        # Invalid: negative interventions
        metrics = AutonomyMetrics(manual_interventions_count=-1)
        assert metrics.validate() is False


class TestQualityMetrics:
    """Tests for QualityMetrics dataclass."""

    def test_quality_metrics_creation(self):
        """Test QualityMetrics dataclass creation with defaults."""
        metrics = QualityMetrics()
        assert metrics.tests_written == 0
        assert metrics.tests_passing == 0
        assert metrics.code_coverage_percentage == 0.0
        assert metrics.linting_errors_count == 0
        assert metrics.type_errors_count == 0
        assert metrics.security_vulnerabilities_count == 0
        assert metrics.functional_completeness_percentage == 0.0

    def test_quality_metrics_with_values(self):
        """Test QualityMetrics with custom values."""
        metrics = QualityMetrics(
            tests_written=50,
            tests_passing=48,
            code_coverage_percentage=85.5,
            linting_errors_count=5,
            linting_errors_by_severity={"error": 2, "warning": 3},
            type_errors_count=2,
            security_vulnerabilities_count=1,
            security_vulnerabilities_by_severity={"medium": 1},
            functional_completeness_percentage=90.0,
        )
        assert metrics.tests_written == 50
        assert metrics.tests_passing == 48
        assert metrics.code_coverage_percentage == 85.5
        assert metrics.linting_errors_by_severity["error"] == 2

    def test_quality_metrics_validation_valid(self):
        """Test QualityMetrics validation with valid data."""
        metrics = QualityMetrics(
            tests_written=10,
            tests_passing=10,
            code_coverage_percentage=80.0,
            functional_completeness_percentage=100.0,
        )
        assert metrics.validate() is True

    def test_quality_metrics_validation_invalid(self):
        """Test QualityMetrics validation with invalid data."""
        # Invalid: tests_passing > tests_written
        metrics = QualityMetrics(tests_written=10, tests_passing=15)
        assert metrics.validate() is False

        # Invalid: coverage > 100%
        metrics = QualityMetrics(code_coverage_percentage=120.0)
        assert metrics.validate() is False


class TestWorkflowMetrics:
    """Tests for WorkflowMetrics dataclass."""

    def test_workflow_metrics_creation(self):
        """Test WorkflowMetrics dataclass creation with defaults."""
        metrics = WorkflowMetrics()
        assert metrics.stories_created == 0
        assert metrics.stories_completed == 0
        assert metrics.avg_cycle_time_seconds == 0.0
        assert metrics.phase_distribution == {}
        assert metrics.rework_count == 0

    def test_workflow_metrics_with_values(self):
        """Test WorkflowMetrics with custom values."""
        metrics = WorkflowMetrics(
            stories_created=9,
            stories_completed=7,
            avg_cycle_time_seconds=450.0,
            phase_distribution={"planning": 20.0, "implementation": 60.0, "testing": 20.0},
            rework_count=2,
        )
        assert metrics.stories_created == 9
        assert metrics.stories_completed == 7
        assert metrics.avg_cycle_time_seconds == 450.0
        assert metrics.phase_distribution["implementation"] == 60.0
        assert metrics.rework_count == 2

    def test_workflow_metrics_validation_valid(self):
        """Test WorkflowMetrics validation with valid data."""
        metrics = WorkflowMetrics(
            stories_created=5,
            stories_completed=5,
            avg_cycle_time_seconds=300.0,
            rework_count=1,
        )
        assert metrics.validate() is True

    def test_workflow_metrics_validation_invalid(self):
        """Test WorkflowMetrics validation with invalid data."""
        # Invalid: completed > created
        metrics = WorkflowMetrics(stories_created=5, stories_completed=10)
        assert metrics.validate() is False

        # Invalid: negative cycle time
        metrics = WorkflowMetrics(avg_cycle_time_seconds=-10.0)
        assert metrics.validate() is False


class TestBenchmarkMetrics:
    """Tests for BenchmarkMetrics composite dataclass."""

    def test_benchmark_metrics_composition(self):
        """Test BenchmarkMetrics with all nested metrics."""
        metrics = BenchmarkMetrics(
            run_id="test-run-123",
            timestamp="2025-10-27T10:00:00Z",
            project_name="test-project",
            benchmark_name="test-benchmark",
            performance=PerformanceMetrics(total_time_seconds=100.0),
            autonomy=AutonomyMetrics(manual_interventions_count=2),
            quality=QualityMetrics(tests_written=10, tests_passing=10),
            workflow=WorkflowMetrics(stories_created=5, stories_completed=5),
        )

        assert metrics.run_id == "test-run-123"
        assert metrics.project_name == "test-project"
        assert metrics.performance.total_time_seconds == 100.0
        assert metrics.autonomy.manual_interventions_count == 2
        assert metrics.quality.tests_written == 10
        assert metrics.workflow.stories_created == 5

    def test_benchmark_metrics_validation(self):
        """Test BenchmarkMetrics validation."""
        # Valid metrics
        metrics = BenchmarkMetrics(
            run_id="test-123",
            timestamp="2025-10-27T10:00:00Z",
            project_name="test",
            benchmark_name="test-bench",
        )
        assert metrics.validate() is True

        # Invalid: empty run_id
        metrics = BenchmarkMetrics(
            run_id="",
            timestamp="2025-10-27T10:00:00Z",
            project_name="test",
            benchmark_name="test-bench",
        )
        assert metrics.validate() is False

    def test_json_serialization(self):
        """Test to_json() and from_json() methods."""
        original = BenchmarkMetrics(
            run_id="test-456",
            timestamp="2025-10-27T12:00:00Z",
            project_name="json-test",
            benchmark_name="serialization-test",
            performance=PerformanceMetrics(
                total_time_seconds=200.0, token_usage_total=5000
            ),
            metadata={"test_key": "test_value"},
        )

        # Serialize to JSON
        json_str = original.to_json()
        assert isinstance(json_str, str)
        assert "test-456" in json_str
        assert "json-test" in json_str

        # Deserialize from JSON
        restored = BenchmarkMetrics.from_json(json_str)
        assert restored.run_id == original.run_id
        assert restored.project_name == original.project_name
        assert restored.performance.total_time_seconds == 200.0
        assert restored.performance.token_usage_total == 5000
        assert restored.metadata["test_key"] == "test_value"

    def test_dict_serialization(self):
        """Test to_dict() and from_dict() methods."""
        original = BenchmarkMetrics(
            run_id="test-789",
            timestamp="2025-10-27T14:00:00Z",
            project_name="dict-test",
            benchmark_name="dict-bench",
            autonomy=AutonomyMetrics(one_shot_success_rate=0.95),
        )

        # Convert to dict
        data_dict = original.to_dict()
        assert isinstance(data_dict, dict)
        assert data_dict["run_id"] == "test-789"
        assert data_dict["autonomy"]["one_shot_success_rate"] == 0.95

        # Restore from dict
        restored = BenchmarkMetrics.from_dict(data_dict)
        assert restored.run_id == original.run_id
        assert restored.autonomy.one_shot_success_rate == 0.95

    def test_invalid_values_rejected(self):
        """Test that validation catches invalid values."""
        metrics = BenchmarkMetrics(
            run_id="test-invalid",
            timestamp="2025-10-27T10:00:00Z",
            project_name="test",
            benchmark_name="test",
            performance=PerformanceMetrics(total_time_seconds=-100.0),  # Invalid
        )
        assert metrics.validate() is False

        metrics = BenchmarkMetrics(
            run_id="test-invalid-2",
            timestamp="2025-10-27T10:00:00Z",
            project_name="test",
            benchmark_name="test",
            quality=QualityMetrics(
                tests_written=5, tests_passing=10  # Invalid: passing > written
            ),
        )
        assert metrics.validate() is False

    def test_default_values(self):
        """Test that all fields have sensible defaults."""
        metrics = BenchmarkMetrics(
            run_id="default-test",
            timestamp="2025-10-27T10:00:00Z",
            project_name="test",
            benchmark_name="test",
        )

        # Check defaults for all nested metrics
        assert metrics.performance.total_time_seconds == 0.0
        assert metrics.autonomy.manual_interventions_count == 0
        assert metrics.quality.tests_written == 0
        assert metrics.workflow.stories_created == 0
        assert metrics.metadata == {}
        assert metrics.version == "1.0.0"

    def test_complex_nested_data(self):
        """Test with complex nested dictionaries and lists."""
        metrics = BenchmarkMetrics(
            run_id="complex-test",
            timestamp="2025-10-27T10:00:00Z",
            project_name="test",
            benchmark_name="test",
            performance=PerformanceMetrics(
                phase_times={"phase1": 10.0, "phase2": 20.0, "phase3": 30.0},
                token_usage_by_agent={"amelia": 5000, "bob": 3000, "john": 2000},
            ),
            autonomy=AutonomyMetrics(
                manual_interventions_types=["clarification", "error", "direction"],
            ),
            quality=QualityMetrics(
                linting_errors_by_severity={"error": 5, "warning": 10, "info": 15},
                security_vulnerabilities_by_severity={"high": 1, "medium": 2, "low": 5},
            ),
            workflow=WorkflowMetrics(
                phase_distribution={"planning": 15.0, "dev": 60.0, "testing": 25.0},
            ),
        )

        # Verify nested data
        assert len(metrics.performance.phase_times) == 3
        assert len(metrics.autonomy.manual_interventions_types) == 3
        assert metrics.quality.linting_errors_by_severity["warning"] == 10
        assert metrics.workflow.phase_distribution["dev"] == 60.0

        # Test serialization preserves nested data
        json_str = metrics.to_json()
        restored = BenchmarkMetrics.from_json(json_str)

        assert len(restored.performance.phase_times) == 3
        assert len(restored.autonomy.manual_interventions_types) == 3
        assert restored.quality.linting_errors_by_severity["warning"] == 10
