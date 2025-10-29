# Story 7.2.6: Load Complete Workflow Registry (55+ Workflows)

**Epic**: 7.2 - Workflow-Driven Core Architecture
**Story Points**: 2
**Status**: Ready
**Priority**: High

---

## User Story

As a **GAO-Dev system**, I want to **load and register all 55+ workflows from GAO-Dev** (not just PRD/Story workflows), so that **Brian can select from the complete catalog of available workflows across all phases**.

---

## Context

Currently, the workflow registry only loads a subset of workflows. GAO-Dev has 55+ workflows across 4 phases but they're not all being loaded and made available for Brian's selection.

**Problem**:
- Workflow registry incomplete - doesn't load all workflows
- Missing Phase 1 (Analysis) workflows: brainstorm, research, product-brief, etc.
- Missing Test Architecture workflows: atdd, ci, test-design, etc.
- Missing helper workflows: workflow-status, sprint-status
- Brian can't select from full catalog
- Terminology inconsistent ("bmm workflows" vs "workflows in GAO-Dev")

**Solution**:
Enhance WorkflowRegistry to:
1. Recursively load all workflows from `bmad/bmm/workflows/`
2. Parse workflow.yaml files across all phases
3. Build complete workflow catalog (55+ workflows)
4. Enable Brian to discover and select any workflow
5. Update terminology throughout codebase

---

## Acceptance Criteria

### AC1: Recursive Workflow Loading
- [ ] WorkflowRegistry recursively scans `bmad/bmm/workflows/`
- [ ] Discovers all workflow.yaml files
- [ ] Parses workflow definitions from all phases
- [ ] Handles sub-workflows (e.g., document-project/deep-dive)

### AC2: Complete Workflow Catalog
- [ ] Load Phase 1 workflows (7 workflows): brainstorm-game, brainstorm-project, document-project, game-brief, product-brief, research
- [ ] Load Phase 2 workflows (5 workflows): prd, gdd, tech-spec, create-ux-design, narrative
- [ ] Load Phase 3 workflows (2 workflows): architecture, solutioning-gate-check
- [ ] Load Phase 4 workflows (10 workflows): create-story, dev-story, story-ready, story-done, review-story, correct-course, retrospective, sprint-planning, epic-tech-context, story-context
- [ ] Load Test Architecture workflows (9 workflows): atdd, automate, ci, framework, nfr-assess, test-design, test-review, trace
- [ ] Load Helper workflows (3 workflows): workflow-status, sprint-status, init
- [ ] Total: 36+ major workflows loaded (55+ including sub-workflows)

### AC3: Workflow Metadata
- [ ] Each workflow includes:
  - Name, description, phase
  - Required agent (analyst, pm, architect, sm, dev, tea)
  - Input requirements
  - Output artifacts
  - Dependencies on other workflows

### AC4: Workflow Discovery API
- [ ] `list_workflows(phase: Optional[str] = None)` - List workflows by phase
- [ ] `get_workflow(name: str)` - Get specific workflow by name
- [ ] `search_workflows(query: str)` - Search workflows by keyword
- [ ] `get_workflows_by_agent(agent: str)` - Get workflows for specific agent

### AC5: Terminology Updates
- [ ] Change "bmm workflows" → "workflows in GAO-Dev" throughout codebase
- [ ] Change "BMAD workflows" → "GAO-Dev workflows" in user-facing docs
- [ ] Update comments and docstrings
- [ ] BMAD remains implementation detail only

### AC6: Tests
- [ ] Unit tests for recursive loading
- [ ] Test workflow count (>= 36 major workflows)
- [ ] Test workflow discovery by phase
- [ ] Test workflow search
- [ ] >80% code coverage

---

## Technical Details

### Enhanced WorkflowRegistry

