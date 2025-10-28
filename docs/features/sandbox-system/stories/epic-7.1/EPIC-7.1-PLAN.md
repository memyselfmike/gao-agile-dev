# Epic 7.1: Integration & Architecture Fix

**Status**: Ready to Start
**Priority**: P0 - Critical (Blocks all benchmark testing)
**Estimated**: 13 story points
**Owner**: Amelia (Developer)

## Problem Statement

Epic 7 components (ArtifactParser, GitCommitManager, ArtifactVerifier) were built but never tested end-to-end. First attempt to run benchmarks revealed:

1. **Integration bugs**: 3 fixed, 2 critical bugs remaining
2. **Architecture issue**: Story-based workflow buried in sandbox, should be core
3. **No working test path**: Neither phase-based nor story-based benchmarks functional

Result: **Cannot run any benchmarks** - system is 85% complete but not integrated.

## Goals

1. **Fix remaining integration bugs** (ConfigLoader, AgentSpawner removal)
2. **Refactor architecture** - Move story workflow to core orchestrator
3. **Get ONE benchmark working end-to-end** (prove the system)
4. **Enable QA-as-you-go workflow** (original requirement)
5. **Create integration tests** (prevent regression)

## Success Criteria

- [ ] Phase-based benchmark runs successfully (greenfield-simple.yaml)
- [ ] Story-based benchmark runs successfully (simple-story-test.yaml)
- [ ] QA validation happens per story (Murat validates after Amelia)
- [ ] Artifacts created and committed atomically
- [ ] Integration test suite catches future breaks
- [ ] Both workflows documented and proven

## Architecture Change

**Before** (Current - Broken):
```
gao_dev/orchestrator/orchestrator.py     ← GAODevOrchestrator (CLI tasks)
gao_dev/sandbox/benchmark/story_orchestrator.py  ← StoryOrchestrator (story workflow)
                                                    Uses removed AgentSpawner
```

**After** (Fixed):
```
gao_dev/orchestrator/orchestrator.py     ← GAODevOrchestrator
   - Individual tasks (create_prd, implement_story)
   - execute_story_workflow() ← NEW (Bob → Amelia → Murat → Commit)
   - execute_epic_workflow() ← NEW (loop through stories)

gao_dev/sandbox/benchmark/story_orchestrator.py  ← REMOVED or thin wrapper
```

**Benefits**:
- Story-by-story workflow available in core (CLI can use it)
- No AgentSpawner dependency
- Single source of truth for orchestration
- QA-as-you-go becomes standard, not special case

## Stories Breakdown

### Story 7.1.1: Fix Phase-Based Workflow (ConfigLoader Bug)
**Points**: 2
**Goal**: Get greenfield-simple.yaml working

- Fix ConfigLoader type mismatch in WorkflowOrchestrator
- Debug phase execution path
- Test with greenfield-simple.yaml
- Verify artifact creation and git commits

**Acceptance Criteria**:
- greenfield-simple.yaml runs without errors
- All 4 phases execute (PRD, Architecture, Stories, Implementation)
- Artifacts created in correct locations
- Git commits made per phase

---

### Story 7.1.2: Move Story Workflow to Core Orchestrator
**Points**: 5
**Goal**: Refactor architecture - make story workflow core feature

- Add `execute_story_workflow()` to GAODevOrchestrator
  - Bob → Create story spec
  - Amelia → Implement + tests
  - Murat → QA validation
  - Git → Atomic commit
- Add `execute_epic_workflow()` to GAODevOrchestrator
- Update StoryOrchestrator to use core methods (or remove)
- Update benchmarks to use new core workflow

**Acceptance Criteria**:
- GAODevOrchestrator has story workflow methods
- Story workflow doesn't use AgentSpawner
- Can execute single story: Bob → Amelia → Murat → Commit
- Can execute full epic (all stories)
- Existing CLI commands still work

---

### Story 7.1.3: Test Story-Based Workflow End-to-End
**Points**: 3
**Goal**: Prove story-based benchmarks work with QA-as-you-go

- Run simple-story-test.yaml successfully
- Verify per-story QA validation (Murat runs after each story)
- Verify atomic commits per story
- Verify story results tracked
- Document any remaining issues

**Acceptance Criteria**:
- simple-story-test.yaml completes successfully
- 2 stories executed: Hello World + Greeting function
- Murat validates each story before commit
- 2 atomic git commits created
- Story metrics collected

---

### Story 7.1.4: Create Integration Test Suite
**Points**: 2
**Goal**: Prevent future integration breaks

- Create test_integration.py for end-to-end testing
- Test phase-based workflow
- Test story-based workflow
- Test artifact creation
- Test git commit creation
- Add to CI (if exists)

**Acceptance Criteria**:
- Integration tests pass
- Cover both workflows (phase-based, story-based)
- Can detect ConfigLoader-type bugs
- Can detect missing orchestrator methods
- Run in under 5 minutes

---

### Story 7.1.5: Update Documentation
**Points**: 1
**Goal**: Document working system and workflows

- Update EPIC-7-INTEGRATION-ISSUES.md (mark bugs as fixed)
- Document story workflow in core orchestrator
- Update benchmark runner docs
- Create troubleshooting guide
- Update sprint-status.yaml

**Acceptance Criteria**:
- All bugs marked as fixed in documentation
- Story workflow documented with examples
- Both benchmark types have working examples
- Troubleshooting guide for common issues

---

## Timeline

**Estimated Time**: 1-2 focused sessions

**Session 1** (Current):
- Story 7.1.1: Fix phase-based (30-45 min)
- Story 7.1.2: Architecture refactor (1-1.5 hrs)
- Story 7.1.3: Test story-based (30-45 min)

**Session 2**:
- Story 7.1.4: Integration tests (45 min)
- Story 7.1.5: Documentation (20 min)

## Dependencies

**Blocks**: Epic 8 (Reference Todo Application)
**Requires**: Epic 7 components (already complete)

## Risks

1. **Architecture refactoring complexity** - Mitigate: Start simple, iterate
2. **Unknown bugs during testing** - Mitigate: Fix as discovered, document
3. **Time overrun** - Mitigate: Get working first, polish later

## Definition of Done

- [ ] Both benchmark types run successfully
- [ ] QA-as-you-go workflow validated
- [ ] Story workflow in core orchestrator
- [ ] Integration tests pass
- [ ] Documentation updated
- [ ] All story points committed atomically
- [ ] sprint-status.yaml updated

---

## Notes

This epic transforms GAO-Dev from "components exist" to "system actually works". It's critical infrastructure work that unblocks all future testing and benchmarking.

**Key Insight**: Story-by-story incremental development with QA validation should be the CORE workflow, not a benchmark feature. This epic fixes that architectural mistake.
