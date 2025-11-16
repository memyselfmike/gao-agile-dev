# Story 39.1: FastAPI Web Server Setup

**Story Number**: 39.1
**Epic**: 39.1 - Backend Foundation
**Feature**: Web Interface
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort Estimate**: S (Small - 2 story points)
**Dependencies**: None

---

## User Story

As a **product owner**
I want **GAO-Dev to start a FastAPI web server on localhost**
So that **I can access the web interface via browser and interact with agents visually**

---

## Acceptance Criteria

### Server Startup
- [ ] AC1: FastAPI server binds to `127.0.0.1:3000` (localhost only, no external access)
- [ ] AC2: Server starts in <3 seconds from `gao-dev start --web` command
- [ ] AC3: Server logs startup message with URL: "Web interface available at http://127.0.0.1:3000"
- [ ] AC4: Server auto-opens browser to `http://127.0.0.1:3000` (configurable via `--no-browser` flag)

### Static File Serving
- [ ] AC5: FastAPI serves React build from `/dist` directory
- [ ] AC6: Index route `/` serves `index.html` from build
- [ ] AC7: Static assets (`/assets/*`) served with correct MIME types
- [ ] AC8: 404 responses for non-existent routes (future: client-side routing fallback)

### Health Check Endpoint
- [ ] AC9: GET `/api/health` returns 200 OK with JSON: `{"status": "healthy", "version": "1.0.0"}`
- [ ] AC10: Health check responds in <10ms

### CORS Configuration
- [ ] AC11: CORS restricted to localhost origins only: `http://localhost:3000`, `http://127.0.0.1:3000`
- [ ] AC12: CORS middleware allows credentials (session tokens)
- [ ] AC13: Pre-flight OPTIONS requests handled correctly

### Graceful Shutdown
- [ ] AC14: Server handles SIGTERM signal and shuts down gracefully
- [ ] AC15: Server handles SIGINT (Ctrl+C) and shuts down gracefully
- [ ] AC16: Shutdown logs "Shutting down web server..." message
- [ ] AC17: All active connections closed cleanly on shutdown

### Error Handling
- [ ] AC18: Port conflict detected and reported: "Port 3000 already in use. Try `--port 3001`"
- [ ] AC19: Frontend build not found error reported: "Frontend build missing. Run `npm run build` first."

---

## Technical Context

### Architecture Integration

**Technology Stack**:
- FastAPI 0.104+ (async, WebSocket support)
- uvicorn ASGI server (production-ready)
- Python 3.10+ async/await

**Project Structure**:
```
gao_dev/
├── web/
│   ├── __init__.py
│   ├── server.py           # FastAPI application
│   ├── config.py           # Server configuration
│   └── middleware.py       # CORS, error handling
├── cli/
│   └── web_commands.py     # CLI: gao-dev start --web
└── frontend/
    └── dist/               # React production build
```

**API Endpoints** (Story 39.1):
- GET `/` - Serve index.html
- GET `/assets/*` - Static assets
- GET `/api/health` - Health check

### Dependencies

**Epic 30 (ChatREPL)**:
- None for this story (server infrastructure only)

**Epic 27 (GitIntegratedStateManager)**:
- None for this story (server infrastructure only)

### Configuration

**Environment Variables**:
- `WEB_HOST`: Default `127.0.0.1` (localhost only)
- `WEB_PORT`: Default `3000`
- `WEB_AUTO_OPEN_BROWSER`: Default `true`

**CLI Arguments**:
```bash
gao-dev start --web              # Start with defaults
gao-dev start --web --port 3001  # Custom port
gao-dev start --web --no-browser # Don't auto-open browser
```

---

## Test Scenarios

### Test 1: Successful Server Startup
**Given**: GAO-Dev is installed and frontend is built
**When**: User runs `gao-dev start --web`
**Then**:
- Server starts in <3 seconds
- Logs show: "Web interface available at http://127.0.0.1:3000"
- Browser opens automatically to localhost:3000
- Health check returns 200 OK

### Test 2: Port Conflict Handling
**Given**: Another process is using port 3000
**When**: User runs `gao-dev start --web`
**Then**:
- Server detects port conflict
- Error message: "Port 3000 already in use. Try `--port 3001`"
- Process exits with code 1

### Test 3: Graceful Shutdown
**Given**: Server is running
**When**: User presses Ctrl+C
**Then**:
- Server logs "Shutting down web server..."
- All connections closed cleanly
- Process exits with code 0

### Test 4: CORS Validation
**Given**: Server is running
**When**: Browser makes request from localhost:3000
**Then**: CORS headers allow request
**When**: Request comes from external origin (example.com)
**Then**: CORS headers reject request

### Test 5: Static File Serving
**Given**: Frontend build exists in /dist
**When**: Browser requests `/` and `/assets/main.js`
**Then**:
- Index.html served with correct content-type
- JavaScript files served with `application/javascript`
- CSS files served with `text/css`

---

## Definition of Done

### Code Quality
- [ ] Code follows GAO-Dev standards (DRY, SOLID, typed)
- [ ] Type hints throughout (no `Any`)
- [ ] structlog for all logging
- [ ] Error handling comprehensive
- [ ] Black formatting applied (line length 100)

### Testing
- [ ] Unit tests: 100% coverage for server.py
- [ ] Integration tests: Server startup, shutdown, health check
- [ ] E2E tests: CLI command → browser opens → health check passes
- [ ] Performance tests: Startup <3s, health check <10ms

### Documentation
- [ ] API documentation: /api/health endpoint
- [ ] Deployment guide: How to run web server
- [ ] Troubleshooting: Common port conflicts, build issues

### Code Review
- [ ] Code review approved by Winston (Technical Architect)
- [ ] No security vulnerabilities (localhost binding validated)
- [ ] No regressions (100% existing CLI tests pass)

---

## Implementation Notes

### FastAPI Application Structure

```python
# gao_dev/web/server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import structlog

logger = structlog.get_logger(__name__)

app = FastAPI(title="GAO-Dev Web Interface", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# Static file serving
app.mount("/assets", StaticFiles(directory="gao_dev/frontend/dist/assets"), name="assets")

@app.get("/")
async def serve_index():
    return FileResponse("gao_dev/frontend/dist/index.html")

def start_server(host: str = "127.0.0.1", port: int = 3000, auto_open: bool = True):
    """Start FastAPI web server"""
    logger.info("starting_web_server", host=host, port=port)

    if auto_open:
        import webbrowser
        webbrowser.open(f"http://{host}:{port}")

    uvicorn.run(app, host=host, port=port, log_level="info")
```

### CLI Command Integration

```python
# gao_dev/cli/web_commands.py
import click
from gao_dev.web.server import start_server

@click.command()
@click.option("--port", default=3000, help="Server port")
@click.option("--no-browser", is_flag=True, help="Don't auto-open browser")
def start_web(port: int, no_browser: bool):
    """Start GAO-Dev web interface"""
    try:
        start_server(port=port, auto_open=not no_browser)
    except OSError as e:
        if "Address already in use" in str(e):
            click.echo(f"Error: Port {port} already in use. Try `--port {port + 1}`")
            raise SystemExit(1)
        raise
```

---

## Related Stories

- **Story 39.2**: WebSocket Manager and Event Bus (builds on this server)
- **Story 39.3**: Session Lock and Read-Only Mode (adds middleware)
- **Story 39.4**: React + Vite Setup (frontend build served by this server)

---

**Story Owner**: Amelia (Software Developer)
**Reviewer**: Winston (Technical Architect)
**Tester**: Murat (Test Architect)
