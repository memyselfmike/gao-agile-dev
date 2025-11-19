# Troubleshooting Guide - Common Errors

Solutions for the most common GAO-Dev issues organized by error codes and symptoms.

## Table of Contents

- [Error Code Reference](#error-code-reference)
- [Top 10 Common Issues](#top-10-common-issues)
- [Provider Issues](#provider-issues)
- [Database Issues](#database-issues)
- [Platform-Specific Issues](#platform-specific-issues)
- [Performance Issues](#performance-issues)
- [Getting Help](#getting-help)

## Error Code Reference

GAO-Dev uses error codes to help identify issues quickly.

| Code | Category | Description |
|------|----------|-------------|
| E001-E099 | Configuration | Configuration and environment errors |
| E100-E199 | Provider | AI provider connection errors |
| E200-E299 | Database | Database and storage errors |
| E300-E399 | Workflow | Workflow execution errors |
| E400-E499 | Agent | Agent communication errors |
| E500-E599 | File System | File and directory errors |
| E600-E699 | Network | Network and API errors |
| E700-E799 | Validation | Input validation errors |

---

## Top 10 Common Issues

### 1. E001: API Key Not Found

**Error Message:**
```
E001: API key not found. Set ANTHROPIC_API_KEY environment variable.
```

**Cause:** The required API key is not set in the environment.

**Solution:**

```bash
# Option 1: Set environment variable
export ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Option 2: Create .env file
echo "ANTHROPIC_API_KEY=sk-ant-api03-your-key-here" >> .env

# Option 3: Pass via command line
gao-dev start --api-key sk-ant-api03-your-key-here
```

**Verification:**
```bash
echo $ANTHROPIC_API_KEY
gao-dev health
```

---

### 2. E101: Provider Not Found

**Error Message:**
```
E101: Provider 'unknown-provider' not found. Available: claude-code, opencode, direct-api
```

**Cause:** Invalid `AGENT_PROVIDER` value or provider not installed.

**Solution:**

```bash
# Check valid providers
gao-dev list-providers

# Set valid provider
export AGENT_PROVIDER=claude-code

# For Claude Code, verify CLI is installed
claude --version

# For OpenCode, verify CLI is installed
opencode --version
```

**Valid Providers:**
- `claude-code` - Anthropic's Claude Code CLI
- `opencode` - OpenCode CLI
- `direct-api-anthropic` - Direct Anthropic API
- `direct-api-openai` - Direct OpenAI API

---

### 3. E102: CLI Tool Not Found

**Error Message:**
```
E102: Claude Code CLI not found. Install from https://claude.ai/code
```

**Cause:** The required CLI tool is not installed or not in PATH.

**Solution:**

**For Claude Code:**
```bash
# Verify installation
which claude
claude --version

# If not found, install from:
# https://claude.ai/code

# Add to PATH if installed but not found
export PATH="$PATH:/path/to/claude"
```

**For OpenCode:**
```bash
# Verify installation
which opencode
opencode --version

# Install if needed
# Follow instructions at OpenCode documentation
```

---

### 4. E201: Database Locked

**Error Message:**
```
E201: Database is locked. Another process may be accessing it.
```

**Cause:** Multiple processes accessing the SQLite database, or a crashed process left a lock.

**Solution:**

```bash
# Find and kill any stuck GAO-Dev processes
ps aux | grep gao-dev
kill <pid>

# Remove stale lock file
rm -f .gao-dev/documents.db-journal
rm -f .gao-dev/documents.db-wal
rm -f .gao-dev/documents.db-shm

# If in Docker, ensure only one container accesses the volume
docker ps | grep gao-dev

# Restart GAO-Dev
gao-dev start
```

---

### 5. E202: Database Corruption

**Error Message:**
```
E202: Database appears to be corrupted.
```

**Cause:** Database file corrupted due to crash, disk issues, or interrupted write.

**Solution:**

```bash
# Run consistency check and repair
gao-dev consistency-check
gao-dev consistency-repair

# If repair fails, backup and recreate
cp .gao-dev/documents.db .gao-dev/documents.db.backup
rm .gao-dev/documents.db
gao-dev migrate  # Recreates database
```

**Prevention:**
- Don't kill GAO-Dev processes forcefully
- Ensure disk has sufficient space
- Use proper shutdown (`exit` or Ctrl+D)

---

### 6. E301: Workflow Not Found

**Error Message:**
```
E301: Workflow 'planning' not found in registry.
```

**Cause:** Requested workflow doesn't exist or workflows not loaded.

**Solution:**

```bash
# List available workflows
gao-dev list-workflows

# Check workflow loading
gao-dev health

# If workflows not loaded, check config
ls gao_dev/workflows/
```

**Common Workflow Names:**
- `planning`, `analysis`, `solutioning`, `implementation`
- Use exact names from `gao-dev list-workflows`

---

### 7. E501: Permission Denied

**Error Message:**
```
E501: Permission denied: Cannot write to .gao-dev/
```

**Cause:** Insufficient permissions to write to project directory.

**Solution:**

```bash
# Check directory ownership
ls -la .gao-dev/

# Fix ownership (Linux/macOS)
sudo chown -R $(whoami) .gao-dev/

# Fix permissions
chmod -R u+rw .gao-dev/

# In Docker, check volume permissions
docker exec gao-dev ls -la /app/.gao-dev/
```

---

### 8. E601: Network Timeout

**Error Message:**
```
E601: Network timeout connecting to API endpoint.
```

**Cause:** Network issues, firewall blocking, or API endpoint down.

**Solution:**

```bash
# Test network connectivity
curl -I https://api.anthropic.com/v1/messages

# Check for proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Increase timeout
export GAO_DEV_TIMEOUT=120

# Check API status
# Anthropic: https://status.anthropic.com
# OpenAI: https://status.openai.com
```

---

### 9. E701: Invalid Input

**Error Message:**
```
E701: Invalid input: Epic number must be a positive integer.
```

**Cause:** Command received invalid input parameters.

**Solution:**

```bash
# Check command help for valid parameters
gao-dev implement-story --help

# Use correct parameter types
gao-dev implement-story --epic 1 --story 1  # Correct
gao-dev implement-story --epic "one" --story "1"  # Wrong
```

---

### 10. E002: Configuration Error

**Error Message:**
```
E002: Invalid configuration in .gao-dev/provider_preferences.yaml
```

**Cause:** Malformed YAML or invalid values in configuration.

**Solution:**

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('.gao-dev/provider_preferences.yaml'))"

# Reset to defaults
rm .gao-dev/provider_preferences.yaml
gao-dev start  # Will prompt for new configuration

# Or manually fix
cat > .gao-dev/provider_preferences.yaml << EOF
provider: claude-code
backend: anthropic
EOF
```

---

## Provider Issues

### Claude Code CLI Issues

**"Claude not authenticated"**
```bash
# Re-authenticate
claude auth login
```

**"Rate limit exceeded"**
```bash
# Wait and retry, or upgrade plan
# Check current usage at console.anthropic.com
```

**"Model not available"**
```bash
# List available models
claude models list

# Use available model
export GAO_DEV_MODEL=claude-sonnet-4-20250514
```

### OpenCode Issues

**"OpenCode server not running"**
```bash
# Start OpenCode server
opencode serve

# Check server status
curl http://localhost:8000/health
```

**"Ollama not responding"**
```bash
# Start Ollama
ollama serve

# Verify model is pulled
ollama list
ollama pull deepseek-r1
```

### Direct API Issues

**"Invalid API key format"**
```bash
# Anthropic keys start with: sk-ant-api03-
# OpenAI keys start with: sk-

# Check format
echo $ANTHROPIC_API_KEY | head -c 20
```

**"Insufficient credits"**
```bash
# Check balance at provider dashboard
# Add credits or switch to different provider
```

---

## Database Issues

### Migration Failures

**"Migration failed: table already exists"**
```bash
# Check current migration state
gao-dev db-status

# Reset migrations if needed (will lose data)
rm .gao-dev/documents.db
gao-dev migrate
```

### Sync Issues

**"File-database mismatch"**
```bash
# Check consistency
gao-dev consistency-check

# Auto-repair
gao-dev consistency-repair

# Manual re-sync
gao-dev sync-documents
```

---

## Platform-Specific Issues

### Windows

**"'gao-dev' is not recognized"**
```cmd
REM Check Python Scripts in PATH
echo %PATH% | find "Scripts"

REM Add to PATH if needed
set PATH=%PATH%;%USERPROFILE%\AppData\Local\Programs\Python\Python311\Scripts

REM Or reinstall
pip install -e .
```

**"Unicode decode error"**
```cmd
REM Set UTF-8 encoding
chcp 65001

REM Or set in Python
set PYTHONIOENCODING=utf-8
```

**"Permission denied on .env"**
```powershell
# Check file attributes
Get-Acl .env

# Fix permissions
icacls .env /grant %USERNAME%:F
```

### macOS

**"SSL certificate verify failed"**
```bash
# Install certificates
/Applications/Python\ 3.11/Install\ Certificates.command

# Or set environment variable
export SSL_CERT_FILE=$(python -m certifi)
```

**"Keychain access denied"**
```bash
# Grant terminal access in System Preferences
# Security & Privacy > Privacy > Full Disk Access
```

### Linux

**"libsqlite3 not found"**
```bash
# Install SQLite development files
sudo apt install libsqlite3-dev  # Ubuntu/Debian
sudo yum install sqlite-devel     # CentOS/RHEL
```

**"DISPLAY not set"**
```bash
# For headless environments
export DISPLAY=:0
# Or use headless mode
export CI=true
```

---

## Performance Issues

### Slow Startup

**Symptoms:** `gao-dev start` takes more than 5 seconds.

**Solutions:**
```bash
# Clear cache
rm -rf .gao-dev/cache/

# Check database size
ls -lh .gao-dev/documents.db

# Vacuum database
sqlite3 .gao-dev/documents.db "VACUUM;"
```

### Slow Context Loading

**Symptoms:** Agent responses are delayed.

**Solutions:**
```bash
# Check cache hit rate in logs
export GAO_DEV_DEBUG=true
gao-dev start

# Increase cache size if needed (in config)
# Default is optimized for most use cases
```

### High Memory Usage

**Symptoms:** GAO-Dev using excessive RAM.

**Solutions:**
```bash
# Limit history size
export GAO_DEV_MAX_HISTORY=50

# Use smaller models
export GAO_DEV_MODEL=claude-3-haiku-20240307

# Check for memory leaks
# Restart GAO-Dev periodically in long-running scenarios
```

---

## Getting Help

### Diagnostic Information

Collect this information when reporting issues:

```bash
# System info
gao-dev version
python --version
echo $AGENT_PROVIDER
gao-dev health

# Error logs
cat .gao-dev/error.log | tail -100

# Environment
env | grep -E "GAO_DEV|AGENT_|ANTHROPIC|OPENAI"
```

### Debug Mode

Enable verbose logging:

```bash
export GAO_DEV_DEBUG=true
export GAO_DEV_LOG_LEVEL=DEBUG
gao-dev start
```

### Log Files

Check these locations for logs:

- `.gao-dev/error.log` - Error logs
- `.gao-dev/debug.log` - Debug logs (when enabled)
- `sandbox/metrics/` - Benchmark logs

### Community Support

- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Ask questions and share solutions
- **Documentation**: Check the full docs at `docs/INDEX.md`

---

**See Also:**
- [Environment Variables Reference](../guides/environment-variables.md)
- [Credential Management Guide](../guides/credential-management.md)
- [Docker Deployment Guide](../getting-started/docker-deployment.md)

---

**Last Updated**: 2025-11-19
