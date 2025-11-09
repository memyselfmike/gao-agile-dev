# Epic 28: Ceremony-Driven Workflow Integration

**Epic ID**: epic-28
**Feature**: Ceremony Integration & Self-Learning System
**Duration**: 1.5 weeks (30 story points)
**Owner**: Amelia (Developer)
**Status**: Planning
**Dependencies**: Epics 22-27 (ceremony infrastructure complete)

---

## Epic Goal

Integrate ceremonies into workflow orchestration so they trigger automatically based on project scale, epic milestones, story progress, and quality gates.

**Success Criteria**:
- [

] Ceremonies trigger automatically in Level 2-4 workflows
- [ ] CeremonyTriggerEngine evaluates all trigger types correctly
- [ ] Enhanced WorkflowSelector injects ceremonies appropriately
- [ ] CLI command `gao-dev ceremony hold <type>` works
- [ ] 25+ tests passing
- [ ] <2% ceremony overhead

---

## Overview

**Current State**: CeremonyOrchestrator exists but is never invoked - ceremonies are "orphaned infrastructure"

**Desired State**: Ceremonies trigger automatically:
- **Planning**: At epic start (Level 3+)
- **Standups**: Every N stories (Level 2+, varies by scale)
- **Retrospectives**: At epic completion, mid-epic checkpoints (Level 2+)

**Impact**: True autonomous operation with team coordination built-in

---

## User Stories (5 stories, 30 points)

### Story 28.1: Ceremony Workflow Types
**Points**: 5
**Owner**: Amelia
**Status**: Pending

**Description**:
Create ceremony workflow definitions that can be loaded by WorkflowRegistry and included in workflow sequences.

**Acceptance Criteria**:
- [ ] Create `gao_dev/workflows/5-ceremonies/` directory
- [ ] Create `ceremony-planning/workflow.yaml`
- [ ] Create `ceremony-standup/workflow.yaml`
- [ ] Create `ceremony-retrospective/workflow.yaml`
- [ ] Each ceremony workflow includes:
  - Metadata (ceremony_type, participants, trigger)
  - Steps (load context, hold ceremony, extract learnings, create action items)
  - Success criteria
- [ ] WorkflowRegistry loads ceremony workflows
- [ ] WorkflowStep supports ceremony metadata
- [ ] 5 unit tests

**Technical Details**:
```yaml
# ceremony-retrospective.yaml
name: ceremony-retrospective
description: Hold retrospective ceremony to extract learnings
phase: retrospective
type: ceremony

inputs:
  epic_num: {required: true}
  trigger: {required: true}
  participants: {default: ["team"]}

steps:
  - name: Load context
    agent: System
    action: FastContextLoader.get_epic_context(epic_num)
  - name: Hold ceremony
    agent: Brian
    action: CeremonyOrchestrator.hold_retrospective(epic_num, participants)
  - name: Extract learnings
    agent: Brian
    action: LearningIndexService.index_from_ceremony(ceremony_id)
  - name: Create action items
    agent: Bob
    action: ActionItemService.create_from_ceremony(ceremony_id)
```

---

### Story 28.2: Enhanced Workflow Selector
**Points**: 8
**Owner**: Amelia
**Status**: Pending

**Description**:
Enhance WorkflowSelector to inject ceremony workflows into Level 2-4 sequences at appropriate points.

**Acceptance Criteria**:
- [ ] Modify `workflow_selector.py` with ceremony injection logic
- [ ] Add `_inject_ceremonies(workflows, scale_level)` method
- [ ] Add `_create_planning_ceremony()`, `_create_standup_ceremony()`, `_create_retrospective_ceremony()`
- [ ] Level 2 workflows include:
  - Planning (optional)
  - Standup (every 3 stories if >3 total)
  - Retrospective (required)
- [ ] Level 3 workflows include:
  - Planning (required)
  - Standup (every 2 stories + quality gate failures)
  - Retrospective (mid-epic + completion)
- [ ] Level 4 workflows include:
  - Planning (required)
  - Standup (every story + daily)
  - Retrospective (per phase + completion)
- [ ] Ceremony WorkflowSteps have correct dependencies
- [ ] 10 unit tests (one per level + injection logic)

**Technical Details**:
- Each ceremony WorkflowStep includes metadata:
  - `ceremony_type`: "planning", "standup", "retrospective"
  - `participants`: List of agent names
  - `trigger`: TriggerType enum value
  - `interval` (standup only): Story interval
  - `required`: Boolean

