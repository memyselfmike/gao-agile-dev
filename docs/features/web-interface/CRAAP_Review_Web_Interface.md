# CRAAP Review: Browser-Based Web Interface

**Review Date**: 2025-01-16
**Reviewer**: CRAAP Framework Analysis
**Documents Reviewed**:
- `docs/features/web-interface/VISION.md` (775 lines)
- `docs/features/web-interface/ARCHITECTURE.md` (1,500+ lines)

---

## Executive Summary

The Vision and Architecture documents for Epic 39 (Browser-Based Web Interface) are comprehensive, well-structured, and demonstrate thorough planning. However, this CRAAP review has identified **10 critical issues**, **15 moderate concerns**, and **8 minor improvements** that should be addressed before proceeding to PRD and implementation.

**Overall Health**: **B+ (Good, with important gaps to address)**

**Key Strengths**:
- Clear vision with dual human-AI interface focus
- Detailed technology stack decisions with rationale
- Comprehensive API specifications
- Strong integration strategy with existing epics

**Critical Gaps**:
- Missing test architecture and E2E testing strategy
- Underdefined error handling and edge case flows
- Potential memory leaks and performance issues not addressed
- Security vulnerabilities in WebSocket authentication
- Mutual exclusion decision may limit user flexibility

---

## CRAAP Analysis

### C - Critique and Refine

#### Identified Issues

**1. Mutual Exclusion Limitation (High Impact)**
- **Issue**: Decision to enforce CLI OR web (never both) significantly restricts power users
- **Impact**: Users cannot script with CLI while monitoring in web UI - a common use case for "mission control"
- **Vague Rationale**: "Simplifies state synchronization" but actually still requires session locking, PID validation, cleanup
- **Recommendation**: Reconsider to allow **read-only web observability** while CLI is active
  - Web UI cannot send commands, only observe
  - Simpler than full bidirectional, still provides "mission control" value

**2. Agent Chat History Management Undefined (Medium Impact)**
- **Issue**: Vision mentions multi-agent switching, but architecture doesn't specify how chat history is managed
- **Questions**:
  - Separate chat history per agent (Brian vs Mary)?
  - Merged history with agent tags?
  - How to switch context without losing history?
  - What's the maximum history size before pagination kicks in?
- **Recommendation**: Define ChatHistory data model with per-agent partitioning

**3. Test Architecture Completely Missing (High Impact)**
- **Issue**: No mention of test setup, E2E testing strategy, or how to test adapter layer
- **Missing**:
  - How to test WebSocket integration?
  - How to test adapter layer (BrianWebAdapter, StateChangeAdapter)?
  - How to run Playwright tests (the whole AI testing vision!)?
  - How to mock ChatSession, GitIntegratedStateManager in tests?
- **Recommendation**: Add dedicated "Testing Architecture" section with:
  - Unit testing strategy (Jest/Vitest for frontend, pytest for backend)
  - Integration testing (adapter layer)
  - E2E testing (Playwright with MCP integration plan)
  - Test data management

**4. Error Handling Strategy Underspecified (Medium Impact)**
- **Issue**: Limited detail on how backend errors should surface in UI
- **Missing**:
  - Error boundary strategy for React
  - Toast notification vs modal for different error types
  - Retry logic for failed API calls
  - Error logging and reporting
- **Recommendation**: Define error handling taxonomy and UI patterns

**5. Session Recovery UX Not Detailed (Medium Impact)**
- **Issue**: Mentions `.gao-dev/last_session_history.json` but doesn't detail what persists or recovery UX
- **Questions**:
  - What gets persisted? (open files, chat history, active tab, scroll positions?)
  - When does recovery trigger? (browser refresh, crash, intentional restart?)
  - Does user see "Restore session?" prompt or automatic?
- **Recommendation**: Define session persistence schema and recovery UX flow

