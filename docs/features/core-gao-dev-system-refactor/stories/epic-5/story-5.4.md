# Story 5.4: Decouple Core from BMAD Specifics

**Epic**: Epic 5 - Methodology Abstraction
**Story Points**: 5
**Priority**: P2 (Medium)
**Status**: Ready

---

## User Story

**As a** core developer
**I want** core orchestrator to use IMethodology interface instead of BMAD specifics
**So that** core has zero BMAD dependencies and can work with any methodology

---

## Description

Refactor core orchestrator and related components to use `IMethodology` interface instead of direct BMAD references. Remove all `ScaleLevel`, BMAD-specific assumptions from core.

**Current State**:
- Core imports from brian_orchestrator
- ScaleLevel references throughout core
- BMAD workflow assumptions
- Direct coupling to BMAD agents

**Target State**:
- Core uses IMethodology interface
- Methodology selected from registry
- Generic ComplexityLevel (not ScaleLevel)
- brian_orchestrator.py deleted

---

## Acceptance Criteria

### Core Refactoring

- [ ] **GAODevOrchestrator refactored**:
  - Accepts `methodology: IMethodology` in constructor
  - No direct BMAD imports
  - Uses methodology.assess_complexity()
  - Uses methodology.build_workflow_sequence()
  - Uses methodology.get_recommended_agents()

- [ ] **Remove brian_orchestrator.py**:
  - All logic moved to BMADMethodology
  - File deleted
  - All imports updated

- [ ] **Remove ScaleLevel from core**:
  - No ScaleLevel imports in core/
  - Replace with ComplexityLevel
  - ScaleLevel only in methodologies/bmad/

- [ ] **Configuration support**:
  - `methodology` config option added
  - Defaults to "bmad"
  - Can specify alternative methodology
  - Validates methodology exists

### Integration Points

- [ ] **Workflow selection**:
  - Uses methodology.build_workflow_sequence()
  - No BMAD-specific workflow logic in core

- [ ] **Agent selection**:
  - Uses methodology.get_recommended_agents()
  - No hardcoded agent lists in core

- [ ] **Complexity assessment**:
  - Uses methodology.assess_complexity()
  - No direct Brian orchestrator calls

### Backward Compatibility

- [ ] **Default behavior preserved**:
  - BMAD still default methodology
  - Existing configs work without changes
  - All existing functionality intact

- [ ] **Migration path**:
  - Old code continues working
  - New code uses methodology interface
  - Gradual migration supported

### Testing

- [ ] Unit tests with mock methodology (85%+ coverage)
- [ ] Integration tests with BMAD methodology
- [ ] Integration tests with alternative methodology
- [ ] Regression tests - all existing tests pass
- [ ] Configuration tests

---

## Technical Details

### Refactored Orchestrator

```python
from typing import Optional
from gao_dev.core.interfaces.methodology import IMethodology
from gao_dev.methodologies.registry import MethodologyRegistry

class GAODevOrchestrator:
    """Core orchestrator - now methodology-agnostic."""

    def __init__(
        self,
        config_loader,
        methodology: Optional[IMethodology] = None
    ):
        """Initialize orchestrator.

        Args:
            config_loader: Configuration loader
            methodology: Methodology to use (defaults to BMAD from registry)
        """
        self.config_loader = config_loader

        # Get methodology from registry if not provided
        if methodology is None:
            registry = MethodologyRegistry.get_instance()
            methodology_name = config_loader.get("methodology", "bmad")
            methodology = registry.get_methodology(methodology_name)

        self.methodology = methodology

    async def execute_workflow(self, prompt: str):
        """Execute workflow using configured methodology."""

        # Use methodology to assess complexity
        assessment = await self.methodology.assess_complexity(prompt)

        # Use methodology to build workflow sequence
        sequence = self.methodology.build_workflow_sequence(assessment)

        # Execute workflows
        for step in sequence.workflows:
            # Get recommended agents from methodology
            agents = self.methodology.get_recommended_agents(
                step.workflow_name,
                context={"phase": step.phase}
            )

            # Execute workflow step
            await self._execute_step(step, agents)
```

### Configuration

```yaml
# gao_dev/config/defaults.yaml

# Methodology configuration
methodology: bmad  # Options: bmad, scrum, kanban, custom

# BMAD-specific config (only used if methodology=bmad)
bmad:
  default_scale_level: 2
  use_brian_agent: true

# Alternative methodology configs
scrum:
  sprint_length_days: 14

kanban:
  wip_limit: 5
```

### Files to Refactor

1. **gao_dev/orchestrator/orchestrator.py**:
   - Remove ScaleLevel imports
   - Add IMethodology interface usage
   - Remove direct brian_orchestrator imports

2. **gao_dev/core/workflow_coordinator.py**:
   - Use methodology for workflow selection
   - Remove BMAD hardcoding

3. **DELETE gao_dev/core/brian_orchestrator.py**:
   - All logic moved to BMADMethodology (Story 5.2)
   - File no longer needed

---

## Definition of Done

- [ ] Core has zero BMAD dependencies
- [ ] brian_orchestrator.py deleted
- [ ] ScaleLevel removed from core
- [ ] IMethodology interface used throughout
- [ ] Configuration supports methodology selection
- [ ] 85%+ test coverage
- [ ] All existing tests pass (backward compatible)
- [ ] Integration tests with multiple methodologies
- [ ] Code review approved
- [ ] Committed to feature branch

---

## Files to Modify

1. `gao_dev/orchestrator/orchestrator.py`
2. `gao_dev/core/workflow_coordinator.py`
3. `gao_dev/config/defaults.yaml`
4. All core files importing brian_orchestrator

---

## Files to Delete

1. `gao_dev/core/brian_orchestrator.py` (logic moved to BMADMethodology)

---

## Related

- **Previous**: Story 5.3 - Methodology Registry
- **Next**: Story 5.5 - Example Alternative Methodology
- **Critical**: Story 5.2 must be complete (BMAD extracted)
