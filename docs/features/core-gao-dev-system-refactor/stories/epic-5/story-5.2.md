# Story 5.2: Extract BMAD Methodology Implementation

**Epic**: Epic 5 - Methodology Abstraction
**Story Points**: 8
**Priority**: P2 (Medium)
**Status**: Ready

---

## User Story

**As a** core developer
**I want** all BMAD-specific logic extracted into a dedicated BMADMethodology class
**So that** BMAD is just one methodology implementation (not hardcoded in core)

---

## Description

Extract all BMAD Method logic from `brian_orchestrator.py` and other core files into a dedicated `BMADMethodology` class that implements `IMethodology`. This is the largest refactoring in Epic 5.

**Current State**: BMAD logic scattered throughout:
- `brian_orchestrator.py` - Scale level analysis, workflow selection
- Core orchestrator - BMAD assumptions everywhere
- Workflow selection - Hardcoded BMAD scale levels (0-4)

**Target State**: Clean `BMADMethodology` class in `gao_dev/methodologies/bmad/` containing all BMAD logic, implementing IMethodology interface.

---

## Acceptance Criteria

### BMAD Methodology Implementation

- [ ] **Directory created**: `gao_dev/methodologies/bmad/`
- [ ] **BMADMethodology class** implements IMethodology completely
- [ ] **Size**: < 500 lines (complex logic, acceptable)
- [ ] **All BMAD logic extracted** from brian_orchestrator.py
- [ ] **Backward compatible**: Existing BMAD behavior preserved 100%

### Core Classes

- [ ] **BMADMethodology class** (main implementation):
  - Implements all IMethodology methods
  - Contains scale level logic (0-4)
  - Contains workflow selection strategy
  - Contains agent recommendation logic
  - Preserves all existing BMAD behavior

- [ ] **ScaleLevel enum** (BMAD-specific):
  - LEVEL_0_CHORE = 0 (minutes)
  - LEVEL_1_BUG_FIX = 1 (hours)
  - LEVEL_2_SMALL_FEATURE = 2 (3-8 stories)
  - LEVEL_3_MEDIUM_FEATURE = 3 (12-20 stories)
  - LEVEL_4_GREENFIELD = 4 (40+ stories)
  - Maps to ComplexityLevel from IMethodology

- [ ] **BMADAnalysis dataclass** (BMAD-specific assessment):
  - scale_level: ScaleLevel
  - project_type: ProjectType
  - estimated_stories: int
  - estimated_epics: int
  - recommended_workflows: List[str]
  - agent_recommendations: Dict[str, List[str]]
  - complexity_indicators: Dict[str, Any]

### Method Implementations

- [ ] **assess_complexity() implementation**:
  - Uses Claude API to analyze prompt
  - Applies BMAD scale level logic
  - Returns ComplexityAssessment with BMAD metadata
  - Uses existing brian_orchestrator logic
  - Preserves confidence scoring
  - Maps ScaleLevel to ComplexityLevel

- [ ] **build_workflow_sequence() implementation**:
  - Based on scale level, select workflows
  - Level 0: Simple workflows (chores)
  - Level 1: Bug fix workflows
  - Level 2: Small feature (PRD → Stories → Implementation)
  - Level 3: Medium feature (full BMAD phases)
  - Level 4: Greenfield (all phases + architecture)
  - Returns WorkflowSequence with BMAD strategy

- [ ] **get_recommended_agents() implementation**:
  - Based on task and phase, recommend agents
  - Analysis: Mary (Business Analyst)
  - Planning: John (Product Manager)
  - Design: Winston (Architect), Sally (UX Designer)
  - Implementation: Bob (Scrum Master), Amelia (Developer)
  - Testing: Murat (Test Architect)
  - BMAD-specific agent selection rules

- [ ] **validate_config() implementation**:
  - Validates BMAD-specific config
  - Checks scale_level (0-4)
  - Validates project_type
  - Returns ValidationResult

