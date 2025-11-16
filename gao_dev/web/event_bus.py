"""Event bus for pub/sub messaging using asyncio.Queue."""

import asyncio
import threading
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

import structlog

from .events import EventType, WebEvent

logger = structlog.get_logger(__name__)


class WebEventBus:
    """Asynchronous event bus using asyncio.Queue for pub/sub messaging.

    The event bus allows multiple subscribers to listen for specific event types.
    Events are delivered via asyncio.Queue with automatic overflow handling.

    Features:
    - In-memory pub/sub (no external dependencies)
    - Per-subscriber queues (1000 events max)
    - FIFO overflow handling (drop oldest)
    - Thread-safe sequence numbering
    - Pattern-based subscriptions (e.g., "workflow.*")

    Attributes:
        subscribers: Map of event type to list of subscriber queues
        sequence_counter: Global sequence counter (thread-safe)
        max_queue_size: Maximum events per subscriber queue
    """

    def __init__(self, max_queue_size: int = 1000):
        """Initialize the event bus.

        Args:
            max_queue_size: Maximum events per subscriber queue (default: 1000)
        """
        self.subscribers: Dict[str, List[asyncio.Queue[WebEvent]]] = defaultdict(list)
        self.sequence_counter: int = 0
        self.max_queue_size: int = max_queue_size
        self._lock = threading.Lock()  # Thread-safe sequence counter

        logger.info("event_bus_initialized", max_queue_size=max_queue_size)

    def _next_sequence_number(self) -> int:
        """Get next sequence number (thread-safe).

        Returns:
            Next sequence number
        """
        with self._lock:
            seq = self.sequence_counter
            self.sequence_counter += 1
            return seq

    def subscribe(self, event_type: str) -> asyncio.Queue[WebEvent]:
        """Subscribe to an event type.

        Args:
            event_type: Event type to subscribe to (e.g., "workflow.started")
                       Use "*" for all events

        Returns:
            Queue that will receive matching events
        """
        queue: asyncio.Queue[WebEvent] = asyncio.Queue(maxsize=self.max_queue_size)
        self.subscribers[event_type].append(queue)

        logger.debug(
            "subscriber_added",
            event_type=event_type,
            subscriber_count=len(self.subscribers[event_type]),
        )

        return queue

    def unsubscribe(self, event_type: str, queue: asyncio.Queue[WebEvent]) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: Event type to unsubscribe from
            queue: Queue to remove
        """
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(queue)
                logger.debug(
                    "subscriber_removed",
                    event_type=event_type,
                    remaining_subscribers=len(self.subscribers[event_type]),
                )

                # Clean up empty subscriber lists
                if not self.subscribers[event_type]:
                    del self.subscribers[event_type]

            except ValueError:
                logger.warning(
                    "subscriber_not_found",
                    event_type=event_type,
                )

    async def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WebEvent:
        """Publish an event to all subscribers.

        Args:
            event_type: Type of event
            data: Event data payload
            metadata: Optional metadata

        Returns:
            The published event
        """
        # Create event with sequence number
        sequence_number = self._next_sequence_number()
        event = WebEvent.create(
            event_type=event_type,
            data=data,
            sequence_number=sequence_number,
            metadata=metadata or {},
        )

        # Find matching subscribers
        matching_queues: List[asyncio.Queue[WebEvent]] = []

        # Direct event type match
        if event_type.value in self.subscribers:
            matching_queues.extend(self.subscribers[event_type.value])

        # Wildcard subscribers (subscribe to all events)
        if "*" in self.subscribers:
            matching_queues.extend(self.subscribers["*"])

        # Pattern-based subscribers (e.g., "workflow.*")
        event_prefix = event_type.value.split(".")[0] + ".*"
        if event_prefix in self.subscribers:
            matching_queues.extend(self.subscribers[event_prefix])

        # Publish to all matching subscribers
        delivery_count = 0
        for queue in matching_queues:
            try:
                # Try to add to queue (non-blocking)
                queue.put_nowait(event)
                delivery_count += 1
            except asyncio.QueueFull:
                # Queue full - drop oldest event (FIFO)
                try:
                    queue.get_nowait()  # Remove oldest
                    queue.put_nowait(event)  # Add new event
                    delivery_count += 1
                    logger.debug(
                        "event_queue_overflow",
                        event_type=event_type.value,
                        sequence_number=sequence_number,
                        action="dropped_oldest",
                    )
                except Exception as e:
                    logger.error(
                        "event_delivery_failed",
                        event_type=event_type.value,
                        sequence_number=sequence_number,
                        error=str(e),
                    )

        logger.debug(
            "event_published",
            event_type=event_type.value,
            sequence_number=sequence_number,
            subscribers=delivery_count,
        )

        return event

    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for an event type.

        Args:
            event_type: Event type to check

        Returns:
            Number of subscribers
        """
        return len(self.subscribers.get(event_type, []))

    def get_total_subscribers(self) -> int:
        """Get total number of subscriber queues across all event types.

        Returns:
            Total subscriber count
        """
        return sum(len(queues) for queues in self.subscribers.values())

    def get_event_types(self) -> Set[str]:
        """Get all event types with active subscribers.

        Returns:
            Set of event types
        """
        return set(self.subscribers.keys())

    def clear_all_subscribers(self) -> None:
        """Clear all subscribers (used for testing/cleanup)."""
        self.subscribers.clear()
        logger.info("all_subscribers_cleared")
