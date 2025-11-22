# GAO-Dev Web Interface - Startup Guide

This guide explains how to start the GAO-Dev web interface with flexible port configuration.

## Quick Start

### Option 1: Using the Startup Script (Recommended)

```bash
# Start both backend and frontend
start_web.bat
```

This will:
- Load configuration from `.env` file (if it exists)
- Stop any existing Python/Node processes
- Start backend on port 3000 (or `WEB_PORT` from `.env`)
- Start frontend on port 5173+ (auto-finds available port)
- Open both in separate terminal windows

### Option 2: Using the CLI Command

```bash
# Start with defaults
gao-dev web start

# Custom port
gao-dev web start --port 3001

# Custom host (e.g., for network access)
gao-dev web start --host 0.0.0.0 --port 3000

# Don't auto-open browser
gao-dev web start --no-browser
```

### Option 3: Manual Startup

**Backend:**
```bash
python -m uvicorn gao_dev.web.server:app --host 127.0.0.1 --port 3000 --reload
```

**Frontend:**
```bash
cd gao_dev/web/frontend
npm run dev
```

## Configuration

### Environment Variables

Create or edit `.env` in the project root:

```bash
# Web server host (default: 127.0.0.1 - localhost only)
WEB_HOST=127.0.0.1

# Web server port (default: 3000)
# If port is in use, try another port or set this to auto-select
WEB_PORT=3000

# Auto-open browser on startup (default: true)
WEB_AUTO_OPEN_BROWSER=true
```

### Port Handling

The system is designed to handle port conflicts gracefully:

**Backend:**
- Default: Port 3000
- Configurable via `WEB_PORT` environment variable
- CLI command supports `--port` flag
- CORS configured for ports 3000-3010

**Frontend:**
- Default: Port 5173 (Vite default)
- Auto-fallback: Tries 5173, 5174, 5175, ... 5180
- Vite proxy forwards `/api` and `/ws` to backend
- CORS configured for ports 5173-5180

**Why This Works:**
- Vite's proxy configuration forwards API requests to the backend
- CORS allows requests from any port in the configured ranges
- Frontend port doesn't matter as long as it's in the 5173-5180 range

## Troubleshooting

### Port Already in Use

If you see "Port already in use" errors:

**Solution 1:** Use a different port
```bash
set WEB_PORT=3001
start_web.bat
```

**Solution 2:** Kill existing processes
```bash
# Windows
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# Or use restart script
restart_server.bat
```

**Solution 3:** Use the startup script (handles this automatically)
```bash
start_web.bat  # Kills existing processes by default
```

### Frontend Can't Connect to Backend

**Check backend is running:**
- Look for "Uvicorn running on http://127.0.0.1:3000" message
- Visit http://127.0.0.1:3000/api/health

**Check CORS configuration:**
- Backend CORS is configured for ports 3000-3010 and 5173-5180
- If using different ports, update `gao_dev/web/config.py`

**Check proxy configuration:**
- Frontend proxy is in `gao_dev/web/frontend/vite.config.ts`
- Should forward `/api` to `http://127.0.0.1:3000`

### File Watcher Errors

If you see file watcher errors on startup:
- This was fixed in the latest version
- Ensure you have the latest code
- Check `gao_dev/web/file_watcher.py` imports `EventType`

## Scripts Reference

### `start_web.bat`
**Purpose:** Start both backend and frontend with one command
**Features:**
- Loads `.env` configuration
- Kills existing processes
- Starts both servers in separate windows
- Shows configuration and URLs

**Usage:**
```bash
start_web.bat              # Normal start
start_web.bat --no-kill    # Don't kill existing processes
```

### `restart_server.bat`
**Purpose:** Restart backend only (legacy script, updated for .env support)
**Features:**
- Loads `.env` configuration
- Kills all Python processes
- Restarts backend in new window

**Usage:**
```bash
restart_server.bat
```

## Architecture Notes

### Backend (FastAPI + Uvicorn)
- **Location:** `gao_dev/web/server.py`
- **Config:** `gao_dev/web/config.py`
- **Default Port:** 3000 (configurable)
- **API Endpoints:** `/api/*`
- **WebSocket:** `/ws`
- **Features:**
  - Real-time file watching
  - WebSocket for live updates
  - Session management
  - Read-only mode protection

### Frontend (Vite + React + TypeScript)
- **Location:** `gao_dev/web/frontend/`
- **Default Port:** 5173 (auto-fallback to 5174+)
- **Build Tool:** Vite 7.x
- **Framework:** React 19
- **Features:**
  - Hot module replacement (HMR)
  - Auto-proxy to backend
  - Monaco editor integration
  - Real-time collaboration UI

### CORS Configuration
The backend CORS is configured to accept requests from:
- Backend ports: 3000-3010 (both localhost and 127.0.0.1)
- Frontend ports: 5173-5180 (both localhost and 127.0.0.1)

This wide range ensures smooth startup even when default ports are busy.

## Advanced Configuration

### Network Access (Access from other devices)

To allow access from other devices on your network:

```bash
# Set in .env
WEB_HOST=0.0.0.0
WEB_PORT=3000

# Or use CLI
gao-dev web start --host 0.0.0.0
```

**Warning:** This exposes the server to your local network. Use with caution.

### Custom Port Ranges

If you need ports outside the default ranges, edit `gao_dev/web/config.py`:

```python
def _get_cors_origins() -> List[str]:
    # Add your custom port ranges here
    for port in range(8000, 8010):  # Custom range
        origins.extend([...])
```

### Production Deployment

For production:

1. Build the frontend:
```bash
cd gao_dev/web/frontend
npm run build
```

2. Run backend with production settings:
```bash
uvicorn gao_dev.web.server:app --host 0.0.0.0 --port 80 --workers 4
```

3. Consider using:
   - Nginx as reverse proxy
   - SSL/TLS certificates
   - Environment-based configuration
   - Process manager (systemd, supervisor, PM2)

## Support

If you encounter issues not covered here:
1. Check the logs in the terminal windows
2. Verify `.env` configuration
3. Try manual startup to isolate the issue
4. Check `gao_dev/web/server.py` logs for backend errors
5. Check browser console for frontend errors

## Recent Improvements

- **Dynamic CORS:** Support for port ranges 3000-3010 and 5173-5180
- **Environment Variables:** Full `.env` support for configuration
- **Smart Startup:** `start_web.bat` handles process cleanup automatically
- **File Watcher Fix:** Resolved async/sync issues with file watching
- **Better Error Messages:** Clear port conflict messages with suggestions
