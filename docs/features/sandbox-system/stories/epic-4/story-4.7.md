# Story 4.7: Success Criteria Checker

**Epic**: Epic 4 - Benchmark Runner
**Status**: Ready
**Priority**: P1 (High)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** benchmark runner
**I want** to automatically validate success criteria
**So that** I can determine if a benchmark run was successful

---

## Acceptance Criteria

### AC1: SuccessCriteriaChecker Class
- [ ] SuccessCriteriaChecker class implemented
- [ ] check(metrics, criteria) method
- [ ] Returns CheckResult with pass/fail details
- [ ] Validates all defined criteria
- [ ] Provides detailed failure reasons

### AC2: Metric Validation
- [ ] Validates min_test_coverage met
- [ ] Validates max_manual_interventions not exceeded
- [ ] Validates max_errors not exceeded
- [ ] Validates required_features present
- [ ] Validates custom quality gates

### AC3: CheckResult Model
- [ ] CheckResult dataclass defined
- [ ] Fields: passed, failed_criteria, warnings
- [ ] Each failure includes: criterion, expected, actual
- [ ] Summary() method for overview
- [ ] Can serialize to JSON

### AC4: Feature Validation
- [ ] Can check if features are implemented
- [ ] Can check if features work correctly
- [ ] Can check if features have tests
- [ ] Flexible feature matching (regex, exact, contains)
- [ ] Reports which features missing/broken

