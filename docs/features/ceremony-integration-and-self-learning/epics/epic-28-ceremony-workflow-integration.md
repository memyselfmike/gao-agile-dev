# Epic 28: Ceremony-Driven Workflow Integration

**Epic ID**: epic-28
**Feature**: Ceremony Integration & Self-Learning System
**Duration**: 2 weeks (35 story points) - Updated from 1.5 weeks (C4 Fix)
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

## User Stories (6 stories, 35 points - Updated C4 Fix)

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
**Points**: 8 (REVISED from 5 - C4 Fix: Transaction boundaries + failure handling)
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

### Story 28.6: DocumentStructureManager (C4 Fix - Missing Component)
**Points**: 5
**Owner**: Amelia
**Status**: Pending

**Description**:
Create `DocumentStructureManager` service to systematically initialize and maintain document structure based on work type and scale level. This component was missing from the original plan but is required by Epic 29.5 (Action Item Integration).

**Acceptance Criteria**:
- [ ] Create `gao_dev/core/services/document_structure_manager.py` (~300 LOC)
- [ ] Implement `initialize_feature_folder(feature_name, scale_level)`:
  - Level 0 (Chore): No folder created
  - Level 1 (Bug): Optional `docs/bugs/<bug-id>.md`
  - Level 2 (Small Feature): `docs/features/<name>/` with PRD, stories/, CHANGELOG.md
  - Level 3 (Medium Feature): + ARCHITECTURE.md, epics/, retrospectives/
  - Level 4 (Greenfield): + ceremonies/, MIGRATION_GUIDE.md
- [ ] Implement `update_global_docs(feature_name, epic_num, update_type)`:
  - Update `docs/PRD.md` with feature status
  - Update `docs/CHANGELOG.md` with epic completion
  - Link to feature folder
- [ ] Document template system:
  - PRD template (lightweight vs. full)
  - ARCHITECTURE template
  - CHANGELOG template
- [ ] Integration with `DocumentLifecycleManager`:
  - Auto-register all created documents
  - Track document metadata (feature, scale_level)
- [ ] Git commit after folder initialization
- [ ] 8 unit tests:
  - Folder initialization for each scale level (5 tests)
  - Global doc updates (2 tests)
  - Template rendering (1 test)

**Technical Details**:
```python
class DocumentStructureManager:
    """
    Manages document structure based on work type and scale level.

    Responsibilities:
    - Initialize feature folders with correct structure
    - Create document templates (PRD, ARCHITECTURE, etc.)
    - Update global docs (PRD.md, CHANGELOG.md)
    - Enforce structure consistency
    """

    def __init__(
        self,
        project_root: Path,
        doc_lifecycle: DocumentLifecycleManager,
        git_manager: GitManager
    ):
        self.project_root = project_root
        self.doc_lifecycle = doc_lifecycle
        self.git = git_manager

    def initialize_feature_folder(
        self,
        feature_name: str,
        scale_level: ScaleLevel
    ) -> Optional[Path]:
        """
        Initialize feature folder based on scale level.

        Returns:
            Path to created folder, or None for Level 0
        """
        if scale_level == ScaleLevel.LEVEL_0_CHORE:
            return None

        # Level 1: Optional bug report
        if scale_level == ScaleLevel.LEVEL_1_BUG_FIX:
            bug_path = self.project_root / "docs" / "bugs"
            bug_path.mkdir(parents=True, exist_ok=True)
            return bug_path

        # Level 2+: Feature folder
        feature_path = self.project_root / "docs" / "features" / feature_name
        feature_path.mkdir(parents=True, exist_ok=True)

        # Create structure based on level
        if scale_level >= ScaleLevel.LEVEL_2_SMALL_FEATURE:
            self._create_file(
                feature_path / "PRD.md",
                self._prd_template(feature_name, "lightweight")
            )
            (feature_path / "stories").mkdir(exist_ok=True)
            (feature_path / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n")

        if scale_level >= ScaleLevel.LEVEL_3_MEDIUM_FEATURE:
            self._create_file(
                feature_path / "ARCHITECTURE.md",
                self._architecture_template(feature_name)
            )
            (feature_path / "epics").mkdir(exist_ok=True)
            (feature_path / "retrospectives").mkdir(exist_ok=True)

        if scale_level == ScaleLevel.LEVEL_4_GREENFIELD:
            (feature_path / "ceremonies").mkdir(exist_ok=True)
            (feature_path / "MIGRATION_GUIDE.md").write_text("# Migration Guide\n\nTBD\n")

        # Register with document lifecycle
        self.doc_lifecycle.register_document(
            path=feature_path / "PRD.md",
            doc_type=DocumentType.PRD,
            metadata={
                "feature": feature_name,
                "scale_level": scale_level.value
            }
        )

        # Git commit
        self.git.add_all()
        self.git.commit(
            f"docs({feature_name}): initialize feature folder (Level {scale_level.value})"
        )

        return feature_path

    def update_global_docs(
        self,
        feature_name: str,
        epic_num: int,
        update_type: str  # 'planned', 'architected', 'completed'
    ) -> None:
        """Update global PRD and ARCHITECTURE docs."""
        if update_type == 'planned':
            self._update_global_prd(feature_name, epic_num, status="Planned")
        elif update_type == 'architected':
            self._update_global_architecture(feature_name, epic_num)
        elif update_type == 'completed':
            self._update_global_prd(feature_name, epic_num, status="Completed")
            self._update_changelog(feature_name, epic_num)
```

**Dependencies**:
- DocumentLifecycleManager (Epic 20)
- GitManager (Epic 23)
- Template rendering system

**Required By**:
- Story 29.5: Action Item Integration (depends on DocumentStructureManager)

---

## Epic Deliverables

### Code (1,300+ LOC - Updated C4 Fix)
1. `gao_dev/workflows/5-ceremonies/` - 3 ceremony workflows (~150 LOC YAML)
2. `gao_dev/core/services/ceremony_trigger_engine.py` - Trigger evaluation (~350 LOC)
3. `gao_dev/methodologies/adaptive_agile/workflow_selector.py` - Enhanced (~200 LOC added)
4. `gao_dev/core/services/workflow_coordinator.py` - Integration updates (~100 LOC)
5. `gao_dev/cli/ceremony_commands.py` - CLI commands (~200 LOC)
6. `gao_dev/core/services/document_structure_manager.py` - Document structure (~300 LOC) **NEW - C4 Fix**

### Tests (550+ LOC - Updated C4 Fix)
- Unit tests: 46 tests (+8 for DocumentStructureManager)
- Integration tests: 8 tests
- E2E tests: 3 scenarios
- CLI tests: 5 tests

### Documentation
- Epic document (this file)
- 6 story files (updated from 5 - C4 Fix)
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

### Unit Tests (46 tests - Updated C4 Fix)
- CeremonyTriggerEngine: 15 tests
- Enhanced WorkflowSelector: 10 tests
- DocumentStructureManager: 8 tests **NEW - C4 Fix**
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
   - [ ] All 6 stories completed and tested (updated from 5 - C4 Fix)
   - [ ] Ceremonies trigger automatically in Level 2-4 workflows
   - [ ] CLI commands work for manual invocation
   - [ ] DocumentStructureManager creates correct folder structures **NEW - C4 Fix**
   - [ ] 62+ tests passing (46 unit + 8 integration + 5 CLI + 3 E2E) - updated from 54

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
**Target Completion**: TBD + 2 weeks (updated from 1.5 weeks - C4 Fix)
