# Story 39.3: Session Lock and Read-Only Mode

**Story Number**: 39.3
**Epic**: 39.1 - Backend Foundation
**Feature**: Web Interface
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort Estimate**: M (Medium - 3 story points)
**Dependencies**: Story 39.1 (FastAPI Web Server), Story 39.2 (WebSocket Manager)

---

## User Story

As a **product owner**
I want **exclusive write access control between CLI and web interface**
So that **I can observe agent activities in the web UI while CLI workflows run without conflicts**

---

## Acceptance Criteria

### Session Lock Mechanism
- [ ] AC1: Session lock file created at `.gao-dev/session.lock`
- [ ] AC2: Lock file contains: `{interface: "cli"|"web", mode: "read"|"write", pid: int, timestamp: ISO8601}`
- [ ] AC3: Write lock acquired exclusively (only one interface can hold write lock)
- [ ] AC4: Read lock always succeeds (multiple readers allowed)
- [ ] AC5: Stale lock detection: Validate PID before denying lock acquisition
- [ ] AC6: Lock released on graceful shutdown
- [ ] AC7: Lock auto-released if process dies (PID no longer exists)

### CLI Lock Behavior
- [ ] AC8: `gao-dev start` acquires write lock (can execute workflows, modify files)
- [ ] AC9: CLI blocks if web holds write lock with error: "Web session active. Close browser first."
- [ ] AC10: CLI releases lock on exit (Ctrl+C, `exit` command)

### Web Lock Behavior
- [ ] AC11: `gao-dev start --web` acquires read lock by default (observability mode)
- [ ] AC12: Web can upgrade to write lock if no CLI session active
- [ ] AC13: Web automatically downgrades to read lock when CLI acquires write lock
- [ ] AC14: Web displays banner: "Read-only mode: CLI is active. You can observe but not send commands."

### Read-Only Mode Enforcement
- [ ] AC15: API middleware checks lock state on every request
- [ ] AC16: GET/HEAD/OPTIONS requests always allowed (observability)
- [ ] AC17: POST/PATCH/PUT/DELETE rejected with 423 Locked when in read-only mode
- [ ] AC18: Error response: `{error: "Session locked by CLI", mode: "read-only", message: "Exit CLI to enable write operations"}`
- [ ] AC19: Frontend disables write controls (buttons, inputs) when in read-only mode

### Lock State Synchronization
- [ ] AC20: Web polls lock file every 2 seconds
- [ ] AC21: Web emits `session.mode_changed` event when lock state changes
- [ ] AC22: Frontend updates UI within 100ms of mode change
- [ ] AC23: Banner appears/disappears based on lock state

### Manual Override
- [ ] AC24: Admin command `gao-dev unlock --force` removes stale lock
- [ ] AC25: Force unlock logs warning: "Force unlocking session. Use with caution."
- [ ] AC26: Force unlock validates that process is actually dead before removing lock

---

## Technical Context

### Architecture Integration

**Session Lock Implementation**:
```python
# gao_dev/core/session_lock.py
import os
import json
import psutil
from pathlib import Path
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

class SessionLock:
    def __init__(self, project_root: Path):
        self.lock_file = project_root / ".gao-dev" / "session.lock"
        self.current_mode: str = "none"  # "read", "write", "none"

    def acquire(self, interface: str, mode: str = "write") -> bool:
        """
        Acquire session lock.

        Args:
            interface: "cli" or "web"
            mode: "read" or "write"

        Returns:
            True if acquired, False if denied
        """
        if mode == "read":
            # Read mode always succeeds (observability only)
            self.current_mode = "read"
            return True

        # Write mode requires exclusive lock
        if self.lock_file.exists():
            lock_data = json.loads(self.lock_file.read_text())
            if self.is_process_alive(lock_data["pid"]):
                logger.warning("write_lock_held", holder=lock_data["interface"])
                return False
            else:
                # Stale lock, remove it
                logger.info("removing_stale_lock", pid=lock_data["pid"])
                self.lock_file.unlink()

        # Acquire write lock
        lock_data = {
            "interface": interface,
            "mode": "write",
            "pid": os.getpid(),
            "timestamp": datetime.now().isoformat()
        }
        self.lock_file.write_text(json.dumps(lock_data, indent=2))
        self.current_mode = "write"
        logger.info("write_lock_acquired", interface=interface)
        return True

    def release(self):
        """Release session lock"""
        if self.lock_file.exists():
            self.lock_file.unlink()
            logger.info("lock_released")
        self.current_mode = "none"

    def is_write_locked_by_other(self) -> bool:
        """Check if another process holds write lock"""
        if not self.lock_file.exists():
            return False

        lock_data = json.loads(self.lock_file.read_text())
        if lock_data["pid"] == os.getpid():
            return False  # We hold the lock

        return self.is_process_alive(lock_data["pid"])

    @staticmethod
    def is_process_alive(pid: int) -> bool:
        """Check if process with given PID is running"""
        return psutil.pid_exists(pid)
```

