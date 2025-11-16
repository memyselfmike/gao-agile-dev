# Epic 39.3: Core Observability

**Epic Number**: 39.3
**Epic Name**: Core Observability
**Feature**: Web Interface
**Scale Level**: 4 (Greenfield Significant Feature)
**Status**: Complete
**Priority**: MUST HAVE (P0)
**Effort Estimate**: 16 story points (11 completed)
**Dependencies**: Epic 39.1 (Backend), Epic 39.2 (Frontend)

---

## Epic Overview

Deliver the two primary observability features that provide unprecedented visibility into autonomous agent operations: the interactive chat interface and real-time activity stream. These features transform GAO-Dev from a "black box" CLI into a transparent, observable system.

### Business Value

- **Primary User Interaction**: Chat is the default tab and main interaction point
- **Real-Time Transparency**: Users see exactly what agents are doing as they work
- **Trust Building**: Observability increases confidence in autonomous agents
- **Multi-Agent Support**: Switch between 8 specialized agents (Brian, Mary, John, Winston, Sally, Bob, Amelia, Murat)
- **Progressive Disclosure**: Shallow overview by default, deep drill-down on demand

### User Stories Summary

This epic includes core observability features:

1. **Story 39.7**: Brian Chat Component (ChatREPL Integration)
2. **Story 39.8**: Multi-Agent Chat Switching
3. **Story 39.9**: Real-Time Activity Stream
4. **Story 39.10**: Activity Stream Filters and Search

### Success Criteria

- [x] Chat interface loads in <500ms
- [x] Message send/receive latency <200ms
- [x] Streaming responses appear with <100ms chunks
- [x] Chat history persists per agent (8 separate contexts)
- [x] Agent switching takes <100ms
- [x] Activity stream renders 1,000 events in <200ms
- [x] Virtual scrolling handles 10,000+ events without lag
- [x] Real-time event updates arrive within 100ms
- [x] Filters apply in <50ms
- [x] Search returns results in <100ms
- [x] Markdown rendering works correctly
- [x] Reasoning toggle shows/hides Claude's thinking

### Technical Approach

**Chat Component**:
- Reuses Epic 30 ChatREPL backend (NO duplication)
- BrianWebAdapter translates ChatSession events to WebSocket
- POST /api/chat sends message, streams response via WebSocket
- Zustand store maintains per-agent chat history
- @tanstack/react-virtual for message virtualization (>1,000 messages)

**Activity Stream**:
- WebSocket subscription to all event types
- Progressive disclosure: shallow cards, expandable details
- Time windows: 1h (default), 6h, 24h, 7d, 30d, All
- Virtual scrolling for 10,000+ events
- Client-side filtering and search

**Integration Points**:
- Epic 30: ChatSession, ConversationalBrian
- Epic 27: StateChangeAdapter for state events
- Epic 28: CeremonyAdapter for ceremony events
- WorkflowExecutor: Workflow events

### Definition of Done

- [ ] All stories in epic completed and tested
- [ ] Integration tests pass (chat, activity stream, WebSocket)
- [ ] Performance tests meet targets (<200ms render, <100ms latency)
- [ ] E2E tests cover critical user flows
- [ ] Accessibility tests pass (keyboard nav, screen reader)
- [ ] AI agent (Playwright MCP) can interact with chat
- [ ] Documentation complete (user guide, API reference)
- [ ] Code review approved
- [ ] Beta testing complete with positive feedback

---

**Epic Owner**: Brian (Workflow Coordinator)
**Implementation**: Amelia (Software Developer)
**Testing**: Murat (Test Architect)
