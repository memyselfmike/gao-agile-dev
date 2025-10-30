"""Event system for GAO-Dev using Observer Pattern."""

from .event_bus import EventBus, Event

__all__ = ["EventBus", "Event"]
