# Story 7.1.1: Fix Phase-Based Workflow (ConfigLoader Bug)

**Epic**: 7.1 - Integration & Architecture Fix
**Story Points**: 2
**Priority**: P0 - Critical
**Status**: Ready
**Owner**: Amelia (Developer)

## User Story

As a GAO-Dev user
I want phase-based benchmarks to run successfully
So that I can test basic autonomous project generation

## Context

First benchmark test run failed with error: `argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'ConfigLoader'`

The WorkflowOrchestrator is receiving a ConfigLoader object instead of a Path somewhere in the phase execution path.

## Problem

Phase-based benchmarks (greenfield-simple.yaml) fail immediately during workflow execution. Something in the orchestration chain is passing wrong type to a method expecting Path.

## Goal

Fix the ConfigLoader type mismatch and get greenfield-simple.yaml running successfully through all 4 phases.

## Acceptance Criteria

- [ ] greenfield-simple.yaml runs without ConfigLoader error
- [ ] All 4 phases execute: Product Requirements, System Architecture, Story Creation, Implementation
- [ ] Artifacts created in sandbox/projects/greenfield-simple-run-XXX/
- [ ] Git commits created per phase (4 total commits)
- [ ] Benchmark completes with status: success
- [ ] Metrics collected for all phases

## Technical Details

**Files to Check**:
- `gao_dev/sandbox/benchmark/runner.py` - Line ~293+ in `_execute_workflow()`
- `gao_dev/sandbox/benchmark/orchestrator.py` - WorkflowOrchestrator initialization
- `gao_dev/sandbox/benchmark/config.py` - Config loading

**Likely Issue**:
```python
# Somewhere we're doing:
orchestrator = WorkflowOrchestrator(
    project_path=config,  # ❌ Passing ConfigLoader object
    ...
)

# Should be:
project_path = sandbox_manager.get_project_path(project.name)
orchestrator = WorkflowOrchestrator(
    project_path=project_path,  # ✅ Passing Path
    ...
)
```

**Debug Approach**:
1. Run greenfield-simple.yaml with verbose logging
2. Find exact line where ConfigLoader is passed as Path
3. Fix to pass actual Path object
4. Test end-to-end
5. Verify all 4 phases complete

## Testing

**Test Command**:
```bash
python -m gao_dev.cli.commands sandbox run \
  sandbox/benchmarks/greenfield-simple.yaml \
  --timeout 7200
```

**Expected Output**:
```
>> Phase 1/4: Product Requirements (John)
   - Creating PRD...
   - Artifact: docs/PRD.md ✓
   - Git commit: feat(prd): create product requirements

>> Phase 2/4: System Architecture (Winston)
   - Creating architecture...
   - Artifact: docs/ARCHITECTURE.md ✓
   - Git commit: feat(architecture): design system architecture

>> Phase 3/4: Story Creation (Bob)
   - Creating stories...
   - Artifacts: docs/stories/* ✓
   - Git commit: feat(stories): create user stories

>> Phase 4/4: Implementation (Amelia)
   - Implementing features...
   - Artifacts: src/*, tests/* ✓
   - Git commit: feat(implementation): implement features

>> Benchmark Status: SUCCESS ✓
```

## Dependencies

None - This is the first story to unblock testing

## Risks

- May discover additional type errors in related code
- Phase execution might reveal other integration issues

## Definition of Done

- [ ] Bug fix code written and tested
- [ ] greenfield-simple.yaml completes successfully
- [ ] All phases execute without errors
- [ ] Artifacts and commits verified
- [ ] Code committed atomically
- [ ] Story status updated to Done

## Notes

This is the critical first fix to get ANY benchmark working. Once this works, we can test the rest of the system.
