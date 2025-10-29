# Story 7.2.2: Add Multi-Workflow Sequence Executor to Core

**Epic**: 7.2 - Workflow-Driven Core Architecture
**Story Points**: 7
**Status**: Done
**Priority**: High

---

## User Story

As a **GAO-Dev system**, I want to **execute multi-workflow sequences autonomously across phases (Analysis → Planning → Solutioning → Implementation)**, so that **I can independently orchestrate complete development lifecycles from initial prompt to production-ready code**.

---

## Context

Currently, the benchmark system orchestrates workflow execution. This story adds **multi-workflow sequence execution** to GAO-Dev core, enabling complete lifecycle orchestration across phases.

**Problem**:
- Can only execute single workflows, not sequences (PRD → Architecture → Stories)
- No phase transition handling (Phase 2 → Phase 3 → Phase 4)
- No Just-In-Time (JIT) tech-spec generation during implementation
- Workflow execution logic scattered in benchmark system
- Can't handle scale-adaptive workflow paths (Level 0-4 require different sequences)

**Solution**:
Add `execute_workflow_sequence()` method to GAODevOrchestrator that:
1. Takes initial prompt or uses Brian's selected workflow sequence (Story 7.2.1)
2. Executes workflows in sequence across phases:
   - Phase 1 (Analysis) → Phase 2 (Planning) → Phase 3 (Solutioning) → Phase 4 (Implementation)
3. Handles phase transitions with state persistence
4. Supports JIT tech-spec generation (one per epic during Phase 4)
5. Calls appropriate agents per workflow step
6. Manages state, creates artifacts, commits after each workflow
7. Returns comprehensive multi-workflow results

---

## Acceptance Criteria

### AC1: Workflow Execution Method
- [ ] Add `execute_workflow(initial_prompt: str, workflow: Optional[Workflow] = None)` to GAODevOrchestrator
- [ ] If workflow not provided, use WorkflowSelector to choose one
- [ ] Execute workflow steps sequentially
- [ ] Return WorkflowResult with metrics and artifacts

### AC2: Workflow Step Execution
- [ ] Create `_execute_step(step: WorkflowStep)` private method
- [ ] Parse step definition to determine agent and task
- [ ] Call appropriate agent method (create_prd, implement_story, etc.)
- [ ] Collect agent output and artifacts
- [ ] Handle step failures gracefully

### AC3: State Management
- [ ] Track workflow progress (current step, completed steps)
- [ ] Persist state to allow resume on failure
- [ ] Update state after each step completion
- [ ] Clean state on successful completion

### AC4: Artifact Collection
- [ ] Collect artifacts created during each step
- [ ] Parse agent output for artifact paths
- [ ] Verify artifacts exist on disk
- [ ] Record artifact metadata in WorkflowResult

### AC5: Git Integration
- [ ] Commit artifacts after each workflow step (optional)
- [ ] Use GitCommitManager for atomic commits
- [ ] Include step name and workflow in commit message
- [ ] Track commit hashes in WorkflowResult

### AC6: Error Handling
- [ ] Handle step failures (timeout, agent error, validation failure)
- [ ] Provide detailed error messages
- [ ] Allow workflow to fail-fast or continue on error (configurable)
- [ ] Log errors with full context

### AC7: Metrics Collection
- [ ] Track time per step
- [ ] Track tokens used (if available from agent)
- [ ] Track cost per step
- [ ] Include metrics in WorkflowResult

### AC8: Logging and Observability
- [ ] Structured logging for workflow execution
- [ ] Log workflow start/end with metadata
- [ ] Log each step start/completion
- [ ] Progress indicators for long-running workflows

### AC9: Tests
- [ ] Unit tests for execute_workflow()
- [ ] Unit tests for _execute_step()
- [ ] Integration test with simple workflow
- [ ] Test error handling and failure scenarios
- [ ] >80% code coverage

---

## Technical Details

### File Structure

```
gao_dev/orchestrator/
├── orchestrator.py           # Add execute_workflow() method
├── workflow_executor.py      # NEW - WorkflowExecutor class (optional refactor)
├── workflow_results.py       # Add WorkflowResult dataclass
└── workflow_selector.py      # From Story 7.2.1
```

