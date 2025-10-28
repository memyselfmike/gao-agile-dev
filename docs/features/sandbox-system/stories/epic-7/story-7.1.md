# Story 7.1: Remove AgentSpawner & Refactor to GAODevOrchestrator

**Epic**: Epic 7 - Autonomous Artifact Creation & Git Integration
**Status**: Ready
**Priority**: P0 (Critical)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-28

---

## User Story

**As a** benchmark system
**I want** to use GAODevOrchestrator instead of AgentSpawner
**So that** agent outputs are properly persisted as artifacts with git commits

---

## Context

The benchmark system currently uses `AgentSpawner` which:
- Directly calls Anthropic API
- Generates agent responses but discards them
- Does NOT create artifacts (docs, code, tests)
- Does NOT commit to git
- Bypasses GAO-Dev's orchestration entirely

**This defeats the purpose of GAO-Dev**: to autonomously build real projects with visible artifacts and atomic commits.

---

## Acceptance Criteria

### AC1: AgentSpawner Removed
- [x] `gao_dev/sandbox/benchmark/agent_spawner.py` deleted
- [x] All imports of AgentSpawner removed
- [x] No references to AgentSpawner in codebase

### AC2: GAODevOrchestrator Integration
- [ ] BenchmarkRunner imports GAODevOrchestrator
- [ ] Phase execution uses orchestrator.execute_command()
- [ ] Project root passed to orchestrator
- [ ] Orchestrator initialized per benchmark run

### AC3: Command Mapping
- [ ] Benchmark phases mapped to GAO-Dev commands
- [ ] "Product Requirements" -> `create-prd`
- [ ] "System Architecture" -> `create-architecture`
- [ ] "Story Creation" -> `create-story --epic all`
- [ ] "Implementation" -> `implement-story --all`

### AC4: Tests Updated
- [ ] All tests using AgentSpawner refactored
- [ ] New tests for orchestrator integration
- [ ] Mock orchestrator for unit tests
- [ ] Integration tests with real orchestrator

### AC5: Error Handling
- [ ] Graceful handling of orchestrator failures
- [ ] Clear error messages
- [ ] Proper cleanup on failure
- [ ] Timeout enforcement maintained

---

## Technical Details

### Current Architecture (Broken)

```
BenchmarkRunner
    -> AgentSpawner (direct API calls)
        -> [Response generated]
            -> [Discarded!] ❌
```

### New Architecture (Correct)

```
BenchmarkRunner
    -> GAODevOrchestrator.execute_command()
        -> Agent spawning with proper context
        -> Artifact parsing and creation
        -> File writes to disk
        -> Git commits
        -> [Real project artifacts] ✅
```

### Command Mapping

| Benchmark Phase | GAO-Dev Command | Creates |
|----------------|-----------------|---------|
| Product Requirements | `create-prd` | `docs/PRD.md` + commit |
| System Architecture | `create-architecture` | `docs/ARCHITECTURE.md` + commit |
| Story Creation | `create-story --epic all` | `docs/stories/*.md` + commit |
| Implementation | `implement-story --all` | `src/`, `tests/` + commits per story |

### Implementation Steps

1. **Delete AgentSpawner**
   - Remove `gao_dev/sandbox/benchmark/agent_spawner.py`
   - Remove all imports

2. **Update BenchmarkRunner**
   - Import GAODevOrchestrator
   - Replace AgentSpawner calls with orchestrator.execute_command()
   - Pass project_root to orchestrator

3. **Create Command Mapping**
   - Map phase names to command names
   - Handle command arguments (epic numbers, story numbers)

4. **Update Tests**
   - Remove AgentSpawner tests
   - Add orchestrator integration tests
   - Mock orchestrator for unit tests

5. **Validate**
   - Run all tests
   - Manually test benchmark run
   - Verify artifacts created

---

## Files to Modify

**Delete**:
- `gao_dev/sandbox/benchmark/agent_spawner.py`

**Modify**:
- `gao_dev/sandbox/benchmark/orchestrator.py` - Use GAODevOrchestrator
- `gao_dev/sandbox/benchmark/runner.py` - Update phase execution
- `tests/sandbox/benchmark/test_orchestrator.py` - Update tests
- `tests/sandbox/benchmark/test_runner.py` - Update tests

**New Files**:
- None (using existing GAODevOrchestrator)

---

## Dependencies

**Requires**:
- Existing GAODevOrchestrator in `gao_dev/orchestrator/orchestrator.py`
- Existing CLI commands (create-prd, create-architecture, etc.)
- Existing GitManager

**Blocks**:
- Story 7.2 (Artifact Output Parser) - needs orchestrator working first
- All subsequent Epic 7 stories

---

## Risks & Mitigations

### Risk 1: GAODevOrchestrator Not Designed for Batch Operation
**Likelihood**: Medium
**Impact**: High
**Mitigation**: Add batch mode flag to orchestrator if needed. Keep it simple - orchestrator should handle sequential command execution.

### Risk 2: Command Arguments Complex
**Likelihood**: Low
**Impact**: Medium
**Mitigation**: Start with simple commands (create-prd, create-architecture). Add argument handling incrementally.

### Risk 3: Breaking Existing Tests
**Likelihood**: High
**Impact**: Medium
**Mitigation**: Update tests incrementally. Mock orchestrator for unit tests. Add integration tests with real orchestrator.

---

## Testing Approach

### Unit Tests
- Test command mapping (phase name -> command name)
- Test orchestrator initialization
- Test error handling
- Mock orchestrator for isolated tests

### Integration Tests
- Test full benchmark run with orchestrator
- Verify artifacts created
- Verify git commits created
- Test timeout enforcement

### Manual Testing
- Run simple benchmark (greenfield-simple.yaml)
- Verify PRD created in docs/
- Verify git commits created
- Check project structure

---

## Definition of Done

- [ ] AgentSpawner deleted
- [ ] BenchmarkRunner uses GAODevOrchestrator
- [ ] Phase execution calls appropriate commands
- [ ] All tests passing (unit + integration)
- [ ] Manual test successful (artifacts created)
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Committed with atomic commit

---

## Notes

**This is THE critical refactor** that makes GAO-Dev actually create artifacts. Without this, GAO-Dev is just a chatbot that generates responses and throws them away.

**Quote from user**: "the whole point is to have gao-dev build a real project we can see all artefacts for and live commit atomically as we go"

This story lays the foundation for all artifact creation and git integration work.

---

**Created by**: Bob (Scrum Master) via BMAD workflow
**Ready for Implementation**: Yes
**Estimated Completion**: 3-4 hours

---

*This story is the foundation of Epic 7 - all subsequent stories depend on this refactor.*