**6. Scalability Thresholds Undefined (Low Impact)**
- **Issue**: "Design for production scale" but no definition of when to warn or optimize
- **Missing**:
  - At what event count should activity stream warn "showing last 10,000 events, some hidden"?
  - At what file count should file tree warn "large project, search recommended"?
  - Memory usage thresholds for warnings?
- **Recommendation**: Define scalability guardrails and warning thresholds

**7. Browser Compatibility Not Specified (Low Impact)**
- **Issue**: Says "modern browsers" without minimum versions
- **Impact**: Unclear what to test, potential support burden
- **Recommendation**: Define browser test matrix:
  - Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
  - Explicitly exclude IE11

**8. Vague Implementation Details**
- **Monaco editor pooling**: Mentioned 5+ times but never detailed (pool size? disposal logic?)
- **Virtual scrolling configuration**: Uses @tanstack/react-virtual but no config (overscan, estimateSize, etc.)
- **Event buffering and time windows**: How do buffered events (last 100) interact with time windows (1 hour)? Do buffered events get filtered or always shown?
- **Agent avatars**: Decided on "agent-specific icons" but no design direction
- **Recommendation**: Add implementation specifications section or defer to stories

#### Redundancies

1. **Event types listed in both documents**: VISION.md and ARCHITECTURE.md both list event types - architecture should be single source
2. **Technology stack repeated**: Executive summary + detailed section
3. **Integration requirements duplicated**: Listed in both vision and architecture

**Recommendation**: Cross-reference between documents instead of duplicating

#### Opportunities for Improvement

1. **Add Migration Plan**: How do existing GAO-Dev users adopt web interface? Training? Feature tour?
2. **Add Monitoring/Observability for Web Server**: How to monitor the server itself? Logs? Metrics? Health checks?
3. **Add Internationalization Plan**: Even if MVP is English-only, should architecture support i18n hooks?
4. **Add Analytics/Telemetry Plan**: How to track which features are used most? (Privacy-preserving)
5. **Add Plugin Extension Points**: Where can plugins hook into web UI?

---

### R - Risk Potential and Unforeseen Issues

#### Critical Risks Not Addressed

**1. Large Chat History Memory Leak (HIGH SEVERITY)**
- **Risk**: Chat history persisted in Zustand with no limit
- **Scenario**: User has 10,000-message conversation over weeks
- **Consequence**: Browser memory exhaustion, tab crash
- **Blind Spot**: No mention of chat history pagination or archival
- **Mitigation**: Implement message virtualization + archive old messages to indexedDB

**2. WebSocket Message Order Guarantees (MEDIUM SEVERITY)**
- **Risk**: asyncio.Queue with multiple subscribers doesn't guarantee order across event types
- **Scenario**: `file.created` arrives before `agent.activated` due to async processing
- **Consequence**: UI shows file creation before showing "Amelia is working..."
- **Blind Spot**: No sequence numbers or correlation IDs mentioned
- **Mitigation**: Add sequence numbers to all events + client-side reordering buffer

**3. Monaco Editor Concurrent Edits (HIGH SEVERITY)**
- **Risk**: User edits file in Monaco while agent modifies same file
- **Scenario**: User typing in `src/auth.py`, Amelia writes to same file
- **Consequence**: Conflicting edits, lost work, unclear which version wins
- **Blind Spot**: No file locking or conflict resolution UI
- **Mitigation**: File-level operation locking + diff UI for conflicts

**4. Kanban Drag-and-Drop Race Conditions (MEDIUM SEVERITY)**
- **Risk**: Optimistic update + slow API call (5s git commit) = confusing UI
- **Scenario**: User drags 3 cards rapidly, each triggers git commit, operations pile up
- **Consequence**: UI shows moved cards but backend still processing, unclear state
- **Blind Spot**: No loading indicators per card, no operation queue visualization
- **Mitigation**: Per-card loading state + operation queue with cancel option

