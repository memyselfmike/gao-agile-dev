# Story 1.3: Implement Base Agent Class

**Epic**: Epic 1 - Foundation
**Story Points**: 5
**Priority**: P0 (Critical)
**Status**: Draft

---

## User Story

**As a** core developer
**I want** a base agent class with common functionality
**So that** all agents (built-in and plugins) have consistent behavior and lifecycle

---

## Description

Implement `BaseAgent` abstract class that provides common agent functionality and enforces the IAgent interface. This class will be the parent for all agent implementations, including specialized bases like `PlanningAgent` and `ImplementationAgent`.

---

## Acceptance Criteria

### Base Agent Implementation

- [ ] **BaseAgent** class created in `gao_dev/agents/base.py`
  - Implements IAgent interface
  - Properties: name, role, persona, tools
  - Lifecycle methods: initialize(), cleanup()
  - Context management: __aenter__, __aexit__
  - Abstract method: execute_task() (subclasses must implement)

- [ ] **PlanningAgent** class created (inherits BaseAgent)
  - Base for planning-focused agents (Mary, John, Winston, Sally)
  - Common planning workflow helpers
  - Document creation utilities

- [ ] **ImplementationAgent** class created (inherits BaseAgent)
  - Base for implementation-focused agents (Amelia, Murat, Bob)
  - Common implementation workflow helpers
  - Code/test execution utilities

### Agent Lifecycle

- [ ] **initialize()** method: Set up agent resources
- [ ] **cleanup()** method: Clean up agent resources
- [ ] **Context manager support**: Async with BaseAgent() as agent
- [ ] **Proper error handling**: AgentExecutionError for failures

### Testing

- [ ] BaseAgent tests (with concrete test implementation)
- [ ] PlanningAgent tests
- [ ] ImplementationAgent tests
- [ ] Lifecycle tests (initialize, cleanup, context manager)
- [ ] Error handling tests

---

## Technical Details

### BaseAgent Implementation

```python
from abc import abstractmethod
from typing import List, AsyncGenerator, Optional
from ..core.interfaces.agent import IAgent
from ..core.models.agent import AgentCapability, AgentContext

class BaseAgent(IAgent):
    """
    Base implementation for all GAO-Dev agents.

    Provides common functionality and enforces consistent behavior
    across all agent implementations.
    """

    def __init__(
        self,
        name: str,
        role: str,
        persona: str,
        tools: List[str],
        model: str = "claude-sonnet-4-5-20250929"
    ):
        self._name = name
        self._role = role
        self._persona = persona
        self._tools = tools
        self._model = model
        self._initialized = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def role(self) -> str:
        return self._role

    async def initialize(self) -> None:
        """Initialize agent resources."""
        if self._initialized:
            return
        # Subclasses can override to add initialization
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        # Subclasses can override to add cleanup
        self._initialized = False

    async def __aenter__(self):
        """Context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.cleanup()
        return False

    @abstractmethod
    async def execute_task(
        self,
        task: str,
        context: AgentContext
    ) -> AsyncGenerator[str, None]:
        """Execute task (subclasses must implement)."""
        pass

    def get_capabilities(self) -> List[AgentCapability]:
        """Get agent capabilities (override in subclasses)."""
        return []

    def can_handle_task(self, task: str) -> bool:
        """Check if agent can handle task (override in subclasses)."""
        return True  # Default: can handle any task
```

---

## Dependencies

- Story 1.1: Define Core Interfaces (IAgent needed)
- Story 1.2: Create Value Objects (AgentCapability needed)

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] 80%+ test coverage
- [ ] All tests passing
- [ ] Type hints complete
- [ ] Documentation complete
- [ ] Code review approved
- [ ] Merged to feature branch

---

## Related

- **Epic**: Epic 1 - Foundation
- **Previous Story**: Story 1.2 - Create Value Objects
- **Next Story**: Story 1.4 - Implement Base Workflow Class
