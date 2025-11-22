"""Hook system models for plugin extension points.

This module provides data models for the hook system, which allows plugins
to register callbacks for lifecycle events throughout GAO-Dev.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol


class HookEventType(Enum):
    """Lifecycle event types that plugins can hook into.

    These events are fired at specific points during workflow, agent,
    plugin, and system lifecycle, allowing plugins to extend functionality.
    """

    # Workflow lifecycle events
    WORKFLOW_START = "workflow.start"
    WORKFLOW_END = "workflow.end"
    WORKFLOW_ERROR = "workflow.error"

    # Agent lifecycle events
    AGENT_CREATED = "agent.created"
    AGENT_EXECUTE_START = "agent.execute.start"
    AGENT_EXECUTE_END = "agent.execute.end"

    # Plugin lifecycle events
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_UNLOADED = "plugin.unloaded"
    PLUGIN_ERROR = "plugin.error"

    # System lifecycle events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"


class HookHandler(Protocol):
    """Protocol for hook handler functions.

    Hook handlers can be synchronous or asynchronous functions that accept
    event data and optionally return a result. The result can be used by
    subsequent hooks or logged for debugging.

    Example:
        def my_hook_handler(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            workflow_id = event_data.get("workflow_id")
            print(f"Workflow {workflow_id} started")
            return {"processed": True}

    Example (async):
        async def my_async_hook(event_data: Dict[str, Any]) -> None:
            await some_async_operation(event_data)
    """

    def __call__(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute hook handler with event data.

        Args:
            event_data: Dictionary containing event-specific data

        Returns:
            Optional dictionary with results (can be None)
        """
        ...


@dataclass
class HookInfo:
    """Information about a registered hook.

    Stores metadata about a hook handler including its event type,
    priority, and origin plugin.

    Attributes:
        event_type: The event type this hook responds to
        handler: The callback function to execute
        priority: Execution priority (higher = earlier), default 100
        name: Human-readable name for logging
        plugin_name: Name of plugin that registered this hook (optional)
    """

    event_type: HookEventType
    handler: HookHandler
    priority: int = 100
    name: str = ""
    plugin_name: Optional[str] = None

    def __post_init__(self):
        """Validate and set defaults after initialization."""
        if not self.name:
            self.name = getattr(self.handler, '__name__', 'anonymous_hook')


@dataclass
class HookResults:
    """Results from executing hooks for an event.

    Aggregates results and errors from all hook executions for a
    specific event type.

    Attributes:
        executed_count: Number of hooks successfully executed
        failed_count: Number of hooks that raised exceptions
        results: List of return values from all hooks
        errors: List of exceptions raised by failed hooks
    """

    executed_count: int = 0
    failed_count: int = 0
    results: List[Any] = field(default_factory=list)
    errors: List[Exception] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage.

        Returns:
            Success rate from 0.0 to 1.0, or 1.0 if no hooks executed
        """
        total = self.executed_count + self.failed_count
        if total == 0:
            return 1.0
        return self.executed_count / total

    @property
    def has_errors(self) -> bool:
        """Check if any hooks failed.

        Returns:
            True if any hooks raised exceptions
        """
        return self.failed_count > 0