```python
# gao_dev/core/workflow_registry.py

from pathlib import Path
from typing import List, Optional, Dict
import yaml

class WorkflowRegistry:
    """
    Complete workflow registry loading all 55+ workflows from GAO-Dev.

    Workflows are loaded from bmad/bmm/workflows/ but referred to as
    "workflows in GAO-Dev" (BMAD is implementation detail).
    """

    def __init__(self, workflows_dir: Optional[Path] = None):
        """
        Initialize workflow registry.

        Args:
            workflows_dir: Path to workflows (default: bmad/bmm/workflows/)
        """
        self.workflows_dir = workflows_dir or self._get_default_workflows_dir()
        self.workflows: Dict[str, Workflow] = {}
        self._load_all_workflows()

    def _load_all_workflows(self):
        """
        Recursively load all workflows from workflow directory.

        Scans for workflow.yaml files in:
        - 1-analysis/
        - 2-plan-workflows/
        - 3-solutioning/
        - 4-implementation/
        - testarch/
        - helpers/
        """
        workflow_files = self.workflows_dir.rglob("workflow.yaml")

        for workflow_file in workflow_files:
            workflow = self._parse_workflow(workflow_file)
            if workflow:
                self.workflows[workflow.name] = workflow

        self.logger.info(
            "workflows_loaded",
            count=len(self.workflows),
            phases=self._count_by_phase()
        )

    def _parse_workflow(self, workflow_file: Path) -> Optional[Workflow]:
        """Parse workflow.yaml file into Workflow object."""
        try:
            with open(workflow_file, 'r') as f:
                data = yaml.safe_load(f)

            # Determine phase from directory structure
            phase = self._determine_phase(workflow_file)

            return Workflow(
                name=data.get('name'),
                description=data.get('description'),
                phase=phase,
                agent=data.get('agent'),
                input_requirements=data.get('inputs', []),
                output_artifacts=data.get('outputs', []),
                steps=data.get('steps', [])
            )
        except Exception as e:
            self.logger.warning(
                "workflow_parse_failed",
                file=str(workflow_file),
                error=str(e)
            )
            return None

    def _determine_phase(self, workflow_file: Path) -> str:
        """Determine phase from directory structure."""
        parts = workflow_file.parts
        if "1-analysis" in parts:
            return "Phase 1: Analysis"
        elif "2-plan-workflows" in parts:
            return "Phase 2: Planning"
        elif "3-solutioning" in parts:
            return "Phase 3: Solutioning"
        elif "4-implementation" in parts:
            return "Phase 4: Implementation"
        elif "testarch" in parts:
            return "Test Architecture"
        elif "helpers" in parts or "workflow-status" in parts:
            return "Helpers"
        return "Unknown"

    def list_workflows(self, phase: Optional[str] = None) -> List[Workflow]:
        """
        List all workflows, optionally filtered by phase.

        Args:
            phase: Optional phase filter (e.g., "Phase 1: Analysis")

        Returns:
            List of Workflow objects
        """
        if phase:
            return [w for w in self.workflows.values() if w.phase == phase]
        return list(self.workflows.values())

    def get_workflow(self, name: str) -> Optional[Workflow]:
        """Get specific workflow by name."""
        return self.workflows.get(name)

    def search_workflows(self, query: str) -> List[Workflow]:
        """Search workflows by keyword in name or description."""
        query_lower = query.lower()
        return [
            w for w in self.workflows.values()
            if query_lower in w.name.lower() or
               query_lower in (w.description or "").lower()
        ]

    def get_workflows_by_agent(self, agent: str) -> List[Workflow]:
        """Get all workflows for specific agent."""
        return [w for w in self.workflows.values() if w.agent == agent]

    def _count_by_phase(self) -> Dict[str, int]:
        """Count workflows by phase."""
        counts = {}
        for workflow in self.workflows.values():
            counts[workflow.phase] = counts.get(workflow.phase, 0) + 1
        return counts
```

---

## Testing Strategy

```python
# tests/test_workflow_registry.py

def test_load_all_workflows():
    """Test that all workflows are loaded."""
    registry = WorkflowRegistry()

    # Should load 36+ major workflows
    assert len(registry.workflows) >= 36

    # Verify phase distribution
    counts = registry._count_by_phase()
    assert counts.get("Phase 1: Analysis", 0) >= 6
    assert counts.get("Phase 2: Planning", 0) >= 5
    assert counts.get("Phase 3: Solutioning", 0) >= 2
    assert counts.get("Phase 4: Implementation", 0) >= 10
    assert counts.get("Test Architecture", 0) >= 8

def test_workflow_discovery():
    """Test workflow discovery APIs."""
    registry = WorkflowRegistry()

    # Test get by name
    prd = registry.get_workflow("prd")
    assert prd is not None
    assert prd.phase == "Phase 2: Planning"

    # Test list by phase
    impl_workflows = registry.list_workflows("Phase 4: Implementation")
    assert len(impl_workflows) >= 10

    # Test search
    story_workflows = registry.search_workflows("story")
    assert len(story_workflows) >= 5

def test_terminology():
    """Test that terminology is consistent."""
    registry = WorkflowRegistry()

    # Check that we refer to workflows consistently
    # (no "bmm workflows" in user-facing strings)
    pass
```

---

## Dependencies

- **WorkflowRegistry**: Already exists, needs enhancement
- **BMAD Workflows**: All 55+ workflows in `bmad/bmm/workflows/` (EXIST)
- **PyYAML**: For parsing workflow.yaml files (INSTALLED)

---

## Definition of Done

- [ ] WorkflowRegistry loads all 55+ workflows recursively
- [ ] All phases covered (Phase 1-4, Test Architecture, Helpers)
- [ ] Workflow discovery APIs implemented (list, get, search)
- [ ] Terminology updated throughout codebase
- [ ] Unit tests passing (>80% coverage)
- [ ] Workflow count verified (>= 36 major workflows)
- [ ] Type hints complete (mypy passes)
- [ ] Docstrings for all public methods
- [ ] Code review completed
- [ ] Story committed atomically to git

---

## Out of Scope

- Workflow execution (Story 7.2.2)
- Workflow validation/linting
- Workflow versioning
- Custom workflow creation UI

---

## Notes

- This is foundational for Brian's workflow selection - can't select what's not loaded!
- Focus on completeness - load ALL workflows
- Terminology change is important for user clarity
- Recursive loading handles sub-workflows automatically
- Workflow metadata enables Brian to make informed selections
