# Story 3.2: Implement Strategy Pattern for Workflows

**Epic**: Epic 3 - Design Pattern Implementation
**Story Points**: 8
**Priority**: P1 (High)
**Status**: Draft

---

## User Story

**As a** core developer
**I want** workflow building logic to use the Strategy Pattern
**So that** different workflow types can be handled polymorphically without if/else chains

---

## Description

Implement the Strategy Pattern for workflow building by creating workflow strategy classes that encapsulate different workflow building logic. This replaces hard-coded if/else chains with polymorphic strategies that can be selected based on scale level, project type, and workflow type.

**Current State**: Workflow selection uses if/else chains in orchestrator and BrianOrchestrator with hard-coded logic for different workflow types.

**Target State**: New strategy classes in `gao_dev/core/strategies/` that handle workflow building polymorphically.

---

## Acceptance Criteria

### Strategy Interface

- [ ] **Interface created**: `IWorkflowBuildStrategy` in `gao_dev/core/interfaces/workflow.py`
- [ ] **Methods defined**:
  - `can_handle(context)` → bool (determine if strategy can handle this context)
  - `build_workflow_sequence(context)` → WorkflowSequence (build the workflow sequence)
  - `get_priority()` → int (for strategy selection when multiple match)

### Concrete Strategy Implementations

- [ ] **ScaleLevelStrategy**: Selects workflows based on scale level (0-4)
  - Level 0: Chore workflow
  - Level 1: Bug fix workflow
  - Level 2: Small feature workflow (3-8 stories)
  - Level 3: Medium feature workflow (12-20 stories)
  - Level 4: Greenfield application workflow (40+ stories)

- [ ] **ProjectTypeStrategy**: Selects workflows based on project type
  - Software projects: dev-story, create-story workflows
  - Documentation projects: doc workflows
  - Infrastructure projects: infra workflows

- [ ] **CustomWorkflowStrategy**: Handles explicit workflow sequences
  - When user specifies exact workflows to run

### Strategy Registry

- [ ] **Class created**: `WorkflowStrategyRegistry` in `gao_dev/core/strategies/workflow_strategy.py`
- [ ] **Methods**:
  - `register_strategy(strategy)` → None
  - `get_strategy(context)` → IWorkflowBuildStrategy
  - `list_strategies()` → List[str]

### Integration with Brian Orchestrator

- [ ] **BrianOrchestrator refactored**:
  - Uses WorkflowStrategyRegistry instead of if/else chains
  - Delegates workflow selection to strategies
  - Falls back to default strategy if none match

### Testing

- [ ] Unit tests for each strategy (80%+ coverage)
- [ ] Unit tests for strategy registry
- [ ] Integration tests with BrianOrchestrator
- [ ] All existing tests still pass

---

## Technical Details

### Strategy Interface

```python
class IWorkflowBuildStrategy(ABC):
    """
    Strategy interface for building workflow sequences.

    Implementations encapsulate different workflow building logic
    based on scale level, project type, or other criteria.
    """

    @abstractmethod
    def can_handle(self, context: WorkflowContext) -> bool:
        """
        Check if this strategy can handle the given context.

        Args:
            context: Workflow execution context

        Returns:
            bool: True if strategy can handle this context
        """
        pass

    @abstractmethod
    def build_workflow_sequence(
        self,
        context: WorkflowContext
    ) -> WorkflowSequence:
        """
        Build workflow sequence for the given context.

        Args:
            context: Workflow execution context

        Returns:
            WorkflowSequence: Sequence of workflows to execute
        """
        pass

    @abstractmethod
    def get_priority(self) -> int:
        """
        Get strategy priority for selection.

        Higher priority strategies are preferred when multiple
        strategies can handle the same context.

        Returns:
            int: Priority (higher is better)
        """
        pass
```

### Concrete Strategy Example

```python
class ScaleLevelStrategy(IWorkflowBuildStrategy):
    """
    Strategy that selects workflows based on scale level.

    Scale levels:
    - 0: Chore (update docs, fix typo)
    - 1: Bug fix (single file change)
    - 2: Small feature (3-8 stories)
    - 3: Medium feature (12-20 stories)
    - 4: Greenfield application (40+ stories)
    """

    def __init__(self, workflow_registry: IWorkflowRegistry):
        self.workflow_registry = workflow_registry
        self._workflow_map = {
            ScaleLevel.CHORE: ["quick-fix"],
            ScaleLevel.BUG_FIX: ["bug-fix-workflow"],
            ScaleLevel.SMALL_FEATURE: ["create-prd", "create-story", "dev-story"],
            ScaleLevel.MEDIUM_FEATURE: ["create-prd", "create-architecture", "create-story", "dev-story"],
            ScaleLevel.GREENFIELD: ["create-prd", "create-architecture", "create-epic", "create-story", "dev-story"]
        }

    def can_handle(self, context: WorkflowContext) -> bool:
        """Check if context has scale level."""
        return hasattr(context, 'scale_level') and context.scale_level is not None

    def build_workflow_sequence(self, context: WorkflowContext) -> WorkflowSequence:
        """Build workflow sequence based on scale level."""
        scale_level = context.scale_level
        workflow_names = self._workflow_map.get(scale_level, [])

        workflows = []
        for name in workflow_names:
            workflow_info = self.workflow_registry.get_workflow(name)
            if workflow_info:
                workflows.append(workflow_info)

        return WorkflowSequence(
            workflows=workflows,
            scale_level=scale_level,
            metadata={"strategy": "scale_level"}
        )

    def get_priority(self) -> int:
        """Scale level strategy has medium priority."""
        return 50
```

