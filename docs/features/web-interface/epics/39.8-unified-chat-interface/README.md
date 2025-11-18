# Epic 39.8: Unified Chat/Channels/DM Interface (Slack-Style)

**Feature**: Web Interface
**Epic Number**: 39.8
**Scale Level**: 4 (Greenfield Significant Feature)
**Status**: Ready for Implementation
**Phase**: 3 (V1.2)
**Priority**: Could Have (P2)
**Owner**: Winston (Technical Architect)
**Scrum Master**: Bob
**Developer**: Amelia
**Designer**: Sally

---

## Executive Summary

Epic 39.8 delivers a **unified Slack-style communication interface** that transforms the web UI from a simple chat component to a comprehensive communication hub. This epic replaces the original "Ceremony Channels" concept with a broader vision that includes direct messages (DMs) with all 8 GAO-Dev agents, ceremony channels for multi-agent collaboration, and threading capabilities.

### Key Changes from Original Epic 39.8

**Original Vision** (14 points, 4 stories):
- Narrow focus: Ceremony channels only (#planning, #retrospective)
- Channels visible only when ceremonies active
- Simple message streaming

**New Vision** (52 points, 8 stories):
- **Broad focus**: Complete communication platform (DMs + Channels + Threading)
- **Dual sidebar navigation**: Primary (categories) + Secondary (detailed lists)
- **Direct Messages section**: 1:1 conversations with all 8 agents
- **Channels section**: Multi-agent ceremony channels
- **Threading**: Single-level replies with slide-in panel
- **Message search**: Search across all DMs and channels
- **Replaces agent switcher**: Agent selection becomes spatial/visual (click DM)

### Business Value

1. **Familiar UX**: Mirrors Slack, Teams, Discord - zero learning curve
2. **Better agent interaction**: No dropdown needed - click agent to chat
3. **Context preservation**: Separate conversation history per agent (DM)
4. **Ceremony transparency**: Observe multi-agent collaboration in channels
5. **Improved navigation**: Spatial model replaces abstract switching
6. **Scalable foundation**: Supports future features (notifications, mentions, reactions)

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Goals and Objectives](#goals-and-objectives)
3. [User Personas and Use Cases](#user-personas-and-use-cases)
4. [Epic Architecture](#epic-architecture)
5. [Story Breakdown](#story-breakdown)
6. [Dependencies and Integration](#dependencies-and-integration)
7. [Risk Analysis](#risk-analysis)
8. [Timeline and Effort](#timeline-and-effort)
9. [Success Criteria](#success-criteria)
10. [Open Questions](#open-questions)

---

## 1. Problem Statement

### Current State (Stories 39.7-39.8)

**Story 39.7: Brian Chat Component**
- Single chat interface with agent switcher dropdown
- User selects agent from dropdown
- Chat history NOT preserved per agent (switches context)
- Abstract agent selection (dropdown menu)

**Story 39.8: Multi-Agent Chat Switching**
- Simple dropdown switcher
- No visual indication of agent availability
- No separate conversation contexts
- Limited to single active conversation

### The Problem

**Poor UX Pattern**:
- Dropdown switchers are outdated (Slack abandoned this in 2016)
- Switching agents loses conversation context
- No visual indication of which agents you've talked to
- Cannot reference past conversations easily
- Cannot observe multi-agent collaboration (ceremonies)

**Lack of Ceremony Visibility**:
- No way to observe intra-agent discussions
- Ceremonies are black boxes (user cannot see what agents discuss)
- Missed opportunity for transparency and trust-building

**No Threading**:
- Long conversations become unmanageable
- Cannot reply to specific messages
- Context gets lost in long message streams

### The Solution

A **unified Slack-style interface** with:

**Dual Sidebar Navigation**:
- Primary sidebar (narrow): Home, DMs, Channels, Settings
- Secondary sidebar (wider): Detailed list of DMs or channels

**Direct Messages Section**:
- List all 8 GAO-Dev agents (Brian, Mary, John, Winston, Sally, Bob, Amelia, Murat)
- Click agent to open 1:1 conversation
- Separate conversation history per agent
- Last message preview and timestamp
- Unread indicators (optional for V1.2)

**Channels Section**:
- Channels for ceremonies: #stand-ups, #retrospectives, #sprint-planning
- Channels auto-appear when ceremony triggered
- Multi-agent conversations visible to user
- Archive channels after ceremony ends (read-only)

**Threading**:
- Single-level thread replies (parent message + threaded replies)
- Thread panel slides in from right (doesn't navigate away)
- Thread count indicator on parent message

**Message Search**:
- Search across all DMs and channels
- Filter by agent, date, message type
- Jump to message in context

---

## 2. Goals and Objectives

### Primary Goals

1. **Modernize Communication UX**
   - Replace dropdown agent switcher with spatial DM list
   - Provide familiar Slack-style navigation
   - Zero learning curve for users who know Slack/Teams/Discord

2. **Preserve Conversation Context**
   - Separate conversation history per agent (DM)
   - Threads maintain context within conversations
   - Search enables finding past discussions

3. **Enable Ceremony Observability**
   - Channels for multi-agent collaboration (ceremonies)
   - Real-time streaming of intra-agent messages
   - Archive for post-ceremony review

4. **Improve Agent Discoverability**
   - All 8 agents visible in DM list
   - Visual indication of recent activity
   - Encourages exploration of all agents (not just Brian)

5. **Scalable Foundation**
   - Architecture supports future features (reactions, mentions, notifications)
   - Clean separation: DMs (1:1) vs Channels (multi-agent)

### Success Criteria

**User Adoption**:
- >80% of beta testers prefer new UI to original chat component
- Users report "feels like Slack" (familiarity)
- Average time to find agent conversation: <5 seconds

**Performance**:
- DM list renders in <200ms
- Channel message stream handles 1,000+ messages without lag
- Thread panel opens in <100ms
- Search returns results in <500ms

**Observability**:
- Users can observe 100% of ceremony messages in real-time
- Thread drill-down provides clear context for long discussions
- Search finds relevant messages with >90% accuracy

**Quality**:
- WCAG 2.1 AA compliant (keyboard navigation, screen reader support)
- AI agent (Playwright MCP) finds 0 UX regressions
- Zero data loss (messages persist correctly)

---

## 3. User Personas and Use Cases

### Primary Persona: Sarah - Product Manager

**Use Case 1: Finding Past Conversation with John**

**Scenario**:
1. Sarah talked with John (Product Manager agent) about feature priorities last week
2. She wants to review that discussion before sprint planning
3. Opens web UI, sees DM sidebar with all agents
4. Clicks "John" in DM list
5. Chat history loads instantly
6. Scrolls up to find past conversation
7. Uses search: "feature priorities" to jump to exact message

**Success**: Sarah finds conversation in <10 seconds without remembering dates or exact wording.

---

**Use Case 2: Observing Sprint Planning Ceremony**

**Scenario**:
1. Sarah triggers sprint planning: "Brian, let's plan Sprint 5"
2. Brian starts ceremony, invites Bob (Scrum Master), John, Winston
3. Channels tab badge shows "1 active"
4. Sarah clicks Channels tab
5. Sees #sprint-planning-epic-5 channel (active, green indicator)
6. Clicks channel
7. Message stream shows:
   - Brian: "Welcome to Sprint 5 planning. Bob, what's our velocity?"
   - Bob: "Average velocity: 12 points per sprint"
   - John: "I recommend prioritizing Epic 5 stories 5.1-5.4"
   - Winston: "Story 5.2 has architecture dependency on Epic 4"
8. Sarah observes entire ceremony, gains trust in agent collaboration

**Success**: Sarah sees transparent multi-agent decision-making, understands ceremony outcomes.

---

### Primary Persona: Alex - Senior Developer

**Use Case 3: Threaded Discussion with Winston**

**Scenario**:
1. Alex is chatting with Winston about database architecture
2. Winston suggests using PostgreSQL with partitioning
3. Alex wants to ask follow-up questions without losing main thread
4. Clicks "Reply in thread" on Winston's message
5. Thread panel slides in from right (main chat still visible)
6. Alex types: "What partition key do you recommend?"
7. Winston replies in thread: "Use created_at timestamp for time-series data"
8. Thread conversation continues (3 messages)
9. Alex closes thread panel, returns to main chat
10. Main chat shows: "Winston's message [3 replies]"

**Success**: Alex drills into specific topic without cluttering main conversation.

---

### Primary Persona: Claude - AI Agent (Playwright MCP)

**Use Case 4: Testing DM Navigation**

**Scenario**:
1. Claude navigates to web UI
2. Locates DM section via `data-testid="dm-section"`
3. Finds all 8 agents via `data-testid="dm-item-brian"`, `data-testid="dm-item-mary"`, etc.
4. Clicks DM item for Mary
5. Verifies chat messages load via `data-testid="chat-message-mary"`
6. Sends test message via `data-testid="chat-input"`
7. Verifies response appears
8. Clicks DM item for John (switch agent)
9. Verifies chat history is different (separate context)

**Success**: AI agent successfully tests DM navigation, finds 0 UX issues.

---

## 4. Epic Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Browser (Unified Chat UI)                  │
│                                                                 │
│  ┌────────────┬────────────────────────────────────────────┐   │
│  │  Primary   │  Secondary Sidebar                         │   │
│  │  Sidebar   │                                            │   │
│  │            │  DMs Section (when "DMs" selected):        │   │
│  │  [Home]    │  ┌──────────────────────────────────────┐  │   │
│  │  [DMs] ←   │  │ Brian                 "Hi there..." │  │   │
│  │  [Channels]│  │ Mary                  "Let's brainstorm"│   │
│  │  [Settings]│  │ John                  2 min ago      │  │   │
│  │            │  │ Winston               ...            │  │   │
│  │            │  │ Sally                 ...            │  │   │
│  │            │  │ Bob                   ...            │  │   │
│  │            │  │ Amelia                ...            │  │   │
│  │            │  │ Murat                 ...            │  │   │
│  │            │  └──────────────────────────────────────┘  │   │
│  │            │                                            │   │
│  │            │  Channels Section (when "Channels" selected):│
│  │            │  ┌──────────────────────────────────────┐  │   │
│  │            │  │ #sprint-planning     🟢 Active      │  │   │
│  │            │  │ #retrospective-epic-4  Archived    │  │   │
│  │            │  └──────────────────────────────────────┘  │   │
│  └────────────┴────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                Main Chat/Channel View                    │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Message Stream (virtualized scrolling)           │  │  │
│  │  │  - Agent avatar, name, timestamp                  │  │  │
│  │  │  - Markdown rendering                             │  │  │
│  │  │  - Thread indicator: "3 replies" (clickable)      │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Message Input (with send button)                 │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Thread Panel (slides in from right, conditional)       │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Thread: "Winston's architecture suggestion"      │  │  │
│  │  │  ────────────────────────────────────────────────  │  │  │
│  │  │  [Parent Message]                                 │  │  │
│  │  │  Winston: "Use PostgreSQL with partitioning"      │  │  │
│  │  │  ────────────────────────────────────────────────  │  │  │
│  │  │  [Thread Replies]                                 │  │  │
│  │  │  Alex: "What partition key?"                      │  │  │
│  │  │  Winston: "created_at timestamp"                  │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Model

**DM Conversation**:
```typescript
interface DMConversation {
  agent: AgentName;  // "brian" | "mary" | "john" | ...
  messages: Message[];
  lastMessageAt: Date;
  lastMessagePreview: string;
  unreadCount: number;  // Optional for V1.2
}
```

**Channel**:
```typescript
interface Channel {
  id: string;  // "sprint-planning-epic-5"
  name: string;  // "#sprint-planning-epic-5"
  ceremonyType: string;  // "sprint-planning" | "retrospective" | ...
  status: "active" | "archived";
  messages: Message[];
  participants: AgentName[];
  startedAt: Date;
  endedAt?: Date;
}
```

**Message**:
```typescript
interface Message {
  id: string;
  conversationId: string;  // DM agent or channel ID
  conversationType: "dm" | "channel";
  sender: AgentName | "user";
  content: string;  // Markdown
  timestamp: Date;
  threadId?: string;  // If message is in thread
  threadCount?: number;  // If message has thread replies
  replyToMessageId?: string;  // Parent message ID
}
```

**Thread**:
```typescript
interface Thread {
  id: string;
  parentMessageId: string;
  messages: Message[];
  participantCount: number;
}
```

### State Management (Zustand)

```typescript
// stores/unifiedChatStore.ts
interface UnifiedChatState {
  // Navigation
  primaryView: "home" | "dms" | "channels" | "settings";
  activeDM: AgentName | null;
  activeChannel: string | null;

  // DMs
  dmConversations: Map<AgentName, DMConversation>;

  // Channels
  channels: Channel[];

  // Threading
  activeThread: Thread | null;

  // Search
  searchQuery: string;
  searchResults: Message[];

  // Actions
  selectDM: (agent: AgentName) => void;
  selectChannel: (channelId: string) => void;
  sendMessage: (content: string) => Promise<void>;
  openThread: (parentMessageId: string) => Promise<void>;
  closeThread: () => void;
  searchMessages: (query: string) => Promise<void>;
}
```

### Backend API

**DM Endpoints**:
```python
GET  /api/dms                           # List all DM conversations
GET  /api/dms/{agent}/messages          # Get messages for specific agent
POST /api/dms/{agent}/messages          # Send message to agent
```

**Channel Endpoints**:
```python
GET  /api/channels                      # List all channels
GET  /api/channels/{channel_id}/messages # Get channel messages
POST /api/channels/{channel_id}/messages # Send message to channel (user participation)
POST /api/channels/{channel_id}/archive  # Archive channel (admin only)
```

**Thread Endpoints**:
```python
GET  /api/threads/{thread_id}           # Get thread messages
POST /api/threads/{thread_id}/messages  # Reply in thread
```

**Search Endpoint**:
```python
GET  /api/search/messages?q={query}&type={dm|channel|all}&agent={agent_name}
```

### WebSocket Events

**DM Events**:
```typescript
dm.message.sent       // User sent message to agent
dm.message.received   // Agent replied in DM
dm.updated            // Last message preview updated
```

**Channel Events**:
```typescript
channel.created       // Ceremony started, channel created
channel.message       // Agent sent message in channel
channel.archived      // Ceremony ended, channel archived
```

**Thread Events**:
```typescript
thread.created        // User or agent started thread
thread.reply          // New reply in thread
thread.updated        // Thread count updated
```

---

## 5. Story Breakdown

### Story 39.30: Dual Sidebar Navigation (Primary + Secondary)

**Size**: Medium (4 points)

**Description**: Implement Slack-style dual sidebar with primary navigation (Home, DMs, Channels, Settings) and secondary sidebar showing detailed lists.

**User Story**:
> As a user, I want a dual sidebar navigation so that I can quickly switch between DMs, Channels, and other sections with familiar Slack-like UX.

**Acceptance Criteria**:
- [ ] Primary sidebar (narrow, ~60px width) with 4 icons: Home, DMs, Channels, Settings
- [ ] Secondary sidebar (wider, ~250px width) with detailed content based on primary selection
- [ ] Primary sidebar icons highlight when active
- [ ] Secondary sidebar shows:
  - "DMs" selected: List of 8 agents with last message preview
  - "Channels" selected: List of active/archived ceremony channels
  - "Home" selected: Dashboard overview (out of scope for this story, placeholder)
  - "Settings" selected: Settings panel (out of scope, placeholder)
- [ ] Responsive: Secondary sidebar collapsible on smaller screens (min-width 1024px)
- [ ] Smooth transitions (<100ms) when switching primary sections
- [ ] Keyboard navigation: Tab through primary icons, Enter to select
- [ ] ARIA labels: `aria-label="Direct Messages"`, `aria-label="Channels"`, etc.
- [ ] Stable test IDs: `data-testid="primary-sidebar"`, `data-testid="secondary-sidebar"`

**Technical Notes**:
- Component: `<DualSidebar>` with `<PrimarySidebar>` and `<SecondarySidebar>` children
- Use shadcn/ui `<Separator>` for visual dividers
- State: Zustand store for `primaryView` selection
- Layout: CSS Grid or Flexbox (primary | secondary | main content)

**Dependencies**:
- Epic 39.2: Frontend Foundation (shadcn/ui setup)

**Test Scenarios**:
1. Happy path: Click "DMs" in primary sidebar, see agent list in secondary sidebar
2. Edge case: Resize window below 1024px, secondary sidebar collapses (hamburger menu)
3. Error: None (pure UI component)

---

### Story 39.31: DMs Section - Agent List and Conversation UI

**Size**: Large (5 points)

**Description**: Implement Direct Messages section with list of all 8 GAO-Dev agents, last message previews, and ability to open 1:1 conversations.

**User Story**:
> As a user, I want to see a list of all 8 agents with last message previews so that I can quickly find and resume conversations.

**Acceptance Criteria**:
- [ ] DM list shows all 8 agents: Brian, Mary, John, Winston, Sally, Bob, Amelia, Murat
- [ ] Each DM item displays:
  - Agent avatar (icon or colored circle with initial)
  - Agent name
  - Last message preview (truncated to 50 characters)
  - Timestamp (relative: "2 min ago", "yesterday")
- [ ] Click DM item to open conversation in main view
- [ ] Active DM item highlighted (background color change)
- [ ] DM list sorted by recent activity (most recent first)
- [ ] Empty state: "No messages yet" if agent never chatted
- [ ] Hover state: Visual feedback on DM item hover
- [ ] Keyboard navigation: Arrow keys to navigate, Enter to open
- [ ] Stable test IDs: `data-testid="dm-item-brian"`, `data-testid="dm-item-mary"`, etc.
- [ ] Unread count placeholder (optional, defer badge to V1.3)

**API Integration**:
- `GET /api/dms` - Fetch all DM conversations with last message metadata
- Response:
  ```json
  {
    "conversations": [
      {
        "agent": "brian",
        "lastMessage": "How can I help you today?",
        "lastMessageAt": "2025-01-16T10:30:00Z",
        "messageCount": 12
      },
      ...
    ]
  }
  ```

**Technical Notes**:
- Component: `<DMList>` with `<DMItem>` children
- State: Zustand `dmConversations` map
- Reuse existing ChatSession logic from Epic 30 for conversation history
- Virtual scrolling NOT needed (only 8 agents)
- WebSocket: Subscribe to `dm.updated` events for real-time last message updates

**Dependencies**:
- Story 39.30: Dual Sidebar Navigation
- Epic 30: ChatREPL (ChatSession for conversation history)

**Test Scenarios**:
1. Happy path: Load DM list, see all 8 agents, click Brian, conversation loads
2. Edge case: Agent never chatted, shows "No messages yet"
3. Real-time: Agent sends message while DM list open, last message preview updates
4. Error: API fails, show error toast "Failed to load DMs [Retry]"

---

### Story 39.32: DM Conversation View and Message Sending

**Size**: Large (5 points)

**Description**: Implement conversation view for 1:1 chats with agents, message sending, and streaming responses.

**User Story**:
> As a user, I want to send messages to agents and see responses in real-time so that I can have natural conversations.

**Acceptance Criteria**:
- [ ] Main content area shows conversation when DM selected
- [ ] Header displays: Agent name, avatar, status indicator (online/offline - optional)
- [ ] Message stream displays all messages chronologically (newest at bottom)
- [ ] Each message shows:
  - Sender (agent or user)
  - Avatar
  - Message content (Markdown rendered)
  - Timestamp (relative: "2 min ago")
  - Thread count indicator if message has replies ("3 replies", clickable)
- [ ] Message input textarea at bottom with "Send" button
- [ ] Streaming response support: Agent messages appear character-by-character
- [ ] Auto-scroll to bottom on new message
- [ ] Message virtualization for >1,000 messages (@tanstack/react-virtual)
- [ ] "Load more" button at top to fetch older messages (pagination)
- [ ] Keyboard shortcut: Enter to send (Shift+Enter for newline)
- [ ] "Send" button disabled during agent response
- [ ] Error handling: Show retry button if send fails
- [ ] Stable test IDs: `data-testid="chat-message-brian"`, `data-testid="chat-input"`, `data-testid="chat-send-button"`

**API Integration**:
- `GET /api/dms/{agent}/messages?offset=0&limit=50` - Fetch messages
- `POST /api/dms/{agent}/messages` - Send message
  ```json
  {
    "content": "User message text"
  }
  ```
- WebSocket: Subscribe to `dm.message.received` for streaming responses

**Technical Notes**:
- Reuse BrianWebAdapter from Epic 30 for agent conversation handling
- State: Zustand `activeDM` and `dmConversations[agent].messages`
- Markdown rendering: Use react-markdown with syntax highlighting
- Streaming: WebSocket chunks append to message content in real-time

**Dependencies**:
- Story 39.31: DMs Section - Agent List
- Epic 30: ChatREPL (BrianWebAdapter for agent responses)

**Test Scenarios**:
1. Happy path: Select Brian, send message, see streaming response
2. Edge case: Very long message (10,000 characters), textarea expands
3. Real-time: Agent sends message while conversation open, message appears
4. Error: API fails, show "Failed to send message [Retry]"

---

### Story 39.33: Channels Section - Ceremony Channels UI

**Size**: Medium (4 points)

**Description**: Implement Channels section showing active and archived ceremony channels with multi-agent message streams.

**User Story**:
> As a user, I want to see ceremony channels so that I can observe multi-agent collaboration during sprint planning, retrospectives, etc.

**Acceptance Criteria**:
- [ ] Channel list in secondary sidebar when "Channels" selected in primary sidebar
- [ ] Each channel item displays:
  - Channel name (e.g., "#sprint-planning-epic-5")
  - Status indicator: Green dot (active), Gray dot (archived)
  - Last message preview
  - Timestamp
- [ ] Click channel to open in main view
- [ ] Active channel highlighted
- [ ] Channels sorted: Active first, then archived by date
- [ ] Empty state: "No active ceremonies" if no channels
- [ ] Channel message stream shows:
  - All messages chronologically
  - Agent avatar, name, timestamp
  - Markdown rendering
  - Multi-agent participants visible (Brian, Bob, John, Winston in #sprint-planning)
- [ ] User can send message to channel (participate in ceremony)
- [ ] Archive indicator: Banner "This channel is archived (read-only)" if archived
- [ ] Stable test IDs: `data-testid="channel-item"`, `data-testid="channel-message"`

**API Integration**:
- `GET /api/channels` - List channels
  ```json
  {
    "channels": [
      {
        "id": "sprint-planning-epic-5",
        "name": "#sprint-planning-epic-5",
        "ceremonyType": "sprint-planning",
        "status": "active",
        "participants": ["brian", "bob", "john", "winston"],
        "lastMessageAt": "2025-01-16T10:45:00Z"
      }
    ]
  }
  ```
- `GET /api/channels/{channel_id}/messages` - Fetch channel messages
- `POST /api/channels/{channel_id}/messages` - Send message to channel

**Technical Notes**:
- Component: `<ChannelList>` and `<ChannelView>`
- State: Zustand `channels` array and `activeChannel` string
- Integrate with Epic 28: CeremonyOrchestrator via CeremonyAdapter
- WebSocket: Subscribe to `channel.created`, `channel.message`, `channel.archived`

**Dependencies**:
- Story 39.30: Dual Sidebar Navigation
- Epic 28: CeremonyOrchestrator (ceremony event streaming)

**Test Scenarios**:
1. Happy path: Brian starts retrospective, #retrospective-epic-4 appears, user clicks, sees messages
2. Edge case: No active ceremonies, shows empty state
3. Real-time: Agent sends message in active channel, message appears
4. Error: API fails, show "Failed to load channels [Retry]"

---

### Story 39.34: Message Threading Infrastructure

**Size**: Medium (4 points)

**Description**: Implement backend infrastructure for single-level message threading (parent message + threaded replies).

**User Story**:
> As a user, I want to reply to specific messages in threads so that I can have focused sub-conversations without cluttering the main stream.

**Acceptance Criteria**:
- [ ] Database schema for threads:
  - `threads` table: `id`, `parent_message_id`, `created_at`
  - `messages` table: Add `thread_id` (nullable), `reply_to_message_id` (nullable)
- [ ] API endpoint: `POST /api/threads` - Create thread from parent message
  ```json
  {
    "parentMessageId": "msg-123",
    "conversationId": "brian",  // DM agent or channel ID
    "conversationType": "dm"     // "dm" | "channel"
  }
  ```
  Response:
  ```json
  {
    "threadId": "thread-456"
  }
  ```
- [ ] API endpoint: `GET /api/threads/{thread_id}` - Fetch thread messages
  Response:
  ```json
  {
    "parentMessage": { "id": "msg-123", "content": "...", ... },
    "replies": [
      { "id": "msg-124", "content": "...", "threadId": "thread-456", ... }
    ]
  }
  ```
- [ ] API endpoint: `POST /api/threads/{thread_id}/messages` - Reply in thread
  ```json
  {
    "content": "Thread reply text"
  }
  ```
- [ ] WebSocket events:
  - `thread.created` - New thread started
  - `thread.reply` - New reply in thread
  - `thread.updated` - Thread count updated on parent message
- [ ] Parent message thread count updates when reply added
- [ ] Thread count persisted in `messages.thread_count` (denormalized for performance)

**Technical Notes**:
- Use existing `.gao-dev/documents.db` SQLite database
- Add migration script for schema changes
- Thread count denormalization avoids COUNT queries on every message render
- Single-level threading: Replies in thread cannot have sub-threads

**Dependencies**:
- Epic 27: GitIntegratedStateManager (database access)

**Test Scenarios**:
1. Happy path: User creates thread, sends reply, thread count updates
2. Edge case: Thread with 100+ replies, pagination works
3. Error: Database error, show "Failed to create thread [Retry]"

---

### Story 39.35: Thread Panel UI (Slide-In from Right)

**Size**: Large (5 points)

**Description**: Implement thread panel UI that slides in from right when user clicks "Reply in thread" or clicks thread count indicator.

**User Story**:
> As a user, I want to see thread replies in a slide-in panel so that I can drill into specific discussions without losing my place in the main conversation.

**Acceptance Criteria**:
- [ ] "Reply in thread" button on every message (hover to show)
- [ ] Thread count indicator on messages with replies ("3 replies", clickable)
- [ ] Click "Reply in thread" or thread count → Thread panel slides in from right
- [ ] Thread panel layout:
  - Header: "Thread: [Parent message preview]" with close button
  - Parent message display (full content)
  - Divider
  - Thread replies (chronological, newest at bottom)
  - Message input at bottom (send reply)
- [ ] Thread panel width: 40% of viewport, min 400px
- [ ] Main view remains visible (60% width) - user can still see main conversation
- [ ] Thread panel slide-in animation: 200ms ease-out
- [ ] Close thread panel: Click close button or click outside panel
- [ ] Thread replies show same format as main messages (avatar, name, timestamp, Markdown)
- [ ] Real-time updates: New replies appear immediately
- [ ] Virtual scrolling for threads with >100 replies
- [ ] Keyboard shortcut: Escape to close thread panel
- [ ] Stable test IDs: `data-testid="thread-panel"`, `data-testid="thread-reply-button"`

**Technical Notes**:
- Component: `<ThreadPanel>` with slide-in animation (CSS transform or Framer Motion)
- State: Zustand `activeThread` (null when closed)
- Layout: CSS Grid with main view and thread panel columns
- WebSocket: Subscribe to `thread.reply` for real-time updates

**Dependencies**:
- Story 39.34: Message Threading Infrastructure
- Story 39.32: DM Conversation View (reuse message components)

**Test Scenarios**:
1. Happy path: User clicks "Reply in thread", panel slides in, user sends reply, reply appears
2. Edge case: User opens thread with 100+ replies, virtual scrolling works
3. Real-time: Agent replies in thread while panel open, reply appears
4. Error: API fails, show "Failed to load thread [Retry]"

---

### Story 39.36: Message Search Across DMs and Channels

**Size**: Medium (3 points)

**Description**: Implement message search functionality with filters for agent, date range, and message type (DM or channel).

**User Story**:
> As a user, I want to search messages across all DMs and channels so that I can quickly find past discussions.

**Acceptance Criteria**:
- [ ] Search input in top bar (always visible)
- [ ] Search query triggers API request (debounced 300ms)
- [ ] Search filters:
  - Message type: All, DMs only, Channels only
  - Agent: All, or specific agent (dropdown)
  - Date range: All time, Last 7 days, Last 30 days, Custom range
- [ ] Search results display:
  - Message preview (50 characters)
  - Sender (agent or user)
  - Conversation context (DM with Brian, or #sprint-planning)
  - Timestamp
  - Click result to jump to message in context (opens DM or channel, scrolls to message)
- [ ] Search results sorted by relevance (full-text search ranking)
- [ ] Highlight search query in results
- [ ] Empty state: "No messages found for '[query]'"
- [ ] Loading state: Spinner while searching
- [ ] Keyboard shortcut: Cmd+K to focus search input
- [ ] Stable test IDs: `data-testid="search-input"`, `data-testid="search-result"`

**API Integration**:
- `GET /api/search/messages?q={query}&type={dm|channel|all}&agent={agent_name}&date_range={7d|30d|all}`
  Response:
  ```json
  {
    "results": [
      {
        "messageId": "msg-123",
        "conversationId": "brian",
        "conversationType": "dm",
        "content": "Let's create a PRD for user authentication...",
        "sender": "brian",
        "timestamp": "2025-01-10T14:30:00Z",
        "highlights": ["PRD", "authentication"]
      }
    ],
    "total": 15
  }
  ```

**Technical Notes**:
- Use SQLite FTS5 (Full-Text Search) extension for efficient search
- Debounce search input to avoid excessive API calls
- Component: `<SearchBar>` and `<SearchResults>` modal or slide-in panel
- State: Zustand `searchQuery` and `searchResults`

**Dependencies**:
- Story 39.31: DMs Section
- Story 39.33: Channels Section

**Test Scenarios**:
1. Happy path: User searches "architecture", sees results from Winston DM and #retrospective channel
2. Edge case: User searches non-existent term, shows "No messages found"
3. Performance: Search completes in <500ms for 10,000+ messages
4. Error: API fails, show "Search failed [Retry]"

---

### Story 39.37: Channel Archive and Export

**Size**: Small (2 points)

**Description**: Implement channel archive functionality (mark ceremony channels as read-only after ceremony ends) and export channel transcript to Markdown.

**User Story**:
> As a user, I want to archive ceremony channels after ceremonies end so that I can review past discussions without cluttering active channels.

**Acceptance Criteria**:
- [ ] Ceremony channels automatically archived when ceremony ends (CeremonyOrchestrator emits `ceremony.completed`)
- [ ] Archived channels show:
  - Gray status indicator (not green)
  - "Archived" badge
  - Read-only banner: "This channel is archived. Messages cannot be sent."
- [ ] Archived channels moved to "Archived" section in channel list (collapsible)
- [ ] Export button on archived channels: "Export Transcript"
- [ ] Export generates Markdown file:
  ```markdown
  # Sprint Planning - Epic 5
  **Date**: 2025-01-16
  **Participants**: Brian, Bob, John, Winston

  ---

  **Brian** (10:30 AM):
  Welcome to Sprint 5 planning.

  **Bob** (10:31 AM):
  Average velocity: 12 points per sprint.

  ...
  ```
- [ ] Export downloads as `{ceremony-type}-{epic-num}-{date}.md`
- [ ] Archive action also available via API: `POST /api/channels/{channel_id}/archive` (admin only, for manual archive)
- [ ] Stable test IDs: `data-testid="channel-export-button"`, `data-testid="archived-channel"`

**API Integration**:
- `POST /api/channels/{channel_id}/archive` - Archive channel (manual)
- `GET /api/channels/{channel_id}/export` - Export transcript
  Response: Markdown file download

**Technical Notes**:
- Archive status stored in `channels.status` column ("active" | "archived")
- WebSocket: Subscribe to `channel.archived` event
- Export uses existing message data, formats to Markdown template

**Dependencies**:
- Story 39.33: Channels Section

**Test Scenarios**:
1. Happy path: Ceremony ends, channel auto-archived, user exports transcript
2. Edge case: Channel with 1,000+ messages, export completes in <5 seconds
3. Error: Export fails, show "Export failed [Retry]"

---

### Story 39.38: Context Switching and Unread Indicators (Optional - Defer to V1.3)

**Size**: Medium (3 points) - DEFERRED

**Description**: Implement unread message indicators on DM and channel items to help users track new activity.

**Status**: DEFERRED to V1.3 (not required for V1.2 launch)

**Rationale**: Unread indicators are valuable but not critical for MVP. They require additional state management, backend tracking, and real-time synchronization. Defer to V1.3 to focus on core unified interface for V1.2.

**Acceptance Criteria** (if implemented in V1.3):
- [ ] Unread badge on DM items showing unread count
- [ ] Unread badge on channel items
- [ ] Bold text for DM/channel items with unread messages
- [ ] Mark as read when user opens conversation/channel
- [ ] Persist unread state across sessions (database)

---

## 6. Dependencies and Integration

### Internal Dependencies

**Epic 30: Interactive Brian Chat Interface (ChatREPL)**
- **Reuse**: ChatSession for conversation history
- **Reuse**: BrianWebAdapter for agent response streaming
- **Reuse**: ConversationalBrian for agent logic
- **Integration Point**: DM conversations use same ChatSession instances, one per agent
- **Migration**: Existing chat component (Story 39.7) refactored to use DM interface

**Epic 27: Git-Integrated Hybrid Wisdom**
- **Reuse**: GitIntegratedStateManager for database access (thread storage)
- **Reuse**: `.gao-dev/documents.db` for message persistence
- **Integration Point**: Thread and message tables added via migration

**Epic 28: Ceremony-Driven Workflow Integration**
- **Reuse**: CeremonyOrchestrator for ceremony lifecycle
- **Reuse**: CeremonyAdapter for event translation to WebSocket
- **Integration Point**: Ceremony channels created when `ceremony.started` event emitted

**Epic 39.2: Frontend Foundation**
- **Reuse**: React + Vite + Zustand setup
- **Reuse**: shadcn/ui components (Button, Card, Sheet, Tabs, etc.)
- **Integration Point**: Unified chat uses same component library

**Epic 39.3: Core Observability**
- **Reuse**: WebSocket infrastructure (WebEventBus)
- **Reuse**: Real-time event streaming
- **Integration Point**: DM and channel messages stream via WebSocket

---

### External Dependencies

**Slack UX Patterns**:
- **Research**: Study Slack's 2023 redesign (dual sidebar)
- **Inspiration**: DM list with last message previews, threading model
- **Note**: Don't copy exact design, but follow established UX patterns

**Browser APIs**:
- **IndexedDB**: For archiving old messages (>30 days)
- **Page Visibility API**: Detect when user switches tabs (pause real-time updates)
- **Keyboard Events**: For keyboard shortcuts (Enter to send, Cmd+K for search)

---

### Migration Impact

**Story 39.8 (Multi-Agent Chat Switching) - OBSOLETE**:
- **Status**: Replaced by DM list navigation
- **Migration**: Remove agent switcher dropdown component
- **Refactor**: Update chat component to integrate with DM interface

**Story 39.7 (Brian Chat Component) - ADAPTATION NEEDED**:
- **Status**: Partial reuse
- **Migration**: Refactor to work as DM conversation view
- **Changes**: Remove agent switcher, integrate with DM list

**Database Schema**:
- **New tables**: `threads` table
- **Modified tables**: `messages` table (add `thread_id`, `reply_to_message_id`, `thread_count`)
- **Migration**: SQL migration script for schema changes

---

## 7. Risk Analysis

### Critical Risks

**Risk 1: Epic Scope Creep (52 Points vs Original 14 Points)**
- **Impact**: HIGH - Timeline extends beyond Phase 3 (8 weeks)
- **Likelihood**: MEDIUM
- **Mitigation**:
  - Break epic into V1.2 (core features) and V1.3 (polish)
  - Story 39.38 (Unread Indicators) already deferred to V1.3
  - Can defer Story 39.36 (Message Search) to V1.3 if timeline pressure
  - Focus: DMs (Stories 39.31-39.32), Channels (Story 39.33), Threading (Stories 39.34-39.35)
- **Owner**: Bob (Scrum Master)

**Risk 2: ChatREPL Integration Complexity**
- **Impact**: HIGH - DM conversations may not preserve context correctly
- **Likelihood**: MEDIUM
- **Mitigation**:
  - Early spike: Test ChatSession with multiple agent instances (one per DM)
  - Ensure ChatSession state is isolated per agent
  - Add integration tests for agent switching (verify separate contexts)
- **Owner**: Amelia (Developer)

**Risk 3: Threading State Management Complexity**
- **Impact**: MEDIUM - Thread panel state conflicts with main view
- **Likelihood**: MEDIUM
- **Mitigation**:
  - Use single Zustand store for all chat state
  - Clear ownership: `activeThread` controls thread panel visibility
  - Test edge cases: Open thread, switch DM, verify thread closes
- **Owner**: Amelia (Developer)

**Risk 4: Real-Time Performance Degradation**
- **Impact**: MEDIUM - WebSocket events cause UI lag with many active conversations
- **Likelihood**: LOW
- **Mitigation**:
  - Virtual scrolling for message streams (already planned)
  - Debounce search input (300ms)
  - Limit active WebSocket subscriptions (unsubscribe from inactive DMs/channels)
  - Performance testing with 1,000+ messages per conversation
- **Owner**: Winston (Architect)

---

### Medium Risks

**Risk 5: Ceremony Channel Auto-Creation Timing**
- **Impact**: MEDIUM - Channel appears before ceremony messages arrive
- **Likelihood**: MEDIUM
- **Mitigation**:
  - WebSocket event ordering: `ceremony.started` before `ceremony.message`
  - Backend buffers messages if channel not created yet
  - Frontend shows loading spinner until first message arrives
- **Owner**: Amelia (Developer)

**Risk 6: Message Search Performance**
- **Impact**: MEDIUM - Search takes >500ms for large message databases
- **Likelihood**: LOW
- **Mitigation**:
  - Use SQLite FTS5 (Full-Text Search) for efficient indexing
  - Database index on `messages.timestamp` for date range filters
  - Limit search results to 100 (pagination for more)
  - Performance benchmark: 10,000+ messages in <500ms
- **Owner**: Winston (Architect)

**Risk 7: Thread Panel Mobile Responsiveness**
- **Impact**: LOW - Thread panel doesn't fit on smaller screens
- **Likelihood**: MEDIUM (but mobile is out of scope for MVP)
- **Mitigation**:
  - Document minimum screen width: 1024px (same as entire web UI)
  - On smaller screens, thread panel replaces main view (full-width modal)
  - Defer mobile optimization to V2.0
- **Owner**: Sally (UX Designer)

---

### Low Risks

**Risk 8: Agent Avatars Design Consistency**
- **Impact**: LOW - Avatars look inconsistent across DM list and messages
- **Likelihood**: LOW
- **Mitigation**:
  - Define avatar system upfront (colored circles with initials)
  - Sally creates design guide for agent avatars
  - Reuse same avatar component in DM list, messages, thread panel
- **Owner**: Sally (UX Designer)

---

## 8. Timeline and Effort

### Total Story Points: 52 Points

**Breakdown by Story**:
- Story 39.30: Dual Sidebar Navigation - 4 points (M)
- Story 39.31: DMs Section - Agent List - 5 points (L)
- Story 39.32: DM Conversation View - 5 points (L)
- Story 39.33: Channels Section - 4 points (M)
- Story 39.34: Message Threading Infrastructure - 4 points (M)
- Story 39.35: Thread Panel UI - 5 points (L)
- Story 39.36: Message Search - 3 points (M)
- Story 39.37: Channel Archive and Export - 2 points (S)
- Story 39.38: Unread Indicators - 3 points (M) - DEFERRED to V1.3

**V1.2 Scope (Epic 39.8)**: 32 points (Stories 39.30-39.37, excluding 39.38)

**Deferred to V1.3**: 3 points (Story 39.38)

---

### Sprint Allocation (Phase 3 - V1.2)

**Assumption**: Team velocity = 5-6 points per week

**Sprint 13 (Week 21-22): Sidebar and DMs Foundation**
- Story 39.30: Dual Sidebar Navigation (4 pts)
- Story 39.31: DMs Section - Agent List (5 pts)
- **Velocity**: 9 points (2-week sprint)

**Sprint 14 (Week 23-24): DM Conversations and Channels**
- Story 39.32: DM Conversation View (5 pts)
- Story 39.33: Channels Section (4 pts)
- **Velocity**: 9 points (2-week sprint)

**Sprint 15 (Week 25): Threading Infrastructure**
- Story 39.34: Message Threading Infrastructure (4 pts)
- **Velocity**: 4 points (1-week sprint)

**Sprint 16 (Week 26): Thread Panel UI**
- Story 39.35: Thread Panel UI (5 pts)
- **Velocity**: 5 points (1-week sprint)

**Sprint 17 (Week 27): Search and Archive**
- Story 39.36: Message Search (3 pts)
- Story 39.37: Channel Archive and Export (2 pts)
- **Velocity**: 5 points (1-week sprint)

**Sprint 18 (Week 28): Testing and Polish**
- E2E testing, bug fixes, UX polish
- **Velocity**: 0 points (buffer)

---

### Revised Phase 3 Timeline

**Original Phase 3 Plan** (8 weeks):
- Epic 39.8: Ceremony Channels (14 points) - Weeks 21-23
- Epic 39.9: Customizable Layout (10 points) - Week 24
- Epic 39.10: Advanced Metrics (18 points) - Weeks 25-28

**New Phase 3 Plan** (8 weeks):
- Epic 39.8: Unified Chat Interface (32 points) - Weeks 21-27
- **COMPRESSED**: Epic 39.9 (Layout) + Epic 39.10 (Metrics) - Week 28 (buffer/stretch)

**Timeline Impact**: +1 week buffer used for Epic 39.8 (originally 3 weeks, now 7 weeks including buffer)

**Recommendation**: Consider extending Phase 3 to 10 weeks OR deferring Epic 39.9 and Epic 39.10 to V1.3 release.

---

## 9. Success Criteria

### Functional Completeness

- [ ] All 8 stories complete (Stories 39.30-39.37)
- [ ] DM conversations work with all 8 agents
- [ ] Ceremony channels auto-create and archive correctly
- [ ] Threading works in both DMs and channels
- [ ] Message search returns accurate results

### User Experience

- [ ] >80% of beta testers rate UX as "Excellent" or "Good"
- [ ] Users report "feels like Slack" (familiarity target: >90% agreement)
- [ ] Average time to find agent conversation: <5 seconds
- [ ] Zero confusion about how to switch agents (spatial navigation is intuitive)

### Performance

- [ ] DM list renders in <200ms
- [ ] Channel message stream handles 1,000+ messages without lag
- [ ] Thread panel opens in <100ms
- [ ] Message search returns results in <500ms
- [ ] Virtual scrolling works smoothly (60fps) with 10,000+ messages

### Observability

- [ ] Users can observe 100% of ceremony messages in real-time
- [ ] Thread drill-down provides clear context for long discussions
- [ ] Search finds relevant messages with >90% accuracy (measured by user feedback)

### Quality

- [ ] WCAG 2.1 AA compliant (keyboard navigation, screen reader support)
- [ ] AI agent (Playwright MCP) finds 0 UX regressions compared to Story 39.7-39.8
- [ ] Zero data loss (messages persist correctly across sessions)
- [ ] E2E test coverage >80% for all stories

### Integration

- [ ] ChatREPL integration works correctly (separate contexts per agent)
- [ ] Ceremony channels integrate with Epic 28 (CeremonyOrchestrator)
- [ ] WebSocket events stream correctly for DMs and channels
- [ ] Database migrations apply successfully with zero downtime

---

## 10. Open Questions

### Q1: Should DM list show online/offline status for agents?

**Context**: Agents are always "online" (they're AI, not humans with presence status).

**Options**:
A. Don't show status (simplest, agents always available)
B. Show "Available" for all agents (visual consistency with Slack)
C. Show busy indicator when agent is processing request (e.g., Brian is "Typing...")

**Recommendation**: Option C (show typing indicator when agent is responding). Defer online/offline to V1.3 if user research shows demand.

**Owner**: Sally (UX Designer)

---

### Q2: Should thread panel replace main view on smaller screens?

**Context**: Thread panel takes 40% of viewport width. On screens <1024px, this may be cramped.

**Options**:
A. Thread panel always slides in (40% width), main view compressed (60%)
B. Thread panel replaces main view entirely on <1024px screens (full-width modal)
C. Disable threading on <1024px screens

**Recommendation**: Option B (full-width modal on smaller screens). Maintains functionality while respecting screen constraints.

**Owner**: Sally (UX Designer)

---

### Q3: Should ceremony channels support user participation in V1.2?

**Context**: Story 39.33 includes user sending messages to channels. This enables "user joins ceremony" workflow but adds complexity (user messages vs agent messages).

**Options**:
A. Read-only channels in V1.2 (user observes, cannot send messages)
B. User can send messages in V1.2 (full participation)
C. User can send messages only in active ceremonies, not archived

**Recommendation**: Option B (user can send messages in V1.2). This is a key value proposition ("participate in ceremonies") and aligns with Slack UX. Defer moderation/permissions to V1.3 if needed.

**Owner**: John (Product Manager)

---

### Q4: Should message search include file attachments or only text?

**Context**: Agents may attach files in messages (e.g., Winston shares architecture diagram). Should search index file content?

**Options**:
A. Search text only in V1.2 (simplest)
B. Search file metadata (filename, type) in V1.2
C. Full-text search of file content (e.g., search inside PDFs) in V1.3

**Recommendation**: Option B (search file metadata in V1.2). Defer full-text file search to V1.3 (requires additional indexing infrastructure).

**Owner**: Winston (Architect)

---

### Q5: Should archived channels be deletable?

**Context**: Archived channels accumulate over time. Should users be able to delete old ceremony channels?

**Options**:
A. Archived channels are permanent (cannot delete)
B. Admin can delete archived channels after 90 days
C. User can delete any archived channel

**Recommendation**: Option A (permanent archive in V1.2). Defer deletion to V1.3 with proper confirmation flow and data retention policy.

**Owner**: John (Product Manager)

---

## Summary

Epic 39.8 has been **significantly expanded** from 14 points (4 stories) to **32 points (8 stories)** to deliver a comprehensive Slack-style unified chat interface. This expansion is **justified by the business value**: familiar UX, better agent interaction, context preservation, and ceremony transparency.

**Key Deliverables**:
1. Dual sidebar navigation (Primary + Secondary)
2. DMs section with all 8 agents and 1:1 conversations
3. Channels section for ceremony collaboration
4. Threading for focused sub-conversations
5. Message search across all DMs and channels
6. Channel archive and export

**Timeline Impact**: Phase 3 extends from 8 weeks to **8 weeks with compressed Epic 39.9 and 39.10** OR consider 10-week Phase 3 to maintain quality.

**Recommendation**: Approve expanded Epic 39.8 scope and adjust Phase 3 timeline OR defer Epic 39.9 (Customizable Layout) and Epic 39.10 (Advanced Metrics) to V1.3 release.

---

**Document Status**: Ready for Review
**Next Steps**:
1. Product Owner: Approve expanded scope and timeline adjustment
2. Sally: Create UX mockups for dual sidebar and thread panel
3. Winston: Review database schema for threading
4. Murat: Create test strategy for expanded epic
5. Bob: Schedule Sprint 13 planning (Stories 39.30-39.31)

**Last Updated**: 2025-01-17
**Version**: 1.0
