# Story 39.34: Message Threading Infrastructure

**Epic**: 39.8 - Unified Chat/Channels/DM Interface (Slack-Style)
**Story Points**: 4 (Medium)
**Priority**: P2 (Could Have - V1.2)
**Status**: Pending
**Assignee**: Amelia (Developer)

---

## User Story

> As a user, I want to reply to specific messages in threads so that I can have focused sub-conversations without cluttering the main stream.

---

## Description

Implement backend infrastructure for single-level message threading (parent message + threaded replies).

---

## Acceptance Criteria

**Database Schema**:
- [ ] `threads` table: `id`, `parent_message_id`, `created_at`
- [ ] `messages` table: Add `thread_id` (nullable), `reply_to_message_id` (nullable)
- [ ] Migration script for schema changes

**API Endpoints**:
- [ ] POST `/api/threads` - Create thread from parent message
  - Request: `{"parentMessageId": "msg-123", "conversationId": "brian", "conversationType": "dm"}`
  - Response: `{"threadId": "thread-456"}`
- [ ] GET `/api/threads/{thread_id}` - Fetch thread messages
  - Response: `{"parentMessage": {...}, "replies": [...]}`
- [ ] POST `/api/threads/{thread_id}/messages` - Reply in thread
  - Request: `{"content": "Thread reply text"}`

**WebSocket Events**:
- [ ] `thread.created` - New thread started
- [ ] `thread.reply` - New reply in thread
- [ ] `thread.updated` - Thread count updated on parent message

**Thread Count**:
- [ ] Parent message thread count updates when reply added
- [ ] Thread count persisted in `messages.thread_count` (denormalized for performance)

---

## Technical Notes

**Database**: Use existing `.gao-dev/documents.db` SQLite database

**Migration**: Add migration script for schema changes

**Performance**: Thread count denormalization avoids COUNT queries on every message render

**Constraint**: Single-level threading (replies in thread cannot have sub-threads)

---

## Dependencies

- Epic 27: GitIntegratedStateManager (database access)

---

## Test Scenarios

1. **Happy path**: User creates thread, sends reply, thread count updates
2. **Edge case**: Thread with 100+ replies, pagination works
3. **Error**: Database error, show "Failed to create thread [Retry]"

---

## Definition of Done

- [ ] Code complete and peer reviewed
- [ ] All acceptance criteria met
- [ ] Database schema migration applied successfully
- [ ] Unit tests written and passing
- [ ] Integration tests with database written and passing
- [ ] API endpoints tested
- [ ] WebSocket events tested
- [ ] Thread count updates tested
- [ ] Performance tested (thread operations <50ms)
- [ ] Documentation updated
- [ ] Merged to main branch

---

**Created**: 2025-01-17
**Last Updated**: 2025-01-17