**API Middleware for Read-Only Enforcement**:
```python
# gao_dev/web/middleware.py
from fastapi import Request
from fastapi.responses import JSONResponse

@app.middleware("http")
async def read_only_middleware(request: Request, call_next):
    """Enforce read-only mode when CLI holds lock"""
    # GET/HEAD/OPTIONS: always allowed (observability)
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return await call_next(request)

    # Write operations (POST/PATCH/PUT/DELETE): check lock
    session_lock = request.app.state.session_lock
    if session_lock.is_write_locked_by_other():
        return JSONResponse(
            status_code=423,  # Locked
            content={
                "error": "Session locked by CLI",
                "mode": "read-only",
                "message": "Exit CLI session to enable write operations"
            }
        )

    return await call_next(request)
```

### Dependencies

**Epic 30 (ChatREPL)**:
- CLI ChatREPL acquires write lock before starting

**Epic 27 (GitIntegratedStateManager)**:
- All write operations check lock state before executing

### Frontend Integration

**Lock State Polling**:
```typescript
// Poll lock state every 2 seconds
useEffect(() => {
  const interval = setInterval(async () => {
    const response = await fetch('/api/session/lock-state')
    const data = await response.json()

    if (data.isReadOnly !== isReadOnly) {
      setIsReadOnly(data.isReadOnly)
      eventBus.emit('session.mode_changed', { mode: data.mode })
    }
  }, 2000)

  return () => clearInterval(interval)
}, [isReadOnly])
```

**Read-Only Banner**:
```typescript
{isReadOnly && (
  <Banner variant="info" className="sticky top-0 z-50">
    <Icon name="eye" />
    Read-only mode: CLI is active. You can observe but not send commands.
    <Button variant="ghost" onClick={() => showHelp('read-only-mode')}>
      Learn More
    </Button>
  </Banner>
)}
```

---

## Test Scenarios

### Test 1: CLI Acquires Write Lock
**Given**: No active session
**When**: User runs `gao-dev start`
**Then**:
- CLI acquires write lock
- Lock file created with interface="cli", mode="write"
- CLI can execute workflows

### Test 2: Web Starts in Read-Only Mode
**Given**: CLI holds write lock
**When**: User runs `gao-dev start --web`
**Then**:
- Web acquires read lock
- Banner displays: "Read-only mode: CLI is active"
- POST requests return 423 Locked
- Write controls disabled in UI

### Test 3: Web Upgrades to Write Mode
**Given**: Web in read-only mode, CLI exits
**When**: Web polls lock state
**Then**:
- Web detects CLI released lock
- Web upgrades to write lock
- Banner disappears
- Write controls enabled

### Test 4: Stale Lock Removal
**Given**: Lock file exists with PID of dead process
**When**: User runs `gao-dev start`
**Then**:
- System detects PID not alive
- Stale lock removed
- New write lock acquired
- Warning logged

### Test 5: Force Unlock
**Given**: Lock file exists (stale or active)
**When**: Admin runs `gao-dev unlock --force`
**Then**:
- Lock file removed
- Warning logged: "Force unlocking session. Use with caution."
- Next interface can acquire lock

---

## Definition of Done

### Code Quality
- [ ] Code follows GAO-Dev standards (DRY, SOLID, typed)
- [ ] Type hints throughout (no `Any`)
- [ ] structlog for all logging
- [ ] Error handling comprehensive
- [ ] Black formatting applied (line length 100)

### Testing
- [ ] Unit tests: 100% coverage for session_lock.py
- [ ] Integration tests: CLI/web lock acquisition, read-only mode enforcement
- [ ] E2E tests: Full lock lifecycle (acquire, upgrade, downgrade, release)
- [ ] Race condition tests: Simultaneous lock acquisition attempts

### Documentation
- [ ] User guide: Understanding read-only mode
- [ ] Troubleshooting: Stale locks, force unlock
- [ ] API documentation: /api/session/lock-state endpoint

### Code Review
- [ ] Code review approved by Winston (Technical Architect)
- [ ] Security review: Lock file permissions, PID validation
- [ ] UX review: Read-only banner clarity

---

## Implementation Notes

### Lock State API Endpoint

```python
@app.get("/api/session/lock-state")
async def get_lock_state():
    """Return current session lock state"""
    session_lock = app.state.session_lock

    if not session_lock.lock_file.exists():
        return {"mode": "write", "isReadOnly": False, "holder": None}

    lock_data = json.loads(session_lock.lock_file.read_text())

    if lock_data["pid"] == os.getpid():
        # We hold the lock
        return {"mode": "write", "isReadOnly": False, "holder": "web"}

    if session_lock.is_process_alive(lock_data["pid"]):
        # Another process holds write lock
        return {
            "mode": "read",
            "isReadOnly": True,
            "holder": lock_data["interface"]
        }

    # Stale lock
    return {"mode": "write", "isReadOnly": False, "holder": None}
```

### Platform Compatibility

**Process Detection**:
- Uses `psutil` library (cross-platform)
- Handles Windows, macOS, Linux

**Lock File Permissions**:
- Create with 0644 (readable by owner)
- Prevent race conditions with atomic writes

---

## Related Stories

- **Story 39.1**: FastAPI Web Server Setup (foundation)
- **Story 39.2**: WebSocket Manager (session token integration)
- **Story 39.7**: Brian Chat Component (respects read-only mode)
- **Story 39.14**: Monaco Edit Mode (respects read-only mode)

---

**Story Owner**: Amelia (Software Developer)
**Reviewer**: Winston (Technical Architect)
**Tester**: Murat (Test Architect)
