# Story 39.36: Message Search Across DMs and Channels

**Epic**: 39.8 - Unified Chat/Channels/DM Interface (Slack-Style)
**Story Points**: 3 (Medium)
**Priority**: P2 (Could Have - V1.2)
**Status**: Pending
**Assignee**: Amelia (Developer)

---

## User Story

> As a user, I want to search messages across all DMs and channels so that I can quickly find past discussions.

---

## Description

Implement message search functionality with filters for agent, date range, and message type (DM or channel).

---

## Acceptance Criteria

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

---

## API Integration

**Endpoint**: `GET /api/search/messages?q={query}&type={dm|channel|all}&agent={agent_name}&date_range={7d|30d|all}`

**Response**:
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

---

## Technical Notes

**Search Engine**: SQLite FTS5 (Full-Text Search) extension for efficient search

**Debouncing**: 300ms debounce to avoid excessive API calls

**Components**: `<SearchBar>` and `<SearchResults>` modal or slide-in panel

**State**: Zustand `searchQuery` and `searchResults`

---

## Dependencies

- Story 39.31: DMs Section
- Story 39.33: Channels Section

---

## Test Scenarios

1. **Happy path**: User searches "architecture", sees results from Winston DM and #retrospective channel
2. **Edge case**: User searches non-existent term, shows "No messages found"
3. **Performance**: Search completes in <500ms for 10,000+ messages
4. **Error**: API fails, show "Search failed [Retry]"

---

## Definition of Done

- [ ] Code complete and peer reviewed
- [ ] All acceptance criteria met
- [ ] SQLite FTS5 index created
- [ ] Unit tests written and passing
- [ ] Integration tests with search API written and passing
- [ ] E2E tests written and passing
- [ ] Search performance tested (<500ms for 10,000+ messages)
- [ ] Debouncing tested
- [ ] Keyboard shortcut tested (Cmd+K)
- [ ] Accessibility tested
- [ ] Component documented
- [ ] Merged to main branch

---

**Created**: 2025-01-17
**Last Updated**: 2025-01-17
