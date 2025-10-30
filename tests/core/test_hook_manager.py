"""Tests for hook manager and hook system."""

import pytest
import asyncio
from typing import Dict, Any

from gao_dev.core.hook_manager import HookManager
from gao_dev.core.models.hook import (
    HookEventType,
    HookInfo,
    HookResults,
)


# Test Fixtures

@pytest.fixture
def hook_manager():
    """Create HookManager instance."""
    return HookManager()


@pytest.fixture
def sample_event_data():
    """Create sample event data."""
    return {
        "workflow_id": "test-workflow",
        "context": {"project": "test-project"},
    }


# Test Hook Models

class TestHookModels:
    """Tests for hook data models."""

    def test_hook_event_type_enum(self):
        """Test that all expected hook event types exist."""
        assert HookEventType.WORKFLOW_START == HookEventType("workflow.start")
        assert HookEventType.WORKFLOW_END == HookEventType("workflow.end")
        assert HookEventType.WORKFLOW_ERROR == HookEventType("workflow.error")
        assert HookEventType.AGENT_CREATED == HookEventType("agent.created")
        assert HookEventType.PLUGIN_LOADED == HookEventType("plugin.loaded")
        assert HookEventType.SYSTEM_STARTUP == HookEventType("system.startup")

    def test_hook_info_creation(self):
        """Test creating HookInfo."""
        def my_handler(event_data: Dict[str, Any]) -> None:
            pass

        hook_info = HookInfo(
            event_type=HookEventType.WORKFLOW_START,
            handler=my_handler,
            priority=100,
            name="my_handler",
            plugin_name="test-plugin",
        )

        assert hook_info.event_type == HookEventType.WORKFLOW_START
        assert hook_info.handler == my_handler
        assert hook_info.priority == 100
        assert hook_info.name == "my_handler"
        assert hook_info.plugin_name == "test-plugin"

    def test_hook_info_auto_name(self):
        """Test that HookInfo automatically sets name from handler."""
        def my_handler(event_data: Dict[str, Any]) -> None:
            pass

        hook_info = HookInfo(
            event_type=HookEventType.WORKFLOW_START,
            handler=my_handler,
        )

        assert hook_info.name == "my_handler"

    def test_hook_results_success_rate(self):
        """Test HookResults success rate calculation."""
        results = HookResults(
            executed_count=8,
            failed_count=2,
            results=[],
            errors=[],
        )

        assert results.success_rate == 0.8

    def test_hook_results_success_rate_zero_hooks(self):
        """Test success rate when no hooks executed."""
        results = HookResults()
        assert results.success_rate == 1.0

    def test_hook_results_has_errors(self):
        """Test has_errors property."""
        results_no_errors = HookResults(executed_count=5)
        assert not results_no_errors.has_errors

        results_with_errors = HookResults(executed_count=3, failed_count=2)
        assert results_with_errors.has_errors


# Test HookManager Registration

class TestHookManagerRegistration:
    """Tests for hook registration."""

    def test_register_hook(self, hook_manager):
        """Test registering a hook."""
        def my_handler(event_data: Dict[str, Any]) -> None:
            pass

        hook_manager.register_hook(
            HookEventType.WORKFLOW_START,
            my_handler,
            priority=100,
        )

        hooks = hook_manager.get_registered_hooks(HookEventType.WORKFLOW_START)
        assert len(hooks) == 1
        assert hooks[0].handler == my_handler
        assert hooks[0].priority == 100

    def test_register_multiple_hooks_same_event(self, hook_manager):
        """Test registering multiple hooks for same event."""
        def handler1(event_data: Dict[str, Any]) -> None:
            pass

        def handler2(event_data: Dict[str, Any]) -> None:
            pass

        hook_manager.register_hook(
            HookEventType.WORKFLOW_START,
            handler1,
            priority=100,
        )
        hook_manager.register_hook(
            HookEventType.WORKFLOW_START,
            handler2,
            priority=50,
        )

        hooks = hook_manager.get_registered_hooks(HookEventType.WORKFLOW_START)
        assert len(hooks) == 2

    def test_register_hooks_priority_ordering(self, hook_manager):
        """Test that hooks are ordered by priority (highest first)."""
        def handler1(event_data: Dict[str, Any]) -> None:
            pass

        def handler2(event_data: Dict[str, Any]) -> None:
            pass

        def handler3(event_data: Dict[str, Any]) -> None:
            pass

        hook_manager.register_hook(HookEventType.WORKFLOW_START, handler1, priority=50)
        hook_manager.register_hook(HookEventType.WORKFLOW_START, handler2, priority=150)
        hook_manager.register_hook(HookEventType.WORKFLOW_START, handler3, priority=100)

        hooks = hook_manager.get_registered_hooks(HookEventType.WORKFLOW_START)
        assert len(hooks) == 3
        assert hooks[0].handler == handler2  # Priority 150 (highest)
        assert hooks[1].handler == handler3  # Priority 100
        assert hooks[2].handler == handler1  # Priority 50

    def test_register_hook_with_plugin_name(self, hook_manager):
        """Test registering hook with plugin name."""
        def my_handler(event_data: Dict[str, Any]) -> None:
            pass

        hook_manager.register_hook(
            HookEventType.WORKFLOW_START,
            my_handler,
            plugin_name="test-plugin",
        )

        hooks = hook_manager.get_registered_hooks(HookEventType.WORKFLOW_START)
        assert hooks[0].plugin_name == "test-plugin"


