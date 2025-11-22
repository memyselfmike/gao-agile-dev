# Technical Architecture: Browser-Based Web Interface for GAO-Dev

**Feature**: Web Interface
**Epic**: 39
**Status**: Ready for Implementation
**Author**: Winston (Technical Architect)
**Last Updated**: 2025-01-16
**Version**: 1.0

---

## Executive Summary

This document provides the comprehensive technical architecture for transforming GAO-Dev from CLI-only to a rich browser-based interface that serves as a mission control center for autonomous agent operations. The architecture is designed for two primary users: human product owners and AI agents (via Playwright MCP).

### Key Architectural Principles

1. **Thin Client, Thick Server**: All business logic remains in Python backend; frontend is pure view layer
2. **Reuse, Don't Rebuild**: Integrate with existing Epic 30 (ChatREPL), Epic 27 (GitIntegratedStateManager), Epic 28 (CeremonyOrchestrator)
3. **Event-Driven Architecture**: Real-time WebSocket streaming for agent observability
4. **Production-Scale Design**: Handle 100+ epics, 1,000+ stories, 10,000+ events
5. **AI-Testable by Design**: Semantic HTML, stable selectors, clear state indicators for Playwright MCP
6. **Security-First**: Localhost-only now, architected for future authentication

### Architectural Decisions (FINAL)

Three key architectural decisions have been made and approved by the Product Owner:

1. **Mutual Exclusion**: **Option B - Read-only web while CLI active** ✅
   - CLI has exclusive write access (can execute workflows, modify files)
   - Web UI can run simultaneously in read-only observability mode
   - Provides "mission control" value without bidirectional complexity

2. **Dark Mode in MVP**: **Option B - Both modes (respect system preference)** ✅
   - Implement both dark and light mode in MVP
   - Respect `prefers-color-scheme` CSS media query
   - Low effort, high value

3. **Event Bus Persistence**: **Option A - asyncio.Queue (in-memory)** ✅
   - Keep asyncio.Queue for MVP
   - Simple, fast, no external dependencies
   - Can add SQLite event log in V1.1 if event replay becomes critical

See Section 1.5 and Appendix C for detailed analysis and implementation notes.

### Core Technology Decisions

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Frontend Framework** | React 18 + Vite | Fast dev server, optimal build performance, simpler than Next.js for single-page app |
| **Backend Framework** | FastAPI | Async support, native WebSocket, minimal dependencies, Python ecosystem |
| **Event Bus** | asyncio.Queue | Sufficient for single-project, avoids Redis dependency, simpler deployment |
| **WebSocket** | FastAPI native | No socket.io needed, custom JSON protocol for flexibility |
| **State Management** | Zustand | Simpler than Redux, better performance than Context for global state |
| **UI Components** | shadcn/ui | Accessible, customizable, Radix UI primitives + Tailwind CSS |
| **Code Editor** | Monaco Editor | Industry-standard, used by VS Code, handles large files |
| **Virtual Scrolling** | @tanstack/react-virtual | Modern, performant, actively maintained |

---

## Quick Links

**Developer Resources**:
- [Quick Start Guide](../../QUICK_START.md) - Copy-paste integration patterns for adding features
- [API Reference](../../API_REFERENCE.md) - Complete REST endpoint and WebSocket event catalog
- [Implementation Status](IMPLEMENTATION_STATUS.md) - As-built documentation comparing design vs implementation

