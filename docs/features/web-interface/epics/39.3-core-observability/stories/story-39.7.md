# Story 39.7: Brian Chat Component (ChatREPL Integration)

**Story Number**: 39.7
**Epic**: 39.3 - Core Observability
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort**: L (Large - 5 points)
**Dependencies**: Story 39.2 (WebSocket), Story 39.4 (React setup), Epic 30 (ChatREPL)

## User Story
As a **user**, I want **to chat with Brian in the browser** so that **I can interact with GAO-Dev naturally without using the CLI**.

## Acceptance Criteria
- [ ] AC1: Chat input textarea with "Send" button
- [ ] AC2: Message history displays user and agent messages
- [ ] AC3: Streaming response support (chunks appear as agent types)
- [ ] AC4: Markdown rendering in agent messages (code blocks, lists, bold, italic)
- [ ] AC5: Reasoning toggle (show/hide Claude's thinking)
- [ ] AC6: Message timestamps (relative: "2 minutes ago")
- [ ] AC7: Auto-scroll to bottom on new message (with pause option)
- [ ] AC8: Message virtualization for >1,000 messages (@tanstack/react-virtual)
- [ ] AC9: "Send" button disabled during agent response
- [ ] AC10: Error handling with retry button
- [ ] AC11: WebSocket reconnection preserves chat state
- [ ] AC12: BrianWebAdapter translates ChatSession events to WebSocket

## Technical Context
**Integration**: Reuses Epic 30 ChatSession (NO duplication)
**Backend**: POST /api/chat sends message, streams via WebSocket
**Frontend**: Zustand chat store, virtual scrolling
**Adapter**: BrianWebAdapter (chat.message_sent, chat.message_received, chat.thinking_started)
