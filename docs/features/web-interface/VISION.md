# Vision Document: Browser-Based Web Interface for GAO-Dev

**Feature**: Web Interface
**Epic**: 39
**Scale Level**: 4 (Greenfield Significant Feature)
**Created**: 2025-01-16
**Elicitation Method**: Interactive 5W1H Framework + SCAMPER Integration Brainstorming
**Facilitator**: Mary (Business Analyst)
**Stakeholder**: Product Owner

---

## Executive Summary

Transform GAO-Dev from CLI-only to a rich browser-based interface that provides unprecedented observability into autonomous agent operations. Think **"Mini VS Code in browser, but optimized as a mission control center for observing and steering the GAO-Dev autonomous agent team."**

This interface serves two primary users:
1. **Product owners** working with GAO-Dev on production-scale SaaS projects
2. **AI agents (Claude Code)** testing and improving the system via Playwright MCP

---

## Problem Statement

### The Observability Gap

**Primary Frustration**: The CLI lacks richness of observability and interactivity. Users cannot clearly see:
- Brian's reasoning process during workflow selection
- Which agents are active and what they're doing
- Real-time file creation and modification
- Intra-agent collaboration during ceremonies
- Workflow execution progress

A web interface opens the door for much clearer interaction and transparency.

### The AI Testing Limitation

**Secondary (Critical) Frustration**: Claude Code cannot interact with the CLI to act as a beta tester.

**Vision**: Use Playwright MCP to enable Claude Code as an AI agent to:
- Interact with GAO-Dev like a human user
- Find bugs and UX issues
- Look for ways to improve outputs and user experience
- Provide continuous automated testing

This requires a **programmatically testable** web interface with:
- Semantic HTML and proper ARIA labels
- Stable `data-testid` attributes for Playwright selectors
- Clear state indicators that an AI agent can understand

---

## Vision Statement (5W1H Framework)

### WHY: The Core Problem

**Observability Gap**: CLI can't provide the rich, clear interaction that a web UI enables

**AI Agent Testability**: Need programmatic testing via Playwright MCP for continuous improvement

**Trust Building**: Users need to see and understand what autonomous agents are doing to trust the system

### WHO: Primary Users

1. **Product Owner** (Human User)
   - Working with GAO-Dev on active projects
   - Managing production-scale SaaS applications
   - Needs visibility and control

2. **Claude (AI Agent)**
   - Teaching, training, and improving the system
   - Active release cycle with automated testing
   - Needs identical human experience (no special AI mode)

### WHAT: The Core Experience

**Mental Model**: "Mini VS Code in browser, but focused on agent observability and interactivity"

**Not**: Another code editor
**Is**: Mission control center for watching and steering the GAO-Dev agent team

### WHERE: Local Access

- Runs on `localhost:3000`
- Localhost-only for now (127.0.0.1)
- No authentication required (trusted environment)
- Future: Docker container/volume deployment with auth

### WHEN: Initialization

- Starts when `gao-dev start --web` is run
- Initialization flow:
  1. Check if greenfield/brownfield project
  2. Check if `.gao-dev/` exists (already managing?)
  3. Initialize repo if required
  4. Prompt for project name (smart default: folder name)
  5. Transition to main interface

- Auto-opens browser (configurable)

### HOW: Architecture Pattern

**Reuse and Share**: Build on existing CLI infrastructure
- Same `ChatSession` instance for CLI and web
- All business logic stays in Python backend
- Web UI is thin view layer
- Event-driven architecture (WebSocket streaming)

---

## Core Interface Components

### Tab Structure

**Five Main Tabs**:

1. **Chat Tab** (Default/Home)
   - Conversation with current agent (Brian, Mary, John, Winston, Sally, Bob, Amelia, Murat)
   - Agent switcher: "Who am I talking to?"
   - Optional reasoning toggle (show/hide Claude's thinking)
   - Clean, minimalist (ChatGPT/Claude.ai style)

2. **Activity Stream Tab**
   - Real-time timeline of all workflow activities
   - **Progressive disclosure**:
     - Shallow (default): High-level overview ("Winston is creating ARCHITECTURE.md")
     - Deep (on-demand): Click to expand for details (agent reasoning, tool calls, context)
   - Filters: By agent, workflow, event type
   - Time windows: Default 1 hour, expandable (24h, 7d, 30d, All)

3. **Kanban Board Tab** ⭐ NEW
   - Visual project management
   - State columns: Backlog → Ready → In Progress → In Review → Done
   - Cards for epics and stories
   - Drag-and-drop to change state (triggers `GitIntegratedStateManager`)
   - Real-time updates as agents complete work
   - Powered by `.gao-dev/documents.db`

4. **Files Tab** (Monaco Editor)
   - File tree navigation (tracked directories only)
   - Monaco editor for viewing/editing
   - **Enforce conventions**: All saves require commit message
   - Validation checks before save (document lifecycle rules)
   - Real-time file updates from agents
   - Diff view

5. **Git Tab** (Timeline)
   - Chronological list of commits
   - Commit cards with message, author, timestamp
   - Click to see diff view
   - Filter by author (agent or human)

**Conditional Tab**:

6. **Ceremony Channels Tab** ⭐ NEW
   - Only visible when ceremony is active (planning, retro, sprint review)
   - **Slack-like interface** for intra-agent discussions
   - Channel list: #planning-ceremony, #retrospective, #sprint-review
   - Watch agents collaborate in real-time
   - User can optionally participate (post messages)

### Layout

**Top Bar**:
- Project name and status
- Agent switcher (current agent indicator)
- Session status indicator
- Settings/preferences

**Sidebar**:
- Tab icons (Chat, Activity Stream, Kanban, Files, Git, Ceremonies)
- Quick navigation

**Main Content Area**:
- Renders content for selected tab
- Full-width, full-height

**Visual Tone**: Minimal, clean, professional (shadcn/ui components)

---

## First-Time Experience (30 Seconds)

1. User runs `gao-dev start --web` in project directory
2. Browser opens to `localhost:3000`
3. **Initialization screen**:
   - "Checking project status..."
   - Detects greenfield/brownfield
   - Detects if `.gao-dev/` exists
4. **If new project**:
   - "Let's initialize your project!"
   - Prompt: "Project name?" (default: folder name)
   - Initialize git repo if needed
   - Create `.gao-dev/` structure
5. **Main interface loads**:
   - Chat tab (default)
   - Brian's welcome message: "Welcome to GAO-Dev! I'm Brian, your Workflow Coordinator. What would you like to work on today?"
   - Sidebar with tab icons visible
   - Top bar shows project name

**First impression**: Familiar (like ChatGPT), but with agent observability tools available in sidebar

---

## Architectural Decisions

### 1. Build on CLI Foundation (Reuse, Don't Replace)

**Decision**: Web UI builds on top of existing CLI infrastructure, sharing core services.

**Rationale**:
- CLI work (Epic 30, 27, etc.) is foundational and battle-tested
- Avoids duplication of complex business logic
- Maintains consistency

**Implementation**:
- Web UI shares same `ChatSession` instance
- All file operations through `GitIntegratedStateManager`
- Workflow execution uses existing `WorkflowExecutor`
- **Thin client, thick server** pattern

### 2. Mutual Exclusion (CLI OR Web, Never Both) ⭐ NEW

**Decision**: Only one interface (CLI or web) can be active at a time.

**Rationale**:
- Prevents concurrent operation conflicts
- Simplifies state synchronization (no need to sync two active interfaces)
- Easier to reason about and test
- User explicitly chooses their interface

**Implementation**:
- Session lock file: `.gao-dev/session.lock` (interface type, PID, timestamp)
- `gao-dev start` (CLI): Check lock, block if web active
  - Error: "Web session active. Please close browser first."
- `gao-dev start --web`: Check lock, block if CLI active
  - Error: "CLI session active. Please exit CLI first."
- Graceful cleanup on exit
- Stale lock detection (PID validation)

### 3. Enforce Conventions for Humans AND AI Agents ⭐ KEY

**Decision**: All file edits, commits, and operations must follow the same conventions, whether performed by humans or autonomous agents.

**Rationale**:
- **Consistency**: Same quality standards for everyone
- **Traceability**: Every change has proper git commit
- **Quality**: Document lifecycle constraints enforced universally
- **Trust**: System "eats its own dog food"

**Implementation**:
- Monaco editor saves → **Commit message prompt** → Validation → `GitIntegratedStateManager` → Atomic commit
- **No shortcuts** for manual edits
- Same validation rules apply (document lifecycle, structure compliance, naming conventions)
- Same git commit message format

**User Flow Example**:
1. User edits file in Monaco, clicks "Save"
2. System prompts: "Commit message?" (with template/suggestions)
3. Backend validates against document lifecycle rules
4. If valid: Atomic file+DB+git commit via `GitIntegratedStateManager`
5. If invalid: Show error with actionable fix suggestions
6. Activity stream shows commit (just like agent commits)

### 4. Design for Production Scale ⭐ CRITICAL

**Decision**: Architect for production-ready SaaS applications, not toy projects.

**Rationale**:
- **GAO-Dev projects can become very large production-ready SaaS applications**
- Hundreds of epics over months/years
- Bug/issue management
- Very long-running conversations

**Scale Expectations**:
- 100+ epics per project
- 1,000+ stories across all epics
- 10,000+ activity stream events
- 500+ files in project
- 30+ minute long-running workflows
- Multi-month/year project lifespans

**Performance Strategies**:
- On-demand rendering / lazy loading
- Short time windows (user can extend to view more history)
- Virtual scrolling (activity stream, file tree)
- Monaco handles file performance (worth the dependency)
- **Defer to Winston (architect) for detailed performance design**

### 5. Localhost-Only for Now, Docker Later

**Decision**: Initial release runs on localhost only, no authentication required.

**Rationale**:
- Trusted environment (local machine)
- Focus on core functionality before security
- Auth complexity deferred to future

**Future**: Docker container/volume deployment with authentication when deploying in "real world"

### 6. AI Agents = Full Human Experience ⭐ CRITICAL

**Decision**: AI agents (via Playwright MCP) experience the **exact same UI** as humans, with no shortcuts or special modes.

**Rationale**:
- **True user acceptance testing**: AI finds real UX issues
- **Full fidelity testing**: AI tests what humans use
- If AI struggles, humans will too

**Implementation**:
- Semantic HTML with proper ARIA labels
- Stable `data-testid` attributes for Playwright
- Clear state indicators (loading, success, error)
- **No hidden "AI API"** that bypasses UI
- AI interacts via browser automation only

**Purpose**: AI should act as human tester/researcher, so it must have the same experience

---

## Integration Requirements with Existing Features

### Epic 30: Interactive Brian Chat Interface (ChatREPL)

**Reuse**:
- ✅ `ChatSession` instance (shared between CLI and web)
- ✅ Conversation history
- ✅ Brian's prompt templates and configuration
- ❌ **DO NOT** duplicate ChatREPL logic

**Adapter**: `BrianWebAdapter` translates ChatSession events to WebSocket messages

### Epic 27: Git-Integrated Hybrid Wisdom

**Reuse**:
- ✅ `GitIntegratedStateManager` for ALL file operations (Monaco saves, agent writes)
- ✅ Kanban board queries from `.gao-dev/documents.db`
- ✅ Git tab reads from local git repository
- ❌ **DO NOT** create separate state management

**Pattern**: Web UI **observes** state, doesn't manage it

### Epic 35: Interactive Provider Selection

**Reuse**:
- ✅ Provider preferences from `.gao-dev/provider_preferences.yaml`
- ✅ Provider validation logic
- ❌ **DO NOT** duplicate validation

**Future**: Web UI settings panel to change provider (writes to YAML)

### Epic 31: Mary (Business Analyst)

**Reuse**:
- ✅ Chat tab supports switching to Mary agent
- ✅ Mary's prompts and workflows accessible
- This interactive session is an example!

### Epic 7.2: Workflow-Driven Core

**Reuse**:
- ✅ Activity stream subscribes to workflow events
- ✅ Workflows emit events at each step
- ❌ **DO NOT** duplicate workflow logic

**Backend**: `WorkflowEventBus` publishes events to WebSocket clients

### Epic 28: Ceremony-Driven Workflow Integration ⭐ NEW

**Reuse**:
- ✅ Ceremony Channels tab activates when ceremony starts
- ✅ Intra-agent messages streamed to Slack-like interface
- ✅ User can observe and optionally participate

**Backend**: `CeremonyOrchestrator` publishes messages to dedicated WebSocket channel

---

## Technology Stack (Proposed)

**Backend** (Python):
- **FastAPI** (async, WebSocket support, minimal new dependencies)
- WebSocket for real-time bidirectional communication
- Static file serving for frontend build
- Adapter layer for event translation

**Frontend** (JavaScript):
- **React 18+** (hooks, context)
- **Next.js 14+** (App Router) OR **Vite** (TBD by Winston)
- **shadcn/ui** components (Radix UI + Tailwind CSS)
- **Monaco Editor** (@monaco-editor/react)
- **Zustand** or React Context for state management
- Native WebSocket API or socket.io-client

**Event Bus** (Backend):
- Python `asyncio.Queue` for event streaming (sufficient for single-project)
- Future: Redis pub/sub if multi-project support needed

**Note**: Final technology decisions to be made by Winston (Architect)

---

## Architecture Patterns

### Pattern 1: Thin Client, Thick Server

- **ALL business logic** in Python backend
- Web UI is pure **view layer** (React components)
- Backend emits events, frontend renders them
- No duplication of ChatREPL, WorkflowExecutor, StateManager logic

### Pattern 2: Event Sourcing

- All agent activities emit events (workflow started, tool used, file created, etc.)
- EventBus publishes to WebSocket clients
- Frontend subscribes and renders events in real-time
- Event history stored for playback (activity stream with time windows)

### Pattern 3: Single Source of Truth

- All state changes through `GitIntegratedStateManager`
- Frontend **observes** state via WebSocket events and API queries
- Frontend does **NOT** manage state (no local state mutations)
- Git repository + `.gao-dev/documents.db` = source of truth

### Pattern 4: Progressive Disclosure

- Activity stream: Shallow overview by default, deep drill-down on click
- Minimize cognitive load, maximize clarity
- Users glance for awareness, click for details

---

## Workflow Observability Requirements

When Brian runs a workflow autonomously, the activity stream shows **all of the following** (in real-time):

**Top-Level (Shallow Overview)**:
- Current workflow step ("Step 3/7: Creating Architecture Document")
- Which agent is active ("Winston is working...")
- Tools being used ("Winston used Write tool on ARCHITECTURE.md")
- Git commits ("Committed: feat(architecture): Create system design")
- File changes (highlight in file tree, can view in Monaco tab)

**Deep Drill-Down (Clickable)**:
- Agent reasoning (expand to see Claude's thinking)
- Tool call details (parameters, results)
- File diffs (quick link to Files tab)
- Commit details (quick link to Git tab)

**Goal**: User feels **"I can see what's happening and trust the process"**

---

## Multi-Agent Chat Switching ⭐ NEW

**Requirement**: UI must support switching between different agent conversations.

**Agents**: Brian, Mary, John, Winston, Sally, Bob, Amelia, Murat

**Use Case**: When interacting directly with Mary (like this vision elicitation session) instead of Brian, this must be distinctly managed in the UI.

**Implementation**:
- Agent switcher in top bar or chat header
- Each agent maintains separate conversation context
- Clear indicator: "You are now chatting with Mary (Business Analyst)"
- Conversation history persists per agent
- Easy switching without losing context

**Example**: User switches from Brian to Mary to conduct a brainstorming session, then back to Brian to execute workflows

---

## Ceremony Channels (Slack-Like) ⭐ NEW

**Requirement**: When ceremonies are running, show a Slack-like channel interface for intra-agent discussions.

**Activation**: Ceremony Channels tab becomes visible when a ceremony is triggered (e.g., planning, retro, sprint review)

**Features**:
- **Channel list** (sidebar within tab):
  - #planning-ceremony
  - #retrospective
  - #sprint-review
  - etc.
- **Message stream** (center pane):
  - Agent avatar + name
  - Timestamp
  - Markdown-rendered messages
  - Threaded replies (optional, TBD)
- **Observability**: Watch agents collaborate (Brian + John + Winston discussing architecture)
- **Participation**: User can optionally post messages

**Value**: Unprecedented visibility into **intra-agent collaboration**, not just individual agent work

**Ties to**: Epic 28 (Ceremony-Driven Workflow Integration)

---

## Performance Requirements

### Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Page load** | <2 seconds | User expectation |
| **Event latency** | <100ms | Real-time feel |
| **Activity stream** | Handle 10,000+ events | Large projects |
| **File tree** | Handle 500+ files | Large projects |
| **Monaco editor** | Handle 10,000-line files | Large files |

### Strategies

- **Virtual scrolling**: Only render visible items
- **Lazy loading**: On-demand data fetch
- **Time windows**: Default 1 hour, user-expandable
- **Monaco optimization**: Built-in performance (industry-standard)
- **Database indexing**: Fast queries
- **WebSocket throttling**: Batch if needed

**Note**: Detailed performance architecture to be designed by Winston

---

## Security Considerations

**Localhost-Only** (for now):
- Server binds to 127.0.0.1 only
- No external access
- No authentication required (trusted environment)

**Future** (when deploying remotely):
- Authentication (JWT, OAuth)
- CORS policies for external access
- HTTPS/TLS
- CSRF tokens
- Input validation and sanitization

**Current Security**:
- Path validation (files stay within project directory)
- Input sanitization (commit messages, file edits)
- No eval() or dangerous patterns

---

## Success Criteria

### User Adoption (3 months post-launch)

- ✅ >50% of new users choose web interface over CLI
- ✅ >70% of sessions use web interface
- ✅ Positive feedback from beta testers

### Performance Benchmarks

- ✅ Page load <2 seconds
- ✅ Event latency <100ms
- ✅ No browser crashes with large datasets
- ✅ Monaco handles large files without lag

### Reliability

- ✅ <1 crash per 1,000 sessions
- ✅ WebSocket reconnection >95% success rate
- ✅ Session state recovery after crash

### Quality Assurance

- ✅ Zero regressions (100% of existing CLI tests pass)
- ✅ Web UI E2E tests: >80% coverage
- ✅ **AI agent (Playwright MCP) finds at least 5 real UX issues during beta**

### Accessibility

- ✅ WCAG 2.1 AA compliance
- ✅ Keyboard navigation: All features accessible
- ✅ Screen reader support (VoiceOver, NVDA)

---

## Risks & Mitigations

### Risk 1: WebSocket Stability

**Risk**: Connection drops during long-running workflows
**Mitigation**:
- Auto-reconnect with exponential backoff
- Buffer events during disconnect, replay on reconnect
- Fallback to HTTP polling
- Clear UI indicator: "Reconnecting..."

### Risk 2: Large Project Performance

**Risk**: Activity stream, file tree, or Kanban lag with large datasets
**Mitigation**:
- Virtual scrolling, lazy loading, time windows
- Database indexing
- Performance testing with mock large projects

### Risk 3: Session Lock Bugs

**Risk**: Lock not enforced correctly, both CLI and web run simultaneously
**Mitigation**:
- Comprehensive integration tests
- Stale lock detection (PID validation)
- Clear error messages
- Manual override: `gao-dev unlock --force`

### Risk 4: Monaco Memory Leaks

**Risk**: Long-running sessions cause browser memory growth
**Mitigation**:
- Editor instance pooling (reuse editors)
- Proper disposal of Monaco models
- Memory profiling
- Tab limit (10 files max, auto-close LRU)

### Risk 5: Security Vulnerabilities

**Risk**: XSS, path traversal, command injection
**Mitigation**:
- Input sanitization
- Path validation
- Content Security Policy (CSP) headers
- CORS restricted to localhost
- Regular security audits

### Risk 6: Breaking Changes to Existing Features

**Risk**: Web UI integration breaks CLI functionality
**Mitigation**:
- Feature flags (web UI is opt-in)
- Comprehensive regression test suite
- Gradual rollout (alpha → beta → stable)
- Clear rollback plan

---

## Non-Functional Requirements

### Performance

- Page load: <2 seconds
- Event latency: <100ms
- Memory usage (8 hours): <500 MB
- CPU usage (idle): <5%

### Security

- Local-only access (127.0.0.1)
- CORS protection
- CSRF protection (future)
- Session isolation
- File system sandboxing (project directory only)

### Accessibility

- WCAG 2.1 AA compliance
- 100% keyboard accessible
- Screen reader support
- Color contrast: 4.5:1
- Semantic HTML

### Testability (AI Agent Focus) ⭐ CRITICAL

- **Semantic HTML**: `<button>`, `<nav>`, `<main>` (not just `<div>`)
- **ARIA labels**: `aria-label`, `aria-describedby` for context
- **data-testid attributes**: Stable selectors for Playwright
  - Example: `data-testid="chat-input"`, `data-testid="activity-stream-event"`
- **State indicators**: `data-state="loading"`, `data-state="error"` for AI to detect status
- **Deterministic IDs**: Consistent IDs (not random UUIDs)

**Purpose**: Enable Claude Code to interact via Playwright MCP as a human tester

---

## Open Questions for PRD Phase

### Architecture

1. Frontend framework: React + Next.js OR React + Vite?
2. Event bus: asyncio.Queue or Redis?
3. WebSocket protocol: Custom JSON or socket.io?
4. File watching: How to detect agent file changes in real-time?
5. Session state persistence: Memory or database?

### Features

6. Kanban board: Separate boards for epics vs stories?
7. Monaco editor: Which features in MVP? (minimap, multi-cursor, etc.)
8. Git operations: Should users branch/merge in UI? Or read-only for MVP?
9. Ceremony participation: Can users post messages? Or observe-only?
10. Activity stream retention: How long to keep events?

### UX/Design

11. Theme support: Dark + light mode? Or just dark for MVP?
12. Layout customization: Resizable panels? Or fixed?
13. Notifications: Desktop notifications for long operations?
14. Onboarding: Guided tour? Or minimal welcome?
15. Agent avatars: Agent-specific icons? Or just names?

### Testing & Quality

16. E2E testing framework: Playwright OR Cypress?
17. Playwright MCP integration: When to start AI agent testing? (Alpha? Beta?)
18. Performance benchmarks: What to track? How to automate?
19. Accessibility testing: Automated (axe-core) + manual schedule?
20. Beta testers: How many? Internal or external community?

---

## Next Steps

### Immediate (This Week)

1. **Winston (Architect)**: Review this vision, create ARCHITECTURE.md
   - Technology stack finalization
   - API design (REST + WebSocket)
   - Component architecture (frontend)
   - Event bus design (backend)
   - Security architecture
   - Performance optimization strategies

### Short-Term (Next 2 Weeks)

2. **John (Product Manager)**: Create comprehensive PRD.md
   - Feature prioritization (MoSCoW)
   - User stories and acceptance criteria
   - Success metrics and KPIs
   - Timeline and milestones

3. **Bob (Scrum Master)**: Break down into epics and stories
   - Epic 39: Browser-Based Web Interface
   - Stories 39.1-39.16 (estimated)
   - Sprint planning (2-week sprints, 6-8 sprints estimated)

### Medium-Term (Implementation Phase)

4. **Amelia (Developer)**: Implement stories iteratively
5. **Murat (Test Architect)**: Create test strategy and implement tests
6. **Claude Code (AI Agent)**: Beta testing via Playwright MCP (once MVP ready)

---

## Key Takeaways

### What Makes This Vision Unique?

1. **Dual Human-AI Interface**: Designed from day one for both human users AND AI agent testing
2. **Agent Observability**: Focus on making autonomous agents' work visible and understandable
3. **Multi-Agent Chat Switching**: Interact with any of 8 agents (Brian, Mary, John, etc.)
4. **Ceremony Channels**: Slack-like interface for watching intra-agent collaboration
5. **Kanban Board**: Visual project management powered by `GitIntegratedStateManager`
6. **Build on Foundation**: Reuses existing CLI infrastructure, doesn't replace it
7. **Production Scale**: Designed for real-world SaaS applications, not toy projects
8. **Convention Enforcement**: Humans follow same quality standards as AI agents
9. **Mission Control Paradigm**: Not "another code editor," but "agent team steering center"

### Core Principles

- **Transparency**: Make agent activities observable and understandable
- **Consistency**: Same rules for humans and AI agents
- **Reusability**: Build on existing work, don't duplicate
- **Scalability**: Design for production-scale from day one
- **Quality**: No shortcuts, enforce best practices universally
- **Testability**: Enable AI-driven continuous improvement via Playwright MCP

---

**Document Status**: ✅ Complete - Ready for Architecture Phase

**Next Owner**: Winston (Technical Architect) → Create ARCHITECTURE.md

**Vision Elicitation Complete**: 2025-01-16 (Interactive 5W1H session with Product Owner)
