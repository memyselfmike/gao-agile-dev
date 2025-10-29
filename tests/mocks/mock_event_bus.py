"""Mock event bus implementation for testing."""

from typing import Type, List, Callable, Dict, Any
from gao_dev.core.interfaces.event_bus import IEventBus, IEventHandler


class MockEventHandler(IEventHandler):
    """Mock event handler for testing."""

    def __init__(self, event_type: Type = None):
        self._event_type = event_type
        self.events_handled: List[Any] = []

    async def handle(self, event: Any) -> None:
        """Handle event and store it."""
        self.events_handled.append(event)

    def can_handle(self, event_type: Type) -> bool:
        """Check if can handle event type."""
        if self._event_type is None:
            return True
        return event_type == self._event_type


class MockEventBus(IEventBus):
    """Mock event bus for testing."""

    def __init__(self):
        self._subscribers: Dict[Type, List[IEventHandler]] = {}
        self._events_published: List[Any] = []

    def subscribe(
        self,
        event_type: Type,
        handler: IEventHandler
    ) -> None:
        """Subscribe handler to event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def subscribe_func(
        self,
        event_type: Type,
        handler_func: Callable[[Any], Any]
    ) -> None:
        """Subscribe function as handler (wraps in MockEventHandler)."""
        # For simplicity, not implementing this in mock
        pass

    def unsubscribe(
        self,
        event_type: Type,
        handler: IEventHandler
    ) -> None:
        """Unsubscribe handler."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)

    async def publish(self, event: Any) -> None:
        """Publish event to all subscribers."""
        self._events_published.append(event)
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                await handler.handle(event)

    def get_subscribers(self, event_type: Type) -> List[IEventHandler]:
        """Get subscribers for event type."""
        return self._subscribers.get(event_type, []).copy()

    def clear_subscribers(self, event_type: Type = None) -> None:
        """Clear subscribers."""
        if event_type is None:
            self._subscribers.clear()
        else:
            self._subscribers.pop(event_type, None)

    def get_event_history(
        self,
        event_type: Type = None,
        limit: int = 100
    ) -> List[Any]:
        """Get event history."""
        if event_type is None:
            return self._events_published[-limit:]
        return [e for e in self._events_published if type(e) == event_type][-limit:]

    def clear_history(self) -> None:
        """Clear event history (test utility)."""
        self._events_published.clear()