**5. Browser Tab Sleep/Throttling (MEDIUM SEVERITY)**
- **Risk**: Modern browsers throttle background tabs
- **Scenario**: User switches to different tab for >5 minutes, browser suspends WebSocket
- **Consequence**: Connection drops, events missed, user thinks system frozen
- **Blind Spot**: No Page Visibility API handling
- **Mitigation**: Detect tab visibility + reconnect on focus + show "missed events" notification

**6. Git Merge Conflicts Outside GAO-Dev (MEDIUM SEVERITY)**
- **Risk**: User creates merge conflict in external git client
- **Scenario**: User pulls from remote, gets conflict in `.gao-dev/documents.db`
- **Consequence**: GitIntegratedStateManager fails, unclear error
- **Blind Spot**: No merge conflict detection or resolution UI
- **Mitigation**: Detect git conflicts + show resolution UI with "resolve manually" instructions

**7. Cross-Site WebSocket Hijacking (HIGH SEVERITY - SECURITY)**
- **Risk**: No authentication token for WebSocket upgrade
- **Scenario**: Malicious website opens WebSocket to ws://localhost:3000/ws
- **Consequence**: Malicious site can read all events (file contents, chat messages)
- **Blind Spot**: Architecture mentions CORS for HTTP but not WebSocket origin validation
- **Mitigation**: Generate session token on server start + require in WebSocket upgrade header + validate origin

**8. Event Bus Memory Growth (MEDIUM SEVERITY)**
- **Risk**: Event buffering with 1000-event queue, but what if no clients?
- **Scenario**: Server running, no browser connected, events accumulate
- **Consequence**: Server memory grows unbounded
- **Blind Spot**: Buffer cleanup not mentioned
- **Mitigation**: Clear buffer when last subscriber disconnects

**9. Provider Configuration Mismatch (LOW SEVERITY)**
- **Risk**: User changes provider in CLI, web UI doesn't update
- **Scenario**: Web UI caches provider as "OpenCode", user switches to "Claude" in CLI
- **Consequence**: Wrong model used for web requests
- **Blind Spot**: No file watcher on `.gao-dev/provider_preferences.yaml`
- **Mitigation**: Add file watcher + emit `provider.changed` event

**10. Vite Dev vs Production Build Mismatch (LOW SEVERITY)**
- **Risk**: Dev server behavior differs from production build
- **Scenario**: Feature works in `npm run dev` but fails in production build
- **Consequence**: Bugs discovered only in production
- **Blind Spot**: No pre-deploy testing mentioned
- **Mitigation**: Require production build testing before releases

#### Missing Risk Categories

**1. Data Integrity Risks**
- What if `.gao-dev/documents.db` gets corrupted?
- What if git repo is in detached HEAD state?
- What if session.lock file has stale PID?

**2. Network Risks**
- What if localhost DNS fails (rare but happens)?
- What if port 3000 already in use?
- What if firewall blocks localhost connections?

**3. Resource Exhaustion**
- What if project has 100,000 files?
- What if single workflow creates 1,000 events per second?
- What if commit history is 10,000 commits?

**Recommendation**: Add "Risk Register" section with comprehensive risk list + likelihood/impact scoring

---

### A - Analyse Flow / Dependencies

#### Dependency Issues

**1. Circular Dependency Potential (CRITICAL)**
```
FileSystemWatcher → EventBus → WebSocket
    ↓                              ↓
GitIntegratedStateManager ← StateChangeAdapter
    ↓
File Write → FileSystemWatcher (LOOP!)
```
- **Risk**: Infinite loop if file write triggers watcher, which emits event, which triggers adapter, which writes file again
- **Mitigation Missing**: Event deduplication logic, ignore events for self-triggered operations
- **Recommendation**: Add `source` field to events ("agent" | "user" | "self") + filter self-triggered

**2. Tight Coupling in BrianWebAdapter (MEDIUM)**
- **Issue**: Adapter accesses `ChatSession.context.current_agent` directly
- **Problem**: If ChatSession internals change, adapter breaks
- **Better Approach**: ChatSession should provide `get_active_agent()` and `switch_agent()` public API
- **Recommendation**: Define ChatSession API contract before implementation