### Strategy Registry

```python
class WorkflowStrategyRegistry:
    """
    Registry for workflow build strategies.

    Manages strategy registration and selection based on context.
    """

    def __init__(self):
        self._strategies: List[IWorkflowBuildStrategy] = []

    def register_strategy(self, strategy: IWorkflowBuildStrategy) -> None:
        """Register a workflow build strategy."""
        if not isinstance(strategy, IWorkflowBuildStrategy):
            raise ValueError("Strategy must implement IWorkflowBuildStrategy")

        self._strategies.append(strategy)
        # Sort by priority (highest first)
        self._strategies.sort(key=lambda s: s.get_priority(), reverse=True)

    def get_strategy(self, context: WorkflowContext) -> Optional[IWorkflowBuildStrategy]:
        """
        Get the best strategy for the given context.

        Returns the highest priority strategy that can handle the context.
        """
        for strategy in self._strategies:
            if strategy.can_handle(context):
                return strategy
        return None

    def list_strategies(self) -> List[str]:
        """List all registered strategies."""
        return [strategy.__class__.__name__ for strategy in self._strategies]
```

### Refactor BrianOrchestrator

```python
class BrianOrchestrator:
    def __init__(
        self,
        workflow_registry: IWorkflowRegistry,
        api_key: Optional[str] = None,
        brian_persona_path: Optional[Path] = None,
        strategy_registry: Optional[WorkflowStrategyRegistry] = None
    ):
        self.workflow_registry = workflow_registry

        # Initialize strategy registry
        if strategy_registry is None:
            strategy_registry = WorkflowStrategyRegistry()
            # Register default strategies
            strategy_registry.register_strategy(
                ScaleLevelStrategy(workflow_registry)
            )
            strategy_registry.register_strategy(
                ProjectTypeStrategy(workflow_registry)
            )
            strategy_registry.register_strategy(
                CustomWorkflowStrategy(workflow_registry)
            )

        self.strategy_registry = strategy_registry

    async def select_workflows(
        self,
        initial_prompt: str,
        project_type: ProjectType,
        scale_level: Optional[ScaleLevel] = None
    ) -> WorkflowSequence:
        """Select workflows using strategy pattern."""

        # Build context
        context = WorkflowContext(
            initial_prompt=initial_prompt,
            project_type=project_type,
            scale_level=scale_level
        )

        # Get strategy
        strategy = self.strategy_registry.get_strategy(context)

        if strategy is None:
            raise ValueError("No strategy can handle this context")

        # Build workflow sequence using strategy
        return strategy.build_workflow_sequence(context)
```

---

## Dependencies

- **Depends On**:
  - Story 3.1 (AgentFactory for agent creation)
  - Epic 1 (interfaces defined)

- **Blocks**:
  - Story 3.5 (Dependency injection needs strategies)
  - Epic 4 (Plugin workflows need strategy pattern)

---

## Definition of Done

- [ ] IWorkflowBuildStrategy interface defined
- [ ] 3 concrete strategies implemented (ScaleLevel, ProjectType, Custom)
- [ ] WorkflowStrategyRegistry implemented
- [ ] BrianOrchestrator refactored to use strategies
- [ ] No if/else chains for workflow selection remaining
- [ ] 80%+ test coverage for strategies
- [ ] All existing tests pass (100%)
- [ ] Integration tests demonstrate strategy selection
- [ ] Code review approved
- [ ] Merged to feature branch
- [ ] Documentation updated

---

## Files to Create

1. `gao_dev/core/strategies/__init__.py`
2. `gao_dev/core/strategies/workflow_strategy.py` (ScaleLevelStrategy, ProjectTypeStrategy, CustomWorkflowStrategy)
3. `gao_dev/core/strategies/workflow_registry.py` (WorkflowStrategyRegistry)
4. `gao_dev/core/models/workflow_context.py` (WorkflowContext model)
5. `tests/core/strategies/__init__.py`
6. `tests/core/strategies/test_workflow_strategies.py`
7. `tests/core/strategies/test_strategy_registry.py`
8. `tests/integration/test_workflow_strategy_integration.py`

---

## Files to Modify

1. `gao_dev/core/interfaces/workflow.py` - Add IWorkflowBuildStrategy
2. `gao_dev/orchestrator/brian_orchestrator.py` - Refactor to use strategies
3. Update existing workflow selection logic

---

## Related

- **Epic**: Epic 3 - Design Pattern Implementation
- **Previous Story**: Story 3.1 - Factory Pattern for Agents
- **Next Story**: Story 3.3 - Repository Pattern for Persistence
