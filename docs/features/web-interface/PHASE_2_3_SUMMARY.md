# Epic 39: Phase 2 & Phase 3 - Complete Story Breakdown

**Document Purpose**: This document provides the COMPLETE breakdown of all Phase 2 and Phase 3 stories for Epic 39 (Web Interface). Use this as the single source of truth for creating all story files.

**Status**: Ready for Story Creation
**Created**: 2025-11-16
**Author**: Bob (Scrum Master)

---

## Overview

This breakdown adds **25 additional stories** (39.15-39.39) across **6 new epics** (39.5-39.10) to complete the full Web Interface feature.

**Total Addition**:
- Stories: 25 (on top of 14 MVP stories = 39 total)
- Story Points: 90 (on top of 45 MVP points = 135 total)
- Duration: 18 weeks (on top of 10 MVP weeks = 28 total)

---

## Phase 2: V1.1 (Stories 39.15-39.27) - 10 Weeks, 48 Points

### Epic 39.5: Kanban Board (Visual Project Management)
**Total**: 5 stories, 18 points

#### Story 39.15: Kanban Board Layout and State Columns
- **Estimate**: M (3 points)
- **Priority**: P1
- **Dependencies**: Epic 39.1-39.4 (MVP complete)
- **User Story**: As a user, I want to see a Kanban board with state columns so that I can visualize epic and story progress.
- **Acceptance Criteria** (12 ACs):
  1. Board displays 5 columns: Backlog, Ready, In Progress, In Review, Done
  2. Column headers show name and card count
  3. Columns are equal width and fill screen
  4. Empty column shows "No items" placeholder
  5. Columns scroll independently (virtual scrolling)
  6. Board responsive to window resize
  7. Column order cannot be changed (fixed workflow)
  8. Column visual style matches shadcn/ui theme
  9. Dark/light mode supported
  10. Keyboard navigation: Tab between columns, Arrow keys within
  11. Screen reader announces column names and counts
  12. data-testid="kanban-column-{state}" for each column

#### Story 39.16: Epic and Story Card Components
- **Estimate**: M (4 points)
- **Priority**: P1
- **Dependencies**: Story 39.15
- **User Story**: As a user, I want to see epic and story cards in Kanban columns so that I can understand what's in each state.
- **Acceptance Criteria** (12 ACs):
  1. Epic cards show: epic number, title, story count, status
  2. Story cards show: story number, title, AC count, assignee (if any)
  3. Cards have visual hierarchy (epic larger/bolder than stories)
  4. Cards display status color (backlog=gray, ready=blue, progress=yellow, review=purple, done=green)
  5. Click epic card to expand/collapse stories
  6. Click story card to open detail modal
  7. Cards show loading state during transitions
  8. Cards have hover effect (elevation shadow)
  9. Card avatars for assigned agents
  10. Truncate long titles with ellipsis, show full on hover
  11. Cards keyboard accessible (Enter to expand/open)
  12. data-testid="kanban-card-epic-{num}" and "kanban-card-story-{epic}.{story}"

#### Story 39.17: Drag-and-Drop State Transitions
- **Estimate**: L (5 points)
- **Priority**: P1
- **Dependencies**: Story 39.16, Epic 27 (GitIntegratedStateManager)
- **User Story**: As a user, I want to drag stories between columns so that I can change their state intuitively.
- **Acceptance Criteria** (12 ACs):
  1. Stories draggable to any column (epics NOT draggable)
  2. Drag handle visible on hover
  3. Card opacity 50% during drag
  4. Drop zones highlight on drag-over
  5. Invalid drops show error indicator
  6. Confirmation modal before state transition: "Move Story X.Y to [State]?"
  7. Modal shows: current state, new state, story title
  8. Confirm triggers atomic transition (DB + git commit)
  9. Loading spinner on card during transition
  10. Optimistic UI update, rollback on error
  11. WebSocket broadcasts state change to all sessions
  12. Read-only mode disables drag (cards still clickable)