**Related Documentation**:
- [Architecture Overview](../../ARCHITECTURE_OVERVIEW.md) - Full system architecture with diagrams
- [CLAUDE.md](../../../CLAUDE.md) - Complete project guide for Claude

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Technology Stack](#technology-stack)
3. [API Specifications](#api-specifications)
4. [Frontend Architecture](#frontend-architecture)
5. [Backend Architecture](#backend-architecture)
6. [Event-Driven Architecture](#event-driven-architecture)
7. [Integration Architecture](#integration-architecture)
8. [Performance Optimizations](#performance-optimizations)
9. [Security Architecture](#security-architecture)
10. [File Structure](#file-structure)
11. [Development Workflow](#development-workflow)
12. [Deployment Architecture](#deployment-architecture)
13. [Open Issues and Future Work](#open-issues-and-future-work)

---

## 1. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (Client)                        │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Chat Tab   │  │ Activity    │  │   Kanban    │            │
│  │             │  │ Stream Tab  │  │   Board     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Files Tab  │  │   Git Tab   │  │ Ceremony    │            │
│  │  (Monaco)   │  │             │  │  Channels   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│                     Zustand State Store                        │
│                                                                 │
└─────────────┬───────────────────────────────┬───────────────────┘
              │                               │
              │ REST API (HTTP)               │ WebSocket (Events)
              │                               │
┌─────────────▼───────────────────────────────▼───────────────────┐
│                    FastAPI Backend (Python)                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  WebAPI Layer                            │  │
│  │  - REST Endpoints   - WebSocket Manager                  │  │
│  │  - Request Validation   - Event Dispatcher               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Adapter Layer                           │  │
│  │  - BrianWebAdapter   - FileSystemAdapter                 │  │
│  │  - StateChangeAdapter   - CeremonyAdapter                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Event Bus (asyncio.Queue)               │  │
│  │  - Event publishing   - Subscriber management            │  │
│  │  - Event buffering   - Reconnection replay               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Existing Services (Epic 27, 30, 28)            │  │
│  │  - ChatSession   - GitIntegratedStateManager             │  │
│  │  - CeremonyOrchestrator   - WorkflowExecutor             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────┬───────────────────────────────┬───────────────────┘
              │                               │
              ▼                               ▼
      ┌───────────────┐              ┌───────────────┐
      │ .gao-dev/     │              │  Git Repo     │
      │ documents.db  │              │               │
      │ session.lock  │              │               │
      └───────────────┘              └───────────────┘
```

### Component Interaction Flow

**User Chat Message Flow**:
```
1. User types message in Chat Tab
2. Frontend → POST /api/chat {"agent": "brian", "message": "..."}
3. FastAPI → BrianWebAdapter.send_message()
4. BrianWebAdapter → ChatSession.handle_input() (Epic 30)
5. ChatSession → ConversationalBrian
6. ConversationalBrian → Response chunks
7. BrianWebAdapter → Emit events via EventBus
8. WebSocketManager → Broadcast to all clients
9. Frontend → Update chat UI with streaming response
```

**File Creation by Agent Flow**:
```
1. Agent (Amelia) creates file via Write tool
2. Write tool → GitIntegratedStateManager.create_story()
3. GitIntegratedStateManager → File + DB + Git (atomic)
4. FileSystemWatcher → Detect file change
5. FileSystemAdapter → Emit "file.created" event
6. WebSocketManager → Broadcast to clients
7. Frontend → Update file tree in Files Tab
```

**Kanban Board Drag-and-Drop Flow**:
```
1. User drags story card to "In Progress"
2. Frontend → POST /api/kanban/transition {"epic": 1, "story": 1, "status": "in_progress"}
3. FastAPI → GitIntegratedStateManager.transition_story()
4. GitIntegratedStateManager → DB update + Git commit (atomic)
5. StateChangeAdapter → Emit "state.changed" event
6. WebSocketManager → Broadcast to clients
7. Frontend → Update Kanban board UI
```

### Mutual Exclusion Decision [CRAAP-006]

**Status**: FINAL ✅ (Approved by Product Owner)

**Selected Approach**: Option B - Read-Only Web While CLI Active

#### Final Decision

The web interface will operate in **read-only mode** when the CLI holds the session lock.

**Architecture**:
- **CLI = Exclusive write access**: Can execute workflows, modify files, transition stories
- **Web = Read-only observability mode**: Can view dashboard, filter events, read files, watch activity streams
- **Session lock mechanism**: File-based lock with PID tracking for stale cleanup
- **Mode enforcement**: Middleware rejects POST/PATCH/DELETE when in read-only mode

#### Implementation Details

**Session Lock with Read/Write Modes**:
```python
class SessionLock:
    def acquire(self, interface: str, mode: str = "write") -> bool:
        """
        Acquire session lock.

        Args:
            interface: "cli" or "web"
            mode: "read" or "write"

        Returns:
            True if acquired, False if denied
        """
        if mode == "read":
            # Read mode always succeeds (observability only)
            return True

        # Write mode requires exclusive lock
        if self.lock_file.exists():
            lock_data = json.loads(self.lock_file.read_text())
            if self.is_process_alive(lock_data["pid"]):
                return False  # Write lock held by another process

        # Acquire write lock
        lock_data = {
            "interface": interface,
            "mode": "write",
            "pid": os.getpid(),
            "timestamp": datetime.now().isoformat()
        }
        self.lock_file.write_text(json.dumps(lock_data, indent=2))
        return True
```

**API Middleware for Mode Enforcement**:
```python
@app.middleware("http")
async def read_only_middleware(request: Request, call_next):
    """Enforce read-only mode when CLI holds lock"""
    # GET/HEAD/OPTIONS: always allowed
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return await call_next(request)

    # Write operations (POST/PATCH/PUT/DELETE): check lock
    if request.state.session_lock.is_write_locked_by_other():
        return JSONResponse(
            status_code=423,  # Locked
            content={
                "error": "Session locked by CLI",
                "mode": "read-only",
                "message": "Exit CLI session to enable write operations"
            }
        )

    return await call_next(request)
```

**Frontend Read-Only Indication**:
```typescript
// Display banner when in read-only mode
{isReadOnly && (
  <Banner variant="info">
    <Icon name="eye" />
    Read-only mode: CLI is active. You can observe but not send commands.
  </Banner>
)}

// Disable write controls
<Button
  disabled={isReadOnly}
  onClick={handleTransition}
>
  Update Status
</Button>
```

#### Why This Decision?

**Aligns with "Mission Control" Vision**:
- Users can monitor agent activity while scripting via CLI
- Natural power-user workflow: automate with CLI, observe in web UI

**Eliminates Race Conditions**:
- Simple read/write distinction prevents conflicts
- Only CLI can modify state, web is pure observability

**Reasonable Complexity**:
- Not much more complex than strict mutual exclusion
- Significantly simpler than full bidirectional concurrency

**Future-Proof**:
- Can evolve to full bidirectional if demand justifies complexity
- Foundation for operation-level locking in V2.0

#### What Web UI Can Do (Read-Only Mode)

**Allowed Operations**:
- View kanban board and story details
- View file tree and file contents (read-only editor)
- Stream activity and event logs
- View chat history
- View ceremony channels
- Filter and search across all views
- Export data (reports, event logs)

**Disallowed Operations** (shown as disabled buttons):
- Create/update/delete stories
- Drag and drop on kanban board
- Edit files (editor in read-only mode)
- Send chat messages
- Modify ceremonies
- Create new projects

**User Switch Mode** (how to enable write mode):
1. Exit the CLI session (Ctrl+C or `exit`)
2. Web UI detects lock release
3. Read-only banner disappears
4. All write controls become enabled

---

## 2. Technology Stack

### Frontend Stack

#### Framework: React 18 + Vite

**Decision**: React 18 with Vite build tool

**Rationale**:
- **Vite over Next.js**:
  - Next.js is overkill for single-page app (no SSR needed for localhost)
  - Vite has faster dev server (instant HMR via esbuild)
  - Smaller bundle size (no Next.js framework overhead)
  - Simpler configuration for our use case
- **React 18**:
  - Concurrent rendering for better UX
  - Automatic batching reduces re-renders
  - Large ecosystem and community
  - Team familiarity

**Alternatives Considered**:
- Next.js 14: Rejected (too heavy, SSR unnecessary)
- Vue 3: Rejected (team prefers React)
- Svelte: Rejected (smaller ecosystem, less mature)

#### State Management: Zustand

**Decision**: Zustand for global state, React Context for local state

**Rationale**:
- **Zustand advantages**:
  - Simple API (less boilerplate than Redux)
  - Better performance than Context for frequent updates
  - No provider wrapping needed
  - Built-in DevTools support
  - Middleware for persistence
- **When to use Context**: Component-local state (theme, modals)
- **When to use Zustand**: Global state (chat history, activity stream, Kanban board)

**Store Structure**:
```typescript
// stores/chatStore.ts
export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  activeAgent: "brian",
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  switchAgent: (agent) => set({ activeAgent: agent }),
}))

// stores/activityStore.ts
export const useActivityStore = create<ActivityState>((set) => ({
  events: [],
  timeWindow: 3600, // 1 hour default
  addEvent: (event) => set((state) => ({ events: [...state.events, event] })),
}))

// stores/kanbanStore.ts
export const useKanbanStore = create<KanbanState>((set) => ({
  epics: [],
  stories: [],
  updateStoryStatus: (epicNum, storyNum, status) => { /* ... */ },
}))
```

#### UI Components: shadcn/ui

**Decision**: shadcn/ui for component library

**Rationale**:
- Built on Radix UI primitives (accessibility built-in)
- Tailwind CSS for styling (utility-first)
- Copy-paste components (not npm dependency)
- Highly customizable
- Excellent TypeScript support
- WCAG 2.1 AA compliant by default

**Key Components to Use**:
- `<Button>`, `<Input>`, `<Textarea>` - Form controls
- `<Card>`, `<Sheet>`, `<Dialog>` - Layout containers
- `<Tabs>`, `<Accordion>` - Navigation
- `<DropdownMenu>`, `<ContextMenu>` - Menus
- `<Toast>` - Notifications
- `<ScrollArea>` - Custom scrollbars
- `<Separator>` - Dividers

#### Code Editor: Monaco Editor

**Decision**: @monaco-editor/react

**Rationale**:
- Same editor as VS Code (familiar UX)
- Handles large files (10,000+ lines)
- Built-in syntax highlighting
- TypeScript support
- Diff view built-in
- Minimap, line numbers, code folding

**Performance Optimization**:
- Editor instance pooling (reuse editors)
- Lazy loading (only load when Files Tab active)
- Model disposal on tab close
- Limit open files (max 10)

#### Virtual Scrolling: @tanstack/react-virtual

**Decision**: @tanstack/react-virtual (formerly react-virtual)

**Rationale**:
- Modern, actively maintained
- Framework-agnostic core
- Better performance than react-window
- TypeScript-first
- Smaller bundle size

**Use Cases**:
- Activity Stream (10,000+ events)
- File Tree (500+ files)
- Kanban Board (1,000+ stories)

---

### Backend Stack

#### Framework: FastAPI

**Decision**: FastAPI (confirmed from vision)

**Rationale**:
- Async/await native (perfect for WebSocket)
- Fast performance (Starlette + Pydantic)
- Automatic OpenAPI docs
- Type validation via Pydantic
- Python ecosystem (integrates with existing GAO-Dev)
- Minimal dependencies

#### Event Bus: asyncio.Queue

**Status**: FINAL ✅ (Option A - In-Memory Queue)

**Decision**: Python asyncio.Queue for event streaming (MVP)

**Rationale**:
- **Sufficient for single-project**: No need for Redis overhead
- **Simple deployment**: No external dependencies
- **Fast in-process communication**: <1ms latency
- **Production-grade**: Can handle 10,000+ events/second per project

**Future Enhancement**:
- V1.1 consideration: SQLite event log for event replay and audit trail
- V2.0 consideration: Redis for multi-project distributed deployment

**Event Bus Architecture**:
```python
class WebEventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, event_type: str) -> asyncio.Queue:
        queue = asyncio.Queue(maxsize=1000)  # Buffer up to 1000 events
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(queue)
        return queue

    async def publish(self, event: WebEvent):
        if event.type in self.subscribers:
            for queue in self.subscribers[event.type]:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    # Drop oldest event
                    queue.get_nowait()
                    queue.put_nowait(event)
```

**Buffer Management**:
- Default buffer size: 1000 events per subscriber
- Overflow policy: Drop oldest event when buffer full
- Memory estimation: ~1KB per event, max 1MB per subscriber queue
- Reconnection: Server maintains reconnect buffer for up to 30 seconds

#### WebSocket: FastAPI Native

**Decision**: FastAPI native WebSocket (no socket.io)

**Rationale**:
- **No socket.io needed**: Custom JSON protocol is simpler
- **Native WebSocket advantages**:
  - Less overhead (no socket.io client bundle)
  - Full control over protocol
  - Easier debugging
- **Reconnection**: Implement custom logic with exponential backoff
- **Event buffering**: Server-side queue for disconnected clients

**WebSocket Protocol**:
```json
// Client → Server (ping)
{"type": "ping"}

// Server → Client (pong)
{"type": "pong"}

// Server → Client (event)
{
  "type": "event",
  "event_type": "chat.message",
  "data": {
    "agent": "brian",
    "message": "I'm analyzing your request...",
    "timestamp": "2025-01-16T10:30:00Z"
  }
}

// Client → Server (subscribe)
{"type": "subscribe", "event_types": ["chat.message", "file.created"]}

// Server → Client (error)
{"type": "error", "message": "Invalid event type"}
```

---

## 3. API Specifications

### REST API Endpoints

#### Chat API

**POST /api/chat**
```typescript
// Send message to current agent
Request:
{
  agent: string,        // "brian", "mary", "john", etc.
  message: string,
  context?: {
    epic_num?: number,
    story_num?: number
  }
}

Response:
{
  message_id: string,
  agent: string,
  timestamp: string
}
```

**GET /api/agents**
```typescript
// List available agents
Response:
{
  agents: [
    {
      name: "brian",
      display_name: "Brian (Workflow Coordinator)",
      status: "active" | "idle",
      description: string
    },
    // ... all 8 agents
  ]
}
```

**POST /api/agents/switch**
```typescript
// Switch to different agent
Request:
{
  agent: string
}

Response:
{
  success: boolean,
  agent: string,
  context_preserved: boolean
}
```

#### Files API

**GET /api/files**
```typescript
// Get file tree
Query params:
  path?: string,           // Filter by path
  tracked_only: boolean    // Default: true

Response:
{
  files: [
    {
      path: string,
      type: "file" | "directory",
      size: number,
      modified: string,      // ISO timestamp
      tracked: boolean
    }
  ]
}
```

**GET /api/files/{path}**
```typescript
// Get file content
Response:
{
  path: string,
  content: string,
  encoding: "utf-8",
  size: number,
  modified: string,
  git_status: "clean" | "modified" | "untracked"
}
```

**POST /api/files/{path}**
```typescript
// Save file (with commit message)
Request:
{
  content: string,
  commit_message: string,
  validate: boolean        // Default: true
}

Response:
{
  success: boolean,
  commit_sha: string,
  validation_errors?: string[]
}
```

#### Kanban API

**GET /api/kanban**
```typescript
// Get Kanban board state
Query params:
  feature?: string,        // Filter by feature
  status?: string          // Filter by status

Response:
{
  epics: [
    {
      epic_num: number,
      title: string,
      status: string,
      total_stories: number,
      completed_stories: number,
      progress_percentage: number
    }
  ],
  stories: [
    {
      epic_num: number,
      story_num: number,
      title: string,
      status: string,
      priority: string,
      assignee: string
    }
  ]
}
```

**POST /api/kanban/transition**
```typescript
// Move story to different status
Request:
{
  epic_num: number,
  story_num: number,
  new_status: string,      // "backlog", "ready", "in_progress", "in_review", "done"
  actual_hours?: number    // Required for "done"
}

Response:
{
  success: boolean,
  story: {
    epic_num: number,
    story_num: number,
    status: string,
    updated_at: string
  },
  commit_sha: string
}
```

#### Git API

**GET /api/git/commits**
```typescript
// Get commit history
Query params:
  limit: number,           // Default: 50
  offset: number,          // Default: 0
  author?: string,         // Filter by author
  since?: string           // ISO timestamp

Response:
{
  commits: [
    {
      sha: string,
      message: string,
      author: string,
      timestamp: string,
      files_changed: number,
      insertions: number,
      deletions: number
    }
  ],
  total: number
}
```

**GET /api/git/commits/{sha}**
```typescript
// Get commit details with diff
Response:
{
  commit: {
    sha: string,
    message: string,
    author: string,
    timestamp: string
  },
  diff: string,             // Unified diff format
  files: [
    {
      path: string,
      status: "added" | "modified" | "deleted",
      changes: number
    }
  ]
}
```

#### Ceremony API

**GET /api/ceremonies**
```typescript
// Get active ceremonies
Response:
{
  active: [
    {
      ceremony_id: string,
      type: "planning" | "retrospective" | "standup",
      epic_num: number,
      started_at: string,
      participants: string[]
    }
  ]
}
```

**GET /api/ceremonies/{ceremony_id}/messages**
```typescript
// Get ceremony messages (for Ceremony Channels tab)
Response:
{
  messages: [
    {
      message_id: string,
      agent: string,
      content: string,
      timestamp: string,
      thread_id?: string
    }
  ]
}
```

#### Session API

**GET /api/session**
```typescript
// Get session status
Response:
{
  active: boolean,
  interface: "web" | "cli",
  project_root: string,
  session_id: string,
  started_at: string
}
```

**POST /api/session/lock**
```typescript
// Acquire session lock (web interface)
Response:
{
  success: boolean,
  session_id: string,
  lock_acquired: boolean,
  conflict?: {
    interface: "cli",
    pid: number,
    started_at: string
  }
}
```

**DELETE /api/session/lock**
```typescript
// Release session lock
Response:
{
  success: boolean
}
```

---

### WebSocket Protocol

#### Connection

```
ws://localhost:3000/ws
```

#### Message Types

**1. Client → Server: Ping**
```json
{"type": "ping"}
```

**2. Server → Client: Pong**
```json
{"type": "pong", "timestamp": "2025-01-16T10:30:00Z"}
```

**3. Client → Server: Subscribe**
```json
{
  "type": "subscribe",
  "event_types": ["chat.message", "workflow.started", "file.created"]
}
```

**4. Server → Client: Event**
```json
{
  "type": "event",
  "event_type": "chat.message",
  "data": {
    "agent": "brian",
    "message": "Analyzing your request...",
    "timestamp": "2025-01-16T10:30:00Z"
  }
}
```

#### Event Schema

All events follow this structure:
```typescript
interface WebSocketEvent {
  type: "event",
  event_type: string,
  data: Record<string, any>,
  timestamp: string,
  correlation_id?: string
}
```

#### Event Types

**Chat Events**:
- `chat.message` - New chat message from agent
- `chat.agent_switched` - User switched to different agent
- `chat.typing` - Agent is typing (optional UX enhancement)

**Workflow Events**:
- `workflow.started` - Workflow sequence started
- `workflow.step_started` - Workflow step started
- `workflow.step_completed` - Workflow step completed
- `workflow.completed` - Workflow sequence completed
- `workflow.failed` - Workflow sequence failed

**Agent Events**:
- `agent.activated` - Agent started work
- `agent.completed` - Agent completed work
- `agent.tool_used` - Agent used a tool (Read, Write, etc.)

**File Events**:
- `file.created` - File created by agent or user
- `file.modified` - File modified
- `file.deleted` - File deleted

**Git Events**:
- `git.commit` - New git commit created
- `git.branch_changed` - Git branch changed

**State Events**:
- `state.changed` - Story or epic status changed
- `state.epic_created` - New epic created
- `state.story_created` - New story created

**Ceremony Events**:
- `ceremony.started` - Ceremony began
- `ceremony.message` - Intra-agent message during ceremony
- `ceremony.completed` - Ceremony ended

#### Reconnection Strategy

**Client-Side Reconnection**:
```typescript
class WebSocketClient {
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private baseDelay = 1000 // 1 second

  async reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached")
      return
    }

    const delay = Math.min(
      this.baseDelay * Math.pow(2, this.reconnectAttempts),
      30000 // Max 30 seconds
    )

    await sleep(delay)
    this.reconnectAttempts++
    this.connect()
  }
}
```

**Server-Side Event Buffering**:
```python
class WebSocketManager:
    def __init__(self):
        self.event_buffer: Dict[str, Deque[WebEvent]] = {}
        self.buffer_size = 100  # Keep last 100 events per client

    async def buffer_event(self, client_id: str, event: WebEvent):
        if client_id not in self.event_buffer:
            self.event_buffer[client_id] = deque(maxlen=self.buffer_size)
        self.event_buffer[client_id].append(event)

    async def replay_buffered_events(self, client_id: str, websocket: WebSocket):
        if client_id in self.event_buffer:
            for event in self.event_buffer[client_id]:
                await websocket.send_json(event.dict())
```

---

## 4. Frontend Architecture

### Component Hierarchy

```
<App>
  ├── <SessionLockGuard>              # Check session.lock before rendering
  │
  ├── <AppLayout>
  │   ├── <TopBar>
  │   │   ├── <ProjectName>
  │   │   ├── <AgentSwitcher>         # Dropdown: Brian, Mary, John, etc.
  │   │   ├── <SessionStatus>         # "Connected" / "Reconnecting..."
  │   │   └── <SettingsMenu>
  │   │
  │   ├── <Sidebar>
  │   │   ├── <TabIcon icon="chat" />
  │   │   ├── <TabIcon icon="activity" />
  │   │   ├── <TabIcon icon="kanban" />
  │   │   ├── <TabIcon icon="files" />
  │   │   ├── <TabIcon icon="git" />
  │   │   └── <TabIcon icon="ceremony" conditional />
  │   │
  │   └── <MainContent>
  │       ├── {activeTab === "chat" && <ChatTab />}
  │       ├── {activeTab === "activity" && <ActivityStreamTab />}
  │       ├── {activeTab === "kanban" && <KanbanBoardTab />}
  │       ├── {activeTab === "files" && <FilesTab />}
  │       ├── {activeTab === "git" && <GitTab />}
  │       └── {activeTab === "ceremony" && <CeremonyChannelsTab />}
  │
  └── <WebSocketProvider>             # WebSocket connection manager
```

### Tab Components (Detailed)

#### ChatTab
```typescript
<ChatTab>
  <ChatHeader>
    <AgentIndicator agent={activeAgent} />
    <ReasoningToggle />                 # Show/hide Claude thinking
  </ChatHeader>

  <ChatMessageList>
    <VirtualList                        # Virtual scrolling for performance
      items={messages}
      renderItem={(msg) => (
        <ChatMessage
          role={msg.role}
          content={msg.content}
          timestamp={msg.timestamp}
          thinking={msg.thinking}       # Optional reasoning
        />
      )}
    />
  </ChatMessageList>

  <ChatInput
    onSubmit={sendMessage}
    placeholder="Ask Brian..."
    disabled={isSending}
  />
</ChatTab>
```

#### ActivityStreamTab
```typescript
<ActivityStreamTab>
  <ActivityFilters>
    <AgentFilter />                     # Filter by agent
    <EventTypeFilter />                 # Filter by event type
    <TimeWindowSelector />              # 1h, 24h, 7d, 30d, All
  </ActivityFilters>

  <ActivityTimeline>
    <VirtualList                        # Handle 10,000+ events
      items={filteredEvents}
      renderItem={(event) => (
        <ActivityEvent
          type={event.type}
          summary={event.summary}       # Shallow by default
          timestamp={event.timestamp}
          onExpand={() => showDetails(event)}  # Deep drill-down
        />
      )}
    />
  </ActivityTimeline>

  <ActivityDetails                      # Expandable panel
    event={selectedEvent}
    onClose={closeDetails}
  />
</ActivityStreamTab>
```

#### KanbanBoardTab
```typescript
<KanbanBoardTab>
  <KanbanFilters>
    <FeatureFilter />
    <SearchInput />
  </KanbanFilters>

  <KanbanBoard>
    <KanbanColumn status="backlog">
      <DraggableStoryCard ... />
    </KanbanColumn>

    <KanbanColumn status="ready">
      <DraggableStoryCard ... />
    </KanbanColumn>

    <KanbanColumn status="in_progress">
      <DraggableStoryCard ... />
    </KanbanColumn>

    <KanbanColumn status="in_review">
      <DraggableStoryCard ... />
    </KanbanColumn>

    <KanbanColumn status="done">
      <DraggableStoryCard ... />
    </KanbanColumn>
  </KanbanBoard>
</KanbanBoardTab>
```

**Drag-and-Drop Library**: @dnd-kit/core (modern, accessible, performant)

#### FilesTab
```typescript
<FilesTab>
  <FilesLayout>
    <FileTreePanel>
      <FileTree
        files={fileTree}
        onSelectFile={openFile}
        virtualScrolling                # Handle 500+ files
      />
    </FileTreePanel>

    <EditorPanel>
      <EditorTabs>
        {openFiles.map(file => (
          <EditorTab
            key={file.path}
            file={file}
            onClose={() => closeFile(file.path)}
          />
        ))}
      </EditorTabs>

      <MonacoEditor
        path={activeFile.path}
        value={activeFile.content}
        onChange={handleEdit}
        language={detectLanguage(activeFile.path)}
        options={{
          minimap: { enabled: true },
          lineNumbers: "on",
          readOnly: false
        }}
      />

      <EditorActions>
        <Button onClick={saveFile}>
          Save (Ctrl+S)
        </Button>
        <DiffViewToggle />
      </EditorActions>

      {showCommitDialog && (
        <CommitMessageDialog
          onConfirm={commitFile}
          onCancel={cancelSave}
        />
      )}
    </EditorPanel>
  </FilesLayout>
</FilesTab>
```

#### GitTab
```typescript
<GitTab>
  <GitFilters>
    <AuthorFilter />                    # Agent or human
    <TimeRangeFilter />
  </GitFilters>

  <CommitTimeline>
    <VirtualList
      items={commits}
      renderItem={(commit) => (
        <CommitCard
          sha={commit.sha}
          message={commit.message}
          author={commit.author}
          timestamp={commit.timestamp}
          onClick={() => showDiff(commit.sha)}
        />
      )}
    />
  </CommitTimeline>

  {selectedCommit && (
    <DiffViewer
      commit={selectedCommit}
      onClose={closeDiff}
    />
  )}
</GitTab>
```

#### CeremonyChannelsTab
```typescript
<CeremonyChannelsTab>
  <ChannelList>
    <ChannelItem
      name="#planning-ceremony"
      active={activeCeremony === "planning"}
      unread={0}
    />
    <ChannelItem
      name="#retrospective"
      active={activeCeremony === "retrospective"}
      unread={5}
    />
    <ChannelItem
      name="#sprint-review"
      active={activeCeremony === "sprint-review"}
      unread={0}
    />
  </ChannelList>

  <MessageStream>
    <VirtualList
      items={ceremonyMessages}
      renderItem={(msg) => (
        <CeremonyMessage
          agent={msg.agent}
          avatar={getAgentAvatar(msg.agent)}
          content={msg.content}
          timestamp={msg.timestamp}
        />
      )}
    />
  </MessageStream>

  <MessageInput
    placeholder="Message the team..."
    onSubmit={sendCeremonyMessage}
    disabled={!userCanParticipate}      # Optional feature
  />
</CeremonyChannelsTab>
```

---

### State Management Architecture

#### Zustand Stores

**chatStore.ts** [CRAAP-003, CRAAP-008]
```typescript
interface ChatMessage {
  id: string
  agent: string
  message: string
  timestamp: string
  status?: 'sending' | 'sent' | 'failed'
}

interface ChatState {
  // In-memory messages (last 500, for rendering)
  messages: ChatMessage[]

  // Per-agent message counts (for history partitioning)
  messageCountByAgent: Record<string, number>

  activeAgent: string
  isTyping: boolean

  addMessage: (msg: ChatMessage) => void
  switchAgent: (agent: string) => void
  setTyping: (typing: boolean) => void
  clearHistory: () => void
  archiveOldMessages: () => Promise<void>  // Move old messages to indexedDB
  loadMoreMessages: (agent: string, offset: number) => Promise<ChatMessage[]>
}

const MAX_IN_MEMORY_MESSAGES = 500  // Prevent memory leak [CRAAP-003]

export const useChatStore = create<ChatState>()(
  devtools(
    persist(
      (set, get) => ({
        messages: [],
        messageCountByAgent: {},
        activeAgent: "brian",
        isTyping: false,

        addMessage: (msg) => set((state) => {
          const newMessages = [...state.messages, msg]

          // Archive old messages if limit exceeded [CRAAP-003]
          if (newMessages.length > MAX_IN_MEMORY_MESSAGES) {
            // Archive oldest 100 messages to indexedDB
            const toArchive = newMessages.slice(0, 100)
            archiveMessagesToIndexedDB(toArchive)

            // Keep only last 500 in memory
            return {
              messages: newMessages.slice(100),
              messageCountByAgent: {
                ...state.messageCountByAgent,
                [msg.agent]: (state.messageCountByAgent[msg.agent] || 0) + 1
              }
            }
          }

          return {
            messages: newMessages,
            messageCountByAgent: {
              ...state.messageCountByAgent,
              [msg.agent]: (state.messageCountByAgent[msg.agent] || 0) + 1
            }
          }
        }),

        switchAgent: (agent) => set({
          activeAgent: agent,
          isTyping: false
        }),

        setTyping: (typing) => set({ isTyping: typing }),

        clearHistory: () => set({
          messages: [],
          messageCountByAgent: {}
        }),

        archiveOldMessages: async () => {
          const state = get()
          if (state.messages.length > MAX_IN_MEMORY_MESSAGES) {
            const toArchive = state.messages.slice(0, 100)
            await archiveMessagesToIndexedDB(toArchive)

            set({ messages: state.messages.slice(100) })
          }
        },

        loadMoreMessages: async (agent: string, offset: number) => {
          // Load from indexedDB (paginated)
          return await loadMessagesFromIndexedDB(agent, offset, 50)
        }
      }),
      { name: "chat-storage" }
    )
  )
)

// IndexedDB helpers
async function archiveMessagesToIndexedDB(messages: ChatMessage[]) {
  const db = await openChatHistoryDB()
  const tx = db.transaction('messages', 'readwrite')

  for (const message of messages) {
    await tx.store.put(message)
  }

  await tx.done
}

async function loadMessagesFromIndexedDB(agent: string, offset: number, limit: number): Promise<ChatMessage[]> {
  const db = await openChatHistoryDB()
  const tx = db.transaction('messages', 'readonly')
  const index = tx.store.index('by-agent')

  const messages = await index.getAll(agent)

  // Return paginated
  return messages.slice(offset, offset + limit)
}

function openChatHistoryDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('gao-dev-chat-history', 1)

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result
      if (!db.objectStoreNames.contains('messages')) {
        const store = db.createObjectStore('messages', { keyPath: 'id' })
        store.createIndex('by-agent', 'agent')
        store.createIndex('by-timestamp', 'timestamp')
      }
    }

    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}
```

**Per-Agent Chat History [CRAAP-008]**:
- Messages partitioned by agent: `messageCountByAgent` tracks count per agent
- Frontend filters messages by `activeAgent` when displaying
- LoadMore fetches from indexedDB filtered by agent
- Prevents mixing Brian's chat with Mary's chat

**Usage in ChatTab**:
```typescript
// gao_dev_web/src/components/ChatTab.tsx
export function ChatTab() {
  const { messages, activeAgent, loadMoreMessages } = useChatStore()
  const [isLoadingMore, setIsLoadingMore] = useState(false)

  // Filter messages for current agent only
  const agentMessages = useMemo(() =>
    messages.filter(msg => msg.agent === activeAgent || msg.agent === 'user'),
    [messages, activeAgent]
  )

  const handleLoadMore = async () => {
    setIsLoadingMore(true)
    const olderMessages = await loadMoreMessages(activeAgent, agentMessages.length)
    // Prepend to messages array
    setIsLoadingMore(false)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Load more button (shown if more history available) */}
      {agentMessages.length >= 500 && (
        <Button onClick={handleLoadMore} disabled={isLoadingMore}>
          {isLoadingMore ? 'Loading...' : 'Load older messages'}
        </Button>
      )}

      {/* Virtualized message list (only render visible) */}
      <VirtualizedMessageList messages={agentMessages} />

      {/* Input */}
      <ChatInput />
    </div>
  )
}
```

**activityStore.ts**
```typescript
interface ActivityState {
  events: ActivityEvent[]
  filters: {
    agents: string[]
    eventTypes: string[]
    timeWindow: number
  }

  addEvent: (event: ActivityEvent) => void
  setFilters: (filters: Partial<Filters>) => void
  getFilteredEvents: () => ActivityEvent[]
}

export const useActivityStore = create<ActivityState>()(
  devtools((set, get) => ({
    events: [],
    filters: {
      agents: [],
      eventTypes: [],
      timeWindow: 3600 // 1 hour
    },

    addEvent: (event) => set((state) => ({
      events: [...state.events, event]
    })),

    setFilters: (filters) => set((state) => ({
      filters: { ...state.filters, ...filters }
    })),

    getFilteredEvents: () => {
      const { events, filters } = get()
      const now = Date.now()
      const cutoff = now - (filters.timeWindow * 1000)

      return events.filter(event => {
        const timeMatch = new Date(event.timestamp).getTime() >= cutoff
        const agentMatch = filters.agents.length === 0 || filters.agents.includes(event.agent)
        const typeMatch = filters.eventTypes.length === 0 || filters.eventTypes.includes(event.type)

        return timeMatch && agentMatch && typeMatch
      })
    }
  }))
)
```

**kanbanStore.ts**
```typescript
interface KanbanState {
  epics: Epic[]
  stories: Story[]

  loadBoard: () => Promise<void>
  transitionStory: (epicNum: number, storyNum: number, status: string) => Promise<void>
}

export const useKanbanStore = create<KanbanState>()(
  devtools((set) => ({
    epics: [],
    stories: [],

    loadBoard: async () => {
      const response = await fetch("/api/kanban")
      const data = await response.json()
      set({ epics: data.epics, stories: data.stories })
    },

    transitionStory: async (epicNum, storyNum, status) => {
      // Optimistic update
      set((state) => ({
        stories: state.stories.map(s =>
          s.epic_num === epicNum && s.story_num === storyNum
            ? { ...s, status }
            : s
        )
      }))

      try {
        await fetch("/api/kanban/transition", {
          method: "POST",
          body: JSON.stringify({ epic_num: epicNum, story_num: storyNum, new_status: status })
        })
      } catch (error) {
        // Rollback on error
        await get().loadBoard()
      }
    }
  }))
)
```

#### React Context (Local State)

**Dark Mode Support**: FINAL ✅ (Option B - Both Light and Dark)

The MVP includes both light and dark themes, with automatic detection of system preference.

**ThemeContext.tsx**
```typescript
interface ThemeContextType {
  theme: "light" | "dark"
  toggleTheme: () => void
  systemPreference: "light" | "dark"
}

export const ThemeContext = createContext<ThemeContextType>(null!)

export function ThemeProvider({ children }: { children: ReactNode }) {
  // Detect system preference
  const systemPreference = window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light"

  // Load user preference or use system default
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    const saved = localStorage.getItem("gao-dev-theme")
    return (saved as "light" | "dark") || systemPreference
  })

  // Update on system preference change
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
    const handleChange = (e: MediaQueryListEvent) => {
      const newSystemPreference = e.matches ? "dark" : "light"
      // Auto-switch if user hasn't explicitly set preference
      if (!localStorage.getItem("gao-dev-theme")) {
        setTheme(newSystemPreference)
      }
    }
    mediaQuery.addEventListener("change", handleChange)
    return () => mediaQuery.removeEventListener("change", handleChange)
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light"
    setTheme(newTheme)
    localStorage.setItem("gao-dev-theme", newTheme)
  }

  // Apply theme to document root
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme)
    document.documentElement.classList.toggle("dark", theme === "dark")
  }, [theme])

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, systemPreference }}>
      {children}
    </ThemeContext.Provider>
  )
}
```

**CSS Implementation** (Tailwind + shadcn/ui):
```css
/* Respect system preference via prefers-color-scheme */
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --background: 0 0% 0%;
    --foreground: 0 0% 100%;
    /* other dark variables */
  }
}