**3. Missing Dependency Version Specifications (MEDIUM)**
- **Issue**: "Reuse Epic 30 ChatREPL" but no version/commit specified
- **Problem**: If Epic 30 changes, web interface might break unexpectedly
- **Recommendation**: Pin dependency versions OR define interface contracts with semantic versioning

**4. Initialization Order Not Explicit (LOW)**
- **Issue**: `app.py` startup mentions FileSystemWatcher, but when is EventBus initialized?
- **Problem**: Potential race condition if adapter publishes before EventBus ready
- **Recommendation**: Explicit startup ordering:
  1. EventBus
  2. WebSocketManager
  3. Adapters (subscribe to EventBus)
  4. FileSystemWatcher (publishes to EventBus)

#### Flow Improvements

**1. File Save Flow - Validation Before Commit Message (MEDIUM)**
- **Current**: User saves → Commit message prompt → Validate → Commit
- **Problem**: If validation fails after user writes commit message, they wasted effort
- **Better**: Validate → Commit message prompt → Commit
- **Recommendation**: Reorder flow for better UX

**2. Agent Switching Flow - Handle In-Progress Workflows (MEDIUM)**
- **Current**: User switches agent → New chat context
- **Missing**: What happens to in-progress workflows? Cancel? Continue in background?
- **Problem**: User confusion, potential data loss
- **Recommendation**: Prompt "Workflow in progress, switch anyway? [Yes] [Wait]"

**3. Ceremony Channels Activation - Event Not Specified (LOW)**
- **Current**: "Tab becomes visible when ceremony starts"
- **Missing**: How does frontend know? Poll? Event?
- **Recommendation**: Explicit `ceremony.started` event with ceremony_id + tab activation logic

**4. Error Recovery Flows - Completely Missing (HIGH)**
- **Missing Flows**:
  - What if API call fails? Show error + retry button?
  - What if WebSocket reconnect fails 10 times? Show "Offline mode"?
  - What if git commit fails? Rollback UI state + show error?
- **Recommendation**: Define error recovery flows for all operations

---

### A - Alignment with Goal

#### Goal Alignment Issues

**1. Mutual Exclusion vs "Mission Control" Vision (HIGH MISALIGNMENT)**
- **Vision**: "Mini VS Code in browser, mission control center for watching agents"
- **Decision**: Cannot use CLI and web simultaneously
- **Misalignment**: "Mission control" implies observability while work happens elsewhere (CLI)
- **Problem**: Power users want to script with CLI while monitoring in web
- **Recommendation**: Allow **simultaneous read-only web** while CLI active
  - Web UI can observe, cannot send commands
  - Simple mutex: "CLI has write lock, web is read-only"

**2. AI Testing vs Human UX Priority (MEDIUM MISALIGNMENT)**
- **Vision**: "Dual human-AI interface" (equal priority)
- **Architecture**: Optimizes for human UX (animations, virtual scrolling, smooth transitions)
- **Missing**: AI testing considerations (test mode? disable animations for speed? expose test IDs?)
- **Problem**: AI agent tests might be slow due to animations, hard to debug without test IDs everywhere
- **Recommendation**: Add "test mode" environment variable:
  - `GAO_DEV_TEST_MODE=true`: Disable animations, add data-testid to all elements, deterministic IDs

**3. "Build on Foundation" vs New Dependencies (LOW OBSERVATION)**
- **Vision**: "Reuse, don't rebuild" - emphasizes integration with existing
- **Architecture**: Adds React, Vite, shadcn/ui, Monaco, Zustand, Tailwind, @tanstack/react-virtual (6+ major frontend deps)
- **Observation**: Frontend is entirely new (expected), but is this "reuse"?
- **Clarification Needed**: Does "reuse" only apply to backend? Or should vision acknowledge frontend is greenfield?
- **Recommendation**: Update vision to clarify "Reuse backend, new frontend built on modern stack"