### WorkflowResult Dataclass

```python
# gao_dev/orchestrator/workflow_results.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class WorkflowStatus(Enum):
    """Status of workflow execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class WorkflowStepResult:
    """Result of executing a single workflow step."""
    step_name: str
    agent: str
    status: str  # success, failed, skipped
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    artifacts_created: List[str] = field(default_factory=list)
    commit_hash: Optional[str] = None
    error_message: Optional[str] = None
    output: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowResult:
    """Result of executing complete workflow."""
    workflow_name: str
    initial_prompt: str
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    step_results: List[WorkflowStepResult] = field(default_factory=list)
    total_artifacts: int = 0
    project_path: Optional[str] = None

    @property
    def success(self) -> bool:
        """Check if workflow completed successfully."""
        return self.status == WorkflowStatus.COMPLETED

    @property
    def duration_seconds(self) -> float:
        """Total workflow duration."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def total_steps(self) -> int:
        """Total number of steps."""
        return len(self.step_results)

    @property
    def successful_steps(self) -> int:
        """Number of successful steps."""
        return sum(1 for step in self.step_results if step.status == "success")
```

### Execute Workflow Implementation

```python
# gao_dev/orchestrator/orchestrator.py

from datetime import datetime
from typing import Optional, AsyncGenerator
from .workflow_results import WorkflowResult, WorkflowStepResult, WorkflowStatus
from .workflow_selector import WorkflowSelection
from ..core.workflow_registry import Workflow, WorkflowStep

class GAODevOrchestrator:

    async def execute_workflow(
        self,
        initial_prompt: str,
        workflow: Optional[Workflow] = None,
        commit_after_steps: bool = True
    ) -> WorkflowResult:
        """
        Execute complete workflow from initial prompt.

        This is the core autonomous execution method that:
        1. Selects appropriate workflow (if not provided)
        2. Executes workflow steps sequentially
        3. Calls agents to perform tasks
        4. Creates artifacts and commits to git
        5. Returns comprehensive results

        Args:
            initial_prompt: User's initial request
            workflow: Optional pre-selected workflow (if None, auto-select)
            commit_after_steps: Whether to commit after each step

        Returns:
            WorkflowResult with execution details and metrics
        """
        # Initialize result
        result = WorkflowResult(
            workflow_name=workflow.name if workflow else "auto-select",
            initial_prompt=initial_prompt,
            status=WorkflowStatus.IN_PROGRESS,
            start_time=datetime.now(),
            project_path=str(self.project_root) if self.project_root else None
        )

        try:
            # Step 1: Select workflow if not provided
            if workflow is None:
                self.logger.info("workflow_auto_select", prompt=initial_prompt)
                selection: WorkflowSelection = await self.select_workflow_for_prompt(
                    initial_prompt
                )

                if selection.workflow is None:
                    # Need clarification
                    result.status = WorkflowStatus.FAILED
                    result.end_time = datetime.now()
                    self.logger.warning(
                        "workflow_needs_clarification",
                        questions=selection.clarifying_questions
                    )
                    # TODO: Handle clarification (Story 7.2.4)
                    return result

                workflow = selection.workflow
                result.workflow_name = workflow.name

            self.logger.info(
                "workflow_execution_started",
                workflow=workflow.name,
                steps=len(workflow.steps)
            )

            # Step 2: Execute workflow steps sequentially
            for i, step in enumerate(workflow.steps, 1):
                self.logger.info(
                    "workflow_step_started",
                    step=i,
                    total=len(workflow.steps),
                    step_name=step.name
                )

                step_result = await self._execute_step(
                    step=step,
                    step_number=i,
                    total_steps=len(workflow.steps)
                )

                result.step_results.append(step_result)

                # Commit after step if enabled
                if commit_after_steps and step_result.status == "success":
                    commit_hash = await self._commit_step_artifacts(
                        step=step,
                        step_result=step_result,
                        workflow_name=workflow.name
                    )
                    step_result.commit_hash = commit_hash

                # Fail-fast: Stop on first failure
                if step_result.status == "failed":
                    self.logger.error(
                        "workflow_step_failed",
                        step=step.name,
                        error=step_result.error_message
                    )
                    result.status = WorkflowStatus.FAILED
                    break

            # Step 3: Mark complete if all steps succeeded
            if result.status != WorkflowStatus.FAILED:
                result.status = WorkflowStatus.COMPLETED
                self.logger.info(
                    "workflow_execution_completed",
                    workflow=workflow.name,
                    steps_completed=len(result.step_results),
                    duration=result.duration_seconds
                )

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            self.logger.error(
                "workflow_execution_error",
                workflow=workflow.name if workflow else "unknown",
                error=str(e),
                exc_info=True
            )

        finally:
            result.end_time = datetime.now()
            result.total_artifacts = sum(
                len(step.artifacts_created) for step in result.step_results
            )

        return result

    async def _execute_step(
        self,
        step: WorkflowStep,
        step_number: int,
        total_steps: int
    ) -> WorkflowStepResult:
        """
        Execute a single workflow step.

        Maps step to appropriate agent method and executes.
        """
        step_result = WorkflowStepResult(
            step_name=step.name,
            agent=step.agent,
            status="in_progress",
            start_time=datetime.now()
        )

        try:
            # Map step to agent method
            agent_method = self._get_agent_method(step.agent, step.task_type)

            if agent_method is None:
                raise ValueError(f"No method found for agent {step.agent} task {step.task_type}")

            # Execute agent method
            output_parts = []
            async for message in agent_method(**step.parameters):
                output_parts.append(message)
                # Could yield progress here for real-time updates

            step_result.output = "\n".join(output_parts)

            # Parse artifacts from output
            step_result.artifacts_created = self._parse_artifacts(step_result.output)

            step_result.status = "success"

        except Exception as e:
            step_result.status = "failed"
            step_result.error_message = str(e)
            self.logger.error(
                "step_execution_failed",
                step=step.name,
                agent=step.agent,
                error=str(e)
            )

        finally:
            step_result.end_time = datetime.now()
            step_result.duration_seconds = (
                step_result.end_time - step_result.start_time
            ).total_seconds()

        return step_result

    def _get_agent_method(self, agent_name: str, task_type: str):
        """
        Map agent name and task type to orchestrator method.

        Examples:
        - agent="John", task="create_prd" -> self.create_prd
        - agent="Amelia", task="implement_story" -> self.implement_story
        """
        # Task type mapping
        method_map = {
            "create_prd": self.create_prd,
            "create_architecture": self.create_architecture,
            "create_story": self.create_story,
            "implement_story": self.implement_story,
            "validate_story": self.validate_story,
        }

        return method_map.get(task_type)

    def _parse_artifacts(self, output: str) -> List[str]:
        """
        Parse artifact paths from agent output.

        Looks for file paths in output.
        """
        # Simplified - should use ArtifactParser from Epic 7
        artifacts = []
        lines = output.split("\n")
        for line in lines:
            if "Created:" in line or "Writing:" in line or "File:" in line:
                # Extract file path
                # This is simplified - production should use regex or parser
                pass
        return artifacts

    async def _commit_step_artifacts(
        self,
        step: WorkflowStep,
        step_result: WorkflowStepResult,
        workflow_name: str
    ) -> Optional[str]:
        """
        Commit artifacts created in this step.

        Returns commit hash if successful.
        """
        if not step_result.artifacts_created:
            return None

        try:
            # Use GitCommitManager
            from ..sandbox.git_commit_manager import GitCommitManager

            git_manager = GitCommitManager(
                project_root=self.project_root,
                run_id=workflow_name
            )

            commit_hash = await git_manager.commit_phase_artifacts(
                phase_name=step.name,
                agent_name=step.agent,
                artifact_paths=step_result.artifacts_created
            )

            return commit_hash

        except Exception as e:
            self.logger.warning(
                "step_commit_failed",
                step=step.name,
                error=str(e)
            )
            return None
```

