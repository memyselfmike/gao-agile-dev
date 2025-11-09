# Story 22.3: Extract AgentCoordinator

**Epic**: Epic 22 - Orchestrator Decomposition & Architectural Refactoring
**Story ID**: 22.3
**Priority**: P0
**Estimate**: 6 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Extract agent lifecycle management and coordination logic from the GAODevOrchestrator into a dedicated AgentCoordinator service. This service will handle agent task execution, agent-workflow mapping, and agent lifecycle management.

The AgentCoordinator reduces the orchestrator's complexity by centralizing all agent-related operations into a focused service with clear responsibilities.

---

## Acceptance Criteria

- [ ] Create `AgentCoordinator` service (~180 LOC)
- [ ] Move agent task execution logic (~135 LOC)
- [ ] Move agent-workflow mapping logic (~35 LOC)
- [ ] Orchestrator delegates to coordinator
- [ ] All agent coordination tests pass
- [ ] 10 unit tests for coordinator
- [ ] Zero breaking changes

---

## Technical Approach

### Implementation Details

The AgentCoordinator encapsulates all agent lifecycle operations including task execution via agents, agent selection for workflows, and agent state management.

**Key Responsibilities**:
1. Execute tasks via appropriate agents
2. Map workflows to correct agents
3. Manage agent lifecycle (creation, caching)
4. Coordinate agent-specific context
5. Handle agent errors and retries

**Design Pattern**: Service pattern with agent factory integration

### Files to Modify

- `gao_dev/orchestrator/agent_coordinator.py` (+180 LOC / NEW)
  - Add: AgentCoordinator class
  - Add: execute_task() method
  - Add: get_agent() method
  - Add: Agent caching logic
  - Add: Error handling

- `gao_dev/orchestrator/orchestrator.py` (-170 LOC / +20 delegation)
  - Remove: _execute_agent_task_static() (~135 LOC)
  - Remove: _get_agent_for_workflow() (~35 LOC)
  - Add: Delegate to agent_coordinator
  - Add: agent_coordinator initialization

### New Files to Create

- `gao_dev/orchestrator/agent_coordinator.py` (~180 LOC)
  - Purpose: Coordinate agent operations
  - Key components:
    - AgentCoordinator class
    - execute_task(agent_name, instructions, context) -> Response
    - get_agent(workflow_name) -> str (agent name)
    - _create_agent() helper
    - _agent_cache management

- `tests/orchestrator/test_agent_coordinator.py` (~150 LOC)
  - Purpose: Unit tests for agent coordinator
  - Key components:
    - 10 unit tests
    - Mock AgentFactory
    - Test agent task execution
    - Test agent selection
    - Test error handling
    - Test agent caching

---

## Testing Strategy

### Unit Tests (10 tests)

- test_execute_task_success() - Test successful task execution
- test_execute_task_with_context() - Test context passing
- test_execute_task_error_handling() - Test agent failures
- test_get_agent_for_workflow_prd() - Test PRD workflow → John
- test_get_agent_for_workflow_story() - Test story workflow → Bob
- test_get_agent_for_workflow_implementation() - Test implementation → Amelia
- test_agent_caching() - Test agent instance reuse
- test_agent_creation() - Test agent factory integration
- test_coordinator_initialization() - Test constructor
- test_multiple_agent_execution() - Test sequential agent calls

**Total Tests**: 10 tests
**Test File**: `tests/orchestrator/test_agent_coordinator.py`

---

## Dependencies

**Upstream**: Story 22.1, Story 22.2

**Downstream**: Story 22.6 (Orchestrator facade needs coordinator)

---

## Implementation Notes

### Current Methods to Extract

```python
# From gao_dev/orchestrator/orchestrator.py

@staticmethod
def _execute_agent_task_static(
    agent: BaseAgent,
    instructions: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Execute task via agent."""
    # ~135 LOC
    # Prepare agent context
    # Execute via agent
    # Handle errors
    # Return response

def _get_agent_for_workflow(self, workflow_name: str) -> str:
    """Get agent name for workflow."""
    # ~35 LOC
    # Map workflow to agent
    # Return agent name
```

### New Service Structure

```python
# gao_dev/orchestrator/agent_coordinator.py

class AgentCoordinator:
    """Service for coordinating agent operations."""

    def __init__(
        self,
        agent_factory: AgentFactory,
        config: ConfigLoader
    ):
        self.factory = agent_factory
        self.config = config
        self._agent_cache: Dict[str, BaseAgent] = {}

    def execute_task(
        self,
        agent_name: str,
        instructions: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute task via named agent."""
        # Get or create agent
        # Execute instructions
        # Return response

    def get_agent(self, workflow_name: str) -> str:
        """Get agent name for workflow."""
        # Map workflow to agent
        # Return agent name

    def _create_agent(self, agent_name: str) -> BaseAgent:
        """Create agent instance via factory."""
        # Use factory to create
        # Cache if needed
        # Return agent
```

### Agent-Workflow Mapping

The coordinator maintains workflow-to-agent mapping:

**PRD Workflows** → John (Product Manager)
**Architecture Workflows** → Winston (Technical Architect)
**Story Workflows** → Bob (Scrum Master)
**Implementation Workflows** → Amelia (Developer)
**Test Workflows** → Murat (Test Architect)
**UX Workflows** → Sally (UX Designer)
**Brian Workflows** → Brian (Workflow Coordinator)

### Agent Caching Strategy

- Cache agents after first creation
- Reuse cached agents for subsequent calls
- Clear cache on error or explicit request
- Configurable cache size limit

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (10/10 unit tests)
- [ ] Code coverage >80% for new service
- [ ] Code review completed
- [ ] Documentation updated (docstrings)
- [ ] No breaking changes
- [ ] Git commit created
- [ ] Service <200 LOC (target: ~180 LOC)
- [ ] MyPy strict mode passes

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09
