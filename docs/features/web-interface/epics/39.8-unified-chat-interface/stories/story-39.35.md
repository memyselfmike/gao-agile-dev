# Story 39.35: Thread Panel UI (Slide-In from Right)

**Epic**: 39.8 - Unified Chat/Channels/DM Interface (Slack-Style)
**Story Points**: 5 (Large)
**Priority**: P2 (Could Have - V1.2)
**Status**: Pending
**Assignee**: Amelia (Developer)

---

## User Story

> As a user, I want to see thread replies in a slide-in panel so that I can drill into specific discussions without losing my place in the main conversation.

---

## Description

Implement thread panel UI that slides in from right when user clicks "Reply in thread" or clicks thread count indicator.

---

## Acceptance Criteria

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

---

## Technical Notes

**Component**: `<ThreadPanel>` with slide-in animation

**Animation**: CSS transform or Framer Motion

**State**: Zustand `activeThread` (null when closed)

**Layout**: CSS Grid with main view and thread panel columns

**WebSocket**: Subscribe to `thread.reply` for real-time updates

---

## Dependencies

- Story 39.34: Message Threading Infrastructure
- Story 39.32: DM Conversation View (reuse message components)

---

## Test Scenarios

1. **Happy path**: User clicks "Reply in thread", panel slides in, user sends reply, reply appears
2. **Edge case**: User opens thread with 100+ replies, virtual scrolling works
3. **Real-time**: Agent replies in thread while panel open, reply appears
4. **Error**: API fails, show "Failed to load thread [Retry]"

---

## Definition of Done

- [ ] Code complete and peer reviewed
- [ ] All acceptance criteria met
- [ ] Unit tests written and passing
- [ ] E2E tests written and passing
- [ ] Animation tested (smooth 200ms slide-in)
- [ ] Real-time updates tested
- [ ] Virtual scrolling tested with >100 replies
- [ ] Keyboard navigation tested (Escape to close)
- [ ] Mobile responsiveness tested (<1024px: full-width modal)
- [ ] Accessibility tested
- [ ] Component documented
- [ ] Merged to main branch

---

**Created**: 2025-01-17
**Last Updated**: 2025-01-17