### Migration Strategy

- [ ] **Extract without breaking**:
  - Keep brian_orchestrator.py temporarily
  - Create BMADMethodology alongside
  - Test both implementations in parallel
  - Ensure 100% behavioral equivalence
  - Remove brian_orchestrator.py in Story 5.4

- [ ] **Preserve existing behavior**:
  - All scale level logic intact
  - All workflow selection rules identical
  - All agent recommendations unchanged
  - Confidence scoring preserved
  - Prompt analysis using same Claude prompts

### Testing

- [ ] Unit tests for BMADMethodology (85%+ coverage)
- [ ] Test each scale level (0-4)
- [ ] Test workflow sequence generation per level
- [ ] Test agent recommendations per phase
- [ ] Integration test: Compare old vs new behavior
- [ ] Regression test: All existing BMAD tests pass
- [ ] All existing tests still pass (100%)

---

## Technical Details

### Implementation Strategy

**1. Create BMAD Package Structure**:

```
gao_dev/methodologies/
  __init__.py
  bmad/
    __init__.py
    bmad_methodology.py      # Main BMADMethodology class
    scale_levels.py          # ScaleLevel enum and mappings
    workflow_selector.py     # Workflow selection logic
    agent_recommender.py     # Agent recommendation logic
    prompts.py              # Claude prompts for analysis
```

**2. Implement BMADMethodology Class**:

```python
from typing import Dict, List, Optional, Any
from gao_dev.core.interfaces.methodology import (
    IMethodology,
    ComplexityAssessment,
    ComplexityLevel,
    WorkflowSequence,
    WorkflowStep,
    ValidationResult
)
from .scale_levels import ScaleLevel, map_scale_to_complexity
from .workflow_selector import BMADWorkflowSelector
from .agent_recommender import BMADAgentRecommender

class BMADMethodology(IMethodology):
    """BMAD Method implementation.

    Business, Market, Architecture, Development (BMAD) is a scale-adaptive
    agile methodology with 5 scale levels (0-4) for different project sizes.

    Scale Levels:
        0. Chore (minutes) - Simple tasks
        1. Bug Fix (hours) - Single file changes
        2. Small Feature (days) - 3-8 stories
        3. Medium Feature (weeks) - 12-20 stories
        4. Greenfield (months) - 40+ stories, full application

    Features:
        - Scale-adaptive workflow selection
        - Brian agent for complexity analysis
        - 7 specialized agents (Mary, John, Winston, Sally, Bob, Amelia, Murat)
        - 4 phases (Analysis, Planning, Solutioning, Implementation)
    """

    def __init__(self, config_loader=None):
        """Initialize BMAD methodology.

        Args:
            config_loader: Optional config loader for BMAD settings
        """
        self.config_loader = config_loader
        self.workflow_selector = BMADWorkflowSelector()
        self.agent_recommender = BMADAgentRecommender()

    @property
    def name(self) -> str:
        return "bmad"

    @property
    def description(self) -> str:
        return "Business, Market, Architecture, Development (BMAD) - Scale-adaptive agile methodology"

    @property
    def version(self) -> str:
        return "6.0.0-alpha"

    @property
    def supports_scale_levels(self) -> bool:
        return True

    async def assess_complexity(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ComplexityAssessment:
        """Assess complexity using BMAD scale levels.

        Uses Brian agent (via Claude API) to analyze prompt and determine:
        - Scale level (0-4)
        - Project type
        - Estimated stories and epics
        - Confidence score

        Args:
            prompt: User's initial request
            context: Optional context (project history, etc.)

        Returns:
            ComplexityAssessment with BMAD scale level in metadata
        """
        # Use existing Brian orchestrator logic
        from gao_dev.core.brian_orchestrator import analyze_prompt_complexity

        # Analyze using Brian (Claude API call)
        analysis_result = await analyze_prompt_complexity(prompt, context)

        # Extract BMAD-specific data
        scale_level = analysis_result.get("scale_level", 2)
        project_type = analysis_result.get("project_type", "web_app")
        estimated_stories = analysis_result.get("estimated_stories", 5)
        estimated_epics = analysis_result.get("estimated_epics", 1)
        confidence = analysis_result.get("confidence", 0.7)
        reasoning = analysis_result.get("reasoning", "")

        # Map ScaleLevel to ComplexityLevel
        complexity_level = map_scale_to_complexity(ScaleLevel(scale_level))

        return ComplexityAssessment(
            complexity_level=complexity_level,
            project_type=ProjectType(project_type),
            estimated_stories=estimated_stories,
            estimated_epics=estimated_epics,
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                "methodology": "bmad",
                "scale_level": scale_level,
                "bmad_analysis": analysis_result
            }
        )

    def build_workflow_sequence(
        self,
        assessment: ComplexityAssessment
    ) -> WorkflowSequence:
        """Build BMAD workflow sequence based on scale level.

        Args:
            assessment: Complexity assessment with BMAD scale level in metadata

        Returns:
            WorkflowSequence with BMAD workflows
        """
        # Extract BMAD scale level from metadata
        scale_level = ScaleLevel(assessment.metadata.get("scale_level", 2))

        # Use workflow selector to get BMAD workflows
        workflows = self.workflow_selector.select_workflows(scale_level)

        return WorkflowSequence(
            workflows=workflows,
            total_phases=self._count_phases(workflows),
            can_parallelize=False,  # BMAD is sequential
            metadata={
                "methodology": "bmad",
                "scale_level": scale_level.value
            }
        )

    def get_recommended_agents(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Recommend BMAD agents for task.

        Args:
            task: Task description or type
            context: Optional context (phase, workflow, etc.)

        Returns:
            List of BMAD agent names
        """
        return self.agent_recommender.recommend(task, context)

    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate BMAD-specific configuration.

        Args:
            config: Configuration dictionary

        Returns:
            ValidationResult with errors/warnings
        """
        errors = []
        warnings = []

        # Validate scale level if present
        if "scale_level" in config:
            scale_level = config["scale_level"]
            if not isinstance(scale_level, int) or not 0 <= scale_level <= 4:
                errors.append(
                    f"Invalid scale_level: {scale_level}. Must be 0-4."
                )

        # Validate project type if present
        valid_types = [t.value for t in ProjectType]
        if "project_type" in config:
            if config["project_type"] not in valid_types:
                warnings.append(
                    f"Unknown project_type: {config['project_type']}"
                )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _count_phases(self, workflows: List[WorkflowStep]) -> int:
        """Count unique phases in workflow sequence."""
        phases = {w.phase for w in workflows}
        return len(phases)
```

**3. Implement Scale Level Mapping**:

```python
# gao_dev/methodologies/bmad/scale_levels.py

from enum import IntEnum
from gao_dev.core.interfaces.methodology import ComplexityLevel

class ScaleLevel(IntEnum):
    """BMAD scale levels (0-4)."""
    LEVEL_0_CHORE = 0         # Minutes: Typo, config change
    LEVEL_1_BUG_FIX = 1       # Hours: Single file bug fix
    LEVEL_2_SMALL_FEATURE = 2 # Days: 3-8 stories, simple feature
    LEVEL_3_MEDIUM_FEATURE = 3  # Weeks: 12-20 stories, complex feature
    LEVEL_4_GREENFIELD = 4    # Months: 40+ stories, full application

def map_scale_to_complexity(scale_level: ScaleLevel) -> ComplexityLevel:
    """Map BMAD scale level to generic complexity level."""
    mapping = {
        ScaleLevel.LEVEL_0_CHORE: ComplexityLevel.TRIVIAL,
        ScaleLevel.LEVEL_1_BUG_FIX: ComplexityLevel.SMALL,
        ScaleLevel.LEVEL_2_SMALL_FEATURE: ComplexityLevel.MEDIUM,
        ScaleLevel.LEVEL_3_MEDIUM_FEATURE: ComplexityLevel.LARGE,
        ScaleLevel.LEVEL_4_GREENFIELD: ComplexityLevel.XLARGE,
    }
    return mapping[scale_level]
```