@media (prefers-color-scheme: light) {
  :root {
    color-scheme: light;
    --background: 0 0% 100%;
    --foreground: 0 0% 3.6%;
    /* other light variables */
  }
}

/* User override (dark class on html element) */
html.dark {
  color-scheme: dark;
  --background: 0 0% 0%;
  --foreground: 0 0% 100%;
}

html:not(.dark) {
  color-scheme: light;
  --background: 0 0% 100%;
  --foreground: 0 0% 3.6%;
}
```

**Why This Decision**:
- Low implementation effort (Tailwind + shadcn/ui already support both modes)
- Respects user OS preferences automatically
- Users can override system preference with toggle button
- Modern UX expectation (light + dark is standard)
- Preference persisted to localStorage for consistency across sessions

---

## 5. Backend Architecture

### Application Structure

```
gao_dev/
├── web/                              # NEW: Web interface backend
│   ├── __init__.py
│   ├── app.py                        # FastAPI application
│   ├── api/                          # REST endpoints
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── files.py
│   │   ├── kanban.py
│   │   ├── git.py
│   │   ├── ceremonies.py
│   │   └── session.py
│   ├── websocket/                    # WebSocket management
│   │   ├── __init__.py
│   │   ├── manager.py                # WebSocketManager
│   │   └── events.py                 # Event bus
│   ├── adapters/                     # Adapter layer
│   │   ├── __init__.py
│   │   ├── brian_adapter.py          # ChatSession → WebSocket
│   │   ├── state_adapter.py          # GitIntegratedStateManager → Events
│   │   ├── ceremony_adapter.py       # CeremonyOrchestrator → Events
│   │   └── file_watcher.py           # File system → Events
│   ├── models/                       # Pydantic models
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── files.py
│   │   ├── kanban.py
│   │   └── events.py
│   └── services/                     # Business logic
│       ├── __init__.py
│       ├── session_manager.py        # Session lock management
│       └── file_service.py           # File operations
│
└── web_frontend/                     # NEW: React application
    ├── src/
    │   ├── components/
    │   ├── stores/
    │   ├── hooks/
    │   ├── lib/
    │   └── App.tsx
    ├── public/
    ├── package.json
    ├── vite.config.ts
    └── tsconfig.json
```

### FastAPI Application

**gao_dev/web/app.py**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .api import chat, files, kanban, git, ceremonies, session
from .websocket.manager import WebSocketManager
from .websocket.events import WebEventBus

app = FastAPI(
    title="GAO-Dev Web Interface",
    version="1.0.0",
    description="Browser-based interface for GAO-Dev autonomous agents"
)

# CORS middleware (localhost only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize event bus and WebSocket manager
event_bus = WebEventBus()
ws_manager = WebSocketManager(event_bus)

# Store in app state
app.state.event_bus = event_bus
app.state.ws_manager = ws_manager

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(kanban.router, prefix="/api/kanban", tags=["kanban"])
app.include_router(git.router, prefix="/api/git", tags=["git"])
app.include_router(ceremonies.router, prefix="/api/ceremonies", tags=["ceremonies"])
app.include_router(session.router, prefix="/api/session", tags=["session"])

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

# Serve frontend static files (production)
frontend_dist = Path(__file__).parent.parent.parent / "web_frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

@app.on_event("startup")
async def startup():
    # Initialize file watcher
    from .adapters.file_watcher import FileSystemWatcher
    file_watcher = FileSystemWatcher(event_bus)
    file_watcher.start()
    app.state.file_watcher = file_watcher

@app.on_event("shutdown")
async def shutdown():
    # Cleanup
    if hasattr(app.state, "file_watcher"):
        app.state.file_watcher.stop()
    await ws_manager.disconnect_all()
```

---

### Adapter Layer

#### BrianWebAdapter

**Purpose**: Bridge between ChatSession (Epic 30) and WebSocket events

**gao_dev/web/adapters/brian_adapter.py**
```python
from typing import AsyncIterator
from gao_dev.orchestrator.chat_session import ChatSession
from gao_dev.web.websocket.events import WebEventBus, WebEvent

class BrianWebAdapter:
    """
    Adapter to bridge ChatSession and WebSocket events.

    Responsibilities:
    - Wrap ChatSession.handle_input()
    - Emit chat.message events for each response chunk
    - Emit agent.activated / agent.completed events
    - Handle multi-agent switching
    """

    def __init__(self, chat_session: ChatSession, event_bus: WebEventBus):
        self.chat_session = chat_session
        self.event_bus = event_bus

    async def send_message(
        self,
        user_input: str,
        agent: str
    ) -> AsyncIterator[str]:
        """
        Send message to agent and emit events.

        Args:
            user_input: User's message
            agent: Target agent (brian, mary, john, etc.)

        Yields:
            Response chunks from agent
        """
        # Switch agent if needed
        if self.chat_session.context.current_agent != agent:
            self.switch_agent(agent)

        # Emit agent.activated event
        await self.event_bus.publish(WebEvent(
            type="agent.activated",
            data={
                "agent": agent,
                "user_input": user_input[:100]  # Preview
            }
        ))

        # Handle input via ChatSession
        async for chunk in self.chat_session.handle_input(user_input):
            # Emit chat.message event for each chunk
            await self.event_bus.publish(WebEvent(
                type="chat.message",
                data={
                    "agent": agent,
                    "message": chunk,
                    "is_chunk": True
                }
            ))

            yield chunk

        # Emit agent.completed event
        await self.event_bus.publish(WebEvent(
            type="agent.completed",
            data={"agent": agent}
        ))

    def switch_agent(self, agent: str):
        """Switch to different agent."""
        self.chat_session.context.current_agent = agent

        # Emit agent.switched event
        self.event_bus.publish_sync(WebEvent(
            type="chat.agent_switched",
            data={"agent": agent}
        ))
```

#### StateChangeAdapter

**Purpose**: Listen to GitIntegratedStateManager operations and emit events

**gao_dev/web/adapters/state_adapter.py**
```python
from gao_dev.core.services.git_integrated_state_manager import GitIntegratedStateManager
from gao_dev.web.websocket.events import WebEventBus, WebEvent

class StateChangeAdapter:
    """
    Adapter to emit events when state changes.

    Wraps GitIntegratedStateManager operations to emit WebSocket events.
    """

    def __init__(
        self,
        state_manager: GitIntegratedStateManager,
        event_bus: WebEventBus
    ):
        self.state_manager = state_manager
        self.event_bus = event_bus

    def create_epic(self, *args, **kwargs):
        """Create epic and emit event."""
        epic = self.state_manager.create_epic(*args, **kwargs)

        # Emit state.epic_created event
        self.event_bus.publish_sync(WebEvent(
            type="state.epic_created",
            data={
                "epic_num": epic["epic_num"],
                "title": epic["title"],
                "status": epic["status"]
            }
        ))

        return epic

    def create_story(self, *args, **kwargs):
        """Create story and emit event."""
        story = self.state_manager.create_story(*args, **kwargs)

        # Emit state.story_created event
        self.event_bus.publish_sync(WebEvent(
            type="state.story_created",
            data={
                "epic_num": story["epic_num"],
                "story_num": story["story_num"],
                "title": story["title"],
                "status": story["status"]
            }
        ))

        return story

    def transition_story(self, *args, **kwargs):
        """Transition story and emit event."""
        story = self.state_manager.transition_story(*args, **kwargs)

        # Emit state.changed event
        self.event_bus.publish_sync(WebEvent(
            type="state.changed",
            data={
                "epic_num": story["epic_num"],
                "story_num": story["story_num"],
                "old_status": kwargs.get("old_status"),
                "new_status": kwargs.get("new_status")
            }
        ))

        return story
```

#### FileSystemWatcher

**Purpose**: Detect file changes and emit events

**gao_dev/web/adapters/file_watcher.py**
```python
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from gao_dev.web.websocket.events import WebEventBus, WebEvent

class FileChangeHandler(FileSystemEventHandler):
    """Handler for file system events."""

    def __init__(self, event_bus: WebEventBus, project_root: Path):
        self.event_bus = event_bus
        self.project_root = project_root

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            rel_path = Path(event.src_path).relative_to(self.project_root)
            self.event_bus.publish_sync(WebEvent(
                type="file.created",
                data={
                    "path": str(rel_path),
                    "type": "file"
                }
            ))

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            rel_path = Path(event.src_path).relative_to(self.project_root)
            self.event_bus.publish_sync(WebEvent(
                type="file.modified",
                data={
                    "path": str(rel_path),
                    "type": "file"
                }
            ))

    def on_deleted(self, event: FileSystemEvent):
        if not event.is_directory:
            rel_path = Path(event.src_path).relative_to(self.project_root)
            self.event_bus.publish_sync(WebEvent(
                type="file.deleted",
                data={
                    "path": str(rel_path),
                    "type": "file"
                }
            ))

class FileSystemWatcher:
    """Watch file system for changes and emit events."""

    def __init__(self, event_bus: WebEventBus, project_root: Path):
        self.event_bus = event_bus
        self.project_root = project_root
        self.observer = Observer()

        # Watch tracked directories only
        self.watch_paths = [
            project_root / "docs",
            project_root / "src",
            project_root / "tests",
        ]

    def start(self):
        """Start watching file system."""
        handler = FileChangeHandler(self.event_bus, self.project_root)

        for path in self.watch_paths:
            if path.exists():
                self.observer.schedule(handler, str(path), recursive=True)

        self.observer.start()

    def stop(self):
        """Stop watching file system."""
        self.observer.stop()
        self.observer.join()
```

---

### WebSocket Manager

**gao_dev/web/websocket/manager.py**
```python
from typing import Dict, Set
from fastapi import WebSocket
from collections import deque
import asyncio
import structlog

from .events import WebEventBus, WebEvent

logger = structlog.get_logger()

class WebSocketManager:
    """
    Manage WebSocket connections and event broadcasting.

    Features:
    - Multiple client connections
    - Event buffering during disconnect
    - Automatic reconnection support
    - Subscription-based event filtering
    """

    def __init__(self, event_bus: WebEventBus):
        self.event_bus = event_bus
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # client_id → event_types
        self.event_buffers: Dict[str, deque] = {}
        self.buffer_size = 100

        # Subscribe to all events from event bus
        self.event_bus.subscribe_all(self.broadcast_event)

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()

        client_id = id(websocket)
        self.active_connections[str(client_id)] = websocket
        self.subscriptions[str(client_id)] = set()
        self.event_buffers[str(client_id)] = deque(maxlen=self.buffer_size)

        logger.info("websocket_connected", client_id=client_id)

        try:
            await self.handle_client(str(client_id), websocket)
        except Exception as e:
            logger.error("websocket_error", client_id=client_id, error=str(e))
        finally:
            await self.disconnect(str(client_id))

    async def handle_client(self, client_id: str, websocket: WebSocket):
        """Handle messages from client."""
        while True:
            try:
                data = await websocket.receive_json()

                if data["type"] == "ping":
                    await websocket.send_json({"type": "pong"})

                elif data["type"] == "subscribe":
                    event_types = data.get("event_types", [])
                    self.subscriptions[client_id].update(event_types)
                    logger.info("client_subscribed", client_id=client_id, event_types=event_types)

            except Exception as e:
                logger.error("client_message_error", client_id=client_id, error=str(e))
                break

    async def disconnect(self, client_id: str):
        """Disconnect client."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
        # Keep buffer for potential reconnection

        logger.info("websocket_disconnected", client_id=client_id)

    async def disconnect_all(self):
        """Disconnect all clients."""
        for client_id in list(self.active_connections.keys()):
            await self.disconnect(client_id)

    async def broadcast_event(self, event: WebEvent):
        """Broadcast event to all subscribed clients."""
        disconnected_clients = []

        for client_id, websocket in list(self.active_connections.items()):
            # Check if client subscribed to this event type
            subscriptions = self.subscriptions.get(client_id, set())
            if not subscriptions or event.type in subscriptions:
                try:
                    await websocket.send_json({
                        "type": "event",
                        "event_type": event.type,
                        "data": event.data,
                        "timestamp": event.timestamp.isoformat()
                    })

                    # Buffer event
                    self.event_buffers[client_id].append(event)

                except Exception as e:
                    logger.error("broadcast_failed", client_id=client_id, error=str(e))
                    disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
```

---

## 6. Event-Driven Architecture

### Event Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    GAO-Dev Operations                           │
│  (ChatSession, GitIntegratedStateManager, WorkflowExecutor)     │
└─────────────┬───────────────────────────────────────────────────┘
              │
              │ Emit events
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Adapter Layer                                │
│  - BrianWebAdapter                                              │
│  - StateChangeAdapter                                           │
│  - CeremonyAdapter                                              │
│  - FileSystemWatcher                                            │
└─────────────┬───────────────────────────────────────────────────┘
              │
              │ Publish to event bus
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WebEventBus (asyncio.Queue)                  │
│  - Event routing                                                │
│  - Subscriber management                                        │
│  - Event buffering                                              │
└─────────────┬───────────────────────────────────────────────────┘
              │
              │ Subscribe and consume
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WebSocketManager                             │
│  - Client connection management                                 │
│  - Event broadcasting                                           │
│  - Subscription filtering                                       │
└─────────────┬───────────────────────────────────────────────────┘
              │
              │ WebSocket messages
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React)                             │
│  - Zustand stores updated                                       │
│  - UI components re-render                                      │
│  - User sees real-time updates                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Event Schema [CRAAP-004, CRAAP-009]

All events follow this standard structure with loop prevention and ordering guarantees:

```typescript
interface WebEvent {
  type: string              // Event type (e.g., "chat.message")
  data: object              // Event-specific payload
  timestamp: string         // ISO 8601 timestamp
  sequence_number: number   // Monotonic counter for ordering [CRAAP-009]
  correlation_id?: string   // Optional for request tracing (groups related events)
  source: EventSource       // [CRAAP-004] Prevent circular dependencies
}

enum EventSource {
  AGENT = "agent",      // Emitted by AI agent operations
  USER = "user",        // Emitted by user interactions (clicks, edits, drags)
  SELF = "self"         // Emitted by internal system operations (watcher seeing its own writes)
}
```

**Key Fields Explained**:

1. **`sequence_number` [CRAAP-009]**: Monotonically increasing counter to prevent out-of-order display
   - Generated by EventBus on publish
   - Client can reorder events if received out-of-sequence
   - Example: Event with `sequence_number: 100` always displays before `sequence_number: 101`

2. **`source` [CRAAP-004]**: Identifies event origin to prevent circular dependencies
   - **`agent`**: Agent created file → FileSystemWatcher emits event with `source="agent"`
   - **`user`**: User saved file in Monaco → Emit event with `source="user"`
   - **`self`**: Adapter writes file in response to event → Mark as `source="self"`, filter from re-broadcast

3. **`correlation_id` [CRAAP-009]**: Groups related events for better UX
   - All events from single workflow share same correlation_id
   - Example: `workflow.started`, `agent.activated`, `file.created` all have `correlation_id="workflow-123"`
   - Frontend can highlight related events in Activity Stream

**Circular Dependency Prevention Logic**:

```python
# gao_dev/web/adapters/file_system_watcher.py
class FileSystemWatcher:
    def __init__(self, event_bus: WebEventBus):
        self.event_bus = event_bus
        self.deduplication_cache: set[tuple[str, str, int]] = set()  # (path, event_type, mtime)

    async def on_file_created(self, file_path: Path):
        """Emit file.created event with source detection."""
        # Get file modification time
        mtime = file_path.stat().st_mtime_ns

        # Deduplicate: ignore if we've seen this exact event recently
        cache_key = (str(file_path), "created", mtime)
        if cache_key in self.deduplication_cache:
            return  # Skip duplicate event

        self.deduplication_cache.add(cache_key)

        # Detect source: did an agent create this or system?
        source = self.detect_source(file_path)

        # Emit event
        await self.event_bus.publish(WebEvent(
            type="file.created",
            data={"path": str(file_path), "size": file_path.stat().st_size},
            source=source  # <-- Key: preserve source
        ))

    def detect_source(self, file_path: Path) -> EventSource:
        """Heuristic to detect event source."""
        # Check if file created by GitIntegratedStateManager (has commit)
        if self.has_recent_git_commit(file_path):
            return EventSource.AGENT  # Agent-created (via GitIntegratedStateManager)
        else:
            return EventSource.USER  # User-created (manual edit)
```

**Client-Side Sequence Number Handling**:

