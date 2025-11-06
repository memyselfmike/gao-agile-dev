# E2E Testing Plan - Epic 5: Methodology Abstraction

## Overview

This document outlines the end-to-end testing strategy for validating the Epic 5 methodology abstraction refactoring.

**Epic**: Epic 5 - Methodology Abstraction
**Stories**: 5.1 (Interface), 5.2 (AdaptiveAgile), 5.3 (Registry), 5.4 (Decoupling), 5.5 (Simple)
**Status**: Ready for E2E Testing
**Date**: 2025-10-30

## Test Objectives

1. Verify methodology abstraction works end-to-end
2. Validate both AdaptiveAgile and SimpleMethodology implementations
3. Ensure MethodologyRegistry correctly manages multiple methodologies
4. Confirm orchestrator integration with new architecture
5. Validate backward compatibility with legacy code

## Test Environment

**Prerequisites:**
- All Epic 5 stories completed and merged to main
- 464/484 unit tests passing (96%)
- Test isolation issues documented (non-blocking)

**Setup:**
```bash
cd "D:\GAO Agile Dev"
python -m pytest tests/integration/ --no-cov -v
```

## E2E Test Scenarios

### Scenario 1: MethodologyRegistry Lifecycle

**Objective**: Verify registry can manage multiple methodologies

**Steps:**
1. Get MethodologyRegistry instance
2. Verify AdaptiveAgile auto-registered
3. Register SimpleMethodology
4. List all methodologies (should show both)
5. Switch default to SimpleMethodology
6. Verify default changed
7. Switch back to AdaptiveAgile

**Expected:**
- ✅ Registry is singleton
- ✅ AdaptiveAgile auto-registered on init
- ✅ SimpleMethodology registers successfully
- ✅ Can list both methodologies
- ✅ Can switch default
- ✅ Thread-safe operations

**Test File**: `tests/methodologies/test_registry.py` (existing)

**Status**: ⬜ Not Run | ✅ Passed | ❌ Failed

---

### Scenario 2: AdaptiveAgile Full Workflow

**Objective**: End-to-end workflow with AdaptiveAgileMethodology

**Steps:**
1. Create orchestrator with AdaptiveAgile (default)
2. Submit prompt: "Fix login bug" (Level 0)
3. Verify complexity assessment
4. Verify workflow sequence built
5. Check scale level mapping
6. Validate recommended agents

**Prompts to Test:**
- "Fix login bug" → Level 0 (TRIVIAL)
- "Add user profile page" → Level 1 (SMALL)
- "Build todo app with auth" → Level 2 (MEDIUM)
- "Create CRM system" → Level 3 (LARGE)
- "Build enterprise ERP" → Level 4 (XLARGE)

**Expected:**
- ✅ Correct scale level for each prompt
- ✅ Appropriate workflow sequence generated
- ✅ Phase breakdown makes sense
- ✅ JIT tech specs for Level 3+
- ✅ Agent recommendations correct

**Test File**: `tests/methodologies/adaptive_agile/test_adaptive_agile_methodology.py` (existing)

**Status**: ⬜ Not Run | ✅ Passed | ❌ Failed

---

### Scenario 3: SimpleMethodology Full Workflow

**Objective**: End-to-end workflow with SimpleMethodology

**Steps:**
1. Register SimpleMethodology with registry
2. Set as default
3. Submit prompt: "Quick bug fix" (TRIVIAL)
4. Verify assessment
5. Check workflow sequence (should be single "implement" step)
6. Submit prompt: "Add authentication" (MEDIUM)
7. Verify 3-step workflow (plan, implement, test)
8. Submit prompt: "Build complete system" (XLARGE)
9. Verify 4-step workflow (design, plan, implement, test)

**Expected:**
- ✅ TRIVIAL → 1 workflow step
- ✅ MEDIUM → 3 workflow steps
- ✅ XLARGE → 4 workflow steps
- ✅ Correct agent recommendations per phase
- ✅ Project type detection works

**Test File**: `tests/methodologies/simple/test_simple_methodology.py` (existing)

**Status**: ⬜ Not Run | ✅ Passed | ❌ Failed

---

### Scenario 4: Orchestrator Integration

**Objective**: Verify orchestrator correctly uses methodologies

**Steps:**
1. Initialize GAODevOrchestrator with default methodology
2. Submit various prompts
3. Verify orchestrator calls methodology.assess_complexity()
4. Verify orchestrator calls methodology.build_workflow_sequence()
5. Verify workflow execution uses correct agents
6. Check WorkflowContext has correct complexity_level
7. Verify metadata includes scale_level (backward compat)

**Expected:**
- ✅ Orchestrator initializes with default methodology
- ✅ Complexity assessment triggered correctly
- ✅ Workflow sequence built properly
- ✅ WorkflowContext has complexity_level
- ✅ Backward compatibility maintained (metadata.scale_level)
- ✅ Workflow strategies use correct scale level

**Test File**: `tests/integration/test_workflow_driven_core.py` (existing)

**Status**: ⬜ Not Run | ✅ Passed | ❌ Failed

---

### Scenario 5: Backward Compatibility

**Objective**: Ensure legacy code still works after refactoring

**Steps:**
1. Import from gao_dev.core.legacy_models (WorkflowInfo, etc.)
2. Use old scale_level property on WorkflowContext
3. Verify orchestrator.models exports work
4. Check brian_orchestrator still functional
5. Validate workflow_strategies with int scale levels

**Expected:**
- ✅ legacy_models imports work
- ✅ WorkflowContext.scale_level property works
- ✅ Metadata-based backward compat functional
- ✅ brian_orchestrator uses orchestrator.models correctly
- ✅ workflow_strategies handles int scale levels