#### Story 39.18: Kanban Filters and Search
- **Estimate**: M (3 points)
- **Priority**: P1
- **Dependencies**: Story 39.16
- **User Story**: As a user, I want to filter and search Kanban cards so that I can focus on specific work.
- **Acceptance Criteria** (10 ACs):
  1. Filter bar above board: Epic dropdown, Agent dropdown, Status checkboxes
  2. Epic filter: "All Epics" or specific epic
  3. Agent filter: "All Agents" or specific agent
  4. Status filter: Multi-select checkboxes (default: all checked)
  5. Search input: Real-time search by story title/description
  6. Filters apply immediately (<50ms)
  7. Search results highlight matching text
  8. Clear all filters button
  9. Filter state persists in URL query params
  10. Empty results show "No stories match filters" message

#### Story 39.19: Virtual Scrolling for Large Boards
- **Estimate**: M (3 points)
- **Priority**: P1
- **Dependencies**: Story 39.16
- **User Story**: As a user, I want the Kanban board to handle 1,000+ stories without lag so that I can manage large projects.
- **Acceptance Criteria** (8 ACs):
  1. Virtual scrolling per column using @tanstack/react-virtual
  2. Only render visible cards + buffer (10 above/below)
  3. Handle 1,000+ cards without performance degradation
  4. Scroll position preserved during state updates
  5. Smooth scrolling (60 FPS, no jank)
  6. Drag-and-drop works with virtual scrolling
  7. Memory usage stable (no leaks) after 1 hour usage
  8. Performance test: Render 1,000 cards <1 second

---

### Epic 39.6: Workflow Visualization
**Total**: 3 stories, 13 points

#### Story 39.20: Workflow List and Details View
- **Estimate**: M (4 points)
- **Priority**: P1
- **Dependencies**: Epic 39.1-39.4, Epic 7.2 (WorkflowExecutor)
- **User Story**: As a user, I want to see a list of active and recent workflows so that I can monitor multi-step operations.
- **Acceptance Criteria** (11 ACs):
  1. Workflow list shows: Name, agent, status, start time, current step
  2. Active workflows at top, recently completed below
  3. Status: Running (blue), Completed (green), Failed (red), Cancelled (gray)
  4. Click workflow to see detail panel
  5. Detail panel shows: All steps, current step highlighted, elapsed time
  6. Auto-refresh every 5 seconds
  7. Real-time updates via WebSocket
  8. Filter by status: All, Running, Completed, Failed
  9. Search by workflow name
  10. Virtual scrolling for >100 workflows
  11. Empty state: "No active workflows"

#### Story 39.21: Workflow Step Progress Tracking
- **Estimate**: M (4 points)
- **Priority**: P1
- **Dependencies**: Story 39.20
- **User Story**: As a user, I want to see step-by-step progress in workflows so that I can understand what's happening.
- **Acceptance Criteria** (10 ACs):
  1. Progress bar shows: Step X of Y (e.g., "Step 3 of 7")
  2. Step list with visual indicators: Completed (checkmark), Current (spinner), Pending (circle)
  3. Click step to see details: Agent, start time, duration, outputs
  4. Step details show: Tool calls, agent reasoning (if available)
  5. Estimated time remaining (based on average step duration)
  6. Real-time step updates (<100ms latency)
  7. Step errors shown inline with error message
  8. Long-running steps show elapsed time
  9. Completed workflows show total duration
  10. Export workflow log to JSON

#### Story 39.22: Workflow Controls (Pause/Resume/Cancel)
- **Estimate**: L (5 points)
- **Priority**: P1
- **Dependencies**: Story 39.21
- **User Story**: As a user, I want to pause, resume, or cancel workflows so that I can control long-running operations.
- **Acceptance Criteria** (12 ACs):
  1. Cancel button on workflow detail panel
  2. Confirmation modal: "Cancel workflow [Name]? This cannot be undone."
  3. Cancel triggers WorkflowExecutor.cancel()
  4. Workflow status changes to "Cancelled"
  5. Current step interrupted gracefully
  6. Partial results preserved
  7. Real-time cancellation feedback
  8. Read-only mode hides control buttons
  9. Error handling if cancellation fails
  10. Cancelled workflows archived, not deleted
  11. Pause/resume buttons (if workflow supports - may defer to V1.2)
  12. keyboard shortcuts: Esc to cancel confirmation