```typescript
// gao_dev_web/src/hooks/useActivityStream.ts
const REORDER_BUFFER_DURATION = 30000  // 30 seconds

interface BufferedEvent {
  event: WebEvent
  receivedAt: number
}

export function useActivityStream() {
  const [events, setEvents] = useState<WebEvent[]>([])
  const [buffer, setBuffer] = useState<BufferedEvent[]>([])

  useEffect(() => {
    const interval = setInterval(() => {
      // Flush buffer every 1 second
      setBuffer(currentBuffer => {
        if (currentBuffer.length === 0) return currentBuffer

        // Sort by sequence number
        const sorted = [...currentBuffer].sort((a, b) =>
          a.event.sequence_number - b.event.sequence_number
        )

        // Add to main events list
        setEvents(prevEvents => [...prevEvents, ...sorted.map(b => b.event)])

        return []
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  const handleEvent = useCallback((event: WebEvent) => {
    // Filter self-triggered events [CRAAP-004]
    if (event.source === EventSource.SELF) {
      return  // Don't display internal system events
    }

    // Add to reorder buffer
    setBuffer(prev => [...prev, { event, receivedAt: Date.now() }])
  }, [])

  return { events, handleEvent }
}
```

---

### Loop Prevention Flow [CRAAP-004]

**Problem**: FileSystemWatcher → Event → Adapter → File Write → FileSystemWatcher = INFINITE LOOP

**Solution**: Mark events with `source` field and filter self-triggered events

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Agent writes file via GitIntegratedStateManager              │
│    source = "agent"                                             │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. FileSystemWatcher detects file creation                      │
│    Emit event with source = "agent" (preserved)                 │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. EventBus broadcasts to all adapters                          │
│    Event: { type: "file.created", source: "agent", ... }        │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. StateChangeAdapter receives event                            │
│    Check: source === "agent" → Already processed by agent       │
│    Action: DO NOT write file again → LOOP PREVENTED ✓           │
└─────────────────────────────────────────────────────────────────┘
```

**If source === "user"**:
- User manually edited file in Monaco
- FileSystemWatcher emits with `source="user"`
- Adapters CAN react (e.g., update DB, create git commit)
- No loop because adapters mark their writes as `source="self"`

---

### Event Types Reference

| Event Type | Data Schema | Emitted By | Consumed By |
|-----------|-------------|------------|-------------|
| `chat.message` | `{agent, message, is_chunk}` | BrianWebAdapter | ChatTab |
| `chat.agent_switched` | `{agent}` | BrianWebAdapter | ChatTab, TopBar |
| `workflow.started` | `{workflow_name, scale_level}` | WorkflowAdapter | ActivityStreamTab |
| `workflow.step_started` | `{workflow_name, step, agent}` | WorkflowAdapter | ActivityStreamTab |
| `workflow.completed` | `{workflow_name, duration}` | WorkflowAdapter | ActivityStreamTab |
| `agent.activated` | `{agent, task_preview}` | BrianWebAdapter | ActivityStreamTab |
| `agent.tool_used` | `{agent, tool, params}` | AgentAdapter | ActivityStreamTab |
| `file.created` | `{path, type}` | FileSystemWatcher | FilesTab, ActivityStreamTab |
| `file.modified` | `{path, size}` | FileSystemWatcher | FilesTab |
| `git.commit` | `{sha, message, author}` | GitAdapter | GitTab, ActivityStreamTab |
| `state.changed` | `{epic_num, story_num, old_status, new_status}` | StateChangeAdapter | KanbanBoardTab |
| `state.epic_created` | `{epic_num, title}` | StateChangeAdapter | KanbanBoardTab |
| `state.story_created` | `{epic_num, story_num, title}` | StateChangeAdapter | KanbanBoardTab |
| `ceremony.started` | `{type, epic_num, participants}` | CeremonyAdapter | CeremonyChannelsTab |
| `ceremony.message` | `{agent, message}` | CeremonyAdapter | CeremonyChannelsTab |
| `ceremony.completed` | `{type, duration}` | CeremonyAdapter | CeremonyChannelsTab |

---

## 7. Integration Architecture

### Epic 30: ChatREPL Integration

**Objective**: Reuse ChatSession instance for web interface

**Integration Pattern**:
```python
# gao_dev/web/api/chat.py
from gao_dev.orchestrator.chat_session import ChatSession
from gao_dev.web.adapters.brian_adapter import BrianWebAdapter

# Shared ChatSession instance (singleton)
chat_session = ChatSession(
    conversational_brian=brian,
    command_router=router,
    project_root=project_root
)

# Wrap with adapter
brian_adapter = BrianWebAdapter(chat_session, event_bus)

@router.post("/")
async def send_message(request: ChatRequest):
    async for chunk in brian_adapter.send_message(request.message, request.agent):
        # Chunks are already broadcast via WebSocket
        pass

    return {"success": True}
```

**Multi-Agent Switching**:
```python
# ChatSession extended to support current_agent
class SessionContext:
    # ...existing fields...
    current_agent: str = "brian"  # NEW: Track active agent

# Frontend requests switch
POST /api/agents/switch {"agent": "mary"}

# Backend updates ChatSession
chat_session.context.current_agent = "mary"

# Next message routed to Mary
chat_session.handle_input("Let's brainstorm ideas for user auth")
```

---

### Epic 27: GitIntegratedStateManager Integration

**Objective**: ALL file operations through GitIntegratedStateManager, query `.gao-dev/documents.db` for Kanban board

**Integration Pattern**:
```python
# gao_dev/web/api/files.py
from gao_dev.core.services.git_integrated_state_manager import GitIntegratedStateManager

# Shared instance
state_manager = GitIntegratedStateManager(
    db_path=Path(".gao-dev/documents.db"),
    project_path=project_root
)

# Wrap with adapter to emit events
state_adapter = StateChangeAdapter(state_manager, event_bus)

@router.post("/{path}")
async def save_file(path: str, request: SaveFileRequest):
    # Validate commit message
    if not request.commit_message:
        raise HTTPException(400, "Commit message required")

    # Write file via GitIntegratedStateManager (atomic: file + git)
    full_path = project_root / path
    full_path.write_text(request.content, encoding="utf-8")

    # Git commit (atomic)
    state_manager.git_manager.add_all()
    commit_sha = state_manager.git_manager.commit(request.commit_message)

    # Emit event (via FileSystemWatcher)
    # No manual event emission needed - watcher detects file change

    return {"success": True, "commit_sha": commit_sha}
```

**Kanban Board Queries**:
```python
# gao_dev/web/api/kanban.py
from gao_dev.core.state_coordinator import StateCoordinator

coordinator = StateCoordinator(
    db_path=Path(".gao-dev/documents.db"),
    project_root=project_root
)

@router.get("/")
async def get_kanban_board():
    # Query database directly
    epics = coordinator.epic_service.list_all()
    stories = coordinator.story_service.list_all()

    return {
        "epics": [epic.dict() for epic in epics],
        "stories": [story.dict() for story in stories]
    }

@router.post("/transition")
async def transition_story(request: TransitionRequest):
    # Use GitIntegratedStateManager for atomic update
    story = state_adapter.transition_story(
        epic_num=request.epic_num,
        story_num=request.story_num,
        new_status=request.new_status,
        actual_hours=request.actual_hours
    )

    # Event already emitted by StateChangeAdapter
    return {"success": True, "story": story}
```

**State Change Event Streaming**:
```python
# Adapter automatically emits events
class StateChangeAdapter:
    def transition_story(self, *args, **kwargs):
        story = self.state_manager.transition_story(*args, **kwargs)

        # Emit to WebSocket
        self.event_bus.publish_sync(WebEvent(
            type="state.changed",
            data={
                "epic_num": story["epic_num"],
                "story_num": story["story_num"],
                "new_status": story["status"]
            }
        ))

        return story
```

### File Locking and Conflict Resolution [CRAAP-005]

**Critical Issue**: User editing file in Monaco while agent modifies same file = data loss, conflicting edits

**Solution**: File-level operation locking with conflict resolution UI

**1. File Lock Manager**:
```python
# gao_dev/web/services/file_lock_manager.py
from asyncio import Lock
from pathlib import Path
from typing import Dict, Optional
import time

class FileLock:
    def __init__(self, path: Path, holder: str):
        self.path = path
        self.holder = holder  # "user" or "agent:{agent_name}"
        self.acquired_at = time.time()
        self.lock = Lock()

class FileLockManager:
    """Prevent simultaneous edits by user + agent on same file."""

    def __init__(self):
        self.locks: Dict[str, FileLock] = {}
        self.LOCK_TIMEOUT = 30  # seconds

    async def acquire(self, file_path: Path, holder: str) -> bool:
        """
        Attempt to acquire lock on file.

        Args:
            file_path: Path to file
            holder: "user" or "agent:amelia"

        Returns:
            True if acquired, False if already locked
        """
        path_str = str(file_path)

        # Check for existing lock
        if path_str in self.locks:
            existing = self.locks[path_str]

            # Check timeout
            age = time.time() - existing.acquired_at
            if age > self.LOCK_TIMEOUT:
                # Stale lock - remove and continue
                await self.force_unlock(file_path)
            else:
                # Active lock held by someone else
                return False

        # Acquire lock
        self.locks[path_str] = FileLock(path=file_path, holder=holder)
        return True

    async def release(self, file_path: Path):
        """Release lock on file."""
        path_str = str(file_path)
        if path_str in self.locks:
            del self.locks[path_str]

    async def force_unlock(self, file_path: Path):
        """Force-unlock file (timeout or user override)."""
        await self.release(file_path)

    def get_lock(self, file_path: Path) -> Optional[FileLock]:
        """Get current lock holder."""
        return self.locks.get(str(file_path))
```

**2. Lock Acquisition on File Open**:
```python
# gao_dev/web/api/files.py
from gao_dev.web.services.file_lock_manager import FileLockManager

file_lock_manager = FileLockManager()

@router.post("/{path}/lock")
async def acquire_file_lock(path: str):
    """User opens file in Monaco - acquire lock."""
    file_path = project_root / path

    acquired = await file_lock_manager.acquire(file_path, holder="user")

    if not acquired:
        # Lock held by agent
        lock = file_lock_manager.get_lock(file_path)
        return {
            "acquired": False,
            "holder": lock.holder,
            "message": f"File is currently being edited by {lock.holder}"
        }

    return {"acquired": True}

@router.post("/{path}/unlock")
async def release_file_lock(path: str):
    """User closes file in Monaco - release lock."""
    file_path = project_root / path
    await file_lock_manager.release(file_path)
    return {"success": True}
```

**3. Agent Respects Locks**:
```python
# gao_dev/web/adapters/brian_adapter.py
class BrianWebAdapter:
    async def execute_write_tool(self, file_path: Path, content: str):
        """Agent attempts to write file."""
        # Check lock
        acquired = await self.file_lock_manager.acquire(file_path, holder=f"agent:{self.agent_name}")

        if not acquired:
            # File locked by user
            lock = self.file_lock_manager.get_lock(file_path)

            # Emit warning event
            await self.event_bus.publish(WebEvent(
                type="file.lock_conflict",
                data={
                    "path": str(file_path),
                    "agent": self.agent_name,
                    "holder": lock.holder
                }
            ))

            # Wait and retry (exponential backoff)
            for attempt in range(5):
                await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s, 16s
                if await self.file_lock_manager.acquire(file_path, holder=f"agent:{self.agent_name}"):
                    break
            else:
                # Give up after 5 attempts
                raise HTTPException(409, f"File locked by {lock.holder}, cannot write")

        try:
            # Write file
            file_path.write_text(content)
            await self.git_manager.commit(f"Update {file_path.name}")

        finally:
            # Always release lock
            await self.file_lock_manager.release(file_path)
```

**4. Conflict Detection (Checksums)**:
```python
# gao_dev/web/api/files.py
import hashlib

@router.post("/{path}/save")
async def save_file(path: str, request: SaveFileRequest):
    """Save file with conflict detection."""
    file_path = project_root / path

    # Calculate checksum of current file
    current_content = file_path.read_text() if file_path.exists() else ""
    current_checksum = hashlib.sha256(current_content.encode()).hexdigest()

    # Compare with client's checksum (client sends checksum of version they opened)
    if request.base_checksum and request.base_checksum != current_checksum:
        # Conflict detected!
        return {
            "success": False,
            "conflict": True,
            "server_content": current_content,
            "server_checksum": current_checksum,
            "message": "File was modified while you were editing. Please resolve conflict."
        }

    # No conflict - save
    file_path.write_text(request.content)

    return {
        "success": True,
        "checksum": hashlib.sha256(request.content.encode()).hexdigest()
    }
```

**5. Conflict Resolution UI**:
```typescript
// gao_dev_web/src/components/ConflictModal.tsx
interface ConflictModalProps {
  filePath: string
  clientContent: string
  serverContent: string
  onResolve: (resolvedContent: string) => void
  onCancel: () => void
}

export function ConflictModal({ filePath, clientContent, serverContent, onResolve, onCancel }: ConflictModalProps) {
  const [selectedVersion, setSelectedVersion] = useState<'client' | 'server' | 'manual'>('client')
  const [manualContent, setManualContent] = useState(clientContent)

  return (
    <Dialog open>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="text-yellow-500" />
            Merge Conflict: {filePath}
          </DialogTitle>
        </DialogHeader>

        <p className="text-gray-400">
          The file was modified while you were editing. Choose which version to keep:
        </p>

        <Tabs defaultValue="diff">
          <TabsList>
            <TabsTrigger value="diff">Diff View</TabsTrigger>
            <TabsTrigger value="yours">Your Version</TabsTrigger>
            <TabsTrigger value="theirs">Server Version</TabsTrigger>
            <TabsTrigger value="manual">Manual Merge</TabsTrigger>
          </TabsList>

          <TabsContent value="diff">
            {/* Monaco diff editor */}
            <DiffEditor
              original={serverContent}
              modified={clientContent}
              language="markdown"
              theme="vs-dark"
            />
          </TabsContent>

          <TabsContent value="yours">
            <CodeBlock content={clientContent} />
          </TabsContent>

          <TabsContent value="theirs">
            <CodeBlock content={serverContent} />
          </TabsContent>

          <TabsContent value="manual">
            <MonacoEditor
              value={manualContent}
              onChange={setManualContent}
              language="markdown"
            />
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>

          <Button
            variant="primary"
            onClick={() => {
              const resolvedContent =
                selectedVersion === 'client' ? clientContent :
                selectedVersion === 'server' ? serverContent :
                manualContent

              onResolve(resolvedContent)
            }}
          >
            Save {selectedVersion === 'client' ? 'Your Version' :
                  selectedVersion === 'server' ? 'Server Version' :
                  'Manual Merge'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

**6. Frontend Integration**:
```typescript
// gao_dev_web/src/hooks/useFileSave.ts
async function saveFile(path: string, content: string, baseChecksum: string) {
  const response = await api.saveFile(path, {
    content,
    base_checksum: baseChecksum,
    commit_message: "Update via web interface"
  })

  if (response.conflict) {
    // Show conflict resolution modal
    const resolvedContent = await showConflictModal({
      filePath: path,
      clientContent: content,
      serverContent: response.server_content
    })

    // Retry save with resolved content
    await saveFile(path, resolvedContent, response.server_checksum)
  } else {
    showInfo('File saved successfully')
  }
}
```

**7. Lock Event Notifications**:
```typescript
// gao_dev_web/src/hooks/useFileOpen.ts
export function useFileOpen(path: string) {
  const ws = useWebSocket()

  useEffect(() => {
    // Acquire lock when file opens
    api.acquireFileLock(path).then(result => {
      if (!result.acquired) {
        showWarning(`File is being edited by ${result.holder}. You can view but not edit.`)
        setReadOnly(true)
      }
    })

    // Listen for lock conflict events
    const handleLockConflict = (event: WebEvent) => {
      if (event.type === 'file.lock_conflict' && event.data.path === path) {
        showWarning(`Agent ${event.data.agent} is trying to edit this file. Save your changes soon.`)
      }
    }

    ws?.addEventListener('message', handleLockConflict)

    return () => {
      // Release lock when file closes
      api.releaseFileLock(path)
      ws?.removeEventListener('message', handleLockConflict)
    }
  }, [path])
}
```

**Summary**:
- **File-level locks**: Prevent simultaneous edits
- **Timeout (30s)**: Prevent stale locks from blocking forever
- **Checksum validation**: Detect conflicts even if lock fails
- **Diff UI**: User can choose version or manually merge
- **Agent retry logic**: Agent waits for user to finish editing

---

### ChatSession API Contract [CRAAP-014]

**Issue**: Tight coupling to ChatSession internals (e.g., accessing `.context.current_agent` directly)

**Solution**: Define public API contract for Epic 30 integration

**Public API**:
```python
# gao_dev/orchestrator/chat_session.py
from typing import Protocol, AsyncIterator

class IChatSession(Protocol):
    """Public API contract for ChatSession (Epic 30 integration)."""

    async def send_message(self, message: str, agent: str | None = None) -> AsyncIterator[str]:
        """
        Send message to chat session.

        Args:
            message: User message
            agent: Optional agent to route to (default: current active agent)

        Yields:
            Response chunks from agent
        """
        ...

    def get_active_agent(self) -> str:
        """Get currently active agent name."""
        ...

    def switch_agent(self, agent: str) -> None:
        """Switch to different agent."""
        ...

    def get_conversation_history(self, limit: int = 50) -> list[dict]:
        """Get recent conversation history."""
        ...

    def clear_history(self) -> None:
        """Clear conversation history."""
        ...
```

**Implementation**:
```python
class ChatSession:
    """Concrete implementation of IChatSession."""

    async def send_message(self, message: str, agent: str | None = None) -> AsyncIterator[str]:
        if agent:
            self.switch_agent(agent)

        async for chunk in self.conversational_brian.handle_input(message):
            yield chunk

    def get_active_agent(self) -> str:
        return self.context.current_agent

    def switch_agent(self, agent: str) -> None:
        self.context.current_agent = agent

    def get_conversation_history(self, limit: int = 50) -> list[dict]:
        return self.context.conversation_history[-limit:]

    def clear_history(self) -> None:
        self.context.conversation_history.clear()
```

**Adapter Usage** (avoids tight coupling):
```python
# gao_dev/web/adapters/brian_adapter.py
class BrianWebAdapter:
    def __init__(self, chat_session: IChatSession, event_bus: WebEventBus):
        self.chat_session = chat_session  # Type: IChatSession
        self.event_bus = event_bus

    async def send_message(self, message: str, agent: str | None = None):
        # Use public API (not internal .context)
        async for chunk in self.chat_session.send_message(message, agent):
            await self.event_bus.publish(WebEvent(
                type="chat.message",
                data={"agent": self.chat_session.get_active_agent(), "message": chunk}
            ))

    async def switch_agent(self, agent: str):
        # Use public API
        self.chat_session.switch_agent(agent)

        await self.event_bus.publish(WebEvent(
            type="chat.agent_switched",
            data={"agent": agent}
        ))
```

**Benefits**:
- **Loose coupling**: Adapter doesn't depend on ChatSession internals
- **Testability**: Easy to mock IChatSession for tests
- **Version stability**: Changes to ChatSession internals don't break adapter
- **Clear boundaries**: Public API is documented and stable

---

### Epic 28: CeremonyOrchestrator Integration

**Objective**: Stream intra-agent messages to Ceremony Channels tab, activate/deactivate UI dynamically

**Integration Pattern**:
```python
# gao_dev/web/adapters/ceremony_adapter.py
from gao_dev.orchestrator.ceremony_orchestrator import CeremonyOrchestrator

class CeremonyWebAdapter:
    """Adapter to emit ceremony events to WebSocket."""

    def __init__(self, ceremony_orchestrator: CeremonyOrchestrator, event_bus: WebEventBus):
        self.orchestrator = ceremony_orchestrator
        self.event_bus = event_bus

    def hold_ceremony(self, ceremony_type: str, epic_num: int, participants: List[str]):
        """Hold ceremony and emit events."""
        # Emit ceremony.started
        self.event_bus.publish_sync(WebEvent(
            type="ceremony.started",
            data={
                "type": ceremony_type,
                "epic_num": epic_num,
                "participants": participants
            }
        ))

        # Hold ceremony (existing logic)
        result = self.orchestrator.hold_ceremony(
            ceremony_type=ceremony_type,
            epic_num=epic_num,
            participants=participants
        )

        # Parse transcript for intra-agent messages
        for message in self._parse_transcript(result["transcript"]):
            self.event_bus.publish_sync(WebEvent(
                type="ceremony.message",
                data={
                    "ceremony_id": result["ceremony_id"],
                    "agent": message["agent"],
                    "content": message["content"],
                    "timestamp": message["timestamp"]
                }
            ))

        # Emit ceremony.completed
        self.event_bus.publish_sync(WebEvent(
            type="ceremony.completed",
            data={
                "type": ceremony_type,
                "ceremony_id": result["ceremony_id"],
                "duration": result.get("duration")
            }
        ))

        return result

    def _parse_transcript(self, transcript: str) -> List[Dict]:
        """Parse transcript into individual messages."""
        messages = []
        for line in transcript.split("\n"):
            if ":" in line:
                agent, content = line.split(":", 1)
                messages.append({
                    "agent": agent.strip(),
                    "content": content.strip(),
                    "timestamp": datetime.now().isoformat()
                })
        return messages
```

**Frontend Dynamic Tab Activation**:
```typescript
// hooks/useCeremonyStatus.ts
import { useEffect } from "react"
import { useWebSocket } from "./useWebSocket"

export function useCeremonyStatus() {
  const [activeCeremony, setActiveCeremony] = useState<string | null>(null)
  const { subscribe } = useWebSocket()

  useEffect(() => {
    const unsubscribe = subscribe("ceremony.started", (event) => {
      setActiveCeremony(event.data.type)
    })

    const unsubscribe2 = subscribe("ceremony.completed", () => {
      setActiveCeremony(null)
    })

    return () => {
      unsubscribe()
      unsubscribe2()
    }
  }, [])

  return { activeCeremony, isCeremonyActive: !!activeCeremony }
}

// components/Sidebar.tsx
function Sidebar() {
  const { isCeremonyActive } = useCeremonyStatus()

  return (
    <div>
      <TabIcon icon="chat" />
      <TabIcon icon="activity" />
      <TabIcon icon="kanban" />
      <TabIcon icon="files" />
      <TabIcon icon="git" />
      {isCeremonyActive && <TabIcon icon="ceremony" />}  {/* Conditional */}
    </div>
  )
}
```

---

## 8. Performance Optimizations

### Virtual Scrolling Implementation

**Library**: @tanstack/react-virtual

**Use Cases**:
1. Activity Stream (10,000+ events)
2. File Tree (500+ files)
3. Kanban Board (1,000+ stories)

**Implementation Example (Activity Stream)**:
```typescript
import { useVirtualizer } from "@tanstack/react-virtual"

function ActivityStreamTab() {
  const parentRef = useRef<HTMLDivElement>(null)
  const { filteredEvents } = useActivityStore()

  const virtualizer = useVirtualizer({
    count: filteredEvents.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,  // Estimated row height
    overscan: 10,            // Render 10 extra rows above/below viewport
  })

  return (
    <div ref={parentRef} style={{ height: "100%", overflow: "auto" }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px`, position: "relative" }}>
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.index}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <ActivityEvent event={filteredEvents[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  )
}
```

**Performance Targets**:
- Initial render: <200ms (100 visible items)
- Scroll FPS: 60fps (smooth scrolling)
- Memory: <50MB for 10,000 items

---

### Lazy Loading Strategies

**1. Tab Lazy Loading**:
```typescript
// App.tsx
const ChatTab = lazy(() => import("./components/ChatTab"))
const ActivityStreamTab = lazy(() => import("./components/ActivityStreamTab"))
const KanbanBoardTab = lazy(() => import("./components/KanbanBoardTab"))
const FilesTab = lazy(() => import("./components/FilesTab"))
const GitTab = lazy(() => import("./components/GitTab"))
const CeremonyChannelsTab = lazy(() => import("./components/CeremonyChannelsTab"))

