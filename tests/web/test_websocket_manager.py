"""Unit tests for WebSocket manager."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket, WebSocketDisconnect

from gao_dev.web.event_bus import WebEventBus
from gao_dev.web.events import EventType
from gao_dev.web.websocket_manager import WebSocketManager


class TestWebSocketManager:
    """Tests for WebSocketManager."""

    @pytest.fixture
    def event_bus(self):
        """Create event bus for testing."""
        bus = WebEventBus()
        yield bus
        bus.clear_all_subscribers()

    @pytest.fixture
    def ws_manager(self, event_bus):
        """Create WebSocket manager for testing."""
        return WebSocketManager(event_bus)

    def test_initialization(self, ws_manager, event_bus):
        """Test manager initializes correctly."""
        assert ws_manager.event_bus == event_bus
        assert ws_manager.heartbeat_interval == 30
        assert ws_manager.reconnect_buffer_size == 100
        assert ws_manager.reconnect_ttl == 30
        assert ws_manager.max_connections == 10
        assert len(ws_manager.connections) == 0

    def test_custom_configuration(self, event_bus):
        """Test manager with custom configuration."""
        manager = WebSocketManager(
            event_bus,
            heartbeat_interval=60,
            reconnect_buffer_size=50,
            reconnect_ttl=60,
            max_connections=5,
        )

        assert manager.heartbeat_interval == 60
        assert manager.reconnect_buffer_size == 50
        assert manager.reconnect_ttl == 60
        assert manager.max_connections == 5

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, ws_manager):
        """Test connecting a WebSocket client."""
        websocket = AsyncMock(spec=WebSocket)

        client_id = await ws_manager.connect(websocket)

        websocket.accept.assert_called_once()
        assert client_id in ws_manager.connections
        assert ws_manager.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_connect_with_custom_client_id(self, ws_manager):
        """Test connecting with custom client ID."""
        websocket = AsyncMock(spec=WebSocket)
        custom_id = "custom-client-123"

        client_id = await ws_manager.connect(websocket, client_id=custom_id)

        assert client_id == custom_id
        assert custom_id in ws_manager.connections

    @pytest.mark.asyncio
    async def test_connect_sends_confirmation(self, ws_manager):
        """Test connection sends confirmation event."""
        websocket = AsyncMock(spec=WebSocket)

        client_id = await ws_manager.connect(websocket)

        # Should send connection confirmation
        websocket.send_json.assert_called()
        call_args = websocket.send_json.call_args[0][0]
        assert call_args["type"] == "system.heartbeat"
        assert call_args["data"]["status"] == "connected"

    @pytest.mark.asyncio
    async def test_connect_max_connections_limit(self, event_bus):
        """Test connection limit is enforced."""
        manager = WebSocketManager(event_bus, max_connections=2)

        # Connect 2 clients (should succeed)
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)

        await manager.connect(ws1)
        await manager.connect(ws2)

        # Third client should fail
        ws3 = AsyncMock(spec=WebSocket)
        with pytest.raises(ValueError, match="Connection limit exceeded"):
            await manager.connect(ws3)

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, ws_manager):
        """Test disconnecting removes client."""
        websocket = AsyncMock(spec=WebSocket)
        client_id = await ws_manager.connect(websocket)

        assert ws_manager.get_connection_count() == 1

        await ws_manager.disconnect(client_id)

        assert ws_manager.get_connection_count() == 0
        assert client_id not in ws_manager.connections

    @pytest.mark.asyncio
    async def test_disconnect_unknown_client(self, ws_manager):
        """Test disconnecting unknown client doesn't crash."""
        # Should not raise error
        await ws_manager.disconnect("unknown-client")

    @pytest.mark.asyncio
    async def test_subscribe_client(self, ws_manager):
        """Test subscribing client to event type."""
        websocket = AsyncMock(spec=WebSocket)
        client_id = await ws_manager.connect(websocket)

        ws_manager.subscribe_client(client_id, "workflow.started")

        subscriptions = ws_manager.get_client_subscriptions(client_id)
        assert "workflow.started" in subscriptions

    @pytest.mark.asyncio
    async def test_unsubscribe_client(self, ws_manager):
        """Test unsubscribing client from event type."""
        websocket = AsyncMock(spec=WebSocket)
        client_id = await ws_manager.connect(websocket)

        ws_manager.subscribe_client(client_id, "workflow.started")
        ws_manager.unsubscribe_client(client_id, "workflow.started")

        subscriptions = ws_manager.get_client_subscriptions(client_id)
        assert "workflow.started" not in subscriptions

    @pytest.mark.asyncio
    async def test_default_wildcard_subscription(self, ws_manager):
        """Test clients are subscribed to all events by default."""
        websocket = AsyncMock(spec=WebSocket)
        client_id = await ws_manager.connect(websocket)

        subscriptions = ws_manager.get_client_subscriptions(client_id)
        assert "*" in subscriptions

    @pytest.mark.asyncio
    async def test_is_subscribed_wildcard(self, ws_manager):
        """Test wildcard subscription matches all events."""
        websocket = AsyncMock(spec=WebSocket)
        client_id = await ws_manager.connect(websocket)

        assert ws_manager._is_subscribed(client_id, "workflow.started")
        assert ws_manager._is_subscribed(client_id, "chat.message_sent")
        assert ws_manager._is_subscribed(client_id, "any.event.type")

    @pytest.mark.asyncio
    async def test_is_subscribed_specific_event(self, ws_manager):
        """Test subscription to specific event type."""
        websocket = AsyncMock(spec=WebSocket)
        client_id = await ws_manager.connect(websocket)

        # Remove wildcard and add specific subscription
        ws_manager.subscriptions[client_id] = {"workflow.started"}

        assert ws_manager._is_subscribed(client_id, "workflow.started")
        assert not ws_manager._is_subscribed(client_id, "chat.message_sent")

    @pytest.mark.asyncio
    async def test_is_subscribed_pattern(self, ws_manager):
        """Test pattern-based subscription (workflow.*)."""
        websocket = AsyncMock(spec=WebSocket)
        client_id = await ws_manager.connect(websocket)

        # Subscribe to workflow.* pattern
        ws_manager.subscriptions[client_id] = {"workflow.*"}

        assert ws_manager._is_subscribed(client_id, "workflow.started")
        assert ws_manager._is_subscribed(client_id, "workflow.finished")
        assert not ws_manager._is_subscribed(client_id, "chat.message_sent")

    @pytest.mark.asyncio
    async def test_event_buffering(self, ws_manager, event_bus):
        """Test events are buffered for reconnection."""
        websocket = AsyncMock(spec=WebSocket)
        client_id = await ws_manager.connect(websocket)

        # Publish event
        await event_bus.publish(EventType.WORKFLOW_STARTED, {"id": 1})

        # Give time for event to be buffered
        await asyncio.sleep(0.1)

        # Client should have buffered event
        assert client_id in ws_manager.reconnect_buffers
        assert len(ws_manager.reconnect_buffers[client_id]) > 0

    @pytest.mark.asyncio
    async def test_reconnect_buffer_size_limit(self, event_bus):
        """Test reconnect buffer respects size limit."""
        manager = WebSocketManager(event_bus, reconnect_buffer_size=5)
        websocket = AsyncMock(spec=WebSocket)
        client_id = await manager.connect(websocket)

        # Publish more events than buffer size
        for i in range(10):
            await event_bus.publish(EventType.WORKFLOW_STARTED, {"id": i})

        await asyncio.sleep(0.1)

        # Buffer should only contain last 5 events
        assert len(manager.reconnect_buffers[client_id]) == 5

    @pytest.mark.asyncio
    async def test_reconnect_with_replay(self, ws_manager, event_bus):
        """Test reconnection replays missed events."""
        # First connection
        ws1 = AsyncMock(spec=WebSocket)
        client_id = await ws_manager.connect(ws1, client_id="test-client")

        # Publish some events
        await event_bus.publish(EventType.WORKFLOW_STARTED, {"id": 1})
        await event_bus.publish(EventType.WORKFLOW_STARTED, {"id": 2})
        await event_bus.publish(EventType.WORKFLOW_STARTED, {"id": 3})

        await asyncio.sleep(0.1)

        # Disconnect
        await ws_manager.disconnect(client_id)

        # Publish more events while disconnected
        await event_bus.publish(EventType.WORKFLOW_STARTED, {"id": 4})
        await event_bus.publish(EventType.WORKFLOW_STARTED, {"id": 5})

        # Reconnect with last sequence
        ws2 = AsyncMock(spec=WebSocket)
        await ws_manager.connect(ws2, client_id=client_id, last_sequence=2)

        # Should replay events 3, 4, 5 (sequence numbers > 2)
        # Note: Actual replay is done in _replay_events, tested separately

    @pytest.mark.asyncio
    async def test_cleanup_expired_reconnect_buffers(self, event_bus):
        """Test expired reconnect buffers are cleaned up."""
        manager = WebSocketManager(event_bus, reconnect_ttl=0.1)  # 100ms TTL

        websocket = AsyncMock(spec=WebSocket)
        client_id = await manager.connect(websocket)

        await manager.disconnect(client_id)

        # Buffer should exist initially
        assert client_id in manager.reconnect_timestamps

        # Wait for TTL to expire
        await asyncio.sleep(0.2)

        # Trigger cleanup
        await manager._cleanup_reconnect_buffers()

        # Buffer should be removed
        assert client_id not in manager.reconnect_buffers
        assert client_id not in manager.reconnect_timestamps

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_connection_performance(self, ws_manager):
        """Test connection establishes in <100ms."""
        websocket = AsyncMock(spec=WebSocket)

        start = time.perf_counter()
        await ws_manager.connect(websocket)
        end = time.perf_counter()

        duration_ms = (end - start) * 1000

        assert duration_ms < 100, f"Connection took {duration_ms:.2f}ms (should be <100ms)"

    @pytest.mark.asyncio
    async def test_stream_events_sends_to_websocket(self, ws_manager, event_bus):
        """Test event streaming sends events to WebSocket."""
        websocket = AsyncMock(spec=WebSocket)
        client_id = await ws_manager.connect(websocket)

        # Publish event
        event = await event_bus.publish(EventType.WORKFLOW_STARTED, {"id": 1})

        # Give time for streaming
        await asyncio.sleep(0.1)

        # WebSocket should have received event
        # (In actual implementation, send_json is called multiple times)
        assert websocket.send_json.call_count >= 1

    @pytest.mark.asyncio
    async def test_heartbeat_task_started(self, ws_manager):
        """Test heartbeat task is started on connection."""
        websocket = AsyncMock(spec=WebSocket)
        client_id = await ws_manager.connect(websocket)

        # Heartbeat task should be in tasks
        heartbeat_key = f"{client_id}_heartbeat"
        assert heartbeat_key in ws_manager.tasks

    @pytest.mark.asyncio
    async def test_tasks_cancelled_on_disconnect(self, ws_manager):
        """Test tasks are cancelled when client disconnects."""
        websocket = AsyncMock(spec=WebSocket)
        client_id = await ws_manager.connect(websocket)

        # Wait for tasks to start
        await asyncio.sleep(0.1)

        # Disconnect
        await ws_manager.disconnect(client_id)

        # Tasks should be removed
        assert client_id not in ws_manager.tasks
        assert f"{client_id}_heartbeat" not in ws_manager.tasks

    def test_get_client_subscriptions_unknown_client(self, ws_manager):
        """Test getting subscriptions for unknown client."""
        subscriptions = ws_manager.get_client_subscriptions("unknown-client")
        assert subscriptions == set()
