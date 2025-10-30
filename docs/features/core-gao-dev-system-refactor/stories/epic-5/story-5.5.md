# Story 5.5: Create Example Alternative Methodology

**Epic**: Epic 5 - Methodology Abstraction
**Story Points**: 2
**Priority**: P2 (Medium)
**Status**: Ready

---

## User Story

**As a** core developer
**I want** an example alternative methodology implementation
**So that** I can prove the abstraction works and provide a template for custom methodologies

---

## Description

Create `SimpleMethodology` - a minimal alternative methodology that proves IMethodology abstraction works. Simpler than BMAD, demonstrates pluggability.

**Current State**: Only BMAD exists.

**Target State**: Working `SimpleMethodology` in `gao_dev/methodologies/simple/` that can be used as template for custom methodologies.

---

## Acceptance Criteria

### SimpleMethodology Implementation

- [ ] **Directory created**: `gao_dev/methodologies/simple/`
- [ ] **SimpleMethodology class** implements IMethodology
- [ ] **Size**: < 200 lines (minimal implementation)
- [ ] **Simpler than BMAD**: 3 complexity levels (not 5)
- [ ] **Works end-to-end**: Can run complete workflow

### Simplified Approach

- [ ] **3 complexity levels** (not 5):
  - SMALL: Quick task (hours)
  - MEDIUM: Feature (days)
  - LARGE: Project (weeks)

- [ ] **Simplified workflow selection**:
  - SMALL: Direct implementation
  - MEDIUM: Plan → Implement → Test
  - LARGE: Design → Plan → Implement → Test

- [ ] **Simplified agent recommendations**:
  - Single agent per phase
  - No BMAD-specific agents
  - Generic agent selection

### Method Implementations

- [ ] **assess_complexity()**:
  - Simple keyword-based analysis (no Claude API)
  - Returns SMALL/MEDIUM/LARGE based on keywords
  - Fast, deterministic assessment

- [ ] **build_workflow_sequence()**:
  - Maps complexity to simple workflow
  - Fewer phases than BMAD
  - Linear, no complex dependencies

- [ ] **get_recommended_agents()**:
  - Simple phase-based recommendations
  - Not BMAD-specific

- [ ] **validate_config()**:
  - Minimal validation
  - No complex rules

### Documentation

- [ ] **README.md** in simple/ directory:
  - Explains SimpleMethodology approach
  - Shows how to use it
  - Template for custom methodologies
  - Comparison with BMAD

### Testing

- [ ] Unit tests for SimpleMethodology (80%+ coverage)
- [ ] Test all complexity levels
- [ ] Test workflow generation
- [ ] Integration test: Run with SimpleMethodology
- [ ] All existing tests pass

---

## Technical Details

```python
# gao_dev/methodologies/simple/simple_methodology.py

from typing import Dict, List, Optional, Any
from gao_dev.core.interfaces.methodology import (
    IMethodology,
    ComplexityAssessment,
    ComplexityLevel,
    WorkflowSequence,
    WorkflowStep,
    ValidationResult,
    ProjectType
)

class SimpleMethodology(IMethodology):
    """Simple alternative methodology.

    Demonstrates IMethodology implementation with minimal complexity.
    Uses 3 levels (not 5), keyword-based analysis, linear workflows.

    Complexity Levels:
        SMALL: Hours - Quick task or bug fix
        MEDIUM: Days - Feature with planning
        LARGE: Weeks - Project with design

    Example:
        ```python
        from gao_dev.methodologies.simple import SimpleMethodology
        from gao_dev.methodologies.registry import MethodologyRegistry

        # Register SimpleMethodology
        registry = MethodologyRegistry.get_instance()
        registry.register_methodology(SimpleMethodology())

        # Use it
        simple = registry.get_methodology("simple")
        assessment = await simple.assess_complexity("Fix login bug")
        # Returns SMALL complexity
        ```
    """

    @property
    def name(self) -> str:
        return "simple"

    @property
    def description(self) -> str:
        return "Simple 3-level methodology for straightforward projects"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supports_scale_levels(self) -> bool:
        return False  # No scale levels in Simple

    async def assess_complexity(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ComplexityAssessment:
        """Assess complexity using keyword analysis."""

        prompt_lower = prompt.lower()

        # LARGE indicators
        large_keywords = [
            "application", "system", "platform", "full stack",
            "greenfield", "from scratch", "entire", "complete"
        ]

        # SMALL indicators
        small_keywords = [
            "fix", "bug", "typo", "update", "change", "quick",
            "simple", "minor", "small"
        ]

        # Check for LARGE
        if any(kw in prompt_lower for kw in large_keywords):
            complexity = ComplexityLevel.LARGE
            reasoning = "Detected large project keywords"
        # Check for SMALL
        elif any(kw in prompt_lower for kw in small_keywords):
            complexity = ComplexityLevel.SMALL
            reasoning = "Detected small task keywords"
        # Default to MEDIUM
        else:
            complexity = ComplexityLevel.MEDIUM
            reasoning = "Default medium complexity (feature-sized)"

        return ComplexityAssessment(
            complexity_level=complexity,
            project_type=self._detect_project_type(prompt),
            confidence=0.6,  # Lower confidence (no AI analysis)
            reasoning=reasoning,
            metadata={"methodology": "simple"}
        )

    def build_workflow_sequence(
        self,
        assessment: ComplexityAssessment
    ) -> WorkflowSequence:
        """Build simple workflow sequence."""

        if assessment.complexity_level == ComplexityLevel.SMALL:
            # SMALL: Direct implementation
            workflows = [
                WorkflowStep("implement", "implementation", required=True)
            ]
        elif assessment.complexity_level == ComplexityLevel.MEDIUM:
            # MEDIUM: Plan → Implement → Test
            workflows = [
                WorkflowStep("plan", "planning", required=True),
                WorkflowStep("implement", "implementation", required=True),
                WorkflowStep("test", "testing", required=True)
            ]
        else:  # LARGE
            # LARGE: Design → Plan → Implement → Test
            workflows = [
                WorkflowStep("design", "design", required=True),
                WorkflowStep("plan", "planning", required=True),
                WorkflowStep("implement", "implementation", required=True),
                WorkflowStep("test", "testing", required=True)
            ]

        return WorkflowSequence(
            workflows=workflows,
            total_phases=len({w.phase for w in workflows}),
            can_parallelize=False,
            metadata={"methodology": "simple"}
        )

    def get_recommended_agents(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Recommend agents based on phase."""

        context = context or {}
        phase = context.get("phase", "").lower()

        # Simple phase-based recommendations
        if "design" in phase:
            return ["Architect"]
        elif "plan" in phase:
            return ["Planner"]
        elif "implement" in phase:
            return ["Developer"]
        elif "test" in phase:
            return ["Tester"]
        else:
            return ["Developer"]  # Default

    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Minimal validation."""
        # SimpleMethodology has no complex config requirements
        return ValidationResult(valid=True, errors=[], warnings=[])

    def _detect_project_type(self, prompt: str) -> Optional[ProjectType]:
        """Simple project type detection."""
        prompt_lower = prompt.lower()

        if "web" in prompt_lower or "website" in prompt_lower:
            return ProjectType.WEB_APP
        elif "api" in prompt_lower:
            return ProjectType.API
        elif "cli" in prompt_lower or "command" in prompt_lower:
            return ProjectType.CLI
        else:
            return ProjectType.UNKNOWN
```

