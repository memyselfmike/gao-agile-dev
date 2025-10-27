# Story 4.1: Benchmark Config Schema

**Epic**: Epic 4 - Benchmark Runner
**Status**: Ready
**Priority**: P0 (Critical)
**Estimated Effort**: 2 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer running benchmarks
**I want** a well-defined configuration schema for benchmark runs
**So that** I can specify what to test, how to test it, and what success looks like

---

## Acceptance Criteria

### AC1: Benchmark Config Data Model
- [ ] BenchmarkConfig dataclass defined
- [ ] Fields: name, description, version, project_name, boilerplate_url
- [ ] Fields: timeout_seconds, success_criteria, workflow_phases
- [ ] Type hints for all fields
- [ ] JSON/YAML serialization support
- [ ] Validation methods included

### AC2: Success Criteria Model
- [ ] SuccessCriteria dataclass defined
- [ ] Fields: min_test_coverage, max_manual_interventions, max_errors
- [ ] Fields: required_features, quality_gates
- [ ] Type hints for all fields
- [ ] Validation logic

### AC3: Workflow Phase Config
- [ ] WorkflowPhaseConfig dataclass defined
- [ ] Fields: phase_name, timeout_seconds, expected_artifacts
- [ ] Fields: quality_gates, skip_if_failed
- [ ] Type hints for all fields

### AC4: YAML Schema Definition
- [ ] Schema file created: `schemas/benchmark-config.schema.yaml`
- [ ] Defines all required and optional fields
- [ ] Includes field descriptions and examples
- [ ] Validation rules documented

### AC5: Example Configurations
- [ ] Example config for todo-app benchmark created
- [ ] Example config for minimal benchmark created
- [ ] Example config for full-featured benchmark created
- [ ] All examples validate against schema

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/benchmark/config.py`

```python
"""Benchmark configuration data models."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import json


@dataclass
class SuccessCriteria:
    """Success criteria for benchmark run."""

    min_test_coverage: float = 80.0
    max_manual_interventions: int = 0
    max_errors: int = 0
    required_features: List[str] = field(default_factory=list)
    quality_gates: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate success criteria."""
        return (
            0 <= self.min_test_coverage <= 100 and
            self.max_manual_interventions >= 0 and
            self.max_errors >= 0
        )


@dataclass
class WorkflowPhaseConfig:
    """Configuration for a workflow phase."""

    phase_name: str
    timeout_seconds: int = 3600
    expected_artifacts: List[str] = field(default_factory=list)
    quality_gates: Dict[str, Any] = field(default_factory=dict)
    skip_if_failed: bool = False

    def validate(self) -> bool:
        """Validate phase config."""
        return (
            bool(self.phase_name) and
            self.timeout_seconds > 0
        )


@dataclass
class BenchmarkConfig:
    """Complete benchmark configuration."""

    name: str
    description: str
    version: str = "1.0.0"
    project_name: str = ""
    boilerplate_url: Optional[str] = None
    boilerplate_path: Optional[Path] = None
    timeout_seconds: int = 7200  # 2 hours default
    success_criteria: SuccessCriteria = field(default_factory=SuccessCriteria)
    workflow_phases: List[WorkflowPhaseConfig] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate entire configuration."""
        return (
            bool(self.name) and
            bool(self.description) and
            self.timeout_seconds > 0 and
            self.success_criteria.validate() and
            all(phase.validate() for phase in self.workflow_phases)
        )

    @classmethod
    def from_yaml(cls, path: Path) -> "BenchmarkConfig":
        """Load config from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def from_json(cls, path: Path) -> "BenchmarkConfig":
        """Load config from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        from dataclasses import asdict
        return asdict(self)
```

**Schema File**: `gao_dev/sandbox/benchmark/schemas/benchmark-config.schema.yaml`

**Example Configs**:
- `sandbox/benchmarks/todo-app.yaml`
- `sandbox/benchmarks/minimal.yaml`
- `sandbox/benchmarks/full-featured.yaml`

---

## Dependencies

- None (foundational story for Epic 4)

---

## Definition of Done

- [ ] BenchmarkConfig dataclass implemented
- [ ] SuccessCriteria dataclass implemented
- [ ] WorkflowPhaseConfig dataclass implemented
- [ ] YAML/JSON loading methods implemented
- [ ] Schema file created and documented
- [ ] 3 example configurations created
- [ ] All models have type hints
- [ ] All models have validation methods
- [ ] Unit tests written (>80% coverage)
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated

---

## Test Strategy

### Unit Tests

**Test File**: `tests/sandbox/benchmark/test_config.py`

```python
def test_benchmark_config_creation():
    """Test creating BenchmarkConfig."""

def test_benchmark_config_validation():
    """Test config validation logic."""

def test_success_criteria_validation():
    """Test success criteria validation."""

def test_workflow_phase_config_validation():
    """Test phase config validation."""

def test_load_from_yaml():
    """Test loading config from YAML."""

def test_load_from_json():
    """Test loading config from JSON."""

def test_example_configs_validate():
    """Test that all example configs are valid."""
```

---

## Notes

- Keep schema simple initially, extend as needed
- Focus on essential fields first
- Ensure good error messages for validation failures
- Schema should support both simple and complex benchmarks