---

### Epic 39.7: Git Integration and Provider UI
**Total**: 5 stories, 17 points

#### Story 39.23: Git Timeline Commit History
- **Estimate**: M (4 points)
- **Priority**: P1
- **Dependencies**: Epic 39.1-39.4, Epic 27 (GitIntegratedStateManager)
- **User Story**: As a user, I want to see a chronological commit history so that I can track changes over time.
- **Acceptance Criteria** (11 ACs):
  1. Commit list shows: Message, author, timestamp, hash (short)
  2. Commit cards with author badge: Agent (blue robot icon) vs User (purple user icon)
  3. Commits ordered newest first (reverse chronological)
  4. Click commit to see diff view
  5. Real-time updates when new commits made
  6. Virtual scrolling for >10,000 commits
  7. Load more button for pagination (50 commits at a time)
  8. Timestamp format: Relative (< 7 days), absolute (>= 7 days)
  9. Commit hash clickable to copy
  10. Link to file in Files tab
  11. Empty state: "No commits yet"

#### Story 39.24: Monaco Diff Viewer for Commits
- **Estimate**: M (4 points)
- **Priority**: P1
- **Dependencies**: Story 39.23, Story 39.12 (Monaco editor)
- **User Story**: As a user, I want to see file diffs for commits so that I can review changes.
- **Acceptance Criteria** (10 ACs):
  1. Click commit opens diff panel
  2. List of changed files: Name, change type (added/modified/deleted), lines changed
  3. Click file to see diff in Monaco diff editor
  4. Diff view: Side-by-side (default) or unified (toggle)
  5. Syntax highlighting in diff
  6. Added lines green, deleted lines red, modified lines yellow
  7. Navigate between files (Next/Previous buttons)
  8. Handle binary files (show "Binary file changed" message)
  9. Large diffs (>1,000 lines) show warning, allow expand
  10. Keyboard shortcuts: N (next file), P (previous file), T (toggle view)

#### Story 39.25: Git Filters and Search
- **Estimate**: M (3 points)
- **Priority**: P1
- **Dependencies**: Story 39.23
- **User Story**: As a user, I want to filter and search commits so that I can find specific changes.
- **Acceptance Criteria** (9 ACs):
  1. Filter bar: Author dropdown (All, Agents only, User only, specific agent)
  2. Date range picker (Last 7 days, Last 30 days, Last 90 days, Custom)
  3. Search input: Search commit messages (real-time)
  4. Filters apply immediately (<50ms)
  5. Search highlights matching text
  6. Clear all filters button
  7. Filter state persists in URL query params
  8. Empty results: "No commits match filters"
  9. Filter count badge shows active filters

#### Story 39.26: Provider Selection Settings Panel
- **Estimate**: S (2 points)
- **Priority**: P1
- **Dependencies**: Epic 39.1-39.4, Epic 35 (Provider Selection)
- **User Story**: As a user, I want to select AI provider from the web UI so that I don't have to edit YAML files.
- **Acceptance Criteria** (8 ACs):
  1. Settings icon in top bar opens settings panel
  2. Provider dropdown: Claude Code, OpenCode, Ollama
  3. Model dropdown (filtered by provider)
  4. Current provider/model shown
  5. Save button prompts confirmation: "Change provider to [X]?"
  6. Cancel button closes panel without changes
  7. Settings panel accessible via keyboard (Tab, Enter, Esc)
  8. Dark/light mode supported

#### Story 39.27: Provider Validation and Persistence
- **Estimate**: M (4 points)
- **Priority**: P1
- **Dependencies**: Story 39.26
- **User Story**: As a user, I want provider changes validated and persisted so that my settings are saved correctly.
- **Acceptance Criteria** (10 ACs):
  1. Validation on save: Provider + model combination valid
  2. API key validation (if applicable) shows status: Valid (green check), Invalid (red X), Not configured (yellow warning)
  3. Save writes to `.gao-dev/provider_preferences.yaml`
  4. Atomic write (backup existing file, write new, delete backup)
  5. Success toast: "Provider changed to [X]"
  6. Error toast with fix suggestions: "Invalid API key. Check environment variable ANTHROPIC_API_KEY."
  7. File watcher emits `provider.changed` event
  8. Real-time validation during typing (debounced 500ms)
  9. Rollback on save failure
  10. Settings panel shows loading state during save

