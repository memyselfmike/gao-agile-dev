# Story 3.1: Metrics Data Models

**Epic**: Epic 3 - Metrics Collection System
**Status**: Done
**Priority**: P0 (Critical)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27
**Completed**: 2025-10-27

---

## User Story

**As a** developer building the metrics system
**I want** strongly-typed data models for all metric categories
**So that** metrics are consistent, validated, and easy to work with

---

## Acceptance Criteria

### AC1: Performance Metrics Model
- [ ] PerformanceMetrics dataclass defined
- [ ] Fields: total_time, phase_times, token_usage, api_calls, cost
- [ ] Type hints for all fields
- [ ] Validation methods included
- [ ] JSON serialization support

### AC2: Autonomy Metrics Model
- [ ] AutonomyMetrics dataclass defined
- [ ] Fields: manual_interventions, prompts_needed, one_shot_success_rate, error_recovery_rate, agent_handoffs
- [ ] Type hints for all fields
- [ ] Validation methods included
- [ ] JSON serialization support

### AC3: Quality Metrics Model
- [ ] QualityMetrics dataclass defined
- [ ] Fields: tests_written, tests_passing, code_coverage, linting_errors, type_errors, security_vulnerabilities, functional_completeness
- [ ] Type hints for all fields
- [ ] Validation methods included
- [ ] JSON serialization support

### AC4: Workflow Metrics Model
- [ ] WorkflowMetrics dataclass defined
- [ ] Fields: stories_created, stories_completed, avg_cycle_time, phase_distribution, rework_count
- [ ] Type hints for all fields
- [ ] Validation methods included
- [ ] JSON serialization support