---

### Story 28.3: CeremonyTriggerEngine
**Points**: 8
**Owner**: Amelia
**Status**: Pending

**Description**:
Create CeremonyTriggerEngine service to evaluate trigger conditions and decide when ceremonies should run.

**Acceptance Criteria**:
- [ ] Create `gao_dev/core/services/ceremony_trigger_engine.py` (~350 LOC)
- [ ] Implement `TriggerType` enum (10 trigger types)
- [ ] Implement `TriggerContext` dataclass
- [ ] Implement `CeremonyTriggerEngine` class with methods:
  - `should_trigger_planning(context) -> bool`
  - `should_trigger_standup(context) -> bool`
  - `should_trigger_retrospective(context) -> bool`
  - `evaluate_all_triggers(context) -> List[CeremonyType]`
- [ ] Trigger logic handles:
  - Epic lifecycle (start, completion, mid-checkpoint)
  - Story intervals (every N stories)
  - Quality gates (failure triggers standup)
  - Time-based (daily for Level 4)
  - Error recovery (repeated failures)
- [ ] Integration with StateCoordinator for epic/story state
- [ ] 15 unit tests (edge cases, each trigger type)

**Trigger Rules Matrix**:
```
Level 2:
- Planning: Optional (epic_start)
- Standup: Every 3 stories (if >3 total)
- Retrospective: Epic completion

Level 3:
- Planning: Required (epic_start)
- Standup: Every 2 stories OR quality_gate_failure
- Retrospective: mid_epic_checkpoint (50%) + epic_completion

Level 4:
- Planning: Required (epic_start)
- Standup: Every story OR daily (whichever first)
- Retrospective: phase_end (4 phases) + epic_completion
```

---

### Story 28.4: Orchestrator Integration
**Points**: 5
**Owner**: Amelia
**Status**: Pending

**Description**:
Integrate CeremonyTriggerEngine with WorkflowCoordinator so ceremonies execute seamlessly in workflow sequences.

**Acceptance Criteria**:
- [ ] Modify `WorkflowCoordinator` to use CeremonyTriggerEngine
- [ ] After each workflow step completion:
  - Build TriggerContext
  - Call `trigger_engine.evaluate_all_triggers(context)`
  - Execute triggered ceremonies via CeremonyOrchestrator
- [ ] Ceremony outcomes (transcript, action items, learnings) committed to git atomically
- [ ] Context updated with ceremony results before next workflow
- [ ] Handle ceremony failures gracefully (log, continue workflow)
- [ ] Modify `orchestrator_factory.py` to initialize CeremonyTriggerEngine
- [ ] 8 integration tests (full workflows with ceremonies)

**Integration Flow**:
```
WorkflowCoordinator.execute_sequence():
  for workflow_step in sequence:
    execute_workflow(workflow_step)

    # NEW: Evaluate ceremony triggers
    context = build_trigger_context()
    ceremonies = trigger_engine.evaluate_all_triggers(context)

    for ceremony_type in ceremonies:
      result = ceremony_orchestrator.hold_ceremony(
        ceremony_type=ceremony_type,
        epic_num=context.epic_num,
        participants=get_participants(ceremony_type)
      )
      commit_ceremony_artifacts(result)
      update_context_with_ceremony_results(result)
```

---

### Story 28.5: CLI Commands & Testing
**Points**: 4
**Owner**: Amelia
**Status**: Pending

**Description**:
Add CLI commands for manual ceremony invocation and comprehensive E2E tests validating full ceremony integration.

**Acceptance Criteria**:
- [ ] Create `gao_dev/cli/ceremony_commands.py`
- [ ] Add commands:
  - `gao-dev ceremony hold <type> --epic <N>` - Manual ceremony
  - `gao-dev ceremony list --epic <N>` - List past ceremonies
  - `gao-dev ceremony show <id>` - Show ceremony details
- [ ] Commands integrate with CeremonyOrchestrator
- [ ] Pretty CLI output (transcript, action items, learnings)
- [ ] 3 E2E tests:
  - Level 2 feature with ceremonies (simple)
  - Level 3 feature with mid-epic retro
  - Quality gate failure triggering standup
- [ ] Update main CLI (`commands.py`) to include ceremony subcommands
- [ ] Documentation in `--help` output
- [ ] 5 CLI tests

