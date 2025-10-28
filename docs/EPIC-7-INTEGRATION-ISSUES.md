# Epic 7 Integration Issues - Discovery Report

**Date**: 2025-10-28
**Status**: Epic 7 components built, integration incomplete
**Severity**: High - Blocks benchmark testing

## Executive Summary

Attempted to run first autonomous benchmark test with QA-as-you-go workflow. Discovered that while Epic 7 components (ArtifactParser, GitCommitManager, ArtifactVerifier) were successfully implemented, the **integration with the benchmark runner was not fully tested end-to-end**.

Result: **Cannot run benchmarks yet** - multiple integration bugs discovered.

---

## Bugs Found & Fixed (Session 2025-10-28)

### ✅ Bug 1: GitCloner Method Name Mismatch
**File**: `gao_dev/sandbox/benchmark/runner.py:275`
**Issue**: Calling non-existent `clone()` method instead of `clone_repository()`
**Fix**: Updated to use correct method name `clone_repository(repo_url, destination)`
**Commit**: feea3e6

### ✅ Bug 2: ProjectMetadata Missing Attribute
**File**: `gao_dev/sandbox/benchmark/runner.py:276-277`
**Issue**: Trying to access `project.project_path` but ProjectMetadata doesn't have that attribute
**Fix**: Use `sandbox_manager.get_project_path(project.name)` instead
**Commit**: 30d72dd

### ✅ Bug 3: Variable Scope Issue
**File**: `gao_dev/sandbox/benchmark/runner.py:362`
**Issue**: `total_stories` variable used before definition
**Fix**: Moved variable definition before first use, removed duplicate
**Commit**: fc0037b

---

## Bugs Remaining (Not Fixed Yet)

### ❌ Bug 4: ConfigLoader Type Mismatch (Phase-Based Workflow)
**File**: Unknown location in workflow orchestrator
**Error**: `argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'ConfigLoader'`
**Impact**: Phase-based benchmarks (greenfield-simple.yaml) fail immediately
**Severity**: High - blocks all phase-based testing

**Details**:
- Occurs in phase-based workflow execution
- Something is passing a ConfigLoader object where a Path is expected
- Need to trace through WorkflowOrchestrator to find exact location

### ❌ Bug 5: StoryOrchestrator Still Uses AgentSpawner (Story-Based Workflow)
**File**: `gao_dev/sandbox/benchmark/story_orchestrator.py:156-157`
**Error**: `No module named 'gao_dev.sandbox.benchmark.agent_spawner'`
**Impact**: Story-based benchmarks (todo-app-incremental.yaml) fail immediately
**Severity**: High - blocks all story-based testing with QA-as-you-go

**Details**:
- StoryOrchestrator still imports and uses AgentSpawner
- AgentSpawner was removed in Epic 7 (Story 7.1)
- Should use GAODevOrchestrator instead
- Affects all story lifecycle methods:
  - `_execute_story_creation()` - line 390
  - `_execute_story_implementation()` - line 429
  - `_execute_story_validation()` - line 468 (QA validation!)

**Root Cause**: Epic 7 Story 7.1 removed AgentSpawner from phase-based workflow but didn't update StoryOrchestrator (story-based workflow).

---

## What Works vs. What Doesn't

### ✅ Components Built (Epic 7.1-7.7)
- ArtifactParser - Parses agent output for artifacts
- GitCommitManager - Creates atomic git commits
- ArtifactVerifier - Validates artifacts were created
- WorkflowOrchestrator - Phase-based execution (with bug 4)
- Benchmark config system - Reads YAML configs
- Metrics collection - Tracks all metrics
- Project initialization - Creates sandbox projects with git

### ❌ Not Working (Integration Issues)
- Phase-based benchmarks - ConfigLoader type error (bug 4)
- Story-based benchmarks - AgentSpawner missing (bug 5)
- **No end-to-end test path currently working**

---

## Impact Assessment

**Critical**: Cannot run ANY benchmarks until bugs 4 & 5 are fixed.

### User Story Blocked
Original goal: "Run greenfield todo-app benchmark with QA-as-you-go validation per story"

