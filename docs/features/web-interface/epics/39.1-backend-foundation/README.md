# Epic 39.1: Backend Foundation

**Epic Number**: 39.1
**Epic Name**: Backend Foundation
**Feature**: Web Interface
**Scale Level**: 4 (Greenfield Significant Feature)
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort Estimate**: 8 story points
**Dependencies**: Epic 30 (ChatREPL), Epic 27 (GitIntegratedStateManager)

---

## Epic Overview

Establish the FastAPI backend infrastructure that serves as the foundation for all web interface functionality. This epic delivers the web server, WebSocket communication, event bus, and session management required for real-time agent observability.

### Business Value

- **Foundation for All Web Features**: Enables all subsequent web interface development
- **Real-Time Communication**: WebSocket infrastructure for instant agent activity updates
- **Session Management**: Prevents conflicts between CLI and web interface operations
- **Security**: Localhost-only access with session token authentication

### User Stories Summary

This epic includes foundational backend services:

1. **Story 39.1**: FastAPI Web Server Setup
2. **Story 39.2**: WebSocket Manager and Event Bus
3. **Story 39.3**: Session Lock and Read-Only Mode

### Success Criteria

- [ ] FastAPI server starts and serves frontend in <3 seconds
- [ ] WebSocket connections establish successfully with <100ms latency
- [ ] Session lock prevents concurrent CLI/web write operations
- [ ] Read-only mode enforced when CLI holds lock
- [ ] Event bus handles 1,000+ events/second without lag
- [ ] Health check endpoint returns 200 OK
- [ ] Graceful shutdown on SIGTERM/SIGINT

### Technical Approach

**Technology Stack**:
- FastAPI 0.104+ (async, WebSocket support)
- uvicorn ASGI server
- asyncio.Queue for event bus (in-memory, no Redis)
- File-based session lock with PID tracking

**Integration Points**:
- Epic 30: ChatREPL (BrianWebAdapter)
- Epic 27: GitIntegratedStateManager (atomic operations)
- Epic 28: CeremonyOrchestrator (ceremony events)

**Architecture Pattern**:
- Thin client, thick server (all logic in Python)
- Event-driven architecture (pub/sub via asyncio.Queue)
- Middleware-enforced read-only mode

### Definition of Done

- [ ] All stories in epic completed and tested
- [ ] Integration tests pass (FastAPI + WebSocket + Event Bus)
- [ ] Performance tests meet targets (<3s startup, <100ms latency)
- [ ] Security tests validate session lock and read-only enforcement
- [ ] Documentation complete (API specs, deployment guide)
- [ ] Code review approved
- [ ] Zero regressions (100% CLI tests pass)

---

**Epic Owner**: Winston (Technical Architect)
**Implementation**: Amelia (Software Developer)
**Testing**: Murat (Test Architect)
