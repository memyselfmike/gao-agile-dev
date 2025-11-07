# Story 18.1: WorkflowExecutor Integration

**Epic:** 18 - Workflow Variable Resolution and Artifact Tracking
**Story Points:** 8
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Integrate WorkflowExecutor into the orchestrator execution path to enable proper variable resolution from workflow.yaml definitions. Currently, the orchestrator bypasses WorkflowExecutor and loads instructions.md raw, sending unresolved variables like `{{prd_location}}` directly to the LLM. This story fixes this critical architectural flaw by ensuring all workflow variables are resolved from workflow.yaml defaults, config, and parameters before rendering instructions and sending them to the LLM.

---

## Business Value

This story fixes a fundamental bug in workflow execution:

- **Correct File Locations**: Files created at locations defined in workflow.yaml (e.g., docs/PRD.md)
- **Convention Enforcement**: Project conventions enforced by design, not LLM guessing
- **Variable Flexibility**: Workflow authors can define and override variables easily
- **Configuration Override**: Users can override defaults via config without editing workflows
- **Maintainability**: Variables defined once in workflow.yaml, not duplicated in prompts
- **Observability**: Variable resolution logged for debugging and troubleshooting
- **LLM Clarity**: LLM receives clear, resolved instructions without ambiguous placeholders
- **Foundation for Artifacts**: Prerequisites for artifact detection (Story 18.2)
- **Production Quality**: Workflow execution works as originally designed
- **Developer Experience**: Clear separation between workflow definition and execution

---

## Acceptance Criteria

### Variable Resolution
- [ ] Orchestrator has `WorkflowExecutor` instance initialized
- [ ] `_execute_agent_task_static()` calls `workflow_executor.resolve_variables()` before execution
- [ ] Parameters dict includes epic, story, project_name, project_root
- [ ] All workflow variables resolved from workflow.yaml defaults
- [ ] Config values override workflow.yaml defaults
- [ ] Parameter values override config and workflow defaults
- [ ] Required variables raise ValueError if missing
- [ ] Common variables (date, timestamp) added automatically

### Template Rendering
- [ ] Instructions template rendered with resolved variables using Mustache syntax
- [ ] All `{{variable}}` placeholders replaced with actual values
- [ ] LLM receives fully resolved instructions (no {{variables}} remain)
- [ ] Nested variable references work (up to 2 levels)
- [ ] Template rendering preserves markdown formatting

### Logging & Observability
- [ ] Logs show `workflow_variables_resolved` with variable list
- [ ] Logs show `workflow_instructions_rendered` with prompt length
- [ ] Logs include variables_used list for debugging
- [ ] Error logs show which variables failed to resolve

### Testing
- [ ] Unit tests verify variable resolution from workflow.yaml defaults
- [ ] Unit tests verify parameter override of defaults
- [ ] Unit tests verify config override priority
- [ ] Integration test: PRD workflow creates file at correct location (docs/PRD.md)
- [ ] Integration test: Story workflow uses resolved dev_story_location
- [ ] No regression in existing orchestrator tests

---

## Technical Notes

### Implementation Approach

**File:** `gao_dev/orchestrator/orchestrator.py`

**Step 1:** Add WorkflowExecutor to orchestrator:

```python
from ..core.workflow_executor import WorkflowExecutor

class GAODevOrchestrator:
    def __init__(self, ...):
        # ... existing code ...
        self.workflow_executor = WorkflowExecutor(self.config_loader)
```

**Step 2:** Refactor `_execute_agent_task_static()` method (lines 940-1012):

```python
async def _execute_agent_task_static(
    self, workflow_info: "WorkflowInfo", epic: int = 1, story: int = 1
) -> AsyncGenerator[str, None]:
    """
    Execute agent task via ProcessExecutor with proper variable resolution.

    NEW BEHAVIOR:
    - Uses WorkflowExecutor to resolve workflow variables
    - Renders instructions template with resolved variables
    """
    logger.debug("executing_agent_task", workflow=workflow_info.name, epic=epic, story=story)

    # STEP 1: Build parameters for variable resolution
    params = {
        "epic_num": epic,
        "story_num": story,
        "epic": epic,
        "story": story,
        "project_name": self.project_root.name,
        "project_root": str(self.project_root),
    }

    # STEP 2: Use WorkflowExecutor to resolve variables
    variables = self.workflow_executor.resolve_variables(workflow_info, params)

    logger.info(
        "workflow_variables_resolved",
        workflow=workflow_info.name,
        variables=variables,
        variables_used=list(variables.keys())
    )

    # STEP 3: Load instructions from instructions.md
    installed_path = (
        Path(workflow_info.installed_path)
        if isinstance(workflow_info.installed_path, str)
        else workflow_info.installed_path
    )
    instructions_file = installed_path / "instructions.md"
    if instructions_file.exists():
        task_prompt = instructions_file.read_text(encoding="utf-8")
    else:
        task_prompt = workflow_info.description
        logger.warning(
            "workflow_missing_instructions",
            workflow=workflow_info.name,
            path=str(instructions_file),
        )

    # STEP 4: Render instructions with resolved variables
    task_prompt = self.workflow_executor.render_template(task_prompt, variables)

    logger.info(
        "workflow_instructions_rendered",
        workflow=workflow_info.name,
        prompt_length=len(task_prompt),
        variables_used=list(variables.keys())
    )

    # STEP 5: Execute via ProcessExecutor (existing code continues...)
    async for output in self.process_executor.execute_agent_task(
        task=task_prompt,
        tools=["Read", "Write", "Edit", "MultiEdit", "Bash", "Grep", "Glob", "TodoWrite"],
        timeout=None
    ):
        yield output
```