# Test HookManager Unregistration

class TestHookManagerUnregistration:
    """Tests for hook unregistration."""

    def test_unregister_hook(self, hook_manager):
        """Test unregistering a specific hook."""
        def my_handler(event_data: Dict[str, Any]) -> None:
            pass

        hook_manager.register_hook(HookEventType.WORKFLOW_START, my_handler)
        assert len(hook_manager.get_registered_hooks(HookEventType.WORKFLOW_START)) == 1

        result = hook_manager.unregister_hook(HookEventType.WORKFLOW_START, my_handler)
        assert result is True
        assert len(hook_manager.get_registered_hooks(HookEventType.WORKFLOW_START)) == 0

    def test_unregister_nonexistent_hook(self, hook_manager):
        """Test unregistering hook that doesn't exist."""
        def my_handler(event_data: Dict[str, Any]) -> None:
            pass

        result = hook_manager.unregister_hook(HookEventType.WORKFLOW_START, my_handler)
        assert result is False

    def test_unregister_plugin_hooks(self, hook_manager):
        """Test unregistering all hooks from a plugin."""
        def handler1(event_data: Dict[str, Any]) -> None:
            pass

        def handler2(event_data: Dict[str, Any]) -> None:
            pass

        def handler3(event_data: Dict[str, Any]) -> None:
            pass

        hook_manager.register_hook(
            HookEventType.WORKFLOW_START, handler1, plugin_name="plugin1"
        )
        hook_manager.register_hook(
            HookEventType.WORKFLOW_END, handler2, plugin_name="plugin1"
        )
        hook_manager.register_hook(
            HookEventType.WORKFLOW_START, handler3, plugin_name="plugin2"
        )

        removed = hook_manager.unregister_plugin_hooks("plugin1")
        assert removed == 2

        # Plugin1 hooks removed
        workflow_start_hooks = hook_manager.get_registered_hooks(
            HookEventType.WORKFLOW_START
        )
        assert len(workflow_start_hooks) == 1
        assert workflow_start_hooks[0].handler == handler3

        workflow_end_hooks = hook_manager.get_registered_hooks(HookEventType.WORKFLOW_END)
        assert len(workflow_end_hooks) == 0

    def test_clear_hooks_specific_event(self, hook_manager):
        """Test clearing hooks for specific event type."""
        def handler1(event_data: Dict[str, Any]) -> None:
            pass

        def handler2(event_data: Dict[str, Any]) -> None:
            pass

        hook_manager.register_hook(HookEventType.WORKFLOW_START, handler1)
        hook_manager.register_hook(HookEventType.WORKFLOW_END, handler2)

        removed = hook_manager.clear_hooks(HookEventType.WORKFLOW_START)
        assert removed == 1

        assert len(hook_manager.get_registered_hooks(HookEventType.WORKFLOW_START)) == 0
        assert len(hook_manager.get_registered_hooks(HookEventType.WORKFLOW_END)) == 1

    def test_clear_all_hooks(self, hook_manager):
        """Test clearing all hooks."""
        def handler1(event_data: Dict[str, Any]) -> None:
            pass

        def handler2(event_data: Dict[str, Any]) -> None:
            pass

        hook_manager.register_hook(HookEventType.WORKFLOW_START, handler1)
        hook_manager.register_hook(HookEventType.WORKFLOW_END, handler2)

        removed = hook_manager.clear_hooks()
        assert removed == 2

        all_hooks = hook_manager.get_registered_hooks()
        assert len(all_hooks) == 0


# Test HookManager Execution

