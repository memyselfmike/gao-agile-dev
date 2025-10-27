"""Tests for success criteria checker."""

import pytest
from datetime import datetime

from gao_dev.sandbox.benchmark.checker import (
    SuccessCriteriaChecker,
    CheckResult,
    CriterionResult,
    CriterionStatus,
)
from gao_dev.sandbox.benchmark.config import SuccessCriteria
from gao_dev.sandbox.metrics.models import (
    BenchmarkMetrics,
    PerformanceMetrics,
    AutonomyMetrics,
    QualityMetrics,
    WorkflowMetrics,
)


@pytest.fixture
def sample_metrics():
    """Create sample benchmark metrics."""
    return BenchmarkMetrics(
        run_id="test-run",
        project_name="test-project",
        benchmark_name="test-benchmark",
        timestamp=datetime.now(),
        performance=PerformanceMetrics(total_time_seconds=100.0),
        autonomy=AutonomyMetrics(manual_interventions_count=2),
        quality=QualityMetrics(
            code_coverage_percentage=85.0,
            linting_errors_count=1,
            type_errors_count=2,
        ),
        workflow=WorkflowMetrics(),
    )


@pytest.fixture
def default_criteria():
    """Create default success criteria."""
    return SuccessCriteria()


class TestCriterionStatus:
    """Tests for CriterionStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert CriterionStatus.PASSED.value == "passed"
        assert CriterionStatus.FAILED.value == "failed"
        assert CriterionStatus.WARNING.value == "warning"
        assert CriterionStatus.SKIPPED.value == "skipped"


class TestCriterionResult:
    """Tests for CriterionResult."""

    def test_creation(self):
        """Test creating criterion result."""
        result = CriterionResult(
            name="Test Criterion",
            status=CriterionStatus.PASSED,
            expected=">= 80%",
            actual="85%",
            message="Coverage meets minimum",
        )
        assert result.name == "Test Criterion"
        assert result.status == CriterionStatus.PASSED
        assert result.expected == ">= 80%"
        assert result.actual == "85%"
        assert result.message == "Coverage meets minimum"

    def test_string_format_passed(self):
        """Test string format for passed criterion."""
        result = CriterionResult(
            name="Coverage",
            status=CriterionStatus.PASSED,
            expected=">= 80%",
            actual="85%",
            message="Meets minimum",
        )
        str_result = str(result)
        assert "[PASS]" in str_result
        assert "Coverage" in str_result

    def test_string_format_failed(self):
        """Test string format for failed criterion."""
        result = CriterionResult(
            name="Coverage",
            status=CriterionStatus.FAILED,
            expected=">= 80%",
            actual="70%",
            message="Below minimum",
        )
        str_result = str(result)
        assert "[FAIL]" in str_result
        assert "Coverage" in str_result

    def test_string_format_warning(self):
        """Test string format for warning criterion."""
        result = CriterionResult(
            name="Coverage",
            status=CriterionStatus.WARNING,
            expected=">= 80%",
            actual="81%",
            message="Just above minimum",
        )
        str_result = str(result)
        assert "[WARN]" in str_result
        assert "Coverage" in str_result

    def test_string_format_skipped(self):
        """Test string format for skipped criterion."""
        result = CriterionResult(
            name="Coverage",
            status=CriterionStatus.SKIPPED,
            expected=">= 80%",
            actual="N/A",
            message="Not applicable",
        )
        str_result = str(result)
        assert "[SKIP]" in str_result
        assert "Coverage" in str_result


class TestCheckResult:
    """Tests for CheckResult."""

    def test_empty_result(self):
        """Test empty check result."""
        result = CheckResult()
        assert result.passed is True  # Empty is considered passed
        assert len(result.failed_criteria) == 0
        assert len(result.passed_criteria) == 0
        assert len(result.warnings) == 0

    def test_all_passed(self):
        """Test result with all criteria passed."""
        result = CheckResult(
            criteria_results=[
                CriterionResult("C1", CriterionStatus.PASSED, "x", "y", "msg"),
                CriterionResult("C2", CriterionStatus.PASSED, "x", "y", "msg"),
            ]
        )
        assert result.passed is True
        assert len(result.passed_criteria) == 2
        assert len(result.failed_criteria) == 0

    def test_with_failures(self):
        """Test result with failed criteria."""
        result = CheckResult(
            criteria_results=[
                CriterionResult("C1", CriterionStatus.PASSED, "x", "y", "msg"),
                CriterionResult("C2", CriterionStatus.FAILED, "x", "y", "msg"),
            ]
        )
        assert result.passed is False
        assert len(result.passed_criteria) == 1
        assert len(result.failed_criteria) == 1

    def test_with_warnings(self):
        """Test result with warnings."""
        result = CheckResult(
            criteria_results=[
                CriterionResult("C1", CriterionStatus.PASSED, "x", "y", "msg"),
                CriterionResult("C2", CriterionStatus.WARNING, "x", "y", "msg"),
            ]
        )
        assert result.passed is True  # Warnings don't fail
        assert len(result.warnings) == 1

    def test_with_skipped(self):
        """Test result with skipped criteria."""
        result = CheckResult(
            criteria_results=[
                CriterionResult("C1", CriterionStatus.PASSED, "x", "y", "msg"),
                CriterionResult("C2", CriterionStatus.SKIPPED, "x", "y", "msg"),
            ]
        )
        assert result.passed is True  # Skipped don't fail

    def test_summary_all_passed(self):
        """Test summary with all passed."""
        result = CheckResult(
            criteria_results=[
                CriterionResult("C1", CriterionStatus.PASSED, "x", "y", "msg"),
                CriterionResult("C2", CriterionStatus.PASSED, "x", "y", "msg"),
            ]
        )
        summary = result.summary()
        assert "PASSED" in summary
        assert "Passed: 2" in summary
        assert "Failed: 0" in summary

    def test_summary_with_failures(self):
        """Test summary with failures."""
        result = CheckResult(
            criteria_results=[
                CriterionResult("C1", CriterionStatus.PASSED, "x", "y", "msg"),
                CriterionResult("C2", CriterionStatus.FAILED, "x", "y", "Failed msg"),
            ]
        )
        summary = result.summary()
        assert "FAILED" in summary
        assert "Passed: 1" in summary
        assert "Failed: 1" in summary
        assert "Failed Criteria:" in summary
        assert "[FAIL]" in summary

    def test_summary_with_warnings(self):
        """Test summary with warnings."""
        result = CheckResult(
            criteria_results=[
                CriterionResult("C1", CriterionStatus.PASSED, "x", "y", "msg"),
                CriterionResult("C2", CriterionStatus.WARNING, "x", "y", "Warning msg"),
            ]
        )
        summary = result.summary()
        assert "PASSED" in summary
        assert "Warnings: 1" in summary
        assert "Warnings:" in summary
        assert "[WARN]" in summary

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = CheckResult(
            criteria_results=[
                CriterionResult("C1", CriterionStatus.PASSED, "x", "y", "msg"),
            ]
        )
        data = result.to_dict()
        assert isinstance(data, dict)
        assert "passed" in data
        assert "criteria_results" in data
        assert data["passed"] is True


class TestSuccessCriteriaChecker:
    """Tests for SuccessCriteriaChecker."""

    def test_checker_creation(self):
        """Test creating checker."""
        checker = SuccessCriteriaChecker()
        assert checker is not None

    def test_check_test_coverage_passes(self, sample_metrics):
        """Test coverage check passes when above minimum."""
        criteria = SuccessCriteria(
            min_test_coverage=80.0,
            max_manual_interventions=10,  # Set high to pass
            max_errors=10,  # Set high to pass
        )
        checker = SuccessCriteriaChecker()

        result = checker.check(sample_metrics, criteria)

        assert result.passed is True
        coverage_results = [r for r in result.criteria_results if "Coverage" in r.name]
        assert len(coverage_results) == 1
        assert coverage_results[0].status == CriterionStatus.PASSED

    def test_check_test_coverage_fails(self, sample_metrics):
        """Test coverage check fails when below minimum."""
        criteria = SuccessCriteria(min_test_coverage=90.0)
        checker = SuccessCriteriaChecker()

        result = checker.check(sample_metrics, criteria)

        assert result.passed is False
        coverage_results = [r for r in result.criteria_results if "Coverage" in r.name]
        assert len(coverage_results) == 1
        assert coverage_results[0].status == CriterionStatus.FAILED

    def test_check_manual_interventions_passes(self, sample_metrics):
        """Test interventions check passes when within limit."""
        criteria = SuccessCriteria(
            min_test_coverage=80.0,  # Set to pass
            max_manual_interventions=5,
            max_errors=10,  # Set high to pass
        )
        checker = SuccessCriteriaChecker()

        result = checker.check(sample_metrics, criteria)

        assert result.passed is True
        intervention_results = [
            r for r in result.criteria_results if "Interventions" in r.name
        ]
        assert len(intervention_results) == 1
        assert intervention_results[0].status == CriterionStatus.PASSED

    def test_check_manual_interventions_fails(self, sample_metrics):
        """Test interventions check fails when exceeds limit."""
        criteria = SuccessCriteria(max_manual_interventions=1)
        checker = SuccessCriteriaChecker()

        result = checker.check(sample_metrics, criteria)

        assert result.passed is False
        intervention_results = [
            r for r in result.criteria_results if "Interventions" in r.name
        ]
        assert len(intervention_results) == 1
        assert intervention_results[0].status == CriterionStatus.FAILED

    def test_check_errors_passes(self, sample_metrics):
        """Test errors check passes when within limit."""
        # Sample has 3 total errors (1 linting + 2 type)
        criteria = SuccessCriteria(
            min_test_coverage=80.0,  # Set to pass
            max_manual_interventions=10,  # Set high to pass
            max_errors=5,
        )
        checker = SuccessCriteriaChecker()

        result = checker.check(sample_metrics, criteria)

        assert result.passed is True
        error_results = [r for r in result.criteria_results if r.name == "Errors"]
        assert len(error_results) == 1
        assert error_results[0].status == CriterionStatus.PASSED

    def test_check_errors_fails(self, sample_metrics):
        """Test errors check fails when exceeds limit."""
        # Sample has 3 total errors (1 linting + 2 type)
        criteria = SuccessCriteria(max_errors=2)
        checker = SuccessCriteriaChecker()

        result = checker.check(sample_metrics, criteria)

        assert result.passed is False
        error_results = [r for r in result.criteria_results if r.name == "Errors"]
        assert len(error_results) == 1
        assert error_results[0].status == CriterionStatus.FAILED

    def test_check_required_features(self, sample_metrics):
        """Test required features check."""
        criteria = SuccessCriteria(
            required_features=["authentication", "data-persistence"]
        )
        checker = SuccessCriteriaChecker()

        result = checker.check(sample_metrics, criteria)

        feature_results = [r for r in result.criteria_results if "Feature:" in r.name]
        assert len(feature_results) == 2
        assert all(r.status == CriterionStatus.PASSED for r in feature_results)

    def test_check_no_required_features(self, sample_metrics):
        """Test with no required features."""
        criteria = SuccessCriteria(required_features=[])
        checker = SuccessCriteriaChecker()

        result = checker.check(sample_metrics, criteria)

        feature_results = [r for r in result.criteria_results if "Feature:" in r.name]
        assert len(feature_results) == 0

    def test_check_quality_gates(self, sample_metrics):
        """Test quality gates check."""
        criteria = SuccessCriteria(
            quality_gates={"performance": {"max_time": 120}, "security": {"scan": True}}
        )
        checker = SuccessCriteriaChecker()

        result = checker.check(sample_metrics, criteria)

        gate_results = [r for r in result.criteria_results if "Quality Gate:" in r.name]
        assert len(gate_results) == 2
        assert all(r.status == CriterionStatus.PASSED for r in gate_results)

    def test_check_no_quality_gates(self, sample_metrics):
        """Test with no quality gates."""
        criteria = SuccessCriteria(quality_gates={})
        checker = SuccessCriteriaChecker()

        result = checker.check(sample_metrics, criteria)

        gate_results = [r for r in result.criteria_results if "Quality Gate:" in r.name]
        assert len(gate_results) == 0

    def test_check_all_criteria(self, sample_metrics):
        """Test checking all criteria together."""
        criteria = SuccessCriteria(
            min_test_coverage=80.0,
            max_manual_interventions=5,
            max_errors=5,
            required_features=["auth"],
            quality_gates={"perf": {"max": 100}},
        )
        checker = SuccessCriteriaChecker()

        result = checker.check(sample_metrics, criteria)

        assert result.passed is True
        # Should have 5 criteria checked (coverage, interventions, errors, 1 feature, 1 gate)
        assert len(result.criteria_results) == 5

    def test_check_mixed_pass_fail(self, sample_metrics):
        """Test with mixed passing and failing criteria."""
        criteria = SuccessCriteria(
            min_test_coverage=90.0,  # Will fail (actual 85%)
            max_manual_interventions=5,  # Will pass (actual 2)
            max_errors=2,  # Will fail (actual 3)
        )
        checker = SuccessCriteriaChecker()

        result = checker.check(sample_metrics, criteria)

        assert result.passed is False
        assert len(result.passed_criteria) == 1
        assert len(result.failed_criteria) == 2