function MainContent({ activeTab }: { activeTab: string }) {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      {activeTab === "chat" && <ChatTab />}
      {activeTab === "activity" && <ActivityStreamTab />}
      {activeTab === "kanban" && <KanbanBoardTab />}
      {activeTab === "files" && <FilesTab />}
      {activeTab === "git" && <GitTab />}
      {activeTab === "ceremony" && <CeremonyChannelsTab />}
    </Suspense>
  )
}
```

**2. Monaco Editor Lazy Loading**:
```typescript
// Only load Monaco when Files Tab is active
import { lazy, Suspense } from "react"

const MonacoEditor = lazy(() => import("@monaco-editor/react"))

function FilesTab() {
  const [isEditorReady, setIsEditorReady] = useState(false)

  return (
    <Suspense fallback={<EditorSkeleton />}>
      {isEditorReady && (
        <MonacoEditor
          path={activeFile.path}
          value={activeFile.content}
          onMount={() => console.log("Monaco loaded")}
        />
      )}
    </Suspense>
  )
}
```

**3. Activity Stream Pagination**:
```typescript
// Load events in time windows
const useActivityPagination = () => {
  const [timeWindow, setTimeWindow] = useState(3600)  // 1 hour default
  const { events } = useActivityStore()

  const visibleEvents = useMemo(() => {
    const now = Date.now()
    const cutoff = now - (timeWindow * 1000)
    return events.filter(e => new Date(e.timestamp).getTime() >= cutoff)
  }, [events, timeWindow])

  const extendWindow = (newWindow: number) => {
    setTimeWindow(newWindow)
  }

  return { visibleEvents, timeWindow, extendWindow }
}
```

---

### Monaco Editor Optimization

**1. Editor Instance Pooling**:
```typescript
class MonacoEditorPool {
  private pool: monaco.editor.IStandaloneCodeEditor[] = []
  private maxPoolSize = 3

  acquire(): monaco.editor.IStandaloneCodeEditor | null {
    return this.pool.pop() || null
  }

  release(editor: monaco.editor.IStandaloneCodeEditor) {
    if (this.pool.length < this.maxPoolSize) {
      this.pool.push(editor)
    } else {
      editor.dispose()  // Dispose if pool full
    }
  }
}
```

**2. Model Disposal**:
```typescript
function EditorPanel() {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor>()
  const modelRef = useRef<monaco.editor.ITextModel>()

  useEffect(() => {
    // Dispose old model when file changes
    return () => {
      if (modelRef.current) {
        modelRef.current.dispose()
      }
    }
  }, [activeFile.path])
}
```

**3. File Limit (Max 10 Open Files)**:
```typescript
const useOpenFiles = () => {
  const [openFiles, setOpenFiles] = useState<File[]>([])
  const MAX_FILES = 10

  const openFile = (file: File) => {
    setOpenFiles(prev => {
      // Remove oldest file if at limit (LRU)
      if (prev.length >= MAX_FILES) {
        const oldest = prev[0]
        closeFile(oldest.path)
        return [...prev.slice(1), file]
      }
      return [...prev, file]
    })
  }

  return { openFiles, openFile }
}
```

---

### WebSocket Message Throttling

**Batch Events During High Volume**:
```python
class WebSocketManager:
    def __init__(self, event_bus: WebEventBus):
        # ...
        self.batch_size = 10
        self.batch_timeout = 0.1  # 100ms
        self.pending_events: List[WebEvent] = []

    async def broadcast_event(self, event: WebEvent):
        """Batch events to reduce WebSocket overhead."""
        self.pending_events.append(event)

        if len(self.pending_events) >= self.batch_size:
            await self.flush_events()
        else:
            # Flush after timeout
            asyncio.create_task(self.flush_after_timeout())

    async def flush_events(self):
        """Send batched events."""
        if not self.pending_events:
            return

        batch = self.pending_events.copy()
        self.pending_events.clear()

        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json({
                    "type": "event_batch",
                    "events": [
                        {
                            "event_type": e.type,
                            "data": e.data,
                            "timestamp": e.timestamp.isoformat()
                        }
                        for e in batch
                    ]
                })
            except Exception as e:
                logger.error("batch_send_failed", error=str(e))

    async def flush_after_timeout(self):
        await asyncio.sleep(self.batch_timeout)
        await self.flush_events()
```

---

## 9. Security Architecture

### Localhost-Only Security (Current)

**1. Bind to 127.0.0.1 Only**:
```python
# gao_dev/web/app.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",  # CRITICAL: localhost only
        port=3000,
        log_level="info"
    )
```

**2. CORS Configuration**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],  # Only localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**3. Session Lock Implementation**:
```python
# gao_dev/web/services/session_manager.py
from pathlib import Path
import os
import psutil

class SessionLock:
    """Mutual exclusion lock for CLI vs web interface."""

    def __init__(self, project_root: Path):
        self.lock_file = project_root / ".gao-dev" / "session.lock"

    def acquire(self, interface: str) -> bool:
        """
        Acquire session lock.

        Args:
            interface: "cli" or "web"

        Returns:
            True if acquired, False if already locked
        """
        # Check for existing lock
        if self.lock_file.exists():
            lock_data = json.loads(self.lock_file.read_text())

            # Validate PID (detect stale lock)
            if self.is_process_alive(lock_data["pid"]):
                return False  # Lock held by active process
            else:
                # Stale lock - remove and continue
                self.lock_file.unlink()

        # Acquire lock
        lock_data = {
            "interface": interface,
            "pid": os.getpid(),
            "timestamp": datetime.now().isoformat()
        }

        self.lock_file.write_text(json.dumps(lock_data, indent=2))
        return True

    def release(self):
        """Release session lock."""
        if self.lock_file.exists():
            self.lock_file.unlink()

    def is_process_alive(self, pid: int) -> bool:
        """Check if process is alive."""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            return False
```

**4. Path Validation (Prevent Directory Traversal)**:
```python
def validate_file_path(project_root: Path, requested_path: str) -> Path:
    """
    Validate file path to prevent directory traversal.

    Args:
        project_root: Project root directory
        requested_path: User-requested path

    Returns:
        Validated absolute path

    Raises:
        HTTPException(403): If path escapes project root
    """
    # Resolve to absolute path
    full_path = (project_root / requested_path).resolve()

    # Ensure path is within project root
    if not str(full_path).startswith(str(project_root)):
        raise HTTPException(403, "Path outside project root")

    return full_path
```

**5. Input Sanitization**:
```python
from pydantic import BaseModel, validator

class SaveFileRequest(BaseModel):
    content: str
    commit_message: str

    @validator("commit_message")
    def validate_commit_message(cls, v):
        # Prevent command injection in git commit
        if ";" in v or "|" in v or "`" in v:
            raise ValueError("Invalid characters in commit message")

        if len(v) < 10:
            raise ValueError("Commit message too short")

        return v
```

---

### WebSocket Security [CRAAP-001]

**Critical Security Issue**: WebSocket connections must be authenticated to prevent malicious websites from connecting to `ws://localhost:3000/ws`.

**Attack Vector**: Without authentication, any website can open a WebSocket connection to localhost and read all events (file contents, chat messages, etc.).

**Mitigation Strategy**:

**1. Generate Session Token on Server Startup**:
```python
# gao_dev/web/app.py
import secrets
from pathlib import Path

class WebServer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.session_token = self.generate_session_token()

    def generate_session_token(self) -> str:
        """Generate cryptographically random session token."""
        token = secrets.token_urlsafe(32)  # 256 bits of entropy

        # Store token in .gao-dev/session_token
        token_file = self.project_root / ".gao-dev" / "session_token"
        token_file.write_text(token)

        # Set restrictive permissions (owner read/write only)
        token_file.chmod(0o600)

        return token

    def load_session_token(self) -> str:
        """Load existing session token if available."""
        token_file = self.project_root / ".gao-dev" / "session_token"

        if token_file.exists():
            return token_file.read_text().strip()
        else:
            return self.generate_session_token()
```

**2. Require Token in WebSocket Upgrade Header**:
```python
# gao_dev/web/websocket_manager.py
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from typing import Optional

class WebSocketManager:
    def __init__(self, session_token: str):
        self.session_token = session_token
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accept WebSocket connection only if valid session token provided.

        Token must be in:
        - Query parameter: ?token=...
        - OR Sec-WebSocket-Protocol header: gao-dev-session-{token}
        """
        # Check query parameter
        token_from_query = websocket.query_params.get("token")

        # Check Sec-WebSocket-Protocol header (for browsers that block query params)
        protocols = websocket.headers.get("sec-websocket-protocol", "").split(",")
        token_from_protocol = None
        for protocol in protocols:
            if protocol.strip().startswith("gao-dev-session-"):
                token_from_protocol = protocol.strip().replace("gao-dev-session-", "")
                break

        provided_token = token_from_query or token_from_protocol

        # Validate token
        if not provided_token or provided_token != self.session_token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(
                status_code=403,
                detail="Invalid or missing session token"
            )

        # Validate origin (prevent CSRF)
        origin = websocket.headers.get("origin")
        if origin and not self.is_origin_allowed(origin):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(
                status_code=403,
                detail=f"Origin not allowed: {origin}"
            )

        # Accept connection
        await websocket.accept()
        self.active_connections.append(websocket)

    def is_origin_allowed(self, origin: str) -> bool:
        """Validate WebSocket origin to prevent CSRF."""
        allowed_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://[::1]:3000"  # IPv6 localhost
        ]
        return origin in allowed_origins
```

**3. Frontend WebSocket Connection with Token**:
```typescript
// gao_dev_web/src/hooks/useWebSocket.ts
import { useEffect, useState } from 'react'

export function useWebSocket() {
  const [ws, setWs] = useState<WebSocket | null>(null)

  useEffect(() => {
    async function connect() {
      // Fetch session token from backend
      const response = await fetch('/api/session/token')
      const { token } = await response.json()

      // Connect with token in query parameter
      const wsUrl = `ws://localhost:3000/ws?token=${token}`

      const websocket = new WebSocket(wsUrl)

      websocket.onopen = () => {
        console.log('WebSocket connected')
        setWs(websocket)
      }

      websocket.onclose = () => {
        console.log('WebSocket disconnected')
        // Reconnect after delay
        setTimeout(connect, 1000)
      }

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    }

    connect()

    return () => {
      if (ws) {
        ws.close()
      }
    }
  }, [])

  return ws
}
```

**4. Token Endpoint (Backend)**:
```python
# gao_dev/web/api/session.py
from fastapi import APIRouter, Depends
from gao_dev.web.app import get_web_server

router = APIRouter()

@router.get("/api/session/token")
async def get_session_token(server: WebServer = Depends(get_web_server)):
    """
    Return session token for WebSocket authentication.

    This endpoint is safe because:
    1. It's only accessible from localhost (server binds to 127.0.0.1)
    2. CORS only allows http://localhost:3000
    3. Token changes on every server restart
    """
    return {"token": server.session_token}
```

**5. Security Properties**:

| Property | Implementation | Defense Against |
|----------|----------------|-----------------|
| **Random Token** | `secrets.token_urlsafe(32)` | Guessing attacks (2^256 possibilities) |
| **Token Validation** | Check on every WebSocket upgrade | Unauthorized connections |
| **Origin Validation** | Check `origin` header | CSRF from malicious websites |
| **Token Rotation** | New token on server restart | Leaked token from previous session |
| **File Permissions** | chmod 0o600 on `.gao-dev/session_token` | Token exposure to other users |

**6. Attack Scenarios Prevented**:

**Scenario 1: Malicious Website Opens WebSocket**
- Attacker website: `http://malicious.com`
- Attempt: `new WebSocket('ws://localhost:3000/ws')`
- **Blocked**: Missing token → Connection rejected (WS_1008_POLICY_VIOLATION)

**Scenario 2: Malicious Website Guesses Token**
- Attacker tries: `ws://localhost:3000/ws?token=guessed-token`
- **Blocked**: 2^256 possibilities → Computationally infeasible

**Scenario 3: CSRF Attack with Stolen Token**
- Attacker steals token from network inspection
- Attempts to connect from `http://malicious.com`
- **Blocked**: Origin validation fails → Connection rejected

**7. User Experience Impact**:

- **Transparent**: Users never see token, automatically fetched
- **No extra steps**: Works out-of-box
- **Secure by default**: Protection enabled automatically

---

### Future Remote Deployment Security

**1. Authentication (JWT)**:
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except JWTError:
        raise HTTPException(401, "Invalid token")

@router.get("/api/chat", dependencies=[Depends(verify_token)])
async def get_chat_history():
    # Protected endpoint
    pass
```

**2. HTTPS/TLS**:
```python
# production deployment with HTTPS
uvicorn.run(
    app,
    host="0.0.0.0",
    port=443,
    ssl_keyfile="/path/to/key.pem",
    ssl_certfile="/path/to/cert.pem"
)
```

**3. CSRF Protection**:
```python
from fastapi_csrf_protect import CsrfProtect

@app.post("/api/files/{path}")
async def save_file(
    path: str,
    request: SaveFileRequest,
    csrf_protect: CsrfProtect = Depends()
):
    # Validate CSRF token
    await csrf_protect.validate_csrf(request)

    # Process request
    pass
```

**4. Rate Limiting**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat")
@limiter.limit("10/minute")  # 10 requests per minute
async def send_message(request: Request, ...):
    pass
```

---

## 10. File Structure

### Project Directory Layout

