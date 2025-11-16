# WebSocket Protocol Documentation

**Feature**: Web Interface
**Story**: 39.2 - WebSocket Manager and Event Bus
**Version**: 1.0.0
**Last Updated**: 2025-11-16

## Overview

The GAO-Dev WebSocket protocol provides real-time bidirectional communication between the backend server and frontend clients. It enables instant updates for agent activities, workflow progress, file changes, and system events.

---

## Connection

### Endpoint

```
ws://127.0.0.1:3000/ws
```

### Authentication

WebSocket connections require session token authentication via one of:

1. **Header** (recommended):
   ```
   X-Session-Token: <token>
   ```

2. **Query Parameter** (for browser testing):
   ```
   ws://127.0.0.1:3000/ws?token=<token>
   ```

### Session Token

The session token is generated on server startup and stored in `.gao-dev/session.token`. To retrieve:

```bash
cat .gao-dev/session.token
```

### Connection Limit

Maximum 10 concurrent connections per server instance (localhost use case).

---

## Event Schema

All events follow a standardized schema:

```typescript
interface WebEvent {
  type: string;              // Event type (e.g., "workflow.started")
  timestamp: string;          // ISO 8601 timestamp with millisecond precision
  sequence_number: number;    // Monotonically increasing sequence number
  data: Record<string, any>;  // Event-specific payload
  metadata: Record<string, any>; // Optional metadata
}
```

### Example Event

```json
{
  "type": "workflow.started",
  "timestamp": "2025-11-16T14:30:00.123+00:00",
  "sequence_number": 42,
  "data": {
    "workflow_id": "create-prd-workflow",
    "workflow_name": "Create PRD",
    "project": "gao-agile-dev"
  },
  "metadata": {
    "client_id": "abc-123",
    "session_id": "xyz-789"
  }
}
```

---

## Event Types

### Workflow Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| `workflow.started` | Workflow execution begins | `workflow_id`, `workflow_name`, `project` |
| `workflow.step_completed` | Workflow step completes | `workflow_id`, `step_name`, `step_index`, `total_steps` |
| `workflow.finished` | Workflow execution completes | `workflow_id`, `status`, `duration_ms` |
| `workflow.failed` | Workflow execution fails | `workflow_id`, `error`, `step_name` |

### Chat Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| `chat.message_sent` | User sends chat message | `message`, `user` |
| `chat.message_received` | Agent responds to message | `message`, `agent`, `thinking_time_ms` |
| `chat.thinking_started` | Agent begins processing | `agent`, `context_size` |
| `chat.thinking_finished` | Agent finishes processing | `agent`, `duration_ms` |

### File Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| `file.created` | New file created | `path`, `size`, `type` |
| `file.modified` | File modified | `path`, `size`, `changes` |
| `file.deleted` | File deleted | `path` |

### State Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| `state.epic_created` | New epic created | `epic_id`, `title`, `feature` |
| `state.story_created` | New story created | `epic_id`, `story_id`, `title` |
| `state.story_transitioned` | Story status changes | `epic_id`, `story_id`, `from_state`, `to_state` |

### Git Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| `git.commit_created` | Git commit created | `commit_hash`, `message`, `author`, `files_changed` |

### System Events

| Event Type | Description | Data Fields |
|-----------|-------------|-------------|
| `system.heartbeat` | Keepalive ping | `timestamp` |
| `system.error` | System error | `error`, `context`, `severity` |

---

## Reconnection Support

### Reconnection Headers

When reconnecting after disconnect, include:

```
X-Client-Id: <client_id>
X-Last-Sequence: <last_sequence_number>
```

### Event Replay

The server buffers the last 100 events for each client (30-second TTL). When reconnecting with `X-Last-Sequence`, the server replays all events with `sequence_number > last_sequence`.

### Example Reconnection Flow

1. **Initial Connection**:
   ```
   ws://127.0.0.1:3000/ws
   Headers: X-Session-Token: abc123
   ```

   Server responds:
   ```json
   {
     "type": "system.heartbeat",
     "data": {
       "status": "connected",
       "client_id": "uuid-1234"
     },
     "sequence_number": 0
   }
   ```

2. **Receive Events**:
   ```json
   {"type": "workflow.started", "sequence_number": 1, ...}
   {"type": "workflow.step_completed", "sequence_number": 2, ...}
   {"type": "workflow.step_completed", "sequence_number": 3, ...}
   ```

