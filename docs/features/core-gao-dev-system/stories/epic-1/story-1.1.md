# Story 1.1: Define Core Interfaces

**Epic**: Epic 1 - Foundation
**Story Points**: 5
**Priority**: P0 (Critical)
**Status**: Draft

---

## User Story

**As a** core developer
**I want** clearly defined interfaces for all major components
**So that** we can implement components independently and enable dependency injection

---

## Description

Create comprehensive interface definitions for all core GAO-Dev components. These interfaces will serve as contracts that all implementations must follow, enabling dependency injection, testing with mocks, and future plugin development.

This story establishes the foundational contracts for the entire refactoring effort.

---

## Acceptance Criteria

### Core Interfaces Defined

- [ ] **IAgent interface** created in `gao_dev/core/interfaces/agent.py`
  - Properties: name, role
  - Methods: execute_task(), get_capabilities(), can_handle_task()
  - Comprehensive docstrings with parameter/return types

- [ ] **IAgentFactory interface** created in `gao_dev/core/interfaces/agent.py`
  - Method: create_agent(agent_type, config) → IAgent
  - Method: register_agent_class(agent_type, agent_class)

- [ ] **IWorkflow interface** created in `gao_dev/core/interfaces/workflow.py`
  - Properties: identifier, required_tools
  - Methods: execute(context), validate_context(context)

- [ ] **IWorkflowRegistry interface** created in `gao_dev/core/interfaces/workflow.py`
  - Methods: get_workflow(name), list_workflows(phase), workflow_exists(name)
  - Method: register_workflow(workflow)

- [ ] **IRepository interface** created in `gao_dev/core/interfaces/repository.py`
  - Generic type: IRepository[T]
  - Methods: find_by_id(id), find_all(), save(entity), delete(id)
  - Async methods throughout

- [ ] **IStoryRepository interface** created in `gao_dev/core/interfaces/repository.py`
  - Extends: IRepository[Story]
  - Methods: find_by_epic(epic), find_by_status(status)

- [ ] **IProjectRepository interface** created in `gao_dev/core/interfaces/repository.py`
  - Extends: IRepository[Project]
  - Methods: find_by_tags(tags), find_active()

- [ ] **IEventBus interface** created in `gao_dev/core/interfaces/event_bus.py`
  - Methods: publish(event), subscribe(event_type, handler), unsubscribe()

- [ ] **IEventHandler interface** created in `gao_dev/core/interfaces/event_bus.py`
  - Method: handle(event) → None (async)

- [ ] **IMethodology interface** created in `gao_dev/core/interfaces/methodology.py`
  - Properties: name
  - Methods: assess_complexity(prompt), build_workflow_sequence(assessment)
  - Method: get_recommended_agents(assessment)

- [ ] **IOrchestrator interface** created in `gao_dev/core/interfaces/orchestrator.py`
  - Methods: execute_workflow(), execute_story_workflow(), execute_epic_workflow()

### Documentation

- [ ] All interfaces have comprehensive docstrings
- [ ] Each method has parameter and return type documentation
- [ ] Example usage provided for each interface
- [ ] Interface design rationale documented

### Code Quality

- [ ] All interfaces use ABC (Abstract Base Class)
- [ ] All interface methods marked with @abstractmethod
- [ ] Type hints for all parameters and return values
- [ ] No implementation code in interfaces (pure contracts)

### File Structure

- [ ] Directory created: `gao_dev/core/interfaces/`
- [ ] File created: `__init__.py` (exports all interfaces)
- [ ] File created: `agent.py` (IAgent, IAgentFactory)
- [ ] File created: `workflow.py` (IWorkflow, IWorkflowRegistry)
- [ ] File created: `repository.py` (IRepository, IStoryRepository, IProjectRepository)
- [ ] File created: `event_bus.py` (IEventBus, IEventHandler)
- [ ] File created: `methodology.py` (IMethodology)
- [ ] File created: `orchestrator.py` (IOrchestrator)