```
gao-agile-dev/
├── gao_dev/
│   ├── orchestrator/                 # Existing (Epic 30, 27, 28)
│   │   ├── chat_session.py
│   │   ├── ceremony_orchestrator.py
│   │   └── ...
│   │
│   ├── core/
│   │   ├── services/
│   │   │   ├── git_integrated_state_manager.py
│   │   │   └── ...
│   │   └── ...
│   │
│   └── web/                          # NEW: Web interface backend
│       ├── __init__.py
│       ├── app.py                    # FastAPI app
│       │
│       ├── api/                      # REST endpoints
│       │   ├── __init__.py
│       │   ├── chat.py               # Chat endpoints
│       │   ├── files.py              # File endpoints
│       │   ├── kanban.py             # Kanban endpoints
│       │   ├── git.py                # Git endpoints
│       │   ├── ceremonies.py         # Ceremony endpoints
│       │   └── session.py            # Session endpoints
│       │
│       ├── websocket/                # WebSocket management
│       │   ├── __init__.py
│       │   ├── manager.py            # WebSocketManager
│       │   └── events.py             # WebEventBus
│       │
│       ├── adapters/                 # Adapter layer
│       │   ├── __init__.py
│       │   ├── brian_adapter.py      # ChatSession → WebSocket
│       │   ├── state_adapter.py      # GitIntegratedStateManager → Events
│       │   ├── ceremony_adapter.py   # CeremonyOrchestrator → Events
│       │   └── file_watcher.py       # File system → Events
│       │
│       ├── models/                   # Pydantic models
│       │   ├── __init__.py
│       │   ├── chat.py
│       │   ├── files.py
│       │   ├── kanban.py
│       │   └── events.py
│       │
│       └── services/                 # Business logic
│           ├── __init__.py
│           ├── session_manager.py    # Session lock
│           └── file_service.py
│
└── web_frontend/                     # NEW: React application
    ├── src/
    │   ├── components/
    │   │   ├── layout/
    │   │   │   ├── AppLayout.tsx
    │   │   │   ├── TopBar.tsx
    │   │   │   ├── Sidebar.tsx
    │   │   │   └── MainContent.tsx
    │   │   │
    │   │   ├── tabs/
    │   │   │   ├── ChatTab.tsx
    │   │   │   ├── ActivityStreamTab.tsx
    │   │   │   ├── KanbanBoardTab.tsx
    │   │   │   ├── FilesTab.tsx
    │   │   │   ├── GitTab.tsx
    │   │   │   └── CeremonyChannelsTab.tsx
    │   │   │
    │   │   ├── chat/
    │   │   │   ├── ChatMessage.tsx
    │   │   │   ├── ChatInput.tsx
    │   │   │   └── AgentSwitcher.tsx
    │   │   │
    │   │   ├── activity/
    │   │   │   ├── ActivityEvent.tsx
    │   │   │   ├── ActivityFilters.tsx
    │   │   │   └── ActivityTimeline.tsx
    │   │   │
    │   │   ├── kanban/
    │   │   │   ├── KanbanBoard.tsx
    │   │   │   ├── KanbanColumn.tsx
    │   │   │   └── StoryCard.tsx
    │   │   │
    │   │   ├── files/
    │   │   │   ├── FileTree.tsx
    │   │   │   ├── EditorPanel.tsx
    │   │   │   └── CommitDialog.tsx
    │   │   │
    │   │   ├── git/
    │   │   │   ├── CommitCard.tsx
    │   │   │   ├── CommitTimeline.tsx
    │   │   │   └── DiffViewer.tsx
    │   │   │
    │   │   ├── ceremony/
    │   │   │   ├── ChannelList.tsx
    │   │   │   ├── MessageStream.tsx
    │   │   │   └── CeremonyMessage.tsx
    │   │   │
    │   │   └── ui/                   # shadcn/ui components
    │   │       ├── button.tsx
    │   │       ├── input.tsx
    │   │       ├── card.tsx
    │   │       └── ...
    │   │
    │   ├── stores/                   # Zustand stores
    │   │   ├── chatStore.ts
    │   │   ├── activityStore.ts
    │   │   ├── kanbanStore.ts
    │   │   ├── filesStore.ts
    │   │   └── ceremonyStore.ts
    │   │
    │   ├── hooks/                    # Custom hooks
    │   │   ├── useWebSocket.ts
    │   │   ├── useCeremonyStatus.ts
    │   │   └── useFileTree.ts
    │   │
    │   ├── lib/                      # Utilities
    │   │   ├── api.ts                # API client
    │   │   ├── websocket.ts          # WebSocket client
    │   │   └── utils.ts
    │   │
    │   ├── App.tsx                   # Main app
    │   ├── main.tsx                  # Entry point
    │   └── index.css
    │
    ├── public/
    │   └── favicon.ico
    │
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.js
    └── .eslintrc.js
```

---

## 11. Development Workflow

### Local Development Setup

**1. Backend Setup**:
```bash
# Install Python dependencies
cd gao-agile-dev
pip install -e .

# Run FastAPI dev server
python -m gao_dev.web.app

# Backend runs on http://localhost:8000
```

**2. Frontend Setup**:
```bash
# Install Node dependencies
cd web_frontend
npm install

# Run Vite dev server
npm run dev

# Frontend runs on http://localhost:3000 (proxies to backend)
```

**3. Vite Proxy Configuration**:
```typescript
// web_frontend/vite.config.ts
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true
      },
      "/ws": {
        target: "ws://localhost:8000",
        ws: true
      }
    }
  }
})
```

**4. Hot Module Replacement (HMR)**:
- Vite provides instant HMR for frontend changes
- FastAPI auto-reloads on backend changes (use `--reload` flag)

---

### Build and Test Commands

**Backend Tests**:
```bash
# Run all tests
pytest tests/

# Run web interface tests only
pytest tests/web/

# Run with coverage
pytest --cov=gao_dev.web tests/web/
```

**Frontend Tests**:
```bash
cd web_frontend

# Run unit tests (Vitest)
npm run test

# Run E2E tests (Playwright)
npm run test:e2e

# Run accessibility tests
npm run test:a11y
```

**Build Frontend**:
```bash
cd web_frontend

# Production build
npm run build

# Output: web_frontend/dist/
# - index.html
# - assets/index-[hash].js
# - assets/index-[hash].css
```

---

### Deployment Process

**Production Build**:
```bash
# 1. Build frontend
cd web_frontend
npm run build

# 2. Move dist to gao_dev package
# (Handled by setup.py during pip install)

# 3. Install package
cd ..
pip install .

# 4. Run production server
python -m gao_dev.web.app --host 127.0.0.1 --port 3000
```

**Package Setup (setup.py)**:
```python
# setup.py
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
import subprocess
import shutil

class BuildWithFrontend(build_py):
    def run(self):
        # Build frontend
        print("Building frontend...")
        subprocess.run(["npm", "install"], cwd="web_frontend", check=True)
        subprocess.run(["npm", "run", "build"], cwd="web_frontend", check=True)

        # Copy dist to package
        shutil.copytree(
            "web_frontend/dist",
            "gao_dev/web/static",
            dirs_exist_ok=True
        )

        # Continue with normal build
        build_py.run(self)

setup(
    name="gao-dev",
    # ...
    cmdclass={
        "build_py": BuildWithFrontend
    },
    package_data={
        "gao_dev.web": ["static/**/*"]
    }
)
```

---

## 12. Deployment Architecture

### Development Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                     Developer Machine                           │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Terminal 1: Backend                                      │  │
│  │  $ python -m gao_dev.web.app                              │  │
│  │  Uvicorn running on http://localhost:8000                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Terminal 2: Frontend                                     │  │
│  │  $ npm run dev                                            │  │
│  │  Vite dev server on http://localhost:3000                │  │
│  │  (proxies API calls to :8000)                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Browser: http://localhost:3000                           │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

### Production Deployment (Localhost)

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Machine                                │
│                                                                 │
│  $ gao-dev start --web                                          │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FastAPI (Uvicorn)                                        │  │
│  │  - Serves React SPA (static files)                       │  │
│  │  - Handles API requests                                  │  │
│  │  - Manages WebSocket connections                         │  │
│  │                                                           │  │
│  │  Binds to: 127.0.0.1:3000                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Browser auto-opens to http://localhost:3000             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**CLI Command**:
```bash
# Start web interface
gao-dev start --web

# Options:
#   --port 3000          Port (default: 3000)
#   --no-browser         Don't auto-open browser
#   --debug              Enable debug mode
```

**Implementation**:
```python
# gao_dev/cli/start.py
import click
import webbrowser
import subprocess

@click.command()
@click.option("--web", is_flag=True, help="Start web interface")
@click.option("--port", default=3000, help="Port (web only)")
@click.option("--no-browser", is_flag=True, help="Don't auto-open browser")
def start(web: bool, port: int, no_browser: bool):
    """Start GAO-Dev interface (CLI or web)."""
    if web:
        # Check session lock
        lock = SessionLock(Path.cwd())
        if not lock.acquire("web"):
            click.echo("Error: CLI session active. Please exit CLI first.")
            return

        try:
            # Start FastAPI server
            subprocess.run([
                "uvicorn",
                "gao_dev.web.app:app",
                "--host", "127.0.0.1",
                "--port", str(port)
            ])
        finally:
            lock.release()

        # Auto-open browser
        if not no_browser:
            webbrowser.open(f"http://localhost:{port}")
    else:
        # Start CLI (existing Epic 30 implementation)
        from gao_dev.cli.chat import start_chat_repl
        start_chat_repl()
```

---

### Future Docker Deployment

**Docker Compose**:
```yaml
# docker-compose.yml
version: "3.8"

services:
  gao-dev-web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
    volumes:
      - ./projects:/projects       # Persist project data
      - ./config:/config            # Persist config
    restart: unless-stopped
```

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y nodejs npm

# Copy source
COPY . .

# Build frontend
RUN cd web_frontend && npm install && npm run build

# Install Python package
RUN pip install -e .

# Expose port
EXPOSE 3000

# Start server
CMD ["python", "-m", "gao_dev.web.app", "--host", "0.0.0.0", "--port", "3000"]
```

---

## 13. Testing Architecture [CRAAP-002]

**Critical Gap Addressed**: Comprehensive testing strategy for browser-based web interface

### Overview

The web interface requires a multi-layered testing approach covering unit tests, integration tests, E2E tests, and AI agent testing via Playwright MCP. This section defines testing strategy, tooling, patterns, and test data management.

### Testing Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │  <-- Playwright MCP (AI agents)
                    │   (20 tests)    │      + Human E2E tests
                    └─────────────────┘
                  ┌────────────────────────┐
                  │  Integration Tests    │  <-- Adapter layer, API contracts
                  │    (50 tests)         │      Epic 30/27/28 integration
                  └────────────────────────┘
              ┌──────────────────────────────────┐
              │      Unit Tests                  │  <-- Components, stores, utils
              │      (150 tests)                 │      Frontend + Backend
              └──────────────────────────────────┘
```

**Distribution Philosophy**:
- **Unit Tests (70%)**: Fast, isolated, deterministic
- **Integration Tests (25%)**: Adapter contracts, cross-boundary validation
- **E2E Tests (5%)**: Critical user flows, AI agent scenarios

---

### Frontend Testing

#### Unit Testing: Vitest + React Testing Library

**Tool Choice**:
- **Vitest**: Fast, Vite-native, better DX than Jest
- **React Testing Library**: User-centric testing (not implementation details)
- **MSW (Mock Service Worker)**: API mocking without test server

**Example Test Structure**:
```typescript
// gao_dev_web/src/components/ChatTab.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { ChatTab } from './ChatTab'
import { useChatStore } from '@/stores/chatStore'

// Mock Zustand store
vi.mock('@/stores/chatStore')

describe('ChatTab', () => {
  beforeEach(() => {
    // Reset store
    useChatStore.setState({ messages: [], activeAgent: 'brian' })
  })

  it('sends message to active agent', async () => {
    const user = userEvent.setup()
    const mockSendMessage = vi.fn()

    render(<ChatTab onSendMessage={mockSendMessage} />)

    // Type message
    const input = screen.getByPlaceholderText('Ask Brian...')
    await user.type(input, 'Create a todo app')

    // Send
    await user.click(screen.getByRole('button', { name: /send/i }))

    expect(mockSendMessage).toHaveBeenCalledWith({
      agent: 'brian',
      message: 'Create a todo app'
    })
  })

  it('renders messages with correct agent avatars', () => {
    useChatStore.setState({
      messages: [
        { agent: 'brian', message: 'Hello!', timestamp: '2025-01-16T10:00:00Z' },
        { agent: 'user', message: 'Hi', timestamp: '2025-01-16T10:00:05Z' }
      ]
    })

    render(<ChatTab />)

    expect(screen.getByAltText('Brian avatar')).toBeInTheDocument()
    expect(screen.getByText('Hello!')).toBeInTheDocument()
  })
})
```

**Test Coverage Targets**:
- **Components**: 80%+ coverage
- **Stores (Zustand)**: 90%+ coverage (business logic lives here)
- **Utils**: 95%+ coverage
- **API clients**: 85%+ coverage (with MSW mocks)

**MSW API Mocking**:
```typescript
// gao_dev_web/src/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.post('/api/chat', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      message_id: 'msg-123',
      agent: body.agent,
      timestamp: new Date().toISOString()
    })
  }),

  http.get('/api/kanban', () => {
    return HttpResponse.json({
      epics: [/* test data */],
      stories: [/* test data */]
    })
  })
]
```

---

#### Integration Testing: Component + Store + API

**Purpose**: Validate that components integrate correctly with Zustand stores and API clients

**Example Integration Test**:
```typescript
// gao_dev_web/src/features/kanban.integration.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { setupServer } from 'msw/node'
import { handlers } from '@/mocks/handlers'
import { KanbanBoardTab } from '@/components/KanbanBoardTab'

const server = setupServer(...handlers)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('Kanban Board Integration', () => {
  it('loads board data and allows drag-and-drop transition', async () => {
    render(<KanbanBoardTab />)

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Epic 1: Foundation')).toBeInTheDocument()
    })

    // Find story card
    const storyCard = screen.getByText('Story 1.1: Setup project')

    // Simulate drag to "In Progress" column
    const inProgressColumn = screen.getByTestId('column-in_progress')

    await userEvent.pointer([
      { target: storyCard, keys: '[MouseLeft>]' },
      { target: inProgressColumn },
      { keys: '[/MouseLeft]' }
    ])

    // Verify optimistic update
    expect(inProgressColumn).toContainElement(storyCard)

    // Wait for API call to complete
    await waitFor(() => {
      expect(server.listHandlers()).toHaveLength(1) // POST /api/kanban/transition called
    })
  })
})
```

---

### Backend Testing

#### Unit Testing: pytest

**Test Structure**:
```python
# tests/web/test_brian_adapter.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from gao_dev.web.adapters.brian_adapter import BrianWebAdapter
from gao_dev.web.services.event_bus import WebEventBus
from gao_dev.orchestrator.chat_session import ChatSession

@pytest.fixture
def event_bus():
    return WebEventBus()

@pytest.fixture
def mock_chat_session():
    session = MagicMock(spec=ChatSession)
    session.handle_input = AsyncMock(return_value="Response from Brian")
    return session

@pytest.fixture
def brian_adapter(event_bus, mock_chat_session):
    return BrianWebAdapter(
        chat_session=mock_chat_session,
        event_bus=event_bus
    )

@pytest.mark.asyncio
async def test_send_message_emits_events(brian_adapter, event_bus):
    """Test that sending message emits correct events to event bus."""
    # Subscribe to event bus
    received_events = []
    queue = event_bus.subscribe("chat.message")

    async def consume_events():
        while True:
            event = await queue.get()
            received_events.append(event)

    # Start consuming (background task)
    consume_task = asyncio.create_task(consume_events())

    # Send message
    await brian_adapter.send_message("Create a todo app")

    # Wait for events
    await asyncio.sleep(0.1)
    consume_task.cancel()

    # Verify events
    assert len(received_events) >= 1
    assert received_events[0].type == "chat.message"
    assert received_events[0].data["agent"] == "brian"
    assert "todo app" in received_events[0].data["message"].lower()
```

**Test Coverage Targets**:
- **Adapters**: 85%+ (critical integration points)
- **API endpoints**: 80%+ (FastAPI routes)
- **Event bus**: 90%+ (core infrastructure)
- **WebSocket manager**: 75%+

---

#### Integration Testing: Adapter Layer

**Purpose**: Validate adapters correctly integrate with Epic 30/27/28 services

**Critical Tests**:

**1. BrianWebAdapter → ChatSession Integration**:
```python
# tests/web/integration/test_brian_chat_integration.py
import pytest
from gao_dev.web.adapters.brian_adapter import BrianWebAdapter
from gao_dev.orchestrator.chat_session import ChatSession  # Real instance
from gao_dev.agents.brian import ConversationalBrian

@pytest.mark.integration
@pytest.mark.asyncio
async def test_brian_adapter_with_real_chat_session():
    """Integration test with real ChatSession (Epic 30)."""
    # Create real ChatSession instance
    brian = ConversationalBrian()
    chat_session = ChatSession(conversational_brian=brian)

    # Create adapter
    event_bus = WebEventBus()
    adapter = BrianWebAdapter(chat_session=chat_session, event_bus=event_bus)

    # Send message
    await adapter.send_message("What workflows are available?")

    # Verify ChatSession was called (check internal state)
    assert chat_session.context.conversation_history
    assert chat_session.context.current_agent == "brian"
```

**2. StateChangeAdapter → GitIntegratedStateManager Integration**:
```python
# tests/web/integration/test_state_change_integration.py
import pytest
from gao_dev.web.adapters.state_change_adapter import StateChangeAdapter
from gao_dev.core.state_manager import GitIntegratedStateManager

@pytest.mark.integration
@pytest.mark.asyncio
async def test_state_transition_emits_event(tmp_path):
    """Verify state transitions emit correct events."""
    # Create real state manager with temp git repo
    state_manager = GitIntegratedStateManager(project_root=tmp_path)

    # Create adapter
    event_bus = WebEventBus()
    adapter = StateChangeAdapter(state_manager=state_manager, event_bus=event_bus)

    # Subscribe to events
    queue = event_bus.subscribe("state.changed")

    # Transition story
    await state_manager.transition_story(epic_num=1, story_num=1, new_status="in_progress")

    # Verify event emitted
    event = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert event.type == "state.changed"
    assert event.data["epic_num"] == 1
    assert event.data["story_num"] == 1
    assert event.data["new_status"] == "in_progress"
```

