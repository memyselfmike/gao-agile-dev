"""Tests for EventBus."""

from gao_dev.core.events.event_bus import EventBus, Event


class TestEventBus:
    def test_subscribe_and_publish(self):
        """Test basic pub/sub."""
        bus = EventBus()
        events_received = []

        def handler(event: Event):
            events_received.append(event)

        bus.subscribe("test_event", handler)
        bus.publish(Event("test_event", {"key": "value"}))

        assert len(events_received) == 1
        assert events_received[0].type == "test_event"

    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event."""
        bus = EventBus()
        calls = {"handler1": 0, "handler2": 0}

        def handler1(event: Event):
            calls["handler1"] += 1

        def handler2(event: Event):
            calls["handler2"] += 1

        bus.subscribe("event", handler1)
        bus.subscribe("event", handler2)
        bus.publish(Event("event"))

        assert calls["handler1"] == 1
        assert calls["handler2"] == 1

    def test_unsubscribe(self):
        """Test unsubscribing."""
        bus = EventBus()
        calls = []

        def handler(event: Event):
            calls.append(event)

        bus.subscribe("event", handler)
        bus.publish(Event("event"))
        bus.unsubscribe("event", handler)
        bus.publish(Event("event"))

        assert len(calls) == 1