**4. Implement Workflow Selector**:

```python
# gao_dev/methodologies/bmad/workflow_selector.py

from typing import List
from gao_dev.core.interfaces.methodology import WorkflowStep
from .scale_levels import ScaleLevel

class BMADWorkflowSelector:
    """Selects BMAD workflows based on scale level.

    Implements BMAD's scale-adaptive workflow selection strategy.
    """

    def select_workflows(self, scale_level: ScaleLevel) -> List[WorkflowStep]:
        """Select workflows for given scale level."""
        if scale_level == ScaleLevel.LEVEL_0_CHORE:
            return self._level_0_workflows()
        elif scale_level == ScaleLevel.LEVEL_1_BUG_FIX:
            return self._level_1_workflows()
        elif scale_level == ScaleLevel.LEVEL_2_SMALL_FEATURE:
            return self._level_2_workflows()
        elif scale_level == ScaleLevel.LEVEL_3_MEDIUM_FEATURE:
            return self._level_3_workflows()
        elif scale_level == ScaleLevel.LEVEL_4_GREENFIELD:
            return self._level_4_workflows()
        else:
            raise ValueError(f"Invalid scale level: {scale_level}")

    def _level_0_workflows(self) -> List[WorkflowStep]:
        """Level 0: Chore - Direct implementation."""
        return [
            WorkflowStep("direct-implementation", "implementation", required=True)
        ]

    def _level_1_workflows(self) -> List[WorkflowStep]:
        """Level 1: Bug Fix - Quick fix with verification."""
        return [
            WorkflowStep("analyze-bug", "analysis", required=True),
            WorkflowStep("implement-fix", "implementation", required=True),
            WorkflowStep("verify-fix", "testing", required=True)
        ]

    def _level_2_workflows(self) -> List[WorkflowStep]:
        """Level 2: Small Feature - PRD → Stories → Implementation."""
        return [
            WorkflowStep("create-prd", "planning", required=True),
            WorkflowStep("create-stories", "planning", required=True),
            WorkflowStep("implement-stories", "implementation", required=True),
            WorkflowStep("test-feature", "testing", required=True)
        ]

    def _level_3_workflows(self) -> List[WorkflowStep]:
        """Level 3: Medium Feature - Full BMAD phases."""
        return [
            # Planning
            WorkflowStep("create-prd", "planning", required=True),
            WorkflowStep("create-epics", "planning", required=True),
            WorkflowStep("create-stories", "planning", required=True),
            # Solutioning
            WorkflowStep("create-architecture", "solutioning", required=True),
            WorkflowStep("create-tech-spec", "solutioning", required=False),
            # Implementation
            WorkflowStep("implement-stories", "implementation", required=True),
            WorkflowStep("code-review", "implementation", required=True),
            # Testing
            WorkflowStep("integration-testing", "testing", required=True)
        ]

    def _level_4_workflows(self) -> List[WorkflowStep]:
        """Level 4: Greenfield - All phases + architecture."""
        return [
            # Analysis
            WorkflowStep("research", "analysis", required=False),
            WorkflowStep("product-brief", "analysis", required=False),
            # Planning
            WorkflowStep("create-prd", "planning", required=True),
            WorkflowStep("create-epics", "planning", required=True),
            WorkflowStep("create-stories", "planning", required=True),
            # Solutioning
            WorkflowStep("create-architecture", "solutioning", required=True),
            WorkflowStep("create-tech-spec", "solutioning", required=True),
            WorkflowStep("design-database", "solutioning", required=True),
            WorkflowStep("design-api", "solutioning", required=False),
            # Implementation
            WorkflowStep("implement-stories", "implementation", required=True),
            WorkflowStep("code-review", "implementation", required=True),
            WorkflowStep("create-tests", "implementation", required=True),
            # Testing
            WorkflowStep("integration-testing", "testing", required=True),
            WorkflowStep("e2e-testing", "testing", required=True)
        ]
```

