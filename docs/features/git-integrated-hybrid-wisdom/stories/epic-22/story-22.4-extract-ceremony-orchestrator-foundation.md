# Story 22.4: Extract CeremonyOrchestrator (Foundation)

**Epic**: Epic 22 - Orchestrator Decomposition & Architectural Refactoring
**Story ID**: 22.4
**Priority**: P1
**Estimate**: 5 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Create the foundation for the CeremonyOrchestrator service that will be fully implemented in Epic 26. This story establishes the service structure, interface definition, and basic ceremony coordination framework.

The foundation includes stub implementations of ceremony methods and the core infrastructure needed for Epic 26's full ceremony implementation.

---

## Acceptance Criteria

- [ ] Create `CeremonyOrchestrator` service (~100 LOC stub)
- [ ] Define ceremony interface (hold_standup, hold_retro, hold_planning)
- [ ] Create ceremony lifecycle framework
- [ ] Orchestrator integrates ceremony orchestrator
- [ ] Basic ceremony test framework created
- [ ] 5 unit tests for foundation
- [ ] Documentation for future Epic 26 implementation

---

## Technical Approach

### Implementation Details

The CeremonyOrchestrator foundation provides the structural framework for multi-agent ceremonies. Epic 26 will build on this foundation to implement full ceremony logic.

**Foundation Responsibilities**:
1. Define ceremony interfaces
2. Establish ceremony lifecycle (prepare → execute → record)
3. Create stub methods for all ceremony types
4. Prepare integration points for Epic 26
5. Document ceremony architecture

**Design Pattern**: Service pattern with template method for ceremony lifecycle

### Files to Modify

- `gao_dev/orchestrator/ceremony_orchestrator.py` (+100 LOC / NEW)
  - Add: CeremonyOrchestrator class
  - Add: hold_standup() stub
  - Add: hold_retrospective() stub
  - Add: hold_planning() stub
  - Add: Ceremony lifecycle methods
  - Add: Documentation for Epic 26

- `gao_dev/orchestrator/orchestrator.py` (+20 delegation)
  - Add: ceremony_orchestrator initialization
  - Add: Delegate ceremony calls (when needed)

### New Files to Create

- `gao_dev/orchestrator/ceremony_orchestrator.py` (~100 LOC)
  - Purpose: Foundation for ceremony coordination (full implementation in Epic 26)
  - Key components:
    - CeremonyOrchestrator class
    - hold_standup() stub
    - hold_retrospective() stub
    - hold_planning() stub
    - _prepare_ceremony() framework
    - _execute_ceremony() framework
    - _record_ceremony() framework

- `tests/orchestrator/test_ceremony_orchestrator.py` (~80 LOC)
  - Purpose: Test ceremony foundation
  - Key components:
    - 5 basic tests
    - Test ceremony interface exists
    - Test stub methods callable
    - Test ceremony lifecycle framework
    - TODO markers for Epic 26 tests

---

## Testing Strategy

### Unit Tests (5 tests)

- test_ceremony_orchestrator_initialization() - Test constructor
- test_standup_interface_exists() - Test hold_standup() callable
- test_retrospective_interface_exists() - Test hold_retrospective() callable
- test_planning_interface_exists() - Test hold_planning() callable
- test_ceremony_lifecycle_framework() - Test lifecycle methods exist

**Total Tests**: 5 tests
**Test File**: `tests/orchestrator/test_ceremony_orchestrator.py`

**Note**: Full ceremony tests will be added in Epic 26

---

## Dependencies

**Upstream**: Story 22.1, 22.2, 22.3

**Downstream**:
- Story 22.6 (Orchestrator facade integration)
- Epic 26 (Full ceremony implementation builds on this)

---

## Implementation Notes

### Foundation Service Structure

```python
# gao_dev/orchestrator/ceremony_orchestrator.py

class CeremonyOrchestrator:
    """
    Ceremony orchestration service.

    Foundation created in Epic 22.
    Full implementation in Epic 26.
    """

    def __init__(self, config: ConfigLoader):
        self.config = config
        # Epic 26 will add:
        # - FastContextLoader
        # - ConversationManager
        # - GitIntegratedStateManager

    def hold_standup(
        self,
        epic_num: int,
        participants: List[str]
    ) -> None:
        """
        Hold daily stand-up ceremony.

        Foundation in Epic 22 (stub).
        Full implementation in Epic 26.
        """
        # TODO: Epic 26 - Implement stand-up logic
        raise NotImplementedError("Full implementation in Epic 26")

    def hold_retrospective(
        self,
        epic_num: int,
        participants: List[str]
    ) -> None:
        """
        Hold retrospective ceremony.

        Foundation in Epic 22 (stub).
        Full implementation in Epic 26.
        """
        # TODO: Epic 26 - Implement retrospective logic
        raise NotImplementedError("Full implementation in Epic 26")

    def hold_planning(
        self,
        epic_num: int,
        participants: List[str]
    ) -> None:
        """
        Hold planning ceremony.

        Foundation in Epic 22 (stub).
        Full implementation in Epic 26.
        """
        # TODO: Epic 26 - Implement planning logic
        raise NotImplementedError("Full implementation in Epic 26")

    def _prepare_ceremony(
        self,
        ceremony_type: str,
        epic_num: int
    ) -> Dict[str, Any]:
        """
        Prepare ceremony context.

        Framework in Epic 22.
        Full implementation in Epic 26.
        """
        # TODO: Epic 26 - Load context, participants, agenda
        return {}

    def _execute_ceremony(
        self,
        ceremony_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute ceremony with multi-agent conversation.

        Framework in Epic 22.
        Full implementation in Epic 26.
        """
        # TODO: Epic 26 - ConversationManager integration
        return {}

    def _record_ceremony(
        self,
        ceremony_type: str,
        results: Dict[str, Any]
    ) -> None:
        """
        Record ceremony outcomes.

        Framework in Epic 22.
        Full implementation in Epic 26.
        """
        # TODO: Epic 26 - Save transcript, action items, learnings
        pass
```

### Documentation for Epic 26

The ceremony orchestrator includes comprehensive documentation for Epic 26 implementation:

**Ceremony Types**:
- Stand-up: Daily status sync, blockers, action items
- Retrospective: Learning capture, improvements, team health
- Planning: Story estimation, sprint commitment, capacity planning

**Epic 26 Will Add**:
- FastContextLoader integration (<5ms context)
- ConversationManager (multi-agent dialogues)
- Ceremony artifacts (transcripts, summaries)
- Action item creation and tracking
- Learning extraction and indexing

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (5/5 unit tests)
- [ ] Code review completed
- [ ] Documentation complete with Epic 26 TODO markers
- [ ] No breaking changes
- [ ] Git commit created
- [ ] Service <150 LOC (stub foundation)
- [ ] Clear integration points for Epic 26

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09
