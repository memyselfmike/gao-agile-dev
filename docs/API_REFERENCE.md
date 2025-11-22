# API Reference: GAO-Dev Web Interface

## TL;DR

**What**: Complete reference for all REST endpoints and WebSocket events in GAO-Dev Web Interface

**When**: Use when integrating with the API, handling events, or troubleshooting

**Key Points**:
- 50+ REST endpoints organized by feature
- 25+ WebSocket events for real-time updates
- Token-based authentication required for most endpoints
- WebSocket connection auto-reconnects with exponential backoff
- All endpoints return JSON, events are JSON-formatted messages

**Quick Links**:
- [Quick Start Guide](QUICK_START.md) - Integration patterns
- [Web Interface Architecture](features/web-interface/ARCHITECTURE.md) - System overview
- [Authentication](#authentication) - How to get/use session tokens

---

## Table of Contents

- [REST Endpoints](#rest-endpoints)
  - [System](#system-endpoints)
  - [Chat](#chat-endpoints)
  - [Files](#file-endpoints)
  - [Git](#git-endpoints)
  - [Workflows](#workflow-endpoints)
  - [Kanban](#kanban-endpoints)
  - [Settings](#settings-endpoints)
  - [Direct Messages](#direct-message-endpoints)
  - [Channels](#channel-endpoints)
  - [Threads](#thread-endpoints)
  - [Search](#search-endpoints)
  - [Onboarding](#onboarding-endpoints)
- [WebSocket Events](#websocket-events)
- [Quick Reference](#quick-reference)
  - [Authentication](#authentication)
  - [Error Codes](#error-codes)
  - [WebSocket Connection](#websocket-connection)

---

## REST Endpoints

### System Endpoints

| Method | Endpoint | Purpose | Auth | Request | Response |
|--------|----------|---------|------|---------|----------|
| GET | `/api/health` | Health check | No | None | `{status: "ok", version: "1.0.0"}` |
| GET | `/api/session/token` | Get session token | No | None | `{token: "uuid"}` |
| GET | `/api/agents` | List all agents | Token | None | `{agents: Agent[]}` |
| GET | `/api/session/lock-state` | Check CLI lock state | Token | None | `{is_locked: bool, locked_by: str}` |

**Example: Health Check**
```bash
curl http://localhost:3000/api/health
# Response: {"status": "ok", "version": "1.0.0"}
```

---

### Chat Endpoints

| Method | Endpoint | Purpose | Auth | Request | Response |
|--------|----------|---------|------|---------|----------|
| POST | `/api/chat` | Send message to agent | Token | `{message: str, agent: str}` | Streaming response |
| GET | `/api/chat/history` | Get chat history | Token | `?agent=brian&limit=50` | `{messages: Message[]}` |
| GET | `/api/chat/context` | Get execution context | Token | None | `{project_root: str, active_workflows: []}` |

**Example: Send Chat Message**
```bash
curl -X POST http://localhost:3000/api/chat \
  -H "X-Session-Token: your-token" \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a new feature", "agent": "Brian"}'
# Response: Streaming SSE events with agent responses
```

---

### File Endpoints

| Method | Endpoint | Purpose | Auth | Request | Response |
|--------|----------|---------|------|---------|----------|
| GET | `/api/files/tree` | Get file tree | Token | `?path=/&depth=3` | `{tree: FileNode[]}` |
| GET | `/api/files/content` | Get file contents | Token | `?path=src/main.py` | `{path: str, content: str, language: str}` |
| POST | `/api/files/save` | Save file | Token | `{path: str, content: str}` | `{success: bool, commit_sha: str}` |
| GET | `/api/files/diff` | Get file diff | Token | `?path=src/main.py` | `{hunks: DiffHunk[]}` |

**Example: Get File Tree**
```bash
curl http://localhost:3000/api/files/tree?path=/&depth=2 \
  -H "X-Session-Token: your-token"
# Response: {
#   "tree": [
#     {"name": "src", "type": "directory", "children": [...]},
#     {"name": "README.md", "type": "file", "size": 1024}
#   ]
# }
```

---

### Git Endpoints

| Method | Endpoint | Purpose | Auth | Request | Response |
|--------|----------|---------|------|---------|----------|
| GET | `/api/git/commits` | List commits | Token | `?limit=50&offset=0&author=brian` | `{commits: Commit[], total: int}` |
| GET | `/api/git/commits/{hash}/diff` | Get commit diff | Token | None | `{files: FileDiff[], stats: Stats}` |

**Example: Get Recent Commits**
```bash
curl http://localhost:3000/api/git/commits?limit=10 \
  -H "X-Session-Token: your-token"
# Response: {
#   "commits": [
#     {
#       "hash": "abc123",
#       "message": "feat: Add feature X",
#       "author": "brian",
#       "timestamp": "2025-01-16T10:00:00Z"
#     }
#   ],
#   "total": 142
# }
```

---

### Workflow Endpoints

| Method | Endpoint | Purpose | Auth | Request | Response |
|--------|----------|---------|------|---------|----------|
| GET | `/api/workflows/timeline` | Get workflow timeline | Token | `?limit=50` | `{workflows: WorkflowRun[]}` |
| GET | `/api/workflows/{id}/details` | Get workflow details | Token | None | `{workflow: WorkflowDetails}` |
| GET | `/api/workflows/graph` | Get workflow DAG | Token | None | `{nodes: Node[], edges: Edge[]}` |
| GET | `/api/workflows/metrics` | Get workflow metrics | Token | `?start_date=...&end_date=...` | `{metrics: Metrics}` |
| GET | `/api/workflows/history` | Get workflow history | Token | `?workflow_name=create-prd` | `{runs: Run[]}` |
| GET | `/api/workflows/{id}/export` | Export workflow data | Token | None | JSON or CSV file |
| GET | `/api/workflows/compare` | Compare workflow runs | Token | `?run1=id1&run2=id2` | `{comparison: Comparison}` |

**Example: Get Workflow Timeline**
```bash
curl http://localhost:3000/api/workflows/timeline \
  -H "X-Session-Token: your-token"
# Response: {
#   "workflows": [
#     {
#       "id": "wf-123",
#       "name": "create-prd",
#       "status": "completed",
#       "started_at": "2025-01-16T10:00:00Z",
#       "completed_at": "2025-01-16T10:05:00Z"
#     }
#   ]
# }
```

---

### Kanban Endpoints

| Method | Endpoint | Purpose | Auth | Request | Response |
|--------|----------|---------|------|---------|----------|
| GET | `/api/kanban/board` | Get kanban board | Token | None | `{columns: Column[], cards: Card[]}` |
| PATCH | `/api/kanban/cards/{id}/move` | Move card | Token | `{target_status: str}` | `{card: Card, commit_sha: str}` |

**Example: Move Story Card**
```bash
curl -X PATCH http://localhost:3000/api/kanban/cards/story-1.1/move \
  -H "X-Session-Token: your-token" \
  -H "Content-Type: application/json" \
  -d '{"target_status": "in_progress"}'
# Response: {
#   "card": {"id": "story-1.1", "status": "in_progress", ...},
#   "commit_sha": "def456"
# }
```

---

### Settings Endpoints

| Method | Endpoint | Purpose | Auth | Request | Response |
|--------|----------|---------|------|---------|----------|
| GET | `/api/settings/provider` | Get current provider | Token | None | `{provider: str, model: str, config: {...}}` |
| POST | `/api/settings/provider` | Set provider | Token | `{provider: str, model: str}` | `{success: bool}` |
| GET | `/api/settings/provider/validate` | Validate provider | Token | `?provider=anthropic` | `{valid: bool, error: str}` |

**Example: Get Current Provider**
```bash
curl http://localhost:3000/api/settings/provider \
  -H "X-Session-Token: your-token"
# Response: {
#   "provider": "anthropic",
#   "model": "claude-sonnet-3-5-20241022",
#   "config": {"api_key_set": true}
# }
```

---

### Direct Message Endpoints

| Method | Endpoint | Purpose | Auth | Request | Response |
|--------|----------|---------|------|---------|----------|
| GET | `/api/dms` | List DM conversations | Token | None | `{conversations: Conversation[]}` |
| GET | `/api/dms/{agent_id}/history` | Get DM history | Token | None | `{messages: Message[]}` |
| GET | `/api/dms/{agent_id}/messages` | Get DM messages | Token | `?limit=50&before=timestamp` | `{messages: Message[]}` |
| POST | `/api/dms/{agent_id}/messages` | Send DM | Token | `{content: str}` | `{message: Message}` |

**Example: Send Direct Message to Brian**
```bash
curl -X POST http://localhost:3000/api/dms/brian/messages \
  -H "X-Session-Token: your-token" \
  -H "Content-Type: application/json" \
  -d '{"content": "What is the status of Epic 5?"}'
# Response: {
#   "message": {
#     "id": "msg-123",
#     "role": "user",
#     "content": "What is the status of Epic 5?",
#     "timestamp": 1705401600000
#   }
# }
```

---

### Channel Endpoints

| Method | Endpoint | Purpose | Auth | Request | Response |
|--------|----------|---------|------|---------|----------|
| GET | `/api/channels` | List channels | Token | `?status=active` | `{channels: Channel[]}` |
| GET | `/api/channels/{id}/messages` | Get channel messages | Token | `?limit=50` | `{messages: Message[]}` |
| POST | `/api/channels/{id}/messages` | Send channel message | Token | `{content: str}` | `{message: Message}` |
| POST | `/api/channels/{id}/archive` | Archive channel | Token | None | `{success: bool}` |
| GET | `/api/channels/{id}/export` | Export channel | Token | `?format=json` | JSON or Markdown file |

**Example: List Active Channels**
```bash
curl http://localhost:3000/api/channels?status=active \
  -H "X-Session-Token: your-token"
# Response: {
#   "channels": [
#     {
#       "id": "sprint-planning-epic-5",
#       "name": "#sprint-planning-epic-5",
#       "ceremonyType": "sprint-planning",
#       "participants": ["brian", "bob", "john"],
#       "messageCount": 12
#     }
#   ]
# }
```

---

### Thread Endpoints

| Method | Endpoint | Purpose | Auth | Request | Response |
|--------|----------|---------|------|---------|----------|
| POST | `/api/threads` | Create thread | Token | `{parent_message_id: str, content: str}` | `{thread: Thread}` |
| GET | `/api/threads/{id}` | Get thread | Token | None | `{thread: Thread, messages: Message[]}` |
| POST | `/api/threads/{id}/messages` | Reply to thread | Token | `{content: str}` | `{message: Message}` |

**Example: Create Thread**
```bash
curl -X POST http://localhost:3000/api/threads \
  -H "X-Session-Token: your-token" \
  -H "Content-Type: application/json" \
  -d '{"parent_message_id": "msg-456", "content": "Good idea! Let me add details."}'
# Response: {
#   "thread": {
#     "id": "thread-789",
#     "parent_message_id": "msg-456",
#     "created_at": "2025-01-16T10:30:00Z",
#     "reply_count": 1
#   }
# }
```

---

### Search Endpoints

| Method | Endpoint | Purpose | Auth | Request | Response |
|--------|----------|---------|------|---------|----------|
| GET | `/api/search/messages` | Search messages | Token | `?query=epic&limit=20` | `{results: SearchResult[]}` |

**Example: Search Messages**
```bash
curl http://localhost:3000/api/search/messages?query=epic%205&limit=10 \
  -H "X-Session-Token: your-token"
# Response: {
#   "results": [
#     {
#       "message_id": "msg-123",
#       "content": "Working on Epic 5...",
#       "agent": "brian",
#       "timestamp": 1705401600000,
#       "channel": "sprint-planning-epic-5"
#     }
#   ]
# }
```

---

### Onboarding Endpoints

| Method | Endpoint | Purpose | Auth | Request | Response |
|--------|----------|---------|------|---------|----------|
| GET | `/api/onboarding/status` | Get onboarding status | No | None | `{completed: bool, current_step: str}` |
| POST | `/api/onboarding/project` | Set project info | No | `{name: str, path: str}` | `{success: bool, next_step: str}` |
| POST | `/api/onboarding/git` | Set git config | No | `{user_name: str, email: str}` | `{success: bool, next_step: str}` |
| POST | `/api/onboarding/provider` | Set AI provider | No | `{provider: str, model: str}` | `{success: bool, next_step: str}` |
| POST | `/api/onboarding/credentials` | Set credentials | No | `{api_key: str}` | `{success: bool, next_step: str}` |
| POST | `/api/onboarding/complete` | Complete onboarding | No | None | `{success: bool, redirect: str}` |

**Example: Get Onboarding Status**
```bash
curl http://localhost:3000/api/onboarding/status
# Response: {
#   "completed": false,
#   "current_step": "provider",
#   "steps": {
#     "project": true,
#     "git": true,
#     "provider": false,
#     "credentials": false
#   }
# }
```

---

## WebSocket Events

**Connection**: `ws://localhost:3000/ws?token=your-session-token`

### Event Schema

All events follow this standardized schema:

```typescript
interface WebEvent {
  type: string;              // Event type (see EventType enum)
  timestamp: string;         // ISO 8601 timestamp
  sequence_number: number;   // Monotonically increasing
  data: Record<string, any>; // Event-specific payload
  metadata?: Record<string, any>; // Optional metadata
}
```

### Event Types

#### Workflow Events

| Event Type | Direction | When Emitted | Data Schema | Frontend Handler |
|------------|-----------|--------------|-------------|------------------|
| `workflow.started` | S→C | Workflow execution begins | `{workflow_id: str, name: str}` | Update timeline |
| `workflow.step_completed` | S→C | Workflow step finishes | `{workflow_id: str, step: str}` | Update progress |
| `workflow.finished` | S→C | Workflow completes | `{workflow_id: str, result: any}` | Mark complete |
| `workflow.failed` | S→C | Workflow fails | `{workflow_id: str, error: str}` | Show error |

**Example: workflow.started**
```json
{
  "type": "workflow.started",
  "timestamp": "2025-01-16T10:00:00.123Z",
  "sequence_number": 42,
  "data": {
    "workflow_id": "wf-123",
    "name": "create-prd",
    "agent": "john"
  }
}
```

---

#### Chat Events

| Event Type | Direction | When Emitted | Data Schema | Frontend Handler |
|------------|-----------|--------------|-------------|------------------|
| `chat.message_sent` | C→S | User sends message | `{message: str, agent: str}` | Add to UI |
| `chat.message_received` | S→C | Agent responds | `{message: str, agent: str}` | Display response |
| `chat.streaming_chunk` | S→C | Streaming response chunk | `{chunk: str, message_id: str}` | Append to message |
| `chat.thinking_started` | S→C | Claude starts reasoning | `{message_id: str}` | Show thinking indicator |
| `chat.thinking_finished` | S→C | Claude finishes reasoning | `{message_id: str}` | Hide thinking indicator |

**Example: chat.streaming_chunk**
```json
{
  "type": "chat.streaming_chunk",
  "timestamp": "2025-01-16T10:00:01.456Z",
  "sequence_number": 43,
  "data": {
    "chunk": "I'll help you create a PRD for",
    "message_id": "msg-789",
    "agent_name": "John"
  }
}
```

---

#### File Events

| Event Type | Direction | When Emitted | Data Schema | Frontend Handler |
|------------|-----------|--------------|-------------|------------------|
| `file.created` | S→C | New file created | `{path: str, type: str}` | Add to file tree |
| `file.modified` | S→C | File modified | `{path: str, size: int}` | Update file tree |
| `file.deleted` | S→C | File deleted | `{path: str}` | Remove from tree |

**Example: file.created**
```json
{
  "type": "file.created",
  "timestamp": "2025-01-16T10:05:00.789Z",
  "sequence_number": 44,
  "data": {
    "path": "docs/PRD.md",
    "type": "file",
    "size": 2048
  }
}
```

---

#### State Events

| Event Type | Direction | When Emitted | Data Schema | Frontend Handler |
|------------|-----------|--------------|-------------|------------------|
| `state.epic_created` | S→C | Epic created | `{epic_num: int, title: str}` | Add to kanban |
| `state.story_created` | S→C | Story created | `{epic_num: int, story_num: int, title: str}` | Add to kanban |
| `state.story_transitioned` | S→C | Story state changes | `{epic_num: int, story_num: int, from_status: str, to_status: str}` | Move card |

**Example: state.story_transitioned**
```json
{
  "type": "state.story_transitioned",
  "timestamp": "2025-01-16T11:00:00.000Z",
  "sequence_number": 45,
  "data": {
    "epic_num": 5,
    "story_num": 1,
    "from_status": "ready",
    "to_status": "in_progress",
    "commit_sha": "abc123"
  }
}
```

---

#### Git Events

| Event Type | Direction | When Emitted | Data Schema | Frontend Handler |
|------------|-----------|--------------|-------------|------------------|
| `git.commit_created` | S→C | Commit created | `{sha: str, message: str, author: str}` | Add to timeline |

**Example: git.commit_created**
```json
{
  "type": "git.commit_created",
  "timestamp": "2025-01-16T11:30:00.000Z",
  "sequence_number": 46,
  "data": {
    "sha": "def456",
    "message": "feat(epic-5): Implement Story 5.1",
    "author": "amelia",
    "files_changed": 3
  }
}
```

---

#### Provider Events

| Event Type | Direction | When Emitted | Data Schema | Frontend Handler |
|------------|-----------|--------------|-------------|------------------|
| `provider.changed` | S→C | AI provider changed | `{provider: str, model: str}` | Update UI badge |

**Example: provider.changed**
```json
{
  "type": "provider.changed",
  "timestamp": "2025-01-16T12:00:00.000Z",
  "sequence_number": 47,
  "data": {
    "provider": "anthropic",
    "model": "claude-sonnet-3-5-20241022"
  }
}
```

---

#### System Events

| Event Type | Direction | When Emitted | Data Schema | Frontend Handler |
|------------|-----------|--------------|-------------|------------------|
| `system.heartbeat` | S→C | Every 30 seconds | `{uptime: int}` | Update status |
| `system.error` | S→C | System error occurs | `{error: str, context: {...}}` | Show error toast |

**Example: system.heartbeat**
```json
{
  "type": "system.heartbeat",
  "timestamp": "2025-01-16T12:00:30.000Z",
  "sequence_number": 48,
  "data": {
    "uptime": 3600,
    "active_connections": 2
  }
}
```

---

#### Future Events (V1.1+)

| Event Type | Direction | When Emitted | Data Schema |
|------------|-----------|--------------|-------------|
| `ceremony.started` | S→C | Ceremony begins | `{ceremony_id: str, type: str}` |
| `ceremony.message` | S→C | Ceremony message sent | `{ceremony_id: str, message: str}` |
| `ceremony.ended` | S→C | Ceremony completes | `{ceremony_id: str, outcome: str}` |
| `kanban.card_moved` | S→C | Card moved in UI | `{card_id: str, from: str, to: str}` |
| `kanban.card_updated` | S→C | Card details updated | `{card_id: str, fields: {...}}` |

---

## Quick Reference

### Authentication

**How to get a session token**:

```bash
# 1. Get token
curl http://localhost:3000/api/session/token
# Response: {"token": "uuid-here"}

# 2. Use token in subsequent requests
curl -H "X-Session-Token: uuid-here" http://localhost:3000/api/agents
```

**WebSocket authentication**:
```javascript
const token = await fetch('/api/session/token').then(r => r.json()).then(d => d.token);
const ws = new WebSocket(`ws://localhost:3000/ws?token=${token}`);
```

**Token lifecycle**:
- Tokens are UUID v4 strings
- Tokens are session-scoped (cleared on server restart)
- No expiration (valid until server restart)
- Multiple clients can share the same token

---

### Error Codes

| Status Code | Meaning | Common Cause | Solution |
|-------------|---------|--------------|----------|
| 400 | Bad Request | Invalid input data | Check request schema |
| 401 | Unauthorized | Missing or invalid token | Get new session token |
| 404 | Not Found | Resource doesn't exist | Verify ID/path |
| 409 | Conflict | CLI is active | Wait for CLI to finish or use read-only mode |
| 422 | Validation Error | Pydantic validation failed | Check field types and required fields |
| 500 | Internal Server Error | Server exception | Check server logs |

**Error Response Format**:
```json
{
  "detail": "Error message here",
  "error_code": "SPECIFIC_ERROR_CODE",
  "context": {
    "field": "value"
  }
}
```

---

### WebSocket Connection

**Connection lifecycle**:

```javascript
// 1. Connect
const ws = new WebSocket(`ws://localhost:3000/ws?token=${token}`);

// 2. Handle events
ws.onmessage = (event) => {
  const webEvent = JSON.parse(event.data);
  console.log(`Received: ${webEvent.type}`);

  // Handle specific event types
  switch (webEvent.type) {
    case 'workflow.started':
      handleWorkflowStarted(webEvent.data);
      break;
    case 'chat.streaming_chunk':
      appendToMessage(webEvent.data.chunk);
      break;
  }
};

// 3. Handle disconnection
ws.onclose = () => {
  console.log('Disconnected, reconnecting...');
  setTimeout(() => reconnect(), 1000); // Exponential backoff recommended
};

// 4. Handle errors
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

**Auto-reconnection pattern** (with exponential backoff):

```javascript
let reconnectAttempts = 0;
const MAX_RECONNECT_DELAY = 30000; // 30 seconds

function connect() {
  const ws = new WebSocket(`ws://localhost:3000/ws?token=${token}`);

  ws.onopen = () => {
    console.log('Connected');
    reconnectAttempts = 0; // Reset on successful connection
  };

  ws.onclose = () => {
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY);
    reconnectAttempts++;
    console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})...`);
    setTimeout(() => connect(), delay);
  };

  return ws;
}

const ws = connect();
```

**Event filtering** (client-side):

```javascript
const eventHandlers = {
  'workflow.*': handleWorkflowEvent,
  'chat.*': handleChatEvent,
  'file.*': handleFileEvent,
};

ws.onmessage = (event) => {
  const webEvent = JSON.parse(event.data);
  const [category] = webEvent.type.split('.');
  const wildcardKey = `${category}.*`;

  if (eventHandlers[wildcardKey]) {
    eventHandlers[wildcardKey](webEvent);
  } else if (eventHandlers[webEvent.type]) {
    eventHandlers[webEvent.type](webEvent);
  }
};
```

---

## See Also

- [Quick Start Guide](QUICK_START.md) - Integration patterns and code examples
- [Web Interface Architecture](features/web-interface/ARCHITECTURE.md) - System architecture details
- [Implementation Status](features/web-interface/IMPLEMENTATION_STATUS.md) - As-built documentation

**Estimated tokens**: ~2,900