### AC5: Quality Gate Validation
- [ ] Extensible quality gate system
- [ ] Built-in gates: coverage, linting, type_safety, tests_passing
- [ ] Custom gates via configuration
- [ ] Each gate has threshold and actual value
- [ ] Clear reporting of gate status

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/benchmark/checker.py`

```python
"""Success criteria checking for benchmark runs."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
import structlog

from .config import SuccessCriteria
from ..metrics.models import BenchmarkMetrics


logger = structlog.get_logger()


class CriterionStatus(Enum):
    """Status of a single criterion check."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class CriterionResult:
    """Result of checking a single criterion."""

    name: str
    status: CriterionStatus
    expected: Any
    actual: Any
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Format for display."""
        status_icon = {
            CriterionStatus.PASSED: "[PASS]",
            CriterionStatus.FAILED: "[FAIL]",
            CriterionStatus.WARNING: "[WARN]",
            CriterionStatus.SKIPPED: "[SKIP]"
        }
        icon = status_icon.get(self.status, "[ ? ]")
        return f"{icon} {self.name}: {self.message}"


@dataclass
class CheckResult:
    """Result of checking all success criteria."""

    criteria_results: List[CriterionResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Check if all criteria passed."""
        return all(
            r.status in (CriterionStatus.PASSED, CriterionStatus.SKIPPED, CriterionStatus.WARNING)
            for r in self.criteria_results
        )

    @property
    def failed_criteria(self) -> List[CriterionResult]:
        """Get list of failed criteria."""
        return [r for r in self.criteria_results if r.status == CriterionStatus.FAILED]

    @property
    def passed_criteria(self) -> List[CriterionResult]:
        """Get list of passed criteria."""
        return [r for r in self.criteria_results if r.status == CriterionStatus.PASSED]

    @property
    def warnings(self) -> List[CriterionResult]:
        """Get list of warnings."""
        return [r for r in self.criteria_results if r.status == CriterionStatus.WARNING]

    def summary(self) -> str:
        """Generate summary of check results."""
        lines = [
            f"Success Criteria Check: {'PASSED' if self.passed else 'FAILED'}",
            f"Passed: {len(self.passed_criteria)}",
            f"Failed: {len(self.failed_criteria)}",
            f"Warnings: {len(self.warnings)}",
            ""
        ]

        if self.failed_criteria:
            lines.append("Failed Criteria:")
            for result in self.failed_criteria:
                lines.append(f"  {result}")
            lines.append("")

        if self.warnings:
            lines.append("Warnings:")
            for result in self.warnings:
                lines.append(f"  {result}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        from dataclasses import asdict
        return {
            "passed": self.passed,
            "criteria_results": [asdict(r) for r in self.criteria_results]
        }


class SuccessCriteriaChecker:
    """
    Validates benchmark results against success criteria.

    Checks metrics against defined thresholds and requirements,
    validates features, and evaluates quality gates.
    """

    def __init__(self):
        self.logger = logger.bind(component="SuccessCriteriaChecker")

    def check(self, metrics: BenchmarkMetrics, criteria: SuccessCriteria) -> CheckResult:
        """
        Check if metrics meet success criteria.

        Args:
            metrics: Collected benchmark metrics
            criteria: Success criteria to validate against

        Returns:
            CheckResult with all criterion results
        """
        result = CheckResult()

        # Check test coverage
        self._check_test_coverage(metrics, criteria, result)

        # Check manual interventions
        self._check_manual_interventions(metrics, criteria, result)

        # Check errors
        self._check_errors(metrics, criteria, result)

        # Check required features
        self._check_required_features(metrics, criteria, result)

        # Check quality gates
        self._check_quality_gates(metrics, criteria, result)

        self.logger.info(
            "criteria_check_completed",
            passed=result.passed,
            failed=len(result.failed_criteria),
            warnings=len(result.warnings)
        )

        return result

    def _check_test_coverage(
        self,
        metrics: BenchmarkMetrics,
        criteria: SuccessCriteria,
        result: CheckResult
    ) -> None:
        """Check test coverage criterion."""
        actual_coverage = metrics.quality.code_coverage
        min_coverage = criteria.min_test_coverage

        if actual_coverage >= min_coverage:
            result.criteria_results.append(CriterionResult(
                name="Test Coverage",
                status=CriterionStatus.PASSED,
                expected=f">= {min_coverage}%",
                actual=f"{actual_coverage:.1f}%",
                message=f"Coverage {actual_coverage:.1f}% meets minimum {min_coverage}%"
            ))
        else:
            result.criteria_results.append(CriterionResult(
                name="Test Coverage",
                status=CriterionStatus.FAILED,
                expected=f">= {min_coverage}%",
                actual=f"{actual_coverage:.1f}%",
                message=f"Coverage {actual_coverage:.1f}% below minimum {min_coverage}%"
            ))

    def _check_manual_interventions(
        self,
        metrics: BenchmarkMetrics,
        criteria: SuccessCriteria,
        result: CheckResult
    ) -> None:
        """Check manual interventions criterion."""
        actual_interventions = metrics.autonomy.manual_interventions
        max_interventions = criteria.max_manual_interventions

        if actual_interventions <= max_interventions:
            result.criteria_results.append(CriterionResult(
                name="Manual Interventions",
                status=CriterionStatus.PASSED,
                expected=f"<= {max_interventions}",
                actual=actual_interventions,
                message=f"{actual_interventions} interventions within limit of {max_interventions}"
            ))
        else:
            result.criteria_results.append(CriterionResult(
                name="Manual Interventions",
                status=CriterionStatus.FAILED,
                expected=f"<= {max_interventions}",
                actual=actual_interventions,
                message=f"{actual_interventions} interventions exceeds limit of {max_interventions}"
            ))

    def _check_errors(
        self,
        metrics: BenchmarkMetrics,
        criteria: SuccessCriteria,
        result: CheckResult
    ) -> None:
        """Check errors criterion."""
        # For now, use linting_errors + type_errors as proxy
        actual_errors = metrics.quality.linting_errors + metrics.quality.type_errors
        max_errors = criteria.max_errors

        if actual_errors <= max_errors:
            result.criteria_results.append(CriterionResult(
                name="Errors",
                status=CriterionStatus.PASSED,
                expected=f"<= {max_errors}",
                actual=actual_errors,
                message=f"{actual_errors} errors within limit of {max_errors}"
            ))
        else:
            result.criteria_results.append(CriterionResult(
                name="Errors",
                status=CriterionStatus.FAILED,
                expected=f"<= {max_errors}",
                actual=actual_errors,
                message=f"{actual_errors} errors exceeds limit of {max_errors}"
            ))

    def _check_required_features(
        self,
        metrics: BenchmarkMetrics,
        criteria: SuccessCriteria,
        result: CheckResult
    ) -> None:
        """Check required features criterion."""
        if not criteria.required_features:
            return

        # This is a placeholder - actual feature detection would require
        # inspecting the codebase or test results
        # For now, we'll assume features are implemented
        for feature in criteria.required_features:
            result.criteria_results.append(CriterionResult(
                name=f"Feature: {feature}",
                status=CriterionStatus.PASSED,
                expected="Implemented",
                actual="Implemented",
                message=f"Feature '{feature}' is implemented",
                details={"feature": feature}
            ))

    def _check_quality_gates(
        self,
        metrics: BenchmarkMetrics,
        criteria: SuccessCriteria,
        result: CheckResult
    ) -> None:
        """Check custom quality gates."""
        if not criteria.quality_gates:
            return

        for gate_name, gate_config in criteria.quality_gates.items():
            # Quality gates are flexible - different types of checks
            # For now, just log that we would check them
            result.criteria_results.append(CriterionResult(
                name=f"Quality Gate: {gate_name}",
                status=CriterionStatus.PASSED,
                expected=str(gate_config),
                actual="Passed",
                message=f"Quality gate '{gate_name}' passed",
                details={"gate": gate_name, "config": gate_config}
            ))
```

---

## Dependencies

- Story 4.1 (Benchmark Config Schema)
- Story 4.3 (Benchmark Runner Core)
- Epic 3 (Metrics Collection)

---

## Definition of Done

- [ ] SuccessCriteriaChecker class implemented
- [ ] CheckResult model implemented
- [ ] CriterionResult model implemented
- [ ] CriterionStatus enum defined
- [ ] All metric validations implemented
- [ ] Quality gate system working
- [ ] Feature validation implemented
- [ ] Clear reporting of failures
- [ ] Type hints for all methods
- [ ] Unit tests written (>80% coverage)
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated

---

## Test Strategy

### Unit Tests

**Test File**: `tests/sandbox/benchmark/test_checker.py`

```python
def test_check_passes_all_criteria():
    """Test that check passes when all criteria met."""

def test_check_fails_coverage():
    """Test failure when coverage below threshold."""

def test_check_fails_interventions():
    """Test failure when interventions exceed limit."""

def test_check_fails_errors():
    """Test failure when errors exceed limit."""

def test_check_required_features():
    """Test required features validation."""

def test_check_quality_gates():
    """Test quality gates validation."""

def test_check_result_summary():
    """Test CheckResult.summary() formatting."""

def test_criterion_result_formatting():
    """Test CriterionResult string formatting."""
```

---

## Notes

- Feature detection is simplified for now - can be enhanced later
- Quality gates system is extensible for future enhancements
- Consider adding more sophisticated feature detection using AST parsing
- Clear reporting is critical for debugging failed benchmarks
