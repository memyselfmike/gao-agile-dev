# Story 39.9: Real-Time Activity Stream

**Story Number**: 39.9
**Epic**: 39.3 - Core Observability
**Status**: Complete
**Priority**: MUST HAVE (P0)
**Effort**: L (Large - 5 points)
**Dependencies**: Story 39.2 (WebSocket + Event Bus), Story 39.5 (Layout)

## User Story
As a **user**, I want **to see a real-time feed of all agent activities** so that **I understand what agents are doing and trust the autonomous process**.

## Acceptance Criteria
- [x] AC1: Event cards display: timestamp, agent, action, summary
- [x] AC2: Time window selector: 1h (default), 6h, 24h, 7d, 30d, All
- [x] AC3: Progressive disclosure: Click event to expand details
- [x] AC4: Shallow view: "Winston is creating ARCHITECTURE.md"
- [x] AC5: Deep view: Agent reasoning, tool calls, file diffs
- [x] AC6: Auto-scroll on new events (with pause option)
- [x] AC7: Virtual scrolling for >10,000 events (@tanstack/react-virtual)
- [x] AC8: Real-time updates via WebSocket (<100ms latency)
- [x] AC9: Event types: Workflow, Chat, File, State, Ceremony, Git
- [x] AC10: "Load more" for older events beyond time window
- [x] AC11: Event sequence numbers displayed (detect missed events)
- [x] AC12: Reconnection replays missed events from buffer

## Technical Context
**Event Bus**: Subscribes to all event types via WebSocket
**Rendering**: Virtual scrolling prevents DOM bloat
**Buffer**: Default 1000 events client-side, time windows for older