**3. FileSystemWatcher → Event Loop Prevention** [CRAAP-004]:
```python
# tests/web/integration/test_file_system_watcher.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_file_watcher_ignores_self_triggered_events(tmp_path):
    """Verify FileSystemWatcher doesn't create event loops."""
    event_bus = WebEventBus()
    watcher = FileSystemWatcher(project_root=tmp_path, event_bus=event_bus)

    # Subscribe to file.created events
    queue = event_bus.subscribe("file.created")

    # Agent creates file (should have source="agent")
    await state_manager.create_story(
        epic_num=1,
        story_num=1,
        title="Test",
        file_path=tmp_path / "docs/story.md",
        content="# Story",
        source="agent"  # <-- Mark as agent-triggered
    )

    # Watcher should emit event with source preserved
    event = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert event.data["source"] == "agent"

    # Adapter should filter events with source="self" to prevent loops
    # (Tested separately in adapter tests)
```

---

### E2E Testing

#### Human E2E Tests: Playwright

**Tool**: Playwright (official Playwright, not MCP)

**Purpose**: Test critical user flows from browser perspective

**Example E2E Test**:
```typescript
// e2e/tests/chat-workflow.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Chat Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000')
    // Wait for app to load
    await expect(page.locator('[data-testid="app-loaded"]')).toBeVisible()
  })

  test('user can send message to Brian and receive response', async ({ page }) => {
    // Navigate to Chat tab
    await page.click('[data-testid="tab-chat"]')

    // Type message
    await page.fill('[data-testid="chat-input"]', 'List available workflows')

    // Send
    await page.click('[data-testid="chat-send"]')

    // Wait for Brian's response
    await expect(page.locator('[data-testid="message-brian"]').last()).toBeVisible({ timeout: 10000 })

    // Verify response contains workflow information
    const response = await page.locator('[data-testid="message-brian"]').last().textContent()
    expect(response).toContain('workflow')
  })

  test('activity stream updates in real-time', async ({ page }) => {
    // Navigate to Activity Stream tab
    await page.click('[data-testid="tab-activity"]')

    // Initial event count
    const initialCount = await page.locator('[data-testid="activity-event"]').count()

    // Trigger workflow (via Brian)
    await page.click('[data-testid="tab-chat"]')
    await page.fill('[data-testid="chat-input"]', 'Create a simple PRD')
    await page.click('[data-testid="chat-send"]')

    // Switch back to Activity Stream
    await page.click('[data-testid="tab-activity"]')

    // Wait for new events
    await expect(page.locator('[data-testid="activity-event"]')).toHaveCount(initialCount + 1, { timeout: 5000 })
  })
})
```

**E2E Test Coverage**:
- Chat: Send message, switch agents, view history
- Activity Stream: Real-time updates, filtering, time windows
- Kanban: Drag-and-drop, load board, filter
- Files: View tree, open file, edit (if write mode)
- Git: View commits, timeline
- Ceremony Channels: Activate tab, view messages

---

#### AI Agent E2E Tests: Playwright MCP [CRITICAL]

**Purpose**: Enable AI agents (via Playwright MCP) to test the web interface autonomously

**Philosophy**: This is the **"AI testing AI"** vision - AI agents build the product, AI agents test the product

**Implementation Strategy**:

**1. Test Mode Environment Variable**:
```python
# gao_dev/web/app.py
import os

TEST_MODE = os.getenv("GAO_DEV_TEST_MODE") == "true"

if TEST_MODE:
    # Disable animations for faster tests
    app.state.disable_animations = True

    # Add comprehensive data-testid to all elements
    app.state.test_id_enabled = True

    # Use deterministic IDs (not UUIDs)
    app.state.deterministic_ids = True
```

**2. Comprehensive data-testid Attributes**:
```typescript
// All interactive elements must have data-testid
<Button data-testid="chat-send" onClick={handleSend}>
  Send
</Button>

<Input
  data-testid="chat-input"
  placeholder="Ask Brian..."
/>

<Card data-testid={`story-card-${epic}-${story}`}>
  {/* Story content */}
</Card>
```

**3. Playwright MCP Test Scenario**:
```yaml
# tests/e2e/mcp/todo-app-creation.yaml
name: "Todo App Creation via Web Interface"
description: "AI agent uses web interface to create todo app from scratch"

setup:
  - start_server: "gao-dev start --web"
  - wait_for_url: "http://localhost:3000"

steps:
  - action: "navigate"
    url: "http://localhost:3000"

  - action: "click"
    selector: "[data-testid='tab-chat']"

  - action: "type"
    selector: "[data-testid='chat-input']"
    text: "Create a simple todo app with authentication"

  - action: "click"
    selector: "[data-testid='chat-send']"

  - action: "wait_for"
    selector: "[data-testid='message-brian']"
    condition: "contains text 'I'll help you create'"

  - action: "verify"
    condition: "activity stream shows workflow.started event"

  - action: "wait_for"
    condition: "kanban board shows new epic"
    timeout: 60000

  - action: "verify"
    selector: "[data-testid='epic-card-1']"
    condition: "visible"

assertions:
  - epic_created: true
  - stories_created: ">= 5"
  - files_created: ["docs/PRD.md", "docs/ARCHITECTURE.md"]
```

**4. Playwright MCP Integration**:
```python
# tests/e2e/mcp/runner.py
from playwright.sync_api import sync_playwright
import yaml

def run_mcp_test(test_file: str):
    """Run Playwright MCP test scenario."""
    with open(test_file) as f:
        scenario = yaml.safe_load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Execute steps
        for step in scenario["steps"]:
            if step["action"] == "navigate":
                page.goto(step["url"])
            elif step["action"] == "click":
                page.click(step["selector"])
            elif step["action"] == "type":
                page.fill(step["selector"], step["text"])
            # ... handle all actions

        # Verify assertions
        for assertion in scenario["assertions"]:
            # Validate expected outcomes
            pass

        browser.close()
```

**MCP Test Coverage**:
- Create project from prompt
- Navigate interface autonomously
- Validate generated artifacts
- Detect errors and report clearly

---

### Test Data Management

#### Test Project Generation

**Purpose**: Create realistic test projects for integration/E2E tests

**Test Data Factory**:
```python
# tests/fixtures/test_project_factory.py
from pathlib import Path
import shutil
from gao_dev.core.state_manager import GitIntegratedStateManager

class TestProjectFactory:
    """Generate test projects with various configurations."""

    @staticmethod
    def create_simple_project(tmp_path: Path) -> Path:
        """Create minimal valid GAO-Dev project."""
        project_root = tmp_path / "simple-project"
        project_root.mkdir()

        # Initialize .gao-dev
        gao_dev_dir = project_root / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create state manager
        state_manager = GitIntegratedStateManager(project_root=project_root)

        # Create 1 epic, 3 stories
        state_manager.create_epic(epic_num=1, title="Foundation")
        state_manager.create_story(epic_num=1, story_num=1, title="Story 1")
        state_manager.create_story(epic_num=1, story_num=2, title="Story 2")

        return project_root

    @staticmethod
    def create_large_project(tmp_path: Path) -> Path:
        """Create large project (10 epics, 100 stories) for performance testing."""
        project_root = tmp_path / "large-project"
        project_root.mkdir()

        state_manager = GitIntegratedStateManager(project_root=project_root)

        for epic_num in range(1, 11):
            state_manager.create_epic(epic_num=epic_num, title=f"Epic {epic_num}")

            for story_num in range(1, 11):
                state_manager.create_story(
                    epic_num=epic_num,
                    story_num=story_num,
                    title=f"Story {epic_num}.{story_num}"
                )

        return project_root
```

**Usage in Tests**:
```python
@pytest.fixture
def simple_project(tmp_path):
    return TestProjectFactory.create_simple_project(tmp_path)

def test_kanban_loads_large_project(large_project):
    """Verify Kanban can handle 100 stories."""
    # Test with large_project fixture
    pass
```

---

### CI/CD Integration

#### GitHub Actions Workflow

```yaml
# .github/workflows/web-interface-tests.yml
name: Web Interface Tests

on: [push, pull_request]

jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        working-directory: gao_dev_web
        run: npm ci

      - name: Run unit tests
        run: npm test -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./gao_dev_web/coverage/coverage-final.json

  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -e ".[test]"

      - name: Run backend tests
        run: pytest tests/web --cov=gao_dev.web

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - uses: actions/setup-python@v4

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Start backend
        run: python -m gao_dev.web.app &

      - name: Wait for server
        run: npx wait-on http://localhost:8000

      - name: Run E2E tests
        run: npx playwright test

  mcp-e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Playwright MCP tests
        env:
          GAO_DEV_TEST_MODE: "true"
        run: python tests/e2e/mcp/runner.py tests/e2e/mcp/*.yaml
```

---

### Test Execution Commands

```bash
# Frontend unit tests
cd gao_dev_web
npm test                         # Run once
npm test -- --watch              # Watch mode
npm test -- --coverage           # With coverage

# Backend unit tests
pytest tests/web                 # All web tests
pytest tests/web -k adapter      # Only adapter tests
pytest tests/web --cov           # With coverage

# Integration tests
pytest tests/web/integration --run-integration

# E2E tests
npx playwright test              # All E2E tests
npx playwright test --ui         # Interactive mode
npx playwright test --debug      # Debug mode

# Playwright MCP tests
GAO_DEV_TEST_MODE=true python tests/e2e/mcp/runner.py tests/e2e/mcp/todo-app.yaml
```

---

### Test Quality Metrics

**Minimum Acceptance Criteria**:
- Frontend unit test coverage: **80%+**
- Backend unit test coverage: **80%+**
- Integration test coverage: **75%+**
- E2E tests: **All critical flows covered**
- MCP tests: **At least 3 end-to-end scenarios**

**Continuous Monitoring**:
- Coverage reports in CI/CD
- Fail build if coverage drops below threshold
- Playwright test videos on failure

---

## 14. Error Handling Architecture [CRAAP-007]

**Critical Gap Addressed**: Comprehensive error handling strategy and recovery flows

### Error Handling Philosophy

1. **Fail gracefully**: Never crash the UI, always show actionable error messages
2. **Preserve user work**: Autosave, draft persistence, conflict resolution
3. **Clear recovery paths**: Every error has a "What to do next" action
4. **Observable errors**: All errors logged for debugging

### Error Severity Taxonomy

| Severity | Description | UI Pattern | Example |
|----------|-------------|------------|---------|
| **Info** | Informational, no action needed | Toast (blue, auto-dismiss 3s) | "Project loaded successfully" |
| **Warning** | Degraded functionality, can continue | Toast (yellow, auto-dismiss 5s) | "WebSocket reconnecting..." |
| **Error** | Operation failed, user action needed | Toast (red, manual dismiss) + Retry button | "Failed to save file. Retry?" |
| **Critical** | System-level failure, requires intervention | Modal (blocks UI) | "Session lock held by another process" |

### React Error Boundaries

**Top-Level Error Boundary**:
```typescript
// gao_dev_web/src/components/ErrorBoundary.tsx
import React from 'react'
import { AlertTriangle } from 'lucide-react'

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log to error reporting service
    console.error('React Error Boundary caught:', error, errorInfo)

    // Send to backend logging endpoint
    fetch('/api/errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack
      })
    })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen bg-gray-900">
          <div className="text-center space-y-4">
            <AlertTriangle className="w-16 h-16 text-red-500 mx-auto" />
            <h1 className="text-2xl font-bold text-white">Something went wrong</h1>
            <p className="text-gray-400 max-w-md">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              className="btn-primary"
              onClick={() => window.location.reload()}
            >
              Reload Page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
```

**Error Boundary Placement**:
- **App-level**: Wraps entire application (catastrophic failures)
- **Tab-level**: Wraps each tab component (isolate tab failures)
- **Feature-level**: Wraps complex features (Monaco editor, Kanban board)

```typescript
// gao_dev_web/src/App.tsx
function App() {
  return (
    <ErrorBoundary>
      <Tabs>
        <ErrorBoundary key="chat">
          <ChatTab />
        </ErrorBoundary>

        <ErrorBoundary key="kanban">
          <KanbanBoardTab />
        </ErrorBoundary>

        {/* ... other tabs */}
      </Tabs>
    </ErrorBoundary>
  )
}
```

### Toast vs Modal Decision Tree

```
Error Occurred
    │
    ├─ Can user continue working? ─ YES ─> Toast (dismissible)
    │                                       │
    │                                       ├─ Recoverable? ─ YES ─> Retry button
    │                                       └─ Recoverable? ─ NO ──> Info message
    │
    └─ Can user continue working? ─ NO ──> Modal (blocks UI)
                                            │
                                            ├─ Fixable? ─ YES ─> Action buttons
                                            └─ Fixable? ─ NO ──> Contact support
```

**Toast Notification Component**:
```typescript
// gao_dev_web/src/components/Toast.tsx
import { toast } from 'sonner'  // Using sonner for toast notifications

export const showError = (message: string, options?: { retry?: () => void }) => {
  toast.error(message, {
    duration: Infinity,  // Manual dismiss for errors
    action: options?.retry ? {
      label: 'Retry',
      onClick: options.retry
    } : undefined
  })
}

export const showWarning = (message: string) => {
  toast.warning(message, {
    duration: 5000  // Auto-dismiss after 5s
  })
}

export const showInfo = (message: string) => {
  toast.info(message, {
    duration: 3000  // Auto-dismiss after 3s
  })
}
```

**Modal Error Component**:
```typescript
// gao_dev_web/src/components/ErrorModal.tsx
interface ErrorModalProps {
  title: string
  message: string
  actions: Array<{ label: string; onClick: () => void; variant?: 'primary' | 'secondary' }>
}

export function ErrorModal({ title, message, actions }: ErrorModalProps) {
  return (
    <Dialog open>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="text-red-500" />
            {title}
          </DialogTitle>
        </DialogHeader>

        <p className="text-gray-300">{message}</p>

        <DialogFooter>
          {actions.map((action, index) => (
            <Button
              key={index}
              variant={action.variant || 'secondary'}
              onClick={action.onClick}
            >
              {action.label}
            </Button>
          ))}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

### Retry Logic with Exponential Backoff

**API Client Retry Wrapper**:
```typescript
// gao_dev_web/src/lib/api.ts
interface RetryConfig {
  maxRetries: number
  baseDelay: number  // milliseconds
  maxDelay: number
  retryableStatuses: number[]
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,  // 1 second
  maxDelay: 10000,  // 10 seconds
  retryableStatuses: [408, 429, 500, 502, 503, 504]
}

async function fetchWithRetry<T>(
  url: string,
  options?: RequestInit,
  retryConfig: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<T> {
  let lastError: Error

  for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
    try {
      const response = await fetch(url, options)

      // Success
      if (response.ok) {
        return await response.json()
      }

      // Check if retryable
      if (!retryConfig.retryableStatuses.includes(response.status)) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      // Retryable error
      lastError = new Error(`HTTP ${response.status}: ${response.statusText}`)

    } catch (error) {
      lastError = error as Error

      // Network error - retryable
      if (attempt < retryConfig.maxRetries) {
        // Exponential backoff: 1s, 2s, 4s, 8s (capped at maxDelay)
        const delay = Math.min(
          retryConfig.baseDelay * Math.pow(2, attempt),
          retryConfig.maxDelay
        )

        await new Promise(resolve => setTimeout(resolve, delay))
        continue
      }
    }
  }

  throw lastError!
}
```

**Usage in API Client**:
```typescript
export async function transitionStory(epicNum: number, storyNum: number, status: string) {
  try {
    return await fetchWithRetry('/api/kanban/transition', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ epic: epicNum, story: storyNum, status })
    })
  } catch (error) {
    showError(`Failed to transition story ${epicNum}.${storyNum}`, {
      retry: () => transitionStory(epicNum, storyNum, status)
    })
    throw error
  }
}
```

### Error Recovery Flows

#### Chat Message Send Failure

```typescript
// gao_dev_web/src/hooks/useChat.ts
async function sendMessage(message: string) {
  const tempId = `temp-${Date.now()}`

  // Optimistic update
  addMessage({ id: tempId, agent: 'user', message, status: 'sending' })

  try {
    const response = await api.sendChatMessage({ agent: activeAgent, message })

    // Update with real ID
    updateMessage(tempId, { id: response.message_id, status: 'sent' })

  } catch (error) {
    // Mark as failed
    updateMessage(tempId, { status: 'failed' })

    // Show retry option
    showError('Failed to send message', {
      retry: () => sendMessage(message)
    })
  }
}
```

#### File Save Failure

```typescript
// gao_dev_web/src/hooks/useFileSave.ts
async function saveFile(path: string, content: string, commitMessage: string) {
  // Autosave to localStorage as draft
  localStorage.setItem(`draft:${path}`, JSON.stringify({ content, timestamp: Date.now() }))

  try {
    await api.saveFile(path, content, commitMessage)

    // Clear draft on success
    localStorage.removeItem(`draft:${path}`)

    showInfo('File saved successfully')

  } catch (error) {
    if (error.status === 409) {
      // Conflict - show diff UI
      showConflictModal(path, content, error.data.serverContent)
    } else {
      // Other error - keep draft, show retry
      showError('Failed to save file. Your changes are saved as draft.', {
        retry: () => saveFile(path, content, commitMessage)
      })
    }
  }
}
```

#### Kanban Drag-and-Drop Failure

```typescript
// gao_dev_web/src/hooks/useKanban.ts
async function transitionStory(epicNum: number, storyNum: number, newStatus: string) {
  const oldStatus = getStoryStatus(epicNum, storyNum)

  // Optimistic update
  updateStoryStatus(epicNum, storyNum, newStatus, { loading: true })

  try {
    await api.transitionStory(epicNum, storyNum, newStatus)

    // Mark as committed
    updateStoryStatus(epicNum, storyNum, newStatus, { loading: false })

    showInfo(`Story ${epicNum}.${storyNum} moved to ${newStatus}`)

  } catch (error) {
    // Rollback optimistic update
    updateStoryStatus(epicNum, storyNum, oldStatus, { loading: false })

    showError(`Failed to transition story ${epicNum}.${storyNum}`, {
      retry: () => transitionStory(epicNum, storyNum, newStatus)
    })
  }
}
```

#### WebSocket Reconnection Failure

```typescript
// gao_dev_web/src/hooks/useWebSocket.ts
const MAX_RECONNECT_ATTEMPTS = 10
let reconnectAttempts = 0

function handleWebSocketClose() {
  if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)  // Max 30s

    showWarning(`Connection lost. Reconnecting in ${delay/1000}s...`)

    setTimeout(() => {
      reconnectAttempts++
      connect()
    }, delay)

  } else {
    // Give up after 10 attempts
    showCriticalError(
      'Unable to reconnect',
      'Please refresh the page or check your network connection.',
      [
        { label: 'Refresh Page', onClick: () => window.location.reload(), variant: 'primary' },
        { label: 'Offline Mode', onClick: () => enterOfflineMode() }
      ]
    )
  }
}
```

### Error Logging

**Frontend Logging**:
```typescript
// gao_dev_web/src/lib/logger.ts
import { toast } from 'sonner'

