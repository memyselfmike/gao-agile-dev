# Story 39.2: WebSocket Manager and Event Bus

**Story Number**: 39.2
**Epic**: 39.1 - Backend Foundation
**Feature**: Web Interface
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort Estimate**: M (Medium - 3 story points)
**Dependencies**: Story 39.1 (FastAPI Web Server)

---

## User Story

As a **product owner**
I want **real-time WebSocket communication between backend and frontend**
So that **I can see agent activities instantly without polling and experience smooth, responsive updates**

---

## Acceptance Criteria

### WebSocket Connection
- [ ] AC1: WebSocket endpoint available at `/ws` (ws://127.0.0.1:3000/ws)
- [ ] AC2: Connection requires session token in upgrade header: `X-Session-Token`
- [ ] AC3: Invalid/missing token returns 401 Unauthorized
- [ ] AC4: Connection establishes in <100ms
- [ ] AC5: Heartbeat/ping sent every 30 seconds to keep connection alive
- [ ] AC6: Client receives pong response within 5 seconds

### Event Bus Architecture
- [ ] AC7: WebEventBus implemented using asyncio.Queue (in-memory, no Redis)
- [ ] AC8: Event bus supports pub/sub pattern with typed event subscriptions
- [ ] AC9: Multiple subscribers can listen to same event type
- [ ] AC10: Events published to bus appear in subscriber queues within <10ms
- [ ] AC11: Buffer size: 1000 events per subscriber queue
- [ ] AC12: Overflow policy: Drop oldest event when buffer full (FIFO)

### Event Schema
- [ ] AC13: All events follow standardized schema: `{type, timestamp, sequence_number, data, metadata}`
- [ ] AC14: Event types defined: `workflow.*`, `chat.*`, `file.*`, `state.*`, `ceremony.*`, `git.*`
- [ ] AC15: Sequence numbers monotonically increase (detect missed events)
- [ ] AC16: Timestamps are ISO 8601 format with millisecond precision

### WebSocket Manager
- [ ] AC17: WebSocketManager tracks all active client connections
- [ ] AC18: Manager broadcasts events to all connected clients
- [ ] AC19: Per-client subscription filters (client can subscribe to specific event types)
- [ ] AC20: Disconnected clients automatically unsubscribed
- [ ] AC21: Connection limit: 10 concurrent clients (localhost use case)

### Reconnection Support
- [ ] AC22: Server buffers events for 30 seconds during disconnect
- [ ] AC23: Client reconnects with last sequence number received
- [ ] AC24: Server replays missed events from reconnect buffer
- [ ] AC25: Reconnect buffer size: 100 events per client

### Error Handling
- [ ] AC26: WebSocket errors logged with context (client ID, error type)
- [ ] AC27: Client receives error message: `{type: "error", message: "..."}`
- [ ] AC28: Server continues operating if single client disconnects

---

## Technical Context

### Architecture Integration

**Event Bus Design**:
```python
class WebEvent:
    type: str                    # "workflow.started", "chat.message", etc.
    timestamp: datetime
    sequence_number: int
    data: Dict[str, Any]
    metadata: Dict[str, Any]

class WebEventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        self.sequence_counter = 0

    def subscribe(self, event_type: str) -> asyncio.Queue:
        queue = asyncio.Queue(maxsize=1000)
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(queue)
        return queue

    async def publish(self, event: WebEvent):
        event.sequence_number = self.sequence_counter
        self.sequence_counter += 1

        if event.type in self.subscribers:
            for queue in self.subscribers[event.type]:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    # Drop oldest event
                    queue.get_nowait()
                    queue.put_nowait(event)
```

**WebSocket Manager**:
```python
class WebSocketManager:
    def __init__(self, event_bus: WebEventBus):
        self.event_bus = event_bus
        self.connections: Dict[str, WebSocket] = {}
        self.reconnect_buffers: Dict[str, List[WebEvent]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.connections[client_id] = websocket

        # Start event streaming task
        asyncio.create_task(self.stream_events(websocket, client_id))

    async def stream_events(self, websocket: WebSocket, client_id: str):
        queue = self.event_bus.subscribe("*")  # Subscribe to all events
        try:
            while True:
                event = await queue.get()
                await websocket.send_json(event.to_dict())
        except WebSocketDisconnect:
            self.disconnect(client_id)
```

### Dependencies

**Epic 30 (ChatREPL)**:
- BrianWebAdapter will publish chat events to this event bus (Story 39.7)

**Epic 27 (GitIntegratedStateManager)**:
- StateChangeAdapter will publish state events to this event bus (Story 39.11)

**Epic 28 (CeremonyOrchestrator)**:
- CeremonyAdapter will publish ceremony events to this event bus (Future V1.2)

### Event Types

**Core Event Types** (MVP):
- `workflow.started`, `workflow.step_completed`, `workflow.finished`, `workflow.failed`
- `chat.message_sent`, `chat.message_received`, `chat.thinking_started`, `chat.thinking_finished`
- `file.created`, `file.modified`, `file.deleted`
- `state.epic_created`, `state.story_created`, `state.story_transitioned`
- `git.commit_created`

**Future Event Types** (V1.1+):
- `ceremony.started`, `ceremony.message`, `ceremony.ended`
- `kanban.card_moved`, `kanban.card_updated`

---

## Test Scenarios

### Test 1: WebSocket Connection Establishment
**Given**: FastAPI server is running
**When**: Client connects to ws://127.0.0.1:3000/ws with valid session token
**Then**:
- Connection established in <100ms
- Client receives connection confirmation
- Heartbeat/ping sent every 30 seconds

### Test 2: Event Publishing and Broadcasting
**Given**: 3 clients connected via WebSocket
**When**: Event published to event bus: `{type: "workflow.started", data: {...}}`
**Then**:
- All 3 clients receive event within 10ms
- Event includes sequence number
- Event includes timestamp

### Test 3: Buffer Overflow Handling
**Given**: Client has 1000 events in queue
**When**: New event published
**Then**:
- Oldest event dropped
- New event added to queue
- Queue size remains 1000

### Test 4: Reconnection with Event Replay
**Given**: Client disconnects with last sequence number 100
**When**: Client reconnects 10 seconds later
**Then**:
- Server replays events 101-110 from reconnect buffer
- Client receives all missed events
- Event stream continues normally

### Test 5: Authentication Failure
**Given**: Client attempts connection without session token
**When**: Upgrade request sent
**Then**:
- Server returns 401 Unauthorized
- Connection rejected
- Error logged

---

## Definition of Done

### Code Quality
- [ ] Code follows GAO-Dev standards (DRY, SOLID, typed)
- [ ] Type hints throughout (no `Any`)
- [ ] structlog for all logging
- [ ] Error handling comprehensive
- [ ] Black formatting applied (line length 100)

### Testing
- [ ] Unit tests: 100% coverage for event_bus.py, websocket_manager.py
- [ ] Integration tests: WebSocket connection, event broadcasting, reconnection
- [ ] Load tests: 1000+ events/second, 10 concurrent clients
- [ ] Performance tests: <100ms connection, <10ms event delivery

### Documentation
- [ ] API documentation: WebSocket protocol, event schema
- [ ] Event catalog: All event types documented
- [ ] Troubleshooting: Connection issues, buffer overflow

### Code Review
- [ ] Code review approved by Winston (Technical Architect)
- [ ] Security review: Session token validation
- [ ] Performance review: Event bus scalability

---

## Implementation Notes

### Session Token Authentication

```python
# gao_dev/web/auth.py
import secrets
import structlog

logger = structlog.get_logger(__name__)

class SessionTokenManager:
    def __init__(self):
        self.token = secrets.token_urlsafe(32)  # Generated on server start

    def validate(self, token: str) -> bool:
        return token == self.token

# FastAPI WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.headers.get("X-Session-Token")
    if not session_token_manager.validate(token):
        await websocket.close(code=1008, reason="Unauthorized")
        return

    client_id = str(uuid.uuid4())
    await websocket_manager.connect(websocket, client_id)
```

### Event Bus Performance

**Memory Estimation**:
- Event size: ~1KB average
- Buffer per subscriber: 1000 events = ~1MB
- Max subscribers: 50 (10 clients × 5 event types average)
- Total memory: ~50MB (acceptable)

**Throughput**:
- asyncio.Queue: 100,000+ ops/second
- Expected load: <1,000 events/second
- Headroom: 100x

---

## Related Stories

- **Story 39.1**: FastAPI Web Server Setup (foundation)
- **Story 39.3**: Session Lock and Read-Only Mode (uses session token)
- **Story 39.7**: Brian Chat Component (publishes chat events)
- **Story 39.9**: Real-Time Activity Stream (consumes all events)

---

**Story Owner**: Amelia (Software Developer)
**Reviewer**: Winston (Technical Architect)
**Tester**: Murat (Test Architect)