---

## Technical Details

### Interface Design Principles

1. **Interface Segregation**: Each interface focused on one aspect
2. **Dependency Inversion**: Depend on interfaces, not implementations
3. **Liskov Substitution**: All implementations must be substitutable
4. **Generic Types**: Use TypeVar for generic repositories
5. **Async Throughout**: All I/O operations are async

### Example Interface (IAgent)

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List
from ..models.agent import AgentCapability, AgentContext

class IAgent(ABC):
    """
    Interface for all GAO-Dev agents (built-in and plugins).

    An agent is a specialized AI entity with specific capabilities
    and responsibilities (e.g., Product Manager, Developer, QA).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Agent's unique name.

        Returns:
            str: Agent name (e.g., "Mary", "John")
        """
        pass

    @property
    @abstractmethod
    def role(self) -> str:
        """
        Agent's role/specialty.

        Returns:
            str: Role description (e.g., "Business Analyst", "Developer")
        """
        pass

    @abstractmethod
    async def execute_task(
        self,
        task: str,
        context: AgentContext
    ) -> AsyncGenerator[str, None]:
        """
        Execute a task and yield progress messages.

        Args:
            task: Task description in natural language
            context: Execution context (project, tools, etc.)

        Yields:
            str: Progress messages during execution

        Raises:
            AgentExecutionError: If task execution fails
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """
        Get list of agent capabilities.

        Returns:
            List of capabilities this agent possesses
        """
        pass

    @abstractmethod
    def can_handle_task(self, task: str) -> bool:
        """
        Check if agent can handle given task.

        Args:
            task: Task description

        Returns:
            bool: True if agent can handle this task
        """
        pass
```

### Dependencies

- Python 3.11+ (for typing features)
- `abc` module (Abstract Base Classes)
- `typing` module (type hints)

---

## Implementation Notes

### Implementation Order

1. Create directory structure
2. Implement IRepository (simplest, generic)
3. Implement IAgent and IAgentFactory
4. Implement IWorkflow and IWorkflowRegistry
5. Implement IEventBus and IEventHandler
6. Implement IMethodology
7. Implement IOrchestrator
8. Create __init__.py with exports

### Testing Strategy

- No unit tests yet (interfaces have no implementation)
- Mock implementations in Story 1.5 (Testing Infrastructure)
- Interface validation: All methods have @abstractmethod decorator

### Documentation Strategy

- Docstring for every interface
- Docstring for every method
- Example usage in module docstring
- Link to architecture document

---

## Testing

### Validation Tests

- [ ] All interfaces can be imported from `gao_dev.core.interfaces`
- [ ] All interfaces inherit from ABC
- [ ] All methods have @abstractmethod decorator
- [ ] All type hints are valid (mypy passes)
- [ ] Documentation builds without errors

---

## Dependencies

### Depends On

- None (foundational story)

### Blocks

- Story 1.3: Implement Base Agent Class (needs IAgent)
- Story 1.4: Implement Base Workflow Class (needs IWorkflow)
- Story 1.5: Set Up Testing Infrastructure (needs all interfaces for mocks)
- All of Epic 2 (God Class Refactoring needs interfaces)

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All interfaces defined in correct files
- [ ] All interfaces documented with docstrings
- [ ] Type hints complete (mypy passes strict mode)
- [ ] Code review approved
- [ ] Merged to feature branch
- [ ] Architecture document updated with interface descriptions

---

## Notes

- Keep interfaces minimal (Interface Segregation Principle)
- Interfaces should be stable (changing them is expensive later)
- Think carefully about async vs sync methods
- Consider future extensibility when designing interfaces

---

## Related

- **Epic**: Epic 1 - Foundation
- **PRD**: Core System Refactoring PRD
- **Architecture**: ARCHITECTURE.md - Component Design section
- **Next Story**: Story 1.2 - Create Value Objects
