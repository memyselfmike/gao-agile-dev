# Epic 39: Web Interface - Complete Breakdown (ALL PHASES)

**Feature**: Browser-Based Web Interface for GAO-Dev
**Epic Number**: 39
**Scale Level**: 4 (Greenfield Significant Feature)
**Total Story Points**: 135 (across all 3 phases)
**Total Duration**: 28 weeks (7 months)
**Status**: Ready for Implementation

---

## Executive Summary

Epic 39 delivers a COMPLETE browser-based web interface transforming GAO-Dev from CLI-only to a rich "mission control center" for autonomous agent operations. This document covers the full implementation across three phases.

### Complete Feature List

**Phase 1 - MVP (10 weeks, 45 points)**:
1. FastAPI Backend - Web server + WebSocket
2. Brian Chat Component - Interactive chat with all 8 agents
3. Real-Time Activity Stream - Chronological agent activity feed
4. Files Tab - File tree + Monaco editor with commit enforcement
5. Basic Layout - Professional UI with shadcn/ui

**Phase 2 - V1.1 (10 weeks, 48 points)**:
6. Kanban Board - Visual project management with drag-and-drop
7. Workflow Visualization - Real-time workflow execution tracking
8. Git Timeline - Commit history with diff viewer
9. Provider Selection UI - Configure AI providers from web

**Phase 3 - V1.2 (8 weeks, 42 points)**:
10. Ceremony Channels - Slack-like interface for agent collaboration
11. Customizable Layout - Resizable panels with persistence
12. Advanced Metrics Dashboard - Analytics and performance visualization

### Epic Organization (10 Epics Total)

**Phase 1 - MVP**:
- **Epic 39.1: Backend Foundation** (3 stories, 8 points)
- **Epic 39.2: Frontend Foundation** (3 stories, 7 points)
- **Epic 39.3: Core Observability** (4 stories, 16 points)
- **Epic 39.4: File Management** (4 stories, 14 points)

**Phase 2 - V1.1**:
- **Epic 39.5: Kanban Board** (5 stories, 18 points)
- **Epic 39.6: Workflow Visualization** (3 stories, 13 points)
- **Epic 39.7: Git Integration & Provider UI** (5 stories, 17 points)

**Phase 3 - V1.2**:
- **Epic 39.8: Ceremony Channels** (4 stories, 14 points)
- **Epic 39.9: Customizable Layout & UX Polish** (3 stories, 10 points)
- **Epic 39.10: Advanced Metrics Dashboard** (5 stories, 18 points)

---

## Epic 39.1: Backend Foundation

**Effort**: 8 story points
**Duration**: 2 weeks
**Priority**: MUST HAVE (P0)
**Dependencies**: None

### Stories

| Story | Title | Estimate | Priority |
|-------|-------|----------|----------|
| **39.1** | FastAPI Web Server Setup | S (2 points) | P0 |
| **39.2** | WebSocket Manager and Event Bus | M (3 points) | P0 |
| **39.3** | Session Lock and Read-Only Mode | M (3 points) | P0 |

### Deliverables

- FastAPI server binding to localhost:3000
- WebSocket endpoint at /ws with session token auth
- asyncio.Queue event bus (1000+ events/second)
- Session lock mechanism (CLI write, web read-only)
- API middleware enforcing read-only mode
- Health check endpoint
- Graceful shutdown handling

### Success Criteria

- [ ] Server starts in <3 seconds
- [ ] WebSocket connection establishes in <100ms
- [ ] Event delivery latency <10ms
- [ ] Session lock prevents concurrent CLI/web writes
- [ ] Read-only mode enforced via middleware
- [ ] 100% integration test coverage

---

## Epic 39.2: Frontend Foundation

**Effort**: 7 story points
**Duration**: 1.5 weeks
**Priority**: MUST HAVE (P0)
**Dependencies**: Epic 39.1 (Backend Foundation)

### Stories

| Story | Title | Estimate | Priority |
|-------|-------|----------|----------|
| **39.4** | React + Vite + Zustand Setup | S (2 points) | P0 |
| **39.5** | Basic Layout with shadcn/ui | M (3 points) | P0 |
| **39.6** | Dark/Light Theme Support | S (2 points) | P0 |

### Deliverables

