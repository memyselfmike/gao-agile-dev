"""Unit tests for event bus."""

import asyncio
import time

import pytest

from gao_dev.web.event_bus import WebEventBus
from gao_dev.web.events import EventType


class TestWebEventBus:
    """Tests for WebEventBus."""

    @pytest.fixture
    def event_bus(self):
        """Create event bus for testing."""
        bus = WebEventBus()
        yield bus
        bus.clear_all_subscribers()

    def test_initialization(self, event_bus):
        """Test event bus initializes correctly."""
        assert event_bus.max_queue_size == 1000
        assert event_bus.sequence_counter == 0
        assert len(event_bus.subscribers) == 0

    def test_custom_queue_size(self):
        """Test event bus with custom queue size."""
        bus = WebEventBus(max_queue_size=500)
        assert bus.max_queue_size == 500

    def test_subscribe_creates_queue(self, event_bus):
        """Test subscribing creates a queue."""
        queue = event_bus.subscribe("workflow.started")

        assert isinstance(queue, asyncio.Queue)
        assert queue.maxsize == 1000
        assert event_bus.get_subscriber_count("workflow.started") == 1

    def test_subscribe_multiple_subscribers(self, event_bus):
        """Test multiple subscribers to same event type."""
        queue1 = event_bus.subscribe("chat.message_sent")
        queue2 = event_bus.subscribe("chat.message_sent")
        queue3 = event_bus.subscribe("chat.message_sent")

        assert event_bus.get_subscriber_count("chat.message_sent") == 3

    def test_subscribe_different_event_types(self, event_bus):
        """Test subscribing to different event types."""
        queue1 = event_bus.subscribe("workflow.started")
        queue2 = event_bus.subscribe("chat.message_sent")
        queue3 = event_bus.subscribe("file.created")

        assert event_bus.get_subscriber_count("workflow.started") == 1
        assert event_bus.get_subscriber_count("chat.message_sent") == 1
        assert event_bus.get_subscriber_count("file.created") == 1
        assert event_bus.get_total_subscribers() == 3

    def test_subscribe_wildcard(self, event_bus):
        """Test subscribing to all events with wildcard."""
        queue = event_bus.subscribe("*")

        assert event_bus.get_subscriber_count("*") == 1

    @pytest.mark.asyncio
    async def test_publish_delivers_to_subscriber(self, event_bus):
        """Test publishing event delivers to subscriber."""
        queue = event_bus.subscribe("workflow.started")

        event = await event_bus.publish(
            EventType.WORKFLOW_STARTED,
            {"workflow_id": "test-workflow"},
        )

        # Event should be in queue
        received_event = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert received_event.type == "workflow.started"
        assert received_event.data == {"workflow_id": "test-workflow"}
        assert received_event.sequence_number == 0

    @pytest.mark.asyncio
    async def test_publish_multiple_subscribers(self, event_bus):
        """Test publishing delivers to all subscribers."""
        queue1 = event_bus.subscribe("chat.message_sent")
        queue2 = event_bus.subscribe("chat.message_sent")
        queue3 = event_bus.subscribe("chat.message_sent")

        await event_bus.publish(
            EventType.CHAT_MESSAGE_SENT,
            {"message": "Hello"},
        )

        # All subscribers should receive event
        event1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
        event2 = await asyncio.wait_for(queue2.get(), timeout=1.0)
        event3 = await asyncio.wait_for(queue3.get(), timeout=1.0)

        assert event1.data == {"message": "Hello"}
        assert event2.data == {"message": "Hello"}
        assert event3.data == {"message": "Hello"}

    @pytest.mark.asyncio
    async def test_publish_wildcard_receives_all(self, event_bus):
        """Test wildcard subscriber receives all event types."""
        wildcard_queue = event_bus.subscribe("*")

        await event_bus.publish(EventType.WORKFLOW_STARTED, {"id": 1})
        await event_bus.publish(EventType.CHAT_MESSAGE_SENT, {"id": 2})
        await event_bus.publish(EventType.FILE_CREATED, {"id": 3})

        # Wildcard should receive all 3 events
        event1 = await asyncio.wait_for(wildcard_queue.get(), timeout=1.0)
        event2 = await asyncio.wait_for(wildcard_queue.get(), timeout=1.0)
        event3 = await asyncio.wait_for(wildcard_queue.get(), timeout=1.0)

        assert event1.data == {"id": 1}
        assert event2.data == {"id": 2}
        assert event3.data == {"id": 3}

    @pytest.mark.asyncio
    async def test_publish_pattern_subscription(self, event_bus):
        """Test pattern-based subscriptions (e.g., workflow.*)."""
        workflow_queue = event_bus.subscribe("workflow.*")

        await event_bus.publish(EventType.WORKFLOW_STARTED, {"id": 1})
        await event_bus.publish(EventType.WORKFLOW_FINISHED, {"id": 2})
        await event_bus.publish(EventType.CHAT_MESSAGE_SENT, {"id": 3})  # Different pattern

        # Should receive workflow events only
        event1 = await asyncio.wait_for(workflow_queue.get(), timeout=1.0)
        event2 = await asyncio.wait_for(workflow_queue.get(), timeout=1.0)

        assert event1.data == {"id": 1}
        assert event2.data == {"id": 2}

        # Queue should be empty (no chat event)
        assert workflow_queue.empty()

    @pytest.mark.asyncio
    async def test_publish_no_subscribers(self, event_bus):
        """Test publishing with no subscribers doesn't crash."""
        # Should not raise error
        event = await event_bus.publish(
            EventType.WORKFLOW_STARTED,
            {"workflow_id": "test"},
        )

        assert event.sequence_number == 0

    @pytest.mark.asyncio
    async def test_sequence_numbers_increment(self, event_bus):
        """Test sequence numbers increment monotonically."""
        queue = event_bus.subscribe("*")

        await event_bus.publish(EventType.WORKFLOW_STARTED, {})
        await event_bus.publish(EventType.WORKFLOW_STARTED, {})
        await event_bus.publish(EventType.WORKFLOW_STARTED, {})

        event1 = await queue.get()
        event2 = await queue.get()
        event3 = await queue.get()

        assert event1.sequence_number == 0
        assert event2.sequence_number == 1
        assert event3.sequence_number == 2

    @pytest.mark.asyncio
    async def test_queue_overflow_drops_oldest(self, event_bus):
        """Test queue overflow drops oldest event (FIFO)."""
        # Create bus with small queue
        small_bus = WebEventBus(max_queue_size=3)
        queue = small_bus.subscribe("workflow.started")

        # Fill queue to capacity
        await small_bus.publish(EventType.WORKFLOW_STARTED, {"id": 1})
        await small_bus.publish(EventType.WORKFLOW_STARTED, {"id": 2})
        await small_bus.publish(EventType.WORKFLOW_STARTED, {"id": 3})

        # Queue should be full
        assert queue.qsize() == 3

        # Add one more event - should drop oldest
        await small_bus.publish(EventType.WORKFLOW_STARTED, {"id": 4})

        # Queue should still have 3 events
        assert queue.qsize() == 3

        # First event should be id=2 (id=1 was dropped)
        event1 = await queue.get()
        event2 = await queue.get()
        event3 = await queue.get()

        assert event1.data["id"] == 2
        assert event2.data["id"] == 3
        assert event3.data["id"] == 4

    def test_unsubscribe(self, event_bus):
        """Test unsubscribing removes queue."""
        queue = event_bus.subscribe("workflow.started")
        assert event_bus.get_subscriber_count("workflow.started") == 1

        event_bus.unsubscribe("workflow.started", queue)
        assert event_bus.get_subscriber_count("workflow.started") == 0

    def test_unsubscribe_one_of_many(self, event_bus):
        """Test unsubscribing one queue leaves others."""
        queue1 = event_bus.subscribe("chat.message_sent")
        queue2 = event_bus.subscribe("chat.message_sent")
        queue3 = event_bus.subscribe("chat.message_sent")

        event_bus.unsubscribe("chat.message_sent", queue2)

        assert event_bus.get_subscriber_count("chat.message_sent") == 2

    def test_unsubscribe_nonexistent_queue(self, event_bus):
        """Test unsubscribing nonexistent queue doesn't crash."""
        fake_queue = asyncio.Queue()

        # Should not raise error
        event_bus.unsubscribe("workflow.started", fake_queue)

    def test_get_event_types(self, event_bus):
        """Test getting all event types with subscribers."""
        event_bus.subscribe("workflow.started")
        event_bus.subscribe("chat.message_sent")
        event_bus.subscribe("file.created")

        event_types = event_bus.get_event_types()

        assert "workflow.started" in event_types
        assert "chat.message_sent" in event_types
        assert "file.created" in event_types
        assert len(event_types) == 3

    def test_clear_all_subscribers(self, event_bus):
        """Test clearing all subscribers."""
        event_bus.subscribe("workflow.started")
        event_bus.subscribe("chat.message_sent")
        event_bus.subscribe("file.created")

        assert event_bus.get_total_subscribers() == 3

        event_bus.clear_all_subscribers()

        assert event_bus.get_total_subscribers() == 0
        assert len(event_bus.get_event_types()) == 0

    @pytest.mark.asyncio
    async def test_publish_with_metadata(self, event_bus):
        """Test publishing event with metadata."""
        queue = event_bus.subscribe("workflow.started")

        metadata = {"client_id": "test-client", "session_id": "test-session"}
        event = await event_bus.publish(
            EventType.WORKFLOW_STARTED,
            {"workflow_id": "test"},
            metadata=metadata,
        )

        received = await queue.get()
        assert received.metadata == metadata

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_event_delivery_performance(self, event_bus):
        """Test event delivery is fast (<10ms)."""
        queue = event_bus.subscribe("*")

        start = time.perf_counter()
        await event_bus.publish(EventType.WORKFLOW_STARTED, {})
        received = await queue.get()
        end = time.perf_counter()

        duration_ms = (end - start) * 1000

        assert duration_ms < 10, f"Event delivery took {duration_ms:.2f}ms (should be <10ms)"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_high_throughput(self, event_bus):
        """Test bus can handle high event throughput."""
        queue = event_bus.subscribe("*")

        # Publish 1000 events
        start = time.perf_counter()
        for i in range(1000):
            await event_bus.publish(EventType.WORKFLOW_STARTED, {"id": i})
        end = time.perf_counter()

        duration_ms = (end - start) * 1000
        events_per_second = 1000 / (duration_ms / 1000)

        # Should handle at least 1000 events/second
        assert events_per_second > 1000, f"Throughput: {events_per_second:.0f} events/s"

    @pytest.mark.asyncio
    async def test_thread_safe_sequence_counter(self, event_bus):
        """Test sequence counter is thread-safe."""
        import concurrent.futures

        queue = event_bus.subscribe("*")

        # Publish events from multiple threads
        def publish_events():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            for _ in range(10):
                loop.run_until_complete(
                    event_bus.publish(EventType.WORKFLOW_STARTED, {})
                )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(publish_events) for _ in range(5)]
            concurrent.futures.wait(futures)

        # Should have 50 unique sequence numbers (5 threads × 10 events)
        sequence_numbers = set()
        while not queue.empty():
            event = await queue.get()
            sequence_numbers.add(event.sequence_number)

        assert len(sequence_numbers) == 50