#### Missing from Goal

**1. Architecture Success Criteria Undefined (MEDIUM)**
- **Vision**: Clear success criteria (adoption %, performance, crashes)
- **Architecture**: No architecture-specific success metrics
- **Missing**:
  - Bundle size targets (< 500KB gzipped?)
  - API response time targets (< 50ms?)
  - WebSocket message throughput (> 100 events/second?)
- **Recommendation**: Add architecture-level KPIs

**2. Incremental Value Delivery Missing (MEDIUM)**
- **Vision**: Mentions "gradual rollout"
- **Architecture**: Doesn't break down MVP vs V1.1 feature delivery
- **Missing**:
  - Which tabs ship first? (Chat + Activity Stream = MVP, others V1.1?)
  - Can Monaco editor be deferred? (File tree with preview-only?)
- **Recommendation**: Define phased delivery:
  - **MVP**: Chat + Activity Stream + basic file tree (read-only)
  - **V1.1**: Kanban + Monaco editing + Git timeline
  - **V1.2**: Ceremony Channels + advanced features

**3. Backward Compatibility Not Addressed (LOW)**
- **Missing**: Does web interface work with existing `.gao-dev` projects?
- **Missing**: Migration path from CLI-only usage
- **Recommendation**: Define backward compatibility guarantees

---

### P - Perspective (Critical Outsider View)

#### Challenging Assumptions

**1. "Mutual exclusion simplifies everything"**
- **Assumption**: Enforcing CLI OR web reduces complexity
- **Challenge**: Still need session locking, PID validation, stale lock cleanup - not that much simpler
- **Alternative**: Allow simultaneous with read-only web observability
  - Not much more complex (just add read/write mode flag)
  - Provides significant value ("mission control while scripting")
- **Recommendation**: Reconsider this decision

**2. "asyncio.Queue sufficient for event bus"**
- **Assumption**: In-memory queue meets all needs
- **Challenge**: What if we want event history replay? What if multiple servers (future Docker multi-container)?
- **Alternative**: SQLite event log
  - Persistent (survives server restart)
  - Queryable (can replay last N events)
  - Already using SQLite for state, minimal new dependency
- **Recommendation**: Consider SQLite event log for persistence + queryability

**3. "Vite is simpler than Next.js"**
- **Assumption**: Vite is simpler for single-page app
- **Challenge**: Next.js provides routing, API routes, optimized builds, image optimization out-of-box
- **Alternative**: Next.js Pages Router (simpler than App Router, still provides structure)
- **Observation**: Vite is fine, but rationale "Next.js is overkill" undersells Next.js benefits
- **Recommendation**: Keep Vite, but acknowledge trade-offs (no routing, no API routes, manual optimization)

**4. "Dark mode only for MVP"**
- **Assumption**: Defer light mode to V1.1 to ship faster
- **Challenge**: Most developers work at night, dark mode is MVP for many
- **Alternative**: Respect system preference from day 1 (CSS prefers-color-scheme, ~20 lines)
- **Recommendation**: Bump light mode support to MVP (low effort, high value)

**5. "Localhost-only is secure"**
- **Assumption**: Localhost means trusted environment
- **Challenge**: Malicious Chrome extensions can access localhost, malicious websites can try CSRF
- **Alternative**: Generate random session token on startup, require in all requests
- **Recommendation**: Add session token auth even for localhost (defense in depth)

**6. "WebSocket is necessary"**
- **Assumption**: Need WebSocket for real-time bidirectional communication
- **Challenge**: For localhost, Server-Sent Events (SSE) might be simpler
  - SSE: Server-to-client streaming (perfect for events)
  - REST: Client-to-server (commands)
  - SSE has auto-reconnect built-in, simpler protocol
