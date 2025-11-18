# Story 39.37: Channel Archive and Export

**Epic**: 39.8 - Unified Chat/Channels/DM Interface (Slack-Style)
**Story Points**: 2 (Small)
**Priority**: P2 (Could Have - V1.2)
**Status**: Pending
**Assignee**: Amelia (Developer)

---

## User Story

> As a user, I want to archive ceremony channels after ceremonies end so that I can review past discussions without cluttering active channels.

---

## Description

Implement channel archive functionality (mark ceremony channels as read-only after ceremony ends) and export channel transcript to Markdown.

---

## Acceptance Criteria

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

---

## API Integration

**Endpoints**:
- `POST /api/channels/{channel_id}/archive` - Archive channel (manual)
- `GET /api/channels/{channel_id}/export` - Export transcript

**Response** (Export): Markdown file download

---

## Technical Notes

**Archive Status**: Stored in `channels.status` column ("active" | "archived")

**WebSocket**: Subscribe to `channel.archived` event

**Export**: Uses existing message data, formats to Markdown template

---

## Dependencies

- Story 39.33: Channels Section

---

## Test Scenarios

1. **Happy path**: Ceremony ends, channel auto-archived, user exports transcript
2. **Edge case**: Channel with 1,000+ messages, export completes in <5 seconds
3. **Error**: Export fails, show "Export failed [Retry]"

---

## Definition of Done

- [ ] Code complete and peer reviewed
- [ ] All acceptance criteria met
- [ ] Unit tests written and passing
- [ ] Integration tests with CeremonyOrchestrator written and passing
- [ ] E2E tests written and passing
- [ ] Auto-archive tested (ceremony completion triggers archive)
- [ ] Export tested with various message counts
- [ ] Markdown format validated
- [ ] Accessibility tested
- [ ] Component documented
- [ ] Merged to main branch

---

**Created**: 2025-01-17
**Last Updated**: 2025-01-17