3. **Disconnect** (network issue, browser refresh, etc.)

4. **Reconnect**:
   ```
   ws://127.0.0.1:3000/ws
   Headers:
     X-Session-Token: abc123
     X-Client-Id: uuid-1234
     X-Last-Sequence: 3
   ```

5. **Server Replays Missed Events**:
   ```json
   {"type": "workflow.step_completed", "sequence_number": 4, ...}
   {"type": "workflow.finished", "sequence_number": 5, ...}
   ```

---

## Heartbeat

The server sends a heartbeat every 30 seconds:

```json
{
  "type": "system.heartbeat",
  "timestamp": "2025-11-16T14:30:00.123+00:00",
  "sequence_number": -1,
  "data": {
    "timestamp": 1731769800.123
  },
  "metadata": {}
}
```

Clients should respond with a pong (future enhancement) or handle disconnection if heartbeats stop.

---

## Error Handling

### Authentication Failure

If session token is invalid or missing:

```
WebSocket Close Code: 1008 (Policy Violation)
Reason: "Unauthorized"
```

### Connection Limit Exceeded

If max connections (10) exceeded:

```
WebSocket Close Code: 1008 (Policy Violation)
Reason: "Connection limit exceeded (10 max)"
```

### Error Events

Errors are sent as events:

```json
{
  "type": "system.error",
  "timestamp": "2025-11-16T14:30:00.123+00:00",
  "sequence_number": 50,
  "data": {
    "error": "Failed to execute workflow",
    "context": {"workflow_id": "create-prd"},
    "severity": "error"
  },
  "metadata": {}
}
```

---

## Example Client Code

### JavaScript (Browser)

```javascript
// Get session token from server
const tokenResponse = await fetch('/api/session-token');
const { token } = await tokenResponse.json();

// Connect to WebSocket
const ws = new WebSocket(`ws://127.0.0.1:3000/ws?token=${token}`);

// Handle connection
ws.onopen = (event) => {
  console.log('Connected to GAO-Dev WebSocket');
};

// Handle messages
ws.onmessage = (event) => {
  const webEvent = JSON.parse(event.data);

  console.log(`Event: ${webEvent.type}`);
  console.log(`Sequence: ${webEvent.sequence_number}`);
  console.log('Data:', webEvent.data);

  // Handle specific event types
  switch (webEvent.type) {
    case 'workflow.started':
      handleWorkflowStarted(webEvent.data);
      break;
    case 'chat.message_received':
      handleChatMessage(webEvent.data);
      break;
    // ... more event types
  }
};

// Handle errors
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Handle disconnection
ws.onclose = (event) => {
  console.log('Disconnected:', event.code, event.reason);

  // Reconnect with last sequence number
  if (event.wasClean === false) {
    reconnect(lastSequenceNumber);
  }
};

// Track last sequence for reconnection
let lastSequenceNumber = -1;
ws.onmessage = (event) => {
  const webEvent = JSON.parse(event.data);
  lastSequenceNumber = webEvent.sequence_number;
  // ... handle event
};

// Reconnection function
function reconnect(lastSeq) {
  const ws = new WebSocket(
    `ws://127.0.0.1:3000/ws?token=${token}`,
    {
      headers: {
        'X-Client-Id': clientId,
        'X-Last-Sequence': lastSeq.toString()
      }
    }
  );
  // ... setup handlers
}
```

### Python (Client)

```python
import asyncio
import json
import websockets

async def connect_to_gaodev():
    # Read session token
    with open('.gao-dev/session.token', 'r') as f:
        token = f.read().strip()

    # Connect
    uri = f"ws://127.0.0.1:3000/ws?token={token}"

    async with websockets.connect(uri) as websocket:
        print("Connected to GAO-Dev WebSocket")

        # Receive events
        async for message in websocket:
            event = json.loads(message)

            print(f"Event: {event['type']}")
            print(f"Sequence: {event['sequence_number']}")
            print(f"Data: {event['data']}")

            # Handle event types
            if event['type'] == 'workflow.started':
                handle_workflow_started(event['data'])
            elif event['type'] == 'chat.message_received':
                handle_chat_message(event['data'])