- **Alternative**: SSE for events + REST for commands
- **Observation**: WebSocket is fine, but SSE worth mentioning as simpler alternative

#### Alternative Approaches Not Considered

**1. Desktop App (Electron/Tauri)**
- **Pros**:
  - True native experience
  - No browser limitations (file access, system tray, etc.)
  - Can bundle Python backend as executable
  - Better for long-running workflows
- **Cons**:
  - Larger distribution size (~100MB vs ~5MB)
  - Platform-specific builds (Windows, macOS, Linux)
  - More complex deployment
- **Why Not Mentioned**: Probably out of scope, but worth documenting rejection rationale
- **Recommendation**: Add to "Alternatives Considered and Rejected" section

**2. Progressive Web App (PWA)**
- **Pros**:
  - Installable (feels native)
  - Works offline (cached assets)
  - Push notifications
- **Cons**:
  - Localhost-only means no PWA benefits (can't install from localhost)
  - Browser sandbox limitations
- **Why Not Mentioned**: Localhost constraint makes PWA moot
- **Recommendation**: Mention as future consideration if remote deployment happens

**3. Rich Terminal UI (Textual/Rich)**
- **Pros**:
  - Stays in terminal (developer-friendly)
  - Lighter than web browser
  - Works over SSH
  - Still provides rich UI (panels, tables, live updating)
- **Cons**:
  - Limited by terminal capabilities (no mouse in all terminals)
  - Less accessible than web
- **Why Not Mentioned**: "Web interface" in requirements, but TUI could complement CLI
- **Recommendation**: Consider TUI as middle ground for power users

**4. Hybrid: CLI with Read-Only Web Dashboard**
- **Pros**:
  - CLI remains primary interface (scripting, speed)
  - Web is pure observability dashboard (mission control)
  - No mutual exclusion needed (web is read-only)
  - Simpler than full bidirectional web
- **Cons**:
  - Can't send commands from web (but is that needed for "mission control"?)
- **Why Not Mentioned**: Seems like excellent middle ground!
- **Recommendation**: Seriously consider this as alternative to full-featured web interface

---

## Priority Issues

### Critical (Must Fix Before Implementation)

1. **[CRAAP-001] Add WebSocket Authentication (Security)**
   - Generate session token on startup
   - Require token in WebSocket upgrade header
   - Validate origin to prevent CSRF
   - **Owner**: Winston (Architect) → Security Architecture section

2. **[CRAAP-002] Define Test Architecture (Quality)**
   - Unit testing strategy (frontend + backend)
   - Integration testing (adapter layer)
   - E2E testing with Playwright MCP
   - Test data management
   - **Owner**: Murat (Test Architect) → New document or architecture section

3. **[CRAAP-003] Add Chat History Pagination (Performance)**
   - Virtualize chat messages (don't render all 10,000)
   - Archive old messages to indexedDB
   - Load more on scroll
   - **Owner**: Winston → Frontend Architecture

4. **[CRAAP-004] Resolve Circular Dependency Risk (Architecture)**
   - Add event deduplication in FileSystemWatcher
   - Add `source` field to events ("agent" | "user" | "self")
   - Filter self-triggered events
   - **Owner**: Winston → Event-Driven Architecture section

5. **[CRAAP-005] Define File Locking for Monaco Editor (Architecture)**
   - Implement file-level operation locking
   - Add conflict resolution UI (show diff, choose version)
   - Prevent simultaneous edits by user + agent
   - **Owner**: Winston → Integration Architecture

6. **[CRAAP-006] Reconsider Mutual Exclusion Decision (Architecture)**
   - Evaluate **read-only web while CLI active** option
   - If keeping mutual exclusion, add strong rationale
   - If changing, update architecture
   - **Owner**: Product Owner + Winston (joint decision)

7. **[CRAAP-007] Add Error Handling Strategy (Architecture)**
   - Define error boundary strategy (React)
   - Toast vs modal for different error types
   - Retry logic for failed API calls
   - Error recovery flows
   - **Owner**: Winston → New section

### Moderate (Should Fix Soon)

8. **[CRAAP-008] Define Chat History Management (Architecture)**
   - Specify per-agent chat history partitioning
   - Define history size limits
   - Pagination strategy
   - **Owner**: Winston → Backend Architecture

9. **[CRAAP-009] Add Sequence Numbers to Events (Architecture)**
   - Prevent out-of-order event display
   - Add correlation IDs for related events
   - Client-side reordering buffer
   - **Owner**: Winston → Event Schema

10. **[CRAAP-010] Add Page Visibility API Handling (Architecture)**
    - Detect tab backgrounding
    - Reconnect on focus
    - Show "missed events" notification
    - **Owner**: Winston → WebSocket Protocol

11. **[CRAAP-011] Define Session Recovery UX (Architecture)**
    - Specify what persists to `.gao-dev/last_session_history.json`
    - Define recovery trigger (automatic? prompt?)
    - **Owner**: Winston + John (UX decision)

12. **[CRAAP-012] Add Kanban Loading States (Architecture)**
    - Per-card loading indicators
    - Operation queue visualization
    - Cancel operation option
    - **Owner**: Winston → Frontend Architecture

13. **[CRAAP-013] Add Event Bus Buffer Cleanup (Architecture)**
    - Clear buffer when no subscribers
    - Prevent unbounded memory growth
    - **Owner**: Winston → Backend Architecture

14. **[CRAAP-014] Define ChatSession API Contract (Architecture)**
    - Define public API for agent switching
    - Avoid tight coupling to internals
    - Version pinning or semantic versioning
    - **Owner**: Winston → Integration Architecture

15. **[CRAAP-015] Add Migration Plan (PRD)**
    - How do existing users adopt web interface?
    - Training materials?
    - Feature tour on first launch?
    - **Owner**: John (Product Manager) → PRD

### Minor (Nice to Have)

16. **[CRAAP-016] Define Browser Test Matrix (Architecture)**
    - Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
    - **Owner**: Murat (Test Architect)

17. **[CRAAP-017] Add Scalability Guardrails (Architecture)**
    - Define warning thresholds (event count, file count)
    - Memory usage monitoring
    - **Owner**: Winston → Performance section

18. **[CRAAP-018] Reduce Document Redundancy (Documentation)**
    - Cross-reference instead of duplicating event types
    - Single source of truth for technology stack
    - **Owner**: Mary (BA) → Vision doc cleanup

19. **[CRAAP-019] Add Monitoring/Observability Plan (Architecture)**
    - How to monitor web server health?
    - Logging strategy
    - Metrics collection (optional, privacy-preserving)
    - **Owner**: Winston → Operations section

20. **[CRAAP-020] Consider Dark + Light Mode in MVP (Architecture)**
    - Respect system preference (low effort)
    - High value for many developers
    - **Owner**: Winston + John (priority decision)

21. **[CRAAP-021] Add Risk Register (Architecture)**
    - Comprehensive risk list with likelihood/impact
    - Data integrity risks
    - Network risks
    - Resource exhaustion
    - **Owner**: Winston → New section

22. **[CRAAP-022] Document Alternative Approaches (Architecture)**
    - Why not Electron/Tauri?
    - Why not PWA?
    - Why not TUI?
    - **Owner**: Winston → Alternatives Considered section

23. **[CRAAP-023] Define Phased Delivery Plan (PRD)**
    - MVP: Chat + Activity Stream + read-only files
    - V1.1: Kanban + Monaco editing + Git
    - V1.2: Ceremony Channels + advanced
    - **Owner**: John (PM) + Bob (Scrum Master) → PRD + Epic breakdown

---

## Action Items

### Immediate (Before PRD)

- [ ] **[Winston]** Add "Testing Architecture" section to ARCHITECTURE.md
- [ ] **[Winston]** Add "Security Architecture - WebSocket Authentication" to ARCHITECTURE.md
- [ ] **[Winston]** Add "Error Handling Strategy" section to ARCHITECTURE.md
- [ ] **[Winston]** Resolve circular dependency in Event-Driven Architecture section
- [ ] **[Winston]** Add file locking specification to Integration Architecture
- [ ] **[Product Owner + Winston]** **DECISION REQUIRED**: Reconsider mutual exclusion OR provide stronger rationale
- [ ] **[Winston]** Add session recovery UX specification

### Short-Term (During PRD Phase)

- [ ] **[John]** Add migration plan to PRD
- [ ] **[John]** Define phased delivery (MVP vs V1.1 vs V1.2) in PRD
- [ ] **[Murat]** Create Test Strategy document (can be parallel to PRD)
- [ ] **[Winston]** Add comprehensive Risk Register to ARCHITECTURE.md
- [ ] **[Winston]** Document alternative approaches (Electron, PWA, TUI) and rejection rationales

### Medium-Term (During Epic Breakdown)

- [ ] **[Bob]** Ensure stories include error handling acceptance criteria
- [ ] **[Bob]** Ensure stories include test requirements (unit, integration, E2E)
- [ ] **[Bob]** Break down phased delivery into sprints
- [ ] **[Amelia]** Review adapter layer coupling issues before implementation

---

## Recommendations Summary

### Architectural Decisions to Revisit

1. **Mutual Exclusion (CLI OR Web)**
   - **Current**: CLI and web cannot run simultaneously
   - **Recommendation**: Allow **read-only web observability** while CLI active
   - **Rationale**: Provides "mission control" value without complexity of full bidirectional
   - **Decision Needed**: YES/NO by Product Owner

2. **Event Bus Implementation (asyncio.Queue)**
   - **Current**: In-memory queue, non-persistent
   - **Alternative**: SQLite event log (persistent, queryable, already using SQLite)
   - **Rationale**: Event replay, history, survives restart
   - **Decision Needed**: Keep asyncio.Queue or switch to SQLite

3. **Dark Mode Only for MVP**
   - **Current**: Defer light mode to V1.1
   - **Recommendation**: Support both in MVP (respect system preference, ~20 lines CSS)
   - **Rationale**: Low effort, high value for developers who work at night
   - **Decision Needed**: MVP or V1.1?

### Must-Add Sections to Architecture

1. **Testing Architecture** (Critical)
2. **Error Handling Strategy** (Critical)
3. **Security Architecture - WebSocket Auth** (Critical)
4. **Risk Register** (Important)
5. **Session Recovery UX** (Important)
6. **Alternative Approaches Considered** (Nice-to-Have)

### Integration Concerns

1. **ChatSession API Contract** - Define public API, avoid tight coupling
2. **Circular Dependency Prevention** - Add event deduplication logic
3. **File Locking Mechanism** - Prevent concurrent edits by user + agent

---

## Conclusion

The Vision and Architecture documents are **thorough and well-structured**, demonstrating excellent planning for this significant Epic 39. However, this CRAAP review has surfaced **critical gaps** in security, testing, and error handling that must be addressed before proceeding to implementation.

**Recommended Next Steps**:

1. **Resolve Critical Issues (CRAAP-001 through CRAAP-007)** - Estimated 1-2 days
2. **Make Architectural Decisions** (mutual exclusion, event bus, dark mode) - Estimated 1 day
3. **Update Architecture Document** with new sections (testing, error handling, security) - Estimated 1 day
4. **Proceed to PRD** with John (Product Manager) - Estimated 3-5 days

**Timeline Impact**: +3 to 4 days before PRD phase, but significantly reduces implementation risk and rework.

**Overall Assessment**: **Strong foundation with important gaps to fill.** Addressing these issues now will prevent costly rework during implementation and ensure a robust, production-ready web interface.

---

**Review Complete**: 2025-01-16
**Next Review**: After architecture updates (before PRD)
