# Troubleshooting Guide

**TL;DR**: Solutions to common issues across installation, development, web interface, workflows, and agents. Start with "Quick Diagnosis" section to identify your issue category.

**Quick Links**:
- [Installation Issues](#installation-issues) - Setup and environment problems
- [Development Issues](#development-issues) - Coding and testing problems
- [Web Interface Issues](#web-interface-issues) - UI and API problems
- [Workflow Issues](#workflow-issues) - Execution and variable resolution
- [Agent Issues](#agent-issues) - LLM and provider problems
- [Git & State Management](#git--state-management-issues) - File-DB sync issues
- [Performance Issues](#performance-issues) - Slow operations

---

## Quick Diagnosis

**Use this table to quickly find your issue category:**

| Symptoms | Category | Go To |
|----------|----------|-------|
| Code changes don't take effect, wrong project_root in logs | Installation | [Stale Installation](#stale-installation) |
| Import errors, module not found | Installation | [Import Errors](#import-errors) |
| `gao-dev` command not found | Installation | [CLI Not Found](#cli-not-found) |
| Tests failing, type errors | Development | [Test Failures](#test-failures) |
| Web UI not loading, blank page | Web Interface | [Web UI Not Loading](#web-ui-not-loading) |
| WebSocket disconnects, events not updating | Web Interface | [WebSocket Issues](#websocket-issues) |
| Variables not resolved, `{{var}}` in output | Workflows | [Variable Resolution](#variable-resolution-issues) |
| Files created in wrong location | Workflows | [File Location Issues](#file-location-issues) |
| API key errors, rate limits | Agents | [Provider Issues](#provider-configuration-issues) |
| File-DB out of sync, orphaned records | Git & State | [Consistency Issues](#consistency-issues) |
| Slow context loads, <80% cache hit rate | Performance | [Cache Performance](#cache-performance-issues) |

---

## Installation Issues

### Stale Installation

**Symptoms**:
- Code changes don't take effect
- Web server uses wrong `project_root`
- Logs show `C:\Python314\Lib\site-packages` instead of project directory
- CLI commands run old code

**Cause**: Mixed installation modes (beta testing + development)

**Solution**:

```bash
# 1. Verify installation mode
python verify_install.py

# If shows [FAIL]:

# Windows
reinstall_dev.bat

# macOS/Linux
./reinstall_dev.sh

# 2. Verify again
python verify_install.py  # Should show all [PASS]
```

**Prevention**:
- **NEVER** install both `pip install git+https://...` (beta) AND `pip install -e .` (dev)
- Always run `python verify_install.py` at session start
- If switching modes, clean first with `reinstall_dev.bat`

**See**: [CONTRIBUTING.md](CONTRIBUTING.md#installation) for detailed installation guide.

---

### Import Errors

**Symptoms**:
```
ModuleNotFoundError: No module named 'gao_dev'
ImportError: cannot import name 'GAODevOrchestrator'
```

**Solution**:

```bash
# 1. Ensure you're in project root
cd C:\Projects\gao-agile-dev

# 2. Install in development mode
pip install -e ".[dev]"

# 3. Verify installation
python verify_install.py  # Should show [PASS]

# 4. If still failing, check Python path
python -c "import sys; print('\n'.join(sys.path))"
# Should show: C:\Projects\gao-agile-dev

# 5. If not, reinstall
reinstall_dev.bat  # Windows
./reinstall_dev.sh  # macOS/Linux
```

**Common Causes**:
- Not in project root directory
- Virtual environment not activated
- Editable install not configured
- Conflicting installations in site-packages

---

### CLI Not Found

**Symptoms**:
```
'gao-dev' is not recognized as an internal or external command
```

**Solution**:

```bash
# 1. Verify installation
pip show gao-dev
# Should show: Location: c:\projects\gao-agile-dev

# 2. If not found, install
pip install -e ".[dev]"

# 3. Verify PATH includes Scripts directory
where gao-dev  # Windows
which gao-dev  # macOS/Linux

# 4. If still not found, use Python module syntax
python -m gao_dev.cli.main --help
```

**Windows-Specific**:
- Ensure `C:\Python314\Scripts` is in PATH
- Restart terminal after installation
- Use `py -m gao_dev.cli.main` if `python` not in PATH

---

## Development Issues

### Test Failures

**Symptoms**:
```
pytest tests/
FAILED tests/web/api/test_chat.py::test_send_message
```

**Diagnosis**:

```bash
# 1. Run specific test with verbose output
pytest tests/web/api/test_chat.py::test_send_message -vv

# 2. Check for missing dependencies
pip install -e ".[dev]"

# 3. Verify database is clean
rm -f .gao-dev/documents.db  # Or delete manually
gao-dev migrate

# 4. Check for stale fixtures
pytest --cache-clear tests/
```

**Common Causes**:

| Error | Cause | Fix |
|-------|-------|-----|
| `fixture 'client' not found` | Missing test dependencies | `pip install -e ".[dev]"` |
| `database is locked` | Stale DB connection | Delete `.gao-dev/documents.db`, re-run |
| `AssertionError: 401 != 200` | Missing API key in test | Set `ANTHROPIC_API_KEY` env var |
| `FileNotFoundError` | Test working directory wrong | Run `pytest` from project root |

**See**: [TESTING_GUIDE.md](developers/TESTING_GUIDE.md) for testing patterns.

---

### Type Errors

**Symptoms**:
```
mypy gao_dev/ --strict
error: Incompatible types in assignment
error: Missing type parameters
```

**Solution**:

```bash
# 1. Check specific file
mypy gao_dev/core/workflow_executor.py --strict

# 2. Common fixes:

# Missing type hints
def my_function(param):  # ❌ Bad
    return param

def my_function(param: str) -> str:  # ✅ Good
    return param

# Using Any
from typing import Any
def my_function(param: Any):  # ❌ Bad (not allowed)

def my_function(param: str | None):  # ✅ Good (explicit)

# Missing generic types
def my_function(items: list):  # ❌ Bad
def my_function(items: list[str]):  # ✅ Good
```

**Common Type Issues**:

| Issue | Fix |
|-------|-----|
| `Incompatible return value` | Add explicit return type hint |
| `Missing type parameters` | Use `list[str]` not `list` |
| `Need type annotation` | Add variable type hint |
| `Incompatible types in assignment` | Check types match on both sides |

---

### Code Changes Not Reflected

**Symptoms**:
- Edit file, but old behavior persists
- Breakpoints not hit in debugger
- Print statements don't appear

**Solution**:

```bash
# 1. Verify installation mode
python verify_install.py  # Must show [PASS]

# 2. If [FAIL], reinstall
reinstall_dev.bat  # Windows
./reinstall_dev.sh  # macOS/Linux

# 3. Restart any running processes
# Kill gao-dev web server
# Kill pytest processes
# Restart terminal

# 4. Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +  # macOS/Linux
# Windows: Delete __pycache__ folders manually

# 5. Verify changes loaded
python -c "import gao_dev; print(gao_dev.__file__)"
# Should show: C:\Projects\gao-agile-dev\gao_dev\__init__.py
```

---

## Web Interface Issues

### Web UI Not Loading

**Symptoms**:
- Blank page in browser
- "This site can't be reached"
- 404 errors

**Diagnosis**:

```bash
# 1. Check if server is running
gao-dev start

# 2. Check server logs
# Look for "Uvicorn running on http://127.0.0.1:3000"

# 3. Check port availability
netstat -ano | findstr :3000  # Windows
lsof -i :3000  # macOS/Linux

# 4. Try different port
gao-dev start --port 3001
```

**Common Issues**:

| Error | Cause | Fix |
|-------|-------|-----|
| `ERR_CONNECTION_REFUSED` | Server not running | Run `gao-dev start` |
| `Address already in use` | Port 3000 taken | Kill process or use `--port 3001` |
| `404 Not Found` | Wrong URL | Use `http://localhost:3000` not `http://127.0.0.1:3000` |
| Blank page, no errors | Frontend build issue | `cd gao_dev/web/frontend && npm run build` |

**Frontend Build Issues**:

```bash
# 1. Navigate to frontend
cd gao_dev/web/frontend

# 2. Install dependencies
npm install

# 3. Build frontend
npm run build

# 4. Verify build output
ls dist/  # Should contain index.html, assets/

# 5. Restart server
cd ../../..
gao-dev start
```

**See**: [features/web-interface/TROUBLESHOOTING.md](features/web-interface/TROUBLESHOOTING.md)

---

### WebSocket Issues

**Symptoms**:
- Events not updating in real-time
- "WebSocket disconnected" message
- Activity stream not showing new events

**Diagnosis**:

```bash
# 1. Check browser console (F12)
# Look for: "WebSocket connection failed"

# 2. Verify session token exists
ls .gao-dev/session.token  # Should exist

# 3. Check server logs
# Look for: "WebSocket client connected"

# 4. Test WebSocket connection
# Browser console:
new WebSocket('ws://localhost:3000/ws?token=YOUR_TOKEN')
```

**Solutions**:

```bash
# 1. Regenerate session token
rm .gao-dev/session.token
gao-dev start  # Creates new token

# 2. Check CORS settings
# In browser console, check if domain is allowed
# Should be: localhost:3000-3010, localhost:5173-5180

# 3. Verify WebSocket endpoint
curl http://localhost:3000/api/session/token
# Should return: {"token": "..."}

# 4. Check for proxy issues
# If behind corporate proxy, WebSocket may be blocked
# Try direct connection or different network
```

**Common Causes**:

| Issue | Cause | Fix |
|-------|-------|-----|
| Connection drops after 30s | Idle timeout | Server sends heartbeat, check server logs |
| Initial connection fails | Invalid token | Delete `.gao-dev/session.token`, restart |
| Events not received | EventBus not publishing | Check server logs for event emissions |
| Multiple disconnects | Port forwarding issue | Use direct connection, not SSH tunnel |

---

### API Errors (401, 403, 500)

**Symptoms**:
```
401 Unauthorized
403 Forbidden
500 Internal Server Error
```

**Solutions**:

```bash
# 401 Unauthorized - Invalid session token
rm .gao-dev/session.token
gao-dev start

# 403 Forbidden - Read-only mode (CLI active)
# Expected when CLI holds write lock
# Web UI shows "Read-only mode: CLI is active"
# Wait for CLI to release lock, or stop CLI

# 500 Internal Server Error - Check server logs
# Look in terminal running gao-dev start
# Common causes:
#   - Database locked
#   - File permission error
#   - Missing provider credentials

# Fix database lock
rm .gao-dev/documents.db
gao-dev migrate

# Fix file permissions
chmod 644 .gao-dev/*  # macOS/Linux
# Windows: Right-click → Properties → Security → Full Control
```

---

## Workflow Issues

### Variable Resolution Issues

**Symptoms**:
- Variables appear as `{{variable_name}}` in output
- Files created with literal `{{prd_location}}` in path
- Error: "Unresolved variable: prd_location"

**Diagnosis**:

```bash
# 1. Check workflow.yaml
cat gao_dev/workflows/2-plan/prd/workflow.yaml

# Should have:
# variables:
#   prd_location:
#     description: "Where to save PRD"
#     type: string
#     default: "docs/PRD.md"

# 2. Check config/defaults.yaml
cat gao_dev/config/defaults.yaml

# 3. Test variable resolution
gao-dev create-prd --name "Test" --prd-location "custom/path.md"
```

**Solutions**:

```yaml
# Add missing variable to workflow.yaml
variables:
  my_variable:
    description: "Description of variable"
    type: string
    default: "default/value"
    required: false

# Or add to config/defaults.yaml for global defaults
defaults:
  my_variable: "global/default"
```

**Variable Resolution Priority**:
1. **Runtime parameters** (highest) - `--prd-location "custom.md"`
2. **Workflow YAML defaults** - `workflow.yaml` → `variables` → `default`
3. **Config defaults** - `config/defaults.yaml` → `defaults`
4. **Common variables** (lowest) - Auto-generated: `{{date}}`, `{{project_name}}`

**See**: [features/document-lifecycle-system/VARIABLE_RESOLUTION.md](features/document-lifecycle-system/VARIABLE_RESOLUTION.md)

---

### File Location Issues

**Symptoms**:
- Files created in unexpected location
- Error: "Path traversal detected"
- Files created outside project root

**Diagnosis**:

```bash
# 1. Check resolved variable
gao-dev list-workflows --verbose
# Shows resolved variables for each workflow

# 2. Verify project root detection
gao-dev health
# Shows: "Project Root: /path/to/project"

# 3. Check for .gao-dev/ directory
ls -la .gao-dev/  # Should exist in project root
```

**Solutions**:

```bash
# 1. Verify project root
# GAO-Dev searches for .gao-dev/ or .sandbox.yaml
# Ensure you're in correct directory

cd /path/to/project  # Navigate to project root
gao-dev health       # Verify project root

# 2. Fix variable paths
# Paths should be relative to project root
# ✅ Good: "docs/PRD.md"
# ❌ Bad: "/absolute/path/PRD.md"
# ❌ Bad: "../outside/project/PRD.md"

# 3. Create .gao-dev/ if missing
mkdir .gao-dev
gao-dev migrate
```

---

### Workflow Execution Failures

**Symptoms**:
```
Error: Workflow 'prd' failed
Error: Agent did not complete successfully
```

**Diagnosis**:

```bash
# 1. Check workflow exists
gao-dev list-workflows | grep prd

# 2. Run with verbose logging
export LOG_LEVEL=DEBUG
gao-dev create-prd --name "Test"

# 3. Check agent logs
# Look for API errors, timeout errors

# 4. Verify provider configured
cat .gao-dev/provider_preferences.yaml
# Or check env var
echo $AGENT_PROVIDER
```

**Common Causes**:

| Error | Cause | Fix |
|-------|-------|-----|
| `Workflow not found` | Typo in workflow name | Check `gao-dev list-workflows` |
| `Agent timeout` | LLM API timeout | Increase timeout, check API key |
| `Variable unresolved` | Missing variable definition | Add to workflow.yaml or config/defaults.yaml |
| `Template not found` | Missing template.md | Create `template.md` in workflow directory |

---

## Agent Issues

### Provider Configuration Issues

**Symptoms**:
```
Error: Invalid API key
Error: Rate limit exceeded
Error: Model not found
```

**Solutions**:

```bash
# 1. Verify API key (Anthropic)
echo $ANTHROPIC_API_KEY
# Should start with: sk-ant-...

# 2. Set API key if missing
# Windows
set ANTHROPIC_API_KEY=sk-ant-...

# macOS/Linux
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Or configure provider preferences
cat > .gao-dev/provider_preferences.yaml <<EOF
provider: anthropic
model: claude-sonnet-4-5-20250929
api_key: sk-ant-...
EOF

# 4. Test provider connection
gao-dev health
# Shows: "Provider: anthropic ✓"

# 5. For Ollama (local models)
# Ensure Ollama is running
ollama serve  # In separate terminal
ollama list   # Verify models installed

# Configure for Ollama
cat > .gao-dev/provider_preferences.yaml <<EOF
provider: ollama
model: deepseek-r1
base_url: http://localhost:11434
EOF
```

**Rate Limit Handling**:

```bash
# Anthropic rate limits:
# - Free tier: 50 requests/day
# - Paid tier: Higher limits

# If rate limited:
# 1. Wait (limits reset after 24 hours)
# 2. Upgrade to paid tier
# 3. Use Ollama for local processing (no limits)

# Check rate limit status
# Look in server logs for:
# "rate_limit_error", retry_after: 3600  # Wait 1 hour
```

---

### Model Errors

**Symptoms**:
```
Error: Model 'gpt-4' not found
Error: Context length exceeded
```

**Solutions**:

```bash
# 1. Verify model name
# Anthropic models:
#   - claude-sonnet-4-5-20250929 (recommended)
#   - claude-3-5-sonnet-20241022
#   - claude-3-opus-20240229

# OpenAI models:
#   - gpt-4-turbo
#   - gpt-4
#   - gpt-3.5-turbo

# Ollama models (local):
#   - deepseek-r1
#   - llama2
#   - codellama

# 2. Update provider preferences
cat > .gao-dev/provider_preferences.yaml <<EOF
provider: anthropic
model: claude-sonnet-4-5-20250929
EOF

# 3. For context length issues
# Reduce conversation history size
# Or use model with larger context window
```

---

## Git & State Management Issues

### Consistency Issues

**Symptoms**:
- File exists but not in database
- Database record but file missing
- "Orphaned DB records detected"

**Diagnosis**:

```bash
# 1. Run consistency check
gao-dev consistency-check

# Shows:
# ✅ Files with DB records: 45
# ❌ Files without DB records: 3
# ❌ DB records without files: 2

# 2. See detailed report
gao-dev consistency-check --verbose
# Lists specific files/records
```

**Solutions**:

```bash
# 1. Automatic repair
gao-dev consistency-repair

# Performs:
# - Registers files missing from DB
# - Removes DB records for deleted files
# - Shows summary of changes

# 2. Manual verification
gao-dev state list-epics
gao-dev state list-stories

# 3. If corruption persists, rebuild DB
rm .gao-dev/documents.db
gao-dev migrate
# Note: Loses some metadata (timestamps, custom fields)
```

**Prevention**:
- ✅ Use `StateManager` for all file operations (automatic atomic transactions)
- ❌ Don't manually edit files in `docs/epics/` without updating DB
- ✅ Use `gao-dev state transition` for state changes
- ✅ Run `gao-dev consistency-check` regularly

**See**: [features/git-integrated-hybrid-wisdom/TROUBLESHOOTING.md](features/git-integrated-hybrid-wisdom/TROUBLESHOOTING.md)

---

### Git Commit Failures

**Symptoms**:
```
Error: Git commit failed
Error: Nothing to commit
Error: Detached HEAD state
```

**Solutions**:

```bash
# 1. Check git status
git status

# 2. Ensure on a branch (not detached HEAD)
git checkout main
# Or create new branch
git checkout -b feature/my-feature

# 3. Verify git user configured
git config user.name
git config user.email

# If not set:
git config user.name "Your Name"
git config user.email "you@example.com"

# 4. Check for uncommitted changes
git diff
git diff --staged

# 5. If "nothing to commit" but file was created
# StateManager may have already committed
git log --oneline -5  # Check recent commits
```

---

## Performance Issues

### Cache Performance Issues

**Symptoms**:
- Context loads taking >50ms consistently
- Cache hit rate <80%
- Slow workflow execution

**Diagnosis**:

```bash
# 1. Check cache stats
# (Requires instrumentation in FastContextLoader)

# 2. Monitor context load times
export LOG_LEVEL=DEBUG
gao-dev create-prd --name "Test"
# Look for: "context_loaded", duration_ms: ...

# 3. Verify cache size
# Default: 128 entries
# Check config/defaults.yaml
```

**Solutions**:

```python
# Increase cache size in config/defaults.yaml
fast_context_loader:
  cache_size: 256  # Increased from 128

# Or in code (for development):
from gao_dev.core.services.fast_context_loader import FastContextLoader

loader = FastContextLoader(cache_size=256)
```

**Expected Performance**:

| Metric | Target | What to Check |
|--------|--------|---------------|
| **Cache Hit Rate** | >80% | If <80%, increase cache_size |
| **Cache Hit Latency** | <5ms | If >5ms, check disk I/O |
| **Cache Miss Latency** | <50ms | If >50ms, check file system performance |

---

### Slow Workflow Execution

**Symptoms**:
- Workflows taking 2x+ expected time
- LLM API calls timing out

**Diagnosis**:

```bash
# 1. Enable debug logging
export LOG_LEVEL=DEBUG
gao-dev create-prd --name "Test"

# 2. Look for slow operations:
#    - "llm_call", duration_s: >30  # API call
#    - "file_write", duration_s: >1  # File I/O
#    - "git_commit", duration_s: >5  # Git operations

# 3. Check network latency
ping api.anthropic.com
# Should be <100ms

# 4. Check disk I/O
# Windows: Task Manager → Performance → Disk
# macOS/Linux: iostat -x 1
```

**Solutions**:

| Slow Operation | Cause | Fix |
|----------------|-------|-----|
| LLM API calls | Network latency | Check internet connection, try different network |
| File I/O | Disk performance | Close other programs, check disk health |
| Git commits | Large repo | Run `git gc` to optimize repository |
| Context loading | Cache misses | Increase cache size, warm cache |

---

## Getting Help

### Collect Diagnostic Information

Before asking for help, collect this information:

```bash
# 1. Installation verification
python verify_install.py > diagnostic.txt

# 2. System info
gao-dev health >> diagnostic.txt

# 3. Recent logs (if web server)
# Copy last 50 lines from terminal running gao-dev start

# 4. Error messages
# Copy complete error traceback

# 5. Environment
python --version >> diagnostic.txt
pip list | grep gao >> diagnostic.txt
git --version >> diagnostic.txt
```

### Where to Get Help

| Issue Type | Resource |
|------------|----------|
| **Installation** | [CONTRIBUTING.md](CONTRIBUTING.md#installation) |
| **Development** | [DEVELOPMENT_PATTERNS.md](developers/DEVELOPMENT_PATTERNS.md) |
| **Web Interface** | [features/web-interface/TROUBLESHOOTING.md](features/web-interface/TROUBLESHOOTING.md) |
| **Workflows** | [features/document-lifecycle-system/VARIABLE_RESOLUTION.md](features/document-lifecycle-system/VARIABLE_RESOLUTION.md) |
| **Git & State** | [features/git-integrated-hybrid-wisdom/TROUBLESHOOTING.md](features/git-integrated-hybrid-wisdom/TROUBLESHOOTING.md) |
| **Bug Reports** | [GitHub Issues](https://github.com/memyselfmike/gao-agile-dev/issues) |
| **General Questions** | Check [CLAUDE.md](../CLAUDE.md) for quick reference |

---

**See Also**:
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development workflow
- [DEVELOPMENT_PATTERNS.md](developers/DEVELOPMENT_PATTERNS.md) - Development patterns
- [VISUAL_ARCHITECTURE.md](VISUAL_ARCHITECTURE.md) - Architecture diagrams
- [API_REFERENCE.md](API_REFERENCE.md) - API documentation
- Feature-specific troubleshooting in `docs/features/*/TROUBLESHOOTING.md`
