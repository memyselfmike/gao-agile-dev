# Story 7.2.1: Create Brian Agent & Scale-Adaptive Workflow Selection

**Epic**: 7.2 - Workflow-Driven Core Architecture
**Story Points**: 5
**Status**: Ready
**Priority**: High

---

## User Story

As a **GAO-Dev system**, I want **Brian (Workflow Orchestrator agent) to analyze project complexity and intelligently select scale-appropriate workflow sequences**, so that **I can autonomously determine the optimal development approach based on project scale (Level 0-4) without external orchestration**.

---

## Context

Currently, workflows are defined and orchestrated by the benchmark system. GAO-Dev needs **Brian**, the Workflow Orchestrator agent, to analyze prompts, assess project complexity using scale-adaptive principles (Level 0-4), and select appropriate workflow sequences.

**Problem**:
- Benchmark defines workflow phases and agent sequence (wrong!)
- GAO-Dev is passive, just executes what benchmark tells it
- No intelligence in workflow selection - no scale-level assessment
- No Brian agent to orchestrate workflows
- 55+ workflows in GAO-Dev (`bmad/bmm/workflows/`) aren't being intelligently selected
- Scale-adaptive routing (BMAD's core innovation) not implemented

**Solution**:
Create **Brian agent** (Workflow Orchestrator) who:
1. Analyzes initial prompts using AI
2. Assesses project complexity and assigns scale level (0-4)
3. Selects appropriate workflow sequences based on scale
4. Routes based on project type (game/software) and context (greenfield/brownfield)
5. Asks clarifying questions when scope is ambiguous

---

## Acceptance Criteria

### AC1: Brian Agent Created
- [ ] Create `gao_dev/agents/brian.md` agent definition (DONE - see brian.md)
- [ ] Brian persona defined with scale-adaptive expertise
- [ ] Agent registered in GAODevOrchestrator

### AC2: Scale-Adaptive Workflow Selection Class
- [ ] Create `gao_dev/orchestrator/brian_orchestrator.py`
- [ ] `BrianOrchestrator` class implementing Brian agent logic
- [ ] Uses AI (Claude) to analyze prompts and assess complexity
- [ ] Returns scale level (0-4) and workflow sequence

### AC3: Scale Level Assessment
- [ ] Analyzes initial prompt to determine:
  - **Scale Level** (0: atomic change, 1: small feature, 2: medium, 3: large, 4: enterprise)
  - Project type (game/software/mobile/backend/etc.)
  - Context (greenfield vs brownfield)
  - Domain complexity indicators
  - Technical complexity indicators
- [ ] Uses AI with structured prompt for scale assessment

### AC4: Workflow Sequence Building
- [ ] Builds complete workflow sequences based on scale level:
  - **Level 0**: [tech-spec, create-story, dev-story]
  - **Level 1**: [tech-spec, create-story (x3), dev-story (x3)]
  - **Level 2**: [prd, tech-spec, implementation loop]
  - **Level 3-4**: [prd, architecture, JIT tech-specs, implementation loop]
  - **Game projects**: [game-brief (optional), gdd, solutioning (if complex), implementation]
  - **Brownfield**: [document-project (required first), then normal flow]
- [ ] Returns list of Workflow objects in execution order

### AC5: Integration with GAODevOrchestrator
- [ ] Add `brian_orchestrator` attribute to GAODevOrchestrator
- [ ] Initialize BrianOrchestrator with workflow registry
- [ ] Add method: `assess_and_select_workflows(prompt: str) -> WorkflowSequence`
- [ ] WorkflowSequence includes scale_level, workflows list, routing_rationale

### AC6: Clarification Questions
- [ ] If scope ambiguous, returns clarifying questions
- [ ] Questions focus on scale indicators (scope, timeline, complexity)
- [ ] Can re-analyze with clarification answers

### AC7: Logging and Observability
- [ ] Log scale level assessment with reasoning
- [ ] Log workflow sequence selection with rationale
- [ ] Include confidence scores in logs
- [ ] Structured logging for Brian's decisions

### AC8: Tests
- [ ] Unit tests for BrianOrchestrator
- [ ] Test scale level assessment for various prompts
  - Level 0: "Fix login bug"
  - Level 1: "Add user profile page"
  - Level 2: "Build todo app"
  - Level 3: "Create CRM system with 3 modules"
  - Level 4: "Enterprise ERP system"
- [ ] Test game vs software routing
- [ ] Test greenfield vs brownfield detection
- [ ] Test ambiguous prompts that need clarification
- [ ] >80% code coverage

---

## Technical Details

### File Structure

```
gao_dev/orchestrator/
├── orchestrator.py           # Add workflow selection capability
├── workflow_selector.py      # NEW - WorkflowSelector class
└── workflow_results.py       # Existing
```

### WorkflowSelector Implementation

```python
# gao_dev/orchestrator/workflow_selector.py

from typing import List, Union, Optional, Dict, Any
from dataclasses import dataclass
import structlog
from anthropic import Anthropic

from ..core.workflow_registry import WorkflowRegistry, Workflow

logger = structlog.get_logger()


@dataclass
class PromptAnalysis:
    """Analysis of an initial user prompt."""
    project_type: str  # greenfield, enhancement, bug_fix, maintenance
    scope: str  # simple, medium, complex
    required_phases: List[str]  # e.g., ["planning", "architecture", "implementation"]
    technology_hints: List[str]  # e.g., ["python", "web", "api"]
    confidence: float  # 0.0-1.0
    reasoning: str  # Why this analysis was chosen


@dataclass
class WorkflowSelection:
    """Result of workflow selection."""
    workflow: Optional[Workflow]
    confidence: float
    reasoning: str
    clarifying_questions: List[str] = None  # If workflow unclear


class WorkflowSelector:
    """
    Intelligently selects appropriate workflow based on initial prompt.

    Uses AI to analyze user intent and match to BMAD workflows.
    """

    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        api_key: Optional[str] = None
    ):
        """
        Initialize workflow selector.

        Args:
            workflow_registry: Registry of available workflows
            api_key: Anthropic API key (optional, uses env var if not provided)
        """
        self.workflow_registry = workflow_registry
        self.anthropic = Anthropic(api_key=api_key) if api_key else Anthropic()
        self.logger = logger.bind(component="workflow_selector")

    async def select_workflow(
        self,
        initial_prompt: str,
        available_workflows: Optional[List[Workflow]] = None
    ) -> WorkflowSelection:
        """
        Analyze prompt and select best workflow.

        Args:
            initial_prompt: User's initial request
            available_workflows: List of workflows to choose from
                               (if None, uses all from registry)

        Returns:
            WorkflowSelection with chosen workflow or clarifying questions
        """
        # Get available workflows
        if available_workflows is None:
            available_workflows = self.workflow_registry.list_workflows()

        # Analyze the prompt
        analysis = await self._analyze_prompt(initial_prompt, available_workflows)

        # Select workflow based on analysis
        selection = self._match_workflow(analysis, available_workflows)

        # Log decision
        self.logger.info(
            "workflow_selected",
            workflow=selection.workflow.name if selection.workflow else None,
            confidence=selection.confidence,
            reasoning=selection.reasoning
        )

        return selection

    async def _analyze_prompt(
        self,
        prompt: str,
        available_workflows: List[Workflow]
    ) -> PromptAnalysis:
        """
        Use AI to analyze the initial prompt.

        Returns structured analysis of user intent.
        """
        # Format workflows for prompt
        workflow_descriptions = self._format_workflows(available_workflows)

        # Create analysis prompt
        analysis_prompt = f"""Analyze this software development request and determine the appropriate workflow.

User Request:
{prompt}

Available Workflows:
{workflow_descriptions}

Analyze the request and determine:
1. Project type: Is this greenfield (new project), enhancement (add features), bug_fix (fix issues), or maintenance (refactor/cleanup)?
2. Scope: Is this simple (1-2 stories), medium (3-10 stories), or complex (>10 stories)?
3. Required phases: Which development phases are needed? (analysis, planning, architecture, implementation, testing)
4. Technology hints: What technologies or domains are mentioned? (python, web, api, etc.)
5. Confidence: How confident are you in this analysis? (0.0-1.0)
6. Reasoning: Explain your analysis in 1-2 sentences.

Return your analysis in JSON format:
{{
    "project_type": "greenfield|enhancement|bug_fix|maintenance",
    "scope": "simple|medium|complex",
    "required_phases": ["phase1", "phase2", ...],
    "technology_hints": ["tech1", "tech2", ...],
    "confidence": 0.85,
    "reasoning": "Explanation here..."
}}
"""

        # Call Claude for analysis
        response = self.anthropic.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{"role": "user", "content": analysis_prompt}]
        )

        # Parse response (simplified - should add robust JSON parsing)
        import json
        analysis_data = json.loads(response.content[0].text)

        return PromptAnalysis(**analysis_data)

    def _match_workflow(
        self,
        analysis: PromptAnalysis,
        available_workflows: List[Workflow]
    ) -> WorkflowSelection:
        """
        Match analysis to best workflow.

        Returns workflow or clarifying questions if ambiguous.
        """
        # Simplified matching logic
        # In production, this should be more sophisticated

        if analysis.project_type == "greenfield":
            # Look for full development workflow
            for workflow in available_workflows:
                if "prd" in workflow.name.lower() or "greenfield" in workflow.name.lower():
                    return WorkflowSelection(
                        workflow=workflow,
                        confidence=analysis.confidence,
                        reasoning=f"Selected {workflow.name} for greenfield project: {analysis.reasoning}"
                    )

        elif analysis.project_type == "enhancement":
            # Look for story-based workflow
            for workflow in available_workflows:
                if "story" in workflow.name.lower() or "feature" in workflow.name.lower():
                    return WorkflowSelection(
                        workflow=workflow,
                        confidence=analysis.confidence,
                        reasoning=f"Selected {workflow.name} for enhancement: {analysis.reasoning}"
                    )

        # If no clear match, ask for clarification
        return WorkflowSelection(
            workflow=None,
            confidence=0.0,
            reasoning="Could not determine appropriate workflow",
            clarifying_questions=[
                "Is this a new project (greenfield) or enhancing an existing one?",
                "What is the approximate scope? (small feature, medium project, large system)",
                "Do you need architecture design or just implementation?"
            ]
        )

    def _format_workflows(self, workflows: List[Workflow]) -> str:
        """Format workflows for prompt."""
        lines = []
        for wf in workflows:
            lines.append(f"- {wf.name}: {wf.description or 'No description'}")
            lines.append(f"  Phases: {', '.join(wf.phases)}")
        return "\n".join(lines)
```

### Integration with GAODevOrchestrator

```python
# gao_dev/orchestrator/orchestrator.py

from .workflow_selector import WorkflowSelector, WorkflowSelection

class GAODevOrchestrator:

    def __init__(self, project_root: Optional[Path] = None, api_key: Optional[str] = None):
        # Existing initialization...

        # NEW: Initialize workflow selector
        self.workflow_selector = WorkflowSelector(
            workflow_registry=self.workflow_registry,
            api_key=api_key
        )

    async def select_workflow_for_prompt(self, initial_prompt: str) -> WorkflowSelection:
        """
        Select appropriate workflow for the given prompt.

        Args:
            initial_prompt: User's initial request

        Returns:
            WorkflowSelection with chosen workflow or clarifying questions
        """
        return await self.workflow_selector.select_workflow(initial_prompt)
```

---

## Testing Strategy

### Unit Tests (`tests/test_workflow_selector.py`)

```python
import pytest
from gao_dev.orchestrator.workflow_selector import WorkflowSelector, PromptAnalysis

@pytest.mark.asyncio
async def test_greenfield_prompt_selection():
    """Test that greenfield prompts select appropriate workflow."""
    selector = WorkflowSelector(workflow_registry=mock_registry)

    prompt = "Build a new todo application with Python and FastAPI"
    selection = await selector.select_workflow(prompt)

    assert selection.workflow is not None
    assert "greenfield" in selection.workflow.name.lower()
    assert selection.confidence > 0.7

@pytest.mark.asyncio
async def test_enhancement_prompt_selection():
    """Test that enhancement prompts select story workflow."""
    selector = WorkflowSelector(workflow_registry=mock_registry)

    prompt = "Add user authentication to existing app"
    selection = await selector.select_workflow(prompt)

    assert selection.workflow is not None
    assert "story" in selection.workflow.name.lower()

@pytest.mark.asyncio
async def test_ambiguous_prompt_asks_questions():
    """Test that ambiguous prompts return clarifying questions."""
    selector = WorkflowSelector(workflow_registry=mock_registry)

    prompt = "Fix it"
    selection = await selector.select_workflow(prompt)

    assert selection.workflow is None
    assert len(selection.clarifying_questions) > 0
```

---

## Dependencies

- **Epic 7**: Autonomous Artifact Creation (COMPLETE)
- **Epic 7.1**: Integration & Architecture Fix (COMPLETE)
- **WorkflowRegistry**: Must be functional (EXISTS)
- **Anthropic SDK**: For AI-powered analysis (INSTALLED)

---

## Definition of Done

- [ ] Brian agent definition file created (`gao_dev/agents/brian.md`)
- [ ] BrianOrchestrator class created with scale-adaptive logic
- [ ] Scale level assessment (Level 0-4) working with AI
- [ ] Workflow sequence building based on scale level
- [ ] Integration with GAODevOrchestrator complete
- [ ] Clarification questions for ambiguous prompts
- [ ] Structured logging for Brian's decisions and reasoning
- [ ] Unit tests written and passing (>80% coverage)
  - Tests for each scale level (0-4)
  - Tests for game vs software routing
  - Tests for greenfield vs brownfield
- [ ] Type hints complete (mypy passes)
- [ ] Docstrings for all public methods
- [ ] Code review completed
- [ ] Story committed atomically to git

---

## Story Enhancement Notes

**Original Story Points**: 3 points
**Updated Story Points**: 5 points (+2 points)

**Reason for Increase**:
- Added Brian agent creation and persona definition
- Added scale-adaptive complexity assessment (Level 0-4)
- Added workflow sequence building (not just single workflow selection)
- Added support for game projects, brownfield projects, multi-phase routing
- Increased scope to match BMAD Method's scale-adaptive principles

---

## Out of Scope

- Complex multi-turn clarification dialog (Story 7.2.4)
- Full workflow execution (Story 7.2.2)
- Benchmark integration (Story 7.2.3)

---

## Notes

- Keep workflow matching logic simple initially - can be improved iteratively
- Focus on common cases: greenfield, enhancement, bug fix
- Logging is critical for understanding selection decisions
- Use structured prompts to get consistent analysis from Claude
