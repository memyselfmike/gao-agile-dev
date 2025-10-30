"""Hook manager for plugin extension points.

This module provides the HookManager class which coordinates hook registration
and execution throughout the GAO-Dev lifecycle.
"""

import asyncio
import threading
from typing import Any, Dict, List, Optional

import structlog

from .models.hook import HookEventType, HookHandler, HookInfo, HookResults

logger = structlog.get_logger(__name__)


class HookManager:
    """Manages hook registration and execution for plugin extension points.

    The HookManager provides a centralized system for plugins to register
    callbacks (hooks) that execute at specific lifecycle events. This enables
    plugins to extend core functionality without modifying core code.

    Features:
        - Register hooks for lifecycle events
        - Execute hooks in priority order
        - Support both sync and async hooks
        - Handle hook errors gracefully
        - Thread-safe registration

    Example:
        ```python
        hook_manager = HookManager()

        # Register a hook
        def on_workflow_start(event_data: Dict[str, Any]) -> None:
            print(f"Workflow {event_data['workflow_id']} starting")

        hook_manager.register_hook(
            HookEventType.WORKFLOW_START,
            on_workflow_start,
            priority=100
        )

        # Execute hooks
        await hook_manager.execute_hooks(
            HookEventType.WORKFLOW_START,
            {"workflow_id": "my-workflow"}
        )
        ```

    Attributes:
        _hooks: Dictionary mapping event types to lists of hook info
        _lock: Thread lock for safe concurrent registration
    """

    def __init__(self):
        """Initialize hook manager with empty hook registry."""
        self._hooks: Dict[HookEventType, List[HookInfo]] = {}
        self._lock = threading.Lock()

        logger.info("hook_manager_initialized")

    def register_hook(
        self,
        event_type: HookEventType,
        handler: HookHandler,
        priority: int = 100,
        name: Optional[str] = None,
        plugin_name: Optional[str] = None,
    ) -> None:
        """Register a hook handler for a specific event type.

        Hooks are executed in priority order (higher priority first) when
        their event type is triggered. Multiple hooks can be registered
        for the same event type.

        Args:
            event_type: The lifecycle event to hook into
            handler: Callable that accepts event_data dict
            priority: Execution priority (higher = earlier), default 100
            name: Human-readable name for logging (defaults to function name)
            plugin_name: Name of plugin registering this hook (for cleanup)

        Example:
            ```python
            hook_manager.register_hook(
                HookEventType.WORKFLOW_END,
                my_handler,
                priority=150,  # Execute before default priority hooks
                plugin_name="my-plugin"
            )
            ```
        """
        with self._lock:
            if event_type not in self._hooks:
                self._hooks[event_type] = []

            hook_info = HookInfo(
                event_type=event_type,
                handler=handler,
                priority=priority,
                name=name or handler.__name__,
                plugin_name=plugin_name,
            )

            self._hooks[event_type].append(hook_info)

            # Sort by priority (highest first)
            self._hooks[event_type].sort(key=lambda h: h.priority, reverse=True)

            logger.info(
                "hook_registered",
                event_type=event_type.value,
                handler_name=hook_info.name,
                priority=priority,
                plugin_name=plugin_name,
            )

    def unregister_hook(
        self,
        event_type: HookEventType,
        handler: HookHandler,
    ) -> bool:
        """Unregister a specific hook handler.

        Args:
            event_type: The event type the hook is registered for
            handler: The handler function to remove

        Returns:
            True if hook was found and removed, False otherwise

        Example:
            ```python
            removed = hook_manager.unregister_hook(
                HookEventType.WORKFLOW_START,
                my_handler
            )
            ```
        """
        with self._lock:
            if event_type not in self._hooks:
                return False

            original_count = len(self._hooks[event_type])
            self._hooks[event_type] = [
                h for h in self._hooks[event_type] if h.handler != handler
            ]
            removed = len(self._hooks[event_type]) < original_count

            if removed:
                logger.info(
                    "hook_unregistered",
                    event_type=event_type.value,
                    handler_name=handler.__name__,
                )

            return removed

    def unregister_plugin_hooks(self, plugin_name: str) -> int:
        """Unregister all hooks from a specific plugin.

        This is typically called during plugin cleanup to ensure no
        orphaned hooks remain in the system.

        Args:
            plugin_name: Name of plugin whose hooks should be removed

        Returns:
            Number of hooks removed

        Example:
            ```python
            removed_count = hook_manager.unregister_plugin_hooks("my-plugin")
            ```
        """
        removed_count = 0

        with self._lock:
            for event_type in list(self._hooks.keys()):
                original_count = len(self._hooks[event_type])
                self._hooks[event_type] = [
                    h for h in self._hooks[event_type] if h.plugin_name != plugin_name
                ]
                removed_count += original_count - len(self._hooks[event_type])

        if removed_count > 0:
            logger.info(
                "plugin_hooks_unregistered",
                plugin_name=plugin_name,
                count=removed_count,
            )

        return removed_count

    async def execute_hooks(
        self, event_type: HookEventType, event_data: Dict[str, Any]
    ) -> HookResults:
        """Execute all registered hooks for an event type.

        Hooks are executed in priority order (highest priority first).
        Both synchronous and asynchronous hooks are supported. Hook
        errors are caught and logged but don't prevent other hooks
        from executing.

        Args:
            event_type: The event type to fire hooks for
            event_data: Dictionary of event-specific data passed to hooks

        Returns:
            HookResults containing execution statistics and results

        Example:
            ```python
            results = await hook_manager.execute_hooks(
                HookEventType.WORKFLOW_START,
                {
                    "workflow_id": "my-workflow",
                    "context": workflow_context
                }
            )

            print(f"Executed {results.executed_count} hooks")
            if results.has_errors:
                print(f"{results.failed_count} hooks failed")
            ```
        """
        hooks = self._hooks.get(event_type, [])

        if not hooks:
            logger.debug("no_hooks_registered", event_type=event_type.value)
            return HookResults()

        logger.debug(
            "executing_hooks",
            event_type=event_type.value,
            hook_count=len(hooks),
        )

        executed_count = 0
        failed_count = 0
        results = []
        errors = []

        for hook_info in hooks:
            try:
                # Execute async or sync handler
                if asyncio.iscoroutinefunction(hook_info.handler):
                    result = await hook_info.handler(event_data)
                else:
                    result = hook_info.handler(event_data)

                results.append(result)
                executed_count += 1

                logger.debug(
                    "hook_executed",
                    event_type=event_type.value,
                    handler_name=hook_info.name,
                    plugin_name=hook_info.plugin_name,
                )

            except Exception as e:
                logger.error(
                    "hook_execution_failed",
                    event_type=event_type.value,
                    handler_name=hook_info.name,
                    plugin_name=hook_info.plugin_name,
                    error=str(e),
                    exc_info=True,
                )
                errors.append(e)
                failed_count += 1

        hook_results = HookResults(
            executed_count=executed_count,
            failed_count=failed_count,
            results=results,
            errors=errors,
        )

        logger.info(
            "hooks_executed",
            event_type=event_type.value,
            executed=executed_count,
            failed=failed_count,
            success_rate=hook_results.success_rate,
        )

        return hook_results

    def get_registered_hooks(
        self, event_type: Optional[HookEventType] = None
    ) -> List[HookInfo]:
        """Get list of registered hooks, optionally filtered by event type.

        Args:
            event_type: Event type to filter by (None = all hooks)

        Returns:
            List of HookInfo objects for registered hooks

        Example:
            ```python
            # Get all workflow start hooks
            workflow_hooks = hook_manager.get_registered_hooks(
                HookEventType.WORKFLOW_START
            )

            # Get all hooks
            all_hooks = hook_manager.get_registered_hooks()
            ```
        """
        if event_type:
            return list(self._hooks.get(event_type, []))

        # Return all hooks from all event types
        all_hooks = []
        for hooks_list in self._hooks.values():
            all_hooks.extend(hooks_list)
        return all_hooks

    def clear_hooks(self, event_type: Optional[HookEventType] = None) -> int:
        """Clear hooks, optionally for specific event type.

        Args:
            event_type: Event type to clear (None = clear all)

        Returns:
            Number of hooks removed

        Example:
            ```python
            # Clear all workflow start hooks
            removed = hook_manager.clear_hooks(HookEventType.WORKFLOW_START)

            # Clear all hooks
            total_removed = hook_manager.clear_hooks()
            ```
        """
        removed_count = 0

        with self._lock:
            if event_type:
                removed_count = len(self._hooks.get(event_type, []))
                self._hooks[event_type] = []
            else:
                removed_count = sum(len(hooks) for hooks in self._hooks.values())
                self._hooks.clear()

        if removed_count > 0:
            logger.info(
                "hooks_cleared",
                event_type=event_type.value if event_type else "all",
                count=removed_count,
            )

        return removed_count
