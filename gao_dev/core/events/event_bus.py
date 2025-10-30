"""Simple Event Bus implementation using Observer Pattern."""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any
from datetime import datetime
import structlog

logger = structlog.get_logger()


@dataclass
class Event:
    """Event dataclass."""
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventBus:
    """
    Simple synchronous event bus using Observer Pattern.

    Allows components to communicate without tight coupling.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(handler)
        logger.info("event_subscribed", event_type=event_type, handler=handler.__name__)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        if event.type in self._subscribers:
            for handler in self._subscribers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error("event_handler_failed", event_type=event.type, error=str(e))

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)
