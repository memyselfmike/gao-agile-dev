"""
Core interfaces for GAO-Dev.

This module exports all core interfaces used throughout GAO-Dev.
These interfaces define contracts for agents, workflows, repositories,
event handling, methodologies, and orchestration.

All implementations (built-in and plugins) must conform to these interfaces.

Example:
    ```python
    from gao_dev.core.interfaces import IAgent, IWorkflow, IRepository

    class MyCustomAgent(IAgent):
        # Implementation
        pass
    ```
"""

# Agent interfaces
from .agent import (
    IAgent,
    IAgentFactory,
)

# Workflow interfaces
from .workflow import (
    IWorkflow,
    IWorkflowRegistry,
)

# Repository interfaces
from .repository import (
    IRepository,
    IStoryRepository,
    IProjectRepository,
)

# Event bus interfaces
from .event_bus import (
    IEventBus,
    IEventHandler,
)

# Methodology interfaces
from .methodology import (
    IMethodology,
    IMethodologyRegistry,
)

# Orchestrator interface
from .orchestrator import (
    IOrchestrator,
)

# Plugin interfaces
from .plugin import (
    IPluginDiscovery,
    IPluginLoader,
    IPluginRegistry,
)

__all__ = [
    # Agent
    "IAgent",
    "IAgentFactory",
    # Workflow
    "IWorkflow",
    "IWorkflowRegistry",
    # Repository
    "IRepository",
    "IStoryRepository",
    "IProjectRepository",
    # Event Bus
    "IEventBus",
    "IEventHandler",
    # Methodology
    "IMethodology",
    "IMethodologyRegistry",
    # Orchestrator
    "IOrchestrator",
    # Plugin
    "IPluginDiscovery",
    "IPluginLoader",
    "IPluginRegistry",
]
