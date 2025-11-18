# Story 39.31: DMs Section - Agent List and Conversation UI

**Epic**: 39.8 - Unified Chat/Channels/DM Interface (Slack-Style)
**Story Points**: 5 (Large)
**Priority**: P2 (Could Have - V1.2)
**Status**: Pending
**Assignee**: Amelia (Developer)

---

## User Story

> As a user, I want to see a list of all 8 agents with last message previews so that I can quickly find and resume conversations.

---

## Description

Implement Direct Messages section with list of all 8 GAO-Dev agents, last message previews, and ability to open 1:1 conversations.

---

## Acceptance Criteria

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

---

## API Integration

**Endpoint**: `GET /api/dms`

**Response**:
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

---

## Technical Notes

**Component**: `<DMList>` with `<DMItem>` children

**State Management**: Zustand `dmConversations` map

**Integration**: Reuse existing ChatSession logic from Epic 30 for conversation history

**Virtual Scrolling**: NOT needed (only 8 agents)

**WebSocket**: Subscribe to `dm.updated` events for real-time last message updates

---

## Dependencies

- Story 39.30: Dual Sidebar Navigation
- Epic 30: ChatREPL (ChatSession for conversation history)

---

## Test Scenarios

1. **Happy path**: Load DM list, see all 8 agents, click Brian, conversation loads
2. **Edge case**: Agent never chatted, shows "No messages yet"
3. **Real-time**: Agent sends message while DM list open, last message preview updates
4. **Error**: API fails, show error toast "Failed to load DMs [Retry]"

---

## Definition of Done

- [ ] Code complete and peer reviewed
- [ ] All acceptance criteria met
- [ ] Unit tests written and passing
- [ ] Integration tests with API written and passing
- [ ] E2E tests written and passing
- [ ] Real-time updates tested with WebSocket
- [ ] Accessibility tested (keyboard navigation, screen reader)
- [ ] Component documented
- [ ] Merged to main branch

---

**Created**: 2025-01-17
**Last Updated**: 2025-01-17
