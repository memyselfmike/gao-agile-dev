"""
Event system interfaces for GAO-Dev.

This module defines the Observer pattern interfaces for event-driven
coordination between components.
"""

from abc import ABC, abstractmethod
from typing import Type, List, Callable, Any, Optional


class IEventHandler(ABC):
    """
    Interface for event handlers.

    Event handlers are invoked when specific events occur in the system.
    They enable loose coupling between components through the Observer pattern.

    Example:
        ```python
        class MetricsCollectorHandler(IEventHandler):
            async def handle(self, event: Event) -> None:
                if isinstance(event, StoryCompleted):
                    await self.collect_metrics(event.story_id)
        ```
    """

    @abstractmethod
    async def handle(self, event: 'Event') -> None:  # Forward reference
        """
        Handle an event.

        This method is invoked when an event the handler is subscribed to
        is published to the event bus.

        Args:
            event: Event instance containing event data

        Raises:
            EventHandlerError: If event handling fails
        """
        pass

    @abstractmethod
    def can_handle(self, event_type: Type['Event']) -> bool:  # Forward reference
        """
        Check if this handler can handle events of given type.

        Args:
            event_type: Event class type

        Returns:
            bool: True if handler can handle this event type
        """
        pass


class IEventBus(ABC):
    """
    Event bus interface for publish-subscribe pattern.

    The event bus enables components to communicate through events
    without direct dependencies. Publishers emit events, subscribers
    receive them.

    Example:
        ```python
        event_bus = DefaultEventBus()

        # Subscribe
        event_bus.subscribe(StoryCompleted, metrics_handler)
        event_bus.subscribe(StoryCompleted, notification_handler)

        # Publish
        await event_bus.publish(StoryCompleted(story_id="1.1"))
        ```
    """

    @abstractmethod
    def subscribe(
        self,
        event_type: Type['Event'],  # Forward reference
        handler: IEventHandler
    ) -> None:
        """
        Subscribe a handler to an event type.

        When events of the specified type are published, the handler
        will be invoked.

        Args:
            event_type: Event class to subscribe to
            handler: Handler to invoke for events of this type

        Raises:
            SubscriptionError: If subscription fails
        """
        pass

    @abstractmethod
    def subscribe_func(
        self,
        event_type: Type['Event'],  # Forward reference
        handler_func: Callable[['Event'], Any]
    ) -> None:
        """
        Subscribe a function as an event handler.

        Convenience method for subscribing simple functions without
        creating a full IEventHandler class.

        Args:
            event_type: Event class to subscribe to
            handler_func: Async function to invoke for events

        Raises:
            SubscriptionError: If subscription fails
        """
        pass

    @abstractmethod
    def unsubscribe(
        self,
        event_type: Type['Event'],  # Forward reference
        handler: IEventHandler
    ) -> None:
        """
        Unsubscribe a handler from an event type.

        Args:
            event_type: Event class to unsubscribe from
            handler: Handler to remove

        Raises:
            UnsubscriptionError: If handler not subscribed
        """
        pass

    @abstractmethod
    async def publish(self, event: 'Event') -> None:  # Forward reference
        """
        Publish an event to all subscribers.

        All handlers subscribed to this event type will be invoked
        asynchronously.

        Args:
            event: Event instance to publish

        Raises:
            PublishError: If publishing fails
        """
        pass

    @abstractmethod
    def get_subscribers(
        self,
        event_type: Type['Event']  # Forward reference
    ) -> List[IEventHandler]:
        """
        Get all handlers subscribed to an event type.

        Args:
            event_type: Event class

        Returns:
            List of subscribed handlers
        """
        pass

    @abstractmethod
    def clear_subscribers(
        self,
        event_type: Optional[Type['Event']] = None  # Forward reference
    ) -> None:
        """
        Clear subscribers for an event type, or all if None.

        Args:
            event_type: Event class to clear, or None for all
        """
        pass

    @abstractmethod
    def get_event_history(
        self,
        event_type: Optional[Type['Event']] = None,  # Forward reference
        limit: int = 100
    ) -> List['Event']:  # Forward reference
        """
        Get history of published events.

        Useful for debugging and auditing.

        Args:
            event_type: Filter by event type, or None for all
            limit: Maximum number of events to return

        Returns:
            List of events (most recent first)
        """
        pass