---

## Phase 3: V1.2 (Stories 39.28-39.39) - 8 Weeks, 42 Points

### Epic 39.8: Ceremony Channels
**Total**: 4 stories, 14 points

#### Story 39.28: Ceremony Channel UI Components
- **Estimate**: M (4 points)
- **Priority**: P2 (Could Have)
- **Dependencies**: Epic 39.1-39.7, Epic 28 (CeremonyOrchestrator)
- **User Story**: As a user, I want to see ceremony channels in a Slack-like interface so that I can observe agent collaboration.
- **Acceptance Criteria** (11 ACs):
  1. Ceremony Channels tab visible only when ceremony active
  2. Channel list sidebar: #planning, #retrospective, #sprint-review
  3. Active channel highlighted
  4. Channel shows unread count badge
  5. Click channel to switch
  6. Empty state: "No active ceremonies"
  7. Channel header shows: Ceremony name, participants, status (Active/Archived)
  8. Archive indicator for completed ceremonies (read-only)
  9. Dark/light mode supported
  10. Keyboard navigation: Tab to channels, Enter to select
  11. Screen reader announces channel switch

#### Story 39.29: Channel Message Stream and Rendering
- **Estimate**: M (4 points)
- **Priority**: P2
- **Dependencies**: Story 39.28
- **User Story**: As a user, I want to see real-time messages in ceremony channels so that I can follow agent discussions.
- **Acceptance Criteria** (11 ACs):
  1. Message stream shows: Agent avatar, name, timestamp, message
  2. Markdown rendering in messages (code blocks, lists, bold, italic)
  3. Agent colors distinct (Brian=blue, Mary=purple, John=green, etc.)
  4. Real-time message streaming via WebSocket (<100ms latency)
  5. Auto-scroll to bottom on new message (pause on manual scroll)
  6. Virtual scrolling for >1,000 messages
  7. Timestamp format: Time only (same day), date + time (different day)
  8. Message search within channel
  9. Copy message button
  10. Link detection and rendering
  11. Loading state while fetching history

#### Story 39.30: User Participation in Ceremonies
- **Estimate**: M (3 points)
- **Priority**: P2
- **Dependencies**: Story 39.29
- **User Story**: As a user, I want to post messages in ceremony channels so that I can participate in discussions.
- **Acceptance Criteria** (9 ACs):
  1. Message input textarea at bottom of channel
  2. Send button (Enter key or click)
  3. Message validation: Not empty, max 10,000 characters
  4. User messages visually distinct from agent messages (different color)
  5. Posting disabled in archived channels
  6. Read-only mode disables posting
  7. Error handling: Failed send shows retry button
  8. Message optimistic UI update, rollback on error
  9. Keyboard shortcuts: Cmd+Enter to send

#### Story 39.31: Channel Archive and Export
- **Estimate**: M (3 points)
- **Priority**: P2
- **Dependencies**: Story 39.29
- **User Story**: As a user, I want to export ceremony transcripts so that I can review discussions later.
- **Acceptance Criteria** (8 ACs):
  1. Export button in channel header
  2. Export formats: JSON, Markdown, Plain text
  3. Export includes: Channel name, ceremony type, participants, all messages (with timestamps)
  4. Export downloads as file
  5. Archived channels remain accessible (read-only)
  6. Archive list shows: Ceremony name, date, participant count
  7. Search across all archives
  8. Archive auto-created when ceremony ends

---

### Epic 39.9: Customizable Layout and UX Polish
**Total**: 3 stories, 10 points

