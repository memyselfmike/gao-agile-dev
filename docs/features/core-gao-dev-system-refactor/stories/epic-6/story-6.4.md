# Story 6.4: Extract QualityGateManager Service

**Epic**: 6 - Legacy Cleanup & God Class Refactoring
**Story Points**: 3
**Priority**: P0 (Critical)
**Type**: Refactoring
**Status**: Ready

---

## Overview

Extract artifact validation and quality gate logic from `GAODevOrchestrator` into a dedicated `QualityGateManager` service.

---

## User Story

**As a** GAO-Dev architect
**I want** quality gate validation isolated
**So that** artifact checking is consistent and testable

---

## Acceptance Criteria

1. **Service Created**
   - [ ] `gao_dev/core/services/quality_gate.py` created
   - [ ] Class `QualityGateManager` < 150 lines
   - [ ] Single responsibility: Validate workflow outputs

2. **Functionality**
   - [ ] Validates workflow produced expected artifacts
   - [ ] Checks file existence and structure
   - [ ] Validates content against templates/schemas
   - [ ] Reports validation failures with details
   - [ ] Publishes validation events

3. **Testing**
   - [ ] Unit tests for each validator
   - [ ] Test valid/invalid artifacts
   - [ ] Test validation reporting
   - [ ] Mock file system for tests

---

## Technical Details

```python
class QualityGateManager:
    """Validate workflow artifacts meet quality standards."""

    def __init__(
        self,
        validators: List[IArtifactValidator],
        event_bus: IEventBus
    ):
        pass

    async def validate_artifacts(
        self,
        workflow_id: str,
        artifacts: List[Artifact]
    ) -> ValidationResult:
        """
        Validate workflow produced expected artifacts.

        Returns: ValidationResult with pass/fail and details
        """
        pass

    def add_validator(self, validator: IArtifactValidator) -> None:
        """Add custom validator."""
        pass
```

---

## Implementation Steps

1. Create service file
2. Define IArtifactValidator interface
3. Implement built-in validators (file exists, schema validation)
4. Extract validation logic from orchestrator
5. Write comprehensive tests
6. Update orchestrator

---

## Definition of Done

- [ ] QualityGateManager created (< 150 lines)
- [ ] All acceptance criteria met
- [ ] Unit tests (80%+ coverage)
- [ ] Orchestrator updated
- [ ] Tests pass

---

**Related Stories**: 6.1, 6.5
**Estimated Time**: Half day
