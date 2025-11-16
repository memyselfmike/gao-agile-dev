# Story 39.10: Activity Stream Filters and Search

**Story Number**: 39.10
**Epic**: 39.3 - Core Observability
**Status**: Complete
**Priority**: MUST HAVE (P0)
**Effort**: M (Medium - 4 points)
**Dependencies**: Story 39.9 (Activity Stream)

## User Story
As a **user**, I want **to filter and search activity stream** so that **I can focus on specific agents, workflows, or events without information overload**.

## Acceptance Criteria
- [x] AC1: Event type filter: Workflow, Chat, File, State, Ceremony, Git (multi-select)
- [x] AC2: Agent filter: Filter by specific agent or "All agents"
- [x] AC3: Search within activity stream (fuzzy search)
- [x] AC4: Search returns results in <100ms
- [x] AC5: Filters apply in <50ms
- [x] AC6: Filter state persists in URL query params (shareable links)
- [x] AC7: "Clear filters" button resets all filters
- [x] AC8: Active filters displayed as chips/badges
- [x] AC9: Filter count badge shows number of active filters
- [x] AC10: Export filtered events to JSON/CSV
- [x] AC11: Keyboard shortcuts: Cmd+F for search, Cmd+Shift+F for filters

## Technical Context
**Implementation**: Client-side filtering for performance
**Search**: Fuzzy search library (fuse.js)
**Export**: JSON.stringify or CSV generation