### README Template

```markdown
# SimpleMethodology

A minimal alternative methodology demonstrating IMethodology implementation.

## Overview

SimpleMethodology is intentionally simple to show how custom methodologies can be created. It uses:
- 3 complexity levels (SMALL, MEDIUM, LARGE)
- Keyword-based analysis (no AI)
- Linear workflows
- Simple agent recommendations

## When to Use

- Small projects that don't need BMAD complexity
- Learning how to create custom methodologies
- Template for your own methodology

## Complexity Levels

| Level | Duration | Description | Workflow |
|-------|----------|-------------|----------|
| SMALL | Hours | Quick tasks, bug fixes | Implement only |
| MEDIUM | Days | Features with planning | Plan → Implement → Test |
| LARGE | Weeks | Projects with design | Design → Plan → Implement → Test |

## Usage

```python
from gao_dev.methodologies.registry import MethodologyRegistry

# Get SimpleMethodology
registry = MethodologyRegistry.get_instance()
simple = registry.get_methodology("simple")

# Use it
assessment = await simple.assess_complexity("Build a todo app")
# Returns MEDIUM complexity

workflows = simple.build_workflow_sequence(assessment)
# Returns: Plan → Implement → Test
```

## Creating Your Own Methodology

Use SimpleMethodology as a template:

1. Copy `simple/` directory to `methodologies/your_methodology/`
2. Implement IMethodology interface
3. Customize complexity assessment logic
4. Define your workflow sequences
5. Register in MethodologyRegistry

See `docs/methodology-development-guide.md` for details.
```

---

## Definition of Done

- [ ] SimpleMethodology implements IMethodology
- [ ] 3 complexity levels working
- [ ] Workflow generation for all levels
- [ ] Agent recommendations implemented
- [ ] README with usage examples
- [ ] 80%+ test coverage
- [ ] Integration test passes
- [ ] Can be registered and used
- [ ] All existing tests pass
- [ ] Code review approved
- [ ] Committed to feature branch

---

## Files to Create

1. `gao_dev/methodologies/simple/__init__.py`
2. `gao_dev/methodologies/simple/simple_methodology.py`
3. `gao_dev/methodologies/simple/README.md`
4. `tests/methodologies/simple/test_simple_methodology.py`

---

## Files to Modify

1. `gao_dev/methodologies/__init__.py` - Export SimpleMethodology

---

## Related

- **Previous**: Story 5.4 - Decouple Core from BMAD
- **Validates**: Epic 5 - Proves abstraction works
- **Template**: For custom methodology development

---

## Notes

- Keep it simple - this is a proof-of-concept
- No Claude API calls - use keyword matching
- Linear workflows only - no complex dependencies
- Useful as template for custom methodologies
- Can serve as fallback methodology
