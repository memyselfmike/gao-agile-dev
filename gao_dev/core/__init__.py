"""Core services and interfaces for GAO-Dev."""

# Health models (from health_check.py - no longer in legacy_models.py)
from .health_check import (
    HealthStatus,
    CheckResult,
    HealthCheckResult,
)

# Core services
from .config_loader import ConfigLoader
from .workflow_registry import WorkflowRegistry
from .workflow_executor import WorkflowExecutor
from .state_manager import StateManager
from .git_manager import GitManager
from .health_check import HealthCheck
from .hook_manager import HookManager
from .version_manager import VersionManager, CompatibilityResult

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
    WorkflowInfo,  # Migrated from legacy_models.py
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
    # Migrated models (from legacy_models.py)
    "WorkflowInfo",
    "HealthStatus",
    "CheckResult",
    "HealthCheckResult",
    # Services
    "ConfigLoader",
    "WorkflowRegistry",
    "WorkflowExecutor",
    "StateManager",
    "GitManager",
    "HealthCheck",
    "HookManager",
    "VersionManager",
    "CompatibilityResult",
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
    "WorkflowInfo",
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