**Test Files**:
- `tests/core/models/test_workflow_context.py`
- `tests/core/strategies/test_workflow_strategies.py`
- `tests/orchestrator/test_brian_orchestrator.py`

**Status**: ⬜ Not Run | ✅ Passed | ❌ Failed

---

### Scenario 6: Project Type Routing

**Objective**: Verify project type detection and routing

**Steps:**
1. Test greenfield project routing
2. Test brownfield project routing (should include document-project)
3. Test game project routing (should use game-specific workflows)
4. Verify web app detection
5. Verify API detection
6. Verify CLI detection

**Prompts:**
- "Build new todo app" → Greenfield + Web App
- "Add auth to existing app" → Brownfield
- "Create 2D platformer game" → Game
- "Build REST API" → API
- "Create CLI tool" → CLI

**Expected:**
- ✅ Correct project type detected
- ✅ Brownfield includes document-project first
- ✅ Game projects use game workflows
- ✅ Technical type detection accurate

**Test Files**:
- `tests/orchestrator/test_brian_orchestrator.py` (TestProjectTypeRouting)
- `tests/methodologies/simple/test_simple_methodology.py` (project type tests)

**Status**: ⬜ Not Run | ✅ Passed | ❌ Failed

---

### Scenario 7: Clarification Questions

**Objective**: Verify orchestrator handles ambiguous prompts

**Steps:**
1. Submit ambiguous prompt: "Fix it"
2. Verify needs_clarification flag set
3. Check clarifying_questions populated
4. Verify empty workflow sequence returned
5. Test with clearer prompt
6. Verify workflow sequence generated

**Expected:**
- ✅ Ambiguous prompts trigger clarification
- ✅ Questions are meaningful
- ✅ Workflow sequence empty when clarification needed
- ✅ Clear prompts generate workflows

**Test File**: `tests/orchestrator/test_brian_orchestrator.py` (TestClarificationQuestions)

**Status**: ⬜ Not Run | ✅ Passed | ❌ Failed

---

## Test Execution Plan

### Phase 1: Unit Test Validation (Current)
```bash
# Run all methodology tests
pytest tests/methodologies/ --no-cov -v

# Run orchestrator tests
pytest tests/orchestrator/ --no-cov -v

# Run integration tests
pytest tests/integration/ --no-cov -v
```

**Expected**: 464+ tests passing

### Phase 2: Integration Test Run
```bash
# Run full integration suite
pytest tests/integration/test_workflow_driven_core.py --no-cov -v

# Run methodology integration tests
pytest tests/methodologies/adaptive_agile/test_adaptive_agile_methodology.py --no-cov -v
pytest tests/methodologies/simple/test_simple_methodology.py --no-cov -v
```

**Expected**: All integration scenarios pass

### Phase 3: Manual E2E Validation
```bash
# Test CLI with real prompts
gao-dev init --name "test-e2e-project"
cd test-e2e-project

# Test with AdaptiveAgile (default)
# Manually verify workflow selection for various prompts

# Switch to SimpleMethodology
# Verify different workflow paths
```

**Expected**: Real-world usage validates design

### Phase 4: Regression Testing
```bash
# Run full test suite
pytest tests/ --no-cov -x

# Check for test isolation issues
pytest tests/ --no-cov --count=3
```

**Expected**: Identify and document remaining issues

## Known Issues

### Test Isolation (Non-Blocking)
- **Issue**: 15 tests fail in full suite but pass individually
- **Root Cause**: MethodologyRegistry singleton state, event loop cleanup
- **Impact**: Does not affect production code
- **Resolution**: Separate task to add proper teardown

### Resource Warnings (Non-Blocking)
- **Issue**: Unclosed socket warnings in async tests
- **Root Cause**: Event loop not properly closed
- **Impact**: Test warnings only
- **Resolution**: Add proper async teardown

## Success Criteria

✅ **Must Pass:**
1. All 7 E2E scenarios pass
2. 95%+ unit tests passing
3. No regressions in existing functionality
4. Backward compatibility validated

⚠️ **Nice to Have:**
1. Test isolation issues resolved
2. Resource warnings eliminated
3. 100% test pass rate

🚫 **Known Not Blocking:**
1. Test ordering issues (singleton state)
2. Async event loop warnings
3. Coverage under 80% for individual test runs

## Post-E2E Actions

### If Tests Pass:
1. ✅ Mark Epic 5 as complete
2. ✅ Update sprint status
3. ✅ Create Epic 5 completion summary
4. ✅ Plan next epic (Epic 6?)

### If Tests Fail:
1. ❌ Document failures
2. ❌ Create bug tickets
3. ❌ Fix critical issues
4. ❌ Re-run E2E tests

## Test Execution Log

**Date**: 2025-10-30
**Tester**: Claude/User
**Branch**: main
**Commit**: 7e8fa1c

| Scenario | Status | Notes |
|----------|--------|-------|
| 1. Registry Lifecycle | ⬜ | Not yet run |
| 2. AdaptiveAgile Workflow | ⬜ | Not yet run |
| 3. SimpleMethodology Workflow | ⬜ | Not yet run |
| 4. Orchestrator Integration | ⬜ | Not yet run |
| 5. Backward Compatibility | ⬜ | Not yet run |
| 6. Project Type Routing | ⬜ | Not yet run |
| 7. Clarification Questions | ⬜ | Not yet run |

## References

- **Epic 5 Stories**: `docs/features/core-gao-dev-system-refactor/stories/epic-5/`
- **Test Files**: `tests/methodologies/`, `tests/orchestrator/`, `tests/integration/`
- **Architecture**: `docs/features/core-gao-dev-system-refactor/ARCHITECTURE.md`
- **PRD**: `docs/features/core-gao-dev-system-refactor/PRD.md`
