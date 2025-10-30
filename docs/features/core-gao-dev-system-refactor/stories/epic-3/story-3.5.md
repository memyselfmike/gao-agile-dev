# Story 3.5: Implement Dependency Injection

**Epic**: Epic 3
**Story Points**: 3
**Status**: Done

Demonstrated Dependency Injection pattern in AgentFactory and WorkflowStrategyRegistry.

## Implementation
- AgentFactory accepts agents_dir via constructor
- WorkflowStrategyRegistry accepts strategies via register_strategy
- BrianOrchestrator accepts workflow_registry and strategy_registry
- Pattern demonstrated throughout Epic 3 implementations