**5. Implement Agent Recommender**:

```python
# gao_dev/methodologies/bmad/agent_recommender.py

from typing import Dict, List, Optional, Any

class BMADAgentRecommender:
    """Recommends BMAD agents for tasks."""

    PHASE_AGENTS = {
        "analysis": ["Mary"],  # Business Analyst
        "planning": ["John", "Bob"],  # PM, Scrum Master
        "solutioning": ["Winston", "Sally"],  # Architect, UX Designer
        "implementation": ["Bob", "Amelia", "Murat"],  # SM, Dev, Test Architect
        "testing": ["Murat", "Amelia"]  # Test Architect, Dev
    }

    def recommend(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Recommend agents for task."""
        context = context or {}

        # Check if phase specified in context
        phase = context.get("phase")
        if phase and phase in self.PHASE_AGENTS:
            return self.PHASE_AGENTS[phase]

        # Check task keywords
        task_lower = task.lower()
        if "research" in task_lower or "analysis" in task_lower:
            return ["Mary"]
        elif "prd" in task_lower or "plan" in task_lower:
            return ["John", "Bob"]
        elif "architecture" in task_lower or "design" in task_lower:
            return ["Winston", "Sally"]
        elif "implement" in task_lower or "code" in task_lower:
            return ["Bob", "Amelia"]
        elif "test" in task_lower:
            return ["Murat"]
        else:
            # Default: All agents
            return ["Mary", "John", "Winston", "Sally", "Bob", "Amelia", "Murat"]
```

---

## Dependencies

- **Depends On**: Story 5.1 complete (IMethodology interface exists)
- **Blocks**: Story 5.4 (Core refactoring needs BMAD extracted)

---

## Definition of Done

- [ ] BMADMethodology class implements IMethodology completely
- [ ] All BMAD logic extracted from brian_orchestrator.py
- [ ] ScaleLevel enum and mapping implemented
- [ ] Workflow selector with all 5 scale levels
- [ ] Agent recommender with BMAD agents
- [ ] 85%+ test coverage
- [ ] Behavioral equivalence verified (old vs new)
- [ ] All existing tests pass (100%)
- [ ] Code review approved
- [ ] Committed to feature branch
- [ ] Documentation updated

---

## Files to Create

1. `gao_dev/methodologies/bmad/__init__.py`
2. `gao_dev/methodologies/bmad/bmad_methodology.py` - Main class
3. `gao_dev/methodologies/bmad/scale_levels.py` - ScaleLevel enum
4. `gao_dev/methodologies/bmad/workflow_selector.py` - Workflow selection
5. `gao_dev/methodologies/bmad/agent_recommender.py` - Agent recommendations
6. `gao_dev/methodologies/bmad/prompts.py` - Claude prompts (optional)
7. `tests/methodologies/bmad/test_bmad_methodology.py`
8. `tests/methodologies/bmad/test_workflow_selector.py`
9. `tests/methodologies/bmad/test_agent_recommender.py`

---

## Files to Modify

1. `gao_dev/methodologies/__init__.py` - Export BMADMethodology
2. Keep `gao_dev/core/brian_orchestrator.py` (remove in Story 5.4)

---

## Related

- **Epic**: Epic 5 - Methodology Abstraction
- **Previous Story**: Story 5.1 - Create IMethodology Interface
- **Next Story**: Story 5.3 - Implement Methodology Registry
- **Migration**: Story 5.4 will remove brian_orchestrator.py

---

## Notes

- This is the largest story in Epic 5 (8 points)
- Extract carefully - preserve all BMAD behavior
- Test extensively - regression critical
- Brian orchestrator stays until Story 5.4
- Focus on clean extraction, not optimization