- React 18 + Vite build configuration
- Zustand state management setup
- Professional layout (top bar, sidebar, main content)
- Tab navigation (Chat, Activity, Files, Kanban, Git, Ceremonies)
- Dark/light theme with system preference detection
- shadcn/ui component integration
- WCAG 2.1 AA compliant UI

### Success Criteria

- [ ] Vite dev server starts in <2 seconds
- [ ] Production build completes in <30 seconds
- [ ] Page load time <2 seconds (Lighthouse TTI)
- [ ] Theme toggle works smoothly (<100ms)
- [ ] Keyboard navigation works for all tabs
- [ ] Lighthouse accessibility score >95/100

---

## Epic 39.3: Core Observability

**Effort**: 16 story points
**Duration**: 3.5 weeks
**Priority**: MUST HAVE (P0)
**Dependencies**: Epic 39.1 (Backend), Epic 39.2 (Frontend)

### Stories

| Story | Title | Estimate | Priority |
|-------|-------|----------|----------|
| **39.7** | Brian Chat Component (ChatREPL Integration) | L (5 points) | P0 |
| **39.8** | Multi-Agent Chat Switching | S (2 points) | P0 |
| **39.9** | Real-Time Activity Stream | L (5 points) | P0 |
| **39.10** | Activity Stream Filters and Search | M (4 points) | P0 |

### Deliverables