**Current Reality**:
- ❌ Can't use story-based (todo-app-incremental.yaml) - needs bug 5 fix
- ❌ Can't use phase-based (greenfield-simple.yaml) - needs bug 4 fix
- ❌ No workaround available

### What We Learned
1. Epic 7 components are well-implemented individually
2. Integration testing was missing - components never tested together
3. Unit tests passed but end-to-end flow was never validated
4. Need comprehensive integration test suite

---

## Recommended Next Steps

### Option A: Quick Fix (2-3 hours estimated)
**Goal**: Get ONE workflow type working for testing

**Plan**:
1. Fix bug 4 (ConfigLoader type issue) - debug phase-based workflow
2. Run greenfield-simple.yaml successfully
3. Skip story-based (QA-as-you-go) for now
4. Document that story-based needs separate fix

**Pros**: Gets basic benchmarking working quickly
**Cons**: No QA-as-you-go validation (original goal not met)

### Option B: Complete Integration (4-6 hours estimated)
**Goal**: Fix both workflows, get full QA-as-you-go working

**Plan**:
1. Fix bug 4 (ConfigLoader) - debug and fix
2. Fix bug 5 (StoryOrchestrator AgentSpawner) - refactor to use GAODevOrchestrator
3. Test phase-based workflow end-to-end
4. Test story-based workflow end-to-end with QA validation
5. Create integration test suite
6. Document both workflows working

**Pros**: Complete solution, QA-as-you-go working as intended
**Cons**: Takes longer, requires more complex refactoring

### Option C: Create Epic 7.1 (Recommended)
**Goal**: Proper planning and implementation of integration fixes

**Plan**:
1. Create **Epic 7.1: "Integration & End-to-End Testing"**
2. Break down into stories:
   - Story 7.1.1: Fix ConfigLoader type issue (phase-based)
   - Story 7.1.2: Refactor StoryOrchestrator to use GAODevOrchestrator
   - Story 7.1.3: Create integration test suite
   - Story 7.1.4: Document both workflows
   - Story 7.1.5: Run comprehensive end-to-end tests
3. Follow proper BMAD agile process for each story
4. Ensure atomic commits per story
5. Full testing before marking complete

**Pros**: Proper agile process, well-documented, atomic commits, fully tested
**Cons**: Takes most time upfront, but prevents future issues

---

## Technical Details

### Bug 4 Debug Starting Point
```python
# gao_dev/sandbox/benchmark/runner.py
# Line ~293 in _execute_workflow()
# Likely passing wrong type to WorkflowOrchestrator initialization
```

### Bug 5 Fix Approach
```python
# gao_dev/sandbox/benchmark/story_orchestrator.py

# Current (broken):
if api_key:
    from .agent_spawner import AgentSpawner
    self.agent_spawner = AgentSpawner(api_key=api_key)

# Should be:
if api_key:
    from ...orchestrator import GAODevOrchestrator
    self.gao_orchestrator = GAODevOrchestrator(project_root=self.project_path)

# Then update all spawn_agent() calls to use GAODevOrchestrator methods:
# - Bob: gao_orchestrator.create_story()
# - Amelia: gao_orchestrator.implement_story()
# - Murat: (need to add QA method to orchestrator)
```

---

## Lessons Learned

1. **Integration testing is critical** - Unit tests aren't enough
2. **End-to-end workflows must be tested** before marking epic complete
3. **Document known limitations** when marking work done
4. **Follow agile process even for bug fixes** - creates better quality
5. **One working path is better than two broken paths** - prioritize

---

## Files Modified in This Session

1. `gao_dev/sandbox/benchmark/runner.py` - 3 bug fixes
2. `sandbox/benchmarks/simple-story-test.yaml` - New test benchmark created
3. `docs/bmm-workflow-status.md` - Updated Epic 7 status
4. `docs/EPIC-7-INTEGRATION-ISSUES.md` - This file

---

## Conclusion

**Epic 7 is 85% complete** - Components built but integration incomplete.

**Recommendation**: Create Epic 7.1 for proper integration work using BMAD process.

**Next Session Goal**: Either quick fix (Option A) or comprehensive fix (Option B/C) depending on time and priority.
