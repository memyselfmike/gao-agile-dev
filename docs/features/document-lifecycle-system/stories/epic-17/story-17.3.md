# Story 17.3: Orchestrator Integration

**Epic:** 17 - Context System Integration
**Story Points:** 8
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Wire WorkflowContext into GAODevOrchestrator lifecycle so workflows automatically create and persist context. This makes context tracking completely automatic and transparent - every workflow execution gets a WorkflowContext created at startup, persisted to the database, and updated throughout the workflow lifecycle. Agents can access context via thread-local storage without explicit passing, and workflow results include context_id for traceability.

---

## Business Value

This story makes context tracking automatic and seamless:

- **Automatic Tracking**: Every workflow gets context without manual creation
- **Lifecycle Management**: Context created, updated, and finalized automatically
- **Agent Access**: Agents access context via thread-local storage (no parameter passing)
- **Traceability**: Every workflow result includes context_id for tracking
- **Decision Tracking**: All workflow decisions recorded in context
- **Artifact Tracking**: All created artifacts linked to context
- **Failure Handling**: Failed workflows marked in context for debugging
- **Observability**: Full workflow history with context persistence
- **Analytics Ready**: Context data enables workflow analytics and optimization
- **Foundation for Agents**: Essential for agent prompt integration (Story 17.4)

---

## Acceptance Criteria

### Context Creation
- [ ] Orchestrator creates WorkflowContext at workflow start
- [ ] Context persisted to database at workflow initialization
- [ ] Context includes workflow_id, feature, epic, story
- [ ] Context status set to 'in_progress' initially
- [ ] Context metadata includes workflow type and scale level

### Context Updates
- [ ] Context updated after each workflow phase transition
- [ ] Phase changes recorded in context (e.g., 'planning' -> 'implementation')
- [ ] Decisions recorded in context during execution
- [ ] Artifacts recorded in context as they're created
- [ ] Document access tracked automatically (via AgentContextAPI)

### Context Finalization
- [ ] Failed workflows mark context status as 'failed'
- [ ] Completed workflows mark context status as 'completed'
- [ ] Final context persisted to database at workflow end
- [ ] Context includes final metadata (duration, outcome)

### WorkflowResult Integration
- [ ] WorkflowResult includes context_id field
- [ ] Context_id can be used to query full workflow context
- [ ] WorkflowResult serialization includes context_id

### Thread-Local Access
- [ ] `set_workflow_context()` called at workflow start
- [ ] Agents can access context via `get_workflow_context()`
- [ ] Thread-local storage isolated per workflow execution
- [ ] Context cleared on workflow completion

### Testing
- [ ] Integration tests verify full workflow with context tracking
- [ ] Benchmark workflows show context tracking in action
- [ ] Test context persisted correctly for successful workflows
- [ ] Test context marked as failed for failed workflows
- [ ] Test concurrent workflows have isolated contexts

---

## Technical Notes

### Implementation Approach

**File:** `gao_dev/orchestrator/orchestrator.py`

Update GAODevOrchestrator to create and manage context:

```python
from gao_dev.core.context import ContextPersistence, WorkflowContext, set_workflow_context
from pathlib import Path

class GAODevOrchestrator:
    def __init__(self, ...):
        # ... existing code ...
        self._context_persistence = ContextPersistence()

    async def execute_workflow(
        self,
        workflow_name: str,
        context: Dict[str, Any],
        ...
    ) -> WorkflowResult:
        """Execute workflow with automatic context tracking."""

        # Create workflow context
        workflow_context = WorkflowContext(
            workflow_id=workflow_id,
            feature_name=context.get('feature_name', 'unknown'),
            epic_number=context.get('epic_number'),
            story_number=context.get('story_number'),
            phase='initialization',
            status='in_progress',
            metadata={
                'workflow_name': workflow_name,
                'scale_level': context.get('scale_level'),
                'methodology': context.get('methodology', 'adaptive_agile'),
            }
        )

        # Persist initial context
        self._context_persistence.save_context(workflow_context)

        # Set thread-local context for agent access
        set_workflow_context(workflow_context)

        try:
            # Execute workflow phases
            for phase in workflow_phases:
                # Update context phase
                workflow_context.phase = phase
                self._context_persistence.update_context(workflow_context)

                # Execute phase
                phase_result = await self._execute_phase(phase, context)

                # Record decisions
                if phase_result.decisions:
                    for decision in phase_result.decisions:
                        workflow_context.add_decision(
                            decision_type=decision['type'],
                            decision=decision['content'],
                            rationale=decision['rationale']
                        )

                # Record artifacts
                if phase_result.artifacts:
                    for artifact in phase_result.artifacts:
                        workflow_context.add_artifact(
                            artifact_type=artifact['type'],
                            artifact_path=artifact['path'],
                            description=artifact['description']
                        )

            # Mark as completed
            workflow_context.status = 'completed'
            self._context_persistence.update_context(workflow_context)

            # Return result with context_id
            return WorkflowResult(
                success=True,
                context_id=workflow_context.id,
                artifacts=artifacts,
                ...
            )

        except Exception as e:
            # Mark as failed
            workflow_context.status = 'failed'
            workflow_context.metadata['error'] = str(e)
            self._context_persistence.update_context(workflow_context)

            return WorkflowResult(
                success=False,
                context_id=workflow_context.id,
                error=str(e),
                ...
            )

        finally:
            # Clear thread-local context
            set_workflow_context(None)
```