#### Story 39.32: Resizable Panels Infrastructure
- **Estimate**: M (3 points)
- **Priority**: P2
- **Dependencies**: Epic 39.1-39.8
- **User Story**: As a user, I want to resize panels so that I can customize my workspace.
- **Acceptance Criteria** (9 ACs):
  1. Sidebar resizable (drag divider)
  2. File tree/editor split resizable
  3. Min/max width constraints (sidebar: 200-400px)
  4. Resize handle visible on hover
  5. Smooth resize (60 FPS, no jank)
  6. Double-click divider to reset to default
  7. Resize state auto-saved to localStorage
  8. Keyboard accessible: Focus divider, arrow keys to resize
  9. Touch support for resize (mobile, future-proofing)

#### Story 39.33: Layout Persistence and Presets
- **Estimate**: M (3 points)
- **Priority**: P2
- **Dependencies**: Story 39.32
- **User Story**: As a user, I want my layout preferences saved so that I don't have to reconfigure every session.
- **Acceptance Criteria** (8 ACs):
  1. Layout state persists to localStorage on change
  2. Layout restored on page load
  3. Reset to default layout button
  4. Layout presets: Compact, Balanced (default), Spacious
  5. Preset selector in settings panel
  6. Layout validation on load (handle schema changes gracefully)
  7. Invalid layout falls back to default
  8. Export/import layout config (JSON)

#### Story 39.34: Performance Optimization and Memory Management
- **Estimate**: M (4 points)
- **Priority**: P2
- **Dependencies**: All previous stories
- **User Story**: As a user, I want the web interface to remain performant after extended use so that I don't experience slowdowns.
- **Acceptance Criteria** (11 ACs):
  1. Memory usage <500MB after 8 hours usage
  2. Memory profiling tests pass (no leaks detected)
  3. Monaco editor instance pooling (max 10 open files)
  4. WebSocket event cleanup on disconnect
  5. React component cleanup on unmount
  6. Virtual scrolling prevents DOM bloat
  7. Image lazy loading
  8. Code splitting (dynamic imports for tabs)
  9. Service worker for offline functionality (optional)
  10. Performance monitoring dashboard (internal)
  11. Automated performance regression tests

---

### Epic 39.10: Advanced Metrics Dashboard
**Total**: 5 stories, 18 points

#### Story 39.35: Metrics Data Aggregation Service
- **Estimate**: M (4 points)
- **Priority**: P2
- **Dependencies**: Epic 39.1-39.9, Epic 27 (GitIntegratedStateManager)
- **User Story**: As a system, I need a metrics aggregation service so that the dashboard can display accurate data.
- **Acceptance Criteria** (10 ACs):
  1. Backend service queries `.gao-dev/documents.db` for state data
  2. Queries git history for commit metrics
  3. Aggregates story completion velocity (stories/week)
  4. Aggregates agent activity (commits/agent, tool calls/agent)
  5. Calculates workflow success rate
  6. Calculates test coverage trends (if test data available)
  7. Data cached for 5 minutes (avoid repeated queries)
  8. API endpoint: GET `/api/metrics` returns JSON
  9. Privacy-preserving (no external analytics)
  10. Metrics update on state changes

#### Story 39.36: Story Velocity and Agent Activity Charts
- **Estimate**: L (5 points)
- **Priority**: P2
- **Dependencies**: Story 39.35
- **User Story**: As a user, I want to see story velocity and agent activity charts so that I can understand project progress.
- **Acceptance Criteria** (12 ACs):
  1. Story velocity chart: Line chart, stories completed per week, last 12 weeks
  2. Agent activity heatmap: Commits per agent per day, last 30 days
  3. Chart library: Recharts (responsive, accessible)
  4. Charts responsive to window resize
  5. Tooltips on hover with details
  6. Legend with color coding
  7. Export chart data to CSV
  8. Empty state: "Not enough data to display chart"
  9. Loading state while fetching data
  10. Dark/light mode supported
  11. Keyboard accessible (Tab to interact)
  12. Screen reader announces chart data

#### Story 39.37: Workflow Success Rate Visualization
- **Estimate**: M (3 points)
- **Priority**: P2
- **Dependencies**: Story 39.35
- **User Story**: As a user, I want to see workflow success rates so that I can identify problematic workflows.
- **Acceptance Criteria** (9 ACs):
  1. Pie chart: Workflow outcomes (Completed, Failed, Cancelled)
  2. Bar chart: Success rate per workflow type
  3. Time range selector: Last 7 days, 30 days, 90 days, All time
  4. Click chart segment to filter workflow list
  5. Tooltips show count and percentage
  6. Export to CSV
  7. Empty state: "No workflows executed"
  8. Dark/light mode
  9. Accessible