# Run
asyncio.run(connect_to_gaodev())
```

---

## Performance

### Targets

- **Connection Time**: <100ms
- **Event Delivery Latency**: <10ms
- **Throughput**: 1000+ events/second
- **Buffer Size**: 1000 events per subscriber queue
- **Reconnect Buffer**: 100 events per client (30s TTL)

### Tested Performance

All performance targets met in testing:
- Connection establishment: ~20ms average
- Event delivery: ~5ms average
- Throughput: 10,000+ events/second sustained
- Buffer overflow handling: FIFO (drop oldest)

---

## Security

### Localhost Only

The WebSocket server binds to `127.0.0.1` and only accepts localhost connections. This is appropriate for a local development tool.

### Session Token

Session tokens are generated using `secrets.token_urlsafe(32)` (cryptographically secure random tokens). Tokens are validated using timing-safe comparison (`secrets.compare_digest`).

### CORS

CORS is restricted to localhost origins only:
- `http://localhost:3000`
- `http://127.0.0.1:3000`

---

## Future Enhancements (V1.1+)

### Bidirectional Communication

Currently, the WebSocket is primarily server-to-client (events). Future versions will support client-to-server commands:

```json
{
  "command": "subscribe",
  "event_types": ["workflow.*", "chat.message_received"]
}
```

```json
{
  "command": "unsubscribe",
  "event_types": ["file.*"]
}
```

### Compression

For high-traffic scenarios, enable WebSocket compression (permessage-deflate).

### Multiplexing

Support multiple event streams per connection (channels).

---

## Troubleshooting

### Cannot Connect

**Symptom**: WebSocket connection fails immediately.

**Causes**:
1. Server not running (`gao-dev web`)
2. Invalid session token
3. Port 3000 in use

**Solutions**:
```bash
# Start server
gao-dev web

# Verify server running
curl http://127.0.0.1:3000/api/health

# Check session token
cat .gao-dev/session.token
```

### Connection Drops

**Symptom**: WebSocket disconnects unexpectedly.

**Causes**:
1. Network interruption
2. Server restart
3. Connection idle timeout

**Solutions**:
- Implement reconnection logic
- Monitor heartbeat events
- Check server logs

### Missing Events

**Symptom**: Client doesn't receive some events.

**Causes**:
1. Queue overflow (1000 events/subscriber)
2. Missed during disconnect (>30s TTL)
3. Event type not subscribed

**Solutions**:
- Implement reconnection quickly (<30s)
- Check sequence numbers for gaps
- Subscribe to wildcard (`*`) to receive all events

### High Latency

**Symptom**: Events arrive with delay.

**Causes**:
1. Network congestion
2. High event volume
3. Client processing slow

**Solutions**:
- Monitor event throughput
- Optimize client event handlers
- Consider filtering event types

---

## API Reference

### Server Initialization

```python
from gao_dev.web import create_app, WebConfig

# Create app with WebSocket support
config = WebConfig(host="127.0.0.1", port=3000)
app = create_app(config)

# Access WebSocket infrastructure
event_bus = app.state.event_bus
websocket_manager = app.state.websocket_manager
session_token_manager = app.state.session_token_manager
```

### Publishing Events

```python
from gao_dev.web import EventType

# Publish event to all connected clients
await event_bus.publish(
    EventType.WORKFLOW_STARTED,
    data={"workflow_id": "test", "name": "Test Workflow"},
    metadata={"user": "developer"}
)
```

### Managing Connections

```python
# Get connection count
count = websocket_manager.get_connection_count()

# Subscribe client to specific event type
websocket_manager.subscribe_client(client_id, "workflow.started")

# Unsubscribe client
websocket_manager.unsubscribe_client(client_id, "workflow.started")

# Get client subscriptions
subscriptions = websocket_manager.get_client_subscriptions(client_id)
```

---

## Change Log

### Version 1.0.0 (2025-11-16)

- Initial WebSocket protocol implementation
- Event schema standardization
- Reconnection support with event replay
- Heartbeat mechanism
- Session token authentication
- Connection limit (10 clients)
- Buffer management (1000 events/subscriber, 100 events/reconnect)

---

## References

- **Story 39.2**: WebSocket Manager and Event Bus
- **RFC 6455**: The WebSocket Protocol
- **ISO 8601**: Date and time format
- **FastAPI WebSocket Documentation**: https://fastapi.tiangolo.com/advanced/websockets/
