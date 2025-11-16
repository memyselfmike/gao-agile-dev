# Epic 39.5: Visual Project Management (Kanban Board)

**Epic Number**: 39.5
**Epic Name**: Kanban Board (Visual Project Management)
**Feature**: Web Interface
**Scale Level**: 4 (Greenfield Significant Feature)
**Status**: Planned
**Priority**: SHOULD HAVE (P1 - Phase 2)
**Effort Estimate**: 18 story points
**Dependencies**: Epic 39.1-39.4 (MVP complete), Epic 27 (GitIntegratedStateManager)

---

## Epic Overview

Deliver a drag-and-drop Kanban board for visual project management, enabling users to manage epic and story lifecycles through an intuitive interface. This epic provides the primary visual project management tool in GAO-Dev's web interface.

### Business Value

- **Visual Project Management**: Transform state management from CLI commands to intuitive drag-and-drop
- **Enhanced User Experience**: Familiar Kanban paradigm (Trello, Jira) lowers learning curve
- **Real-Time Collaboration**: Instant updates across all sessions via WebSocket
- **State Transparency**: Clear visualization of epic/story progress through development lifecycle

### User Stories Summary

This epic delivers complete Kanban board functionality:

1. **Story 39.15**: Kanban Board Layout and State Columns (M - 3 points)
2. **Story 39.16**: Epic and Story Card Components (M - 4 points)
3. **Story 39.17**: Drag-and-Drop State Transitions (L - 5 points)
4. **Story 39.18**: Kanban Filters and Search (M - 3 points)
5. **Story 39.19**: Virtual Scrolling for Large Boards (M - 3 points)

### Success Criteria

- [ ] Board displays all 5 state columns (Backlog, Ready, In Progress, In Review, Done)
- [ ] Epic cards show epic number, title, story count, status
- [ ] Story cards show story number, title, acceptance criteria count
- [ ] Drag-and-drop changes story state with confirmation
- [ ] Atomic state transitions (DB + git commit) succeed
- [ ] Real-time updates across all browser sessions (<100ms latency)
- [ ] Handles 1,000+ stories without performance degradation
- [ ] Filters and search return results in <50ms
- [ ] Virtual scrolling prevents DOM bloat
- [ ] Read-only mode disables drag, preserves viewing

### Technical Approach

**Technology Stack**:
- React DnD or dnd-kit for drag-and-drop
- @tanstack/react-virtual for virtual scrolling
- Zustand for Kanban state management
- WebSocket for real-time updates

**Integration Points**:
- Epic 27: GitIntegratedStateManager.transition_story()
- `.gao-dev/documents.db` for epic/story queries
- WebSocket event bus for state changes

**Architecture Pattern**:
- Optimistic UI updates with rollback on error
- Per-card loading states during transitions
- Operation queue for concurrent updates
- Confirmation modals prevent accidental state changes

### Performance Targets

| Metric | Target |
|--------|--------|
| Initial board render | <400ms (100 stories) |
| Drag start/end | <50ms |
| State transition | <500ms (DB + git + UI update) |
| Filter application | <50ms |
| Search results | <100ms |
| Virtual scroll frame rate | 60 FPS (no jank) |

### Definition of Done

- [ ] All stories in epic completed and tested
- [ ] Drag-and-drop works smoothly across all browsers
- [ ] State transitions are atomic (DB + git)
- [ ] Real-time updates work reliably
- [ ] Virtual scrolling handles 1,000+ stories
- [ ] Filters and search functional
- [ ] E2E tests cover all user flows
- [ ] Performance tests validate targets
- [ ] Accessibility tests pass (WCAG 2.1 AA)
- [ ] Code review approved
- [ ] Zero regressions

---

## User Personas and Use Cases

### Primary Persona: Sarah (Product Manager)

**Goal**: Manage epic and story lifecycle visually without CLI commands

**User Journey**:
1. Opens web interface, navigates to Kanban tab
2. Sees board with 5 state columns
3. Epic 5 has 3 stories in Backlog, 2 in Ready, 1 in Progress
4. Drags Story 5.4 from Backlog to Ready
5. Confirmation modal: "Move Story 5.4 to Ready?"
6. Confirms → Loading indicator on card
7. State transition succeeds (DB + git commit)
8. Card smoothly animates to Ready column
9. Git timeline shows new commit
10. Other browser sessions update instantly

### Secondary Persona: Alex (Senior Developer)

**Goal**: Monitor story progress while working

**User Journey**:
1. Opens Kanban board in second monitor
2. Filters to Epic 5 only
3. Sees 3 stories in Progress (being implemented)
4. Agent moves Story 5.1 to In Review (via CLI)
5. Kanban updates in real-time
6. Alex reviews story, drags to Done
7. Celebrates progress

---

## Technical Risks and Mitigations

### Risk 1: Concurrent Drag Operations
**Impact**: High - Race conditions, lost updates
**Mitigation**:
- Per-card operation locks
- Optimistic UI with rollback
- Clear error messaging

### Risk 2: Large Board Performance
**Impact**: Medium - Slow rendering, janky scrolling
**Mitigation**:
- Virtual scrolling (only render visible cards)
- Lazy loading of epic expansions
- Database query optimization

### Risk 3: WebSocket Disconnection During Drag
**Impact**: Medium - State inconsistency
**Mitigation**:
- Detect disconnect, show warning
- Block drags during disconnect
- Re-sync on reconnect

---

## Integration Requirements

### Epic 27: GitIntegratedStateManager

**Methods Used**:
- `transition_story(epic_num, story_num, new_state)` - Atomic state transition
- `get_epics()` - Query all epics
- `get_stories(epic_num)` - Query stories for epic

**Events Published**:
- `state.epic_created` - New epic added
- `state.story_created` - New story added
- `state.story_transitioned` - Story state changed

### Epic 39.2: WebSocket Event Bus

**Events Subscribed**:
- `state.story_transitioned` → Update card position
- `state.epic_created` → Add epic card
- `state.story_created` → Add story card

**Events Published**:
- `kanban.filter_changed` - User changed filter
- `kanban.story_clicked` - User clicked story (open detail modal)

---

## Testing Strategy

### Unit Tests
- Card component rendering
- Drag-and-drop handlers
- Filter logic
- Search functionality

### Integration Tests
- State transition API calls
- WebSocket event handling
- Database query correctness

### E2E Tests (Playwright)
1. **Drag story between columns**
   - Verify confirmation modal
   - Verify state transition
   - Verify git commit
   - Verify real-time update
2. **Filter by epic**
   - Verify cards filtered correctly
3. **Search stories**
   - Verify search results
4. **Read-only mode**
   - Verify drag disabled
   - Verify cards clickable

### Performance Tests
- Render 1,000 stories: <1 second
- Drag-and-drop latency: <50ms
- Filter application: <50ms

### Accessibility Tests
- Keyboard navigation (Tab, Enter, Escape)
- Screen reader announcements
- Focus management during drag
- ARIA labels for drag handles

---

**Epic Owner**: Winston (Technical Architect)
**Implementation**: Amelia (Software Developer)
**Testing**: Murat (Test Architect)
**Design**: Sally (UX Designer)