#### Story 39.38: Test Coverage and Code Quality Metrics
- **Estimate**: M (3 points)
- **Priority**: P2
- **Dependencies**: Story 39.35
- **User Story**: As a user, I want to see test coverage trends so that I can ensure quality standards.
- **Acceptance Criteria** (9 ACs):
  1. Line chart: Test coverage % over time
  2. Metrics shown: Unit test coverage, integration test coverage, E2E coverage
  3. Current vs target coverage shown (target: 80%)
  4. Code quality metrics: Linting errors, type errors (if available)
  5. Time range selector
  6. Export to CSV
  7. Empty state: "Coverage data not available"
  8. Dark/light mode
  9. Accessible

#### Story 39.39: Metrics Export and Reporting
- **Estimate**: M (3 points)
- **Priority**: P2
- **Dependencies**: Stories 39.36-39.38
- **User Story**: As a user, I want to export metrics reports so that I can share with stakeholders.
- **Acceptance Criteria** (8 ACs):
  1. Export button in metrics dashboard
  2. Export formats: PDF, CSV, JSON
  3. PDF includes: All charts (as images), summary statistics, date range
  4. CSV includes: Raw data for all metrics
  5. JSON includes: Full metrics object
  6. Report metadata: Generated date, project name, date range
  7. Export downloads as file
  8. Export loading state (generation takes <5 seconds)

---

## Story Count and Point Summary

### Phase 2 (V1.1)

| Epic | Stories | Points |
|------|---------|--------|
| 39.5: Kanban Board | 5 | 18 |
| 39.6: Workflow Visualization | 3 | 13 |
| 39.7: Git & Provider UI | 5 | 17 |
| **Phase 2 Total** | **13** | **48** |

### Phase 3 (V1.2)

| Epic | Stories | Points |
|------|---------|--------|
| 39.8: Ceremony Channels | 4 | 14 |
| 39.9: Layout & Polish | 3 | 10 |
| 39.10: Advanced Metrics | 5 | 18 |
| **Phase 3 Total** | **12** | **42** |

### Grand Total (All Phases)

| Phase | Stories | Points | Weeks |
|-------|---------|--------|-------|
| Phase 1 (MVP) | 14 | 45 | 10 |
| Phase 2 (V1.1) | 13 | 48 | 10 |
| Phase 3 (V1.2) | 12 | 42 | 8 |
| **TOTAL** | **39** | **135** | **28** |

---

## Next Steps for Bob (Scrum Master)

**DELIVERABLE 1**: Create all epic README files (6 files)
- `docs/features/web-interface/epics/39.5-kanban-board/README.md` (DONE)
- `docs/features/web-interface/epics/39.6-workflow-visualization/README.md`
- `docs/features/web-interface/epics/39.7-git-integration-provider-ui/README.md`
- `docs/features/web-interface/epics/39.8-ceremony-channels/README.md`
- `docs/features/web-interface/epics/39.9-customizable-layout-ux-polish/README.md`
- `docs/features/web-interface/epics/39.10-advanced-metrics/README.md`

**DELIVERABLE 2**: Create all story files (25 files)
- Stories 39.15-39.19 (Epic 39.5)
- Stories 39.20-39.22 (Epic 39.6)
- Stories 39.23-39.27 (Epic 39.7)
- Stories 39.28-39.31 (Epic 39.8)
- Stories 39.32-39.34 (Epic 39.9)
- Stories 39.35-39.39 (Epic 39.10)

**DELIVERABLE 3**: Update index documents
- Update `STORY_INDEX.md` with all 39 stories
- Update `EPIC_BREAKDOWN.md` with all 10 epics (IN PROGRESS)

**Template**: Use existing story format (see story-39.7.md for reference)

---

**Document Status**: Complete - Ready for Story Creation
**Last Updated**: 2025-11-16
**Author**: Bob (Scrum Master)