### AC5: Composite Metrics Model
- [ ] BenchmarkMetrics dataclass defined
- [ ] Aggregates all metric categories
- [ ] Fields: run_id, timestamp, performance, autonomy, quality, workflow
- [ ] Metadata fields (project_name, benchmark_name, version)
- [ ] JSON serialization support
- [ ] Validation for all nested models

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/metrics/models.py`

```python
"""Data models for benchmark metrics."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
import json


@dataclass
class PerformanceMetrics:
    """
    Performance metrics tracking time, tokens, and API usage.
    """
    total_time_seconds: float = 0.0
    phase_times: Dict[str, float] = field(default_factory=dict)
    token_usage_total: int = 0
    token_usage_by_agent: Dict[str, int] = field(default_factory=dict)
    api_calls_count: int = 0
    api_calls_cost: float = 0.0

    def validate(self) -> bool:
        """Validate performance metrics."""
        return (
            self.total_time_seconds >= 0 and
            self.token_usage_total >= 0 and
            self.api_calls_count >= 0 and
            self.api_calls_cost >= 0
        )


@dataclass
class AutonomyMetrics:
    """
    Autonomy metrics tracking manual intervention and success rates.
    """
    manual_interventions_count: int = 0
    manual_interventions_types: List[str] = field(default_factory=list)
    prompts_needed_initial: int = 0
    prompts_needed_followup: int = 0
    one_shot_success_rate: float = 0.0  # 0.0 - 1.0
    error_recovery_rate: float = 0.0  # 0.0 - 1.0
    agent_handoffs_successful: int = 0
    agent_handoffs_failed: int = 0

    def validate(self) -> bool:
        """Validate autonomy metrics."""
        return (
            self.manual_interventions_count >= 0 and
            0.0 <= self.one_shot_success_rate <= 1.0 and
            0.0 <= self.error_recovery_rate <= 1.0
        )


@dataclass
class QualityMetrics:
    """
    Quality metrics tracking tests, coverage, and code quality.
    """
    tests_written: int = 0
    tests_passing: int = 0
    code_coverage_percentage: float = 0.0  # 0.0 - 100.0
    linting_errors_count: int = 0
    linting_errors_by_severity: Dict[str, int] = field(default_factory=dict)
    type_errors_count: int = 0
    security_vulnerabilities_count: int = 0
    security_vulnerabilities_by_severity: Dict[str, int] = field(default_factory=dict)
    functional_completeness_percentage: float = 0.0  # 0.0 - 100.0

    def validate(self) -> bool:
        """Validate quality metrics."""
        return (
            self.tests_written >= 0 and
            self.tests_passing >= 0 and
            0.0 <= self.code_coverage_percentage <= 100.0 and
            0.0 <= self.functional_completeness_percentage <= 100.0
        )


@dataclass
class WorkflowMetrics:
    """
    Workflow metrics tracking story progress and phase distribution.
    """
    stories_created: int = 0
    stories_completed: int = 0
    avg_cycle_time_seconds: float = 0.0
    phase_distribution: Dict[str, float] = field(default_factory=dict)
    rework_count: int = 0

    def validate(self) -> bool:
        """Validate workflow metrics."""
        return (
            self.stories_created >= 0 and
            self.stories_completed >= 0 and
            self.stories_completed <= self.stories_created and
            self.avg_cycle_time_seconds >= 0 and
            self.rework_count >= 0
        )


@dataclass
class BenchmarkMetrics:
    """
    Composite benchmark metrics aggregating all metric categories.
    """
    run_id: str
    timestamp: str  # ISO format
    project_name: str
    benchmark_name: str
    version: str = "1.0.0"

    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    autonomy: AutonomyMetrics = field(default_factory=AutonomyMetrics)
    quality: QualityMetrics = field(default_factory=QualityMetrics)
    workflow: WorkflowMetrics = field(default_factory=WorkflowMetrics)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate all metrics."""
        return (
            self.run_id and
            self.timestamp and
            self.project_name and
            self.benchmark_name and
            self.performance.validate() and
            self.autonomy.validate() and
            self.quality.validate() and
            self.workflow.validate()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkMetrics":
        """Create from dictionary."""
        return cls(
            run_id=data["run_id"],
            timestamp=data["timestamp"],
            project_name=data["project_name"],
            benchmark_name=data["benchmark_name"],
            version=data.get("version", "1.0.0"),
            performance=PerformanceMetrics(**data.get("performance", {})),
            autonomy=AutonomyMetrics(**data.get("autonomy", {})),
            quality=QualityMetrics(**data.get("quality", {})),
            workflow=WorkflowMetrics(**data.get("workflow", {})),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "BenchmarkMetrics":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
```

### Dependencies

- Python dataclasses module (built-in)
- JSON module for serialization (built-in)
- Type hints from typing module

### Design Decisions

1. **Use Dataclasses**: Simpler than Pydantic, no external dependency
2. **Nested Structure**: Organize metrics by category for clarity
3. **JSON Serialization**: Support export to JSON for storage/reporting
4. **Validation Methods**: Ensure data integrity before storage
5. **Default Values**: All fields have sensible defaults

---

## Testing Requirements

### Unit Tests

**File**: `tests/sandbox/metrics/test_models.py`

```python
def test_performance_metrics_creation():
    """Test PerformanceMetrics dataclass creation."""
    pass


def test_performance_metrics_validation():
    """Test PerformanceMetrics validation."""
    pass


def test_autonomy_metrics_creation():
    """Test AutonomyMetrics dataclass creation."""
    pass


def test_autonomy_metrics_validation():
    """Test AutonomyMetrics validation."""
    pass


def test_quality_metrics_creation():
    """Test QualityMetrics dataclass creation."""
    pass


def test_quality_metrics_validation():
    """Test QualityMetrics validation."""
    pass


def test_workflow_metrics_creation():
    """Test WorkflowMetrics dataclass creation."""
    pass


def test_workflow_metrics_validation():
    """Test WorkflowMetrics validation."""
    pass


def test_benchmark_metrics_composition():
    """Test BenchmarkMetrics with all nested metrics."""
    pass


def test_benchmark_metrics_validation():
    """Test BenchmarkMetrics validation."""
    pass


def test_json_serialization():
    """Test to_json() and from_json() methods."""
    pass


def test_dict_serialization():
    """Test to_dict() and from_dict() methods."""
    pass


def test_invalid_values_rejected():
    """Test that validation catches invalid values."""
    pass
```

### Test Coverage Target
- **Target**: 100% coverage (data models should be fully tested)

---

## Definition of Done

- [X] All 5 dataclasses implemented (Performance, Autonomy, Quality, Workflow, BenchmarkMetrics)
- [X] All type hints complete
- [X] All validation methods implemented
- [X] JSON serialization/deserialization working
- [X] Unit tests passing (100% coverage - 23/23 tests passed)
- [X] No type errors (models.py has no errors)
- [X] Documentation complete
- [X] Code reviewed
- [X] Committed with proper message

---

## Dependencies

- **Requires**: None (foundational story)
- **Blocks**: Story 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9

---

## Notes

- Keep models simple and focused
- Add fields as needed in future stories
- Consider Pydantic if validation becomes complex
- JSON format enables easy export to other tools

---

*Created as part of Epic 3: Metrics Collection System*