**Step 3:** Update WorkflowExecutor to expose public methods:

**File:** `gao_dev/core/workflow_executor.py`

```python
def resolve_variables(self, workflow: WorkflowInfo, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve workflow variables from params, config, and defaults.

    PUBLIC API for orchestrator to resolve variables before execution.
    """
    return self._resolve_variables(workflow, params)

def render_template(self, template: str, variables: Dict[str, Any]) -> str:
    """
    Render template with variables using Mustache-style syntax.

    PUBLIC API for orchestrator to render instructions with resolved variables.
    """
    return self._render_template(template, variables)
```

**Step 4:** Update WorkflowCoordinator (optional parameter):

**File:** `gao_dev/core/services/workflow_coordinator.py`

```python
def __init__(
    self,
    workflow_registry: IWorkflowRegistry,
    agent_factory: IAgentFactory,
    event_bus: IEventBus,
    agent_executor: Callable,
    project_root: Path,
    doc_manager: Optional['DocumentLifecycleManager'] = None,
    workflow_executor: Optional['WorkflowExecutor'] = None,  # NEW
    max_retries: int = 3
):
    # ... existing code ...
    self.workflow_executor = workflow_executor  # NEW
```

---

## Dependencies

- Epic 10 (Prompt Abstraction) - WorkflowExecutor and variable system exist
- WorkflowInfo model with variables dict
- ConfigLoader with workflow defaults support

---

## Tasks

### Implementation Tasks
- [ ] Add WorkflowExecutor instance to GAODevOrchestrator.__init__()
- [ ] Add WorkflowExecutor initialization in _initialize_default_services()
- [ ] Refactor _execute_agent_task_static() to use WorkflowExecutor
- [ ] Build parameters dict (epic, story, project_name, project_root)
- [ ] Call workflow_executor.resolve_variables() with workflow and params
- [ ] Call workflow_executor.render_template() on instructions
- [ ] Add comprehensive logging for variable resolution
- [ ] Make _resolve_variables() public as resolve_variables()
- [ ] Make _render_template() public as render_template()
- [ ] Update WorkflowCoordinator to accept optional workflow_executor param
- [ ] Update orchestrator factory methods to pass WorkflowExecutor instance

### Testing Tasks
- [ ] Write unit test: test_resolve_variables_from_workflow_defaults()
- [ ] Write unit test: test_resolve_variables_param_override()
- [ ] Write unit test: test_resolve_variables_config_override()
- [ ] Write unit test: test_resolve_variables_priority()
- [ ] Write unit test: test_render_template_with_variables()
- [ ] Write unit test: test_render_template_preserves_formatting()
- [ ] Write integration test: test_prd_workflow_correct_location()
- [ ] Write integration test: test_story_workflow_uses_dev_story_location()
- [ ] Run regression tests on existing orchestrator tests
- [ ] Validate no breaking changes

### Documentation Tasks
- [ ] Update method docstrings with new behavior
- [ ] Add code comments explaining variable resolution flow
- [ ] Document new log events (workflow_variables_resolved, etc.)

---

## Definition of Done

- [ ] All acceptance criteria met and verified
- [ ] All tasks completed
- [ ] Unit tests pass (>80% coverage)
- [ ] Integration tests pass
- [ ] Regression tests pass (no breaking changes)
- [ ] Code review approved
- [ ] Logging implemented and verified
- [ ] Documentation updated
- [ ] Manual testing with PRD and story workflows successful
- [ ] Merged to feature branch

---

## Files to Modify

1. `gao_dev/orchestrator/orchestrator.py` (~150 LOC changes)
   - Add WorkflowExecutor instance
   - Refactor _execute_agent_task_static()
   - Add in __init__ and _initialize_default_services()

2. `gao_dev/core/workflow_executor.py` (~20 LOC additions)
   - Add public resolve_variables() method
   - Add public render_template() method

3. `gao_dev/core/services/workflow_coordinator.py` (~10 LOC)
   - Add optional workflow_executor parameter to __init__()

4. `tests/orchestrator/test_workflow_executor_integration.py` (new file, ~200 LOC)
   - Unit tests for variable resolution
   - Unit tests for template rendering
   - Integration tests for end-to-end workflow execution

---

## Success Metrics

- **Correctness**: 100% of workflow variables resolved before LLM execution
- **File Locations**: 100% of files created at correct locations defined in workflow.yaml
- **Test Coverage**: >80% coverage for new code
- **Regression**: 0 breaking changes to existing tests
- **Performance**: Variable resolution overhead <10ms (p95)
- **Observability**: All variable resolutions logged with context

---

## Risk Assessment

**Risks:**
- Breaking changes to existing workflows that relied on LLM guessing
- Performance overhead from variable resolution
- Edge cases in template rendering

**Mitigations:**
- Comprehensive regression testing
- Performance benchmarking before/after
- Extensive unit tests for edge cases
- Clear migration guide for affected workflows

---

## Notes

- This is the foundation story for Epic 18 - all other stories depend on this
- Variable resolution must be fast (<10ms) to avoid impacting workflow performance
- Template rendering must preserve markdown formatting exactly
- Error messages must be clear when variables are missing or invalid
- Consider adding dry-run mode to show resolved variables without execution

---

**Created:** 2025-11-07
**Last Updated:** 2025-11-07
**Author:** Bob (Scrum Master)