**CLI Example**:
```bash
$ gao-dev ceremony hold retrospective --epic 5

Ceremony: Retrospective for Epic 5
Participants: team
Trigger: epic_completion

[Holding ceremony...]

Results:
- Transcript: .gao-dev/ceremonies/retrospective_epic5_20251109.txt
- Action Items: 3 created
- Learnings: 2 indexed

Action Items:
1. [HIGH] Add integration tests for auth module (→ Story 5.7)
2. [MED] Improve error messages in API responses
3. [LOW] Update documentation with new endpoints

Learnings:
1. [Quality] JWT token validation needs edge case tests
2. [Process] Mid-epic standups caught blocker early

Git commit: docs(epic-5): retrospective ceremony complete
```

---

## Epic Deliverables

### Code (1,000+ LOC)
1. `gao_dev/workflows/5-ceremonies/` - 3 ceremony workflows (~150 LOC YAML)
2. `gao_dev/core/services/ceremony_trigger_engine.py` - Trigger evaluation (~350 LOC)
3. `gao_dev/methodologies/adaptive_agile/workflow_selector.py` - Enhanced (~200 LOC added)
4. `gao_dev/core/services/workflow_coordinator.py` - Integration updates (~100 LOC)
5. `gao_dev/cli/ceremony_commands.py` - CLI commands (~200 LOC)

### Tests (500+ LOC)
- Unit tests: 38 tests
- Integration tests: 8 tests
- E2E tests: 3 scenarios
- CLI tests: 5 tests

### Documentation
- Epic document (this file)
- 5 story files
- CLI help text
- ARCHITECTURE.md updates

---

## Dependencies

**Required (Completed)**:
- ✅ Epic 26: CeremonyOrchestrator with hold_ceremony(), hold_standup(), hold_retrospective()
- ✅ Epic 24: ActionItemService, LearningIndexService
- ✅ Epic 25: FastContextLoader, GitIntegratedStateManager
- ✅ WorkflowRegistry, WorkflowCoordinator

**Blocks**:
- Epic 29 (self-learning) depends on Epic 28 completion

---

## Technical Risks

**Risk 1: Ceremony Overhead**
- Mitigation: Make most ceremonies optional, track time cost, <2% target

**Risk 2: Trigger Evaluation Complexity**
- Mitigation: Simple boolean logic, comprehensive tests, gradual rollout

**Risk 3: Git Commit Failures**
- Mitigation: Transaction support from Epic 25, rollback on errors

---

## Testing Strategy

### Unit Tests (38 tests)
- CeremonyTriggerEngine: 15 tests
- Enhanced WorkflowSelector: 10 tests
- Workflow loading: 5 tests
- CLI commands: 5 tests
- Utility functions: 3 tests

### Integration Tests (8 tests)
- Full workflow with planning ceremony
- Standup triggered by story interval
- Standup triggered by quality gate failure
- Mid-epic retrospective (Level 3)
- Multiple ceremonies in sequence
- Ceremony artifact commits
- Context updates with ceremony results
- Error recovery (ceremony failure)

### E2E Tests (3 scenarios)
- Small feature (Level 2) end-to-end
- Medium feature (Level 3) with all ceremonies
- Quality gate failure scenario

---

## Acceptance Criteria (Epic-Level)

Epic 28 is **COMPLETE** when:

1. **Ceremony Integration**:
   - [ ] All 5 stories completed and tested
   - [ ] Ceremonies trigger automatically in Level 2-4 workflows
   - [ ] CLI commands work for manual invocation
   - [ ] 54+ tests passing (38 unit + 8 integration + 5 CLI + 3 E2E)

2. **Validation**:
   - [ ] Benchmark run with Level 2 feature shows ceremonies triggering
   - [ ] No regression in existing workflows
   - [ ] Ceremony overhead <2% of workflow time

3. **Documentation**:
   - [ ] All story files created
   - [ ] ARCHITECTURE.md updated
   - [ ] CLI help documentation complete

---

## Next Steps

After Epic 28 completion → **Epic 29: Self-Learning Feedback Loop**
- Learnings from retrospectives feed back into Brian's workflow selection
- System learns from past mistakes and improves

---

**Status**: Ready for Story Breakdown and Implementation
**Start Date**: TBD
**Target Completion**: TBD + 1.5 weeks
