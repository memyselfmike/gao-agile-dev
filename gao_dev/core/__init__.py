"""Core services and interfaces for GAO-Dev."""

# Legacy models (from legacy_models.py - for backward compatibility)
from .legacy_models import (
    WorkflowInfo,
    StoryStatus as LegacyStoryStatus,  # Renamed to avoid conflict
    HealthStatus,
    CheckResult,
    HealthCheckResult,
    AgentInfo,
)

# Core services
from .config_loader import ConfigLoader
from .workflow_registry import WorkflowRegistry
from .workflow_executor import WorkflowExecutor
from .state_manager import StateManager
from .git_manager import GitManager
from .health_check import HealthCheck
from .hook_manager import HookManager

# New interfaces (Epic 1 - Foundation)
from .interfaces import (
    IAgent,
    IAgentFactory,
    IWorkflow,
    IWorkflowRegistry,
    IRepository,
    IStoryRepository,
    IProjectRepository,
    IEventBus,
    IEventHandler,
    IMethodology,
    IMethodologyRegistry,
    IOrchestrator,
)

# New value objects (Epic 1 - Foundation)
from .models import (
    StoryIdentifier,
    StoryStatus,  # New StoryStatus from models/
    ProjectPath,
    ProjectStatus,
    WorkflowIdentifier,
    ComplexityLevel,
    AgentCapability,
    AgentCapabilityType,
    CommonCapabilities,
    Story,
    Project,
    WorkflowContext,
    WorkflowResult,
    WorkflowSequence,
    AgentContext,
    AgentConfig,
    HookEventType,
    HookHandler,
    HookInfo,
    HookResults,
)

__all__ = [
    # Legacy models (for backward compatibility)
    "WorkflowInfo",
    "LegacyStoryStatus",
    "HealthStatus",
    "CheckResult",
    "HealthCheckResult",
    "AgentInfo",
    # Services
    "ConfigLoader",
    "WorkflowRegistry",
    "WorkflowExecutor",
    "StateManager",
    "GitManager",
    "HealthCheck",
    "HookManager",
    # Interfaces
    "IAgent",
    "IAgentFactory",
    "IWorkflow",
    "IWorkflowRegistry",
    "IRepository",
    "IStoryRepository",
    "IProjectRepository",
    "IEventBus",
    "IEventHandler",
    "IMethodology",
    "IMethodologyRegistry",
    "IOrchestrator",
    # Value Objects
    "StoryIdentifier",
    "StoryStatus",
    "ProjectPath",
    "ProjectStatus",
    "WorkflowIdentifier",
    "ComplexityLevel",
    "AgentCapability",
    "AgentCapabilityType",
    "CommonCapabilities",
    "Story",
    "Project",
    "WorkflowContext",
    "WorkflowResult",
    "WorkflowSequence",
    "AgentContext",
    "AgentConfig",
    # Hook System
    "HookEventType",
    "HookHandler",
    "HookInfo",
    "HookResults",
]