---

## Testing Strategy

### Unit Tests (`tests/test_workflow_executor.py`)

```python
import pytest
from unittest.mock import Mock, AsyncMock
from gao_dev.orchestrator import GAODevOrchestrator
from gao_dev.orchestrator.workflow_results import WorkflowStatus

@pytest.mark.asyncio
async def test_execute_workflow_success():
    """Test successful workflow execution."""
    orchestrator = GAODevOrchestrator(project_root="/tmp/test")

    # Mock workflow with 2 steps
    workflow = Mock()
    workflow.name = "test-workflow"
    workflow.steps = [
        Mock(name="Step 1", agent="John", task_type="create_prd", parameters={}),
        Mock(name="Step 2", agent="Amelia", task_type="implement_story", parameters={})
    ]

    result = await orchestrator.execute_workflow(
        initial_prompt="Build todo app",
        workflow=workflow
    )

    assert result.success
    assert result.status == WorkflowStatus.COMPLETED
    assert len(result.step_results) == 2
    assert result.successful_steps == 2

@pytest.mark.asyncio
async def test_execute_workflow_step_failure():
    """Test workflow stops on step failure."""
    orchestrator = GAODevOrchestrator(project_root="/tmp/test")

    # Mock workflow where step 2 fails
    workflow = Mock()
    workflow.steps = [
        Mock(name="Step 1", agent="John", task_type="create_prd", parameters={}),
        Mock(name="Step 2", agent="Bad", task_type="invalid", parameters={})
    ]

    result = await orchestrator.execute_workflow(
        initial_prompt="Build app",
        workflow=workflow
    )

    assert not result.success
    assert result.status == WorkflowStatus.FAILED
    assert len(result.step_results) == 2  # Both attempted
    assert result.step_results[1].status == "failed"

@pytest.mark.asyncio
async def test_execute_workflow_auto_select():
    """Test workflow auto-selection from prompt."""
    orchestrator = GAODevOrchestrator(project_root="/tmp/test")

    # Should auto-select greenfield workflow
    result = await orchestrator.execute_workflow(
        initial_prompt="Build a new todo application with Python"
    )

    # Workflow should be selected automatically
    assert result.workflow_name != "auto-select"
```

