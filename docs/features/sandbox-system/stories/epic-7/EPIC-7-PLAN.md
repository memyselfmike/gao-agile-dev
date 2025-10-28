# Epic 7: Autonomous Artifact Creation & Git Integration

**Status**: Planning
**Priority**: P0 (Critical - Core GAO-Dev Feature)
**Estimated Story Points**: 21
**Sprint**: Next

---

## Problem Statement

The benchmark system currently spawns agents directly via AgentSpawner, which:
- ❌ Generates agent responses but discards them
- ❌ Does NOT create artifacts (docs, code, tests)
- ❌ Does NOT commit to git
- ❌ Bypasses GAO-Dev's orchestration entirely

**The whole point of GAO-Dev is to autonomously build real projects with visible artifacts and atomic commits.**

## Current (Broken) Flow

```
┌─────────────────┐
│ Benchmark Runner│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AgentSpawner   │ ← Direct Anthropic API calls
└────────┬────────┘
         │
         ▼
  [Response Generated]
         │
         ▼
  [Discarded!] ❌
```

## Correct Flow (To Implement)

```
┌─────────────────┐
│ Benchmark Runner│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ GAO-Dev Commands             │
│ - create-prd                 │
│ - create-architecture        │
│ - create-story              │
│ - implement-story           │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ GAODevOrchestrator          │
│ - Spawns agents properly    │
│ - Creates artifacts         │
│ - Parses agent outputs      │
│ - Writes files to disk      │
│ - Commits atomically        │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Real Project Artifacts       │
│ docs/PRD.md                  │
│ docs/ARCHITECTURE.md         │
│ docs/stories/*.md            │
│ src/**/*.ts                  │
│ tests/**/*.test.ts           │
│ [Git commits]                │
└──────────────────────────────┘
```

---

## Root Cause Analysis

### What Exists Today

1. **GAODevOrchestrator** (`gao_dev/orchestrator/orchestrator.py`)
   - ✅ Knows how to spawn agents properly
   - ✅ Has access to all GAO-Dev tools
   - ✅ Can create artifacts and commit to git
   - ✅ Used by CLI commands (create-prd, implement-story, etc.)

2. **CLI Commands** (`gao_dev/cli/commands.py`)
   - ✅ `create-prd` - Creates PRD using John
   - ✅ `create-architecture` - Creates architecture using Winston
   - ✅ `create-story` - Creates stories using Bob
   - ✅ `implement-story` - Full workflow with commits

3. **AgentSpawner** (`gao_dev/sandbox/benchmark/agent_spawner.py`)
   - ❌ Bypasses GAODevOrchestrator entirely
   - ❌ Direct Anthropic API calls
   - ❌ No artifact creation
   - ❌ No git integration
   - ❌ **SHOULD NOT EXIST** - duplicate functionality

### The Gap

The benchmark system created its own parallel agent spawning mechanism instead of using GAO-Dev's existing orchestration. This is architectural duplication and defeats the purpose of GAO-Dev.

**The benchmark system should invoke GAO-Dev commands, not spawn agents itself.**

---

## Epic Goals

### Primary Goal
**Make benchmarks use GAO-Dev's existing orchestration to create real, visible project artifacts with atomic git commits.**

### Success Criteria

1. ✅ Benchmark runs execute GAO-Dev commands (not AgentSpawner)
2. ✅ All agent outputs persisted to appropriate files
3. ✅ Atomic git commits after each phase/story
4. ✅ Full project artifacts visible in sandbox/projects/
5. ✅ Metrics still collected (tokens, cost, duration)
6. ✅ Can see complete project history in git log

### Out of Scope (For Now)

- Interactive user prompts during execution
- Manual intervention/approval workflows
- Multi-project orchestration

---

## Architecture Design

### Benchmark Runner Refactor

**Old**:
```python
# Benchmark spawns agents directly
agent_spawner = AgentSpawner(api_key=api_key)
result = agent_spawner.spawn_agent(
    agent_name="Amelia",
    task_prompt="Create PRD",
    project_path=project_path
)
# result.output is discarded ❌
```

**New**:
```python
# Benchmark calls GAO-Dev orchestrator
from gao_dev.orchestrator import GAODevOrchestrator

orchestrator = GAODevOrchestrator(project_root=project_path)
await orchestrator.execute_command(
    command="create-prd",
    initial_prompt=benchmark_config.initial_prompt
)
# PRD created at docs/PRD.md ✅
# Git commit created ✅
```

### Command Mapping

Map benchmark phases to GAO-Dev commands:

| Benchmark Phase | GAO-Dev Command | Creates |
|----------------|-----------------|---------|
| Product Requirements | `create-prd` | `docs/PRD.md` + commit |
| System Architecture | `create-architecture` | `docs/ARCHITECTURE.md` + commit |
| Story Creation | `create-story --epic all` | `docs/stories/*.md` + commit |
| Implementation | `implement-story --all` | `src/`, `tests/` + commits per story |

### Metrics Collection

Metrics should be collected **around** GAO-Dev commands, not inside them:

```python
# Before
metrics_start = time.time()

# Execute GAO-Dev command
await orchestrator.execute_command("create-prd", prompt)

# After
duration = time.time() - metrics_start
metrics.record(duration=duration, phase="create-prd")
```

---

## Story Breakdown

### Story 7.1: Remove AgentSpawner & Refactor to GAODevOrchestrator
**Points**: 5
**Priority**: P0

**Description**: Remove duplicate AgentSpawner and make benchmark runner use GAODevOrchestrator.

**Acceptance Criteria**:
- [ ] AgentSpawner removed from codebase
- [ ] Benchmark runner uses GAODevOrchestrator
- [ ] Phase execution calls appropriate GAO-Dev commands
- [ ] Tests updated and passing

