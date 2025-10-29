# Story 7.2.1: Create Workflow Selector

**Epic**: 7.2 - Workflow-Driven Core Architecture
**Story Points**: 3
**Status**: Ready
**Priority**: High

---

## User Story

As a **GAO-Dev system**, I want to **intelligently select the appropriate workflow based on an initial prompt**, so that **I can autonomously determine how to approach each development task without external orchestration**.

---

## Context

Currently, workflows are defined and orchestrated by the benchmark system. GAO-Dev needs the ability to analyze an initial prompt, understand user intent, and select the most appropriate workflow from the BMAD registry.

**Problem**:
- Benchmark defines workflow phases and agent sequence
- GAO-Dev is passive, just executes what benchmark tells it
- No intelligence in workflow selection
- BMAD workflows in `bmad/bmm/workflows/` aren't used

**Solution**:
Create a `WorkflowSelector` component that uses AI to analyze prompts and select appropriate workflows.

---

## Acceptance Criteria

### AC1: WorkflowSelector Class Created
- [ ] Create `gao_dev/orchestrator/workflow_selector.py`
- [ ] `WorkflowSelector` class with `select_workflow()` method
- [ ] Uses AI (Claude) to analyze prompts
- [ ] Returns selected `Workflow` object or list of clarifying questions

### AC2: Prompt Analysis
- [ ] Analyzes initial prompt to understand:
  - Project type (greenfield, enhancement, bug fix, maintenance)
  - Scope (simple, medium, complex)
  - Required phases (analysis, planning, architecture, implementation)
  - Domain/technology hints
- [ ] Uses structured prompt to Claude for analysis

### AC3: Workflow Matching
- [ ] Loads available workflows from workflow registry
- [ ] Matches user intent to workflow capabilities
- [ ] Returns best matching workflow
- [ ] If ambiguous, returns clarifying questions

### AC4: Integration with GAODevOrchestrator
- [ ] Add `workflow_selector` attribute to GAODevOrchestrator
- [ ] Initialize WorkflowSelector with workflow registry
- [ ] Add method: `select_workflow_for_prompt(prompt: str) -> Union[Workflow, List[str]]`

### AC5: Logging and Observability
- [ ] Log workflow selection decision and reasoning
- [ ] Include confidence score or reasoning in logs
- [ ] Structured logging for analysis

### AC6: Tests
- [ ] Unit tests for WorkflowSelector
- [ ] Test various prompt types (greenfield, enhancement, bug fix)
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

- [ ] WorkflowSelector class created with select_workflow() method
- [ ] Prompt analysis uses AI to understand user intent
- [ ] Workflow matching returns best workflow or clarifying questions
- [ ] Integrated with GAODevOrchestrator
- [ ] Structured logging for selection decisions
- [ ] Unit tests written and passing (>80% coverage)
- [ ] Type hints complete (mypy passes)
- [ ] Docstrings for all public methods
- [ ] Code review completed
- [ ] Story committed atomically to git

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
