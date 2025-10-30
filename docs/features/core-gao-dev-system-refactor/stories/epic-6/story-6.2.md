# Story 6.2: Extract StoryLifecycleManager Service

**Epic**: 6 - Legacy Cleanup & God Class Refactoring
**Story Points**: 5
**Priority**: P0 (Critical)
**Type**: Refactoring
**Status**: Ready

---

## Overview

Extract story and epic lifecycle management logic from `GAODevOrchestrator` into a dedicated `StoryLifecycleManager` service responsible for story state transitions and epic tracking.

---

## User Story

**As a** GAO-Dev architect
**I want** story lifecycle logic extracted into a dedicated service
**So that** story state management is isolated and testable

---

## Acceptance Criteria

1. **Service Created**
   - [ ] `gao_dev/core/services/story_lifecycle.py` created
   - [ ] Class `StoryLifecycleManager` < 200 lines
   - [ ] Single responsibility: Manage story/epic lifecycle

2. **Functionality**
   - [ ] Creates new stories and epics
   - [ ] Transitions story states (draft → ready → in_progress → done)
   - [ ] Validates state transitions
   - [ ] Tracks epic progress
   - [ ] Publishes lifecycle events

3. **Dependencies**
   - [ ] Uses `StoryRepository` for persistence
   - [ ] Uses `EventBus` for events
   - [ ] Constructor dependency injection

4. **Testing**
   - [ ] Unit tests (80%+ coverage)
   - [ ] State transition tests
   - [ ] Invalid transition tests
   - [ ] Epic tracking tests
   - [ ] Event publishing tests

5. **Documentation**
   - [ ] Class and method docstrings
   - [ ] Type hints throughout
   - [ ] State machine diagram in docstring

---

## Technical Details

### Service Interface

```python
class StoryLifecycleManager:
    """
    Manages story and epic lifecycle.

    Responsible for:
    - Creating stories and epics
    - Managing state transitions
    - Validating transitions
    - Publishing lifecycle events
    """

    def __init__(
        self,
        story_repository: IStoryRepository,
        event_bus: IEventBus
    ):
        pass

    async def create_story(
        self,
        epic: int,
        story: int,
        details: StoryDetails
    ) -> Story:
        """Create new story and publish event."""
        pass

    async def transition_state(
        self,
        story_id: StoryIdentifier,
        new_state: StoryStatus
    ) -> Story:
        """Transition story to new state with validation."""
        pass

    async def get_epic_progress(
        self,
        epic: int
    ) -> EpicProgress:
        """Get epic completion status."""
        pass
```

### State Machine

```
draft → ready → in_progress → ready_for_review → done
           ↑                            ↓
           └────────────────────────────┘
                  (back to ready if review fails)
```

### Events Published
- `StoryCreated(story_id, epic, story)`
- `StoryStateTransitioned(story_id, old_state, new_state)`
- `EpicCompleted(epic, story_count)`

---

## Implementation Steps

1. Create service file in `gao_dev/core/services/`
2. Implement story creation logic
3. Implement state transition with validation
4. Implement epic progress tracking
5. Extract from orchestrator.py
6. Write comprehensive tests
7. Update orchestrator to use service

---

## Definition of Done

- [ ] StoryLifecycleManager created (< 200 lines)
- [ ] All acceptance criteria met
- [ ] Unit tests (80%+ coverage)
- [ ] State machine validated with tests
- [ ] Orchestrator updated
- [ ] Regression tests pass

---

**Related Stories**: 6.1 (WorkflowCoordinator), 6.5 (Orchestrator Facade)
**Estimated Time**: 1 day