**Technical Details**:
- Delete `gao_dev/sandbox/benchmark/agent_spawner.py`
- Update `orchestrator.py` to use `GAODevOrchestrator`
- Map phase names to command names
- Update imports and dependencies

---

### Story 7.2: Implement Artifact Output Parser
**Points**: 3
**Priority**: P0

**Description**: Parse agent outputs to extract artifacts and determine file paths.

**Acceptance Criteria**:
- [ ] Can parse agent markdown output
- [ ] Extracts file paths and content
- [ ] Handles multiple files in single response
- [ ] Error handling for malformed outputs

**Technical Details**:
- Create `ArtifactParser` class
- Use regex/markdown parsing to find code blocks
- Map artifacts to file paths based on phase
- Validate file paths are within project

**Example Output to Parse**:
```markdown
# Product Requirements Document

## Overview
...

**Save as**: docs/PRD.md
```

---

### Story 7.3: Implement Atomic Git Commits
**Points**: 3
**Priority**: P0

**Description**: Automatically commit artifacts after each phase with descriptive messages.

**Acceptance Criteria**:
- [ ] Git commit after each command execution
- [ ] Commit messages follow convention
- [ ] Only commits relevant files
- [ ] Handles merge conflicts gracefully

**Technical Details**:
- Use existing GitManager
- Commit message format: `feat(phase-name): Create [artifact]`
- Stage only files created in current phase
- Tag commits with benchmark run ID

**Example Commits**:
```
feat(prd): Create Product Requirements Document
feat(architecture): Create system architecture design
feat(stories): Create user stories for Epic 1
feat(story-1.1): Implement authentication system
```

---

### Story 7.4: Update Metrics Collection
**Points**: 2
**Priority**: P1

**Description**: Collect metrics around GAO-Dev command execution.

**Acceptance Criteria**:
- [ ] Metrics collected for each command
- [ ] Includes token usage, cost, duration
- [ ] Artifacts count and size tracked
- [ ] Git commit SHAs recorded

**Technical Details**:
- Wrap orchestrator calls with metrics collection
- Extract usage from Claude SDK
- Record file counts and sizes
- Link metrics to git commits

---

### Story 7.5: Add Artifact Verification
**Points**: 3
**Priority**: P1

**Description**: Verify that expected artifacts were created and are valid.

**Acceptance Criteria**:
- [ ] Checks that files exist
- [ ] Validates file content (not empty)
- [ ] Checks git commits were created
- [ ] Reports missing artifacts as warnings

**Technical Details**:
- Define expected artifacts per phase
- File existence checks
- Content validation (min length, valid syntax)
- Git log verification

---

### Story 7.6: Create Example Benchmark with Artifacts
**Points**: 2
**Priority**: P1

**Description**: Create a simple benchmark that demonstrates full artifact creation.

**Acceptance Criteria**:
- [ ] New benchmark config: `simple-todo-with-artifacts.yaml`
- [ ] Runs successfully end-to-end
- [ ] Creates all expected artifacts
- [ ] Git history shows all commits
- [ ] Documentation updated

**Technical Details**:
- Copy greenfield-simple.yaml
- Add artifact expectations
- Run and verify output
- Document expected results

---

### Story 7.7: Update Documentation
**Points**: 3
**Priority**: P2

**Description**: Document the new architecture and how benchmarks work.

**Acceptance Criteria**:
- [ ] Architecture diagram updated
- [ ] Benchmark creation guide updated
- [ ] Troubleshooting guide added
- [ ] Examples provided

**Files to Update**:
- `docs/sandbox-autonomous-benchmark-guide.md`
- `docs/features/sandbox-system/ARCHITECTURE.md`
- `README.md` with artifact examples

---

## Technical Decisions

### Decision 1: Use Existing GAODevOrchestrator

**Rationale**: GAODevOrchestrator already has all the logic we need. Don't duplicate it.

**Implementation**: Import and use GAODevOrchestrator directly in benchmark runner.

### Decision 2: Keep Benchmark-Specific Metrics

**Rationale**: Benchmarks need specific metrics (phase timing, cost tracking) that aren't part of normal GAO-Dev operation.

**Implementation**: Metrics collection wrapper around orchestrator calls.

### Decision 3: Delete AgentSpawner

**Rationale**: It's duplicate functionality that bypasses GAO-Dev's design.

**Implementation**: Complete removal, use GAODevOrchestrator instead.

---

## Dependencies

**Requires**:
- Existing GAODevOrchestrator
- Existing GitManager
- Claude SDK integration

**Blocks**:
- All future benchmark development
- Artifact-based success criteria
- Multi-agent collaboration testing

---

## Risks & Mitigations

### Risk 1: GAODevOrchestrator Not Designed for Batch Operation

**Mitigation**: Add batch mode flag to orchestrator if needed. Keep it simple.

### Risk 2: Git Conflicts During Benchmarking

**Mitigation**: Each benchmark run gets isolated sandbox project. No conflicts possible.

### Risk 3: Performance Impact

**Mitigation**: Git operations are fast. Artifact writes are minimal overhead.

---

## Definition of Done

- [ ] All 7 stories completed
- [ ] AgentSpawner deleted
- [ ] Benchmark uses GAODevOrchestrator
- [ ] Artifacts created and visible
- [ ] Git commits atomic and descriptive
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Example benchmark runs successfully

---

## Notes

This is **THE** core functionality of GAO-Dev. Without artifact creation and git integration, GAO-Dev is just a chatbot. This epic makes it a real autonomous development system.

**Quote from user**: "the whole point is to have gao-dev build a real project we can see all artefacts for and live commit atomically as we go"

This is foundational work that everything else depends on.