### Integration Tests (`tests/integration/test_workflow_execution.py`)

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow_execution():
    """Test complete workflow execution end-to-end."""
    # This test requires actual BMAD workflows and agents
    # Should be run in sandbox environment
    pass
```

---

## Dependencies

- **Story 7.2.1**: Workflow Selector (REQUIRED)
- **Epic 7**: ArtifactParser, GitCommitManager (EXISTS)
- **WorkflowRegistry**: Must load BMAD workflows (EXISTS)
- **Agent Methods**: create_prd, implement_story, etc. (EXIST)

---

## Definition of Done

- [ ] execute_workflow() method added to GAODevOrchestrator
- [ ] Workflow steps executed sequentially with proper agent calls
- [ ] State management tracks workflow progress
- [ ] Artifacts collected and recorded
- [ ] Git commits created after each step (optional)
- [ ] Error handling for step failures
- [ ] Metrics collection (time, artifacts, commits)
- [ ] Structured logging throughout execution
- [ ] WorkflowResult returned with comprehensive details
- [ ] Unit tests written and passing (>80% coverage)
- [ ] Integration test with simple workflow
- [ ] Type hints complete (mypy passes)
- [ ] Docstrings for all public methods
- [ ] Code review completed
- [ ] Story committed atomically to git

---

## Story Enhancement Notes

**Original Story Points**: 5 points
**Updated Story Points**: 7 points (+2 points)

**Reason for Increase**:
- Added multi-workflow sequence execution (not just single workflow)
- Added phase transition handling (Phase 1 → 2 → 3 → 4)
- Added Just-In-Time tech-spec generation during implementation
- Added state persistence across workflows
- Increased complexity to support scale-adaptive routing

---

## Out of Scope

- Clarification dialog (Story 7.2.4)
- Benchmark integration (Story 7.2.3)
- Real-time progress streaming to UI
- Workflow resume from checkpoint (future enhancement)
- Parallel step execution (future enhancement)

---

## Notes

- This is the core autonomy feature - GAO-Dev decides and executes independently
- Multi-workflow sequencing is critical for scale-adaptive approach
- Focus on sequential execution first, parallel can come later
- Fail-fast is important - stop on first error
- Logging is critical for debugging workflow issues
- Phase transitions must persist state for next phase
