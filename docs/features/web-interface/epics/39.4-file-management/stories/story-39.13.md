# Story 39.13: Real-Time File Updates from Agents

**Story Number**: 39.13
**Epic**: 39.4 - File Management
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort**: M (Medium - 3 points)
**Dependencies**: Story 39.11 (File Tree), Story 39.12 (Monaco), Story 39.2 (WebSocket)

## User Story
As a **user**, I want **to see files created/modified by agents in real-time** so that **I can monitor agent work as it happens**.

## Acceptance Criteria
- [ ] AC1: FileSystemWatcher detects agent file changes (create, modify, delete)
- [ ] AC2: FileSystemAdapter emits events: file.created, file.modified, file.deleted
- [ ] AC3: File tree updates in real-time (<100ms latency)
- [ ] AC4: Highlight recently changed files (green indicator, last 5 minutes)
- [ ] AC5: Open file in Monaco refreshes when modified by agent
- [ ] AC6: Diff indicator shows changes vs last viewed version
- [ ] AC7: Toast notification: "Winston created ARCHITECTURE.md"
- [ ] AC8: Activity stream shows file events
- [ ] AC9: File events include metadata: agent, timestamp, operation type
- [ ] AC10: Graceful handling of deleted files (close tab if open)
- [ ] AC11: File tree respects .gitignore in real-time (new .gitignore entries)

## Technical Context
**Backend**: FileSystemWatcher monitors project directory
**Events**: file.created, file.modified, file.deleted via WebSocket
**Integration**: Epic 27 GitIntegratedStateManager for file operations
