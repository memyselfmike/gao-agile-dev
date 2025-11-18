# Story 39.33: Channels Section - Ceremony Channels UI

**Epic**: 39.8 - Unified Chat/Channels/DM Interface (Slack-Style)
**Story Points**: 4 (Medium)
**Priority**: P2 (Could Have - V1.2)
**Status**: Pending
**Assignee**: Amelia (Developer)

---

## User Story

> As a user, I want to see ceremony channels so that I can observe multi-agent collaboration during sprint planning, retrospectives, etc.

---

## Description

Implement Channels section showing active and archived ceremony channels with multi-agent message streams.

---

## Acceptance Criteria

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

---

## API Integration

**Endpoints**:
- `GET /api/channels` - List channels
- `GET /api/channels/{channel_id}/messages` - Fetch channel messages
- `POST /api/channels/{channel_id}/messages` - Send message to channel

**Response** (GET /api/channels):
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

---

## Technical Notes

**Components**: `<ChannelList>` and `<ChannelView>`

**State**: Zustand `channels` array and `activeChannel` string

**Integration**: Epic 28 CeremonyOrchestrator via CeremonyAdapter

**WebSocket**: Subscribe to `channel.created`, `channel.message`, `channel.archived`

---

## Dependencies

- Story 39.30: Dual Sidebar Navigation
- Epic 28: CeremonyOrchestrator (ceremony event streaming)

---

## Test Scenarios

1. **Happy path**: Brian starts retrospective, #retrospective-epic-4 appears, user clicks, sees messages
2. **Edge case**: No active ceremonies, shows empty state
3. **Real-time**: Agent sends message in active channel, message appears
4. **Error**: API fails, show "Failed to load channels [Retry]"

---

## Definition of Done

- [ ] Code complete and peer reviewed
- [ ] All acceptance criteria met
- [ ] Unit tests written and passing
- [ ] Integration tests with CeremonyOrchestrator written and passing
- [ ] E2E tests written and passing
- [ ] Real-time channel creation tested
- [ ] User participation in channels tested
- [ ] Accessibility tested
- [ ] Component documented
- [ ] Merged to main branch

---

**Created**: 2025-01-17
**Last Updated**: 2025-01-17