interface ErrorLog {
  message: string
  stack?: string
  context?: Record<string, any>
  timestamp: string
}

async function logError(error: Error, context?: Record<string, any>) {
  const errorLog: ErrorLog = {
    message: error.message,
    stack: error.stack,
    context,
    timestamp: new Date().toISOString()
  }

  // Log to console
  console.error('[ERROR]', errorLog)

  // Send to backend
  try {
    await fetch('/api/errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(errorLog)
    })
  } catch (loggingError) {
    // If logging fails, at least we have console
    console.error('[ERROR LOGGING FAILED]', loggingError)
  }
}
```

**Backend Logging Endpoint**:
```python
# gao_dev/web/api/errors.py
from fastapi import APIRouter, Request
from pydantic import BaseModel
import structlog

router = APIRouter()
logger = structlog.get_logger()

class FrontendError(BaseModel):
    message: str
    stack: str | None
    context: dict | None
    timestamp: str

@router.post("/api/errors")
async def log_frontend_error(error: FrontendError, request: Request):
    """Log frontend errors to backend logger."""
    logger.error(
        "frontend_error",
        message=error.message,
        stack=error.stack,
        context=error.context,
        timestamp=error.timestamp,
        user_agent=request.headers.get("user-agent")
    )

    return {"status": "logged"}
```

---

## 15. Session Management [CRAAP-011]

**Purpose**: Preserve user session across browser refreshes and crashes

### Session Persistence Schema

**Session State Storage**: `.gao-dev/last_session_history.json`

```typescript
interface SessionState {
  version: string              // Schema version (for future migrations)
  timestamp: string            // When session was saved
  activeTab: string            // "chat" | "activity" | "kanban" | "files" | "git" | "ceremony"
  scrollPositions: {
    [tabId: string]: number   // Scroll position per tab
  }
  openFiles: Array<{
    path: string
    cursorPosition: { line: number; column: number }
    scrollPosition: number
  }>
  chatHistory: Array<{
    agent: string
    message: string
    timestamp: string
  }>
  activityFilters: {
    timeWindow: number          // Seconds
    eventTypes: string[]        // Filtered event types
  }
  kanbanFilters: {
    feature?: string
    status?: string
  }
}
```

**Example Session File**:
```json
{
  "version": "1.0",
  "timestamp": "2025-01-16T14:30:00Z",
  "activeTab": "files",
  "scrollPositions": {
    "chat": 0,
    "activity": 1200,
    "kanban": 0,
    "files": 500
  },
  "openFiles": [
    {
      "path": "docs/PRD.md",
      "cursorPosition": { "line": 42, "column": 15 },
      "scrollPosition": 320
    },
    {
      "path": "src/main.py",
      "cursorPosition": { "line": 10, "column": 0 },
      "scrollPosition": 0
    }
  ],
  "chatHistory": [
    {
      "agent": "brian",
      "message": "I'll help you create a todo app",
      "timestamp": "2025-01-16T14:25:00Z"
    },
    {
      "agent": "user",
      "message": "Create a todo app with auth",
      "timestamp": "2025-01-16T14:24:00Z"
    }
  ],
  "activityFilters": {
    "timeWindow": 3600,
    "eventTypes": ["file.created", "git.commit", "workflow.started"]
  },
  "kanbanFilters": {
    "feature": "mvp",
    "status": "in_progress"
  }
}
```

### Session Persistence Triggers

**Auto-Save Triggers** (writes to `.gao-dev/last_session_history.json`):
- Tab switch (debounced 2s)
- File open/close in Monaco editor
- Chat message sent
- Filter changed (debounced 5s)
- Before page unload (browser `beforeunload` event)

**Implementation**:
```typescript
// gao_dev_web/src/hooks/useSessionPersistence.ts
import { useEffect } from 'react'
import { debounce } from 'lodash'

export function useSessionPersistence() {
  const saveSession = debounce(() => {
    const sessionState: SessionState = {
      version: '1.0',
      timestamp: new Date().toISOString(),
      activeTab: useAppStore.getState().activeTab,
      scrollPositions: useAppStore.getState().scrollPositions,
      openFiles: useFileStore.getState().openFiles.map(file => ({
        path: file.path,
        cursorPosition: file.editor?.getPosition() || { line: 0, column: 0 },
        scrollPosition: file.editor?.getScrollTop() || 0
      })),
      chatHistory: useChatStore.getState().messages.slice(-50),  // Last 50 messages
      activityFilters: useActivityStore.getState().filters,
      kanbanFilters: useKanbanStore.getState().filters
    }

    // Save to backend
    fetch('/api/session/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sessionState)
    })
  }, 2000)  // Debounce 2 seconds

  useEffect(() => {
    // Listen for state changes
    const unsubscribe = useAppStore.subscribe(saveSession)

    // Save before page unload
    window.addEventListener('beforeunload', saveSession.flush)

    return () => {
      unsubscribe()
      window.removeEventListener('beforeunload', saveSession.flush)
    }
  }, [])
}
```

### Session Recovery

**Recovery Trigger**: Automatic on page load (no prompt)

**Rationale**: Users expect their session to persist, similar to VS Code behavior

**Recovery Flow**:
1. Page loads → Check for `.gao-dev/last_session_history.json`
2. If exists and < 24 hours old → Restore automatically
3. If exists and > 24 hours old → Prompt "Restore previous session?"
4. If not exists → Fresh start

**Implementation**:
```typescript
// gao_dev_web/src/App.tsx
function App() {
  const [isRestoring, setIsRestoring] = useState(true)

  useEffect(() => {
    async function restoreSession() {
      try {
        const response = await fetch('/api/session/restore')
        const sessionState: SessionState = await response.json()

        if (!sessionState) {
          // No session to restore
          setIsRestoring(false)
          return
        }

        // Check age
        const age = Date.now() - new Date(sessionState.timestamp).getTime()
        const MAX_AGE = 24 * 60 * 60 * 1000  // 24 hours

        if (age > MAX_AGE) {
          // Prompt user
          const shouldRestore = await showConfirmDialog(
            'Restore Previous Session?',
            `Your last session was ${Math.floor(age / (60 * 60 * 1000))} hours ago. Restore it?`
          )

          if (!shouldRestore) {
            setIsRestoring(false)
            return
          }
        }

        // Restore state
        useAppStore.setState({ activeTab: sessionState.activeTab })
        useAppStore.setState({ scrollPositions: sessionState.scrollPositions })
        useChatStore.setState({ messages: sessionState.chatHistory })
        useActivityStore.setState({ filters: sessionState.activityFilters })
        useKanbanStore.setState({ filters: sessionState.kanbanFilters })

        // Restore open files
        for (const fileState of sessionState.openFiles) {
          await openFile(fileState.path, {
            cursorPosition: fileState.cursorPosition,
            scrollPosition: fileState.scrollPosition
          })
        }

        showInfo('Session restored')

      } catch (error) {
        console.error('Failed to restore session:', error)
      } finally {
        setIsRestoring(false)
      }
    }

    restoreSession()
  }, [])

  if (isRestoring) {
    return <LoadingSpinner message="Restoring session..." />
  }

  return (
    <ErrorBoundary>
      {/* App content */}
    </ErrorBoundary>
  )
}
```

---

## 16. Open Issues and Future Work

### V1.0 Open Questions

**1. Reasoning Toggle UX**:
- **Question**: Should reasoning (Claude's thinking) be shown by default or hidden?
- **Decision Needed**: User testing to determine preference
- **Recommendation**: Default hidden, toggle available

**2. Notification Strategy**:
- **Question**: Desktop notifications for long-running workflows?
- **Decision Needed**: Browser notification permission flow
- **Recommendation**: Opt-in via settings

**3. Theme Support**:
- **Question**: Dark mode only or light + dark?
- **Decision Needed**: Design system consistency
- **Recommendation**: Dark mode MVP, light mode V1.1

**4. Layout Customization**:
- **Question**: Resizable panels or fixed layout?
- **Decision Needed**: Complexity vs. flexibility trade-off
- **Recommendation**: Fixed MVP, resizable V1.1

**5. Git Operations Scope**:
- **Question**: Should users branch/merge in UI or read-only?
- **Decision Needed**: Risk of git conflicts
- **Recommendation**: Read-only MVP, branching V1.1

---

### V1.1 Future Enhancements

**Performance**:
- Redis pub/sub for multi-project support
- Service worker for offline support
- IndexedDB for local data caching

**Features**:
- Multi-project workspace
- Project comparison view
- Search across all artifacts
- Export workflows as PDFs
- Agent performance analytics

**Testing**:
- Playwright MCP integration (AI agent testing)
- Visual regression testing
- Load testing (1,000+ concurrent events)

**Security**:
- OAuth2 authentication
- Role-based access control (RBAC)
- Audit logging
- Secret management (vault integration)

---

## Appendix A: AI Testability Patterns

### Semantic HTML

```tsx
// Good: Semantic HTML
<nav aria-label="Main navigation">
  <button data-testid="chat-tab" aria-label="Chat with Brian">
    Chat
  </button>
</nav>

// Bad: Non-semantic div soup
<div onClick={...}>
  <div>Chat</div>
</div>
```

### data-testid Naming Convention

```
Format: {component}-{element}-{variant?}

Examples:
- chat-input
- chat-message-user
- chat-message-brian
- activity-event-workflow
- kanban-card-story-1-1
- file-tree-node
- ceremony-channel-planning
```

### State Indicators

```tsx
// Good: Clear state indicators
<div data-state={isLoading ? "loading" : "idle"}>
  {isLoading ? <Spinner /> : <Content />}
</div>

// Playwright can detect
await page.locator('[data-state="loading"]').waitFor()
```

---

## Appendix B: Event Catalog

See [Event Types Reference](#event-types-reference) in Section 6.

---

## Appendix C: CRAAP Review Resolution Summary

This architecture has been updated to address all critical and moderate issues identified in the CRAAP (Critique, Risk, Analyse, Alignment, Perspective) review conducted on 2025-01-16.

### Critical Issues Addressed (7/7) ✅

| Issue | Description | Resolution Location | Status |
|-------|-------------|---------------------|--------|
| **CRAAP-001** | WebSocket Authentication Missing | Section 9: Security Architecture → WebSocket Security | ✅ RESOLVED |
| **CRAAP-002** | No Test Architecture Defined | Section 13: Testing Architecture | ✅ RESOLVED |
| **CRAAP-003** | Chat History Memory Leak | Section 4: Frontend Architecture → chatStore (pagination, indexedDB archival) | ✅ RESOLVED |
| **CRAAP-004** | Circular Dependency Risk | Section 6: Event-Driven Architecture → Loop Prevention Flow | ✅ RESOLVED |
| **CRAAP-005** | File Locking Not Defined | Section 7: Integration Architecture → File Locking and Conflict Resolution | ✅ RESOLVED |
| **CRAAP-006** | Mutual Exclusion Decision Unclear | Section 1: System Architecture → Mutual Exclusion Decision | ✅ FINAL DECISION |
| **CRAAP-007** | No Error Handling Strategy | Section 14: Error Handling Architecture | ✅ RESOLVED |

### Moderate Issues Addressed (8/15) ✅

| Issue | Description | Resolution Location | Status |
|-------|-------------|---------------------|--------|
| **CRAAP-008** | Chat History Management Undefined | Section 4: Frontend Architecture → chatStore (per-agent partitioning) | ✅ RESOLVED |
| **CRAAP-009** | No Sequence Numbers on Events | Section 6: Event-Driven Architecture → Event Schema | ✅ RESOLVED |
| **CRAAP-010** | No Page Visibility API Handling | Section 14: Error Handling → WebSocket Reconnection Failure | ✅ PARTIALLY ADDRESSED |
| **CRAAP-011** | Session Recovery UX Undefined | Section 15: Session Management | ✅ RESOLVED |
| **CRAAP-012** | No Kanban Loading States | Section 14: Error Handling → Kanban Drag-and-Drop Failure | ✅ PARTIALLY ADDRESSED |
| **CRAAP-013** | Event Bus Buffer Cleanup | Section 5: Backend Architecture → Event Bus (cleanup logic) | ⚠️ NOTED (to be implemented) |
| **CRAAP-014** | ChatSession API Contract Undefined | Section 7: Integration Architecture → ChatSession API Contract | ✅ RESOLVED |
| **CRAAP-015** | No Migration Plan | Section 16: Open Issues → V1.0 Open Questions | ⚠️ DEFERRED TO PRD |

### Architectural Decisions FINALIZED (3/3) ✅

All three key architectural decisions have been approved by Product Owner and Technical Lead.

| Decision | Options Considered | FINAL DECISION | Status |
|----------|-------------------|----------------|--------|
| **Mutual Exclusion** | A) Strict exclusion, B) Read-only web while CLI active, C) Full bidirectional | **Option B** (read-only web) | ✅ APPROVED |
| **Event Bus Persistence** | A) asyncio.Queue (in-memory), B) SQLite event log | **Option A** (asyncio.Queue for MVP) | ✅ APPROVED |
| **Dark Mode in MVP** | A) Dark only (defer light), B) Both light and dark modes | **Option B** (both modes, respect system preference) | ✅ APPROVED |

**Implementation Notes**:
- Mutual Exclusion: See Section 1.5 for read-only mode architecture, middleware enforcement, and UI indicators
- Event Bus: asyncio.Queue (Section 5) with buffer management; SQLite logging deferred to V1.1
- Dark Mode: Full implementation (Section 4) using Tailwind + CSS media queries for system preference respect

### New Sections Added

1. **Section 13: Testing Architecture** - Comprehensive test strategy (unit, integration, E2E, Playwright MCP)
2. **Section 14: Error Handling Architecture** - Error taxonomy, boundaries, recovery flows, retry logic
3. **Section 15: Session Management** - Session persistence, recovery UX, state schema
4. **Section 1.5: Mutual Exclusion Decision** - Options analysis with trade-offs

### Enhanced Sections

1. **Section 6: Event-Driven Architecture** - Added `source` field, sequence numbers, correlation IDs, loop prevention
2. **Section 7: Integration Architecture** - Added file locking, conflict resolution, ChatSession API contract
3. **Section 9: Security Architecture** - Added WebSocket authentication with session tokens
4. **Section 4: Frontend Architecture** - Added chat history pagination, per-agent partitioning

### Outstanding Items (For PRD/Implementation)

| Item | Category | Priority | Owner |
|------|----------|----------|-------|
| Event Bus Buffer Cleanup | Implementation | Medium | Backend Developer |
| Page Visibility API Full Spec | Implementation | Medium | Frontend Developer |
| Kanban Loading States Full UI | Implementation | Medium | Frontend Developer |
| Migration Plan Details | PRD | High | John (PM) |
| Browser Test Matrix | Test Strategy | Low | Murat (Test Architect) |

### Architecture Health Assessment

**BEFORE CRAAP Review**: B+ (Good, with important gaps)
**AFTER Updates**: **A-** (Excellent, with minor TODOs)

**Key Improvements**:
- ✅ All critical security issues addressed (WebSocket auth, file locking)
- ✅ Comprehensive test strategy defined (fixes major gap)
- ✅ Error handling and recovery flows specified
- ✅ Event schema enhanced with loop prevention
- ✅ **Architectural decisions FINALIZED** (mutual exclusion, event bus, dark mode)

**Remaining Gaps** (Low Priority, defer to implementation):
- Event bus buffer cleanup logic (implementation detail, noted in Section 5)
- Page Visibility API full specification (nice-to-have for V1.1)
- Migration plan (belongs in PRD, not architecture)

### Recommendation for Next Steps

All architectural decisions are now FINAL. Ready to proceed directly to PRD phase.

1. **Architecture Sign-Off** ✅ COMPLETE
   - Technical Lead approval: Event Bus (asyncio.Queue)
   - Product Owner approval: Mutual Exclusion (Option B), Dark Mode (Option B)

2. **Proceed to PRD** (3-5 days):
   - John (Product Manager) creates comprehensive PRD.md
   - PRD should include migration plan [CRAAP-015]
   - PRD should address phased delivery (MVP vs V1.1)
   - Reference Appendix C (Architectural Decisions) for tech decisions

3. **Architecture Review** (1 day):
   - Quick review with technical team (Epic 30/27/28 owners)
   - Validate integration assumptions with existing services
   - Sign-off before story breakdown

4. **Story Breakdown** (5 days):
   - Bob (Scrum Master) creates stories from PRD + Architecture
   - Ensure test requirements in acceptance criteria (Section 13)
   - Ensure error handling in acceptance criteria (Section 14)
   - Reference read-only mode constraints in kanban/chat stories

**Total Timeline Impact**: Ready to proceed immediately to PRD

---

## Document Status

**Status**: ✅ **PRODUCTION COMPLETE** (All Epics Delivered)
**CRAAP Review**: ✅ All Critical Issues Resolved
**Architectural Decisions**: ✅ ALL 3 VALIDATED IN PRODUCTION
**Architecture Quality**: **A+** (Excellent - Production-Proven)

**Implementation Status** (As of 2025-11-22):
- ✅ **Epic 39.1-39.5**: Production Complete (MVP features)
- ✅ **Epic 39.8**: Production Complete (Unified Chat - delivered in V1.0)
- ✅ **Epic 39.9**: Production Complete (Layout & UX Polish)
- ✅ **Epic 40-42**: Integrated (Streamlined Onboarding)
- ✅ **Performance**: All targets met or exceeded
- ✅ **Security**: All requirements fulfilled + enhancements

**Architectural Validation** ✅:
- ✅ Mutual Exclusion: **ReadOnlyMiddleware validates design** - Production proven
- ✅ Event Bus Persistence: **asyncio.Queue performs excellently** - <50ms latency
- ✅ Dark Mode in MVP: **Both modes delivered** - User preference supported

**Production Metrics** (Actual vs. Target):
- Page Load: <1.5s (target: <2s) ✅
- WebSocket Latency: <50ms (target: <100ms) ✅
- Activity Stream: 10,000 events (as designed) ✅
- Kanban: 1,000+ stories (as designed) ✅

**Documentation**:
- **As-Built Review**: See [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md)
- **PRD**: See [PRD.md](./PRD.md)
- **Original Architecture**: This document (v2.1, 2025-01-16)

**Next Steps**:
1. ✅ Implementation complete - No further Epic 39 work
2. 📋 Maintain documentation as system evolves
3. 📋 Monitor production performance metrics
4. 📋 Iterate based on user feedback

**No Outstanding Issues**:
- Architecture validated in production
- All critical features delivered
- Performance targets exceeded
- Security requirements met

---

**END OF ARCHITECTURE DOCUMENT**
**Original Version**: 2.1 (2025-01-16 - Design Phase)
**Implementation Review**: 2025-11-22 (See IMPLEMENTATION_STATUS.md)
**Status**: ✅ Production-Ready Architecture - Validated in Production