**File:** `gao_dev/orchestrator/workflow_results.py`

Add context_id to WorkflowResult:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class WorkflowResult:
    """Result of workflow execution."""

    success: bool
    context_id: Optional[str] = None  # NEW: Link to WorkflowContext
    artifacts: List[Dict] = None
    decisions: List[Dict] = None
    error: Optional[str] = None
    metadata: Dict = None
```

**Files to Modify:**
- `gao_dev/orchestrator/orchestrator.py` - Add context creation and management
- `gao_dev/orchestrator/workflow_results.py` - Add context_id field
- `gao_dev/core/context/agent_context_api.py` - Ensure thread-local storage works

**Files to Create:**
- `tests/orchestrator/test_context_integration.py` - Integration tests
- `tests/orchestrator/test_workflow_context_lifecycle.py` - Lifecycle tests

**Dependencies:**
- Story 17.1 (Document Loading)
- Story 17.2 (Database Unification)
- Story 16.2 (WorkflowContext)
- Story 16.3 (ContextPersistence)

---

## Testing Requirements

### Integration Tests

**Context Creation:**
- [ ] Test workflow creates WorkflowContext at start
- [ ] Test context persisted to database
- [ ] Test context includes workflow metadata
- [ ] Test context_id included in WorkflowResult

**Context Updates:**
- [ ] Test context updated after phase transitions
- [ ] Test decisions recorded in context
- [ ] Test artifacts recorded in context
- [ ] Test document access tracked

**Context Finalization:**
- [ ] Test completed workflow marks context as 'completed'
- [ ] Test failed workflow marks context as 'failed'
- [ ] Test context includes final metadata

**Thread-Local Access:**
- [ ] Test agents can access context via get_workflow_context()
- [ ] Test context isolated per workflow execution
- [ ] Test concurrent workflows have separate contexts
- [ ] Test context cleared after workflow completion

**Workflow Result:**
- [ ] Test WorkflowResult includes context_id
- [ ] Test context_id can query full context from DB
- [ ] Test WorkflowResult serialization includes context_id

### End-to-End Tests
- [ ] Test full workflow with context tracking (create PRD)
- [ ] Test full workflow with context tracking (implement story)
- [ ] Test benchmark workflow shows context in action
- [ ] Test workflow failure captures context

### Unit Tests
- [ ] Test WorkflowContext creation with orchestrator metadata
- [ ] Test set_workflow_context() stores in thread-local
- [ ] Test get_workflow_context() retrieves from thread-local
- [ ] Test context cleared on workflow completion

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Update orchestrator documentation with context tracking
- [ ] Document WorkflowContext lifecycle (creation, updates, finalization)
- [ ] Add examples of accessing context in agents
- [ ] Document WorkflowResult.context_id usage
- [ ] Add troubleshooting guide for context issues
- [ ] Document thread-local storage behavior
- [ ] Add sequence diagram showing context lifecycle
- [ ] Document context metadata fields

---

## Implementation Details

### Development Approach

**Phase 1: Basic Integration**
1. Add ContextPersistence to orchestrator __init__
2. Create WorkflowContext at workflow start
3. Persist context to database
4. Add context_id to WorkflowResult

**Phase 2: Lifecycle Management**
1. Update context after phase transitions
2. Record decisions in context
3. Record artifacts in context
4. Mark context as completed/failed

**Phase 3: Thread-Local Access**
1. Call set_workflow_context() at start
2. Clear context on completion
3. Test agent access via get_workflow_context()

**Phase 4: Testing**
1. Write integration tests for full lifecycle
2. Test concurrent workflow isolation
3. Test failure handling
4. Verify benchmark workflows work

### Quality Gates
- [ ] All integration tests pass
- [ ] Context created automatically for all workflows
- [ ] Context persisted correctly (no data loss)
- [ ] Thread-local access working (agents can access)
- [ ] WorkflowResult includes context_id
- [ ] Documentation updated with examples
- [ ] No regression in existing workflows

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Orchestrator creates WorkflowContext at workflow start
- [ ] Context persisted to database at initialization
- [ ] Context updated after each phase transition
- [ ] Decisions and artifacts recorded in context
- [ ] Failed workflows mark context as 'failed'
- [ ] Completed workflows mark context as 'completed'
- [ ] WorkflowResult includes context_id field
- [ ] Thread-local storage working (set/get_workflow_context)
- [ ] Integration tests pass (>80% coverage)
- [ ] Benchmark workflows show context tracking
- [ ] Concurrent workflows have isolated contexts
- [ ] Code reviewed and approved
- [ ] Documentation updated with lifecycle details
- [ ] No regression in existing functionality
- [ ] Committed with atomic commit message:
  ```
  feat(epic-17): implement Story 17.3 - Orchestrator Integration

  - Wire WorkflowContext into GAODevOrchestrator lifecycle
  - Create WorkflowContext automatically at workflow start
  - Persist context to database at initialization
  - Update context after each phase transition
  - Record decisions and artifacts in context
  - Mark context as completed/failed at workflow end
  - Add context_id to WorkflowResult for traceability
  - Implement thread-local storage (set/get_workflow_context)
  - Add integration tests for full context lifecycle
  - Test concurrent workflow context isolation

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