- Chat interface with text input and message history
- Streaming response support (chunks appear as agent types)
- Markdown rendering in messages
- Reasoning toggle (show/hide Claude's thinking)
- Agent switcher (Brian, Mary, John, Winston, Sally, Bob, Amelia, Murat)
- Per-agent chat history (separate contexts)
- Activity stream with virtual scrolling (10,000+ events)
- Progressive disclosure (shallow cards, expandable details)
- Time windows (1h, 6h, 24h, 7d, 30d, All)
- Event type filters (Workflow, Chat, File, State, Ceremony, Git)
- Agent filter and search

### Success Criteria

- [ ] Chat interface loads in <500ms
- [ ] Message send/receive latency <200ms
- [ ] Streaming chunks appear within 100ms
- [ ] Agent switching takes <100ms
- [ ] Activity stream renders 1,000 events in <200ms
- [ ] Virtual scrolling handles 10,000+ events without lag
- [ ] Filters apply in <50ms
- [ ] Search returns results in <100ms
- [ ] BrianWebAdapter correctly integrates with ChatREPL

---

## Epic 39.4: File Management

**Effort**: 14 story points
**Duration**: 3 weeks
**Priority**: MUST HAVE (P0)
**Dependencies**: Epic 39.1 (Backend), Epic 39.2 (Frontend), Epic 27 (GitIntegratedStateManager)

### Stories

| Story | Title | Estimate | Priority |
|-------|-------|----------|----------|
| **39.11** | File Tree Navigation Component | M (3 points) | P0 |
| **39.12** | Monaco Editor Integration (Read-Only) | M (4 points) | P0 |
| **39.13** | Real-Time File Updates from Agents | M (3 points) | P0 |
| **39.14** | Monaco Edit Mode with Commit Enforcement | M (4 points) | P0 |

### Deliverables

- File tree with hierarchical folder structure
- Only tracked directories shown (docs/, src/, gao_dev/, tests/)
- Respect .gitignore files
- Virtual scrolling for large file trees (500+ files)
- File icons by type
- Monaco editor for code viewing
- Syntax highlighting for 20+ languages
- Read-only mode when CLI holds lock
- Edit mode with commit message prompt
- Commit message validation (not empty, follows format)
- Atomic save: file write + DB update + git commit
- Document lifecycle validation enforced
- Real-time file updates from agent writes
- Highlight recently changed files (last 5 minutes)
- Editor instance pooling (max 10 open files)

### Success Criteria

- [ ] File tree loads 500+ files in <300ms
- [ ] Monaco editor loads 10,000-line files in <500ms
- [ ] Real-time updates appear within 100ms
- [ ] Commit enforcement works (all saves require commit message)
- [ ] GitIntegratedStateManager atomic operations succeed
- [ ] Document lifecycle validation prevents invalid edits
- [ ] Editor pooling prevents memory leaks
- [ ] Diff view shows changes vs last commit

---

## Implementation Roadmap

### Phase 1: Backend Foundation (Week 1-2)

**Sprint 1: Backend Core**
- Story 39.1: FastAPI Web Server Setup
- Story 39.2: WebSocket Manager and Event Bus
- Story 39.3: Session Lock and Read-Only Mode

**Milestone**: Backend infrastructure complete, API endpoints functional

---

### Phase 2: Frontend Foundation (Week 3-4)

**Sprint 2: Frontend Scaffolding**
- Story 39.4: React + Vite + Zustand Setup
- Story 39.5: Basic Layout with shadcn/ui
- Story 39.6: Dark/Light Theme Support

**Milestone**: Professional UI layout complete, ready for feature integration

---

### Phase 3: Core Observability (Week 5-7)

**Sprint 3: Chat Component**
- Story 39.7: Brian Chat Component (ChatREPL Integration)
- Story 39.8: Multi-Agent Chat Switching

**Sprint 4: Activity Stream**
- Story 39.9: Real-Time Activity Stream
- Story 39.10: Activity Stream Filters and Search

**Milestone**: Users can chat with agents and see real-time activity

---

### Phase 4: File Management (Week 8-10)

**Sprint 5: File Tree & Read-Only Editor**
- Story 39.11: File Tree Navigation Component
- Story 39.12: Monaco Editor Integration (Read-Only)
- Story 39.13: Real-Time File Updates from Agents

**Sprint 6: Edit Mode with Commit Enforcement**
- Story 39.14: Monaco Edit Mode with Commit Enforcement

**Milestone**: MVP Complete - Full web interface with all 5 MUST HAVE features

---

## Story Point Summary

### By Epic

| Epic | Stories | Points | Percentage |
|------|---------|--------|------------|
| **39.1: Backend Foundation** | 3 | 8 | 18% |
| **39.2: Frontend Foundation** | 3 | 7 | 16% |
| **39.3: Core Observability** | 4 | 16 | 35% |
| **39.4: File Management** | 4 | 14 | 31% |
| **TOTAL** | **14** | **45** | **100%** |

### By Size

| Size | Points Each | Count | Total Points |
|------|-------------|-------|--------------|
| S (Small) | 2 | 4 | 8 |
| M (Medium) | 3-4 | 7 | 24 |
| L (Large) | 5 | 3 | 13 |
| **TOTAL** | - | **14** | **45** |

### Effort Distribution

- **Backend**: 8 points (18%)
- **Frontend Infrastructure**: 7 points (16%)
- **Chat & Activity**: 16 points (35%)
- **File Management**: 14 points (31%)

---

## Dependencies and Integration Points

### Epic 30: Interactive Brian Chat Interface (ChatREPL)

**Integration Points**:
- Story 39.7: Reuses ChatSession instance (shared context)
- Story 39.7: BrianWebAdapter translates ChatSession events to WebSocket
- Story 39.8: All 8 agent prompts and configurations reused

**Critical**: DO NOT duplicate ChatREPL logic. All chat functionality must integrate with existing ChatSession.

### Epic 27: Git-Integrated Hybrid Wisdom

**Integration Points**:
- Story 39.14: ALL file operations through GitIntegratedStateManager
- Story 39.14: Atomic file+DB+git commits enforced
- Story 39.13: FileSystemWatcher detects agent file changes
- Future (V1.1): Kanban queries from .gao-dev/documents.db

**Critical**: DO NOT create separate state management. Web UI observes state, doesn't manage it.

### Epic 35: Interactive Provider Selection

**Integration Points**:
- Future (V1.1): Settings UI reads/writes .gao-dev/provider_preferences.yaml
- Reuse provider validation logic

### Epic 28: Ceremony-Driven Workflow Integration

**Integration Points**:
- Future (V1.2): CeremonyAdapter publishes messages to WebSocket
- Ceremony Channels tab activates when ceremony starts

### Epic 7.2: Workflow-Driven Core

**Integration Points**:
- Story 39.9: Activity stream subscribes to workflow events
- Workflow events: workflow.started, workflow.step_completed, workflow.finished

---

## Technical Decisions (FINAL)

All architectural decisions have been approved by Product Owner:

### 1. Mutual Exclusion Model

**Decision**: Read-only web while CLI active (Option B)

**Implementation**:
- CLI = Exclusive write access
- Web = Read-only observability mode when CLI holds lock
- Session lock file: .gao-dev/session.lock
- Middleware enforces read-only mode

### 2. Dark/Light Mode

**Decision**: Both modes in MVP (Option B)

**Implementation**:
- Respect `prefers-color-scheme` CSS media query
- User can override in settings
- Theme stored in localStorage

### 3. Event Bus Persistence

**Decision**: asyncio.Queue in-memory (Option A)

**Implementation**:
- No Redis dependency for MVP
- Simple, fast, sufficient for single-project
- Future: SQLite event log in V1.1 if needed

### 4. Technology Stack

**Frontend**:
- React 18 + Vite (NOT Next.js - simpler for SPA)
- Zustand (NOT Redux - lighter, simpler)
- shadcn/ui (Radix UI + Tailwind CSS)
- Monaco Editor (@monaco-editor/react, basic NOT monaco-vscode-api)

**Backend**:
- FastAPI (async, WebSocket native)
- uvicorn ASGI server
- asyncio.Queue event bus
- No socket.io (native WebSocket)

---

## Quality Standards

### Performance Targets (95th Percentile)

| Metric | Target | Story |
|--------|--------|-------|
| Page load time | <2 seconds | 39.4, 39.5 |
| WebSocket connection | <100ms | 39.2 |
| Event delivery | <10ms | 39.2 |
| Chat message latency | <200ms | 39.7 |
| Activity stream render | <200ms | 39.9 |
| File tree render | <300ms | 39.11 |
| Monaco editor load | <500ms | 39.12 |
| Filter application | <50ms | 39.10 |

### Accessibility (WCAG 2.1 AA)

- [ ] Color contrast: 4.5:1 for text, 3:1 for large text
- [ ] 100% keyboard accessible
- [ ] Screen reader support (VoiceOver, NVDA)
- [ ] Semantic HTML throughout
- [ ] ARIA labels for all interactive elements
- [ ] Focus visible indicators
- [ ] Lighthouse accessibility score >95/100

### AI Testability

- [ ] Semantic HTML (button, nav, main, not div onclick)
- [ ] Stable data-testid attributes on all interactive elements
- [ ] ARIA labels for context
- [ ] Clear state indicators (data-state="loading", "error", "success")
- [ ] Deterministic IDs (not random UUIDs)

---

## Release Criteria

All criteria must be met before MVP GA:

### Functional Completeness
- [ ] All 14 stories completed (39.1 - 39.14)
- [ ] All acceptance criteria met
- [ ] No P0 or P1 bugs

### Performance
- [ ] All performance targets met (see table above)
- [ ] Handle 10,000+ events, 500+ files, 10,000-line files
- [ ] Memory usage (8 hours): <500 MB
- [ ] CPU usage (idle): <5%

### Security
- [ ] WebSocket authentication implemented
- [ ] CORS restricted to localhost
- [ ] Path validation prevents directory traversal
- [ ] Input sanitization prevents injection
- [ ] Session lock prevents conflicts

### Accessibility
- [ ] WCAG 2.1 AA compliance verified
- [ ] axe-core tests pass (0 violations)
- [ ] Lighthouse accessibility score >95/100
- [ ] Screen reader testing complete
- [ ] Keyboard navigation: All features accessible

### Testing
- [ ] E2E test coverage >80%
- [ ] All critical user flows tested
- [ ] Cross-browser testing complete (Chrome, Firefox, Safari, Edge)
- [ ] 100% CLI tests pass (zero regressions)

### Documentation
- [ ] User guide complete
- [ ] Troubleshooting guide complete
- [ ] API documentation complete

---

## Next Steps

1. **Winston (Architect)**: Review epic breakdown ✅ (approval needed)
2. **Murat (Test Architect)**: Create test strategy for Epic 39
3. **Amelia (Developer)**: Begin implementation with Story 39.1
4. **Sally (UX Designer)**: Create wireframes/mockups for layout and components
5. **Bob (Scrum Master)**: Schedule sprint planning for Sprint 1 (Stories 39.1-39.3)

---

**Document Status**: Complete - Ready for Implementation
**Epic Owner**: Winston (Technical Architect)
**Scrum Master**: Bob
**Developer**: Amelia
**Tester**: Murat
**Designer**: Sally

**Last Updated**: 2025-11-16
**Version**: 1.0