class TestHookManagerExecution:
    """Tests for hook execution."""

    @pytest.mark.asyncio
    async def test_execute_sync_hook(self, hook_manager, sample_event_data):
        """Test executing synchronous hook."""
        executed = []

        def my_handler(event_data: Dict[str, Any]) -> None:
            executed.append(event_data)

        hook_manager.register_hook(HookEventType.WORKFLOW_START, my_handler)

        results = await hook_manager.execute_hooks(
            HookEventType.WORKFLOW_START, sample_event_data
        )

        assert results.executed_count == 1
        assert results.failed_count == 0
        assert len(executed) == 1
        assert executed[0] == sample_event_data

    @pytest.mark.asyncio
    async def test_execute_async_hook(self, hook_manager, sample_event_data):
        """Test executing asynchronous hook."""
        executed = []

        async def my_async_handler(event_data: Dict[str, Any]) -> None:
            await asyncio.sleep(0.001)
            executed.append(event_data)

        hook_manager.register_hook(HookEventType.WORKFLOW_START, my_async_handler)

        results = await hook_manager.execute_hooks(
            HookEventType.WORKFLOW_START, sample_event_data
        )

        assert results.executed_count == 1
        assert results.failed_count == 0
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_execute_multiple_hooks(self, hook_manager, sample_event_data):
        """Test executing multiple hooks in priority order."""
        execution_order = []

        def handler1(event_data: Dict[str, Any]) -> None:
            execution_order.append("handler1")

        def handler2(event_data: Dict[str, Any]) -> None:
            execution_order.append("handler2")

        def handler3(event_data: Dict[str, Any]) -> None:
            execution_order.append("handler3")

        hook_manager.register_hook(HookEventType.WORKFLOW_START, handler1, priority=50)
        hook_manager.register_hook(HookEventType.WORKFLOW_START, handler2, priority=150)
        hook_manager.register_hook(HookEventType.WORKFLOW_START, handler3, priority=100)

        await hook_manager.execute_hooks(HookEventType.WORKFLOW_START, sample_event_data)

        # Should execute in priority order (highest first)
        assert execution_order == ["handler2", "handler3", "handler1"]

    @pytest.mark.asyncio
    async def test_execute_hook_with_return_value(self, hook_manager, sample_event_data):
        """Test hook that returns a value."""

        def my_handler(event_data: Dict[str, Any]) -> Dict[str, Any]:
            return {"processed": True, "data": event_data}

        hook_manager.register_hook(HookEventType.WORKFLOW_START, my_handler)

        results = await hook_manager.execute_hooks(
            HookEventType.WORKFLOW_START, sample_event_data
        )

        assert len(results.results) == 1
        assert results.results[0]["processed"] is True

    @pytest.mark.asyncio
    async def test_execute_hook_error_handling(self, hook_manager, sample_event_data):
        """Test that hook errors are caught and don't stop other hooks."""
        executed = []

        def failing_handler(event_data: Dict[str, Any]) -> None:
            raise ValueError("Hook failed")

        def successful_handler(event_data: Dict[str, Any]) -> None:
            executed.append("success")

        hook_manager.register_hook(HookEventType.WORKFLOW_START, failing_handler)
        hook_manager.register_hook(HookEventType.WORKFLOW_START, successful_handler)

        results = await hook_manager.execute_hooks(
            HookEventType.WORKFLOW_START, sample_event_data
        )

        assert results.executed_count == 1
        assert results.failed_count == 1
        assert len(results.errors) == 1
        assert isinstance(results.errors[0], ValueError)
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_execute_no_hooks_registered(self, hook_manager, sample_event_data):
        """Test executing when no hooks registered."""
        results = await hook_manager.execute_hooks(
            HookEventType.WORKFLOW_START, sample_event_data
        )

        assert results.executed_count == 0
        assert results.failed_count == 0
        assert results.success_rate == 1.0


# Test HookManager Queries

class TestHookManagerQueries:
    """Tests for querying registered hooks."""

    def test_get_hooks_for_event_type(self, hook_manager):
        """Test getting hooks for specific event type."""

        def handler1(event_data: Dict[str, Any]) -> None:
            pass

        def handler2(event_data: Dict[str, Any]) -> None:
            pass

        hook_manager.register_hook(HookEventType.WORKFLOW_START, handler1)
        hook_manager.register_hook(HookEventType.WORKFLOW_END, handler2)

        workflow_start_hooks = hook_manager.get_registered_hooks(
            HookEventType.WORKFLOW_START
        )
        assert len(workflow_start_hooks) == 1
        assert workflow_start_hooks[0].handler == handler1

    def test_get_all_hooks(self, hook_manager):
        """Test getting all registered hooks."""

        def handler1(event_data: Dict[str, Any]) -> None:
            pass

        def handler2(event_data: Dict[str, Any]) -> None:
            pass

        hook_manager.register_hook(HookEventType.WORKFLOW_START, handler1)
        hook_manager.register_hook(HookEventType.WORKFLOW_END, handler2)

        all_hooks = hook_manager.get_registered_hooks()
        assert len(all_hooks) == 2
