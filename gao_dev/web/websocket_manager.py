"""WebSocket connection management and event broadcasting."""

import asyncio
import time
import uuid
from collections import deque
from typing import Any, Dict, Optional, Set

import structlog
from fastapi import WebSocket, WebSocketDisconnect

from .event_bus import WebEventBus
from .events import EventType, WebEvent

logger = structlog.get_logger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and event broadcasting.

    Features:
    - Connection tracking with unique client IDs
    - Event broadcasting to all connected clients
    - Per-client subscription filters
    - Reconnection support with event replay
    - Heartbeat/ping every 30 seconds
    - Connection limit (10 concurrent clients)

    Attributes:
        event_bus: Event bus for pub/sub messaging
        connections: Map of client_id to WebSocket
        subscriptions: Map of client_id to subscribed event types
        reconnect_buffers: Map of client_id to buffered events
        heartbeat_interval: Seconds between heartbeat pings
        reconnect_buffer_size: Max events to buffer per client
        reconnect_ttl: Seconds to keep reconnect buffer
        max_connections: Maximum concurrent connections
    """

    def __init__(
        self,
        event_bus: WebEventBus,
        heartbeat_interval: int = 30,
        reconnect_buffer_size: int = 100,
        reconnect_ttl: int = 30,
        max_connections: int = 10,
    ):
        """Initialize WebSocket manager.

        Args:
            event_bus: Event bus instance
            heartbeat_interval: Seconds between heartbeat pings (default: 30)
            reconnect_buffer_size: Max events to buffer per client (default: 100)
            reconnect_ttl: Seconds to keep reconnect buffer (default: 30)
            max_connections: Maximum concurrent connections (default: 10)
        """
        self.event_bus = event_bus
        self.connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}
        self.reconnect_buffers: Dict[str, deque[WebEvent]] = {}
        self.reconnect_timestamps: Dict[str, float] = {}
        self.client_queues: Dict[str, asyncio.Queue[WebEvent]] = {}
        self.tasks: Dict[str, asyncio.Task[Any]] = {}

        # Configuration
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_buffer_size = reconnect_buffer_size
        self.reconnect_ttl = reconnect_ttl
        self.max_connections = max_connections

        logger.info(
            "websocket_manager_initialized",
            heartbeat_interval=heartbeat_interval,
            reconnect_buffer_size=reconnect_buffer_size,
            max_connections=max_connections,
        )

    async def connect(
        self,
        websocket: WebSocket,
        client_id: Optional[str] = None,
        last_sequence: Optional[int] = None,
    ) -> str:
        """Connect a WebSocket client.

        Args:
            websocket: WebSocket connection
            client_id: Optional client ID for reconnection
            last_sequence: Last sequence number received (for replay)

        Returns:
            Client ID

        Raises:
            ValueError: If connection limit exceeded
        """
        # Check connection limit
        if len(self.connections) >= self.max_connections:
            logger.warning(
                "connection_limit_exceeded",
                max_connections=self.max_connections,
                current_connections=len(self.connections),
            )
            raise ValueError(f"Connection limit exceeded ({self.max_connections} max)")

        # Generate or reuse client ID
        if not client_id:
            client_id = str(uuid.uuid4())

        # Accept connection
        await websocket.accept()

        # Store connection
        self.connections[client_id] = websocket
        self.subscriptions[client_id] = {"*"}  # Subscribe to all events by default

        logger.info(
            "websocket_connected",
            client_id=client_id,
            total_connections=len(self.connections),
        )

        # Create queue for this client
        queue = self.event_bus.subscribe("*")
        self.client_queues[client_id] = queue

        # Send connection confirmation
        await self._send_event(
            websocket,
            EventType.SYSTEM_HEARTBEAT,
            {"status": "connected", "client_id": client_id},
            0,
        )

        # Replay missed events if reconnecting
        if last_sequence is not None and client_id in self.reconnect_buffers:
            await self._replay_events(websocket, client_id, last_sequence)

        # Start event streaming task
        task = asyncio.create_task(self._stream_events(websocket, client_id))
        self.tasks[client_id] = task

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(self._heartbeat(websocket, client_id))
        self.tasks[f"{client_id}_heartbeat"] = heartbeat_task

        return client_id

    async def disconnect(self, client_id: str) -> None:
        """Disconnect a WebSocket client.

        Args:
            client_id: Client ID to disconnect
        """
        if client_id not in self.connections:
            logger.warning("disconnect_unknown_client", client_id=client_id)
            return

        # Remove connection
        self.connections.pop(client_id, None)

        # Unsubscribe from event bus
        if client_id in self.client_queues:
            queue = self.client_queues.pop(client_id)
            self.event_bus.unsubscribe("*", queue)

        # Cancel tasks
        for task_key in [client_id, f"{client_id}_heartbeat"]:
            if task_key in self.tasks:
                task = self.tasks.pop(task_key)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Store reconnect buffer timestamp
        self.reconnect_timestamps[client_id] = time.time()

        # Clean up subscriptions (but keep reconnect buffer)
        self.subscriptions.pop(client_id, None)

        logger.info(
            "websocket_disconnected",
            client_id=client_id,
            remaining_connections=len(self.connections),
        )

        # Clean up old reconnect buffers
        await self._cleanup_reconnect_buffers()

    async def _stream_events(self, websocket: WebSocket, client_id: str) -> None:
        """Stream events from queue to WebSocket client.

        Args:
            websocket: WebSocket connection
            client_id: Client ID
        """
        queue = self.client_queues.get(client_id)
        if not queue:
            return

        try:
            while True:
                # Get event from queue
                event = await queue.get()

                # Check if client is still subscribed to this event type
                if not self._is_subscribed(client_id, event.type):
                    continue

                # Send event to client
                await websocket.send_json(event.to_dict())

                # Buffer event for reconnection
                await self._buffer_event(client_id, event)

        except WebSocketDisconnect:
            logger.info("websocket_stream_ended", client_id=client_id, reason="disconnect")
            await self.disconnect(client_id)
        except asyncio.CancelledError:
            logger.debug("websocket_stream_cancelled", client_id=client_id)
        except Exception as e:
            logger.error(
                "websocket_stream_error",
                client_id=client_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            await self.disconnect(client_id)

    async def _heartbeat(self, websocket: WebSocket, client_id: str) -> None:
        """Send periodic heartbeat pings to keep connection alive.

        Args:
            websocket: WebSocket connection
            client_id: Client ID
        """
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)

                # Send heartbeat
                await self._send_event(
                    websocket,
                    EventType.SYSTEM_HEARTBEAT,
                    {"timestamp": time.time()},
                    -1,  # Heartbeats don't have sequence numbers
                )

                logger.debug("heartbeat_sent", client_id=client_id)

        except WebSocketDisconnect:
            logger.debug("heartbeat_ended", client_id=client_id, reason="disconnect")
        except asyncio.CancelledError:
            logger.debug("heartbeat_cancelled", client_id=client_id)
        except Exception as e:
            logger.error(
                "heartbeat_error",
                client_id=client_id,
                error=str(e),
            )

    async def _send_event(
        self,
        websocket: WebSocket,
        event_type: EventType,
        data: Dict[str, Any],
        sequence_number: int,
    ) -> None:
        """Send an event to a WebSocket client.

        Args:
            websocket: WebSocket connection
            event_type: Type of event
            data: Event data
            sequence_number: Sequence number
        """
        event = WebEvent.create(
            event_type=event_type,
            data=data,
            sequence_number=sequence_number,
        )
        await websocket.send_json(event.to_dict())

    async def _buffer_event(self, client_id: str, event: WebEvent) -> None:
        """Buffer an event for reconnection support.

        Args:
            client_id: Client ID
            event: Event to buffer
        """
        if client_id not in self.reconnect_buffers:
            self.reconnect_buffers[client_id] = deque(maxlen=self.reconnect_buffer_size)

        self.reconnect_buffers[client_id].append(event)

    async def _replay_events(
        self,
        websocket: WebSocket,
        client_id: str,
        last_sequence: int,
    ) -> None:
        """Replay missed events after reconnection.

        Args:
            websocket: WebSocket connection
            client_id: Client ID
            last_sequence: Last sequence number received by client
        """
        if client_id not in self.reconnect_buffers:
            logger.debug("no_reconnect_buffer", client_id=client_id)
            return

        buffer = self.reconnect_buffers[client_id]
        replayed = 0

        for event in buffer:
            if event.sequence_number > last_sequence:
                await websocket.send_json(event.to_dict())
                replayed += 1

        logger.info(
            "events_replayed",
            client_id=client_id,
            last_sequence=last_sequence,
            replayed=replayed,
        )

    async def _cleanup_reconnect_buffers(self) -> None:
        """Clean up expired reconnect buffers."""
        now = time.time()
        expired_clients = []

        for client_id, timestamp in self.reconnect_timestamps.items():
            if now - timestamp > self.reconnect_ttl:
                expired_clients.append(client_id)

        for client_id in expired_clients:
            self.reconnect_buffers.pop(client_id, None)
            self.reconnect_timestamps.pop(client_id, None)
            logger.debug("reconnect_buffer_expired", client_id=client_id)

    def _is_subscribed(self, client_id: str, event_type: str) -> bool:
        """Check if client is subscribed to an event type.

        Args:
            client_id: Client ID
            event_type: Event type to check

        Returns:
            True if subscribed, False otherwise
        """
        if client_id not in self.subscriptions:
            return False

        subscriptions = self.subscriptions[client_id]

        # Wildcard subscription
        if "*" in subscriptions:
            return True

        # Direct match
        if event_type in subscriptions:
            return True

        # Pattern match (e.g., "workflow.*")
        event_prefix = event_type.split(".")[0] + ".*"
        if event_prefix in subscriptions:
            return True

        return False

    def subscribe_client(self, client_id: str, event_type: str) -> None:
        """Subscribe a client to an event type.

        Args:
            client_id: Client ID
            event_type: Event type to subscribe to
        """
        if client_id not in self.subscriptions:
            self.subscriptions[client_id] = set()

        self.subscriptions[client_id].add(event_type)

        logger.debug(
            "client_subscribed",
            client_id=client_id,
            event_type=event_type,
        )

    def unsubscribe_client(self, client_id: str, event_type: str) -> None:
        """Unsubscribe a client from an event type.

        Args:
            client_id: Client ID
            event_type: Event type to unsubscribe from
        """
        if client_id in self.subscriptions:
            self.subscriptions[client_id].discard(event_type)

            logger.debug(
                "client_unsubscribed",
                client_id=client_id,
                event_type=event_type,
            )

    def get_connection_count(self) -> int:
        """Get number of active connections.

        Returns:
            Active connection count
        """
        return len(self.connections)

    def get_client_subscriptions(self, client_id: str) -> Set[str]:
        """Get event types a client is subscribed to.

        Args:
            client_id: Client ID

        Returns:
            Set of event types
        """
        return self.subscriptions.get(client_id, set())
